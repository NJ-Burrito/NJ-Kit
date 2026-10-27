---
name: nj-narration
description: 'Cast and engineer a TTS voice for any story: casting brief from the character, licensed sources, signal-only rubric, top 3 for the ear; engine, reference prep, caps, one take; mastering chain, loudness, gates, healing. Triggers: voice casting, narrator, TTS voice quality, sound engineering, noise at start or end of lines, Arabic MSA narration, اختيار صوت الراوي.'
---

# NJ-Narration

From "who is this character?" to a clean, mastered take the owner approves by ear.
Words of the script belong to `nj-writer`; a quick master of a human recording is `voice-clean`; music and SFX
sourcing is `bg-music`. This skill owns the voice: who it is, how it is made, how it is mastered, how it is healed.

## Hard rules (never traded away)

- **Clean data only.** CC0, verifiable public domain, a permissive licence with documented consent, or our own or
  talent recordings with written consent. No scraped audio, no public figures, no NC or unclear licences. Full
  provenance with sha256 per reference.
- **One take per line.** No re-voice, no best-of-N, no ASR, no model or LLM that listens, no second TTS.
- **The engine is a recorded owner decision per project.** Paid TTS only on the owner's word. Prefer licensed, local, open-weight engines.
- **Numbers are not ears.** Every gate passes first; the owner's ear decides last. No gate is loosened to pass.
- **Fix at the source**, once, at the stage that owns it. Never hand gain on one line.
- **Never cut a sound or a word short** to remove noise.

## The four jobs

| Job | Read | Tools |
|---|---|---|
| 1. Voice scouting | `references/voice-scouting.md` | `templates/casting-brief.md`, `templates/scout-brief.md`, `templates/rubric.broadcaster-male.json`, `scripts/voice_measure.py` |
| 2. Voice engineering | `references/voice-engineering.md` | `scripts/tts_guards.py`, `scripts/voice_edges.py --no-pad` (references) |
| 3. Sound engineering | `references/sound-engineering.md` | `templates/sound_profile.example.json`, gates table |
| 4. Healing | `references/healing.md` | symptom, measurement, root cause, fix at the source |
| The noise window | `references/noise-window.md` | `scripts/voice_edges.py`, `scripts/tts_guards.py` |

## Scouting in six steps

1. **Brief from the character**: needs, attributes, origins, backstory, region, accent or MSA, the owner's rejections.
   Turn it into numbers: F0 band, timbre (centroid, top band), room (decay), age, pace, energy.
2. **Rubric written before measuring.** Never retuned after a ranking.
3. **Search licensed sources by slice**, one scout per slice (Common Voice splits, LibriVox readers, Wikimedia / Lingua
   Libre, studio corpora with a read licence). Provenance per clip.
4. **Measure with signal metrics only**: `voice_measure.py ref <clip> --edge-fix --rate 24000 --rubric <r.json>`; then again on the edge-cleaned reference you will clone, before the owner listens (edge room tone flatters the first number).
5. **Voice a shortlist** (10 voices x 5 lines, one take each, same settings), trim, master, score the takes.
6. **Top 3 to the owner's ear** on a local preview page. Record the pick; it is frozen.

## Two rules from the 2026-10-27 casting

- A pick that fails REF-QUALITY as cloned is replaced by the next passing candidate in the ranking, never by a looser gate; references under about 5 s are flagged for the owner's ear.
- Mastering keeps the pause distance of the generated take (post-limiter pause floor); a take that fails as generated is regenerated, not rescued.

## The noise window, in one breath

Prevent (per-voice generation cap from measured letters/s, EOS guard after the text is complete, reference edges
cleaned once), then clean every take word-safe (four-feature span, guards, fades inside the guards, span samples
identical, fricative and nasal endings protected), then gate (VOICE-EDGE-NOISE). Details: `references/noise-window.md`.

## Scripts (numpy only; librosa optional for F0; scipy optional for `--rate`)

```bash
S="<plugin dir>/skills/nj-narration/scripts"   # where the nj-kit plugin is installed
uv run --with numpy python "$S/voice_edges.py" measure take.raw.wav            # exit 1 = noise window found
uv run --with numpy python "$S/voice_edges.py" clean take.raw.wav take.wav     # word-safe; --no-pad for a reference
uv run --with numpy --with librosa --with scipy python "$S/voice_measure.py" ref clip.wav --edge-fix --rate 24000 --rubric r.json
uv run --with numpy python "$S/voice_measure.py" take take.wav                 # TAKE-QUALITY
uv run --with numpy python "$S/tts_guards.py" cap "<tts_text>" --slowest 7.08  # token cap + done-after time
uv run --with numpy python "$S/test_nj_narration.py"                           # offline self-test
```

All accept `--profile` / `--limits` with a project sound profile (the calibration schema). Defaults are the calibration project's
calibrated numbers of 2026-10-26; recalibrate per project against the owner's approved and rejected clips.
`PYTHONUTF8=1` always. Output never overwrites input.

## Calibration

The bundled scripts were calibrated on one production pipeline (2026-10-26) and reproduce its numbers. Treat the defaults as a
starting point: recalibrate against clips your own listeners approved and rejected.

This skill ships no voices and no audio. It holds the method, the gates, the templates and the measuring scripts.
