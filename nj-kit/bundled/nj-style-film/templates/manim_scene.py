"""One Manim scene for a style film. Copy to <project>/manim/scene_<n>.py, replace the body.

Render (duration = the scene window in CUES.md):
  PYTHONUTF8=1 manim render -qh -t --format webm --disable_caching scene_<n>.py SceneN

reference/motion-engines.md explains each guard below.
"""
import os
from pathlib import Path

import manimpango
from fontTools.ttLib import TTFont
from manim import DOWN, LEFT, UP, Arrow, Circle, Create, FadeIn, MarkupText, Scene, VGroup, Write

# Two roles, brand/DESIGN.md §2: display (Serif Display) for title/hero words,
# body (Sans) for labels and numerals. Font files come straight from the repo
# (brand/fonts/thmanyah/otf/*.otf, tracked since 2026-09-21) — no WOFF2 step;
# Pango reads OTF directly. Personal grant to the owner: never copy these files
# into anything published for others to reuse.
REPO_FONTS = Path(os.environ.get("ENSERA_FONTS", Path.home() / "Desktop" / "ENSERA" / "brand" / "fonts" / "thmanyah" / "otf"))  # fixed repo path, not project-relative
DISPLAY_FILE = REPO_FONTS / "thmanyahserifdisplay-Bold.otf"
BODY_FILE = REPO_FONTS / "thmanyahsans-Medium.otf"


def family_name(path):
    """Read the family name FROM the file (devil #9: a guessed name silently
    falls back to a system face when Pango's registration and the requested
    name disagree). name ID 1 = family, ID 2 = subfamily/weight."""
    tt = TTFont(str(path), lazy=True)
    names = {n.nameID: n.toUnicode() for n in tt["name"].names if n.nameID in (1, 2, 16)}
    tt.close()
    # nameID 1 (font-specific family, e.g. "thmanyah sans Med") is what Pango's
    # registration keys weights apart by; nameID 16 (typographic family, e.g.
    # "thmanyah sans") is shared across every weight and would ask Pango to
    # pick one of several registered files itself — silently, per motion-engines.md.
    return names[1], names.get(2, "Regular")


assert DISPLAY_FILE.exists() and BODY_FILE.exists(), f"font files missing: {DISPLAY_FILE}, {BODY_FILE}"
assert manimpango.register_font(str(DISPLAY_FILE)), "display face did not register"
assert manimpango.register_font(str(BODY_FILE)), "body face did not register"
DISPLAY_FONT, DISPLAY_SUBFAMILY = family_name(DISPLAY_FILE)
BODY_FONT, BODY_SUBFAMILY = family_name(BODY_FILE)
# Request the weight the requested FILE actually is, never a guessed constant —
# a mismatch here is exactly the fault that shipped Sans-only on the first run.
DISPLAY_WEIGHT = "BOLD" if "bold" in DISPLAY_SUBFAMILY.lower() else "NORMAL"
BODY_WEIGHT = "BOLD" if "bold" in BODY_SUBFAMILY.lower() else "NORMAL"

# From the project's STYLE-DNA, never Manim's defaults.
INK = "#FFFFFF"
ACCENT = "#FFFFFF"


def word(text, scale=1.0, color=INK, role="body"):
    """MarkupText, never Text: Text('قرار') renders zero glyphs without an error."""
    font, weight = (DISPLAY_FONT, DISPLAY_WEIGHT) if role == "display" else (BODY_FONT, BODY_WEIGHT)
    m = MarkupText(text, font=font, weight=weight, color=color).scale(scale)
    assert m.width > 0 and len(m.submobjects) > 0, f"dropped by the renderer: {text!r}"
    return m


class SceneN(Scene):
    def construct(self):
        title = word("العنوان", role="display").to_edge(UP)
        nodes = VGroup(*[Circle(radius=0.45, color=ACCENT) for _ in range(3)])
        nodes.arrange(LEFT, buff=1.6)  # Arabic reads right to left: first node on the right
        labels = VGroup(*[
            word(t, scale=0.4, role="body").next_to(n, DOWN)
            for t, n in zip(["أولاً", "ثانياً", "ثالثاً"], nodes)
        ])
        arrows = VGroup(*[
            Arrow(a.get_left(), b.get_right(), buff=0.1, color=INK)
            for a, b in zip(nodes, nodes[1:])
        ])
        self.play(Write(title), run_time=0.8)
        self.play(Create(nodes), FadeIn(labels), run_time=0.8)
        self.play(Create(arrows), run_time=0.6)
        self.wait(0.3)
