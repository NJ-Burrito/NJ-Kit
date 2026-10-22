---
name: nj-rank
description: 'Register finished work, keep its evidence paths, and file it to Jira as Done Tasks assigned to the user; close the user''s own open Tasks. Triggers: rank my work, log this task, log this work, file my work to Jira, close my open tasks, سجّل العمل, ارفع المهام إلى جيرا, أغلق مهامي المفتوحة, رتّب أعمالي.'
---

# nj-rank

Turns finished work into Jira Tasks (Done, assigned to the user) with the evidence kept on disk.
Stdlib Python only. Script: `scripts/nj_rank.py`. Tests: `scripts/test_nj_rank.py` (offline, mock HTTP).

## The four steps

1. **Title per service or segment.** One item per (service, work type) (the owner, 2026-10-19): 144 notes tested on one service = 1 Task; notes tested + SRS on the same service = 2 Tasks; never one Task per note. **Only PROJ work is tasked (the owner, 2026-10-19):** nj-kit, skills, ENSERA, MOA, QA-Wrap, alaa and every other project get no Jira Task; `file` skips non-PROJ items with a message and never calls Jira for them. Title = work-type label + the Arabic card name or segment name, e.g. `SRS · تسجيل منتج غذائي`. A user manual is one item (AR + EN together).
2. **Description.** 3 to 6 plain sentences: what was produced, languages, formats, counts, where delivered. Arabic names verbatim.
3. **Dates.** `finished` = newest mtime of the item's evidence (or a better log timestamp); `started` = oldest stage-time or log start, else null. Record `time_source`. Unknown is null, never invented.
4. **Evidence folder and filing.** Evidence paths are kept, not copied. The item folder is `<root>\<project>\<session>\<YYYY-MM-DD_HHMM of finished>\<safe title>\`. Filing then creates the Task, attaches each file under the upload limit that is on the allowlist (Allowed evidence types are screenshots (.png .jpg .jpeg), videos (.mp4 .webm), .gif, .md and .pdf (official output letters), nothing else; .docx .txt .json .log are refused (the owner, 2026-10-19); `check_attachable` in `nj_rank.py` refuses anything else, and `register` also drops non-allowed files from the item's evidence list (it prints each skipped file and the allowed list, and registers the rest); any that still reach filing stay local, are archived in `evidence.7z` and are listed as `local_only` in the item record; text that matters goes into a `.md`), transitions it to Done, reads it back, and only then archives the evidence to `evidence.7z` (7z ultra, tested).

## Commands

Run from any folder with `PYTHONUTF8=1 python <skill>\scripts\nj_rank.py <cmd>`. Root = `NJ_RANK_ROOT`, default `<NJ_RANK_ROOT>`.

| Command | What it does |
|---|---|
| `register --project PROJ --session S --title T --description D --work-type srs --finished ISO --evidence <abs path> [...]` | One item. `--json <file or inline JSON>` also works. |
| `log ...` | Same as `register`; the Lead uses it when new work starts. |
| `import <file.jsonl> ...` | Bulk. Invalid lines are reported and skipped. |
| (automatic) | Every registry change rewrites `preview.html` and its Desktop copy `<NJ_RANK_ROOT> preview.html`; while anything is pending the page reloads itself every 15 s, keeping search, filters, sort and scroll (the owner 2026-10-12: always current, unasked). |
| (tracker tab) | `<root>\trackers.json` = `[{name, tickets, latest, baseUrl}]` merges Jira Bug trackers into the same page as a «🐞 Jira Bugs» tab (`preview.html#bugs`), grouped by directorate → service, with status chips. This page replaces the old tracker HTML for the owner (the owner 2026-10-12); `npm run jira:track` refreshes it. |
| `preview [--no-open]` | Writes `<root>\preview.md` + `preview.html` and **opens the HTML for the owner** (rule, the owner 2026-10-12: he always sees the HTML preview before anything is filed). `file` refuses unless `preview.html` is newer than `registry.jsonl`. Before a bulk `file`, run `file --only <n>` once as the positive sample. |
| `file [--only 1,4] [--dry-run] [--retry-failed] [--link-to KEY]` | Files pending items. Dry-run makes read-only calls only. `--link-to` Relates-links each newly filed Done Task to the source key (a failed link is reported, the Task stays filed; dry-run never links). |
| `close-mine [--apply] [--protect FILE_OR_KEYS]` | Open Tasks reported by or assigned to the user. **Never closes** a Task labelled `untestable` or `wrapup`, nor a key listed by `--protect` (a wrap-up `trace.json`, or a comma/space key list) or by env `NJ_RANK_PROTECT` (same forms). Dry-run writes `close-mine-preview.md` with a "Skipped" table (key + reason) and prints each skip. |
| `link A B [--type Relates]` | Links two issues through REST v2 `issueLink` (Relates by default). |
| `whoami` | Prints the API user's name (`/rest/api/2/myself`). |

