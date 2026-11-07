# Changelog

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
