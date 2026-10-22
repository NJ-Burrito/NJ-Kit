# tashkeel — how to send Arabic narration to Gemini 3.1 Flash TTS (Kore) so it voices every vowel

Entry ids refer to `kb/tashkeel.db` (`scripts/kb.py query --sector tashkeel --full`). Every Because is a verified entry.

### R-TASHKEEL-001 · Keep the marks in the order every tool emits (vowel, then shadda)
**Rule:** Send marks in NFC/NFD order (طَّ = U+0637 U+064E U+0651); do not re-order to shadda-first, it measured no better. Whatever you do, never leave a stray control character or a dropped vowel from a re-ordering helper: re-read the text after any mark rewrite.
**When:** building the Arabic text sent to TTS, or any step that normalizes text.
**Because:** #1, #14
**Strength:** advisory
**Decay:** volatile, recheck 2027-01-01
**Tags:** tashkeel, shadda, unicode, nfc, tts

### R-TASHKEEL-002 · Never expand a shadda into letter + sukun + letter
**Rule:** Write the geminate with a shadda, not as كَتْتَبَ-style doubling.
**When:** a geminate word is voiced wrong and doubling looks like a fix.
**Because:** #15
**Strength:** binding
**Decay:** volatile, recheck 2027-01-01
**Tags:** tashkeel, shadda, respelling

### R-TASHKEEL-003 · Keep full tashkeel in the TTS input
**Rule:** Send every Arabic word fully marked (case endings included); the marks measurably raise voiced accuracy.
**When:** any Arabic narration line sent to Kore.
**Because:** #13
**Strength:** binding
**Decay:** volatile, recheck 2027-01-01
**Tags:** tashkeel, tts, kore

### R-TASHKEEL-004 · Send full case endings; do not mark waqf yourself
**Rule:** Write the full i'rab ending on clause-final words; expect Kore to read clause ends in pausal form, which is correct, and never replace endings with sukun to force it.
**When:** the last word of a clause, a list item, or a sentence.
**Because:** #6, #7
**Strength:** binding
**Decay:** volatile, recheck 2027-01-01
**Tags:** tashkeel, waqf, case-endings

### R-TASHKEEL-005 · Verify by transcription and re-roll, never trust one take
**RETIRED 2026-10-03 (owner):** no model other than gemini-3.1-flash-tts-preview may be called; voice once, no verify. Kept as history only.
**Rule:** After voicing, transcribe the clip with gemini-3.6-flash, compare per word ignoring the final letter's mark, and re-voice up to 3 takes keeping the one with the fewest mismatches (`scripts/tashkeel_verify.py`).
**When:** delivering any Arabic narration clip.
**Because:** #8, #10, #16
**Strength:** retired
**Decay:** n/a
**Tags:** tashkeel, verify, reroll, stochastic

### R-TASHKEEL-006 · Do not verify with the lite transcriber
**RETIRED 2026-10-03 (owner):** no model other than gemini-3.1-flash-tts-preview may be called; voice once, no verify. Kept as history only.
**Rule:** Use google/gemini-3.6-flash as the transcriber; never gemini-3.5-flash-lite.
**When:** choosing the audio-to-text model for a tashkeel check.
**Because:** #10
**Strength:** retired
**Decay:** n/a
**Tags:** tashkeel, asr, verify

### R-TASHKEEL-007 · Numbers: spell out when case or gender matters
**Rule:** Digits are voiced acceptably but cannot carry marks; where the number's case or gender must be exact, write it in words with marks.
**When:** a number in narration.
**Because:** #11
**Strength:** advisory
**Decay:** volatile, recheck 2027-01-01
**Tags:** tashkeel, numbers

### R-TASHKEEL-008 · Latin tokens: spell them in Arabic letters
**Rule:** Write PDF as بِي دِي إِفْ in the TTS text so it can carry marks; the visible text keeps the Latin form.
**When:** an acronym or Latin word in Arabic narration.
**Because:** #11
**Strength:** advisory
**Decay:** volatile, recheck 2027-01-01
**Tags:** tashkeel, latin, acronym

### R-TASHKEEL-009 · Connected-speech differences are not misses
**Rule:** Do not flag a sakin-sakin repair (عَنْ ٱلْ voiced عَنِ ٱلْ) or ا/ٱ spelling as a tashkeel miss.
**When:** reading a transcript comparison.
**Because:** #12
**Strength:** advisory
**Decay:** evergreen
**Tags:** tashkeel, wasl, connected-speech

## Not yet supported

- Forcing a shadda'd minimal pair (مُعَلِّم / مُعَلَّم, كَتَّبَ / كَتَبَ): 71% of key words came back as sent; no tested respelling fixed it (entries #8, #9). Open: sentence context that disambiguates.
- Loanword internals such as إلكترونيا: the voice follows the marks about 2 of 3 takes; only re-rolling helps (#8).
- Whether Gemini documents any diacritics handling for the 3.1 preview model (entry #2 stays draft: one vendor page, describes 3.8).
