# Council vote: the developer who receives the tickets (Shahed / operations engineer)

Calibration (read-only GET, 4 calls): PROJ-1234 Bug High To Do, signing 500 SIGNING_F..., the owner reassigned it to operations in a comment (so the filing assignee was wrong first time). PROJ-1234 / 5096 Bug Medium To Do (5094 carried the lane's own "may close Not Bug" risk). PROJ-1234 Task Medium. From trial-2: 8 of 16 keys filed on 2026-10-12 turned Not Bug (5028/29/32 because a later/other ticket or test-data gap explained it). That is the cost I feel: each Not Bug is a read, a reproduce attempt and a comment from me.

| P# | Vote | Reason | Amended text |
|---|---|---|---|
| P1 | APPROVE | Duplicates reach me first; discovering what is already filed is the cheapest dup gate. | |
| P2 | AMEND | Right idea; a re-check session must never create Bugs from its own result. | Add: re-check type may only comment/transition our Bugs (Done / Re Opened with the new observation); a new defect found during re-check goes through the notes-ticket gates, not straight to a key. |
| P3 | AMEND | Fewer filers is fine for me, but up to 4 lanes means 4 writing styles and 4 ideas of priority. | Keep the numbers; add: the Lead runs one normalisation pass (template sections present, priority per P17, assignee per N-dev-2, wording per P18) over all drafts before the first create. Lanes never create before P5/P6 have run. |
| P4 | APPROVE | Generic core is fine if the PROJ profile still carries the template, known-not-a-bug list and assignee rules that make tickets actionable. | |
| P5 | APPROVE | The single biggest Not-Bug reducer; 8 of 8 later Not-Bugs were catchable. | Add a 5th gate: test-data / account cause (5032 was "use a facility that has a practice licence"). A row that is explained by our data is an open item, not a Bug. |
| P6 | APPROVE | "File it" must not cover rows the lane itself marked "may close Not Bug" (5094). | Risky-row question must show, per row, the precedent key and the dev's reason when it was closed. |
| P7 | AMEND | the owner's verdict wins, but I will close a Bug whose body contradicts the design if the only support is "the owner said so". | When the owner's verdict conflicts with design evidence and he confirms, the Bug quotes his ruling as the source (key/date/author) AND states the design evidence in one line, so I see it is a deliberate change request, not a defect. Prefer type Task/change request if the design shows the current behaviour is intended. |
| P8 | AMEND | One Bug per root cause is good for me only if I can reproduce each instance. | Systemic Bug body = common root cause (BPMN node / variable / template) + one row per affected service: card, step, account type, expected, actual, evidence file. Merge only when root cause is the same; same symptom with different causes stays separate. Dev closes the key only after every row is checked, so add a checklist of the rows. |
| P9 | APPROVE | Counts I read in the email/QA message must match Jira. | |
| P10 | APPROVE | I have received tickets with wrong assignee/type from lane self-reports; the Lead GET catches it. | Read-back also asserts: type, priority value, assignee, Relates link to Story, attachment count > 0 for UI defects. |
| P11 | AMEND | Agree: environment/data blockage is not a Bug. But a reproducible app 5xx is a Bug and must go to the right team. | Blocker Bug carries: request serial type, timestamp, endpoint, HTTP status, one-line error body, steps to reach it. Assignee = operations/integration owner for integration or infra faults (see N-dev-2), never the feature dev by default. |
| P12 | APPROVE | Matches 5092 as filed (reproducible 500 on Sanad callback). | |
| P13 | AMEND | A Task for me must say what to check in code; trial-2 shows 7 untestables with no code action. | Dev-verifiable Task body must name the concrete thing: file/config/BPMN node/variable/template key and the exact value expected; if the lane cannot name one, it is an open item for the owner/BA, not a Task. Link "is blocked by" as written. |
| P14 | APPROVE | Re-check with Done / Re Opened is exactly what closes my loop. | Re Opened comment states what still fails vs the original steps and the date/build. |
| P15 | APPROVE | Stops us filing the same Not-Bug twice. | Entry records my closing reason verbatim (key, date, commenter). |
| P16 | APPROVE | Mass-closing Tasks I have not yet read would be bad. | |
| P17 | AMEND | Priority inflation makes me ignore High. Observed: all non-blocker Bugs were Medium. | Table: blocker (cannot proceed past a step) = High; wrong behaviour with workaround = Medium; wording/label/order = Low. Set only fields the Jira project actually has (verify a severity field exists before writing one). "Found in" env + build date in the body (already in template). |
| P18 | APPROVE | «لم يُصلح رغم إغلاق» reads as an accusation and starts an argument. | Neutral line must still name the closed key and what it changed so I can see regression vs never fixed. |
| P19 | APPROVE | Not mine to use, but the email must not promise things about my tickets. | Email states assignee/status only from the P10 read-back, with an "as of HH:MM" line. |
| P20 | APPROVE | Open staging requests table helps me find the requests the ticket mentions. | |
| P21 | APPROVE | Fewer wasted lanes. | |
| P22 | APPROVE | Preview before filing is a pre-file human check; fewer bad tickets. | |

Count: APPROVE 14, AMEND 8, REJECT 0.

## New proposals

**N-dev-1 "What to check" section in every Bug and Task.** Add to the bug template, after the expected/actual blocks: 2-4 lines "للمطوّر: أين تتحقق" naming the design pointer from the flowable lookup (process, node, variable, output template) and the exact expected value, or "no design pointer found" stated openly. Reason: a Bug that only describes a screen forces me to hunt; trial notes show routing/output defects were disputed because the design check was not on the ticket.

**N-dev-2 Assignee routing rule.** Feature defect on a service -> the Story's dev; integration/infra faults (Sanad, payment gateway, 5xx not tied to a form) -> operations owner; unknown -> ask once in the P6 batch. 5092 was filed to the feature dev and the owner had to reassign it to operations.

**N-dev-3 Lineage and not-duplicate line.** Every Bug lists related Done/closed tickets with what each changed and one line on why this is not the same item (as the lane did for 4563/4565 in N16). Plus preconditions to reproduce: account type, request state and data needed, without real IDs. Cuts "duplicate" and "cannot reproduce" Not-Bug closes.

## The one thing that must not ship

P3 (more or fewer parallel filers) without P5 + P6 enforced as hard gates before the first create. Filing is irreversible and lands in my queue; a faster fan-out that can still create risky or already-explained rows (as on 2026-10-12, 8 of 16 keys Not Bug) just produces Not-Bug round-trips quicker. If only one thing is kept from this package, keep the pre-classify gates and the held risky rows.
