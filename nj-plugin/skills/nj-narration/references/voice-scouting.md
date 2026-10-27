# Voice scouting: from a character to a shortlist the owner hears

Source: the calibration project narrator search, 2026-10-26 (a scout brief, a judge script,
`ranking.json`, `top3.json`): 18 scouts, 388 rows, 363 distinct speakers measured, 10 voiced,
top 3 to the owner's ear; he picked one Common Voice CC0 clip by ear.

## 1. Start from the need and the character

Read the story bible and the owner's words first. Write down, in their words and with the date, what they want the voice
to do and what they rejected. Then fill `templates/casting-brief.md`:

- **Who**: role, age band, sex as heard, origins and backstory, region, the register (MSA or a named dialect, or a named
  English accent), the personality heard in the voice.
- **What it measures as**: target F0 band, pitch movement, smoothness, warmth (centroid), brightness (top band), room
  (decay), cleanliness (SNR with a real floor), pace (letters or words per second), dynamics (crest).
- **Accent comes from the reference and the written word habits**, never from effects or level.

Example that worked: "male MSA narrator, radio broadcaster (صوت إذاعي): deep, warm, calm, authoritative, studio-clean"
became F0 90-115 Hz full score, F0 sd 1.8-3.5 st, decay20 <= 0.06 s, SNR >= 50 dB, centroid 450-750 Hz.
the owner's earlier verdict "get another narrator voice type ... deep and sound like wisdom" is what moved the band down.

## 2. Write the rubric before you measure

Copy `templates/rubric.broadcaster-male.json`, set each band from the brief, save it beside the brief. Gates come
before the score (licence tier, target sex by F0 band, not already rejected, duplicates merged, REF-QUALITY pass ranks
above fail). Never retune the rubric after seeing a ranking; a wrong rubric means a new search with a new file.

## 3. The clean-data standard

| Allowed | Condition |
|---|---|
| Mozilla Common Voice | CC0-1.0, community-validated (record up/down votes; the calibration project needs >= 2 up, 0 down) |
| LibriVox | Public domain; provenance carries the source page and a licence evidence URL; validation `published-audiobook` |
| Wikimedia Commons / Lingua Libre | CC-BY or CC-BY-SA with the speaker's own upload; attribution kept. Share-alike on a voice is the owner's decision: rank as tier B |
| Studio corpora | Only with a licence text read and saved that allows commercial use and cloning, and speaker consent documented (e.g. a single-speaker TTS corpus released for synthesis). Unclear = tier B or out |
| Own or talent recording | Written consent naming cloning, commercial posting and AI disclosure; stored outside the repo, referenced by date and holder |

**Banned**: scraped YouTube, podcasts, radio, TV, found clips; celebrities, journalists, religious reciters, any
identifiable public figure or anyone who did not consent; no sound-alike of a known voice; non-commercial (NC) or
research-only corpora; unread or unclear licences; clips with unknown processing history; any voice the owner banned;
any banned engine.

**Tiers** (first match wins): X = banned (named public figure, PA or broadcast, a commercial
course tape uploaded by a third party, a lecture where the lecturer is not the uploader); A = castable today (CC0, PD);
B = licence allows it but consent undocumented, or share-alike; ranked below A, not castable without the owner.

**Provenance per reference** (`templates/provenance.example.json`): source_url, download_url, licence + evidence URL,
consent, validation and votes, source span with sha256 of the download, the DSP log, sha256 of the clip as cloned,
measures with an empty problem list, readers_note (never identify a volunteer), transcript only if published (never
ASR). A missing field or a hash mismatch means not castable.

**The engine's own training data** is a separate, open risk: Chatterbox, SILMA and every open model checked state no
per-speaker consent for their training data (`research/voice/msa-narrator-2026-10-26.md`). Say it plainly; moving to an
engine with documented consent, or a narrator who records for you, is the owner's decision.

## 4. Search by slice (parallel scouts)

One scout per slice so no two read the same files; each writes only its own folder (`templates/scout-brief.md`).
Slices that worked: Common Voice by split (test / dev / train shards, each a scout), Common Voice mirrors, LibriVox by
book and reader, Wikimedia Commons / Lingua Libre by language category, named studio corpora one per scout. Expect access
walls (Mozilla Data Collective needs a bearer token: the scout reports 0 and does not sign up). Merge on a speaker key
(Common Voice client-id prefix, LibriVox reader slug), keep the first scout's row for a duplicate.

