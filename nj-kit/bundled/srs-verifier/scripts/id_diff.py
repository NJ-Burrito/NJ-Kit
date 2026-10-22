#!/usr/bin/env python
"""
Compare two documents by their identifier sets, not by their prose.

Arabic prose does not survive PDF extraction well enough to diff (see
method-ar.md §4), but Latin identifiers do. So a version comparison that is
actually trustworthy is a set comparison over FR-/BR-/US-/NFR-/ERROR_ ids:
what was removed, what was added, and — the finding that matters most —
whether the document was renumbered, which breaks every traceability link
into it while looking, section by section, like nothing changed.

Inputs are two text files (extract with `pdftotext -enc UTF-8`) or two PDFs
(extracted here, with poppler, automatically).

Usage
-----
  python id_diff.py old.txt new.txt
  python id_diff.py "v1.pdf" "v2.pdf" --json report.json
  python id_diff.py old.txt new.txt --pattern 'RQ-\\d+'

Exit code 1 when anything differs, so it can gate a build.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# One named group per family, so a report can say which family shifted.
FAMILIES = {
    "FR":    r"\bFR-\d+\b",
    "NFR":   r"\bNFR-\d+\b",
    "BR":    r"\bBR-[A-Z0-9][A-Z0-9-]*\b",
    "US":    r"\bUS-\d+\b",
    "UC":    r"\bUC-\d+\b",
    "ERROR": r"\bERROR_\d+\b",
}


def read(path: str) -> str:
    p = Path(path)
    if not p.exists():
        sys.exit(f"not found: {path}")
    if p.suffix.lower() == ".pdf":
        exe = shutil.which("pdftotext")
        if not exe:
            sys.exit("pdftotext (poppler) not on PATH — needed to read a PDF.")
        out = subprocess.run([exe, "-enc", "UTF-8", "-layout", str(p), "-"],
                             capture_output=True)
        if out.returncode != 0:
            sys.exit(out.stderr.decode("utf-8", "replace").strip())
        return out.stdout.decode("utf-8", "replace")
    return p.read_text(encoding="utf-8", errors="replace")


def ids(text: str, patterns: dict[str, str]) -> dict[str, list[str]]:
    found = {}
    for name, pat in patterns.items():
        hits = re.findall(pat, text)
        if hits:
            # order of first appearance, deduplicated
            seen, ordered = set(), []
            for h in hits:
                if h not in seen:
                    seen.add(h)
                    ordered.append(h)
            found[name] = ordered
    return found


def numeric(i: str) -> int | None:
    m = re.search(r"(\d+)$", i)
    return int(m.group(1)) if m else None


def renumber_signal(old: list[str], new: list[str]) -> str | None:
    """
    A renumbering looks like: many ids gone, many arrived, count barely moved,
    and the survivors are few. Prose-level diffing misses it entirely; a reader
    sees familiar sections and assumes the ids are the familiar ones too.
    """
    o, n = set(old), set(new)
    if not o or not n:
        return None
    kept = len(o & n)
    churn = len(o ^ n)
    if churn == 0:
        return None
    ratio = kept / max(len(o), len(n))
    if ratio < 0.5 and abs(len(o) - len(n)) <= max(2, 0.15 * len(o)):
        return (f"RENUMBERING SUSPECTED: {len(o)} -> {len(n)} ids but only "
                f"{kept} survive by name ({ratio:.0%}). Every external "
                f"reference into this family is now pointing at a different "
                f"requirement. Demand a mapping table before accepting it.")
    return None


def gaps(items: list[str]) -> list[int]:
    nums = sorted({v for v in (numeric(i) for i in items) if v is not None})
    if len(nums) < 2:
        return []
    missing = [k for a, b in zip(nums, nums[1:]) for k in range(a + 1, b)]
    # One outlier id (FR-99 among FR-01..FR-19) would otherwise report eighty
    # "gaps" and bury the real one. A sequence that is more hole than sequence
    # is not a numbering gap, it is a different numbering scheme — say nothing
    # and let the removed/added lists carry the finding.
    return missing if len(missing) <= len(nums) else []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--pattern", action="append", default=[],
                    metavar="REGEX", help="extra id pattern (repeatable)")
    ap.add_argument("--json", metavar="PATH", help="also write the result as JSON")
    args = ap.parse_args()

    patterns = dict(FAMILIES)
    for i, extra in enumerate(args.pattern, 1):
        patterns[f"CUSTOM{i}"] = extra

    old_txt, new_txt = read(args.old), read(args.new)
    old_ids, new_ids = ids(old_txt, patterns), ids(new_txt, patterns)

    result: dict[str, dict] = {}
    differs = False
    families = sorted(set(old_ids) | set(new_ids))
    if not families:
        print("No identifiers matched in either file. Either the documents "
              "carry none — a finding — or extraction lost them; run "
              "fold_ar.py --check-extraction before concluding.")
        return 1

    print(f"old: {args.old}\nnew: {args.new}\n")
    for fam in families:
        o, n = old_ids.get(fam, []), new_ids.get(fam, [])
        removed = [i for i in o if i not in set(n)]
        added = [i for i in n if i not in set(o)]
        entry = {
            "old_count": len(o), "new_count": len(n),
            "removed": removed, "added": added,
            "kept": len(set(o) & set(n)),
            "gaps_in_new": gaps(n),
        }
        signal = renumber_signal(o, n)
        if signal:
            entry["renumbering"] = signal
        result[fam] = entry
        if removed or added:
            differs = True

        print(f"[{fam}]  {len(o)} -> {len(n)}   kept {entry['kept']}")
        if removed:
            print(f"  removed ({len(removed)}): " + ", ".join(removed[:30])
                  + (" ..." if len(removed) > 30 else ""))
        if added:
            print(f"  added   ({len(added)}): " + ", ".join(added[:30])
                  + (" ..." if len(added) > 30 else ""))
        if entry["gaps_in_new"]:
            print(f"  numbering gaps in new: "
                  + ", ".join(map(str, entry["gaps_in_new"][:30])))
        if signal:
            print(f"  ** {signal}")
        print()

    print("Reminder: 'removed' means the id is absent, not that the "
          "requirement was deleted — search the new document for its text "
          "before reporting a deletion. Report separately what was fixed, "
          "what remains, and what got worse in the update.")

    if args.json:
        Path(args.json).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")

    return 1 if differs else 0


if __name__ == "__main__":
    raise SystemExit(main())
