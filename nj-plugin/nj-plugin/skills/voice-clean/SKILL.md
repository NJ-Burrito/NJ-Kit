---
name: voice-clean
description: 'Clean and master spoken voice (voiceover, narration, podcast, reel) to broadcast loudness with ffmpeg only: the Premiere chain EQ, DeEsser, DeNoise, Compressor, Amplify, Limiter in one command. Triggers: fix the audio, clean the voiceover, نظف الصوت, معالجة الصوت, LUFS target.'
---

# voice-clean

One voice recording in, one mastered file out. No paid software, no Premiere,
no subscription — ffmpeg, which is already on this machine.

## The chain, and why each link exists

Taken from a Premiere voiceover chain (Instagram `_ghada.32`, reel
`DdCYyndoNgt`, "How to edit your audio on Adobe Premiere"), read frame by frame
and re-implemented on free filters. Order matters: **subtractive first, gain
last.** Compressing before you cut the mud just makes the mud louder.

| # | Premiere effect | its settings in the reel | free equivalent | why |
|---|---|---|---|---|
| 1 | Parametric EQ — HP band | high-pass ≈ 40 Hz | `highpass=f=80` | kills desk rumble, aircon, plosive thump. 80 Hz for voice; nothing musical lives below it |
| 2 | Parametric EQ — bell cut | −5.5 dB @ 795 Hz, Q 2 | `equalizer=f=795:t=q:w=2:g=-5.5` | the "boxy/muddy" band of a room recording. **Sweep it, do not trust the number** |
| 3 | DeNoise | amount ≈ 50 % | `afftdn=nf=-25:nt=w` (or `arnndn` with a model) | removes steady hiss/fan. Over-applied it makes speech sound underwater |
| 4 | DeEsser | default | `deesser=i=0.35` | tames `س`/`ش`/"s" spikes that the compressor would otherwise pump on |
| 5 | Single-band Compressor | thr −3.8 dB, **4:1**, attack 5 ms, release 100 ms | `acompressor=threshold=-18dB:ratio=4:attack=5:release=100` | evens loud and quiet words. ffmpeg's threshold is measured on the raw signal, so the number differs from Premiere's — the ratio and times are what transfer |
| 6 | Amplify | preset "+6 dB Boost" | `loudnorm=I=-16:TP=-1.5:LRA=11` | a fixed +6 dB is a guess; loudness normalisation is a measurement. This is the one place to *improve* on the reel |
| 7 | Hard Limiter | max −4.0 dB, look-ahead 7 ms, release 100 ms | `alimiter=limit=-1.5dB:attack=7:release=100` | the ceiling nothing crosses. −1.5 dBTP is the platform-safe ceiling; −4 dB is needlessly quiet in 2026 |
| 8 | Panner | centred | `pan=stereo\|c0=c0\|c1=c0` (mono→dual mono) | a voice belongs in the centre; a lopsided mono take is a phone artefact |

## Run it

```bash
python ~/.claude/skills/voice-clean/scripts/voice_clean.py IN.mp4 -o OUT.wav
```

| flag | default | use |
|---|---|---|
| `--target LUFS` | `-16` | `-14` YouTube/Spotify/Instagram, `-16` podcast/web, `-23` EBU broadcast |
| `--mud-hz N` | `795` | the boxy frequency; **sweep before trusting** (`--sweep`) |
| `--mud-db N` | `-5.5` | depth of that cut |
| `--denoise N` | `-25` | noise floor in dB; `0` disables. Less is more |
| `--deess N` | `0.35` | 0–1; `0` disables |
| `--ratio N` | `4` | compression ratio |
| `--ceiling N` | `-1.5` | true-peak ceiling in dB |
| `--preset NAME` | `voice` | `voice`, `phone` (harsher source), `broadcast` (−23 LUFS), `gentle` (minimal processing) |
| `--sweep` | off | renders 8 probe files each with a different band cut, so the ear picks the frequency instead of the internet |
| `--report` | on | prints measured LUFS / true peak before and after |
| `--dry-run` | off | prints the ffmpeg command and stops |

The script **measures** the result with `loudnorm` analysis and refuses to
claim success if the output is off target by more than 1 LU or exceeds the
ceiling. That gate is part of the run, not a second opinion.

## Rules that save takes

1. **Never process the only copy.** Output goes to a new file; the input is
   never overwritten. Keep the raw take forever.
2. **Denoise is not free.** Every dB of hiss removed takes some voice with it.
   If the room can be fixed instead — mic closer, aircon off — fix the room.
3. **Sweep, do not copy numbers.** 795 Hz was that person's room and that
   person's voice. `--sweep` takes 20 seconds and is always more right.
4. **One loudness target per destination**, applied at the very end. Do not
   normalise twice, and do not normalise a stem that will be mixed later.
5. **Arabic speech is sibilant-heavy** (س، ص، ش، ث). If de-essing sounds like a
   lisp, lower `--deess` rather than raising it.
6. **Music under voice**: clean the voice first, then duck the music to it. This
   skill handles one voice track; the ducking lives in the editor or in
   `hyperframes-audio` for a HyperFrames composition.

## When this is the wrong tool

- **Generating** a voice (TTS) or sourcing music/SFX → `media-use`.
- **Mixing inside a HyperFrames composition** (beds, ducking, automation) →
  `hyperframes-audio`.
- **Transcription/captions** → `watch`, or Whisper directly.
- **A hand-drawn, per-word edit** (removing breaths, re-timing phrases) → a
  free DAW: Audacity (simple) or Reaper (evaluation licence, full featured).
  This skill masters a take; it does not perform surgery on it.

## Tooling

`ffmpeg` and `ffprobe` on PATH — already installed here
(`~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg*`). No other
dependency, no API key, no network, nothing paid. `arnndn` needs a model file
(`.rnnn`) from the free `richardpl/rnnoise-models` set; without one the script
uses `afftdn`, which needs nothing.
