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
no console error, no thrown promise. It substitutes a system font, prints a page
that looks nearly right, and embeds that substitute in the PDF.

That is measured, not theorised:

```
setContent + file://   →  every family FALLBACK
setContent + data:     →  every family loaded
goto('file:///…')      →  every family loaded
```

It is also how the PROJ SRS came to ship 31 pages set in **Segoe UI** while its
stylesheet asked for IBM Plex Sans Arabic. Two consequences, both bad: the
document was never in the typeface anyone chose, and it embeds a Microsoft font
in a file handed to a ministry, which a Windows licence does not cover.

So: **fonts are delivered as base64 `data:` URIs**, always. It is the only form
that survives `setContent`, and the only one that reaches Chrome's header and
footer templates, which are rendered as separate documents with no access to the
page's stylesheet. (A `@font-face` inside the footer template's own `<style>`
does work — verified — as long as it is a `data:` URI.)

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

Every family is SIL OFL 1.1 or Apache 2.0. This is not pedantry: a PDF *embeds*
the glyphs it draws with, so shipping the document redistributes the typeface.
Anything commercial goes in `fonts/licensed/` by hand, after someone has read
the licence and confirmed it grants **document embedding** — a separate right
from installing the font, and one a webfont-only licence usually withholds.

```bash
node scripts/fetch-fonts.mjs              # refresh what is missing
node scripts/fetch-fonts.mjs --force      # re-download everything
node scripts/font-css.mjs                 # list the roster
```

`reference/families.md` says what to reach for and why, with the measurements
behind each recommendation.

## Choosing the face: ask once, then inherit

**The first document in a project needs a decision. Every one after it inherits
that decision without asking.**

Ask it as a short choice, not an open question: two or three candidates from
`reference/families.md`, what each looks like, and each one's copy-fidelity
number so the trade-off is visible. Recommend one.

Then write it down, because a rule kept in someone's head lasts one session:

```bash
node scripts/house-style.mjs --set "Amiri,Literata" --note "client chose the naskh look"
node scripts/house-style.mjs                      # what does this project use?
```

That lands in `.pdf-typography.json` at the project root, and `render-pdf.mjs`
reads it on every build. The theme — the document's own colours and scale — is
inherited the same way: from the template or stylesheet the last document used,
not reinvented per build.

**When the user asks to change the font or the theme, ask one question before
touching anything: does this apply to every document, or only the new one?**

- *Every document* — rewrite the record with `--set`, then **re-render the
  existing documents too**. Say so plainly: a house style changed for new work
  only leaves the set inconsistent, which is worse than either choice alone.
- *Only this one* — pass `fonts` to that single `renderPdf` call and leave
  `.pdf-typography.json` alone. The next document goes back to the house style.

Never guess between those two. They are different amounts of work and only the
user knows which they meant.

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
Pandoc's own PDF writer goes through LaTeX, which knows nothing about the vault,
picks its own fonts, and produces exactly the silent substitution this whole
skill exists to prevent. Pandoc is the *reader*; the renderer below is the
writer.

## Building a document

Use the renderer. It applies every rule below already, and each of them was a
bug in this project before it was a line of code.

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
  not `check()` alone (`design-gate` SKILL.md § gate bugs, 2026-09-18).
- **`tagged: true`** on `page.pdf()`. It writes a structure tree, which is what
  Acrobat, Word and screen readers use to recover reading order. It does not
  change what a crude extractor sees, so it is not a fix for bad copy — it is
  the accessibility floor, and it costs nothing.
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
mixed line in *visual* order: `رقم الطلب 1234567890 ضمن…` comes back as
`… ضمن مديرية1234567890 رقم الطلب`. Every real viewer — Acrobat, Chrome's
viewer, Word — runs the Unicode bidi algorithm on copy and recovers it. Crude
extractors do not. `<bdi dir="ltr">`, `dir` attributes and U+2066 isolates were
all tested and change nothing about extraction (they matter for *rendering*, so
keep them). The trailing full stop of an Arabic paragraph moving to the front of
the copied string is the same artefact, in every font including Segoe UI.

**4. Words arriving whole but split.** Vocalised Arabic — `تُحمَّل`, `وتُضمَّن` —
extracts with breaks around the marks, and two table cells with no gap between
them run together as `رقم المرجعTQN-PDF-001`. The letters are all there, in
order. `check-pdf.py` reports these as `~ intact but split by extraction` and
passes them, which is the right call: no viewer shows it and nothing in the
document causes it. Only *scrambled* fails the build.

