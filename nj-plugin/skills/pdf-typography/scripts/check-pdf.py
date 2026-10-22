#!/usr/bin/env python
"""Audit a produced PDF: is it set in the fonts we chose, and can it be copied?

Chrome fails at this quietly. When a @font-face does not load it substitutes a
system font, prints a page that looks almost right, and embeds that substitute
instead — the only place the truth survives is the font list inside the PDF.
So the first thing this checks is which fonts actually made it in.

    python check-pdf.py doc.pdf
    python check-pdf.py doc.pdf --expect "يشرح هذا الدليل" --expect "SRS v1.2"

Exit status is 1 if anything failed, so it can gate a build.
"""
import argparse
import json
import re
import sys

# Windows consoles default to cp1252, which cannot encode an Arabic path — and
# these documents are delivered in Arabic-named folders. Without this the check
# runs, passes, and then dies printing the filename, which every caller reads as
# "the PDF failed". Report in the encoding the paths are actually in.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import unicodedata
from pathlib import Path

try:
    import pymupdf
except ImportError:
    sys.exit("needs pymupdf:  pip install pymupdf")

VAULT = Path(__file__).resolve().parent.parent / "fonts"

# Fonts that mean a fallback happened. Not an exhaustive list of system fonts —
# just the ones Chrome reaches for, which is what a silent substitution looks
# like. Any of these in a document we set ourselves is a bug, and embedding the
# Microsoft ones in a file we hand to a client is also a licence problem.
SYSTEM_FONTS = re.compile(
    r"segoe|arial|calibri|cambria|times|tahoma|dubai|courier|helvetica|"
    r"simplifiedarabic|traditionalarabic|sakkal|majalla|aptos|verdana|georgia",
    re.I,
)

BIDI = set("‎‏‪‫‬⁦⁧⁨⁩")


def base_name(font: str) -> str:
    """`AAAAAA+Amiri-Regular` -> `Amiri-Regular`."""
    return font.split("+")[-1]


def vault_families() -> set:
    """Everything the vault can legitimately have put in a document: the
    downloaded roster, plus whatever was dropped into `licensed/` by hand."""
    known = set()
    path = VAULT / "MANIFEST.json"
    if path.exists():
        known |= {e["family"].replace(" ", "").lower()
                  for e in json.loads(path.read_text(encoding="utf-8"))}
    for file in (VAULT / "licensed").glob("*"):
        match = re.match(r"^(.+)-\d{3}i?\.(ttf|otf)$", file.name, re.I)
        if match:
            known.add(match.group(1).replace(" ", "").lower())
    return known


def strip_punct(token: str) -> str:
    """Punctuation off both ends, whatever the script.

    A neutral character at a direction boundary — a full stop, a guillemet, a
    colon — moves when the line is extracted, and lands welded to whichever word
    is now beside it. `»المرفقات` is not a broken word; it is an intact word
    with somebody else's quote mark on it. Stripping by Unicode category keeps
    the check honest about the difference."""
    return token.strip("".join(c for c in token if unicodedata.category(c).startswith("P")))


