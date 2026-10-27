# Voice scout brief (one per scout; the slice is named in the prompt)

Generalised from a production scout brief (2026-10-26: 18 scouts, 363 speakers measured).

Goal: <one line from the casting brief, e.g. "a male MSA narrator, deep, warm, calm, studio-clean">.
Casting brief: <path>. Rubric: <path> (do not edit). Your slice: <source family + split / page range / query set>.
Aim: at least 20 distinct speakers in your slice.

## Hard rules
- Clean data only (references/voice-scouting.md section 3). Record the licence URL for every clip.
- Banned: scraped YouTube / podcast / radio / TV of identifiable people, celebrities, journalists, religious reciters,
  non-commercial (NC) or research-only datasets, unclear licences, any banned engine or voice.
- No ASR, no speech model, no LLM listening. Judge only with signal measures.
- Write ONLY inside <work>/voice-scout/<your-id>/. Never edit tracked files. No git. Do not sign up for anything.
- Python via `uv run --with numpy --with scipy --with librosa`; PYTHONUTF8=1; ffmpeg for cutting. No GPU.
- Small downloads: one best clip of 6-15 s per speaker. Stop every process you start.

## Measure every clip the same way
`uv run --with numpy --with librosa --with scipy <skill>/scripts/voice_measure.py ref <clip.wav> --edge-fix --rate 24000
--rubric <rubric.json>` (or the project's own measure functions, if the brief names them, so every scout is comparable).

## Output (your folder)
- `clips/<speaker_id>.wav`
- `candidates.jsonl`, one JSON per speaker: scout, speaker_id, source_name, source_url (exact file), licence, licence_url,
  consent_basis, gender and age_band and accent (only as the source labels them), clip_path, transcript (only if the source
  publishes one; never generated), metrics, ref_quality_pass, notes
- `SUMMARY.md` (at most 15 lines): speakers found and measured, top 5 by the rubric, licence doubts, access walls hit.
Receipt (at most 10 lines): speakers measured, top 3 ids with F0 / SNR, folder path.
