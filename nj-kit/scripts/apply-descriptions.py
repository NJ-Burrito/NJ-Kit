#!/usr/bin/env python3
"""
Re-apply the trimmed third-party skill descriptions after an install.

    python apply-descriptions.py                  # rewrite ~/.claude/skills/<skill>/SKILL.md
    python apply-descriptions.py --check          # report drift, change nothing
    python apply-descriptions.py --skills <dir>   # a project-scope .claude/skills

**Descriptions are the only always-on token cost.** Every installed skill's
`description:` is loaded into every session before any work happens, so a
third-party skill that describes itself in 152 words is charging rent whether it
is ever invoked or not. `description-overrides.json` holds the trimmed text for
the 23 third-party skills the audit named, at 40 words or fewer each, keeping
every distinctive trigger phrase.

The reason this is a script and not 23 hand edits: `install.py` fetches those
skills from their upstream repos, which carry the long originals. A hand edit is
correct on this machine and gone on the next one, which defeats the point of the
kit — that a new machine produces the same output. So the trim is data, applied.

Two rules keep it safe to run against somebody else's skill:

- **Only the `description:` field is touched.** The body belongs upstream; an
  edit there would fork the skill and lose the next upstream fix. Every other
  frontmatter key, and every byte after the closing `---`, is preserved exactly.
- **A skill that is not installed is reported, not created.** The override is a
  trim of something that exists; writing a SKILL.md for an absent skill would
  invent a skill with no body.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
OVERRIDES = KIT / "description-overrides.json"
USER_SKILLS = Path.home() / ".claude" / "skills"

BLOCK_MARKERS = (">", "|", ">-", "|-", ">+", "|+")


def say(ok: bool | None, text: str) -> None:
    print(f"  {'✓' if ok else ('!' if ok is None else '✗')} {text}")


def split_front(text: str) -> tuple[list[str], str] | None:
    """
    The frontmatter lines and everything after them, or None if there is none.

    The split is on the *second* `---`, and the tail keeps its own newlines
    untouched — the body is never rewritten, only carried across.
    """
    if not text.startswith("---"):
        return None
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines[1:], start=1):
        if line.rstrip("\r\n") == "---":
            return lines[1:i], "".join(lines[i:])
    return None


def find_description(front: list[str]) -> tuple[int, int, str] | None:
    """
    Where the description lives, and what it currently says.

    Returns (first line index, one past the last, the joined text). A YAML block
    scalar (`description: >`) puts its text on the following indented lines, so
    the field is a *range* of lines, not one line — replacing only the key's own
    line would leave the old prose behind as a stray indented block.
    """
    for i, line in enumerate(front):
        if not line.startswith("description:"):
            continue
        value = line.split(":", 1)[1].strip()
        if value not in BLOCK_MARKERS:
            return i, i + 1, dequote(value)
        block: list[str] = []
        end = i + 1
        for j in range(i + 1, len(front)):
            follow = front[j]
            if follow.strip() and not follow.startswith((" ", "\t")):
                break
            block.append(follow.strip())
            end = j + 1
        return i, end, " ".join(b for b in block if b)
    return None


def dequote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        inner = value[1:-1]
        return inner.replace('\\"', '"') if value[0] == '"' else inner.replace("''", "'")
    return value


def yaml_line(text: str) -> str:
    """
    One double-quoted YAML scalar. Quoted always, so a description that starts
    with a character YAML reads as syntax — `>`, `*`, `#`, `[` — or contains a
    colon cannot silently change the file's meaning.
    """
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'description: "{escaped}"\n'


def apply(skills: Path, check_only: bool) -> int:
    data = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    entries = {k: v for k, v in data.items() if not k.startswith("_")}

    print(f"description overrides · {len(entries)} third-party skills → {skills}")
    print(f"{'CHECK ONLY — nothing is written' if check_only else 'applying'}\n")

    drift = missing = applied = 0
    for name in sorted(entries):
        wanted = entries[name]["description"]
        md = skills / name / "SKILL.md"

        if not md.is_file():
            say(None, f"{name:<28} not installed — skipped (re-run install.py to fetch it)")
            missing += 1
            continue

        text = md.read_text(encoding="utf-8")
        parts = split_front(text)
        if parts is None:
            say(False, f"{name:<28} no YAML frontmatter — left alone")
            drift += 1
            continue
        front, body = parts
        found = find_description(front)
        if found is None:
            say(False, f"{name:<28} no description: field — left alone")
            drift += 1
            continue
        start, end, current = found

        if current == wanted:
            say(True, f"{name:<28} already trimmed ({len(wanted.split())} words)")
            continue

        now, was = len(wanted.split()), len(current.split())
        if check_only:
            say(None, f"{name:<28} DRIFT — installed {was} words, override {now}")
            drift += 1
            continue

        front[start:end] = [yaml_line(wanted)]
        md.write_text("---\n" + "".join(front) + body, encoding="utf-8")
        say(True, f"{name:<28} {was} → {now} words")
        applied += 1

    print("\n" + "-" * 62)
    if check_only:
        print(f"{len(entries) - missing - drift} of {len(entries)} match the overrides; "
              f"{drift} drifted, {missing} not installed.")
        if drift:
            print("Run without --check to re-apply.")
    else:
        print(f"{applied} rewritten, {len(entries) - missing - applied} already correct, "
              f"{missing} not installed.")
    print("Only the description: field is touched — bodies belong upstream.")
    return 1 if (check_only and drift) else 0


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report drift, change nothing")
    ap.add_argument("--skills", type=Path, default=USER_SKILLS,
                    help="skills directory (default: ~/.claude/skills)")
    args = ap.parse_args()

    if not OVERRIDES.exists():
        say(False, f"{OVERRIDES} not found — nothing to apply")
        return 1
    return apply(args.skills, args.check)


if __name__ == "__main__":
    sys.exit(main())
