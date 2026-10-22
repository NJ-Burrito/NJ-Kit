# Tier → runtime map (workspace-local, NOT policy) — NJ Governance v3

On-demand. Read this only when a brief must name a concrete runtime or a wait
mechanism; never quote it inside the core policy, and never route by the name
instead of by the reasoning type (`SKILL.md` §3). If the roster changes, only
this file changes.

| tier | `Agent` alias | model id (checked 2026-09-29 against the claude-api skill's table, cached 2026-09-25) | $/MTok in / out · cache read | notes |
|---|---|---|---|---|
| DETERMINISTIC | — | no model — Python/PowerShell, CLI, parsers, tests, git, grep | — | always tried first |
| FREE-LOCAL | — | none installed on this machine | — | rung is empty here; do not invent one |
| ECONOMY | `haiku` | `claude-haiku-4-5` (Haiku 4.5; use the alias, no date suffix) | 1 / 5 · not in the table | bulk/extraction classes, the interpreter |
| STANDARD | `sonnet` | `claude-sonnet-5-5` (Sonnet 5.5; `claude-sonnet-5` is the previous generation), effort default `high` | 2 / 10 · 0.20 (0.1×) | implementation, debugging, scoring, authoring to a spec |
| FRONTIER | `opus` | `claude-opus-5-5` (Opus 5.5), thinking always on, effort default `medium` | 4 / 20 · 0.20 (0.05×) | judgement only; no per-batch ceiling since 2026-09-17 |
| FRONTIER+ | `fable` | `claude-fable-5-1` (Fable 5.1) | 10 / 50 · 0.25 (0.025×) | only when the owner names it, or a measured CAPABILITY_LIMIT on the FRONTIER runtime |

**Lead:** Opus 5.5 (`claude-opus-5-5`), effort set explicitly at session start and written to
the batch row (default `medium`). It is not switched mid-session (`SKILL.md` §11.1 r7).
Telemetry records the runtime id the `Agent` result reports, never this table. Which id an
alias resolves to is not visible from inside a session [U] — established when a ledger row
records `runtime` from the `Agent` result. Re-check this table at every model release: the
claude-api skill's "Current Models" table is the source.

Prices: claude-api skill model table (cached 2026-09-25). Treat them as list price; the owner's plan
may bill differently.

**Under v3 this table is consulted twice, not once.** §0.8 asks for a free verifier *before* a
tier: where one exists, the cheapest plausible runtime attempts the stage and only its failures
escalate, so one stage may touch two rows of this table. Start model and effort come from
`relay.py route <project> --class C` (floor Sonnet 5.5, learned from ledger.md); a failed verifier
moves the stage to Opus 5.5 once via `relay.py route --failed … --cause …`, replacing the old
"only CAPABILITY_LIMIT, in writing" rule (owner, 2026-10-02). Where none exists, one row is chosen and
the brief says `verifier: none because …`.

## Waiting — what Claude Code actually supports (checked 2026-09-20)

There is **no generic event callback**: a running worker cannot raise
DECISION_REQUIRED or RISK_DISCOVERED to the Lead mid-run. The closest supported
mechanisms, in order of preference:

| need | mechanism | Lead turns consumed |
|---|---|---|
| a batch of independent workers, one wake — **required for workers that build or edit** (owner, 2026-09-29) | several `Agent` calls **in one message**, each `run_in_background: false` — they run concurrently and the Lead resumes once, when all have returned | 1 |
| read-only research while the conversation stays open | `Agent` default (background): the harness re-invokes the Lead with a task notification per completion; the brief keeps its `FOCUS` line | 1 per worker — if nothing needs deciding yet, end the turn without tool calls (count it as `lead-passes-while-active`) |
| a long command | `Bash`/`PowerShell` foreground with `timeout` (≤ 600000 ms), or `run_in_background: true` — re-invoked on exit | 0 while waiting |
| a condition (file appears, port opens) | one shell until-loop with a bound, or the `Monitor` tool | 0 while waiting |
| a worker's own recorder/build | the worker waits in the foreground inside ONE shell call (until-loop, bounded) | none of the Lead's |
| stall detection | a script comparing output mtime to the brief's stall bound (`nj-supervise` check A); a detached zero-token refresher where a project has one | 0 |
| `/loop` sessions only, and only where the harness exposes it (the main session here does; subagents do not) | `ScheduleWakeup` as a long fallback heartbeat (≥ 1200 s), never a short poll | 1 per heartbeat |

A worker's only way to reach the Lead early is to **end its turn** with a
receipt (`status: partial` + `QUESTION n/2`, or a blocker) — that arrives as
WORKER_COMPLETE and the Lead classifies the real event from the receipt.
Deadlock guard while the Lead is idle: every brief carries a stall bound and a
budget, so a worker stops itself; the user can always interrupt. Nested spawning
is not blocked by the runtime for general-purpose agents — it is governed by the
brief clause and the receipt's `delegations` count, not enforced.

**Measured ratios that justify the ladder** (derived, see
`<project>/PROJ-tests/artifacts/ops/model-routing-audit-2026-09-16.md` — per-run
tokens there are estimated from tool calls, not counter-measured):
ECONOMY ≈ 350 tok/tool-call, STANDARD ≈ 878, FRONTIER ≈ 2015. On 2026-09-15,
14 of 22 FRONTIER runs (61 % of FRONTIER spend, 28 % of the day) were scoring,
verification, authoring or apply-a-known-rule stages a lower tier would have
done, at the same rework and partial rates.

## Claude Code mechanics that change what the Lead or a worker does (2026-09-29)

Grades: [V] = read from this session's `Agent`/`SendMessage` tool schema on 2026-09-29;
[A] = from the Lead's 2026-09-29 summary, not re-checked here (falsified by the command or
setting being refused).

| mechanism | what it changes |
|---|---|
| `Agent` `run_in_background` [V] | **Foreground (`false`) for any worker that builds or edits** (owner, 2026-09-29): he can watch it, and his messages cannot kill or derail it mid-phase. Background (default) only for read-only research and reading. The `FOCUS` line goes in every brief either way. |
| `SendMessage` to an agent id [V] | continues that agent with its context intact — the way to send a fault back or resume after an interrupt or a rate limit; a new `Agent` call starts cold. |
| `Agent` `model` (`haiku`/`sonnet`/`opus`/`fable`) [V]; agent-definition frontmatter sets model, effort and tools [V] | a brief cannot change a worker's API effort; the Lead picks it with the model or a defined agent type. |
| `Agent` `isolation: "worktree"` [V] | a writer gets its own git worktree (auto-cleaned if unchanged) — for parallel writers whose paths could collide. |
| Workflow tool, opt-in only (e.g. ultracode) [A] | a scripted multi-agent run; load `workflow-authoring` in the brief of the agent that writes the script, never in the Lead. |
| `resumeFromRunId` [A] | relaunch a stopped or interrupted workflow; finished agents replay from cache. |
| `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` [A] | caps a workflow's concurrent agents — set it to the disjoint write-set count, or lower under rate pressure (§11.1 r2). |
| hooks `SubagentStart` / `SubagentStop` / `PostToolBatch` [A] | where deterministic per-worker checks belong (e.g. a CHANGED-vs-`git status` check at SubagentStop) instead of a Lead turn. |
| `/tasks`, `/workflows` [A] | the one look at live workers' state when the owner asks for progress (§7 interrupt guard). |
| `/goal` [A] | a session-level objective; it does not replace the brief's OBJECTIVE or FOCUS. |
