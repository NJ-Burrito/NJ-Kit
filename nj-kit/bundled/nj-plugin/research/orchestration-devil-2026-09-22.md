# Five orchestration architectures, attacked — 2026-09-22

Devil pass (`nj-kit:devil`) on **NJ Governance v2** against four alternatives.
Read "model" as *orchestration architecture*, not LLM — that is the only reading where
"my model" and "cascade model" are the same kind of thing. Evidence is this workspace's own
measurements; nothing here comes from a benchmark paper.

**Evidence base:** `.agent-ops/ledger.md` (311 rows), `.agent-ops/batches.md` (4 rows),
`artifacts/ops/fable-usage-rca-2026-09-08.md`, `model-routing-audit-2026-09-16.md`,
`session-review-2026-09-17.md`, `nj-supervise` (P1–P4), and run `vct-2026-09-20` (today's two-worker trial).

---

## PROPOSAL

> Route all delegated work through one Lead that alone decides classification, tier, scope,
> parallelism and adjudication; workers own a bounded phase, never talk to each other, and hand
> back artefacts by path; the Lead sleeps between events; worker count is whatever the critical
> path needs; cheapest reliable tier wins; budgets are ceilings; review is risk-based.

Costs: one full-context Lead wake per worker completion, ~4.5 KB of governance boilerplate per
brief, and a Lead that is a bottleneck by design. Buys: no nested fan-out, no context replay,
no duplicate discovery, an auditable decision trail.

## ASSUMPTIONS everything rests on

- **A1** The Lead's classification is better than a worker's local judgement of the same stage.
- **A2** The runtime can actually deliver event-driven wakes (not polling).
- **A3** The ledger/batch telemetry is clean enough to prove or disprove a routing choice later.
- **A4** Worker-to-worker delegation was a real cost driver worth banning.
- **A5** Coordination through the Lead is cheaper than duplicated exploration.

---

## OBJECTIONS (ranked by cost if true)

### 1. The calibration loop is already dead — A3 is false today

*attacks A3 · costs: every future routing and budget decision reverts to taste, which is the exact
failure v2 was written to end.*

§12 and `nj-agent-ops` §5 say an optimisation is proved against a ledger baseline of the same task
class. Measured on the 311 existing rows:

| Check | Result |
|---|---|
| rows with no `exec-status` | **179 / 311 (58 %)** |
| `tier` column holding a task class (`record-build`, `author`, `rootcause`) | 36 rows |
| `role` column holding integers (40, 44, 42, 31 …) | ~20 rows — column drift |
| `rework = y` | **3 rows**, against **52 failed/partial (17 %)** |
| usable duration figures | 50 rows (median 18 min, max 130) |

The corpus that is supposed to settle "was FRONTIER needed here?" cannot answer it. `relay.py`
accepts any string in most columns and never validates a written row.

**Kill criterion:** type-validate all 311 rows against `LEDGER_COLUMNS`; >20 % invalid = loop dead.
*(Already run. It fails.)* **Fix is cheap:** `relay.py ledger` refuses a row whose `tier` is not in
`VALID_TIERS` or whose `exec-status` is empty — ~6 lines, and it is a machine gate, not a habit.

### 2. The Lead is the single point of failure, and it failed today

*attacks A1 · costs: a Lead error is not contained — it propagates into every lane it briefs.*

Run `vct-2026-09-20`: M2 reported blocked at sign-in. The Lead adjudicated, asserted **as a verified
fact** that two records in the credentials file were the applicant accounts, and re-dispatched.
That assertion was an inference from a neighbouring doc, never checked against the login form.
Cost: one wasted pass, ~30k tokens, 5 min, and a worker made to disprove its own correct finding.

Centralisation converts "one worker was wrong" into "everything downstream of this decision is
wrong". v2 has no counter-authority: no worker may challenge a brief, and the only appeal is
`QUESTION n/2`, which M2 had been told not to use for this class.

**Kill criterion:** over 10 tasks, count reworks caused by a Lead adjudication vs by a worker error.
If Lead-caused ≥ worker-caused, centralisation is net-negative and needs a challenge path.

### 3. "Event-driven, no polling" is half-fictional in this runtime — A2 is shaky

*attacks A2 · costs: the headline benefit (minimum frontier attention) is overstated in the document
that is meant to be the source of truth.*

`runtime-map.md` § Waiting already admits there is no generic event callback: only "worker returned"
and "command exited" arrive. Today, from **2 workers**, the Lead took **4 wakes** — one an interim
stop because M1 ended a turn with its own build still running, which then required a liveness check.
A liveness check triggered by a notification is polling with extra steps.
Observed wake-to-worker ratio **2.0** against a design target of 1.0.

**Kill criterion:** `lead-wakeups / worker-count` in `batches.md` across 5 tasks. Staying >1.5 means
the event model is aspirational; write down what the runtime really does instead.

### 4. Routing has no verifier, so a misroute is only ever found by rework

*attacks A5 and the whole deterministic-first ladder · costs: a recurring invisible tax, measured
once at 28 % of a day.*

This is exactly what cascade buys and v2 refuses. v2 picks a tier **once**, from the Lead's reading
of "reasoning type", and §0.12 forbids escalating on failure alone. The 2026-09-16 audit found
**14 of 22 FRONTIER runs (61 % of FRONTIER spend, 28 % of that day)** were stages a cheaper tier
would have done — found by a human audit a day later, not by the system. A cascade catches that for
free *where a cheap verifier exists*. Often none does — but at the places one does (a gate, a schema,
a test), v2 declines to use it.

**Kill criterion:** on 10 scoring stages, run STANDARD-then-FRONTIER-on-disputed-cells against
FRONTIER-direct; compare total tokens and defects found. §3(c)1 already claims this works — it has
never been measured.

### 5. Governance boilerplate now eats the context economy it preaches

*attacks A5 · costs: small at 2 workers, a real tax at 10 — and it demonstrably does not buy compliance.*

Today's brief was ~4.5 KB before a word of task content, and v2 *added* five clauses. M1 read all of
it and still (a) ended a turn with work running, (b) ran 213 tool calls against a 160 cap, (c)
reported "~120–140, estimated" for that count. Longer rules did not produce obedience; they produced
a longer preamble and a worker that estimated its own telemetry.

**Kill criterion:** run one batch with a 15-line brief and the same gates; compare violations.
If violations are equal, the other 45 lines are ritual.

### 6. "Minimum-sufficient, no quota" is unfalsifiable

*attacks A1 · costs: permits silent drift back to the 2026-09-08 shape with no rule broken.*

The old `0/1/max 2` was wrong but auditable — a reviewer could see it violated. "Whatever the
critical path needs, by fit" can justify 1 or 12 after the fact. On 2026-09-08, 11 workers (8 on the
top tier) moved worker share from 13 % to 88 % of spend, and five concurrent workers died together on
one 429. Nothing in v2's wording forbids re-running that day; only the Lead's taste does.

