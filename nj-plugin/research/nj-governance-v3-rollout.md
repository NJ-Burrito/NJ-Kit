# NJ Governance v3 — parallel tree, nothing loads it yet

**v2 is live and untouched.** It runs from `<NJ_PLUGIN_ROOT>\skills\` and the installed plugin
cache; both CLAUDE.md files, the memory notes and the PROJ briefs all still point at it. This tree
is a candidate. Nothing here is loaded by any session until the switch below is run deliberately.

| | v2 (live) | v3 (this tree) |
|---|---|---|
| Source | `<NJ_PLUGIN_ROOT>\skills\` | `<NJ_PLUGIN_ROOT>-v3\` |
| Loaded by sessions | yes, via the nj-kit plugin cache | **no** |
| Canonical text | `nj-delegate/SKILL.md` §0 | `nj-delegate/SKILL.md` §0 |
| Status | production | candidate, under review |

## What v3 changes, and the measured reason for each

v3 exists because the v2 devil pass
(`<NJ_PLUGIN_ROOT>\research\orchestration-devil-2026-09-22.md`) confirmed three defects by
measurement and raised three more that were untestable as written.

| # | v2 defect (measured) | v3 fix | Clause | Enforced by |
|---|---|---|---|---|
| 1 | Ledger unusable: 179/311 rows unscored, 36 with a task class in the tier column, `rework=y` 3× against 52 failed/partial | validation at **write** time; a bad row is refused, not written; `verify` audits the corpus | §0.14 | `relay.py` |
| 2 | The Lead wrote an inference as fact; a worker spent a pass disproving it | evidence grades `[V]/[A]/[U]` + a worker **CHALLENGE** right + a `LEAD_DEFECT` class | §0.2, §0.12 | `check_governance.py --brief` |
| 3 | "Event-driven, no polling" overstated — observed wake ratio 2.0 vs a target of 1.0 | state the two signals the runtime really raises; the rest are receipt classifications; ratio becomes a KPI with a trigger | §0.4, §0.15 | `relay.py verify` |
| 4 | Routing had no verifier — 14 of 22 FRONTIER runs misrouted, found by a human audit a day later | **verifier-first routing**: a free verifier makes cascade mandatory; no verifier means one routed pass and a written reason | §0.8 | `check_governance.py --brief` |
| 5 | A 4.5 KB brief bought no compliance — the worker that read it all still broke two rules | brief is a **contract ≤ 25 lines**; standing rules read by path, once | §0.9 | `check_governance.py --brief` |
| 6 | "Minimum-sufficient workers" was unfalsifiable — it could justify any count afterwards | **count = the number of disjoint write-sets** on the critical path; overlap is refused | §0.6 | `check_governance.py --run`, `relay.py claim` |
| — | Single-writer was stated and enforced by nobody | ownership registry claimed at runtime | §0.6 | `relay.py claim` |
| — | A worker estimated its own telemetry ("~120–140" against a true 213) | `NOT_MEASURED` / `NOT_VISIBLE`; estimates may never occupy a numeric field | §0.14 | `relay.py` |

**The organising rule, and the real difference from v2:** every clause is either `[GATE: <script>]`
or `[HABIT]`. v2's three worst failures were all rules it claimed to enforce and did not. v3 is
allowed to have habits — it is not allowed to call one a gate.

Also new, and the honest answer to the monolith comparison: **§0.0, when this governance does not
apply.** If one context holds the task, the correct architecture is one agent and no brief.

## What survives from v2, unchanged

Flat topology and no worker-to-worker delegation · artefact handoff by path · budgets as ceilings
never targets · no tier escalation on an environment failure · risk-based review · run-once scoped
to re-checking and never to a gate · honest `NOT_VISIBLE` telemetry.

## Verifying this tree

```bash
export PYTHONUTF8=1
cd "<NJ_PLUGIN_ROOT>-v3"
uv run --no-project python tests/test_v3.py                         # the suite, incl. negative controls
uv run --no-project python nj-delegate/scripts/check_governance.py --selftest
uv run --no-project python nj-delegate/scripts/check_governance.py \
    --brief .agent-ops/briefs/v3-build/CODE.md
uv run --no-project python nj-delegate/scripts/check_governance.py \
    --run .agent-ops/briefs/v3-build
