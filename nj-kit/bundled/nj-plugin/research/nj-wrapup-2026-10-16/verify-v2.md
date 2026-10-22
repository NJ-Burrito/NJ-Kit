# nj-wrapup v2 verification (2026-10-16): v1 vs v2

Method: 3 Haiku helpers (one per trial, one foreground batch, delegations 3) walked v2 step by step, read-only. The lead spot-checked `reconcile.py` l.100-111 (CLOSED check on `existing` rows only), `_common.load_results` (`d.get` on a list shape) and `nj_rank.py` `--protect`. Selftests of discover / reconcile / render: all PASS. Detail: `v2-t1/2/3.md|json`. Grades: [V] verified by the lead in code, [A] helper inference.

## Verdict: SHIP WITH FIXES
v2 fixes the v1 structure problems (router, size rule, scripts, held-row end batch, no hand-typed counts), and the reconcile gate really catches the v1 double count. It is not yet safe for a multi-service run: nothing in code stops a Bug that a developer will close as Not Bug. Fix items 1-3 below before the next real wrap-up; 4-8 can follow.

## Counts per trial (rows are walk steps, so row totals differ between versions)
| Trial | v1 ok / amb / wrong / missing / wasted (rows) | v2 ok / amb / wrong / missing / wasted (rows) | v1 defects fixed / partly / open in v2 |
|---|---|---|---|
| T1 notes-ticket PROJ-1234 | 13 / 12 / 1 / 4 / 4 (34) | 10 / 7 / 6 / 1 / 0 (24) | 12 / 3 / 6 of 21 |
| T2 multi-service + re-check | 1 / 7 / 6 / 4 / 1 (19) | 6 / 20 / 9 / 3 / 0 (38) | 4 / 7 / 8 of 19 |
| T3 non-testing + blocked probe | 0 / 5 / 2 / 6 / 2 (15) | 14 / 12 / 6 / 6 / 1 (39) | 4 / 4 / 7 of 15, plus 9 new |

Reading: wasted fell from 7 to 1; ok rose in T2 and T3. "wrong" rose in T1 and T3 because v2 now has scripts that can be wrong; those are concrete, fixable defects. T2 is still mostly ambiguous.

## Specific checks
| Check | Result |
|---|---|
| Router picks type, skips | OK for all 3 (notes-ticket 0-12; multi-service 0-7, 9-12; non-testing 0, 9, 10, 12). Gaps: a re-check inside a multi-service run is two rows and the skill does not say they combine; a blocked non-testing session matches two rows (no precedence). |
| Size rule | T1 A=16 gives up to 4 lanes (matches the 4 real lanes). T2 A=8 after gates gives 1 Sonnet filer (A=16 without gates gives 4 lanes). T3 A=0 gives the Lead alone. OK. |
| 5031 filed once | NOT guaranteed [A]. The one-Bug-per-root-cause rule is in step 3, but lanes claim by note id, so a by-service split can still make up to 5 copies; reconcile does not check duplicates across services. |
| Gates vs the 8 T2 Not-Bugs | table below: 6 are stopped only if the Lead applies a HABIT gate or a known-list entry written after the case, 1 slips outright, reconcile catches none. |
| Untestable split Task vs open item | OK. The code-anchor rule is clear and enforced by reconcile in strict mode. T1 Tasks 5097-5102 would fail strict (no `wrapup` label, no anchor): correct for a pre-v2 session, `--legacy` passes. |
| Held rows end batch | OK in text (one AskUserQuestion at the end). Memory «Lead decides, no questions» (2026-10-11) could be read as a conflict; the global CLAUDE.md still routes decisions through AskUserQuestion, so say so in the skill. |
| Email / QA message from trace with lint | T1: render from the legacy trace passed, AR and EN 28 lines each, lint clean, v1 leaks caught in selftest. T2: single-service context schema only; counts not checked against live Jira. T3: no path without a trace. |
| nj-rank protect/link | `--protect` and `--link-to` exist [V]. The trace holds the Bug keys, not the nj-rank Task keys (PROJ-1234..5108), so `close-mine --protect trace.json` does not protect the rank items themselves [A]. |
| Close step | `relay.py sweep\|batch\|verify` exist. `sweep` is project-wide: exit 1 on 5 peer leftovers in T3, so exit 0 may be unreachable. The skill says "else name the leftovers"; add that peers do not fail the step. |
| Conflicts | Handoff: the skill says only at threshold or "end session"; global CLAUDE.md says before every session end, and PROJ has two named streams. Step 3 approval wording vs the nj-rank preview gate is unchanged. No conflict with the trigger-only hierarchy or the leftovers rule. |

