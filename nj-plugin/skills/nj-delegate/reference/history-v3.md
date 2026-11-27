# NJ Governance v3: the text v4 reworded or retired (history, not policy)

Moved here verbatim from `SKILL.md` when it became NJ Governance v4 (2026-10-16). Nothing in this file is
current policy; the live rules are `SKILL.md` section 0 and `team-topology.md`. Line references below are to
the v3 `SKILL.md` of 2026-10-11 (the 2026-09-22 text plus the SDLC owner exception). Read this only when a v4
clause is challenged and you need to see what it replaced.

## What v4 changed, in one table

| v3 | v4 |
|---|---|
| The Lead is the sole orchestrator and may do bounded work itself | The Lead decides, dispatches, reviews, merges, pushes, reports and writes no product file (0.1, 0.20) |
| 0.3 flat topology, one named exception for six `sdlc-*` stage agents | A tree of depth 2 for every team agent; helpers spawn nothing (0.3) |
| 0.6 "There is no ceiling and no floor" | Ceiling 20 live (platform cap), operating wave 10 (0.19) |
| 0.12 Haiku-to-Sonnet escalation by the Lead (ESCALATE) | A failed helper is redone once by its team agent; a failed team agent STOPs (0.12) |
| Tags GATE and HABIT only | GATE, LINT, HABIT, and a GATE needs a trace and a killed mutant |
| 25-line brief, 20 fields | 28-line brief, ROLE/HELPERS/GIT added, STALL_BOUND and PARALLEL folded in (0.9) |
| Git rights silent | Agents commit on their own branch; only the Lead merges and pushes (0.18) |

## v3 0.0 (the "default to no governance" clause, pre-reword)

#### v3 0.0 When this governance does not apply [HABIT]

**Default to no governance.** If one context can hold the task and one agent can finish it,
that is the correct architecture — briefs, tiers and receipts are pure overhead on it.
Delegation begins only when at least one is true: the work exceeds one context; two or more
lanes write disjoint file sets and both are on the critical path; a cheaper tier can do a
bounded part reliably; noisy output must be contained; or independent verification is
required by risk. **Zero workers is the most common correct answer, and choosing it is not
a failure to delegate.** A governance that cannot say "not here" is a ritual.


## v3 0.1 The Lead is the sole orchestrator

#### v3 0.1 The Lead is the sole orchestrator [GATE: check_governance]

The Lead alone classifies, decomposes, creates workers, sets tier, effort, scope and write
ownership, decides parallelism, moves ownership, picks reviewers, decides retry and
escalation, synthesises across workers, and adjudicates. Workers execute inside a bounded
phase and decide everything inside it.


## v3 0.3 Flat topology, with the named owner exception

#### v3 0.3 Flat topology — no worker-to-worker delegation [GATE: check_governance, receipt field]

A worker never intentionally spawns, delegates to, instructs, re-scopes or picks a model for
another worker, and never hands ownership to one directly. Topology is Lead → A, Lead → B,
Lead → reviewer C; never A → B. Cross-worker work travels as an artefact **by path**, routed
by the Lead: A writes E17 and a receipt; the Lead evaluates; the Lead briefs B with the path.
Large results never pass through Lead context. *Enforcement is honest:* the runtime does not
block nested spawning — the brief clause plus `delegations` in the receipt (expected 0) is
the whole control, and the gate checks that the clause is present and the field is reported.

**Named owner exception (Nader, 2026-10-11): the SDLC stage agents.** `sdlc-requirements`, `sdlc-design`,
`sdlc-build`, `sdlc-test`, `sdlc-review` and `sdlc-release` (permanent Sonnet 5.5, `~/.claude/agents/`) may
each spawn Haiku 5.5 helpers; helpers spawn nothing and return files. Stage agents still never delegate to
or instruct one another; the Lead routes between stages by path. Nothing else is widened. See nj-agent-ops
"SDLC team and triggers".


## v3 0.6 Worker count falls out of write-sets (the paragraph with 'no ceiling')

#### v3 0.6 Worker count falls out of write-sets [GATE: check_governance --run]

