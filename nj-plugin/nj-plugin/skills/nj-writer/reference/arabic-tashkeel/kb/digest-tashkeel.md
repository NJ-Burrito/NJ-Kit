# Arabic tashkeel KB digest -- tashkeel -- 2026-10-01

Only `verified` entries. Draft, recheck and stale entries are not publishable.
An entry flagged SELF-VERIFIED or UNKNOWN INDEPENDENCE is not independent corroboration -- do not cite it as a second source.

## #10 asr-lite-noisy
Transcriber choice: gemini-3.5-flash-lite scored the same demo audio 72% with marks and 75% bare (marks looked useless), gemini-3.6-flash scored 96% vs 88%. The lite model is too noisy to verify with; gemini-3.6-flash is the verifier. Other Gemini audio models were blocked by the account guardrail (404). **Retired 2026-10-03 (owner): no transcriber is called any more — gemini-3.1-flash-tts-preview is the only model, one take, no verify.**



- retrieved 2026-10-01, confidence 0.85
- file:///<PROJ_ROOT>/PROJ-tests/work/batch2-2026-09-30/tashkeel-kb/json/run1.json
- file:///<PROJ_ROOT>/PROJ-tests/work/batch2-2026-09-30/tashkeel-kb/json/run2.json

## #11 digits-latin
Digits and Latin tokens are voiced acceptably: ٣٠ يَوْمًا came back as ثَلَاثِينَ يَوْمًا, and PDF as بِي دِي إِفْ (1 clip each). Digits cannot carry marks, so case and gender of the number are the voice own choice.



- retrieved 2026-10-01, confidence 0.85
- file:///<PROJ_ROOT>/PROJ-tests/work/batch2-2026-09-30/tashkeel-kb/json/run1.json

## #14 mark-order
Mark order: vowel-then-shadda (NFC/NFD order, what every tool emits) is at least as good as shadda-first: internal-exact 486/505 (96.2%) vs 466/505 (92.3%), 5 takes each; the shadda-first deficit (3.9 points) is inside its take-to-take spread (per-take range 84-97%). No evidence for re-ordering marks. Noise floor: two 3-take sets of the SAME text scored 96% and 87% in an earlier run.



- retrieved 2026-10-01, confidence 0.85
- file:///<PROJ_ROOT>/PROJ-tests/work/batch2-2026-09-30/tashkeel-kb/json/run5.json

## #13 marks-help-v2
Marks raise voiced accuracy and cut variance. 9 lines (3 demo, 6 sentences), 5 takes each, 505 words per variant, transcriber gemini-3.6-flash: words whose internal marks (final letter ignored) were voiced as sent: 486/505 (96.2%, per-take range 94-98%) with full marks vs 460/505 (91.1%, range 80-96%) with all marks stripped.



- retrieved 2026-10-01, confidence 0.85
- file:///<PROJ_ROOT>/PROJ-tests/work/batch2-2026-09-30/tashkeel-kb/json/run5.json

## #9 pairs-ceiling
Minimal pairs in a neutral frame (قَالَ الْمُدِيرُ X فِي الْمَكْتَبِ), 29 words x 2 takes: key word voiced as sent 41/58 (71%). Misses cluster on shadda: كَتَّبَ read as كَتَبَ 4/4, مُوَظِّفٌ as مُوَظَّفٌ 4/4, مُعَلَّمٌ as مُعَلِّمًا 4/4. The transcriber cannot separate a voice miss from its own miss, so 71% is a floor on faithfulness, not a rate.



- retrieved 2026-10-01, confidence 0.85
- file:///<PROJ_ROOT>/PROJ-tests/work/batch2-2026-09-30/tashkeel-kb/json/run2.json

## #16 reroll-gain
Re-rolling pays: from run5 (9 lines, first 3 takes each, full marks), mismatched words per line fall from 0.33 (a single take) to 0.11 (best of 3), and lines with zero mismatches rise from 6.0 of 9 to 8 of 9. Transcriber-measured; the 9 lines carry 505/5 = 101 words.



