# Council vote: POV = the owner (owner) — nj-wrapup v2

Lens: saves his time/attention? respects "Lead decides, no questions" (2026-10-11), "run once", trigger-only agents? asks only what only he can decide? output forwardable as-is?
Reading of the two rules in tension: ordinary forks are the Lead's (decide, state in one line). Only outward-facing/irreversible choices that guessing could get wrong are his, and those go as ONE batched question at the END, never mid-run. "Upload/file" in his request already approves the clean set.

| P# | Vote | Reason | Amended text |
|---|---|---|---|
| P1 | APPROVE | Stops double-filing/double-registering; must be a silent script step, no output unless something already exists. | |
| P2 | AMEND | Router yes, but detected by script from the results table; Lead states the type in one line. Never ask him which type. | "Detect session type from the results table by script (verdict counts, any filed request). Lead confirms in one line. Ask only if two types tie." |
| P3 | APPROVE | Kills the mandatory-helper tax (lanes 2 and 4 reported delegations 0 anyway). Matches minimum-sufficient workers. | |
| P4 | AMEND | Good for portability, but it is a file move, not new behaviour: do it last and only if it costs no extra run. Core must still work for PROJ with zero extra steps. | "Move PROJ hooks to references/profile-PROJ.md; no behaviour change; ships after P1-P3, P5, P9." |
| P5 | AMEND | Right gate, wrong place: a script/lookup, not a per-row worker, and it must not stop for him. Row failing a gate is held and listed, not asked about. | "Pre-classify gates run as one script pass over not-fixed rows; a failing row is HELD with its reason in the final held-table. No mid-run question." |
| P6 | AMEND | Keep the clean/risky split (PROJ-1234 proves the need) but not as a blocking AskUserQuestion mid-run; that breaks "Lead decides" and trigger-only. | "'Upload' files CLEAN rows. RISKY rows are not filed; the final report ends with ONE held-table (row, risk, proposed ticket, recommended default). He answers once; a single AskUserQuestion at the very end is allowed only if the table has >=1 row." |
| P7 | APPROVE | His verdict beats later design evidence; the conflict shows as a line in the held-table, not an interruption. Partial-split is right. | |
| P8 | APPROVE | One Bug per systemic defect = fewer tickets for him to read and for devs to dedupe; claim table is cheap. | |
| P9 | APPROVE | Wrong counts in a boss email cost him credibility; mechanical counts are the best value in the list. Script, zero tokens. | |
| P10 | AMEND | Merge into P9: the reconcile script does the GETs (it already must). No separate model-run read-back. | "reconcile.py GETs every new key and checks type/assignee/labels/links/attachments; the Lead reads one summary line." |
| P11 | APPROVE | 29-of-77 blocked rows had no route. Output is an "asks" list he can forward. Our-tooling blocker never becomes a client Bug. | |
| P12 | APPROVE | It is his own 2026-10-15 ruling; one canonical text, ends a contradiction between skills. | |
| P13 | APPROVE | Stops junk developer Tasks. Dev-verifiable only. | |
| P14 | AMEND | Fine, but only when the router says re-check; section 0's "touch no ticket we did not file" must be reworded so it does not forbid our own re-check comments. | "Re-check route applies only to Bugs we filed; the 'touch no ticket' rule reads 'no ticket we did not file, except to verify our own'." |
| P15 | APPROVE | Learns once, never asked again. Auto-append with key+date, no question. | |
| P16 | APPROVE | `close-mine --apply` silently closing unverified Tasks is data loss. Must be a code guard, not a note. | |
| P17 | APPROVE | Defaults table decides severity/priority; he is never asked. Found-in env/build is free. | |
| P18 | APPROVE | Neutral wording is the KB rule; protects him from dev pushback. | |
| P19 | AMEND | Test-summary shape yes. But delivery: he explicitly wants copy-ready plain text in chat (skill, memory) and long detail as a file. Do both: Desktop `.txt` per language AND chat paste; one summary line before them. No paths, tokens, error bodies in the email body. | "Write email-ar.txt / email-en.txt / qa-message.txt to Desktop from reconcile data; paste AR and EN in the chat as code blocks (plain text, forwardable as-is); reply otherwise = verdict line + held-table + paths." |
| P20 | AMEND | Sweep and open-staging table: always. Handoff.md: only when context >= ~120k or he says end (his project rule), not on every wrap-up. nj-kit sync only if a skill changed. | "Close = relay.py sweep --tag, open-requests table. handoff.md only at the context threshold or on 'end session'; nj-kit sync only if skills changed." |
| P21 | APPROVE | Pure removal, matches nj-delegate. | |
| P22 | APPROVE | nj-rank's own gate is mechanical (`file` refuses unless preview.html is newer; the preview opens by itself). It costs him one glance, no wait: do not add a pause when his request already said "update nj-rank". | Add: "preview is opened, then filing continues; no wait for a reply when the request already said to update nj-rank." |

Counts: APPROVE 14 / AMEND 8 / REJECT 0 (APPROVE: P1 P3 P7 P8 P9 P11 P12 P13 P15 P16 P17 P18 P21 P22).

## New proposals

- **N-owner-1 One held-table, one wake.** All holds (risky rows, failed gates, partials, open signing/letter questions, new-ticket contradictions) land in a single table at the end of the one report. Nothing is asked mid-run. If he answers "go", the Lead files the held rows in a short second pass using the same plan.md; no re-research. This is the mechanism that makes P5/P6/P7 compatible with "Lead decides, no questions".
- **N-owner-2 First screen = verdict card (ADHD rule 2026-10-11).** Reply opens with: counts from reconcile (filed / existing / untestable / held / fixed), blocker yes/no, then the held-table, then paths. Icon+word states, next step per item. Detail stays in trace.md.
- **N-owner-3 Forwardable-as-is gate.** A script lints email and QA message: no serials, tokens, internal paths, risk wording, AR/EN counts equal, "as of HH:MM" line, keys re-GET at send time. If lint fails the Lead fixes it before showing him; he never edits a draft.

## The one thing that must not ship

A mid-run blocking AskUserQuestion on risky rows (P6 as written). It contradicts "Lead decides, no questions", stalls the Lead against the trigger-only model, and trains him to babysit the wrap-up. Hold-and-report at the end is the same safety at a tenth of the interruption. Close second: any wording that lets `close-mine --apply` run after a wrap-up (P16 is a hard guard).
