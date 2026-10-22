# The first run — QA Wrap collage cut, 20 September 2026

Why this skill has the rules it has. Clock times are file timestamps.
Output: 1080×1920, 52.0 s, 15.7 MB, 14 scenes, 69 timed cues, one 604-line composition.

## Timeline

| clock | event | lesson → rule |
| --- | --- | --- |
| ~14:25 | prompt: a reel link, a pasted Style-DNA template, "3 files in Downloads", "the version before the latest" | several calls went on working out WHICH film → slot 2 is a path, REQUIRED |
| 14:28 | reel downloaded; the `watch` skill's frame step failed (`-vsync` gone from ffmpeg 8) | → `scripts/ref_sheets.py` uses `-fps_mode vfr` |
| 14:31 | storyboard written; the pace figure was first stated from memory (43 events) and was wrong (69) | → compute N and the longest gap from the Synchronization lines |
| ~14:33 | "go" | built with no notes on the storyboard → the stage 3 gate |
| 14:33–14:38 | an unrelated product fix requested mid-film and done at once | → `PARKED.md`, only "now" interrupts |
| 14:39–14:47 | photo sourcing: HeyGen signed out, Openverse → 1 usable image, Met API → furniture | 3 attempts, 0 assets → sourcing is budgeted, fallback is DRAWN props |
| — | four messages asking about time and tokens; estimate given as 1.5–2.5 h, then 1–1.5 h, then 30–45 min | three estimates caused more confusion than the work → ONE estimate from the table |
| 14:50–15:02 | composition written; lint: 1 error; check: 6 layout errors; all fixed | → `reference/hyperframes-contract.md` |
| 15:02 | one snapshot run, two contact sheets read, three faults fixed in one pass | kept as stage 5 exactly |
| 15:04 | render started in the background | |
| 15:07:51 | MP4 written to `hf/renders/` | |
| ~15:08 | asked "where is the output?"; the background log was empty, concluded it had died, rendered again | → judge a render by the file, never the log |
| 15:10 | second, identical MP4 | 3.5 min of machine time wasted |

Also that day, outside the film but inside the same session: a `git checkout -- .`
during a mutation test wiped uncommitted work and it had to be redone → the git
line in "Not in this process".

## Cost

Prompt → finished MP4: ~43 min. "go" → MP4: ~35 min (≈5 detour, ≈3.5 render).
Session counter, film only: ~135,000 tokens — a floor, not a bill. Largest
shares: skill manuals read (~¼), eight images read, the composition, the
storyboard. The render costs none.

Skipped to save tokens, against the workflow's own rule: `hyperframes-animation`
and `hyperframes-creative`. The budget table makes that an explicit choice now
instead of a quiet one.

## What the result lacked

The references were grayscale PHOTO cut-outs; the film shipped DRAWN props. No
intake asked for a cut-out folder, so there was none. That is slot 1, and it is
the single largest quality lever in this kind of film.

Not checked before delivery: sound, and sync by ear. Still true of stage 6 —
it is reported, not hidden.

## Sources behind the skill's shape

- Anthropic, *Skill authoring best practices*, platform.claude.com, retrieved
  2026-09-20 — degrees of freedom (low for fragile sequences), copyable
  checklists, plan → validate → execute with a machine-checked intermediate
  file, utility scripts executed not read, references one level deep, body
  under 500 lines.
- microsoft/playwright-cli and HeyGen HyperFrames skill docs as installed on
  this machine (0.8.48) — the composition contract and the check gates.
- This log — first-hand, n = 1. Every budget number in SKILL.md is this run's
  actual figure rounded up, not a benchmark.

## Second run, 20 Sept 2026 — kinetic type on cream and black (QA Wrap reel)

- First reference (character animation) was stopped at stage 2 by NOT IN HTML: the gate did its job, nothing was built.
- New narration, voice, word times and 13 product captures were made BEFORE stage 0; the skill had no step for that, so one was added.
- Ledger: GO 1 16:34 -> GO 6 17:08, render done 17:11. About 40 minutes from the new reference to the MP4, 10 scenes, 56.2 s.
- `check` passed on the first run (0 errors); one snapshot pass, five faults fixed in one edit, one render.
- What made it fast: words popped from `words.json` by one builder function, captures shot before the storyboard, no asset hunting.
- Found on the way: whisper absent, so `hyperframes transcribe` skipped; intake_check treats free text in `captures_dir`/`fonts_dir` as a path.

## Third run, 20 Sept 2026 — the commercial, both aspects, full sound

