# Licensed fonts (drop-in)

Fonts that cannot be downloaded automatically because somebody sells them.
Put the files here, one per weight, named `<Family>-<weight>[i].ttf` — spaces
and all, e.g. `AmmanV3 Sans-700.ttf`, `FF Amman Serif-400i.ttf`. The name is the
record; nothing else knows what these are.

**A `.otf` must be converted first.** Chrome cannot embed a CFF font program in
a PDF: it falls back to unnamed Type 3 glyph procedures, silently. The curves
survive the conversion intact.

```bash
python ../../scripts/otf-to-ttf.py "AmmanV3 Sans-700.otf"
```

Before you do: check the licence covers **embedding in a document**, which
is a separate grant from installing the font. A desktop licence usually
permits it; a webfont-only licence usually does not.

## FF Amman Sans / FF Amman Serif

Yanone, 2010, published by FontFont — now Monotype. One of the very few
families drawn bilingually from scratch: Arabic and Latin in the same file,
and the first with true Arabic italics. Seven sans weights, four serif.
Because the Latin is *in* the family, "Amman in English" needs no separate
font — buy the family and both scripts are there.

It is commercial. The `Amman V3` files circulating on the free-download
sites are repackaged copies of it, and a document embedding one is
distributing an unlicensed typeface. Buy it from Monotype, drop the files
here, and `make-font-css.mjs` will pick them up on its own.

Until then the open stand-ins are **Amiri** for the Arabic and **Literata**
for the Latin.
