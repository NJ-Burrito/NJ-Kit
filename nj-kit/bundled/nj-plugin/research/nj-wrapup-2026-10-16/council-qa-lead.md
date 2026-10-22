# Council vote: QA lead / test manager POV (ISTQB CTAL-TM), nj-wrapup v2

Authority: QA Engineer KB (kb/rules/defects.md, design.md R-DESIGN-010, management.md; knowledge/06-practice/qa-workflow.md 3.6-3.8, 6, 8).
Totals: APPROVE 10 · AMEND 12 · REJECT 0.

| P# | Vote | Reason (rule id) | Amended text |
|---|---|---|---|
| P1 | APPROVE | Discovering what exists first prevents duplicate defects and keeps one trace per result (R-DESIGN-010, R-DEFECTS-005). | |
| P2 | AMEND | Router is fine, but a skipped step must be written as "N/A: <reason>" in trace.md, not silently absent, or completion cannot be audited (qa-workflow 3.8, R-MANAGEMENT-009). Unknown type: ask once. | "Each type lists steps that run; every other step is recorded `N/A: <reason>` in trace.md. No type matched: AskUserQuestion." |
| P3 | AMEND | Thresholds are ceilings, not targets (R-MANAGEMENT-007). Whoever files must not be the only one who verifies: P10 read-back by the Lead is mandatory at every size. | "A<6 etc. are ceilings; receipt states worker count and why. Read-back (P10) runs at every size." |
| P4 | AMEND | Splitting is good, but the quality invariants (severity+priority, traceability, reconcile, exit statement, confirm+regress) are core, not profile; only tool names move (R-DEFECTS-002, R-DESIGN-010). | "Profile holds tool/path/assignee hooks only. Gates P5, P9, P10, P17, P19 stay in the core." |
| P5 | APPROVE | Classify by cause before logging defects; mass false defects destroy developer trust (qa-workflow 9, R-AUTOMATION-013, R-DEFECTS-001). A row rejected by a gate is still a recorded result. | |
| P6 | APPROVE | Triage decision on doubtful items belongs to the accountable owner; one batched question is cheap (R-DEFECTS-005, qa-workflow 3.6). Held rows must appear in trace.md as `held`. | |
| P7 | AMEND | Owner verdict can decide filing, but conflicting evidence must stay on record, never be dropped (R-DEFECTS-003, R-DESIGN-010). | "the owner's verdict decides whether to file. The conflicting design evidence is kept in trace.md and in the ticket's design-check line. Partial notes: fixed half listed, not-fixed half Bug, untestable half Task." |
| P8 | AMEND | One Bug per root cause is correct, but confirmation must cover every affected service or one retest closes a still-broken sibling (R-DEFECTS-004). Merge only on a confirmed root cause (design lookup), otherwise link Relates. Severity = worst instance. | "One Bug lists each service + serial + note. Retest steps cover all listed services. Merge needs a design-lookup root cause; symptom similarity alone = separate Bugs linked Relates." |
| P9 | APPROVE | Single source for counts is the metrics-honesty gate (R-MANAGEMENT-008, R-DESIGN-010). Must exit non-zero and block email/QA message/rank titles on any mismatch. Add severity/priority split and `held`/`skipped` buckets to the printed numbers. | |
| P10 | APPROVE | Lane self-report is not evidence. Lead read-back should compare against the intended fields (type, severity, priority, links, attachments), not just existence (R-DEFECTS-001). | |
| P11 | AMEND | Environment/data blockers are not product defects (R-AUTOMATION-013) but are project risks (R-MANAGEMENT-003): they reduce coverage and must be counted as uncovered, with the exact error, in the report. | "...listed as open items with the exact error, counted as NOT COVERED in coverage and named in residual risk." |
| P12 | APPROVE | Consistent classification of the signing step; reproducible 5xx stays a product defect (R-AUTOMATION-013). Use the same sentence in both places. | |
| P13 | AMEND | Untestable is a coverage gap, not a defect. A Task to dev is fine when dev can verify; the env-only items must still appear in residual risk (qa-workflow 3.8, R-MANAGEMENT-008). | "...open item with no Task, listed under residual risk and counted as not covered." |
| P14 | AMEND | Re-check must do confirmation AND regression before Done (R-DEFECTS-004); a failed fix goes back to Open on the same key (qa-workflow 6: Resolved to Open). | "Verify = re-run the original steps (confirmation) + a regression set (same component and sibling services, named in the comment); both pass before Done. Failure: Re Opened on the same key with new evidence." |
| P15 | AMEND | Feeding Not-Bug closures back is right (qa-workflow 6: Rejected to Closed only when the reporter agrees), but a wrong entry silently suppresses real bugs via P5. Only design/not-a-defect reasons qualify, not duplicate or cannot-reproduce. | "Add to the known-not-a-bug list only for reason = by design/not a defect, with key, date, reason; the owner confirms the entry." |
| P16 | APPROVE | Prevents losing open untestable work items (data-loss guard; R-DEFECTS-005: no item without an owner). | |
| P17 | AMEND | Two separate fields (R-DEFECTS-002); but the table is a default, not an automatic mapping (impact is severity, urgency is priority). "Found in" = env + date is enough on staging; "introduced" is advisory (R-DEFECTS-006). | "Set severity (impact) and priority (urgency) explicitly; table gives defaults only. Record found-in env/date; introduced-in if known, else `unknown`." |
| P18 | APPROVE | Facts about the work product, no blame (R-DEFECTS-003). Keep dates and both keys. | |
| P19 | AMEND | Must be criteria-based (R-MANAGEMENT-008/009): show coverage (notes verified X of N, with untestable/blocked counted as not covered), not only defect counts. Exit statement names the criteria met or unmet. | "...exit statement: 'criteria met / unmet: <list>; ready / not ready for <next step> because ...', coverage line 'verified X of N notes; Y not covered'." |
| P20 | AMEND | Completion per qa-workflow 3.8 also needs: no planned defect left open without a decision, residual risk, archived testware, and a short retrospective line with an owner. | "Add: open defects each have a decision; residual risk stated; testware archived (rank evidence); 1-3 lessons with owner." |
| P21 | APPROVE | Quota contradicts minimum-sufficient delegation; hard counts rot (R-MANAGEMENT-007). | |
| P22 | AMEND | Mis-targeted: SKILL section 0 overrides nj-jira 4b (Jira review page), not nj-rank (section 6 already says preview before filing). Replace with P6: clean rows file on "upload", risky rows wait. | "Remove the nj-jira 4b override for risky rows (P6 governs); keep nj-rank preview-before-file as already written." |

## New proposals

- **N-qa-1 Exit criteria in trace.md header.** Declare before filing: every note has a verdict; every not-fixed has a key or a recorded reason; every Bug has severity, priority, evidence; every blocker listed. Wrap-up is "complete" only when met; otherwise the report says "exit by budget/time, residual risk: ..." openly (qa-workflow 8, R-MANAGEMENT-009).
- **N-qa-2 Two-way trace and fixed-needs-evidence.** trace.md rows: note -> test (serial, desk, date) -> result -> key; plus reverse key -> notes. A `fixed` verdict must carry the retest evidence path, not just "no defect seen" (R-DESIGN-010, R-DEFECTS-004).
- **N-qa-3 Retest block in every Bug.** Each Bug carries "confirmation steps" and "regression neighbours", so the P14 re-check route starts with ready input, and counts are labelled with denominators ("8 of 27 notes became new Bugs; 3 existing") and never used as a score (R-DEFECTS-004, R-MANAGEMENT-007/008).

## The one thing that must not ship

P8 as written. Merging systemic defects into one Bug without per-service traceability and a retest that covers every listed service lets a fix confirmed on one service close a defect still present on the others (R-DEFECTS-004, R-DESIGN-010). Ship it only with the amended text above.
