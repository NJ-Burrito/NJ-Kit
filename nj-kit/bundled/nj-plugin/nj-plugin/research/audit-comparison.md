# Audit of the v2/v3 comparison — author-bias pass, 2026-09-22

Target: `nj-plugin-v3/research/comparison-v2-v3-and-the-field.md`, written by the Lead that
also wrote `nj-delegate/SKILL.md`. Method: `nj-kit:devil`.

**M** = measured by this worker, today, command in the text · **M\[src]** = measured by someone
else, cited, not re-measured here · **J** = judged from structure, no measurement.
Scale unchanged: ●●● strong · ●● adequate · ● weak · ✕ disqualifying.

Every re-score below carries the command or line that produced it. Nothing here is estimated
into a number.

---

## PROPOSAL

> NJ v3 keeps v2's topology and repairs the three promises v2 asserted without backing; scored
> against v2 and four alternative architectures, it wins every aspect where v2 was measured to
> fail, each win backed by a gate that runs; its only unestablished claim is field performance.

That is a fair restatement, and the *direction* is right. The diagnosis of v2 is correct and
four of v3's gates are real machines where v2 had none. What follows attacks the scorecard, not
the architecture.

## ASSUMPTIONS the scorecard rests on

- **C1** A cell marked **M** was measured, and the number in it is the number a machine returns.
- **C2** "Backed by a gate that runs" means the gate refuses the violation of the clause — not
  that the gate exists and exits 0.
- **C3** The harsh scores on v2 (four ✕) describe v2 as written, not v2 as the comparison needs
  it to be.
- **C4** "Unknown" is an honest entry in a row where every rival carries a named disaster.

---

## OBJECTIONS (ranked by cost if true)

### 1. The cell that claims honesty prints a number that is wrong, and it is wrong for the exact reason this whole chain exists

*attacks C1 · costs: the comparison's standing as evidence. If the one cell whose subject is
honest counting is miscounted under an **M** label, no other **M** in the table can be taken on
trust — and the audit cost of re-deriving them all is the whole document.*

Cell: `Honest about enforcement | v3 ●●● 8 gates / 9 habits, derived **M**`.

Measured (M):

```
$ python nj-delegate/scripts/check_governance.py --tally
gates:  8  (+1 prose placeholder)
habits: 9
tally: 8 gates, 9 habits, 0 naming a missing script
```

The core is §0.0–§0.15 — **16 clauses**. 8 + 9 = 17. One clause is counted twice.

Cause, located (M): `check_governance.py:307` filters the preamble placeholder out of the gate
count (`placeholders = [g for g in raw if g.strip().startswith("<")]`); `:309` runs
`re.findall(r"\[HABIT[^\]]*\]", sec)` with no equivalent filter, so it counts the preamble
`[HABIT]` at `SKILL.md:30` as a clause. Ground truth by clause heading (M,
`grep -n "\[HABIT" SKILL.md`): **8 gated clauses, 8 habit clauses**.

Three different counts now exist for the same 16 clauses: the commissioning brief said 9/7,
`devil-v3.md` measured 8/8, the comparison prints 8/9. The comparison's is the only one produced
by a script, and the script is off by one. It is labelled **M**, which is the strongest label in
the document.

Second defect in the same cell, unrebutted from `devil-v3.md` objection 1: 4 of the 8 gates
refuse the property of the clause, 4 refuse only a brief that omits conforming text. The
prescribed fix was a third marker. Measured (M): `grep -n "\[LINT" SKILL.md` → **0 hits**. The
fix was not applied, so the cell still scores a distinction the document does not draw.

**Re-score: ●●● → ●●.** Relative to v2's ✕ (three false claims, measured) the honesty is a real
and large gain; it is not ●●● while its own headline count is wrong and gate/lint are conflated.

**Kill criterion:** add the placeholder filter at `:309` and re-run `--tally`. If it prints
8 and 8, the comparison's number was wrong. *(Already settled by grep; the code fix is one line
and is CODE's, not mine.)*

### 2. Three of v3's gates return 0 on an empty or missing input, and that is also v3's characteristic disaster

*attacks C2 and C4 · costs: the failure mode a whole governance was written to end — a green
that certifies nothing — reappears inside the gates that were supposed to end it. Cost if true
is one full run believing itself audited when nothing was inspected.*

