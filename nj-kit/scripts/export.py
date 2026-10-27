#!/usr/bin/env python3
"""
Snapshot the current setup into `manifest.json`.

Run this whenever the toolkit changes — a skill added, a hook changed, the
house font swapped — so the manifest stays a description of what is actually
here rather than of what was here once.

    python export.py                 refresh manifest.json in place
    python export.py --dry-run       show what would change

Third-party skills are recorded as `owner/repo@skill`, so a fresh machine
re-fetches them from source rather than carrying a stale copy. Skills that are
ours — the ones no registry has — are recorded as `bundled` and their files are
copied into `bundled/` by this script, because a reference to something that
exists only on this laptop is not portable.

A third class exists and is not scanned: skills that belong to a repository
(`PROJECT_SKILLS`). Those are linked, never copied, and are recorded by hand in
`manifest.json` → `project_skills`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
# The skills live in one directory — whichever one this kit is sitting in.
# They were split between a project folder and the user folder until
# 2026-09-03; a single location means no guessing about which copy is current,
# and ~/.claude/skills is the one that is private to this machine and active in
# every repo. `SKILLS` is derived rather than hardcoded so the kit still works
# when it is installed into a project.
SKILLS = KIT.parent
USER_HOME = Path.home() / ".claude"

# Supply-chain pins (hand-maintained, never rewritten here): see pinned-sources.json.
PINS_FILE = KIT / "pinned-sources.json"
PINS = json.loads(PINS_FILE.read_text(encoding="utf-8")) if PINS_FILE.exists() else {}


# -- redaction (security fix 2026-10-27) --------------------------------------------------------
# Everything read from the machine that lands in manifest.json, bundled/ or the zip goes through
# these. Pure functions, covered by tests/test_export_redaction.py.
_SECRET_FLAG = re.compile(r"^--?(?:token|access[-_]?token|api[-_]?key|apikey|key|secret|client[-_]?secret|"
                          r"password|passwd|pass|auth|authorization|bearer|cookie)$", re.I)
_SECRET_VALUE = re.compile(
    r"(sk-or-v1-[A-Za-z0-9]{10,}|gsk_[A-Za-z0-9]{10,}|sk-ant-[A-Za-z0-9_-]{10,}|sk-(?:proj-)?[A-Za-z0-9]{32,}"
    r"|gh[pousr]_[A-Za-z0-9]{20,}|github[_]pat_[A-Za-z0-9_]{20,}|AIza[0-9A-Za-z_-]{30,}|xox[abprs]-[A-Za-z0-9-]{10,}"
    r"|npm_[A-Za-z0-9]{30,}|Bearer\s+[A-Za-z0-9._~+/=-]{16,})")
_ENV_ASSIGN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|AUTH|COOKIE)[A-Za-z0-9_]*)="
                         r"(\"[^\"]*\"|'[^']*'|[^\s;&|]+)", re.I)
_URL_QUERY = re.compile(r"(https?://[^\s\"'?#]+)\?[^\s\"'#]*")
_URL_USERINFO = re.compile(r"(://)[^/\s@\"']+:[^/\s@\"']+@")
_FLAG_INLINE = re.compile(r"(--?[A-Za-z][A-Za-z0-9_-]*)[=\s]+(\"[^\"]*\"|'[^']*'|[^\s;&|]+)")
REDACTED = "<redacted>"


def _home_variants() -> list[str]:
    h = str(Path.home())
    return sorted({h, h.replace("\\", "/"), h.replace("/", "\\"), h.replace("\\", "\\\\")}, key=len, reverse=True)


def redact_text(text: str) -> str:
    """Remove credential-shaped values, URL query strings and userinfo, and the home directory path."""
    for hv in _home_variants():
        text = text.replace(hv, "~")
    text = _URL_USERINFO.sub(r"\1" + REDACTED + "@", text)
    text = _URL_QUERY.sub(lambda m: m.group(1) + "?" + REDACTED, text)
    text = _ENV_ASSIGN.sub(lambda m: m.group(1) + "=" + REDACTED, text)
    text = _FLAG_INLINE.sub(lambda m: (m.group(1) + " " + REDACTED) if _SECRET_FLAG.match(m.group(1)) else m.group(0), text)
    text = _SECRET_VALUE.sub(REDACTED, text)
    return text


def redact_command(cmd: str) -> str:
    """A hook or statusLine command line."""
    return redact_text(cmd)


def redact_args(args: list) -> list:
    """An MCP args list: the value after --token/--api-key/--key..., --flag=value forms, URLs, key shapes."""
    out, hide = [], False
    for a in args:
        if not isinstance(a, str):
            out.append(a)
            continue
        if hide:
            out.append(REDACTED)
            hide = False
            continue
        m = re.match(r"^(--?[A-Za-z][A-Za-z0-9_-]*)=(.*)$", a, re.S)
        if m and _SECRET_FLAG.match(m.group(1)):
            out.append(m.group(1) + "=" + REDACTED)
            continue
        if _SECRET_FLAG.match(a):
            out.append(a)
            hide = True
            continue
        out.append(redact_text(a))
    return out


def pin_npx_args(args: list) -> list:
    """Force every npm package named in pinned-sources.json to its exact version (no @latest, no bare name)."""
    pins = PINS.get("npm", {})
    out = []
    for a in args:
        if isinstance(a, str):
            for pkg, ver in pins.items():
                if a == pkg or (a.startswith(pkg + "@") and a[len(pkg) + 1:] in ("latest", "")):
                    a = f"{pkg}@{ver}"
        out.append(a)
    return out


# What the zip must never carry. Provider key shapes and private keys only, so docs that merely
# mention the word "token" do not block an export.
_LEAK_RE = re.compile(_SECRET_VALUE.pattern + r"|-----BEGIN [A-Z ]*PRIVATE KEY")


def leak_scan(root: Path) -> list[str]:
    """Return 'relative/path: shape' for every text file under root holding a credential shape."""
    hits = []
    for f in root.rglob("*"):
        if not f.is_file() or f.stat().st_size > 2_000_000 or f.suffix.lower() in {".woff2", ".otf", ".ttf", ".png", ".gif", ".webp", ".pdf", ".zip", ".db", ".jpg"}:
            continue
        if {"node_modules", ".git", "__pycache__"} & set(f.parts):
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        m = _LEAK_RE.search(text)
        if m:
            hits.append(f"{f.relative_to(root)}: {m.group(0)[:6]}...")
    return hits

# Skills that live in a public repo. Anything not listed here and present on
# disk is treated as ours and bundled.
KNOWN_SOURCES = {
    # caveman — terse output mode (the owner 2026-09-17; on-request only since 2026-09-29).
    # Docs only, no scripts; 514K installs on skills.sh.
    "caveman": "juliusbrussee/caveman",
    "web-design-guidelines": "nexu-io/open-design",
    "doc-coauthoring": "anthropics/skills",
    "frontend-design": "anthropics/skills",
    "mcp-builder": "anthropics/skills",
    "skill-creator": "anthropics/skills",
    "playwright-best-practices": "currents-dev/playwright-best-practices-skill",
    "test-fixing": "mhattingpete/claude-skills-marketplace",
    "chrome-extension-development": "mindrally/skills",
    "prompt-engineering-patterns": "wshobson/agents",
    "webapp-testing": "anthropics/skills",
    "docx": "anthropics/skills",
    "xlsx": "anthropics/skills",
    "pdf": "anthropics/skills",
    # emilkowalski/skills — apple-design, Apple's WWDC "Designing Fluid
    # Interfaces" rules translated to the web (springs, 1:1 tracking, velocity,
    # interruptible motion, materials, optical type). Installed 2026-09-17 for
    # the QA Wrap UI rework; audited by nj-security-review, 0 findings, docs
    # only, no scripts and no hosts. Emil Kowalski (sonner, vaul), 145.9K installs.
    "apple-design": "emilkowalski/skills",
    # heygen-com/hyperframes — the entry point plus its domain skills (core,
    # animation, creative, keyframes, cli). Installed 2026-09-16
    # with `npx skills add heygen-com/hyperframes -g`, for QA Wrap (thumbnails)
    # and the ENSERA project in the same evening. Audited by nj-security-review:
    # one medium finding, hyperframes-cli/references/lambda.md mentions
    # ~/.aws/credentials as a prerequisite of the optional Lambda renderer —
    # prose, not code; nothing reads the file. Hosts referenced are docs only.
    # The entry-point skill calls itself the "mandatory" video default; in this
    # house it is NOT — films stay on Playwright + ffmpeg + Gemini TTS (OpenRouter).
    # Runtime: `npx hyperframes` (0.8.43), no global.
    "hyperframes": "heygen-com/hyperframes",
    "hyperframes-core": "heygen-com/hyperframes",
    "hyperframes-animation": "heygen-com/hyperframes",
    "hyperframes-creative": "heygen-com/hyperframes",
    "hyperframes-keyframes": "heygen-com/hyperframes",
    "hyperframes-cli": "heygen-com/hyperframes",
    # Three more heygen-com/hyperframes skills that arrived with the 2026-09-16
    # install (registry, audio, media-use). Public, so re-fetched, not bundled:
    # media-use alone carries ~1.5 MB of SFX assets that were bloating the zip.
    "hyperframes-registry": "heygen-com/hyperframes",
    "hyperframes-audio": "heygen-com/hyperframes",
    "media-use": "heygen-com/hyperframes",
    # Anthropic's own vulnerability scanner, reviewed 2026-09-07 and passed
    # (no network egress anywhere in the package, stdlib-only hooks, git run
    # through argument lists rather than a shell). It ships as a *plugin*, not
    # a bare skill: `plugins/claude-security/skills/claude-security/` cannot
    # stand alone because its jobs shell out to the plugin's own scripts/ and
    # dispatch to its agents/. Listed here so that if it is installed it is
    # classified as public rather than frozen into bundled/. Not installed on
    # this machine: it registers session-wide hooks, which is a change to the
    # harness that is the owner's to make. See the 2026-09-07 addendum.
    "claude-security": "anthropics/claude-plugins-official",
    # remotion-dev/claude-code-plugin — the official Remotion skill pack (12
    # skills: create, best-practices, animation/markup, captions, multimedia,
    # maps, studio, render, interactivity, saas, docs, upgrade). Installed
    # 2026-09-21 on the owner's word: code-driven motion graphics in React, a
    # second lane next to HyperFrames. MIT, docs only — 162 markdown files, no
    # scripts, no hooks, no egress; the only credential names in it are doc
    # examples for OPTIONAL third-party services (REMOTION_MAPBOX_TOKEN,
    # REMOTION_MAPTILER_KEY, ELEVENLABS_API_KEY) in the maps and voiceover
    # pages. Those cost money, so they stay unused here (free-tools rule).
    # Ships as a *plugin*, so the record of why lives in manifest.json →
    # plugins; listed here only so a new machine re-fetches rather than
    # bundling 162 files into the zip.
    "remotion-create": "remotion-dev/claude-code-plugin",
    "remotion-best-practices": "remotion-dev/claude-code-plugin",
    "remotion-markup": "remotion-dev/claude-code-plugin",
    "remotion-captions": "remotion-dev/claude-code-plugin",
    "remotion-multimedia": "remotion-dev/claude-code-plugin",
    "remotion-maps": "remotion-dev/claude-code-plugin",
    "remotion-studio": "remotion-dev/claude-code-plugin",
    "remotion-render": "remotion-dev/claude-code-plugin",
    "remotion-interactivity": "remotion-dev/claude-code-plugin",
    "remotion-saas": "remotion-dev/claude-code-plugin",
    "remotion-docs": "remotion-dev/claude-code-plugin",
    "remotion-upgrade": "remotion-dev/claude-code-plugin",
    "no-ai-slop": "petergyang/no-ai-slop",
    "ui-ux-pro-max": "nextlevelbuilder/ui-ux-pro-max-skill",
    "simple-issue-description": "every-app/open-seo",
    # taoufik123-collab/claude-watch — ships its own SessionStart hook under
    # hooks/ and talks to api.groq.com / api.openai.com with a Whisper key
    # read from ~/.config/watch/.env. Only the skill is installed; the hook
    # is not registered. Verdict REVIEW — see SECURITY-REVIEW-2026-09-06.md.
    "watch": "taoufik123-collab/claude-watch",
    # DietrichGebert/ponytail — over-engineering brake, added 2026-09-05 after a
    # security review (MIT, prompt-text only; the optional plugin tier writes a
    # statusLine to ~/.claude/settings.json, which we did NOT install).
    "ponytail": "dietrichgebert/ponytail",
    "ponytail-review": "dietrichgebert/ponytail",
    # github/awesome-copilot — behaviour-preserving refactoring method, added
    # 2026-09-07. MIT, one SKILL.md, prompt text only: no scripts, no hooks, no
    # network, no credential or environment reads, no install-time action.
    # `audit.py` returns 0 findings across all ten categories. Verdict SAFE —
    # see SECURITY-REVIEW-2026-09-06.md, the 2026-09-07 `refactor` row. Chosen
    # over mattpocock/skills@request-refactor-plan, which the registry still
    # lists at 209K installs but which no longer exists in that repository.
    "refactor": "github/awesome-copilot",
    # anthropics/financial-services — added 2026-09-10 as the client's «pitch».
    # 34.8K stars, 2.1K installs, and the only candidate for that name that
    # cleared the vetting bar: everything else was an unknown author under
    # 1.6K installs, and the 1.6K one fails Agent Trust Hub. Five markdown files,
    # 68 KB, no scripts, no network, no credential reads, no hooks. audit.py: 0
    # findings, one host referenced (schemas.openxmlformats.org — the OOXML
    # namespace URI, not a call). skillspector: 17/100 LOW; its single HIGH
    # ("hidden instructions", xml-reference.md:90) is `<!-- -->` inside a
    # PowerPoint XML example. Verdict SAFE. **Scope caveat, worth knowing before
    # reaching for it:** it populates an existing IB .pptx template and says so
    # — "not for creating presentations from scratch" — so a from-scratch
    # one-pager is not what it does. Installed under its published name; the
    # client's short name for it is `pitch`.
    "pitch-deck": "anthropics/financial-services",
}

# Hand-written `why` notes. The manifest's `why` is otherwise the skill's own
# description, which is written to *trigger* a skill rather than to explain to a
# reader why it is on this machine — and for a third-party skill it is the
# author's sentence, not ours. Anything named here wins over `describe()`.
# Added 2026-09-10 with the five skills below.
WHY = {
    "devil": "Adversarial critique of a plan or decision before it is acted on — ranked objections, the assumption each attacks, and the cheapest test that would settle it.",
    "10x": "Senior-engineer discipline for work someone else will run: read before writing, small-and-complete changes, a check that could have failed, and a report that says what is not done.",
    "scout": "Read-only reconnaissance of an unfamiliar repository, delivered as a one-page brief — how it builds and runs, what a change will drag with it, and where the traps are.",
    "script-your-tools": "The token rule: more than ~3 tool calls of one kind become one script, run as a single action, printing only the summary — with dry-run, idempotence and safe-delete as the guards.",
    "pitch-deck": "Populating an investment-banking pitch-deck template from source data — the client's «pitch». Template population only, not decks from scratch.",
}

# Skills that belong to a repository rather than to this machine. They are ours,
# they are NOT in KNOWN_SOURCES, and they are **linked, never copied**: a
# junction on Windows, a symlink elsewhere, from the working directory's
# `.claude/skills/<name>` to the repo's own copy. A copy would drift from the
# tracked original the moment either side is edited, and the repo — which tracks
# these in git — is the authority, not the kit.
#
# They live outside `SKILLS`, so `collect()` never sees them and nothing here
# derives them; `manifest.json` → `project_skills` is the hand-maintained record
# of where each one lives and why it exists, and `install.py` links them.
# Added 2026-09-06 (project-tests).
PROJECT_SKILLS = {
    # ENSERA (<ENSERA-root>/.claude/skills), 2026-09-16 -- the five
    # sector skills; they read the project's kb.py, so they cannot live outside it.
    "nj-research",
    "nj-design",
    "nj-marketing",
    "nj-programs",
    "nj-production",
    "project-e2e",
    "project-manuals",
    "project-srs",
    "project-automation-tests",
}

# Skills that are ours and must travel as files. Kept in step with what
# `collect()` actually classifies as ours — this list is documentation for a
# reader, not the decision (the decision is "not in KNOWN_SOURCES"), and it had
# drifted three skills behind by 2026-09-06.
#
# The last three live OUTSIDE `SKILLS`, in the project-tests repository. They are
# listed here because they are ours by the same test — absent from
# KNOWN_SOURCES — but they are exempt from bundling in both directions below,
# because bundling one would freeze a copy of a file the repo tracks.
OURS = {
    "arabic-english-proofreading",
    "nj-kit",
    "nj-delegate",  # added 2026-09-08: the director/worker modes (Standard, Eco, Max), routing table, worker brief, per-project handoff.md
    "nj-learn",
    "nj-method",
    "nj-security-review",
    "pdf-typography",
    "safe-delete",
    # added 2026-09-09: auditing a document against the built system — the
    # client's Arabic method (references/method-ar.md, verbatim) generalised to
    # manuals, training material, README/API docs, plus the ISO 29148 / INCOSE
    # / traceability / docs-as-code additions. Ours: written here, in no repo.
    "srs-verifier",
    # website-fine-print — added 2026-09-06. Ours, deliberately NOT in
    # KNOWN_SOURCES: the nineteen-point list it is built on came off a public
    # Instagram reel (research/46-reel-brief.md), but the skill — the split into
    # machine-checkable / delegated / judgement, the DECLARED-OBSERVED-GAP-MANUAL
    # vocabulary, the bilingual report and the standards mapping — is written
    # here and exists in no repository. Bundled, so it travels.
    "website-fine-print",
    "workflow-diagram",
    # Added 2026-09-10. Four skills the client asked for by short name. Three of
    # them were searched for on skills.sh first and authored here instead,
    # because nothing published cleared the bar: `devil` — the best
    # devils-advocate skill had 258 installs from an unknown author, the rest
    # under 130; `10x` — no published skill answers "senior-engineer quality
    # guidance" (the 10x-cli hits are a different product, and the 2.3K
    # `engineering-skills` is a 32-skill pack, wrong shape for one short name);
    # `scout` — the 1.1K `ruvnet/ruflo@agent-scout-explorer` is a claude-flow
    # agent persona built on mandatory memory-coordination hooks, which is a
    # harness change, not a skill. The fourth is the client's own rule.
    "devil",
    "10x",
    "scout",
    "script-your-tools",  # "stop calling tools one by one" — batch into one script, one call
    # added 2026-10-16: the knowledge-book layer on nj-evidence, distilled from the QA Engineer
    # repo and hardened by a 5-POV devil council over 3 rounds. Ours, in no public repo. Bundled.
    "nj-knowledge-book",
    *PROJECT_SKILLS,
}


def describe(skill_dir: Path) -> str:
    """
    The skill's description, including the YAML block-scalar form.

    `description: >` or `description: |` puts the text on the *following*
    indented lines. Reading only the key's own line returns the marker itself —
    three skills came back described as ">" and "|" before this handled it.
    """
    md = skill_dir / "SKILL.md"
    if not md.exists():
        return ""
    lines = md.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("description:"):
            continue
        value = line.split(":", 1)[1].strip()
        if value not in (">", "|", ">-", "|-", ">+", "|+"):
            return value.strip('"')[:160]
        block = []
        for follow in lines[i + 1:]:
            if follow.strip() and not follow.startswith((" ", "\t")):
                break
            block.append(follow.strip())
        return " ".join(b for b in block if b)[:160]
    return ""


def collect() -> dict:
    """
    Everything beside this kit, split by whether a registry can supply it.

    Anything in KNOWN_SOURCES is re-fetchable and recorded as a reference.
    Everything else is treated as ours and bundled — including skills added
    later that this file has never heard of, which is the safer default: a skill
    wrongly bundled still works, whereas one wrongly assumed to be public
    vanishes on the next machine.
    """
    third_party, ours = [], []

    for d in sorted(SKILLS.iterdir()):
        if not d.is_dir() or not (d / "SKILL.md").exists() or d.name == "nj-kit":
            continue
        # A project skill reached this directory only by being linked into it.
        # Following the link and bundling it would copy a file the repo tracks
        # and then ship the copy for ever; `manifest.json` → `project_skills`
        # carries these instead, and install.py re-creates the link.
        if d.name in PROJECT_SKILLS:
            continue
        why = WHY.get(d.name) or describe(d)
        if d.name in KNOWN_SOURCES:
            src_repo = KNOWN_SOURCES[d.name]
            ref = PINS.get("repos", {}).get(src_repo)
            if not ref:
                print(f"  WARNING: {d.name} ({src_repo}) has no pinned commit in pinned-sources.json; install.py will refuse to fetch it")
            third_party.append({"skill": d.name, "source": src_repo, "ref": ref, "why": why})
        else:
            ours.append({"skill": d.name, "from": "local", "why": why})

    return {"third_party": third_party, "ours": ours}


def live_mcp_servers(previous: dict) -> dict:
    """
    MCP servers as actually configured, keeping the hand-written `why` notes.

    The roster is derivable and the reasons are not — "real Chrome because the
    portal's sign-in is behind reCAPTCHA" is knowledge no config file holds. So
    the shape is taken from `~/.claude.json` and the explanation is carried
    across; a server that appears with no note is flagged rather than silently
    shipped undocumented.
    """
    path = Path.home() / ".claude.json"
    if not path.exists():
        return previous
    live = json.loads(path.read_text(encoding="utf-8")).get("mcpServers", {})
    home = str(Path.home()).replace("\\", "/")
    out = {}
    for name, spec in live.items():
        spec = dict(spec)
        if "args" in spec:
            # Store the portable form; install.py expands it again. Normalise separators first:
            # a mixed "C:\\Users\\X/..." path never matched the forward-slash home and shipped verbatim.
            spec["args"] = [a.replace("\\", "/").replace(home, "~") if isinstance(a, str) and (home in a.replace("\\", "/")) else a
                            for a in spec["args"]]
        # Never ship a credential (2026-10-10: a Figma API key went out in env). Names only; the user sets values.
        if isinstance(spec.get("env"), dict):
            spec["env"] = {k: "<set your own>" for k in spec["env"]}
        for k in ("headers",):
            if isinstance(spec.get(k), dict):
                spec[k] = {h: "<set your own>" for h in spec[k]}
        if isinstance(spec.get("args"), list):
            spec["args"] = pin_npx_args(redact_args(spec["args"]))
        for k in ("url", "command"):
            if isinstance(spec.get(k), str):
                spec[k] = redact_text(spec[k])
        spec["why"] = previous.get(name, {}).get("why", "TODO: say why this server is here")
        out[name] = spec
    return out


def live_hooks(previous: dict) -> dict:
    """
    Every hook event in user settings, plus the statusLine, reasons preserved.

    Widened 2026-09-06. This read only `Stop` before, because `Stop` was the only
    event the kit itself registers — and that made every *other* hook invisible.
    The security review found a `SessionStart` hook and a `statusLine` command
    running node out of `~/.claude/.claude-manager/` on every session and every
    render, installed by a tool outside this kit and recorded nowhere. A manifest
    that lists only the hooks we installed cannot answer "what runs on this
    machine without being asked?", which is the question a hook block is for.
    """
    path = Path.home() / ".claude" / "settings.json"
    if not path.exists():
        return previous
    settings = json.loads(path.read_text(encoding="utf-8"))
    was = {}
    for entries in previous.values():
        for h in (entries if isinstance(entries, list) else []):
            if isinstance(h, dict):
                was[h.get("command", "")] = h

    out: dict = {}
    for event, groups in settings.get("hooks", {}).items():
        rows = []
        for group in groups:
            for hook in group.get("hooks", []):
                cmd = redact_command(hook.get("command", ""))
                rows.append({
                    "command": cmd,
                    "scope": "user",
                    "why": was.get(cmd, {}).get("why", "TODO: say what this hook is for"),
                })
        if rows:
            out[event] = rows

    status = settings.get("statusLine")
    if isinstance(status, dict) and status.get("command"):
        cmd = redact_command(status["command"])
        out["statusLine"] = [{
            "command": cmd,
            "scope": "user",
            "why": was.get(cmd, {}).get("why", "TODO: say what this statusLine command is for"),
        }]

    return out or previous


def newest_content(skills: Path, kit: Path) -> float:
    """
    Timestamp of the most recently touched content file under the skills tree.

    The set comparison catches skills appearing, disappearing and being renamed.
    It does not catch a skill being *edited* — rewriting the body of a SKILL.md
    leaves the set identical, so the bundled copy and the zip silently go stale
    while the manifest insists everything is current. Editing is the commonest
    change of the three, so it needs its own signal.

    `bundled/` is excluded because it is this script's own output: including it
    would make every run dirty the instant the previous one finished.

    **Project skills are outside this scan on purpose.** `SKILLS` is one
    directory — the one the kit sits in — so a skill living in a repository is
    invisible here and to the Stop hook that calls `--if-changed`. That is
    correct rather than a gap: nothing in the kit re-syncs when one of them
    changes, because they are linked and not copied, and the repo's own history
    is what records the edit. What the kit does hold is the *record* of them, in
    `manifest.json` → `project_skills`, and that is hand-maintained — so
    creating or renaming one is a manifest edit somebody makes, not something a
    timestamp will ever notice. Noted 2026-09-06.
    """
    newest = 0.0
    skip = {"node_modules", "__pycache__", ".git", "fonts"}
    for path in skills.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".py", ".mjs", ".json", ".sh"}:
            continue
        # Everything this script writes must be excluded, or the run dirties its
        # own signal and the hook re-exports for ever: `bundled/` is its output
        # tree, and `manifest.json` is stamped on every write.
        if (kit / "bundled") in path.parents or path == kit / "manifest.json":
            continue
        if skip & set(path.parts):
            continue
        newest = max(newest, path.stat().st_mtime)
    return round(newest, 3)


# Optional. The kit ships no font files; set NJ_HOUSE_FONT_SOURCE to a folder you are licensed to use.
HOUSE_FONT_SOURCE = Path(os.environ["NJ_HOUSE_FONT_SOURCE"]) if os.environ.get("NJ_HOUSE_FONT_SOURCE") else None


def sync_house_fonts() -> list[str]:
    """
    Copy the house face from the folder named by NJ_HOUSE_FONT_SOURCE into `fonts/thmanyah/`.

    Optional: when the variable is unset or the folder is missing, nothing is copied and the
    kit copy (if any) is left untouched. Compared by sha256 so an updated cut replaces the
    kit copy on the next export. Only copy fonts you are licensed to redistribute.
    """
    import hashlib
    if HOUSE_FONT_SOURCE is None or not HOUSE_FONT_SOURCE.is_dir():
        return []
    dst = KIT / "fonts" / "thmanyah"
    dst.mkdir(parents=True, exist_ok=True)
    digest = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
    changed = []
    for src in sorted(HOUSE_FONT_SOURCE.iterdir()):
        if src.suffix.lower() not in {".otf", ".ttf", ".pdf"}:
            continue
        out = dst / src.name
        if not out.exists() or digest(out) != digest(src):
            shutil.copy2(src, out)
            changed.append(src.name)
    return changed


# Credential-shaped values: a memory note that quotes one is skipped, not shipped.
SECRET_RE = re.compile(
    r"(sk-or-v1-[A-Za-z0-9]{10,}|gsk_[A-Za-z0-9]{10,}|sk-ant-[A-Za-z0-9_-]{10,}"
    r"|Bearer\s+[A-Za-z0-9._-]{20,}|(?:password|passwd|api[_-]?key|secret|token)\s*[:=]\s*[^\s`'\"|]{8,})",
    re.I)


WITH_MEMORY = False          # --with-memory
WITH_PERSONAL = False        # --with-personal


def bundle_memory(bundled: Path) -> list[str]:
    """
    Copy every ~/.claude/projects/*/memory/ into bundled/memory/<project-dir>/.
    Added 2026-10-04: without the auto-memory a new machine or a reset ~/.claude
    has the skills but none of the decisions behind them. Files over 1 MB and any
    file holding a credential-shaped value are skipped and named.
    """
    root = Path.home() / ".claude" / "projects"
    dst_root = bundled / "memory"
    if dst_root.exists():
        shutil.rmtree(dst_root)
    if not WITH_MEMORY:
        return ["memory: NOT bundled (private by default; pass --with-memory for a private migration, never publish it)"]
    n = 0
    skipped: list[str] = []
    for mem in sorted(root.glob("*/memory")):
        for f in mem.rglob("*"):
            if not f.is_file():
                continue
            rel = f.relative_to(root)
            if f.stat().st_size > 1_000_000:
                skipped.append(f"{rel} (over 1 MB)")
                continue
            try:
                text = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                skipped.append(f"{rel} (binary)")
                continue
            if SECRET_RE.search(text):
                skipped.append(f"{rel} (credential-shaped value)")
                continue
            out = dst_root / rel.parts[0] / Path(*rel.parts[2:])
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(redact_text(text), encoding="utf-8")
            n += 1
    lines = [f"memory: {n} file(s) bundled from {len(list(root.glob('*/memory')))} project dir(s)"]
    lines += [f"  memory skipped: {s}" for s in skipped]
    return lines


