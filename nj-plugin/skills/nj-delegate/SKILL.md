---
name: nj-delegate
description: 'NJ Governance v4: the Lead (Opus) administers and decides, Sonnet leads build in their own worktrees, Haiku helpers do bounded mechanical work (depth 2, at most 20 agents counted, helpers required by the ITEMS rule). Every clause is machine-enforced, a habit, or marked PENDING. Graded evidence with a worker challenge path, verifier-first routing, a 25-line brief contract, validated telemetry. Triggers: delegate, a named mode or count, /clear, handoff.md.'
---

# nj-delegate — the Lead, the Sonnet leads and the Haiku helpers

The main session (the **Lead**, a.k.a. director) **decides**: it analyses, routes, briefs,
reviews, merges, delivers and reports. It does not build. Deterministic tools and existing
evidence come first; every build, fix or script goes to a worker (§0.1). The Lead answers
questions and reads evidence itself, never broad repository exploration.

Project-agnostic: every project-specific fact comes from that project's
`CLAUDE.md`, its `.claude/skills`, and its `handoff.md`.

## 0. NJ Governance v4 — the operating model (2026-10-16)

`GOVERNANCE_VERSION = nj-governance-v4`. Supersedes nj-governance-v3 (2026-09-22) and the
2026-10-14 trigger-only note. Binding input (owner, 2026-10-16):
`research/governance-v4-2026-10-16/decisions.md`; detail in `design.md` beside it.
**This section is the one canonical statement.** Every other skill, template, CLAUDE.md and
memory file points here and never restates it; model ids live only in `reference/runtime-map.md`.

**The rule that shapes every other rule: a clause is either enforced by a named machine, or
it is marked a habit, or it is marked `PENDING (B3)` (the machine is specified, not yet
built — hooks and agent definitions — and the clause runs as a habit until it is).** No clause claims an enforcement that does
not exist. `check_governance.py --tally` counts the labels; a hand-written count is the
ungraded claim §0.2 forbids. Every clause carries `[GATE: <script>]` (a machine refuses the
violation), `[HABIT]`, or `[PENDING (B3): <enforcer>]`; §0.21 is the gates table.

**Lifecycle:** DECIDE → DISPATCH → SLEEP → RECEIPT → DECIDE. Sonnet leads and helpers
execute; the Lead decides; machines judge. The Lead is a decision authority, not a progress monitor.
### 0.0 When this governance does not apply, and where the Lead stops [HABIT]

A question, a decision or a read-only look that one context answers is answered by the Lead
directly: briefs, tiers and receipts are pure overhead on it. **Anything that builds, fixes,
scripts, harvests, records or probes is a worker's job, whatever its size** (owner, 2026-10-16:
the Lead writes admin files only). Proportionality stays: a task with `ITEMS` < 6 (§0.6) is
ONE Sonnet lead with no helpers; fan-out begins only when the work exceeds one context, two or
more lanes write disjoint file sets on the critical path, a cheaper tier can do a bounded part
reliably, noisy output must be contained, or risk demands independent verification. A
governance that cannot say "not here" is a ritual.

### 0.1 Roles: the Lead decides, Sonnet leads build, Haiku helpers assist [GATE: check_governance]

| Role | Model, effort (ids: runtime-map) | Runs as | May | Must not |
|---|---|---|---|---|
| **Lead** | Opus 5.5, medium | the main session | read receipts; `git diff --stat`, then only risk-high diffs (R-MANAGEMENT-004); run the project's gate commands; decide; brief; `git merge`; push only where the project's CLAUDE.md allows it; deliver; write **admin files only**; Jira review writes (comments, transitions); answer the owner; write the Interpreter line (§0.19) | write or edit deliverable, source or script files; run harvests, records or probes; read a credentials file; poll or sleep on workers |
| **Sonnet lead** | Sonnet 5.5, medium (high only for a diagnosis brief) | background (`run_in_background: true`), completion is the trigger; own git worktree where the project is a repo | author, fix, run gates, brief Haiku helpers, review every helper receipt, commit on its branch | push, merge, touch main, write outside `OWNED_PATHS`, message a sibling, put a credential in a helper brief, end its turn with a child or its own command running |
| **Haiku helper** | Haiku 5.5, low | ONE foreground batch per phase inside a Sonnet lead | mechanical bounded work: grep, read, extract, count, probe, Jira sync, image log; write its one report file | spawn (no `Agent` tool), `git push`/`git merge`, read secrets paths, write outside its report path, decide anything |

**Admin files** (the Lead's only writes): `handoff*.md`, decision and ledger logs, `CLAUDE.md`,
memory files, trackers. The Lead's diff-and-gate review before a merge is the merge gate, not
"self-verification": the Owner's run-once exception (§0.11) is unaffected.

The Lead alone classifies, decomposes, creates Sonnet leads, sets model, effort, scope and
write ownership, decides parallelism, moves ownership, picks reviewers, decides retry and
escalation, synthesises across workers, and adjudicates. A Sonnet lead owns its bounded phase
and decides everything inside it, including whether and how many helpers it briefs (§0.6).
Enforcement today: the brief clause (`check_governance.py --brief` requires exactly one of the
HIERARCHY / NO_SPAWN clauses, matching the TIER/MODEL line) and `relay.py verify`; agent
definitions (`~/.claude/agents/sonnet-lead.md`, `haiku-helper.md`) and the Lead write-allow-list
hook are `PENDING (B3)`.

### 0.2 Evidence grades, and the worker's right to challenge [GATE: check_governance --brief]

*This clause exists because on 2026-09-20 the Lead wrote an inference into a brief as a
verified fact and a worker spent a whole pass disproving it.*

Every factual claim in a brief is graded, in the text:

| Grade | Means | The Lead must |
|---|---|---|
| `[V]` | verified — the Lead read it, this run | cite `file:line`, a command output, or a URL |
| `[A]` | assumed — inference, plausible, unchecked | say what would falsify it |
| `[U]` | unknown — the worker establishes it | say what counts as established |

An ungraded factual claim is a defect the brief gate rejects. **A worker that finds a `[V]`
claim false returns `CHALLENGE: <claim> — <counter-evidence>` and stops that line of work.**
The Lead must re-check against the source before re-dispatching; re-issuing a challenged
claim without new evidence is a **lead-defect**, and it is logged as one (§0.14). A worker is
never penalised for a correct challenge, and never obliged to disprove an `[A]`.

**Both directions are counted.** `lead-defects` records a brief whose `[V]` was disproved;
`false-challenges` records a challenge the source did not support. A path that only ever
scores against the Lead would be gamed in one turn, and a worker that fears the count would
stop challenging — which is the failure this clause exists to prevent.

### 0.3 Depth-2 tree: Lead → Sonnet lead → Haiku helper [GATE: relay.py verify]

Depth 2 is the maximum. A Sonnet lead may brief Haiku helpers (§0.6); **a helper never spawns,
a Sonnet lead never briefs another Sonnet lead, and siblings never talk, instruct, re-scope or
pick a model for one another.** Cross-worker work travels as an artefact **by path**, routed by
the parent: A writes E17 and a receipt; the parent evaluates; the parent briefs B with the
path. Large results never pass through the Lead's context. *Enforcement is honest:* the
runtime does not stop a general-purpose agent from spawning, so the control is after the fact:
`relay.py verify` reads the spawn log `.agent-ops/spawns.jsonl` (one JSON line per spawn:
`ts, parent, child_type, model, depth`) and **fails** an illegal spawn through
`delegation_legal` (Haiku → anything, Sonnet → non-Haiku, depth > 2); a legal Sonnet → Haiku
spawn is not a breach. What stops it before it happens is `PENDING (B3)`: the SubagentStart
hook that writes the log, `haiku-helper.md` without the `Agent` tool, and
`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2`. Mechanics (foreground batch,
background leads, depth env): `reference/runtime-map.md`. The v3 "workers never delegate"
clause is dropped (§0.20).

### 0.3a Trigger-only [HABIT + brief clause]

**HARD RULE (owner, 2026-10-14; kept in v4): agents communicate and report only by triggers, in a hierarchy.**
Every agent, the Lead included, is asleep by default. It wakes only on a trigger: a task
brief from its parent, or a child's completion report (for the Lead: the owner's message or a
Sonnet lead's completion). It works, reports ONCE upward (receipt file + report of at most 25
lines), then sleeps. The parent reviews, then assigns the next task or delivers. No polling,
no peer messages, no progress chatter; anything between siblings is an artefact the parent
routes by path. A Sonnet lead launches its helpers in ONE foreground batch (several `Agent`
calls in one message, never `run_in_background`; in non-interactive mode a nested background
child outlives its launcher and reports to the main conversation) and never ends its turn with
a child or its own command running. Guards: stall bound, budget, `QUESTION n/2` upward; a child
silent past its stall bound is failed and reported, not awaited twice.

