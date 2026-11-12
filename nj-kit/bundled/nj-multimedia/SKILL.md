---
name: nj-multimedia
description: 'NJ-MULTIMEDIA: produce a commercial, launch film, brand film or promo video the way an agency does it: a creative crew and a marketing crew in parallel, a director who merges them into one storyboard, one owner approval on proposal plus keyframe boards, then sound and motion crews in parallel, machine gates, one render per deliverable, and a release kit. Motion graphics only (no screenshots), story before features, every claim sourced. Use for any commercial, promo, ad, launch video, product film, brand film, teaser, reel or explainer made to sell, including when the user says "make it like that video", "the last commercial was boring / static / only screenshots", "I want something alive", "make a crew/agency for the video", or in Arabic: إعلان، فيديو تسويقي، فيديو ترويجي، فيلم إعلاني، كوميرشال، فريق ملتيميديا. Not for user manuals or tutorials of a single task (a manual pipeline, nj-style-film).'
---

# NJ-MULTIMEDIA: a crew that makes commercials

This skill turns a product into a 30–60 s commercial that looks like it came
from a motion-design studio. It is the method behind the QA Wrap commercial
«Cannot Reproduce → Proof Attached» (2026-10-23), which the owner accepted
after he had rejected a screenshot film as "unacceptable". This version keeps
what made that film good and adds the fixes for what went wrong, both then and
in the 2026-11-10 rebuild (`references/lessons.md`).

**What made it good** (keep all five):
1. **Separate minds, one owner for each.** A creative crew and a marketing crew
   work in parallel, each with real research. A director then merges them and
   settles every conflict in writing. No single agent invents both the look and
   the message.
2. **A story, not a feature list.** The film shows one pain the viewer already
   knows. Every feature then appears as a step in one rescue, and the ending
   answers the opening (a bookend).
3. **Drawn, not captured.** There are no screenshots or screen recordings.
   The value is shown through graphic metaphors on one continuous stage that
   is always moving.
4. **Measured craft.** Each technique comes from a reference with a timestamp.
   The music has a set tempo and a drop on a beat. Grid alignment is checked to
   1 px by script.
5. **Every file is a checkpoint.** Each stage leaves files the next stage
   reads, so a revision re-runs one stage, not the film.

## Stages (each one leaves files, and a gate checks them before the next)

Run the gate before every stage. Exit 1 means do not start:
`PYTHONUTF8=1 python <SKILL_DIR>/scripts/mm.py gate <project> <stage>`

```
NJ-MULTIMEDIA progress:
- [ ] 0 intake      BRIEF.md complete                       (mm.py init, then fill it)
- [ ] 1 research    creative/ + marketing/ (parallel crews)  claims.md has a source per claim
- [ ] 2 direction   proposal/ PROPOSAL, storyboard, script.json, DEVIL.md; mm.py fit PASS
- [ ] 3 boards      boards/ one keyframe per beat per aspect + APPROVAL.md "approved:"  ← the one owner stop
- [ ] 4 production  audio/ (sound crew) ∥ build/ (motion crew); timing.json drives the build
- [ ] 5 review      frame_probe.mjs PASS, contact sheets read, review/REVIEW.md "verdict: PASS"
- [ ] 6 render      out/*.mp4, mm.py probe PASS for each, pairs match
- [ ] 7 release     release/ poster, SRT, description with sources; source kept; LESSONS.md row
```

`mm.py init <project>` creates the layout and copies `templates/BRIEF.md`.
The project folder lives **inside the product's repo** (e.g.
`<repo>/film/<film-id>/`), not in a git-ignored scratch folder. The
2026-10-23 HyperFrames source was lost that way and had to be rebuilt by
eye a month later. Keep the source; ignore only the heavy outputs
(`out/`, `audio/*.wav`, renders).

### 0 · Intake

