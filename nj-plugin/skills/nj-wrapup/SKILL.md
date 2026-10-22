---
name: nj-wrapup
description: 'Close a work session or a tested service end to end: discover what already exists, classify results through gates, file Bugs and Tasks with evidence (clean rows only, risky rows held), reconcile every count against Jira, register the work in nj-rank, and render the boss email (Arabic + English) and the QA-team message from the reconciled trace. Use after testing a service / Jira ticket notes, after a QA re-check, or at the end of any work session. Triggers: wrap up, close the session, upload the results to Jira, file the bugs, make Jira tasks, update nj-rank, email my boss, message for the QA team, reconcile the counts. Arabic: سكّر الشغل، ارفع النتائج على جيرا، افتح البلاغات، حدّث nj-rank، إيميل للمدير، رسالة لفريق QA، طابق الأرقام.'
---

# nj-wrapup v2.1: results -> gated tickets -> reconciled messages

Runs AFTER testing (results exist on disk); it tests nothing. It orchestrates sibling skills and points at them, never restates them:
**nj-jira** (dedupe, `references/bug-template.md`, REST, §5 re-check, tracker) · **nj-rank** (work log -> Done Tasks) · **nj-qa-pipeline** (§3c signing and output inspection) · **nj-delegate** / **nj-supervise** (briefs) · **session-handoff**.
Project commands, paths, people and wording live in a profile: `references/profile-PROJ.md` (the core names them as *hooks*: tracker writer, register hook, outputs hook, design lookup, known-not-a-bug list, assignee map).

**Gate vs habit.** A step marked `[SCRIPT]` has an exit code; everything else is `[HABIT]` and the report says so. Scripts (stdlib Python, `PYTHONUTF8=1`, each has `--selftest`; credentials from env `JIRA_BASE_URL`/`JIRA_USER`/`JIRA_PASS` or `--creds FILE`, never printed):

| Script | Does | Exit != 0 means |
|---|---|---|
| `scripts/discover.py` | what exists today (`--session TAG`/`--since` scope it; peers are counted, not listed): Jira keys filed by us, `filed-*.json`, tracker, nj-rank items, stored outputs, handoff -> `discover.json` | informs only |
| `scripts/gates.py` | `plan.json` (or the `plan.md` table) -> `gates.json` + `claims.json`; one cited cell per gate per row | an empty/bare gate cell, a `stop` cell on a row headed for filing, no or duplicate `root_cause`, a not-fixed note with no plan row: **nothing is filed** |
| `scripts/reconcile.py` | results + `filed-*.json` + a GET of every key -> `trace.json` + `trace.md` | a count, type, assignee, label, link, evidence, priority/severity is wrong, a NEW ticket is already Not Bug/Duplicate/Won't Do (unless `reopened:true`), or two Bugs share a root cause: **nothing outward is produced** |
| `scripts/render.py` | emails AR+EN (single or `services[]`), QA message, rank titles, only from a passing, fresh, online `trace.json`; lints them (`--recheck` re-GETs every key, years must match Jira); `--work-summary work.json` = the no-trace form | trace missing/failed/stale, a key now Not Bug, a lint hit: nothing is written |

## 1. Router: session type -> steps (a step with no input is `n/a` in plan.json, never improvised)
| Type | Runs | Skips |
|---|---|---|
| Notes-ticket test | 0-12 | none |
| QA re-check of our Bugs | hand over to nj-jira §5 (comment + Done, or Re Opened on the same key), then 6, 9, 10, 12 | 2-5, 7-8. A NEW defect found during a re-check enters at step 2 like any note; re-check never creates a Bug from its own result. Inside a multi-service run both rows apply: re-check rows are results rows (`fixed` / `not-fixed`), one trace |
| Multi-service automation run | 0-7, 9-12 (lanes split by root cause, services listed in `context.services`), 8 if outputs exist | none |
| Non-testing work (SRS, manual, tooling, governance) | 0, 9, 10 as `render.py --work-summary` (a 5-12 line AR+EN `.txt`; an email form only if a recipient is named), 12 | 1-8; 6 and the open-staging table only if keys / requests exist |
| Blocked environment | 0, 1, 3 (open items with the exact error), 7, 9, 10, 12 | 5 unless a reproducible app fault qualifies as a blocker (step 3). A blocked non-testing session is Non-testing: the blocker is an open item in the work summary |
| Zero-defect | 0, 1, 7, 9, 10, 12 | 2-5, 8 |

