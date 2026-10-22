# Timing: words to seconds, per beat

## Rates, and how to justify one

| Read | wpm | When |
|---|---|---|
| Tired, intimate, held | 120–130 | dread beats, a first-person confession |
| Unhurried conversational (**house default**) | **140** | QA Wrap films; no announcer lift |
| Corporate / explainer | 155–165 | tutorial narration where nothing is sold |
| Hard-sell broadcast commercial | 170–185 | not the house voice; listener fatigue past 5 min |
| Arabic, MSA narration | **~120** | BBC Institute of Journalism figure vs 180 English |

Sources: `references/../nj-writer-SOURCES.md` rows 1–4.

Write the justification **in the file**, one sentence, naming the register.
Rev 3 of the QA Wrap treatment does this well:

> 140 wpm = 2.333 words/s. The rate of an unhurried conversational read with no
> announcer lift, and the rate the voice direction mandates. Do not record at
> 160+; the concept dies.

## The arithmetic

```
words_per_second = wpm / 60          # 140 wpm -> 2.333
speech_s         = words / wps
slack_s          = beat_s - speech_s - lead_in_s - tail_s
```

**Every beat carries a tail, not only the last one** (default 0.5 s; the end
card 2.2 s). This is not the writer's arithmetic to keep in its head:
`nj-director/scripts/density.py` is the single implementation and the only
table that ships. Run it, paste it, and put the editorial verdict column
(below) beside its PASS/FAIL. A hand-computed slack that disagrees with the
script is wrong by definition.

**Lead-in** is the seconds a line waits after its beat opens. If the treatment
mandates one (QA Wrap: 0.5–1.5 s, midpoint 1.0), it is part of the arithmetic,
not a note. Omitting it is how five of nine beats passed a check they failed:
against speech alone only beat 7 was negative; with the mandated 1.0 s lead-in
and the 2.2 s tail on the last beat, beats 1, 2, 3, 7 and 9 all broke
(`research/114` §1).

**Tail** is the silence the end card holds. It is protected: the tail is what
keeps the call to action on screen. Seconds never come out of the tail.

## The table

| # | Words | Speech s | Beat s | Lead-in | Slack | Verdict |
|---|---|---|---|---|---|---|
| 1 | 8 | 3.43 | 3.2 | 1.0 | −1.73 | **starved** |
| 4 | 12 | 5.14 | 8.0 | 1.0 | +1.36 | ok |
| 7 | 20 | 8.57 | 7.5 | 1.0 | −2.57 | **starved** |

(Slack includes the 0.5 s default tail. The `research/114` figures quoted
elsewhere — −1.23, +1.86, −2.07 — predate the tail term and are kept only as
the historical devil-pass numbers.)

Verdicts: `starved` (< −1.0 s), `crammed` (−1.0 to 0), `ok` (0 to +1.5),
`healthy` (> +1.5). More than +4 s on a beat is its own fault — the picture is
carrying a beat the words abandoned; tell `nj-director`.

Footer line, mandatory:

> 105 words = 45.0 s of speech in 50.5 s. Silence budget 5.5 s. Implied rate 140 wpm.

If someone states a silence budget larger than `runtime − speech_s`, they have
confused **placement with duration**. Placement moves speech; it does not
shorten it. This is the single most expensive error in the archive: whoever
records the voice works from the wrong number and the take is unusable.

## Redistribution before rewriting

Total slack positive but beats failing = a **distribution** problem, not an
over-written script. Move seconds from an adjacent healthy beat first; state
which beat lent them. Two constraints:

- A continuous camera move fixes each beat's wall clock — non-adjacent slack
  cannot be lent. Ask `nj-director` before assuming it can.
- Never take seconds from the end card's tail.

Only when redistribution fails do words leave. Then: §Cutting in
`revision-and-voice.md`.

## Bilingual timing

One table per language. Set `"lang": "ar"` in `beats.json` — the script then
defaults to 120 wpm and **refuses** Arabic text with no stated rate.
 Never reuse the English table for the Arabic script:
Arabic reads ~20–30 % slower per word and translated Arabic usually grows in
word count. If the Arabic overruns, **rewrite the Arabic to time** — do not
speed the read, and do not compress by dropping the claim that the English
side makes. The pair must say the same thing or neither ships.
