# NJ Governance v4 — design input (2026-10-16, Sonnet lead; draft for the owner's call)

Grades: [DOC] Claude Code docs (via claude-code-guide: code.claude.com/docs/en/sub-agents.md, worktrees.md, hooks.md, agents.md); [M] measured in our runs (runtime-map.md, 2026-10-14/15); [A] assumed, falsifier given; [U] unknown, how to settle. Helper digests (scratchpad): `qa-kb-digest.md`, `lessons-digest.md`; sources cited inline by rule id / file.

## 1. The v4 operating model (<= 40 lines)

**Roles**
1. **Lead** = Opus 5.5, effort medium. MAY: read receipts, `git diff`/`--stat`, run the project's gate commands, decide, brief, `git merge`/`git push`, deliver, write handoff/decision logs, answer the owner. MUST NOT: write or edit deliverable/source files, run harvests/records/probes, read a credentials file, poll or sleep on workers. Wakes only on the owner or a worker completion.
2. **Sonnet lead** (agent type `sonnet-lead`, Sonnet 5.5, effort medium; high only for diagnosis briefs) = owns one whole bounded phase/service on its own branch + worktree. MAY: author/fix, run gates, brief Haiku helpers, review every helper receipt, commit on its branch. MUST NOT: push, merge, touch main, write outside OWNED_PATHS, message a sibling, put a credential in a helper brief, end its turn with a child or its own command running.
3. **Haiku helper** (agent type `haiku-helper`, Haiku 5.5, effort low) = bounded read-mostly or mechanical stage (grep/read/extract/Jira sync/image log/count/probe). MAY: Read, Grep, Glob, Write one report file. MUST NOT: spawn (no `Agent` tool), free-form Bash, read secrets paths, write outside its one report path, decide anything.

**Topology** Lead -> Sonnet leads (`run_in_background: true`, completion = trigger) -> Haiku helpers (one FOREGROUND batch per phase, several `Agent` calls in one message [M: a nested background child reports to main, probe 2026-10-14]). Depth 2; set `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2` so a third layer cannot exist [DOC; value semantics INFERRED]. Siblings exchange artefacts by path through the parent only.

**Ceiling 20 (a cap, not a quota)** = live subagents across the whole tree; the Lead's own session is not counted [DOC: default cap 20, error `Concurrent subagent limit reached`, `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`; M: 5 leads x 6 helpers refused 2026-10-15]. Rule: `S + sum(h_i) <= 20`; default shape 4 leads x <= 4 helpers. Cost evidence: a ~20-agent fixed fan-out cost ~1.0-1.3M tokens, and half the agents gave the same tickets (trial-1.md l.190/219), so spawn count follows items, never the cap. Slots are claimed with `relay.py slots` (new, s3), not self-counted. Rate limit: 5 workers died at once on one 429 in a past day (director-token-discipline.md) — queueing/429 behaviour at 20 is [U]; stagger starts.

**Helpers: mandatory vs optional (checkable)** The brief declares `ITEMS=<n>` (independent bounded units: services, files, tickets, notes). `HELPERS_REQUIRED = 0 if n<6 else min(4, ceil(n/6))`. n<6: `delegations: 0` is correct and the receipt says `helpers_required: 0`. n>=6: the lead must spawn >= required; a hook (not the receipt) counts real spawns; mismatch = `relay.py verify` FAIL and the Lead re-dispatches, never accepts. This replaces v3 s0.6 "no floor" and fixes "delegations: 0" (3 of 4 lanes, devil.md row 4; trial-1.md l.32), which a prose mandate could not.

**Git** Each Sonnet lead runs `isolation: worktree` [DOC: branched from default branch, auto-removed if unchanged, lock held while running]. Leads commit only; the receipt carries `BRANCH`, `HEAD`, `CHANGED` (from `git diff --name-only main...BRANCH`, not memory). Lead review = `git diff --stat main...BRANCH`, read the diff only for risk-high paths (R-MANAGEMENT-004), run required checks (R-CI-003: red = no merge, back to the same lead, qa-workflow s6), then merge/push. Push, merge, checkout main, reset --hard are denied to every non-Lead agent type.

**Reporting** Trigger-only: one receipt (<= 25 lines: STATUS/FINDING/EVIDENCE/FILES-SYMBOLS/RISK/NEXT + `helpers_spawned`, `helpers_required`, `branch`) + a detail file; written pass or fail (R-CI-001). No progress messages; `AMEND:` via SendMessage is the only mid-run change.

