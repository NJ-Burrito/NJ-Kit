# Changelog

## 2.4.3 — 2026-11-12

- Dead-code sweep. Knip 5 (JS/TS) and vulture (Python, confidence ≥ 90) over the whole repo; every finding checked by hand before a change.
- `pdf-typography`: removed `scripts/--help` and `scripts/--help.pages.json`, a PDF and its page map written by running the renderer with `--help` as the output name; they had shipped since 2.0.0.
- `nj-motion-deck` template: `Root.tsx` takes the frame rate from `theme.ts`'s `FPS` instead of a second literal `30`; `Slide.tsx`'s `Props` type is module-private (only that file uses it).
- `nj-evidence/scripts/kb.py`: two `… if False else None` statements that never ran removed from the self-test.
- `nj-writer/reference/arabic-tashkeel/evidence/corpus.py`: a `re.sub` whose replacement always returned the match (a no-op) removed.
- `tests/test_v3.py`: an unused `import re as _re` removed.
- Left as they are: `arabic-english-proofreading/scripts/pdf-structure.py` `render_page(..., has_table)` keeps its unused parameter (callers pass it; signature kept); the Knip notes from 2.4.2 still hold.

## 2.4.2 — 2026-11-12

- `nj-method` and `nj-kit`: the delegation sections now state the plain working mode (2026-10-30) that replaced NJ Governance v3/v4: the session does the work itself on the normal model; subagents only for real parallel work or a crew a skill defines; `nj-delegate`, `nj-agent-ops`, `nj-supervise` and `nj-director` stay in the kit and run only when the owner names them.
- Knip 5 scan of every JS/TS file (temporary config, scripts treated as entry points, vendored code ignored): no unused files, no unused dependencies. Findings left as they are, with the reason: unlisted `playwright` / `react` / `remotion` / `@receptron/laya` imports are by design (each skill's scripts run inside the user's own project, which supplies them); unused entry exports are public functions the skill docs call or template examples; `general-video/scripts/frame-packets.mjs` imports `../../hyperframes/scripts/lib/frame-packets-core.mjs`, which the pinned upstream `hyperframes` no longer ships — third-party code, reported upstream-side, not patched here.

## 2.4.1 — 2026-11-12

- `nj-method`: the routing table sends commercials, promos, launch and brand films to `nj-multimedia`; other video still starts at `hyperframes` (or `nj-style-film` for a narrated style film). The checkpoint list names the crew folders a commercial adds before the script.

## 2.4.0 — 2026-11-12