def bundle_plugin(bundled: Path) -> list[str]:
    """
    Carry the nj-kit plugin (nj-method, nj-delegate, nj-agent-ops, nj-supervise,
    nj-writer ...). Source is <NJ_PLUGIN_ROOT>; when that folder is gone the
    installed cache copy (installed_plugins.json) is the only copy left.
    """
    src = Path(os.environ.get("NJ_PLUGIN_ROOT") or (Path.home() / "Desktop" / "nj-plugin"))
    origin = "<NJ_PLUGIN_ROOT>"
    if not (src / ".claude-plugin").exists():
        origin = "plugin cache"
        src = None
        try:
            inst = json.loads((Path.home() / ".claude/plugins/installed_plugins.json").read_text(encoding="utf-8"))
            src = Path(inst["plugins"]["nj-kit@nj-kit"][0]["installPath"])
        except Exception:
            pass
    if not src or not src.exists():
        return ["nj-plugin: NOT FOUND, not bundled"]
    dst = bundled / "nj-plugin"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
        "node_modules", "__pycache__", "*.pyc", ".git", "*.bak-*", "*.bak"))
    return [f"nj-plugin: bundled from {origin} ({src})"]


def bundle_v4(bundled: Path) -> list[str]:
    """NJ Governance v4 tooling: ~/.claude/agents/{sonnet-lead,haiku-helper}.md and hooks/nj_*.py (manifest governance_v4)."""
    home = Path.home() / ".claude"
    dst = bundled / "claude-v4"
    if not (home / "hooks").is_dir() and not (home / "agents").is_dir():
        return ["claude-v4: ~/.claude/{agents,hooks} not found, bundled copy kept as is"]
    if dst.exists():
        shutil.rmtree(dst)
    n = 0
    for sub, pat in (("agents", "*.md"), ("hooks", "nj_*.py")):
        for f in sorted((home / sub).glob(pat)):
            if sub == "agents" and f.stem not in ("sonnet-lead", "haiku-helper"):
                continue
            (dst / sub).mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst / sub / f.name)
            n += 1
    return [f"claude-v4: bundled {n} agent/hook file(s)"]


