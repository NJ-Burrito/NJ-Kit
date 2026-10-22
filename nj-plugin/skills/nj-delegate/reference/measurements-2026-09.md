# Measurements behind nj-delegate §11 and §14 (moved 2026-09-29)

Moved verbatim out of `SKILL.md` so the Lead's loaded context carries the rules, not the
incident numbers (prompt audit 2026-09-29, B-14). Numbering matches `SKILL.md`: rule rN here is
the evidence for §11.1 rule N there. Figures were measured on the 2026-09-08 and 2026-09-17
runtimes (a Fable-era Lead); re-baseline before quoting dollar figures for Opus 5.5.
Where a rule's wording here differs from `SKILL.md`, `SKILL.md` is current (§11.1 r4 was
revised 2026-09-29: receipt ≤ 25 lines plus the stage detail file).

## §11 Director token discipline — measured

On **2026-09-08** the project burned **6.6×** what it burned on 09-07 with the
same method. The director's own spend was flat (12.6M → 8.6M → 10.3M
input-equivalent across 09-06/07/08). **Eleven workers ran instead of one, eight
of them on Opus, several in rebuild-per-fix loops: worker spend went from 13 %
of the day to 88 %.** Full evidence:
`<project>/PROJ-tests/artifacts/ops/fable-usage-rca-2026-09-08.md` (other
projects keep their copy under their own `artifacts/ops/`).

**In one line: director token discipline is worker-brief discipline. The
director's own habits were 14 % of that day; the briefs it wrote were 88 %.**

### 11.1 The nine rules

0. **Once a phase is dispatched, the Lead manages; it does not execute it**
   (owner, 2026-09-16 20:15). No probes, edits, gates or monitor refreshes from
   the Lead inside a worker's phase; every such step goes into the brief.
   Bounded deterministic work nobody was dispatched for stays allowed (intro,
   §1.2) — a project may forbid even that in its own CLAUDE.md. **Workers report
   once, at the end** — no progress messages; they stop early only for a
   `QUESTION`.
1. **Every brief carries a build budget and a token/context budget** (tool calls
   are a runaway cap only — §3(f)). Measured: the three most expensive workers
   made 1,324 API calls and 843 tool uses and ran 36 full rebuilds between them;
   one spent **5 h 06 m on 11 builds and 3 typechecks** of the same PDF. Write
   it: *"apply the whole list, then build — two builds maximum; uncached input ≤
   65k, files read ≤ 15; tool_calls ≤ 80 as a runaway cap. If you are about to
   exceed a budget, stop, state the cause and what is left — do not abandon the
   work."* Worth **55 % of that day's cost**.
2. **Parallel only on genuinely disjoint, bounded lanes** (§0.6). Concurrency
   multiplies the *rate* against a **shared** five-hour window: at 12:55 five
   concurrent FRONTIER workers hit `HTTP 429 — "You have hit your session limit
   · resets 1pm"` and **all five died in the same second**, losing in-flight
   work. That is a capacity fact to weigh, not a worker quota: parallelism is
   for bounded disjoint stages, never for open-ended loops.
3. **STANDARD is the default; FRONTIER must be argued for** by §3, not by feel.
   2,142 of 2,664 worker calls that day ran FRONTIER — **77.5 % of the day's
   cost on one routing choice**. The worker that derives the rule can be
   FRONTIER; the worker that applies it to twelve files is STANDARD.
4. **Reports are short and structured** (revised 2026-09-16 — the old hard
   150-word cap truncated findings that mattered). Six headings, nothing else:

   ```
   STATUS:        ok | partial | failed, one clause
   FINDING:       what is true now, in the fewest lines that carry it
   EVIDENCE:      gate lines verbatim, counts, the one number that proves it
   FILES-SYMBOLS: paths (and symbols / line ranges) touched or relied on
   RISK:          what could still be wrong, and for whom
   NEXT ACTION:   the single next executable step, or "none"
   ```

   **No raw logs and no full files** unless a claim needs them; detail goes to
   the detail file and **the director never reads it** unless a leftover forces
   it. Brevity is the default, not a ceiling met by omission. Measured: reports
   returned 135k–313k characters a day into a context that never releases them.
5. **Keep images out of the director context unless visual adjudication is
   material.** Zero images entered on 09-06 and 09-07; **18** on 09-08. The
   worker looks at the PNG and reports the one number or fault — "figure is
   1,988×1,405, fits A4 landscape, no clipped box". Images cost ~1,568 visual
   tokens each, stay in context for every later turn, and when Claude Code
   evicts them it reprocesses the conversation from the earliest evicted message
   onward — a cache invalidation, not just a resend.