- New kit skill `nj-multimedia` (kit now 18 bundled skills; 45 with the installer): an agency-crew method for commercials, launch and brand films. Eight stages, each leaving files a gate checks: intake with a deliverables matrix (aspects × languages decided up front), creative and marketing crews in parallel (measured reference breakdown, style DNA, drawn metaphors, sound plan; positioning, three scripts, a `claims.md` with a source per claim), a director merge plus a devil pass, one owner stop on the proposal and keyframe boards, sound and motion crews in parallel (one take per voice line, fitted deterministically), review, render, release kit. Ready-to-fill crew briefs, a craft reference (stage, shot, motion grammar per object type, pacing profile, voice and captions, Arabic and RTL, 9:16, end card), review checklists and lessons from the reference runs.
- `scripts/mm.py` (stdlib + ffmpeg): `init`, `gate` (refuses a stage whose inputs are missing, a brief with empty required slots, a claim without a source, an unapproved storyboard, an unpassed review or render), `fit` (each line's spoken length against its window before any voice call), `probe` (duration ±1 frame, size, fps, audio, loudness, language-pair parity), `sheet`, `selftest`.
- `scripts/frame_probe.mjs` (Playwright): seeks a HyperFrames composition and fails on an element more than 1 px off its declared axis, a rendered face outside the house font (Chrome's platform fonts, not the CSS), Arabic on-screen text with tashkeel, tatweel, Persian letters, Latin punctuation or Arabic-Indic digits, or a page error. Fixture and self-test included.

## 2.3.3 — 2026-11-10

- `nj-writer` voice gate: a product name registered in `voice-styles.json` under `latin_brands` (an entry lists the forms of one name, e.g. `QA Wrap` and `QA-Wrap`) may stay Latin in `tts_text` of an Arabic narration line, so it is said exactly as in English. `voice_style_gate.py` (`tts_fails(n, vis, tts, brands=())`) exempts such a name from the spell-it-out rule (R-TASHKEEL-008); an unregistered Latin word still fails, and a missing Arabic word still fails. Four self-test asserts added.
- `nj-writer/reference/arabic-tashkeel/kb/rules/tashkeel.md`: R-TASHKEEL-008 names the exception.
- Known, not changed: `voice_style_gate.py --selftest` fails in this repo on the placeholder brand in the sample lines (the visible text says `Acme`, the tashkeel sample still has the original name); it passes on the author's machine. CI does not run it.

## 2.3.2 — 2026-11-10

- `nj-jira/references/bug-template.md`: the evidence rules now say what 2.3.1 changed in `nj-qa` and `nj-jira/SKILL.md`: file names are Arabic `<المشكلة>-<الخدمة>-<التاريخ>-<الوقت>`, made by `nj-qa/scripts/evidence_name.py` (the template still told readers to name files by what they show).
- `nj-qa/scripts/test_nj_qa.py`: the self-check now covers the evidence-name rules (name format, forbidden characters, the 150-character limit, `-2` repeats, refusals that name the file, `report-check` and `preview-check`, and `NJQA_LEGACY_EVIDENCE=1`). It was missing from 2.3.1.
- Not changed: `nj-qa/scripts/creds.py` stays the single-account version. The newer multi-account version reads a schema file and default accounts from the author's review hub, which this repo does not ship, so it cannot run on its own.

## 2.3.1 — 2026-11-09

- Evidence file names are Arabic only, `<المشكلة>-<الخدمة>-<التاريخ>-<الوقت>` (issue, the service's Arabic name, `YYYY-MM-DD`, `HH.MM` in 24 hours, 150 characters at most, `-2` for a repeat in the same minute). New `nj-qa/scripts/evidence_name.py` (CLI and import); `nj_qa.py` `report-check` and `preview-check` refuse any other picture or video name, except in a run imported with `NJQA_LEGACY_EVIDENCE=1`. Documented in `nj-qa/SKILL.md`, `nj-qa/references/lessons.md`, `nj-jira/SKILL.md` and `nj-jira/references/bug-template.md`.
- `nj-qa`: a `blocked` or `cannot-test` note may carry `block_cause` (`data`, `system` or `tool`); the review check refuses any other use. Self-check extended.
- Website: the grouped skill list, its counts and `llms.txt` are generated by `site/_build/build.py` from `.claude-plugin/marketplace.json` and each `SKILL.md`, with the group and the Arabic line per skill in `site/_build/skills.json`. The build fails when a plugin skill has no group or no Arabic line, when the kit list differs from `nj-kit/bundled`, or when a page states a different skill count. CI runs `build.py --check`. The three 2.3.0 skills (`nj-chart`, `nj-qa`, `agent-halo`) were missing from the list; a stale "23 installed by the plugin" was corrected to 27. System fonts only; no font reference remains.
- README: release links and a 2.3.1 section; the NJ-Font section now says plainly that the font is not published yet.

## 2.3.0 — 2026-11-09

- New skills in the plugin (now 27; 44 with the kit installer):
  - `nj-chart`: charts, dashboards and KPI rows on Microsoft's Flint chart engine (MIT, MCP `flint`), with house rules for reading comfort, Arabic and English, light and dark, and offline pages that vendor the compiled backend with its licence.
  - `nj-qa`: an agent-crew method for testing a service's Jira notes on the live system, with route planning, walls and healing, and `scripts/nj_qa.py` enforcing the limits (preflight, leases, plan, report and preview checks; tests in `test_nj_qa.py`). The author's review hub and agent definitions are not included.
  - `agent-halo`: a coloured border and the agent's name on every browser window an agent opens (`halo.js`, `halo_keeper.js`); hidden from screenshots and page text.
- Updated: `nj-jira` (UAT-notes standard and `uat_preview.py`, `file_bugs.py`, `task.py`, a small REST client), `nj-rank` (metrics tab, `team_metrics.py`, existing-task registration, not-a-bug rendering), `nj-delegate` (anti-slowness rules), `nj-method` routing rows, `nj-jira-to-automation` (evidence-bound four-layer checks), `pdf-typography`, `workflow-diagram` (left-to-right only), `bg-music`, `nj-writer`.
- New release gate `scripts/publish-check.py` (with `--selftest`): fails on credentials, known secret formats, private project and people names (English and Arabic), private hosts and IPs, machine paths, long ID-like digit runs, font files and binary or large artefacts. It prints file, line and rule, never the value. CI runs it.
- New `scripts/skill-table.py`: the README's plugin skill table is generated from each `SKILL.md` description; CI fails when it is stale.
- Removed: every font file (the Thmanyah folder under `NJ-Font/` and the website's `site/fonts/`); the site now uses system fonts. Project names, paths, ticket serials and people's names left in earlier files were generalised to placeholders (`PROJ-123`, `ACME`, `<project-root>`).
- Kept private (not published): per-project profiles (`references/<project>.md`), personal team data and the scheduled-task launcher of `nj-rank`, and the author's review hub for `nj-qa`.

## 2.2.0 — 2026-11-07

- `nj-narration`: narration breathes. New `references/breath.md`: split each line after punctuation, voice each segment as its own utterance so the next word starts like a new sentence, and join the segments with breath pauses cut from the voice's own room tone (comma about 0.22 s, `؛`/`:` 0.30 s, `.`/`…` 0.40 s, `؟`/`!` 0.45 s), never digital silence. Short comma segments merge; the inhale is off by default. Each segment is still one take. `SKILL.md` gets a short section and job-table row 12.

## 2.1.0 — 2026-11-07

- `nj-narration` learns to describe a voice by numbers and to build a voice library. New `references/listening.md`: the stack in three layers (measured, model-predicted, inferred) with picks, licences, CPU and 6 GB notes and what failed in practice; reporting rules (basis and confidence on every attribute, never "listened", end with "needs a human ear"); child provenance (acoustics veto and never clear, ages 13 to 16 count as child, provenance recorded with date and basis); an age/gender model with a non-commercial licence is not used; and the hard boundary that these tools analyse source clips only and never judge a generated take, so the one-take rule stands.
- New `references/harvest.md` (separation, VAD, speaker embeddings, cross-clip clustering, picking a 6 to 12 s reference, and the pitfalls hit) and `references/emotions.md` (per-emotion Chatterbox knob table, conditioning on real emotion slices, whisper is not truly supported, gate failures recorded not re-voiced, one voice for several characters with preset variants).
- New `scripts/voice_listen.py`: a generic, CPU-only analyser for one source clip that prints JSON with basis and confidence per attribute and a veto-only child gate. Imports are lazy, so `--help` works with no models installed; the optional praat-parselmouth is GPL-3.0 and is the owner's licence call.

## 2.0.3 — 2026-11-07

- `nj-narration` upgraded with the 2026 research (sources cited in each reference note). New: a direction sheet per character and per line, mapped to the knobs each engine really has (`templates/direction-sheet.md`, `references/direction.md`); a pronunciation lexicon template and a note on where Arabic tashkeel comes from, with the licence and evidence of seven diacritizers and the rule that a diacritizer is a model and therefore an owner decision (`templates/lexicon.example.json`, `references/pronunciation.md`); reference preparation per emotion register (5-8 s, a transcript beside each clip, the REF-QUALITY lessons of a 16-role casting, a child's voice is never cloned) (`references/reference-prep.md`); a commissioned-talent route with a consent record and a recording spec (`templates/consent-record.md`, `templates/recording-spec.md`); an engine decision table with cited prices and dates, including the notice that Chatterbox's README calls it retired since August 2026 (unconfirmed, an owner decision) (`references/engines.md`).
- QA: a deterministic click metric in `voice_measure.py` (report-only until you measure a limit), `voice_declick.py` (ffmpeg `adeclick`, allowed only outside the guarded speech span, speech samples copied back unchanged), `voice_preflight.py` (refuses to load a local model when free VRAM or RAM is short), and a self-test that now builds synthetic known-bad takes and checks every FAIL path, with pyloudnorm as an optional LUFS oracle. GPL-3.0 audio libraries are listed as an owner licence call and not used (`references/qa-tools.md`).
- `SKILL.md` opens with the thirteen-step session checklist. The one-take, clean-data and no-model rules are unchanged; where paid tools regenerate passages, the skill says so and keeps its rule.
- README: one bullet added to the NJ-Narration section.

## 2.0.2 — 2026-10-27

- New skill `nj-narration` (plugin now 24 skills, 41 with the kit installer): cast a licensed TTS voice from a character brief, engineer it once, master it, and heal noise before or after a line without cutting words. Offline numpy scripts (`voice_edges.py`, `voice_measure.py`, `tts_guards.py`), a self-test, templates and five reference notes. It ships no voices, no audio samples and no voice engine; it reads no credential and calls no network service.
- Site (EN and AR) and README: the NJ-Narration section now gives the real install line.

## 2.0.1 — 2026-10-27

Security fixes from the 2026-10-27 audit of this repo and the site.

- `install.py` pins every third-party skill to a commit (`nj-kit/pinned-sources.json`, 13 repositories, 22 skills), fetches that exact commit and verifies it, pins the `skills` CLI (1.7.4) and `playwright` (1.64.1), shows the list and asks once before downloading (`--yes` accepts it). An unpinned source is refused.
- `context7` MCP is pinned to 4.4.4 (was `@latest`).
- `install.py` no longer writes the author's own CLAUDE.md. It writes a neutral template (`nj-kit/templates/CLAUDE.neutral.md`) and only when you have no `~/.claude/CLAUDE.md`. The old `bundled/CLAUDE.md` is removed.
- `export.py` no longer bundles auto-memory or the personal CLAUDE.md by default (`--with-memory`, `--with-personal` are private-migration opt-ins, gitignored), redacts secrets, query strings and the home path in hook commands and MCP args/urls, forces the pinned npm versions, and refuses to write a zip that holds a credential shape. Tests: `nj-kit/tests`, run in CI.
- graphify asset bumped to graphifyy 0.9.70 (fixes GHSA-pcc4-rvhr-2pr8); the skill pins that version and warns to index only trusted repositories.
- `nj_guard.py` inspects the PowerShell tool as well as Bash and blocks `~/.config/<project>/*.env` style paths for helpers. It stays a best-effort, fail-open guard.
- Site (EN and AR): meta Content-Security-Policy with computed script hashes, referrer policy, and a line saying what the installer changes (hooks, status line, env, MCP, neutral CLAUDE.md). The build computes the hashes and fails if a script is not covered.
- CI and Pages actions pinned by commit SHA; `ci.yml` has `permissions: contents: read`.

## 2.0.0 — 2026-10-22

- Trimmed: no client material, no duplicate plugin copies, no archives. `nj-kit/assets-manifest.json` plus `nj-kit/scripts/fetch_assets.py` fetch the heavy parts (graphify package, researcher `sources.db`, tashkeel evidence runs) on demand, sha256-checked. `install.py` restores the plugin from the repo's own `nj-plugin/`.

- First public release: the `nj-kit` plugin (23 skills) and the `nj-kit` installer with its bundled skills.
- All credentials, private hosts and machine paths replaced by environment variables and placeholders.