### 0.4 What the runtime actually delivers [HABIT — the numbers are gated]

The runtime raises exactly two signals: **a worker returned** and **a command exited**. There
is no generic event callback; a running worker cannot interrupt the Lead. Everything else —
BLOCKER, DECISION_REQUIRED, RISK_DISCOVERED, RETRY_EXHAUSTED, CHALLENGE, MATERIAL_AMBIGUITY,
PHASE_COMPLETE, FINAL_ADJUDICATION — is a **classification the Lead derives from a receipt**,
not something that wakes it. A worker reaches the Lead early only by ending its turn with a
receipt. Ordinary progress reaches nobody, and no turn is spent on "finished yet?", "how
far?", "still rendering?", "monitor alive?". The cost of this is measured, not assumed:
`lead-wakeups / worker-count` is a KPI with a review trigger (§0.15).

### 0.5 Waiting is deterministic, never model-mediated [GATE: relay.py verify]

Builds, renders, recordings, test suites, browser runs and long scripts are waited on by the
runtime or by a script: start → deterministic wait → exit or meaningful timeout → one wake.
A worker waits on its own work inside ONE bounded shell call and **never ends a turn with its
own work still running**. Deterministic supervision stays legal and encouraged — a script
checking mtime, process state, expected artefact or a timeout (`nj-supervise`). Waking the
Lead to interpret "still running" does not. Mechanisms and their limits:
`reference/runtime-map.md` § Waiting.

### 0.6 Counts: write-sets, the 20 ceiling, and the helpers floor [GATE: check_governance --run, relay.py]

Gated today: write-set disjointness (`check_governance --run`, `relay.py claim`), the ceiling (`relay.py slots claim|release|list`: refuses the 21st claim, all roles counted, stale claims expire) and the helpers floor (`relay.py verify`: brief `ITEMS=n` against the Haiku spawns in `.agent-ops/spawns.jsonl`). `PENDING (B3)`: the SubagentStart hook that writes the spawn log.

**Sonnet leads = the number of disjoint write-sets on the critical path.** Not a quota, not a
feeling. **A read-only lane still has a write-set: its report path.** Two lanes that write any
common path are one lane. The brief declares `OWNED_PATHS`; the gate refuses a run whose briefs
declare overlapping paths, and `relay.py claim` refuses the second claim at runtime.
Parallelism is **looked for**, not avoided: independent objectives, disjoint writes, no lane
waiting on another's conclusion, outputs independently auditable, coordination cheaper than the
critical-path saving. Do not parallelise when both lanes chase one root cause, B needs A's
result, or failures reveal the next problem in sequence.

**Ceiling: at most 20 agents at a time, ALL counted** (Sonnet leads + Haiku helpers + nj-rank
workers + any other subagent). A ceiling, never a quota or a target; default shape 4 leads ×
≤ 4 helpers. Slots are claimed with `relay.py slots`, not self-counted; the runtime cap
(`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=20`) is the backstop. Spawn count follows items, never
the cap: a ~20-agent fixed fan-out cost ~1.0-1.3M tokens and half the agents returned the same
tickets (design.md §1). Stagger starts under rate pressure (R-MANAGEMENT-007: ceilings are loop
detectors, not goals).

**Helpers required.** The brief declares `ITEMS=<n>`, the number of independent bounded units
(services, files, tickets, notes). `HELPERS_REQUIRED = 0 if n < 6 else min(4, ceil(n/6))`.
n < 6: zero helpers is correct and the receipt says `helpers_required: 0`. n ≥ 6: the Sonnet
lead must spawn at least the required number. The count is taken from the SubagentStart spawn
log, **not from the receipt**; a mismatch is a `relay.py verify` failure and the Lead
re-dispatches, never accepts. Until the hook writes the log automatically, the spawn lines are appended
by hand; an empty log is "not recorded", never a pass.

### 0.7 A worker owns its whole bounded phase [GATE: relay.py verify]

Targeted inspection → execution → the deterministic verification that phase requires →
bounded correction → re-verification → durable evidence → **one** receipt. The Lead does not
wake for intermediate steps and does not redo a worker's investigation after a valid receipt
unless the evidence is contradictory, incomplete, stale or invalidated.

### 0.8 Routing: verifier first, then tier [GATE: check_governance --brief]

Before choosing a tier, answer one question in the brief: **is there a free verifier for this
stage's output?** — a gate, a schema, a test, an exact count, a diff, a compiler.

- **Verifier exists → cascade is mandatory.** The cheapest plausible tier attempts it, the
  verifier judges, and only the failures escalate (start model and effort per task-class
  from `relay.py route <project> --class C`; Lead moves a failed stage up once with
  `relay.py route --failed "<gate line>" --cause <§0.12 class>`, 2026-10-02). Scoring a checklist, applying a known
  rule, bulk extraction and mechanical fixes all live here. *(Measured 2026-09-15: 14 of 22
  FRONTIER runs — 61 % of frontier spend — were stages of exactly this shape.)*
- **No verifier → route once**, by the reasoning the stage requires, and say so:
  `verifier: none because <why>`. A brief with neither a named verifier nor that sentence is
  rejected by the gate.