**5. Chrome writes RTL text in visual order, and there is no flag for it.** This
is the big one, and worth stating plainly because it looks like a bug somebody
introduced and is not.

Every PDF headless Chrome produces stores an Arabic line as the glyphs appear
left to right on the page. A reader that runs the Unicode bidi algorithm on copy
recovers the sentence; one that does not hands back the line reversed. MuPDF
recovers it. **PDFium — which is what Chrome's and Edge's built-in viewers copy
with — does not**, so pasting from those gives «ةمدخلا ةقاطب».

Measured across every variable available:

| changed | result |
|---|---|
| font (Amman / Almarai / Amiri / Segoe) | reversed in all four |
| tagged true / false | reversed in both |
| bdi isolation on / off | reversed in both |
| documents produced months before any of this work | **also reversed** |

The last row is the important one: it is not a regression. And no CSS or
page.pdf() option changes it, because the order is decided by HarfBuzz when the
run is shaped and Skia writes the glyphs in the order it is handed.

What would fix it is a different producer — one that writes the string in
logical order and positions the glyphs, which is what Word and LibreOffice do.
That is a rewrite of the renderer, not a setting. Until then: say so, and check
copy with MuPDF (check-pdf.py) rather than with a PDFium viewer — MuPDF measures
the document, PDFium measures the reader.

Do not chase 2, 3, 4 or 5 into the ground. Fix 1, choose sensibly for 2, explain
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
typeface: the face never loaded, Chrome fell back, and nothing said so.

It hides well because a sibling template one directory up works perfectly with
the identical rule, so the path *looks* proven. **Check asset paths whenever a
template moves or a new one is added**, and confirm with the font list of the
PDF rather than by eye — a fallback that reads acceptably is the failure mode.

## Nothing on a printed page may carry alpha

`opacity` on text, `rgba()` on a rule, a PNG with an alpha channel — any of them
makes Chrome composite the page as a transparency group, and **every glyph on
that page is then written as a Type 3 outline**. The font list loses its names,
the text layer is written twice, and selection behaves like a picture.

It is easy to miss because the page looks perfect. Three lines of `opacity` on a
cover did it once; a single `rgba()` hairline did it again; a transparent logo
did it a third time.

Use solid colours mixed to the same value over their ground, and flatten images
onto the background they sit on. Keep the cut-out version beside the flattened
one for grounds that are not flat.

## Never fake a weight with a stroke

-webkit-text-stroke looks like the obvious way to thicken a Light face that has
no Regular. It destroys the PDF.

Chrome stops emitting glyphs from the embedded font and draws them as **Type 3
outlines**: unnamed fonts in the font list, the text layer written twice, and
selection that behaves like a picture. Measured on one document — extractable
text went from 26,986 characters to 51,359, and the audit lost every font name.

The same applies to text-shadow and anything else that forces Skia off the glyph
path. When a family has no Regular, the answers are size, colour and leading:
half a point larger, secondary text darkened. Not a fake stroke.

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
box**. On a document with a warm paper and a 16mm margin that is a cream panel
inside a pure-white frame, with a visible join on every sheet — the client's
words were «the padding is gold but the background is white, make it seamless».

Six candidates were printed and their corners sampled
(`ground-probe.mjs` pattern: paint a loud colour, read the four corners of the
raster). Only one reaches the margin:

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

«It pastes gibberish» is three faults wearing one costume, and only a
measurement separates them. Copy fidelity is **a property of the typeface**, and
the vault holds families that differ by a factor of two on the same sentence.

