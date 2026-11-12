#!/usr/bin/env python3
"""
Read a PDF's real structure — tables, lists, layers and reading order — and
render it as markdown a proofreader can actually work through.

Why this exists: a plain text dump flattens a document. Table cells run
together into one line, list nesting disappears, and anything sitting on a
non-default optional-content layer is simply absent. That last one is the
failure mode people know from applicant tracking systems, which read a CV as a
single column and miss half of it — the text is in the file, and the reader
never asks for it.

    python pdf-structure.py FILE                 markdown, tables and lists intact
    python pdf-structure.py FILE --layers        just the layer report
    python pdf-structure.py FILE --json          machine-readable
    python pdf-structure.py FILE -o out.md       write instead of printing

Two engines, each used only for what it is reliable at:

  * **poppler (`pdftotext`) for every character of text.** mupdf and pdfium
    return Arabic that is missing whole words — measured on one nine-word
    sentence: mupdf 6/9, pdfium 0/9, poppler 9/9. Text extracted with anything
    but poppler cannot be trusted for Arabic, and this file never does.
  * **pymupdf for geometry and metadata only** — where the tables are, what
    layers exist, whether a structure tree is present. It is never asked what
    the words say.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import pymupdf
except ImportError:
    pymupdf = None

ARABIC_RE = re.compile(r"[؀-ۿݐ-ݿﭐ-﻿]")
BIDI_CONTROLS = dict.fromkeys(map(ord, "‎‏‪‫‬‭‮⁦⁧⁨⁩"))

# A bullet at the head of a line, in either script's conventions.
BULLET_RE = re.compile(r"^(\s*)([•·▪◦\-\*●▪]|[0-9]+[.)]|[٠-٩]+[.)]|[a-zA-Z][.)]|[أ-ي][.)])\s+(.*)$")


def need_poppler() -> None:
    if not shutil.which("pdftotext"):
        sys.exit(
            "pdftotext (poppler/xpdf) is required and was not found.\n"
            "Every other extractor tested drops Arabic words silently, so there is\n"
            "no safe fallback — install it rather than accept a quiet wrong answer."
        )


def text_of(pdf: Path, page: int | None = None, mode: str = "-layout") -> str:
    """Page text via poppler. `mode` is -layout, -table, or -raw."""
    cmd = ["pdftotext", "-enc", "UTF-8", mode]
    if page is not None:
        cmd += ["-f", str(page), "-l", str(page)]
    cmd += [str(pdf), "-"]
    run = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return run.stdout if run.returncode == 0 else ""


def clean(s: str) -> str:
    """Drop bidi controls — they are invisible, and they break every comparison."""
    return s.translate(BIDI_CONTROLS).strip()


# ── layers ───────────────────────────────────────────────────────────────────

def layers(pdf: Path) -> list[dict]:
    """
    Optional content groups, and whether each is on by default.

    A layer that is off by default holds text a plain reader never sees. That is
    not always a problem — it is how watermarks, alternate languages and
    print-only marks are done — but it is always worth knowing, because the
    document says something the reader is not being shown.
    """
    if pymupdf is None:
        return []
    doc = pymupdf.open(pdf)
    out = []
    try:
        ocgs = doc.get_ocgs() or {}
    except Exception:
        ocgs = {}
    for xref, info in ocgs.items():
        out.append(
            {
                "xref": xref,
                "name": info.get("name", "(unnamed)"),
                "visible_by_default": bool(info.get("on", True)),
                "usage": info.get("usage", ""),
            }
        )
    doc.close()
    return out


def structure_summary(pdf: Path) -> dict:
    if pymupdf is None:
        return {}
    doc = pymupdf.open(pdf)
    try:
        catalog = doc.xref_object(doc.pdf_catalog())
        tagged = "StructTreeRoot" in catalog
    except Exception:
        tagged = False
    info = {
        "pages": doc.page_count,
        "tagged": tagged,
        "toc_entries": len(doc.get_toc() or []),
    }
    doc.close()
    return info


def table_regions(pdf: Path) -> dict[int, int]:
    """How many tables pymupdf finds per page — geometry only, never text."""
    if pymupdf is None:
        return {}
    doc = pymupdf.open(pdf)
    found: dict[int, int] = {}
    for i in range(doc.page_count):
        try:
            n = len(doc[i].find_tables().tables)
        except Exception:
            n = 0
        if n:
            found[i + 1] = n
    doc.close()
    return found


# ── tables and lists from poppler's aligned output ───────────────────────────

def split_columns(lines: list[str]) -> list[list[str]] | None:
    """
    Recover columns from `pdftotext -table`, which aligns cells with runs of
    spaces. Column boundaries are the character positions that are blank on
    *every* line of the block — a gap one row happens to have is not a column.
    """
    body = [ln for ln in lines if ln.strip()]
    if len(body) < 2:
        return None
    width = max(len(ln) for ln in body)
    padded = [ln.ljust(width) for ln in body]
    blank = [all(row[c] == " " for row in padded) for c in range(width)]

    # A separator is a blank run of 2+ columns; single spaces are word gaps.
    cuts, run_start = [], None
    for c, is_blank in enumerate(blank):
        if is_blank and run_start is None:
            run_start = c
        elif not is_blank and run_start is not None:
            if c - run_start >= 2:
                cuts.append((run_start, c))
            run_start = None
    if not cuts:
        return None

    bounds = [0] + [c[1] for c in cuts]
    ends = [c[0] for c in cuts] + [width]
    rows = [[clean(row[s:e]) for s, e in zip(bounds, ends)] for row in padded]
    rows = [r for r in rows if any(cell for cell in r)]
    if not rows:
        return None

    # Drop columns empty in every row.
    keep = [c for c in range(len(rows[0])) if any(r[c] for r in rows)]
    rows = [[r[c] for c in keep] for r in rows]

    # Then merge adjacent columns that never both carry content in the same row.
    # A header cell centred over a left-aligned column below it lands at a
    # different x-position, so the detector sees two columns where the document
    # has one — a four-column table came out with five, the header text in one
    # and the body text in its neighbour. Two columns that never collide on any
    # row are that same column, drifting; two that do collide are genuinely
    # separate and are left alone.
    merged = True
    while merged and len(rows[0]) > 2:
        merged = False
        for c in range(len(rows[0]) - 1):
            if all(not (r[c] and r[c + 1]) for r in rows):
                rows = [r[:c] + [(r[c] or r[c + 1])] + r[c + 2:] for r in rows]
                merged = True
                break

    return rows if len(rows[0]) > 1 else None


def to_markdown_table(rows: list[list[str]]) -> str:
    cols = max(len(r) for r in rows)
    rows = [r + [""] * (cols - len(r)) for r in rows]
    head, body = rows[0], rows[1:]
    out = ["| " + " | ".join(head) + " |", "|" + "|".join([" --- "] * cols) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in body]
    return "\n".join(out)


def render_page(pdf: Path, page: int, has_table: bool) -> str:
    """
    One page as markdown.

    Always extracted with -layout, and every block is offered to the column
    detector regardless of what pymupdf thought. pymupdf's find_tables() found
    zero tables on a page holding an obvious four-column Arabic one, so gating
    the conversion on its answer silently flattened the table into prose — the
    exact failure this script exists to prevent. The aligned text is the better
    evidence: if a block has blank columns running through every one of its
    lines, it is a table whatever the detector says. pymupdf's count is kept for
    the header, as a hint, and given no authority.

    -layout rather than -table, which sounds backwards. xpdf's -table mode
    emits each positioned run separately, and for an RTL cell that means the
    words come out reversed inside the cell — «اسم الحقل» became «الحقل اسم».
    -layout keeps the column alignment *and* the cell text intact, so it is
    the better input for both jobs.
    """
    raw = text_of(pdf, page, "-layout")
    blocks, current = [], []
    for line in raw.splitlines():
        if line.strip():
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)

    parts = []
    for block in blocks:
        rows = split_columns(block)
        if rows:
            parts.append(to_markdown_table(rows))
            continue
        rendered = []
        for line in block:
            m = BULLET_RE.match(line)
            if m:
                indent, marker, rest = m.groups()
                depth = len(indent) // 2
                # Numbered markers are kept as written; a renumbered list is a
                # content change, and this tool only re-presents what is there.
                bullet = marker if marker[0].isdigit() or marker[0] in "٠١٢٣٤٥٦٧٨٩" else "-"
                rendered.append(f"{'  ' * depth}{bullet} {clean(rest)}")
            else:
                rendered.append(clean(line))
        parts.append("\n".join(r for r in rendered if r))
    return "\n\n".join(p for p in parts if p.strip())


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--layers", action="store_true", help="only report optional-content layers")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("-o", "--out", type=Path, help="write markdown to a file")
    args = ap.parse_args()

    need_poppler()
    if not args.pdf.exists():
        sys.exit(f"no such file: {args.pdf}")

    info = structure_summary(args.pdf)
    ocgs = layers(args.pdf)
    tables = table_regions(args.pdf)
    hidden = [l for l in ocgs if not l["visible_by_default"]]

    if args.layers or args.json:
        payload = {"file": str(args.pdf), **info, "layers": ocgs, "tables_per_page": tables}
        if args.json and not args.layers:
            payload["markdown"] = "\n\n".join(
                render_page(args.pdf, p, p in tables) for p in range(1, info.get("pages", 0) + 1)
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    pages = info.get("pages", 0)
    header = [
        f"<!-- {args.pdf.name} · {pages} pages"
        f" · {'tagged' if info.get('tagged') else 'NOT tagged'}"
        f" · {sum(tables.values())} table(s)"
        f" · {len(ocgs)} layer(s) -->",
    ]
    if hidden:
        names = ", ".join(l["name"] for l in hidden)
        header.append(
            f"<!-- {len(hidden)} layer(s) hidden by default: {names}."
            " Their text is in the file but not shown to a normal reader. -->"
        )
    if not info.get("tagged"):
        header.append(
            "<!-- No structure tree: reading order is inferred from geometry, so"
            " a multi-column page may interleave. Check anything that reads oddly"
            " against the rendered page. -->"
        )

    body = "\n\n".join(
        f"<!-- page {p} -->\n\n" + render_page(args.pdf, p, p in tables) for p in range(1, pages + 1)
    )
    out = "\n".join(header) + "\n\n" + body + "\n"

    if args.out:
        args.out.write_text(out, encoding="utf-8")
        print(f"wrote {args.out}  ({len(out)} chars, {pages} pages, {sum(tables.values())} tables)")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