```

None of these touch v2, `~/.claude`, or `PROJ-tests`.

## Switching to v3 — deliberate, reversible, one day's work

Do **not** half-install it: a session reading a v2 CLAUDE.md against v3 skills gets the worst of
both. The switch is atomic or it is not made.

### The measured migration surface (counted 2026-09-22, not estimated)

- **15 files in the PROJ project alone still name v2** — both handoffs, the project CLAUDE.md,
  eight live briefs, the batch ledger, two result JSONs and the review package. Every one of them
  is read by a session that would then be running v3 skills under v2 wording.
- **The global CLAUDE.md calls v2 "the one canonical statement"** — and a CLAUDE.md is read every
  turn while a skill is read on trigger, so a half-install means v2 wins the argument it should
  have lost.
- **Two plugin-cache versions serve the skill** (`cache/nj-kit/nj-kit/1.0.0` and `1.1.0`), plus a
  loose `nj-supervise` in `.claude/skills/`, the source tree, and the Desktop copy. Syncing one is
  not syncing the install. The v2 migration already tripped on exactly this: the cache was stale
  and the gate still reported green.

**So the switch is atomic or it is not made.** The single most dangerous state is not v2 or v3 —
it is a session holding one of each.

1. Back up: copy `<NJ_PLUGIN_ROOT>\skills\{nj-delegate,nj-agent-ops,nj-method}` and
   `~/.claude/skills/nj-supervise` into a dated archive folder.
2. Copy this tree's four skills over them.
3. Re-point both CLAUDE.md files at `nj-governance-v3` (the delegation section in each), and add
   §0.2 grading plus §0.9's 25-line contract to the PROJ brief rule.
4. Sync the installed plugin cache from source — otherwise sessions keep loading the old text.
   This was a real finding on the v2 migration: the cache was stale and the gate reported green.
5. Add a `nj-governance-v3` memory note; mark the v2 note historical.
6. Run `check_governance.py` against every project (PROJ, ENSERA, QA-Wrap) and `relay.py verify`
   on each `.agent-ops`. Expect `verify` to fail on the existing PROJ ledger — 311 legacy rows
   predate validation. Decide once: archive them as `ledger-v2.md` and start a clean ledger, or
   accept a permanently red baseline. **Archiving is the right answer**; a KPI that is always red
   teaches people to ignore it.

**Rollback:** restore step 1's archive and re-sync the cache. Nothing in v3 writes to a v2 path, so
a rollback loses only v3's own artefacts.

## What the build itself measured

The v2 pass demanded one experiment before scaling: the short brief against the long one, same
gates. This run was it, and the evidence is n=2 per arm, confounded by task class — evidence, not
proof.

| | v2 brief (~60 lines, 4.5 KB) | v3 contract (25 lines) |
|---|---|---|
| Workers | 2 (media pipeline) | 2 (code + review) |
| Rule violations | **4** — a turn ended with work running · 213 tool calls against a 160 cap · telemetry estimated ("~120–140" vs a true 213) · credentials written to disk | **0** |
| Scope violations | 0 | 0 |
| Self-reported telemetry | estimated into a numeric field | `NOT_MEASURED`, honestly |

It points against the hypothesis that brief length is ritual — but the v3 tasks were also less
error-prone, so the right reading is "not refuted, re-run it on the same task class".

The gate/habit count is **derived, never quoted**: `check_governance.py --tally` says 8 gates and
9 habits, each gate naming a script that exists. It is derived because the number was written by
hand exactly once and both the author (9/7) and the reviewer (8/8) got it wrong — in a governance
whose §0.2 forbids precisely that.

## Open, and deliberately not decided here

- The KPI targets in §0.15 (wake ratio ≤ 1.5, cascade escalation 10–40 %) are **judgement, not
  measurement** — there is no corpus behind them yet. They are written as review triggers, not
  budgets, and the first ten v3 tasks should re-derive them. Treating them as facts would repeat
  the exact sin v2 committed with its class budgets.
- Whether §0.8's mandatory cascade is too strong where a "free" verifier is only nearly free.
- Whether v3 should ship as a second plugin (`nj-kit-v3`) so both can be installed and A/B run.
