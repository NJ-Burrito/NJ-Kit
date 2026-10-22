# Choreography — entrance/exit and the hero, owner's review 21 Sept 2026

the owner's three notes on reel 2, verbatim in `run-log.md`'s fifth run. Rules 1
and 2 here; rule 3 (one caption system) is in `SKILL.md`'s house-finish table
directly, short enough not to need its own section.

## 1. Every element has a designed entrance AND a designed exit

No element may simply appear at its clip's `data-start` or vanish at its end
— unless the style record names a hard cut as that kind of element's move,
in which case tag it `data-hold="cut-in"` / `"cut-out"` with the storyboard
reason (paper-punch's hard-cut transitions still choreograph the ELEMENT
inside the cut; the cut itself is the style's transition, not an excuse to
skip the element's own move).

- **Entrance:** has anticipation or direction — it comes FROM somewhere that
  makes sense in the picture's world (slid in from the edge it is nearest,
  unfolded, dropped and settled, stuck down with tape), an ease that fits the
  style (paper-punch: snap, no ease-in-out), and a settle.
- **Exit:** mirrors or answers the entrance and finishes before or as the
  next scene's hero arrives — never a dead hold, never everything leaving at
  once. Overlaps between scenes are choreographed: the outgoing element
  finishes on the beat the incoming one starts, not before or long after.
- **Stagger** within a group: 60–120 ms, house default, to be tuned by eye.
  Hero first or hero last, never buried in the middle of the pack.
- The style record's `motion_vocabulary` supplies the specific moves. A
  storyboard scene names the entrance and exit move for each element in the
  existing `Typography Animation` (for text) and `Transition Style` (for the
  scene-level move) fields — no new, tenth field. A prop's own entrance/exit
  goes in `Graphic Elements`' line, one clause each, e.g. "cathedral cut-out —
  drops from top edge, settles with a 2-frame bounce; exits by hard cut with
  the scene".

**Gate (build stage, `gate.py` reads `hf/index.html`):** for every element
with class `clip` and every `<img>` inside a scene section, count the GSAP
timeline tweens that target it: at least one starting within 0.6 s after its
`data-start` (entrance) and one ending within 0.6 s before its scene's end
(exit), unless it carries `data-hold="cut-in"`/`"cut-out"`. Elements with
neither are printed by id.

## 2. The hero of a scene must be unmissable

- One hero per scene, named in the storyboard (`data-hero` attribute on the
  built element — required, the gate reads it).
- The hero occupies at least 35% of the frame's shorter side at its resting
  size (house default, to be tuned by eye).
- Nothing else in the scene is larger or more saturated than the hero.
- **Toning a picture to the palette (RECIPES.md #9) must not flatten it into
  the ground.** After toning, the hero's mean luminance must differ from its
  surrounding ground by at least 15 luminance units (0–255 scale), `house
  default, to be tuned by eye`. Supporting pictures are toned DOWN relative
  to the hero (lower contrast, e.g. `toneWarmPetra` instead of `toneWarm`, or
  smaller scale) — never equal to it.
- Text never covers the hero's focal area (its centre third).
- The hero holds still and fully visible for at least 0.8 s of its scene —
  not constantly in motion or occluded.
- **Light ground (prefilm-fix-0921, Lead's decision):** when the scene's
  ground luminance is above 0.8, a paper-white sticker stroke alone cannot
  separate the hero from it. The hero instead sits on a solid backing shape
  cut from dark paper (navy `#0B1F2A` or teal `#0F9D9A` — a disc, rounded
  card or torn-edge panel, larger than the hero, folding in with it, marked
  `data-hero-backing`), keeps its sticker stroke, and gets a stronger contact
  shadow. `hero_check.py` then measures hero-vs-backing and backing-vs-ground
  separately (both `house default, to be tuned by eye`). On dark or
  saturated grounds nothing changes.

**Gate (look stage, `scripts/hero_check.py`):** given a snapshot frame per
scene and the hero's bounding box, measures the hero's size share of the
frame's shorter side and its luminance separation from the surrounding
pixels; fails under either threshold. The bounding box comes from a
`data-hero` element's box, written to `<d>/snapshots/hero-boxes.json` by the
snapshot step alongside the contact sheet (reading live DOM geometry from a
static HTML file is not otherwise feasible without a browser — this is the
one place `hyperframes snapshot`'s own browser context is asked to note
something besides the picture). `hero_check.py` uses Pillow
(`uv run --with pillow`) to crop and measure; it is a look-stage script, not
part of `gate.py`'s own dependency-free checks.