- Five notes on run two became house defaults (SKILL.md, "The house finish"): no dead air, music, SFX per action, whole-product narration, two aspects.
- Silence went from 15.9 s of 56.6 s to 6.2 s of 56.5 s by placing lines on real takes with a 0.35 s rest.
- The TTS PERFORMED the line "Make a request fail on purpose..." (9 s, then 14 s for 12 words). Fixed by rewording to a statement; voice.py now redraws over-long takes.
- One film.html, two frames: words box + 960x900 prop box, CSS variables per aspect. Both checks passed first time; one fix pass covered both.
- The popup will not draw taller than its window: for one picture of a scrolling wall, lift the clip with a style tag and shoot full page.
- The gate was NOT run on this project (it only knew hf/); gate.py now knows hf-v/ and hf-h/ and refuses a page that names a mix that does not exist.
- Mastered: -13.9 LUFS, peak -6 dBFS, both files.

## Fourth run, 21 Sept 2026 — paper-punch collage, REJECTED

the owner: *"it didnt use any assets for motion graphic … i dont want it like the
state it is in now."* Correct: `ASSETS.txt` listed no ids; every prop shipped
DRAWN (CSS/SVG) although `production/library/` held 21 licensed cut-outs,
textures and overlays made that same morning for this style. `STAGES.log`
stopped at `GO 4`: the look and render gates never ran either.

Cost (`STAGES.log` + the receipt): 206,808 worker tokens, 132 tool calls, 18.5
min wall clock — for a film that had to be re-storyboarded and rebuilt.

Root cause: `SKILL.md:194`'s "Missing cut-outs are DRAWN" was an unconditional
build rule, not a fallback — nothing upstream ever asked whether the library
had a candidate. Twelve contributing faults, traced in
`production/test-reel-2026-09-21/DEVIL.md`, fixed in the same pass (worker
`fix-reel-0921`): DRAWN demoted to a named fallback; `style.json`
`material_needs[]` now gates stage 4 (NO-GO without an id or a named
shortfall); `templates/STORYBOARD.md` shipped with a ninth field, `Material`;
a material-lookup step added before the storyboard; `cues.py` prints `FILM
ENDS` and length drift; `gate.py` writes elapsed-per-stage; DNA sections and
the Synchronization format are asserted, not just present; `manim_scene.py`
registers two font roles by the file's own name; the WOFF2 conversion step is
gone (OTF straight from the repo); `hyperframes-contract.md` gained the
`video_nested_in_timed_element` and `sfx is not defined` entries and the stub.

## Fifth run, 21 Sept 2026 — paper-punch collage, five pictures, still REJECTED

The fourth run's fixes held (11/13 reel-1 corrections, see
`production/test-reel-2-2026-09-21/DEVIL.md` §A). But "no pictures" became
"pictures that are not a collage": five opaque rectangles with a hard
drop-shadow, an English-captioned full-colour map under the Arabic end card,
and the same unaudited SFX sample shipping a second time. Fixed in worker
`fix-reel2-0921`: `gate.py` now reads a built page's cut-outs for real alpha
(PNG colour type/`tRNS`, 5–95% transparent share), the torn-edge `clip-path`
or the file's own alpha, and a mandatory tone-to-palette filter class;
`Material` requires a `— because <clause>` tying the picture to the line;
`sfx_check.py` refuses an unaudited-tag cue unless `--allow-unaudited`; three
one-line fixes (`contact-sheet*.jpg` glob, the template's own worked example,
`--with fonttools`); `mix.py` resolves `bed.wav` in two places or `--bed`.
Cost: 185,487 tokens, 116 tool calls, 13.6 min (`STAGES.log`).

### OWNER'S REVIEW — the owner, after watching the delivered MP4, 21 Sept 2026

Verbatim, in the same pass as the devil's findings above:

1. *"the entry of each asset and the outro is not perfect."* — no element had
   a designed entrance AND exit; things appeared at clip start and vanished at
   clip end. Fixed: `reference/choreography.md` rule 1, `gate.py` stage 4/5
   entrance/exit check.
2. *"the illustrations are not really visible and they don't stand out from
   the assets to grab the attention of the viewer."* — the hero cut-out was
   not visually dominant against its own ground once toned. Fixed:
   `reference/choreography.md` rule 2 (hero size/contrast/hold-time),
   `scripts/hero_check.py`, `data-hero` attribute.
3. *"there was 2 types of captions one are on every word and one on motion
   graphic pick one don't have 2 captions."* — Lead's decision: kinetic
   on-picture words ARE the captions for a recorded style; a plain subtitle
   strip is a second, forbidden system in the same film unless
   `PROJECT.md captions: subtitle`. Fixed: `gate.py` refuses both systems in
   one page; `templates/PROJECT.md` gained the `captions:` slot.

