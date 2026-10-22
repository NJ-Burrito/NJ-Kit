---
name: arabic-english-proofreading
description: 'Proofread Arabic, English or bilingual text (SRS, ministry and PROJ submissions, manuals, UI strings). Catches hamza and taa-marbuta errors, Persian letters, invisible bidi characters, tatweel, mixed numerals, Latin punctuation inside Arabic. Triggers: proofread, review, تدقيق, مراجعة لغوية, check the Arabic.'
---

# Proofreading Arabic and English

Arabic errors are largely invisible to the tools that catch English ones. A
spellchecker flags "recieve"; nothing flags «الخدمه» for «الخدمة», a Persian
`ک` typed where an Arabic `ك` belongs, or a zero-width character that Word
left behind and that quietly breaks every search for the word containing it.

So the work splits in two, and the split is the method:

- **Mechanical faults** — countable, decidable from the codepoints alone.
  `scripts/scan.py` finds all of them, exhaustively, in one pass. Never hunt
  for these by reading; reading misses invisible characters by definition.
- **Faults of meaning** — grammar, register, agreement, word choice, and the
  Arabic letter pairs whose correctness depends on the sentence rather than
  the character. These need reading, and reading is where attention should go.

## Start with the scanner

```bash
python scripts/scan.py FILE [FILE...]     # human-readable, grouped by kind
python scripts/scan.py --json FILE        # machine-readable
```

`scan.py` exits 0 even with findings — gate on its "N mechanical finding(s)"
line, not the exit code. And never write an Arabic check as a `grep` character
class: in Git Bash on this laptop `[^ء-ي]` silently matches nothing, so the
check passes on text that is full of the fault (2026-10-15, QA KB translation).
Put it in Python (`re`, `؀-ۿ`) and prove it fails on a bad sample.

It reports invisible and bidi-control characters, tatweel, Persian/Urdu
letters, Latin punctuation inside Arabic, space before punctuation, doubled
words, multiple spaces, trailing whitespace, and mixed numeral systems.

Run it before reading. It costs a second, it is exhaustive where a human is
not, and it clears the noise so the reading pass is about language.

For a `.docx` — most source documents here are Word — convert first, because
pandoc is installed and the alternative is guessing:

```bash
pandoc -f docx -t markdown --wrap=none "SRS - …docx" -o /tmp/doc.md
python scripts/scan.py /tmp/doc.md
```

## For a PDF, read its structure — never a flat text dump

```bash
python scripts/pdf-structure.py FILE -o /tmp/doc.md   # tables, lists, layers
python scripts/pdf-structure.py FILE --layers         # just the layer report
python scripts/scan.py /tmp/doc.md                    # then the usual scan
```

A plain `pdftotext` dump flattens the document: table cells run together into
one line, list nesting disappears, and text on a hidden optional-content layer
is absent entirely. Proofreading that dump means proofreading a different
document from the one the reader sees — corrections land in the wrong cell, and
a whole layer goes unreviewed. This is the failure people know from applicant
tracking systems reading a two-column CV as one column: the text was in the
file, and nothing asked for it.

`pdf-structure.py` returns tables as markdown tables, keeps list markers and
nesting, and reports every layer with whether it is visible by default. Its
header comment names what it found, including anything hidden — read that line
before the body.

**Two engines, and the split is not arbitrary.** All text comes from poppler;
pymupdf is used only for geometry and metadata and is never asked what the words
say. Measured on one nine-word Arabic sentence from a Cairo PDF:

| engine | words recovered |
| --- | --- |
| pypdf | 0 / 9 |
| pymupdf | 6 / 9 |
| poppler (`pdftotext`) | **9 / 9** |

mupdf and pdfium drop Arabic words silently. Two of them agreeing looks like
corroboration and is one shared bug — that is how a sound font came to be
recorded as corrupting text. If `pdftotext` is missing, the script stops rather
than fall back, because a quiet wrong answer is worse than no answer.

## The trap: not every mangled word is a typo

**Text extracted from a PDF can be corrupted by the PDF itself.** Certain
Arabic fonts displace letters inside words during extraction — the word looks
correct on the page and comes out wrong when copied. «متطلبات» extracting as
«متتطلبات» is the documented example, and it was reported as a typo when the
document was in fact spelled correctly.

So before correcting an Arabic word that looks misspelled in extracted text:

1. Ask where the text came from. Copied out of a PDF? Suspect the font first.
2. Look at the *rendered* page — the screenshot or the PDF itself — not the
   extracted string.
3. If the page is right and the extraction is wrong, the defect is in the PDF
   pipeline, not the prose. Say so; correcting the text would be fixing the
   wrong artefact and would leave the real fault shipping.

The `pdf-typography` skill covers which faces survive extraction and which do
not. Amiri round-trips whole words; some widely used UI faces do not.

## The reading pass

Read `references/arabic-checks.md` for the Arabic rules that need judgement —
hamza forms, ة/ه, ى/ي, agreement, and the formal-register conventions that
ministry and PROJ documents are held to. Read it whenever the text under
review contains Arabic; the rules are specific and not worth reconstructing
from memory.

For English, the ordinary things apply, with two that matter more in
translated text than in original writing:

- **Calques.** Arabic-to-English drafts carry Arabic sentence shape:
  "It is to be noted that the system will be doing the validation" for "The
  system validates". Prefer the plain verb.
- **Terminology drift.** A term translated three ways across one document —
  "request", "application", "submission" for «طلب» — reads as three different
  things to a reader who does not have the Arabic. Fix by choosing one and
  applying it, and say which you chose.

## Bilingual documents

When Arabic and English appear as a pair — a manual, a form, a UI string
table — the pair is the unit of review, not each language alone:

- **Do both sides say the same thing?** A correction to one side that leaves
  the other stale is worse than the original error, because now the document
  contradicts itself.
- **Do numbers, dates, IDs and product names match exactly** across the two?
  These are where silent divergence hides, and they are checkable.
- **Latin runs inside Arabic** — API, PROJ, Playwright, a URL — should be
  wrapped in directional isolates (`U+2066…U+2069`) or the equivalent markup.
  Without isolation, adjacent punctuation jumps to the wrong end of the run
  when rendered. The scanner reports existing isolates so you can see whether
  a document uses them; it does not insert them, because whether a run needs
  one depends on what surrounds it.

## Reporting

Correct the text, then account for it. A returned document with silent edits
is impossible to check and impossible to trust.

Group by kind rather than walking line by line, since one root cause usually
produces many instances:

```markdown
## Mechanical (from scan.py)
- 14 × zero-width characters removed (pasted from Word)
- 3 × Latin comma → Arabic comma «،»
- Mixed numerals: 27 Western, 4 Arabic-Indic → standardised on Western

## Language
- «الخدمه» → «الخدمة» (taa marbuta) ×6
- «إن الطلب» → «أن الطلب» — reported speech, not emphasis (line 42)
- "request"/"application" both used for «طلب» → standardised on "request"

## Not corrected — needs your decision
- Line 88 «المستحضر» vs «المنتج» — both defensible; the rest of the document
  uses «المستحضر», but the client's own letter uses «المنتج»
```

That last section matters. Where a change is a judgement about house style,
client preference, or meaning you cannot verify, propose it and leave it — do
not quietly decide on the author's behalf. In a document going to a ministry,
an unrequested wording change can alter what was committed to.

## When the text is not a file

For a paragraph pasted into the conversation, the same order applies — write
it to a temp file, scan it, then read it. It is tempting to skip the scanner
for three lines, but zero-width characters and Persian letters are exactly
what a paste out of Word carries, and exactly what reading will not reveal.