**Kill criterion:** give three fresh sessions the same task and ask for a count plus reason. Spread
> 2 means it is a sentiment, not a rule. **Cheap fix:** keep "no quota", but require the brief to
name the *disjoint write-sets* — the count then falls out of the work instead of the judgement.

### Second-order (one line, unranked)

v2 removes the fan-out ceiling while the historically expensive failure was fan-out onto **shared
code** — `reannotate.ts` patched 9× in a day; P3's worker editing a script other live workers were
reading. Single-writer is *stated* in the brief and enforced by nobody at runtime:
`check_governance.py` validates **text**, never a run.

---

## THE FIVE, COMPARED

| | **NJ v2** (Lead-only, flat) | **Cascade** (cheap→escalate) | **Hierarchical supervisor** (nested delegation) | **Swarm** (peer handoff) | **Monolith** (one agent, no delegation) |
|---|---|---|---|---|---|
| Who decides routing | Lead, once, up front | the verifier, per attempt | each supervisor for its own subtree | whichever agent holds the task | nobody — one model does all |
| Token cost shape | one pass, right tier if the guess is right | cheap pass always, full pass on hard items | lowest per decision, highest in aggregate (re-discovery per subtree) | low coordination, high duplicate context | no coordination cost, huge context cost |
| Latency / critical path | good — parallel lanes dispatched together | **worst** — serial by construction | best raw throughput | good | serial by definition |
| Wasted frontier attention | low *if* routing is right; no self-correction | very low — frontier sees only what failed | high — supervisors are frontier and multiply | medium | total — everything is frontier |
| Error containment | worker errors contained; **Lead errors are not** | contained by the verifier | poor — a bad sub-brief is invisible to the root | poor — nobody holds the whole picture | total: one blast radius, one owner |
| Context economy | strong — artefact by path, no replay | strong | weak — each level re-explains | weak — context travels with the handoff | worst at scale, best for small tasks |
| Observability | good *by design*, **broken in practice** (58 % unscored rows) | excellent — every escalation is a labelled event | poor — nested runs unlogged | poor — handoffs leave no ledger | trivial: one transcript |
| Write safety | single-writer stated, unenforced | n/a | **worst** — nobody owns the file set | bad — ownership moves with control | perfect |
| Scaling limit | Lead context (~120k) and the rate window | verifier quality | supervisor sprawl | coordination entropy | context length |
| Debuggability afterwards | brief + receipt + ledger row | the escalation trail | near-impossible | near-impossible | read the transcript |
| Where it genuinely wins | heterogeneous work, disjoint lanes, auditable delivery | one repeated task class with a **free** correctness signal | huge independent subtrees, cost no object | exploratory research with no delivery bar | anything one context can hold |
| Characteristic disaster | the Lead is wrong, confidently, for everyone | the verifier is wrong → double cost, silently | 2026-09-08: 11 workers, 88 % of spend | shared-file corruption (P3) | one 429 loses the session |

