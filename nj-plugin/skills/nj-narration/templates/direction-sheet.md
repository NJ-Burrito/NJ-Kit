# Direction sheet: <character or narrator>

One sheet per character (the standing direction, written once, owner-approved, then frozen) and a short block per line
(only what differs from the standing direction). Written BEFORE the line is voiced: there is one take, so the direction
cannot be fixed afterwards. Method and sources: `references/direction.md`.

Rules for filling it:
- Say what you want in plain words first, then map it to the knobs the engine really has (section 3). A word the engine
  cannot act on is deleted, not kept as a wish.
- Never add a persona, accent or age the owner did not ask for. Make implicit details explicit; do not invent new ones.
- Do not mix opposing instructions ("calm but urgent"). One register per line; a shift is two lines.
- Change one thing at a time between settings trials. A trial is a throwaway line at casting, one take per setting, the
  owner picks by ear; the result is frozen here. It is never repeated per line.
- Tags or markup only if the engine's own documentation lists them. Test on one throwaway line by ear before relying on them.

## 1. Standing direction (per character)

| Field | Entry |
|---|---|
| Voice id and reference sha256 | (from the casting record) |
| Engine and version | |
| Affect | e.g. grave, unhurried, certain |
| Tone | e.g. warm, dry, no irony |
| Pacing | target rate band (words or syllables per second, set from the owner's approved take, not from the first sample) |
| Emotion range | which registers this voice uses (neutral, tender, angry, afraid, ...) and which it never uses |
| Pronunciation | the lexicon file and version (`templates/lexicon.example.json`); tashkeel policy |
| Pauses | where the voice breathes: after a clause mark, before a name, never mid-word |
| Emphasis | how stress is shown in the text (word order, punctuation), not by volume |
| Delivery | close, intimate, no projection / projected, hall; the distance the reference carries |
| Reference per register | file, length (5-8 s), transcript file, sha256 (`references/reference-prep.md`) |
| Banned | what the owner rejected, in their words, with the date |

## 2. Per line (only differences)

| Line id | Text (tashkeel in the TTS text only) | Register | Pace nudge | Pause before / after | Emotion | Knob changes (section 3) | Pronunciation notes |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

## 3. Map to the engine's real knobs

| Engine | Knobs it really has | Direction words it can follow | Notes |
|---|---|---|---|
| Chatterbox Multilingual (local) | `exaggeration` 0.25-2.0 (default 0.5), `cfg_weight` 0-1 (default 0.5), `temperature` 0.05-5 (default 0.8); the reference clip; the text (punctuation, tashkeel) | more or less intensity (exaggeration), more or less pace and stability (cfg, temperature) | Higher exaggeration tends to speed speech; lower cfg slows it. Fast reference: cfg about 0.3. Expressive: cfg about 0.3 with exaggeration about 0.7 or more. Accent leaking from the reference: cfg 0. Paralinguistic tags (`[laugh]`, `[chuckle]`, `[cough]`) are listed for the Turbo model only: not assumed for Multilingual. Source: engine README, fetched 2026-11-07 |
| ElevenLabs v3 (paid; owner's word) | Audio tags such as `[whispers]`, `[shouts]`, `[softly]`, `[pause]`, `[rushed]`, `[drawn out]`, `[sighs]`; capitals and ellipses for rhythm; stability (lower = tags respond more); one voice per request | tags at the start of a line, few, where the text supports them | SSML is not supported on v3 or v4. A voice that does not fit the delivery may speak the tag aloud. Arabic on v3 is unverified. Source: vendor blog "v3 audio tags", updated 2026-10-15 |
| OpenAI `gpt-4o-mini-tts` (paid; owner's word) | an `instructions` text: accent, emotion, intonation, speed, tone, whisper | a natural-language direction block per take | Model announced for shutdown 2027-01-06. Built-in voices only. Source: vendor TTS guide, fetched 2026-11-07 |
| Azure Neural, Arabic (paid; owner's word) | voice choice (32 Arabic voices, one female and one male per locale) | none: no styles or roles are listed for any Arabic voice | Direction is only the text. Source: vendor language-support page, 2026-10-28 |

Columns of the per-line block follow the "Affect, Tone, Pacing, Emotion, Pronunciation, Pauses, Emphasis, Delivery"
structure of a published speech-prompting guide (OpenAI `speech` skill, `references/prompting.md`, read 2026-11-07); the
engine map and the rules above are from the sources named in the table.

## 4. Approval

| Owner heard | Date | Verdict (their words) | Frozen as version |
|---|---|---|---|
| | | | |
