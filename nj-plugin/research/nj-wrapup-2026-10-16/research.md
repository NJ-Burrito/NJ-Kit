# nj-wrapup: research and analysis (2026-10-16)

Read-only study. Nothing in the skills was edited. Grades: [V] read in a file and cited, [A] inference that can be falsified, [U] not established.
Sources read: nj-wrapup SKILL.md + email-template.md; QA Engineer KB (`kb/rules/defects.md`, `design.md`, `management.md`, `automation.md` R-013; `qa-workflow.md` 3.6-3.8, 6, 8; `mentor-path.md` 7; `jira.md`); siblings nj-jira (SKILL, bug-template, PROJ.md), nj-rank (SKILL, trigger-model, `nj_rank.py`), nj-qa-pipeline (SKILL, lessons-2026-10-12), nj-delegate 0.0/0.3a/0.6/0.16, nj-method line 92; the 2026-10-15 run (`work/jira-3997-2026-10-15/jira/filed-L1..L4.md/json`, `tracker.json`, six nj-rank `item.json`, the QA-team message). Web: 3 searches (standard).

## Facts from the 2026-10-15 run (the friction evidence)
- [V] Results: 27 notes = 11 not-fixed + 10 fixed + 6 untestable (`tracker.json`). Filed: 9 Bugs (5087-5091, 5093-5096) + 1 blocker Bug (5092, High) + 6 Tasks (5097-5102); 3 notes already covered (4369, 4370, 4564); output finding "C" became Bug 5088.
- [V] The SKILL header says "10 Bugs + 6 Tasks + 1 blocker". The filed keys give 9 Bugs + 1 blocker = 10 including the blocker. The tally in the skill's own header is off by one; the nj-rank item title repeats "10 Bugs + 6 Tasks". Counts were typed by hand.
- [V] The SKILL mandates "delegations >= 1 required" per lane. L1, L2, L4 reported `delegations: 0`; L3's file does not report the field. The mandate was not followed and nothing checked it.
- [V] Lanes did not run `note.py`, `jira:add`, `jira:track` (Lead-only, step 4). The Lead's queue after four lane reports was therefore serial by design.
- [V] Evidence is scattered across `jira/ev`, `ev2`, `ev3`, `ev-l4`; `ev` and `ev3` both hold B1-B7 (same blocker evidence copied).
- [V] L4: five of six Tasks carry B7-error-summary / the signed-letter page as evidence for "could not test because signing fails" (PROJ-1234), yet the links created are Relates PROJ-1234 + PROJ-1234 only.
- [V] L2 N12: a sibling Bug on another service (PROJ-1234) is Not Bug with no comment; the lane flagged the risk but the skill has no step for it.
- [V] nj-rank: 6 items registered (PROJ-1234..5108), all `service_ar = None`, work types `segment` x5 + `jira-filing`; the tracker.html item spans 16:27 -> 23:55.

