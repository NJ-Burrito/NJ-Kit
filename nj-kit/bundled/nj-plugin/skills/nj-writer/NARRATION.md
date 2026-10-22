This is the only narration guide. If you find a narration rule anywhere else,
it is a bug: move it here and leave a pointer. (Retirement patches for every
other location: `ENSERA/artifacts/production/narration-patches-2026-09-21.md`.)

Built 2026-09-21, Phase 2, from the repaired knowledge
(`ENSERA/artifacts/research/narration-knowledge-2026-09-21.json`, 38 findings,
27 sourced by verbatim quote, 11 unsourced) and the devil pass
(`ENSERA/artifacts/ops/devil-narration-2026-09-21.md`). Every rule below ends
with a tag: `[f#]` (a finding id — check the id in the knowledge file),
`[house default — tune by ear]`, `[the owner, 2026-09-21]` (his pace decision),
or `[measured 2026-09-21]` (this run's own ffmpeg/voice.py measurement). A
number is a HARD checker threshold only where the tag says `hard_threshold`
and the finding's own `use_as` field agrees — today that is f31 (voice name)
and f37 (request byte limit) only. Everything else is guidance
`scripts/narration_check.py` WARNS on, never fails on.

# NARRATION.md — rules for every narrated piece, Arabic and English

Scope: commercial marketing, educational material, walkthroughs/tutorials,
podcasts. `scripts/narration_brief.py` and `scripts/narration_check.py`
parse the `## Matrix (machine-readable)` fenced block below — don't hand-edit
numbers anywhere else. Sourced research checkpoint this guide is drawn from:
`ENSERA/artifacts/research/narration-2026-09-21.md`.

## Every request — one screen

1. Fill `templates/NARRATION-BRIEF.md` (genre, language(s), destination, length,
   audience, the one thing the listener does/knows after, KB ids for facts,
   `templates/LEXICON.md` terms, tone words, bans).
2. `PYTHONUTF8=1 python scripts/narration_brief.py <brief.md>` → missing
   REQUIRED slots (exit 1) or the tailored rule sheet: matrix row(s), words
   budget, structure, the five highest-risk mistakes for that combination,
   per-beat DIRECTION prompts (§3 below).
3. Write the script. Every beat carries a `direction:` line (§3) — never a
   silent line.
4. `PYTHONUTF8=1 python scripts/narration_check.py <script> <brief.md>` →
   FAILS before a word is voiced (§6 for the full list).
5. `no-ai-slop` + `brand/COPY-CHECKS.md` on the text; `arabic-english-proofreading`
   on the Arabic side.
6. Voice: `nj-style-film/scripts/voice.py`, one request per line, DIRECTION
   from the script, not the old fixed constant (§4 "what replaces the rest").
7. `voice-clean` masters the take to the matrix's `loudness_target_lufs`.
8. You cannot hear. Every "does this sound right" question goes to the owner with
   the measurable proxies from §7, not a claim that it sounds good.

---

## 1. What makes a read feel alive, per sector and language

Terms: **pitch contour** = where pitch rises/falls across a sentence (a
question rises at the end in English, a listed item resets pitch at each
comma, a declarative sentence declines toward its end — "declination", a
well-established finding across languages, Cruttenden *Intonation*, 2nd ed.
1997, and 't Hart/Collier/Cohen *A Perceptual Study of Intonation*, 1990).
**Rhythm** = stress-timing and sentence-length variation. **Emphasis** =
one stressed word per sentence carrying the point (contrastive stress falls
on the word that answers "as opposed to what"). None of the specific
millisecond numbers below are from a single controlled study done on this
project — they are practitioner convention from voice-acting/broadcast
coaching (Susan Berkley *The Art of Voice Acting* school material; ADR/promo
coaching handouts widely taught, not one citable paper) unless a row says
otherwise. Flagged `house default, to be tuned by ear` throughout §Matrix.

| sector | target emotion | pitch contour | rhythm | pauses | emphasis | energy/warmth | arc |
|---|---|---|---|---|---|---|---|
| commercial | desire, confidence | wide range; rises into the claim, resets on each benefit in a list, falls with authority on the CTA verb | short-long-short: a 3-word hook, a longer proof sentence, a short CTA (rule of three — classical rhetoric, still the default ad-copy pattern) | 300-500ms dramatic pause BEFORE the key claim; 150-250ms breath pause between clauses | one stressed word per sentence, usually the benefit noun or the CTA verb | high energy, audible smile (raising the corners of the mouth measurably brightens formants — common VO-coaching claim, "smile in your voice") | opens fast (hook), lifts on the proof, lands hard and short on the CTA |
| educational | curiosity, reassurance | moderate range; rises to signal a new idea, flattens (not monotone — narrower, not flat) during worked detail so the listener can track content over performance | longer sentences allowed, but vary length beat to beat so the ear doesn't lock into one cadence; signpost words ("first", "now", "so") get a small pitch lift | 400-600ms after a claim before its proof (processing gap — aligns with Mayer's segmenting principle: pause = a chunk boundary); 200ms breath | emphasis on the NEW term the first time it's said, not on function words | patient, warm, unhurried; energy stays present but softer than commercial | opens with the objective (calm, clear), lifts slightly at the "aha" moment of the lesson, lands flat and settled on the recap |
| walkthrough | calm competence | narrow-moderate range; a small rise on the action verb ("click", "open"), a small fall on the confirmation ("...and you're done") | one action per sentence, matched beat to beat — rhythm should feel like footsteps, not a race | 250-350ms between "say it" and the screen catching up (never say the next step before the current one can be seen) | emphasis on the UI label being clicked, spoken as it's written on screen | steady, unshowy competence — the voice of someone who has done this a hundred times and isn't bored, isn't performing | flat-to-slightly-rising through the steps, settles on the confirmation line |
| podcast | intimacy, presence | the widest range of the four — closest to real conversation; rises on genuine questions, falls at chapter ends | most variation in sentence length of any sector; laughter/breath sounds (if the engine allows) read as human | 500-800ms at a chapter boundary (a real pause, not a glitch); 150-200ms breath elsewhere | emphasis follows normal conversational stress — the informative word in the sentence, no per-line marking needed beyond the writer choosing where the sentence's own stress naturally falls | conversational warmth, first person allowed, closest to just talking | opens with a hook/tease, several small lifts at each chapter, lands with an intimate, quieter outro (closing a conversation, not ending a broadcast) |

### Arabic prosody — its own findings, not English translated

- **MSA recitation rhythm vs. conversational Levantine.** [f27] Formal MSA news-style
  reading (the register `nj-writer`'s existing 120wpm baseline models) carries
  a more even, declamatory rhythm with less pitch swing per word and more
  weight on **vowel length and gemination (shadda)** than on pitch — long
  vowels and doubled consonants carry emphasis the way English uses pitch and
  loudness. A flat MSA read that has no lengthening on the emphasised
  syllable sounds stiff even at a "correct" pace — this is a documented
  contrast in Arabic phonology/prosody literature (Watson, *The Phonology and
  Morphology of Arabic*, 2002, ch. on stress and length) rather than a
  house guess, though the exact ms values below are house-tuned.
- **White dialect (اللهجة البيضاء)** for consumer commercial/podcast carries
  more pitch movement, closer to the English commercial contour, because it
  is built to sound regionally neutral and conversational rather than formal.
  [house default — tune by ear]
- **Where emphasis lands:** Arabic stress is largely predictable from
  syllable weight (a rule-governed system, not free placement like English
  contrastive stress) — do not mark emphasis by writing in ALL CAPS or bold
  (voice engines ignore Latin-script emphasis conventions on Arabic script);
  mark it instead by **sentence position** (put the emphasised word last, the
  position Arabic naturally stresses in a pausal / end-of-utterance form) or
  by a short pause immediately before it. [f26]
- **What sounds stiff:** full grammatical case-ending vocalisation (i'rab)
  read aloud on every word, in a commercial or podcast register — it sounds
  like a recitation, not an ad or a chat. Reserve full tashkīl for
  disambiguation only (§5). Also stiff: zero variation in sentence length
  (a wall of 12-word MSA sentences back to back) and translating English
  filler words ("well,", "so,") literally instead of using Arabic's own
  discourse markers (إذن، طيب، وبالتالي). [f29]
- **Contradiction disclosed:** some regional VO coaching treats white dialect
  as strictly avoiding MSA vocabulary; other practitioners mix MSA vocabulary
  with white-dialect grammar for a "credible but accessible" register
  (common in Gulf/Levant ad practice). No single primary source settles
  this — brief must state which the audience expects; default is the mixed
  form for commercial, pure MSA for educational/institutional.
  [house default — tune by ear]

## 2. Getting this out of a synthetic voice — the engine in use

> **Current rule: §11.** Voice is Kore with a registered style from `voice-styles.json`; the `Aoede` voice and the single fixed direction described below are historical (pre-2026-10-01). The paragraph below records how the mechanism was found.

`nj-style-film/scripts/voice.py` (read in full for this brief) sends one
HTTP request per line to `google/gemini-3.1-flash-tts-preview` via
OpenRouter, `voice: "Aoede"`, with a **fixed English-language DIRECTION
string prepended to every line**: *"Read this at a calm, natural,
conversational pace, warm and sure, like one tester talking to another. Fall
at the end:"* — this is the whole performance-direction surface today: one
paragraph of natural-language style instruction, per run, not per line.

**Not independently re-verified against Google's own Gemini TTS documentation
this run** (budget/time; flagged as an open risk in the plan file, not
silently assumed). What follows is drawn from the code, its comments, and
what `voice.py`'s own retry logic already tells us the model does:

- The endpoint accepts a **natural-language style/direction prefix** — this
  is how `voice.py` already steers tone, so the mechanism exists and works
  for at least "pace" and "mood" adjectives. [f30]
- The model **sometimes performs a line instead of reading it** (`voice.py`'s
  own comment: "a 12-word line came back 14 s long" — a redraw-if-too-long
  safety net already exists). This means the model DOES respond to
  performance cues, sometimes more than asked — a redraw budget must exist
  for any expressive direction, not just the current word-count check.
  [measured 2026-09-21]
- **Punctuation is very likely to steer prosody** (standard behaviour for
  neural TTS generally, not confirmed against this specific model's docs
  today): a comma reads as a short pause, an em dash or ellipsis as a longer
  one, a question mark as a rising contour, a period as a fall. This is the
  cheapest lever a script can pull without any code change to `voice.py`.
  [house default — tune by ear]
- **What is NOT supported today:** per-word tags (no SSML seen in `voice.py`
  — it posts plain `input` text, not a markup payload), per-phrase DSP
  (`--rate`/`--pitch` flags — not applicable, this isn't a CLI engine), or a
  different direction per line without a code change. [f32]

### Writing for prosody, concretely

- **Force a pitch reset:** a genuine question ("So what does that mean for
  you?") or a listed item ("First… then… finally…") gives the model a shape
  it is already primed to read with a contour, because the DIRECTION prompt
  says "conversational" and conversational TTS models are trained on
  question/list intonation heavily (a strong prior in these models' training
  data — general TTS-research observation, not a claim about this model's
  weights specifically). [house default — tune by ear]
- **Put the stressed word last or isolated**, per §1's Arabic emphasis rule;
  in English, put it right before the sentence's terminal punctuation, not
  buried mid-clause. [f26]
- **Short-long-short sentence shapes** (rhythm, §1) force pace variation even
  under one fixed DIRECTION prompt, because sentence length is the one
  lever a per-line request always carries regardless of the direction text.
  [f15]
- **A per-line direction is possible without touching the shared script**:
  `voice.py`'s DIRECTION is a module constant applied to every line. The A/B
  test in `artifacts/production/narration-ab/` uses a **copy** of `voice.py`
  (never the original — brief forbids a second copy inside `nj-writer`,
  and this copy lives only in the AB folder, not shipped) that reads an
  optional `"direction"` key per beat in `beats.json` and falls back to the
  module constant when absent. That is the concrete mechanism version B
  uses; it is not proposed as a change to the shared `voice.py` — that
  proposal is a patch, in the patches file, for the Lead to apply.
  [needs_voiced_ab — see §10 tag test]

### What reliably goes wrong, and the fix

| symptom | cause | fix |
|---|---|---|
| monotone list ("one, two, three, four items") | no pitch reset cue in the text | write it as a real list with commas/"and", or split into short sentences — forces the model's list-reading prior |
| rushed numbers | digits read fast, no pause around them | spell numbers out in words (already a §Matrix `numeral_policy` rule); put a comma before and after a number in a sentence |
| flat endings | sentence trails off with no terminal punctuation, or ends on a function word | end on the stressed content word (§1 Arabic rule) + explicit period; avoid ending a line on "and", "so", "و" |
| wrong stress on an Arabic word | ambiguous consonant skeleton with no vowel marks (heteronym) | targeted tashkīl on JUST that word (§5), not the whole line |
| the "not-human" per-phrase DSP artefact `nj-kit` warns about | rate/pitch flags bolted onto a flat, non-expressive engine as post-processing | does not apply to this engine — no DSP rate/pitch flags exist in `voice.py`'s call. See reconciliation below. |

### Reconciling `nj-kit`'s existing rule

`nj-kit/manifest.json` `house_style.film.voice`: *"One TTS request per line at
fixed settings — consistency over expression. Per-phrase rate/pitch variation
(split-and-join) reads as not human."* That rule was written for a **flat,
non-expressive engine driven by CLI DSP flags** (`edge-tts --rate=-6%`, history: removed 2026-10-01; the only engine now is Gemini 3.1 Flash TTS via OpenRouter) — splitting a line to bolt a
different `--rate`/`--pitch` value onto each half and rejoining the audio is
what it correctly forbids: mechanical, non-linguistic pitch/rate steps that
don't correspond to anything in the words.

**What survives:** one request per line, at whatever settings that run uses
— never split a single line into fragments with different DSP flags and
splice them. **What replaces "fixed settings":** expressiveness is now
carried by (a) the WRITING (sentence shape, punctuation, word order, per
§1-§2 above) and (b) a natural-language **DIRECTION prompt the model
actually reads and responds to**, per line where the engine supports it —
this is not DSP, it's telling the model what to perform, the same category
of input `voice.py` already sends for every line today, just made per-line
instead of fixed. [f30, f15] The patch for `nj-kit/manifest.json` records this
distinction; see the patches file.

**Two engine hard limits (checker FAILS, not warns — the only two ids whose
`use_as` is `hard_threshold` in the knowledge file):**
- `voice` must be one of the 30 prebuilt voice names Google documents. [f31 — hard_threshold]
- `input` (direction + line, UTF-8 bytes) must be ≤ 8000 bytes per request. [f37 — hard_threshold]

## 3. Per-line DIRECTION — required on every beat

> **Voiced narration (§11):** the direction is the registered style's direction, byte-exact, and the line records its style id. Free-form direction below applies to the writing brief only, never to what is sent to the TTS.

Every beat in a narration script carries a `direction:` line before the
spoken text: 6-12 words, plain language, matching §1's row for that
genre/language (e.g. *"warm, leaning in, slow down on the last three
words"*). `narration_check.py` FAILS a beat with no direction line. Two
worked examples (used verbatim in the A/B test):

**English, commercial, before (flat, no direction — version A style):**
> Ensera builds AI and robotics training for students and companies across
> Jordan.

**English, commercial, after (version B, directed):**
> direction: confident, warm, lean in on the last three words
> Ensera trains the people who will build the region's AI — starting now.

**Arabic, commercial, before (flat):**
> تقدم إنسيرا تدريباً في الذكاء الاصطناعي والروبوتات للطلاب والشركات في الأردن.

**Arabic, commercial, after (directed, stressed word placed last per §1):**
> direction: دافئ وواثق، تمهّل على الكلمة الأخيرة
> إنسيرا تُعِدّ جيلاً كاملاً لبناء الذكاء الاصطناعي — من الأردن.

## 4. Bilingual pair

Transcreate, don't translate: write the language whose register is harder to
match first (usually Arabic, because MSA/white-dialect choice and case
vocalisation constrain word choice more than English does), then write the
English to the same beat clock, not word-for-word. Expect Arabic to run
10-25% longer in character count for the same idea even though it's spoken
slower (fewer, denser words) — budget both languages' word counts
independently from the matrix, never reuse one table (existing house rule,
`nj-writer/SKILL.md` §6, kept). [house default — tune by ear] Shared
pronunciation lexicon: `templates/LEXICON.md`.

**Pair drift tolerance (checker gate):** the AR and EN versions of the same
beat may differ in expected duration (matrix wpm) by at most **±20%**
[house default — tune by ear, no finding covers pair drift per the devil
pass gap 5]; `narration_check.py` FAILS a pair whose beat counts differ at
all, or whose expected-duration ratio exceeds this.

## 5. Arabic specifics — numerals, terms, TTS pitfalls

- **Numerals, dates, currency:** spoken in full Arabic words for this engine
  (`numeral_policy` in the matrix) — digits read by TTS models are a common
  failure point across engines generally (not confirmed for this specific
  model without a live test); spelling out is the cheap, verifiable-by-ear
  mitigation. Percentages: "ثمانون بالمئة" not "80%". Currency: name the unit
  in full ("دينار أردني") after the spoken number. [house default — tune by ear]
- **English terms/brand names inside Arabic:** transliterate into Arabic
  script for a brand the audience should recognise by sound (إنسيرا), keep
  Latin-script acronyms that are read as letters (AI → إيه آي or "الذكاء
  الاصطناعي" depending on whether the brief wants the acronym or the
  translated term — state which in the brief; default: translate on first
  use, may use the Arabic acronym after). Code-switching a whole English
  clause reads as authentic in casual white-dialect podcasts, wrong in MSA
  educational material — genre-gated in the matrix's `register` field.
  [house default — tune by ear]
- **Sun/moon letters, hamza, tanwīn, pausal forms:** where TTS commonly
  mis-stresses — a word ending in tanwīn read in pausal form (no nunation)
  at the end of a sentence but WITH nunation mid-sentence is standard MSA
  and gets missed if the writer vocalises inconsistently; write the pausal
  form at any point the model is likely to treat as a break (before a
  comma-equivalent pause), full form mid-clause. [f29]
- **Tashkīl as a targeted disambiguation tool, not full vocalisation:** mark
  diacritics ONLY on a heteronym the TTS is likely to mis-read (a word whose
  unmarked form has two readings with different meanings/stress) — full
  vocalisation of a whole line reads as a recitation register (§1) and is
  banned outside that register. [f29]
- **Gendered/plural address:** state the audience's grammatical gender split
  in the brief; default to explicit dual forms (أنتَ/أنتِ) only where the
  audience is genuinely mixed and the beat is short enough to carry both —
  otherwise default to plural أنتم, which is gender-neutral and shorter.
  [house default — tune by ear]
- **Punctuation as prosody control:** see §2 — commas and question marks are
  the primary lever available today. [f32]

## 6. Checks — `narration_check.py` FAILS on

> Voice-side checks (style registered, direction byte-equal, wpm band, tempo cap, visible text keeps only the source's own marks, full tashkeel in `tts_text`) run in `voice_style_gate.py`, §11.

Pre-voicing (text-only): words over/under the length's budget; a sentence
over the matrix's word ceiling; a beat with no `direction:` line; three
sentences in a row within one beat of the same length ±1 word (rhythm
flatness); more than one marked emphasis word per sentence; a beat that
cannot be said in its window at the matrix wpm; a digit/symbol that must be
spelled out per the language's numeral policy; a lexicon term written in a
form the lexicon forbids; a factual line with no `kb:#id` when the brief
requires sourcing; a missing required structural part (hook, CTA,
disclosure, recap…); no declared emotional arc (open/lift/land mapped to
beats); for a pair — beat counts differing, or length drift beyond the
matrix's tolerance.

Post-voicing (measurable, ffmpeg-based — everything below runs with the
ffmpeg already on PATH, no new install): words-per-second per line (from the
known word count and the take's duration via `ffprobe`); pause lengths via
`ffmpeg -af silencedetect`; **pitch variability** via `ffmpeg -af astats`
(reports RMS/peak level per frame; a fundamental-frequency contour needs
pitch tracking `ffmpeg` doesn't do natively — flagged as a real ceiling, see
§8) — where a true F0 track isn't available on this CPU-only, no-new-install
machine, the proxy is **level (RMS) variability** across the take via
`astats`, labelled explicitly as an approximation of pitch variability, not
pitch itself; a flatness flag fires when that RMS variability falls under a
threshold (`house default, to be tuned by ear`, printed by the script, tuned
after the first real A/B listen). [f14 — pitch variability is NOT a universal
aliveness proxy; RMS-variability flag is guidance only, never a hard fail]

## 7. Loudness and mastering

Matrix's `loudness_target_lufs` per destination; `voice-clean` runs the
actual chain (EQ, De-Esser, De-Noise, Compressor, Amplify, Limiter) — not
restated here. `-14 LUFS integrated / -1 dBTP` for social video is the
existing house master target (`nj-kit house_style.film.masters`, kept,
pointed to, not duplicated). **All masters were landing 2-3 LU hot until
2026-09-21** — cause was `voice-clean`'s mono->dual-mono pan step measuring
louder under BS.1770, not the loudness engine; fixed in `voice-clean`, not
restated here. [measured 2026-09-21]

## 8. Ceilings — say what this machine really cannot measure

No pitch (F0) tracking library is installed and none is added (100%-free,
CPU-only rule) — RMS-level variability from `ffmpeg astats` is used as a
labelled proxy for "sounds more varied", not a substitute for a real pitch
contour. A tighter measurement (e.g. `librosa` pitch tracking) would need a
new dependency; not installed this run — named as an open item for the owner,
not silently worked around. Every delivery judgement beyond these measured
proxies is a question for the owner, who listens; this file cannot verify
"feels alive" by itself, only reduce how often a flat take reaches his ears
in the first place.

## 9. Missing sectors — event promo, recruitment, investor/partnership

Not in the original four; devil pass and the repair both flagged the gap.
Built from the nearest sourced sector plus house defaults, labelled as such.
No dedicated finding covers any of the three — every row below is
`[house default — tune by ear]` unless it inherits a tagged rule by pointer.

- **Event promo** (an expo booth, a talk announcement, a meetup invite) —
  nearest sector: **commercial** (short, hook-first, one CTA = "come" /
  "register"). Same wpm band and structure as commercial; the required part
  "claim+proof" becomes "what + why attend"; CTA is a date/place/link, never
  an unfalsifiable adjective (`nj-writer` §4, kept). [house default — tune by ear]
- **Recruitment call** (a hiring pitch, "join us") — nearest sector:
  **commercial** for hook and CTA shape, **educational** for the body (it
  has to explain the role/programme accurately, not just excite). Register:
  direct, second person, names the ONE ask (apply, a link) exactly once, at
  the end only, per commercial's `cta_rule`. [house default — tune by ear]
- **Investor / partnership piece** — nearest sector: **educational** (it has
  to be accurate and structured — a claim to an investor is a claim with the
  same source discipline as any other spoken fact, `nj-writer` §4, KB id
  required) with commercial's arc (opens on the opportunity, lifts on
  traction, lands on the ask). Longer sentences than commercial are allowed
  (educational's ceiling), but the CTA rule is commercial's: one verb, one
  checkable ask (a meeting, a deck, a reply). [house default — tune by ear]

Matrix rows for these three: language x one destination each (`social_video`
for event promo, `elearning_video` for recruitment, `podcast_audio` for
investor, since these are usually a call or a voice note) — `genre` values
`event_promo`, `recruitment`, `investor_partnership`, in `rows[]` below.

## 10. Tag test outcome — inline bracket tags vs prose DIRECTION

One voiced test, one Arabic line, three ways (plain / prose DIRECTION /
`[whispers]`-style inline tag), through an unmodified copy of `voice.py` in
`artifacts/production/narration-ab/`. Outcome, measurements and the resulting
rule are written here after the test runs (the PHASE_RECEIPT carries the same
finding). If the test could not run (no key, no network, budget), the
voicing section above stands as written — **prose DIRECTION only, bracket
tags marked `untested`, not banned and not endorsed.**

**Outcome (2026-09-21, measured):** one Arabic line (~7 words) voiced 3 ways
through an unmodified `voice.py` (`artifacts/production/narration-ab/tag_test.py`):
plain 4.35s, prose DIRECTION ("Whisper this softly, intimately: ...") 3.59s
(-17% vs plain), bracket tag (`[whispers] ...`) 4.60s (+6% vs plain, inside
noise). **Conclusion: prose DIRECTION measurably changes delivery; the
bracket tag did not.** Rule: **use prose DIRECTION only** (§3's per-beat
`direction:` line). Bracket-style inline tags (`[whispers]`) are marked
**untested for reliable effect** on this engine — not banned outright (a
single 7-word sample is not proof of "never works"), but not recommended:
do not build a checker rule around them. [measured 2026-09-21]

## Matrix (machine-readable)

```json
{
  "_meta": {
    "file": "NARRATION.md #Matrix",
    "purpose": "Rows for narration_brief.py / narration_check.py. rows[] = genre x language x destination parameters (was narration-matrix.json, folded in per the owner's 2026-09-21 amendment). delivery{} = prosody targets per genre x language, §1.",
    "row_count": 28,
    "source_pairing": "wpm_min/wpm_max share 'wpm_source'; words_budget_* fields share 'words_budget_source'; loudness_target_lufs pairs with 'loudness_target_source'. Every other numeric field pairs with '<field>_source'."
  },
  "rows": [
    {"genre":"commercial","language":"en","destination":"social_video","wpm_min":150,"wpm_max":170,"wpm_source":"practitioner convention, VO industry rate cards (Edge Studio / GravyForTheBrain 'commercial read' band); scaled from house 180wpm news baseline","max_words_per_sentence":12,"max_words_per_sentence_source":"house default, to be tuned by ear","max_sentences_per_beat":1,"max_sentences_per_beat_source":"house default, to be tuned by ear","hook_window_s":3,"hook_window_s_source":"practitioner convention, short-form video ad platforms (Meta/YouTube skippable-ad guidance: first 3s carries the hook)","words_budget_15s":38,"words_budget_30s":75,"words_budget_60s":150,"words_budget_source":"derived: wpm_max/60 x length, minus 10% for lead-in/tail (house default)","required_parts":["hook","claim+proof","cta"],"register":"direct, second person, confident","address_form":"anta/anti or plural you per audience","numeral_policy":"round and spoken form; never two numbers in one line (nj-writer/speakable.md)","cta_rule":"one verb, one concrete checkable action; no unfalsifiable adjective without proof (nj-writer S4)","disclosure_rule":"sponsored/ad-read disclosure only if third-party product named; no known Jordan-specific ad-disclosure statute found (say so)","silence_ratio_max":0.15,"silence_ratio_max_source":"house default (nj-style-film 'no dead air' rule, 20 Sept 2026)","loudness_target_lufs":-14,"loudness_target_source":"house default, social video master (ITU-R BS.1770 / streaming-platform norm)","caption_rule":"verbatim spoken words (nj-style-film house rule)"},
    {"genre":"commercial","language":"en","destination":"podcast_audio","wpm_min":150,"wpm_max":165,"wpm_source":"practitioner convention, podcast ad-read pacing (mid-roll reads run close to host conversational rate)","max_words_per_sentence":14,"max_words_per_sentence_source":"house default, to be tuned by ear","max_sentences_per_beat":2,"max_sentences_per_beat_source":"house default, to be tuned by ear","hook_window_s":5,"hook_window_s_source":"house default, to be tuned by ear","words_budget_15s":36,"words_budget_30s":72,"words_budget_60s":145,"words_budget_source":"derived: wpm_max/60 x length, minus 10% (house default)","required_parts":["hook","claim+proof","cta"],"register":"conversational, host-voice","address_form":"anta/anti or plural you","numeral_policy":"round and spoken form; never two numbers in one line","cta_rule":"one verb, one concrete checkable action","disclosure_rule":"host-read ad disclosure where the segment is paid; convention, no Jordan-specific rule found","silence_ratio_max":0.15,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default, podcast stereo master (commonly -16 LUFS stereo / -19 mono)","caption_rule":"verbatim spoken words"},
    {"genre":"educational","language":"en","destination":"elearning_video","wpm_min":130,"wpm_max":150,"wpm_source":"Mayer, R. Cognitive Theory of Multimedia Learning (2001/2009) pacing/segmenting principle; exact wpm is a house scaling, not Mayer's own number","max_words_per_sentence":16,"max_words_per_sentence_source":"house default, to be tuned by ear","max_sentences_per_beat":2,"max_sentences_per_beat_source":"house default, to be tuned by ear","hook_window_s":10,"hook_window_s_source":"house default, to be tuned by ear","words_budget_180s":400,"words_budget_600s":1300,"words_budget_source":"derived: wpm_min/60 x length (favour the slower end, house default)","required_parts":["learning objective","signpost","worked content","recap"],"register":"plain, second person, patient","address_form":"anta/anti (singular, direct)","numeral_policy":"spoken form; units/formulas read in full, not symbol-read","cta_rule":"recap states the ONE thing the listener should now know or do","disclosure_rule":"not applicable","silence_ratio_max":0.20,"silence_ratio_max_source":"house default (Mayer's segmenting principle; exact ratio house-set)","loudness_target_lufs":-16,"loudness_target_source":"house default, e-learning master (no single mandated standard found; using podcast-stereo convention)","caption_rule":"verbatim spoken words"},
    {"genre":"educational","language":"en","destination":"podcast_audio","wpm_min":140,"wpm_max":160,"wpm_source":"house default, to be tuned by ear","max_words_per_sentence":16,"max_words_per_sentence_source":"house default","max_sentences_per_beat":2,"max_sentences_per_beat_source":"house default","hook_window_s":15,"hook_window_s_source":"house default, to be tuned by ear","words_budget_180s":420,"words_budget_600s":1400,"words_budget_source":"derived: wpm_max/60 x length x 0.9 (house default)","required_parts":["intro","learning objective","content","recap","outro"],"register":"conversational, patient","address_form":"anta/anti","numeral_policy":"spoken form","cta_rule":"recap states the ONE thing the listener should now know or do","disclosure_rule":"not applicable","silence_ratio_max":0.20,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default, podcast stereo","caption_rule":"verbatim spoken words"},
    {"genre":"walkthrough","language":"en","destination":"screen_capture_video","wpm_min":140,"wpm_max":160,"wpm_source":"practitioner convention, screencast/tutorial narration guidance (match narration to on-screen action, avoid outrunning the cursor)","max_words_per_sentence":14,"max_words_per_sentence_source":"house default, to be tuned by ear","max_sentences_per_beat":1,"max_sentences_per_beat_source":"house default - one action, one sentence, voice and cursor stay locked","hook_window_s":5,"hook_window_s_source":"house default, to be tuned by ear","words_budget_15s":35,"words_budget_30s":70,"words_budget_60s":140,"words_budget_source":"derived: wpm_max/60 x length x 0.9 (house default)","required_parts":["goal statement","step-by-step (say-then-do)","confirmation"],"register":"instructional, imperative-lite","address_form":"anta/anti, imperative verb forms where natural","numeral_policy":"spoken form; UI labels read exactly as on screen, quoted","cta_rule":"confirmation line names the checkable end state","disclosure_rule":"not applicable","silence_ratio_max":0.15,"silence_ratio_max_source":"house default","loudness_target_lufs":-14,"loudness_target_source":"house default, social/video master","caption_rule":"verbatim spoken words; UI text not re-captioned"},
    {"genre":"walkthrough","language":"en","destination":"elearning_video","wpm_min":135,"wpm_max":155,"wpm_source":"house default, to be tuned by ear","max_words_per_sentence":14,"max_words_per_sentence_source":"house default","max_sentences_per_beat":1,"max_sentences_per_beat_source":"house default","hook_window_s":8,"hook_window_s_source":"house default","words_budget_180s":420,"words_budget_600s":1400,"words_budget_source":"derived (house default)","required_parts":["goal statement","step-by-step (say-then-do)","confirmation"],"register":"instructional","address_form":"anta/anti","numeral_policy":"spoken form; UI labels quoted verbatim","cta_rule":"confirmation line names the checkable end state","disclosure_rule":"not applicable","silence_ratio_max":0.18,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"podcast","language":"en","destination":"podcast_audio","wpm_min":150,"wpm_max":170,"wpm_source":"practitioner convention, NPR Training / conversational-radio pacing guidance (~150-160 wpm) plus house scaling for synthetic voice","max_words_per_sentence":20,"max_words_per_sentence_source":"house default, to be tuned by ear","max_sentences_per_beat":3,"max_sentences_per_beat_source":"house default","hook_window_s":20,"hook_window_s_source":"house default, to be tuned by ear","words_budget_600s":1500,"words_budget_1800s":4500,"words_budget_source":"derived: wpm_min/60 x length x 0.9 (house default)","required_parts":["cold open / intro","chaptered content","outro","ad-read disclosure if applicable"],"register":"conversational, first person allowed","address_form":"anta/anti or plural","numeral_policy":"spoken form","cta_rule":"one ask in the outro, not per segment","disclosure_rule":"host-read ad disclosure convention (no Jordan-specific statute found)","silence_ratio_max":0.20,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default, podcast stereo (mono alt -19 LUFS, common platform convention)","caption_rule":"verbatim spoken words"},
    {"genre":"commercial","language":"ar","destination":"social_video","wpm_min":100,"wpm_max":113,"wpm_source":"derived: en band x 0.667 (house Arabic/English ratio, nj-writer S6, BBC Institute of Journalism convention)","max_words_per_sentence":10,"max_words_per_sentence_source":"house default, to be tuned by ear - Arabic clause structure runs longer per word","max_sentences_per_beat":1,"max_sentences_per_beat_source":"house default","hook_window_s":3,"hook_window_s_source":"house default (mirrors en row)","words_budget_15s":26,"words_budget_30s":52,"words_budget_60s":105,"words_budget_source":"derived: wpm_max/60 x length x 0.9","required_parts":["hook","claim+proof","cta"],"register":"white dialect for consumer audience; MSA if formal/institutional - brief states which","address_form":"anta/anti explicit split (see LEXICON gender note); plural antum for mixed/unknown audience","numeral_policy":"numerals spoken in full Arabic words, not digits; percentages as spoken number + percent word; light tashkeel only on ambiguous heteronyms (S5)","cta_rule":"one verb, one checkable action","disclosure_rule":"same as en row; no Jordan-specific ad-disclosure statute found","silence_ratio_max":0.15,"silence_ratio_max_source":"house default","loudness_target_lufs":-14,"loudness_target_source":"house default, social video master","caption_rule":"verbatim spoken words, full Arabic script (no Arabizi)"},
    {"genre":"commercial","language":"ar","destination":"podcast_audio","wpm_min":100,"wpm_max":110,"wpm_source":"derived: en band x 0.667","max_words_per_sentence":12,"max_words_per_sentence_source":"house default","max_sentences_per_beat":2,"max_sentences_per_beat_source":"house default","hook_window_s":5,"hook_window_s_source":"house default","words_budget_15s":25,"words_budget_30s":48,"words_budget_60s":97,"words_budget_source":"derived","required_parts":["hook","claim+proof","cta"],"register":"white dialect or MSA per brief","address_form":"anta/anti split; plural for mixed audience","numeral_policy":"spoken words, not digits","cta_rule":"one verb, one checkable action","disclosure_rule":"same as en row","silence_ratio_max":0.15,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"educational","language":"ar","destination":"elearning_video","wpm_min":87,"wpm_max":100,"wpm_source":"derived: en band x 0.667","max_words_per_sentence":13,"max_words_per_sentence_source":"house default","max_sentences_per_beat":2,"max_sentences_per_beat_source":"house default","hook_window_s":10,"hook_window_s_source":"house default","words_budget_180s":270,"words_budget_600s":870,"words_budget_source":"derived: wpm_min/60 x length","required_parts":["learning objective","signpost","worked content","recap"],"register":"MSA, formal-plain","address_form":"anta/anti or antum per audience stated in brief","numeral_policy":"spoken words; formulas/units read in full","cta_rule":"recap states the ONE thing to know or do","disclosure_rule":"not applicable","silence_ratio_max":0.20,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"educational","language":"ar","destination":"podcast_audio","wpm_min":93,"wpm_max":107,"wpm_source":"derived: en band x 0.667","max_words_per_sentence":13,"max_words_per_sentence_source":"house default","max_sentences_per_beat":2,"max_sentences_per_beat_source":"house default","hook_window_s":15,"hook_window_s_source":"house default","words_budget_180s":280,"words_budget_600s":930,"words_budget_source":"derived","required_parts":["intro","learning objective","content","recap","outro"],"register":"MSA or white dialect per brief","address_form":"anta/anti or antum","numeral_policy":"spoken words","cta_rule":"recap states the ONE thing to know or do","disclosure_rule":"not applicable","silence_ratio_max":0.20,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"walkthrough","language":"ar","destination":"screen_capture_video","wpm_min":93,"wpm_max":107,"wpm_source":"derived: en band x 0.667","max_words_per_sentence":11,"max_words_per_sentence_source":"house default","max_sentences_per_beat":1,"max_sentences_per_beat_source":"house default","hook_window_s":5,"hook_window_s_source":"house default","words_budget_15s":24,"words_budget_30s":47,"words_budget_60s":93,"words_budget_source":"derived","required_parts":["goal statement","step-by-step (say-then-do)","confirmation"],"register":"instructional, white dialect for consumer app, MSA for enterprise","address_form":"anta/anti, imperative forms where natural","numeral_policy":"spoken words; UI labels quoted verbatim in ORIGINAL language","cta_rule":"confirmation line names the checkable end state","disclosure_rule":"not applicable","silence_ratio_max":0.15,"silence_ratio_max_source":"house default","loudness_target_lufs":-14,"loudness_target_source":"house default","caption_rule":"verbatim spoken words; UI text not re-captioned"},
    {"genre":"walkthrough","language":"ar","destination":"elearning_video","wpm_min":90,"wpm_max":103,"wpm_source":"derived: en band x 0.667","max_words_per_sentence":11,"max_words_per_sentence_source":"house default","max_sentences_per_beat":1,"max_sentences_per_beat_source":"house default","hook_window_s":8,"hook_window_s_source":"house default","words_budget_180s":280,"words_budget_600s":930,"words_budget_source":"derived","required_parts":["goal statement","step-by-step (say-then-do)","confirmation"],"register":"instructional","address_form":"anta/anti","numeral_policy":"spoken words; UI labels quoted verbatim","cta_rule":"confirmation line names the checkable end state","disclosure_rule":"not applicable","silence_ratio_max":0.18,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"podcast","language":"ar","destination":"podcast_audio","wpm_min":100,"wpm_max":113,"wpm_source":"derived: en band x 0.667","max_words_per_sentence":15,"max_words_per_sentence_source":"house default","max_sentences_per_beat":3,"max_sentences_per_beat_source":"house default","hook_window_s":20,"hook_window_s_source":"house default","words_budget_600s":1000,"words_budget_1800s":3000,"words_budget_source":"derived: wpm_min/60 x length x 0.9","required_parts":["cold open / intro","chaptered content","outro","ad-read disclosure if applicable"],"register":"white dialect for general regional audience; MSA for formal/institutional show","address_form":"anta/anti or antum","numeral_policy":"spoken words","cta_rule":"one ask in the outro","disclosure_rule":"same as en row","silence_ratio_max":0.20,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"commercial","language":"en","destination":"elearning_video","wpm_min":140,"wpm_max":160,"wpm_source":"house default, to be tuned by ear","max_words_per_sentence":13,"max_words_per_sentence_source":"house default","max_sentences_per_beat":1,"max_sentences_per_beat_source":"house default","hook_window_s":4,"hook_window_s_source":"house default","words_budget_15s":36,"words_budget_30s":72,"words_budget_60s":145,"words_budget_source":"derived","required_parts":["hook","claim+proof","cta"],"register":"direct","address_form":"anta/anti","numeral_policy":"round and spoken form","cta_rule":"one verb, one checkable action","disclosure_rule":"same as commercial/social row","silence_ratio_max":0.15,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"commercial","language":"ar","destination":"elearning_video","wpm_min":93,"wpm_max":107,"wpm_source":"derived: en band x 0.667","max_words_per_sentence":11,"max_words_per_sentence_source":"house default","max_sentences_per_beat":1,"max_sentences_per_beat_source":"house default","hook_window_s":4,"hook_window_s_source":"house default","words_budget_15s":24,"words_budget_30s":48,"words_budget_60s":97,"words_budget_source":"derived","required_parts":["hook","claim+proof","cta"],"register":"white dialect or MSA per brief","address_form":"anta/anti split","numeral_policy":"spoken words","cta_rule":"one verb, one checkable action","disclosure_rule":"same as commercial/social row","silence_ratio_max":0.15,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"educational","language":"en","destination":"screen_capture_video","wpm_min":135,"wpm_max":150,"wpm_source":"house default, to be tuned by ear","max_words_per_sentence":15,"max_words_per_sentence_source":"house default","max_sentences_per_beat":2,"max_sentences_per_beat_source":"house default","hook_window_s":8,"hook_window_s_source":"house default","words_budget_180s":400,"words_budget_600s":1300,"words_budget_source":"derived","required_parts":["learning objective","signpost","worked content","recap"],"register":"plain, patient","address_form":"anta/anti","numeral_policy":"spoken form","cta_rule":"recap names the ONE thing to know or do","disclosure_rule":"not applicable","silence_ratio_max":0.20,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"educational","language":"ar","destination":"screen_capture_video","wpm_min":90,"wpm_max":100,"wpm_source":"derived: en band x 0.667","max_words_per_sentence":12,"max_words_per_sentence_source":"house default","max_sentences_per_beat":2,"max_sentences_per_beat_source":"house default","hook_window_s":8,"hook_window_s_source":"house default","words_budget_180s":270,"words_budget_600s":870,"words_budget_source":"derived","required_parts":["learning objective","signpost","worked content","recap"],"register":"MSA","address_form":"anta/anti or antum","numeral_policy":"spoken words","cta_rule":"recap names the ONE thing to know or do","disclosure_rule":"not applicable","silence_ratio_max":0.20,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"podcast","language":"en","destination":"elearning_video","wpm_min":145,"wpm_max":165,"wpm_source":"house default, to be tuned by ear","max_words_per_sentence":18,"max_words_per_sentence_source":"house default","max_sentences_per_beat":3,"max_sentences_per_beat_source":"house default","hook_window_s":15,"hook_window_s_source":"house default","words_budget_180s":430,"words_budget_600s":1450,"words_budget_source":"derived","required_parts":["cold open / intro","chaptered content","outro"],"register":"conversational","address_form":"anta/anti","numeral_policy":"spoken form","cta_rule":"one ask","disclosure_rule":"same as podcast row","silence_ratio_max":0.20,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"podcast","language":"ar","destination":"elearning_video","wpm_min":97,"wpm_max":110,"wpm_source":"derived: en band x 0.667","max_words_per_sentence":14,"max_words_per_sentence_source":"house default","max_sentences_per_beat":3,"max_sentences_per_beat_source":"house default","hook_window_s":15,"hook_window_s_source":"house default","words_budget_180s":290,"words_budget_600s":970,"words_budget_source":"derived","required_parts":["cold open / intro","chaptered content","outro"],"register":"white dialect or MSA per brief","address_form":"anta/anti or antum","numeral_policy":"spoken words","cta_rule":"one ask","disclosure_rule":"same as podcast row","silence_ratio_max":0.20,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"walkthrough","language":"en","destination":"podcast_audio","wpm_min":140,"wpm_max":160,"wpm_source":"house default, to be tuned by ear","max_words_per_sentence":15,"max_words_per_sentence_source":"house default","max_sentences_per_beat":2,"max_sentences_per_beat_source":"house default","hook_window_s":8,"hook_window_s_source":"house default","words_budget_180s":420,"words_budget_600s":1400,"words_budget_source":"derived","required_parts":["goal statement","step-by-step (say-then-do)","confirmation"],"register":"instructional-conversational","address_form":"anta/anti","numeral_policy":"spoken form; UI labels quoted verbatim","cta_rule":"confirmation line names the checkable end state","disclosure_rule":"not applicable","silence_ratio_max":0.18,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"walkthrough","language":"ar","destination":"podcast_audio","wpm_min":93,"wpm_max":107,"wpm_source":"derived: en band x 0.667","max_words_per_sentence":12,"max_words_per_sentence_source":"house default","max_sentences_per_beat":2,"max_sentences_per_beat_source":"house default","hook_window_s":8,"hook_window_s_source":"house default","words_budget_180s":280,"words_budget_600s":930,"words_budget_source":"derived","required_parts":["goal statement","step-by-step (say-then-do)","confirmation"],"register":"instructional","address_form":"anta/anti","numeral_policy":"spoken words; UI labels quoted verbatim","cta_rule":"confirmation line names the checkable end state","disclosure_rule":"not applicable","silence_ratio_max":0.18,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"event_promo","language":"en","destination":"social_video","wpm_min":150,"wpm_max":170,"wpm_source":"house default - inherits commercial|en|social_video row","max_words_per_sentence":12,"max_words_per_sentence_source":"house default","max_sentences_per_beat":1,"max_sentences_per_beat_source":"house default","hook_window_s":3,"hook_window_s_source":"house default","words_budget_15s":38,"words_budget_30s":75,"words_budget_source":"derived, same as commercial","required_parts":["hook","what+why attend","date/place/link"],"register":"direct, second person","address_form":"anta/anti or plural","numeral_policy":"spoken date/time in full","cta_rule":"one concrete come/register action with date+link","disclosure_rule":"not applicable","silence_ratio_max":0.15,"silence_ratio_max_source":"house default","loudness_target_lufs":-14,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"event_promo","language":"ar","destination":"social_video","wpm_min":100,"wpm_max":113,"wpm_source":"derived: en band x 0.667","max_words_per_sentence":10,"max_words_per_sentence_source":"house default","max_sentences_per_beat":1,"max_sentences_per_beat_source":"house default","hook_window_s":3,"hook_window_s_source":"house default","words_budget_15s":26,"words_budget_30s":52,"words_budget_source":"derived","required_parts":["hook","what+why attend","date/place/link"],"register":"white dialect for consumer events; MSA for institutional","address_form":"anta/anti split; plural antum for mixed","numeral_policy":"spoken words; date/time in full Arabic words","cta_rule":"one come/register action with date+link","disclosure_rule":"not applicable","silence_ratio_max":0.15,"silence_ratio_max_source":"house default","loudness_target_lufs":-14,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"recruitment","language":"en","destination":"elearning_video","wpm_min":135,"wpm_max":155,"wpm_source":"house default - hook/CTA from commercial, body pacing from educational","max_words_per_sentence":15,"max_words_per_sentence_source":"house default","max_sentences_per_beat":2,"max_sentences_per_beat_source":"house default","hook_window_s":5,"hook_window_s_source":"house default","words_budget_60s":150,"words_budget_180s":400,"words_budget_source":"derived (house default)","required_parts":["hook","role/programme explained accurately","one apply CTA"],"register":"direct, second person, accurate","address_form":"anta/anti","numeral_policy":"spoken form","cta_rule":"one verb (apply/link), exactly once, at the end","disclosure_rule":"not applicable","silence_ratio_max":0.16,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"recruitment","language":"ar","destination":"elearning_video","wpm_min":90,"wpm_max":103,"wpm_source":"derived: en band x 0.667","max_words_per_sentence":13,"max_words_per_sentence_source":"house default","max_sentences_per_beat":2,"max_sentences_per_beat_source":"house default","hook_window_s":5,"hook_window_s_source":"house default","words_budget_60s":100,"words_budget_180s":270,"words_budget_source":"derived","required_parts":["hook","role/programme explained accurately","one apply CTA"],"register":"white dialect or MSA per brief","address_form":"anta/anti or antum","numeral_policy":"spoken words","cta_rule":"one verb (apply/link), exactly once, at the end","disclosure_rule":"not applicable","silence_ratio_max":0.16,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"investor_partnership","language":"en","destination":"podcast_audio","wpm_min":145,"wpm_max":165,"wpm_source":"house default - educational sentence ceiling, commercial CTA rule","max_words_per_sentence":18,"max_words_per_sentence_source":"house default","max_sentences_per_beat":3,"max_sentences_per_beat_source":"house default","hook_window_s":10,"hook_window_s_source":"house default","words_budget_180s":430,"words_budget_600s":1450,"words_budget_source":"derived (house default)","required_parts":["opportunity","traction (kb:#id required)","one checkable ask"],"register":"conversational, precise, second person","address_form":"anta/anti","numeral_policy":"spoken form; every figure carries a kb:#id","cta_rule":"one verb, one checkable ask (meeting/deck/reply)","disclosure_rule":"not applicable","silence_ratio_max":0.18,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"},
    {"genre":"investor_partnership","language":"ar","destination":"podcast_audio","wpm_min":97,"wpm_max":110,"wpm_source":"derived: en band x 0.667","max_words_per_sentence":15,"max_words_per_sentence_source":"house default","max_sentences_per_beat":3,"max_sentences_per_beat_source":"house default","hook_window_s":10,"hook_window_s_source":"house default","words_budget_180s":290,"words_budget_600s":970,"words_budget_source":"derived","required_parts":["opportunity","traction (kb:#id required)","one checkable ask"],"register":"MSA or white dialect per brief, precise","address_form":"anta/anti or antum","numeral_policy":"spoken words; every figure carries a kb:#id","cta_rule":"one verb, one checkable ask","disclosure_rule":"not applicable","silence_ratio_max":0.18,"silence_ratio_max_source":"house default","loudness_target_lufs":-16,"loudness_target_source":"house default","caption_rule":"verbatim spoken words"}
  ],
  "delivery": {
    "commercial|en": {"target_emotion":"desire, confidence","pause_ms_dramatic":450,"pause_ms_breath":200,"arc":"open fast, lift on proof, land hard short on CTA"},
    "commercial|ar": {"target_emotion":"desire, confidence","pause_ms_dramatic":450,"pause_ms_breath":200,"arc":"open fast, lift on proof, land on stressed final word"},
    "educational|en": {"target_emotion":"curiosity, reassurance","pause_ms_dramatic":500,"pause_ms_breath":200,"arc":"open with objective, small lift at the aha, settle on recap"},
    "educational|ar": {"target_emotion":"curiosity, reassurance","pause_ms_dramatic":550,"pause_ms_breath":220,"arc":"open with objective, small lift at the aha, settle on recap"},
    "walkthrough|en": {"target_emotion":"calm competence","pause_ms_dramatic":300,"pause_ms_breath":150,"arc":"flat-to-slightly-rising through steps, settle on confirmation"},
    "walkthrough|ar": {"target_emotion":"calm competence","pause_ms_dramatic":320,"pause_ms_breath":150,"arc":"flat-to-slightly-rising through steps, settle on confirmation"},
    "podcast|en": {"target_emotion":"intimacy, presence","pause_ms_dramatic":650,"pause_ms_breath":175,"arc":"hook/tease, small lifts per chapter, quiet intimate outro"},
    "podcast|ar": {"target_emotion":"intimacy, presence","pause_ms_dramatic":650,"pause_ms_breath":175,"arc":"hook/tease, small lifts per chapter, quiet intimate outro"},
    "event_promo|en": {"target_emotion":"urgency, invitation","pause_ms_dramatic":400,"pause_ms_breath":180,"arc":"same as commercial|en"},
    "event_promo|ar": {"target_emotion":"urgency, invitation","pause_ms_dramatic":420,"pause_ms_breath":190,"arc":"same as commercial|ar"},
    "recruitment|en": {"target_emotion":"aspiration, trust","pause_ms_dramatic":450,"pause_ms_breath":200,"arc":"open on the role, lift on impact, land on apply"},
    "recruitment|ar": {"target_emotion":"aspiration, trust","pause_ms_dramatic":470,"pause_ms_breath":210,"arc":"open on the role, lift on impact, land on apply"},
    "investor_partnership|en": {"target_emotion":"confidence, credibility","pause_ms_dramatic":500,"pause_ms_breath":200,"arc":"open on opportunity, lift on traction, land on the ask"},
    "investor_partnership|ar": {"target_emotion":"confidence, credibility","pause_ms_dramatic":520,"pause_ms_breath":210,"arc":"open on opportunity, lift on traction, land on the ask"}
  }
}
```

## 11. Voice & styles (Kore) — the rule every project inherits

Registry: `voice-styles.json` beside this file (the one global copy; evidence and
samples: ENSERA `documentation/11-Voice-Design/v2/`). Lister: `scripts/voice_style.py`.
Gate: `scripts/voice_style_gate.py`. This section holds the rules; the registry holds
the values, and **the registry wins** if the table below ever disagrees.

- **Engine and voice:** Gemini 3.1 Flash TTS via OpenRouter (`google/gemini-3.1-flash-tts-preview`), voice **Kore** (Female, 25-35, warm and confident; Arabic MSA, English neutral American). The only engine.
- **HARD RULE — one model, one take (the owner 2026-10-03, permanent):** `google/gemini-3.1-flash-tts-preview` is the ONLY model any voice pipeline may call. No other model of any kind — no transcriber/ASR, no LLM judge, no tashkeel checker, no second TTS. Each line is voiced ONCE: no verify, no re-voice, no best-of-N takes. the owner checks the finished product by ear. The 2026-10-01 verify/re-roll step (`tashkeel_verify.py`, gemini-3.6-flash) was removed for cost; never reintroduce it. Offline deterministic gates that make no model call (`voice_style_gate.py`) stay.
- **Pace:** Arabic 115 wpm (band 110-120), English 150 wpm (band 145-155): visible words / finished clip seconds x 60, per-clip atempo after the silence trim. Applied tempo never above **1.7**.
- **Loudness:** `loudnorm=I=-14:TP=-2.0:LRA=11` single final pass (§7).
- **Tashkeel (the owner 2026-10-01, binding):** Arabic text sent to TTS carries full tashkeel on EVERY word, on every letter that takes a mark and on case endings (إعراب), no exceptions, proofread with `arabic-english-proofreading` before voicing; visible text keeps only the marks the source itself writes. Only a letter that takes no mark (bare alif, madd و/ي after damma/kasra, ى, the lam of ال before a sun letter) goes bare. The manifest carries the marked text as `tts_text`; the gate fails the line otherwise.
- **Where the marks live (the owner 2026-10-01):** website and PDF wording stays EXACTLY as the source writes it, its own tanween and shadda included. Tashkeel is added ONLY to the TTS input (`tts_text`), letters unchanged.
- **How to send Arabic (measured, KB `reference/arabic-tashkeel/`, rules R-TASHKEEL-001..009):** `input = direction + tts_text`, one sentence per call. (1) Full marks stay: 96.2% of words voiced as sent vs 91.1% bare, and the take-to-take swing shrinks. (2) Marks in NFC order (vowel, then shadda); re-ordering to shadda-first measured no better. (3) Never split a shadda into letter+sukun+letter (89.9%, worse). (4) Write full case endings; Kore reads clause ends in waqf by itself, never force it with sukun. (5) Digits are voiced acceptably but cannot carry marks, so spell out a number whose case or gender matters; spell acronyms in Arabic letters in the TTS text (PDF as بِي دِي إِفْ). (6) **Voice is stochastic** (the same marked text can change vowels between calls) — accepted: one take, no verify/re-roll (hard rule above). Known gaps: shadda minimal pairs (مُعَلِّم / مُعَلَّم) came back as sent only 71% and no respelling fixed it; loanwords such as إلكترونيا follow the marks about 2 of 3 takes.
- **Pre-voicing gates (the owner 2026-10-03):** `voice_style_gate.py --text-only` (every check that needs no audio) runs in compose before the first TTS call, and `tashkeel_fix_apply.py` (real apply or `--stamp`) writes `narration.ar.checked.json` {step id -> sha256 of ttsAr}; on a cache miss an AR line whose sha is not in the receipt is refused before any call. A refused line costs zero calls; cache hits are never refused.
- **Brand in Arabic:** إنسيرا.
- **Direction syntax:** Direction is a natural-language English prefix to the input text, used for both languages; Gemini does not speak it (read-back checked). Send `direction + text` as `input`; one style per clip.
- **Never invent or edit a direction.** Wording changes the audio. Need a delivery no style gives? Propose a new style (registry entry + sample + read-back), do not improvise one inline.

| id | good_for | never_for | direction (byte-exact) |
|---|---|---|---|
| `reel` | Social reels, short promos, teasers, launch clips under about 60 s. | Safety notices, legal or regulatory statements, step-by-step manuals (energy reads as hype and rushes the listener). | Say this warmly and confidently with a smile in your voice, with more energy and a lively, upbeat pace, like a friendly expert sharing exciting news: |
| `manual` | User manuals, tutorials, e-learning explainers, onboarding walkthroughs and narrated product demos (this style also covers explainer, demo and welcome use). | Announcements, ads, anything urgent: the unhurried pace makes urgency sound careless. | Say this warmly and confidently with a smile in your voice, calm and clear, unhurried, like a friendly expert guiding someone step by step: |
| `official` | Company statements, press and ministry-facing text, announcements and news items, formal introductions, investor or grant material. | Reels, stories, casual chat: the formal register sounds cold where warmth is needed. | Say this warmly and confidently, composed and measured, with a formal professional tone: |
| `story` | Brand story, founder or mission narration, testimonials told as narrative, keynote or inspirational openings, about-us films. | Instructions, data, warnings: emotion gets in the way of the information. | Say this warmly and confidently, with more emotion and feeling, like a storyteller who cares about the story: |
| `alert` | Robot and workplace safety notices, warnings, error and failure messages in a product, critical reminders where the listener must act. | Marketing, welcome, storytelling; and gentle recoverable product errors ("something went wrong, try again"), which belong to chat: a firm tone turns a friendly message into a scolding. | Say this warmly and confidently but firm and serious, clear and deliberate, like a caring safety officer who needs you to listen: |
| `data` | Statistics and results readouts, QA and test-report summaries, dashboard and quarterly-figures narration, benchmark results. | Reels, stories, invitations: the level, even delivery flattens anything meant to move people. | Say this warmly and confidently, but crisp and matter-of-fact, brisker than usual, with a short beat before each number and a clear stress on the figures, no emotional colouring, like an analyst reading out results: |
| `invite` | Event and open-day invitations, programme and webinar calls to join, call-to-action closes at the end of a film or post. | Warnings, official statements, data: the bright, personal address sounds out of place. | Say this warmly and confidently, in a soft, personal, intimate tone, a little slower than a promo, with a gentle rising lift on the final invitation, like a host quietly inviting a friend to join: |
| `chat` | Assistant and chatbot voice, FAQ answers, podcast-style asides, customer-support replies, informal Q and A, short testimonial-style quotes. Also gentle recoverable errors and soft apologies. | Official statements, warnings, long narration: the casual register undermines authority and drifts over length. | Say this warmly and confidently, in a relaxed, natural, conversational way, like talking to a colleague over coffee: |

### FIRST-USE RULE (binding, any project, any agent)

Before a project's first narration, in this order:
1. Run `PYTHONUTF8=1 python <nj-writer>/scripts/voice_style.py list`.
2. Pick the style per line by `good_for` / `never_for`, not by taste.
3. Record per line in the project's narration manifest (`narration-manifest.json`): `id`, `lang`, `style`, `direction` (copied from `voice_style.py get <id>`), visible `text`, `tts_text` (every Arabic line: the fully marked text sent to TTS), finished `seconds`, applied `tempo`.
4. Run `PYTHONUTF8=1 python <nj-writer>/scripts/voice_style_gate.py narration-manifest.json`. A FAIL blocks delivery: no style, unregistered style, edited direction, wpm outside the band, tempo above max, visible text that looks like the TTS text pasted in (over 50% of its Arabic words marked; the portal's own marks such as فتحاً are allowed); for Arabic: no `tts_text`, a word with no mark, a letter (case ending included) without its mark, `tts_text` letters differing from the visible text, a shadda split into letter+sukun+letter, a control character in `tts_text`. The gate names every failing word.
