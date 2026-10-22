# Tier → runtime map (workspace-local, NOT policy) — NJ Governance v4

On-demand. Read this only when a brief must name a concrete runtime or a wait
mechanism; never quote it inside the core policy, and never route by the name
instead of by the reasoning type (`SKILL.md` §3). If the roster changes, only
this file changes.

| tier | `Agent` alias | model id (checked 2026-09-29 against the claude-api skill's table, cached 2026-09-25) | $/MTok in / out · cache read | notes |
|---|---|---|---|---|
| DETERMINISTIC | — | no model — Python/PowerShell, CLI, parsers, tests, git, grep | — | always tried first |
| FREE-LOCAL | — | none installed on this machine | — | rung is empty here; do not invent one |
| ECONOMY | `haiku` | `claude-haiku-5-5` (Haiku 5.5, the **helper** role, effort `low`) | 1 / 5 · not in the table | mechanical/bounded classes inside a Sonnet lead: grep/read/extract/count, Jira sync + image logging, probes, sweeps; no `Agent` tool |
| STANDARD | `sonnet` | `claude-sonnet-5-5` (Sonnet 5.5; `claude-sonnet-5` is the previous generation), the **Sonnet-lead** role, effort `medium` (`high` only for a diagnosis brief) | 2 / 10 · 0.20 (0.1×) | implementation, debugging, scoring, authoring to a spec, briefing and reviewing helpers |
| FRONTIER | `opus` | `claude-opus-5-5` (Opus 5.5), thinking always on, effort `medium` | 4 / 20 · 0.20 (0.05×) | **the Lead only** since v4: decisions, review, merge, delivery; never dispatched as a worker or as an escalation step |
| FRONTIER+ | `fable` | `claude-fable-5-1` (Fable 5.1) | 10 / 50 · 0.25 (0.025×) | only when the owner names it, or a measured CAPABILITY_LIMIT on the FRONTIER runtime |

**Model id per role (v4, `SKILL.md` §0.1):**

| role | `Agent` `model` | id | effort | runs |
|---|---|---|---|---|
| Lead | — (the main session) | `claude-opus-5-5` | `medium` | the session; written to the batch row |
| Sonnet lead | `sonnet` | `claude-sonnet-5-5` | `medium`; `high` for a diagnosis brief | background, own worktree |
| Haiku helper | `haiku` | `claude-haiku-5-5` | `low` | one foreground batch inside a Sonnet lead |

The Lead decides per stage which of the two worker models runs it. It is not switched
mid-session (`SKILL.md` §11.1 r7). Telemetry records the runtime id the `Agent` result reports,
never this table. Which id an alias resolves to is not visible from inside a session [U] —
established when a ledger row records `runtime` from the `Agent` result. Re-check this table at
every model release: the claude-api skill's "Current Models" table is the source.

Prices: claude-api skill model table (cached 2026-09-25). Treat them as list price; the owner's plan
may bill differently.

**Under v4 this table is consulted twice, not once.** §0.8 asks for a free verifier *before* a
tier: where one exists, the cheapest plausible runtime attempts the stage and only its failures
escalate. Start model and effort come from
`relay.py route <project> --class C --start haiku|sonnet` (the Lead's start choice; effort learned from ledger.md); a failed verifier
moves the stage up **once, haiku → sonnet** via `relay.py route --failed … --cause … --ran-on <model>`.
**Opus is no longer an escalation step** (decisions.md 2026-10-16): `relay.py route` has
`NEXT_TIER = haiku → sonnet` only; a stage that fails on sonnet prints STOP and is reported to the
Lead, who adjudicates. Where no verifier exists, one
row is chosen and the brief says `verifier: none because …`.

## Waiting — what Claude Code actually supports (checked 2026-09-20)

There is **no generic event callback**: a running worker cannot raise
DECISION_REQUIRED or RISK_DISCOVERED to the Lead mid-run. The closest supported
mechanisms, in order of preference:

| need | mechanism | Lead turns consumed |
|---|---|---|
| a batch of independent Sonnet leads, one wake | several `Agent` calls **in one message**, each `run_in_background: true` — the Lead stays free; each lead's completion is the trigger (receipt + ≤ 25-line report) and the harness re-invokes the Lead with a task notification | 1 per lead — if nothing needs deciding yet, end the turn without tool calls (count it as `lead-passes-while-active`); never poll or sleep |
| a batch of Haiku helpers, one wake | several `Agent` calls **in one message**, `model: "haiku"`, **foreground** (no `run_in_background`), issued by a Sonnet lead; the lead reads each receipt before its own single report | 0 of the Lead's |
| a long command | `Bash`/`PowerShell` foreground with `timeout` (≤ 600000 ms), or `run_in_background: true` — re-invoked on exit | 0 while waiting |
| a condition (file appears, port opens) | one shell until-loop with a bound, or the `Monitor` tool | 0 while waiting |
| a worker's own recorder/build | the worker waits inside ONE shell call (until-loop, bounded) and ends its turn only when done | none of the Lead's |
| stall detection | the worker's own stall bound; a script comparing output mtime to it, run once at a wake (`nj-supervise` check A) — no cron watchdog, no monitor polling in v4 | 0 |
| `/loop` sessions only, and only where the harness exposes it (the main session here does; subagents do not) | `ScheduleWakeup` as a long fallback heartbeat (≥ 1200 s), never a short poll; **not used for worker supervision** (v4: no model-mediated polling, `SKILL.md` §0.5) | 1 per heartbeat |

A worker's only way to reach the Lead early is to **end its turn** with a
receipt (`status: partial` + `QUESTION n/2`, or a blocker) — that arrives as
WORKER_COMPLETE and the Lead classifies the real event from the receipt.
Deadlock guard while the Lead is idle: every brief carries a stall bound and a
budget, so a worker stops itself; the user can always interrupt. Nested spawning
is not blocked by the runtime for general-purpose agents: depth is capped by the env below, helpers
are kept from spawning by an agent definition without the `Agent` tool (`PENDING (B3)`), and
`helpers_spawned` comes from the spawn log `.agent-ops/spawns.jsonl` (`ts, parent, child_type, model, depth`; checked by `relay.py verify` with `delegation_legal`), not from the receipt.

**Measured ratios that justify the ladder** (derived, see
`<project>/PROJ-tests/artifacts/ops/model-routing-audit-2026-09-16.md` — per-run
tokens there are estimated from tool calls, not counter-measured):
ECONOMY ≈ 350 tok/tool-call, STANDARD ≈ 878, FRONTIER ≈ 2015. On 2026-09-15,
14 of 22 FRONTIER runs (61 % of FRONTIER spend, 28 % of the day) were scoring,
verification, authoring or apply-a-known-rule stages a lower tier would have
done, at the same rework and partial rates.

## v4 tree mechanics (2026-10-16; supersedes the 2026-10-14 trigger-only section)

Canonical policy: `SKILL.md` §0 (not restated here). Grades: [DOC] Claude Code docs
(sub-agents, worktrees, hooks), [M] measured in our runs, [U] still to settle in the pilot.

| edge or fact | mechanism |
|---|---|
| Lead → Sonnet lead | `Agent` with `model: "sonnet"`, `run_in_background: true`, `isolation: "worktree"` where the project is a git repo; completion notification is the trigger |
| Sonnet lead → Haiku helpers | `Agent` `model: "haiku"`, FOREGROUND, all helpers of a batch in ONE message; one wake per batch [M: a nested foreground spawn returned its report, probe 2026-10-14; a nested *background* child reports to the main conversation, so never use it]. The lead never ends its turn with a child running |
| depth | `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2` so no third layer exists [DOC; value semantics inferred, [U] until the pilot]. The `Agent(type)` allowlist is ignored inside subagent definitions [DOC], so the control on helpers is **omitting `Agent` from `tools`** in `haiku-helper.md` |
| width | `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=20` [DOC: default 20, error `Concurrent subagent limit reached`]; [M: 5 leads × ~6 helpers refused 2026-10-15]. **Policy counts ALL agents against 20** (leads + helpers + nj-rank workers + any other) via `relay.py slots claim|release|list` (`.agent-ops/slots.json`, built). Size batches so the total ≤ 20 (default 4 leads × ≤ 4 helpers); a refused helper is retried once with a smaller batch, never replaced by the lead authoring under an alias. Queueing/429 behaviour at 20 is [U]: stagger starts |
| effort | per-call `effort` exists from Claude Code v2.1.292 only, and `CLAUDE_CODE_EFFORT_LEVEL` overrides everything [DOC]; trust the agent-definition frontmatter (`sonnet-lead.md`, `haiku-helper.md`); Haiku effort support is [U] |
| precedence | model: `Agent` call parameter > agent-definition frontmatter > env > main session [DOC] |
| agent definitions | `~/.claude/agents/sonnet-lead.md` (`model: sonnet`, `effort: medium`, `isolation: worktree`, tools incl. `Agent`, Bash, Edit, Write) and `haiku-helper.md` (`model: haiku`, `effort: low`, tools Read/Grep/Glob/Write, no `Agent`, no Bash): `PENDING (B3)` |
| background vs foreground | lead background, helper foreground is a **measured workaround [M]**, not a documented rule; docs say background subagents get a smaller tool set [DOC] and fork mode removes `run_in_background` [DOC]: keep the probe in the pilot |
| worktree | `isolation: "worktree"` branches from the default branch, is auto-removed if unchanged, and holds a lock while running [DOC]; the branch name the Agent result returns is [U] until the pilot |
| hooks | `SubagentStart` (writes the spawn log `.agent-ops/spawns.jsonl`; whether the input carries a parent id is [U], fallback: count `Agent` tool_use in the lead transcript), `SubagentStop` (receipt ≤ 25 lines, CHANGED vs claim; exit 2 can block) [DOC], `PreToolUse` (deny `git push`/`git merge`/`checkout main`/`reset --hard` for non-Lead agents; deny secrets paths for helpers): all `PENDING (B3)` |

## Claude Code mechanics that change what the Lead or a worker does (2026-09-29)

Grades: [V] = read from this session's `Agent`/`SendMessage` tool schema on 2026-09-29;
[A] = from the Lead's 2026-09-29 summary, not re-checked here (falsified by the command or
setting being refused).

| mechanism | what it changes |
|---|---|
| `Agent` `run_in_background` [V] | **`true` for every Sonnet lead; helpers are foreground** (owner, 2026-10-16 v4; leads background since 2026-10-11): the Lead stays free, an interrupt from the owner cannot kill a background lead, and the completion notification is the trigger. Mid-run changes: `AMEND:` via `SendMessage`. The `FOCUS` line goes in every brief. |
| `SendMessage` to an agent id [V] | continues that agent with its context intact (auto-resume) — the way to send a fault back or resume after an interrupt or a rate limit; a new `Agent` call starts cold. Sent only by the parent to its child; never sibling to sibling. |
| `Agent` `model` (`haiku`/`sonnet`/`opus`/`fable`) [V]; agent-definition frontmatter sets model, effort and tools [V] | a brief cannot change a worker's API effort; the Lead picks it with the model or a defined agent type. |
| `Agent` `isolation: "worktree"` [V] | a writer gets its own git worktree (auto-cleaned if unchanged) — for parallel writers whose paths could collide. |
| Workflow tool, opt-in only (e.g. ultracode) [A] | a scripted multi-agent run; load `workflow-authoring` in the brief of the agent that writes the script, never in the Lead. |
| `resumeFromRunId` [A] | relaunch a stopped or interrupted workflow; finished agents replay from cache. |
| `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS` [A] | caps a workflow's concurrent agents — set it to the disjoint write-set count, or lower under rate pressure (§11.1 r2). |
| hooks `SubagentStart` / `SubagentStop` / `PostToolBatch` [A] | where deterministic per-worker checks belong (e.g. a CHANGED-vs-`git status` check at SubagentStop) instead of a Lead turn. |
| `/tasks`, `/workflows` [A] | the one look at live workers' state when the owner asks for progress (§7 interrupt guard). |
| `/goal` [A] | a session-level objective; it does not replace the brief's OBJECTIVE or FOCUS. |