## (A) Gaps against the QA KB rules
| Rule | What nj-wrapup lacks | Proposed change |
|---|---|---|
| R-DEFECTS-001 reproducible report (id, title, author, date, test object + environment, context, expected/actual, references) | Fields are listed in section 3 but build/version tag and test object are omitted; the Task template has no build line | Point to `bug-template.md` (it has "رقم الإصدار") and add the build line to the Task template; delete the duplicated field list |
| R-DEFECTS-002 severity and priority as two fields; never everything critical | Only the blocker gets "priority High". Nothing says what priority/severity the other 9 Bugs get, nor who decides. KB `jira.md` 143: Jira has no standard severity field | Fixed mapping: Priority proposed by impact class (blocker of a whole route = High; wrong content on a legal output = Medium; wording/label = Low); severity as a first description line «الأثر: ...»; write "priority is a proposal, the product owner decides" (web: product owner sets priority; QA proposes severity) |
| R-DEFECTS-003 constructive tone | Summary pattern «لم يُصلح رغم إغلاق <key>» reads as blaming the closer | Use «ما زال قائماً بعد إغلاق <key>»; the description states what the screen shows, never "the developer did not" |
| R-DEFECTS-004 confirm the fix, then regression | "fixed -> nothing filed" with no regression note; no route for OUR Bugs that are In QA (that is nj-jira section 5: comment + Done/Re Opened) | Classify row "our Bug, In QA/Resolved -> nj-jira section 5"; the email's FIXED block states how many neighbours were sampled for regression, or "regression not run" |
| R-DEFECTS-005 short workflow; next state has a different owner | The untestable Task has no exit: who closes it, on what evidence, what QA does next | Task lifecycle line in the template: developer verifies in code -> comment -> QA retests (item 6 of the Task) -> QA closes |
| R-DEFECTS-006 phase introduced/found | Not recorded. "Closed yet present" is the only escape signal and it is only a title | Label `escaped-<oldkey>` on those Bugs; the email counts new / already-known / escaped separately |
| R-DEFECTS-007 let the tool attach evidence | Covered by nj-jira; but evidence staging is per lane and duplicated (ev, ev3) | Stage masked evidence ONCE as `evidence/<note>/` before the lanes (a script, not a worker); lanes only attach |
| R-DEFECTS-008 protect vulnerability/sensitive results | Masking is covered (section 0). Missing: a finding that exposes a secret/PII itself | One line: such a finding goes to the owner first, attachments held back |
| R-DESIGN-010 traceability basis -> condition -> result -> defect | `tracker.json` + `filed-L*.json` exist but nothing joins them; email counts are typed by hand (see the 10 vs 11 tally) | Generate `jira/trace.md` (note -> verdict -> action -> key -> evidence) by script from the two files; the email and QA message read counts from it |
| R-AUTOMATION-013 classify failure causes; environment first | Classify table has no cause class and no `blocked` row; payment/env-outage rules live in nj-qa-pipeline 1b | Add the `blocked` row (valid reasons only, point to nj-qa-pipeline 1b) and "cause class TEST / PORTAL-KNOWN / PORTAL-NEW / LIB / STAGING first; only PORTAL-NEW can become a Bug" |
| R-MANAGEMENT-008 report more than the pass rate | Email has counts, blocker, tickets, next steps; no residual risk, coverage statement or deviation from plan | A 3-line block «الخطر المتبقي»: what was verified by design-check only, what is unreached, what depends on 5092 |
| R-MANAGEMENT-009 exit criteria / DoD; qa-workflow 8 "say openly if you stop on time" | The skill has no definition of "wrap-up done" | A DoD gate (item 10): every note has verdict + key; read-back OK; tracker ran; rank items `filed`; email counts == trace; sweep exit 0; handoff written |
| qa-workflow 3.8 / 29119-3 completion report (summary, deviations, evaluation vs exit criteria, blockers, measures, residual risk, deliverables, reusable assets, lessons) | No lessons step, no "deviations" | One line per heading in the email footer; lessons appended to `nj-qa-pipeline/references/lessons-<date>.md` (3 lines, the Lead) |
| qa-workflow 6 (Rejected -> Open) | Risk of our Bug being closed Not Bug (L2 N12 / PROJ-1234) lives only in a lane report | If a sibling Bug on another service is Not Bug, put the design/BPMN cite in our description up front |
| R-MANAGEMENT-007 metrics as feedback | Email opens with "N Bugs filed", which can read as a quota | Lead with verdict counts of the service (fixed / not fixed / untestable), not tickets created |