Measured (M), three commands:

```
$ python nj-delegate/scripts/check_governance.py --run .agent-ops/briefs/typo-here
run check: 0 briefs, 0 overlap(s)
rc=0
```

`run_run()` (`check_governance.py:268`) globs `*.md` in a directory and returns
`1 if fails else 0`. A mistyped or moved directory is indistinguishable from a clean run. This
is the gate behind `Count is auditable ●●●`.

```
$ python nj-agent-ops/scripts/relay.py verify .
lead-wakeups/worker-count: NOT_VISIBLE (no batch rows with both fields)
lead-defects per 10 tasks: NOT_VISIBLE (no batch rows with lead-defects)
ledger rows failing verify: 0 (target 0)
worker->worker delegations + nested spawns: NOT_VISIBLE
cascade escalation rate: NOT_VISIBLE (no cascade attempts recorded)
rc=0
```

Four of five KPIs are NOT_VISIBLE; the fifth reads 0-against-target-0 on an empty ledger.

```
$ find .agent-ops -type f
.agent-ops/briefs/v3-build/{AUDIT,CODE,DEVIL}.md
.agent-ops/claims/{v3-audit,v3-build}.json
```

**Zero ledger rows. Zero batch rows. Zero receipts on disk.** The run v3 governed wrote no
telemetry at all, while telemetry-validated-at-write is v3's headline fix.

To be fair to `verify`: printing NOT_VISIBLE rather than inventing a figure is exactly right, and
strictly better than v2's 179/311 unscored rows **M\[v2 devil]**. The defect is the rc, not the
prose.

This also answers the brief's question about the `Characteristic disaster` row. **"Unknown" is a
free pass**, and it is the only cell in the table that opts out of being scored. Every rival
carries a disaster derived from structure or history; v3 can be held to the same standard. From
the three commands above, derived (J, from M inputs):

> **v3's characteristic disaster: a degenerate-input green.** A gate exits 0 because it inspected
> nothing — a missing brief directory, an empty ledger, a `[V]` citation whose shape is checked
> and whose truth is not (`devil-v3.md` obj 5) — and the run is certified by a scorecard of
> greens over an empty corpus.

That is worse-shaped than v2's disaster, not better: v2's Lead is wrong *loudly* and costs a
pass; v3's gates are wrong *quietly* and cost the audit trail that justified the rewrite.

**Re-score:** `Count is auditable` ●●● → **●●** (overlap is genuinely auditable; the count is
not — see objection 4 of `devil-v3.md`, and this run is its own counter-example: AUDIT's
write-set is one report file the Lead named). `Observability` ●●● → **●●**.
`Characteristic disaster` **unknown** → **degenerate-input green — a gate that passed on nothing**.

**Kill criterion:** make `--run` exit 1 on 0 briefs and `verify` exit 1 when a KPI it is asked
for has no rows. Re-run both against `.agent-ops/briefs/typo-here` and an empty ledger. Two rc-1s
means the ●●● was scoring a filter that had never been handed anything.

### 3. "Context economy ●●● 25-line contract" measures one of three parts; the measured per-worker preamble went **up**

