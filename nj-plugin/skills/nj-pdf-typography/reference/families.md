# What to set it in

Eighteen families, all open licence, all in `fonts/`. This is what each is for.

## Arabic

| family | use it for | copy fidelity |
|---|---|---|
| **Amiri** | body text in anything formal — reports, SRS documents, official correspondence. Classical Naskh, the look of a printed Arabic book. Has true italics, which almost no Arabic face does. | **perfect** |
| **Readex Pro** | UI-flavoured documents where Arabic and Latin share a line. Arabic *and* Latin in one file, so mixed runs never split across two fonts. | good — lam-alef only |
| **Almarai** | compact sans; sets tighter than Cairo at the same size, useful in dense tables. | good — lam-alef only |
| **Tajawal** | geometric sans, very common in Jordanian and Gulf government work; reads as modern-official. | good — lam-alef only |
| **Noto Sans Arabic** | fallback of last resort. Widest coverage of any Arabic sans: every mark, every Quranic sign, every rare letter. | poor — extractors chop words |
| **Noto Naskh Arabic** | as above, in Naskh. | poor — extractors chop words |
| **Cairo** | headings and display only. | **bad — scrambles words** |
| **IBM Plex Sans Arabic** | headings and display only. Matches IBM Plex Sans/Serif/Mono in Latin, which is its one real advantage. | **bad — scrambles words** |

The measurements are in `SKILL.md`. The short version: Cairo and IBM Plex Sans
Arabic displace letters *within* words when text is extracted, reproducibly, in
two independent engines. That is invisible on the page and obvious the moment
somebody pastes a paragraph into an email.

## Latin

| family | use it for |
|---|---|
| **Inter** | the default UI sans. Tabular figures via `font-feature-settings:'tnum'`. |
| **Literata** | reading serif with real character — sturdy, large x-height, true italics. The distinctive choice when a document should not look like every other document. |
| **Source Serif 4** | the workhorse text serif, when Literata is too much personality. |
| **IBM Plex Serif** | slab-ish serif; the Latin partner to IBM Plex Sans Arabic. |
| **IBM Plex Sans** | Latin partner to IBM Plex Sans Arabic — same skeleton, same metrics. |
| **Source Sans 3** | neutral humanist sans; the quiet alternative to Inter. |
| **Roboto**, **Open Sans** | here so that a house style asking for them can be satisfied. |
| **IBM Plex Mono**, **JetBrains Mono** | code, identifiers, request numbers. JetBrains has the taller x-height and survives small table cells better. |

## Pairings that work

- **Amiri + Literata** — formal Arabic report with English alongside. Two
  serious book faces of similar weight and colour; neither defers to the other.
- **Readex Pro alone** — bilingual UI-style document. One family, both scripts,
  no fallback, no split runs. The safest thing to build a mixed document out of.
- **Almarai + Inter** — dense tabular material, screens-to-print.
- **IBM Plex Sans Arabic (headings) + Amiri (body) + IBM Plex Mono (codes)** —
  keeps the Plex look where it is seen and the copy clean where it is read.

Set Latin explicitly rather than leaving it to fallback:

```css
body { font-family: 'Amiri', serif; }
:lang(en), .latin, code { font-family: 'Literata', serif; }
```

## FF Amman

The family originally asked for. Yanone, 2010, published by FontFont, now
Monotype. One of very few families drawn bilingually from scratch — Arabic and
Latin in the same file — and the first with true Arabic italics. Seven sans
weights, four serif.

Two things follow. First, **"Amman in English" needs no second font**: the Latin
is in the same family, so buying it gets both scripts with matched metrics,
which is exactly the property that stops runs splitting. Second, it is
**commercial**. The `Amman V3` files on the free-download sites are repackaged
copies, and a PDF embedding one is redistributing an unlicensed typeface — a
real exposure on a government deliverable, not a technicality.

Buy it from Monotype, drop the files in `fonts/licensed/` named
`FF Amman Serif-400.ttf` and so on, convert any `.otf` with `otf-to-ttf.py`, and
the CSS generator picks them up.

**Measured**, from the `AmmanV3 Sans` Light and Bold on this machine: **10/11
words intact, both engines** — it loses only `الأعمال`, the lam-alef slip, which
puts it exactly level with Tajawal, Almarai and Readex Pro and well clear of
Cairo and IBM Plex Sans Arabic. Its Latin and Arabic share one file, so a mixed
line never splits across two fonts. As a document face it holds up.

Until then: **Amiri** for the Arabic and **Literata** for the Latin. Amiri gives
you the serious book-serif Arabic and the true italics; Literata is the closest
open match to Amman Serif's Latin — sturdy, large x-height, slightly quirky,
built to be read at length.
