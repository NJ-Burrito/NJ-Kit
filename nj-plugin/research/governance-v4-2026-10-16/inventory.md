# Governance v4 inventory - where agents-work rules live (2026-10-16)

Read-only inventory for the NEW METHOD: Lead = Opus 5.5 medium (review, decisions, git push/merge, delivery only); workers = Sonnet 5.5; each Sonnet runs several Haiku 5.5 helpers; up to 20 agents at once.

Counts: files 133 (with clauses 91), clauses 305, conflicts yes 98, partial 136, no 71. Delegations: 8 Haiku helpers (one foreground batch). Rows were extracted by Haiku helpers and merged unedited (one secret redaction); verbatim text is not re-checked line by line.

## Top conflicts (read first)
1. `~/.claude/CLAUDE.md` + `<PROJ_ROOT>/CLAUDE.md` + nj-kit manifest/bundled copies: Lead "does small work", workers Haiku-or-Sonnet chosen by the Lead, interpreter on every message. The 2026-10-14 hierarchy (Lead -> Sonnet service lead -> Haiku helpers, foreground batch) sits beside the 2026-10-11 "every worker in the background" rule, so foreground vs background contradicts itself in at least 4 files (global CLAUDE.md l.45 vs l.55, PROJ CLAUDE.md l.44 vs l.90, worker-supervision-standard memory, nj-delegate s0.3a vs s6).
2. `nj-delegate/SKILL.md` s0 (canonical): "workers never delegate" core, worker count = disjoint write-sets, Lead may read and diagnose; s0.3a is the only hierarchy exception. Needs one rewrite; everything else should point at it.
3. `nj-agent-ops/scripts/relay.py`: Opus is a worker escalation target (NEXT_TIER ~l.813, `--ran-on` choices ~l.1024, selftest asserts ~l.858-863); `w2w-delegations` / `nested-spawns` are BREACH (~l.436, 751-756), so any Sonnet->Haiku brief fails `relay.py verify`. No cap-of-20 constant exists anywhere in code; no foreground/background logic in code.
4. `nj-delegate/scripts/check_governance.py`: TIER/EFFORT brief fields (REQUIRED_BRIEF_FIELDS ~l.35) and the no-delegation clause check; the tier set would reject Sonnet-lead rows.
5. PROJ hooks: `<PROJ_ROOT>/.claude/settings.json` UserPromptSubmit interpreter trigger fires on every message and says both "Sonnet interpreter" and "spawn Haiku", and uses SendMessage. `<PROJ_ROOT>/.claude/workflows/srs-consolidate.js` pins every agent to Sonnet, `delegations: 0`, one worker per stage.
6. Polling-by-design in memory: PROJ `haiku-token-time-monitor.md`, `lead-checks-workers-every-5-min.md` (cron watchdog) contradict "agents sleep, triggers only".
7. Lead-does-work rules: nj-wrapup sizing table / "Lead does small work", nj-method "may execute bounded work itself", nj-rank trigger-model (Lead runs nj_rank.py), memory `lead-does-small-work.md`; PROJ-manuals `work-process.md:10` + SKILL.md:779 "Lead alone, zero workers".
8. Git: `~/.claude/projects/*QA-Wrap*/memory/owner-always-merge.md:15` forbids `git push`; the new method makes push/merge a Lead duty. Needs the owner's push policy before rewriting.
9. Brief templates `remake-TEMPLATE-S.md`, `remake-TEMPLATE-LANE.md`, `consolidation/README.md` hardcode Sonnet-only, no Haiku helpers.
10. Sync trap: an edit to `~/.claude/CLAUDE.md` alone does not refresh `nj-kit/bundled/CLAUDE.md` (`export.py --if-changed` returns at ~l.574 before the copy at ~l.617). `<NJ_KIT_ROOT>` and `nj-kit.zip` duplicate 20 skills plus CLAUDE.md and go stale unless re-exported. Side finding: a plaintext TAISCE_TOKEN sits in `<PROJ_ROOT>/.claude/settings.local.json` (value withheld here).

## Canonical-source chain (today)

| Topic | Canonical today | Derived / copies that must follow |
|---|---|---|
| Governance core (roles, workers, counts, tiers, Lead) | `nj-plugin/skills/nj-delegate/SKILL.md` s0 (s0.3a hierarchy, s0.11 owner exception, s0.16 leftovers) | `~/.claude/CLAUDE.md` summary, PROJ CLAUDE.md, nj-kit manifest standing_instructions, nj-method |
| Model ids / effort / Claude Code mechanics | `nj-delegate/reference/runtime-map.md` (the only model table; 20-subagent width) | CLAUDE.md "Standing facts", nj-kit |
| Brief format | `nj-delegate/templates/worker-brief.md` (+ SERVICE-LEAD variant) | `check_governance.py` REQUIRED_BRIEF_FIELDS |
| Transport (results via files, ledger, telemetry, interpreter) | `nj-agent-ops/SKILL.md` + `scripts/relay.py` | `worker-rules.md`, `interpreter-brief.md` |
| Brief clauses + artefact checks | `nj-supervise/SKILL.md` | `worker-brief.md` |
| Per-request method | `nj-method/SKILL.md` (CLAUDE.md steps 1-6 point at it) | |
| Work-log team | `nj-rank/SKILL.md` + `references/trigger-model.md` | CLAUDE.md "Work log" |
| Standing instructions (global) | `~/.claude/CLAUDE.md` | `nj-kit/bundled/CLAUDE.md`, `<NJ_KIT_ROOT>/`, `nj-kit.zip` (export.py) |
| Per-project overrides | each project CLAUDE.md (PROJ is the only large one) | memory `~/.claude/projects/*/memory/*.md` (old dated rules) |
| Interpreter hook | `<PROJ_ROOT>/.claude/settings.json` UserPromptSubmit (PROJ only) | `nj-agent-ops/templates/interpreter-brief.md`, PROJ CLAUDE.md "Sessions and the interpreter" |

## Projects with their own CLAUDE.md

- `~/.claude/CLAUDE.md` (global)
- `<PROJ_ROOT>/CLAUDE.md` (large; delegation, interpreter, monitor, 00:30 budget, parallel lanes)
- `Desktop/ENSERA/CLAUDE.md`, `Desktop/MOA/CLAUDE.md`, `Desktop/QA Engineer/CLAUDE.md`, `Desktop/QA-Wrap/CLAUDE.md`

No AGENTS.md at depth <=3. No `.claude/agents` or `.claude/commands` folders under Desktop (depth <=4). Evalto, Taisce, nj-plugin have no CLAUDE.md. Memory dirs: 11 under `~/.claude/projects/` (PROJ has ~228 files).

## Hooks

| Where | Event | What | Conflicts |
|---|---|---|---|
| `<PROJ_ROOT>/.claude/settings.json:49` | UserPromptSubmit | `echo "INTERPRETER TRIGGER (the owner, 2026-09-17, ALWAYS; Haiku 5.5 since 2026-10-10): ... send its raw text to the session's Sonnet interpreter agent (SendMessage ...; spawn one Agent with model haiku if none is alive) ... No exceptions"` (timeout 10) | yes: every message, peer SendMessage, "Sonnet" vs "haiku" wording |
| `~/.claude/settings.json` | Stop | `nj-kit-sync.sh` (export.py --if-changed --zip) ; `taisce release` | no (but see sync trap, item 10) |
| `~/.claude/settings.json` | SessionStart / PreToolUse(mcp__taisce.*) / statusLine | taisce touch/ensure; `.claude-manager` session-start and statusline taps | no |
| `<PROJ_ROOT>/.claude/settings.json` | SessionStart | `PROJ-tests/tools/doctor.ps1 -Quiet` | no |
| `<PROJ_ROOT>/.claude/settings.json` | Stop | `.claude/hooks/typecheck.sh`; `PROJ-tests/tools/sweep-browsers.ps1` | no |
| `<PROJ_ROOT>/.claude/settings.json` + `PROJ-tests/.claude/settings.json` | SubagentStop | `sweep-browsers.ps1` | no |
| `Desktop/ENSERA/.claude/settings.json` | SessionStart | `scripts/taisce_session.py read` | no |
| global settings.json | enabled plugin | `ponytail@ponytail: true` (SubagentStart context injection) | partial: injects style into every subagent |

There is no UserPromptSubmit hook in the global settings.json, so the interpreter exists only in PROJ sessions.


## Per-file clause tables

### ~/.claude/CLAUDE.md

_Role: Global standing instructions for all projects; canonical pointer to nj-delegate for delegation, plus Owner exception, output style, asking-the owner and finishing rules._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 26 | lead-duties | The main session is the **Lead**: sole orchestrator and decision authority, woken by events (worker complete, blocker, decision, risk), never by progress | partial | Lead as orchestrator fits, but nj-method step 4 has the Lead execute; new method forbids Lead hands-on work. | Lead = Opus 5.5 medium; review, decisions, git push/merge, delivery only; no hands-on work. |
| 29 | hierarchy | Workers own a whole bounded phase, report once, and **never delegate to or instruct each other** | yes | Forbids Sonnet workers running Haiku helpers; contradicts the new tree. | Sonnet worker may run its own Haiku helpers (one level); helpers never spawn; no peer messages. |
| 33 | models | least expensive tier that is reliable (DETERMINISTIC / FREE-LOCAL / ECONOMY / STANDARD / FRONTIER) by the reasoning the stage needs, never its importance. | partial | Five-tier ladder does not map to fixed Opus Lead / Sonnet worker / Haiku helper roles. | Fixed roles: Lead Opus 5.5 medium, workers Sonnet 5.5, helpers Haiku 5.5; drop the tier ladder. |
| 34 | count | **Minimum-sufficient workers for the critical path — zero, one or many; no quota, and useful parallelism is looked for.** | partial | No hard cap; new method sets up to 20 agents at a time. | Cap at 20 concurrent agents (Sonnet workers each with Haiku helpers); count by disjoint write-sets within the cap. |
| 37 | models | Model names live only in `nj-delegate/reference/runtime-map.md`. | partial | Canonical roster lives in a file this group did not read; it may still say Haiku workers. | Point runtime-map at the new roles: Opus Lead, Sonnet workers, Haiku helpers, cap 20. |
| 45 | foreground-background | every worker, builders and editors included, runs in the **background** (`run_in_background: true`) | partial | Background-only for workers clashes with the foreground helper batch on line 55 of the same file. | Workers background; Haiku helper batch under a Sonnet worker stated as one rule, not two. |
| 55 | hierarchy | Tree: Lead (Opus) -> Sonnet service lead per service -> Haiku helpers; a service lead briefs helpers in one FOREGROUND batch and reviews each receipt; helpers never spawn. | partial | Tree matches the new method; FOREGROUND helpers contradict the background rule on line 45. | Sonnet worker runs up to N Haiku helpers in one batch, reviews receipts; pick one background/foreground rule and state it once. |
| 55 | polling | Every agent, the Lead (Opus 5.5) included, sleeps by default; it wakes only on a trigger | no | Trigger-only wake is consistent with the new method. | Keep. |
| 59 | other | Whatever a session starts, it closes before reporting done: browsers and persistent profiles, background commands, subagents, dispatched runs. | no | Subagent cleanup applies equally to Sonnet workers and Haiku helpers. | Keep. |
| 75 | models | nj-rank's team is trigger-only: the Lead (Opus 5.5 medium) sleeps until triggered; Haiku 5.5 workers (up to 20) sleep until briefed and report once. | yes | Workers are Haiku here; new method says Sonnet workers with Haiku helpers. The 20 cap matches. | Lead Opus 5.5 medium review-only; up to 20 agents at once, Sonnet workers each running Haiku helpers. |
| 81 | models | the Lead is Opus 5.5 at effort medium; workers are Sonnet 5.5 and Haiku 5.5, and the Lead decides per stage which one and which effort | yes | Lead picks worker model per stage and does stage work; new method fixes Sonnet workers and Haiku helpers. | Lead Opus 5.5 medium, no hands-on work; Sonnet 5.5 workers each run Haiku 5.5 helpers; cap 20. |
| 81 | models | Haiku (`model: "haiku"`) for mechanical/bounded work (Jira sync, image logging, report builds + gates, non-filing runs, probes, sweeps, the interpreter), Sonnet for diagnosis, fixes, authoring, live filing. | partial | Haiku-for-mechanical fits helpers; Sonnet-for-diagnosis and fixes must sit in workers, not the Lead. | Mechanical work to Haiku helpers under a Sonnet worker; diagnosis and fixes to Sonnet workers; Lead decides only. |
| 81 | budgets | a failed verifier escalates the stage one tier once (haiku → sonnet → opus) via `relay.py route --failed … --ran-on <model>` | partial | Escalation to Opus would put execution on the Lead, which is review-only under the new method. | Escalate helper to Sonnet worker once; Lead reviews the result, never re-runs it. |
| 174 | models | a failed verifier moving the stage to Opus 5.5 once via `relay.py route --failed` is not a retry | partial | Same Opus-escalation conflict as line 81; the Lead must not do the stage. | Escalation target is a Sonnet worker, not the Lead. |

### ~/.claude/hooks/nj-kit-sync.sh

_Role: Stop-hook script: runs nj-kit export.py --if-changed --zip and reports via systemMessage. Not canonical for agent roles._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 23 | hooks | out=$(python "$KIT/scripts/export.py" --if-changed --zip --quiet 2>&1) | partial | Sole automatic sync trigger; no path for a CLAUDE.md-only change. | Also trigger a full export when ~/.claude/CLAUDE.md differs from bundled/CLAUDE.md. |

### ~/.claude/projects/c--Users-<user>-Desktop-ENSERA/memory/director-only-and-permanent-interpreter.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 13 | lead-duties | The director (Lead) does not execute the work itself | no | Matches v4 Lead rule. | Keep; make universal. |
| 16 | interpreter | One ECONOMY-tier interpreter per session, spawned on a trigger | partial | Interpreter tier named; v4 has no interpreter. | Drop or fold into Haiku helper tier. |
| 24 | hierarchy | Workers report once, at the end, and never brief each other. | no | Matches v4 no-delegation rule. | Keep. |

