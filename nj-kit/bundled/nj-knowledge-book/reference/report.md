# The report (one PDF per language)

Chain: pages (md) → pandoc fragments → one HTML (parts from `book.json`) →
`pdf-typography` renderer (headless Chrome, Thmanyah, tagged) → PDF. Then
`repair-tounicode.py` on the Arabic PDF per `pdf-typography`'s definition of done.

`build_report.py` does all of it; `check_report.py` gates it.

## Navigation floor (any book over ~100 pages)

- **Outline (bookmarks)** mirroring parts and pages: `renderPdf({outline: true})`.
  The QA run shipped 384 and 389 pages with zero bookmarks.
- **TOC with page numbers** by a two-print pass: print, read each anchor's page
  from the PDF, write the numbers into the TOC, print again. (Chrome does not
  honour `target-counter` — not relied on.)
- Cross-references are links (`<a href="#id">`), not text.
- Back-of-book: a **bilingual glossary generated from the term map** (term,
  Arabic, first-use page). No hand-made index.
- The cover prints the **oldest `retrieved` date** of any cited source, so a
  reader sees how stale the book can be.
- A **Method page** states what the gate proves, the audit's n, misses and 95 %
  upper bound, that independence is by agent name, and what was not verified
  (e.g. semantic fidelity of the twin). `build_report.py` refuses without a passing audit.
- **Practice banks** print as their own part after the pages, answer keys as a
  separate part after that (a PDF cannot "cover until answered"); opt out with
  `banks.print = false`.
- Every page's ids are prefixed per page (the QA HTML had 215 / 225 duplicate ids);
  the TOC page numbers are matched by heading order, one extra print at most.

## Glyphs

Thmanyah lacks → ← ≥ ≤ ≈ ² ₂ and box drawing; Chrome then falls back to Times
silently. The build substitutes from one table applied to every text path (body,
TOC, titles, footer template, SVG labels) in both languages, and
`check_report.py` reads the Thmanyah cmaps (fontTools) and fails on any visible
codepoint none covers.

## What `check_report.py` derives (never hard-codes)

Every source page title is in the PDF text (from the source list, not the built
list) · PDF words / source words within 0.95–1.06 (QA run: 0.993 EN, 1.021 AR) ·
no duplicate HTML ids · inline SVGs == number of mermaid fences in
the source · every `pdffonts` row is a Thmanyah face (not just "no Cairo") ·
outline entries ≥ parts + pages · Arabic build has `dir="rtl" lang="ar"` and
Arabic SVG text; English SVG text has none · glyph-gap set empty. Missing
pymupdf or fontTools prints a SKIP line for that check, never a silent pass.
