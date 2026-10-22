#!/usr/bin/env python3
"""
Reproduce this toolkit on another machine or in another repo.

    python install.py                      # private: skills go to ~/.claude/skills
    python install.py --scope project      # this repo only, and gitignored
    python install.py --scope project --commit    # this repo, and shared with it
    python install.py --check              # report what is missing, change nothing
    python install.py --no-privacy         # skip the user-settings block

**User scope is the default, and that is a privacy decision, not a convenience
one.** Skills under `~/.claude/skills/` are files on one machine: they work in
every repo you open, they are never committed, and nobody sharing the Claude
account can read or edit them. Skills under a repo's `.claude/skills/` are part
of the repo — anyone with the repo gets them, which is right for a team
convention and wrong for a private toolkit. `--scope project` therefore adds the
directory to `.gitignore` unless you pass `--commit` to say you meant to share
it.

What the account can and cannot see is worth being exact about: a shared login
means shared *account* state — claude.ai skill sync, uploaded sessions,
artifacts. It does not mean a shared filesystem. This installer keeps the
toolkit on the filesystem and turns the account-level sharing off.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((KIT / "manifest.json").read_text(encoding="utf-8"))
USER_CLAUDE = Path.home() / ".claude"


def say(ok: bool | None, text: str) -> None:
    print(f"  {'✓' if ok else ('!' if ok is None else '✗')} {text}")


# ── tooling ──────────────────────────────────────────────────────────────────

def find_tool(cmd: str) -> str | None:
    """
    PATH first, then the places Windows installers actually put things.

    A shell started before an installer ran keeps the old PATH for its whole
    life, so `which` says "missing" for a tool that is installed and on the
    *persistent* PATH. Reporting that as missing sends someone off to reinstall
    something they already have; the honest answer is "installed, restart your
    shell".
    """
    hit = shutil.which(cmd)
    if hit:
        return hit
    home = Path.home()
    candidates = [
        home / "AppData/Local" / cmd.capitalize() / f"{cmd}.exe",
        home / "AppData/Local/Programs" / cmd / f"{cmd}.exe",
        Path(f"C:/Program Files/{cmd.capitalize()}/{cmd}.exe"),
    ]
    candidates += list((home / "AppData/Local/Microsoft/WinGet/Packages").glob(f"*/{cmd}.exe")) \
        if (home / "AppData/Local/Microsoft/WinGet/Packages").exists() else []
    for c in candidates:
        if c.exists():
            return str(c)
    return None


def check_tools() -> list[str]:
    missing = []
    print("\ntooling")
    for group, required in (("required", True), ("optional", False)):
        for tool in MANIFEST["tooling"].get(group, []):
            found = find_tool(tool["cmd"])
            on_path = bool(shutil.which(tool["cmd"]))
            if found and on_path:
                say(True, f"{tool['cmd']:<12} {tool['why']}")
            elif found:
                say(None, f"{tool['cmd']:<12} installed but not on this shell's PATH — restart the shell"
                          f"\n                 at: {found}")
            else:
                say(False if required else None,
                    f"{tool['cmd']:<12} MISSING — {tool['why']}"
                    + (f"\n                 install: {tool['install']}" if tool.get("install") else ""))
                if required:
                    missing.append(tool["cmd"])
    return missing


# ── skills ───────────────────────────────────────────────────────────────────

def _is_link(p: Path) -> bool:
    """True for a symlink or a Windows junction.

    Several of our skills are links into ~/.agents/skills so one copy serves
    every harness. shutil.rmtree refuses a link and copytree would replace the
    link with a frozen copy, so a linked skill is left exactly as it is.
    """
    if p.is_symlink():
        return True
    try:
        attrs = os.lstat(p).st_file_attributes
    except (AttributeError, OSError):
        return False
    return bool(attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def install_skills(target: Path, check_only: bool) -> None:
    target.mkdir(parents=True, exist_ok=True)
    ours = MANIFEST["skills"]["ours"]
    third = MANIFEST["skills"]["third_party"]

    print(f"\nour skills → {target}")
    for entry in ours:
        src = KIT / "bundled" / entry["skill"]
        dst = target / entry["skill"]
        if not src.exists():
            say(False, f"{entry['skill']} — not bundled; re-run export.py on the source machine")
            continue
        if check_only:
            say(dst.exists(), f"{entry['skill']} {'present' if dst.exists() else 'would be installed'}")
            continue
        if _is_link(dst):
            say(True, f"{entry['skill']} — linked, left as is")
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        say(True, entry["skill"])

    print(f"\nthird-party skills ({len(third)}) → {target}")
    if check_only:
        for entry in third:
            say((target / entry["skill"]).exists(), f"{entry['skill']:<30} {entry['source']}")
        link_project_skills(target, check_only)
        return

    if not shutil.which("npx"):
        say(False, "npx not found — cannot fetch third-party skills")
        link_project_skills(target, check_only)
        return

    user_scope = target == USER_CLAUDE / "skills"
    scope_flag = ["-g"] if user_scope else []
    # `-g` installs to ~/.claude/skills; without it the CLI installs into the
    # current directory's .claude/skills, so project scope runs from the repo.
    workdir = None if user_scope else str(target.parent.parent)

    # On Windows `npx` is `npx.cmd`, which CreateProcess cannot execute
    # directly — subprocess raises WinError 2 as if npx were not installed.
    # Going through cmd.exe is what makes it runnable; this is the same trap
    # that makes spawnSync('npx') fail silently in Node on this platform.
    launcher = ["cmd", "/c", "npx"] if os.name == "nt" else ["npx"]

    for entry in third:
        if (target / entry["skill"]).exists():
            say(True, f"{entry['skill']:<30} already present")
            continue
        run = subprocess.run(
            [*launcher, "-y", "skills", "add", entry["source"], "--skill", entry["skill"],
             "--agent", "claude-code", "-y", "--copy", *scope_flag],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=workdir,
        )
        ok = (target / entry["skill"]).exists() or "Done!" in (run.stdout or "")
        say(ok, f"{entry['skill']:<30} {entry['source']}"
                + ("" if ok else f"  — {(run.stderr or run.stdout or '').strip().splitlines()[-1][:70]}"
                   if (run.stderr or run.stdout) else ""))

    link_project_skills(target, check_only)


def _repo_path(entry: dict, target: Path) -> Path | None:
    """
    Where this project skill's real files are, if they are on this machine.

    Two places are tried, in order, and neither is a guess: the repository
    checked out under the root we are installing into — the normal case, and the
    reason `<root>/<repo>/<path>` is the shape — and the absolute `checkout`
    recorded in the manifest, which is where it sits on the machine the kit was
    exported from. If neither exists the skill is simply not here, which is a
    fact to report and not a failure to install.
    """
    block = MANIFEST.get("project_skills", {})
    root = target.parent.parent          # <root>/.claude/skills → <root>
    candidates = [root / entry["repo"] / entry["path"]]
    checkout = block.get("checkout")
    if checkout:
        candidates.append(Path(checkout) / entry["path"])
    for c in candidates:
        if c.exists():
            return c
    return None


def link_project_skills(target: Path, check_only: bool) -> None:
    """
    Link the skills that belong to a repository. Never copy one.

    A project skill is tracked by its repo and edited there. Copying it into
    `.claude/skills` produces a second original that drifts from the first the
    next time either is touched, and the drift is silent — the agent reads the
    copy while the reviewer reads the commit. So the installer creates a link,
    and if it cannot, it says so and leaves nothing behind.

    On Windows the link is a **directory junction made by PowerShell**, not
    `mklink`: under Git Bash, MSYS rewrites the arguments of `cmd //c mklink /J`
    before cmd sees them, and the command fails on paths that are perfectly
    valid. `New-Item -ItemType Junction` also needs no elevation, which a
    symbolic link on Windows does. Everywhere else, `os.symlink`.
    """
    block = MANIFEST.get("project_skills", {})
    entries = block.get("skills", [])
    if not entries:
        return

    print(f"\nproject skills ({len(entries)}) → {target}   [linked, never copied]")

    # User scope is the wrong home for these. A project skill describes one
    # portal, one pipeline, one document standard; linked into ~/.claude/skills
    # it would be active in every repo opened on this machine and would offer
    # project-tests' rules to a project that has none. The link belongs in the
    # directory you actually open — `--scope project` from there.
    if target == USER_CLAUDE / "skills":
        say(None, "user scope — not linked here on purpose: these describe one repo and"
                  "\n                 would be active in every one. Use --scope project"
                  " from the directory you open"
                  f"\n                 (here: {MANIFEST.get('project_skills', {}).get('link_into', '').split(' — ')[0]})")
        return

    for entry in entries:
        name = entry["skill"]
        dst = target / name
        src = _repo_path(entry, target)

        if dst.exists() or dst.is_symlink():
            say(True, f"{name:<30} already linked or present at {dst}")
            continue
        if src is None:
            say(None, f"{name:<30} {entry['repo']} is not on this machine — skipped."
                      f"\n                 clone it, then re-run; nothing is copied in its place")
            continue
        if check_only:
            say(None, f"{name:<30} would link → {src}")
            continue

        try:
            if os.name == "nt":
                # The paths are interpolated into the command STRING, quoted.
                # `powershell -Command <string> <more args>` does not bind those
                # extra arguments to `$args` — it appends them to the command
                # text — so a `$args[0]` form runs `New-Item -Path` with nothing
                # and fails on a valid path. Single quotes stop PowerShell
                # expanding anything inside; a literal quote is doubled.
                def ps(p: Path) -> str:
                    return "'" + str(p).replace("'", "''") + "'"
                subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                     f"New-Item -ItemType Junction -Path {ps(dst)} -Target {ps(src)} | Out-Null"],
                    check=True, capture_output=True, text=True,
                    encoding="utf-8", errors="replace")
            else:
                os.symlink(src, dst, target_is_directory=True)
        except Exception as exc:  # noqa: BLE001 — the reason is what matters here
            detail = (getattr(exc, "stderr", "") or str(exc)).strip()
            reason = detail.splitlines()[-1][:70] if detail else repr(exc)
            say(False, f"{name:<30} link failed — {reason}")
            continue
        say(dst.exists(), f"{name:<30} → {src}")


# ── settings ─────────────────────────────────────────────────────────────────

def apply_privacy(check_only: bool) -> None:
    path = USER_CLAUDE / "settings.json"
    wanted = MANIFEST["privacy"]["user_settings"]
    current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    print("\nprivacy (user scope — affects this machine only, never teammates)")
    drift = {k: v for k, v in wanted.items() if current.get(k) != v}
    if not drift:
        say(True, "all settings already as specified")
        return
    for k, v in drift.items():
        say(None if check_only else True, f"{k} = {json.dumps(v)}" + (" (would set)" if check_only else ""))
    if check_only:
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy(path, path.with_suffix(".json.bak-njkit"))
    current.update(wanted)
    path.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def apply_mcp(check_only: bool) -> None:
    path = Path.home() / ".claude.json"
    print("\nMCP servers (user scope)")
    if not path.exists():
        say(None, "~/.claude.json not found — start Claude Code once, then re-run")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    servers = data.setdefault("mcpServers", {})
    changed = False
    for name, spec in MANIFEST["mcp_servers"].items():
        spec = {k: v for k, v in spec.items() if k != "why"}
        if "args" in spec:
            spec["args"] = [a.replace("~", str(Path.home())) if a.startswith("~") else a for a in spec["args"]]
        if servers.get(name) == spec:
            say(True, f"{name} already configured")
            continue
        if check_only:
            say(None, f"{name} would be added")
            continue
        servers[name] = spec
        changed = True
        say(True, f"{name} added")
    if changed:
        shutil.copy(path, path.with_suffix(".json.bak-njkit"))
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _localise(cmd: str) -> str:
    """Hook commands store the home directory as '~'; expand it to this machine's home."""
    home = Path.home()
    return cmd.replace("~/", str(home).replace("\\", "/") + "/").replace("~\\", str(home) + "\\")