### ~/.claude/projects/c--Users-<user>-Desktop-ENSERA/memory/lead-plus-workflows.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 11 | lead-duties | the Lead orchestrates through **background Workflows**, never its own reading | no | Matches v4 Lead rule and background launch. | Keep. |

### ~/.claude/projects/c--Users-<user>-Desktop-ENSERA/memory/learning-router-escalation.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 14 | models | ≥5 sonnet rows: first-pass <60% → start opus | yes | Starts workers on Opus; v4 keeps Opus for the Lead only. | Start Sonnet; route failures to Lead review. |
| 15 | models | ESCALATE opus once for CAPABILITY_LIMIT / IMPLEMENTATION_DEFECT / TEST_FAILURE | yes | Escalates a worker to Opus. | Escalate to Lead, not an Opus worker. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/agents-sonnet-only.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 8 | models | Sonnet 5.5 and Haiku 5.5 are the working agents; Opus decides which and what effort. | yes | Lead picks model per stage; v4 fixes workers to Sonnet with Haiku helpers. | Workers are Sonnet 5.5 agents; helpers Haiku 5.5; no per-stage model picking. |
| 11 | models | a failed verifier escalates one tier once (haiku → sonnet → opus) | yes | Escalates a worker to Opus; v4 gives Opus only to the Lead. | On a failed verifier, escalate to Lead review, not an Opus worker. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/blocked-after-two-failures.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 11 | budgets | no third attempt in that session. Also: AR and EN run in parallel per service, and workers never loop | no | Loop cap is consistent with budget ceilings. | Keep. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/director-managerial-workers-report-once.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 10 | lead-duties | I want the director (Opus) to only do the managerial work, and the agents not to report after each step | no | Matches Lead-no-hands-on and report-once. | Keep. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/director-token-discipline.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 33 | models | Opus by default — 2,142 of 2,664 worker calls. | no | Historical evidence for keeping Opus out of workers. | Keep as evidence; no Opus workers. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/errors-two-questions-then-skip.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 12 | budgets | one fix attempt → `QUESTION n/2:` in the result JSON and end the turn | partial | Line 12 says one fix attempt; line 14 replaced it with a budget cap. | Keep only the budget-and-progress cap; QUESTION to Lead, two per worker. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/governance-v4-method.md

