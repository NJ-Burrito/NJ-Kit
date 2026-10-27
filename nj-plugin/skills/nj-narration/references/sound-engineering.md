# Sound engineering: the chain, the profile, the mix, the gates

Reference implementation: a production pipeline with a take chain and a mix script
preset `phone-first` (episode mix), `tools/audio_checks.py`, `tools/sound_profile.json`. Measurements behind it:
`research/sound-e01c.md`. For a one-off recording (not TTS) the quick ffmpeg chain is the `voice-clean` skill.

## 1. One profile file for every number

Every level, band, time and limit lives in ONE JSON file with a `why` per value (`templates/sound_profile.example.json`).
Docs name the key (`voice.lufs_target`), code reads the key, nobody types a literal. A number changes only by a profile
edit with the measurement that justifies it. A check limit is never loosened to pass.

## 2. The chain, in order

| # | Stage | What it is for | Rule |
|---|---|---|---|
| 0 | Reference clean (once per voice) | edges trimmed word-safe, high-pass, one gain; logged | no denoise that hurts, no gate |
| 1 | Take edge clean | prevent (gen cap, EOS guard), then remove noise-only edges | the span is never touched (`noise-window.md`) |
| 2 | High-pass | rumble a phone cannot play | 70 Hz deep male, 90 Hz otherwise, Butterworth 12 dB/oct |
| 3 | De-noise (expander) | lower noise between words | downward expander only when pauses sit above the target; never to zero; never inside the speech span; hold and lookahead keep soft onsets and word ends open |
| 4 | Corrective EQ | cut boxy mud (about 315 Hz), lift presence (about 3.15 kHz) toward a tonal target | clamped (6 dB max), never the other way, dead band 1 dB |
| 5 | Conditional de-ess | only a take whose sibilant band is hot | on every take it dulls; Arabic س ش ص is sibilant-heavy |
| 6 | Level + gentle compressor | even syllables | per voice, never on the sum |
| 7 | Per-take level match | narrator and characters at one loudness | `voice.lufs_target` |
| 8 | True-peak limiter | ceiling before the bus | lookahead, static trim guarantees it |
| 9 | Music bed | felt more than heard under speech | band-limited to what a phone plays, a scoop in the speech band, mono-safe (same waveform both sides) |
| 10 | SFX | foley and transitions | level by loudness relative to the voice on the phone simulation, never by file peak; per-sound band limits; duplicates dropped |
| 11 | Ducking | bed and SFX dip under words | computed from the voice stem: fixed depth per bus, lookahead (80 ms), gaps under 0.3 s bridged; no reactive sidechain |
| 12 | Master | one linear gain to delivery loudness | limiter only if true peak needs it; no compressor on the sum |
| 13 | Encode and measure | AAC in the delivered file | measure loudness and true peak again on the AAC: the encode moves peaks |

Why EQ, de-ess and de-noise sit AFTER the compressor in the take chain: compression moved all three in the rehearsal
(mud +1.4 dB, sibilance +2.7 dB, floor up by its own gain reduction). A take already in spec passes untouched, which
makes the chain idempotent: a second pass is a no-op within tolerance (0.3 LU, 0.5 dB TP, 2 dB noise, 1 dB per octave).

Contract on every stage: same length out, no new digital silence, never clips.

## 3. Loudness and true peak

| Destination | Integrated | Tolerance | True peak max | Source |
|---|---|---|---|---|
| Instagram / Facebook Reels | -14 LUFS | 1 LU | -1.0 dBTP | measured on delivered reels |
| YouTube | -14 LUFS | 1 LU | -1.0 dBTP | measured on delivered files |
| Podcast / web | -16 LUFS | 1 LU | -1.5 dBTP | `voice-clean` presets |
| EBU broadcast | -23 LUFS | 1 LU | -1.0 dBTP | EBU R128 |
| Social / film masters (house) | -14 LUFS | | -1 dBTP | house default |

Aim the master under the ceiling (-1.5 dBTP) so the encode has headroom. One target per destination, applied once at
the end; never normalise a stem that is mixed later. A platform with no sourced number is a gap to report, not a guess.
A failing file is never uploaded. Verify with `ffmpeg -af ebur128=peak=true` and `silencedetect` for holes.

## 4. Mix hierarchy

**Voice > SFX > music bed**, in every scene, measured through a phone simulation (mono, band-pass from about 300 Hz),
then earbuds. A cue may lead or follow a word, never cover it. The bed fills pauses; pauses are never digital zero.
No silence gap over the profile limit (0.6 s in the calibration project). Narrator and characters: same level, same closeness,
same room. The quiet heart of a story gets no swell.

## 5. Gates (run every time, none skipped)

| Gate | What it refuses | Tool |
|---|---|---|
| REF-QUALITY | reference: noisy floor, digital-silence floor, low SNR, squashed, muffled, reverberant, gated (zero share), boxy, mains hum, clipped, unvalidated | `voice_measure.py ref` |
| TAKE-QUALITY | take: noise between words (pauses above -24 dB re voice), boxy, clipped, hum, digital-silence gaps inside speech | `voice_measure.py take` |
| VOICE-EDGE-NOISE | noise-only lead-in over 30 ms or tail over 50 ms beyond the guards | `voice_edges.py measure` |
| VOICE-TAIL | a clipped word ending (level at the cut within 24 dB of the peak) or energy in the last 100 ms | the project's voice gate |
| VOICE-MASTER | after the chain: loudness off target over 1 LU, true peak over the ceiling, noise re voice over -40 dB, sibilance over -14 dB, new digital silence | the project's master chain |
| Licence / provenance | any field missing, hash mismatch, banned voice or engine | project gate (for example VOICE-REF, VOICE-BANNED-REF) |
| Mix gates | dialogue clarity on the phone, mono safety, peak and cue over voice, silence gaps, delivered loudness on the AAC | the project's audio checks and compose gate |

A FAIL is fixed at the stage that owns it (`healing.md`), then only that stage and later ones rerun.
The owner's ear comes after the gates pass, never instead of them.
