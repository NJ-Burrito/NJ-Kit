#!/usr/bin/env python3
"""Rebuild the README's plugin skill table from each SKILL.md description, so it cannot drift.

    python scripts/skill-table.py           # rewrite the block between the markers in README.md
    python scripts/skill-table.py --check   # PASS if the README is current, FAIL otherwise (CI)

The skill list comes from .claude-plugin/marketplace.json; each row is the first sentence of
that skill's frontmatter `description`.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
START, END = "<!-- skills:start -->", "<!-- skills:end -->"


def description(skill_md: Path) -> str:
    m = re.search(r"^---\s*$(.*?)^---\s*$", skill_md.read_text(encoding="utf-8"), re.S | re.M)
    d = re.search(r"^description:\s*(.+?)(?=^\w[\w-]*:|\Z)", m.group(1), re.S | re.M).group(1).strip()
    if d[:1] in "'\"":
        q = d[0]
        d = d[1:d.rindex(q)].replace(q * 2, q)
    d = " ".join(d.split())
    first = re.split(r"(?<=[.!?])\s+(?=[A-Z])", d)[0]
    return first.rstrip(".").replace("|", "\\|")


def table() -> str:
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    plugin = market["plugins"][0]
    base = ROOT / plugin["source"]
    rows = [f"| [{Path(s).name}](nj-plugin/skills/{Path(s).name}) | {description(base / s / 'SKILL.md')} |"
            for s in sorted(plugin["skills"])]
    return "\n".join([START, "", "| Skill | What it does |", "|---|---|", *rows, "", END])


def main() -> int:
    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print("README.md has no skill-table markers\nFAIL")
        return 1
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: table(), text, flags=re.S)
    if "--check" in sys.argv:
        ok = new == text
        print("skill table current" if ok else "skill table stale: run python scripts/skill-table.py")
        print("PASS" if ok else "FAIL")
        return 0 if ok else 1
    README.write_text(new, encoding="utf-8", newline="\n")
    print("README skill table rebuilt\nPASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
