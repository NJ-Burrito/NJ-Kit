# Measuring the type face

Open this before trusting an average-advance-width guess or a line-height assumption for a new face. Referenced from SKILL.md § Measure the face.

## Measure the face; never assume it

Three numbers decide whether text fits, and all three must be measured in the
real face rather than reasoned about:

- **Advance width is not one number.** In Cairo, «رفض» runs 0.62 of the type
  size per character and «تعبئة نموذج الطلب (4 أقسام)» runs 0.34 — short strings
  are dominated by side bearings and wide letters. A single average
  *under*-reserves every short caption, which is exactly the set that ends up
  drawn on top of each other. Use a slope plus an intercept, with the slope kept
  above the fit: `w = size · (0.42·len + 1.2)`. Over-reserving costs air,
  under-reserving costs a collision.
- **A line's glyph box is 1.82× the type size**, not the line spacing. Arabic
  ascenders and a shadda need the room, and inside a diamond — which narrows
  away from its middle — a three-unit error there is the whole difference
  between text inside the shape and text out past its edge.
- **`text-anchor` is relative to the inline direction.** With `direction="rtl"`,
  `start` is the run's **right** edge and `end` its left. Reading those the
  Latin way puts every caption's reserved rectangle on the wrong side of its own
  line — a collision checker cheerfully agreeing with a drawing that plainly
  overlaps.
- **The font must actually be loading when you measure.** `@import` inside
  `page.setContent()` silently does not fetch. Every "clean" reported for weeks
  was measured in a fallback face; the faults the client could see appeared the
  moment a `<link>` replaced it. Assert `document.fonts.check()` in the checker.

Full failure catalogue (every symptom that has actually shipped, its cause and
its fix) and what was tried and abandoned are in `reference/failures.md` —
open it when a symptom mid-build matches one of its rows, before re-deriving
a fix.