- retrieved 2026-10-01, confidence 0.85
- file:///<PROJ_ROOT>/PROJ-tests/work/batch2-2026-09-30/tashkeel-kb/json/run5.json

## #15 split-shadda
Expanding a shadda into letter+sukun+letter (كَتْتَبَ) is worse: 454/505 (89.9%) overall and 132/160 (82.5%) on shadda-bearing words, 5 takes each, against 486/505 (96.2%) and 148/160 (92.5%) for the shadda as authored.



- retrieved 2026-10-01, confidence 0.85
- file:///<PROJ_ROOT>/PROJ-tests/work/batch2-2026-09-30/tashkeel-kb/json/run5.json
- file:///<PROJ_ROOT>/PROJ-tests/work/batch2-2026-09-30/tashkeel-kb/json/run6.json

## #8 stoch
The same marked text gives different vowels on different calls. إِلِكْتْرُونِيًّا sent 3 times came back with kaf-sukun 2/3 (damma 1/3); sent bare it came back sukun 2/3, kasra 1/3; five respellings tried, none fixed it. Demo line 02, 3 takes: 9, 8, 1 mismatches (the word وَغَيْرُهُمْ was dropped in takes 1 and 2 per the transcriber).



- retrieved 2026-10-01, confidence 0.85
- file:///<PROJ_ROOT>/PROJ-tests/work/batch2-2026-09-30/tashkeel-kb/json/run4.json
- file:///<PROJ_ROOT>/PROJ-tests/work/batch2-2026-09-30/tashkeel-kb/json/retest-before.json

## #1 ucd-order
Combining class: fathatan 27, dammatan 28, kasratan 29, fatha 30, damma 31, kasra 32, shadda 33, sukun 34. NFC/NFD therefore sort the vowel BEFORE the shadda (U+0637 U+064E U+0651), the reverse of the usual typed/printed order (shadda then vowel).



- retrieved 2026-10-01, confidence 0.85
- https://www.unicode.org/Public/UCD/latest/ucd/extracted/DerivedCombiningClass.txt
- https://www.unicode.org/reports/tr15/

## #6 waqf-final
Kore reads the last word of a clause, and list items, in pausal form (case ending dropped, sukun) even when the full case ending is sent: counting the final letter, 181/204 words match vs 196/204 ignoring it, so the 15 extra misses are final-letter marks (e.g. مَجَّانِيَّةٌ, الْجُمْهُورِ, وَالْقَمَرُ in a list). This is correct MSA waqf, not a fault.



- retrieved 2026-10-01, confidence 0.85
- file:///<PROJ_ROOT>/PROJ-tests/work/batch2-2026-09-30/tashkeel-kb/json/run1.json
- file:///<PROJ_ROOT>/PROJ-tests/work/batch2-2026-09-30/tashkeel-kb/json/run2.json

## #7 waqf-nogain
Marking waqf yourself (sukun on clause-final words) or dropping all case endings did not improve voicing: internal-exact 53/68 (waqf) and 65/68 (no case endings) vs 66/68 (full marks) on 3 clips each, one take. No benefit; send full case endings.



- retrieved 2026-10-01, confidence 0.85
- file:///<PROJ_ROOT>/PROJ-tests/work/batch2-2026-09-30/tashkeel-kb/json/run1.json

## #12 wasl
Hamzat al-wasl: ا and ٱ gave the same voiced result (1 clip each). Connected speech applies sakin-sakin rules (عَنْ الْمَسْؤُولِيَّةِ voiced as عَنِ ٱلْ) which are correct, so a transcript difference there is not a miss.



- retrieved 2026-10-01, confidence 0.85
- file:///<PROJ_ROOT>/PROJ-tests/work/batch2-2026-09-30/tashkeel-kb/json/run1.json

