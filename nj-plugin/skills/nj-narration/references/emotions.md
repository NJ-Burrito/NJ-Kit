# Emotion and mode variants with Chatterbox

How one harvested voice was voiced in eleven emotion/mode variants, plus how to reuse one voice for several characters.
The knob values are **design choices, not tested by ear**: they follow `references/direction.md` section 2 (higher
exaggeration speeds speech and lower cfg offsets it; defaults 0.5 / 0.5 / 0.8; a fast reference wants cfg near 0.3).
Treat them as a starting row for the owner's ear, then freeze the pick.

Fixed for all variants: `repetition_penalty` 2.0, `min_p` 0.05, `top_p` 1.0. Language id `ar` for Arabic (multilingual model). Seed per take = first 8 hex of sha256(take id). EOS guard 40 tokens (1.6 s) after the text is complete; token cap = 25 x (1.5 + letters / 4.5) (`scripts/tts_guards.py`).

## 1. The per-emotion knob table

| Emotion | exaggeration | cfg_weight | temperature | Why |
|---|---|---|---|---|
| narration | 0.40 | 0.50 | 0.70 | steady storyteller |
| neutral | 0.50 | 0.50 | 0.80 | package defaults, the baseline |
| calm | 0.30 | 0.60 | 0.60 | flat contour, slower, steady |
| happy | 0.70 | 0.40 | 0.80 | brighter contour, cfg lowered to offset the speed-up |
| joyful | 0.90 | 0.35 | 0.90 | stronger than happy, livelier pitch; a laugh slice as reference where one exists |
| sad | 0.35 | 0.65 | 0.70 | low energy, slowest of the set |
| surprised | 0.85 | 0.35 | 0.90 | abrupt, rising; `?!` and interjections in the text |
| angry | 0.95 | 0.30 | 0.85 | forceful and quick, a little steadier than excited |
| excited | 0.95 | 0.30 | 0.90 | fast, high energy; an excited slice as reference where one exists |
| scared | 0.75 | 0.35 | 0.95 | tense, uneven; ellipsis for hesitation |
| whisper | 0.25 | 0.60 | 0.50 | floor of the range: see section 3 |

Stay inside your project's knob limits (the run used exaggeration 0.25 to 2.0, cfg 0 to 1, temperature 0.05 to 5, and for a
per-line tone the stricter exaggeration 0.25 to 1.0, cfg 0.2 to 0.9). Words carry emotion too: punctuation, interjections and
ellipses belong to the writer and the direction sheet, not to a knob.

## 2. Conditioning on real emotion slices

Use a slice of the real speaker as the reference only where a matching one exists: a laugh for joyful, an excited passage for excited.
Rule, decided before any result: the slice must be at least 2.0 s (the longest one wins), otherwise the 6 to 12 s base reference is used.
Slices are short (2 to 3.7 s) and cut by loudness, pitch and voicing heuristics, so they are a weaker and riskier conditioning than the base
reference (the engine uses up to about 6 s for its prompt). In the run, five of 24 voices had a usable joyful or excited slice and none had a
usable whisper, sad or angry slice. Record `ref_used` on every take so the owner can tell which variants rode on a slice.

## 3. Whisper is not truly supported

Chatterbox has no whisper control. The "whisper" row is a soft, low-energy voice, nothing more. Label it so in the direction sheet and
to the owner. A true whisper needs a recorded whisper reference or another engine (an owner decision, `references/engines.md`).

## 4. Gate failures are recorded, not re-voiced

Offline gates, no model: duration 4.0 to 12.0 s after trimming (line target 6 to 9 s), not silent, no clipping, no token-cap run-on,
a trailing burst shorter than 0.7 s after a pause of 0.45 s or more trimmed (80 ms lead and 150 ms tail pads), final loudness -16 LUFS
within 1 and true peak at or below -1.5 dBTP. A take that fails is **logged as failed with the gate line**; it is not re-voiced, not
best-of-N, and not judged by a classifier. A fix goes to the stage that owns the cause (the reference, the text, the cap), and the new
line is a new take with a new id (`references/healing.md`). This keeps the one-take rule honest.

## 5. One voice for several characters: `variant.py`

When two characters must share one licensed voice, reshape the **reference or finished clip slightly** so they still sound different.
`variant.py` (kept with the voice library, not bundled here) uses ffmpeg rubberband for pitch and tempo with formants preserved, an
independent formant shift (resample by the ratio, then rubberband restores duration), an EQ preset and a grit stage. No model, no network.
Output keeps the input loudness (matched in LUFS, peak limited to about -1.5 dBFS).

| Preset | pitch (st) | formant | tempo | EQ | grit |
|---|---|---|---|---|---|
| older | -1.0 | 0.97 | 0.96 | dark | 0 |
| younger | +1.5 | 1.04 | 1.04 | bright | 0 |
| rougher | -0.5 | 0.98 | 1.00 | rough | 0.35 |

Limits are deliberately small: pitch plus or minus 3 st, formant 0.9 to 1.1, tempo 0.85 to 1.15. More than that stops sounding like the same
voice. Explicit flags override the preset (`--pitch --formant --tempo --eq --grit`).

Rules: a variant is a new reference with its own record that names the parent voice and the preset. **Never use a variant to make an adult
voice sound like a child**: "younger" is a small shift, and a child's voice is never cloned or imitated by processing (`SKILL.md`). Measure
the variant like any reference (`voice_measure.py ref`) and let the owner's ear confirm the two characters are told apart.