**Count = the number of disjoint write-sets on the critical path.** Not a quota, not a
feeling. **A read-only lane still has a write-set: its report path.** A reviewer,
investigator or auditor writes exactly one file and that file is its claim on the
partition — without this the rule divides by zero on the most common review shape, and
this very run is the counter-example that found it. Two lanes that write any common path are one lane, and get one worker. The brief
declares `OWNED_PATHS`; the gate refuses a run whose briefs declare overlapping paths, and
`relay.py claim` refuses the second claim on a path at runtime. There is no ceiling and no
floor — zero, one or many are all correct — but the number is now derived and auditable
instead of asserted. Parallelism is **looked for**, not avoided: independent objectives,
disjoint writes, no lane waiting on another's conclusion, outputs independently auditable,
coordination cheaper than the critical-path saving. Do not parallelise when both lanes chase
one root cause, B needs A's result, or failures reveal the next problem in sequence.


## v3 0.10 and 0.11 as written

#### v3 0.10 Review is risk-based [HABIT]

A large diff, an open PR, a long session or a busy worker is not a reason. Independent
stronger review is for security, authorisation, destructive operations, business-rule
ambiguity, data integrity, concurrency, production impact, architecture, and irreversible
client output with no deterministic gate. **Where a deterministic gate can prove the
property, write the gate instead** — it is cheaper and it runs every time.

#### v3 0.11 Verification: waste versus gates [HABIT + Owner exception]

Repeated human or model re-checking of the same output is waste. **Deterministic machine
gates that establish correctness are not optional**, and no safety or integrity gate is
removed to save tokens or time. An Owner's "run once, I verify manually" is a **named
exception in that Owner's CLAUDE.md**, scoped to re-checking only; it never cancels a gate,
and it does not apply where the Owner asked for review or verification in the request itself.


## v3 0.12 Escalate-on-fail (2026-10-02)

#### v3 0.12 Classify the failure before any retry or escalation [GATE: relay.py verify]

CAPABILITY_LIMIT · CONTEXT_DEFECT · IMPLEMENTATION_DEFECT · TOOL_FAILURE ·
ENVIRONMENT_FAILURE · TEST_FAILURE · AMBIGUOUS_REQUIREMENT · AUTHORIZATION_BLOCKER ·
**LEAD_DEFECT** (new: the brief was wrong — §0.2). **Escalate-on-fail (2026-10-02):** workers
start on Haiku 5.5 (ECONOMY classes) or Sonnet 5.5 (STANDARD and former FRONTIER classes), floor Haiku, never Opus (model policy 2026-10-10); when the verifier fails, the Lead runs
`relay.py route <project> --class C --failed "<gate line>" --cause <class>`. CAPABILITY_LIMIT,
IMPLEMENTATION_DEFECT and TEST_FAILURE on a haiku stage print ESCALATE: the stage moves up
once to Sonnet 5.5 (row records `escalations=1`); any other cause, or a stage already on sonnet,
prints STOP, the worker reports the failing line and the Lead re-briefs by cause (no Opus worker ever). One escalation max per stage; workers never
escalate themselves. Never resend the same prompt; never spawn a second worker because the first failed;
never escalate on an environment failure. Attempt cap is budget and progress, not a count:
continue while the budget has room, every attempt is a *different* cause-classified fix, and
the evidence moved. Stop the moment an attempt reproduces the same evidence, the budget hits
80 %, or the next fix would leave the owned paths.


## v3 0.13 Budgets (the call-cap paragraph)

#### v3 0.13 Budgets are ceilings, warnings and loop detectors [GATE: relay.py verify — after the run, uncached input only]

Never quality targets. Correct work is not stopped to hit a number; fewer calls are not
rewarded if correctness suffers; no gate is skipped to fit a budget. Budgets are token and
context figures, per task class; `tool_calls` is a runaway cap only. On overrun: stop, name
the cause (context too wide / duplicate reads / environment rework / capability) and report.

**What no machine does:** stop a running worker at its `tool_calls` cap. `verify` reads the
ledger afterwards and checks uncached input, not calls; a brief that said 60 was followed by
199 calls and nothing intervened. While a worker runs, the cap is a [HABIT] kept by the
worker's own count, and the stall bound (§0.5) is the only other brake.

## v3 0.15 KPIs as a table