The ladder, unchanged and still first: **DETERMINISTIC** (script, CLI, parser, test, git,
counts, exact comparison) → **existing evidence** → **FREE-LOCAL** (only where proven) →
**ECONOMY** (Haiku helpers: extraction, discovery, bounded routine reasoning) → **STANDARD**
(Sonnet leads: implementation to a spec, debugging, focused investigation, review and scoring)
→ **FRONTIER** (ambiguity, architecture, hard root cause, security, data-sensitive change,
high-risk adjudication). **In v4 FRONTIER is the Lead's own tier; it is never a worker tier**
(§0.20): a stage that needs it comes back to the Lead as a receipt. FRONTIER is never chosen
for importance, client visibility, language, or because code is edited. Gates never depend on
the tier. Provider and model names appear only in `reference/runtime-map.md`.

### 0.9 The brief is a contract, not an essay [GATE: check_governance --brief]

**Core brief ≤ 25 lines**, fixed fields, no prose, no pasted standing rules. That is the
*contract header*, and it is not the whole packet: a brief file may carry a spec below it,
and every worker also reads `worker-rules.md`. Measured on this build, a worker's fixed
preamble is ~5.8 KB against v2's ~4.5 KB — **v3's packet is bigger, not smaller**. What the
25 lines buy is a checkable contract, not fewer tokens; claiming context economy for it was
a caption written over a header (audit, 2026-09-22) — those are read
by path, once, by the worker: `templates/worker-rules.md`. Fields: the `REQUIRED_BRIEF_FIELDS`
list in `scripts/check_governance.py` (GOVERNANCE · FOCUS · TASK · OBJECTIVE · VERIFIED_FACTS
(graded, §0.2) · SCOPE · OWNED_PATHS · PARALLEL · VERIFIER · TIER · EFFORT · BUDGET ·
STALL_BOUND · GATES · ENTRY_SMOKE · RESUME · DELIVERABLES · RECEIPT, whose CHANGED line is
also gated). v4 adds `ITEMS`, `HELPERS_REQUIRED`, `BRANCH`, `HIERARCHY` and `CREDENTIALS`
to the Sonnet-lead brief (`templates/worker-brief.md`; `ITEMS=n` is read by `relay.py verify`, the HIERARCHY / NO_SPAWN clause by `check_governance --brief`);
a Haiku helper gets the 12-line `templates/helper-brief.md`. Never the parent conversation, whole-repo
reads, duplicated logs, green test output or raw artefacts the worker can read itself.
Prefer paths, symbols, line ranges, deltas, exception signatures, failed tests, counts.
*Rationale: v2's 4.5 KB brief did not buy compliance — the worker that read all of it still
broke two rules. Length is not obedience; a gate is.*

### 0.10 Review is risk-based [HABIT]

A large diff, an open PR, a long session or a busy worker is not a reason. Independent
stronger review is for security, authorisation, destructive operations, business-rule
ambiguity, data integrity, concurrency, production impact, architecture, and irreversible
client output with no deterministic gate. **Where a deterministic gate can prove the
property, write the gate instead** — it is cheaper and it runs every time.

### 0.11 Verification: waste versus gates [HABIT + Owner exception]

Repeated human or model re-checking of the same output is waste. **Deterministic machine
gates that establish correctness are not optional**, and no safety or integrity gate is
removed to save tokens or time. An Owner's "run once, I verify manually" is a **named
exception in that Owner's CLAUDE.md**, scoped to re-checking only; it never cancels a gate,
and it does not apply where the Owner asked for review or verification in the request itself.

### 0.12 Classify the failure before any retry or escalation [GATE: relay.py verify]

