---
name: pdf-typography
description: 'PDFs whose text stays real: selectable and searchable. Self-hosted open-licence fonts as base64 @font-face, printed by headless Chrome, then audited. Use for PDFs from HTML/CSS; when text copies out garbled, Arabic does not join, or fonts fall back to Arial.'
---

# Typography for generated PDFs

A PDF is not a picture of a document. It carries the glyphs, the font programs
they came from, and a table mapping each glyph back to Unicode. Get those three
right and the text selects, searches, copies and reflows like text. Get them
wrong and the page still *looks* fine — which is why this goes wrong quietly and
stays wrong for months.

The pipeline is: **fonts on disk → base64 `@font-face` → HTML/CSS → headless
Chrome `page.pdf()` → audit the result.** Never a screenshot, never a system
font, never an unverified build.

## The one failure that starts every other one

`page.setContent(html)` gives the page no document origin. A `file:///` font URL
is then a cross-origin subresource, and Chrome **refuses it without a word** —
no console error, no thrown promise — and silently substitutes a system font.
Measured, not theorised:

```
setContent + file://   →  every family FALLBACK
setContent + data:     →  every family loaded
goto('file:///…')      →  every family loaded
```

It is also how the PROJ SRS shipped 31 pages set in **Segoe UI** while its
stylesheet asked for IBM Plex Sans Arabic — never the chosen typeface, and a
Microsoft font embedded in a file a Windows licence does not cover to redistribute.

So: **fonts are delivered as base64 `data:` URIs**, always — the only form that
survives `setContent`, and the only one that reaches Chrome's header/footer
templates (rendered as separate documents with no access to the page's
stylesheet; a `@font-face` inside the footer template's own `<style>` does work,
verified, as a `data:` URI). `page.goto('file:///…')` also loads every family
correctly and is the other safe option (reconfirmed on this machine 2026-09-19,
`report/research/pdf-toolchain.md`) — either form works, `setContent` + `file://`
is the one combination that silently doesn't.

## The vault

`fonts/` holds every family as an original `.ttf`, downloaded from Google's CSS
API with the User-Agent `Mozilla/5.0` and nothing after it. That exact UA
matters: a modern UA gets woff2 split into a dozen `unicode-range` subsets — one
file for Arabic, one for maths, one for symbols — and a build that grabbed the
wrong one would embed a font with no Arabic in it. The bare UA gets one whole
font per weight. `fetch-fonts.mjs` refuses any answer containing a
`unicode-range` rather than save a quarter of a typeface under a full name.

**Drop-ins must be TrueType.** Handed a CFF/OpenType `.otf`, Chrome gives up on
embedding the font program and writes every glyph as a **Type 3** drawing
procedure — one unnamed font object per text run, no font name in the file,
rejected by strict validators. It says nothing, and the page looks right.
Proven by isolation: the same typeface converted to TrueType outlines comes out
as `Type0 AAAAAA+AmmanV3Sans-Bold`, and clearing the font's `fsType` embedding
flag changes nothing — it is the outline format, not the licence. So convert
first, and `font-css.mjs` refuses a bare `.otf` rather than let it ship:

```bash
python scripts/otf-to-ttf.py "fonts/licensed/AmmanV3 Sans-700.otf"
```

