# Boss email and QA message (rendered by `scripts/render.py`)

Nothing here is typed by hand. `render.py` fills these shapes from `trace.json` (all counts, keys, verdicts) and `context.json` (free text). It refuses on a missing, failed, offline or stale trace, and lints the result.

## Email shape (Arabic and English, same content, plain text, at most 35 lines per language)
Subject: `<ticket> test results — <service> — <new total> new tickets (<n> blocker)`, and the Arabic equivalent.

| Line | Content | Source |
|---|---|---|
| 1 | Verdict: READY / NOT READY to move to the next step | trace |
| 2 | `Of <N> notes: <a> fixed · <b> not fixed · <c> untestable · <d> blocked` | trace counts, denominator N |
| 3 | Blocker: `<KEY> — <one plain line>`, or none (no endpoint, status code, error body, serial) | trace + context |
| 4 | New tickets: `<bugs> Bugs + <blocker> blocker + <tasks> Tasks = <total>` · `<n>` already existing | trace |
| 5 | Not covered by testing: `<untestable + blocked>` of `<N>` | trace |
| 6 | Exit criteria: `<met>` of `<M>` met (+ the unmet ones) | trace header |
| then | New Bugs (key — note: one line each) · Already reported (not duplicated) · Tasks for the developer · Fixed (note numbers) · Residual risk | trace + context |
| then | What is needed, at most 5 lines `who: what — date`; a date only if the owner gave one, else «الموعد: لم يُحدَّد — أحتاج تحديده» / "Date: not set — needs to be set" | context |
| last | `Status as of HH:MM on <env>` (the time the keys were re-checked), sign-off «المالك» / "the owner" | trace |

Style: ADHD standard (verdict first, red first, one line per ticket, no paragraph over 2 lines). English keeps the Arabic screen labels in «…».
The blocker is never counted twice; held rows never appear as filed or failed (they show only as a count under residual risk).

## Lint (hard failures)
URL or API path · file path or file name · request serial (9+ digits) · HTTP 4xx/5xx number, raw error body or ALL_CAPS_CODE · token-looking string · test account (test account, passwords) · staff names (taken from the trace assignees) · the words «Not Bug risk», "conflict", "inferred" · a key not in the trace · AR numbers != EN numbers · more than 35 lines · the first 6 lines missing verdict, counts, blocker or exit criteria. Run it alone on any text: `render.py --lint FILE --deny word,word`.

## QA-team message (Arabic, `.txt`)
Header «جاهز للطباعة» only if at least one file is «اطبع». Then one line per file: what it is, one verdict word: «اطبع» / «اطبع مع العلم بالخلل: <KEY>» / «لا تطبع». Only final-stage outputs of requests filed in this session may be printed; drafts, previews and anything from another session or a defective signed request are «لا تطبع». Last block «ما المطلوب منكم الآن». No file names, serials or test accounts.

## context.json (written by the Lead from the results; full schema in the `render.py` docstring)
`ticket, service_ar, service_en, env, date, lines{KEY:{ar,en}}, blocker{ar,en}, risk{ar,en}, needs[{ar,en,date}], outputs[{ar,verdict,stage,filed_this_session,key}], rank_items[{work_type,title}], deny[]`. Multi-service run: add `services[{id,ar,en}]` and give each filed row `service: id`; the subject joins the names and a «By service» block is rendered from the trace. `render.py --recheck` re-GETs every key at send time and refuses a key now Not Bug; a typed year must be the session year or appear in a cited ticket summary.

## Non-testing session (`render.py --work-summary work.json`)
No trace, no Jira counts: `title{ar,en}, date, done[], outputs[], open[], needs[], recipient, rank_items[]` -> `work-summary-{ar,en}.txt` (title, done, outputs, open, needs; 12 lines at most; counts are list lengths) and `rank-titles.json`. Subject and sign-off only when `recipient` is named. Same lint, AR numbers == EN numbers; a `jira-filing` rank item is refused (it needs a trace).

## Reply in chat
Verdict card (counts from the trace) -> held-row table -> paths. The two email texts are pasted in code blocks, one per language, because the owner forwards them as they are; the same texts are saved as `.txt` on the Desktop.