Work types: `srs`, `user-manual`, `user-manual-remake`, `staff-manual`, `automation-tests`, `jira-filing`, `segment`.

## Filing order (per item)

JQL dedupe (exact summary, Task, project) → create Task (assignee = API user) → attach files at or under the upload limit; larger files are listed in a comment by path → transition to Done → GET read-back (assignee, Done, attachment count) → 7z a, then 7z t → status `filed`. Any failure records the error, keeps every file, and moves on to the next item. A duplicate found by the JQL dedupe is recorded as `exists` and not touched.

## Authorisation

- Create Tasks assigned to the user only.
- Transition only Tasks the user reported or is assigned to. Never a Bug. `close-mine` filters on `issuetype = Task` in JQL and again in code.
- `close-mine` skips wrap-up Tasks (label `untestable`/`wrapup`) and protected keys: they stay open for their owner. The only write `link` makes is an issue link.
- No comments or transitions on anyone else's issue. The only comment this skill writes is the oversize-evidence list on an issue it just created.

## Credentials

Never in this skill, never printed, never written to a file. Order: `JIRA_BASE_URL` + `JIRA_USER` + `JIRA_PASS` env → `NJ_RANK_SECRETS` file → `~/.claude/secrets/jira.json`. Every error message is masked before output.

## Limits

- Long paths (over 260 characters) work: every filesystem call on evidence or root paths goes through `longpath()` (`\\?\` prefix).
- Deletion, if any, goes to the Recycle Bin and only for files nj-rank staged inside the root. Evidence originals outside the root are never touched.
- Arabic is kept in paths (illegal Windows characters stripped, title trimmed to 80 characters).

## Pitfalls (2026-10-12 lessons 13–15)

- **Jira text search** rejects Lucene operators (`[ ] ( ) : ·` …): strip them from the phrase, then match the summary exactly. Rule and recipe: `nj-jira/references/rest-recipes.md` (Pitfalls).
- **Segment dedupe with `service_ar` null:** the registry key falls back to the title (`project|title|work_type`), so two segments with different titles are two items and the same title is a `duplicate`. Always give each segment a distinct, stable title; never register a segment without one.
- **7-Zip refuses duplicate basenames** (two `README.md` in one archive): the call uses `-spf2`.
- **Unit tests never open a browser or preview:** set `NJ_RANK_NO_OPEN`. Portable suites never hold machine paths; use the env vars `NJ_RANK_PREVIEW` and `NJ_RANK_SCRIPT` (the selftest catches a hard-coded path).

See `references/trigger-model.md` for who runs this and when.

## Task descriptions (the owner, 2026-10-20; canonical = the final PROJ-2169, supersedes 2026-10-18)
The registered `description` IS the Jira body (`compose_description` adds nothing): the owner's own work only, 2-3 short labelled blocks (`h3. مراجعة وثيقة المتطلبات`, `h3. البلاغات`), one short bullet per Bug key, no agent test counts, no verdict/source lines (`create_task` refuses them). Every `--jira-key` becomes a "Relates" link on create. Evidence is NOT attached by default (item field `attach_evidence: true` opts in); it is still archived to `evidence.7z`. Layout in `nj-jira/SKILL.md` § Task wording.

## Jira stage label (the owner, 2026-10-19)
Fixed label `phase2-uat` on every Bug/Task; rule in `nj-jira/SKILL.md` § Jira stage label; scripts read `STAGE_LABEL` in `nj_rank.py`.

Tasks: `register` needs no label flag; the Jira `labels` default to `STAGE_LABEL` on create (`--label` only overrides).

Evidence method (the owner 2026-10-18): follow `nj-jira/references/bug-template.md` § Evidence rules (viewport + red ring + minimal mask, no .txt/.json, named shots); Suite helper `shotOf(page, target, path)` (`tests/PROJ/_shared/shot.ts` in PROJ-tests, `lib/shot.ts` in Automation Tests) does the scroll + in-viewport assert. Tools `nj-jira/scripts/evidence-shot.ts`, `ring-pdf.py`.
