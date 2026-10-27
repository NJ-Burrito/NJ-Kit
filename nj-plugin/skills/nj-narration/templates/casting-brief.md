# Casting brief: <character or narrator name>

Fill this before any search. Every row turns a person-word into a number or a rule the scouts can measure.
Written once, approved by the owner, then frozen for the search (a changed brief is a new search).

## 1. Who the voice is (from the story, not from a voice you already like)

| Field | Answer |
|---|---|
| Role | narrator / main character / side character |
| What the owner asked for, in their words | (quote it, with the date) |
| Age band | e.g. 45-60 |
| Sex as heard | male / female / either |
| Origins and backstory that change the sound | e.g. grew up in Aleppo, taught school for 30 years, speaks slowly and precisely |
| Ethnicity / region, only where it changes accent or delivery | |
| Language register | MSA (Fusha) / dialect: name it (Levantine, Gulf, Egyptian, Maghrebi, Iraqi) / English accent: name it |
| Personality heard in the voice | e.g. warm, calm, wise, dry humour; never: hype, sarcasm |
| Voices the owner has already rejected or banned | ids and the words they used |

## 2. The measurable target (the casting brief proper)

| Attribute | Target | Measure | Source of the number |
|---|---|---|---|
| Pitch (median F0) | e.g. 90-115 Hz full score, 0 at 75 / 150 | pyin median F0 | typical adult male 85-155 Hz, female 165-255 Hz; set the band from the brief |
| Pitch movement | e.g. 1.8-3.5 semitones sd (calm, not monotone) | F0 sd in semitones | |
| Smoothness | e.g. median frame step <= 0.15 st | F0 frame-to-frame step | |
| Timbre: warmth | e.g. centroid 450-750 Hz | speech power centroid | |
| Timbre: brightness / band | e.g. top band >= -38 dB | energy > 8 kHz re 0.1-1 kHz | |
| Room | dry: decay20 <= 0.06 s | reverb proxy | |
| Cleanliness | SNR >= 50 dB with a real floor (-75 to -53 dBFS) | REF-QUALITY | |
| Pace | e.g. 6-8 letters/s Arabic, 130-150 wpm English | letters / speech span | |
| Energy / dynamics | crest 20-26 dB | peak minus median speech level | |
| Accent / dialect | the source's own label (Common Voice `accent`, LibriVox reader page) | metadata, never a guess from audio | |

Gender, age and accent labels come from the source's metadata. F0 is a proxy, not an identity: use it to sort, never to
label a person. A clip with no label that passes only by F0 is marked "label: F0 proxy" in its row.

## 3. Hard rules for this search

- Allowed sources and banned sources: `references/voice-scouting.md` section 3.
- No ASR, no speech model, no LLM that listens. Signal measures and this rubric only.
- One clip of 6-15 s per speaker, mono, the source rate or 24 kHz; provenance per clip (`templates/provenance.example.json`).
- Top 3 go to the owner's ear. The judge picks nothing.

## 4. The rubric (written before measuring)

Copy `templates/rubric.broadcaster-male.json`, set the bands from section 2, save it next to this brief, and do not edit
it after the first measurement. If the rubric was wrong, say so and run a new search with a new rubric file.