## 5. Measure with signal metrics only

`scripts/voice_measure.py ref <clip> --edge-fix --rate 24000 --rubric <rubric.json>` gives the REF-QUALITY profile,
F0 stats (librosa pyin) and the score. Every clip at the same rate. No ASR, no model, no LLM listening.

## 6. Voice a shortlist, judge the takes, present 3

1. Take the top 10 by reference score (tier A first). Clean each reference once (`references/voice-engineering.md` 2).
2. Voice the same 5 lines per voice, one model load, one take per line, seeds from the ids, the same settings for all.
3. Trim and master each take through the project chain, then score the takes (the take rubric): edge noise 25,
   problem flags 20, pitch 20, natural movement 10, cleanliness 10, stability across takes 5, warmth 5, sibilance 5.
   Final = 0.4 x reference + 0.6 x take score; tier A always above tier B.
4. **Before the owner listens, re-measure REF-QUALITY on the edge-cleaned reference you will actually clone** (see 7), not on the judged clip.
5. Build a local preview page with the top 3 (a joined clip per voice, provenance beside it). The owner listens and
   picks. The judge never picks; "numbers are not ears".
6. Record the pick (`narrator-record.json`: who chose, when, from which ranking, engine settings). Frozen from then on.

## 7. Lessons that cost a round

- **Common Voice MP3 edges create false "digital silence" fails.** MP3 decode and encoder padding leave exact zeros at
  the clip edges; zero_frac then exceeds 2 % and REF-QUALITY says "gated or denoised". Fix the measurement input
  (`--edge-fix`: strip exact-zero and sub-floor edges, inside untouched), never loosen the limit. calibration project: 21 clips
  passed before the fix, 30 after; One reference clip had 68 ms + 19 ms of zeros and failed until fixed.
- **A gate's digital silence reads as the best floor ever.** A clip whose pauses are exact zero shows a -88 dBFS floor
  and a huge SNR while the speech is boxy. That is why REF-QUALITY has a minimum floor (-75 dBFS) and a zero share limit.
  A narrator later banned passed every older limit this way.
- **pyin floor artefacts.** pyin pinned at its 60 Hz floor reports a "deep voice" that is creak or noise. Count the share
  of voiced frames under 66 Hz; above 0.15 the pitch criterion scores 0.
- **Gender is a source label, F0 is a proxy.** Use F0 (median under 165 Hz for a male target) to sort, never to label a
  person; a mislabelled or unlabelled clip is marked as a proxy.
- **Votes matter.** A clip nobody validated (0 up) can be a misread or a noisy take.
- **Edge room tone flatters the gate (calibration project casting, 2026-10-27).** A judged clip can pass REF-QUALITY only because the
  quiet edges lower the measured noise floor and raise the SNR. Cut the edges (`voice_edges.py clean --no-pad`, the clip as it
  will be cloned) and the same voice can fail: 3 of 7 owner picks did (floor -46.6 to -50.8 dBFS against the -53 limit;
  SNR 28-34 dB against 35). So measure REF-QUALITY on the edge-cleaned reference, as cloned, before the owner listens, and
  keep that measure in the provenance. Never judge, then clean, then trust the first number.
- **A failed pick walks the ranking, never the gate.** Take the next candidate of the same voice slot that passes as cloned
  (one candidate failed at -50.8 dBFS, the next passed at -69.2 dBFS, SNR 52.7) and let the owner hear that one. Do not loosen a limit
  to keep the owner's first choice. Flag any reference shorter than about 5 s (the passing clips ran 4.3-4.6 s): little
  speech for the engine to copy, so the owner's ear checks it first.
- **Rejected voices stay rejected.** Keep a REJECTED list (ids and the owner's words) and exclude them before scoring.
- **What the owner rejected and why** (calibration project, by ear): "too noise and not clear" (a noisy, muffled reference),
  "bad" (SILMA, dropped as an engine), "get another narrator voice type ... deep and sound like wisdom" (the 3-star
  male: right engine, wrong voice). Approved: clips with floor -55 to -63 dBFS, SNR 36-42 dB, crest 20-23 dB, decay
  0.05-0.12 s.