Measure with **three engines**, because they disagree and the disagreement is
the finding:

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
reorder. An opening bracket immediately before such a run belongs **inside** the
isolate — «(SRS)» prints as «)SRS(» without it.

But only when its partner is in the isolate too. «سنوية (12 شهرًا)» put `(`
inside the isolate around `12`, where it is drawn unmirrored, and left `)`
outside in the Arabic run, where it is bidi-neutral and mirrors. Both halves
came out pointing the same way and the reader called it a typo.

The rule is the one a proofreader would state: **a pair is set together or not
at all.** Closing bracket inside the run → the pair is Latin, both halves go in
the isolate. Pair straddling Arabic → both halves stay outside, mirror together,
and enclose the phrase the way an Arabic paragraph encloses one.

## Typographic noise, and what a client means by it

«Remove the AI noise typemarks like long lines ــــ or any other type marks» is
a specific and correct complaint. The em dash is an **English** parenthetical
device; Arabic apposition takes a comma, and a document with a dash on every
second line reads as machine-set.

Convert a *spaced* dash only — «14–16» keeps its dash, because there it is a
range and not an aside. Then check the output, not the source: the one place
text reached paper without passing through the tidy-up was an SVG diagram's
labels, which escaped their own way, so five em dashes survived on the one page
most likely to be photographed. **Anything a reader sees goes through the same
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

### How that becomes CSS

**Chromium honours almost none of the CSS you would reach for first.** Measured,
not assumed: `orphans`, `widows` and `break-after: avoid` on headings were all
added to a thirty-page document and moved **not one page break** — verified by
diffing the first line of every page before and after. Do not spend time tuning
them.

What Chromium does honour is **`break-inside: avoid` on a box that fits within a
page**. So pagination is done by *grouping in the renderer*, not by asking CSS
to be clever:

```css
.keep { break-inside: avoid }           /* the only rule that does any work */
thead { display: table-header-group }   /* a long table repeats its header */
figure, .fig { break-inside: avoid }

/* Kept because other engines honour them and they cost nothing.
   Nothing here relies on them. */
body, p, li, td, dd { orphans: 3; widows: 3 }
```

and in the code that emits the HTML:

- **A heading is wrapped with the block beneath it** in one `.keep`.
  Concatenating them is not enough — they must sit inside one box the engine
  will not split.
- **A lead-in and a short table are wrapped together** in one `.keep`.
- **A lead-in and a *long* table become `<caption>` + table.** A long table
  cannot be wrapped, but a caption is part of the table box and travels with its
  first fragment — so the two can never be separated however far the table runs.
  This is the only mechanism that works for long tables.

**Only group what fits.** `break-inside: avoid` on a box taller than a page
cannot be honoured, so the engine ignores it and breaks anywhere — worse than
not asking, because the rule reads as though it is working. Gate grouping on a
size proxy the renderer can measure: row count for tables, paragraph count for
prose.

**`break-inside: avoid` on something taller than a page is a trap.** The engine
cannot honour it, so it silently ignores it and breaks anywhere — which is worse
than not asking, because the rule reads as though it is doing something. Group
only what genuinely fits: a heading with its first paragraph, a table with its
lead-in, a figure with its caption. Never a whole chapter.

**Rule 4 is the one nothing can express.** Chromium ignores `orphans`/`widows`,
so a two-line remnant cannot be prevented declaratively — it would need a
measuring pass that lays the document out and re-flows it. Grouping removes the
faults anyone actually reports: a lone heading, a divorced table, a split
figure. Stop there. If one section still lands badly, give it `break-before:
page` and say why in a comment.

**Grouping costs pages, and that is the trade.** Keeping topics whole grew this
project's documents by about one page in thirty. A page that ends early because
the next topic would not fit is the intended outcome, not a regression.

**Check it by looking.** Rasterise the built PDF and read the page boundaries —
`page N ends with …` / `page N+1 begins with …`. A pagination bug is invisible
in the HTML and obvious in the render, and it is the single most common reason a
document that passes every automated check still looks wrong to a client.

### CSS cannot balance a page. Print it, measure it, print it again.

Everything above holds a topic together. What it cannot do is notice that the
result wasted a sheet — «point 2.16 is in its own page, add the next point under
it, no need for a full page for one line». That fault only exists *after*
pagination, and the HTML has no pages in it.

So the document is printed **twice**: the first print is the measurement, not a
draft.

1. Print. Measure each sheet: how much of the text area it uses, its first line,
   whether it is a named landscape page.
2. Two corrections, both the client's own rules stated literally:
   - a chapter standing immediately behind a nearly-empty sheet (< 40% used)
     gives up its forced page break and carries on down that sheet;
   - a long table whose last page is a stub gets a break inserted earlier, so
     its last two pages come out roughly equal. A table is the case CSS cannot
     touch at all: `break-inside` on the whole thing is ignored because it does
     not fit, and Chromium's `orphans`/`widows` do not apply to rows. Two
     tables with `break-before:page` on the second is the mechanism —
     `break-before` on a `tbody` is ignored.
3. Print again, with those two changes. **Then stop.** A chapter moving up can
   strand a different page, and chasing that oscillates.

When the first print has nothing to correct, it *is* the deliverable and the
second print never happens.

Three things the measurement has to get right, each of which produced a
convincingly wrong answer first:

- **Exclude the running head and folio by position.** Chrome prints them into
  the page margin, so every page otherwise "ends" with its page number and
  "begins" with the document id — which makes every seam look like a one-line
  remnant and hides the real ones.
- **Exclude the sheet's own background rectangle.** With `@page{background}` and
  a background on the root, three full-page rects are painted on every sheet,
  and counting them reports a page holding four lines as 94% full.
- **Count images and vector art**, not just text. A page holding one screenshot
  is full.

## Latin inside Arabic: isolate the run, not the word

In an RTL paragraph every neutral character — bracket, comma, full stop, slash,
apostrophe, quotation mark, and any digit sequence — takes its direction from
its neighbours. Get that wrong and the text is not merely ugly, it is **wrong**:
«(SRS)» prints as «)SRS(», «jpeg, jpg, png» prints as «jpg ,jpeg», a version
«v1.2» reverses, and a date «4/8/2025» can come apart.

The fix is to wrap each Latin/numeric **run** in `<bdi dir="ltr">`, and three
details decide whether it works:

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

**Never pass `fonts:` to a document build.** It is for one-off probes —
specimens, copy-fidelity runs — and a build that names a family inline is a
build that has silently left the house style, which is exactly how a set of
documents ends up in three faces. If the face should change, change the record:

```bash
node scripts/house-style.mjs --set "Harmattan" --note "why"
```

…and then **re-render everything**, and say so. A house style changed for new
work only leaves the set inconsistent, which is worse than either choice alone.

A build that asserts the face it used is the safety net: `check-pdf.py` lists
every font in the PDF, and the project's own acceptance check compares that list
against the record. Wire both; a face that drifted is invisible by eye.

## Where a copy fault actually shows, and which half of it is yours

Two different faults arrive as one complaint, and they show up in different
readers. Take the reader seriously — the client's own observation was that «the
problem shines in a PDF editor like PDF Gear or Acrobat, not so much on the
Chrome or Edge webview», and that is diagnostic.

**Fault one: the letters are wrong.** «لاستكمال» comes back «الستكمال»,
«الوثيقة» comes back «ةقيثولا». This is the document's, it is caused by the
typeface, and it is fixable — see the two sections below.

**Fault two: the words come back in reverse order along the line.** Every PDF
headless Chrome produces stores an RTL line in visual order. Chrome's and Edge's
viewers run the bidi algorithm when they put the selection on the clipboard, so
a paste out of them reads correctly. A PDF *editor* shows the run as stored, so
it shows the line reversed — which is why an editor looks worse than the browser
on the same file.

That one is the **producer's**, not the font's, and no font, no CSS and no
`page.pdf()` option changes it: the order is decided by HarfBuzz when the run is
shaped and Skia writes the glyphs in the order it is handed. What would fix it
is a producer that writes the string in logical order and positions the glyphs,
which is what Word and LibreOffice do. Say so plainly rather than letting a
client believe the next font will fix it.

## The lam-alef ligature is the whole copy-fidelity gap

**One glyph carrying two characters cannot survive a reversed run.** An engine
that reverses an RTL run reverses the *glyphs* and keeps each glyph's ToUnicode
string intact, so a glyph mapped to «لا» lands with its own two characters the
wrong way round.

That single fact explains the whole table:

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
**map each lam-alef ligature glyph to the single Arabic Presentation Form that
means exactly that ligature** — U+FEFB, U+FEF7, U+FEF9, U+FEF5. One glyph, one
character, so the reversal moves it as a unit and it lands in the right slot. It
renders as «لا» wherever it is pasted and NFKC folds it back to two letters.

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

A panel inset from the measure has four visible edges and reads as something
pasted on afterwards. The client's words: «keep the light gold bg for the fields,
but don't make it like a sticker on the page — make it the page».

Carry the tint out to the trim and it reads as the sheet itself changing colour
for the length of a topic, which is what a banded document does:

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
merely move a box — it makes it **wider than its container**, and Chrome answers
that by widening the whole document's layout box. In an RTL document the extra
width is added at the reading edge, so every page slides away from it.

Measured on a 209.9mm page: the sheet's own ground came out **228.9mm** wide and
the text block sat at 4.8..178.3mm instead of 16..194mm. The client saw it as
«the pages are shifted to the left». Two boxes were doing it — a cover's
bleeding spine, and the bands in one chapter — and each contributed
independently, so removing one left the fault looking half-fixed.

Clipping the overflow is not the fix: what overflows *is* the bleed.

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

A vault of twenty-six families is a menu, and a menu is how a document set ends
up in three faces. Where a client has settled on one, prune to it: the roster
becomes one entry, the index lists one family, and a build that reaches for
anything else fails at the last step instead of silently falling back.

Two rules make the pruning safe:

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

---

# The PROJ house rules

These are this client's, recorded here because every document the project
produces has to match and because a rule kept in someone's head lasts one
session. Another project sets its own; the *shape* of these is the reusable
part.

## The typeface is recorded, and there is only one

`.pdf-typography.json` → `fonts: ["Cairo"]`, no per-document override, and the
vault holds nothing else. A build that names a family inline has silently left
the house style, which is how a set of documents ends up in three faces — so
**never pass `fonts:` to a document build**. It is for specimens and
copy-fidelity probes only.

Wire two assertions and the rule holds itself up: `check-pdf.py` lists every
font in the PDF, and the project's acceptance check compares that list against
the record.

## The client's type scale, asserted on the printed file

A client who has a house style will give it to you as sizes, not as tokens:

| what | size | weight |
| --- | --- | --- |
| document title | 24 | Bold |
| Heading 1 | 18 | Bold |
| Heading 2 / 3 | 14–16 | Bold |
| body text | 14 | Regular |
| tables and screens | 12 or 14 | — |

Declare them once as custom properties and read them everywhere. Then **assert
them on the PDF, not on the stylesheet** — a token can say 14pt while a rule
three hundred lines down overrides it, and only the printed file knows which
won. Read the sizes off the spans and fail on any that is not in the set.

Allow, and name, the sizes that are deliberately below the standard: captions
and control-table labels at 10pt, running head and folio at 9pt. Everything a
reader reads as prose is on the list.

## A figure is proved clean, never eyeballed clean

Two gates, both hard:

1. **No collisions.** The generator declares the box it drew for every shape,
   label and connector, and every arrow declares its path and endpoints; a
   checker reads those back and reports overlaps, arrows through unrelated
   nodes, and anything outside the frame. Exit 1 on any fault.
2. **No illegible type.** Below **7pt** a printed flowchart stops being one. The
   build reports the size the labels will print at; do not ship past it.

Deriving the boxes by parsing the SVG back is a second implementation of the
same geometry, and the two disagree the first time either changes. The generator
is the only thing that knows where it put something, so it is the thing that
says so.

**Place labels last, against everything already drawn.** A label is the only
movable thing on a figure — a node's position states who does the work, a
connector's states where the flow resumes — so nudge it across its own edge,
nearest offset first. Tuning constants until nothing overlaps produced four
rounds of whack-a-mole here: six faults, then four, then nine.

**Grow a connector out of the line, do not lay it on top.** An arrow with a
circle painted over its end is two objects competing for one spot. One stroke
that runs to the ring, parts into two half-circles, and carries on cannot
collide with itself.

## Fixing the page size is a content decision, not a layout one

> **The PROJ client reversed this on 2026-09-04**, and the reversal is as
> instructive as the rule: «one page, one continuous workflow, with every
> decision or button available at each stage, no shortcuts» won over the A4
> constraint, and the sheet became A2 or A1 again. The arithmetic below is what
> made the conflict visible in the first place — keep it.

«Limit it to A4 landscape» is a legitimate and common instruction, and it is not
a tuning parameter. **A4 landscape has a fifth of A2's drawing area, and type
size scales with the square root of area** — so a figure that reads at 8.3pt on
A2 reads at 3.7pt on A4, and no arrangement recovers that. Measured here across
thirty combinations of column count and column width: the best any of them
reached was 4.0pt.

The three real levers, in the order they should be tried:

1. **Carry less.** Take out of the figure what is already in the text beside it.
   A box listing a desk's whole action bar is eight lines tall; the same
   captions are in that desk's table, where a developer reads them anyway.
2. **Say less per stage.** One gateway carrying both its exits instead of two
   consecutive gateways halves the columns a desk costs.
3. **One band per sheet.** A banded pool is already a chart continued, with
   connectors joining the bands. Giving each band its own page is the same idea
   one level up and is how long pools have always been printed — and it is the
   lever that buys back the area the page size took away.

Shrinking the type is not on the list.

---

## A ring on a line owns clearance at both ends, measured on paper

A jump marker — the lettered circle that says «the flow resumes where this
letter appears again» — is usually drawn as a circle painted over the end of an
arrow. That is two objects competing for one spot: the circle covers the
arrowhead, the arrowhead pokes out of the circle, and every fix moves the
collision rather than removing it.

Draw it as **one stroke in the connector's own colour**: a leg in, the ring, a
leg out carrying the arrowhead. Then let the ordinary arrow attach at the *far
end of a leg*. If the leg is long enough, the ordinary arrow can never reach the
ring however the layout moves — the clearance is structural instead of tuned.

Three things make it hold:

- **Specify the leg in millimetres on the printed sheet, and check it there.** A
  leg long enough in the drawing and short on the page is a leg that failed. Have
  the generator record the leg it drew (`data-leg`, in viewBox units) and have
  the checker convert it through the sheet the figure actually prints on.
- **Solve the width, the legs and the gutters together.** A leg's length in
  drawing units depends on millimetres per unit, which depends on the figure's
  width, which depends on the gutters, which have to hold a leg. Two passes of
  the fixed point settle it; a third changes nothing. A gutter derived from what
  goes in it cannot be too small — one chosen by eye always eventually is.
- **The obstacle is the whole assembly, not the ring.** Clearance that labels may
  be placed on is not clearance.

And: **a marker belongs to the node it serves, not to the one it left.** In a
banded or paged figure, the receiving half of a jump belongs with its target. Get
that wrong and it draws on a part of the figure that does not contain it — which
a collision check catches and no eye does.

## When two client rules contradict, the newer one wins and you say so

«Limit it to A4 landscape» and «one page, one continuous workflow, with every
decision or button available at each stage, no shortcuts» cannot both hold: the
second puts eight lines of text in every box, and A4 landscape has a fifth of
A2's drawing area.

Take the newer rule, implement it fully, and **say plainly in the report which
older instruction it displaced and what that cost** — here, two of eight
documents now take an A1 fold-out. Do not quietly average the two into something
that satisfies neither, and do not ship the older rule with type nobody can read
in order to look obedient.

Keep the superseded rule visible in the skill, marked as superseded, with the
measurement that settled it. The next person needs to know it was considered,
not that it was never asked for.

---

## Two corrections worth carrying, both from the same afternoon

**A clearance is as long as it needs to be, not as long as it sounds.** «2cm»
was asked for and «2mm» was meant: the leg's job is to stop two strokes meeting
at a tangent, and two millimetres does that. Two centimetres did it too, and ate
a fifth of the figure's width — width the labels needed, on a page size that had
none to spare. When a client gives a number for a clearance, check what it costs
before implementing it, and say what it costs.

**A checker that silently stops checking is worse than no checker.** A collision
check keyed on `data-el="conn"` immediately followed by `data-box`. A connector
gained a `data-leg` attribute between them, the regex stopped matching
connectors, and the checker reported a figure with three rings drawn across three
nodes as clean — every gate green.

- **Match tolerantly**: allow any attributes between the ones you key on.
- **Print the counts** — boxes and edges found per figure. A count that drops
  when nothing was removed is the checker losing sight of something, and it is
  the only signal that a check has gone blind. Here it was 44 boxes where there
  should have been 58.
- **Never take a green check as proof on its own.** Rasterise the output and
  read it. The check that passed was blind to the connectors, and the *other*
  defect on the same page — text spilling out of every diamond — was something
  no collision check was ever going to catch.

## Size shapes from the column, not with a fixed inset

`BOX_W = COL_W - 52` is right for the 200-unit column it was written against and
nonsense for a 90-unit one: the diamond came out 28 units wide, its text wrapped
at the eight-character floor, and every label hung out of both sides of its
shape. Use proportions — and remember that **a diamond needs more width than a
rectangle for the same words**, because it tapers to a point above and below.
Its height is about 1.7 times its text block, not its text plus padding.