*attacks C1 · costs: v3's clearest-sounding win is the one the table gets backwards, and the
whole point of the 25-line rule (the v2 pass's objection 5) is left untested while being claimed
as won.*

Measured (M), `wc -c -l` on the three real briefs of the only run v3 has governed:

| brief | whole file | contract header | worker-rules.md (mandatory) | preamble a worker reads |
|---|---|---|---|---|
| AUDIT.md | 74 lines / 5,495 B | 23 lines / 2,325 B | 56 lines / 3,491 B | 5,816 B |
| CODE.md | 71 lines / 6,062 B | 22 lines / 2,456 B | same | 5,947 B |
| DEVIL.md | 47 lines / 4,328 B | 22 lines / 2,223 B | same | 5,714 B |

Two things the ●●● hides:

1. **No real brief is 25 lines.** They are 74, 71 and 47. `check_governance --brief AUDIT.md`
   returns rc 0 on the 74-line file, because `_contract_block()` reads only the header — its own
   docstring says so: *"Prose after the block is documentation and is ignored."* The gate is
   sound; the cell's caption is not. The contract is 25 lines; the brief is not.
2. **The preamble grew.** v2's measured brief was ~4,500 B before task content **M\[v2 devil]**.
   v3's header plus the mandatory rules file is **5,816 B** (M, AUDIT) — about +29 %. v3 moved
   text out of the brief into a file every worker must still read, and scored the move as a
   reduction. The 5,816 B is an upper bound on governance-only text, since the header carries
   task-specific field values; v2's 4,500 B is cited, not re-measured here.

The underlying economy — artefact by path, no context replay — is real, and it is *carried over
from v2 unchanged*. Both should carry the same mark.

**Re-score: v3 ●●● → ●●, caption "25-line contract" → "25-line contract header; brief 47–74
lines **M**"**. v2 stays ●●●? No — v2's 4.5 KB brief bought 4 measured rule violations
**M\[v2 devil]**. Both ●●, for opposite reasons: v2's preamble was long and disobeyed, v3's is
longer and untested.

**Kill criterion:** the experiment the v2 pass already prescribed and both passes have now
skipped — one batch at 15 lines total (header + rules), same gates, same task class, count
violations. Until it runs, neither ●●● nor the claim of a win is available to either column.

### 4. Three ●●● cells score mechanisms that have never fired once, and the run that exists contradicts one of them

*attacks C2 · costs: the reader takes "backed by a gate that runs" to mean "observed working".
For three cells it means "the field is required to be present".*

| Cell | Claimed | What has actually happened |
|---|---|---|
| `Error containment ●●● challenge path` | a worker can contest a false `[V]` | **0 challenges** in the corpus (M: no receipts on disk at all). The gate enforces grade *shape*; nothing checks a citation is true (`devil-v3.md` obj 5) |
| `Self-correction ●● cascade where free` | mandatory cascade | **0 cascade attempts** (M: `verify` → "cascade escalation rate: NOT_VISIBLE (no cascade attempts recorded)") |
| `Frontier attention wasted ●●● verifier-first` | verifier before tier | **1 real verifier in 3 briefs** (M: `grep "^VERIFIER"` → CODE has a suite; AUDIT and DEVIL both use "none because"). **2 of 3 lanes routed FRONTIER** (M: `grep "^TIER"`) |

The last row deserves the sharpest version: the v2 defect this cell answers is *14 of 22 FRONTIER
runs misrouted* **M\[v2 devil]**. v3's only run put 2 of 3 lanes on FRONTIER with no verifier on
either. In v3's defence — and it is a real defence — both are adversarial judgement, the escape
clause requires the reason in writing, and both wrote one. That is the clause working honestly.
It is not evidence of frontier attention being saved.

**Re-scores:** `Error containment` ●●● → **●●** (a mechanism beats v2's nothing; ●●● needs one
fired-and-correct challenge). `Frontier attention wasted` ●●● → **●●**. `Self-correction`
v3 ●● → **●** (a mandatory mechanism with zero invocations is text).

**Kill criterion:** one confirmed challenge and one cascade escalation, logged with
`challenges: confirmed|overruled` in the batch row. Each restores its cell to ●●●.

### 5. The opposite bias: three of v2's four ✕ marks are harsher than v2's own text

*attacks C3 · costs: smaller than the others, but it is the specific bias the audit was
commissioned to find, and it inflates the v2→v3 delta on three rows at once.*

Checked against v2 as written, not as remembered:

| Cell | Scored | Measured against v2's text |
|---|---|---|
| `Knows when not to apply` ✕ | disqualifying | **False.** `nj-plugin/skills/nj-delegate/SKILL.md:67` (M): *"Minimum-sufficient workers for the critical path: zero, one or many are all…"*. "Zero" is permission not to apply. Weaker than §0.0 and unmeasured, but not absent → **●** |
| `Self-correction ✕ none` | disqualifying | **Overstated.** v2 carries `QUESTION n/2`, cause-classified attempt caps and the "evidence moved" test. Human-triggered and weak → **●**, not ✕ |
| `Count is auditable ✕ unfalsifiable` | disqualifying | **Fair.** This is the v2 pass's own objection 6, measured and conceded. Stands ✕ |
| `Honest about enforcement ✕ 3 false claims **M**` | disqualifying | **Fair.** Measured in the v2 devil pass. Stands ✕ |

Two ✕ are earned, two are not. With v3 re-scored down and v2 up on the same rows, the row
`Knows when not to apply` goes from ✕ vs ●●● (a four-step gap) to ● vs ●● (one step) — v3's §0.0
is still better, and it is still a `[HABIT]` with nothing counting tasks correctly run with zero
workers (`devil-v3.md` obj 6).

The rivals' harsh marks I checked and did **not** overturn: hierarchical ✕ on write safety and
debuggability, swarm ✕ on observability, monolith ✕ on token cost at scale. Each traces to a
measured event in the corpus (2026-09-08's 11 workers / 88 % of spend; P3's shared-file
corruption) **M\[v2 devil]**, and I found nothing arguing the other way. **Cascade is scored
generously, not harshly** — five ●●● for an architecture that has never run here once. Consistent
with the comparison's own note that cascade is a component of v3 rather than a rival, but the
marks are J and should say so.

**Kill criterion:** none needed — this one is settled by reading v2's §0 line 67.

---

## The scorecard, rewritten

Changed cells are **bold**. Every cell carries M (measured here), M\[src] (measured elsewhere,
cited) or J (judged from structure).

| Aspect | **NJ v2** (live) | **NJ v3** (candidate) | Cascade | Hierarchical | Swarm | Monolith |
|---|---|---|---|---|---|---|
| Token cost at scale | ●●● J | ●●● J | ●●● J | ● M\[08-09] | ●● J | ✕ J |
| Latency / critical path | ●●● M\[vct] | ●●● J | ✕ serial J | ●●● J | ●●● J | ● J |
| Frontier attention wasted | ●● M\[audit] | **●● J** — 1 verifier in 3 briefs, 2/3 FRONTIER M | ●●● J | ● M\[08-09] | ●● J | ✕ J |
| Error containment | ●● Lead errors leak M\[vct] | **●● J** — challenge path, 0 fired M | ●●● J | ● J | ● J | ●●● J |
| Context economy | **●● M** — 4.5 KB bought 4 violations M\[v2 devil] | **●● M** — 25-line *header*; briefs 47–74 lines, preamble 5,816 B | ●●● J | ● J | ● J | ● J |
| Observability | ● broken in practice M\[v2 devil] | **●● M** — validated at write (55/55 checks), 0 rows written | ●●● J | ● J | ✕ J | ●●● J |
| Write safety | ●● stated, unenforced M\[P3] | **●●● M — holds**, see SURVIVES | n/a | ✕ M\[08-09] | ● M\[P3] | ●●● J |
| Self-correction | **● J** — QUESTION n/2, weak, not absent | **● M** — cascade mandatory, 0 attempts | ●●● J | ● J | ● J | ●● J |
| Count is auditable | ✕ unfalsifiable M\[v2 devil] | **●● M** — overlap yes; count no; `--run` rc 0 on a missing dir | n/a | ✕ J | ✕ J | n/a |
| Knows when not to apply | **● M** — "zero… " SKILL.md:67 | **●● M** — §0.0, `[HABIT]`, nothing counts zero-worker tasks | ● J | ✕ J | ✕ J | ●●● J |
| Honest about enforcement | ✕ 3 false claims M\[v2 devil] | **●● M** — 8 gates / **8** habits; `--tally` prints 9; no `[LINT]` | n/a | ✕ J | ✕ J | n/a |
| Debuggability afterwards | ●●● J | ●●● J | ●●● J | ✕ J | ✕ J | ●●● J |
| **Token span per delivered unit** | **457,713 tok M\[receipts]** (281,195 delivered + 176,518 blocked ÷ 1 delivered) | **122,442 tok M\[receipts]** (244,883 ÷ 2 delivered) — **different task class, n=2, confounded** | J: C_cheap + e·C_full, e unmeasured | **J: worker share 13 %→88 % of a day** M\[08-09] | J: duplicate context per hop | J: grows with turns — see the interpreter line |
| **Routing latency (request→first dispatch)** | **2.8 min M\[vct]** (17:29:48→17:32:35) | **≈15 min M\[brief]** — design + two briefs | ~0 to first cheap pass, +1 leg per stage J | low at root, compounding per level J | ~0 J | 0 by definition J |
| **Estimate quality (can it forecast?)** | ● J — no mechanism; 20 min est. vs 90 min actual M\[corpus] | ● J — STALL_BOUND and budgets are *ceilings*, §0.13 says so; no forecast added | ●● J — escalation rate is a forecastable distribution, once measured | ✕ J — nested runs unlogged, no basis | ✕ J — no ledger | ●● J — nothing to mis-coordinate |
| Scaling limit | Lead ctx ~120k | Lead ctx ~120k | verifier quality | sprawl | entropy | context length |
| Characteristic disaster | Lead wrong for everyone M\[vct] | **degenerate-input green — a gate that passed on nothing M** | verifier wrong, silently J | 11 workers, 88 % of spend M\[08-09] | shared-file corruption M\[P3] | one 429 ends the session J |
| Verdict | superseded, still live | **candidate; gates real, corpus empty** | component of v3, not a rival | reject | reject (banned) | keep for small tasks |

### The two new metrics, stated properly

**TOKEN SPAN CONSUMPTION.** Denominator chosen: **one delivered unit of work** — a worker phase
that ended in an accepted artefact. Failed and blocked work stays in the numerator, because a
blocked pass is part of the cost of the delivery that followed it. On the receipts handed to me
(M\[receipts] — I did not re-measure them):

- v2: 281,195 (M1, delivered) + 176,518 (M2, blocked) = **457,713 per delivered unit**, 1 delivered of 2.
- v3: 126,978 (CODE) + 117,905 (DEVIL) = 244,883, **122,442 per delivered unit**, 2 delivered of 2.
- Ratio 3.74×.

**Do not read that as a governance result.** Three reasons, all of which must travel with the
number: (i) different task classes — M1/M2 drove a browser (213 tool calls, screenshots and DOM
snapshots dominate the token count), CODE/DEVIL read and wrote text in one repo; (ii) n=2 per
arm; (iii) **Lead tokens are NOT_VISIBLE and the cached/uncached split is NOT_VISIBLE**, so the
orchestration overhead the metric is named for is precisely the part not in it. The honest claim
is: *on the only evidence available, v3's delivered units were cheaper, on work that was also
intrinsically cheaper.*

The interpreter line is the more important finding. It runs on every user message under **both**
governances and has gone **37,438 → 57,517 and rising** M\[receipts]. It is a function of
conversation length, not of architecture, and at ~50k per message it exceeds a whole v3 worker
phase every two or three messages. Two consequences: any per-message overhead attributed to v2 or
v3 is unattributable, and the rising curve is measured evidence for the *monolith* cost shape —
the one architecture whose cost is context re-sent per turn.

**TIME ROUTING ESTIMATION — two separate things, not merged.**

*(a) Routing latency.* v2: **2.8 min** M\[vct]. v3: **≈15 min** M\[brief] — design plus two
briefs. v3 is roughly 5× slower to first dispatch, and the comparison's `Latency ●●●` scores the
parallel lanes while ignoring the ramp. Structural consequence (J): for any task shorter than
about 15 minutes, v3's routing latency exceeds the work — which is not a defect, it is §0.0
telling you to use a monolith, and the table should say so rather than scoring v3 ●●● on latency
unconditionally.

*(b) Estimate quality.* The corpus has two data points: a 1-unit pilot estimated at 20 min against
a **90 min** actual (4.5× under) and 50 usable ledger durations with a median of 18 min against a
max of 130 (7.2× spread) — both M\[corpus]. Judged (J), and marked J because no architecture here
has ever produced a forecast that was scored: **neither v2 nor v3 has an estimation mechanism at
all.** v3 adds STALL_BOUND and per-service budgets, and §0.13 explicitly calls them ceilings and
loop detectors, *never targets* — so they are deliberately not forecasts. v3's estimate quality is
identical to v2's: ●. Cascade scores highest (●● J) only because an escalation rate, once
measured, is a distribution you can forecast from; it has never been measured. Hierarchical and
swarm are ✕ because nested runs and peer handoffs leave nothing to forecast from.

---

## STRONGEST ALTERNATIVE, argued fairly

**"The comparison is fine; an author scoring their own work with M labels and a public
scorecard is already an unusually honest act, and this audit is re-litigating a document that
volunteered its own weaknesses in §3 and §5."**

It has real force. §3 lists v3's holes in the author's own words — never run on real work, nine
unmeasured habits, cascade never run, two judged KPI targets. §5 says the field comparison is
n=2 and confounded, unprompted. A biased author does not write those paragraphs. Every finding
in this audit except objections 1 and 3 is an *emphasis* dispute: the caveats exist in the prose
and are missing from the cells, which is a presentation fault, not a fabrication.

Against it, and this is why the audit still pays: **a scorecard is read as the cells, not the
prose.** A reader deciding whether to install v3 reads fifteen ●●● and one "unknown". The prose
that qualifies them is two sections away and does not travel when the table is quoted. And
objections 1 and 3 are not emphasis: one number is wrong under an **M** label, and one caption
describes a 25-line brief that does not exist in any of the three briefs written.

## SURVIVES

Said plainly, because a reviewer who finds bias everywhere is as useless as one who finds none.

- **Write safety ●●● is fully earned.** Measured here, just now:
  `relay.py claim . v3-audit --agent FAKE --paths research/audit-comparison.md` →
  `claim REJECTED: FAKE:research/audit-comparison.md overlaps AUDIT:research/audit-comparison.md`,
  rc 1, both agents named. Runtime, not text. This is the cell that most deserved attacking and
  it holds without qualification.
- **The 55 tests are real.** `python tests/test_v3.py` → `TESTS: 55 passed, 0 failed` (M). 55
  assertions across 38 test functions; "55 tests" is loose phrasing, not a false claim.
- **`relay.py verify` prints NOT_VISIBLE rather than a number** for four of five KPIs. That is
  the document's own rule (R9) applied to itself at the one moment it would have been convenient
  to break it. Strictly better than v2's 179/311 unscored rows.
- **The §2 defect-by-defect table is sound.** Every v2 defect in it is measured, every v3 answer
  names a script, and the "Proof today" column is checkable — I checked three entries (brief
  gate rc 0 on a real brief, claim overlap rc 1, suite 55/55) and all three matched.
- **§3 and §5 are honest.** The author wrote down "never run on real delivery work", "nine
  habits nothing measures", "cascade has never run once here" and "n=2, confounded by task
  class" without being asked. The bias that exists is in the cells, not in the argument.
- **The direction of every row is right.** I re-scored seven cells and reversed **none**. v3
  beats v2 on every aspect where the comparison says it does; what changed is the size of the
  gap, which shrinks on five rows and is unchanged on the rest.
- **The four harsh marks on hierarchical and swarm are earned**, each traceable to a measured
  disaster in the corpus.

## VERDICT

**Trust the direction; do not quote the cells. Proceed with four named corrections.**

The bias is real but it is *optimism about tense*, not fabrication: nine of v3's cells score a
mechanism that exists rather than a mechanism that has run, and the table gives a present-tense
mark to a future-tense fact. That is the same category as v2's three false claims — smaller,
better-documented, and committed by a document whose entire thesis is that this category must
stop. Seven cells re-scored down, two of v2's ✕ marks raised, no row reversed.

1. **Fix `--tally`** (one filter at `check_governance.py:309`) and correct the cell to
   **8 gates / 8 habits**. The comparison currently prints a wrong number under **M** in the cell
   about honest counting. *This is the finding I would act on first.*
2. **Correct the context-economy caption to "25-line contract header".** Real briefs measure
   47–74 lines and the per-worker preamble is 5,816 B against v2's ~4,500 — v3's preamble is
   *larger*. Then run the 15-line experiment both passes have now skipped.
3. **Make `--run` and `verify` exit 1 on an empty input set,** and replace `unknown` in the
   disaster row with **degenerate-input green**. A gate that passes on a missing directory is v3's
   characteristic failure, and it is measurable today rather than after the first real run.
4. **Mark every never-fired mechanism `PROVISIONAL — 0 observations`** in the cell itself, not in
   §3: challenge path, cascade, verifier-first. Restore each to ●●● on its first logged firing.

One sentence on the question the brief actually asked: **the comparison cannot be trusted as
written, and it can be trusted as argued.** Its prose already contains almost every correction
above; its table does not, and a table is what gets quoted.

---

*Method: `nj-kit:devil`. Five objections, ranked by cost if true, each with a kill criterion.
Commands in objections 1–4 and in SURVIVES were run on 2026-09-22 against
`<NJ_PLUGIN_ROOT>-v3` and read-only against `<NJ_PLUGIN_ROOT>`.
Token and latency figures came from the commissioning brief's receipt table and are marked
M\[receipts] / M\[brief] — I did not re-measure them, and no figure in this document is
estimated into a number.*
