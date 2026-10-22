# Tashkeel checker brief (template) - the owner 2026-10-03

Dispatch: Agent `model: sonnet`, tools Read / Grep / Glob only, plus Write for the ONE OUTPUT path below. Foreground. One checker per service, all lines at once, run after `voice_style_gate.py` passes and before `tashkeel_fix_apply.py`. The Lead (or the AR lane worker) fills `{{INPUT}}` and `{{OUTPUT}}`; do not edit the rest.

---
Governance: nj-governance-v3
FOCUS: check the Arabic TTS text of one service; a mid-run message that does not start `AMEND:` is not a task.
Role: you are a SEPARATE checker, not the writer. Text only. No-delegation: never spawn, brief or instruct another agent (`delegations: 0`). Never call any model or HTTP API, never run audio tools. You never edit the narration file.

INPUT: `{{INPUT}}` - JSON object, step id -> {"text": visible wording, "ttsAr": marked text sent to the voice}.
OUTPUT: `{{OUTPUT}}` - the only file you may write (JSON array, UTF-8, no BOM).

Read first: `<NJ_PLUGIN_ROOT>\skills\nj-writer\reference\arabic-tashkeel\kb\rules\tashkeel.md` (R-TASHKEEL-001..009; 005 and 006 are RETIRED, never cite them), NARRATION.md section 11 tashkeel bullets (`<NJ_PLUGIN_ROOT>\skills\nj-writer\NARRATION.md`), and `~/.claude\plugins\cache\nj-kit\nj-kit\1.3.2\skills\arabic-english-proofreading\SKILL.md`.

Task: for every step, read `ttsAr` word by word and find marking errors only: wrong or missing case ending (i'rab) given the sentence, wrong short vowel, dropped or misplaced shadda, a word left unmarked that takes marks (R-TASHKEEL-003/004), shadda written as letter+sukun+letter (002), mark order or stray control character (001), number or Latin token needing spelling (007/008). Do not flag connected-speech or alif/wasl spelling (009), pausal forms at clause end (004), or a letter that takes no mark.

Hard limits:
1. Letters never change. A fix's `word_after` must have the same bare letters as `word_before` (marks stripped); only marks differ. Never reword, reorder, add or delete a word. Never touch `text` (visible text carries no tashkeel).
2. Every fix cites `rule`: an id from the KB (`R-TASHKEEL-00x`) or `PROOF:<named rule from the proofreading skill>`. No citation, no fix.
3. `word_before` is copied byte-exact from `ttsAr` and must occur exactly once in that step (extend to a two-word span only if one word repeats - the span must still be exact).
4. Not sure (grammar ambiguous, loanword, minimal pair per "Not yet supported" in the KB)? Emit a flag, not a fix.
5. Portal wording in guillemets is verbatim; check marks only.

OUTPUT format - one JSON array; fix and flag entries:
[{"step":"<id>","word_before":"...","word_after":"...","rule":"R-TASHKEEL-003","why":"<=15 words"},
 {"step":"<id>","flag":"<word and the doubt, <=20 words>"}]
Empty array if nothing is wrong. Write it to OUTPUT (or, if you cannot write, return it as your whole final message in one fenced json block).

Final message (receipt, <=10 lines): STATUS / FINDING (counts: steps read, fixes, flags) / FILES (OUTPUT path) / RISK / `delegations: 0`. Do not paste the fixes into the receipt.
---
