# Narration breathes (owner feedback, 2026-11-07)

Whole-line TTS runs clauses together with no breath and sounds unreal. The fix is made once, in the voice pipeline, never per line.

## The rule

1. **Split** each line after punctuation into segments: `،` `,` `؛` `;` `:` `.` `؟` `?` `!` `…`. The mark stays with the segment it ends.
2. **Voice each segment as its own utterance**, so the next word gets sentence-initial prosody instead of continuing the previous clause's contour.
3. **Join** the segments with breath pauses cut from the voice's own room tone (the reference's noise floor), never digital zero.

| Mark ending the segment | Pause |
|---|---|
| `،` `,` | about 0.22 s |
| `؛` `;` `:` | about 0.30 s |
| `.` `…` | about 0.40 s |
| `؟` `?` `!` | about 0.45 s |

4. **Merge short segments.** A segment under 3 words that ends in a comma, `؛` or `:` merges with a neighbour. A short sentence ending in `.` `?` `!` stays alone.
5. **An inhale sound is optional and off by default.** Turn it on only on the owner's word.

## Boundaries with the other rules

- Each segment is still **one take**: no re-voice, no verify, no ASR, no model that listens. New punctuation is new text.
- Fixed **once in the pipeline** (split, voice, join), never by hand on one line. The pause floor in `sound-engineering.md` still runs last, so mastering does not close these pauses.
- The pauses are room tone, so they pass VOICE-EDGE-NOISE and VOICE-TAIL like any other quiet span; never digital silence.
- The direction sheet (`direction.md`) may ask for a longer pause on a line; that is a new value for that mark, recorded in the sheet.

## Reference implementation

Public repo `NJ-Burrito/Story-Wrap`, `tools/voice.py`: `breath_plan` (split and merge) and `join_segments` (room-tone pauses). Read it before writing a port; numbers above are its defaults.
