---
name: nj-narration
description: 'Cast and engineer a TTS voice for any story: casting brief from the character, licensed sources, signal-only rubric, top 3 for the ear; direction sheet, pronunciation lexicon, reference prep, commissioned-talent consent; engine, caps, one take; edge clean, mastering chain, loudness, gates, healing. Triggers: voice casting, narrator, TTS voice quality, direction sheet, pronunciation lexicon, tashkeel, sound engineering, noise or clicks at start or end of lines, Arabic MSA narration, اختيار صوت الراوي.'
---

# NJ-Narration

From "who is this character?" to a clean, mastered take the owner approves by ear.
Words of the script belong to `nj-writer`; a quick master of a human recording is `voice-clean`; music and SFX
sourcing is `bg-music`. This skill owns the voice: who it is, how it is directed, made, mastered and healed.

## How a session runs (the checklist)

1. **Casting brief** from the character (`templates/casting-brief.md`), owner-approved, frozen.
2. **Rubric** written before measuring (`templates/rubric.broadcaster-male.json`); never retuned after a ranking.
3. **Scout** licensed sources by slice, provenance per clip (`references/voice-scouting.md`, `templates/scout-brief.md`).
4. **Measure** signal-only, on the edge-cleaned reference you will clone (`voice_measure.py ref`).
5. **Shortlist voiced once** (10 voices x 5 lines, one take each, same settings), trimmed, mastered, scored.
6. **Owner ear**: top 3 on a local preview page. The pick is recorded.
7. **Freeze** voice, reference (sha256), engine, settings, generation cap.
8. **Direction sheet** per character and per line, written before voicing (`templates/direction-sheet.md`); lexicon and tashkeel (`templates/lexicon.example.json`).
9. **Preflight** memory and VRAM (`voice_preflight.py`), then **voice once** per line with cap and EOS guard.
10. **Edge clean** (`voice_edges.py`), click check (`voice_measure.py take`), declick outside the span only if needed.
11. **Master** (chain in `references/sound-engineering.md`), pause floor last.
12. **Gates**, none skipped: REF-QUALITY, TAKE-QUALITY, VOICE-EDGE-NOISE, VOICE-TAIL, VOICE-MASTER, provenance.
13. **Owner ear**, last. A fail is fixed at its source stage (`references/healing.md`), never by a retake.

## Hard rules (never traded away)

- **Clean data only.** CC0, verifiable public domain, a permissive licence with documented consent, or our own or
  talent recordings with a written consent record. No scraped audio, no public figures, no NC or unclear licences.
  Full provenance with sha256 per reference. **A child's voice is never cloned**: an adult actor performs the child register.
- **One take per line.** No re-voice, no best-of-N, no ASR, no model or LLM that listens, no second TTS. New words are a new line.
  (Some paid tools regenerate passages until they are right: that is the re-voice we forbid; the rule stays.)
- **The engine is a recorded owner decision per project.** Paid TTS only on the owner's word. Prefer licensed, local, open-weight
  engines. The Chatterbox README says it was retired in Aug 2026 (fetched 2026-11-07, not confirmed by a second source): staying on it
  or leaving it is an owner decision, not a silent switch (`references/engines.md`).
- **A diacritizer is a model**, so adopting one is an owner decision. Until approved, tashkeel is written by the writer stage.
- **Numbers are not ears.** Every gate passes first; the owner's ear decides last. No gate is loosened to pass.
- **Fix at the source**, once, at the stage that owns it. Never hand gain on one line.
- **Never cut a sound or a word short** to remove noise.

## The jobs and where to read

| Job | Read | Tools |
|---|---|---|
| 1. Voice scouting | `references/voice-scouting.md` | `templates/casting-brief.md`, `scout-brief.md`, `rubric.broadcaster-male.json`, `scripts/voice_measure.py` |
| 2. Reference preparation | `references/reference-prep.md` (registers, 5-8 s, transcripts, REF-QUALITY lessons, children) | `voice_edges.py --no-pad`, `templates/provenance.example.json` |
| 3. Talent route | `references/engines.md` section 4 | `templates/consent-record.md`, `templates/recording-spec.md` |
| 4. Direction and pronunciation | `references/direction.md`, `references/pronunciation.md` | `templates/direction-sheet.md`, `templates/lexicon.example.json` |
| 5. Engine and generation | `references/engines.md`, `references/voice-engineering.md` | `scripts/voice_preflight.py`, `tts_guards.py` |
| 6. Sound engineering | `references/sound-engineering.md`, `references/qa-tools.md` | `templates/sound_profile.example.json`, gates table |
| 7. Healing | `references/healing.md` | symptom, measurement, root cause, fix at the source |
| 8. The noise window | `references/noise-window.md` | `voice_edges.py`, `tts_guards.py` |

## Using the direction sheet

One sheet per character, written with the owner before anything is voiced and frozen once approved; a short block per line only
where it differs. Say it in words (affect, tone, pace, emotion, pauses, emphasis), then map each word to a knob the engine really
has (Chatterbox: `exaggeration`, `cfg_weight`, `temperature`, the reference, the text; ElevenLabs v3: audio tags; and so on in
the sheet's section 3) and delete what has no knob. No opposing instructions, no persona the owner did not ask for, tags only if
the engine documents them. A settings trial is one throwaway line at casting, one take per setting, the owner picks, the pick is
frozen; it is never repeated per line. Details and sources: `references/direction.md`.

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

## Scripts (numpy only; librosa optional for F0; scipy optional for `--rate`; ffmpeg for declick)

```bash
S="<plugin dir>/skills/nj-narration/scripts"   # where the nj-kit plugin is installed
python "$S/voice_preflight.py" --need-vram-gb 3.6 --need-ram-gb 6              # 0 fits, 1 short, 2 NOT_MEASURED
uv run --with numpy python "$S/voice_edges.py" measure take.raw.wav            # exit 1 = noise window found
uv run --with numpy python "$S/voice_edges.py" clean take.raw.wav take.wav     # word-safe; --no-pad for a reference
uv run --with numpy --with librosa --with scipy python "$S/voice_measure.py" ref clip.wav --edge-fix --rate 24000 --rubric r.json
uv run --with numpy python "$S/voice_measure.py" take take.wav                 # TAKE-QUALITY + click count (report-only)
uv run --with numpy python "$S/voice_declick.py" take.wav take.declicked.wav   # adeclick outside the guarded span only
uv run --with numpy python "$S/tts_guards.py" cap "<tts_text>" --slowest 7.08  # token cap + done-after time
uv run --with numpy --with pyloudnorm python "$S/test_nj_narration.py"         # offline self-test (pyloudnorm optional)
```

All accept `--profile` / `--limits` with a project sound profile (the calibration schema). Defaults are the calibration project's
calibrated numbers of 2026-10-26; recalibrate per project against the owner's approved and rejected clips.
`PYTHONUTF8=1` always. Output never overwrites input. GPL-3.0 audio libraries (pedalboard, matchering, Parselmouth) are not
used: an owner licence call (`references/qa-tools.md`).

## Calibration

The bundled scripts were calibrated on one production pipeline (2026-10-26) and reproduce its numbers. Treat the defaults as a
starting point: recalibrate against clips your own listeners approved and rejected.

This skill ships no voices and no audio. It holds the method, the gates, the templates and the measuring scripts.
