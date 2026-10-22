---
name: nj-supervise
description: How to brief a delegated worker and how to know it is actually working. Use whenever spawning subagents or teammates for a batch of units - audits, sweeps, per-service fixes, migrations, any fan-out. Covers the brief's mandatory clauses, the four checks that detect parking/drift/undercount, and the director's own estimate discipline. Triggers - delegate this, run workers on each X, fan out, how do I know the agent is working, worker KPI, the agent says running but nothing happens, my estimate slipped.
---

# Supervising delegated workers

Derived from one measured session (PROJ, 2026-09-20, 9 Sonnet workers, 46 videos),
then attacked by `nj-kit:devil` and grounded by `nj-researcher`. It exists so the
same four failures are not rediscovered per project.

## The four failures this prevents

Every one was invisible in the worker's own report and visible on disk.

| # | What happened | Cost |
|---|---|---|
| P1 | Two workers ended turns with a backgrounded job; reported "running" while output mtime was frozen | ~20 min each, the largest single loss |
| P2 | A worker returned **0** findings for a unit whose real answer was **47** — a hardcoded path silently excluded everything before scoring | Would have shipped a clean bill on a broken unit |
| P3 | A worker edited the **shared** script other live workers were reading | Corrupts a whole batch, not one unit |
| P4 | The director estimated 20 min off a 1-unit pilot; actual 90 min, and never volunteered the slip | User had to ask five times |

Sits under `nj-delegate` §0 (NJ Governance v3): the Lead is the sole orchestrator and
spends turns on receipts, not on progress. Everything below is **deterministic supervision** —
artefact checks a script can run — which v3 keeps and encourages; what it bans is waking the
Lead to interpret "still running". Under v3 two of these clauses stopped being habits: named
write paths are claimed at runtime (`relay.py claim`) and checked across briefs
(`check_governance.py --run`), because the count itself is now derived from them (§0.6).

## Part 1 — the brief

Eight clauses. Omit one and you get the matching failure back.

1. **Named write paths.** "Your writes are limited to: `<exact paths>`. Anything
   else is drift." A worker that needs to change shared tooling gets its **own
   copy**; never the file another live worker reads. (P3)
2. **Write per unit, atomically.** "After each unit, append to your output file —
   write a temp file and rename, never edit in place." Incremental writing is
   what makes liveness checkable at all; atomic rename is what stops the race
   the incremental writing would otherwise create. (P1, P3)
3. **A stall bound, not just a total budget.** "If you produce no new output for
   `<~6x the median unit time>`, stop and report the cause." A total budget is a
   claim about the future and is unfalsifiable from a snapshot; a stall bound is
   checkable now. (Lamport 1977 on liveness; SQS visibility timeouts.)
4. **Foreground only.** "Never end a turn with your own work still running. No
   background jobs, no monitors, no polling." Say it, but do not trust it —
   see Part 2, check A. Saying it twice did not work. (P1) The Lead dispatches a
   worker that builds or edits in the foreground too (owner, 2026-09-29); only
   read-only research runs in the background, and every brief carries the `FOCUS`
   line: a mid-run message that does not start `AMEND:` is not a task.
5. **Budgets are ceilings, never targets.** Token and tool-call limits mean
   "name the cause and stop", never "aim for this". Any effort number a worker
   knows it is scored on gets padded. (Goodhart; Campbell; Strathern 1997.)
6. **One report, at the end: a receipt of ≤ 25 lines plus the stage detail file.**
   STATUS / FINDING / EVIDENCE / FILES-SYMBOLS / RISK / NEXT ACTION and a CHANGED
   list from `git status`, in the final message; everything else goes in the detail
   file the brief's RESUME line names, and no other report file. Plus: **a positive
   sample before any sweep** — prove the method reproduces one known-true case
   before spending the batch on it.
7. **No delegation.** "Do not spawn, brief or instruct another worker; write the artefact,
   report the path, the Lead decides the next step. Report `delegations: 0`." The runtime does
   not block nested spawning, so the clause and the count are the whole control.
