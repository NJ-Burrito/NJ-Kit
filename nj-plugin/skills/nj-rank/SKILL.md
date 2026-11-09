---
name: nj-rank
description: Register finished work, keep its evidence paths, and file it to Jira as Done Tasks assigned to the user; close the user's own open Tasks. Triggers: rank my work, log this task, log this work, file my work to Jira, close my open tasks, سجّل العمل, ارفع المهام إلى جيرا, أغلق مهامي المفتوحة, رتّب أعمالي.
---

# nj-rank

Turns finished work into Jira Tasks (Done, assigned to the user) with the evidence kept on disk.
Stdlib Python only. Script: `scripts/nj_rank.py`. Tests: `scripts/test_nj_rank.py` (offline, mock HTTP).

## The four steps

1. **Title per service or segment.** One item per (service, work type) (owner, 2026-10-19): 144 notes tested on one service = 1 Task; notes tested + SRS on the same service = 2 Tasks; never one Task per note. **Only the tracked project's work is tasked (owner, 2026-10-19):** tooling, skills and every other project get no Jira Task; `file` skips items of other projects with a message and never calls Jira for them. Title = work-type label + the Arabic card name or segment name, e.g. `SRS · <service name>`. A user manual is one item (AR + EN together).
2. **Description.** 3 to 6 plain sentences: what was produced, languages, formats, counts, where delivered. Arabic names verbatim.
3. **Dates.** `finished` = newest mtime of the item's evidence (or a better log timestamp); `started` = oldest stage-time or log start, else null. Record `time_source`. Unknown is null, never invented.
4. **Evidence folder and filing.** Evidence paths are kept, not copied. The item folder is `<root>\<project>\<session>\<YYYY-MM-DD_HHMM of finished>\<safe title>\`. Filing then creates the Task, attaches each file under the upload limit that is on the allowlist (Allowed evidence types are screenshots (.png .jpg .jpeg), videos (.mp4 .webm), .gif, .md and .pdf (official output letters), nothing else; .docx .txt .json .log are refused (owner, 2026-10-19); `check_attachable` in `nj_rank.py` refuses anything else, and `register` also drops non-allowed files from the item's evidence list (it prints each skipped file and the allowed list, and registers the rest); any that still reach filing stay local, are archived in `evidence.7z` and are listed as `local_only` in the item record; text that matters goes into a `.md`), transitions it to Done, reads it back, and only then archives the evidence to `evidence.7z` (7z ultra, tested).

## Commands

Run from any folder with `PYTHONUTF8=1 python <skill>\scripts\nj_rank.py <cmd>`. Root = `NJ_RANK_ROOT`, default `<NJ-Rank-root>`.

| Command | What it does |
|---|---|
| `register --project PROJ --session S --title T --description D --work-type srs --finished ISO --evidence <abs path> [...]` | One item. `--json <file or inline JSON>` also works. |
| `log ...` | Same as `register`; the Lead uses it when new work starts. |
| `import <file.jsonl> ...` | Bulk. Invalid lines are reported and skipped. |
| (automatic) | Every registry change rewrites `preview.html` and its Desktop copy `<NJ-Rank-root> preview.html`; while anything is pending the page reloads itself every 15 s, keeping search, filters, sort and scroll (the owner 2026-10-12: always current, unasked). |
| (tracker tab) | `<root>\trackers.json` = `[{name, tickets, latest, baseUrl}]` merges Jira Bug trackers into the same page as a «🐞 Jira Bugs» tab (`preview.html#bugs`), grouped by directorate → service, with status chips. This page replaces the old tracker HTML for the owner (the owner 2026-10-12); `npm run jira:track` refreshes it. |
| (metrics tab) | «📈 Metrics» (`preview.html#metrics`, the owner 2026-11-05, simplified the same day for ADHD/OCD and a reader not used to charts): (1) «📖 Your story» — 3–5 plain sentences, numbers bold, one icon each; (2) «🏁 How you compare» — three ranked lists (Bugs found · Real problems · Fixed so far), you highlighted, no axes; (3) «📈 Your trend» — two Flint charts, each with a one-line «💡 how to read it»; (4) «🔎 More detail» folded. Period buttons: 7 days / 4 weeks / 12 weeks. Code: `scripts/metrics_tab.js` (inlined) + `metrics_data`/`bug_outcome`/`load_team` in `nj_rank.py`; Flint + Vega load from jsdelivr (pinned) only when the tab opens. 🌓/☀/🌙 button switches the theme for the whole page. |
| `team_metrics.py` | Weekly QA-team pull: Bugs each member in `<root>/team.json` reported, **all Jira projects**, → `<root>/team-metrics.json` + `team-metrics-history/<date>.json`, then rebuilds the preview. Read-only on Jira. Bugs only, because the owner's Tasks are auto-filed by nj-rank and would not compare fairly. Schedule it weekly with your OS scheduler if you want the tab kept fresh. |
| (hide) | `<root>\preview-hide.json` = list of project names and/or item ids hidden from the preview (the owner 2026-11-05: «Machine rules» item 8023998ee53a). The registry row stays (KPI hard rule); only the page drops it. |
| `preview [--no-open]` | Writes `<root>\preview.md` + `preview.html` and **opens the HTML for the owner** (rule, the owner 2026-10-12: he always sees the HTML preview before anything is filed). `file` refuses unless `preview.html` is newer than `registry.jsonl`. Before a bulk `file`, run `file --only <n>` once as the positive sample. |
| `file [--only 1,4] [--dry-run] [--retry-failed] [--link-to KEY]` | Files pending items. Dry-run makes read-only calls only. `--link-to` Relates-links each newly filed Done Task to the source key (a failed link is reported, the Task stays filed; dry-run never links). |
| `sync` | Read-only: refreshes the Jira status/resolution of every registered Task into `<root>/task-status.json` (the preview reads it). Nothing is transitioned. |
| `close-mine [--apply] [--protect FILE_OR_KEYS]` | Open Tasks reported by or assigned to the user. **Never closes** a Task labelled `untestable` or `wrapup`, nor a key listed by `--protect` (a wrap-up `trace.json`, or a comma/space key list) or by env `NJ_RANK_PROTECT` (same forms). Dry-run writes `close-mine-preview.md` with a "Skipped" table (key + reason) and prints each skip. |
| `register ... --existing-task PROJ-N` (item field `existing_task`) | First-class: register work against a Task that ALREADY exists (e.g. the UAT service Task made before testing). `file` creates no second Task: it checks the key is a Task assigned to the API user, attaches (only if `attach_evidence`), moves to Done if not yet, reads back, archives `evidence.7z`. |
| `link A B [--type Relates]` | Links two issues through REST v2 `issueLink` (Relates by default). |
| `whoami` | Prints the API user's name (`/rest/api/2/myself`). |