**Converting is itself a licence question.** CFF→TrueType is a modification of
the font program — if the licence says "no modification" (Thmanyah's
`fonts.css` header: *"free commercial use, NO redistribution, NO hosting, NO
modification. Bundled embed only"*), converting for embedding violates it. Get
a TrueType-outline variant, or confirmed sign-off, first
(`report/research/pdf-toolchain.md`, 2026-09-19).

Every family is SIL OFL 1.1 or Apache 2.0. This is not pedantry: a PDF *embeds*
the glyphs it draws with, so shipping the document redistributes the typeface.
Anything commercial goes in `fonts/licensed/` by hand, after someone has read
the licence and confirmed it grants **document embedding** — a separate right
from installing the font, and one a webfont-only licence usually withholds.

**WeasyPrint is not a fallback on this machine** — `error 0x7e` loading
`libgobject-2.0-0.dll`, a broken GTK3 runtime, not a WeasyPrint bug (retried
with GTK's `bin` on `PATH`, same result). It would embed CFF/OTF natively with
a real ToUnicode; re-try it first if GTK3 is ever repaired
(`report/research/pdf-toolchain-v2.md`, 2026-09-19).

```bash
node scripts/fetch-fonts.mjs              # refresh what is missing
node scripts/fetch-fonts.mjs --force      # re-download everything
node scripts/font-css.mjs                 # list the roster
```

`reference/families.md` says what to reach for and why, with the measurements
behind each recommendation.

## Choosing the face: ask once, then inherit

**The first document in a project needs a decision. Every one after it inherits
that decision without asking.** Ask as a short choice — two or three candidates
from `reference/families.md`, each with its copy-fidelity number — and
recommend one. Then write it down:

```bash
node scripts/house-style.mjs --set "Amiri,Literata" --note "client chose the naskh look"
node scripts/house-style.mjs                      # what does this project use?
```

That lands in `.pdf-typography.json` at the project root, and `render-pdf.mjs`
reads it on every build. The theme (colours, scale) inherits the same way —
from the last document's own template, not reinvented per build.

**Font or theme change requested: ask one question first — every document, or
only the new one?** Never guess; they're different amounts of work.

- *Every document* — rewrite with `--set`, then **re-render the existing
  documents too**. A house style changed for new work only leaves the set
  inconsistent, which is worse than either choice alone.
- *Only this one* — pass `fonts` to that single `renderPdf` call and leave
  `.pdf-typography.json` alone.

## Starting from a Word document

Much of the source material here is `.docx` — SRS documents, request forms,
ministry templates — and **pandoc is installed** (`pandoc 3.11`, on the user
PATH), so those are readable and convertible rather than opaque:

```bash
pandoc -f docx -t plain  "SRS - …docx"          # read one
pandoc -f docx -t markdown --wrap=none "…docx"  # structure, tables intact
pandoc -f docx -t html   "…docx" -o body.html   # entry point to the renderer
```

Arabic, RTL and table structure survive all three — verified on a real PROJ SRS.

**Convert to HTML, then render through this skill — never `pandoc -o out.pdf`.**
Pandoc's PDF writer goes through LaTeX, which knows nothing about the vault,
picks its own fonts, and produces exactly the silent substitution this skill
exists to prevent. Pandoc is the *reader*; the renderer below is the writer.

## Building a document

Use the renderer — it applies every rule below, each once a bug here before it
was a line of code.

```js
import { renderPdf } from '<skill>/scripts/render-pdf.mjs';

await renderPdf({
  html,                       // your document; it needs no @font-face of its own
  out: 'doc.pdf',
  // fonts omitted → the project's house style. Pass it only for a one-off.
  landscape: true,
  header: '<div style="width:100%;padding:0 16mm">معرّف الوثيقة</div>',
  footer: '<div style="width:100%;text-align:center">صفحة <span class="pageNumber"></span></div>',
});
```

```bash
node scripts/render-pdf.mjs page.html doc.pdf              # house style
node scripts/render-pdf.mjs page.html doc.pdf --fonts Amiri,Literata --landscape
```

It injects the faces as base64, binds them to the document, includes
`assets/print-base.css`, loads and **asserts** every family, gives the header
and footer templates their own copy of the face, and prints tagged. Playwright
is resolved from the project you run it in, since a global skill has no
`node_modules` of its own.

Writing the renderer by hand instead — because a pipeline already has one, say —
means carrying these four rules yourself, none of them optional:

- **`font-display: block`** on every face (`font-css.mjs` emits it). `swap` lets
  a print run race the fonts and snapshot a page set in the fallback.
- **`document.fonts.load()` each family, then `await document.fonts.ready`, then
  `document.fonts.check()` each family.** `ready` only promises that loading
  finished, not that it succeeded — and a face nothing on page 1 happens to use
  will not have started loading at all. Declaring a `@font-face` does not use
  it: bind it in CSS, or the vault sits unread in the document's head while
  Chrome prints in Arial. **`check()` itself can lie**: it answers for the
  whole fallback chain, not the declared family, so it read `true` for
  characters missing from that family's cmap. Confirm with the font list of
  the printed PDF, or a canvas pixel comparison against a nonexistent family —
  not `check()` alone (archived `design-gate` skill, `nj-plugin/_archive/design-gate/SKILL.md` § gate bugs, 2026-09-18).
- **`tagged: true`** on `page.pdf()`. Writes a structure tree — what Acrobat,
  Word and screen readers use to recover reading order; the accessibility
  floor, costs nothing. Not a general fix for bad copy, but not a no-op
  either: measured 2026-09-19, it's what puts a `ToUnicode` CMap onto Type-3
  glyphs (a CFF font Chrome can't embed natively, see The vault) and that
  alone fixed **English** extraction from an all-Type3 PDF. Arabic still
  extracts blank regardless — see cause 6 below
  (`report/research/pdf-toolchain-v2.md`).
- **`outline: true`** (`renderPdf({outline: true})`, added 2026-10-16) writes PDF
  bookmarks from the headings; needs `tagged`. Any document over ~100 pages
  takes it: the QA knowledge base shipped 384 pages with zero bookmarks because
  the renderer silently dropped the option. A toy PDF gave a 3-entry outline.
- **One family covering every character on the line**, or an explicit rule for
  the second script. When a font lacks a glyph Chrome splits the run and hands
  the pieces to another font, and split runs are where extraction order goes
  wrong. Families with both scripts in one file (Readex Pro; FF Amman if bought)
  remove the problem entirely.
- **Thmanyah has no arrows, maths signs or box drawing** (→ ≥ ≤ ≈ ² ₂ ─ │,
  measured 2026-10-15 on a 384-page English technical report). Chrome silently
  set them in Times New Roman and `check-pdf.py` failed on the system font.
  Substitute in the HTML before rendering (› or "to", >=, <=, ~, `<sup>`/`<sub>`,
  ASCII rules); never add a second family just for these.

## What actually makes text copy badly

Three separate causes. Only two are yours to fix, and conflating them wastes
days.

**1. The wrong font is embedded.** Fix it as above. This is nearly always the
real problem, and it is the one that is objectively wrong rather than a matter
of degree.

**2. The font's own glyph mapping displaces letters.** Measured on the same
sentence in nine families, agreeing across two independent engines (MuPDF and
PDFium):

| family | words intact | what breaks |
|---|---|---|
| Amiri | **11/11** | nothing |
| Almarai, Readex Pro, Tajawal | 10/11 | the lam-alef ligature (`لا`) puts its alef one slot out |
| Noto Sans Arabic, Noto Naskh Arabic | 1/11 | spurious spaces *inside* words — the letters are right, the run is chopped |
| **Cairo, IBM Plex Sans Arabic** | **8/11** | three words per sentence come out scrambled — `يشرح` → `يرشح`, `إلى` → `إىل` |

No CSS lever changes any of it: `font-variant-ligatures:none`,
`font-feature-settings` on `liga`/`clig`/`calt`, `font-kerning:none` and
`text-rendering:geometricPrecision` all score identically. The typeface is the
lever. **Do not set Arabic body text in Cairo or IBM Plex Sans Arabic** — and
note that IBM Plex Sans Arabic is what the PROJ manuals have been using.

**3. Bidi order, which is the reader's job and not a defect.** A PDF stores a
mixed line in *visual* order: `رقم الطلب 78202600026 ضمن…` comes back as
`… ضمن مديرية78202600026 رقم الطلب`. Every real viewer — Acrobat, Chrome's
viewer, Word — runs the Unicode bidi algorithm on copy and recovers it; crude
extractors do not. `<bdi dir="ltr">`, `dir` attributes and U+2066 isolates
change nothing about extraction (tested) — they matter for *rendering*, so
keep them. A trailing full stop moving to the front of the copied string is
the same artefact, in every font including Segoe UI.

**4. Words arriving whole but split.** Vocalised Arabic — `تُحمَّل`, `وتُضمَّن` —
extracts with breaks around the marks, and two table cells with no gap run
together as `رقم المرجعTQN-PDF-001`. Letters all there, in order.
`check-pdf.py` reports these as `~ intact but split by extraction` and passes
them — right call, nothing in the document causes it. Only *scrambled* fails
the build.

**5. Chrome writes RTL text in visual order, and there is no flag for it.**
Worth stating plainly — it looks like a bug someone introduced and is not.

Every PDF headless Chrome produces stores an Arabic line as the glyphs appear
left to right on the page. A reader that runs bidi on copy recovers the
sentence; one that doesn't hands back the line reversed. MuPDF recovers it.
**PDFium — Chrome's and Edge's built-in viewers — does not**, so pasting from
those gives «ةمدخلا ةقاطب». Measured across every variable available:

| changed | result |
|---|---|
| font (Amman / Almarai / Amiri / Segoe) | reversed in all four |
| tagged true / false | reversed in both |
| bdi isolation on / off | reversed in both |
| documents produced months before any of this work | **also reversed** |

The last row is the important one: it is not a regression. No CSS or
`page.pdf()` option changes it — the order is decided by HarfBuzz when the run
is shaped and Skia writes the glyphs in the order it's handed. A different
producer, one that writes logical order and positions glyphs (Word,
LibreOffice), would fix it — that's a rewrite, not a setting. Until then: say
so, and check copy with MuPDF (`check-pdf.py`) rather than a PDFium viewer —
MuPDF measures the document, PDFium measures the reader.

**6. Arabic extracts as blank, not reversed, when the font has no ToUnicode.**
Different from #5: a CFF font stuck as Type3 with `tagged: false` has no
character mapping at all, so Arabic comes back blank/dashes, not reversed.
English still extracts — Poppler recovers Latin glyphs 1:1 from the subsetted
font's retained `cmap`, which Arabic's shaped presentation-form glyphs are
absent from. `tagged: true` adds a ToUnicode and fixes English; Arabic stays
blank either way, unfixed by tagging (`report/research/pdf-toolchain-v2.md`,
2026-09-19). Hard requirement for exact Arabic copy-out: ship a plain-text/
Markdown companion file instead of chasing this further.

Do not chase 2, 3, 4, 5 or 6 into the ground. Fix 1, choose sensibly for 2, explain
the rest.

## What is in here

| | |
|---|---|
| `fonts/` | 18 open-licence families, 67 faces, as original `.ttf`. `MANIFEST.json` indexes them. |
| `fonts/licensed/` | drop-in slot for anything bought, with the licence question spelled out. |
| `assets/print-base.css` | what a page laid out for a screen gets wrong on paper: measure, repeating table headers, keep-together, real lists, logical directions. No colours, no type scale — those are the document's. |
| `scripts/fetch-fonts.mjs` | fills the vault. |
| `scripts/font-css.mjs` | families → base64 `@font-face` CSS. `node font-css.mjs` lists the roster. |
| `scripts/house-style.mjs` | the face this project settled on, in `.pdf-typography.json`. |
| `scripts/render-pdf.mjs` | HTML → PDF with every rule applied. |
| `scripts/rtl.mjs` | `bidi(text)` — wraps Latin phrases in `<bdi dir="ltr">` so a mixed line renders right. |
| `scripts/repair-tounicode.py` | makes the lam-alef ligature copy as itself. Run on the finished PDF, after any incremental save. |
| `scripts/check-pdf.py` | audits a finished PDF. Exit 1 on failure. |
| `scripts/copy-fidelity.mjs` + `.py` | measures a font before you adopt it. |
| `scripts/selftest.mjs` | proves the whole chain in one command. |
| `reference/families.md` | what to reach for, and why. |
| `reference/example.html` | a document that exercises all of it. |

## Prove the chain still works

```bash
node scripts/selftest.mjs          # renders the example, audits it, expects PASS
node scripts/selftest.mjs Cairo    # and this one must FAIL, on three words
```

Run it after touching anything here, and when a pipeline starts behaving oddly —
it separates "the skill is broken" from "this document is broken" in one step.
The second form is the point: a test that cannot fail proves nothing, and Cairo
is a font this vault knows to be bad.

## A template's relative paths resolve against the template

`url('fonts/AmmanV3Sans-300.ttf')` in a stylesheet at `templates/PROJ/x.html`
means `templates/PROJ/fonts/…` — not `templates/fonts/…`, where the fonts
actually live. That one level cost every manual built from that template its
typeface, silently. It hides well: a sibling template one directory up works
with the identical rule, so the path *looks* proven. **Check asset paths
whenever a template moves or a new one is added**, and confirm with the font
list of the PDF, not by eye.

## Nothing on a printed page may carry alpha

`opacity` on text, `rgba()` on a rule, a PNG with an alpha channel — any of
them makes Chrome composite the page as a transparency group, and **every
glyph on that page is then written as a Type 3 outline**: font list loses its
names, text layer written twice, selection behaves like a picture. Easy to
miss because the page looks perfect — three lines of `opacity` on a cover did
it once, a single `rgba()` hairline again, a transparent logo a third time.
Use solid colours mixed to the same value over their ground, and flatten
images onto the background they sit on; keep the cut-out version beside the
flattened one for grounds that are not flat.

## Never fake a weight with a stroke

`-webkit-text-stroke` looks like the obvious way to thicken a Light face with
no Regular. It destroys the PDF: Chrome stops emitting glyphs from the
embedded font and draws **Type 3 outlines** instead — unnamed fonts, doubled
text layer, picture-like selection. Measured on one document: extractable
text went from 26,986 characters to 51,359, and the audit lost every font
name. Same for `text-shadow` and anything else that forces Skia off the glyph
path. No Regular available: use size, colour and leading instead — half a
point larger, secondary text darkened. Not a fake stroke.

## Verify every PDF, every time

```bash
python scripts/check-pdf.py doc.pdf --expect "يشرح هذا الدليل كيفية تسجيل الدخول"
```

It lists every font in the file and flags any that is a system font, is not in
the vault, or is not embedded; reports whether the file is tagged; counts
unmapped characters; and checks that the words of each `--expect` phrase survive
extraction. Exit status 1 on any failure, so it can gate a build. Pass phrases
that are genuinely in the document — a phrase that is not there fails for the
wrong reason.

Run it on the output of every build. It is the only thing standing between a
silent fallback and a delivered document, and it takes a second.

## Definition of done

- [ ] The face came from the project's recorded house style, or — if there was
      none yet — from asking. A change to it was confirmed as *all documents* or
      *this one only* before anything was rewritten.
- [ ] Every font in the PDF is from the vault, embedded, and open-licence — `check-pdf.py` passes.
- [ ] `document.fonts.check()` was asserted in the build, not just `fonts.ready`.
- [ ] `tagged: true` was passed to `page.pdf()`.
- [ ] Arabic body text is not set in Cairo or IBM Plex Sans Arabic.
- [ ] The face came from `.pdf-typography.json`; no build passed `fonts:` inline.
- [ ] `repair-tounicode.py` ran on the finished file, after any `saveIncr`.
- [ ] Vowel marks and tatweel are stripped from generated Arabic.
- [ ] A phrase from the document was copied out and read back — by eye, once, not only by script.
- [ ] No commercial font was embedded without someone having read its embedding grant.

## The sheet is painted by `@page`, and by nothing else

A background on the root element or on `body` paints the page's **content
box**, not the sheet — on a document with a warm paper and a 16mm margin that's
a cream panel inside a pure-white frame, with a visible join on every sheet.
Client's words: «the padding is gold but the background is white, make it
seamless».

Six candidates printed and corners sampled (`ground-probe.mjs` pattern: paint a
loud colour, read the four corners of the raster). Only one reaches the margin:

| rule | corners |
|---|---|
| `html{background}` | white |
| `body{background}` | white |
| both | white |
| `position:fixed` box, `inset:0` | white |
| `position:fixed` box, negative insets | white |
| **`@page{background:…}`** | **painted** |

The propagation rule that would make the root's background cover the canvas
does not survive printing, and `printBackground: true` is not the missing
switch — it was already on for every row above.

Two things follow:

- **`@page` takes a literal, not a token.** There is no element in scope inside
  `@page`, so `var(--paper)` resolves to nothing and the declaration is dropped
  in silence. Read the colour from wherever the tokens come from and write it
  in.
- **Then take the background off `html` and `body`.** Painting it twice is
  invisible — same colour — but it draws two more full-height rectangles into
  every page, and anything measuring the page afterwards counts them as content.
  That is not hypothetical: it made a pagination check report a page holding
  four lines as 94% full, and the fix looked broken for an hour.

And where a coloured band is meant to reach the trim, **bleed it**. A box laid
out to the exact page width leaves a hairline of paper once the sheet is rounded
to points — 1.3mm of white down the edge of a navy spine, unmistakable against
the colour beside it. A box that overshoots cannot leave a gap, and the page
clips the overshoot, so the bleed costs nothing.

## Measure the face before you defend it

«It pastes gibberish» is three faults wearing one costume; only a measurement
separates them. Copy fidelity is **a property of the typeface**, and the vault
holds families that differ by a factor of two on the same sentence.

Measure with **three engines** — they disagree, and the disagreement is the
finding:

| engine | what it is | behaviour |
|---|---|---|
| poppler (`pdftotext`) | the strongest | applies bidi, emits embedding controls; closest to Acrobat and Word |
| MuPDF (PyMuPDF) | what most scripts see | reverses RTL runs |
| PDFium | Chrome's and Edge's viewers, and most lightweight PDF editors | reverses |

`tools/…/copy-fidelity.mjs` in the project does this on the document's own
sentences, which is the only specimen worth measuring — a pangram exercises none
of the constructs that break.

Three residual faults are the **document's**, not the font's, and all three are
fixable in the text:

- **Vowel marks do not survive extraction.** «يُتاح» comes back «ُيتاح» and
  «مقدّم» comes back «مق ّدم»: the mark is a separate glyph positioned over its
  letter, and every engine returns it where it was drawn. Modern technical
  Arabic is unvocalised, so **strip U+064B–U+0652** from generated text and the
  problem is gone. Hamza and madda seats (أ إ آ ئ ؤ) are letters, not marks —
  never touch those.
- **Tatweel** (U+0640) is a stretching character that arrives with pasted text.
  «الـخدمة» matches no search for «الخدمة». Strip it.
- **The lam-alef ligature** — its own section, below.

## Brackets: a pair is isolated together, or not at all

`bidi()` wraps Latin and numeric runs in `<bdi dir="ltr">` so they do not
reorder. An opening bracket immediately before such a run belongs **inside**
the isolate — «(SRS)» prints as «)SRS(» without it — but only when its partner
is in the isolate too. «سنوية (12 شهرًا)» put `(` inside the isolate around
`12` (drawn unmirrored) and left `)` outside in the Arabic run (bidi-neutral,
mirrors): both halves pointed the same way and the reader called it a typo.

Rule a proofreader would state: **a pair is set together or not at all.**
Closing bracket inside the run → pair is Latin, both halves in the isolate.
Pair straddling Arabic → both stay outside, mirror together, enclose the
phrase the way an Arabic paragraph encloses one.

## Typographic noise, and what a client means by it

«Remove the AI noise typemarks like long lines ــــ or any other type marks» is
specific and correct: the em dash is an **English** parenthetical device;
Arabic apposition takes a comma, and a dash on every second line reads as
machine-set. Convert a *spaced* dash only — «14–16» keeps its dash, a range
not an aside. Check the output, not the source: one SVG diagram's labels
escaped the tidy-up their own way and five em dashes survived on the page most
likely to be photographed. **Anything a reader sees goes through the same
function, whatever draws it.**


## Pagination: a page break is a decision about meaning, not about space

The print engine breaks where the box runs out. Left alone it will split a
heading from its first sentence, carry a table's introduction on one page and
the table on the next, and leave a single line of a section stranded at the top
of a fresh sheet. Every one of those reads as carelessness, and the reader
blames the document rather than the renderer.

The client's rule, stated once and applying to every document this project
produces:

1. **A topic does not start at the foot of a page.** If what fits under a
   heading is less than about half the topic's own content, the whole thing
   moves to the next page. A topic that then runs over several pages is fine —
   it is only the *start* that must not be stranded.
2. **A table and the text that introduces it stay together.** Splitting them
   leaves a table nobody can read and a sentence pointing at nothing.
3. **Never split a chart, a drawing or a diagram.** It goes whole onto a page,
   or onto a fold-out of its own.
4. **A section does not end in one or two stranded lines.** Where a page is
   otherwise full of one topic and a couple of lines are left over, break
   earlier and carry roughly half of the remainder across.

### The CSS mechanics and the two-print measurement pass

**Chromium honours almost none of the CSS you'd reach for first** — `orphans`,
`widows`, `break-after: avoid` moved **not one page break** on a thirty-page
document, measured by diffing every page before/after. What it does honour:
`break-inside: avoid` on a box that fits within a page. So pagination is
*grouping in the renderer*, not clever CSS:

```css
.keep { break-inside: avoid }           /* the only rule that does any work */
thead { display: table-header-group }   /* a long table repeats its header */
figure, .fig { break-inside: avoid }
body, p, li, td, dd { orphans: 3; widows: 3 }  /* costs nothing, other engines honour it */
```

Wrap a heading with the block beneath it in one `.keep`; wrap a lead-in with a
short table; for a *long* table (which can't be wrapped) use `<caption>` +
table instead — the caption travels with the table's first fragment. Only
group what actually fits a page — `break-inside: avoid` on a taller box is
silently ignored and reads as though it worked. Rule 4 (no stranded remnant)
can't be expressed declaratively at all; grouping fixes the faults anyone
reports and that's where it stops.

The full worked CSS, the print-measure-print loop (print, measure each sheet's
fill%, correct near-empty chapters and stub table tails, print once more and
stop), and the three measurement gotchas (exclude running head/folio, exclude
the `@page` background rectangle, count images) are in
`references/pagination.md` — open it when actually tuning breaks.

## Latin inside Arabic: isolate the run, not the word

In an RTL paragraph every neutral character — bracket, comma, full stop,
slash, apostrophe, quotation mark, digit sequence — takes its direction from
its neighbours. Get that wrong and it's **wrong**, not just ugly: «(SRS)»
prints as «)SRS(», «jpeg, jpg, png» prints as «jpg ,jpeg», «v1.2» reverses, a
date «4/8/2025» can come apart.

Fix: wrap each Latin/numeric **run** in `<bdi dir="ltr">`. Three details
decide whether it works:

- **The whole run, not each word.** Wrapping token by token leaves the
  separators outside the isolates, where they are still neutral — which is
  exactly how «jpeg, jpg» ends up reversed.
- **The opening bracket belongs inside.** A lone `(` in an Arabic run is
  neutral and mirrors; matching it as part of the Latin run keeps the pair
  together.
- **Escape per segment, not up front.** Escaping first turns `&` into `&amp;`,
  whose letters the pattern then matches and splits down the middle.

Brackets around *Arabic* need no isolation — they mirror correctly on their own,
and «( نص )» is right as it stands. It is only neutrals adjacent to Latin or
digits that go wrong.

**Apply it to every string that reaches the page, not just the obvious ones.**
The metadata fields get isolated early because they are visibly identifiers; the
bug survives in titles, headings and body prose, which is where a service name
carrying a `/` or a fee carrying a currency actually lives.

## The face is a recorded decision. Never pick one at the keyboard.

`.pdf-typography.json` at the project root is the only place a typeface is
chosen. `documents.<kind>` overrides `fonts` for one kind of document, and
`render-pdf.mjs` and every project renderer read it on every build.

**Never pass `fonts:` to a document build.** It is for one-off probes only — a
build that names a family inline has silently left the house style, exactly
how a set of documents ends up in three faces. To change the face, change the
record:

```bash
node scripts/house-style.mjs --set "Harmattan" --note "why"
```

…and then **re-render everything**, and say so. A house style changed for new
work only leaves the set inconsistent, which is worse than either choice alone.

A build that asserts the face it used is the safety net: `check-pdf.py` lists
every font in the PDF, and the project's own acceptance check compares that list
against the record. Wire both; a face that drifted is invisible by eye.

## Where a copy fault actually shows, and which half of it is yours

Two different faults arrive as one complaint and show up in different readers
— take the reader seriously: «the problem shines in a PDF editor like PDF Gear
or Acrobat, not so much on the Chrome or Edge webview» is diagnostic.

**Fault one: the letters are wrong.** «لاستكمال» comes back «الستكمال»,
«الوثيقة» comes back «ةقيثولا». Document's fault, caused by the typeface,
fixable — see the two sections below.

**Fault two: the words come back in reverse order along the line.** Every PDF
headless Chrome produces stores an RTL line in visual order. Chrome/Edge
viewers run bidi when they put the selection on the clipboard, so a paste out
of them reads correctly; a PDF *editor* shows the run as stored, reversed —
why an editor looks worse than the browser on the same file. This one is the
**producer's**, not the font's: no font, CSS or `page.pdf()` option changes
it — HarfBuzz decides the order when the run is shaped, Skia writes glyphs in
the order it's handed. Only a producer that writes logical order and positions
glyphs (Word, LibreOffice) fixes it. Say so plainly; the next font won't.

## The lam-alef ligature is the whole copy-fidelity gap

**One glyph carrying two characters cannot survive a reversed run.** An engine
that reverses an RTL run reverses the *glyphs* and keeps each glyph's
ToUnicode string intact, so a glyph mapped to «لا» lands with its own two
characters the wrong way round. That single fact explains the whole table:

| family | poppler | mupdf | pdfium | why |
|---|---|---|---|---|
| Amiri | 30 | 30 | 30 | no ligature glyph at all — lam and alef stay separate |
| Harmattan | 31 | 24 | 24 | one glyph, two characters |
| Scheherazade New | 30 | 24 | 24 | one glyph, two characters; the hamza forms unmapped |
| Ruwudu / Lateef / Rubik / Readex Pro | 30-31 | 24 | 24 | one glyph, two characters |
| Simplified Arabic | 31 | 24 | 13 | one glyph → a presentation form, plus whole-line reversal |
| Noto Naskh Arabic | 19 | 2 | 1 | spurious spaces inside words |

Things that do **not** fix it, all measured rather than assumed:

- `font-feature-settings` with `rlig`, `liga`, `clig` and `dlig` off. Lam-alef
  is a *required* ligature; the shaper applies it whatever the CSS says.
  Verified on four families — the ToUnicode came out identical.
- Rewriting the pair in reverse order. It helps the reversing engines and breaks
  poppler by the same amount: 8/3/3 → 5/6/6.

What does fix it is `scripts/repair-tounicode.py`, run on the finished PDF:
**map each lam-alef ligature glyph to the single Arabic Presentation Form
that means exactly that ligature** — U+FEFB, U+FEF7, U+FEF9, U+FEF5. One
glyph, one character, so reversal moves it as a unit and it lands in the
right slot. Renders as «لا» wherever pasted; NFKC folds it back to two
letters.

    as printed          poppler 8/8   mupdf 3/8   pdfium 3/8
    the pair reversed   poppler 5/8   mupdf 6/8   pdfium 6/8
    presentation form   poppler 8/8   mupdf 6/8   pdfium 6/8   ← costs nothing anywhere

Two things about finding the glyphs, both of which cost an hour:

- **Not by name.** `lam_alef.isol`, `uniFEFB`, `afii57721` and `gid412` are all
  in the wild.
- **Not from the embedded font.** Chrome's subsetter drops GSUB entirely and
  renames every glyph to `glyph00123`. What it keeps is the original glyph
  **numbering**, so the ligature ids are read from the font on disk in `fonts/`
  and used against the PDF; the face is matched on its PostScript name with the
  subset prefix and separators stripped.

Run it after any incremental save (`saveIncr`), never before — an incremental
save appended afterwards leaves the old CMap in the file ahead of the new one.

## A tinted block is a band of the page, not a card on it

A panel inset from the measure has four visible edges and reads as pasted on
afterwards. Client's words: «keep the light gold bg for the fields, but don't
make it like a sticker on the page — make it the page».

Carry the tint out to the trim and it reads as the sheet itself changing
colour for the length of a topic — a banded document:

```css
:root{ --page-side:16mm }                    /* the same number @page uses */
.band{
  margin-inline: calc(0mm - var(--page-side));
  padding-inline: var(--page-side);          /* text stays on the measure */
  border-top: 2px solid var(--accent);       /* not a leading-edge rule */
}
```

Two details that matter:

- **State the side margin once.** The bleed is that margin negated, and two
  numbers that must be equal should never be written twice — a change to the
  measure otherwise leaves bands stopping short of the trim or running past it.
- **Move any accent rule from the leading edge to the top.** On a full-bleed
  band a vertical rule sits in the trim, where a binder or a guillotine takes
  it.

The same rule applies inside figures: a label knocked out in white on a tinted
lane is a white sticker on a coloured page. Knock out in the colour the label is
standing on.

## A negative margin widens the page, and an RTL document slides left

A full-bleed band needs `margin-inline: -16mm`. But a negative margin does not
merely move a box — it makes it **wider than its container**, and Chrome
widens the whole document's layout box in response. In an RTL document the
extra width is added at the reading edge, so every page slides away from it.

Measured on a 209.9mm page: the sheet's own ground came out **228.9mm** wide,
text block at 4.8..178.3mm instead of 16..194mm. Client saw it as «the pages
are shifted to the left». Two boxes were doing it — a cover's bleeding spine
and the bands in one chapter — contributing independently, so removing one
left the fault looking half-fixed. Clipping the overflow is not the fix: what
overflows *is* the bleed.

**Put the measure on a wrapper and give the page no side margin at all.**

```css
@page { size: A4 portrait; margin: 18mm 0 16mm }   /* no side margin */
.wrap { padding-inline: var(--page-side) }          /* the measure lives here */
.band { margin-inline: calc(0mm - var(--page-side)); padding-inline: var(--page-side) }
```

A band then bleeds to the wrapper's own edge, which is the trim, and nothing is
ever wider than the sheet. The running head and footer are unaffected: Chrome
draws them in the page's margin box and they carry their own padding.

For a full-bleed element that is *not* in the flow — a cover's spine — give its
container `overflow: hidden`. The container is exactly page-sized, so the bleed
is clipped by the page rather than allowed to widen it.

**Check it with a number, not by eye.** Extract the page's own background
rectangle and compare its width to the page's: if they differ, something
overflows, and no amount of squinting at a raster will show you which page it
started on.

## One family in the vault is a design decision, not a tidy-up

A vault of twenty-six families is a menu, and a menu is how a document set
ends up in three faces. Where a client has settled on one, prune to it: one
roster entry, one index entry, and a build that reaches for anything else
fails at the last step instead of silently falling back. Two rules make the
pruning safe:

- **Recycle, never destroy.** The families come back from the bin, and the
  Google-served ones also come back with one command. A licensed drop-in that
  somebody bought does not — say where it went.
- **The index must drop what the vault dropped.** A merge that only ever adds
  leaves `font-css.mjs` offering a face that is no longer on disk, and the build
  fails with «not in the vault» about a family the index says it has. Keep a
  previous entry only if its files still exist.

## Cairo, measured

Recorded here because it is a face clients ask for by name, and because the
number is not what anyone expects of the most widely used Arabic UI sans in the
region:

| engine | Cairo | Harmattan (for scale) |
|---|---|---|
| poppler — Acrobat, Word | 10/11 | 10/11 |
| MuPDF | **3/11** | 8/11 |
| PDFium — Chrome, Edge, most PDF editors | **1/11** | 8/11 |

Cairo returns «على» as «عىل» and «تغيير» as «تغيري». It is **not repairable**:
the fault is the order Chrome writes the glyphs in for this face, not the
ToUnicode map, so `repair-tounicode.py` finds nothing to fix. Normalising its
presentation forms — it maps 55 glyphs to them — changes nothing either;
measured, both before and after.

So: copying out of Acrobat or Word is fine, and out of a PDFium-based viewer or
editor it is not. If a client chooses Cairo anyway, that is their call — record
the numbers beside the choice so nobody is surprised by it later, and say plainly
what the one command to revert is.

Working in the PROJ repo? Open `references/PROJ-house-rules.md` — one client's type scale, page-size and figure rules, not a portable part of this skill.
