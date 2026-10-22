# SFX practice — numbers a script can check

Written for `scripts/sfx_prep.py` and `scripts/sfx_check.py`. Every number is
either measured (this run, `nj-style-film/assets/sfx`, 2026-09-21), sourced
(dated below), or `house default, to be tuned by ear` — never presented as
more certain than it is. Contradictions between sources are kept separate,
not averaged (per brief rule 2).

## Finding 1 — measured cause of "too loud" in `nj-style-film`

`scripts/mix.py` builds three stems: voice (`loudnorm=I=-16`), bed
(`loudnorm=I=-24` then sidechain-ducked ~8 dB under the voice), and **SFX,
which get neither loudnorm nor ducking** — `sfx.wav` is mixed into
`amix=inputs=3:normalize=0` at whatever gain the six generated WAVs already
have (`mix.py` lines 60-67, confirmed by reading the filter graph; the module
docstring's "Levels (bg-music rule)" table only covers voice and bed).
Measured today (`ffmpeg -af ebur128=peak=true`, `volumedetect`) on the six
files in `assets/sfx/`:

| file | integrated LUFS | true peak dBFS | duration |
|---|---|---|---|
| logo | -28.7 | -5.0 | 2.00s |
| reveal | -23.4 | -9.0 | 0.62s |
| sting | -21.2 | -4.9 | 1.30s |
| success | -27.3 | -9.0 | 0.85s |
| swish | -70.0 (gate never opens, see Finding 2) | -12.0 | 0.38s |
| tick | -70.0 (same) | -16.0 | 0.03s |

Two distinct faults, both real: (a) the six files are 7+ LU apart from each
other with no per-category ceiling, so whichever plays loudest that scene
sets the perceived SFX level for the whole film; (b) none of them is ducked
or loudness-matched against the voice/bed group before the final
`amix(normalize=0)` + `alimiter` + master `loudnorm=I=-14`, so a hot SFX can
ride over the limiter's gain-reduction the voice/bed group already absorbed.
**"Too loud" is a mixing-graph gap, not a level number** — the gap is what
`reference/sfx-practice.md` + the mix.py patch (see
`artifacts/production/sfx-style-film-patch-2026-09-21.md`) closes.

## Finding 2 — why per-file peak/LUFS normalisation misleads on short SFX

EBU R128 integrated loudness gates on 400ms blocks (Wikipedia, "EBU R 128",
retrieved 2026-09-21) — a clip shorter than that **cannot** produce a valid
integrated reading; `ffmpeg -af ebur128` reports the -70 LUFS silence floor
for `swish` (0.38s) and `tick` (0.03s) above, not because they are quiet but
because the meter never gates. Measured directly in this run: `sfx_prep.py`'s
selftest hit the identical floor on a 0.5s test tone before the fix. The
practitioner explanation (search summary, retrieved 2026-09-21, on peak vs.
loudness normalisation): peak-normalising a short transient and a sustained
tone to the same dBFS peak makes the sustained one read louder to the ear,
because "human hearing responds to average energy over time, not isolated
peaks" — the inverse problem from R128 gating, same root cause (duration-blind
metering). **What to normalise to instead, for one-shots under ~400ms:** RMS
(mean) level via `volumedetect`, which stays valid at any duration — this is
what `sfx_prep.py` matches to, with an `alimiter` peak safety net at -1 dBTP.

## Finding 3 — measured cause of "crude" and "out of place"

`nj-style-film`'s house rule is literally "a sound for every action on
screen", and each of the six sounds is a single synthetic sample reused for
every occurrence of that action — no variation, no pitch/gain jitter, and
they are generated tones, not recordings of anything physical. Against a
`paper-punch` visual style (flat paper cut-out, stop-motion cadence), a dry
UI blip has no material referent: nothing paper, tape, or card ever made that
sound. That is the "out of place" complaint's measured cause: a style/asset
mismatch, not a level problem, and no gain change fixes it — only a palette
swap (`sfx-palettes.md`) does.

## Level table (per category, RMS dBFS in `sfx_prep.py`, voice at -16 LUFS)

