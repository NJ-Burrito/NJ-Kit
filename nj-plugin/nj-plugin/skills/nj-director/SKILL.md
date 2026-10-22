---
name: nj-director
description: 'Film direction (not agent delegation — see nj-delegate for that). Plans the PICTURE of a 30–90 s film: beat sheet whose durations sum, per-beat speech-vs-silence run by script, seek-safe camera plan, relative anchors, asserted end card. Triggers: direct this film, shooting treatment, beat sheet, storyboard, camera plan.'
---

# nj-director

**This is film direction — shots, coverage, camera, edit — not agent
delegation.** For the "director" that routes work to workers, budgets and
tiers, see `nj-delegate`; the two share only the English word.

You are directing a 30–90 second animated composition, alone, for the owner. No crew
reads your mind; a renderer reads your file. Every claim you make about time must
be arithmetic someone else can re-run, and every claim you make about the picture
must be checkable against a rendered frame.

**Scope.** Staging, picture, camera, timing, performance. **Words, structure and
the page belong to `nj-writer`** — when you need a line, a caption, a tagline or
an ask, get it from there and treat it as fixed input with a word count. This
skill counts words; it does not choose them.

## The four laws

1. **The picture shows what the narration names, at the moment it names it.**
   Naming a thing is not a mechanism for putting it on screen (QA Wrap decision
   110). Every beat gets a row in the violations table — authored by
   `nj-writer` § 3, answered here (§ `checklists.md` C) — before any asset is
   drawn.
2. **Arithmetic is computed, never asserted.** A treatment that says "roughly
   38 s of speech" when 105 words at 140 wpm is 45.0 s hands the voice recordist
   a wrong number (research/114 §1). Run `scripts/density.py`; paste its table.
3. **Anchor relatively.** A beat, a cue or an end-card element anchored to an
   absolute second dies silently on the first retime — that is exactly how a
   shipped commercial lost its tagline, ask and URL with nothing failing
   (decisions 108, 110). Anchor to *its shot*, and refuse an anchor that falls
   outside it.
4. **Frame(t) is a pure function of t.** No `timeScale`, no wall clock, no
   unseeded random, no mid-render fetch. A playback-rate change is stateful:
   scrubbing to t=46 gives a different frame than a linear render does.

## House rules this film inherits

- Captions are the **spoken words verbatim** — the cards *are* the subtitles, so
  a verbatim film regenerates its cue track from the cards every render, never
  "only when the counts differ" (decision 100).
- **One consistent voice** across the whole set, not per film (decision 98).
- **Product films are shot in the product's dark theme.** The theme is pinned
  before the first paint and re-asserted in the render, not assumed (decision 109).
- **Match the deliverable's language to its audience.** Arabic and English are
  both first class. Product UI that is bilingual by design stays bilingual; the
  narration names it rather than the product being changed to suit the film
  (decision 105).
- **Every expensive stage leaves a file.** Treatment, beat sheet, density table,
  camera plan, asset list, end-card assertion — separate files, so a revision
  re-runs one stage. Never re-derive a stage you already wrote down.
- Build budget: **one render, two maximum.** Verify at the cheapest checkpoint
  that can fail (word count, density script, HTML/JSON grep) before anything
  expensive.

## The handshake with `nj-writer`

The two skills are circular if nobody declares the order: the writer needs
durations to write to, the director needs word counts to time. **The director
moves first and the loop closes in exactly two rounds.**

| Round | Director hands over | Writer hands back |
|---|---|---|
| 1 | Beat sheet: numbered beats, provisional durations, the on-screen noun per beat, the target runtime | Draft lines per beat, word counts, the wpm and its justification, the violations table, the end-card strings |
| 2 | `beats.json` built from round 1's durations + round 2's word counts; `density.py` run; answers to every violation row; the durations that moved and which beat paid | Pre-approved trims, word for word, for every beat under +0.25 s |

A third round means the structure is wrong, not the words — say so and go back
to pass 1 rather than nudging.

**Two handoffs out of this loop, both this skill's to trigger:**