def words(text: str) -> list:
    """Words, with the diacritics and direction marks that extraction adds or
    drops taken out, and presentation forms folded back to base letters."""
    text = unicodedata.normalize("NFKC", "".join(c for c in text if c not in BIDI))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return [w for w in (strip_punct(t) for t in text.split()) if w]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--expect", action="append", default=[],
                    help="a string from the source; checked word by word against what copies out")
    ap.add_argument("--allow", action="append", default=[],
                    help="tolerate this font even though it is not in the vault")
    args = ap.parse_args()

    doc = pymupdf.open(args.pdf)
    known = vault_families() | {a.replace(" ", "").lower() for a in args.allow}
    problems = []

    # ── 1. which fonts are actually in the file ──────────────────────────
    seen = {}
    for page in range(doc.page_count):
        for font in doc.get_page_fonts(page):
            seen.setdefault(base_name(font[3]), (font[2], font[1], page))

    print(f"{args.pdf}  ·  {doc.page_count} pages")
    print("\nfonts")
    for name, (kind, ext, first) in sorted(seen.items()):
        stem = re.split(r"[-,]", name)[0].lower()
        embedded = ext not in ("", "n/a")
        # A name on the system list means a fallback happened — unless the face
        # is in the vault, in which case somebody put it there on purpose and
        # the document asked for it by name. Simplified Arabic is both: it ships
        # with Windows and it is a licensed choice a client made. The vault is
        # the record of intent, so the vault wins.
        if SYSTEM_FONTS.search(name) and stem not in known:
            note, bad = "SYSTEM FONT — a @font-face did not load", True
        elif known and stem not in known:
            note, bad = "not from the vault", True
        elif not embedded:
            note, bad = "NOT EMBEDDED", True
        else:
            note, bad = "ok", False
        print(f"  {'✗' if bad else '✓'} {name:<34} {kind:<7} first on page {first + 1:<4} {note}")
        if bad:
            problems.append(f"{name}: {note}")

    # ── 2. is there a structure tree ─────────────────────────────────────
    tagged = "StructTreeRoot" in doc.xref_object(doc.pdf_catalog())
    print(f"\ntagged (accessible) PDF: {'yes' if tagged else 'no'}")
    if not tagged:
        problems.append("not tagged — pass tagged:true to page.pdf()")

    # ── 3. does the text come back out ───────────────────────────────────
    #
    # Poppler first, mupdf only as a fallback. mupdf returns Arabic in visual
    # order, so a correct RTL word compared against logical-order source looks
    # missing — that is how this audit came to fail sound Arabic fonts, Cairo
    # among them, and nearly cost the house face. Measured on one nine-word
    # sentence: pymupdf 6/9, pdftotext 9/9. Poppler answers the question this
    # check is actually asking, which is whether the glyph→Unicode map is right.
    import shutil
    import subprocess

    text = ""
    if shutil.which("pdftotext"):
        run = subprocess.run(
            ["pdftotext", "-enc", "UTF-8", str(args.pdf), "-"],
            capture_output=True, text=True, encoding="utf-8",
        )
        if run.returncode == 0:
            text = run.stdout
    if not text.strip():
        text = "\n".join(doc[i].get_text() for i in range(doc.page_count))
    if not text.strip():
        problems.append("no extractable text at all — the page was rasterised")
        print("text: NONE — this PDF is a picture of a document")
    else:
        tofu = text.count("�")
        print(f"text: {len(text)} characters extractable" + (f", {tofu} replacement chars" if tofu else ""))
        if tofu:
            problems.append(f"{tofu} unmapped characters (U+FFFD) in the text")

    if args.expect:
        print("\ncopy check")
        pool = words(text)
        pool = set(pool) | {w[::-1] for w in pool}

        # The same text with every space removed. A word missing from the word
        # pool but present here was not scrambled — it was *split*, by an
        # extractor that put a break around a diacritic or ran two table cells
        # together. That is the reading tool's doing and every real viewer gets
        # it right; letters landing in the wrong order is the document's doing
        # and no viewer can undo it. Only the second is a failure.
        stream = "".join(words(text))
        stream = stream + "|" + stream[::-1]

        for phrase in args.expect:
            missing = [w for w in words(phrase) if w not in pool]
            split = [w for w in missing if w in stream or w[::-1] in stream]
            scrambled = [w for w in missing if w not in split]

            if scrambled:
                mark, note = "✗", "scrambled: " + " ".join(scrambled[:4])
                problems.append(f"copy: {' '.join(scrambled[:4])}")
            elif split:
                mark, note = "~", "intact but split by extraction: " + " ".join(split[:3])
            else:
                mark, note = "✓", "all words intact"
            print(f"  {mark} {phrase[:52]:<54} {note}")

    print()
    if problems:
        print(f"FAILED — {len(problems)} problem(s)")
        for p in problems:
            print(f"  · {p}")
        return 1
    print("PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