## T2: which gate stops which Not-Bug key
| Key | Reason (Jira) | Stopped by | Holds? |
|---|---|---|---|
| 5028 | dev: PROJ-1234 pt 3 adds the option | step 2 gate 2 (latest dated statement) / risk `conflicting-tickets` | habit only [A] |
| 5029 | dev: PROJ-1234 pt 3 fixed text | gate 2 | habit only [A] |
| 5030 | no comment, no reason | none | SLIPS [A] |
| 5032 | needs a facility with a practice licence | gate 5 (test-data cause) | habit only [A] |
| 5039, 5041 | withdrawn same day (letter number) | known-not-a-bug entry in nj-jira/references/PROJ.md [V] | the entry was written from this case; before it existed they slip to gate 3 |
| 5040 | SIGN_HERE in signature block | known-not-a-bug entry + nj-qa-pipeline §3c [V] | yes |
| 5042 | second output missing | gate 3 (`flowable/lookup.py --q outputs`) | habit only [A] |

Code: `reconcile.py` flags a CLOSED status only on `existing` rows [V], so a new Bug that is already Not Bug passes. 5031 is correctly not among the 8.

## Remaining defects, ranked, one-line fix
1. reconcile passes new Bugs whose live status is Not Bug or closed [V]. Fix: apply the CLOSED check to every filed row; fail unless the row is marked `reopened`.
2. Step 2 gates are [HABIT], so 5030-type rows slip and 5 others rely on discipline. Fix: `plan.md` gets one column per gate (1-5) plus gate 6 «read the developer comments and live status of covering tickets»; a small `gates.py` refuses a row with an empty cell.
3. `reconcile.py` crashes (exit 1) on the tracker shapes `list` and `{rows}` that the profile itself says exist [V]; discover.py reports "0 keys" for the same tracker. Fix: normalise all three shapes in `_common.load_results`.
4. 5031 can become 5 Bugs because lanes claim by note id. Fix: merge same-root-cause rows into one plan row (one owning lane) before lanes start; reconcile warns on identical summaries.
5. `close-mine --protect trace.json` misses the rank Task keys, and there is no sanctioned no-trace form. Fix: protect = trace keys plus discover `rank_items` keys; add `--protect none` that forces a dry run.
6. Non-testing sessions have no output path (render.py needs a trace; the email is test-shaped). Fix: for that row step 10 is a 5-line AR+EN `.txt`, no email unless a recipient is named; make steps 6 and 9 and the staging table conditional on keys existing.
7. The multi-service email and context are single-service and not checked against live Jira status or year (the v1 email said 14 Bugs, 6 later Not Bug; «2031» vs Jira 2027). Fix: `services[]` in context, re-GET statuses at render time, lint the year.
8. discover.py is not session-scoped (lists 14 other sessions' rank items); sweep fails on peers; the handoff rule conflicts with CLAUDE.md. Fix: filter by session tag or date window, name peers without failing, and let the profile name the handoff stream file.

## Incident (not the skill's fault)
The T2 helper's credentials-reading one-liner printed the OpenRouter token and part of the Jira password into its own transcript. Rotating both is recommended. For future briefs: read credentials only through the scripts' `--creds`, never a one-liner that prints.

## Not done / not verified
No live filing, no rank write, no render to the Desktop (dry-run brief). `relay.py batch` not executed. Gate-table grades are [A] except where marked [V].