- **The voice session.** After round 2 closes (words + durations agreed),
  invoke `speech` to render the narration — one call per beat's final line,
  built-in voice matched to the voice sheet's six fields (`nj-writer`
  `references/revision-and-voice.md` §3), `OPENAI_API_KEY` set. It must leave
  one audio file per beat (or one file with beat-timestamped markers) named in
  the treatment, plus the measured per-line durations `timing.md` requires fed
  back into `density.py` before pass 8. Then invoke `voice-clean` on that
  output — its own gate refuses a result off the loudness target by more than
  1 LU, so its pass is what "the voice session is done" means, not a listen.
- **Music and the bed.** Once pass 4 (camera plan) is locked, so the runtime
  and per-beat mood are fixed, invoke `bg-music` for tracks by mood
  (`informational` / `challenge` / `motivational` / `deep` / `arabic` /
  `corporate` / `cinematic`, picked per beat from § 2's On-screen column) at
  `--bed-lufs` well under the mastered voice level. It must leave
  `library.json` (licence, credit, retrieval date per track) and, for any
  CC-BY/CC-BY-SA pick, an `ATTRIBUTION.md` — shipping without it is an
  unlicensed use. Both are pass-5 inputs, before the render.

Neither skill is invoked by `nj-writer`; both live on this side of the
handshake because both need a locked runtime before they can start.

## The pass order

Each pass writes a file and stops. Do not start the next pass by re-opening the
previous one's reasoning.

| # | Pass | Produces | Gate before moving on |
|---|---|---|---|
| 1 | **Concepts** — 2–3 rival treatments, one paragraph each | `NN-concept-*.md` | the owner picks one. Rivals are kept, not deleted |
| 2 | **Beat sheet** — beats, durations, on-screen, camera, line | `NN-treatment.md` § 2 | Durations sum to the target; every beat has an on-screen noun |
| 3 | **Density** — words vs seconds per beat | § 3 + `density.py` output | **Every beat PASS.** A total that passes while one beat starves is a fail |
| 4 | **Camera plan** — position keyframes on one path parameter | § 4 | `p` monotonic, no repeated key, rate table re-derivable in one line |
| 5 | **Artwork + asset list** | § 5–6 | Every named object in § 2 has an asset row |
| 6 | **End-card assertion** — exact strings, sampled frames | § 7 | Written before a frame is authored. Non-negotiable |
| 7 | **Adversarial pass** — run `devil` on your own treatment | `NN-devil-*.md` | Each objection answered in writing or accepted as a named deviation |
| 8 | **Render** | the film | Machine gates inside the run: density, end card, determinism seek-diff |

Pass 7 is not optional politeness. On the QA Wrap commercial it found five of
nine beats breaking the treatment's own placement rule, a call to action that
had never been written down, and a `timeScale` that would not have survived a
seek — all before a frame cost anything.

## References beside this file

- **`timing.md`** — beats, the wpm budget, the PASS rule, relative anchoring,
  caption timing, where the silence goes.
- **`camera.md`** — staging, the line of action, what each move means, lens and
  depth, hold-vs-cut, easing and the animation principles that apply, and how to
  write a camera plan a deterministic renderer cannot misread.
- **`checklists.md`** — the checklists you literally run, and the failure modes
  with their tells.
- **`references/worked-example.md`** — the fault trace and the staging/camera
  calls on the QA Wrap commercial. The words and the density numbers are the
  one worked example, kept only in `nj-writer/references/worked-example.md`.
- **`scripts/density.py`** — `uv run scripts/density.py beats.json`. Exit 1 on
  any starved beat. This is the arithmetic; do not do it in your head.

## Related

- `nj-writer` — the script, the caption text, the ask. Everything verbal.
- `impact-copy` — the shape of a spoken line and its one true number.
- `devil` — pass 7.
- the project's own deterministic gates (contrast script, glyph coverage, layout
  probe) and `web-design-guidelines` — the still-frame defects (contrast, font
  fallback, Arabic coverage) this skill does not look for. (`design-gate` was
  archived 2026-09-19.)