def _missing_paths(cmd: str) -> list[str]:
    """Script/program paths the command names that do not exist here (quoted, or ending .sh/.js/.cmd/.py/.exe)."""
    out = []
    for p in re.findall(r'"([^"]+\.(?:sh|js|cmd|py|exe|ps1))"', cmd):
        q = p.replace("\\\\", "\\")
        if q.startswith("/") and len(q) > 2 and q[2] == "/":  # /c/... → C:/...
            q = q[1].upper() + ":" + q[2:]
        if not Path(q).exists():
            out.append(p)
    return out


def apply_v4(check_only: bool) -> None:
    """NJ Governance v4: copy bundled agents + hook scripts into ~/.claude (backup when different, idempotent)
    and merge the two subagent env limits into settings.json. Runs before apply_hooks so the hook paths exist."""
    spec = MANIFEST.get("governance_v4")
    src = KIT / "bundled" / "claude-v4"
    print("\nNJ Governance v4 (agents, hook scripts, env)")
    if not spec:
        return
    if not src.exists():
        say(None, "claude-v4 not bundled — re-run export.py on the source machine")
    else:
        for f in sorted(p for p in src.rglob("*") if p.is_file()):
            dst = USER_CLAUDE / f.relative_to(src)
            if dst.exists() and dst.read_bytes() == f.read_bytes():
                say(True, f"{dst.name}: already identical")
                continue
            if not check_only:
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.exists():
                    shutil.copy(dst, dst.with_name(dst.name + ".bak-njkit"))
                shutil.copy2(f, dst)
            say(None if check_only else True, f"{dst.name}: {'would copy' if check_only else 'copied'}")
    path = USER_CLAUDE / "settings.json"
    current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    env = current.setdefault("env", {})
    todo = {e["name"]: e["value"] for e in spec.get("env", []) if env.get(e["name"]) != e["value"]}
    if not todo:
        say(True, "env limits already set")
        return
    if not check_only:
        env.update(todo)
        if path.exists():
            shutil.copy(path, path.with_suffix(".json.bak-njkit"))
        path.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    say(None if check_only else True, f"env {'would set' if check_only else 'set'}: {', '.join(todo)}")


