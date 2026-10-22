# NJ Governance v3, attacked — 2026-09-22

Devil pass (`nj-kit:devil`) on the v3 draft, before it is installed anywhere.
Target text: `nj-plugin-v3/nj-delegate/SKILL.md` §0, `nj-delegate/templates/worker-brief.md`,
`nj-agent-ops/templates/worker-rules.md`.
Baseline it claims to answer: `nj-plugin/research/orchestration-devil-2026-09-22.md` (the v2 pass).
Everything numeric below is counted from those files or from this machine; nothing is estimated.

---

## PROPOSAL

> v2's architecture was right and its *claims* were not, so v3 keeps the topology (Lead-only,
> flat, artefact-by-path, ceilings not targets) and repairs the three promises v2 asserted
> without backing: it marks every clause `[GATE: <script>]` or `[HABIT]` so nothing claims an
> enforcement that does not exist; it grades every fact in a brief `[V]/[A]/[U]` and gives the
> worker a right to challenge a false `[V]`; it derives worker count from disjoint write-sets
> instead of judgement; it makes a cheap-tier-then-verifier cascade mandatory wherever a free
> verifier exists; it validates telemetry at write time; and it opens with permission to use no
> governance at all.

That is a fair statement of what the document is trying to do, and on the evidence it is mostly
the right list of things to fix.

## ASSUMPTIONS everything rests on

- **B1** `[GATE: X]` means the same thing everywhere it appears — a machine refuses the violation
  of the clause, not merely a brief that omits a sentence.
- **B2** Moving a judgement into a declarative field (`OWNED_PATHS`, `VERIFIED_FACTS`, `VERIFIER`)
  removes the judgement rather than relocating it.
- **B3** The fixes borrowed from the v2 pass can be adopted without the measurements that pass
  said were the precondition for adopting them.
- **B4** A parallel tree is a safe place to build a replacement for something that is live in at
  least five locations.

---

## OBJECTIONS (ranked by cost if true)

### 1. `[GATE:]` means two different things, and the weaker one is half of them

*attacks B1 · costs: the reason to install v3 at all. If `[GATE:]` can mean "a linter checks the
sentence is present", then v2's clauses were also gated — by anyone re-reading them — and v3 is
v2 with better labels. This is the same sin v3 opens by accusing v2 of, committed in the fix.*

v3's first line is "a clause is either enforced by a named machine, or it is marked a habit. No
clause claims an enforcement that does not exist." Counted against §0.0–§0.15 (16 clauses):

| Clause | Marker | What a script can actually refuse |
|---|---|---|
| §0.9 brief ≤ 25 lines, fields present | GATE | **the property itself** — length and field presence *are* the clause |
| §0.14 telemetry types | GATE | **the property itself** — the row is not written |
| §0.15 rows failing `verify` | GATE | **the property itself** for row validity; **nothing** fires the six review triggers |
| §0.6 overlapping `OWNED_PATHS` | GATE | **overlap, genuinely** (twice: static + `relay.py claim`); **not the count** — see objection 4 |
| §0.1 Lead is sole orchestrator | GATE | nothing. No script observes who classified a stage |
| §0.2 evidence grades | GATE | that each line carries a grade and `[V]` lines carry a citation *shape*. **Never that the citation is true** |
| §0.3 no worker-to-worker | GATE | that the clause is present and the field reported — **v3 says this itself, in the text, honestly** |
| §0.8 verifier-first | GATE | that a `VERIFIER` line exists, or the words "none because". Not that the verifier is real, free, or sufficient — and **not that the cascade was run** |

