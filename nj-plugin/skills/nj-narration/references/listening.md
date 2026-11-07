# Listening: how an agent describes a voice it cannot hear

An agent reads numbers; it does not hear audio. This note says which tools produce those numbers, how to report them,
how to gate children, and where the whole thing stops. Research date 2026-11-07; the stack was then run on 24 harvested
voices (CPU only). Grades: measured (a script computed it), model (a classifier returned it), inferred (the agent's wording).

## 0. The hard boundary

- These tools analyse **SOURCE clips only**: a candidate reference, a harvested slice, a clip being screened before it is chosen.
  They run once, before any generation.
- They are **never a judge of generated takes**. No MOS predictor, emotion classifier, ASR or audio-LLM runs over a
  generated line to accept, reject or re-voice it. The one-take rule stands (`SKILL.md` hard rules); the owner checks finished audio by ear.
- The same model (for example UTMOSv2) is allowed on a source clip and forbidden on a take. The rule is about where it sits in the pipeline.
- Do not wire any of this into the render path.

## 1. The stack, in three layers

Honest headline: no single local model writes a casting sheet in Arabic on 6 GB with a commercial licence. The practical
stack is signal measurements plus a few small specialists; the agent writes the prose from their numbers.

### Layer 1: measured (deterministic, language-free, the only layer that is really measured)

| What | Tool | Notes from the run |
|---|---|---|
| F0 median and p10-p90 range, voiced fraction | Praat via parselmouth | confidence high only for clips of 5 s or more with at least 20 % voiced |
| F1 to F3, vocal-tract length | Praat Burg formants | from running speech, not sustained vowels: confidence med at best. VTL uses F2 and F3 only; F1 gave 24 cm on an adult woman and was dropped |
| jitter, shimmer, HNR | Praat | raspy and breathy proxies, med |
| spectral centroid, LUFS, peak, clipping %, crude SNR | librosa, pyloudnorm | SNR is a percentile estimate (low): clips with no pauses read low |

Licence: parselmouth is **GPL-3.0**. It is used here only as a local analysis step, nothing is bundled or redistributed, and
using it is the owner's licence call (see `references/qa-tools.md`). `scripts/voice_listen.py` imports it lazily and, when it is
missing, still reports centroid, loudness and clipping and says the child gate has no input.

### Layer 2: model-predicted (a classifier returned it; say which model and licence)

| Pick | Gives | Licence | Notes from the run |
|---|---|---|---|
| `badrex/mms-300m-arabic-dialect-identifier` | 5-way dialect: MSA, Egyptian, Gulf, Levantine, Maghrebi | CC-BY-4.0 | 0.3 B, ran on CPU; 80.73 % on its MADIS-5 card. Up to 5 windows of 8 s from the longer file. Trained on TV speech: read speech drifts to MSA with p above 0.95. Call dialect "med" only when the top probability is at least 0.8, otherwise "low" and leave the summary field empty. Five-way only: no Algerian versus Moroccan |
| Audiobox Aesthetics (CE, CU, PC, PQ) | production quality of a source clip | CC-BY-4.0 | ran on CPU; feed a tensor, because file loading needs torchcodec |
| DNSMOS P.835 (SIG, BAK, OVRL) | noise and overall quality; splits "bad voice" from "noisy room" | code MIT, model-file licence UNVERIFIED | CPU, onnxruntime. A first download saved a corrupt file (protobuf error): re-fetch and check it loads |
| UTMOSv2 | a clean-speech score | MIT badge | trained on synthetic-speech ratings, so on a human clip it is not a casting score. All values read low (1.0 to 3.4): left out of the quality tier |
| SpeechBrain VoxLingua107 | language ID | Apache-2.0 | only to catch a wrong-language clip |

CPU/6 GB notes: everything above ran on CPU in its own virtual environment, about 6 s per clip for UTMOSv2, so the GPU and the
voicing environment were never touched. Audio-LLM captioners (Qwen3-Omni 35 B, Step-Audio 2 mini 8 B, Qwen2.5-Omni) do not fit
6 GB and have no verified Arabic voice-attribute evidence: not used. Audio Flamingo (non-commercial), ParaSpeechCaps (non-commercial,
English), Kimi-Audio (English and Chinese) and any hosted service are out. Check licences again before shipping anything.

### Layer 3: inferred (the agent's words)

"Warm", "raspy", "bright", "high register" are the agent's reading of layer 1 and 2, written as `basis: inferred` and never as an observation.
Gender comes from F0 (below 150 Hz male, above 185 Hz female, in between decide by F3 and VTL, confidence low). Age band stays a
low-confidence label unless the clip's provenance states it.

### What failed in practice

- Age from audio: the only strong local age model is non-commercial (section 4), so there is **no age model** in the stack. The
  F0/HNR rule gives a decade band at confidence low.
- Dialect probabilities below 0.8 are common on phone-like or read speech; most were "unsure". Do not force a label.
- A reference clip can sit 3 to 4 semitones away from the same voice's longer recording. Measure both and flag it.
- UTMOSv2's downloader needs `wget`; fetch the weights from the model hub into the cache folder instead.
- Whether two clips are the same performer is not settled by an embedding score or by F0. Report "not settled", keep them separate, ask a human ear.

## 2. Reporting rules

1. **Never say "I listened".** Say "the script measured" or "the classifier returned". Say "heard" only about the owner.
2. **Basis and confidence on every attribute**: `{value, basis: measured|model|inferred, confidence: high|med|low}`.
   High only for measured values on a long enough clip; med for dialect with top p at least 0.8; low for age, emotion, timbre words, VTL and any language a model was not tested on.
3. Print the model id, licence and clip length beside each model result. Under about 3 s: say outputs are unreliable.
4. Keep the three layers separate in the report: measured, then model, then inferred.
5. Quote unverified items as unverified (thresholds, DNSMOS weight licence, Arabic accuracy of every model).
6. **End every description with "needs a human ear."** The final casting choice is the owner's.
7. Never score a generated take with these tools (section 0).

`scripts/voice_listen.py` produces this JSON for one source clip (`--no-models` for measurements and the child gate only). The agent reads the JSON, nothing else.

## 3. Child provenance

No published tool or paper separates a real child from an adult performing a child. So:

- **Provenance is the gate.** Without a documented adult source and consent, the clip is not cloned (`references/reference-prep.md`).
- **Acoustics veto but never clear.** The heuristic in `voice_listen.py` adds points for F0 median at or above 300 Hz, F3 at or above 3100 Hz, F1 at or above 650 Hz, VTL at or below 13.8 cm (two points at or below 13.0), and a male label with F0 at or above 190 Hz. It blocks at 3 points, or 2 with F0 at or above 300 Hz.
  The thresholds are a reading of published ranges and are **not validated on Arabic**.
- Allowed verdicts: `blocked: child signal`, `blocked: no provenance`, `no acoustic child signal; provenance documented`. Never "adult confirmed" or "not a child" from acoustics.
- **Ages 13 to 16 count as child.** Voices change between about 11 and 15 and overshoot at 13 to 15, so a teen can read as adult. A clip labelled teenage with adult-like formants is still blocked until provenance is documented.
- A false block is the safe error: a small adult woman, a voice actor or falsetto can trip it. A real child with a low voice can pass, which is why a pass means nothing.
- Treat a block as final until provenance says otherwise. Do not clone a blocked clip, do not pitch-shift it into an adult.
- **Owner provenance is recorded with date and basis**: who said the speaker is an adult performer, on what date, on what basis (a written statement, a source page, a consent record). Update the voice's record; a chat remark that does not start with the project's amendment marker is not applied.

## 4. Not used: audeering age-gender

`audeering/wav2vec2-large-robust-24-ft-age-gender` gives age and a child class, locally and small, but its licence is
**CC-BY-NC-SA 4.0 (non-commercial)**. It is not used. Whether screening counts as commercial use is the owner's decision; until
then the child gate is the heuristic above plus provenance. Its reported age error is 7 to 11 years anyway, larger than the child/adult boundary.

## 5. Gaps (not verified)

Per-class child accuracy of any model; Arabic behaviour of every classifier; real VRAM and runtime beyond the CPU run; DNSMOS
and emotion2vec weight licences; F0 and formant tables by age; any real-child versus adult-imitator figure. A rehearsal on a few
known adult clips and a few licensed, consented child clips would measure the child gate before it is trusted.
