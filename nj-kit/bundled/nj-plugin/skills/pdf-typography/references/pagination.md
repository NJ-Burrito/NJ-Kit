# Pagination: the CSS mechanics and the two-print measurement pass

Referenced from pdf-typography SKILL.md § Pagination. Open this when actually tuning page breaks — the top-level rule (a page break is a decision about meaning) lives in SKILL.md; this is the worked CSS and the print-measure-print loop.

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

