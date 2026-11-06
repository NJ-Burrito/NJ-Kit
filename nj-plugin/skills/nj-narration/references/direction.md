# Directing a voice: the direction sheet, and what each engine can actually follow

Template: `templates/direction-sheet.md`. Research date 2026-11-07; every source is dated; a vendor claim is marked.

## 1. Why a sheet

The industry standard for expressive speech is a short natural-language direction per take (affect, tone, pacing,
emotion, pronunciation, pauses, emphasis, delivery) that makes implicit details explicit and invents none (OpenAI `speech`
skill and `references/prompting.md`, read 2026-11-07). Our engine is a cloning model with three numeric knobs and no
instruction channel, so the sheet does two jobs: the owner and the writer agree the direction in words before anything is
voiced, then the words are mapped to the knobs, the reference and the text. Words with no knob behind them are removed.

## 2. What the engines can follow

| Engine | Direction channel | Source (date) |
|---|---|---|
| Chatterbox Multilingual (local, MIT) | `exaggeration`, `cfg_weight`, `temperature`, the reference, the text. Defaults 0.5 / 0.5 / 0.8 "work well for most prompts across all languages". Higher exaggeration tends to speed speech, lower cfg offsets it. Fast reference: cfg about 0.3. Expressive: cfg about 0.3, exaggeration about 0.7 or more. Reference accent leaking into the output: cfg 0. Tags `[laugh]`, `[chuckle]`, `[cough]` are listed for the Turbo model, not stated for Multilingual | engine README, fetched 2026-11-07 |
| ElevenLabs v3 / v4 (paid) | Bracketed audio tags (`[whispers]`, `[softly]`, `[pause]`, `[rushed]`, `[drawn out]`, `[sighs]`), capitals and ellipses for rhythm, stability. Tags respond best on voices with wide emotional range; a mismatched voice may speak the tag aloud; SSML unsupported; one voice per request. Overlap and interruption "from tags and script structure alone" is a vendor claim, not measured | vendor blog, updated 2026-10-15; Runware guide (secondary, undated) |
| OpenAI `gpt-4o-mini-tts` (paid) | An `instructions` prompt (accent, emotion, intonation, speed, tone, whisper). Shutdown announced for 2027-01-06 | vendor guide, fetched 2026-11-07 |
| Azure Neural, Arabic (paid) | None: no styles or roles on any Arabic voice | vendor page, 2026-10-28 |

Verdict: direction on the local engine is done with the three knobs, the reference choice, and the script (punctuation, word
choice, tashkeel). Tags are a test, never an assumption: no source shows any local engine handling `[whispers]` or breaths
reliably. Paid engines are used only on the owner's word; their vocabulary is useful as language for the sheet.

**Where the industry differs:** ElevenLabs' audiobook tooling regenerates individual passages until they are right
(secondary source, 2026). That is a re-voice. We keep one take per line; the direction is written before the take so the
take can be right the first time, and a take the owner rejects is a new line with new words, never a retake.

## 3. How to use the sheet in a session

1. Per character, fill section 1 with the owner (words, not numbers), from the casting brief. Pace comes from the owner's
   approved take (band = approved take plus or minus 15 words per minute in the previous casting), not from the first sample.
2. Settings trial, once, at casting, on a throwaway line and not on a script line: one take per setting (for the grave narrator
   in the earlier casting: exaggeration 0.30 against 0.50 against 0.70, same reference, same cfg and temperature). The owner
   picks by ear; the pick is frozen in the sheet. This is a choice of setting, made once, and is not best-of-N on a line.
   Whether to leave the defaults is the owner's call; the research found nothing that says the default is wrong.
3. Per line, write the block only where the line differs. Opposing instructions are not allowed; one register per line.
4. Voice the line once. Edge clean, master, gate. The owner's ear decides last.
5. A pronunciation or word problem is fixed in the lexicon or the text and voiced as a new line (`retext`).

## 4. Pace unit

Words per minute is less precise than syllables per second for Arabic because words differ in syllable count (bilingual
rate study cited in a 2026-11-07 search). No human-verified figure for MSA drama was found; the literature number
(about 4.5 syllables per second for a synthetic MSA voice, Aldholmi et al., Interspeech 2021) is synthetic and is not
used. Measure the owner-approved reference and take, and keep the band in the casting record.

## 5. Dialogue scenes

One clone per speaker per call, the same reference and settings for a speaker across the scene, and the room comes from the
reference, so room drift is a reference problem fixed once at the source, not a per-line one. No published method for turn
timing was found: test one scene by ear before adopting. Multi-speaker open models (a 4-speaker long-form model, a
2-speaker tag-based model) are noted in `engines.md`, untested here.

## Sources

- Chatterbox README, github.com/resemble-ai/chatterbox, fetched 2026-11-07.
- ElevenLabs, "v3 audio tags", elevenlabs.io/blog/v3-audiotags, updated 2026-10-15; Runware, "Directing with audio tags" (secondary).
- OpenAI TTS guide, developers.openai.com/api/docs/guides/text-to-speech, fetched 2026-11-07; OpenAI `speech` skill (github.com/openai/skills, curated), read 2026-11-07.
- Microsoft Learn, Speech language support, ms.date 2026-10-28.
- Aldholmi et al., Interspeech 2021 (isca-archive.org/interspeech_2021/aldholmi21_interspeech).
