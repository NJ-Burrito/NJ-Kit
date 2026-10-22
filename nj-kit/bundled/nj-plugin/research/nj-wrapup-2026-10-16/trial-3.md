# nj-wrapup TRIAL 3 - non-testing session (dry run, 2026-10-16)

Skill under test: `nj-wrapup/SKILL.md` + `references/email-template.md`, calling `nj-rank`. Applied literally. No Jira or nj-rank writes. The only code run was the pure `nj_rank.normalise()` in memory, to validate the dry-run item.

## Session chosen and why
**`work/trigger-hierarchy-2026-10-14`** (governance/tooling). It is the purest non-testing case: no tester results, no Jira notes, no staging requests, zero defects. Evidence: `design.md` and `receipt.md` in the run folder, plus products outside it (nj-delegate SKILL.md s0.3a, runtime-map.md, both CLAUDE.md files, a memory file, the nj-kit manifest and zip export). It is also tiny (one segment, about 1 h), so it tests the "minimum viable close-out" question.

Rejected as primary: `srs-flowable-repoint-2026-10-12` (blocked-environment, zero defects; used below as the second probe), `setup-manual-2026-10-09` (research plus 5 versions, nothing to file), `nj-rank-backfill-2026-10-12` (it is nj-rank itself, circular).

## 1. What the skill makes me do, literally
| Step | Literal demand | Fits this session? |
|---|---|---|
| 0 Hard rules | "upload/file/create" = filing approval; mask PII; the owner's comments binding; single writers | Rules 1-3 vacuous. Rule 1 does not say whether the same words also approve the nj-rank filing, which has its own preview.html gate |
| 1 Inputs | results table, one row per note, verdict fixed/not-fixed/... from `work/<ticket>-<date>/tracker.json` | Empty set. No tracker, no verdicts |
| 2 Classify | test result to Jira action | Empty set. No row for "work done, nothing to file" |
| 3 Lanes | Sonnet lead per lane, "delegations >= 1 required" | 0 lanes. Read literally, even an empty lane list still names a lane for untestable Tasks |
| 4 Register/track | `note.py --reply`, `jira:add`, `jira:track` | Vacuous (no keys) |
| 5 Outputs | real PDFs to `Delivery\QA Outputs\...`, copy to Desktop, QA-team Arabic .txt | Vacuous |
| 6 nj-rank | one Sonnet lead + one Haiku helper per item | The only live step. Needs 1 item |
| 7 Boss email AR+EN | template is test-shaped (Bugs / untestable / fixed / blocker / outputs / re-test) | Does not fit; I must improvise another shape |
| 8 Close | `relay.py sweep`, list open staging requests, "one table: type -> keys" | Sweep applies; staging list empty; table = one nj-rank key |

Not mentioned anywhere in the skill: session handoff, nj-kit sync / zip export, `/clear`.

## 2. Irrelevant steps, and does the skill say how to skip
Steps 1-5 and most of 7-8 are irrelevant here. **The skill gives no skip rule.** The description promises "or at the end of any work session"; the body opens "Runs AFTER the testing is done (results exist on disk)... Built from the PROJ-1234 session". A reader must infer "empty set = skip" step by step. The Pitfalls section is all Jira-testing. There is no "session filed nothing" branch and no minimum path. Only the general nj-method proportionality principle covers it.

## 3. The right close-out for this session (derived)
1. **nj-rank, one item**: `work_type=segment` (there is no tooling/governance type; WORK_TYPES = srs, user-manual, user-manual-remake, staff-manual, automation-tests, jira-filing, segment). `service_ar` null. project PROJ, session `trigger-hierarchy-2026-10-14`, finished = newest evidence mtime `2026-10-14T12:02:46+03:00`, time_source mtime, started null. Evidence must be files: a folder path is rejected ("evidence missing on disk", verified). Dry-run `normalise()` passed; dedupe key `PROJ|<title>|segment`. Then preview.html, `file --only 1` as positive sample, `file`. Result: one Done Task assigned to the owner, the only Jira write.
2. No Bugs, no untestable Tasks, no blocker, no tracker rows, no QA-team message.
3. Email only if someone outside needs it, in a short "work done" shape (changed / why it matters / needs from you / open), both languages.
4. Handoff per CLAUDE.md "Session handoff" (skill silent).
5. nj-kit sync, `export.py --zip`, extract to `<NJ_KIT_ROOT>` (CLAUDE.md "When skills change"; skill silent). Receipt.md says this session already did it, so close-out only verifies.
6. `relay.py sweep <PROJ-tests> --tag <tag>`, expect exit 0.