CAPABILITY_LIMIT · CONTEXT_DEFECT · IMPLEMENTATION_DEFECT · TOOL_FAILURE ·
ENVIRONMENT_FAILURE · TEST_FAILURE · AMBIGUOUS_REQUIREMENT · AUTHORIZATION_BLOCKER ·
**LEAD_DEFECT** (the brief was wrong, §0.2). Classify first (R-AUTOMATION-013: test, system
under test, framework, environment; a mass failure is an environment outage until the logs say
otherwise). **Escalate-on-fail:** the Lead (Opus 5.5, medium) starts each stage on Haiku or
Sonnet by the stage's reasoning need; when the verifier fails, the Lead runs
`relay.py route <project> --class C --failed "<gate line>" --cause <class> --ran-on <model>`.
CAPABILITY_LIMIT, IMPLEMENTATION_DEFECT and TEST_FAILURE print ESCALATE: the stage moves up
**once, haiku → sonnet** (row records `escalations=1`). **Opus is not a worker tier in v4:** a
stage already on sonnet prints STOP, the worker reports the failing line, and the Lead
adjudicates (`relay.py route` has `NEXT_TIER = haiku → sonnet` only: a sonnet failure prints STOP and
is the Lead's decision). Any other cause prints STOP. One
escalation max per stage; workers never escalate themselves. Never resend the same prompt;
never spawn a second worker because the first failed; never escalate on an environment failure.
Attempt cap is budget and progress, not a count: continue while the budget has room, every
attempt is a *different* cause-classified fix, and the evidence moved. Stop the moment an
attempt reproduces the same evidence, the budget hits 80 %, or the next fix would leave the
owned paths.

### 0.13 Budgets are ceilings, warnings and loop detectors [GATE: relay.py verify — after the run, uncached input only]

Never quality targets. Correct work is not stopped to hit a number; fewer calls are not
rewarded if correctness suffers; no gate is skipped to fit a budget. Budgets are token and
context figures, per task class; `tool_calls` is a runaway cap only. On overrun: stop, name
the cause (context too wide / duplicate reads / environment rework / capability) and report.

**What no machine does:** stop a running worker at its `tool_calls` cap. `verify` reads the
ledger afterwards and checks uncached input, not calls; a brief that said 60 was followed by
199 calls and nothing intervened. While a worker runs, the cap is a [HABIT] kept by the
worker's own count, and the stall bound (§0.5) is the only other brake.

### 0.14 Telemetry is validated at write time [GATE: relay.py]

*This clause exists because v2's ledger could not answer the question v2 promised it would:
of 311 rows, 58 % had no status, 36 held a task class in the tier column, and `rework=y`
appeared 3 times against 52 failed or partial runs.*

- `relay.py ledger` **refuses** a row whose tier is outside the tier set, whose exec-status is
  empty, or whose numeric fields are not integers. A rejected row is not written.
- A number a worker cannot measure is written `NOT_MEASURED`; a number the runtime hides is
  `NOT_VISIBLE`. **Estimates never occupy a numeric field** — they go in the note, labelled.
  *(v2 measured: a worker reported "~120–140" tool calls against a true 213.)*
- `relay.py batch` writes one calibration row per task, including `lead-defects` and the
  wake ratio.
- `relay.py verify` audits the whole corpus and exits non-zero on an invalid row. A task is
  not complete until its rows pass it.

**What these four gates do not reach.** They read artefacts, so they see a run only once it
has a ledger row and a results directory: §0.7 and §0.12 key off the run-ids found in the ledger.
A batch that writes no ledger row is invisible to them — which is why "every worker launch gets a
ledger row" remains the rule underneath. §0.13 has no budget for DETERMINISTIC or FREE-LOCAL, and
its class budgets are **derived from tool-call estimates, not counter-measured** — an overrun is a
prompt to explain, never a verdict. Absence is never a breach anywhere: an empty field means "not
recorded", or `verify` goes permanently red and stops being read.

### 0.15 KPIs, each with a review trigger [GATE: relay.py verify]

| KPI | Target | Trigger | Basis |
|---|---|---|---|
| `lead-wakeups / worker-count` | ≤ 1.5 | above it twice → the wake design is wrong, not the workers | **none** — lifted from an n=1 kill criterion (observed 2.0 once). A trigger to look, not a number to hit. |
| `lead-defects` per 10 tasks | 0 | ≥ 2 → briefs are asserting inferences; tighten §0.2 | 1 measured instance (2026-09-20). Direction sound, threshold judged. |
| ledger rows failing `verify` | 0 | any → fix the writer before trusting a comparison | measured — 179/311 unscored in the v2 corpus. |
| sibling messages, depth > 2, ceiling > 20 | 0 | any → the clause is not reaching workers | measured — 0 sibling messages across every v2 run; depth is checked from the spawn log (`relay.py verify`) and the ceiling by `relay.py slots`. |
| `helpers_spawned` vs `helpers_required` (ITEMS ≥ 6) | equal or more | any shortfall → re-dispatch (§0.6) | new in v4; spawn log, not the receipt. |
| runs over 1.5× class budget | < 10 % | above → the class is misjudged, re-classify | **weak** — class budgets are themselves estimated from tool calls (§3(f)). |
| cascade escalation rate, where a verifier exists | 10–40 % | < 10 % → the cheap tier was always enough; > 40 % → it never was | **none** — cascade has never run here. Re-derive from the first 10 cascade stages before treating this as a target. |

**An optimisation is an experiment**, argued against a baseline of the same task class in a
ledger that passes `verify`, and accepted only if cost, context, frontier attention, duplicate
work or model calls fall **without** correctness, testing, review, evidence or safety falling.
Total input tokens alone is not the metric. Estimated figures are labelled and never mixed
with measured ones.

### 0.16 A session ends owing nothing [GATE: relay.py sweep]

*the owner, 2026-09-22: never leave leftovers — browsers, agents, tasks, subagents, runs.*

Whatever this session started, this session closes: every browser and persistent profile it
launched, every background command, every subagent, every dispatched run. **A worker never ends
its turn with its own work running (§0.5), and the Lead never ends a task with a worker, a
browser or a background job still alive.** Before reporting a task finished, run
`relay.py sweep <project> --tag <session tag>`: it lists what is still owned and exits non-zero
if anything survives.

Two limits, stated rather than papered over. **Nothing kills what it did not start** — another
session's browser or process is left alone and named in the report, because destroying a peer's
live work to tidy your own is the worse failure. And the Interpreter line (§0.19) is written by
the Lead, so no agent and no slot is spawned for it and there is no interpreter to leave behind.

### 0.17 Git: worktrees, commits, merge, push [HABIT]

Enforcers are `PENDING (B3)`: the PreToolUse deny hook and the merge-on-green wrapper (§0.21).


- Where the project is a git repo, each Sonnet lead runs in its own worktree
  (`isolation: "worktree"`; the Lead creates the repo with `git init`, local only, where a
  project has none: PROJ, with a `.gitignore` for credentials, `settings.local.json`, fonts,
  artefacts, recordings, `node_modules` and Delivery outputs).
- Sonnet leads **commit on their branch only**; never push, merge, `checkout main`, `reset --hard`.
  The receipt carries `BRANCH`, `HEAD` and `CHANGED` taken from `git diff --name-only main...BRANCH`, not memory.
- The Lead reviews `git diff --stat main...BRANCH`, reads the diff only for risk-high paths
  (R-MANAGEMENT-004), requires the project's checks green (R-CI-003: red = no merge, back to
  the same lead), then merges. A receipt or report is written pass or fail (R-CI-001).
- **Push only where the project's `CLAUDE.md` allows a remote push**; a project rule such as
  QA-Wrap's "never `git push`" stays in force.

### 0.18 Credentials [GATE: relay.py leakscan]

Credentials are never printed, echoed into a receipt, written to a scratch file, or placed in
a brief. A **helper never receives a credentials path or value** and never reads a secrets
path (`~/.claude/secrets/*`, `*creds*`, `.env*`). Only a Sonnet lead's scripts read credentials,
in memory, through a `--creds` flag. The Lead never reads a credentials file either. Today this
is a habit plus the `CREDENTIALS` brief line and `relay.py leakscan <paths...>` (scans
receipts, briefs and reports for secrets, prints file:line and pattern name only, never the
value; exit 1 on a hit blocks delivery). The helper tool set and the PreToolUse path-deny hook
are `PENDING (B3)`.

### 0.19 The Interpreter line [HABIT]

Where a project's CLAUDE.md keeps the interpreter rule, every reply opens with
`Interpreter:` (a one-line reading of the owner's message), **written by the Lead itself**. No
Haiku interpreter agent is spawned, so it costs no slot (§0.6) and nothing to sweep.

### 0.20 Dropped from v3 [HABIT]

Superseded, and not to be re-applied from older text: "workers never delegate" and the flat
topology (now the depth-2 tree, §0.3) · "minimum-sufficient, zero workers is the most common
answer" as a licence for the Lead to build (§0.0) · Opus as a worker or escalation tier
(escalation is haiku → sonnet, §0.12) · cron watchdog and monitor polling · "Lead does small
work" (2026-10-04) · Sonnet-only templates · "every worker runs in the background" (now leads
only; helpers are a foreground batch) · self-reported `delegations`/`nested-spawns` as the
control (replaced by the spawn-log `helpers_spawned`) · a Haiku interpreter agent.
Kept from v3: trigger-only reporting, graded facts and CHALLENGE (§0.2), single writers and
claims, budgets as ceilings (§0.13), classify before retry (§0.12), never leave leftovers
(§0.16), credentials never printed, deletions to the recycle bin (`safe-delete`), the
run-once Owner exception (§0.11).

### 0.21 The gates table: what is enforced by which machine [GATE: check_governance, relay.py]

`EXISTS` = built and run today; `PENDING (B3)` = a hook or agent definition, specified in
design.md §3 and not yet built, a habit until then. Pilot before rollout (R-AUTOMATION-004): one
lead with two helpers end to end, then 4 × 4.

