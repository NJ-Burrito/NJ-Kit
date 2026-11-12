#!/usr/bin/env python
"""
Arabic folding for comparison, and a PDF extraction-fidelity probe.

Two jobs, both from method-ar.md §4:

1. Fold Arabic so two spellings of the same word compare equal
   (stdin -> stdout, or --text "...", or a file argument).
   Folding is for *matching only* — never quote folded text in a report.

2. --check-extraction file.pdf: print the first 600 characters that poppler
   pulls out of the PDF and flag the known corruption signatures. Extraction
   from an Arabic PDF reorders and de-shapes letters silently; counting or
   grepping corrupt text produces confident wrong findings, which is worse
   than no finding at all. Verify first, grep second.

Poppler only. pymupdf and pdfium drop Arabic words without saying so —
measured 6/9 and 0/9 words against poppler's 9/9 on one sentence.

Usage
-----
  echo "الإلكترونيّة" | python fold_ar.py
  python fold_ar.py --text "آلاء"
  python fold_ar.py extracted.txt > folded.txt
  python fold_ar.py --check-extraction "doc.pdf"
  python fold_ar.py --check-extraction "doc.pdf" --page 3 --chars 600
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import unicodedata

if hasattr(sys.stdout, "reconfigure"):          # a cp1252 console cannot print
    sys.stdout.reconfigure(encoding="utf-8")    # one Arabic character
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# --- folding ---------------------------------------------------------------

ALEF = dict.fromkeys(map(ord, "آأإٱا"), "ا")
YEH = dict.fromkeys(map(ord, "ىيﻯ"), "ي")
TEH = {ord("ة"): "ه"}
WAW = {ord("ؤ"): "و"}
HAMZA_YEH = {ord("ئ"): "ي"}
TATWEEL = {ord("ـ"): None}
# harakat, tanwin, shadda, sukun, superscript alef, and the invisible
# bidi/joiner marks Word pastes in (they survive extraction and break grep)
MARKS = {
    ord(c): None
    for c in "ًٌٍَُِّْٓٔ"
    "ٰٕٖٗ٘​‌‍‎‏"
    "‪‫‬‭‮⁦⁧⁨⁩﻿"
}
ARABIC_DIGITS = {ord(d): str(i) for i, d in enumerate("٠١٢٣٤٥٦٧٨٩")}
ARABIC_DIGITS.update({ord(d): str(i) for i, d in enumerate("۰۱۲۳۴۵۶۷۸۹")})

FOLD = {}
for table in (ALEF, YEH, TEH, WAW, HAMZA_YEH, TATWEEL, MARKS, ARABIC_DIGITS):
    FOLD.update(table)


def fold(text: str, digits: bool = True) -> str:
    """Normalise Arabic for comparison. Idempotent."""
    # NFKC first: presentation forms (ﻻ, ﷲ, isolated/medial glyphs) that some
    # extractors emit collapse to their canonical letters here.
    text = unicodedata.normalize("NFKC", text)
    table = FOLD if digits else {k: v for k, v in FOLD.items()
                                 if k not in ARABIC_DIGITS}
    text = text.translate(table)
    return re.sub(r"[ \t ]+", " ", text).strip()


# --- extraction fidelity ---------------------------------------------------

# Signatures of a de-shaped / reordered Arabic extraction. Each is a sequence
# that correct Arabic never produces, and that a broken extractor produces
# constantly: a lam-alef pair rendered as two separate letters in the wrong
# order, an alef-madda split, and a definite article inverted.
CORRUPTION = {
    "اإل": "lam-alef split and reversed (الإ -> اإل) — 'الإلكترونية' becomes 'اإللكرتونية'",
    "آال": "alef-madda split (آلا -> آال) — 'آلاء' becomes 'آالء'",
    "أل ا": "article detached from its noun",
    "ىف": "final yeh + feh — 'في' reversed",
    "نم ": "'من' reversed",
    "ىلع": "'على' reversed",
    "ةي": "taa-marbuta leading a word — the word is written backwards",
}


def pdftotext(pdf: str, page: int | None) -> str:
    exe = shutil.which("pdftotext")
    if not exe:
        sys.exit("pdftotext (poppler) not on PATH. Do not substitute pymupdf "
                 "or pdfium: they drop Arabic words silently.")
    cmd = [exe, "-enc", "UTF-8", "-layout"]
    if page:
        cmd += ["-f", str(page), "-l", str(page)]
    cmd += [pdf, "-"]
    out = subprocess.run(cmd, capture_output=True)
    if out.returncode != 0:
        sys.exit(out.stderr.decode("utf-8", "replace").strip() or
                 f"pdftotext failed on {pdf}")
    return out.stdout.decode("utf-8", "replace")


def check_extraction(pdf: str, page: int | None, chars: int) -> int:
    text = pdftotext(pdf, page)
    head = re.sub(r"\n{3,}", "\n\n", text)[:chars]
    print(f"=== first {chars} chars of {pdf}"
          + (f" (page {page})" if page else "") + " ===")
    print(head)
    print("=== end ===\n")

    hits = [(sig, why) for sig, why in CORRUPTION.items() if sig in text]
    latin_ids = sorted(set(re.findall(
        r"\b(?:FR|BR|NFR|US|UC|SR)-[A-Z0-9-]+|ERROR_\d+", text)))

    if hits:
        print("CORRUPT — extraction is not faithful:")
        for sig, why in hits:
            print(f"  {sig!r}  {why}  ({text.count(sig)}x)")
        print("\nDo NOT grep or count Arabic from this extraction. Latin "
              "identifiers survive de-shaping — build the automated "
              "comparisons on those, and render the page to an image for "
              "anything that must be quoted or decided.")
    else:
        print("CLEAN — no known corruption signature found.")
        print("This is a negative result, not a guarantee: read the printed "
              "text above against the rendered page before trusting a count.")

    if latin_ids:
        print(f"\nLatin identifiers found ({len(latin_ids)}): "
              + ", ".join(latin_ids[:40])
              + (" ..." if len(latin_ids) > 40 else ""))
    else:
        print("\nNo FR-/BR-/US-/ERROR_ identifiers found — either the document "
              "has none (a finding in itself) or extraction lost them.")
    return 1 if hits else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="text file to fold (default: stdin)")
    ap.add_argument("--text", help="fold this string instead of stdin")
    ap.add_argument("--check-extraction", metavar="PDF",
                    help="print the first N chars via poppler and flag corruption")
    ap.add_argument("--page", type=int, help="with --check-extraction: one page only")
    ap.add_argument("--chars", type=int, default=600, help="default 600")
    ap.add_argument("--keep-digits", action="store_true",
                    help="do not map Arabic-Indic digits to ASCII")
    args = ap.parse_args()

    if args.check_extraction:
        return check_extraction(args.check_extraction, args.page, args.chars)

    if args.text is not None:
        src = args.text
    elif args.file:
        src = open(args.file, encoding="utf-8", errors="replace").read()
    else:
        data = sys.stdin.buffer.read()
        src = data.decode("utf-8", "replace")

    for line in src.splitlines() or [""]:
        print(fold(line, digits=not args.keep_digits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