Work types: `srs`, `user-manual`, `user-manual-remake`, `staff-manual`, `automation-tests`, `jira-filing`, `segment`.

**Evidence types:** uploadable = the allowlist above; `.html` / `.htm` (e.g. the UAT `preview.html`) is accepted at `register`, kept, archived in `evidence.7z` and listed `local_only`, never uploaded. The preview gate (`preview` before `file`) is unchanged. UAT notes flow: `nj-jira/references/uat-notes-standard.md` §6.

## Filing order (per item)

JQL dedupe (exact summary, Task, project) → create Task (assignee = API user) → attach files at or under the upload limit; larger files are listed in a comment by path → transition to Done → GET read-back (assignee, Done, attachment count) → 7z a, then 7z t → status `filed`. Any failure records the error, keeps every file, and moves on to the next item. A duplicate found by the JQL dedupe is recorded as `exists` and not touched.

## Not-a-bug rule (owner, 2026-10-22, permanent)
A Task or Bug whose Jira status OR resolution matches not a bug / won't fix / rejected / invalid / works as designed / by design / «ليس خطأ» / «ليست مشكلة» / «مرفوض» is rendered first, with a thick red halo, the chip «🚫 ليس Bug» and a block with the transition author (changelog), date and their latest comment (`NOT_A_BUG_RE`, `not_bug_of`, `nb_block` in `nj_rank.py`); a count chip sits at the top of the preview. Run `sync` (Tasks) / `npm run jira:track` (Bugs) to refresh.

## HARD RULE: records are permanent (owner, 2026-11-02)

Tasks, Bugs, tabs and statuses are his KPI record, even when Jira also holds them. "Clear", "lighten" or "save space" touches evidence files and recordings only, never `registry.jsonl` rows, `item.json`, `task-status.json`, `trackers.json` or the tracker's `tickets.json`. `save_registry` and the tracker's `writeRegistry` refuse to lose an entry. Never bypass them by writing the files directly.

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

## Task descriptions (owner, 2026-10-20; canonical = the final PROJ-5169, supersedes 2026-10-18)
The registered `description` IS the Jira body (`compose_description` adds nothing): the owner's own work only, 2-3 short labelled blocks (`h3. مراجعة وثيقة المتطلبات`, `h3. البلاغات`), one short bullet per Bug key, no agent test counts, no verdict/source lines (`create_task` refuses them). Every `--jira-key` becomes a "Relates" link on create. Evidence is NOT attached by default (item field `attach_evidence: true` opts in); it is still archived to `evidence.7z`. Layout in `nj-jira/SKILL.md` § Task wording.

## Jira stage label (owner, 2026-10-19)
Fixed label `phase2-uat` on every Bug/Task; rule in `nj-jira/SKILL.md` § Jira stage label; scripts read `STAGE_LABEL` in `nj_rank.py`.

Tasks: `register` needs no label flag; the Jira `labels` default to `STAGE_LABEL` on create (`--label` only overrides).

Evidence method (the owner 2026-10-18): follow `nj-jira/references/bug-template.md` § Evidence rules (viewport + red ring + minimal mask, no .txt/.json, named shots); Suite helper `shotOf(page, target, path)` (`tests/PROJ/_shared/shot.ts` in project-tests, `lib/shot.ts` in Automation Tests) does the scroll + in-viewport assert. Tools `nj-jira/scripts/evidence-shot.ts`, `ring-pdf.py`.