| Clause | Enforcer | State |
|---|---|---|
| Brief shape, graded facts, ≤ 25 lines, `VERIFIER` (§0.2, §0.9) | `check_governance.py --brief` | EXISTS |
| Exactly one HIERARCHY (Sonnet lead) or NO_SPAWN (Haiku helper) clause, matching the TIER/MODEL line (§0.3) | `check_governance.py --brief` | EXISTS |
| Disjoint write-sets, runtime claim (§0.6) | `check_governance.py --run`, `relay.py claim` | EXISTS |
| Telemetry, receipts, budgets, KPIs (§0.13-0.15) | `relay.py ledger/batch/digest/verify` | EXISTS |
| One-step escalation haiku → sonnet; a sonnet failure is the Lead's decision (§0.12) | `relay.py route --failed` (`NEXT_TIER = haiku → sonnet`) | EXISTS |
| Legal nesting: Sonnet → Haiku ok, Haiku never spawns, depth ≤ 2 (§0.3) | `relay.py` `delegation_legal`; `verify` over `.agent-ops/spawns.jsonl` (`ts, parent, child_type, model, depth`); `batch --spawns` counts only illegal spawns | EXISTS |
| At most 20 agents, all roles counted (§0.6) | `relay.py slots claim/release/list` (`.agent-ops/slots.json`) + runtime cap | EXISTS |
| Helpers required met (§0.6) | `relay.py verify`: brief `ITEMS=n` vs Haiku spawns logged | EXISTS |
| Secrets never in receipts, briefs, reports (§0.18) | `relay.py leakscan <paths...>` | EXISTS |
| Leftovers (§0.16) | `relay.py sweep --tag` (also lists unreleased slots) | EXISTS |
| The spawn log is written automatically | SubagentStart hook | PENDING (B3) |
| Helpers cannot spawn (§0.3) | `haiku-helper.md` tool set without `Agent`; `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2` | PENDING (B3) |
| Writes only inside `OWNED_PATHS` (§0.1) | SubagentStop hook: `git diff --name-only` vs claim | PENDING (B3) |
| No `git push`/`git merge` by non-Lead agents (§0.17) | PreToolUse hook + `permissions.deny` | PENDING (B3) |
| Helpers cannot read secrets paths (§0.18) | helper tool set, PreToolUse path-deny hook | PENDING (B3) |
| Merge only on green (§0.17) | merge/deliver wrapper script (R-CI-003) | PENDING (B3) |
| Model and effort pinned (§0.1) | `sonnet-lead.md` / `haiku-helper.md` frontmatter; `batch` records the runtime id | PENDING (B3) |
| Lead writes admin files only (§0.1) | PreToolUse hook on Edit/Write for the main agent | PENDING (B3, partial) |
| No polling, report once, risk-based review, decision quality (§0.3a, §0.10) | none: habit, KPI `lead-wakeups / worker-count` | HABIT |

## 1. The Lead loop

**Who leads:** the Lead runs at FRONTIER and decides; it dispatches Sonnet leads (STANDARD)
who brief Haiku helpers (ECONOMY) as §0.6 says, and no worker runs at FRONTIER (§0.8, §0.20).
Routing is verifier-first (§0.8), then by reasoning type; scoring, applying a known rule and
authoring to a spec are STANDARD, and where a free verifier exists they are a cascade. Which
runtime serves which tier: `reference/runtime-map.md`.

1. **Analyse** — deliverable, language, audience, "done" (nj-method step 1).
2. **Choose the path before a worker:** deterministic script/CLI/test/static
   check; existing artefact or evidence; a Sonnet lead for anything that builds or
   fixes (§0.0); helpers inside it by the ITEMS rule (§0.6).
3. **Pick the mode** (§2) only if delegation is needed; the user's last explicit
   mode instruction stands until changed.
4. **Route** by §3, naming only the relevant skill(s) from §4.
5. **Brief** with `templates/worker-brief.md`: numbered rules, file ownership,
   gates, deliverable paths, build/token budgets. A vague brief creates rework.
6. **Verify minimum-sufficient evidence** — a gate line, focused diff, count.
   Never repeat the worker's exploration. Visuals stay with the worker unless
   visual correctness is itself material and cannot be reduced to a check.
7. **Report** once: asked, delivered, not done and why, decisions for the user.

Keep tool output focused: failed tests over full logs, diff hunks over files,
counts over listings.

## 2. The three modes

| Mode | Sonnet leads | Models | When | Verification | Report |
|---|---|---|---|---|---|
| **Standard** (default) | **one per disjoint write-set on the critical path (§0.6)**; helpers by the ITEMS rule; ≤ 20 agents in all | route by §3 | normal work | risk-based gates for touched scope | receipt ≤ 25 lines + detail file (§11.1 r4) |
| **Eco** | **the user's own ceiling: one lead** | STANDARD, helpers ECONOMY for bulk | user asks for economy/one worker/budget, or usage pressure is high | cheapest sufficient checks; one build, one more only if needed | receipt ≤ 25 lines + detail file |
| **Max** | **the user's own ceiling: the N they name** (smallest stated count if Max is named without N), never above the 20-agent ceiling | route by §3 | the user explicitly names a count or asks for heavy research | full gates; independent review only when risk justifies it | receipt ≤ 25 lines + detail file per lead, Lead merges |

**Count is derived, not asserted (§0.6).** Leads equal the number of disjoint write-sets on the
critical path; the fixed ceilings are the 20-agent cap and the ones the user sets (Eco, Max N).
Capacity facts bound it from above: (1) **Lead context headroom** — every completion wakes the Lead
at full context, so the count must keep the session under the ~120k handoff line; (2) **machine
and rate capacity** — two concurrent recorders on this machine, and a shared 5-hour API window that
five open-ended loops exhausted in ~50 min (§5.9, §11.1 r2); (3) **the quality the stage needs** —
one writer per disjoint file set, never two on the same files. Write the chosen count and its
reason in the brief.

**Every worker has a named benefit:** context isolation, a cheaper tier, containment of noisy
output, a specialised capability, a shorter critical path, or independent verification the risk
justifies. A worker with no nameable benefit is not launched, whatever the mode.

Mode phrases: "standard mode" → Standard; "use only one worker" → Eco;
"use N workers" → Max capped at N; "heavy research, only this time" → Max for
that task, then back.

**Script mode (`nj-agent-ops`)** changes result transport and batching, not the count policy: it
inherits the rule above. Its interpreter is the Lead's own `Interpreter:` line (§0.19), not an
agent.

## 3. Routing a stage — the decision procedure

Run this **before writing any brief**. Tiers are capability levels, not
products: **DETERMINISTIC / FREE-LOCAL / ECONOMY / STANDARD / FRONTIER**. Route
to the least expensive tier with demonstrated reliability for the class of work.
**Gates are independent of the tier** — a cheaper tier never means a lighter
gate. Which runtime serves each tier: `reference/runtime-map.md`, read only when
a brief must name one. Skipping this procedure cost 15.8 % of the 2026-09-15
worker day (audit: `<project>/artifacts/ops/model-routing-audit-2026-09-16.md`).

### (a) The ladder — take the first rung that answers the question

1. **DETERMINISTIC** — script, CLI, parser, test, static analysis, git. Always
   deterministic, never a model: counting, filtering, file discovery, exact
   comparison, duplicate detection, log preprocessing, failed-test extraction,
   diff/stat, schema checks, applying a checklist whose rule is exact.
2. **Existing artefact or evidence** — a gate line, an accepted prior report, a
   focused diff already on disk, a ledger row.
3. **FREE-LOCAL** — only for classes it has demonstrably handled reliably here;
   never a first trial on delivery-critical work. (Empty rung on this machine.)
4. **ECONOMY** → 5. **STANDARD** → 6. **FRONTIER**.

### (b) Classify by the reasoning type, not the task title

