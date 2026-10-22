# Arabic twin

The English page is the source of truth; the pair is the unit. Twin = Arabic
only (a French or Turkish twin needs its own checks — out of scope until asked).

## Order

1. **Look for an official Arabic text first** (a regulator's Arabic edition, a
   board's glossary). If one exists, its terms win and the twin is *sourced*, not
   translated. The QA run found none for ISTQB and says so on every page that
   could be read as official wording: «ترجمة المشروع، وليست ترجمة رسمية من ISTQB».
2. **Term map before any translation** — `_terms.md` with a version line, the
   style rules, and a table `English | Arabic | note | avoid`. The QA run's 15
   rules (register, Western digits, what stays Latin, 1:1 structure, first-use
   bracket, Arabic punctuation, forbidden characters, one term one translation,
   fixed phrases, no detached one-letter prefix before a Latin word) are a good
   default: `<QA-project>\knowledge-ar\_terms.md` §0.
3. A map change after translation starts is a numbered amendment, and
   `check_pages.py --pair --terms` re-runs over every page, not one.
4. Translators work per page; the **reviser is never the translator** (ISO 17100
   second-linguist revision; same alias rule as KB verification). Defects are
   logged MQM-style `category/severity` (Terminology, Accuracy, Fluency, Locale;
   minor/major/critical) in the ledger.

## What the pair gate checks (`check_pages.py --pair --terms`)

Pages **and** practice banks are paired (banks: same question ids, key letters,
option counts).

Same numbered sections, heading levels, table rows, list items, code blocks,
URLs and `[KB#]` ids · "not confirmed" count equals «غير مؤكد» count · same
multiset of numbers in prose · no Eastern digits, Persian letters, bidi controls,
tashkeel or tatweel in prose · no detached one-letter prefix (`ب Gherkin`) ·
`<!-- en-sha: <sha1> -->` on line 1 matches the English page (else "stale twin")
· no `avoid` variant from the term map. Then run `arabic-english-proofreading`'s
`scan.py` on every Arabic page.

**Not checked by any script:** semantic fidelity. If revisers spot-read pages
rather than reading them whole, the report says so.

Arabic checks live in Python: a grep with an Arabic class silently matches
nothing in Git Bash on this machine (`arabic-english-proofreading` has the detail).

## Diagrams

Mermaid is translated per language: the Arabic `.mmd` holds Arabic labels and
`flowchart RL`, rendered with `mmdc` and the Thmanyah config; Latin inside an
Arabic node is isolated like prose (`pdf-typography` § Latin inside Arabic).
Never reuse the English SVG in the Arabic book.

## Two traps the pair gate enforces

- Digits 3 and above stay digits in Arabic («3 قيم», never «ثلاث قيم»); only 1 and 2
  may be spelled. Numbers are compared as a multiset.
- Write URLs in parentheses or on their own; a trailing `;` or «؛» used to stick to the URL.
