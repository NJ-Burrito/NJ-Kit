# Orchestra for a large book

Governance is `nj-delegate` §0 (trigger-only tree, receipts, tiers); this file
holds only what is specific to building a book.

## Topology

- **Default zero workers.** `book_status.py plan --slots N [--reserved R]` prints
  the topology: ≤ 5 items solo, else ⌈items / 6⌉ leads, and **first** the one-wave
  option with the computed `MAX_HELPERS` (37 items at 20 slots: 7 leads +
  7 helpers = 14 workers, one wave), then the full-helper plan in waves (44
  workers, 3 waves). Prefer the one-wave option: the first run's single wave took
  27 minutes; three waves take about 2–2.5 hours. Copy `MAX_HELPERS` into each brief.
- **Service leads (Sonnet):** one per group of ≤ 6 pages (~25k words), groups
  bin-packed by load (pages × depth) to ≤ 1.3 × the mean. Topic grouping in the
  first run gave one lead 11 items (27 min) and another 4 (17 min), and the
  big group caused the cap breach. Group boundaries are disjoint write-sets:
  page paths and `--topic` slugs.
- **Helpers (Haiku):** extraction only (fetch, extract, draft entries) — never
  author pages, never verify. Up to `MAX_HELPERS` per lead; a lead given 0
  extracts itself (first run: a lead with 0 helpers matched the wall time of one
  with 3 — a hypothesis on n = 5, so log `helpers` and per-item minutes).
- **Slots:** leads + helpers + anything else live ≤ 20 per session. 5 leads × 3
  helpers = 20 only if nothing else runs; with a builder or translator live, use
  2 helpers or dispatch in waves (leads 1–2, then 3–5). A resumed agent skips the
  cap check — do not use resume to dodge it.
- **A refused spawn is a stop.** Mark the item `PARTIAL(cap)`, report, the Lead
  re-dispatches it later. The first run's lead that worked around a refusal
  self-extracted and self-verified under an alias: 162 entries had to be re-checked.

## Phases A → V → B (the Lead is the hand-off)

Pages may cite only verified entries, so verification cannot come after authoring,
and a lead may not wait on a worker it did not spawn. Three dispatches:

- **A Extract** — leads (and helpers, `MAX_HELPERS=n` in the brief) fetch, extract,
  `add-batch` draft entries. Receipt → Lead.
- **V Verify + audit** — run as **two sequential foreground calls** (the auditor
  needs the verifier's output; a parallel pair races). One ECONOMY verifier per ~200 entries that **wrote nothing**
  runs `kb.py verify-batch` (the script proves each quote is in its own source's
  raw file) and judges support; then a different run draws and checks the audit.
  The first run's "169 entries in 2 minutes" was the status-flip loop — not a
  baseline. Budget one tool call per ~20 entries in a batch.
- **B Author** — the same leads (new dispatch) write pages and banks from verified
  entries only, then a different run audits the banks (stage 3c). **Generate, don't
  hand-type:** the CTFL rehearsal built a 10,800-word page and its Arabic twin from
  one small generator over the verified entries, so the pair gate held by construction.
- **Rehearse one item** with `--topic` on the audit, not in a DB clone. Measured
  (CTFL, 2026-10-16): lead ~75 calls, five helpers 5–13 calls each, ~30 minutes.

## Budgets (ceilings and loop detectors, never targets)

| Role | tool_calls | stall bound | observed in the QA run |
|---|---|---|---|
| service lead, ≤ 6 pages | 130 | 35 min | 73–119 calls / 17–27 min |
| helper, one item | 60 | 10 min | — |
| translation lead, ≤ 11 pages | 60 | 25 min | 27–47 / 11–19 min |
| research lead, 3 helpers | 100 | 30 min | 18–101 / 9–30 min (one at 71 / 56 min overran) |
| verifier, ~200 entries | 40 | 20 min | estimate (no quote-gated run yet) |
| auditor, one sample | 20 | 15 min | estimate |

Banks add roughly 20–25 % to a phase-B lead (estimate); size groups for it.

A worker at its ceiling writes `PARTIAL(budget)` and ends; the Lead does not
extend a ceiling on a time limit.

## Telemetry

Every worker's result JSON carries `uncached_in, output, tool_calls, minutes`;
where the runtime hides tokens write `NOT_VISIBLE`, never an empty cell. The first
run had one token figure in 31 rows, so nobody can say yet whether helpers pay.

## Brief clauses specific to a book

- `OWNED_PATHS` = the item's research file, `_raw/<slug>/`, page, bank, and KB
  rows with `--topic <slug>` written only through `kb.py`.
- "No alias: author as `<slug>-helper` or `<slug>-lead` and nothing else."
- Name a lead's verifier with a **different prefix** (`advq-verifier`, not
  `adv-verifier`): the part before the first hyphen is the agent identity, so a
  verifier sharing the lead's prefix is refused on every entry the lead wrote (phase A, 2026-10-16).
- "Deep link or no source": bare-root URLs are refused by `kb.py add-source`.
- Batch entries go through `kb.py add-batch file.jsonl` (refuses CR, skips
  duplicates, so a resumed lead can re-run it), never a shell loop.
- Before challenging a file's existence, `test -f`, never `ls` output.
- Fetch only through `fetch.py`; never retry a 429/403 by hand.
- Helpers run in the **foreground** and never background a command: a Haiku auditor
  that ended its turn with a draw still running lost it to the KB lock (CTFL v2).
- The verifier records **weak at verify time** (`weak: true` in the verify-batch row,
  which refuses it). A weak verdict kept only in a markdown judgement file never
  reaches the DB — both CTFL audit misses were entries an earlier judge had called weak.
- Write scripts that carry Arabic or quotes with the Write tool, not a shell heredoc.
- **Never open the KB yourself for writing.** Only `kb.py` writes (60 s busy timeout);
  a driver script that holds a connection while spawning `kb.py` deadlocks every
  group (phase A, 2026-10-16: ~40 minutes lost). Reads use `mode=ro` and close first.
