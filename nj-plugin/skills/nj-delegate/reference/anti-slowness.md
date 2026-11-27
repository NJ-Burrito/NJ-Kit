# Anti-slowness rules (on-demand; HABIT, no clause number)

Merged from upstream NJ-Kit 2.3.0 (its section 0.22) at the 2026-11-10 sync. Kept as a reference file, not a numbered
clause, because `check_governance.py --tally` and `tests/test_v4.py` pin exactly clauses 0.0 to 0.28. The local clause
0.22 is "The stop hook checks the receipt"; do not cite these rules as 0.22.

Source: Business-Wrap fix batches, 41 workers = 43.3 agent-hours (2026-10-28 16:40 to 10-29 13:11): 717 min (311 calls)
in sleep-loop waits on test logs, 559 min in `npm test` / suite runs (42 suites, 46+ min serial); 49 % of all agent time;
up to 8 lanes ran browser suites at once on a 12-thread laptop (103 browsers, fork failures); no brief had a wall-clock
ceiling; all 60 spawns ran on opus/inherit, 0 Haiku, 0 `relay.py batch` rows.

1. **Tests while iterating are targeted** [HABIT]: named suites or `test:changed`. The full suite runs ONCE per batch,
   after the Lead's merge, by one worker, which pastes its last line; the Lead re-runs only the touched suites.
2. **Wall-clock ceiling per brief** [HABIT, brief line `WALL`]: default 45 min per lane, test time counts; at 80 % the
   worker stops and reports (QUESTION). A full run needing more than 10 min is a tooling defect to report.
3. **At most 3 lanes run browser/test suites at once on this machine** [HABIT, brief line `PARALLEL`]; other lanes queue
   that step (build and edit still run).
4. **No sleep-loop polling of logs** [HABIT]: run the command in ONE blocking call with a `timeout` (or background it and
   end the step on its completion notice).
5. **Worktree hygiene** [HABIT]: `node_modules` by junction, not `npm ci` (10 min); the Lead removes finished worktrees at
   batch close (recycle bin); stale ones are named in the sweep report and nobody builds from them.
6. **Every spawn sets `model` explicitly** [HABIT]: sonnet for a team agent, haiku for a helper. `inherit` or opus as a
   worker is refused (§0.27 and the spawn hook §0.21); the Lead greps `.agent-ops/spawns.jsonl` for any other `model`
   before the batch row.

Workers cannot run `git merge` or `git push` (hook, §0.18): the Lead merges.
