---
name: nj-qa-pipeline
description: 'End-to-end QA pipeline that combines the Jira skills: Jira -> notes -> staging check -> acceptance report -> automation -> full route walks (one agent per service, extra agents per route share) -> Bug filing -> QA re-check -> tracker -> Docker + share + 7z. Holds the orchestration rules (background workers, AMEND, staging load, Lead decides). Triggers: run the QA pipeline, full QA round, check every service, jira to docker. Arabic: خط الجودة الكامل، جولة فحص كاملة، وكيل لكل خدمة، من Jira إلى Docker.'
---

# nj-qa-pipeline: Jira to Docker, end to end

Combines `nj-jira` (read/file/re-check/track), `nj-jira-to-automation` (notes -> checks) and `nj-automation-suite` (the folder, reports, Docker). Governance is NJ v4 (`nj-delegate` section 0): this file adds only the QA-specific orchestration. Brief skeleton: `nj-delegate/templates/worker-brief.md`; transport: `nj-agent-ops`.

## The line (each stage leaves a file the next reads; the owner's accept gates in bold)
| # | Stage | Skill | Checkpoint | Gate |
|---|---|---|---|---|
| 1 | harvest open Bugs per service | nj-jira §3 | `<RUN>/<KEY>.md` | only To Do / In Progress / In QA, this service only |
| 2 | notes N1..Nn | nj-jira §2 | `notes.md` | count; latest dated wins |
| 3 | staging check, each note once | nj-jira-to-automation | `latest-ticket.json` + evidence | every note has a verdict; customs on staging (since 2026-10-12: staging (was QA only)) |
| 4 | acceptance report (PDF) | nj-automation-suite | run-report PDF | `gates.ts` pass; **the owner accepts the report** |
| 5 | automation: one test per note | nj-jira-to-automation | `jira-checks.ts`, `*.jira.spec.ts` | tsc 0, `--list`, one non-filing run |
| 6 | full route walks | this file §3 | `filed-requests.csv`, `<card>-routes-K.md` | every route run once; no «لم يُشغَّل» left |
| 7 | file Bugs for new defects | nj-jira §4 | `filed.md`, tracker | dedupe done, read-back verified |
| 8 | QA re-check of our Bugs | nj-jira §5 | `svc/<card>.json` | comment + Done / Re Opened |
| 9 | tracker | nj-jira §6 | `reports/jira-tracker/*` | `npm run jira:track` ran |
| 10 | Docker + share + 7z | nj-automation-suite | tar, sha256, 7z | `--list` inside the image; no fonts, no credentials in the archive |

Stage 4 is the one hard stop: automation is built from the notes the owner accepted, not before. Stages 6-9 may overlap per service.

Lessons of each run, with the rule each one produced: `references/lessons-2026-10-12.md` (read it before a run; new lessons are appended there).

## 1b. Verdict rules (2026-10-12, lesson 2)
- A note's verdict is `fixed | not-fixed | blocked | dropped | no-system-change | cannot-test` (`cannot-test` = real technical inability, reason required).
- **Dropped / no-action notes are never "untestable" (the owner 2026-10-18).** A Jira note dropped in discussion or marked no-action keeps its place as a planned check. Label it, everywhere (tracker, page, report, Jira), with exactly one of: `DROPPED` (dropped in discussion) or `NO SYSTEM CHANGE` (internal/technical follow-up). The why goes in the evidence: ticket, comment id, author, date, verbatim quote. Still check the note on the system: requested behaviour not reflected -> Bug with evidence, and the Bug/report HEADER states «مكان النقاش وما قيل» (where the note was discussed and what was said). `DROPPED`: absent = "confirmed not implemented, current behaviour stays" (not a Bug); present unexpectedly = the finding. `NO SYSTEM CHANGE`: check the area the dev comment names, or source confirmation only if it names none (say so). `cannot test` is kept only for a real technical inability, always with its reason.
- Valid blocked reasons only: the step needs a filed request or a back-office desk not yet reached; a named test-data value or account is missing (name it); the environment is down (quote the error line).
- «No ready check», «cannot test: no suite spec» and «time left» are never reasons. Write the check and run it, or check by hand.
- Payment («الفوترة») reachable only from the office network: record the environment block with the exact error, not a verdict.