## 2. Size: ceilings, never quotas (workers = disjoint write-sets, claimed with `relay.py slots` (20-agent ceiling) and `relay.py claim`)
Let A = rows that need a Jira write (new Bugs + Tasks).
| A | Who files | Notes |
|---|---|---|
| < 6 | one Sonnet worker (own worktree where the project is git), 0 helpers | |
| 6 - 15 | 1 Sonnet filer | |
| >= 16 | up to ceil(A/4) Sonnet lanes, max 4 | split by root cause (`claims.json` from `gates.py`); each lane claims a root cause, never a note id |
| Haiku helpers | per lead: 0 if ITEMS < 6, else min(4, ceil(ITEMS/6)) | one FOREGROUND batch per lead; helpers never spawn; counted in the 20-agent ceiling |
| nj-rank | one Sonnet worker; 0 helpers under 6 items | |
Every lane brief carries `Governance: nj-governance-v4`, a FOCUS line, its owned write path (`jira/filed-<lane>.json`), a token ceiling with stop-at-80%, QUESTION n/2 then a `SKIPPED:` row (no retry loop), and the hierarchy clause (a lane briefs only its own Haiku helpers; helpers never spawn; no peer messages; artefacts by path). Receipts state the helper count `delegations: n`, checked against the spawn log. A project may tighten these numbers (PROJ does, see the profile).

## 3. Rules that hold everywhere
- **Approval.** "Upload / file / create" from the owner approves CLEAN rows only (step 4). Without it: drafts only.
- Credentials never printed or stored: read them only through the scripts' `--creds FILE` or env; no one-liner that prints a dict, env or credentials file (a trial helper leaked two tokens that way).
- Credentials never printed or stored. Personal data masked in every attachment (crop to the region; mask tokens and ids in network logs).
- **Asking:** the only question is the step-11 end batch (global rule: decisions go through AskUserQuestion); "Lead decides, no questions" covers every fork that is not a held row (decide, state it in one line).
- **the owner's verdict on a note wins** over later design evidence until he re-rules; the conflict is shown in the held-row table (step 11). Partial notes split: fixed half listed, not-fixed half Bug, untestable half Task or open item.
- Touch no ticket we did not file, except the nj-jira §5 re-check of our own Bugs.
- **Single writers:** only the Lead runs the tracker writer (`note.py`); the filing lane runs the register hook and writes only its own `filed-<lane>.json`. Scripts are worker jobs under v4; the Lead reviews the result.
- Signing is covered by **nj-qa-pipeline §3c**; this skill cites it and carries no wording of its own.