6. **One wake-up per batch.** Launch parallel workers in **one message**, have
   each write its result to a file, act when all are done. Every completion and
   every `SendMessage` resume wakes the director at full context: 40 task
   notifications cost 2.19M input-equivalent tokens that day (7.6 % of the
   director's spend) on top of 40 human wakes at 7.06M (24.5 %). Corollary: a
   **complete brief** — a worker needing three follow-ups costs three
   full-context wakes plus three cold re-reads of its own transcript.
   `SendMessage` is right for *faults*, wrong for drip-feeding a brief.
7. **No model switching mid-session.** Pick the Lead's runtime at the top
   (`reference/runtime-map.md`) and leave it. Each model has its own cache; `/model` means the next
   request reads the whole history with no cache hits. Measured:
   `fable → opus → fable` produced 8 director calls at a **31–35 % hit ratio**
   and 196,855 cache-write tokens for nothing.
8. **At ~120k context, or immediately after any compaction, write `handoff.md`
   and `/clear`.** A compaction invalidates the conversation layer by design and
   everything re-injected afterwards is re-written at 1.25×: measured 259
   injections / 127,809 characters on 09-08 against 78 / 25,144 on 09-07.
   `/clear` costs nothing; `/compact` reads what it summarises. **Related tax:**
   a session left open past the cache TTL pays a cold re-read — three gaps over
   an hour cost 744k, 249k and 220k cache-write tokens in a single call each.
   Close the session, do not park it.
9. **Do not invoke heavy skills from the director.** A skill body loaded there
   sits in context for the rest of the session and is re-injected after a
   compaction. Name it **in the brief** (§4). Never from the director:
   `workflow-diagram`, `artifact-design`, `frontend-design`, `project-srs`,
   `pdf-typography`, the project manuals skill, `safe-delete`. The director may
   invoke only `nj-delegate`, `session-handoff` and `nj-learn`.

### 11.2 One request to the user

> **Please batch instructions into one list.** On 2026-09-08 forty messages
> arrived, median 77 characters, sixteen inside three hours — ten in the 28
> minutes from 12:01 to 12:29, each changing a brief already running. Every
> message wakes the director at full context: those forty cost **24.5 % of the
> director's entire day**, more than every worker report and notification
> combined. And each change to a live brief restarts a render cycle, which is
> most of why that delivery took ~7× longer. One message listing the changes
> costs one wake and one rebuild instead of ten and ten. Interrupting is always
> fine when something is going wrong; it is the *drip* that is expensive.

### 11.3 Eco mode, in numbers

One STANDARD worker; uncached input ≤ 65k; ≤ 2 builds; a structured report; no
images to the director; one wake at the end. That shape measured **4.6M
input-equivalent tokens (~\$9)** for a full stage. The same stage as an
unbounded FRONTIER loop measured **\$66–100** — roughly **10×**, almost entirely
the budgets, not the tier.

### 11.4 The check that catches this early

Watch one number: **worker share of the day**. Healthy days ran 13–36 %; the bad
day ran 88 %. If a worker has passed 1.5× its class budget (§3(f)) or its
runaway call cap, or has run over an hour, stop it and ask what it is looping
on — that signature shows long before the rate limit does.


## §14 Lessons of 2026-09-17 — measured

One 22h session (`PROJ-tests/artifacts/ops/session-review-2026-09-17.md`)
measured: 96 redeliveries against 16 deliveries; `reannotate.ts` patched 9 times
in a day; `deliver.py` rewritten 4 times; a director wake storm (≈12
full-context wakes in 3 minutes) from agents that ended their turn on a
background monitor; ≈1M tokens on a Haiku interpreter called on every message
including ones under ten words. Causes ranked by cost: unverified output shipped
for the client to verify (35 %), masking built on a heuristic model patched
reactively instead of a registry (30 %), staging faults rediscovered per service
instead of registered once (15 %), shared code edited live by many agents with
no owner (8 %), director errors below (7 %), requirements moved with no spec
file to absorb the change (5 %).

**Director rules that follow (superseding looser prior wording):**
- Read `date` before quoting any deadline — a guessed clock (15:20 vs 15:07
  actual) caused a wrong "past budget" call.
- A verification window is the WHOLE time an element is on screen — "scan from
  1:15" missed a leak that started at 1:11.9.
- Never relay a worker's generalisation without its count. "Works in any flow"
  was retracted to "2 of 11". State the count or don't relay the claim.
- No sweep without one positive sample first. A 9-service video sweep and a
  civil-number sweep both ran to 0 hits, ≈370k tokens, before anyone confirmed
  the thing swept for existed anywhere.
- When a new instruction contradicts the previous one on the same point, ask
  ONCE before rewriting code.
- Every worker launch gets a ledger row — the unledgered 45 of 78 launches made
  the waste numbers unrecoverable.
- **A worker never ends its turn while its own work is still running.**
  Foreground waits only, no background monitors (`nj-agent-ops` §2/§6).
- Not recommended as a fix: more workers (they multiplied collisions on shared
  code), a stronger model for execution (the faults were tooling, not
  reasoning), or looser gates.
