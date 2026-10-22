---
name: nj-style-film
description: 'Builds a narrated kinetic-typography film in a visual style taken from supplied references: per-project intake form, Style DNA, storyboard on the voice clock, one HyperFrames composition, render. Triggers: make a video like this reel, style film, فيديو بنفس الستايل.'
---

# Style film: references in, film out, no wandering

A narration and a look go in. A rendered film comes out. The process is fixed,
every stage leaves one file, and the list of things this skill does NOT do is
longer than the list of things it does. That is on purpose: the first run of
this process (`reference/run-log.md`) lost more to wandering than to work.

**Status: run five times on two styles (paper collage three times, kinetic
type twice). Run four REJECTED for zero library assets (fixed). Run five
shipped five pictures but no collage — opaque rectangles, no tone, one
unaudited SFX sample again, no entrance/exit choreography, a flattened hero,
one caption system already (no regression there) — fixed in
`fix-reel2-0921`, owner's three notes in `reference/run-log.md`/
`choreography.md`. Report where this is still wrong.**

## The contract with the person who asked

1. **Seven stages, in order, one output file each.** Before EVERY stage run the
   gate and obey it — exit 1 means do not start:
   `PYTHONUTF8=1 python <SKILL_DIR>/scripts/gate.py <project> <stage>`
   Copy the checklist below into your first reply and tick it as you go.
2. **One estimate, given once**, read off the budget table. Never re-estimate
   unless a stage has failed, and then say which stage and why.
3. **Two questions at most**: missing REQUIRED intake slots (stage 0), and
   storyboard approval (stage 3). Everything else has a fallback written into
   the form. Use the fallback, record it, keep moving.
4. **A message that is a different job goes in `PARKED.md`.** Answer it in one
   line ("parked, after delivery"), append it, continue. Do it after stage 6.
   Only the literal word **now** from the user interrupts the film.

```
Style film progress:
- [ ] 0 intake     PROJECT.md filled, scripts/intake_check.py exits 0
- [ ] 1 cues       CUES.md from scripts/cues.py
- [ ] 2 style      STYLE-DNA.md (template, strict)
- [ ] 3 storyboard STORYBOARD.md, approved or approve: auto
- [ ] 4 build      hf/index.html, `npx hyperframes check` passes
- [ ] 5 look       `python scripts/gate.py <project> 5` GO, one snapshot run, contact sheets read, faults fixed once
- [ ] 6 deliver    `python scripts/gate.py <project> 6` GO, the MP4 exists on disk, path + duration reported
```

No stage 6 GO without stage 5's contact sheets on disk (devil #2). Each `GO`
line carries elapsed-since-previous; delivery timings are a `grep`, never recalled.

## Budgets

The word comes from `budget:` in PROJECT.md (default `normal`). Tool calls are
a runaway cap, not a target. **At a ceiling: stop, report what is left, ask.**

**Only `normal`'s tool-call row is measured — twice now**, run four: 132
calls / 18.5 min / 206,808 tokens; run five: 116 / 13.6 min / 185,487 tokens
(`STAGES.log` both runs). `scripts/cues.py` scales the time estimate by scene
count and prints the sentence to say; you do not compose one. `cheap` and
`best` are still unmeasured ceilings, not promises. The gate writes
`STAGES.log`: the delivery note's timings are read from it, never recalled.
The engine pre-stage (when `engines:` is non-empty) is its own ledger row,
`GO engines`, run before stage 0 and NOT counted against the numbers above.

| | cheap (unmeasured) | normal (measured twice) | best (unmeasured) |
| --- | --- | --- | --- |
| reference images read | ≤ 3 | ≤ 6 | ≤ 10 |
| asset sourcing attempts | 0 — fallback at once | ≤ 2 queries | ≤ 6 queries |
| skills read beyond this one | `hyperframes-core` only | + `hyperframes-animation` | + `hyperframes-creative` |
| `check` runs | ≤ 3 | ≤ 4 | ≤ 6 |
| snapshot runs / sheets read | 1 / 2 | 1 / 2 | 2 / 4 |
| renders | 1 | 1 | 2 |
| workers | 0 | 0 | only if > 8 scenes, 2–3 scenes each, one wave |
| engine-tagged scenes | none | outside cap, per tag (`motion-engines.md`), own `GO engines` row | outside cap |
| total tool calls | 40 (unmeasured) | 116–132 measured | 120 (unmeasured — likely low, see left) |

