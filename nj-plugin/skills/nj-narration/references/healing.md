# Healing steps: symptom, measurement, root cause, fix at the source

Rule: a fault is fixed once, at the stage that owns it (reference, casting, engine settings, profile, chain, library,
plan), so every later line inherits the fix. Never by hand gain on one line, one cue or one episode. Never by
re-voicing. Never by loosening a gate. A bad voice is banned and superseded, not patched.

Measure first: `voice_measure.py ref|take <wav>`, `voice_edges.py measure <wav>`, `ffmpeg -af ebur128=peak=true`.

| Symptom (heard) | Measurement | Root cause | Fix at the source |
|---|---|---|---|
| Hiss or noise in every take of one speaker | take pause_rel above -24 dB; reference floor above -53 dBFS | the reference carries it; the engine clones it | replace the reference (or a gentle logged clean); ban the bad one |
| Take clean as generated, noisy pauses after mastering | pause distance (p95 minus pause median) smaller on the master than on the raw take | compressor and limiter lower the loud part; soft frames keep their gain | post-limiter pause floor that lowers only soft frames until the generated distance is back (`voice-engineering.md` 7); a take that fails as generated is regenerated, not rescued |
| Reference passes judged, fails as cloned | REF-QUALITY floor above -53 dBFS or SNR under 35 dB only after the edges are cut | edge room tone flattered the judged measure | measure the edge-cleaned reference before the owner hears it; walk to the next passing candidate; never loosen the gate (`voice-scouting.md` 7) |
| Noise only in the pauses of some takes | pause_rel near the limit on a few takes | engine noise between words | the chain's expander (only above target, never to zero, never inside speech) |
| Noise-only window before or after the words | `voice_edges.py measure`: lead_noise_ms / tail_noise_ms | model run-on past the text; old trim mistook a drone or breath for speech; room tone at reference edges | `noise-window.md`: gen cap, EOS guard, reference edges, word-safe cleaner, gate |
| Muffled, dull | REF top_db under -58 dB; low centroid | low-passed or MP3-damaged reference; over-denoised | a full-band reference; remove the denoise step |
| Boxy, honky on a phone | centroid under 400 Hz; mud band high re speech | room mode in the reference; no mud cut | corrective EQ toward the target (cut only, clamped); or replace the reference |
| Reverberant, distant | decay20 over 0.15 s (approved 0.05-0.12) | the reference room | a dry reference; reverb cannot be removed honestly |
| Harsh "s", lisp after de-essing | sibilance over -14 dB; or dull after | hot sibilant band; or de-esser on every take | conditional de-ess only on hot takes; lower the depth rather than raise it |
| Uneven loudness between lines or speakers | per-take LUFS spread | no per-take level match | per-take level match to `voice.lufs_target` before the bus |
| Pumping, breathing under the narrator | gain curve of the sum swings (an old mix: 20 dB) | compressor on the sum or reactive sidechain ducking | per-source compression; ducking computed from the voice stem with fixed depth |
| Pitch wobble, creak read as "deep" | F0 octave jumps; pyin floor share over 0.15 | creaky reference or noise; a pyin artefact | do not score it as deep; pick another reference |
| Long tails, mumble after the line | take ends at the token cap; tail_window large | no EOS: the model ran on | gen cap from measured rate; EOS guard; edge cleaner |
| Clipped words, cut endings | VOICE-TAIL: level at the cut within 24 dB of peak; span shrinks after cleaning | trim too tight; a fade over speech; or the model itself cut the word | guards and fades inside guards only; protect fricatives and final nasals; a model-cut word is reported, the owner decides (no re-voice) |
| Clicks at the start or end | a step at the cut | a cut with no fade | equal-power fades inside the guards |
| "Digital silence" failure on a clean clip | zero_frac over 2 % with zeros only at the edges | MP3 decode / encoder padding (Common Voice) | edge-fix the measurement input; never loosen the limit |
| Digital silence inside speech | gate_gaps over 0 (runs of 20 ms of exact zeros) | a noise gate or denoiser ran on the reference or in the chain | remove the gate; replace a gated reference |
| Mains hum | hum_db over 40 dB | the recording's power line | replace the reference; a notch only if logged and measured |
| Music inaudible on a phone yet loudness spent | bed energy under 200 Hz; phone-sim bed LUFS far under voice | bed built for headphones | bed band-limited to what a phone plays, speech scoop |
| Effects as loud as the words | cue loudness re voice on the phone sim | SFX gain from file peak; stacked duplicates | loudness-relative SFX levels; dedupe; fix the plan that stacks cues |
| Mix collapses in mono | mono loss over 1 LU; correlation p05 under 0.2 | detuned or out-of-phase stereo | same waveform both sides; width from slow swells |
| Too quiet or loud on a platform | delivered AAC LUFS / dBTP | master target or encode headroom | profile `master.*` and `delivery.*`; measure on the AAC |
| Wrong pronunciation of a word | (by ear only; no ASR) | the vowelled TTS text | fix `tts_text`, voice it as a new line; the old take stays |

When nothing in the table matches: write the symptom, the measurement and the stage you believe owns it in the project's
research folder before changing anything.
