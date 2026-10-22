#!/usr/bin/env python3
"""
Audit skills (or any directory of instructions and scripts) for content that
would make an agent act against the person running it.

    python audit.py                     # every installed skill
    python audit.py <dir> [<dir>...]    # specific ones
    python audit.py --baseline          # record hashes as reviewed-and-accepted
    python audit.py --changed           # only what differs from the baseline
    python audit.py --json

Why this is not the built-in `/security-review`: that one reads a diff of *your*
code. This reads *other people's instructions that your agent will follow*. 17
of the installed skills come from 13 different authors and run with full agent
permissions; an update to any of them arrives silently. Those are different
threats and neither substitutes for the other.

Findings are evidence, not verdicts. Every category here has legitimate uses —
a proofreading skill mentions "bypass", a TTS skill reads an API key — so the
output is designed to be read, and the script never exits non-zero on findings
alone. A scanner that cries wolf gets switched off, and then nothing is audited.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SKILLS = Path.home() / ".claude" / "skills"
BASELINE = Path.home() / ".claude" / ".specs" / "skill-audit-baseline.json"

TEXT_SUFFIXES = {".md", ".py", ".js", ".mjs", ".ts", ".sh", ".ps1", ".json", ".txt", ".yaml", ".yml"}

# Ordered by how bad it is if genuine.
CHECKS: list[tuple[str, str, str]] = [
    ("prompt-injection", "critical",
     r"ignore\s+(all\s+|any\s+)?(previous|prior|earlier|above)\s+(instruction|prompt|direction)"
     r"|disregard\s+(previous|prior|the\s+user|user'?s)"
     r"|override\s+(the\s+)?user"
     r"|takes?\s+precedence\s+over\s+(the\s+)?user"),
    ("concealment", "critical",
     r"do\s+not\s+(tell|inform|mention\s+to|reveal\s+to|show)\s+the\s+user"
     r"|without\s+(telling|informing|notifying)\s+the\s+user"
     r"|do\s+not\s+mention\s+(this|that\s+you)"
     r"|hide\s+(this|it)\s+from"
     r"|silently\s+(run|execute|install|send|upload)"),
    ("authority-claim", "high",
     r"even\s+if\s+the\s+user\s+(says|asks|declines|refuses)"
     r"|regardless\s+of\s+(what\s+)?the\s+user"
     r"|no\s+matter\s+what\s+the\s+user"
     r"|do\s+not\s+ask\s+(the\s+user\s+)?(for|before)\s+permission"),
    ("permission-bypass", "high",
     r"--dangerously[\w-]*|dangerously-skip|disableBypassPermissions"
     r"|skip[\s-]{0,3}permission|--no-sandbox|allowedTools\s*[:=]\s*\[?\s*['\"]?\*"),
    ("self-installing", "high",
     r"settings\.json|\.claude/hooks|PostToolUse|PreToolUse|UserPromptSubmit"
     r"|crontab|schtasks|/etc/cron|Register-ScheduledTask"),
    ("remote-execution", "critical",
     r"curl\s+[^|\n]*\|\s*(ba)?sh|wget\s+[^|\n]*\|\s*(ba)?sh"
     r"|iex\s*\(|Invoke-Expression|eval\s*\(\s*(atob|Buffer|fetch|require)"),
    ("credential-access", "medium",
     r"\.ssh/|id_rsa|\.aws/credentials|\.npmrc|\.netrc|\.git-credentials"
     r"|ANTHROPIC_API_KEY|OPENAI_API_KEY|\.credentials\.json|keychain|DPAPI"),
    ("destructive", "high",
     r"rm\s+-rf\s+[/~$]|shutil\.rmtree\s*\(|Remove-Item\s+.*-Recurse.*-Force"
     r"|DROP\s+TABLE|git\s+push\s+--force|git\s+reset\s+--hard"),
    ("exfiltration-shape", "medium",
     r"requests\.(post|put)\s*\(|fetch\s*\([^)]*method\s*:\s*['\"]POST"
     r"|urllib\.request\.urlopen\s*\([^)]*data|axios\.post"),
    ("obfuscation", "high",
     r"[A-Za-z0-9+/]{240,}={0,2}|base64\.b64decode\s*\(|atob\s*\(|fromCharCode\s*\("),
]

URL_RE = re.compile(r"https?://([a-zA-Z0-9.-]+)")
# Hosts that are documentation, schemas or package registries — noise, not signal.
BENIGN_HOSTS = re.compile(
    r"^(www\.)?(github\.com|raw\.githubusercontent\.com|json-schema\.org|w3\.org|"
    r"npmjs\.com|registry\.npmjs\.org|pypi\.org|python\.org|developer\.mozilla\.org|"
    r"docs\.\w+|example\.(com|org)|localhost|127\.0\.0\.1|fonts\.(googleapis|gstatic)\.com|"
    r"schema\.org|opensource\.org|creativecommons\.org|unicode\.org)$")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(p for p in path.rglob("*") if p.is_file() and p.suffix in TEXT_SUFFIXES):
        h.update(f.relative_to(path).as_posix().encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


# This scanner's own catalogue quotes every pattern it hunts for, so scanning it
# reports "ignore previous instructions" and "do not tell the user" as critical
# findings against the file whose job is to describe them. Any file inside this
# skill — including copies bundled elsewhere — is therefore skipped. The cost is
# that this scanner cannot audit itself; the alternative is eight false criticals
# that train the reader to skim past the real ones.
SELF = "nj-security-review"


def audit(skill: Path) -> dict:
    findings, hosts = [], set()
    for f in skill.rglob("*"):
        if not f.is_file() or f.suffix not in TEXT_SUFFIXES:
            continue
        if any(part in {"node_modules", "__pycache__", ".git"} for part in f.parts):
            continue
        if SELF in f.parts:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name, severity, pattern in CHECKS:
            for m in re.finditer(pattern, text, re.I):
                line = text[: m.start()].count("\n") + 1
                excerpt = text.splitlines()[line - 1].strip()[:110] if line - 1 < len(text.splitlines()) else ""

                # A good skill states these patterns in order to forbid them.
                # Measured examples: "Do not run a grid without telling the user
                # the cost first" and "never as instructions that override the
                # user" — both protective, both matched as critical. Reporting
                # protective language at the same weight as an attack teaches the
                # reader to skim, and then the real one is skimmed too. The
                # finding is kept and demoted, never dropped: negation is a hint,
                # and an attacker who writes "do not tell the user" inside a
                # sentence that looks like a guardrail is exactly the case where
                # silent suppression would be worst.
                # 140 chars, bounded to the same sentence by the [^.]*$ anchor below.
                # "Do not run a 5x5 grid, or grids for several keywords, without
                # telling the user the cost first" puts the negation 54 characters
                # ahead of the match; a short window misses the very cases that
                # matter most, which are long protective sentences.
                before = text[max(0, m.start() - 140):m.start()].lower()
                negated = bool(re.search(r"\b(do not|don'?t|never|avoid|refuse to|must not|no skill should)\b[^.]*$", before))
                findings.append({
                    "check": name,
                    "severity": "note" if negated else severity,
                    "negated": negated,
                    "file": f.relative_to(skill).as_posix(), "line": line,
                    "match": m.group(0)[:60], "excerpt": excerpt,
                })
        for host in URL_RE.findall(text):
            if not BENIGN_HOSTS.match(host):
                hosts.add(host)

    return {
        "skill": skill.name,
        "digest": digest(skill),
        "files": sum(1 for p in skill.rglob("*") if p.is_file()),
        "findings": findings,
        "external_hosts": sorted(hosts),
    }


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        if hasattr(s, "reconfigure"):
            s.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="*", type=Path)
    ap.add_argument("--baseline", action="store_true", help="record current digests as reviewed")
    ap.add_argument("--changed", action="store_true", help="only skills differing from the baseline")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    targets = args.dirs or sorted(d for d in SKILLS.iterdir() if d.is_dir() and (d / "SKILL.md").exists())
    base = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else {}

    reports = [audit(t) for t in targets]
    if args.changed:
        reports = [r for r in reports if base.get(r["skill"]) != r["digest"]]

    if args.baseline:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps({r["skill"]: r["digest"] for r in reports}, indent=2), encoding="utf-8")
        print(f"baseline recorded for {len(reports)} skill(s) → {BASELINE}")
        return 0

    if args.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
        return 0

    flagged = [r for r in reports if r["findings"]]
    print(f"audited {len(reports)} skill(s)"
          + (f", {len(reports)} changed since baseline" if args.changed else ""))

    for r in reports:
        new = base and base.get(r["skill"]) != r["digest"]
        mark = "CHANGED" if new and r["skill"] in base else ("NEW" if base and r["skill"] not in base else "")
        if not r["findings"] and not r["external_hosts"]:
            continue
        print(f"\n  {r['skill']}  ({r['files']} files) {mark}")
        by_check: dict[str, list] = {}
        for f in r["findings"]:
            by_check.setdefault(f"{f['severity']}/{f['check']}", []).append(f)
        order = ["critical", "high", "medium", "note"]
        for key in sorted(by_check, key=lambda k: order.index(k.split("/")[0])):
            items = by_check[key]
            print(f"    {key} ({len(items)})")
            for f in items[:3]:
                print(f"      {f['file']}:{f['line']}  «{f['match']}»")
                if f["excerpt"]:
                    print(f"         {f['excerpt']}")
            if len(items) > 3:
                print(f"      … {len(items) - 3} more")
        if r["external_hosts"]:
            print(f"    hosts contacted or referenced: {', '.join(r['external_hosts'][:8])}")

    print(f"\n{sum(len(r['findings']) for r in reports)} finding(s) across {len(flagged)} skill(s).")
    print("Findings are evidence, not verdicts — read the excerpt before acting.")
    print("Accept the current state with --baseline, then use --changed to review only updates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