These three are now the fifth thing to check before dispatch, next to the
devil's "five to make first": nothing ships with a bare appear/vanish, a
flattened hero, or two caption systems.

## Sixth run — rehearsal-0921, a rehearsal, not a delivery

Resumed after an initial partial pass: ran the FULL seven-stage pipeline, gate before every stage, on a throwaway 2-scene 9x16 Arabic paper-punch/cool film (scratch project under tools/rehearsal-film/). Output: 1080x1920, 9.13s, 3.36 MB, h264+aac 48kHz, out/rehearsal-9x16.mp4. Every stage's own GO line, narration_check.py PASS, library.py plan-check PASS (0 fails), hyperframes check PASS (attempt 3/4), sfx_check.py CLEAN, ebur128 -14.9 LUFS/-2.5 dBTP, ffprobe confirmed.

10 real faults hit and fixed in the skill (not just the scratch project): (1) GSAP CDN hot-link, vendored; (2) bed_pick.py --commit does not copy the bed file, documented and worked around by hand; (3) id-less elements silently skipped by the entrance/exit gate, now reported; (4) hero_boxes.mjs/hero_check.py never wired into gate.py, now gated, plus two bugs found only by running it for real: window.__timelines undefined under a bare file:// open, CSS.escape called in Node not the browser, both fixed; (5) the id-attribute regex matched data-composition-id="main" as id="main" (false positive on #root), fixed with a negative lookbehind everywhere that pattern appeared, including the new checks; (6) check_entrances_exits flagged #root/#cam themselves, containers that are never choreographed, scoped the scan to each scene's own inner HTML; (7) html dir="rtl" on <html> silently produces a blank video render, moved direction: rtl to #root; (8) ASSET-PLAN.md's visual_era: header and plan-check's real scene-line shape, and the separate ASSETS.txt file gate.py actually reads, none named in SKILL.md before this; (9) mix.py crashes on any real library SFX id because load_seed_manifest() only read the pre-cutover bg-music seed manifest, merged in INDEX.json's sfx rows; (10) mix.py reads/writes state beside its own file, so it must be copied into the project like voice.py, never run from the shared skill dir.

One content judgement finding, not fixed (SKIPPED after 2 attempts, per the brief's cap): palette: cool's coral ground-warm token is certified only as a ground colour with ink text on it, never as text itself, and even after toning plus CSS contrast/brightness pushes one scene's hero/ground luminance separation plateaued at 10.9 (need 15), needs a solid backing panel behind the hero, not just a filter, or a cutout with more built-in tonal range; also style.json's own note that coral at high ground share reads as an error colour is a real risk for palette: cool generally, the owner's call. Full write-up, every gate line verbatim, and the NEXT ACTION checklist for the real film: artifacts/ops/rehearsal-2026-09-21.md (ENSERA repo).

Seventh run (pre-film fixes, prefilm-fix-0921): closed the four tooling gaps rehearsal-0921's NEXT ACTION left, proved on a scratch copy of the rehearsal project, no render. (1) scripts/stage_hf.py: idempotent, copies vendor GSAP + mix/voice/words.py into a project right after `hyperframes init`, logs STAGES.log; proved by deleting the four files from the scratch copy, re-staging, check_no_hotlinks clean. (2) bed_pick.py --stage-to <project>: lands the committed bed at hf/assets/bed.wav (mix.py's find_bed second check), selftest gained a positive (file lands, non-empty) and negative (missing source raises) control; proved on the scratch copy, ffprobe confirmed pcm_s16le/192kHz (mix.py resamples to 48kHz itself, no gap). (3) sfx_check.py --manifest is now optional: resolves cue ids and aliases via library/INDEX.json (kind=sfx) by default; selftest gained an alias-resolve control; proved on the rehearsal cue list with no --manifest, CLEAN: 0 rule breaks. (4) hero_check.py/hero_boxes.mjs/choreography.md/film.html: a scene whose ground luminance is above 0.8 gets a solid dark backing shape (data-hero-backing, navy/teal, .hero-backing in film.html) behind the hero; hero_check.py then measures hero-vs-backing and backing-vs-ground separately. Proved on the scratch copy's scene 2: before (no backing) 10.9 (need 15, matches rehearsal-0921's number); after (backing added, one re-snapshot + hero_boxes.mjs + hero_check.py pass) hero/backing 46.0, backing/ground 25.4, both clear 15 -- HERO OK. Also confirmed gate.py's stage-2/3 style-record path resolves library/styles/paper-punch/style.json through NJ_LIBRARY (one-line proof, check_dna: []). The 3 CDN references outside owned paths (library/, production/, nj-kit/) are still not fixed -- next worker's, listed again in artifacts/ops/prefilm-fix-2026-09-21.md.