def write_zip(dest: Path) -> Path:
    """
    A single carryable file: the kit, its manifest, and the bundled skills.

    `shutil.make_archive` writes to a temporary name first and moves it into
    place, so a half-written zip is never left where somebody might copy it onto
    a USB stick and only discover the truncation on the other machine.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".building")
    made = shutil.make_archive(str(tmp), "zip", root_dir=KIT.parent, base_dir=KIT.name)
    shutil.move(made, dest)
    return dest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--zip", nargs="?", const="", metavar="PATH",
                    help="also write a portable nj-kit.zip (default: beside the Desktop shortcut)")
    ap.add_argument("--quiet", action="store_true", help="only print when something changed")
    ap.add_argument("--if-changed", dest="if_changed", action="store_true",
                    help="do nothing unless the skill set actually differs from the manifest")
    ap.add_argument("--with-memory", action="store_true",
                    help="also bundle auto-memory (private migration only; never publish the result)")
    ap.add_argument("--with-personal", action="store_true",
                    help="also bundle ~/.claude/CLAUDE.md as bundled/CLAUDE.personal.md (private migration only)")
    args = ap.parse_args()
    global WITH_MEMORY, WITH_PERSONAL
    WITH_MEMORY, WITH_PERSONAL = args.with_memory, args.with_personal

    manifest_path = KIT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    before = manifest.get("skills", {})
    before_env = (manifest.get("mcp_servers"), manifest.get("hooks"))
    manifest["skills"] = collect()
    manifest["mcp_servers"] = live_mcp_servers(manifest.get("mcp_servers", {}))
    manifest["hooks"] = live_hooks(manifest.get("hooks", {}))

    if args.dry_run:
        print(json.dumps(manifest["skills"], ensure_ascii=False, indent=2))
        return 0

    # Deciding "has anything changed?" belongs here, not in the caller's shell.
    # A `find -newer` catches additions and edits and is blind to *deletions* —
    # a removed skill leaves no file to be newer than anything, so the manifest
    # kept listing a skill that was gone and bundled/ kept a stale copy of it.
    # Comparing the collected sets catches all three.
    stamp = newest_content(SKILLS, KIT)
    unchanged = (
        before == manifest["skills"]
        and before_env == (manifest["mcp_servers"], manifest["hooks"])
        and manifest.get("synced_content_mtime") == stamp
        and manifest_path.exists()
    )
    if args.if_changed and unchanged:
        return 0
    manifest["synced_content_mtime"] = stamp

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Copy our own skills in, so the kit is self-contained for the parts no
    # registry can supply.
    bundled = KIT / "bundled"
    bundled.mkdir(exist_ok=True)

    # Drop bundles whose skill no longer exists. copytree only ever adds, so
    # without this a deleted skill lives on in the kit and gets reinstalled on
    # the next machine — the toolkit would quietly resurrect things you removed.
    current = {e["skill"] for e in manifest["skills"]["ours"]} | {"memory", "nj-plugin", "claude-v4"}
    for stale in [d for d in bundled.iterdir() if d.is_dir() and d.name not in current]:
        shutil.rmtree(stale)
        print(f"  pruned: {stale.name}")

    copied = []
    for entry in manifest["skills"]["ours"]:
        # Second guard, kept deliberately: a project skill must never end up in
        # bundled/ even if a future edit lets one through collect(). Linked,
        # never copied — see PROJECT_SKILLS and manifest `project_skills`.
        if entry["skill"] in PROJECT_SKILLS:
            continue
        src = SKILLS / entry["skill"]
        dst = bundled / entry["skill"]
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            # node_modules and font vaults are large and re-creatable; the kit
            # stays small enough to commit.
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
                "node_modules", "__pycache__", "*.pyc", "fonts", ".git",
                "*.bak-*", "*.bak"))
            copied.append(entry["skill"])

    # The standing instructions travel with the kit: skills without them
    # reproduce the files and not the behaviour.
    # Security fix 2026-10-27: the author's own CLAUDE.md is private. It is bundled only on request,
    # under a different name (bundled/CLAUDE.personal.md, gitignored), after redaction. The installer
    # ships templates/CLAUDE.neutral.md instead.
    claude_md = Path.home() / ".claude" / "CLAUDE.md"
    personal = bundled / "CLAUDE.personal.md"
    for stale in (bundled / "CLAUDE.md", personal):
        if stale.exists():
            stale.unlink()
    if WITH_PERSONAL and claude_md.exists():
        personal.write_text(redact_text(claude_md.read_text(encoding="utf-8")), encoding="utf-8")

    lines_extra = bundle_memory(bundled) + bundle_plugin(bundled) + bundle_v4(bundled)

    n3 = len(manifest["skills"]["third_party"])
    lines = [f"manifest.json: {n3} third-party skill(s) referenced, {len(copied)} bundled"]

    lines.extend(lines_extra)

    for name in sync_house_fonts():
        lines.append(f"  house font synced: {name}")

    if args.zip is not None:
        target = Path(args.zip) if args.zip else (Path.home() / "Desktop" / "nj-kit.zip")
        leaks = leak_scan(KIT)
        if leaks:
            print("REFUSING to write the zip: credential-shaped values in the kit:")
            for hit in leaks[:20]:
                print("  " + hit)
            return 2
        written = write_zip(target)
        lines.append(f"portable copy: {written}  ({written.stat().st_size // 1024} KB)")

    if not args.quiet:
        print(lines[0])
        for c in copied:
            print(f"  bundled: {c}")
    for extra in lines[1:]:
        print(extra)
    return 0


if __name__ == "__main__":
    sys.exit(main())