_Role: RULE 2026-10-16 (all projects): Lead Opus 5.5 medium only reviews/decides/pushes/merges; Sonnet 5.5 agents each run multiple Haiku 5.5 helpers; up to 20 agents at once._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 8 | lead-duties | **Lead** = Opus 5.5, effort medium — reviews, decides, git push/merge, delivery. No hands-on work. | no | This is the target method. | Canonical; write into nj-delegate section 0. |
| 9 | models | **Workers** = Sonnet 5.5 agents; each runs multiple **Haiku 5.5 helpers**. | no | Target method. | Keep. |
| 10 | count | All together up to **20 agents at a time** (ceiling). | no | Target ceiling. | Keep as ceiling, not target. |
| 13 | other | supersedes [[lead-does-small-work]] and the "minimum-sufficient / zero workers" default of [[nj-governance-v3]] | no | States v4 replaces the zero-worker default. | Keep; update nj-governance-v3 to match. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/haiku-token-time-monitor.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 12 | polling | the Haiku agent only runs it and waits (one Monitor/wait call per cycle) | yes | A Haiku agent waiting in cycles is polling; v4 forbids polling. | Script on cron or stall trigger only; no agent waits. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/lead-checks-workers-every-5-min.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 8 | polling | Rule: the Lead checks every running agent every 5 min itself | yes | Lead polls on a cron; v4 and trigger rule say Lead never polls. | Watchdog script alerts on stall only; Lead wakes on completion or stall trigger. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/lead-decides-no-questions.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 8 | lead-duties | The Lead picks the option itself (the one it would have marked Recommended), acts, and states the choice in one line | no | Lead as decision authority matches v4. | Keep. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/lead-does-small-work.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 11 | lead-duties | the Lead does reading, diagnosis and tiny edits itself. Builds, rebuilds, gate runs and multi-file work go to background Sonnet workers. | yes | Lets Lead do hands-on reading and edits; v4 says Lead does no hands-on work. | Lead does no reading, diagnosis or edits; route every such step to a Sonnet agent. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/lead-free-background-only.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 8 | foreground-background | Every worker, including builders, runs with run_in_background: true. The Lead never waits on a foreground agent, never polls | no | Background-only is consistent with v4; nothing contradicts it. | Keep; apply to Haiku helpers too or state the exception. |
| 12 | foreground-background | A worker reports once and its completion is the trigger (receipt + <=25 lines, task-notification wakes the Lead); never polls | no | Trigger method matches v4 reporting. | Keep as global rule. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/lead-never-works-sanad-individual-only.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 11 | lead-duties | the Lead is a director/manager only, waiting for his prompts; Sonnet workers do all the work; the Lead only reviews | partial | Same as above; no Haiku helper tier. | Add Haiku helper tier under Sonnet agents. |
| 13 | count | 2–3 Sonnet workers in parallel: service lanes share the portal through | partial | Parallel cap of 2-3 versus v4 ceiling of 20; portal lock is a real limit. | Count by disjoint write-sets and shared-resource locks, ceiling 20. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/lead-never-works-workers-background.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 11 | lead-duties | The Lead (main session) never does the work itself. Sonnet workers do every piece of work; the Lead briefs, stays free | partial | Lead-no-work matches v4; omits Haiku helpers under each Sonnet agent. | Lead does review, decisions, push/merge, delivery; Sonnet agents run Haiku helpers. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/lead-plus-workflows-standard.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 17 | foreground-background | launch Workflows in the background (Map lanes with one report file each | no | Background launch matches v4. | Keep. |
| 20 | interpreter | ONE standing Haiku interpreter per session kept alive with SendMessage, never respawned per message | partial | Interpreter role absent from v4; standing agent conflicts with trigger-only sleep. | Drop the standing interpreter, or make it one Haiku helper under a Sonnet agent. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/nj-governance-v3.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 14 | count | read §0 before any brief; brief from `templates/worker-brief.md` | partial | v3 derives count from disjoint write-sets; v4 adds a 20-agent ceiling. | Adopt v4 count rule in section 0; keep relay telemetry gates. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/no-cross-session-and-interpreter.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 8 | interpreter | A Haiku interpreter (nj-agent-ops §4) sits between the owner and the director | partial | Interpreter layer absent from v4; Lead should take the owner prompts directly. | Decide once: keep as a Haiku helper or drop; Lead stays free for the owner. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/parallel-lanes-per-service.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 8 | count | the owner 2026-10-01 asked for 2 agents per service (one per language), 2 services at a time | partial | Per-service count fixed at 2; v4 counts by write-set, ceiling 20. | Count lanes by disjoint write-sets; ceiling 20; no support agents. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/progress-table-at-start-and-finish.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 12 | interpreter | A Haiku interpreter summarises the owner's messages first | partial | Relies on the interpreter layer v4 does not define. | Lead writes the table itself from stage-time medians. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/sonnet-only-agents.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 8 | models | from now on only use sonnet 5.5 agents to work | yes | Marked superseded but still live; bans Haiku helpers. | Delete or archive the file; v4 allows Haiku helpers. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/thirty-minute-hard-budget.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 3 | budgets | every user-manual dispatch has a hard 00:30 clock (blocked at 00:12 without SEND OK, no third send cycle | partial | Hard clock vs v4 budgets as ceilings and loop detectors, not targets. | Express as a per-service ceiling with a stall trigger, not a hard clock. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/trigger-only-agent-hierarchy.md

_Role: HARD RULE 2026-10-14: agents sleep, wake only on triggers, report once upward; canonical is nj-delegate SKILL.md s0.3a._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 6 | hierarchy | Tree: Lead -> Sonnet service lead per service -> Haiku helpers | partial | v4 has Sonnet agents running Haiku helpers; no per-service lead tier. | Lead -> Sonnet agent (ceiling 20) -> Haiku helpers; drop the per-service lead tier. |

### ~/.claude/projects/c--Users-<user>-Desktop-PROJ/memory/worker-supervision-standard.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 20 | foreground-background | writes, an explicit stall bound, foreground-only, budgets as ceilings not | yes | Says foreground-only; contradicts the 2026-10-11 background-only rule. | Replace with background-only and completion-as-trigger. |

### ~/.claude/projects/c--Users-<user>-Desktop-QA-Wrap/memory/agents-sonnet-only.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 12 | models | every Agent / workflow agent() call passes model "sonnet" — no FRONTIER/Opus workers | partial | Sonnet-only, no Haiku helpers; v4 adds them. | Sonnet agents plus Haiku helpers; Lead Opus medium. |

### ~/.claude/projects/c--Users-<user>-Desktop-QA-Wrap/memory/owner-always-merge.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 11 | git | merge it into `main` locally with `--no-ff` without stopping to ask | partial | Merge rule is fine for Lead; v4 makes merge a Lead duty without ask. | Lead merges (no-ff) per v4. |
| 15 | git | still never push, publish or upload | yes | v4 lists git push as a Lead duty; this forbids push. | Confirm push policy with the owner once; the two rules disagree. |

### ~/.claude/projects/c--Users-<user>-Desktop-QA-Wrap/memory/owner-decisions-delegated.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 11 | lead-duties | as for Needs the owner you pick what's best for best practice | no | Lead decides forks; matches v4. | Keep. |

### ~/.claude/projects/c--Users-<user>-Desktop-QA-Wrap/memory/owner-only-important-work.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 17 | count | one worker runs the remaining stages end to end with a single final report | partial | Single-worker mode under budget pressure; v4 has no quota. | Keep as budget-exhaustion mode only. |

### ~/.claude/projects/c--Users-<user>-Desktop-QA-Wrap/memory/owner-opus-director.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 13 | models | and he can generate another Opus if he wanted, and Sonnet and Haiku. | yes | Allows Opus workers; v4 has Opus only as Lead (note: file says superseded by nj-governance-v3). | Remove; no Opus workers. |
| 17 | models | It may spawn further Opus workers at its own judgement | yes | Same conflict: Opus workers chosen by Opus. | Workers Sonnet, helpers Haiku; Opus Lead only. |

### ~/.claude/projects/c--Users-<user>-Desktop-QA-Wrap/memory/owner-token-sensitivity.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 15 | budgets | Default to the cheap route: no workers, no photo/asset hunting | partial | Zero-worker default vs v4 count by write-sets, ceiling 20. | Count by write-sets; keep one-estimate rule. |

### ~/.claude/projects/c--Users-<user>-Desktop-QA-Wrap/memory/subagent-interrupt-resume.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 14 | other | Guard every stage brief with a FOCUS RULE line at the very top | no | Matches the FOCUS line rule in the trigger method. | Keep. |

### ~/.claude/projects/c--Users-<user>-Desktop-QA-Wrap/memory/workers-no-destructive-git.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 8 | git | stage and commit only the worker's own files, by path. | no | Compatible with v4 worker briefs. | Keep in every worker brief. |

### ~/.claude/settings.json

_Role: Global Claude Code settings: model default, effort, model settings, hooks, plugins, marketplaces, status line. Not canonical for agent roles._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 1 | hooks | Stop: bash "~/.claude/hooks/nj-kit-sync.sh" (timeout 120, statusMessage Syncing nj-kit) | no | Deterministic nj-kit export on Stop; no agent behaviour. | none |
| 1 | hooks | Stop: "~/.local/bin/taisce.cmd" release -SessionId "$sid" (timeout 30) | no | Taisce stack release on Stop; no agent behaviour. | none |
| 1 | hooks | SessionStart (matcher empty): node.exe .claude-manager/session-start-tap.js (script not read by this group) | no | Session tap; script outside this group, so its content is unverified. | Check the tap script separately. |
| 1 | hooks | SessionStart: taisce.cmd touch -SessionId "$sid" (timeout 5, statusMessage taisce: fast check) | no | Taisce heartbeat at session start. | none |
| 1 | hooks | PreToolUse (matcher mcp__taisce.*): taisce.cmd ensure -SessionId "$sid" (timeout 300) | no | Brings taisce up on first taisce MCP call; a 300 s wait inside a tool call. | none |
| 1 | hooks | statusLine: node.exe .claude-manager/statusline-tap.js | no | Status line; script not read by this group. | none |
| 4 | models | "model": "opus", | partial | Unpinned alias; the Lead's model and effort are not pinned to Opus 5.5 medium here. | Pin Lead to claude-opus-5-5 at medium effort in this file or the Lead session. |
| 84 | hooks | "ponytail@ponytail": true | partial | Observed in runtime context: a SubagentStart hook injects a 'lazy developer' persona (PONYTAIL MODE ACTIVE) into every subagent, incl. Haiku helpers. Plugin file not read. | Confirm the injection is wanted for helper briefs, or disable it for worker and helper roles. |
| 154 | models | "effortLevel": "low", | partial | Global default low; conflicts with Lead medium unless modelSettings overrides it. | Default low for helpers; Lead medium via modelSettings; workers' effort set per stage. |
| 155 | models | "claude-sonnet-5-5": { "effortLevel": "high" } | partial | Sonnet workers pinned to high effort for every stage; no Haiku entry at all. | Sonnet effort set per stage by Lead; add a Haiku entry (low) for helpers. |
| 172 | other | "crossSessionInbound": "refuse", | no | Refuses inbound messages from other sessions; matches the never-talk-to-another-session rule. | none |

### ~/.claude/skills/nj-kit/SKILL.md

_Role: SKILL.md: kit guide. Section 'Least-cost execution and delegation' (lines 323-341) is a pointer to nj-delegate section 0, not a copy._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 326 | hierarchy | workers own a bounded phase, report once and never delegate to or instruct each other | yes | Forbids Sonnet agents from instructing Haiku helpers; new method needs that. | Sonnet agent may brief its own Haiku helpers; helpers never spawn. |
| 330 | count | minimum-sufficient workers for the critical path - zero, one or many, no quota - with useful parallelism looked for | yes | No quota; new method sets a 20-agent ceiling. | Cap 20 concurrent agents, count stated per batch. |
| 337 | foreground-background | Every worker, builders and editors included, is dispatched in the background | partial | Fits Sonnet agents; Haiku helper batches run foreground inside them. | State both: Sonnet agents background, helper batches foreground. |
| 393 | hooks | \| Standing instructions \| `bundled/CLAUDE.md` \| `install.py` (never overwrites a differing file) \| | partial | Lists the bundled copy as the place; the live source is ~/.claude/CLAUDE.md. | Name ~/.claude/CLAUDE.md as source and bundled/CLAUDE.md as its export copy. |

### ~/.claude/skills/nj-kit/manifest.json

_Role: manifest.json: generated skills roster by export.py; hand-maintained house_style, tooling, standing_instructions and skill_notes. Not canonical for agent policy; points to nj-delegate section 0._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 69 | other | nj-delegate/SKILL.md section 0, INSTALLED and live since 2026-09-22. Every clause carries [GATE: <script>] or [HABIT]; check_governance.py --tally derives the counts (12 gates, 4 habits) | partial | Names nj-delegate section 0 as canonical; that text carries the old v3 model and foreground rules. | Re-point canonical to the new Lead-review / Sonnet-agent / Haiku-helper statement; regenerate tally. |
| 85 | lead-duties | Before spawning a worker, prefer deterministic scripts/CLI/tests/parsers/static analysis/git; then existing artefacts or prior evidence; then a bounded targeted Lead check. | partial | Lead does a bounded hands-on check; new method says Lead does no hands-on work. | Lead never checks hands-on; deterministic first, then hand the check to a Sonnet agent. |
| 87 | models | Tier names are the policy; which runtime serves a tier is workspace mapping, kept out of the policy in nj-delegate/reference/runtime-map.md (2026-09-16). | partial | Five-tier policy does not match a two-model roster (Sonnet agents, Haiku helpers). | Replace tiers with roles: Lead Opus medium, Sonnet agent, Haiku helper. |
| 92 | models | FRONTIER: Ambiguity, architecture, hard root cause, security, production- or data-sensitive change, complex orchestration, high-risk adjudication. | partial | FRONTIER is the Opus tier for workers; new method reserves Opus for the Lead only. | Drop FRONTIER for workers; Lead Opus handles adjudication only. |
| 98 | count | nj-delegate is the single source of truth for worker count: minimum-sufficient for the critical path, set per batch by FIT | yes | Worker count by fit with no ceiling; new method caps concurrent agents at 20. | Cap 20 concurrent agents (Sonnet), each with Haiku helpers; state count per batch. |
| 100 | count | nj-agent-ops is optional script mode. It inherits the nj-delegate count rule (no cap of its own), | yes | Explicitly no cap; conflicts with a 20-agent ceiling. | Inherit the 20-agent ceiling and name it here. |
| 103 | budgets | Budgets are tokens and context, never tool calls | partial | Class budgets keyed to FRONTIER/Opus; new roster needs Sonnet and Haiku budgets. | Budget per Sonnet agent and per Haiku helper; drop FRONTIER class budget. |
| 104 | models | Never the same prompt again, never an automatic tier escalation (only CAPABILITY_LIMIT, in writing), never another worker because the first failed. | yes | Contradicts the one-time haiku->sonnet->opus escalation on a failed verifier (manifest line 163). | Allow one escalation per stage on a failed verifier, as the models clause states. |
| 109 | foreground-background | A worker never ends its turn while its own background work (a recorder, a monitor) is still running - foreground waits only. | partial | Foreground-only waits clash with background dispatch in SKILL.md line 337. | A worker waits inside its own turn; Sonnet agents run background, Haiku batches foreground inside them. |
| 110 | polling | a ~12-wake director storm in 3 minutes from agents ending turns on background monitors | no | Rationale for no background monitors; still consistent with trigger-only. | Keep as is. |
| 112 | lead-duties | Runtime mapping is a workspace fact, not policy: see nj-delegate/reference/runtime-map.md (Lead and tier->runtime table, chosen at the top of a session and never switched mid-session). | partial | Lead runtime table must now list Opus medium Lead and Sonnet/Haiku roles. | Update runtime-map to Lead Opus medium, Sonnet agent, Haiku helper. |
| 113 | foreground-background | a worker that builds or edits runs in the FOREGROUND, so he can watch it and his messages cannot kill or derail it mid-phase | yes | Foreground builders contradict background-for-all dispatch (SKILL.md line 337, 2026-10-11). | Sonnet agents background (completion is the trigger); Haiku helper batch foreground inside them. |
| 163 | models | Lead = Opus 5.5 at effort medium; workers = Sonnet 5.5 and Haiku 5.5, the Lead decides per stage which model and effort (Haiku: mechanical/bounded work and the interpreter; Sonnet: diagnosis, fixes, authoring, live runs). | yes | Lead picks per-stage model and effort; new method: Lead does only review, decisions, git, delivery; Sonnet owns diagnosis and fixes. | Lead Opus medium reviews only; Sonnet agents (max 20) own stages; Haiku helpers under them. |
| 166 | hierarchy | HARD RULE (the owner, 2026-10-14): agents sleep by default, wake only on a parent's brief or a child's completion, report once upward (receipt + <=25 lines) | partial | Tree matches new method; needs 20-agent cap, Lead no-hands-on, and naming (service lead vs Sonnet agent). | Keep trigger rule; rename service lead to Sonnet agent; add 20 cap and Lead review-only. |
| 639 | hooks | "file": "~/.claude/CLAUDE.md", | no | Names the live CLAUDE.md as the file; no hash or export date is recorded. | Record a hash and export date so drift shows. |
| 663 | other | 2026-09-20: section 0 = NJ Governance v3, the one canonical orchestration statement; scripts/check_governance.py is its gate. | partial | Points canonical statement at nj-delegate section 0 (see line 69). | Update together with nj-delegate section 0. |
| 676 | foreground-background | holds the orchestration rules proven that day (background workers + AMEND | no | Background workers, consistent with SKILL.md line 337. | Keep; align with the new Sonnet background rule. |

### ~/.claude/skills/nj-kit/scripts/export.py

_Role: scripts/export.py: writes manifest.json and bundled/, including the copy of ~/.claude/CLAUDE.md at lines 617-619. Source of truth for standing instructions is ~/.claude/CLAUDE.md._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 38 | hooks | SKILLS = KIT.parent | partial | newest_content scans only ~/.claude/skills, so edits to ~/.claude/CLAUDE.md are invisible to the Stop hook. | Add the CLAUDE.md mtime or hash to the stamp. |
| 574 | hooks | and manifest.get("synced_content_mtime") == stamp | partial | --if-changed returns before the CLAUDE.md copy at lines 617-619, so bundled/CLAUDE.md goes stale. | Compare CLAUDE.md too, or copy it before the early return. |
| 617 | hooks | claude_md = Path.home() / ".claude" / "CLAUDE.md" | partial | Copy runs only on a full export; the Stop hook never reaches it unless a skill changed. | Run the copy on every sync and report drift. |

### ~/.claude/skills/nj-kit/scripts/install.py

_Role: scripts/install.py: apply_standing_instructions copies bundled/CLAUDE.md to ~/.claude/CLAUDE.md only when absent (lines 498-535)._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 506 | hooks | An existing CLAUDE.md is never overwritten - it may hold the user's own notes. | partial | A machine that already has a CLAUDE.md never gets the kit's new version. | Show the diff against bundled/CLAUDE.md and offer the update. |

### ~/Desktop/ENSERA/.claude/settings.json

_Role: ENSERA project settings: one SessionStart hook reading taisce. Not canonical for agent roles._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 8 | hooks | SessionStart: PYTHONUTF8=1 python scripts/taisce_session.py read \|\| true (timeout 60) | no | Taisce read at session start; no agent behaviour. Bare python here, not uv. | none (uv rule covers packages, not script runs). |

### ~/Desktop/ENSERA/CLAUDE.md

_Role: ENSERA project rules (338 lines). Defers to nj-delegate §0 for Delegation; canonical for ENSERA KB gates and publication wait._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 147 | hierarchy | the director is the Lead and sole orchestrator; workers own a bounded phase, report once and never spawn, brief or instruct each other | yes | Workers never spawn; new method has Sonnet spawning Haiku helpers | Sonnet workers may spawn Haiku helpers within the 20-agent cap |
| 155 | count | minimum-sufficient workers for the critical path — zero, one or many, no quota (count by fit: context headroom, machine and rate capacity, quality needed) | partial | No quota; new method caps at 20 agents | Cap at 20 live agents; count by fit below it |
| 157 | models | The director's runtime is fixed for the session — no model switching; runtimes per tier live in `nj-delegate/reference/runtime-map.md`. | no | Lead fixed on Opus; matches new method | Keep; name Opus 5.5 medium explicitly |
| 160 | models | Tier by reasoning type (nj-delegate §3): DETERMINISTIC for scripts and gates, ECONOMY for extraction/discovery/triage and the interpreter, STANDARD for authoring, implementation and scoring, **FRONTIER for judgement stages** | yes | FRONTIER means Opus workers; new method workers are Sonnet and Haiku only | Judgement stages go to a Sonnet worker, or to the Lead when it is a decision |
| 163 | lead-duties | the director **does not execute the work itself** (the owner 2026-09-17) — stricter than the v3 core (`nj-delegate` §1 step 2) | no | Lead does no hands-on work; matches new method | Keep; add that Lead delivers and pushes git |
| 181 | models | Routing: run `relay.py route <project> --class <task-class>` before writing a brief and put its START line in the brief's TIER line; ... `--escalations 1` | partial | Routing learns model per stage; new method fixes Sonnet workers and Haiku helpers | Route only to Sonnet or Haiku; escalation Haiku to Sonnet only |
| 194 | models | Tier + effort + budget line: `Tier: <tier> because <reasoning type>; effort: <level>; budget: uncached input ≤ N, output ≤ M, model calls ≤ K` | partial | Effort per worker not in new method; tier names are the old ladder | Name model (Sonnet or Haiku) and budget; effort only if Lead sets it |
| 210 | hierarchy | v3: the line `Governance: nj-governance-v3`, owned write paths (single writer), a stall bound, the **no-delegation clause** (`delegations: 0` in the receipt) | yes | Requires delegations 0; new method allows Sonnet to run Haiku helpers | Receipt reports helper count instead of requiring zero |
| 215 | lead-duties | The director never reads source files or the KB body, renders pages or images, or re-derives a worker's numbers. | partial | Lead reviews only; reading source for review may be needed | Lead reads receipts and diffs only; source review goes to a Sonnet worker |
| 223 | interpreter | The interpreter is called on a trigger. One nj-agent-ops interpreter (ECONOMY tier) is spawned the first time a message from the owner is long, mixes Arabic and English, or changes a brief already running | partial | Conditional interpreter; new method names no interpreter; counts toward cap | Interpreter (Haiku) counts inside the 20-agent cap, or is dropped |
| 230 | models | **Worker tier is chosen by what the task requires** — ECONOMY for interpreting, triage and extraction; STANDARD for authoring, implementation and scoring; FRONTIER for judgement | partial | Tier chosen per task, FRONTIER is Opus; new method: Sonnet workers, Haiku helpers | Lead assigns Sonnet or Haiku by task; no Opus workers |

### ~/<PROJ_ROOT>/.claude/settings.json

_Role: PROJ workspace hooks: doctor at SessionStart, typecheck and browser sweep at Stop and SubagentStop, interpreter trigger on UserPromptSubmit. Not canonical for agent roles._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 8 | hooks | SessionStart: pwsh -NoProfile -File <PROJ_ROOT>/PROJ-tests/tools/doctor.ps1 -Quiet (timeout 30, Toolchain doctor) | no | Toolchain check at session start; no agent behaviour. | none |
| 21 | hooks | Stop: bash "<PROJ_ROOT>/.claude/hooks/typecheck.sh" (timeout 120, Typechecking PROJ-tests) | no | Deterministic npm typecheck after each turn; a gate, not Lead hands-on work, but it runs on the Lead's turn. | Keep; confirm it stays a hook, not a Lead step. |
| 28 | hooks | Stop: powershell -NoProfile -File "<PROJ_ROOT>/PROJ-tests/tools/sweep-browsers.ps1" (timeout 60) | no | Sweeps stray Playwright Chrome on Stop; leftover rule. | none |
| 41 | hooks | SubagentStop: powershell -NoProfile -File "<PROJ_ROOT>/PROJ-tests/tools/sweep-browsers.ps1" (timeout 60) | no | Sweeps browsers on every subagent stop; consistent with leftover rule. | none |
| 54 | interpreter | send its raw text to the session's Sonnet interpreter agent (SendMessage to the live interpreter; spawn one Agent with model haiku if none is alive) | yes | Text says Sonnet then Haiku; uses SendMessage peer messaging; interpreter sits outside the agent tree and cap. | One Haiku interpreter per session, model stated once; count it inside the 20 cap; no peer messaging, parent-child brief only. |

### ~/<PROJ_ROOT>/.claude/settings.local.json

_Role: Local PROJ overrides: TAISCE_TOKEN env, taisce MCP enabled, outputStyle Concise. Not canonical for agent roles._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 3 | other | "TAISCE_TOKEN": <value present in plaintext; withheld from this fragment> | no | Not agent config; a credential sits in plaintext in a settings file. | Move the token to a secrets file or the environment, outside settings. |

### ~/<PROJ_ROOT>/.claude/workflows/srs-consolidate.js

_Role: Workflow script for end-of-batch SRS consolidation: collect, root cause, devil, 5-POV panel, builder. Canonical for that stage order only._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 7 | count | { title: 'Root cause', detail: 'one worker per run' } | partial | Hardcoded one worker per stage; the count should come from write-sets within the cap of 20. | Count by disjoint write-sets from routing; cap 20. |
| 15 | models | Every agent is Sonnet (project rule). Agents read prompt files; this script only routes and tallies. | yes | Pins all agents to Sonnet; mechanical steps should be Haiku helpers under a Sonnet lead. | Sonnet lead per stage; mechanical collect and marker steps as Haiku helpers. |
| 18 | hierarchy | delegations: 0 (never spawn, brief or instruct another agent) | yes | Forbids the Sonnet-to-Haiku tree the new method needs. | Allow one level: Sonnet may brief Haiku helpers; helpers never spawn. |
| 19 | models | const M = { model: 'sonnet' } | yes | One constant pins every agent, including effort-low mechanical calls. | Model passed per stage from Lead routing, not a constant. |
| 78 | models | { ...M, schema: COLLECT, effort: 'low', label: 'read inventory' } | yes | Mechanical read run on a Sonnet agent; Haiku helper is the cheap tier. Same for collect and advance-marker calls (lines 81, 95). | Haiku helper under the Sonnet lead for mechanical reads and writes. |
| 111 | count | const panel = await parallel(POVS.map(pov => () => | partial | Five parallel panel agents hardcoded; fine under 20, but not derived from routing. | Panel width from routing, within the cap of 20. |

### ~/<PROJ_ROOT>/CLAUDE.md

_Role: PROJ project rulebook (455 lines). Canonical for project exceptions to nj-delegate v3; the rest defers to nj-delegate §0._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 15 | models | Agents (the owner, 2026-10-10): the Lead is this session, Opus 5.5 at effort medium; workers are Sonnet 5.5 and Haiku 5.5 and the Lead picks the model and effort per stage (Haiku: mechanical/bounded stages and the interpreter; Sonnet: diagnosis, lib fixes, spec building, filing runs) | yes | Lead chooses worker model per stage; new method fixes workers to Sonnet, Haiku only as helpers | Workers are Sonnet 5.5; each runs Haiku 5.5 helpers; no per-stage model choice by Lead |
| 15 | models | one escalation on a failed verifier (haiku → sonnet → opus). | yes | Escalates a worker to Opus; new method workers are never Opus | Escalate Haiku to Sonnet only; Opus stays Lead-only |
| 17 | hierarchy | the director is the Lead and sole orchestrator; workers never delegate to or instruct each other (artefact by path, through the Lead) | yes | Forbids workers delegating; new method has Sonnet workers run Haiku helpers | Sonnet worker may delegate to its own Haiku helpers; peers still exchange via Lead |
| 20 | count | minimum-sufficient workers for the critical path — zero, one or many, no quota (the owner, 2026-09-16 18:55: count by FIT — context headroom, machine/rate capacity, quality needed) | partial | No fixed cap; new method sets up to 20 agents at a time | Cap all live agents at 20 (Sonnet + Haiku together); count by fit below that |
| 29 | count | worker count = disjoint write-sets, claimed at runtime via `relay.py claim` | yes | Worker count by write-sets only; new method counts agents by a 20 cap | Agent count capped at 20; write-set disjointness is a safety check, not the count |
| 33 | models | Tier by `nj-delegate` §3 (lowest-cost tier that is good enough + effort): DETERMINISTIC → existing evidence → ECONOMY → STANDARD → FRONTIER | partial | Five-tier ladder; new method only Sonnet (workers) and Haiku (helpers) plus Opus Lead | Two worker models: Sonnet for workers, Haiku for helpers; drop FRONTIER tier |
| 40 | lead-duties | **This project's named exceptions to the v3 core** ... director managerial only (below) · the 00:30 hard budget per service · interpreter on every message · the monitor cadence · run-once / the owner verifies manually. | partial | Director managerial-only overlaps new Lead-only-review; interpreter clause conflicts | Lead does review, decisions, git push/merge, delivery; no hands-on work |
| 44 | hierarchy | Tree: Lead (Opus) -> Sonnet service lead per service -> Haiku helpers; a service lead briefs helpers in one FOREGROUND batch and reviews each receipt; helpers never spawn. | partial | Tree matches new method; foreground helper batch clashes with background-only rule at line 90 | Keep tree; Sonnet worker and its Haiku helpers in background or foreground by one rule, stated once |
| 44 | hierarchy | HARD RULE (the owner, 2026-10-14): agents communicate and report only by triggers, in a hierarchy. ... Lead ... sleeps by default; it wakes only on a trigger | no | Consistent with Lead-events model; no change needed beyond tree size | Keep; add 20-agent cap and Lead-only-review wording |
| 64 | hierarchy | the **no-delegation clause** (never spawn, brief or instruct another worker — artefact + path, the director decides; receipt carries `delegations: 0`) | yes | Forbids any worker spawning; new method has Sonnet spawning Haiku helpers | Replace with: Sonnet may spawn Haiku helpers in one batch; receipt reports helper count |
| 90 | foreground-background | **Every worker runs in the background (`run_in_background: true`) and its completion is the trigger** (the owner, 2026-10-11; supersedes the 2026-09-29 foreground rule) | yes | Background-only for all workers; line 44 requires foreground helper batch | Choose one rule for the whole tree: all Sonnet workers background, Haiku helpers foreground inside them |
| 99 | lead-duties | **Director is managerial only** (the owner, 2026-09-16 19:05/20:15): analyse, brief, adjudicate a QUESTION, read one gate line per result, report the table. Never runs gates, extracts frames, delivers, polls logs, edits flows | yes | Says Lead never delivers; new method has Lead doing delivery and git push | Lead does review, decisions, git push/merge, delivery; no gates or source edits |
| 111 | lead-duties | **Director token discipline** — `nj-delegate` §11 and §10 (batch the fixes, build once); read before briefing any worker in this repo. | no | Cost discipline; no agent-role conflict | Keep |
| 116 | other | ## Never leave leftovers ... Every browser ... background command, subagent and dispatched run is closed by the session that started it | no | Cleanup duty; compatible with 20-agent cap | Keep |
| 127 | other | **Never communicate with another Claude session** (SendMessage, or writing into a peer-shared file ...) unless the owner says so | no | Cross-session ban; does not restrict intra-tree messages | Keep; intra-tree AMEND via SendMessage stays allowed |
| 133 | interpreter | **The interpreter runs on every message, no exceptions — Haiku 5.5 since 2026-10-10 (Lead's choice; was Sonnet 2026-09-29)** | yes | Per-message interpreter agent; new method names no interpreter and caps agents at 20 | Drop the per-message interpreter or count it inside the 20-agent cap |
| 142 | polling | The Haiku monitor agent runs briefly only — on the owner's "refresh", or at each service start/finish — never continuously, no polling | no | Monitor is Haiku and event-triggered; consistent with trigger-only rule | Keep; counts toward the 20-agent cap |
| 152 | budgets | ## 00:30 hard budget per service ... The director never extends a dispatch; new information = a new 00:30 dispatch. | no | Time budget per service; no agent-count or model conflict | Keep as project exception |
| 391 | count | Two services staggered ... no support agents. Sign-ins: `portal.lock` + ≥ 3 min spacing; start at 2 concurrent recordings, 4 only after a batch with zero refusals. | partial | Says no support agents; caps concurrent recordings at 2 or 4, not 20 agents | Allow Haiku helpers within 20-agent cap; keep recording concurrency as a browser-level limit |
| 393 | lead-duties | per service one structure worker S does steps 1–6 (sole writer of `flow.ts`), then an AR worker and an EN worker do 7–9 in parallel ... the Lead runs step 10 | partial | Lead running delivery matches new method; no-support-agents clause conflicts | Keep S, AR, EN workers as Sonnet; each adds Haiku helpers; Lead delivers only |

### ~/<PROJ_ROOT>/ENSERA/.claude/skills/nj-design/SKILL.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 87 | models | \| logo / character concept direction \| FRONTIER (taste + meaning; no per-batch cap, own budget line — nj-delegate §0), then STANDARD execution \| | partial | Uses FRONTIER/STANDARD tiers, not Opus/Sonnet/Haiku; Lead tier choice implied. | Map tiers to Sonnet worker and Haiku helper; Lead picks per stage. |

### ~/<PROJ_ROOT>/handoff-automation-tests.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 18 | count | 15 concurrent route agents → staging 503 (17:36–17:47); keep ≤ 5. | partial | Operational cap of 5 concurrent agents; new method allows 20 | Keep 20 agent cap; add staging rate limit separately |

### ~/<PROJ_ROOT>/handoff-user-manuals.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 29 | count | Lanes run in parallel on one kit project collide on the shared Chrome — run live gates serially (one runner). | partial | Serial live gates; shared browser limits parallel lanes | Parallel lanes allowed within 20-agent cap, but live browser gates serialized |

### ~/<PROJ_ROOT>/handoffsrs.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 12 | interpreter | 1. **Interpreter first.** Open each reply with `Interpreter:` and a Sonnet agent's brief. | yes | Interpreter on every reply and Sonnet-run; new method names no interpreter | Drop or count inside 20-agent cap |
| 13 | lead-duties | 2. **Who does what.** The Lead does reading, diagnosis and tiny edits itself. Builds, rebuilds and multi-file work go to background `model: "sonnet"` workers | yes | Lead does hands-on reads and edits; new method: Lead no hands-on work | Lead reviews only; every edit goes to a Sonnet worker |

### ~/<PROJ_ROOT>/PROJ-tests/.agent-ops/briefs/TEMPLATE-service-standard.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 2 | hierarchy | The workflow script fills 3 variables and spawns one worker per slug; the Lead writes nothing per service. | yes | Workflow script, not Lead, spawns the per-service worker; v2 template. | Replace with Lead-briefed Sonnet service worker and Haiku helpers; retire workflow script spawn. |
| 23 | hierarchy | After the last worker the workflow script runs `npx tsx tools/manual/service.ts --close-run <run>` | partial | Script closes run and spawns metrics; a Lead-owned duty moved to a script. | Lead or service worker runs close-run; no script-owned lifecycle. |

### ~/<PROJ_ROOT>/PROJ-tests/.agent-ops/briefs/remake-TEMPLATE-LANE.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 19 | models | TIER         STANDARD (sonnet) · EFFORT medium | partial | Lane workers Sonnet only; no Haiku helper tier. | Sonnet lane worker with Haiku helpers for gates and receipts. |

### ~/<PROJ_ROOT>/PROJ-tests/.agent-ops/briefs/remake-TEMPLATE-S.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 19 | models | TIER         STANDARD (sonnet) · EFFORT medium — cheapest checkpoint (tsc, check-flow-standard) before the one live e2e run | partial | Model fixed to Sonnet; no Haiku helpers; Lead does not choose tier here. | Sonnet service worker; Haiku helper for tsc and checks; Sonnet only for live e2e. |

### ~/<PROJ_ROOT>/PROJ-tests/.claude/settings.json

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 16 | hooks | "SubagentStop": [ { "command": "powershell -NoProfile -File tools/sweep-browsers.ps1" | no | Browser sweep hook on subagent stop; no agent-role rule. | No change. |

### ~/<PROJ_ROOT>/PROJ-tests/.claude/skills/PROJ-automation-tests/SKILL.md

_Role: Pipeline skill for the PROJ Automation Tests suite; holds the Models and Dispatch sections for that suite._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 55 | count | - Filing run: ONE run, 2 workers (`PROJ_WORKERS=2`); `retries: 0` (playwright.config.ts:19). | partial | Playwright worker count, not agent count; ambiguous with agent-count rules. | Label as Playwright threads; agent count stays under the 20-agent cap. |
| 60 | count | Lib fixes: ONE owner edits `lib/**`... Service workers own disjoint service folders and never edit lib or the reporter. | partial | Write-set ownership is a count rule; new method counts agents, not only write-sets. | Keep single-writer per path; state the count is by write-set AND the 20-agent ceiling. |
| 61 | lead-duties | one worker per service folder (triage + fix, non-filing runs only), one lib worker, one Jira-PDF worker; the Lead owns the reporter and the single full re-run. | yes | Lead owns reporter and full re-run = hands-on work; workers not Sonnet-with-Haiku. | Lead reviews only; reporter and full re-run go to a Sonnet worker. |
| 64 | models | Lead = Opus 5.5 (medium) briefs and decides. Haiku 5.5 workers: Jira sync + image logging, `build.ts`/`gates.ts`, non-filing runs, sign-in probes. Sonnet 5.5 workers: discover/generate/data fixes, lib fixes, Jira analysis + checks, filing runs, triage. | yes | Lead picks Haiku or Sonnet per task; new method: Sonnet workers each run Haiku helpers. | Workers are Sonnet 5.5; each Sonnet worker runs Haiku 5.5 helpers; Lead does not pick per-task worker model. |
| 65 | foreground-background | Dispatch (the owner, 2026-10-11): every worker runs in the background (`run_in_background: true`); its completion is the trigger... Supersedes any foreground rule. | partial | Background-only forbids the foreground helper batch the new tree needs. | Workers background; Haiku helpers launched in one foreground batch by their Sonnet worker. |

### ~/<PROJ_ROOT>/PROJ-tests/.claude/skills/PROJ-e2e/SKILL.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 158 | other | Never launch a harvest tool from a shell `for` loop or a long `&&` chain in a background shell. Stopping the agent kills the child it was waiting on | no | Process hygiene, no agent-count or tier rule. | No change. |

### ~/<PROJ_ROOT>/PROJ-tests/.claude/skills/PROJ-manuals/SKILL.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 779 | lead-duties | 9 gates → 10 `deliver.py` (Delivery / Improvement Delivery; no spot-delivery). The Lead alone, zero workers. | yes | Explicit Lead-alone, zero-worker build mode. | Build via Sonnet service worker plus Haiku helpers; Lead only delivers and reviews. |

### ~/<PROJ_ROOT>/PROJ-tests/.claude/skills/PROJ-manuals/references/work-process-v2-2026-09-28.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 12 | hierarchy | `the owner → standing interpreter → Lead → workflow script → ONE worker per service → service.ts → close-run → Lead → the owner` | yes | One worker per service, workflow script spawns; superseded v2 but still a live reference. | Mark archived; new tree: Lead → Sonnet service worker → Haiku helpers. |

### ~/<PROJ_ROOT>/PROJ-tests/.claude/skills/PROJ-manuals/references/work-process.md

_Role: Work process v3 (2026-09-29): canonical for building a manual service; Lead-alone model, supersedes v2._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 10 | lead-duties | **Who:** the Lead, alone — zero workers, no workflow script, no model stages (nj-delegate §0.0: one context can hold it). the owner: gives step 1, answers forks, verifies the output. | yes | Lead does all hands-on steps 1-10 with zero workers; new method has Lead review-only. | Lead briefs Sonnet service workers who run Haiku helpers; Lead keeps review, decisions, push, delivery. |
| 57 | models | **Text checker (the owner 2026-10-03):** after `voice_style_gate.py`, one separate Sonnet checker reviews `ttsAr` | partial | Standalone Sonnet worker, not a Sonnet-with-Haiku-helpers pattern; no Lead model choice. | Sonnet service worker runs the text check via Haiku helper; Lead decides tier per stage. |
| 107 | foreground-background | **Dispatch (the owner, 2026-10-11):** S, AR and EN workers all run in the background (`run_in_background: true`); each reports once and its completion is the trigger that wakes the Lead (receipt + at most 25 lines). The Lead never polls or blocks; mid-run changes go as `AMEND:` via `SendMessage`. | partial | Background and trigger rules match; silent on Sonnet-runs-Haiku-helpers tree. | Keep background trigger; add: Sonnet lane worker briefs its Haiku helpers in one foreground batch, reviews receipts. |

### ~/<PROJ_ROOT>/PROJ-tests/.claude/skills/project-srs/SKILL.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 302 | lead-duties | A set-wide rebuild is over an hour of headless Chrome and Word COM, so it is also the one job to hand to a worker rather than running in the director's turn. | no | Consistent: long rebuild goes to a worker, not the director. | Keep; name the worker as Sonnet service worker. |

### ~/<PROJ_ROOT>/PROJ-tests/.claude/skills/project-srs/references/consolidation/01-root-cause.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 3 | hierarchy | Governance: nj-governance-v3. delegations: 0. You never spawn or instruct another agent. | yes | Forbids spawning; new tree needs Sonnet workers to brief Haiku helpers. | Sonnet stage worker may brief Haiku helpers in one foreground batch; helpers never spawn. |

### ~/<PROJ_ROOT>/PROJ-tests/.claude/skills/project-srs/references/consolidation/03-panel-common.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 3 | hierarchy | Governance: nj-governance-v3. delegations: 0. You are one POV; you never see the other POVs' votes. | yes | Panel POV workers barred from delegating; new tree allows Haiku helpers under them. | POV worker may run Haiku helpers for checks; never sees peers' votes. |

### ~/<PROJ_ROOT>/PROJ-tests/.claude/skills/project-srs/references/consolidation/04-builder.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 3 | hierarchy | Governance: nj-governance-v3. delegations: 0. Owned write paths: the files a rule needs under `src/srs/` | yes | Builder barred from delegation; sole-writer rule is compatible. | Keep single-writer paths; allow Haiku helpers under the Sonnet builder. |
| 11 | git | 6. Commit by explicit path only, trailer «Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>». Then set `.agent-ops/consolidation-marker.json` | partial | Builder commits and pushes-equivalent; new method gives git push/merge to Lead only. | Builder stages and reports; Lead commits, pushes and merges. |

### ~/<PROJ_ROOT>/PROJ-tests/.claude/skills/project-srs/references/consolidation/README.md

_Role: SRS batch consolidation prompt set: run once per batch; stages 1-4 all Sonnet; canonical for consolidation dispatch._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 7 | models | Workflow srs-consolidate  args {"runDir": "<run dir>"}      # stages 1-4, all agents model sonnet | partial | All stages Sonnet; no Haiku helpers; Lead tier choice bypassed. | Sonnet stage workers with Haiku helpers; Lead picks tier per stage. |

### ~/Desktop/MOA/handoff.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 25 | lead-duties | Subagents cannot Write report.md (tool refuses); the Lead saved them. | partial | Lead doing writes is hands-on work; new method Lead no hands-on | Workers write their own reports; Lead only receives |

### ~/Desktop/QA Engineer/CLAUDE.md

_Role: QA Engineer KB project (49 lines): accuracy gate, author/verifier naming; no delegation policy of its own._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 25 | hierarchy | Entries are written by one agent and verified by another. Agent names: author `<slug>-helper`, verifier `svcN-lead`. | no | Author and verifier separation; compatible with Lead-Sonnet-Haiku tree | Keep |

### ~/Desktop/QA Engineer/handoff.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 70 | count | 5 leads × ~6 helpers at once: refused by the 20-live-subagent cap. Keep the tree ≤ 20. | no | Already states 20-live cap counting helpers; matches new method | Keep; use as the reference for the 20 cap |

### ~/Desktop/QA-Wrap/CLAUDE.md

_Role: QA Wrap project rules (54 lines): own Delegation section with Max ceiling 5 and worker-mode names; canonical only for project exceptions._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 5 | hierarchy | no helpers spawned by workers — a worker never spawns, briefs or instructs another, anything between workers is a file the director routes by path | yes | Forbids worker helpers; new method has Sonnet running Haiku helpers | Sonnet worker may run Haiku helpers; cross-worker data still via Lead |
| 5 | count | Eco = the owner's ceiling of one worker, ≤ 13 %/h of the 5-hour session; Max = the N he names. | partial | Modes with ceilings of one or N; new method is a single 20-agent cap | Single mode: up to 20 agents live |
| 11 | count | the owner's own Max ceiling of 5 for the 16 Sept brief (next line) | partial | Historic ceiling of 5; new method cap is 20 | Historic brief only; raise ceiling to 20 going forward |
| 14 | models | Director = the Lead, sole orchestrator (v3). It is Opus 5.5 at effort medium, fixed for the session, and never executes a stage (the owner, 10 Oct 2026). Workers are Sonnet 5.5 ... or Haiku 5.5 ... never Opus; a failed Haiku stage moves once to Sonnet | yes | Lead picks Haiku or Sonnet per stage; new method: workers Sonnet, Haiku only as helpers | Lead Opus medium; workers Sonnet 5.5 each with Haiku 5.5 helpers; no per-stage pick |
| 20 | hierarchy | a receipt of ≤ 25 lines ... plus the CHANGED list and `delegations: 0` | yes | Zero-delegation receipt; new method allows Haiku helpers under Sonnet | Receipt reports helper count, not zero |
| 25 | foreground-background | Dispatch: a worker that builds or edits runs in the foreground (the owner watches it; his messages cannot derail it); read-only research may run in the background. | yes | Foreground for editors vs background-only rule in PROJ line 90 | One rule for every worker; decide foreground vs background once across repos |
| 26 | lead-duties | The director never: reads project source, renders pages or images, re-derives a worker's numbers, or invokes heavy skills | partial | Lead review-only matches; Lead delivery and git push are not named here | Add Lead owns git push/merge and delivery |
| 34 | count | the six `sdlc-*` Sonnet 5.5 agents are in `~/.claude/agents/` | partial | Six fixed Sonnet agents with no Haiku helpers; new method has up to 20 agents with Haiku helpers | Sonnet sdlc agents may run Haiku helpers; total live agents capped at 20 |

### ~/Desktop/QA-Wrap/handoff-qawrap.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 15 | foreground-background | The Lead (main session) never reads project source; workers (Sonnet 5.5, `model: "sonnet"`) do. Editing workers run foreground; read-only research may run in background. | yes | Foreground for editors vs background-only; no-delegation clause in the same line | Single background rule; Sonnet workers run Haiku helpers |
| 67 | foreground-background | dispatch editing workers foreground with `model: "sonnet"`; one check per receipt | yes | Foreground dispatch for editors conflicts with background-only rule | Background dispatch for all workers; Lead checks receipts |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-agent-ops/SKILL.md

_Role: NJ Governance v3 transport under nj-delegate: telemetry refused at write time (relay.py), path claims, KPI audit, results through files, one wake per batch, low-effort interpreter._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 11 | count | Worker count always comes from `nj-delegate` §0.6 (the number of disjoint write-sets) so there is one source of truth. | yes | New method sets up to 20 concurrent agents; this makes write-sets the only count source. | Count = disjoint write-sets, capped at 20 concurrent agents; state the cap once in nj-delegate §0.6. |
| 19 | count | Inherit the count rule (`nj-delegate` §0.6): one worker per disjoint write-set on the critical path; only the user's own Eco / Max N is a fixed ceiling. | partial | Write-set rule kept, but no 20-agent ceiling; Eco/Max N is the only named cap. | Add the global cap of 20 agents at a time as the ceiling beside write-set counting. |
| 27 | hierarchy | Flat topology. Workers never spawn, brief or message each other; a result file is the only thing one worker leaves for another, and the Lead decides who reads it | yes | New method has Sonnet workers run Haiku helpers, so workers do spawn and brief helpers. | Lead -> Sonnet worker -> Haiku helpers (one level); helpers never spawn; siblings exchange only by path via the parent. |
| 50 | hierarchy | Activate a stage only when its inputs already exist on disk. Never spin up a worker to wait for another. | no | Sequencing rule, still consistent with a parent briefing helpers after inputs exist. | Keep; a Sonnet worker activates its Haiku helpers only after inputs exist. |
| 52 | lead-duties | Deactivate an agent whose result JSON says `status: ok` and whose one director check passes. Keep and resume (`SendMessage`) only an agent with faults left | partial | 'director check' has the Lead reading results; under new method the Sonnet worker reviews its helpers' receipts. | Sonnet worker checks its Haiku helpers' receipts; Lead checks only the Sonnet worker receipt and decides. |
| 55 | polling | Monitor deterministically, decide at events. Liveness and stall are a script's job; the Lead is woken only by a `nj-delegate` §0.4 event, never to read 'still running'. | no | Consistent with event-only Lead wakes and no polling. | Keep unchanged. |
| 65 | models | ## 3. Choosing count and models — 3. Run `nj-delegate` §3 per stage ... Tier: <tier> because <reasoning type>; effort: <level> | yes | Tier vocabulary (FRONTIER/STANDARD/ECONOMY) and per-stage model choice replace the fixed Sonnet-worker/Haiku-helper split. | Fixed roles: Sonnet 5.5 workers, Haiku 5.5 helpers; drop per-stage tier choice, keep effort per role. |
| 75 | models | 4. **FRONTIER is the Lead's call (the owner, 2026-09-17).** The Lead may dispatch a FRONTIER worker whenever the stage needs one; no fixed cap. | yes | A Lead-dispatched FRONTIER worker with no cap conflicts with Opus-Lead-does-no-hands-on and the 20 cap. | Workers are Sonnet only; Opus is Lead only; no FRONTIER worker tier; 20-agent cap applies. |
| 92 | foreground-background | 7. Launch every independent stage in one message, before waiting on any; the Lead is then SUPERVISORY-IDLE. Every worker, builders and editors included, is dispatched with `run_in_background: true` | partial | Background-only is consistent for workers; no rule yet for Sonnet launching Haiku helpers (foreground batch per project CLAUDE.md). | Lead dispatches Sonnet workers in background; Sonnet dispatches Haiku helpers as one foreground batch and reviews each receipt. |
| 100 | interpreter | ## 4. The interpreter — called on a trigger. One ECONOMY interpreter per session, spawned the first time a message from the owner is long, mixes Arabic and English, or changes a brief | partial | Adds a fourth agent role outside Lead/Sonnet/Haiku; project CLAUDE.md says interpreter runs on every message. | Decide whether the interpreter is a Haiku helper under the Lead or removed; state it once and align CLAUDE.md with it. |
| 120 | interpreter | Fallback: if `SendMessage` fails, spawn one fresh interpreter and continue — one respawn, not a retry loop. | partial | Tied to the interpreter role; changes only if the interpreter is removed or made a helper. | Follow the interpreter decision; if a helper, respawn via its service lead, not the Lead. |
| 208 | models | Never spawn another worker because the first failed. ... the Lead runs `relay.py route <project> --class C --failed ... --cause <class>`, which prints ESCALATE (sonnet → opus, once ...) | partial | Escalation to Opus makes a worker Opus, which collides with Opus being Lead only; route call is a Lead action. | Escalation: Haiku helper -> Sonnet worker once; Sonnet failure -> Lead decision, not an Opus worker. |
| 239 | other | `scripts/relay.py` — `init`, `digest`, `ledger`, `batch`, `claim`, `verify`, `estimate`, `sweep`, `stale`; the only channel a worker result, ledger row, batch row or path claim goes through. | no | Canonical list of the script's subcommands; no conflict with roles. | Keep; relay.py stays the transport after the role change. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-agent-ops/scripts/relay.py

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 22 | count | claim <project> <run-id> --agent A --paths p1 p2 ... Refuses (exit 1, writes nothing) on overlap with an existing claim by a different agent (core §0.6). | partial | Enforces single-writer by path (write-set rule); no 20-agent cap and no service-level grouping. | Keep overlap refusal; add a 20 concurrent-claims cap and one owner per service for a Sonnet worker plus its helpers. |
| 40 | models | route <project> --class C ... start model + effort per task-class learned from ledger.md (start haiku\|sonnet, chosen by the Lead) | partial | States the Lead picks the start model; conflicts with fixed roles. | Start model fixed by role; route learns effort only. |
| 62 | models | VALID_TIERS = ["DETERMINISTIC", "FREE-LOCAL", "ECONOMY", "STANDARD", "FRONTIER"] | partial | Hardcoded tier set; rows and results refuse any tier outside it, so a role change needs this list. | Replace with the role set (Sonnet worker, Haiku helper, Opus lead) or extend the list; update write-time refusal. |
| 78 | budgets | CLASS_BUDGETS = {"FRONTIER": 150000, "STANDARD": 65000, "ECONOMY": 12000} | partial | Overrun thresholds keyed to tiers; the Sonnet/Haiku tree has no FRONTIER class here. | Key budgets by role (Sonnet worker, Haiku helper); values stay derived and labelled, not measured. |
| 395 | hierarchy | BATCH_FIELDS includes "w2w-delegations", "nested-spawns"; verify (751-756) reports BREACH when total > 0 (target 0) | yes | verify flags any delegation as BREACH, so a Sonnet-to-Haiku batch trips it every time. | Expected delegations = helpers spawned by Sonnet workers; nested-spawns stays 0; change the breach test to match. |
| 436 | hierarchy | for f in ("w2w-delegations", "nested-spawns", "model-polls"): ... print(f"batch WARN: {f}={v} (expected 0)") | yes | Write-time WARN on any non-zero delegation; fires on every correct Sonnet-to-Haiku batch. | Warn only when a helper spawns a helper; allow the one-level Sonnet-to-Haiku count. |
| 511 | other | sweep: 'dispatched run with no receipt'; 'claim ... still open (release it when the batch ends)'; leftover checks | no | Leftover sweep; applies unchanged to Sonnet and Haiku agents, no model names. | Keep; tag helpers with the session tag too. |
| 729 | count | avg_ratio = lead-wakeups / worker-count; breach = avg_ratio > 1.5 ; print(f"lead-wakeups/worker-count: {avg_ratio:.2f} (target <=1.5)") | partial | Wake ratio divides by worker-count; with Sonnet+Haiku trees the denominator is undefined. | Define worker-count as Sonnet workers only (or all agents) and document it; keep the 1.5 target. |
| 808 | other | ROUTE_MIN_N = 5 (learning threshold); route_decide: `if rate < 60:` escalate; blank effort never lowers effort | no | Learning thresholds for start model, independent of the agent tree. | Keep; only the model names fed into it change. |
| 813 | models | NEXT_TIER = {"haiku": "sonnet", "sonnet": "opus"} | yes | Escalation sends a worker to Opus, the Lead's model; Opus is no longer a worker. | Ladder: haiku -> sonnet only; sonnet failure -> STOP and report to Lead (no Opus worker). |
| 816 | models | def route_decide(rows, task_class, failed=None, cause=None, ran_on=None, start="sonnet"): ... NEXT_TIER.get(ran_on or "sonnet") | partial | Default start sonnet fits workers; the opus branch is the conflict. | Keep default sonnet; STOP after sonnet; report to Lead. |
| 854 | models | def row(tc, vs, rt="claude-sonnet-5-5", ...) — selftest asserts 'START opus' / 'ESCALATE opus' (lines 858, 861, 862) | yes | Selftest encodes opus as a worker escalation; it fails once the ladder changes. | Rewrite assertions for haiku->sonnet only and sonnet->STOP. |
| 949 | hierarchy | --role ... director \| worker \| interpreter \| verifier (ledger --role help text) | partial | Role names 'director' and 'interpreter' do not match Lead / Sonnet worker / Haiku helper. | Role enum: lead \| worker \| helper \| verifier; accept old names as aliases for one release. |
| 1024 | models | p_route.add_argument("--ran-on", dest="ran_on", default=None, choices=["haiku", "sonnet", "opus"]) | yes | Accepts opus as a worker runtime for escalation; conflicts with Opus being Lead-only. | choices=[haiku, sonnet] only. |
| 1025 | models | p_route.add_argument("--start", dest="start", default="sonnet", choices=["haiku", "sonnet"], help="the Lead's start model ... Opus Lead decides") | partial | Start model chosen by the Lead; under the new method the model per role is fixed and only effort is learned. | Fix start by role: Sonnet for workers, Haiku for helpers; route learns effort only. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-agent-ops/templates/interpreter-brief.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 1 | interpreter | You are this session's interpreter agent, running at the ECONOMY tier. You are kept alive between messages and invoked only when the director sends you a message | partial | Interpreter is a separate agent role at ECONOMY tier, outside the Lead/Sonnet/Haiku tree. | Follow the interpreter decision; reword to the chosen role and model (Haiku helper, if kept). |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-agent-ops/templates/result.schema.json

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 14 | models | "tier": { "type": ["string", "null"], "enum": ["DETERMINISTIC", "FREE-LOCAL", "ECONOMY", "STANDARD", "FRONTIER", null] } | partial | Tier enum has no Sonnet/Haiku/Opus role; results need runtime plus role instead. | Replace or extend tier with a role enum (lead, service-lead, helper) plus runtime model id. |
| 23 | hierarchy | "delegations": { "type": ["integer", "null"], "minimum": 0, "description": "workers/agents this worker intentionally spawned or instructed; expected 0" } | yes | Expected 0 contradicts a Sonnet worker briefing its Haiku helpers. | Keep the field; expected value is the helper count for a Sonnet worker, 0 for Haiku helpers. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-agent-ops/templates/worker-rules.md

_Role: Worker rules, read once before first edit, R1-R18; canonical for worker behaviour, referenced by the brief._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 5 | hierarchy | R1 — No delegation. Never spawn, brief, instruct, re-scope or pick a model for another worker, and never hand work to one directly. | yes | Forbids a Sonnet worker briefing Haiku helpers, which the new method requires. | Sonnet worker may brief only its own Haiku helpers (one level); helpers never spawn; no peer briefing; Lead picks no models. |
| 17 | foreground-background | R4 — Finish before you report; no model polling. You run in the background and your completion is the trigger that wakes the Lead | partial | Background is right for workers; helpers run foreground per brief, so the wording must cover both. | Workers background, helpers foreground batch; completion of the batch is the trigger. |
| 50 | lead-duties | R10 — Amendments are marked; questions are not tasks. A Lead message that starts `AMEND:` is a contract amendment | no | Messaging rule; applies unchanged to Sonnet workers receiving AMEND. | Keep unchanged. |
| 93 | git | R18 — Never rewrite the owner's working tree. No `git reset --hard`, `git checkout -- .`, `git restore .`, `git stash`, `git clean` ... Stage and commit only your own files, by path. | partial | Workers may commit by path; new method reserves push and merge for the Lead, which this does not state. | Workers stage and commit own paths only; Lead alone pushes and merges; add that line here. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-automation-suite/SKILL.md

_Role: Generic automation-suite skeleton, folder layout, sign-in lock and reports; references docker, PROJ, layout, outputs-pdf._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 29 | other | Worker briefs add an outer lock `mkdir reports/.signin-lock` (retry 10 s, remove only if older than 4 min) | no | Sign-in lock for worker briefs; compatible with any tree. | Keep. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-delegate/SKILL.md

_Role: CANONICAL governance: section 0 'NJ Governance v3 - the operating model' (L17-32) and 0.1-0.16 are the single canonical statement; 0.3a is canonical for the hierarchy; sections 1-14 hold routing, modes, budgets, director rules._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 8 | lead-duties | The main session (the **Lead**, a.k.a. director) **routes**: analyses, picks the cheapest reliable execution path, verifies proportionally to risk, reports. | partial | Routing and reporting fit; cheapest-path choice by the Lead does not. | Lead = review, decisions, git push/merge, delivery; dispatch only. |
| 11 | lead-duties | The Lead may do bounded targeted work itself when cheaper than a worker, never broad repository exploration. | yes | Lead doing hands-on work contradicts Lead = review, decisions, git, delivery only. | Lead does no hands-on work; any bounded task goes to a Sonnet worker. |
| 22 | other | The rule that shapes every other rule: a clause is either enforced by a named machine, or it is marked a habit. | no | Canonical framing of v3; the new method adds no machine-checked clause. | Keep; any new rule gets a GATE or HABIT tag. |
| 41 | count | Zero workers is the most common correct answer, and choosing it is not a failure to delegate. | yes | New method always dispatches Sonnet workers, up to 20. | Remove zero-as-default; Sonnet workers run each stage, Lead decides. |
| 46 | lead-duties | The Lead alone classifies, decomposes, creates workers, sets tier, effort, scope and write ownership, decides parallelism, moves ownership, picks reviewers, decides retry and escalation, synthesises across workers, and adjudicates. | partial | Decisions fit; per-stage tier and effort choice is replaced by fixed Sonnet and Haiku roles. | Lead decides dispatch and review; model roles fixed by design. |
| 77 | hierarchy | A worker never intentionally spawns, delegates to, instructs, re-scopes or picks a model for another worker, and never hands ownership to one directly. | partial | Still forbids worker-to-worker; 0.3a exempts service lead to helper only. | Sonnet workers may brief Haiku helpers; helpers never spawn; siblings never talk. |
| 87 | hierarchy | HARD RULE (the owner, 2026-10-14): agents communicate and report only by triggers, in a hierarchy. | no | Canonical trigger rule; consistent with the new flow. | Keep as canonical hierarchy statement. |
| 89 | hierarchy | Tree: Lead (Opus 5.5) -> Sonnet SERVICE-LEAD per service -> Haiku helpers. A service lead may brief Haiku helpers in ONE foreground batch. | partial | Shape matches; per-service lead and max depth 3 differ from one Sonnet worker per stage with Haiku helpers. | Lead -> Sonnet worker -> Haiku helpers, total at most 20 live. |
| 89 | foreground-background | A service lead may brief Haiku helpers in ONE foreground batch (several Agent calls in one message, never run_in_background, never end your turn with a child running). | yes | Foreground helpers conflict with background-always for every worker (section 6). | Sonnet workers background; their Haiku helper batch foreground inside their own turn; write both into section 6. |
| 104 | polling | Builds, renders, recordings, test suites, browser runs and long scripts are waited on by the runtime or by a script: start → deterministic wait → exit or meaningful timeout → one wake. | no | Consistent with completion-as-trigger. | None. |
| 121 | count | There is no ceiling and no floor — zero, one or many are all correct — but the number is now derived and auditable | yes | Core says no ceiling; new method caps total agents at 20. | State a hard cap: Lead + Sonnet + Haiku at most 20 live agents. |
| 178 | lead-duties | A large diff, an open PR, a long session or a busy worker is not a reason. | partial | Review is risk-based (HABIT); new Lead reviews every worker output. | Lead reviews every worker receipt; risk sets depth, not whether to review. |
| 197 | models | (Opus 5.5, medium) starts each worker on Haiku 5.5 or Sonnet 5.5 by the stage's reasoning need; | partial | Lead may start a direct Haiku worker; new method has Haiku only as a Sonnet helper. | Lead starts Sonnet workers; Haiku is used by Sonnet workers as helpers. |
| 199 | models | CAPABILITY_LIMIT, IMPLEMENTATION_DEFECT and TEST_FAILURE print ESCALATE: the stage moves up once (haiku → sonnet, sonnet → opus; row records escalations=1) | yes | Sonnet to Opus escalation creates an Opus worker, which the new method reserves for the Lead. | Escalate Sonnet failures to Lead review, not to an Opus worker. |
| 226 | models | relay.py ledger refuses a row whose tier is outside the tier set, whose exec-status is | partial | Tier enum in relay.py (outside this group) would reject sonnet and opus-only rows; check that file. | Change the tier set to model names in relay.py. |
| 279 | models | Who leads: the Lead runs at FRONTIER and may dispatch a FRONTIER worker whenever §0.8 says the stage needs one — no per-batch ceiling (the owner, 2026-09-17). | yes | Allows Opus (FRONTIER) workers; new method: Lead is Opus only, workers are Sonnet. | Workers are Sonnet 5.5, with Haiku helpers; no Opus worker. |
| 288 | lead-duties | bounded targeted director work; worker only when delegation has measurable value. | yes | Lead loop step 2 lets the Lead do director work and skip workers. | Replace: Lead dispatches a Sonnet worker; deterministic checks run inside it. |
| 307 | count | \| Standard (default) \| one per disjoint write-set on the critical path (§0.6) — zero when a script or existing evidence answers it \| | yes | Count from write-sets, zero allowed; new method is Sonnet per stage, up to 20. | Sonnet workers per write-set, Haiku helpers under each, total at most 20. |
| 308 | count | \| Eco \| the user's own ceiling: one \| | yes | Eco caps at one worker; new method runs up to 20. | Eco stays a user-named ceiling only, never default. |
| 309 | count | \| Max \| the user's own ceiling: the N they name (smallest stated count if Max is named without N) \| | partial | User-named N versus fixed 20; Max still valid below 20. | Max = min(user N, 20). |
| 313 | count | (1) Lead context headroom — every completion wakes the Lead at full context, so the count must keep the session under the ~120k handoff line; | partial | Capacity list has no 20 cap; runtime-map has it. | Add the 20-agent width as capacity fact, sourced from runtime-map. |
| 332 | interpreter | trigger (a long message, mixed Arabic and English, or a change to a running brief), then kept for the session, never respawned per message, never polled | partial | Interpreter spawned on trigger here; the PROJ CLAUDE.md requires it on every message. | Resolve in one place: interpreter on every message, or on trigger. |
| 365 | models | \| ambiguity, architecture, hard root cause, security, production- or data-sensitive change, complex orchestration, high-risk adjudication \| FRONTIER \| | partial | Routes complex orchestration and adjudication to an Opus worker; new method keeps Opus for the Lead. | Route those to the Lead for review, or to a Sonnet worker with Lead review. |
| 437 | budgets | \| FRONTIER \| 150,000 \| 25 \| 75 \| | partial | Budget row for an Opus worker class that the new method does not use. | Lead budget kept apart; worker budgets are Sonnet and Haiku only. |
| 512 | polling | 8. No model-mediated polling (§0.5). The runtime or a script waits; asking done? costs a full-context turn. | no | Consistent: Lead wakes only on completion. | None. |
| 524 | count | \| five FRONTIER workers in parallel \| — \| exhausts the window in ~50 min \| | yes | Measured: five heavy parallel workers exhaust the 5-hour window; 20 agents is unmeasured. | Re-measure at 20 agents before accepting the cap; Sonnet and Haiku are cheaper. |
| 551 | foreground-background | Every worker runs in the background, builders and editors included | yes | Says every worker, helpers included; clashes with the foreground helper batch in 0.3a. | Background for every Sonnet worker; name the Haiku helper batch as the one exception in 0.3a and section 6. |
| 584 | git | Before trusting a receipt, compare its CHANGED list with git status (one command). | partial | Lead reads git status to verify; no clause gives the Lead push, merge or delivery duty. | Add: Lead alone performs git push, merge and delivery; workers commit nothing. |
| 593 | other | never escalate the tier except through relay.py route --failed (one step, once), never spawn a second worker just because the first failed. | no | Consistent with one escalation per stage and no respawn. | None. |
| 643 | lead-duties | Once a phase is dispatched, the Lead manages; it does not execute it (the owner, 2026-09-16 20:15). Carve-out at L646: Bounded deterministic work nobody was dispatched for stays allowed. | partial | Principle matches; the L646 carve-out lets the Lead do its own deterministic work. | Delete the L646 carve-out; keep the principle. |
| 655 | count | 2. Parallel only on genuinely disjoint, bounded lanes (§0.6). | partial | Disjoint-write-set parallelism fits; the new method parallelises up to 20. | Parallel up to 20 agents on disjoint write-sets. |
| 683 | hierarchy | 6. One wake-up per batch. Launch parallel workers in one message, have each write its result to a file, act when all are done. | partial | Conflicts with completion-as-trigger (one wake per worker, 2026-10-11). | Wake per worker completion; batch wake only when nothing decides earlier. |
| 695 | lead-duties | The director may invoke only nj-delegate, session-handoff and nj-learn. (L695-696) | partial | Blocks the Lead from invoking the delivery and git skills it now owns. | Allow the Lead its delivery and git skills; keep the heavy-skill ban for worker context. |
| 753 | count | Not recommended as a fix: more workers, a stronger model for execution, or looser gates. | partial | Discourages more workers as a fix; the new method expands worker count. | Drop 'more workers' from the not-recommended list; keep the cap. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-delegate/reference/runtime-map.md

_Role: # Tier → runtime map (workspace-local, NOT policy) — NJ Governance v3_

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 12 | models | \| ECONOMY \| haiku \| claude-haiku-5-5 (Haiku 5.5, since 2026-10-10 a full worker tier — the owner) \| | partial | Haiku as a full worker tier; new method: Haiku only as Sonnet's helper. | Haiku helpers only; no direct Haiku worker. |
| 14 | models | \| FRONTIER \| opus \| claude-opus-5-5 (Opus 5.5), thinking always on, effort default medium \| | partial | Opus as a worker tier; new method: Opus is the Lead only. | Opus row = Lead only; FRONTIER removed from worker routing. |
| 17 | models | Lead: Opus 5.5 (claude-opus-5-5) at effort medium (the owner 2026-10-10) | no | Matches the new Lead spec exactly. | None. |
| 18 | models | Workers: Sonnet 5.5 and Haiku 5.5; the Lead decides per stage which one and which effort | yes | New method fixes workers to Sonnet with Haiku helpers; per-stage Lead choice conflicts. | Workers are Sonnet 5.5; Haiku is the helper tier under them. |
| 44 | foreground-background | a batch of independent workers, one wake — every worker, builders and editors included — run_in_background: true | no | Consistent with background-always for workers. | None (helper exception stated at line 76). |
| 46 | polling | a condition (file appears, port opens) \| one shell until-loop with a bound, or the Monitor tool \| 0 while waiting | partial | Monitor is a background watcher; SKILL section 14 forbids background monitors of your own. | Remove Monitor from the Lead's options; keep the shell until-loop inside a worker only. |
| 49 | polling | ScheduleWakeup as a long fallback heartbeat (≥ 1200 s), never a short poll | partial | A timed heartbeat wakes the Lead with no completion trigger. | Forbid heartbeat for the Lead; wake on worker completion only. |
| 71 | hierarchy | A service lead may brief Haiku helpers in ONE foreground batch (several Agent calls in one message, never run_in_background). | partial | Foreground helper batch versus background-everything rule elsewhere. | Background Sonnet worker, foreground Haiku batch inside it; state once in core. |
| 76 | foreground-background | service lead -> Haiku helpers \| Agent FOREGROUND, all helpers of a batch in one message; one wake per batch | yes | Foreground edge contradicts background-always for workers. | Keep foreground only for the helper edge, stated as the one exception. |
| 78 | count | at most 20 live subagents across the whole tree (measured 2026-10-15, qa-kb run: 5 service leads × ~6 Haiku helpers were refused at launch). | no | Matches the new 20 cap, but core 0.6 says no ceiling. | Move the 20 into core 0.6 and section 2; this line stays the source. |
| 94 | count | CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS [A] caps a workflow's concurrent agents — set it to the disjoint write-set count, or lower under rate pressure (§11.1 r2). | partial | Sets the concurrency cap to write-set count, not 20. | Set it to 20, the global cap; lower under rate pressure. |
| 95 | hooks | hooks SubagentStart / SubagentStop / PostToolBatch [A] | no | Deterministic per-worker checks; consistent, but graded [A] and not verified here. | Verify the hook events exist before a rewrite relies on them. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-delegate/scripts/check_governance.py

_Role: check_governance.py -- deterministic gate for nj-governance-v3. Checks brief fields, VERIFIER, --run OWNED_PATHS overlap, GATE script names; no model, tier or worker-cap rule._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 35 | models | "GOVERNANCE", "FOCUS", "TASK", "OBJECTIVE", "VERIFIED_FACTS", "SCOPE", "OWNED_PATHS", | partial | Required fields include TIER and EFFORT, which encode the tier ladder; no model field is required. | Replace TIER with MODEL (sonnet or haiku); keep OWNED_PATHS and VERIFIER. |
| 39 | budgets | MAX_BRIEF_LINES = 25 | no | Brief size, not agent count; consistent with the new method. | None. |
| 91 | other | report("nj-governance-v3" in core, "nj-delegate/SKILL.md: version named nj-governance-v3") | no | Only the version string is checked; run_core asserts no model, tier or cap. | Add asserts for the 20 cap and Sonnet and Haiku model names once the core is rewritten. |
| 333 | count | print(f"run check: {len(files)} briefs, {len(fails)} overlap(s)") | partial | --run checks overlap only; no 20-agent cap. | Add a count check: briefs in one run at most 20 (helpers included). |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-delegate/templates/worker-brief.md

_Role: # Worker brief — the contract (NJ Governance v3)_

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 12 | count | TASK <run-id> · <task class> · worker <name> of <N> (<N> = disjoint write-sets on the critical path) | partial | N is write-set count; new method also caps at 20. | Keep N; add 'total at most 20 across the run'. |
| 23 | models | TIER <DETERMINISTIC\|FREE-LOCAL\|ECONOMY\|STANDARD\|FRONTIER> because <reasoning type>; route: <relay.py route START line> | partial | Tier vocabulary replaces model names; new method names Sonnet and Haiku. | TIER becomes MODEL: sonnet or haiku, with the stage it serves. |
| 62 | foreground-background | Background, always; completion is the trigger (the owner, 2026-10-11; supersedes the 2026-09-29 foreground rule). | yes | Template says background for every worker; its SERVICE-LEAD variant says foreground helpers. | Same as SKILL section 6; one rule, one place. |
| 69 | hierarchy | You are asleep until this brief; you report once (receipt + at most 25 lines) and sleep. You never poll, message a peer, or send progress. Helpers (haiku) never spawn anything. | no | Matches trigger-only rule and the new tree. | None. |
| 74 | foreground-background | Launch each batch FOREGROUND, all Agent calls in ONE message, never run_in_background, never end your turn with a child running. | yes | Contradicts the background-always clause at line 62 of the same template. | Helper batch foreground; the service lead itself background. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-jira-to-automation/SKILL.md

_Role: Turn a Jira ticket (or a service's open Bugs) into a runnable automation; no agent-tier clauses._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 52 | other | Do not edit `lib/**` from a service worker: write `lib-defect-<n>.md` and continue. | no | Ownership rule; compatible with the tree. | Keep. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-jira/references/PROJ.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 28 | other | 9 agents filing at once duplicated defects: re-search (tracker + JQL) immediately before create. | no | Lesson about parallel filing; supports keeping a re-search step in any tree. | Keep the re-search rule in filing briefs. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-method/SKILL.md

_Role: Default working method for every request; routing table is canonical for skill choice; delegation defers to nj-delegate §0._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 27 | lead-duties | The main session owns analysis, routing, planning, review and the answer, and may execute bounded deterministic or targeted work itself. | yes | New method: Lead does review, decisions, git push/merge, delivery only, no hands-on work. | Lead does review, decisions, push/merge and delivery; all hands-on work goes to Sonnet workers. |
| 28 | count | **Default worker count is zero.** A subagent is used only for a measurable benefit | yes | New method runs up to 20 agents at once; zero default contradicts it. | Default is one Sonnet worker per independent lane, up to 20 agents total, plus Haiku helpers under each. |
| 42 | count | **§0.6**, the worker count is the number of disjoint write-sets on the critical path | yes | Count derived only from write-sets; new method fixes the count at up to 20 agents. | Count = min(20, parallel lanes); write-sets decide lanes, the 20 ceiling caps them. |
| 44 | hierarchy | The main session is the sole orchestrator; workers never delegate to each other, | partial | Says workers never delegate; silent on Sonnet-to-Haiku helpers. | Lead is sole orchestrator; a Sonnet worker may run Haiku helpers; no peer delegation. |
| 50 | models | Tiers: **DETERMINISTIC / FREE-LOCAL / ECONOMY / STANDARD / FRONTIER** — route to the least expensive one with demonstrated reliability | partial | Tier ladder picks models per stage; new method fixes Lead Opus, Sonnet workers, Haiku helpers. | Fix roles to Opus Lead / Sonnet worker / Haiku helper; keep tier ladder only inside a worker's choice of helper use. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-qa-pipeline/SKILL.md

_Role: Governance is NJ v3 (`nj-delegate` §0): this file adds only the QA-specific orchestration._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 36 | foreground-background | (Exception from `CLAUDE.md`: a worker that builds/edits may be told to run foreground; follow the project file.) | partial | Foreground exception for builders; new method wants background for all Sonnet workers. | All Sonnet workers background; foreground only for Haiku helper batches. |
| 38 | count | **One agent per service** (disjoint write-set = the service folder + its record file). **Extra agents per route share** | partial | Agent-per-service and extra-agent-per-route-share counts differ from the single 20-agent ceiling. | One Sonnet agent per service up to the 20 ceiling; route shares become Haiku helpers under it. |
| 39 | hierarchy | **Workers never delegate to or instruct each other**; anything between workers is a file the Lead routes by path. Receipt: `delegations: 0`. | yes | Blocks Sonnet agents running Haiku helpers. | Sonnet agent may run Haiku helpers; still no peer messages; receipt reports helper count. |
| 40 | models | **Tiers** (`nj-delegate` §3): deterministic first; Haiku for sync, report build + gates, non-filing runs, sweeps; Sonnet for note analysis, checks, filing runs, triage, Bug filing | partial | Lead picks Haiku or Sonnet per task; new method makes Sonnet the worker tier and Haiku the helper tier. | Sonnet agent per lane; Haiku helpers for sync, gates, sweeps; drop per-stage Haiku-vs-Sonnet choice. |
| 46 | count | **Concurrency:** start 3 workers x 3 services (services run one after another inside a worker); 9 agents for single-service Jira work; 15 for route shares. | yes | Sets its own agent ceilings (3x3, 9, 15) instead of the 20-agent ceiling. | Cap at 20 agents total; split by lanes, not fixed 3x3/9/15 numbers. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-qa-pipeline/references/adhd-standard.md

_Role: Output checklist for every QA artefact and worker receipt; canonical for receipt headings._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 18 | hierarchy | STATUS / FINDING (counts) / EVIDENCE (paths) / FILES-SYMBOLS / RISK / NEXT ACTION · `delegations: 0`. | yes | Receipt fixes delegations at 0. | Receipt states delegations n (Haiku helpers) and why. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-qa-pipeline/references/PROJ.md

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 4 | count | 76 filing routes, 15 route-share agents, 9 single-service Jira agents, 3 workers x 3 services for re-harvest | partial | Historical run counts; sum of agents on one day is 27 and exceeds the 20 ceiling. | Keep as history only; future runs stay under 20 agents at once. |
| 10 | hierarchy | one agent per route share (jt-routes), one agent per service for QA re-check + filing (jt-persvc-jira). | partial | Flat agent-per-route fan-out, no Lead-Sonnet-Haiku tree. | Sonnet agent per service; route shares as Haiku helpers under it. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-qa-pipeline/references/lessons-2026-10-12.md

_Role: Lessons from the 2026-10-12 PROJ Lead session; source of rule changes for nj-qa-pipeline and nj-jira._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 6 | lead-duties | the Lead (a) updates every shared brief in the run folders, (b) sends `AMEND:` to every running worker | partial | Lead edits briefs by hand; new method keeps Lead free of hands-on work. | Lead decides and routes the brief change; a Sonnet worker applies it to the briefs. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-rank/references/trigger-model.md

_Role: nj-rank trigger model: who runs nj-rank, when, and how results come back. Canonical for the nj-rank team._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 10 | lead-duties | - Calls `nj_rank.py log` when the owner starts new work, and `nj_rank.py file` after a batch of registrations. | yes | Lead runs nj_rank.py itself; line 24 also has the Lead running import. | Sonnet worker runs nj_rank.py; Lead only decides and reviews. |
| 14 | models | - Model: Haiku 5.5 only, for nj-rank. Bounded spec-to-code and collection. | yes | Haiku only; new method uses Sonnet workers with Haiku helpers. | Sonnet 5.5 worker; Haiku 5.5 helpers for collection. |
| 15 | count | - Up to 20 workers per run, each in the background (`run_in_background: true`). | partial | Cap of 20 matches, but counts Haiku workers, not Sonnet agents plus helpers. | Up to 20 agents total (Sonnet), Haiku helpers counted under them. |
| 18 | hierarchy | - No worker-to-worker messages. A worker never spawns or instructs another agent; artefacts pass by path, through the Lead. | yes | Forbids Sonnet workers instructing Haiku helpers. | Sonnet worker briefs its Haiku helpers only; no peer messages; artefacts by path. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-rank/scripts/nj_rank.py

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 1 | other | nj_rank.py: grep for haiku, sonnet, opus, model, max_workers, team and the number 20 found no agent or worker-count constants. | no | No code to change for the agent tree. | None needed. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-supervise/SKILL.md

_Role: Supervision standard for delegated workers (measured 2026-09-20 session). Canonical for brief clauses and artefact checks; defers tiers and counts to nj-delegate._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 48 | foreground-background | Every worker, builders and editors included, is dispatched with `run_in_background: true` (the owner, 2026-10-11; supersedes the 2026-09-29 foreground rule) | partial | All workers background; Haiku helpers under a Sonnet worker need a foreground batch carve-out. | Sonnet workers run in background; a worker's Haiku helpers run as one foreground batch it waits on. |
| 62 | hierarchy | **No delegation.** "Do not spawn, brief or instruct another worker; write the artefact, report the path, the Lead decides the next step. Report `delegations: 0`." | yes | Forbids Sonnet workers briefing Haiku helpers; new method needs one-level helpers. | Workers may brief Haiku helpers only (one level); helpers never spawn; receipt states helper count. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-wrapup/SKILL.md

_Role: Close a work session or a tested service end to end: discover, classify, file, reconcile, register in nj-rank, render email._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 35 | lead-duties | \| < 6 \| the Lead, 0 workers \| \| | yes | Lead does the work itself below 6 items. | Under 6 items: one Sonnet worker, Lead still no hands-on work. |
| 36 | count | \| 6 - 15 \| 1 Sonnet filer \| \| | partial | Single-worker band; fine as a floor but not tied to the 20 ceiling. | Sonnet lanes derived from write-sets, capped at 20 agents total. |
| 37 | count | \| >= 16 \| up to ceil(A/4) Sonnet lanes, max 4 \| split by root cause | yes | Caps Sonnet lanes at 4, not 20. | Sonnet lanes up to 20 agents total, each with Haiku helpers. |
| 38 | foreground-background | \| Haiku helpers \| only when evidence prep is mechanical and over ~10 files \| one FOREGROUND batch per lead; helpers never spawn \| | no | Foreground helper batch under a lead is compatible with the new tree. | Keep; name the Sonnet worker as the lead. |
| 39 | lead-duties | \| nj-rank \| <= 3 items: the Lead; more: one Haiku worker \| | yes | Lead does nj-rank work itself and uses a Haiku worker, not Sonnet. | Lead never does it; Sonnet worker with Haiku helpers files it. |
| 40 | hierarchy | Every lane brief carries `Governance: nj-governance-v3`, a FOCUS line, ... and the no-delegation clause. Receipts state `delegations: n` and why 0 or n. | yes | No-delegation clause blocks Sonnet to Haiku helpers. | No-delegation replaced by one-level helper rule; receipt states helper count. |
| 49 | lead-duties | **Single writers:** only the Lead runs the tracker writer and register hook; lanes write only their own `filed-<lane>.json`. | yes | Lead runs writers by hand; new method limits Lead to push, merge, delivery. | A Sonnet worker runs writers; Lead only decides and pushes. |
| 76 | lead-duties | On 'go' the Lead runs a short second pass from the same `plan.json` (no re-research), then steps 7 and 10 again. | yes | Lead does hands-on second pass. | Lead decides go; a Sonnet worker runs the second pass. |

### ~/<NJ_PLUGIN_ROOT>/skills/nj-wrapup/references/profile-PROJ.md

_Role: PROJ overrides for nj-wrapup: tracker, register and outputs hooks, tighter agent-tree and size rules than the SKILL._

| line | topic | verbatim | conflicts? | why | proposed direction |
|---|---|---|---|---|---|
| 8 | lead-duties | Lead only. Also record the key on its note: `note.py --reply N<k> ...` | partial | Register and note writes are Lead-only, which is hands-on. | Sonnet worker writes; Lead reviews the result. |
| 15 | lead-duties | «Lead does small work» (2026-10-04): the Lead may read, diagnose and file small batches itself; builds and multi-file work go to background workers. | yes | Explicitly lets the Lead do hands-on filing and diagnosis. | Lead does no hands-on work at any size; small batches go to one Sonnet worker. |
| 16 | hierarchy | Trigger-only hierarchy: Lead (Opus) -> Sonnet service lead -> Haiku helpers (one FOREGROUND batch, helpers never spawn); workers run in the background. | partial | Tree is close, but names a service lead tier and foreground helper batch. | Lead (Opus, review only) -> Sonnet worker -> Haiku helpers (one foreground batch); drop the extra service-lead name. |

## Files with role notes only (no agent-rule clause)

- ~/.claude/projects: Memory dirs with .md counts: PROJ 118, QA-Wrap 33, ENSERA 30, PROJ-tests 25, MOA 4; C--Users-<user>, Desktop--------, Evalto, QA-Engineer, Taisce 0 each (210 files total).
- ~/.claude/skills/nj-kit/README.md: README.md: kit readme; install steps and folder layout. Not canonical for agent policy.
- ~/.claude/skills/nj-kit/bundled/CLAUDE.md: bundled/CLAUDE.md: export copy of ~/.claude/CLAUDE.md; identical today (diff clean). A copy, not the source.
- ~/.claude/skills/nj-kit/bundled/nj-plugin/_archive/governance-baseline-2026-09-20/nj-agent-ops: bundled copy: bundled/nj-plugin/_archive/governance-baseline-2026-09-20/nj-agent-ops (plugin copy; archive copies are historical)
- ~/.claude/skills/nj-kit/bundled/nj-plugin/_archive/governance-baseline-2026-09-20/nj-delegate: bundled copy: bundled/nj-plugin/_archive/governance-baseline-2026-09-20/nj-delegate (plugin copy; archive copies are historical)
- ~/.claude/skills/nj-kit/bundled/nj-plugin/nj-plugin/skills/nj-agent-ops: bundled copy: bundled/nj-plugin/nj-plugin/skills/nj-agent-ops (plugin copy; archive copies are historical)
- ~/.claude/skills/nj-kit/bundled/nj-plugin/nj-plugin/skills/nj-delegate: bundled copy: bundled/nj-plugin/nj-plugin/skills/nj-delegate (plugin copy; archive copies are historical)
- ~/.claude/skills/nj-kit/bundled/nj-plugin/nj-plugin/skills/nj-method: bundled copy: bundled/nj-plugin/nj-plugin/skills/nj-method (plugin copy; archive copies are historical)
- ~/.claude/skills/nj-kit/bundled/nj-plugin/nj-plugin/skills/nj-supervise: bundled copy: bundled/nj-plugin/nj-plugin/skills/nj-supervise (plugin copy; archive copies are historical)
- ~/.claude/skills/nj-kit/bundled/nj-plugin/skills/nj-agent-ops/SKILL.md: bundled copy: bundled/nj-plugin/skills/nj-agent-ops/SKILL.md (plugin copy; archive copies are historical)
- ~/.claude/skills/nj-kit/bundled/nj-plugin/skills/nj-delegate/SKILL.md: bundled copy: bundled/nj-plugin/skills/nj-delegate/SKILL.md (plugin copy; archive copies are historical)
- ~/.claude/skills/nj-kit/bundled/nj-plugin/skills/nj-method/SKILL.md: bundled copy: bundled/nj-plugin/skills/nj-method/SKILL.md (plugin copy; archive copies are historical)
- ~/.claude/skills/nj-kit/bundled/nj-plugin/skills/nj-supervise/SKILL.md: bundled copy: bundled/nj-plugin/skills/nj-supervise/SKILL.md (plugin copy; archive copies are historical)
- ~/.claude/skills/nj-kit/scripts/apply-descriptions.py: scripts/apply-descriptions.py: applies description overrides; no hits on agent or CLAUDE.md clauses.
- ~/<PROJ_ROOT>/.claude/hooks/typecheck.sh: Stop hook: runs npm run typecheck in PROJ-tests and prints a JSON systemMessage on failure. Not canonical for agent roles.
- ~/<PROJ_ROOT>/PROJ-tests/.agent-ops/briefs: 232 briefs in folder; only TEMPLATE-service-standard.md (v2 workflow) and remake-TEMPLATE-S/LANE carry model/count lines; dated briefs not read.
- ~/<PROJ_ROOT>/PROJ-tests/.claude/skills: Searched all project skill folders (PROJ, PROJ-tests, ENSERA, MOA, QA-Wrap): no .claude/agents or .claude/commands folders found under Desktop at depth<=4.
- ~/<PROJ_ROOT>/PROJ-tests/.claude/srs-verifier.profile.json: srs-verifier per-doctype profile: path globs for verifying SRS output; contains no agent, model or count clauses.
- ~/Desktop/MOA/CLAUDE.md: MOA project file (5 lines): holds only the narration voice rule; no agent or delegation clauses.
- ~/Desktop/QA-Wrap/.claude/settings.local.json: QA-Wrap local settings: outputStyle Concise only. Not canonical for agent roles.
- ~/Desktop/Taisce/.claude/settings.local.json: Taisce local settings: outputStyle Concise only. Not canonical for agent roles.
- ~/<NJ_KIT_ROOT>/SKILL.md: Desktop nj-kit SKILL.md: byte-identical to the source SKILL.md today; a copy.
- ~/<NJ_KIT_ROOT>/bundled/nj-plugin/nj-plugin/skills/nj-agent-ops: duplicate copy in Desktop nj-kit extracted bundle (no nj-supervise there)
- ~/<NJ_KIT_ROOT>/bundled/nj-plugin/nj-plugin/skills/nj-delegate: duplicate copy in Desktop nj-kit extracted bundle (no nj-supervise there)
- ~/<NJ_KIT_ROOT>/bundled/nj-plugin/nj-plugin/skills/nj-method: duplicate copy in Desktop nj-kit extracted bundle (no nj-supervise there)
- ~/<NJ_KIT_ROOT>/bundled/nj-plugin/skills/nj-agent-ops: duplicate copy in Desktop nj-kit extracted bundle (no nj-supervise there)
- ~/<NJ_KIT_ROOT>/bundled/nj-plugin/skills/nj-delegate: duplicate copy in Desktop nj-kit extracted bundle (no nj-supervise there)
- ~/<NJ_KIT_ROOT>/bundled/nj-plugin/skills/nj-method: duplicate copy in Desktop nj-kit extracted bundle (no nj-supervise there)
- ~/<NJ_KIT_ROOT>/manifest.json: Desktop nj-kit manifest.json: differs from source only by synced_content_mtime (line 630); content current.
- ~/<NJ_PLUGIN_ROOT>/.claude-plugin/marketplace.json: Plugin manifest for nj-kit: lists the skills in scope (incl. nj-supervise, nj-method, nj-qa-pipeline, nj-wrapup, nj-rank, session-handoff); no agent policy.
- ~/<NJ_PLUGIN_ROOT>/skills/nj-delegate/reference/high-rework.md: # High-rework workflows — browser, recording, environment-sensitive stages (On-demand)
- ~/<NJ_PLUGIN_ROOT>/skills/nj-delegate/scripts/collect.py: collect.py — the director runs this ONCE, after every worker has reported.
- ~/<NJ_PLUGIN_ROOT>/skills/nj-delegate/scripts/report.py: report.py — the last thing a worker runs. Writes the result JSON and the six-heading receipt block.
- ~/<NJ_PLUGIN_ROOT>/skills/nj-delegate/templates/handoff.md: # goals — six-heading handoff skeleton (goals, current state, files in flight, changed, failed attempts, next step). Non-canonical.
- ~/<NJ_PLUGIN_ROOT>/skills/nj-delegate/templates/worker-brief.example.md: It is the **positive control** for `check_governance.py --brief`.
- ~/<NJ_PLUGIN_ROOT>/skills/nj-director/SKILL.md: This is film direction — shots, coverage, camera, edit — not agent delegation.
- ~/<NJ_PLUGIN_ROOT>/skills/nj-jira/SKILL.md: Open the owner's Jira, analyse a ticket, file Bugs with evidence, QA re-check, keep the tracker; no agent-tier clauses.
- ~/<NJ_PLUGIN_ROOT>/skills/nj-learn/SKILL.md: Lessons skill; grep for delegation, agent, model, worker, background lines found only one historical mention (line 61).
- ~/<NJ_PLUGIN_ROOT>/skills/nj-learn/scripts/lessons.py: Bookkeeping script that renders the lessons playbook; no agent clauses.
- ~/<NJ_PLUGIN_ROOT>/skills/nj-rank/SKILL.md: Register finished work, keep its evidence paths, and file it to Jira as Done Tasks assigned to the user.
- ~/<NJ_PLUGIN_ROOT>/skills/session-handoff/SKILL.md: Close a session by writing a handoff.md the next session reads first, instead of dragging degraded context through /compact.
- ~/<NJ_PLUGIN_ROOT>/skills/tests/test_v3.py: Listed only, not read: test_v3.py (35 KB, governance v3 tests), GATE-RUN.md, fixtures/ dir. Probably asserts v3 counts; check before changing counts.