So: **4 gates enforce their clause, 4 enforce the presence of conforming text.** They carry the
same marker. §0.3 already writes the honest version in prose ("*Enforcement is honest:* the
runtime does not block nested spawning — the clause plus the receipt field is the whole control")
— that paragraph is the best writing in the document and it should have become a third marker
instead of a one-off apology.

Corroborating detail, small but exactly on point: **the brief commissioning this review states
"Count them: 9 `[GATE:]`, 7 `[HABIT]`". Measured: 8 and 8.** The ninth "gate" is the
`[GATE: <script>]` placeholder in the preamble at line 27; the eighth habit (§0.0) was missed.
The count was written as a fact, ungraded, in a v3 brief, by the author of §0.2. If the split is
fuzzy enough for its own author to miscount it by one in each direction, it is fuzzy.

**Kill criterion:** for each of the 8 gated clauses, write the single command that fails when the
clause is violated *while the brief is well-formed*. Where no such command can be written, the
marker is wrong. Expected: 4 of 8 produce no command.
**Fix, cheap:** three markers — `[GATE]` (machine refuses the violation), `[LINT]` (machine
refuses a brief that omits the text), `[HABIT]`. Nothing else in v3 changes.

### 2. Mandatory cascade adopts, as a requirement, the one thing v3's own source said to measure first

*attacks B3 · costs: a silent quality regression on exactly the output an Owner verifies by hand,
plus serial latency imported by design.*

The v2 pass's objection 4 is the strongest case in it, and its instruction was explicit:
*"Measure it once, on 10 stages"* — and its closing line made cascade one of two things to test
before trusting. v3 skipped from "never measured here" to **"cascade is mandatory"** (§0.8) in one
step. Three consequences the text does not address:

1. **"Free" is free in tokens, not in wall clock.** The v2 pass's own comparison table rates
   cascade latency "**worst** — serial by construction". §0.8 makes that serialisation compulsory
   at every stage where any cheap check exists — and almost every stage has *some* free check (a
   grep, a count, a diff). The clause as written has very wide reach.
2. **An incomplete verifier converts one wrong answer into a green wrong answer.** A schema passes
   a semantically wrong Arabic document; a count passes a file with the right number of wrong
   rows. v2 at least routed a hard stage to a capable tier once. v3 now has a cheap pass, a gate
   that says yes, and no escalation — and nothing in §0.8 or §0.15 detects a verifier that is
   itself wrong. The failure is *silent*, which is worse than a misroute found by rework.
3. **Mandatory removes the Lead's ability to say "this one goes straight to FRONTIER"** in the one
   situation the ladder was written for: ambiguity that a checklist cannot express.

**Kill criterion:** the measurement that was already prescribed — 10 scoring stages,
STANDARD-then-FRONTIER-on-disputed-cells against FRONTIER-direct, comparing total tokens, wall
clock and defects found. If escalation lands outside 10–40 % or defects rise, "mandatory" is wrong.
**Fix:** demote to *"cascade is the default where a free verifier exists; a brief may route once
instead, in writing, naming why the verifier is insufficient"* until that measurement exists.

### 3. v3 is a parallel tree, and v2 is live in at least five places plus two CLAUDE.md files

*attacks B4 · costs: install day produces two canonical §0s, and the one that is read every session
is the one that still says v2.*

Measured on this machine today:

| Location | What it holds |
|---|---|
| `<NJ_PLUGIN_ROOT>\skills\nj-delegate` | v2 source, live |
| `.claude\plugins\cache\nj-kit\nj-kit\1.0.0\skills\nj-delegate` | v2 copy |
| `.claude\plugins\cache\nj-kit\nj-kit\1.1.0\skills\nj-delegate` | v2 copy (the one served) |
| `.claude\skills\nj-supervise` | loose copy, outside the plugin |
| `<NJ_KIT_ROOT>\` | the extracted-zip copy the global CLAUDE.md *requires* be a real folder |

And the text that contradicts v3 the moment v3 loads:

- **Global `CLAUDE.md`:** "Delegation runs on NJ Governance v2 (2026-09-20) — `nj-delegate` §0 is
  the one canonical statement; read it before any brief." A session reads CLAUDE.md every turn and
  the skill on trigger. **CLAUDE.md wins in practice** — so a half-installed v3 yields v3 briefs
  executed under v2 rules.
- **PROJ `CLAUDE.md`:** "Runs by **NJ Governance v2** … is canonical", and "**Every worker brief
  carries:** the line `Governance: nj-governance-v2`". A v3 `check_governance --brief` would reject
  every brief the project CLAUDE.md mandates.
- **The literal string `nj-governance-v2` appears in 16 places across 15 files in the PROJ repo
  alone** — both handoffs, the project CLAUDE.md, 8 live briefs under `.agent-ops/briefs/`, the
  batches ledger (2 hits), two result JSONs, and `workflow-for-review/README.md`.
- The memory note `nj-governance-v2.md` says "sync the plugin cache after edits" — the plugin cache
  is the served copy, and the v3 tree is not in it.
- Every brief's `rules:` line is an **absolute path into `nj-plugin-v3\`**. On install those paths
  move, and every template and pasted brief carrying them goes stale silently (a worker reading a
  missing path does not fail loudly; it proceeds without the rules).
- Secondary, in scope because it is the same failure class: `nj-plugin-v3\nj-delegate\` contains
  **both** `reference\` and an empty `references\`. One typo away from a dead cross-reference.

**Kill criterion:** `grep -rl nj-governance-v2` across `<NJ_PLUGIN_ROOT>`, `<PROJ_ROOT>`,
`<NJ_KIT_ROOT>` and `.claude` on install day. Any hit outside a `_archive`/history section means
two governances are live. Expected today: ≥ 16 in PROJ alone.
**Fix:** one commit or none — v3 tree, both CLAUDE.md files, the nj-kit manifest, the zip export
and the Desktop extraction, plus a one-line `GOVERNANCE_VERSION` check in `check_governance` that
refuses a brief whose version string does not match the installed skill.

### 4. §0.6 does not derive the count; it relocates the judgement into the partition

*attacks B2 · costs: v3's answer to the v2 pass's objection 6 ("minimum-sufficient is
unfalsifiable") is not an answer, so silent drift back to the 2026-09-08 shape remains possible
with no rule broken.*

"Count = the number of disjoint write-sets on the critical path. Not a quota, not a feeling." But
**the Lead chooses the partition**, so the Lead still chooses the count — one level down, and now
with an audit trail that certifies only *non-overlap*, never *necessity*. The gate refuses two
briefs claiming one path. It cannot refuse twelve briefs claiming twelve paths.

Three shapes where it degrades:

- **Work that writes nothing.** A pure research or review pass has no write-set. Taken literally
  the count is 0 and no worker may be launched. The escape is to count the report file — which
  **this very run uses**: DEVIL's entire write-set is one review file the Lead named. Once a
  report path counts as a write-set, *any* count is derivable by naming more report paths. The
  rule's own first application is its counter-example.
- **Two lanes that must both append to one ledger.** Disjointness forces them into one worker even
  when the work is plainly parallel — or forces a per-lane ledger and a merge step that did not
  need to exist. The rule optimises for the gate, not for the work.
- **Forty tiny files.** Nothing in §0.6 bounds the count from the work side; §2's three capacity
  facts (Lead context, rate window, quality) are the only ceiling — and those are the old
  "count by fit" judgement, still present, now in a different section.

To be fair to the clause: disjoint-writes-per-worker is *correct*, it is enforceable, and it kills
P3's shared-file class outright. The overreach is the word **"derived"**.

**Kill criterion:** the v2 pass's own test, re-run against v3 — give three fresh sessions the same
task with §0.6 in hand and ask for a count plus `OWNED_PATHS`. A spread > 2 means the judgement
moved rather than went away.
**Fix:** keep the rule, drop the claim. "Disjoint write-sets are a **ceiling** on the count and a
hard constraint on overlap; they do not establish that a lane is needed. Name the benefit per
worker (§2) as well as the path."

### 5. The challenge path measures only its upside

*attacks B2 · costs: one wasted lane plus one full-context Lead wake per false challenge —
the same ~30k that the lead-defect it prevents cost — and v3 counts the one and not the other.*

§0.2 and R5 are a genuine improvement: v2 had no counter-authority at all, and the 2026-09-20
failure is real. But the mechanism is asymmetric in three ways the text does not acknowledge:

- **A wrong challenge is expensive and invisible.** A worker that misreads a true `[V]` stops its
  line of work, the Lead must re-check against the source (a wake + a re-read), then re-dispatch.
  `lead-defects` is a KPI with a trigger (§0.15); **false challenges are not counted anywhere.**
  A mechanism whose benefit is measured and whose cost is not will always look like it is working.
- **"A worker is never penalised for a correct challenge" is unfalsifiable at the moment it is
  needed** — whether a challenge was correct is exactly what is in dispute, and the Lead is both
  the accused and the judge (§0.1 makes it sole adjudicator).
- **Nobody checks a citation.** `[V]` requires `file:line`, a command output or a URL. A plausible
  wrong `file:line` passes the gate, reads as verified to the worker, and reproduces the
  2026-09-20 failure with a citation attached — arguably *worse*, because the grade now lends it
  authority. The only real check is the worker's own challenge, i.e. the expensive one.

**Kill criterion:** over 10 tasks, log `lead-defects` **and** `challenges-overruled` side by side.
If overruled ≥ confirmed, the challenge path costs more than the defects it catches.
**Fix:** two lines. Add `challenges: confirmed|overruled` to the batch row, and require a `[V]`
citation to be a **re-runnable command or a path+line the worker can open** — not a prose reference.

### 6. Two of six KPI targets have no empirical basis, and three of the load-bearing clauses are habits nobody measures

*attacks B3 · costs: review triggers that fire on noise, rewriting a working design because an
invented threshold was crossed — which is the class-budget sin v3 criticises v2 for, in §0.15.*

Stated plainly, as the brief asked:

| KPI | Target | Basis |
|---|---|---|
| ledger rows failing `verify` | 0 | **Sound.** 0 is not a guess; 58 % invalid rows measured on 311 |
| worker→worker delegations | 0 | **Sound.** Measured 0 today; 0 is the only coherent target |
| `lead-defects` per 10 tasks | 0, trigger ≥ 2 | **Weak — n = 1.** One observed defect in one run (`vct-2026-09-20`). "≥ 2 per 10" is a guess dressed as a threshold |
| `lead-wakeups / worker-count` | ≤ 1.5 | **Weak — n = 1, and circular.** 1.5 is lifted verbatim from the *kill criterion* of v2 objection 3 ("staying > 1.5 means the event model is aspirational"). The only measurement is 4 wakes / 2 workers = 2.0. A number invented to test a claim has become the target the claim is judged against |
| runs over 1.5× class budget | < 10 % | **Weak.** The class budgets themselves are, in §3(f)'s own words, "derived from the 2026-09-15 medians (per-run tokens there were **estimated from tool calls**, not counter-measured)". §0.15 presents a threshold on those estimates without the caveat |
| cascade escalation rate | 10–40 % | **None. Zero.** Cascade has never been run once in this workspace; the v2 pass says so explicitly. Both bounds are invented, and §0.15 attaches consequences to both ("< 10 % → the cheap tier was always enough; > 40 % → it never was") |

And the mirror of the same problem: **§0.0, §0.5 and §0.11 are `[HABIT]`, and the design collapses
if they are not followed.**

- **§0.0 "default to no governance"** is the most load-bearing clause in the document — if it is
  ignored, v3 is pure overhead on every small task — and **there is no KPI counting tasks that
  correctly ran with zero workers.** The one thing v3 most needs to know about itself is the one
  thing it does not measure.
- **§0.5 no model-mediated polling** — the 2026-09-16 wake storms (≈12 full-context wakes in 3
  minutes) are among the most expensive measured failures in the corpus, and the clause against
  them is discipline only. The wake-ratio KPI is a lagging proxy for it, with an n=1 target.
- **§0.11 gates are not optional** — the 96-redeliveries-vs-16 finding is the strongest single
  piece of evidence in the whole corpus, and the clause protecting it is a habit sitting next to
  an Owner exception that a Lead in a hurry can read loosely.

**Kill criterion:** delete every target that cannot cite a measurement, ship the KPI with the
column and **no** target, and set the target after 10 tasks. If a target cannot survive being
blank for 10 tasks, it was doing rhetorical work, not measurement work.

---

## STRONGEST ALTERNATIVE, argued fairly

**"Patch v2 in place with the three changes its own devil pass prescribed, run the two experiments,
and let the rest of v3 earn its way in on results."**

The v2 pass ended: *"**Proceed with three changes — do not rewrite.**"* v3 is a rewrite. Of the
three prescribed changes, two are small edits to the live tree — `relay.py` refusing invalid rows
(the pass costed it at ~6 lines) and rewording §0.4 as classifications derived from a receipt. The
third was explicitly *"measure it once, on 10 stages"*. And the pass's closing instruction was
**"stop and test one thing first: the 15-line brief against the 60-line brief"**.

**v3 skipped both measurements.** It mandated cascade without the 10 stages, and it set the brief
at 25 lines without running the brief-length experiment. The alternative says: make the two safe
edits today, run the two experiments over the next ten tasks, and adopt grading, write-sets and the
25-line contract on evidence rather than on the strength of a good argument. Its case is that this
is precisely the discipline v3 spends 16 clauses demanding of everyone else.

Against it, honestly: it leaves the 2026-09-20 lead-defect class open with no mechanism at all, and
evidence grading is cheap, obviously right, and does not need an experiment to justify. And the v3
tree already exists — holding it costs nothing, so the rewrite is not wasted work. The alternative's
real force is not "don't build v3"; it is **"don't install v3 as a whole on the strength of taste,
having just written a governance whose entire thesis is that taste is what went wrong."**

## SURVIVES

Said plainly, because a critique that finds everything broken is a random-number generator:

- **§0.0 is the best clause in either version.** It is the honest answer to the monolith comparison,
  and the self-defeat charge is weak: a tool that scopes itself out is normal engineering, not a
  contradiction. The v2 pass's finding that "monolith is right more often than the governance
  admits" is conceded in v3's *first* clause. Keep it exactly as written — the only fault is that
  nothing measures it.
- **§0.14 telemetry validation is a real machine gate** and it kills the real defect: 58 % of 311
  rows unscored, `rework=y` 3 times against 52 failures. This alone justifies a v3.
- **§0.4 rewritten as "classifications the Lead derives from a receipt"** is accurate to the
  runtime and says so. v2's wake taxonomy implied events that do not exist; v3's does not.
- **§0.3's honesty paragraph** — naming the limit of its own enforcement — is the standard the
  other seven gates should be held to (objection 1).
- **R9 / `NOT_MEASURED` / `NOT_VISIBLE`, and estimates banned from numeric fields.** Strictly better
  than v2, directly traceable to a measured failure ("~120–140" against a true 213).
- **Disjoint-writes-per-worker as a constraint** (not as a derivation) removes P3's shared-file
  failure class outright.
- **Carried over intact and still undented:** flat topology, artefact-by-path, budgets as ceilings,
  no tier escalation on environment failure, risk-based review, run-once scoped to re-checking and
  never to a gate.
- **The 25-line brief is the right direction** and §0.9's rationale ("length is not obedience; a
  gate is") is correct — it is just untested, and the test was already prescribed.

## VERDICT

**Proceed with named changes.** The architecture is right, the diagnosis of v2 is right, and four
of the sixteen clauses are genuine machine gates where v2 had none. What must change before it is
canonical:

1. **Split the marker three ways** — `[GATE]` / `[LINT]` / `[HABIT]` — and re-mark §0.1, §0.2,
   §0.3, §0.8 as `[LINT]`. Text-only, no code, and it makes the document's thesis true.
2. **Demote §0.8 cascade from *mandatory* to *default, with a written exception*** until the
   10-stage measurement exists.
3. **Delete the cascade 10–40 % target** and mark the wake-ratio, lead-defect and budget-overrun
   targets `PROVISIONAL — n=1` or blank. A KPI with an invented threshold is the exact thing §0.15
   convicts v2 of.
4. **Add `challenges: confirmed|overruled`** to the batch row, and require `[V]` citations to be
   re-runnable.
5. **Install as one commit or not at all** — v3 tree, both CLAUDE.md files, nj-kit manifest, zip,
   Desktop extraction, plus a `GOVERNANCE_VERSION` mismatch check. 16 live references in one repo
   is not a migration that survives being done in halves.

**And take the free measurement that is already running.** This run — two workers, 25-line briefs,
the new rules file, disjoint write-sets — *is* the brief-length experiment the v2 pass asked for,
and nobody declared it one. Count the rule violations in both receipts against the v2 baseline
(M1: ended a turn with work running, 213 tool calls against a 160 cap, telemetry estimated) before
the run is closed. It costs nothing today and it is unrecoverable tomorrow.

---

*Method: `nj-kit:devil`. Six objections, ranked by cost if true, each with a kill criterion.
Counts of gates, habits, file locations and `nj-governance-v2` references were measured on
2026-09-22; no figure in this document is estimated. The scripts under `nj-plugin-v3/.../scripts/`
were read as evidence only and are worker CODE's to write — at the time of reading they were
byte-identical to v2's, so `--brief`, `--run`, `relay.py claim` and `relay.py verify` did not yet
exist. That is a state-of-today fact, not an objection.*
