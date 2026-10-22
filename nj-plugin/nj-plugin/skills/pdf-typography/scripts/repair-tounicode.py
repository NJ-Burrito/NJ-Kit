# -*- coding: utf-8 -*-
"""Repairs the ToUnicode map of an Arabic PDF so ligatures copy as themselves.

    python repair-tounicode.py doc.pdf [--report]

## The fault

One glyph carrying two characters cannot survive a reversed run.

Every PDF headless Chrome produces stores an Arabic line in **visual** order. A
text engine that reverses the run to recover the sentence — MuPDF, PDFium, and
therefore Chrome's own viewer, Edge's, and most lightweight PDF editors —
reverses the *glyphs* and keeps each glyph's ToUnicode string intact. So a glyph
mapped to the two characters «لا» lands with its own two characters the wrong
way round, and «لاستكمال» comes back «الستكمال».

That is a spelling error in the middle of a word, and it is why a client
reported that copying out of the delivered PDF «pastes gibberish».

Measured across the vault, this is **the** difference between the families:

    Amiri              30/30/30   no ligature glyph at all — HarfBuzz draws lam
                                  and alef separately, so nothing reverses
    Harmattan          31/24/24   one glyph, two characters
    Scheherazade New   30/24/24   one glyph, two characters; the hamza forms
                                  have no ToUnicode entry at all
    Simplified Arabic  31/24/13   one glyph mapped to a presentation form, plus
                                  whole-line reversal

It is not fixable in CSS. `rlig`, `liga`, `clig` and `dlig` off change nothing,
because lam-alef is a **required** ligature and the shaper applies it whatever
the feature settings say — verified on four families.

## The repair

Rewrite the ToUnicode entry for each lam-alef ligature glyph to the **single**
Arabic Presentation Form that means exactly that ligature: U+FEFB, U+FEF7,
U+FEF9, U+FEF5.

One glyph, one character. The reversal moves it as a unit and it lands in the
right slot; it renders as «لا» wherever it is pasted, and NFKC folds it back to
the two letters for anything that normalises.

Three mappings were measured before this one was chosen:

    as printed          poppler 8/8   mupdf 3/8   pdfium 3/8
    the pair, reversed  poppler 5/8   mupdf 6/8   pdfium 6/8   trades one for the other
    presentation form   poppler 8/8   mupdf 6/8   pdfium 6/8   costs nothing anywhere

Reversing the pair trades poppler — which is what Acrobat and Word behave most
like — for the reversing engines. The presentation form helps those and leaves
poppler exactly where it was.

## Finding the glyphs

Not by name, and not from the embedded font.

Glyph names are a convention, not a contract: `lam_alef.isol`, `uniFEFB`,
`afii57721` and plain `gid412` are all in the wild. And Chrome's subsetter
**drops GSUB entirely and renames every glyph to `glyph00123`**, so the embedded
face has no ligature table left to read and no name to recognise.

What the subset does keep is the original glyph **numbering** — gid 896 is still
uni0644 in a 1,762-glyph subset of a 1,762-glyph font. So the ligature ids are
read from the font on disk in `fonts/` and used against the PDF. The face is
matched on its PostScript name with the subset prefix and every separator
removed, which is the part a subsetter leaves alone.

In the font on disk the **GSUB ligature lookups** are walked: a ligature whose
components resolve to lam followed by an alef form *is* a lam-alef ligature,
whatever anyone called it. Contextual forms are resolved by stripping the usual
suffixes (`.init`, `.medi`, `.fina`, `.isol`, `-ar`) and looking the base name up
again, so `lam.init` counts as lam.

A document whose faces have no such ligature — Amiri — is left untouched.
"""
import pathlib
import re
import sys

import pikepdf
import pymupdf
from fontTools.ttLib import TTFont

sys.stdout.reconfigure(encoding="utf-8")

VAULT = pathlib.Path(__file__).resolve().parent.parent / "fonts"

LAM = 0x0644
ALEFS = {0x0627: 0xFEFB, 0x0623: 0xFEF7, 0x0625: 0xFEF9, 0x0622: 0xFEF5}

SUFFIXES = (
    ".init", ".medi", ".fina", ".isol", ".short", ".alt", ".alt1", ".alt2",
    "-ar", "_ar", ".ar",
)

NL = chr(10)