8. **Graded facts, and the right to refuse one.** Every factual claim in the brief is `[V]`
   (cited), `[A]` (falsifiable inference) or `[U]` (to establish). "If a `[V]` claim is false,
   reply `CHALLENGE: <claim> — <counter-evidence>` and stop that line; you are never obliged to
   disprove an `[A]`." This is clause 8 because of a measured failure: on 2026-09-20 a Lead
   wrote an inference as a verified fact and a worker burned a whole pass disproving it. A
   supervision standard that only watches workers will never catch that one.

## Part 2 — the checks

Four, against artefacts, in one command. **When:** once, at the wake event
(worker complete, blocker, stall timeout) — never as a periodic Lead turn. If
liveness must be watched while workers run, a detached script or a bounded
until-loop does check A and wakes the Lead only on a breach.

**A. Liveness — mtime.** `stat -c %y` each worker's output file.
No write within the stall bound = parked, whatever the worker says.
This is the only available proxy for a worker being alive: unlike an OTP
process, an LLM worker emits no death signal, so absence-of-artefact is all
there is — which is exactly why clause 3 must give it a bound to compare to.

**B. Scope — file list.** At report time, list what the worker actually wrote
and compare to its named paths. One `ls`. Do not try to infer drift from
effort signals; those are gameable, a file list is not.

**C. Sibling deviation, both directions.** A unit whose output is far from its
siblings' is a bug until explained — and **zero is only the loudest case**.
P2 was caught at 0-vs-47; a 12-vs-47 would have shipped. Ask for the cause,
not a re-run.

**D. Read one gate line, not the report.** Artefact-based: value is earned at a
checkable artefact — a passing gate, a delivered file, a row count — never at a
worker's narrative of its own progress.

**What is deliberately NOT a check:** tokens-per-unit, calls-per-unit, or rows-
per-unit against the batch median. At n=2–4 workers the "median" is one raw data
point, and unit sizes differ 10x; today's two legitimate workers (6.9k vs 14.1k
tokens/unit) already trip a 2x rule. Below ~8–10 samples use a fixed ceiling,
not a statistical outlier test.

## Part 3 — the director's own discipline

The checks above watch workers. These watch the director, which is where P4 lived.

- **A 1-unit pilot is an n=1 inside-view estimate.** Say so when giving it.
  Re-forecast from the median of *completed* units as they land, and keep the
  class comparable — do not mix blocked units and clean units in one median.
- **Announce a slip unprompted, at the first missed mark**, with the cause.
  "The estimate is void because both workers were parked" is a report;
  waiting to be asked is not.
- **Measure progress by artefacts, not by whether agents are alive.**
  "Still running" is not progress. Rows on disk are.
- **Reach for the cheapest instrument that answers the question.** Check what the
  pipeline already records before rendering, decoding or re-running anything.
  In the source session, ~70 min of video decode was spent to infer what the
  build's own checkpoint files already stated; every finding that survived came
  from JSON and audio reads that took seconds.

## The brief itself

Use `nj-delegate/templates/worker-brief.md`: it carries all eight clauses as gated
fields (`check_governance.py --brief`). Clause 2 (write per unit, atomically) goes in
its RESUME line; the positive sample (clause 6) goes in GATES. There is no second
skeleton here on purpose — two skeletons drifted apart once (prompt audit, 2026-09-29).

## Sources

`nj-researcher` checkpoint, 2026-09-20: Lamport (liveness/safety, 1977); SQS
visibility-timeout and dead-letter practice; Erlang/OTP supervision trees (noted
as *not* transferring — no death signal from an LLM worker); Goodhart/Campbell,
Strathern 1997; Flyvbjerg on reference-class forecasting and the planning
fallacy; small-sample limits of median/MAD (derived, not cited). Adversarial
pass: `nj-kit:devil`, same date — it is what removed the three effort metrics
and forced the director section.
