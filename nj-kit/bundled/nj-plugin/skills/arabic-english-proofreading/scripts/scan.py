#!/usr/bin/env python3
"""
Mechanical checks for Arabic/English text. Deterministic, no judgement.

The point of this script is to take the countable, invisible and boring
problems off the model's plate so its attention goes to meaning, register and
the errors that actually need reading. Anything that can be found by counting
codepoints is found here.

    python scan.py FILE [FILE...]
    python scan.py --json FILE          machine-readable
    python scan.py --context 40 FILE    widen the shown excerpt

Exit status is 0 whether or not findings exist — this reports, it does not gate.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

# ── character classes ────────────────────────────────────────────────────────

ARABIC = r"؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿"
ARABIC_RE = re.compile(f"[{ARABIC}]")

# Invisible and bidi-control characters. These survive copy/paste out of Word
# and PDFs, are impossible to see, and silently break search, diff and sorting.
INVISIBLES = {
    "​": "ZERO WIDTH SPACE",
    "‌": "ZERO WIDTH NON-JOINER",
    "‍": "ZERO WIDTH JOINER",
    "‎": "LEFT-TO-RIGHT MARK",
    "‏": "RIGHT-TO-LEFT MARK",
    "‪": "LEFT-TO-RIGHT EMBEDDING",
    "‫": "RIGHT-TO-LEFT EMBEDDING",
    "‬": "POP DIRECTIONAL FORMATTING",
    "‭": "LEFT-TO-RIGHT OVERRIDE",
    "‮": "RIGHT-TO-LEFT OVERRIDE",
    "﻿": "ZERO WIDTH NO-BREAK SPACE (BOM)",
    " ": "NO-BREAK SPACE",
}

# Directional isolates are the *correct* way to wrap a Latin run inside Arabic,
# so they are reported separately and never as a fault.
ISOLATES = {
    "⁦": "LEFT-TO-RIGHT ISOLATE",
    "⁧": "RIGHT-TO-LEFT ISOLATE",
    "⁨": "FIRST STRONG ISOLATE",
    "⁩": "POP DIRECTIONAL ISOLATE",
}

# Letters from Persian/Urdu keyboards that look almost identical to the Arabic
# ones and are a frequent silent corruption — they break search and shaping.
CONFUSABLES = {
    "ک": ("ک", "ك", "ك", "Persian KEHEH for Arabic KAF"),
    "ی": ("ی", "ي", "ي", "Persian FARSI YEH for Arabic YEH"),
    "ھ": ("ھ", "ه", "ه", "HEH DOACHASHMEE for Arabic HEH"),
}

# Deliberately NOT mechanical: alef maksura (ى) vs yeh (ي), and taa marbuta (ة)
# vs heh (ه). Both are real and frequent errors, and both are decided by
# grammar rather than by codepoint — «يرجى», «مستوى» and «أعلى» are correct
# with ى, «على» is correct, «علي» as a name is also correct. A scanner that
# flags every final ى cries wolf on correct prose, and a reader stops trusting
# it. These belong to the reading pass; see references/arabic-checks.md.

TATWEEL = "ـ"
ARABIC_INDIC = "٠-٩"
EXT_ARABIC_INDIC = "۰-۹"
TASHKEEL_RE = re.compile(r"[ً-ْٰـ]")

# Latin punctuation that should be its Arabic counterpart inside Arabic text.
LATIN_PUNCT_IN_ARABIC = {",": "،", ";": "؛", "?": "؟"}


def _excerpt(line: str, col: int, width: int) -> str:
    lo = max(0, col - width // 2)
    hi = min(len(line), col + width // 2)
    return ("…" if lo else "") + line[lo:hi].strip() + ("…" if hi < len(line) else "")


def scan_text(text: str, width: int = 60) -> list[dict]:
    findings: list[dict] = []

    def add(line_no: int, col: int, kind: str, detail: str, line: str, fix: str = "") -> None:
        findings.append(
            {
                "line": line_no,
                "col": col + 1,
                "kind": kind,
                "detail": detail,
                "fix": fix,
                "excerpt": _excerpt(line, col, width),
            }
        )

    lines = text.splitlines()
    in_code_block = False

    # Numeral systems are counted across the whole document, because the fault
    # is *inconsistency*, not either system on its own.
    western = len(re.findall(r"(?<![\w.])[0-9]", text))
    arabic_indic = len(re.findall(f"[{ARABIC_INDIC}{EXT_ARABIC_INDIC}]", text))

    for i, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        has_arabic = bool(ARABIC_RE.search(line))
        # A markdown table row pads its cells with runs of spaces to line the
        # pipes up. That is layout, not prose. Counting it as a spacing fault
        # produced 1042 findings on a single converted SRS and buried the ~50
        # real ones — a report nobody would read twice.
        is_table_row = line.lstrip().startswith("|") or set(line.strip()) <= set("|-+: ")

        for col, ch in enumerate(line):
            if ch in INVISIBLES:
                add(i, col, "invisible-char", f"U+{ord(ch):04X} {INVISIBLES[ch]}", line, "remove")
            elif ch in ISOLATES:
                add(i, col, "bidi-isolate", f"U+{ord(ch):04X} {ISOLATES[ch]} — intentional?", line)
            elif ch == TATWEEL:
                # One finding per run, not per character: «تمـــديد» is a single
                # mistake, and reporting it three times buries the other results.
                if col == 0 or line[col - 1] != TATWEEL:
                    run = len(line[col:]) - len(line[col:].lstrip(TATWEEL))
                    add(i, col, "tatweel", f"U+0640 ×{run} used as visual justification", line, "remove")
            elif ch in CONFUSABLES:
                glyph, right_cp, right, why = CONFUSABLES[ch]
                add(i, col, "confusable-letter", why, line, f"{glyph} → {right}")

        if has_arabic:
            for col, ch in enumerate(line):
                if ch in LATIN_PUNCT_IN_ARABIC:
                    near = line[max(0, col - 12) : col + 12]
                    if ARABIC_RE.search(near):
                        add(
                            i,
                            col,
                            "latin-punctuation",
                            f"'{ch}' inside Arabic text",
                            line,
                            f"{ch} → {LATIN_PUNCT_IN_ARABIC[ch]}",
                        )

            if TASHKEEL_RE.search(line.replace(TATWEEL, "")):
                m = TASHKEEL_RE.search(line)
                if m:
                    add(i, m.start(), "tashkeel", "diacritics present — usually stripped in formal prose", line)

        for m in re.finditer(r"\s+([،؛؟!?.,:])", line):
            add(i, m.start(), "space-before-punctuation", f"space before '{m.group(1)}'", line, "remove the space")

        if not is_table_row:
            for m in re.finditer(r"[^\s] {2,}[^\s]", line):
                add(i, m.start(), "multiple-spaces", "more than one space between words", line, "collapse to one")

        if line != line.rstrip():
            add(i, len(line.rstrip()), "trailing-whitespace", "trailing whitespace", line, "strip")

        # Doubled words — the single most common real typo in both languages,
        # and one the eye skips over precisely because it reads correctly.
        for m in re.finditer(r"\b(\w+)(\s+)\1\b", line, flags=re.UNICODE):
            add(i, m.start(), "repeated-word", f"'{m.group(1)}' twice in a row", line, "delete one")

    if western and arabic_indic:
        findings.append(
            {
                "line": 0,
                "col": 0,
                "kind": "mixed-numerals",
                "detail": f"{western} Western (0-9) and {arabic_indic} Arabic-Indic (٠-٩) digits in one document",
                "fix": "pick one system and apply it throughout",
                "excerpt": "",
            }
        )

    return findings


def main() -> int:
    # Windows consoles default to cp1252, which cannot encode a single Arabic
    # letter — the script would traceback while printing its own findings. This
    # is the whole point of the tool, so the stream is forced to UTF-8 rather
    # than left to the locale.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--context", type=int, default=60, help="excerpt width (default 60)")
    args = ap.parse_args()

    report: dict[str, list[dict]] = {}
    for path in args.files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"{path}: cannot read — {exc}", file=sys.stderr)
            continue
        report[str(path)] = scan_text(text, args.context)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    total = 0
    for path, findings in report.items():
        print(f"\n{path}")
        if not findings:
            print("  no mechanical issues found")
            continue
        by_kind: dict[str, list[dict]] = {}
        for f in findings:
            by_kind.setdefault(f["kind"], []).append(f)
        for kind, items in sorted(by_kind.items(), key=lambda kv: -len(kv[1])):
            print(f"  {kind} ({len(items)})")
            for f in items[:8]:
                where = f"line {f['line']}:{f['col']}" if f["line"] else "document"
                fix = f"  → {f['fix']}" if f["fix"] else ""
                print(f"    {where}  {f['detail']}{fix}")
                if f["excerpt"]:
                    print(f"        {f['excerpt']}")
            if len(items) > 8:
                print(f"    … and {len(items) - 8} more")
            total += len(items)
    print(f"\n{total} mechanical finding(s). Meaning, register and word choice still need reading.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
