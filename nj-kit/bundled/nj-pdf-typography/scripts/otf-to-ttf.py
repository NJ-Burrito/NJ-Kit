#!/usr/bin/env python
"""Convert a CFF/OpenType `.otf` to TrueType outlines, because Chrome will not
embed the former properly.

Handed a `.otf`, Chrome's PDF backend gives up on embedding the font program and
writes every glyph as a **Type 3** drawing procedure instead: one unnamed font
object per text run, no font name in the file, no subset anybody can identify.
The page still looks right and the text still extracts, so nothing complains —
but the PDF now carries seven anonymous glyph-procedure fonts where it should
carry one named subset, and strict validators reject it.

Proven by isolation: the same typeface, same page, same everything, converted to
TrueType outlines, comes out as `Type0 AAAAAA+AmmanV3Sans-Bold`. It is the
outline format, not the licence — clearing the font's `fsType` embedding flag
changes nothing.

    python otf-to-ttf.py "fonts/licensed/AmmanV3 Sans-700.otf"
    python otf-to-ttf.py fonts/licensed/*.otf --replace

The curves are converted, not redrawn: cubic Béziers become quadratics within a
tolerance of one unit per em, which is far below anything visible in print.
"""
import argparse
import sys
from pathlib import Path

try:
    from fontTools.ttLib import TTFont, newTable
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from cu2qu.pens import Cu2QuPen
except ImportError:
    sys.exit("needs fonttools and cu2qu:  pip install fonttools cu2qu")


def otf_to_ttf(src: Path, dst: Path, tolerance: float = 1.0) -> None:
    font = TTFont(src)
    glyphset = font.getGlyphSet()
    order = font.getGlyphOrder()

    glyf = newTable("glyf")
    glyf.glyphOrder = order
    glyf.glyphs = {}
    for name in order:
        pen = TTGlyphPen(glyphset)
        glyphset[name].draw(Cu2QuPen(pen, tolerance))
        glyf.glyphs[name] = pen.glyph()
    font["glyf"] = glyf
    for name in order:
        glyf[name].recalcBounds(glyf)

    font["loca"] = newTable("loca")
    font["head"].indexToLocFormat = 0
    font["head"].glyphDataFormat = 0
    for table in ("CFF ", "VORG"):
        if table in font:
            del font[table]

    # maxp goes from the CFF form (0.5) to the TrueType form (1.0), which has
    # a dozen more fields. Zeroes are correct for an unhinted font.
    maxp = newTable("maxp")
    maxp.tableVersion = 0x00010000
    maxp.numGlyphs = len(order)
    for field in ("maxZones", "maxTwilightPoints", "maxStorage", "maxFunctionDefs",
                  "maxInstructionDefs", "maxStackElements", "maxSizeOfInstructions",
                  "maxComponentElements", "maxComponentDepth", "maxPoints",
                  "maxContours", "maxCompositePoints", "maxCompositeContours"):
        setattr(maxp, field, 1 if field == "maxZones" else 0)
    font["maxp"] = maxp

    font.sfntVersion = "\x00\x01\x00\x00"
    font.save(dst)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="the .otf files to convert")
    ap.add_argument("--replace", action="store_true", help="delete the .otf once converted")
    ap.add_argument("--tolerance", type=float, default=1.0, help="curve error, units per em")
    args = ap.parse_args()

    for name in args.files:
        src = Path(name)
        if src.suffix.lower() != ".otf":
            print(f"  · {src.name} is not a .otf, skipped")
            continue
        dst = src.with_suffix(".ttf")
        otf_to_ttf(src, dst, args.tolerance)
        print(f"  ✓ {src.name} → {dst.name}")
        if args.replace:
            src.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
