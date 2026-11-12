# Review checklists

Each check is PASS or FAIL, with a frame time. A FAIL names the beat, the rule
(`craft.md` §) and the fix. Anything measurable is measured by script, never
judged by eye. One fix round. The re-check covers only the failed items, on
snapshots, not on a full re-render.

## A. Boards and animatic (stage 3, before polish)

1. Beat count and times match `storyboard.md` (±0.5 s).
2. One idea per beat. The strongest contrast sits on the named focal point.
3. Size changes between neighbours, or the storyboard gives the reason.
4. Light: warm until the product acts, then the success colour. One hero
   accent per beat.
5. The hook lands inside 2–3 s, the turn on the drop, one CTA.
6. Screen direction is consistent. In Arabic, time and progress run right to
   left.
7. Every word on screen is in `script.json` or the storyboard's supers.
   Nothing invented, no lorem.
8. 9:16 boards are a re-layout, with captions and the CTA inside the safe
   area.
9. Cut any beat that does not earn its time.

## B. Render (every aspect and language)

1. `mm.py probe`: the duration ±1 frame, the size, 30 fps, video and audio
   streams, about −14 LUFS, pairs matching.
2. `frame_probe.mjs`: 0 axis faults > 1 px, 0 non-house rendered faces, 0
   Arabic text faults, 0 page errors.
3. Captions: on-set times within 2 frames of `timing.json`. No ghosting on a
   swap frame. Each caption window ≥ 0.3 s per word.
4. Latin runs inside Arabic lines appear in the right order (check a still
   of each).
5. Motion: one lead move per beat, and the ease matches its object type
   (`craft.md` §3). Strip at 0.25 s steps around each lead move.
6. No static second: every 1 s pair of snapshots differs in the foreground.
7. The bookend and graphic matches named in the storyboard are present.
8. Frame 0 and the last frame are designed frames, poster-worthy.
9. Audio: the voice peaks around −14 to −16 dBFS, the bed ≥ 10 dB under
   it, no clipping, the tail faded before the end.
10. Truth: every on-screen claim has a row in `claims.md`. No real client
    data. Third-party logos are neutral tiles.
11. The owner's earlier notes (the project's `LESSONS.md`) are each checked
    by name.

## C. Verdict

`review/REVIEW.md`: one table per deliverable (check | PASS/FAIL | frame time
| rule | fix), then `verdict: PASS` or `verdict: FAIL`. FAIL: the builder fixes
once and the director re-checks only the failed rows.