## (B) Overlaps and contradictions with sibling skills
| Where | Problem | Fix |
|---|---|---|
| wrapup 2 blocker row vs nj-qa-pipeline 3c, lessons-2026-10-12 #8, memory "digital-signature-not-bug" | **Contradiction.** The siblings say «التوقيع الرقمي» is never a Bug or blocker; wrapup files a High Bug when signing fails (PROJ-1234, SIGN_HERE not found). The later, specific act is wrapup, but the sibling text was never amended | DECISION for the owner (one table row). Proposed wording in both skills: "the signing step itself is never a defect; a reproducible 5xx with an error body at that step is a process-blocker Bug (request, status, body). Inspect «معاينة المخرج» regardless." |
| wrapup 0 (the owner's "file" replaces the review page) vs nj-jira 4a/4b ("no review-page approval, no filing") | Unflagged exception; nj-jira never mentions it | Put the exception once in nj-jira 4b ("or the owner's explicit file request in a wrap-up, nj-wrapup 0"); wrapup keeps one line |
| wrapup 0 (credentials, touch no ticket we did not file, single writer) | Restates nj-jira 0 | Delete, one pointer; keep only wrapup-specific lines (the owner's comments binding; a lane writes only its own `filed-<lane>.json`) |
| wrapup 3 Bug paragraph | Near copy of `bug-template.md` + nj-jira 4 (Environment field/label, estimate, assignee, Relates, read-back) | Delete; "Bug: nj-jira 4 + bug-template" |
| wrapup 3 untestable Task template (6 sections) | nj-jira has no Task template, so the only copy lives in a close-out skill | Move to `nj-jira/references/task-template.md`; wrapup points |
| wrapup 4 (`jira:add`, `jira:track`) | Restates nj-jira 4 end and 6 | One pointer: "Lead runs nj-jira 4 register + 6 tracker" |
| wrapup 2 classify vs nj-jira 4 (dedupe 0-4), 5, nj-qa-pipeline 3 (cause classes) and 4a (pattern check, `lookup.py` BPMN check) | wrapup omits dedupe step 0 (known-not-a-bug list) and the `lookup.py` design check (mentions "design check" only in the Task) | Table keeps only what is wrapup's own (closed-but-present, blocker, output finding, fixed); the rest "by nj-jira 4 order" |
| wrapup 1 verdicts (`fixed, not-fixed, partial, untestable, blocked`) vs nj-jira 2 (`fixed, not-fixed, blocked, untestable`) | `partial` exists in one only; no classify row for `blocked` | Keep `partial` as a pre-filing state ("resolve before filing"), add a `blocked` row |
| wrapup 3 lanes ("delegations >= 1 required", Sonnet lead + Haiku helpers per lane) vs nj-delegate 0.0, 0.3a, 0.6 | 0.0: zero workers is the most common right answer; 0.6: count from disjoint write-sets. Wrapup fixes a shape and forces a helper; 3 of 4 lanes ignored it. Also no brief clauses (governance line, FOCUS, OWNED_PATHS, `relay.py claim`, `batch`) | Replace with the size rule (C) and "brief = `nj-delegate/templates/worker-brief.md`"; delete the mandate |
| wrapup 6 ("one Sonnet lead + one Haiku helper per item") vs nj-rank trigger-model ("Haiku only; Lead calls `log`/`import`/`file`") and CLAUDE.md (Haiku for Jira sync) | Tier contradiction; a Sonnet per rank item is the costliest way to run a script | "Lead (or one Haiku) registers via `nj_rank.py import`; evidence = file mtimes" |
| wrapup 6 asks «Relates» to the source ticket on rank Tasks | `nj_rank.py` has no issue-link or label code (grep `issuelink|relates|labels`: 0 hits) [V]; the instruction cannot be met | Drop it from wrapup, or add `links` support to nj-rank (item 1); never leave an unimplementable instruction |
| wrapup pitfall "register segments with `service_ar` null" vs `nj_rank.py` `dedupe_key` (line 248: `project|service_ar or title|work_type`) | Workaround for a tool defect, documented in the wrong skill; costs the service dimension (all six items `service_ar=None`) | Fix the key to always include the title; then delete the pitfall |
| nj-rank `close_mine` (line 720: Tasks with reporter or assignee = currentUser, not Done) vs wrapup 3 untestable Tasks | **Hazard.** The 6 untestable Tasks are reported by the owner's account and are open, so `close-mine --apply` would move them to Done unverified [A: not run; JQL has no label/assignee exclusion] | Exclude `labels = untestable` and foreign assignees in JQL and code; test in `test_nj_rank.py` |
| wrapup 7 + email-template (AR + EN, box dividers, emoji, per-ticket lines) vs nj-qa-pipeline 4.5 and lesson #18 (Outlook plain text, Arabic, signed «نادر», 3-line summary, one line per service, «ما يلزم» last) | Two email specs; they differ in language, length and closing label | Keep AR + EN (the later request), adopt the 3-line summary on top and one closing label; nj-qa-pipeline 4.5 points to wrapup's template |
| wrapup 8 Close vs CLAUDE.md "Session handoff" / session-handoff skill | wrapup never writes the handoff | Add "write handoff via session-handoff" (pointer) as the last step |
| wrapup 5 QA-team message and 7 email | Same letter findings typed twice | Both generated from `trace.md` + one outputs table |
| nj-method line 92 | Consistent with wrapup's description | none |

## (C) Dynamic behaviour: session type and size
Detect the type from the results table by script (count per verdict; whether any request was filed). The Lead confirms in one line; ask the owner only if two types tie.

| Session type | Signal | Run | Skip | Email shape |
|---|---|---|---|---|
| 1. Testing a ticket's notes (the 10-15 case) | notes with verdicts, some not-fixed/untestable | all: classify, file, register, outputs, rank, email | none | full (verdict, blocker, new, existing, untestable, fixed, outputs, next, residual risk) |
| 2. QA re-check of our Bugs | rows are our Bugs In QA | nj-jira 5 (comment + Done/Re Opened), tracker, one rank item "QA re-check" | new Bug/Task filing; outputs to QA unless the re-check produced one | table key -> Done / Re Opened / blocked-by-data; regression sample count (R-DEFECTS-004) |
| 3. Automation run | `jira-checks` results, findings.jsonl | cause-class triage first (R-AUTOMATION-013); only PORTAL-NEW -> Bug via the review page; systemic = ONE Bug | the owner-phrase approval (the review page is the gate) | cause table (TEST/LIB/STAGING/PORTAL-NEW), Bugs, reruns needed |
| 4. Non-testing (SRS, manuals, tools) | no verdict table | rank items + delivery table + handoff | classify, filing, QA outputs | "delivery" variant: what shipped (Arabic service names), where, what is open |
| 5. Blocked environment | most rows `blocked` with an env error | ONE blocker Bug if the cause is the app, else an environment note; rank item for work done; handoff `next step` = rerun list | untestable Tasks for notes merely unreached (invalid reason, nj-qa-pipeline 1b); outputs | blocker first, then "not verified: N notes because <exact error>" |
| 6. Zero-defect | all `fixed` | no filing; tracker; one rank item; confirmations list (+ regression sample) | lanes, classify, Tasks, outputs | 5 lines: "all N fixed", evidence path, note that the owner may close the source ticket (his call, never ours) |

Mixed sessions = union of the rows that apply; rank items stay per segment.

**Size rule (replaces the lane paragraph).** A = rows needing a Jira write (not-fixed with no open Bug + untestable + blocker + output findings).
| A | Workers | Models | Notes |
|---|---|---|---|
| 0 | 0 | Lead only | zero-defect path |
| 1-5 | 0: the Lead files them (one context holds it; nj-delegate 0.0) | Opus Lead | dedupe + read-back still run |
| 6-15 | 1 filer (one write-set `filed.json`) | Sonnet; evidence masking by script | optional 1 Haiku to review crops |
| 16-40+ | lanes = ceil(A/4), max 4 (Jira rate, one JQL re-search per create) + one Task lane; each lane owns `filed-<lane>.json` + its evidence subfolder (`relay.py claim`) | Sonnet per lane; Haiku only for bounded batches (mask review, rank register) | split by screen so sibling duplicates cluster; the Lead checks that no two lanes hold the same defect |

Helpers are optional, never mandated; the receipt reports `delegations: n` as a fact. Rank registration is one `import` (script), never a worker per item. The email is filled deterministically from `trace.md`, then the Lead (client-facing) edits one line. On a 429 or rate limit, drop to the next smaller row; do not retry-loop.

## (D) Top 10 improvements, ranked, with the cheapest proof
| # | Change | Why (rule / evidence) | Cheapest proof it works |
|---|---|---|---|
| 1 | nj-rank: exclude untestable/foreign-assignee Tasks in `close-mine`; `dedupe_key` always includes the title; implement or drop «Relates» on rank Tasks | Hazard and lost service dimension (B); unimplementable instruction | Dry-run `close-mine` now: expect PROJ-1234..5102 listed. After the fix: absent. Add 2 asserts to `test_nj_rank.py`; register two same-service segments with `service_ar` set: 2 items, not `exists` |
| 2 | `wrapup_trace.py`: tracker.json + filed-L*.json -> `trace.md` + counts + plan (type, A, lanes) | R-DESIGN-010; the hand-typed tally is off by one; one source for email, QA message, rank titles | Run on the 2026-10-15 data: prints 27 = 11+10+6, 9 Bugs + 1 blocker + 3 existing + 6 Tasks; diff against the SKILL header shows the error |
| 3 | Resolve the signing-blocker contradiction (ask the owner once, as a table row); amend wrapup and nj-qa-pipeline 3c together | Latest dated statement wins needs one canonical text | `grep -n "التوقيع الرقمي" nj-*/SKILL.md` shows one consistent rule |
| 4 | Priority/severity mapping + constructive titles | R-DEFECTS-002/003 | GET the 10 filed issues, read the priority column (likely uniform [U]); after the change it follows the mapping |
| 5 | Size/type router; delete "delegations >= 1 required" | nj-delegate 0.0/0.6; 3 of 4 lanes ignored it | Replay 10-15 through the rule: A = 17 -> 4 lanes + Task lane with optional helpers; receipts' `delegations` values stop contradicting the skill |
| 6 | De-duplicate the SKILL (delete restated rules; move Task template and Environment pitfall to nj-jira; point to bug-template); stage evidence once | Section B; scattered `ev*` folders | `wc -l` before/after; grep shows each rule once; the `ev`/`ev3` duplicate bytes are gone |
| 7 | Completion block in the email: residual risk, deviations (unreached/untested), exit statement, build/env, lessons line | R-MANAGEMENT-008/009; qa-workflow 3.8; 29119-3 outline | Fill the 10-15 email with it: every heading has a line or "none" |
| 8 | Email format reconcile: 3-line summary first, «ما يلزم» last, AR + EN, plain text, length cap | Lesson #18 vs email-template | `grep -c` for `**` and table pipes = 0 on the generated text; line count vs the current template |
| 9 | Untestable Task: "is blocked by" link to the blocker Bug when reason 3 is a blocker; closing owner/exit line | R-DEFECTS-005; web: prefer "blocks" over "relates" for a real dependency | GET PROJ-1234..5102 `issuelinks` (Relates only today); after one example the link shows |
| 10 | Wrap-up DoD gate script + handoff pointer + lessons append | R-MANAGEMENT-009; session-handoff; CLAUDE.md | Run on the 10-15 folder: lists failing items (expected: count mismatch, handoff, lessons) and exits non-zero |

## Web notes (3 searches; secondary sources, graded [A])
- ISO/IEC/IEEE 29119-3 completion report outline: summary of testing, deviations from plan, completion evaluation, blockers, measures, residual risks, deliverables, reusable assets, lessons learned (store.standards.org.au listing; table of contents only, not normative text).
- Severity = impact (tester proposes), priority = business urgency (product owner decides); do not inflate severity (techtarget, browserstack, excella; secondary).
- Untestable-requirement handling in Jira: nothing authoritative found. Only that "blocks" is advisory and preferable to "relates" for a real dependency (Atlassian community, ones.com). The untestable-Task design rests on the house pattern, not on a standard.

## Not established
- Actual priority values of the 10 filed Bugs [U] (not queried).
- Whether the owner accepted PROJ-1234 as a blocker against the "never a blocker" rule (inferred from the filing).
- Whether L3 ran helpers (its file is silent on `delegations`).
