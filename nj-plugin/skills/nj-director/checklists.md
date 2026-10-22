# Checklists and failure modes

Run these. Each produces a line you paste into the treatment or the report.

## A. Beat sheet check (before density)

1. `sum(durations) == target` — computed, not read off the last Out.
2. `out[n] == in[n+1]` for every row. No overlap, no gap.
3. Every beat has at least one concrete noun in **On screen**.
4. Every beat's **Camera** cell says either `locked` or names a move and what the
   move means.
5. Every beat's narration cell carries its word count.
6. Opening block (product not yet on screen) ≤ 20 % of runtime.
7. 8–12 beats for 30–90 s.

## B. Density check (the arithmetic)

```bash
uv run scripts/density.py beats.json
```

Pass condition: **every beat PASS**, exit 0. Paste the table verbatim.
Then, by hand:

8. The wpm is stated and justified in one sentence.
9. Total silence is stated, and per-beat silence for the beats sold as "quiet".
10. Every beat at margin < +0.25 s has a **pre-approved trim written out**, word
    for word — or is declared as having none and needing a re-take.
11. The end-card beat's tail is ≥ 2.2 s and is marked as not available to pay for
    any other beat.

## C. Violations table (picture vs words) — one row per named thing

**`nj-writer` owns this table and its columns** (`nj-writer` § 3); the director
receives it and answers the non-clean rows. Do not author a second one.

| Beat | The line names | On screen at that moment | Verdict |

12. Every noun, number and proper name in every line gets a row.
13. Verdict is `clean`, `VIOLATION`, or `minor` with the reason.
14. Zero `VIOLATION` rows before pass 5. A minor row carries a written accept.
15. Anything named that is edge-on, receded, out of focus or forbidden by the
    artwork spec is a VIOLATION, not a minor.

## D. Camera plan check

16. Every channel is a function of one `p ∈ [0,1]`; `p` monotonic; no repeated key.
17. The word `timeScale` appears nowhere. Neither does a rate, speed or
    playback-rate change.
18. The keyframe table's rate is shown as `1 / linear-equivalent duration`, and
    one key is re-derived in the text as a check.
19. Screen-relative speed is stated as a number and constant across retimes.
20. The type-in-transform stub has been run and its result recorded.
21. `grep -iE "date\.now|requestAnimationFrame|Math\.random|timeScale" composition/` → empty.

## E. Anchor check

22. `grep -nE "@ *[0-9]+(\.[0-9]+)? *s" treatment.md` → every hit is either a beat
    boundary in § 2 or a fault. Element anchors are `shot(x).in ± offset`.
23. The anchor resolver refuses an out-of-shot anchor, falls back to a declared
    default, and logs it.
24. Retime rehearsal, on paper: shorten one shot by 0.5 s, re-derive. Nothing
    needs hand-nudging and nothing lands outside its shot.

## F. End-card assertion (write before authoring, run inside the render)

25. The exact strings exist in the treatment: wordmark, tagline, **ask**, URL.
    An ask is a verb the viewer can do. A URL is not an ask.
26. Sampled every 0.5 s across the card's whole span, all four text nodes present,
    content equal **exactly and case-sensitively** — substring match is not a pass.
27. Each node `opacity ≥ 0.95`, non-zero width and height, fully inside the frame
    rect at every sample. Present-but-transparent and present-but-off-frame are
    the two ways a naive check passes a broken card.
28. Contrast computed, not asserted: ≥ 7:1 for the wordmark, ≥ 4.5:1 for the rest.
29. Pixel corroboration: the final frame differs from a flat ground fill by
    > 0.8 % of pixels. A near-black last frame FAILS.
30. The caption track's final cue equals the end-card line verbatim, and the cue
    count equals the card count.
31. Failure output **names which element was missing and at which sample times**.
    "End card check failed" with no element name is itself a defect in the gate.
32. It is wired as a build failure, not a warning.

## G. Before you call it done

33. Dead-air gate: no gap > 1.5 s. Report the count and the longest, verbatim.
34. Determinism: seek-rendered and linearly-rendered sample frames byte-identical.
35. Theme pinned to the product's dark theme before first paint, and re-asserted
    in the render — not assumed.
36. Bilingual pair: both languages ran through B separately; neither is stale.
37. Every pass left its file. Name the paths in the report.

---

# Failure modes and their tells

| Failure | The tell, before it costs a render |
|---|---|
| **Dead air** — 1.5–2.2 s of silence between caption and shot | Density table shows large positive margins clustered in the beats that follow long lines; the read is a small fraction of the runtime |
| **Caption ahead of picture** | Fixing dead air by nudging anchors earlier, twice. The second nudge is the tell: the cause is structural, not a timing mistake |
| **Starved beat hidden by a healthy total** | A treatment that quotes a total slack figure and no per-beat column |
| **Wall-to-wall narration sold as "quiet"** | A beat described as held, dread or silent whose words ÷ wpm ≥ its duration. Read it aloud against a stopwatch; ten minutes settles it |
| **Impossible density claim** | Any sentence where placement is said to *reduce* speech time. Placement moves speech; it never shortens it |
| **Product off screen** | An asset spec that invents artwork for beats whose captures already exist; a scene override list that silently shadows the storyboard |
| **Asserted count never drawn** | A number in a line and a spec that forbids drawing that many |
| **Named but illegible** | The named object is mid-transition, edge-on, receding or out of focus in the same beat's On-screen cell |
| **End card drops the ask** | The ask text does not exist as a string anywhere in the treatment; or the card beat is the most over-committed beat, so it is first to be trimmed |
| **Absolute anchor** | A number with `s` after it attached to anything that is not a beat boundary |
| **Seek divergence** | The words speed, rate, `timeScale`, "slow down here" in the camera plan |
| **Type shimmer** | Small type inside a long 3D move, and no stub test on record |
| **Silent frame-count refusal** | A render guard that faults on too many frames as well as too few; a declared trim then looks like a bug. Fault only on too few, and log the drop |
| **Stale bilingual half** | One language's density table dated earlier than the other's |