A `production/library` lookup is not a sourcing attempt — never counted (devil #1e).

## Before stage 0 — only when there is no narration yet

The stages assume a voice track. When the user asks for a NEW narration, make
it first, in this order, and then start stage 0 as usual:

0. Fill `nj-writer/templates/NARRATION-BRIEF.md`, run
   `PYTHONUTF8=1 python nj-writer/scripts/narration_brief.py <brief.md>` for
   the tailored rule sheet, write the script, then
   `PYTHONUTF8=1 python nj-writer/scripts/narration_check.py <script> <brief.md>`
   — it must PASS before `voice.py` is called. Narration rules (wpm, pauses,
   pitch, delivery, the direction string `voice.py` reads) live in
   `nj-writer/NARRATION.md` — the only narration guide, not restated here
   (moved 2026-09-21).
1. Words: invoke `nj-writer`. It leaves `beats.json` (its density table must PASS) and `NARRATION.md`.
2. Voice and SRT: copy `scripts/voice.py` into the project and run it once. It reads `beats.json`,
   voices each line (Gemini TTS through OpenRouter, key read from `~/.config/qa-wrap/openrouter.env`,
   never written), and writes `narration.wav` and `narration.srt`. A long take pushes the next line; it never cuts one.
3. Word times: `scripts/words.py` writes `words.json` from the pauses in each take. It needs no
   speech recogniser (whisper is often absent). Word-by-word type is popped from these times
   ONLY when a scene's Typography Animation names it, not by default (devil #8); `gate.py`
   stage 5 warns if `words.json` exists unreferenced in the built page.
4. Captures the narration names and that do not exist: shoot them once, at 2x, in the theme the house
   rules name, BEFORE the storyboard, so the storyboard describes pictures that exist.
   A changed narration means re-shot captures: never dress old pictures in new words.

## Pre-stage — engine installs (optional)

Once, before stage 0, for engines PROJECT.md § 10 names in `engines:` (fallback:
none) — run each install line from `reference/motion-engines.md` Needs-on-PATH.
Nothing installs after this (see Not in this process).

## The house finish — every film, unless PROJECT.md § 7b says otherwise (owner, 20 Sept 2026)

The first reel came back with five notes. They are defaults now, not options:

| rule | how it is met |
| --- | --- |
| **No dead air.** Rests between lines are 0.35 s, not what the estimate left over | `voice.py` places lines back to back on the REAL takes (`gap` in beats.json). Target: silence under 15 % of the film. A take far over its word count is redrawn by itself (the TTS sometimes performs an imperative line: reword it as a statement) |
| **Music under everything** | `bg-music/scripts/bed_pick.py <project>/PROJECT.md --commit <film-id>` FIRST. **`--commit` does not copy the file** — land it yourself at `<project>/hf/assets/bed.wav` (`reference/hyperframes-contract.md` has the exact steps and why). `scripts/bed.py` (generated) is the named fallback only when `bed_pick.py` finds no match |
| **A sound for: scene/beat boundary (always), a hard cut on the story's turn (usually), a hero word on the line's point (sometimes) — never every element** | write `sfx(12.3, "swish")` or a real `%NJ_LIBRARY%/INDEX.json` sfx id beside the tween it belongs to. **Copy `scripts/mix.py` into the project first**, like `voice.py`/`words.py` (`reference/hyperframes-contract.md` has why). `python mix.py <project>/hf/index.html` resolves `bed.wav`, resolves SFX ids through the library, masters to -14 LUFS into `assets/mix.m4a`. `bg-music/scripts/sfx_check.py --manifest <rows>` gates it (`reference/hyperframes-contract.md` for building `<rows>`); ≤6 cues/10s, ≤1 per beat unless a boundary, no cue inside a spoken word's window. The page plays ONE `<audio>`: the mix |
| **The narration is the whole product** | read it as a new user first (README, every tool's own label, every report tab), then `nj-writer`. One feature only when the user names one |
| **Every element enters and exits on purpose; one hero per scene, unmissable; one caption system** | `reference/choreography.md` — no bare appear/vanish (unless `data-hold` names a cut), hero ≥35% of frame's short side and tone-separated from its ground, `captions:` in PROJECT.md (`kinetic` default, `subtitle` only for footage-led) — never both in one film |
| **Aspects** | a commercial ships 9x16 AND 16x9; a feature short (about 20 s) ships 16x9 only. Both come from ONE `film.html`: copy `templates/film.html` and `templates/build.py`. Every scene is a words box and a 960x900 prop box; the aspect only moves the two boxes (CSS variables on `body.v` / `body.h`). `build.py` fills the word times from words.json and writes `hf-v/` and `hf-h/`. `init`, `BRIEF.md`, `check`, one snapshot pass and one render happen per folder |

## Stage 0 — intake (LOW freedom)

```bash
cp <SKILL_DIR>/templates/PROJECT.md <project>/PROJECT.md      # if absent
PYTHONUTF8=1 python <SKILL_DIR>/scripts/intake_check.py <project>/PROJECT.md
```

Fill every slot you can from the user's message **and nothing else** — do not
go looking through the repo for a better answer than the one you were given.
Exit 1 lists the REQUIRED slots still empty: ask for exactly those, in one
message, then stop. Exit 0: go on. The estimate comes from stage 1.
A slot marked `fallback:` that is empty is NOT a question. Use the fallback and
write one line under `## Fallbacks used`.

## Stage 1 — cues (LOW freedom)

```bash
PYTHONUTF8=1 python <SKILL_DIR>/scripts/cues.py <srt> > <project>/CUES.md
```

CUES.md ends with an `ESTIMATE` line and a `FILM ENDS` line (voice.py's
`END_TAIL`, so the two never disagree — devil #10). **The estimate: quote it
once, never give another.**
No SRT: `npx hyperframes transcribe <audio>` once, then the script. The voice
track is never re-timed, re-voiced or re-cut by this skill. Every time in every
later file is this clock. `gate.py <project> 2` fails past ±10% drift between
`FILM ENDS` and PROJECT.md's `length_seconds` — while changing a line is still
free, not at delivery (devil #3).

## Stage 2 — style DNA (MEDIUM freedom)

For a video reference, do not watch it frame by frame:

```bash
PYTHONUTF8=1 python <SKILL_DIR>/scripts/ref_sheets.py <video-or-url> <project>/ref
```

It prints which sheets to read. Read those and the stills, within the image
budget. Fill `templates/STYLE-DNA.md` **exactly** — six DNA sections, then the
word table. Extract rules, never copy a frame. The user's standing rules
(PROJECT.md § house rules) outrank the reference wherever they collide; say
where they did.

**Then judge whether this style can be built at all**, before a storyboard is
spent on it. The build is one HTML page of DOM, SVG and GSAP:

| verdict | the style is… | what happens |
| --- | --- | --- |
| `BUILDABLE` | flat, typographic, UI-led, geometric, cut-paper with drawn props | go on |
| `BUILDABLE WITH ASSETS` | photo collage, illustration-led, texture-led — the look lives in supplied images | go on only if slot 1 is filled; else say, in one line, that it will ship DRAWN and look flatter, and go on |
| `NOT IN HTML` | 3D, fluid or particle simulation, character animation, photoreal, footage-led | **stop.** Say what it would take instead. The gate refuses stage 3. |

Write the verdict as a line `FEASIBILITY: <verdict> — <reason>` in STYLE-DNA.md.

If PROJECT.md names `style: <name>` and `<library>/styles/<name>/STYLE-DNA.md`
exists (post-cutover: `%NJ_LIBRARY%/styles/<name>/`, or
`<project>/<cutouts_dir>/styles/<name>/` — `production/styles/<name>/` is the
pre-cutover path and is gone), copy it, skip `ref_sheets.py` — a wrong record
is fixed there, versioned; built videos are not re-opened.

## Material, before the storyboard (devil #1g)

`material_needs[]` non-empty: follow `%NJ_LIBRARY%/PROJECT-RESEARCH.md`, then
`python %NJ_LIBRARY%/scripts/library.py find --cutout-only ...` (or plain
`find` for non-cutouts) per need, and write the picks to the project's
`ASSET-PLAN.md` — **needs a `visual_era:` header line and `plan-check`'s own
`- scene: | id: | claim: | relevance: | reason:` shape**, and a separate
`<project>/ASSETS.txt` (one manifest id per line, for `gate.py`'s
`check_material`) — all three undocumented here before rehearsal-0921,
detail in `reference/hyperframes-contract.md`. No candidate -> `PARKED.md`,
never a silent DRAWN. Before the storyboard gate, run
`python %NJ_LIBRARY%/scripts/library.py plan-check <project>/ASSET-PLAN.md --lang ar|en`
and refuse to proceed on FAIL.

## Stage 3 — storyboard (MEDIUM freedom)

One block per scene, `templates/STORYBOARD.md`'s nine fields (`Material`:
manifest ids or `DRAWN: <reason>`), times from CUES.md, window start-to-next-
start. `gate.py <project> 3` prints the PACE line; copy it. Then, unless
`approve: auto`:

> Storyboard at `<path>`. Notes before I build? "go" builds it as written.

Changing a line here costs nothing. Changing a built scene costs a check and a
render. This is the only place the user's taste enters cheaply.

**The engine is chosen here, per scene, and nowhere else.** No tag means HTML +
GSAP. A scene whose `Visual Description` starts with `[engine: svg]` (logo intro,
an icon that draws or morphs), `[engine: manim]` (a diagram that explains: nodes,
flows, axes), `[engine: theatre]` (one hand-curved hero move), or `[engine:
remotion]` (a data-driven template scene, many rows, same layout) is built the
way `reference/motion-engines.md` says. Tag a
scene only when the default would cost real hand-placing; most films need none
of the four. Remotion's licence is confirmed for Ensera's headcount —
`reference/motion-engines.md` has the record; re-check if headcount changes.

## Stage 4 — build (LOW freedom on structure, HIGH on drawing)

Read `hyperframes-core` (SKILL.md body only) and `reference/hyperframes-contract.md`
— the second is the list of failures the first run actually hit. Then:

```bash
npx hyperframes init hf --non-interactive --example=blank --skill=general-video
```

**Straight after `init`, write `hf/BRIEF.md`** with `workflow: general-video`,
`flow: automation`, `storyboard: no`, and the message, aspect, language and
length from PROJECT.md. The HyperFrames router's own rule is "BRIEF.md exists →
ask no brief questions": this file is what stops it pulling you into its
interview. Do not invoke `/hyperframes` or `/general-video`; you are already
past everything they would ask.

- ONE `index.html`, scenes as `<section class="clip scene">`. Sub-compositions
  only under `budget: best`. The lint warnings about file size are accepted.
- Straight after `init`, run `python scripts/stage_hf.py --project <project>`
  (idempotent, re-runs safely) — it copies `templates/vendor/gsap.min.js` to
  `hf/assets/gsap.min.js` and `scripts/mix.py`/`voice.py`/`words.py` into the
  project root, and logs a `STAGE assets` line in `STAGES.log`. Never hot-link,
  never fetch at render; GSAP loads from `hf/assets/gsap.min.js`, never a CDN
  URL. Gate: `check_no_hotlinks` in `gate.py` fails a built page with an
  `http(s)://` URL outside a comment.
- **A cut-out `material_needs[]` calls for is an image from
  `%NJ_LIBRARY%/images/cutout/<category>/` with a record showing `has_alpha: true`
  in `INDEX.json` (`library.py find --cutout-only`)** — not merely filed under
  `cutout/`. DRAWN is the fallback only when the library has none,
  named under `## Fallbacks used` (devil #1 — was the default, not a fallback).
- An engine-tagged scene builds text via that engine's two-role font
  registration (`brand/DESIGN.md` §2) — `templates/manim_scene.py`.
- Loops (tables, fans, rings, counters) are built by deterministic JS at load.
- A scene tagged `[engine: manim]` or `[engine: remotion]` is pre-rendered to an
  alpha WebM, `ffprobe`d, copied into `hf/assets/` and placed as a video clip;
  one render per tagged scene, outside the film's render budget. `[engine:
  theatre]` loads `templates/theatre_scene.html` (core only, never studio) as
  an in-page clip, driven from the GSAP timeline — no pre-render; the agent
  writes the state JSON itself. `[engine: svg]` adds one read of
  `hyperframes-keyframes` (not under `cheap`).
- `npx hyperframes check` until it passes. Fix what it names; do not redesign.
- Entrances, exits and the hero follow the style record's `entrance_exit_map`
  and `hero_treatment`; the style's demo is the reference for how they should
  look. **Folding (unfold-in, fold-out, page-turn) is the `paper-punch`
  signature by the owner's choice, 2026-09-21.**
- Every clip and picture carries an `id` (the template and this SKILL.md
  require it) — the entrance/exit gate only sees elements that carry one, and
  `gate.py` reports (never silently passes) an element it could not check for
  lack of an `id`.

## Stage 5 — look, once

One `npx hyperframes snapshot --at <one time per scene>`; read the contact
sheets it writes, not the frames. List the faults, fix them in one edit pass,
run `check` once more. Do not take a second look under `cheap` or `normal`.
Also write each scene's `data-hero` box to `snapshots/hero-boxes.json`
(id/x/y/w/h) via `scripts/hero_boxes.mjs` (Playwright, headless, seeks the
master timeline to each scene's hero-hold time per
`reference/hyperframes-contract.md`) and run `scripts/hero_check.py` per scene
(choreography.md #2); `gate.py`'s `check_hero_gate` fails a scene with no
`data-hero` element, a missing `hero-boxes.json`, or a scene absent from it —
run before stage 6, not merely documented (hole 4, rehearsal-0921).

### Stage 5b — score the stills against the brief (one gate, same single run)

Ideas from @0xMovez's X article of 2026-10-01 (ideas only, no copied text).
The contact sheets above are scored, not just read: write
`snapshots/score.md` with one row per scene, a 1-10 score against each line of
the director's brief below, and the three worst faults of the sheet. Any score
under 8 is fixed in the same one edit pass, before the full render. This is a
model gate on stills inside the single run, never a second human look and never
a second snapshot pass: score once, fix once, render. Faults still under 8 after
the fix go in PARKED.md and the report.

Director's brief skeleton (`hf/BRIEF.md` carries it, one line each): logline;
the reference frames; tools and engines; beat sheet on the voice clock; the
stage gates; deliverables, with the score table and the contact sheet named.

## Stage 6 — deliver

```bash
npx hyperframes render --output ../<name>.mp4
```

Foreground. **A render is judged by the file, never by the log**: `ls` the MP4
and `ffprobe` its duration and streams. If you ran it in the background and the
log is empty, look for the file in `hf/renders/` before you do anything else.
Report: path, size, duration, what was NOT checked (sound, sync by ear), which
fallbacks were used. Then `PARKED.md`, if it has anything in it.

## Not in this process

Each of these happened on the first run or nearly did. None is allowed without
the user asking for it by name:

- hunting for a better source file than the one named in PROJECT.md
- more asset-sourcing attempts than the budget row allows
- reading a skill, doc or web page not named in the budget row
- fixing, refactoring or committing anything outside `<project>/`
- a second estimate, a progress essay, or a cost lecture — one line if asked
- a second render "to be safe"; a second snapshot pass under `normal`
- inventing on-screen words the narration does not say (unless PROJECT.md allows)
- spawning workers under `cheap` or `normal`
- installing anything after stage 0; signing in to anything; if a sign-in is missing, use the fallback
- `git checkout -- .`, `git stash`, or any repo-wide git command while a film is in flight

## Files

- `templates/PROJECT.md` — the intake form; copied into every project, filled per project
- `templates/STYLE-DNA.md` — the strict shape of stage 2
- `templates/STORYBOARD.md` — the strict shape of stage 3, nine fields including `Material`
- `reference/hyperframes-contract.md` — the rules that fail a first build
- `reference/run-log.md` — the first run, timed, with what it cost and why
- `scripts/gate.py` · `scripts/intake_check.py` · `scripts/cues.py` · `scripts/ref_sheets.py` — run, do not read
- `scripts/stage_hf.py` — run once, right after `hyperframes init`; stages gsap.min.js + mix/voice/words.py into the project
- `scripts/voice.py` · `scripts/words.py` — only for a new narration; copied into the project (by `stage_hf.py`), run once
- `scripts/bed.py` · `scripts/mix.py` — the generated bed, the mixer, six legacy generated house sounds (no licence to clear, `%NJ_LIBRARY%/sfx/` post-cutover); category-matched SFX now come from `%NJ_LIBRARY%/INDEX.json` (`library.py find --alias <old-id>` resolves an old seed id, CC0, per-file provenance), gated by `bg-music/scripts/sfx_check.py`
- `templates/film.html` · `templates/build.py` · `templates/bed.cues.json` — the two-aspect film, worked: copy, then replace the scenes
- `evals/scenarios.json` — four scenarios to run a FRESH agent through before trusting a change to this file
- `reference/motion-engines.md` · `templates/manim_scene.py` · `templates/theatre_scene.html` ·
  `templates/theatre_author.html` · `templates/remotion/` — the per-scene engine choice (GSAP + SVG,
  Manim, Theatre.js, Remotion + Tailwind), faults each one hit, and licence limits

Needs on PATH: `python`, `ffmpeg`, `ffprobe`, `node`/`npx`; `yt-dlp` only for a URL reference;
`manim` (`uv tool install manim`) only for `[engine: manim]`; `npx esbuild` (fetched on
demand) to bundle `@theatre/core`/`@theatre/studio` to browser ESM for `[engine: theatre]`;
one `npm install` inside `<project>/remotion/` for `[engine: remotion]`.