| category | target (RMS dBFS) | ~offset vs voice | source |
|---|---|---|---|
| impact | -18 | louder, punchy | house default, mid-point of the -10..-20 dBFS SFX band a short-form mixing guide gives relative to dialogue at -6..-12 dBFS (Tem.Polor, "Audio Levels for Film, Video", retrieved 2026-09-21) — that guide uses dBFS peak, not RMS/LUFS; unit mismatch disclosed, not resolved, hence "default to be tuned by ear" |
| whoosh | -20 | matches voice roughly | house default |
| tick / UI | -26 | well under voice | house default — ticks are dense and repeat, so kept low to avoid Finding 1's stacking problem |
| paper / foley | -22 | just under voice | house default |
| riser | -24 rising to -18 at peak | builds toward voice | house default; risers are dynamic by design, this is a floor/ceiling not a flat target |
| ambience | -30 | well under everything | house default; **no free ambience source was fetched this run** (budget), category defined but unseeded — see plan file, risk 1 |
| stinger | -16 | most prominent, rare | house default; used sparingly, see density rule |

The Tem.Polor guide's dialogue/music/SFX split (dialogue -6..-12 dBFS, music
-20..-30 dBFS under speech, SFX -10..-20 dBFS) is the only outside source
found for a numeric split; it measures dBFS peak on a DAW meter, not
integrated LUFS or RMS, so it is directional evidence (SFX sits near or just
under dialogue, well above the bed) not a number to copy verbatim — folded in
above as a sanity check on the house defaults, disclosed as such.

## Ducking

House rule (from `mix.py`, unchanged): bed ducks ~8 dB under voice, attack
20ms / release 420ms (sidechaincompress, ratio 5). SFX duck **less and
faster** — house default 3-4 dB, attack 5ms / release 150ms — because a
transient under 300ms is masked less by the ear than a sustained bed, and a
slow release on a short SFX would smear into the next word. `house default,
to be tuned by ear`.

## Variation (kills "crude")

- Never the same sample twice within **8 seconds** (`MIN_REPEAT_GAP_S` in
  `sfx_check.py`) — deterministic: seed the pitch/gain jitter from
  `hash(cue_id + cue_time)` so re-renders are identical, not randomised per run.
- Small pitch (±3%) and gain (±1.5 dB) jitter per repeat instance, applied at
  render time, not baked into the manifest file (one clean seed file per
  sound, jitter is a render-time `atempo`/`volume` pair). `house default`.
- Layering: an impact/stinger reads as one hit but is built from a transient
  (attack, first ~30ms) + body (30-150ms) + optional tail (reverb send,
  below) — three cheap library one-shots read as one designed sound where a
  single library file reads as "a sample". `house default`, standard
  practitioner layering technique (transient+body+tail), not sourced to a
  dated citation this run.

## Timing against picture

Sound pre-laps the cut: a whoosh/impact peaks 2-3 frames (at 24fps, 83-125ms)
**before** the cut lands, not on it — this is standard film-editing practice
(the "sound leads picture" convention popularised by Walter Murch's writing
on editing, general practitioner knowledge, not independently re-verified
this run — flagged, not cited to a dated page). `house default`.

## Density

**Max 2 cues per rolling second** (`MAX_CUES_PER_SECOND` in `sfx_check.py`).
Above that, individual cues stop reading as design and start reading as
noise — this is the numeric form of the owner's "out of place" and "a lot of the
times" complaints: the current house rule (a sound per on-screen action)
routinely exceeds this on any scene with more than 2 elements landing per
second. `house default`.

## Space (shared reverb)

One short room IR/algorithmic reverb (RT60 ≈ 250ms, 8-12% wet, applied to the
whole SFX bus, not per-file) so dry library one-shots from different sources
(Kenney synth UI + OpenGameArt paper foley) read as happening in the same
physical space instead of as a pile of unrelated dry files. `house default`.

## Which actions get a sound (replaces "a sound for every action")

1. **Always:** a new scene/beat boundary (`PROJECT.md` beat change).
2. **Usually:** a hard cut that lands on the story's turn, not every cut.
3. **Sometimes:** a hero word punching in, only if that beat is the line's point.
4. **Never, by default:** every element appearing on screen — this is the
   line in the current house-finish rule that causes the density violation
   above; the patch downgrades it from "every action" to items 1-3.

## Phone-speaker reality

Phone speakers roll off below ~150-200Hz and struggle above ~10kHz; anything
whose energy lives in the sub-150Hz range (a deep riser tail, a heavy thud's
fundamental) will not translate — it becomes felt-as-absence rather than
heard. `house default`, general known phone-speaker limitation, not
independently re-measured this run (would need a phone-speaker frequency
response reference, out of budget).