def base_codepoint(name, reverse):
    """The character a glyph is a form of, or None."""
    if name in reverse:
        return reverse[name]
    stem = name
    for _ in range(3):
        for suffix in SUFFIXES:
            if stem.endswith(suffix):
                stem = stem[: -len(suffix)]
                break
        else:
            break
        if stem in reverse:
            return reverse[stem]
    m = re.fullmatch(r"uni([0-9A-Fa-f]{4})", name)
    return int(m.group(1), 16) if m else None


def lam_alef_glyphs(path):
    """Glyph ids that draw a lam-alef ligature, and the character each means."""
    font = TTFont(str(path), lazy=True)
    if "GSUB" not in font:
        font.close()
        return {}

    reverse = {}
    for table in font["cmap"].tables:
        for code, name in table.cmap.items():
            reverse.setdefault(name, code)

    gid_of = {name: i for i, name in enumerate(font.getGlyphOrder())}

    found = {}
    for lookup in font["GSUB"].table.LookupList.Lookup:
        for sub in lookup.SubTable:
            # An Extension lookup wraps the real one.
            inner = getattr(sub, "ExtSubTable", sub)
            ligatures = getattr(inner, "ligatures", None)
            if not ligatures:
                continue
            for first, entries in ligatures.items():
                if base_codepoint(first, reverse) != LAM:
                    continue
                for lig in entries:
                    if len(lig.Component) != 1:
                        continue
                    alef = base_codepoint(lig.Component[0], reverse)
                    if alef in ALEFS and lig.LigGlyph in gid_of:
                        found[gid_of[lig.LigGlyph]] = ALEFS[alef]
    font.close()
    return found


def vault_font(base_font):
    """The original .ttf a PDF's subset came from, or None."""
    stem = re.sub(r"^[A-Z]{6}\+", "", base_font)
    key = re.sub(r"[^a-z0-9]", "", stem.lower())
    for path in sorted(VAULT.rglob("*.ttf")):
        try:
            font = TTFont(str(path), lazy=True)
            names = {str(r) for r in font["name"].names if r.nameID in (4, 6)}
            font.close()
        except Exception:
            continue
        if any(re.sub(r"[^a-z0-9]", "", n.lower()) == key for n in names):
            return path
    return None


def repair(path, report=False):
    doc = pymupdf.open(path)

    faces = {}
    for page in doc:
        for entry in page.get_fonts(full=True):
            faces.setdefault(entry[0], entry[3])

    targets = {}
    for xref, base in faces.items():
        source = vault_font(base)
        if source is None:
            if report:
                print("  ? %s: not found in the vault, left alone" % base)
            continue
        glyphs = lam_alef_glyphs(source)
        if not glyphs:
            continue
        obj = doc.xref_object(xref, compressed=False)
        m = re.search(r"/ToUnicode (\d+) 0 R", obj)
        if m:
            targets[int(m.group(1))] = glyphs
    doc.close()

    if not targets:
        if report:
            print("%s: no lam-alef ligature glyphs, nothing to repair" % path)
        return 0

    pdf = pikepdf.open(path, allow_overwriting_input=True)
    changed = 0
    for tu, glyphs in targets.items():
        obj = pdf.get_object(tu, 0)
        text = bytes(obj.read_bytes()).decode("latin-1")
        added = []
        for gid, code in sorted(glyphs.items()):
            pattern = re.compile(r"<%04X>\s*<[0-9a-fA-F]+>" % gid)
            replacement = "<%04X> <%04X>" % (gid, code)
            text, n = pattern.subn(replacement, text)
            if n:
                changed += n
            else:
                added.append(replacement)
        if added:
            # Glyphs the subset never mapped at all. The hamza forms are usually
            # here, and an unmapped ligature is where an extractor loses a letter
            # outright rather than merely transposing two.
            #
            # A CMap holds at most 100 entries per bfchar block.
            blocks = []
            for i in range(0, len(added), 100):
                chunk = added[i : i + 100]
                blocks.append(
                    "%d beginbfchar%s%s%sendbfchar%s"
                    % (len(chunk), NL, NL.join(chunk), NL, NL)
                )
            text = text.replace("endcmap", "".join(blocks) + "endcmap", 1)
            changed += len(added)
        obj.write(text.encode("latin-1"))
    pdf.save()
    pdf.close()

    if report:
        print(
            "%s: repaired %d ligature mapping(s) in %d font(s)"
            % (path, changed, len(targets))
        )
    return changed


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    repair(args[0], "--report" in sys.argv)