**Cascade is not a rival to v2 — it is a missing component of it.** They answer different questions:
v2 asks *who does this stage*, cascade asks *was that good enough*. v2 has no answer to the second
question at all, which is objection 4.

**Hierarchical supervisor** is the architecture v2 was built to escape, and his own data justifies
the escape: it is the 2026-09-08 shape. **Swarm** is what the no-delegation clause bans; today's
telemetry shows **0 worker-to-worker delegations, 0 nested spawns**, so the ban costs nothing and
removes P3's class of failure. **Monolith** is right more often than the governance admits — today
one agent could have done the whole M1 job without a brief, and the brief did not prevent its two
rule violations.

---

## STRONGEST ALTERNATIVE, argued fairly

**"Delete most of the governance and keep three rules."**

Keep: (1) one writer per file set, (2) every expensive stage leaves an artefact on disk, (3) a
deterministic gate decides done, never a narrative. Drop the tier ladder, the wake taxonomy, the
telemetry schema and the brief template; run a monolith that spawns a worker only when it wants
context isolation.

The case is strong: **every documented disaster in this workspace was a tooling or ownership failure,
not an orchestration-topology failure.** 96 redeliveries against 16 deliveries (masking logic living
in ad-hoc patches). P2's silent zero from a hardcoded path. P1's parked workers. The 6.6× day was
count and tier — both covered by rule 1 plus a budget. The session review's own conclusion was: "not
recommended as a fix: more workers, a stronger model, looser gates." None of those three rules needs
§0's fourteen clauses to state.

Against it: it discards the audit trail a client-facing pipeline needs, and the wake discipline that
ended the 2026-09-16 wake storms. But it is a serious alternative, and v2 has never been measured
against it.

## SURVIVES

- **Flat topology / no worker-to-worker delegation.** Zero observed cost, removes a real failure class.
- **Artefact handoff by path.** Kills context replay outright; nothing in the data argues against it.
- **Budgets as ceilings, never targets**, and the refusal to escalate tier on an environment failure.
- **Risk-based review** instead of automatic frontier review.
- **Run-once scoped to re-checking, never to a machine gate.** The 2026-09-17 finding (96 vs 16) is
  the strongest single piece of evidence in the corpus, and v2 reads it correctly.
- **Honest `NOT_VISIBLE` telemetry** instead of fabricated numbers.

## VERDICT

**Proceed with three changes — do not rewrite.** The architecture is sound; two of its three promises
are currently unbacked.

1. **Make `relay.py` refuse an invalid ledger row** (tier in `VALID_TIERS`, `exec-status` non-empty,
   `rework` set whenever status ≠ ok). Without it, §12 is decoration. *~6 lines, today.*
2. **Add the free-verifier cascade where a gate already exists.** §3(c)1's "STANDARD scores, FRONTIER
   reads only the disputed cells" is written but never measured. Measure it once, on 10 stages. This
   is the one thing cascade has that v2 lacks.
3. **Rewrite §0.4's wake list as "classifications the Lead derives from a receipt"** (partly done) and
   delete any implication that a running worker can raise an event. Record the observed wake ratio,
   not the intended one.

**Stop and test one thing first:** the 15-line brief against the 60-line brief, same gates, same task
class. If violations come out equal, objection 5 is confirmed and half the governance is ritual that
every worker pays for.
