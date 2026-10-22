# Timing: beats, density, anchors

## What a beat is

A beat is one change — the smallest unit after which the viewer knows something
they did not know before. In animation development a beat board is drawn before
anything is timed, precisely because a beat is a *story* unit; the seconds are
assigned afterwards (Grizandnorm, "Beat Boards"; ECUAD Animation notes). A beat
that has no change is a held shot, which is a legitimate beat — see `camera.md`
— but it must be declared as one, with what the hold is buying.

**A 30–90 s piece runs 8–12 beats.** Fewer and the beats are too long to time
honestly; more and each beat is under 2.5 s, which cannot carry a line plus the
silence around it.

## Beat sheet columns, all six, every row

| # | In → Out | Dur | On screen | Camera | Narration (verbatim = caption) |

- **In → Out** is written, and **also derived**: `out[n] == in[n+1]` for every
  row, and `out[last] == target`. If the columns disagree with the sum, the sum
  wins and the treatment is wrong.
- **On screen** must contain concrete nouns — the objects an asset list can be
  built from. "The product feels fast" is not an on-screen entry.
- **Narration** is the writer's text, pasted verbatim, with its word count.

## The speech-against-silence budget

**Get the wpm from `nj-writer/NARRATION.md`'s Matrix, not from this file.**
Reconciled 2026-09-21: this section used to state its own flat rates (140
en / 120 ar) as if they were THE rate — they were a house-default average
that disagreed with the Matrix's real per-genre bands (commercial en runs
150–170 wpm, educational en 130–150, walkthrough 140–160 — none of them is a
flat 140). Run `nj-writer/scripts/narration_brief.py <brief.md>` for the row
that matches the genre/language/destination, and pass that wpm into
`beats.json` — `density.py` now FAILS if `"wpm"` is missing, for every
language, instead of silently defaulting one.

Pick the rate the performance needs and then *hold the rate fixed* — a tired
or intimate register is not slower per word, it is more space **between**
lines, and that space is counted as silence, not folded into the rate.

**The placement rule, arithmetic not vibes:**

```
speech(beat)   = words / (wpm / 60)
required(beat) = speech + lead-in + tail       # default lead-in 1.0 s, tail 0.5 s
PASS           <=>  duration >= required
```

The end-card beat carries an extra rule: `duration >= speech + 1.0 + 2.2`, a
≥ 2.2 s silent tail so the ask is readable after the voice stops.

**Per-beat pass/fail, never a total.** A film with +5.5 s of total slack can
still have a beat starved by 2.07 s, because slack in beats 4–6 cannot lend to
beat 7 when the camera move fixes each beat's wall clock (research/114 §1). A
total is the number that hides the fault.

Run it:

```bash
uv run scripts/density.py beats.json          # exits 1 if any beat FAILs
```

Paste the table it prints into § 3 of the treatment. Do not retype it.

**words ÷ wpm is an estimate.** A recorded take redraws each line by ±0.3 s —
the same size as the corrections people then chase with anchor nudges
(decision 103). After the voice session, measure the actual per-line durations,
put them in the `words`-equivalent column as measured seconds, and re-run the
gate. A beat passing at +0.00 on paper is a coin flip in the take; that is why
§ tight beats carry a written pre-approved trim.

### When a beat fails

In order of preference:

1. **Cut words from that line.** Pre-approve the trims in writing, word by word,
   before the voice session: "beat 6 drops *actually* (−1 word, −0.43 s)". A trim
   decided at the edit is a trim nobody reviewed.
2. **Grow the beat from an adjacent beat's slack**, and write which beat pays.
3. **Grow the film.** Legitimate, but it changes a client-facing number, so it is
   the owner's ruling, not yours.
4. **Never** take seconds from the end-card tail, and never slow the read — the
   read is the performance he judges by ear (decision 106).

State the margin on every beat. A beat at +0.00 is passing *exactly*, which means
a take that overruns by 0.2 s breaks it; say so and name its trim.

## Silence is a budget line

Write the silence total and the per-beat silence, and say where it is spent. The
QA Wrap rev-3 opening is 11.0 s of picture carrying 4.71 s of speech — **57 %
silent**, declared. A "quiet, held" opening that turns out to be 100 % wall-to-wall
narration is not quiet; it is voiceover over a near-still, and it is the first
thing a client rejects.

## Relative anchoring

**Every anchor names its parent and a relative offset.** Never an absolute second.

```
BAD   endCard.tagline @ 47.2s
GOOD  endCard.tagline @ shot("end").in + 0.4s     # and REFUSE if outside the shot
```

- A cue anchored to `shotIn − 0.85 s` is legitimate; `46.35 s` is not, because a
  half-second trim anywhere upstream silently makes it wrong.
- Any function that resolves an anchor **refuses** one that falls outside its own
  shot, falls back to a declared default, and **logs the fallback** (decision 110).
  Failing loudly is the cheap half of the fix.
- A retime must be a pure re-derivation: change a duration, re-run the density
  script, re-derive the keyframe table. Nothing is hand-nudged.

## Caption timing

Captions are the spoken words verbatim (house rule), so the cards *are* the
subtitle track and there is no second opinion to preserve: **regenerate cues from
the cards on every render of a verbatim film**, unconditionally. Matching cue and
card counts proves nothing about wording — that check is how a shipped film
carried 13 cues the picture no longer said (decision 100).

Borrowed from broadcast practice, as sanity floors:

- Minimum ~0.3 s per word on screen; BBC targets 160–180 wpm reading speed.
- Netflix: ≤ 20 cps, event 5/6 s to 7 s, ≥ 2-frame gap between events.
- **Do not let a caption cross a shot change** when the dialogue does not. Prefer
  ending the cue on the shot change.
- A caption ahead of its own picture by up to a second is worse than a gap. When
  anchor-nudging starts trading one fault for the other, stop nudging — the cause
  is structural (the read does not fit the film), and say so (decision 103).

**Dead air.** Gaps of 1.5–2.2 s between a caption ending and the next shot
starting read as a fault, not as a pause. The house gate: no gap > 1.5 s. Fix by
trimming shot tails in whole half-seconds off **holds, never off action**
(decision 106), not by re-voicing.

## Bilingual timing

"The pair is the unit" and `PYTHONUTF8=1` are `nj-writer`'s rules (it owns the
words); see `nj-writer/SKILL.md` §6. The director's part is mechanical: **run
`density.py` once per language**, passing that language's `"lang"` and word
count — never reuse one language's beat durations for the other, since a
continuous camera move fixes each beat's wall clock and a longer Arabic line
does not get to borrow a second English one already spent.