def apply_hooks(check_only: bool) -> None:
    """Install the manifest's hooks into user settings.json (the owner 2026-10-10: install them, with backup).
    A hook whose script/program is not on this machine is skipped and named; one already present is left alone."""
    path = USER_CLAUDE / "settings.json"
    current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    print("\nhooks (user scope)")
    hooks = current.setdefault("hooks", {})
    changed = False
    for event, items in MANIFEST.get("hooks", {}).items():
        for item in items:
            cmd = _localise(item["command"])
            missing = _missing_paths(cmd)
            if missing:
                say(None, f"{event}: skipped — not on this machine: {', '.join(missing)}")
                continue
            if event == "statusLine":
                if current.get("statusLine"):
                    say(True, "statusLine already set (left as is)")
                    continue
                if not check_only:
                    current["statusLine"] = {"type": "command", "command": cmd}
                    changed = True
                say(None if check_only else True, f"statusLine {'would be set' if check_only else 'set'}")
                continue
            groups = hooks.setdefault(event, [])
            if any(h.get("command") == cmd for g in groups for h in g.get("hooks", [])):
                say(True, f"{event}: already installed")
                continue
            if not check_only:
                groups.append({"hooks": [{"type": "command", "command": cmd}]})
                changed = True
            say(None if check_only else True, f"{event}: {'would add' if check_only else 'added'} — {item.get('why', '')[:70]}")
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            shutil.copy(path, path.with_suffix(".json.bak-njkit"))
        path.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def provision_pdf_typography(target: Path, check_only: bool) -> None:
    """
    Refill the two things the bundle deliberately leaves out.

    `export.py` excludes the font vault (~20 MB) and `node_modules`, which keeps
    the kit small enough to carry — but it means the skill arrives unable to
    render anything: no Cairo to embed, no playwright to print with. Documenting
    that in prose and trusting someone to read it is how a transfer "succeeds"
    and the PDF pipeline is discovered broken later, on a deadline.

    Both are re-creatable from the network, so they are re-created here.
    """
    skill = target / "pdf-typography"
    if not skill.exists():
        return
    print("\npdf-typography (fonts and renderer are not bundled — refilling)")

    fonts = skill / "fonts"
    faces = len(list(fonts.glob("*/*.ttf"))) if fonts.exists() else 0
    have_pw = (skill / "node_modules" / "playwright").exists()

    if check_only:
        say(bool(faces), f"font vault: {faces} face(s)" + ("" if faces else " — would fetch Cairo"))
        say(have_pw, "playwright" + ("" if have_pw else " — would install into the skill"))
        return

    house = MANIFEST.get("house_style", {}).get("font", "Cairo")
    if not faces:
        run = subprocess.run(["node", str(skill / "scripts" / "fetch-fonts.mjs"), house],
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
        got = len(list(fonts.glob("*/*.ttf"))) if fonts.exists() else 0
        say(bool(got), f"font vault: {got} face(s) of {house}"
                       + ("" if got else f" — {(run.stderr or '').strip()[:60]}"))
    else:
        say(True, f"font vault: {faces} face(s) already present")

    if not have_pw:
        launcher = ["cmd", "/c", "npm"] if os.name == "nt" else ["npm"]
        subprocess.run([*launcher, "install", "playwright", "--no-save", "--silent"],
                       cwd=str(skill), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
        say((skill / "node_modules" / "playwright").exists(),
            "playwright installed into the skill, so it runs from any directory")
    else:
        say(True, "playwright already present")


def install_house_fonts(check_only: bool) -> None:
    """
    Install the house face (Thmanyah) for this user, so every project and every
    renderer finds it by family name. Files come from the kit's fonts/thmanyah/;
    a face already installed with the same size is left alone.
    Optional: the kit ships no font files. Point NJ_HOUSE_FONT_DIR at a folder you are
    licensed to use; without it this step is skipped. Installing it is never required.
    """
    src = Path(os.environ["NJ_HOUSE_FONT_DIR"]) if os.environ.get("NJ_HOUSE_FONT_DIR") else KIT / "fonts" / "thmanyah"
    faces = sorted(src.glob("*.otf")) + sorted(src.glob("*.ttf")) if src.exists() else []
    print(f"\nhouse font ({len(faces)} face(s) in the kit)")
    if not faces:
        say(None, "no house font files (optional, skipped); set NJ_HOUSE_FONT_DIR to install your own")
        return
    if os.name == "nt":
        dest = Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Windows" / "Fonts"
    elif sys.platform == "darwin":
        dest = Path.home() / "Library" / "Fonts"
    else:
        dest = Path.home() / ".local" / "share" / "fonts"
    todo = [f for f in faces if not (dest / f.name).exists() or (dest / f.name).stat().st_size != f.stat().st_size]
    if check_only:
        say(not todo, f"{len(faces) - len(todo)}/{len(faces)} installed" + (f" — would install {len(todo)}" if todo else ""))
        return
    dest.mkdir(parents=True, exist_ok=True)
    for f in todo:
        shutil.copy2(f, dest / f.name)
        if os.name == "nt":
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows NT\CurrentVersion\Fonts", 0,
                                winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, f"{f.stem} (OpenType)", 0, winreg.REG_SZ, str(dest / f.name))
    if todo and sys.platform.startswith("linux"):
        subprocess.run(["fc-cache", "-f"], capture_output=True)
    say(True, f"{len(faces)} face(s) installed" + (f" ({len(todo)} new or updated)" if todo else ", all current"))


def audit_installed(target: Path, check_only: bool) -> None:
    """
    Audit what was just fetched, before anyone relies on it.

    `install.py` pulls 17 skills from 13 different authors and they run with full
    agent permissions. Fetching them without looking is the whole risk; doing it
    on a *fresh machine*, where nobody has ever read them, is that risk at its
    worst. The audit is advisory — it prints and never blocks, because a gate
    that fires on a legitimate `rmtree` teaches people to pass `--force`.
    """
    audit = target / "nj-security-review" / "scripts" / "audit.py"
    if check_only or not audit.exists():
        return
    print("\nsecurity audit of the installed skills")
    run = subprocess.run([sys.executable, str(audit), "--changed"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    body = (run.stdout or "").strip()
    for line in body.splitlines()[-14:]:
        print(f"  {line}")
    print("  findings are evidence, not verdicts — read them, then accept with:")
    print(f"    python {audit} --baseline")


def apply_standing_instructions(check_only: bool) -> None:
    """
    Install `~/.claude/CLAUDE.md`, the file that makes nj-method the default.

    Without it a new machine has the skills but not the instruction to reach for
    them, which is most of the value gone: the roster reproduces the files and
    the standing instructions reproduce the behaviour.

    An existing CLAUDE.md is never overwritten — it may hold the user's own
    notes. It is left alone and reported, so the choice to merge stays theirs.
    """
    spec = MANIFEST.get("standing_instructions")
    if not spec:
        return
    src = KIT / "bundled" / "CLAUDE.md"
    dst = Path.home() / ".claude" / "CLAUDE.md"
    print("\nstanding instructions")
    if not src.exists():
        say(None, "CLAUDE.md not bundled — re-run export.py on the source machine")
        return
    if dst.exists():
        same = dst.read_text(encoding="utf-8") == src.read_text(encoding="utf-8")
        say(True if same else None,
            "already present and identical" if same
            else f"{dst} exists and differs — left alone; merge by hand if you want the kit's version")
        return
    if check_only:
        say(None, f"would write {dst}")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, dst)
    say(True, f"wrote {dst} — nj-method is now the default here")


def tracks_project_skills(repo: Path) -> bool:
    """
    Does this repository already track `.claude/skills`?

    If it does, the kit must not ignore that directory. The ignore line exists to
    keep a *private* toolkit out of somebody's commit; a repo that tracks its own
    `.claude/skills` has made the opposite decision on purpose — project-tests
    carries project-e2e, project-manuals and project-srs because the tests depend on
    them. Adding the line there does not untrack anything, which is what makes it
    dangerous: git keeps the existing files and silently stops offering the next
    edit, so a skill change goes uncommitted and nobody is told.

    A non-repo, or no git, answers "no" and the normal behaviour applies.
    """
    if not shutil.which("git"):
        return False
    try:
        run = subprocess.run(["git", "-C", str(repo), "ls-files", "--", ".claude/skills"],
                             capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=20)
    except Exception:  # noqa: BLE001 — no git, no repo, no answer; fall through
        return False
    return run.returncode == 0 and bool((run.stdout or "").strip())


def gitignore(target: Path, commit: bool) -> None:
    if commit:
        print("\ngit: --commit given, the skills directory stays tracked")
        return
    repo = target.parent.parent
    gi = repo / ".gitignore"
    existing = gi.read_text(encoding="utf-8") if gi.exists() else ""

    # skills-lock.json is written at the repo root by the skills CLI. It carries
    # no secrets, but it names every skill installed — so committing it while
    # the skills themselves are ignored publishes the inventory and defeats the
    # point of keeping the toolkit private.
    wanted = [".claude/skills/", "skills-lock.json"]
    if tracks_project_skills(repo):
        wanted.remove(".claude/skills/")
        say(None, "this repo already tracks .claude/skills — NOT ignoring it"
                  " (see manifest project_skills.git); only skills-lock.json is added")
    add = [line for line in wanted if line not in existing]
    if not add:
        say(True, ".gitignore already excludes the toolkit and its lockfile")
        return

    with gi.open("a", encoding="utf-8") as fh:
        fh.write(("" if existing.endswith("\n") or not existing else "\n")
                 + "\n# private toolkit — see .claude/skills/nj-kit\n"
                 + "".join(f"{line}\n" for line in add))
    say(True, f".gitignore: added {', '.join(add)} (pass --commit to share instead)")


def apply_description_overrides(skills_dir: Path, check_only: bool) -> None:
    """
    Re-apply the trimmed third-party descriptions, because upstream carries the
    long ones.

    The 2026-09-18 audit cut 5,463 words of skill description to ~1,675 — the
    only token cost paid in *every* session, before any work happens. For our
    own skills the trim lives in the file. For a third-party skill it cannot:
    this installer fetches it from its upstream repo, which still describes
    itself in 152 words, so a fresh install would silently revert the saving.
    `description-overrides.json` holds the trimmed text and
    `scripts/apply-descriptions.py` re-applies it, idempotently.

    Deliberately non-fatal. A description that is 40 words longer than intended
    is a token cost, not a broken install, so a missing overrides file, an
    unparseable SKILL.md or a crash in the applier is reported and stepped over
    rather than failing the install of the skills themselves.
    """
    applier = KIT / "scripts" / "apply-descriptions.py"
    print("\ndescriptions (trimmed to <=40 words; upstream carries the long ones)")
    if not applier.exists() or not (KIT / "description-overrides.json").exists():
        say(None, "description-overrides.json or apply-descriptions.py missing — skipped")
        return
    cmd = [sys.executable, str(applier), "--skills", str(skills_dir)]
    if check_only:
        cmd.append("--check")
    env = dict(os.environ, PYTHONUTF8="1")
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=120, env=env)
    except Exception as exc:  # noqa: BLE001 — never fail the install over a description
        say(None, f"apply-descriptions.py did not run ({exc}) — descriptions left as fetched")
        return
    tail = [l for l in (run.stdout or "").splitlines() if l.strip()][-2:]
    for line in tail:
        print(f"  {line.strip()}")
    say(True if run.returncode == 0 else None,
        "descriptions match the overrides" if run.returncode == 0
        else "some descriptions differ from the overrides — run"
             " scripts/apply-descriptions.py (non-fatal)")


def restore_memory(check_only: bool) -> None:
    """Restore bundled/memory/<project-dir>/* into ~/.claude/projects/<project-dir>/memory/, never over a newer file."""
    src_root = KIT / "bundled" / "memory"
    print("\nauto-memory")
    if not src_root.exists():
        say(None, "no bundled memory (re-run export.py on the source machine)")
        return
    dst_root = USER_CLAUDE / "projects"
    restored = kept = 0
    for f in sorted(p for p in src_root.rglob("*") if p.is_file()):
        rel = f.relative_to(src_root)
        out = dst_root / rel.parts[0] / "memory" / Path(*rel.parts[1:])
        if out.exists() and out.stat().st_mtime >= f.stat().st_mtime:
            kept += 1
            continue
        restored += 1
        if check_only:
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, out)
    say(True, f"{'would restore' if check_only else 'restored'} {restored} memory file(s); {kept} already present and as new or newer")