**Budgets** Per Sonnet lead: uncached in / output / model calls, stop and say at 80%; ceilings are loop detectors, never targets (R-MANAGEMENT-007). Helper: <= 15 tool calls, one file out. Two QUESTIONs per lead, then skip+mark. A failed verifier escalates one tier once.

**Credentials** Helpers never receive a creds path or value. Only the Sonnet lead's scripts read `~/.claude/secrets/*`, through a `--creds` flag; nobody prints a creds file (incident: v2-t2.md "Incident", a helper one-liner printed secrets; today a habit only). Enforced by tool set (no Bash) + path-deny hook + leak scan (s3).

## 2. Keep / Drop / Conflict

**KEEP from v3:** gate-or-habit label on every clause; graded facts [V]/[A]/[U] + CHALLENGE; OWNED_PATHS = write-set + `relay.py claim` overlap refusal; <= 25-line receipt + result JSON; `relay.py batch/verify/route/sweep`; budgets as ceilings; classify failure before retry (R-AUTOMATION-013); sweep at close; FOCUS/AMEND/RESUME; no polling; single canonical statement per rule.
**DROP:** s0.3 flat topology / "workers never delegate" (replaced by the depth-2 tree); "zero, one or many, no floor" (replaced by the ITEMS floor); memory rule "Lead does small work" (2026-10-04); v3 s0.0 as licence for the Lead to build alone; self-reported `w2w-delegations`/`nested-spawns` (replaced by hook-counted `helpers_spawned`); the trigger rule restated in four files.
**CONFLICTS needing the owner's call:**
- C1 Lead never writes files vs v3 s0.0 / lead-does-small-work (a typo fix now costs a Sonnet spawn). Proposed: Lead may edit only `handoff.md`, decision/ledger logs, CLAUDE.md and memory.
- C2 PROJ is not a git repository (environment: "Is a git repository: false"). Worktrees, branches and merge need `git init` (+ .gitignore for artifacts, fonts, recordings) or a non-git fallback (copy dir + `relay.py claim` + CHANGED list). Which?
- C3 "Run once, no self-verification" Owner exception vs Lead reviewing diff + gates. Proposed: the diff/gate review is the merge gate, not re-checking machine output; the exception stays for output the owner verifies by hand.
- C4 Accept the helper floor ITEMS>=6 -> ceil(n/6) helpers (cost: cheapest tier, about one Haiku per 6 items)?
- C5 An Opus-medium Lead reading diffs is the dearest token (list 4/20 vs Sonnet 2/10, runtime-map). Accept stat-first risk-based reading, or add a Sonnet reviewer before the Lead?
- C6 nj-rank has its own "Haiku up to 20" team: does it share the 20 ceiling?
- C7 Effort: per-call `effort` exists only from Claude Code v2.1.292 and `CLAUDE_CODE_EFFORT_LEVEL` overrides everything [DOC]. Trust agent-definition frontmatter alone? Haiku effort support [U].
- C8 Background (lead) vs foreground (helper batch) is a measured workaround [M], not a documented rule; docs say background subagents get a smaller tool set [DOC] — keep the probe in the pilot.

## 3. Machine-checkable gates (* = to build)
| clause | enforcer |
|---|---|
| helpers never spawn | `haiku-helper.md` omits `Agent` from `tools` [DOC: omission prevents spawning]; `MAX_SUBAGENT_SPAWN_DEPTH=2`. The `Agent(type)` allowlist is ignored inside subagent definitions [DOC], so tool omission is the control |
| helper floor met | `SubagentStart` hook appends `{agent_id,type,ts}` to `.agent-ops/spawns/<run>.jsonl`*; `relay.py verify` compares with `helpers_required`* [U: does hook input carry a parent id? one probe; fallback: count `Agent` tool_use in the lead transcript] |
| 20 ceiling | runtime cap (env) + `relay.py slots acquire/release <n>`* (file lease, `sweep` frees expired); Start/Stop hooks keep the true count, `verify` flags exceed |
| write-sets disjoint | existing `relay.py claim` + `check_governance --run` |
| writes only inside OWNED_PATHS | `SubagentStop` hook: `git diff --name-only` vs claim file*; exit 2 blocks stop [DOC: SubagentStop can block] |
| no push/merge by workers | `PreToolUse` hook on Bash matching `git (push|merge|checkout main|reset --hard)` when agent type is not lead*; plus `permissions.deny` |
| credentials | helper tools Read/Grep/Glob/Write only; PreToolUse hook denies Read of `*/secrets/*`, `*creds*`, `.env*` for `haiku-helper`*; `relay.py leakscan <run>`* greps receipts/transcripts for known secret values; exit 1 blocks delivery |
| receipt shape/size | `relay.py digest/verify` (exist) + result.schema.json; SubagentStop blocks a receipt > 25 lines or without CHANGED* |
| merge only on green | merge/deliver wrapper script* runs required checks, refuses on red (R-CI-003) |
| model/effort pinned | `.claude/agents/*.md` frontmatter [DOC precedence: call model > frontmatter > env > main]; `batch` records the runtime id from the Agent result; `verify` flags drift |
| Lead does not edit deliverables | PreToolUse hook on Edit/Write for the main agent outside an allow-list* (partial) |
| leftovers | `relay.py sweep --tag` (exists) |
| no polling, report-once timing, decision quality | HABIT; KPI lead-wakeups/worker |
Honest tally: about 10 gates (4 exist today, 6 to build), 3 habits.

