# STORYBOARD — the strict shape (devil #5: named twice, shipped never — fixed 2026-09-21)

ALWAYS use this structure. Field names do not change. One block per scene,
times from CUES.md; a scene's window runs from its cue's start to the NEXT
cue's start, so the picture is never empty. Nine fields, in order:

```
SCENE <n>  (<window start> – <window end>)
Spoken Dialogue      "<the narration line, verbatim>"
Visual Description   <what is on screen, in motifs from STYLE-DNA.md §5>
On-Screen Text       <words, all from the dialogue unless PROJECT.md allows more>
Typography Animation <which word class does what>
Graphic Elements      <the props by name>
Material              <library ids/aliases from %NJ_LIBRARY%/INDEX.json (library.py find), comma-
                       separated, one per prop that needs one, each followed by
                       "— because <clause tying this picture to this spoken line>"
                       (devil #2 — required, never a repeat of the id's own words) —
                       or the literal "DRAWN: <reason>" when the library has no
                       candidate for that kind. Never blank when Graphic Elements
                       names a prop. A deliberately rectangular picture is declared
                       "print: <id>" or "photo-card: <id>", not as a cutout.>
Camera Movement      <one move, or "locked">
Transition Style     <how this scene leaves>
Synchronization      <event seconds | event seconds | ...  number LAST on each
                      segment, nothing after it but "|"/end-of-line — every time
                      inside the window>
```

Worked example (Material field, all cases):

```
SCENE 2  (4.20 – 7.24)
Spoken Dialogue      "يجهّز كل شيء قبل أن تسأل"
Visual Description   a torn-paper house cutout drops in behind the hero word
On-Screen Text       يجهّز
Typography Animation HERO word snap scale-in, PUNCH box holds "جهّز"
Graphic Elements     house cutout, one flat amber disc anchor
Material              cutout-house-03 — because the line names "everything ready
                       before you ask", and the house is the thing made ready;
                       disc is DRAWN: recipe 4 is a flat CSS shape, not a
                       photograph — no manifest kind covers it
Camera Movement      locked
Transition Style     hard cut
Synchronization      snap-in 4.4 | disc rock 6.8
```

Close with:

```
PACE   <N> timed events in <T> s, one every <T/N> s; longest gap <G> s (<from> -> <to>)
HOOK   what happens inside the first 2 s, and whether it needs a spoken word
LOCK   the 4–6 rules no scene may break
```

Do not write the PACE line yourself: `scripts/gate.py <project> 3` computes it
from the Synchronization lines and prints it once STORYBOARD.md exists
(devil #12 — this was misdocumented as stage 4). Copy what it prints.
Write every cue as `<event> <seconds>` separated by ` | `, seconds with a
decimal point and nothing else on the same segment — prose after the number
makes the gate's regex find zero times and report a false "no cue time falls
inside its window" (devil #6).
