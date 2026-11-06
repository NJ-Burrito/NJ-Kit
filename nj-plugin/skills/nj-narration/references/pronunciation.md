# Pronunciation: the lexicon, numbers, and where tashkeel comes from

Template: `templates/lexicon.example.json`. Research date 2026-11-07.

## 1. The lexicon

A TTS engine reads the text it is given, so a wrong word is a text fault with a text fix. One versioned lexicon per project
holds the readings the owner and the writer have decided: names, foreign words written in Arabic letters, abbreviations, and
the way numbers are read. Rules:

- It rewrites the TTS text only. The visible text (captions, subtitles) is never vowelled or respelled by it.
- Every entry says who decided it and when, and when the owner heard it right.
- A changed entry changes the words, so every line that uses it is a new line (`retext`). The old take stays on disk; the
  once-per-line gate still refuses a second take of the old line.
- Numbers are written out as words in the TTS text, in the case the sentence needs (gender of the counted noun, case ending).
  Years, ordinals, times and decimals are listed once so every line reads them alike.
- Names are respelled with the vowels the engine should say, plus a plain-letter `reading` note for the owner's ear.
- An offline check lists every lexicon term found in the script and every digit or Latin letter left in a TTS text. No model
  checks pronunciation; no ASR. Listening is the owner's.

A published method for lexicons of names and foreign words for neural TTS was not found in this research pass (gap). The
design above is the minimum that keeps the one-take rule: decide the reading in the text before voicing.

## 2. Tashkeel: where it comes from

Diacritized input helps small-data Arabic TTS: in a 2026 study of an open TTS model, word error rate fell from 3.18 to 1.67
at 4,000 h, from 3.12 to 2.55 at 1,000 h, and from 4.06 to 3.48 at a 100 h maximum-diversity set (Musleh, Zhang, Darwish,
arXiv:2603.01622, 2026-03-02; the metric is ASR WER and an embedding score, not listeners; the model is not ours). Whether
Chatterbox gains the same is untested: try one line by ear. Another system showed phoneme error 3 to 6 times lower with
vowelled input for two locales (arXiv:2307.16709, context only).

**A diacritizer is a model. Our rule is no model of any kind in the voice pipeline except the one TTS model, so adopting a
diacritizer is an owner decision, recorded in the project. Until the owner approves one, tashkeel is written by the writer
stage, by hand, in the TTS text only.** A tool, when approved, runs offline on the script text, never on audio.

| Tool | Licence | Evidence (different benchmarks, DER not comparable across tables) | Local | Verdict |
|---|---|---|---|---|
| CATT (abjadai/catt) | paper says open-sourced; repo and weights licence not read | CATT benchmark, ED model: DER 8.624 with case endings, WER 34.191; GPT-4 9.515, Shakkala 13.494, Farasa 17.825 (arXiv:2407.03236, 2024) | likely (small transformer); not tested | strongest candidate on evidence; read the repo licence first |
| Sadeed (misraj-ai) | not stated on the paper page; repo licence not read | authors' SadeedDiac-25: DER 7.2915 with case endings, 5.2625 without; reports 7.19 hallucinations; self-reported (arXiv:2504.21635v2, 2025). The paper criticises the CATT benchmark's labels | probably, 1.5 B parameters; not tested | best open option on its own benchmark; check licence first |
| Mishkal (linuxscout) | GPL-3.0; rule-based, no ML | CATT table: DER 16.482 with case endings, 10.796 without; WikiNews 15.246 / 8.558 | yes | safe on "no ML", weakest on the tables; GPL-3.0 is an owner licence call; fallback or lexicon helper |
| Shakkala (Barqawiz) | MIT | README "up to 95%" on a beta (no dataset); CATT table DER 13.494 | yes | permissive licence, older model; fallback only |
| Farasa (QCRI) | toolkit research-use only (wrapper MIT; commercial use via the university) | CATT table DER 17.825 | yes | not for commercial output; official repo URL returned 404 on fetch |
| Tashkeel-v3 (gyoom-sa) | not read | self-reported DER 2.85 (SadeedDiac-25), 6.37 (CATT benchmark) | probably | unverified; skip until a licence and an independent run exist |
| Fine-Tashkeel (ByT5) | not read | arXiv:2303.14588 (2023); trained on Classical Arabic | yes | register mismatch for MSA drama; skip |

No tool is both licence-clean and proven for MSA drama on our data. Two to check first: CATT and Sadeed (licences). If the
owner approves one: run it once on the script, write the result into the TTS text, have the writer correct it, freeze it.
The output is still text the writer owns; the diacritizer is never in the loop at voicing time.

## Sources

- arXiv:2603.01622 (2026-03-02); arXiv:2307.16709 (2023); arXiv:2407.03236v3 (CATT, 2024); arXiv:2504.21635v2 (Sadeed, 2025); arXiv:2303.14588 (2023).
- github.com/linuxscout/mishkal; github.com/Barqawiz/Shakkala; farasapy README on pypi.org (all fetched 2026-11-07).
