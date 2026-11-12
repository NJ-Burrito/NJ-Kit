# Extraction traps

The largest silent failure in this work. Extracted text looks fine, reads fine, and is wrong in
exactly the places you are about to count. An audit built on mangled text is confidently false,
which is worse than no audit.

**The rule: anything decisive must be seen at the source.** Extracted text locates candidates; the
rendered page, the model element or the registry row settles them.

SKILL.md §"Arabic PDFs" carries the procedure. This file carries what it does not: the failure
signatures, the non-PDF formats, and safe counting.

## Prove the extraction before any search

```bash
PYTHONUTF8=1 python scripts/fold_ar.py --check-extraction "doc.pdf"
PYTHONUTF8=1 python scripts/fold_ar.py --check-extraction "doc.pdf" --page 12
```

It prints the first 600 characters poppler pulls out, flags the known corruption signatures, and
lists the Latin identifiers it found. **CLEAN is a negative result, not a guarantee** — read the
printed text against the rendered page before trusting a count.

Poppler only (`pdftotext -enc UTF-8`). pymupdf and pdfium drop Arabic words silently: measured
6/9 and 0/9 words against poppler's 9/9 on one sentence. Two of them agreeing is one shared bidi
bug, not corroboration.

To *see* a page, render it and look at it — `pdftoppm -r 160 -f 12 -l 12 -png doc.pdf page` — then
open the image. Every conclusive finding in the report must have been seen this way.

## Right-to-left and Arabic

Extraction breaks Arabic in ways that produce **false zero results**, the worst failure mode
because a zero looks like a clean bill of health.

| Written | Frequently extracted as | Signature |
|---|---|---|
| الإلكترونية | اإللكرتونية | lam-alef split and reversed |
| آلاء | آالء | alef-madda split |
| في، من، على | ىف، نم، ىلع | whole word reversed |
| V03 | 03V | Latin run reordered around Arabic |

Consequences:

- A grep for an Arabic string containing hamza, lam-alef or a ligature may match nothing while the
  term is present on every page.
- Identifiers reorder around Arabic runs: `FR-01` becomes `-01FR`. Anchor on the identifier core,
  or match letters and digits separately.
- Table cells reflow into a reading order that is not the visual order. **Column-to-value
  association from extracted text is unreliable** — read tables from the rendered page. This is
  the single most common way a confident wrong finding gets written.

**Latin identifiers survive**: `FR-14`, `BR-01`, `ERROR_00452`, `2015/30`, `PROJ-SRS-ESV-FPR-01`.
Build every automated comparison on them. `doc_scan.py` does.

**Fold before comparing Arabic**: `آأإا→ا`, `ىي→ي`, `ة→ه`, drop diacritics, tatweel and the
invisible bidi marks Word pastes in, collapse whitespace — `scripts/fold_ar.py`. Never report a
difference that survives only before folding. **Folded text is for matching; quote the original.**

## Other formats

| Format | Traps |
|---|---|
| DOCX | Tracked changes and comments extract as body text. Content controls and text boxes extract out of order or not at all. Check whether revisions are accepted before counting anything |
| PPTX | Speaker notes may or may not extract. Grouped shapes lose reading order. Animated builds flatten to one slide, so a step sequence collapses |
| XLSX | Formulas extract as values or as formulas depending on the reader. Hidden rows, hidden sheets and filtered views hide content that is present |
| HTML | CSS-hidden content extracts, so your extract contains what no reader sees. Tabs and accordions flatten |

## Safe counting

1. Count on the folded text, then **verify the count on the rendered page** for anything that
   enters the report.
2. A count of zero from Arabic text is not evidence of absence until the extraction is proven
   clean for that string.
3. State the extraction method and its verdict in section 8 of the report, always. The reader is
   entitled to know which counts rest on what.
