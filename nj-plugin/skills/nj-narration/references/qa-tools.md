# QA and mastering tools: what was adopted, what was refused, and why (research 2026-11-07)

Filter: signal processing and small deterministic analysers only. A tool that is a model (a denoiser with a weights file, a
neural VAD, a cloud leveler) is excluded by the one-model rule. A tool that rewrites samples inside the speech span is
excluded by the span contract (`noise-window.md`).

## 1. Adopted

| Change | Where | Notes |
|---|---|---|
| Click metric | `voice_measure.py` `click_stats`, part of the `take` profile | Deterministic, numpy only. A click is a sample whose second difference exceeds 15 times the median of its own 10 ms block, exceeds 0.02 of full scale, and stands alone (3 times the largest second difference within 2-25 ms either side, so a periodic pitch pulse does not count). Reported split into inside speech and in pauses. **Report-only: `max_clicks` is None until a threshold is measured on your own approved and rejected takes; no threshold is guessed.** The constants were checked on synthetic fixtures only, not on real takes |
| `adeclick` repair, gated | `voice_declick.py` | ffmpeg filter (parameters read 2026-11-07: window 55 ms, overlap 75%, burst 2, threshold 2). Allowed only outside the guarded speech span: every sample inside `[onset - lead guard, offset + tail guard]` is copied back from the original, so `span_samples_identical` holds by construction. Kept only if the click count falls; run once per take; the input is never overwritten. This is repair of a take, not a re-voice |
| pyloudnorm as a test oracle | self-test `test_lufs_oracle` | MIT, BS.1770-4 integrated loudness, **no true peak**. The test requires agreement with ffmpeg `ebur128` within 0.1 LU on a seeded signal; it skips cleanly when pyloudnorm or ffmpeg is absent (`uv run --with numpy --with pyloudnorm python scripts/test_nj_narration.py`). True peak stays with `ffmpeg -af ebur128=peak=true` |
| Known-bad fixtures | self-test `test_known_bad_fixtures` | Synthetic speech-like takes generated in the test (no downloaded audio), each with one fault: clipped, low-passed (boxy), hiss between words, a digital-silence gap, a click. Each must trip its own TAKE-QUALITY check, so every FAIL path is exercised and no limit can be loosened silently. Note: the mains-hum check did not trip on synthetic 50 Hz tones in this pass, so no hum fixture is claimed |
| Memory and VRAM preflight | `voice_preflight.py` | Refuses to load a local model when free VRAM (nvidia-smi) or RAM and commit memory (OS) is below the engine's measured need; an unreadable value is NOT_MEASURED and refuses. Idea from a local-TTS skill's `mem_need_gb` field (read 2026-11-07), with our own numbers: the engine needs about 3.6 GB VRAM on a 6 GB card |

## 2. Not adopted

| Tool | Reason |
|---|---|
| ffmpeg `afftdn`, `afwtdn`, `anlmdn`, noisereduce, SoX `noisered` | change speech samples; our chain touches only pauses |
| `arnndn`, RNNoise, DeepFilterNet, Silero VAD, Auphonic, iZotope Dialogue Isolate | models or paid cloud; excluded by the one-model rule (Silero's licence also reads MIT in text and CC BY-NC in a badge) |
| ffmpeg `adeclip` | the gate refuses clipped takes on purpose; a repair would hide the fault |
| ffmpeg `deesser` | same parameters as the chain's own conditional de-esser |
| SoX trims, `silenceremove` | `voice_edges.py` already trims with the span contract |
| py-webrtcvad | licence not stated on the page; possible test-only span cross-check later |

## 3. GPL-3.0 tools: an owner licence call

pedalboard (compressor, limiter, convolution), matchering (reference matching) and Parselmouth/Praat (F0, intensity) are
GPL-3.0 (or later), verified on each repository page. Shipping or distributing a tool that links them needs a licence
decision by the owner first. They are not used. Matchering also works against the once-per-voice casting rule (it reshapes
each voice toward a reference), and pedalboard duplicates the existing chain; only its convolution (room match) is new.

## 4. Open items

- ffmpeg `speechnorm`/`loudnorm` parameters were not read; Windows status of RNNoise, SoX, noisereduce, Silero and iZotope RX
  was not stated on the pages read; Auphonic pricing was not retrievable.
- Plosive and breath measures (low-band burst at word onset, broadband energy in pauses) have no deterministic tool; a small
  custom report-only measure is possible. Not built.

## Sources

ffmpeg-filters documentation (ffmpeg.org); github.com/csteinmetz1/pyloudnorm; github.com/spotify/pedalboard; github.com/sergree/matchering;
github.com/YannickJadoul/Parselmouth; github.com/iver56/audiomentations (considered; the fixtures here are hand-built instead, to
add no dependency); github.com/xiph/rnnoise; github.com/Rikorose/DeepFilterNet; github.com/snakers4/silero-vad. All read 2026-11-07.