Fill `BRIEF.md` from the user's message, the product's README or changelog,
and its site. Required: the product, the audience, the length, the
**deliverables matrix** (aspects × languages, e.g. 16:9 + 9:16 × EN + AR),
references (videos, sites, the owner's past work), what to emphasise, the
call to action and the end-card lines. Missing required slots go in **one**
question. Everything else has a written fallback in the template.

Decide the deliverables matrix now, not after the master ships. In the
reference run, 9:16 and Arabic were added afterwards and cost a third
production round plus a month of parity fixes. One composition must serve
every aspect (layout variables, never a crop) and every language (RTL
mirroring, an Arabic line map in the script).

### 1 · Research: two crews in parallel

Launch both in one message. Use the briefs in `references/crew-briefs.md`:
fill the `{…}` slots and paste them as written. Each crew plays several roles
and writes one section per role.

- **Creative crew** (creative director, motion designer, graphic designer,
  sound designer) writes `creative/`. Before writing anything it breaks each
  reference video down **measured**: cuts per second, an ease per object type,
  colours sampled from frames, music BPM, and hit points with timestamps
  (`watch` skill or ffmpeg frames). It then studies the owner's own work
  (portfolio, sites, posts) for signature moves. Outputs: `style-dna.md`
  (8–12 named techniques, each with its reference timestamp), `palette-type.md`
  (tokens with contrast computed, the house type scale, the grid),
  `visual-metaphors.md` (10+ drawn metaphors, each with beats and how to build
  it) and `sound.md` (BPM, bar count, drop, resolve, SFX palette).
- **Marketing crew** (strategist, copywriter, brand marketer, audience
  researcher) writes `marketing/`: `positioning.md`, `story.md` (three acts),
  `scripts.md` (three distinct options with a recommendation) and `cta.md`.
  It also writes **`claims.md`**: every factual line that may be spoken or
  shown, with its source (a file:line in the product repo, or a URL with the
  date fetched). A claim with no source does not reach the script. The
  reference run's strongest beat ("ASKED FOR SINCE 2008") came from a sourced
  Jira ticket, and its weakest risks ("one press installs it", "always
  recording") were caught here.

### 2 · Direction, then the devil

The **director** crew merges the two folders into `proposal/`:
`PROPOSAL.md` (1–2 pages: concept name, why the old film failed if there was
one, tone, key techniques with their reference timestamps, the storyboard
table, a self-check against the brief), `storyboard.md` (per beat: elements,
lead move, ease, depth, palette tokens, grid positions, hit points; the times
sum exactly to the length) and `script.json` (format below). Every conflict
the crews flagged is settled in writing with the line that replaces it.

Then run **`nj-kit:devil`** on the proposal (objections ranked by risk, each
with its cheapest test) and write `proposal/DEVIL.md` with the director's
answer to each objection. This replaces the owner's first round of notes. In
the reference run, every note the owner gave after the render (a misaligned
byline, "ree" instead of "free", a boxed logo, a stray mark in the logo) could
have been caught here or in stage 5.

**Fit gate, before any voice call:**
`PYTHONUTF8=1 python <SKILL_DIR>/scripts/mm.py fit <project>/proposal/script.json`
It checks every line's estimated spoken length against its window, using the
language's target wpm (EN 150, AR 115) plus 0.4 s per internal full stop,
and checks the whole film's pace. A FAIL is fixed in the words now, while that
is free. In the reference run, line 1 was voiced too short for its window and
had to be voiced again, which the one-take rule forbids.

### 3 · Boards, the one owner stop

The motion crew builds **keyframe boards**: one still per beat at its key
time, in each aspect, with Arabic mirrored. They go in `boards/` (cheap
HyperFrames stills or `npx hyperframes snapshot` of a first-pass layout).
Show the owner `PROPOSAL.md` and the boards together in one message, with the
script in full. He approves once; record `approved: <date> <who>` in
`APPROVAL.md`. In the 2026-11-10 run, boards reviewed before rendering caught
layout faults that a text-only proposal could not show.

When the owner has delegated decisions ("you decide"), the director approves
and writes the reason in `APPROVAL.md`. The gate accepts either.

### 4 · Production: two crews in parallel

- **Sound crew** writes `audio/`. Narration manifest, then the nj-writer gates
  (`narration_check.py`, `voice_style_gate.py`), then **one voice call per
  line** (house voice, see the defaults below). The takes are then fitted
  deterministically: pauses tightened, then atempo up to the cap, then a start
  allowed to slide up to 0.15 s; never voiced again. Then the music bed (CC0
  library first via `nj-kit:bg-music`, ffmpeg synthesis as the fallback, never
  a music model), SFX on the storyboard's hit points, the mix at about −14 LUFS
  with the bed about 12 dB under the voice. Outputs: `timing.json` (start and
  end of each line, each SFX hit), `mix.wav`, `LICENCES.md`.
- **Motion crew** writes `build/`, one HyperFrames composition for every
  aspect and language (load `hyperframes`, `hyperframes-core`,
  `hyperframes-animation`, `hyperframes-keyframes`, `hyperframes-creative`).
  Each text and logo element that must sit on an axis carries
  `data-axis="center"` (or `left:<px>` / `right:<px>`) so the frame check can
  measure it. Captions are the spoken words, timed from `audio/timing.json`.
  On-screen supers are separate short graphic words. Build first against the
  storyboard times; once `timing.json` exists, sync to it.

### 5 · Review (machine first, then eyes, one fix round)

1. `npx hyperframes check` clean.
2. `node <SKILL_DIR>/scripts/frame_probe.mjs <build>/index.html --times <every beat key time> --font Thmanyah --out review/frames`
   Output: per-time PNGs, then FAIL on any element more than 1 px off its
   axis, any rendered face that is not the house font (Chrome's real platform
   fonts, not the CSS), Arabic on-screen text with tashkeel, tatweel, Persian
   letters, Latin `, ; ?` next to Arabic or Arabic-Indic digits, and any page
   error. It catches the fonts the CSS hides: the shipped English captions
   rendered in a fallback face that nobody had checked.
3. Snapshot strip every 2 s per aspect, with the contact sheet from
   `mm.py sheet`. Look at the sheets against `references/review.md` §A–B
   (static seconds, crowding, two hero accents, caption ghosting, frame 0 and
   the last frame designed).
4. The director writes `review/REVIEW.md`: PASS/FAIL per check with the frame
   time, the rule and the fix. The builder fixes once, re-snapshotting only
   the failed frames. `verdict: PASS` opens the render.

When the film must match a reference cut (a rebuild or a re-language), compare
with **foreground-weighted SSIM and side-by-side pair sheets**, never global
SSIM alone. A dark ground scored 0.957 while sizes, timing and states differed.

### 6 · Render

One render per deliverable, then
`PYTHONUTF8=1 python <SKILL_DIR>/scripts/mm.py probe out/<file>.mp4 --duration <s> --size 1920x1080 --lufs -14 [--pair out/<other-language>.mp4]`
(duration ±1 frame, size, fps, audio present, loudness, and pair parity
between language versions). A later fix to one beat re-renders that beat's
frame range and re-encodes. It never triggers a full re-render. An
audio-only change is a re-mux.

### 7 · Release kit

`release/`: a designed poster frame per deliverable (also used as the banner
or thumbnail), an `.srt` per language from the captions, a post description
that carries the source of every on-screen claim, and the files copied where
the owner asked (site, desktop). Commit the source (`build/`, `proposal/`,
`script.json`, `timing.json`, licences). Append one row to the project's
`LESSONS.md`: what the owner changed, why, and the fix for next time.

## script.json

```json
{ "length": 40.0, "lang": "en", "wpm": 150,
  "silences": [[9.5, 10.0]],
  "lines": [ { "id": "L01", "start": 0.4, "end": 2.1, "text": "Cannot reproduce. Closed.", "style": "story" } ] }
```
Arabic: `"lang": "ar", "wpm": 115`, with `text` plain (as shown on screen) and
`tts` with full tashkeel (voice input only). Brand names stay Latin in both
(`QA Wrap`), and are spoken as in English.

## House defaults (Nader's machine; change them in BRIEF.md § overrides)

| Rule | Value |
|---|---|
| Voice | Kore, `google/gemini-3.1-flash-tts-preview` via OpenRouter, a style per line from nj-writer `voice-styles.json`, **one take per line**, no transcriber, judge or other model |
| Pace | EN 150 wpm; AR 110–120 wpm; atempo fitting with a cap of 1.7×, no re-voice |
| Type | Thmanyah only (Serif Display headlines, Sans/Serif Text body); Cairo banned; house sizes −2 |
| Ground | dark, never pure black; colour means a state (failure / user action / success) |
| Captions | the spoken words exactly, at most two lines, ≥ 0.3 s per word, never straddling a beat change |
| Truth | no real client data; neutral tiles for third-party logos; every number sourced in `claims.md` |
| Crew model | the session's working model; the 2026-10-23 reference run used Opus 5.5 for every crew |
| Browsers | own throwaway profile, headless for checks, closed by whoever opened them |

## Files

- `references/crew-briefs.md`: the six crew briefs, ready to fill.
- `references/craft.md`: directing, motion grammar, pacing, sound and
  Arabic rules (shot sizes, eases per object type, the 40 s pacing profile).
- `references/review.md`: the animatic and render checklists.
- `references/lessons.md`: what the reference runs got right and wrong, and
  which stage fixes each.
- `templates/BRIEF.md`: the intake form with fallbacks.
- `scripts/mm.py`: `init`, `gate`, `fit`, `probe`, `sheet`, `selftest` (stdlib + ffmpeg).
- `scripts/frame_probe.mjs`: seeks the composition and checks frames, the
  1 px axis, rendered fonts and Arabic text (needs `playwright`).

## Not in this skill

Manuals, staff guides and single-task tutorials (a manual pipeline,
nj-style-film). Screen recordings of the product. Music-generation models.
More than one owner stop before the render, unless the owner asks.