## 1. Orchestration rules (owner, 2026-10-11)
- **Lead = sole orchestrator**, woken by events (worker complete, blocker, decision), never by progress. No model polling: the runtime delivers the completion; a script waits (`Monitor` with an until-loop, never a sleep loop).
- **Background workers with completion triggers:** every Sonnet worker runs in the background (v4: its Haiku helpers run as one foreground batch inside it); its completion (receipt + report <= 25 lines on STATUS / FINDING / EVIDENCE / FILES-SYMBOLS / RISK / NEXT ACTION, detail to a file) wakes the Lead. A worker never ends its turn while anything of its own still runs. (Superseded 2026-10-16 (v4): the old exception that a builder may run foreground; Sonnet workers always background.)
- **AMEND for mid-run changes:** every brief carries a `FOCUS` line; a mid-run message that does not start `AMEND:` is not a task. To stop or change a worker: `SendMessage` `AMEND: ...`; the worker records where it stopped in its detail file. Stopped workers leave partial records: read them before re-dispatching (no double filing).
- **One agent per service** (disjoint write-set = the service folder + its record file). **Route shares are Haiku helpers under the service's Sonnet agent** when a service has many filing routes (v4; helper count by the ITEMS rule): helper K of N owns the filing tests whose 0-based sorted index i has `i % N == K`; K=0 alone runs the per-note Jira spec with `PROJ_RESUME_TICKET`, fixes TEST-class checks and writes `lib-defect-<n>.md`. Skip a route already done today (`filed-requests.csv`, the service's `-run.md`).
- **Hierarchy (v4):** a Sonnet worker briefs only its own Haiku helpers (one foreground batch; helpers never spawn); no peer messages; artefacts pass by path through the Sonnet worker or the Lead. Receipt states the helper count `delegations: n`. Lib/reporter/tools are owned by ONE worker at a time; service workers write `lib-defect-<n>.md` instead.
- **Models** (v4, `nj-delegate` section 0): workers are Sonnet 5.5 (note analysis, checks, filing runs, triage, Bug filing); Haiku 5.5 helpers take the mechanical bounded work (sync, report build + gates, non-filing runs, sweeps). Deterministic first; escalation is haiku -> sonnet, once; no per-stage model picking, no Opus tier. Budgets are ceilings: wall time + tool calls + 80% stop.
- **The Lead decides instead of asking the owner** for anything inside his standing rules (which route, which account, how to dedupe, retry-or-skip). Ask (AskUserQuestion, options) only for what is his: destructive or outward-facing acts not already authorised, or a fork where a wrong guess costs more than asking. Contradictions between his statements go to him as a table (point, each statement with date and verbatim line, reference).

## 2. Staging-load limits (many agents, one staging)
- **Sign-in lock:** `mkdir reports/.signin-lock` (retry every 10 s; remove only if older than 4 min; never remove a fresh one; `rmdir` right after the sign-in lands). Hold it only for the sign-in. Plus the suite's own 5 s queue while reCAPTCHA is on.
- **No clock holds (lesson 3):** never hold a worker until a clock time (an 11:40 hold idled three workers). Serialise sign-ins with the lock and 3-minute spacing only.
- **Concurrency:** start 3 workers x 3 services (services run one after another inside a worker); 9 agents for single-service Jira work; 15 for route shares (v4: all Sonnet workers and Haiku helpers count toward the 20-agent ceiling). Cut it down at the first wave of refusals.
- **503 / 502 / timeout on >= 3 consecutive steps:** record `STAGING`, stop that route, move on. If staging is down altogether, PAUSE the batch with a wait-until-200 loop (below), then resume; do not retry-loop the failing step.
- Wait-until-200 loop (the runtime waits, the model does not): in `Monitor`, `until [ "$(curl -s -o /dev/null -w '%{http_code}' <portal url>)" = 200 ]; do sleep 60; done; echo UP`. One wake when it prints UP.
- Real requests are a cost: at most ONE new request per service per round unless the route share says otherwise; print the real count before a filing run.
- Never press «التوقيع الرقمي»; at that desk press «معاينة المخرج», screenshot, stop. No reject/cancel/return unless it is an explicit reject test.

## 3. Full route walks
Per route, once, no retry: `npm run stage -- "<service>" "<test>" all --yes` (send -> payment -> every desk -> final approval). Data-blocked route = BLOCKED-BY-DATA with the exact message, try the other working account ONCE. Then the per-note Jira spec with `PROJ_RESUME_TICKET=<ticket>`. Triage every ❌ into TEST / PORTAL-KNOWN / PORTAL-NEW / LIB / STAGING; PORTAL-NEW -> Bug (dedupe, re-search right before create).