| KPI | Target | Trigger | Basis |
|---|---|---|---|
| `lead-wakeups / worker-count` | ≤ 1.5 | above it twice → the wake design is wrong, not the workers | **none** — lifted from an n=1 kill criterion (observed 2.0 once). A trigger to look, not a number to hit. |
| `lead-defects` per 10 tasks | 0 | ≥ 2 → briefs are asserting inferences; tighten §0.2 | 1 measured instance (2026-09-20). Direction sound, threshold judged. |
| ledger rows failing `verify` | 0 | any → fix the writer before trusting a comparison | measured — 179/311 unscored in the v2 corpus. |
| worker→worker delegations, nested spawns | 0 | any → the clause is not reaching workers | measured — 0 observed across every v2 run. |
| runs over 1.5× class budget | < 10 % | above → the class is misjudged, re-classify | **weak** — class budgets are themselves estimated from tool calls (§3(f)). |
| cascade escalation rate, where a verifier exists | 10–40 % | < 10 % → the cheap tier was always enough; > 40 % → it never was | **none** — cascade has never run here. Re-derive from the first 10 cascade stages before treating this as a target. |

**An optimisation is an experiment**, argued against a baseline of the same task class in a
ledger that passes `verify`, and accepted only if cost, context, frontier attention, duplicate
work or model calls fall **without** correctness, testing, review, evidence or safety falling.
Total input tokens alone is not the metric. Estimated figures are labelled and never mixed
with measured ones.

## v3 section 1 and 2 intro (who leads, the count facts)

#### v3 1. The Lead loop

**Who leads:** the Lead is Opus 5.5 at effort medium, fixed for the session, and never executes a stage.
Workers are Sonnet 5.5 or Haiku 5.5 only; FRONTIER-class stages run on Sonnet at effort high (Nader, 2026-10-10). Routing is
verifier-first (§0.8), then by reasoning type; scoring, applying a known rule and authoring
to a spec are STANDARD, whoever leads, and where a free verifier exists they are a cascade.
Every worker carries its own budget line and its own gates. Which runtime serves
which tier: `reference/runtime-map.md`.
**Count is derived, not asserted (v3 §0.6).** It equals the number of disjoint write-sets
on the critical path; the only fixed ceilings are ones the user sets (Eco, Max N). Three
capacity facts bound it from above: (1) **Lead context headroom** — every completion wakes the Lead at full
context, so the count must keep the session under the ~120k handoff line;
(2) **machine and rate capacity** — measured on this machine: two concurrent
recorders, and a shared 5-hour API window that five open-ended FRONTIER loops
exhausted in ~50 min (§5.9, §11.1 r2); (3) **the quality the stage needs** —
one writer per disjoint file set, never two on the same files. Write the chosen
count and its reason in the brief. Zero stays valid in every mode.

## v3 5.9 Measured cost per worker-hour (Opus-era runtimes, retired as workers on 2026-10-10)

9. **Budget phrases map to measured numbers** (RCA 2026-09-08, §11). A worker's
   cost is `API calls × its context`; the tier sets the rate (cache-read ratio per
   runtime is in `reference/runtime-map.md`: 0.05× on today's FRONTIER runtime,
   0.1× on STANDARD). Measured per worker-hour: *(the FRONTIER rows were measured on the Opus-worker runtime, retired as a worker model on 2026-10-10; history, not a current runtime)*

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

## v3 11 intro and rule 0 (with the Lead carve-out)

#### v3 11. Director token discipline — measured

On **2026-09-08** the project burned **6.6×** what it burned on 09-07 with the
same method: eleven workers ran instead of one, and worker spend went from 13 %
of the day to 88 %. **Director token discipline is worker-brief discipline.** The
rules are here; the measurement behind each one is in
`reference/measurements-2026-09.md` (same numbering), read only when a rule is
challenged.

0. **Once a phase is dispatched, the Lead manages; it does not execute it**
   (Nader, 2026-09-16 20:15). No probes, edits, gates or monitor refreshes from
   the Lead inside a worker's phase; every such step goes into the brief.
   Bounded deterministic work nobody was dispatched for stays allowed (intro,
   §1.2) — a project may forbid even that in its own CLAUDE.md. **Workers report
   once, at the end** — no progress messages; they stop early only for a
   `QUESTION`.

## v3 14 last bullet

- Not recommended as a fix: more workers, a stronger model for execution, or
  looser gates.
