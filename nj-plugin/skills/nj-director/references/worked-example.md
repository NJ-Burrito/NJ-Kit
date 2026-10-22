# Worked example — the QA Wrap commercial

Four attempts. Three shipped something broken. The fourth survived an adversarial
pass. Sources: `research/56-decisions-2026-09-07.md` (decisions 98–110),
`research/110`, `112`, `113`, `114`, `115`, `116`.

**The words, the density arithmetic and the beat-by-beat numbers are one worked
example, and it lives in `nj-writer/references/worked-example.md`.** Read it
there — this file does not restate the 105/89-word tables, the five-of-nine
breakage, or the rev-3 density table. What follows is the director-specific
half of the same film: the fault trace this skill owns, and the staging,
camera and hold-vs-cut calls made on it.

## What the failures actually were

| # | Fault | Root cause | The rule it produced |
|---|---|---|---|
| 99 | Every spoken line described the shot *before* the one on screen | A 2 s poster card shifted the picture at load; the cue anchors were never shifted | Anchors are relative and re-derived, never hand-kept |
| 100 | 13 cues whose words the picture no longer said | The `.srt` was regenerated only when cue count ≠ card count | Counts prove nothing about wording. A verbatim film regenerates cues unconditionally |
| 103 | Four dead-air gaps of 1.59–1.99 s survived three anchor passes | Structural: 105 words of read in a 58 s film with 4–5 s fixed shots; each re-voice moved line lengths by ±0.3 s, the same size as the correction | Stop nudging at the second pass and diagnose. Trading dead air for caption-drift is not progress |
| 104 | Fifteen seconds — a quarter of the film — with the product off screen | `frames.mjs` `SCENES` was silently overriding the storyboard's real captures with stick figures | The product is the film. Check the override list, not just the storyboard |
| 106 | Fix chosen: shorten, not slow | the owner judges the read by ear, so `rate` is not a timing control | Trim shot tails in whole half-seconds, off holds, never off action. 58.005 → 52.011 s, gaps → longest 1.46 s |
| 107 | The trimmed render was refused: "150 frames on disk, storyboard says 105" | The guard faulted on too many frames as well as too few | Fault only on too few; log every dropped tail |
| 108 | The trimmed film shipped with no tagline, no ask, no URL, no project line | The end-card beat was anchored to an absolute second on a shot that had been retimed | Between two incomplete films, ship the one whose faults are smaller — and write the end-card assertion |
| 110 | Nothing in any gate noticed | `verify.mjs` had no check that the end card drew what it declares | Failing loudly on a bad anchor is the cheap half. The gate on the card's own elements is the other half |
| 109 | The report filmed light through three passes | `driver.mjs` stamped `light` before first paint, and the storyboard *asserted* light | the owner's dark-theme ruling outranks the old bible. Pin the theme and re-assert it |
| 102/105 | An Arabic flow sheet in an English film | `core/flow.js` draws Arabic-first by design | Product UI that is bilingual on purpose stays. The narration names it: "the flow sheet, Arabic and English" |

## Staging and camera on rev 1 — what the devil pass found, picture side only

Four picture violations, all found on paper before a frame was authored:
**"Nineteen tools"** over five tiles with the tool wall banned by the spec;
**"the page shows the path"** at the moment the sheet turns near edge-on;
**"a bug report out"** after the report had receded to black; **"never leaves
your browser"** with no browser ever drawn. (The words that produced these
lines, and the claims/violations table, are the writer's — see the pointer
above.)

The rev-1 treatment ran one 35.5 s unbroken camera move across the whole
middle of the film. Directorial calls made on it, none of them about the
words:

1. **Re-author the slowdown as position keyframes, not a `timeScale` change.**
   The treatment described a "60 % speed dip" at 36.0 s; written as a rate
   change it is stateful and fails a seek. Written as a slower segment on the
   same `p ∈ [0,1]` curve it is visually identical and pure (`camera.md`).
2. **Decide beat 7's staging in writing** — cut the second sentence, or grow
   the beat to 10.0 s by borrowing from beats 5/6's slack, never from beat 9's
   protected tail. A staging decision made "at the edit" is a decision nobody
   reviewed.
3. **Free beat 9's tail.** It is what protects the CTA on screen; seconds for
   any other beat do not come from there — a camera/staging rule, not a words
   rule.
4. Run the three-plane `preserve-3d` type stub before any asset is drawn —
   free, under an hour, and the only test that can invalidate the artwork
   premise rather than the schedule.

## Rev 3 — the camera plan and the end card, what passing looks like

Camera, seek-safe:

```
p ∈ [0,1] over 11.0 → 52.0 s
x = -1150·p , rotY = 10·p , scale = 1 + 0.06·p
rate = 1 / 36.89 s linear-equivalent = 0.02711 p/s
the "dip" = 0.015 p in 0.9 s — a slower position segment, not a timeScale
```

End card, exact strings: `QA Wrap` / `The session is the report.` / `Get it free`
/ `${QA_WRAP_HOST}/qa-wrap` — 16 samples across t ∈ [52.4, 60.0], opacity ≥ 0.95,
in-frame, contrast computed, final frame > 0.8 % different from flat ground,
final cue verbatim, exactly ten cues, failure names the element and the times.
(The strings themselves are the writer's — `nj-writer/references/claims-and-cta.md`.
The assertion above, and running it inside the render, is this skill's job.)

## What survived the critique, and must be protected from every fix

- **The one-move structure.** It structurally cannot reproduce caption-drift,
  because there is no shot boundary for a caption to drift across. That is an
  advance over three failed attempts, not a restyling.
- **The assembly beat** — the evidence moves fast, the camera refuses to.
- **The paste beat** — the whole argument in 4.5 s, the only beat whose picture
  runs ahead of its words.
- **Countable colour discipline** and the recycled-line audit (the writer's,
  answered against the picture here), which had already caught a real fault.