## 3b. Capture, findings, review, recheck (owner, 2026-10-12)
Every draft passes these stages between a filing run and Jira (suite: `tools/findings`, `tools/review`, `tools/recheck`, `lib/findings`):
1. **Capture text:** each screenshot writes masked page text `<name>.txt` beside the PNG (`lib/evidence.ts` `snap()`), saved locally for the scan only and never put on a ticket as evidence (uploader allowlist, the owner 2026-10-19: png/jpg/jpeg/mp4/webm/gif/md/pdf only). The scan reads the text, not the picture.
2. **Findings scan:** `npm run findings -- <folder> [--service X] [--build B] [--out file]` writes `findings.jsonl` (rules: raw-iso-date, wrong-year, empty-dash, raw-boolean, untranslated-ui, raw-enum). No model call. `npm run selftest:findings` must show 9 of 12 known drafts caught and 0 false positives. A clean scan is not a pass: the 3 misses need a UI or role check.
3. **Review page:** `npm run review:build -- "<result.json glob>"` writes `reports/review/<date>.html`; approve, reject or edit each draft; export `decisions.json`.
4. **File approved only:** `npm run review:read -- decisions.json --approved-keys` lists the keys to file. Pending and rejected drafts are never filed.
5. **Recheck per build:** `npm run recheck -- [--service X] [--build B]` writes `reports/recheck/<date>-<build>.md` (unchanged / fixed / broken / new / unreachable). Env-down is `unreachable`, never `fixed`.

Build and run id (`lib/build.ts`) sit on evidence, `run-meta.json` and `filed-requests.csv` (columns `build`, `run_id`), so every row names its build.

## 3c. Output inspection at the signing desk (2026-10-12, lessons 8–9)
- **Signing (single statement; other skills cite this section, never restate it): The signing step itself is never a defect or blocker; a reproducible signing failure (5xx with an error body, e.g. SIGN_HERE not found in PDF) is a process-blocker Bug, routed to the operations owner (owner, 2026-10-15).** Do not stop at the step itself; a failure Bug carries serial type, timestamp, endpoint, HTTP status and the one-line error body (masked), plus screenshots (main + Sanad popup), console errors and exact time.
- Inspect the output: «عرض المخرج» in the back-office request view (approved requests), and «معاينة المخرج» at the open signing desk. Screenshot it, check names, dates, numbers and Arabic wording, and file only what the output shows.
- Check the known not-a-bug list (`nj-jira/references/PROJ.md`) before every draft.

## 3d. Model-change watch (Phase 4, 2026-10-12)
After every Flowable export (`export.py`, `flowable_facts.py`, `diff.py`, then `watch.py`, in `PROJ-tests/reference/flowable`), `CHANGES-since-last.md` lists each service whose BPMN changed, its suite folder and the command `npm run recheck -- --service "<card>"`. Recheck those services on staging before the next batch. A model with no suite folder is listed; the service has to be added first. Nothing is filed from the change list alone: a `broken` or `new` row goes through §3b review, and the §4a Bug-or-design check runs first.

