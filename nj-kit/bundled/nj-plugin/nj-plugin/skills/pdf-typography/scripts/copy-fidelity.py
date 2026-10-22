#!/usr/bin/env python
"""Score the PDF that copy-fidelity.mjs produced: which families copy cleanly.

Two engines, because one engine's quirks are not evidence. PyMuPDF is MuPDF;
pypdfium2 is PDFium, which is what Chrome's own viewer uses. A family is only
condemned when both agree.

The comparison is word by word, and a word counts as intact if it comes back
either forwards or backwards. That is deliberate: a PDF stores a right-to-left
line in visual order and it is the *viewer's* job to run the bidi algorithm on
copy — so reversal is not the document's fault. Letters landing in the wrong
place inside a word is.

    python copy-fidelity.py out.pdf
"""
import sys
import json
import unicodedata
from pathlib import Path

try:
    import pymupdf
except ImportError:
    sys.exit("needs pymupdf:  pip install pymupdf")
try:
    import pypdfium2
except ImportError:
    pypdfium2 = None

import shutil
import subprocess


def poppler_page(pdf: Path, page: int) -> str | None:
    """
    Extract one page with poppler's pdftotext.

    Poppler is the reference implementation and the only one of the three that
    reverses an RTL run correctly. It is the authority here, and the reason is
    worth stating because this file previously concluded the opposite:

    mupdf and pdfium both return Arabic words with their letters in visual
    order. Compared against logical-order source text, whole words look
    "missing", and two engines reporting the same thing reads like corroboration
    when it is really one shared bug. That is how Cairo — a perfectly sound font
    — came to be recorded as displacing letters inside words, and it is why the
    house face was nearly forked to work around a defect that was never in it.

    Measured 2026-09-03 on the same Cairo PDF, one sentence of nine words:
        pypdf      0/9      pymupdf   6/9      pdftotext  9/9
    """
    if not shutil.which("pdftotext"):
        return None
    out = subprocess.run(
        ["pdftotext", "-enc", "UTF-8", "-f", str(page + 1), "-l", str(page + 1), str(pdf), "-"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return out.stdout if out.returncode == 0 else None

BIDI = set("‎‏‪‫‬⁦⁧⁨⁩")


def words(text: str) -> list:
    # Punctuation is stripped by Unicode category, not from a hand-written list:
    # a neutral character at a direction boundary moves when the line is
    # extracted and lands welded to the word beside it, and that is the
    # extractor's doing, not a broken word.
    text = unicodedata.normalize("NFKC", "".join(c for c in text if c not in BIDI))
    text = "".join(c for c in text if not unicodedata.combining(c))
    out = []
    for token in text.split():
        token = token.strip("".join(c for c in token if unicodedata.category(c).startswith("P")))
        if token:
            out.append(token)
    return out


def main() -> int:
    pdf = Path(sys.argv[1])
    meta = json.loads(pdf.with_suffix("").with_suffix(".pages.json").read_text(encoding="utf-8")) \
        if pdf.with_suffix("").with_suffix(".pages.json").exists() \
        else json.loads(Path(str(pdf)[:-4] + ".pages.json").read_text(encoding="utf-8"))

    want = words(meta["sample"])
    mu = pymupdf.open(pdf)
    fi = pypdfium2.PdfDocument(pdf) if pypdfium2 else None

    has_poppler = shutil.which("pdftotext") is not None
    engines = (["poppler"] if has_poppler else []) + ["mupdf"] + (["pdfium"] if fi else [])

    print(f"sample: {meta['sample']}")
    print(f"{len(want)} words · {' / '.join(engines)}")
    if not has_poppler:
        print("  ! pdftotext not found — falling back to mupdf/pdfium, which mis-order RTL")
        print("    and will report sound Arabic fonts as broken. Install poppler.")
    print()

    for i, family in enumerate(meta["families"]):
        scores, missing_by_engine = [], {}

        def take(name: str, text: str) -> None:
            got = words(text)
            pool = set(got) | {w[::-1] for w in got}
            missing = [w for w in want if w not in pool]
            scores.append(len(want) - len(missing))
            missing_by_engine[name] = missing

        if has_poppler:
            take("poppler", poppler_page(pdf, i) or "")
        take("mupdf", mu[i].get_text())
        if fi:
            take("pdfium", fi[i].get_textpage().get_text_bounded())

        # The verdict is poppler's alone when it is present. What we actually
        # need to know is whether the PDF carries a correct glyph→Unicode map,
        # and poppler is the engine that answers that question rather than
        # answering "does this engine handle bidi". The others are printed so a
        # disagreement is visible, but they no longer get a vote — letting them
        # vote is what produced the wrong verdict on Cairo.
        verdict = missing_by_engine["poppler"] if has_poppler else (
            sorted(set(missing_by_engine["mupdf"]).intersection(missing_by_engine.get("pdfium", [])))
            if fi else missing_by_engine["mupdf"]
        )

        mark = "✓" if not verdict else "✗"
        detail = f"   lost: {' '.join(verdict)}" if verdict else ""
        print(f"  {mark} {family:<22} {'/'.join(str(s) for s in scores):>10} of {len(want)}{detail}")

        if has_poppler and not verdict and any(s < len(want) for s in scores[1:]):
            print(f"      (mupdf/pdfium disagree — their bidi handling, not the font)")

    print("\nA family poppler returns whole is safe for body text: the file's")
    print("glyph→Unicode map is correct, which is what a reader's copy depends on.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