def restore_plugin(check_only: bool) -> None:
    """Put the nj-kit plugin back at <NJ_PLUGIN_ROOT> (its marketplace path) when it is missing."""
    src = KIT.parent / "nj-plugin"  # the repo's own plugin tree (no second copy under bundled/)
    dst = Path(os.environ.get("NJ_PLUGIN_ROOT") or (Path.home() / "Desktop" / "nj-plugin"))
    print("\nnj-kit plugin (nj-method, nj-delegate, nj-agent-ops, nj-supervise, nj-writer)")
    if not src.exists():
        say(None, "no plugin tree next to nj-kit/ (run install.py from a clone of the repo)")
        return
    if dst.exists():
        say(True, f"{dst} already present, left alone")
        return
    if check_only:
        say(None, f"would copy plugin to {dst}")
        return
    shutil.copytree(src, dst)
    say(True, f"copied to {dst}. Now run: claude plugin marketplace add \"{dst}\" ; claude plugin install nj-kit@nj-kit")


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scope", choices=["user", "project"], default="user")
    ap.add_argument("--commit", action="store_true", help="with --scope project: do not gitignore")
    ap.add_argument("--check", action="store_true", help="report only, change nothing")
    ap.add_argument("--no-privacy", action="store_true")
    ap.add_argument("--target", type=Path, help="repo root for --scope project (default: cwd)")
    args = ap.parse_args()

    print(f"nj-kit · manifest {MANIFEST['updated']} · {'CHECK ONLY' if args.check else 'installing'}")
    print(f"house style: {MANIFEST['house_style']['font']}, "
          f"extract with {MANIFEST['house_style']['pdf_extractor'].split(' —')[0]}")

    missing = check_tools()

    target = (USER_CLAUDE / "skills") if args.scope == "user" else \
             ((args.target or Path.cwd()) / ".claude" / "skills")
    install_skills(target, args.check)

    apply_description_overrides(target, args.check)

    if args.scope == "project" and not args.check:
        gitignore(target, args.commit)

    provision_pdf_typography(target, args.check)

    install_house_fonts(args.check)

    audit_installed(target, args.check)

    apply_standing_instructions(args.check)
    restore_memory(args.check)
    restore_plugin(args.check)

    if not args.no_privacy:
        apply_privacy(args.check)
    apply_mcp(args.check)
    apply_v4(args.check)
    apply_hooks(args.check)

    print("\n" + "-" * 62)
    if missing:
        print(f"! install these before relying on the toolkit: {', '.join(missing)}")
    if args.scope == "user":
        print("Skills are at ~/.claude/skills — private to this machine, active in every repo.")
    else:
        print(f"Skills are at {target}"
              + ("" if args.commit else " and gitignored, so they stay yours."))
    print("Set PYTHONUTF8=1 on Windows, or Arabic will crash several scripts.")
    print("Restart Claude Code so the MCP servers and settings load.")
    return 1 if missing and not args.check else 0


if __name__ == "__main__":
    sys.exit(main())
