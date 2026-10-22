---
name: nj-writer
description: 'Writes narration and script words: commercials, e-learning, walkthroughs, podcasts, event/recruitment/investor pieces, Arabic or English. Triggers: write the script, narration, voiceover, podcast script, walkthrough narration, e-learning narration, تعليق صوتي, نص بودكاست, نص إعلان.'
---

# nj-writer

Words, structure, voice, the page. **Picture, staging, camera and performance
belong to `nj-director`** — where a rule here touches the image it stops at
"name it or flag it" and points there.

**Every narration rule — wpm, pauses, pitch, delivery, the checker, the
matrix — lives in `NARRATION.md`, the only narration guide. If you find a
narration number anywhere in this file below, it is stale; `NARRATION.md`
wins.** This file keeps only what is not narration-specific: claims/sourcing
discipline, the picture-sync rule, and the script-writing run order.

Voiced narration (Kore, registered styles, first-use rule, gate): `NARRATION.md` §11; registry `voice-styles.json`.

Every rule below traces to a film that failed, in `research/56` decisions
95–120 and `research/113`–`116`. The failures were not taste. They were
arithmetic, a claim nobody could prove, and a line whose object was not on
screen.

## The four things that kill a script

| Failure | Its tell | Rule |
|---|---|---|
| **Fake arithmetic** | a total runtime with no per-beat row; a "silence budget" that appeared without words leaving | Every beat gets a row. §Timing |
| **Written, not sayable** | you can read it but not say it in one breath; a number that is ambiguous aloud | Say it on a stopwatch. §Speakable |
| **Line ahead of its picture** | the line names a thing the frame does not hold *at that second* | Name it or flag it. §Picture |
| **Unfalsifiable claim, no ask** | "fast", "accurate", "powerful"; an end card with a URL and no verb | §Claims |

## 1. Timing — the beat table is the deliverable

Never a total. A total hides a starved beat inside a healthy average — the
v4 treatment claimed "roughly 38 s of speech" at a mandated 140 wpm, which is
really **166 wpm**, an announcer read the same paragraph forbade. Five of nine
beats were over their own runtime and nobody saw it, because only the total
was computed (`research/114` §1).

```
speech_s = words / (wpm / 60)
slack_s  = beat_s − speech_s − lead_in_s − tail_s    # tail on EVERY beat
FAIL if slack_s < 0
```

The implementation is `nj-director/scripts/density.py`; the writer supplies
words and wpm, runs it, and pastes its table. Do not re-derive it by hand.
**And it is an estimate:** a recorded take moves each line by ±0.3 s
(decision 103), so after the voice session the real per-line durations go back
into the table and it is re-run. A film timed only against words ÷ wpm has not
been timed.

wpm targets, budgets and silence ratios by genre/language/destination live in
`NARRATION.md`'s Matrix — read the row there, do not guess a rate here.
**A tired or intimate register is not slower per word — it is more space
between lines.** Space is silence, counted in its own column, never folded
into the rate.

Output shape, per beat: `# | words | speech s | beat s | lead-in | slack |
verdict`. Then one line: total speech, total silence, and the wpm the two
imply. If the implied wpm differs from the mandated one, the table is wrong,
not the read.

## 2. Lines that can be said

Run every line through `references/speakable.md`. Four gates, all free:

1. **Breath** — say it aloud, one breath, no rush. Needs a comma to survive? Cut it in two.
2. **Tongue** — consonant clusters and repeated sibilants across a word boundary.
3. **Numbers** — round and spoken-form ("more than five hundred", not "514"); never two numbers in one line.
4. **Homophones and heard-ambiguity** — the listener has no spelling. No second pass either.

A line that fails any gate is rewritten, not annotated for the voice talent.

## 3. Picture — name it or flag it

**Never write a line whose named object cannot be on screen at that moment.**
Broadcast's "say dog, see dog". Three shipped violations, all found on paper:
"Nineteen tools" over five tiles the spec forbade drawing more of; "in both our
languages" over a sheet at edge-on and illegible; "never leaves your browser"
when no browser is drawn in the film at all (`research/114`).

The writer does not solve these. The writer produces a **violations table** —
`beat | line names | must be on screen at that second | status` — and every
non-clean row goes to `nj-director` as a named question. Guessing what the
picture will do is how the fault ships.

Captions are the spoken words verbatim, and `nj-director` owns that rule in
full (it owns the cue track): `nj-director/SKILL.md` and `timing.md` §Caption
timing. Not restated here.

## 4. Claims and the ask

Claim → proof → ask. Each claim carries a **source**: a file and line, a
decision number, or a counted thing. No source, no claim.

> "In minutes the AI generates the whole script, accurately" was cut because
> *we control the input file, not the model* (`research/116` G6). Unverifiable
> by us = not spoken. Not softened — cut.

The ask is one verb, one concrete action, checkable in the frame. An end card
lost its tagline, ask and URL once and no gate said so (decision 108/110), so:
**write the end-card strings verbatim into the script file**, and hand
`nj-director` an assertion list. Product copy (not spoken) is `impact-copy`'s
job — bold anchor, then an outcome with one true number. Do not restate it here.

Full method, weasel-word list and the substantiation table: `references/claims-and-cta.md`.

## 5. Revising — audit, then cut

A rewrite that reuses the dead draft's sentences is not a rewrite. Before
delivering any revision, run the **recycled-line audit**: pull the previous
version's strings in full, quote them in the new file, and list the closest
contacts with a verdict — including the ones you cleared. An audit that
silently drops its nearest miss is not an audit (`research/116` C12).

Cutting: cut to protect the turn, and **state what each cut costs**. A cut with
no cost line is a cut nobody can review. Where a beat has no spare word, say so
and name the remedy (a re-take, a boundary move) rather than shaving it.
`references/revision-and-voice.md` carries the cut ladder, the cost template,
and the **voice sheet** — how to describe a voice in six fields so another
writer or a recorder can match it.

## 6. Bilingual

Arabic and English are first class. **The pair is the unit**: fixing one side
and leaving the other stale is worse than the original error. wpm ratios,
the pair-drift tolerance and Arabic-specific writing rules are in
`NARRATION.md` §4/§5 — not restated here. Do not translate to time; rewrite
to time. `PYTHONUTF8=1` for anything that touches Arabic on this machine.

## Every narration request

`NARRATION.md` "Every request" section is the run order for narration
(commercial/educational/walkthrough/podcast/event/recruitment/investor):
fill `templates/NARRATION-BRIEF.md`, run `scripts/narration_brief.py`, write
to the rule sheet, run `scripts/narration_check.py`, `no-ai-slop` +
`brand/COPY-CHECKS.md`, `arabic-english-proofreading` for Arabic, voice,
`voice-clean`. Not restated here.

## Run order

The director moves first and the loop closes in two rounds — the handshake
table is in `nj-director` § The handshake. Do not start drafting without a
numbered beat sheet with provisional durations.

1. Beat sheet with runtimes ← from `nj-director` or the brief.
2. Draft lines. **Count words per beat and build the table before polishing a single line.**
3. Speakable gates, aloud, on a stopwatch.
4. Violations table → any non-clean row to `nj-director`.
5. Claims table with sources; end-card strings verbatim.
6. Recycled-line audit against the previous version.
7. Cut to fit, with a cost line per cut.
8. Write the file. `research/NN-script-YYYY-MM-DD.md`. Every stage leaves a file.

A worked example — the QA Wrap commercial, from a broken density paragraph to a
passing table — is in `references/worked-example.md`. Read it before a first script.