## 4. Closing the batch
1. `npm run jira:track`; `npm run sweep-chrome` (0 orphans of yours; peers' are named, not killed); `relay.py sweep` per project CLAUDE.md.
2. Rebuild report PDFs + `reports/index.html`; ADHD pass over each output.
3. Docker image + share + 7z (nj-automation-suite): no fonts, no credentials, no Jira attachments.
4. Update the service READMEs (verdict line first), write the handoff, report once: table of services (stages ✅/❌/⛔, new Bug keys, QA actions) with the report paths.
5. **Report and email (lessons 17–18):** the report step reads the current rule file, not a copy in the builder; a Sonnet worker greps the output for retired rules (e.g. «QA only») and the Lead decides on any hit before handing it over. Email text is pasted into Outlook: plain text, no markdown bold or tables; Arabic, signed «المالك»; a 3-line summary, one line per service, «ما يلزم» last.

## 5. Test oracles and self-healing (the owner 2026-10-18; canonical here, other skills point to it)
Sources, cite as `[id]`/`[KB#id]` like the files do: `QA-handover/self-healing-tests.md` (H/G rules, metrics), `QA Engineer/research/PROJ-e2e-baseline/oracle-integrity.md` (R rules). Read-only inputs.

**The one sentence.** Never change an expected value to match what the system does. If actual differs from expected the result is a **defect** (expected is right), a **question** (nobody knows which is right) or an **expectation fix with a cited source** (the rule changed); the last one needs a person.

**Oracle rules (R1-R8).**
- R1 An unasserted result is not a pass: an `observed` step reports `OBSERVED`, never `PASSED`.
- R2 Every expectation names its source (BPMN task id, catalog row, SRS section or Jira key).
- R3 An expectation is never edited in the same change that makes its test pass, without a person (reviewer label / linked business answer).
- R4 A pin is a question, not an answer: it carries date, question and expiry; expired pins go back to draft.
- R5 Derived is compared: when the test follows the live order, also compare with the reference and report any difference as a finding.
- R6 Skips are visible: the verdict line prints skipped; a skipped baseline check fails the baseline.
- R7 Prove the test can fail: one run against a known-wrong answer must turn each baseline check red.
- R8 The author is not the approver: whoever writes or fixes a test may not approve its expected values.

**Verdicts.** `PASSED` (asserted, green) | `FAILED` | `OBSERVED` (recorded, not asserted) | `SKIPPED` (with reason) | `HEALED` (a human-applied heal, green, separate from passed) | `HEAL-REJECTED` (same-element proof failed or noHeal step; the scenario fails or skips with the reason).

**Heal rules (H1-H7).**
- H1 A heal is a proposal, never a silent edit. H2 Targets: locators and waits only.
- H3 Locator order: role/label/test-id, then text, then structural; every proposal carries role, accessible name and visible text of the matched element.
- H4 Classify first (locator / flake / real bug / env); only locator failures are healed; timeouts, network and data go to the flake path.
- H5 Same-element proof: exactly 1 match whose role and accessible name (Arabic text compared exactly) equal the recorded original.
- H6 At most 1 heal attempt per step per run. H7 The filing project keeps `retries: 0`: no heal at run time; proposals come only from a failed run's trace/error, applied through review.

**Guards (G1-G9).**
- G1 Never heal an assertion, expected value, oracle value or the `observed` flag. G2 Never heal expected Arabic text, business outcomes or status values.
- G3 Never heal negative tests. G4 Human review for login, payment/fee, submission/Send, digital signature (the signature is `noHeal` and never filed as a Bug).
- G5 After a heal a reviewer compares the element with the trace screenshot; the original assertion passes unchanged.
- G6 Reject beats fake pass. G7 A step healed twice in a row is fixed in source and the heal closed. G8 Review sample: 100 % of critical-flow heals, at least 25 % (min 5) of the rest per week, 100 % for a service for 2 weeks after a false heal. G9 The heal log is the countermeasure for silent false repair.

**Metrics** (from the heal log, per run and per service; `heal.report` prints them; no published benchmark, our own baseline first):
| metric | definition |
|---|---|
| heal_attempts | locator-class proposals written |
| heals_accepted | proposals a human applied |
| false_heals_caught | applied heals later judged wrong (key quality number) |
| heal_rate | heal_attempts / steps executed, per service (high = fix the source, G7) |
| failure_split | per failed test: locator / flake / real-bug / env |
| time_to_repair | minutes from failure to merged fix |
| reject_rate | HEAL-REJECTED / attempts |

**Observe-only window: 2026-10-18 -> 2026-11-15 (4 weeks).** In both suites a reporter hook (`heal-reporter.ts` in PROJ-tests `tests/PROJ/_shared/`; `reporter/heal.ts` in Automation Tests) writes a `proposed` record to `heal-log.jsonl` (PROJ-tests `artifacts/`, Automation Tests `reports/`) on a locator-class failure and the test STILL FAILS. Reporters cannot change a result. No apply mode exists in code; `HEAL_MODE=observe` (default) or `off`. `noHeal` (rejected record, never proposed): login, Send, fee/payment, «التوقيع الرقمي», negative tests, assertion steps, tag `@noHeal` or annotation `noHeal`. Weekly: a human reviews proposals against the trace, applies accepted ones in source and appends `accepted`/`false-heal`. On 2026-11-15 read `heal.report`; whether any auto-apply is justified (non-critical, non-filing only) is the owner's decision. Until then the 46 unasserted scenarios (R1) are closed before any green is trusted.

## ADHD output (all stages)
`references/adhd-standard.md`: the single checklist every report, PDF, HTML page, terminal line and AGENT/AI note follows.

## References
- `references/adhd-standard.md`: the output standard
- `references/PROJ.md`: PROJ run of 2026-10-11 (numbers, accounts classes, what each brief was, lessons)
- Briefs of that day (templates for the worker prompts): `PROJ-tests/.agent-ops/briefs/jt-*-2026-10-11.md`

## Screenshots: viewport only (owner, 2026-10-18, global)

## Jira stage label (owner, 2026-10-19)
Every Bug/Task carries the fixed label `phase2-uat`; rule in `nj-jira/SKILL.md` § Jira stage label.

Evidence method (the owner 2026-10-18): follow `nj-jira/references/bug-template.md` § Evidence rules (viewport + red ring + minimal mask, no .txt/.json, named shots); Suite helper `shotOf(page, target, path)` (`tests/PROJ/_shared/shot.ts` in PROJ-tests, `lib/shot.ts` in Automation Tests) does the scroll + in-viewport assert. Tools `nj-jira/scripts/evidence-shot.ts`, `ring-pdf.py`.

## Ticket wording (owner, 2026-10-20)
Bug = five short blocks only (المشكلة / الخطوات / المتوقع / الفعلي / الدليل, each <= 3 lines), no `*Verdict:*` / `*Source:*` line, no [JIRA]/[ASSUMED] label (those stay in QA reports). Task = the owner's own work only, 2-3 labelled blocks, one line per Bug key, "Relates" links, no agent counts, no report attachments by default (canonical PROJ-1234; `nj-jira/SKILL.md` § Task wording). Layout only, no added review step.