## 4. Collisions
| With | Collision |
|---|---|
| nj-rank | (a) wrapup §6 "one Sonnet lead + one Haiku helper per item" vs nj-rank trigger-model "Haiku workers only; the Lead runs import/file". For one item the Lead runs one `register`; two agents are pure overhead. (b) wrapup §0 says explicit "upload/file" replaces the review-page wait; nj-rank `file` refuses unless preview.html is newer than the registry. §6 repeats "preview opened before filing", so nj-rank wins in practice, but §0 wording invites the opposite. (c) Session id and evidence form are not specified. (d) No non-service work type; `segment` is the only fit. |
| session-handoff / PROJ CLAUDE.md | CLAUDE.md names two streams (`handoffsrs.md`, `handoff-user-manuals.md`), but the PROJ root also holds handoff-automation-tests, -qa-automation, -qa-reports, -rawan-food. A governance session belongs to none; the global rule says one handoff.md per project. Wrapup never calls session-handoff, never orders it (it should come after nj-rank so it carries the key), and omits `/clear`. |
| PROJ delivery rules | `Delivery\QA Outputs\<directorate>\<card>\` is not one of the three trees in CLAUDE.md "Delivery layout" ({User Manual, Training Manual, SRS}); "copy to plain Desktop numbered" sits against "no spot-delivery, no zips, no batch folders". Not hit here (no outputs), but unreconciled. |
| nj-delegate | Wrapup §3 "delegations >= 1 required" vs "minimum-sufficient workers: zero, one or many". No carve-out for nothing-to-file sessions. |
| CLAUDE.md "Lead decides, no questions" | wrapup §1 "partials resolved by the owner's decision": not triggered here. |
| Output style | Caveman/concise vs the ADHD email: fine, the email is a deliverable. |

## 5. Second probe: blocked-environment, zero-defect (`srs-flowable-repoint-2026-10-12`)
Deliverable: repointed SRS builds. Blocker: 11 services in `still-unmapped.md` (converter refuses on roles with no Arabic desk name). Literal §2: "process blocker (signing fails, env error with app cause) -> new Bug, priority High". This blocker is a gap in OUR converter and data, not an application defect, so a High Bug would be the wrong class and would land in the staff's Jira. The classifier has no "our-side blocker" row. Right result: nj-rank items (type `srs`), the unmapped table in the email under "open", no Bug. **This is the higher-risk gap.**

## 6. Minimum viable close-out for a tiny session (proposed)
1. The Lead runs one `nj_rank.py register`, then preview, then `file --only 1`. No lanes, no helpers.
2. A 5-line AR+EN summary only if someone outside the session needs it.
3. Handoff for the stream if work continues.
4. nj-kit sync only if skills changed.
5. `relay.py sweep`.
About 3 commands, 0 agents.

## 7. Fixes proposed (ordered)
1. Add a **Scope gate** at the top: session kind `tested` (full flow) / `built` (steps 6, short 7, 8) / `blocked` (blocker-class rule). Rule: "skip any step whose input set is empty; say so in one line".
2. Classifier row: blocker in OUR tooling or data (converter gap, missing label) -> not a Bug; open item in the email.
3. Step 6: "3 items or fewer: the Lead registers directly; helpers above that". State evidence = files not folders; session id = run folder name; `segment` for tooling work with `service_ar` null.
4. Step 7: add a built-session email shape; make the email optional when no recipient is named.
5. Add a handoff step after nj-rank (call session-handoff, name the stream file, `/clear`) and an nj-kit sync check when skills changed.
6. Reconcile `Delivery\QA Outputs` with CLAUDE.md Delivery layout and cite the owner's approval date.

Counts (trial-3.json): 15 findings: ok 0, ambiguous 5, wrong 2, missing 6, wasted 2.
