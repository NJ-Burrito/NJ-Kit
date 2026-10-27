# The noise window before or after a line

> "When the voicing of a sentence starts, a small window sometimes appears before or after with noise only, no words;
> it is distracting and makes the sound quality poor." (the owner, 2026-10-26)

The rule: remove it, and prevent it, **without cutting any sound or word short.** Proof that it can be done:
the calibration project's edge proof (33 takes: noise-only tail 5450 ms before, 0 ms after; the edge gate
failed 3 before, passed 33 after; the speech samples were identical in 33 of 33).

## Why it appears (measured, calibration project 2026-10-24/26)

1. **The model runs past the text.** A token TTS that never emits end-of-speech generates until its cap; the vocoder
   turns the run-on into a low mumble, then hiss. 14 of 50 judge takes ended exactly at the cap (one line of the test set: words end at
   6.76 s, file ends at 11.8 s).
2. **The old trim took noise for speech.** An energy-only trim counted a low drone (loud enough, no formant band) and a
   loud breath burst (flat noise loud enough to skip a hiss test) as words, and kept a 3.97 s tail.
3. **The reference carried room tone at its edges** (0.63 s / 1.15 s), and a cloning engine reproduces it.
4. The mastering chain is not a cause, but its make-up gain lifts whatever edge noise is left: clean edges BEFORE it.

## Account for it: prevent, then clean, then gate

| Layer | What | Tool |
|---|---|---|
| 1. Generation cap per voice | cap from the line's letters and the voice's measured slowest rate, with a 1.3 margin | `tts_guards.py cap` |
| 2. EOS guard | force end-of-speech 1.2 s after the engine marks the text complete | `tts_guards.install_eos_guard` |
| 3. Clean reference edges | once at casting: trim room tone word-safe, no pads | `voice_edges.py clean ref.wav out.wav --no-pad` |
| 4. Word-safe edge cleaner | every take, before the mastering chain | `voice_edges.py clean take.raw.wav take.wav [--text "..." --letters-per-s N]` |
| 5. Expander, not a gate | lowers noise only in the pauses, never inside the speech span, never to zero | the project's chain (the denoise stage) |
| 6. The gate | VOICE-EDGE-NOISE: lead over 30 ms or tail over 50 ms beyond the guards fails | `voice_edges.py measure` (exit 1) |

## How the cleaner stays word-safe

- **The span is found from four features, not energy alone**: frame energy, F0 voicing (autocorrelation AND a formant
  band share AND near the speaker's median pitch, so hum and drones are not voice), spectral flatness and zero
  crossings (a fricative piles energy high with many zero crossings; a hiss is flat).
- **Core, then extend.** Voiced runs form the core; stray runs far under the loud part are dropped. The core is
  extended outward through attached frames: loud ones, voice-shaped energetic ones, fricatives above the floor, and
  periodic decays at the speaker's pitch (final م ن, a soft ه). So word-initial and word-final consonants such as
  س ش ف ث ز ه and a final م are inside the span.
- **Guards**: 100 ms kept before the onset, 200 ms after the offset (a decay, a release, a fricative tail).
- **Fades inside the guards only**: equal-power 20 ms in, 60 ms out, and only where something was cut.
- **No frame of the span is scaled or removed.** The tool checks `span_samples_identical` and exits 1 if not.
- **Run-on detection is text-aware.** With `--text` and `--letters-per-s`, a voiced run that starts after the line
  must be spoken, after a 0.4 s pause, is the model running on and is dropped. Without it no run is dropped for position.
- **Pads**: clean digital-silence pads (80 ms / 150 ms) go on takes, never on references.
- **Never in place**: the output never overwrites the input; the raw take is kept forever.

## Known limits

- A genuine soft word after a 0.4 s pause and 12 dB under the loudest speech can be read as stray: write such a beat
  as its own line.
- A word the model itself cut off cannot be repaired offline: VOICE-TAIL reports it, the owner decides (no re-voice).
- The detector is tuned on adult speech at 24 kHz (F0 60-400 Hz). A child's or a very high voice needs `f0_range_hz`
  checked in the profile, with a measurement, before use.