| The stage requires | Tier |
|---|---|
| mechanical, exactly specified work, verifiable by rule | **DETERMINISTIC** |
| extraction, summarisation, discovery, bounded routine reasoning, low-risk test generation | **ECONOMY** |
| implementation to a spec, debugging, focused investigation, normal review/scoring | **STANDARD** |
| ambiguity, architecture, hard root cause, security, production- or data-sensitive change, complex orchestration, high-risk adjudication | **FRONTIER** (the Lead's own tier in v4; it comes back to the Lead as a receipt, never a worker) |

**FRONTIER is never chosen for importance alone** — not because the output goes
to the client, not because the prose is Arabic, not because code is edited. The
brief states the specific reasoning capability required, or it is not FRONTIER.

### (c) Two downgrades — both proved on 2026-09-15

1. **A review that is mostly scoring is STANDARD.** Six FRONTIER reviews that
   day returned pass/fail cells against a fixed checklist. STANDARD scores every
   cell; **FRONTIER then reads ONLY the failed or disputed cells** — a separate
   short run, never a re-read of the whole document.
2. **Authoring from a model or a spec is STANDARD, even in Arabic.** The day's
   single most expensive run (157 tool calls) was a FRONTIER authoring pass.

### (d) Two upgrades

1. **A stage that has failed twice for the same cause** — upgrade the *cause*,
   not the task: the stage returns to the Lead as a receipt for the root-cause call (FRONTIER is the Lead's tier, §0.8), then the fix goes back to
   STANDARD. An *environment* failure is never upgraded at all
   (`reference/high-rework.md`).
2. **A stage whose output goes to the client with no gate behind it.** If a gate
   can be written instead, write the gate and stay STANDARD — cheaper and
   reusable.

### (e) Effort — named in every brief

Effort is set by the **stage**, not the tier. A STANDARD stage can be high
effort; **a FRONTIER stage is never low** (if it were, it was not FRONTIER).

| effort | means | typical |
|---|---|---|
| `low` | read once, apply, stop; no exploration, no alternatives | listings, deliveries, renames, interpretation |
| `medium` *(default)* | verify at the cheapest checkpoint, one build, one look | applying a fix list, rebuilding, scoring |
| `high` | root-cause, reconcile sources, adjudicate, argue the alternative | rule derivation, unknown failures, client reconciliation |

Paste into the brief:

> **Effort: medium — verify each fix at the cheapest checkpoint (JSON/grep/gate
> line) before any build, one build, one look; do not explore beyond the files
> named above.**

(Or `low — read the named files once, apply, stop`, or `high — establish the
cause from evidence before changing anything; name the alternative you rejected
and why`.)

This field sets the *work* depth: exploration, alternatives, number of builds. It
is not the API `effort` parameter, which a worker cannot change from its brief —
a worker's model and API effort come from the `Agent` call's `model` and the agent
definition's frontmatter (`reference/runtime-map.md` § Claude Code mechanics). Do
not add "think harder / think less" prose. If a stage needs deeper reasoning, route
it to a stronger tier. The Lead's own API effort is set at session start (the
FRONTIER runtime's default is in `reference/runtime-map.md`; `xhigh`/`max` only
where a measured gain exists) and recorded in the batch row.

### (f) The budget line — tokens and context, not tool calls

Tool calls are **a runaway cap only**: measured 2026-09-16, a run under the call
cap was still 2–3× over budget on wide reads.

> `Tier: <tier> because <reasoning type>; effort: <level>; budget: uncached input ≤ <N>, output ≤ <M>, model calls ≤ <K>, files/context read ≤ <F>; tool_calls ≤ <T> (runaway cap only).`

Controlled: cached input, uncached input, output, reasoning tokens, model calls,
files/context read, retries. **When a counter is unavailable, a proxy may be
used and must be labelled** ("est. ≈ tool calls × class rate") — an estimate is
never reported as a measurement.

Class budgets, **derived** from the 2026-09-15 medians (per-run tokens there
were estimated from tool calls, not counter-measured):

| reasoning type | uncached input ≤ | files read ≤ | tool_calls (runaway) |
|---|---|---|---|
| FRONTIER (the Lead's own work; no worker budget in v4) | **150,000** | 25 | 75 |
| STANDARD | **65,000** | 15 | 75 |
| ECONOMY | **12,000** | 8 | 35 |

Output and model-call ceilings are set per brief: no measured baseline exists
yet, and an invented number is not a budget. A brief needing more says so and
says why.

### (g) Overrun — diagnose, never auto-terminate

The worker stops, states the cause; the director acts on the cause:

| cause | fix |
|---|---|
| context too wide | narrow to sections/symbols/diff hunks; name fewer files |
| duplicated reads | reuse the evidence already extracted |
| environment rework | `reference/high-rework.md`, not a tier change |
| **capability / implementation defect / test failure** | `relay.py route --failed … --cause …`: escalate haiku → sonnet once, `escalations=1`; a stage already on sonnet is reported to the Lead (§0.12) |

Any run over **1.5× its class budget** gets a one-line cause note in the
ledger's rework column, and the next brief of that class is tightened. Three
long runs in one class means the class was wrong: re-classify by (b). Never send
judgement to ECONOMY to save tokens; never send bulk to FRONTIER because it
touches code, is Arabic, or goes to the client. Split judgement from execution:
derive once at the stronger tier, apply mechanically at the cheaper one.

## 4. Mapping a task to the skill the worker reads first

The brief names the skill path; the worker reads it **before its first edit**.

| Task | Skill |
|---|---|
| Any deliverable in this repo | the project's `CLAUDE.md`, then its `.claude/skills/*` |
| SRS document, its chapters, tables, figure page | `project-srs` (project) + `workflow-diagram` |
| Verifying a document against the built system | `srs-verifier` |
| The workflow figure itself | `workflow-diagram` |
| PDF from HTML, fonts, copy-paste fidelity | `pdf-typography` |
| Arabic/English wording, proofreading before delivery | `arabic-english-proofreading` |
| Browser automation, portal/back-office walks | the project's e2e skill (e.g. `project-e2e`) |
| Manuals, screenshots, narrated video | the project's manuals skill (e.g. `project-manuals`) |
| Deleting anything | `safe-delete` (recycle bin, never rm) |
| Closing or resuming a session | `session-handoff` + §8 here |
| A lesson learned mid-task | `nj-learn` |
| Installing or auditing a third-party skill / MCP | `nj-security-review` |
| A website before it ships | `website-fine-print` |
| Setting up a new repo or machine | `nj-kit` |
| Challenging a plan before it is acted on | `devil` |

## 5. Context and token economy — every mode

Numbered so a brief can cite them ("apply §5 rules 1–6").

1. **Minimum sufficient context.** Targeted search, symbols, exact line ranges,
   focused diff hunks, failed tests only, unique error signatures. `grep` first,
   then a ranged read. **No full-file read when a section suffices**, no whole
   file over 200 lines, no re-read, **no broad repository read by default**.
1b. **Evidence is extracted once and reused.** The first worker writes the
   extract, the second is given its path. A worker needing more context **asks**
   (`QUESTION n/2:`) instead of reading broadly.
2. **One command per tool call**, never a loop that spawns tools or browsers.
2b. **Batch of the same kind → one script.** More than ~3 reads, greps,
   renames, edits, moves, gate runs or API calls become one Python or PowerShell
   script, run once, printing only counts, failures and paths (write the script
   into your owned path). Twenty tool calls put twenty results in the transcript
   for ever; the script puts one line there.
3. **One typecheck, one build, one look, at most one more build.** A surviving
   small imperfection is a listed item in the report, not a third build.
4. **No sweeps across the set** when one item is in scope.
5. **Reuse the worker** (`SendMessage`) rather than spawning a new one; its
   transcript is the cheapest context there is.
6. **Reports on the §11.1 rule-4 template: a receipt of ≤ 25 lines, plus the stage
   detail file for everything else.** No raw logs, no full files in the receipt;
   the director reads the detail file only when a leftover forces it.
7. **One minimum-sufficient targeted check per result.** Avoid images unless
   visual correctness is the material claim.
8. **No model-mediated polling** (§0.5). The runtime or a script waits; asking
   "done?" costs a full-context turn.
9. **Budget phrases map to measured numbers** (RCA 2026-09-08, §11). A worker's
   cost is `API calls × its context`; the tier sets the rate (cache-read ratio per
   runtime is in `reference/runtime-map.md`: 0.05× on today's FRONTIER runtime,
   0.1× on STANDARD). Measured per worker-hour:

   | shape | measured | ≈ share of a 5-h window |
   |---|---|---|
   | one STANDARD worker, ~150k context, bounded | 4.6M input-equiv, ~\$9 | ~6 %/h |
   | one FRONTIER worker, ~150k context, bounded | 4.0M input-equiv, ~\$20 | ~13 %/h |
   | one FRONTIER worker in a rebuild loop, 250–290k context | 13–20M input-equiv, \$66–100 | **~45 %/h** |
   | five FRONTIER workers in parallel | — | **exhausts the window in ~50 min** |

   So "≤ 13 %/h" = **one STANDARD worker under rules 1–8**, or one FRONTIER
   worker with a hard context budget — *not* one unbounded FRONTIER worker: on
   2026-09-08 three of those cost \$245 between them.

   *Measured 2026-09-08 on a Fable-era Lead; re-baseline before quoting the dollar
   figures for today's FRONTIER runtime: against the FRONTIER+ runtime's list price
   it is 60 % cheaper per input token and 20 % cheaper per cache read
   (`reference/runtime-map.md`).*

## 6. Parallel-batch rules (any mode with more than one worker)

- **Disjoint files, single writer.** Every brief lists the files the worker
  owns and the files it must not touch. A worker needing a shared tool changed
  copies it first (`nj-supervise` clause 1).
- **Shared build output.** When two workers can rebuild the same artefact, say
  so in both briefs: last build wins; on a typecheck failure caused by the other
  worker's half-edit, wait 60 s, retry once, then report.
- **Reviewer → fixer.** One read-only reviewer at the tier §3 gives writes a
  page-referenced fault table **to a file**; the Lead decides, then briefs the
  fixer with that path (§0.3) — the reviewer never instructs the fixer. The
  reviewer edits nothing but its own report.
- **Research worker** writes only under its own folder and produces a rule set
  with sources plus mock-ups; it never edits the renderer.
- Launch independent workers **in one message, before waiting on any**;
  sequential only on a real dependency. Then SUPERVISORY-IDLE (§0.4).
- **Sonnet leads run in the background; helpers run in one foreground batch** (the owner,
  2026-10-16 v4; background-for-leads from 2026-10-11, which superseded the 2026-09-29
  foreground rule). The Lead dispatches each Sonnet lead with `run_in_background: true`; it never
  blocks on one and stays free for the owner's messages. **The trigger method:** a lead reports ONCE,
  and its completion is the trigger (receipt file + report of at most 25 lines, then the
  runtime's task-notification wakes the Lead). The Lead does not poll, sleep or ask
  "finished yet?", and an interrupt from the owner cannot kill a background worker. A lead
  never ends its turn while anything of its own — a helper included — is still running, so the trigger means
  "done". Mid-run changes go as `AMEND:` messages (`SendMessage` to the agent id).
  Independent leads are launched in one message, one wake per batch. Every brief
  carries the `FOCUS` line. Each Sonnet lead takes `isolation: "worktree"` where the project is a repo (§0.17).
  Mechanics (workflows, resume, hooks, concurrency limit, depth env): `reference/runtime-map.md`
  § Claude Code mechanics.

## 7. Guards

- **Runaway loops.** A shell loop that kept opening browsers survived an agent
  stop once and had to be killed at the root. One harvest per command; provide
  and run a stop script (`tools/ops/stop-*.ps1 -Kill`) on every "pause"/"stop".
- **Rate limit (HTTP 429, "session limit")** kills every running worker at once
  and a new one fails the same way. Record state in `handoff.md`
  §files-in-flight and §next-step, tell the user the reset time, and resume the
  **same** agents by `SendMessage` after the reset — their transcripts survive.
  Do not respawn cold.
- **An owner message can kill a worker's running tool call** ("[Request interrupted
  by user for tool use]"); the worker never returns and nothing notifies the Lead
  (seen twice, 2026-09-27). On any progress question, check each live worker's
  transcript tail once (`/tasks`, `/workflows`). If it has not moved within its
  stall bound and the last line is that interrupt, resume the same run from cache
  (`resumeFromRunId` for a workflow, `SendMessage` for an agent); the worker
  continues from its RESUME log. Answer the owner from the journal and file
  timestamps; do not forward the question to a worker. Background dispatch for
  every Sonnet lead (§6, 2026-10-11) avoids this: an owner message does not reach it.
- **Before trusting a receipt**, compare its CHANGED list with `git status`
  (one command). A receipt with no file changes for a writing stage is a failed run.
- **"Pause"** = stop the workers, run the stop script, report the exact state.
- **A worker's "done" is a claim.** The Lead reads one gate line or opens the
  artefact — once, at the wake; it does not redo the investigation (§0.7).
- **Never fabricate** what the user asked to look real (dates, versions,
  approvals); use the real lineage and say so.
- **Retry only by cause, budget not count.** Classify first with the §0.12
  classes (LEAD_DEFECT included) and fix that cause. Never
  resend the same prompt, never escalate the tier except through
  `relay.py route --failed` (one step, once), never spawn a second worker just because the first
  failed. Full stop/question/skip mechanics: `nj-agent-ops` §6 (two questions
  per batch, then `SKIPPED`).

## 8. The handoff

One `handoff.md` **per project, in that project's root**, never shared. Written
with `templates/handoff.md` (six fixed headings) before `/clear`, when context
degrades, or when a rate limit stops work.

On session start, if it exists: **read it first** and continue from
`## next step`. `## failed attempts` is copied into the next brief as a "do not
try" list — that is why the second session is better than the first, not memory.
A stale handoff is worse than none.

## 9. Documenting

- Every non-obvious lesson goes through `nj-learn` into the skill that owns the
  subject, the same turn it is learned.
- The mode, worker count and budget go in the handoff's `## current state`.
- When this skill changes, update `nj-kit` in the same turn (it is bundled there
  and exported to the Desktop copy and the zip).

## Files

- `templates/worker-brief.md` — the brief skeleton.
- `templates/handoff.md` — the six-heading handoff skeleton.
- `reference/runtime-map.md` — tier → runtime for this workspace (on-demand).
- `reference/measurements-2026-09.md` — the incident numbers behind §11 and §14
  (on-demand; read only when a rule is challenged).
- `reference/high-rework.md` — browser / recording / environment-sensitive
  stages (on-demand; read before briefing one).

## 10. Batch the fixes, build once

Apply the whole fix list, verify at the cheapest checkpoint, then one build —
full statement and the measured cost with §11.1 rule 1 below.

## 11. Director token discipline — measured

On **2026-09-08** the project burned **6.6×** what it burned on 09-07 with the
same method: eleven workers ran instead of one, and worker spend went from 13 %
of the day to 88 %. **Director token discipline is worker-brief discipline.** The
rules are here; the measurement behind each one is in
`reference/measurements-2026-09.md` (same numbering), read only when a rule is
challenged.

### 11.1 The rules

0. **Once a phase is dispatched, the Lead manages; it does not execute it**
   (owner, 2026-09-16 20:15). No probes, edits, gates or monitor refreshes from
   the Lead inside a worker's phase; every such step goes into the brief.
   Inside a dispatched phase the Lead does not even do bounded deterministic work: in v4 it
   writes admin files only (§0.1) — a project may not loosen that. **Workers report
   once, at the end** — no progress messages; they stop early only for a
   `QUESTION`.
1. **Every brief carries a build budget and a token/context budget** (tool calls
   are a runaway cap only — §3(f)). Write it: *"apply the whole list, then build —
   two builds maximum; uncached input ≤ 65k, files read ≤ 15; tool_calls ≤ 80 as a
   runaway cap. If you are about to exceed a budget, stop, state the cause and what
   is left — do not abandon the work."* (measured: r1 — worth 55 % of that day's cost)
2. **Parallel only on genuinely disjoint, bounded lanes** (§0.6). Concurrency
   multiplies the *rate* against a **shared** five-hour window; parallelism is for
   bounded disjoint stages, never for open-ended loops. (measured: r2)
3. **STANDARD is the default; FRONTIER must be argued for** by §3, not by feel.
3. **STANDARD is the default; FRONTIER is the Lead's own and must be argued for** by §3, not by feel.
   The Lead derives the rule; a Sonnet lead (STANDARD) applies it to
4. **Reports: a receipt of ≤ 25 lines, plus the stage detail file for everything
   else** (owner, 2026-09-29; the old 150-word cap was dropped 2026-09-16 because it
   truncated findings). The receipt has six headings and the CHANGED list:

   ```
   STATUS:        ok | partial | failed, one clause
   FINDING:       what is true now, in the fewest lines that carry it
   EVIDENCE:      gate lines verbatim, counts, the one number that proves it
   FILES-SYMBOLS: paths (and symbols / line ranges) touched or relied on
   RISK:          what could still be wrong, and for whom
   NEXT ACTION:   the single next executable step, or "none"
   CHANGED:       every path written, from git status or a listing
   ```

   **No raw logs and no full files** in the receipt; findings tables, logs and
   reasoning go to the detail file named in the brief's RESUME line, and **the
   director reads it only when a leftover forces it**. (measured: r4)
5. **Keep images out of the director context unless visual adjudication is
   material.** The worker looks at the PNG and reports the one number or fault —
   "figure is 1,988×1,405, fits A4 landscape, no clipped box". (measured: r5)
6. **One wake-up per batch.** Launch parallel workers in **one message**, have
   each write its result to a file, act when all are done. Write a **complete
   brief**: `SendMessage` is right for *faults*, wrong for drip-feeding a brief.
   (measured: r6)
7. **No model switching mid-session.** Pick the Lead's runtime at the top
   (`reference/runtime-map.md`) and leave it; each model has its own cache.
   (measured: r7)
8. **At ~120k context, or immediately after any compaction, write `handoff.md`
   and `/clear`.** `/clear` costs nothing; `/compact` reads what it summarises.
   Close the session, do not park it past the cache TTL. (measured: r8)
9. **Do not invoke heavy skills from the director.** A skill body loaded there
   sits in context for the rest of the session. Name it **in the brief** (§4).
   Never from the director: `workflow-diagram`, `artifact-design`,
   `frontend-design`, `project-srs`, `pdf-typography`, `workflow-authoring`, the
   project manuals skill, `safe-delete`. The director may invoke only
   `nj-delegate`, `session-handoff` and `nj-learn`. (measured: r9)

### 11.2 One request to the user

> **Please batch instructions into one list.** Every message wakes the director at
> full context, and each change to a live brief restarts a render cycle. One
> message listing the changes costs one wake and one rebuild instead of ten and
> ten. Interrupting is always fine when something is going wrong; it is the
> *drip* that is expensive. (measured: §11.2)

### 11.3 Eco mode, in numbers

One STANDARD worker; uncached input ≤ 65k; ≤ 2 builds; a receipt plus detail
file; no images to the director; one wake at the end — about **10×** cheaper
than the same stage as an unbounded FRONTIER loop, almost entirely from the
budgets, not the tier. (measured: §11.3)

### 11.4 The check that catches this early

Watch one number: **worker share of the day** (healthy days 13–36 %, the bad day
88 %). If a worker has passed 1.5× its class budget (§3(f)) or its runaway call
cap, or has run over an hour, stop it and ask what it is looping on.
(measured: §11.4)

## 12. Proving an optimisation

A change to routing or budgeting is an **experiment**, argued against a
**baseline of the same task class** — comparable runs already in the ledger,
never a feeling or a different class. Accept it only if it reduces cost,
context, frontier attention, duplicate work or model calls **without materially
reducing** correctness, testing, review, evidence or safety; those five are
never traded away. **Total input tokens alone is not the metric.** Report the
class, the baseline runs, the quantities that moved, and the verification result
that did not. Estimated figures are labelled estimated.

## 13. Environment-sensitive work

Browser, recording and environment-driven stages fail for environmental reasons
and are **never auto-upgraded** (2026-09-16: twelve recording attempts lost to
four silently failing helpers). Procedure on demand:
`reference/high-rework.md`.

## 14. Lessons of 2026-09-17 — director rules

Measured in one 22h session; the numbers and the cost ranking are in
`reference/measurements-2026-09.md` §14. These supersede looser prior wording:

- Read `date` before quoting any deadline.
- A verification window is the WHOLE time an element is on screen.
- Never relay a worker's generalisation without its count.
- No sweep without one positive sample first.
- When a new instruction contradicts the previous one on the same point, ask
  ONCE before rewriting code.
- Every worker launch gets a ledger row.
- **A worker never ends its turn while its own work is still running.**
  Wait inside one bounded shell call, no background monitors of your own; the
  worker itself runs in the background and its completion is the trigger (§6, 2026-10-11).
- Not recommended as a fix: more workers, a stronger model for execution, or
  looser gates.
