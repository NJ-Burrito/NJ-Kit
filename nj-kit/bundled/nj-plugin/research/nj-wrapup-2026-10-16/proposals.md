# nj-wrapup v2 — candidate changes (Lead synthesis of research.md, devil.md, trial-1/2/3.md)

Vote each: APPROVE / AMEND (text) / REJECT (reason). A change ships with ≥4/5 APPROVE|AMEND-compatible and no devil kill.

## A. Shape (dynamic)
P1 **Step 0 "Discover"**: before anything, list what already exists for this session — filed keys (tracker tickets.json, today's JQL by reporter), nj-rank items today, outputs already stored, handoff file — so nothing is filed/registered twice. (trial-2, trial-3)
P2 **Session-type router** at the top: notes-ticket test · QA re-check of our Bugs · multi-service automation run · non-testing work (SRS/manual/tooling/governance) · blocked-environment · zero-defect. Each type lists which steps run and which are skipped. (trial-2, trial-3, research C)
P3 **Size rule replaces "delegations ≥ 1 required"**: rows needing a Jira write A: A<6 → Lead files, 0 workers; 6–15 → 1 Sonnet filer (+Haiku helpers only if evidence prep > ~10 files); ≥16 → ceil(A/4) lanes, max 4. nj-rank: ≤3 items → Lead runs it directly; more → 1 Haiku worker. (research, devil 4, trial-1 3, trial-3)
P4 **Generic core + project profile**: move PROJ specifics (note.py, jira:add/jira:track, QA Outputs path, coworker QA rule, Story choice, assignees) into `references/profile-PROJ.md`; core names them as "project hooks". (devil 4)

## B. Gates (correctness)
P5 **Pre-classify gates** per not-fixed row: known not-a-bug list (nj-jira references/<project>.md) → latest dated statement → design lookup (PROJ: flowable lookup.py) → cross-service pattern check; a row failing any → not filed, reason recorded. (trial-2: all 8 later Not-Bugs would have been filed)
P6 **Risk rows held**: explicit "upload" approves only CLEAN rows; RISKY rows (Not-Bug precedent, client-data dependency, design-inferred only, conflicting tickets, the owner-verdict vs design conflict) go to ONE AskUserQuestion batch before filing. (devil 1, trial-1 1)
P7 **Precedence rule**: the owner's verdict on a note wins over later design evidence unless he re-rules; the conflict is shown in the risky-row question. Partial notes split: the fixed half listed, the not-fixed half filed, the untestable half → Task. (trial-1 1)
P8 **Systemic defects = one Bug** grouped by the Lead BEFORE lanes (same defect across services/notes → one Bug + per-service list); lanes split by root cause / workflow node, with a claim table. (devil 3, trial-2)
P9 **Reconcile gate (script)**: join results + filed-*.json → trace.md: notes = fixed + not-fixed + untestable + blocked; every key exists via GET; counts used by email/QA message/nj-rank titles come only from trace.md. (devil 2, research 3, trial-1 2)
P10 **Read-back by the Lead**: after lanes, Lead GETs every new key (type, assignee, labels, links, attachments) — not only lane self-reports.

## C. Routes (coverage)
P11 **Blocked-by-data / environment rows**: not Bugs; listed as open items with the exact error; only a reproducible app 5xx with error body = process-blocker Bug. Blocker in OUR tooling = open item, never a client Bug. (trial-2, trial-3 2)
P12 **Signing wording** (the owner 2026-10-15): the signing step itself is never a defect; a reproducible signing failure (5xx + error body) is a process-blocker Bug. Same text in nj-qa-pipeline §3c + lessons. (research 2)
P13 **Untestable route split**: dev-verifiable (code/config/template) → Task to dev; untestable only by environment/time with no dev action → open item in the report, no Task. Tasks blocked by a key get an "is blocked by" link. (trial-2, research 5)
P14 **Re-check route**: our Bugs In QA/Resolved → nj-jira §5 (verify → comment + Done | Re Opened); regression note per R-DEFECTS-004. (trial-2, research 5)
P15 **Not-Bug feedback**: any of our Bugs closed Not Bug since last wrap-up → add the behaviour to the project's known-not-a-bug list (with key + date). (trial-2)
P16 **nj-rank close-mine guard**: never run `close-mine --apply` after a wrap-up that created Tasks; or exclude label `untestable` / keys filed this session. Rank Tasks link Relates via REST (nj-rank has no link code). (research 1)

## D. Content (KB rules)
P17 **Bug fields per R-DEFECTS-002/006**: severity AND priority set explicitly (rule table: blocker High; screen-label Low/Medium; missing branch Medium/High); "found in" (env, build/date) and "introduced" if known. (research 5)
P18 **Neutral wording** (R-DEFECTS-003): replace «لم يُصلح رغم إغلاق <key>» with «ما زال يظهر — مرتبط بـ <key> (Done بتاريخ …)», in the body, not the title. (research 5, trial-1 2)
P19 **Email = test-summary shape** (R-MANAGEMENT-008/009 + nj-qa-pipeline lesson 18): 3-line summary first, counts from trace.md, blocker, new/existing/untestable, fixed, open staging items, residual risk, exit statement ("ready / not ready for <next step> because …"), «ما يلزم» last; AR+EN plain text in chat; no internal paths, tokens or raw error bodies beyond one line. (devil 5, research 5, trial-1)
P20 **Close step**: handoff file per project CLAUDE.md, nj-kit sync if skills changed, `relay.py sweep --tag`, open staging requests table. (trial-3 3, devil)

## E. Removals
P21 Remove "delegations ≥ 1 required" (superseded by P3) and the hard-coded counts in the header line.
P22 Remove the §0 override of nj-rank's preview gate — nj-rank's own order stays (preview before file).