## 4. Migration list
- **Global `~/.claude/CLAUDE.md`**: replace the delegation, trigger-only and Models bullets with a ~10-line v4 pointer to nj-delegate s0; keep credentials; state the Lead file-edit allow-list (C1).
- **Project `PROJ/CLAUDE.md`**: Delegation section -> v4 reference (remove "workers never delegate" remnants; "Sonnet service lead" stays); resolve C2 and C3; keep the Owner-exception text with the clarification.
- **nj-delegate SKILL.md**: rewrite s0.1, 0.3, 0.3a, 0.6, 0.7, 0.8 and s11.1 r7; `GOVERNANCE_VERSION = nj-governance-v4`; update `check_governance.py` (`--brief` requires ITEMS, HELPERS_REQUIRED, BRANCH); relabel each clause GATE/HABIT per s3.
- **reference/runtime-map.md**: tier table unchanged; replace the "Trigger-only hierarchy mechanics" section with the v4 tree, depth env, 20-cap [DOC], fork-mode caveat (docs: fork mode removes `run_in_background`), per-call effort v2.1.292, precedence, worktree facts, `SendMessage` auto-resume.
- **templates/worker-brief.md**: add `ITEMS`, `HELPERS_REQUIRED`, `HELPER_SLOTS`, `BRANCH`, `NO_PUSH`, `CREDENTIALS` (path never given to helpers); new `templates/helper-brief.md` (<= 12 lines: one report path, no secrets, no spawn).
- **nj-agent-ops / relay.py**: add `slots`, `leakscan`; extend `batch` (`helpers_required`, `helpers_spawned`, `branch`, `head`); `verify` rules for floor, ceiling, merge-green; retire self-reported `nested-spawns`.
- **nj-supervise**: add checks E (helper floor from spawn log), F (branch CHANGED vs claim), G (leak scan); the no-delegation clause becomes the depth-2 clause.
- **nj-method**: routing row "multi-item build -> Lead briefs Sonnet leads, never writes"; keep proportionality (ITEMS<6 -> one Sonnet, no helpers).
- **nj-kit manifest** (`~/.claude/skills/nj-kit/`, then `python scripts/export.py --zip` and extract to `<NJ_KIT_ROOT>`): register the two agent defs and hooks under tooling; refresh `why` notes.
- **Memory**: add `governance-v4.md`; mark superseded lead-does-small-work, lead-never-works-workers-background, trigger-only-agent-hierarchy (folded in), agents-sonnet-only, sonnet-only-agents; fix the MEMORY.md index lines.
- **Agent definitions** (new, global `~/.claude/agents/`): `sonnet-lead.md` — `model: sonnet`, `effort: medium`, `isolation: worktree`, `tools: Agent, Read, Grep, Glob, Edit, Write, Bash`, `maxTurns`, SubagentStop hook; body = no push, helper floor, receipt, credentials. `haiku-helper.md` — `model: haiku`, `effort: low`, `tools: Read, Grep, Glob, Write` (no Agent, no Bash), PreToolUse path-deny hook; body = one report path, never print a file that looks like credentials.
- **Settings**: env `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2`, `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=20`; SubagentStart/Stop and PreToolUse hooks (via `update-config`).

## Pilot before rollout (R-AUTOMATION-004, R-MANAGEMENT-010)
One service end to end (1 lead, 2 helpers): spawn log equals receipt, no push, leak scan clean, cost against the v3 baseline; only then 4 leads x 4 helpers. The same pilot settles the [U]s: hook parent id, Haiku effort, branch name returned by the worktree Agent, nested foreground inside a background lead in a worktree.
