"""
The two deterministic gates every motion deck runs before the expensive render.

    PYTHONUTF8=1 uv run --with fonttools python gates.py glyphs <font.otf> [<font.otf> ...] -- <text files...>
    PYTHONUTF8=1 python gates.py contrast <fg-hex> <bg-hex> [<fg-hex> <bg-hex> ...]

glyphs   : every character typed in the text files must exist in every font listed.
           Exit 1 and name each missing character + codepoint. (Thmanyah has no arrows,
           ticks, "≈", "≤", Latin Extended-A or emoji: draw them as SVG or name a fallback.)
contrast : WCAG 2 ratio for each pair. Exit 1 if any text pair is under 4.5:1.
           3:1 is allowed only for large text (≥ 24 px regular or ≥ 18.66 px bold) —
           pass --large to apply 3:1 instead.
"""
import sys


def lum(h: str) -> float:
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a: str, b: str) -> float:
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def contrast(args: list[str]) -> int:
    large = "--large" in args
    args = [a for a in args if a != "--large"]
    need = 3.0 if large else 4.5
    bad = 0
    for fg, bg in zip(args[::2], args[1::2]):
        r = ratio(fg, bg)
        ok = r >= need
        bad += not ok
        print(f"{'PASS' if ok else 'FAIL'} {fg} on {bg}: {r:.2f}:1 (need {need})")
    return 1 if bad else 0


def glyphs(args: list[str]) -> int:
    from fontTools.ttLib import TTFont
    i = args.index("--")
    fonts, files = args[:i], args[i + 1:]
    text = "".join(open(f, encoding="utf-8").read() for f in files)
    chars = {c for c in text if c not in "\r\n\t "}
    bad = 0
    for f in fonts:
        cmap = TTFont(f).getBestCmap()
        miss = sorted(c for c in chars if ord(c) not in cmap)
        bad += len(miss)
        print(f"{f.split('/')[-1]}: {'OK' if not miss else 'MISSING ' + ' '.join(f'{c} U+{ord(c):04X}' for c in miss)}")
    return 1 if bad else 0


if __name__ == "__main__":
    cmd, rest = sys.argv[1], sys.argv[2:]
    sys.exit(glyphs(rest) if cmd == "glyphs" else contrast(rest))
