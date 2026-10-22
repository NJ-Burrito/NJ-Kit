# nj-wrapup trial 2 (dry run, no writes): multi-service automation run + QA re-check

Date 2026-10-16. Skill under test: `nj-plugin/skills/nj-wrapup/SKILL.md` + `references/email-template.md`, applied literally.
Writes: this folder only. Jira: GET only (22 issues read; credentials never printed).

## 1. Session chosen and why
**Chosen:** the "nine services" automation run of 2026-10-12, with its QA re-check.
Sources (under `Improvement Delivery\Automation Tests\reports\`): `full-9-2026-10-12\{report.html,email-ar.md,pdf}`, `recheck\2026-10-12-latest.{md,json}`, `last3-/outputs-/factcheck-2026-10-12\`, `jira-results.jsonl`, `filed-requests.csv`.
**Why:** it differs from trial 1 on every axis: 9 services (not 1), 31 tickets / 77 notes (not 27 notes of one ticket), two environments (QA + staging, a verdict per note on each), 4 of 9 services with no output, a systemic defect across services (PROJ-1234), a re-check pass that yields transitions instead of Bugs, and Bugs filed during testing, not after it.

Session numbers (`report.html`): 77 notes = 8 not-fixed, 29 fixed, 29 blocked, 7 untestable, 4 withdrawn/not-defect. Outputs opened: 5 of 9. Keys created that day: 16 (14 Bugs, plus PROJ-1234 and PROJ-1234 withdrawn as Not Bug the same day). Re-check (`recheck/…latest.json`): 0 broken, 1 fixed (PROJ-1234 N1), 9 unchanged, 0 new, 9 unreachable.

**Read-only Jira check made 2026-10-16:** of the 16 keys, **8 are now "Not Bug"** (5028, 5029, 5030, 5032, 5039, 5040, 5041, 5042). So 6 of the 14 reported Bugs (43%) turned Not Bug after the email went out. The 8 survivors: 5031 (Dev completed), 5033 (In QA), 5034 (To Do), 5035 (To Do), 5036 (Dev completed), 5037 (Dev completed), 5038 (In QA), 5043 (In QA).
Reasons on the tickets: 5028, dev points to PROJ-1234 point 3, which *adds* «جمعية» (the Bug premise was that 4438 removes it). 5029, dev points to PROJ-1234 point 3 (fixed text for «الإجراءات»). 5032, dev: "submit through a facility that has a practice licence" (test-data gap). 5030, 5040, 5042: no comment, reason unknown. [ASSUMED] 5040 («SIGN_HERE» in the signature block) collides with the 2026-10-12 rule "digital signature is never a Bug". [ASSUMED] 5042 (second output missing) is what `flowable/lookup.py --q outputs` (nj-jira §4a) is meant to catch.

## 2. What the skill tells me to do, step by step, on this session
| Step | Literal instruction | What happens here | Fit |
|---|---|---|---|
| 0 Hard rules | the owner's "upload/file" = approval. | The 2026-10-12 testing brief already said "File new ones (the owner approved)". Filing happened during testing; the skill assumes testing is finished before wrapup starts. | ambiguous |
| 0 | the owner's comments on a note are binding. | The binding rulings of this session were session-wide, not note comments: «التوقيع الرقمي» never a Bug; QA not required after 2026-10-12; payment gateway = office network. Not covered. | missing |
| 1 Inputs | One row per note from `work/<ticket>-<date>/tracker.json` + results.md. | No tracker.json. Results sit in `jira-results.jsonl` (last line per id wins), per-service `result.json/notes.md` in three folders, `history.json`. 31 tickets, 77 notes, two env columns. The verdict enum has no per-environment verdict, no "withdrawn/Not Bug", no "unreachable". | wrong |
| 1 | Partials resolved by the owner before filing. | Two output questions stayed open (letter number; exporter country) and were rightly not filed. No "open decisions" bucket; improvised. | ambiguous |
| 2 Classify | Table by result. | 8 not-fixed: 3 covered by open tickets (4673, 4669, 4667); 1 by a Done ticket (4666 → "new Bug «لم يُصلح رغم إغلاق»"), but that defect is QA-only and QA was dropped on 2026-10-12, so the row files an out-of-scope Bug. 29 blocked: no row. 7 untestable: Task each. Outputs: pattern-check one other service, then Bug. | wrong (blocked, env scope) |
| 3 Lanes | Disjoint lanes by screen/stage, 3–5 items each; Sonnet lead + Haiku helpers per lane, "delegations ≥ 1 required". | Natural lanes are 9 services. Only 5 have anything to file; 4 of them 1–2 items. 9 leads + 9 helper batches to file 8 survivor Bugs. | wasted |
| 3 | Every lead re-searches Jira before each create. | Siblings by service all see the 2027/2031 «وقت اكمال الطلب» year in their outputs and race. Re-search catches it only if the first lane has already created. The one-Bug-plus-comment rule lives in nj-jira §4a, not in nj-wrapup. | ambiguous |
| 3 | Bug template: Relates to source ticket and service Story; Environment + env label. | Fine for single defects. PROJ-1234 spans 5 services, 3 Stories, 2 envs. Actual filing: one Bug, 3 links, comment appended. No instruction for 1-to-many. | ambiguous |
| 3 | Untestable Task, six sections; developer verifies in code. | Of 7 untestable: PROJ-1234 describes an automation task (no product behaviour); medical-device N6 fails because the original email is not in the ticket (BA/the owner, not code); «الخدمة غير معكوسة» is a question for the owner. None has a code check for a developer. | wrong |
| 3 | Blocker Bug (High): env error with app cause. | Candidates: <staging-user> refused on QA; lab login refused; «معاينة المخرج» not opening on 103202600080 and 80202600064; no output section on the stop-service requests; payment gateway unreachable. PROJ.md: permission errors and payment are not defects. A literal read can file 4–5 High Bugs from environment noise. | wrong |
| 4 Register | `note.py --reply`, `jira:add --service` per Bug, `jira:track`. | `note.py` target (tracker.json) absent. `jira:add --service` takes one card; PROJ-1234 spans 5. jira:track fine. | ambiguous |
| 5 Outputs | Download each produced output PDF to `Delivery\QA Outputs\…`, numbered copy on Desktop, Arabic QA-team message. | 5 outputs opened, mostly from requests approved by other sessions (63202600021, 80202600061, 102202600054), several defective (SIGN_HERE, GM-signed). Sending these to QA "for printing" is the opposite of the point. 4 of 9 services produced no output. | ambiguous |
| 6 nj-rank | One item per segment, `service_ar` null. | With 9 services: either 9 × segments (breaks the dedupe note) or ~6 service-less items. The day is already registered under `NJ-Rank\PROJ\2026-10-12-lead` (8 items). No "already registered?" check, so it would double-register. | ambiguous |
| 7 Email | Arabic AND English, template with `<TICKET>`, `<service>`, `<env>`. | Template has one TICKET and one service. The real email (`email-ar.md`, 25 lines) regrouped by output defect and added «ما يلزم» (accounts, data, permissions), 8 of its 25 lines, the part the owner acts on. The template has no such block. No English version was made then; the skill requires one. | wrong (shape) |
| 8 Close | Sweep, open staging requests, table type → keys. | Good fit. The source of open requests is not named: `reports/filed-requests.csv` (77 rows) and the stuck list (85202600025–31 at GM, 80202600064 at secretary, 103202600080 at signature). | ok |
| Re-check | (none) | `recheck/` classes: fixed / broken / new / unchanged / unreachable. Skill: "fixed → nothing filed; listed in email". nj-jira §5: our Bug fixed → comment + Done; not fixed → Re Opened. Wrapup never mentions transitions. Today: 5031/5036/5037 Dev completed, 5033/5038/5043/4677 In QA, PROJ-1234 N1 fixed per re-check. | missing |

## 3. Where the skill does not fit
1. **One ticket / one service / one environment shape** in inputs, lanes, template, nj-rank segments and `jira:add --service`.
2. **Blocked-by-data is the biggest bucket (29 of 77, plus 9 "unreachable" in the re-check) and has no action.** The enum names `blocked`; §2 never routes it. It needs an "asks" list (accounts: جمعية, فني, منشأة مرخصة 200003060; data: lab numbers; access: view rights on 113202600005, 75202600018/19; network: office for payment), one block in the email and nj-rank, no ticket unless a code cause is shown.
3. **Systemic defect across services** (PROJ-1234, five services). The one-Bug rule is in nj-jira §4a only; the lane model of wrapup §3 bypasses it.
4. **Verdict classes incomplete:** per environment, withdrawn/Not Bug, superseded by a later ticket, unreachable, fixed on one env only.
5. **Environment scope:** QA dropped on 2026-10-12; no rule to drop QA-only failures.
6. **No re-check/transition path** for our Bugs.
7. **No outcome loop.** Half of the day's keys turned Not Bug; nothing feeds those rulings into `references/PROJ.md` "Known not-a-bug", which is dedupe step 0.
8. **Filing happens during testing in this pipeline;** wrapup has no "discover what is already filed today" step.
9. **Mandatory delegation per lane** is disproportionate.
10. **Outputs rule** assumes our own walk reached the end; here outputs come from others' approved requests and are defective evidence.

## 4. What a correct close-out would have been
1. **Discover:** keys created that day (tracker + JQL) = 16; `jira-results.jsonl` last-line-wins; nj-rank items already present. Lead only, no workers.
2. **Gates before any key:** PROJ.md known list (digital signature, outgoing letter number, licence block); `flowable/lookup.py --q outputs|routing`; latest dated statement across all source tickets (4164 vs 4438; 4061 pt 3); test-data/account cause (5032); env scope (staging only).
3. **Classify:** 8 Bug candidates stand (5031 systemic with comment; 5033; 5034–5037 as one service lane; 5038; 5043). 5028, 5029, 5030, 5032, 5040, 5042 not filed (or filed as a question to the dev); 5039/5041 not filed. 29 blocked → asks list, 0 tickets. 7 untestable → at most 1–2 notes to the ticket owner, 0 developer Tasks. 0 blocker Bugs.
4. **File:** Lead alone or one worker; 8 Bugs, not 16.
5. **Re-check pass** (nj-jira §5) on our In QA / Dev completed Bugs: Done or Re Opened.
6. **Outputs:** PDFs as evidence only; no Desktop numbered copies, no QA-team message.
7. **nj-rank:** read the existing `2026-10-12-lead` items; register only what is missing.
8. **Email:** one short message: verdict (no service closable), table by service, «ما يلزم» block, systemic block; Arabic + English.
9. **Close:** open staging requests from `filed-requests.csv`, one table type → keys.

## 5. What the skill would file wrongly (literal application)
| Item | Skill path | Why wrong |
|---|---|---|
| PROJ-1234 copies | §3 lanes by service, sibling race | Should be 1 Bug + comment; up to 5 copies. |
| PROJ-1234, 5029, 5030, 5032 | §2 "not-fixed, nothing covers it → Bug" | All four are Not Bug (dev cites other/later ticket points, or a test-data gap). "Latest dated statement wins" sits in Pitfalls, not in the classify step. |
| PROJ-1234 (SIGN_HERE) | §2 output finding | Signature placeholder; the digital-signature rule is not wired into §2. [ASSUMED reason] |
| PROJ-1234 | §2 output finding | No BPMN lookup in wrapup (only nj-jira §4a). Reason unknown (Not Bug, no comment). |
| PROJ-1234 / 5041 (letter number) | §2 "pattern-check one other service" | The known list (step 0) must run first; a one-service pattern check would not catch it. |
| New Bug «لم يُصلح رغم إغلاق PROJ-1234» | §2 row 2 | QA-only symptom; staging fixed; QA retired. |
| Up to 4–5 High blocker Bugs | §2 "process blocker" | Environment/permission cases that PROJ.md lists as not defects. |
| 7 developer Tasks "untestable" | §3 Task template | 4837 has no behaviour; N6 needs a missing email; «غير معكوسة» is a question. |
| 4 "untestable" in إعادة الكشف | §2 | They are blocked (need a filed request/office screens). Wrong label → wrong Tasks. |
| Desktop numbered output copies + QA message | §5 | Defective or other-session outputs are evidence only. |
| Double nj-rank items | §6 | The day is already registered. |

## 6. Fixes proposed (details per step in trial-2.json)
1. Add §1a "Discover what exists" (keys filed today, nj-rank items today, accepted inputs: tracker.json or jira-results.jsonl).
2. Add §2 **gates before the table:** known-not-a-bug list; latest dated statement across all source tickets; flowable lookup for routing/outputs/signature/payment; env scope; test-data cause. A candidate failing any gate is not a Bug.
3. Add a **blocked-by-data → asks list** row; split untestable into (a) code-verifiable → Task, (b) needs info → question to the owner/BA, (c) no product behaviour → drop.
4. **Systemic grouping by the Lead before lanes:** one owner key per pattern; `jira:add` accepts several services for one key.
5. Add the **re-check path** (reference nj-jira §5) and per-env verdicts.
6. **Proportional delegation:** lanes only if ≥ 2 independent services each have ≥ 3 candidates; else Lead alone.
7. **Multi-service email template:** verdict, table by service, «ما يلزم» block, systemic block; English only when requested.
8. **Outcome loop:** at the next session GET the filed keys; Not Bug → append reason to PROJ.md known list.
9. **Outputs** only for clean outputs of our own walk; otherwise evidence only.

Delegations: 0. The reading was a handful of file reads and one Jira GET; briefing Haiku would have cost more than it saved.
