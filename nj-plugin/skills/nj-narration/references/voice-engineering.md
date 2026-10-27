# Voice engineering: engine, reference, settings, caps, one take

## 1. Engine choice

The engine is the owner's recorded decision, per project, in a research file. Criteria in order: licence of the weights
and of the output (commercial use), the training-data provenance, local and free over paid, the language and register
(MSA with tashkeel input, a dialect), fits the GPU (a 6 GB card in the test setup), then quality by the owner's ear on one
throwaway line per engine.

| Engine | Licence | Notes (calibration project research, 2026-10-23/26) |
|---|---|---|
| Chatterbox Multilingual 0.1.7 | MIT, local GPU, ~3.6 GB VRAM | Arabic among 23 languages, clones from a reference clip. Chosen by the owner's ear 2026-10-24 for the calibration project. Training data "0.5M hours cleaned", source not named |
| SILMA TTS v1 | Apache-2.0 weights, MIT code | MSA with tashkeel input, 150M params, 3 GB VRAM. Rated 1 star "bad" by ear: dropped |
| Habibi-TTS | MSA variant Apache-2.0, Gulf variants CC-BY-NC-SA | base F5-TTS weights CC-BY-NC; dropped |
| XTTS-v2, MMS-TTS, OmniVoice, Fish S1-mini | non-commercial | dropped |
| Azure, ElevenLabs, Polly | paid cloud | best-documented talent consent (Azure); paid, so only on the owner's word |

Install recipe that worked (Chatterbox): `uv venv chatterbox --python 3.11`, `uv pip install chatterbox-tts
--index-strategy unsafe-best-match --extra-index-url https://download.pytorch.org/whl/cu124`, `uv pip install
"setuptools<81"` (perth needs `pkg_resources`). Pre-flight free VRAM and commit memory before loading.

## 2. Reference preparation (once per voice, at casting)

A cloning engine copies the reference's level, compression, noise, room and bandwidth into every take. So the
reference is cleaned once, at the source, deterministically, and logged in its provenance.

1. Decode to WAV mono (24 kHz for Chatterbox). Edge fix for MP3 sources (exact zeros at the edges).
2. Trim room tone at the edges with the word-safe cleaner, no pads:
   `voice_edges.py clean ref.wav ref.clean.wav --no-pad` (one reference clip: 0.53 s before the first word and 0.96 s after
   the last removed; span samples bit-identical).
3. High-pass gently (70 Hz, 2 poles for a deep male; 80-90 Hz otherwise). One linear gain to a reference level
   (-23 LUFS).
4. **No denoise that hurts and no gate.** Measured: ffmpeg `afftdn` on these clips lowered the SNR and created digital
   silence, which REF-QUALITY then refuses. If a reference is noisy, replace it; do not scrub it.
5. Re-measure (`voice_measure.py ref`), record sha256, DSP log and measures in the provenance. This measure is the one that
   counts: the edge-cleaned file you clone, not the clip the judge scored (edge room tone flatters floor and SNR, so a clip
   can pass judged and fail cleaned; `voice-scouting.md` 7). On a fail, pick the next passing candidate; never loosen the gate.

## 3. Per-voice settings

Chatterbox knobs: `exaggeration` (0.25-2.0), `cfg_weight` (0-1), `temperature` (0.05-5). Defaults 0.5 / 0.5 / 0.8.
the calibration project's grave narrator: exaggeration 0.30, cfg 0.30, temperature 0.70, the same for every voice in the search so
the comparison is fair. Settings live in the casting record per speaker; a value outside the legal range is refused,
never clamped silently. Settings change style and stability, not where speech ends: they do not fix tails.

## 4. Generation cap per voice (from measured chars/s)

A take that never emits end-of-speech runs to the token cap, so the cap IS the length of the noise tail.

1. After the shortlist takes exist, measure each raw take: `tts_guards.py rate "<tts_text>" raw.wav` (letters over
   the speech span). Keep the slowest per voice AND per exact reference sha256.
2. Cap per line: `cap = 25 tokens/s x (1.0 s + letters / (slowest / 1.3))`, clamped 50-1000
   (`tts_guards.py cap "<text>" --slowest 7.08`). The 1.3 margin keeps a slower, dramatic reading safe.
   An unmeasured voice falls back to 5 letters/s (the conservative old cap).
3. One 54-letter line: 11.8 s cap before, 10.9 s after. The cap is the bound; the EOS guard is the stop.

## 5. The EOS guard

Chatterbox 0.1.7's AlignmentStreamAnalyzer forces EOS on a long tail (attention on the last 3 text tokens for 200 ms)
or on repetition, and suppresses EOS while attention sits earlier. Attention resting on the 4th or 5th token from the
end is neither, so 14 of 50 judge takes ran to the cap. `tts_guards.install_eos_guard(AlignmentStreamAnalyzer, 30)`
forces EOS 1.2 s (30 tokens) after the analyzer marks the text complete: 6x the package's own rule, so a final word is
never cut. Unit-test it on a fake analyzer (the skill's test does). For another engine, find its stop rule and write
the equivalent; do not patch blind.

## 6. One take, no ASR, no model judge

- One take per line. No re-voice, no best-of-N, no "try again with another seed". Seeds come from the line id.
- No ASR, no transcriber, no LLM or audio model that listens, no second TTS. Gates are offline signal checks.
- New words are a new line (a retext record); the old take stays.
- A bad voice is banned and superseded, not patched per line. Nothing is deleted.
- Post-processing (edge clean, mastering) is not a re-voice and is allowed on the one take.
- The owner's ear is the final check, after the gates, never instead of them.

## 7. Mastering must not close the pauses

The compressor and the limiter lower the loud part, and their gain recovers under every soft frame, so the take's p95 falls
and the pauses do not: the pause distance (soft frames under the p95, inside the speech) shrinks by the gain reduction
(one episode: generated at -24.1 to -24.6 dB, limit -24.0, left the chain at -21.2 to -23.3 dB). Fix once in the chain:

1. Add a **post-limiter pause floor**. Measure the pause distance of the take as generated (before the compressor) and of the
   mastered take. If the master is closer than the original, lower only the frames well under the p95 (ramps inside the soft
   region), in small steps (0.25 dB, capped at 6 dB), and stop at the first step that restores the generated distance.
2. Never raise a frame; words, endings and everything above the line keep their gain exactly. Bypass it when the take has
   fewer than 3 pause frames.
3. **A take that already fails as generated is regenerated at its stage, not rescued here**: the floor restores what the
   engine gave, it does not invent distance. This is the post-limiter pause floor stage.