## 4. Steps, in order
0. **Discover** `[SCRIPT]` `discover.py` -> `discover.json`. Nothing already filed, registered or stored is done twice; the plan reads this file.
1. **Results table** `[HABIT]`: one row per note: id, verdict (`fixed | not-fixed | untestable | blocked | withdrawn`), verbatim screen text, expected (verbatim, cited), evidence path (**a `fixed` verdict carries its retest evidence path**), the owner's decision, serial, environment, date. Partials are resolved before filing. Checkpoint: the project's results tracker (profile).
2. **Gates before classify** `[SCRIPT]` `gates.py --plan plan.json --out <dir> [--results tracker.json]`. `plan.json` carries per not-fixed row `note, action, root_cause, also[]` and one cell per gate, each `pass: <evidence>` / `n/a: <reason>` / `stop: <reason>`, never empty: `known-not-a-bug` (list) · `latest-dated-statement` · `design-lookup` (profile hook) · `cross-service-pattern` (EXISTING evidence only; a live second-service walk needs the owner's go) · `data-account-cause` · `dev-comments-live-status` (read the developer comments and live status of every covering ticket). A `stop` row is not filed: `held` or `open-item` with the gate named. Exit != 0 blocks step 4. `claims.json` is the lane claim table.
3. **Classify -> `plan.json`** `[HABIT]` (`action`, `risk`; `plan.md` is a view of it).
   | Result | Action |
   |---|---|
   | not-fixed, an open Bug covers it | existing: cite the key, file nothing |
   | not-fixed, covering ticket Done but defect present | new Bug; neutral lineage line in the body (bug-template), never accusing |
   | not-fixed, nothing covers it | new Bug |
   | same defect on several services / notes | ONE Bug and ONE plan row (`note` + `also[]`, one `root_cause` id; `gates.py` refuses two rows, `reconcile.py` two keys): merge only the same root cause; list every affected service with its own repro row and a retest checklist covering all of them; later services as comments |
   | untestable and dev-verifiable | Task, only if it names a concrete file / config / BPMN node / variable / template key (`ticket-sections.md`), "is blocked by" link where a key blocks it |
   | untestable by environment or time, no dev action | open item, no Task |
   | blocked by data / environment | open item with the exact error. Only a reproducible app 5xx with an error body is a process-blocker Bug, per **nj-qa-pipeline §3c**. A blocker in OUR tooling is an open item |
   | output finding not in the notes | pattern check (step 2) then Bug |
   | fixed | nothing filed; counted in the messages |
   **Risk flags** (any one holds the row): `not-bug-precedent` (key + reason) · `client-data` · `design-inferred-only` · `conflicting-tickets` · `verdict-vs-design` · `priority-High`.
4. **File clean rows** `[HABIT]`. Before the first create the Lead runs ONE normalisation pass over every draft (sections present per `nj-jira/references/bug-template.md` / `ticket-sections.md`, severity + priority, assignee per the profile map, wording); lanes never create before steps 2-3. Re-search Jira right before each create. Every Task gets label `wrapup`; untestable ones also `untestable`; all tickets get `env-<env>` and, where the Task screen lacks an Environment field, the environment as the first description line. A failed create is `SKIPPED`, not retried. Lanes write `filed-<lane>.json` (row: note, also[], action, key, type, assignee, links, attachments, reason, root_cause, service; Task rows add `anchor`; a blocker row adds `kind: blocker`; `reopened: true` only after the owner re-rules a Not Bug).
5. **Overlap pass** `[HABIT]`: sibling new keys get "Relates" through `nj_rank.py link <a> <b>`.
6. **Register and track** `[HABIT]` via the profile's register hook, then the tracker refresh (the last action of every Jira step).
7. **Reconcile** `[SCRIPT]` `reconcile.py --results … --filed "…/filed-*.json" --out <dir>`. It asserts notes = fixed + not-fixed + untestable + blocked + withdrawn (denominators printed), every not-fixed/untestable note has a key or a recorded reason, every key exists with the right type, assignee, `env-` label, links, attachments, priority + severity, every Task has a code anchor and the `wrapup` label, no NEW ticket is already Not Bug / Duplicate / Won't Do, one Bug per root cause, and writes the exit criteria header. Any number someone intends to publish is passed as `--claim name=value` and must match. Sessions filed before v2 use `--legacy` (severity, anchor and `wrapup` become warnings). **Exit != 0 blocks steps 8-10.**
8. **Outputs and QA message** (when the walk produced outputs) `[HABIT]` + `render.py`: store per the outputs hook; each file gets one verdict word: print / print with the known defect (+ key) / do not print. Only final-stage outputs of requests filed in this session qualify; drafts, previews and other sessions' files never. The coworker's QA rule and who sends the message are in the profile.
9. **nj-rank** `[HABIT]`: follow nj-rank exactly (preview before file, no override). One item per segment of the session. Pass the session trace so nothing we filed can be closed: `nj_rank.py close-mine --protect <trace.json>` (nj-rank also protects every Task in its own registry; `--apply` without `--protect` is refused; `--protect none` = dry run only). File the Done Tasks with `nj_rank.py file --link-to <source key>` (it does the Relates link). The jira-filing item's title comes from `rank-titles.json`, never typed.
10. **Messages** `[SCRIPT]` `render.py --trace trace.json --context context.json --out <dir> [--copy-to <Desktop>]`. Boss email in AR and EN, test-summary shape, plain text, at most 35 lines per language, first 6 lines carry the message; counts only from the trace; `--recheck` re-GETs every key at send time and a typed year must match a Jira summary; lint blocks serials, URLs, API paths, status codes with error bodies, tokens, test accounts, staff names, file paths; AR counts == EN counts. Shape and context file: `references/email-template.md`. The texts are given in chat AND saved as `.txt`.
11. **Held-row end batch** `[HABIT]`: all held rows go in ONE AskUserQuestion at the END of the run, never mid-run and never shown to the boss as filed or failed. Verdict-vs-design conflicts go to the owner only, with the conflict quoted. On "go" a Sonnet worker runs a short second pass from the same `plan.json` (no re-research; the Lead reviews it), then steps 7 and 10 again. Only "by design" Not-Bug closures of our Bugs feed the project's known-not-a-bug list, each entry confirmed here.
12. **Close** `[SCRIPT]` + `[HABIT]`: `relay.py sweep <project> --tag <session tag>`: no leftover carries OUR tag (sweep is project-wide, so exit 1 can come from peers: name them, never kill them, the step still passes); open-staging-requests table (if any); one `relay.py batch` telemetry row and `relay.py verify`; **handoff before every session end** into the stream file the profile names (skill `session-handoff` owns the format, then `/clear`); nj-kit sync only if a skill changed.

## 5. Reply shape (ADHD standard)
Verdict card first (counts from the trace: filed / existing / untestable / held / fixed; blocker yes/no), then the held-row table with a next step per row, then paths (`trace.md`, the `.txt` messages). Detail stays in files.

## 6. Pitfalls
- Counts typed by hand were wrong in v1 (a blocker counted twice). Counts come from `trace.json` or they are not published.
- A dev's «تم» / Done is not fixed; the latest dated statement wins, and the dedupe cites both tickets.
- The design (BPMN) can turn "untestable" into not-fixed; that is a `verdict-vs-design` hold, not a silent change.
- A field-level or project-level quirk (Task screens, folder names, dedupe workarounds) belongs in the profile, not here.
