---
name: nj-agent-ops
description: 'NJ Governance v4 (v3 briefs still accepted) transport under nj-delegate: telemetry refused at write time (relay.py), path claims that enforce single-writer, KPI audit via verify, results through files, one wake per batch, a low-effort interpreter spawned on a trigger. Use for explicit agent-ops or script-mode requests.'
---

# nj-agent-ops — the machines under NJ Governance v3

Layers on `nj-delegate`; it does not replace its routing rules. It owns the parts of v3 that
are `[GATE: relay.py]`: **telemetry validated at write time**, a **runtime ownership
registry**, and the **KPI audit**. It also carries file-based result relay, batch-only
feedback and the trigger-spawned interpreter. **Worker count always comes from `nj-delegate` §0.6**
(the number of disjoint write-sets) so there is one source of truth.

Governance version: `nj-governance-v4` (2026-10-16; `batch` writes it by default; v3 briefs still pass
`check_governance.py --brief`). A clause here is a gate only where it names the
script that refuses the violation.

## 1. Transport

- **Inherit the count rule** (`nj-delegate` §0.6): one worker per disjoint write-set on the
  critical path; only the user's own Eco / Max N is a fixed ceiling. Script mode never
  changes the count by itself.
- **Ownership is claimed, not assumed** `[GATE: relay.py claim]`. Before a batch runs, each
  worker's owned paths are claimed:
  `relay.py claim <project> <run-id> --agent A --paths p1 p2 …`. A claim overlapping a live
  one is refused, naming both agents and the path. This is what finally enforces single-writer
  — v2 stated it in the brief and no machine checked it.
- **Hierarchy, not flat (v4).** Lead (Opus) → Sonnet lead → Haiku helpers, depth ≤ 2. A Sonnet
  lead may spawn Haiku helpers only; **Haiku never spawns**; nobody messages a peer — a result
  file is the only thing one agent leaves for another, routed through the parent. Legal pairs
  are decided by `relay.py` (`delegation_legal`): lead→sonnet|haiku, sonnet→haiku, depth ≤ 2;
  everything else is a BREACH in `verify` and in `batch --spawns`.
- **Agent slots — at most 20 live agents, all roles counted** `[GATE: relay.py slots]`.
  `relay.py slots claim <project> --agent ID --role sonnet|haiku` before spawning (refused,
  exit 1, nothing written, when 20 are active); `slots release <project> --agent ID` when the
  agent has reported; `slots list <project>`. Ledger: `.agent-ops/slots.json`. A claim older than
  `--stale-min` (default 180) expires with a WARN, so a crashed agent cannot hold a slot forever.
  `sweep` lists any unreleased slot as a leftover.
- **Helpers required** `[GATE: relay.py verify]`. A brief may carry `ITEMS n` (or `ITEMS=n`);
  required helpers = 0 if n < 6 else min(4, ceil(n/6)) (6→1, 13→3, 24+→4). `verify` counts the
  Haiku spawns in the spawn log and fails below the requirement; no log with required > 0 fails.
- **Spawn log** (written by the SubagentStart hook, one JSON object per line, default
  `<project>/.agent-ops/spawns.jsonl`, override `verify --spawn-log PATH`):
  `{"ts": "<ISO-8601>", "parent": "<spawning agent's name; carry the task id, e.g. sonnet-lead:<task-id>>",
  "child_type": "<agent type, e.g. haiku-helper>", "model": "<child model, e.g. haiku>"}`; optional
  `depth` (int, default 2). Roles are read from the words haiku / sonnet / opus in `model`
  (else `child_type`) and in `parent`; a parent naming none (e.g. `main`) is the Lead. Spawns
  are attributed to a brief when `parent` contains the brief's TASK id or file stem; with a single
  `ITEMS` brief in scope, unattributed spawns count for it.
- **Leak scan** `[GATE: relay.py leakscan]`: `relay.py leakscan <paths…> [--secrets-file F]` scans
  receipts, briefs and reports (files, or directories walked) for `sk-or-…`, `Bearer <token>`,
  `password=…`, `token=…`, `JIRA_PASS=…` carrying a real value (placeholders such as `${…}`, `<…>`,
  `****` pass), and for every literal in the secrets file (JSON string leaves, or one per line /
  `KEY=value`). It prints `file:line pattern=<name>` only — never the value — and exits 1 on a hit.
  Run it over `.agent-ops/` before reporting done.
- **Workers never hand results back through conversation.** Each writes one JSON
  file to `<project>/.agent-ops/results/<run-id>/<agent-name>.json` on the schema
  in `templates/result.schema.json`. The director reads only the **digest** that
  `scripts/relay.py digest <run-id>` prints — one line per agent — never a
  worker's transcript or its `detail_path`.
- All nj-delegate per-worker rules still apply: build and token/context budgets
  in the brief (tool calls are a runaway cap only), the STATUS / FINDING /
  EVIDENCE / FILES-SYMBOLS / RISK / NEXT ACTION receipt of ≤ 25 lines plus the
  stage detail file for everything else (`worker-rules.md` R11), minimum-sufficient
  verification, `safe-delete` for deletions, no images to the director unless
  visual adjudication is material.

## 2. Agent control — activate / deactivate / monitor

- **A worker never ends its turn while its own work is still running** (session
  review 2026-09-17: a director wake storm, ≈12 full-context wakes in 3 minutes,
  traced to agents ending their turn on a background monitor/recorder).
  The worker itself runs in the background and its completion is the trigger that
  wakes the Lead (owner, 2026-10-11); it waits on its own recorders inside ONE bounded
  shell until-loop — a script waits, not one model call per check.
- **Activate** a stage only when its inputs already exist on disk. Never spin up
  a worker to wait for another.
- **Deactivate** an agent whose result JSON says `status: ok` and whose one
  director check passes. **Keep and resume** (`SendMessage`) only an agent with
  faults left — a fresh agent re-reads everything cold, the more expensive path.
- **Monitor deterministically, decide at events.** Liveness and stall are a
  script's job (output mtime vs the brief's stall bound, process state, expected
  artefact, timeout — `nj-supervise` check A); the Lead is woken only by a
  `nj-delegate` §0.4 event, never to read "still running". At the wake it reads
  the digest line: status, usage if known, leftover count. An agent found over
  **1.5× its class budget** (nj-delegate §3(f)), over its runaway call cap, or
  past its stall bound is asked what it is looping on — the early signature,
  well before a rate limit. Asking is not killing: valuable work is never
  auto-terminated on an overrun.

## 3. Choosing count and models

1. Name the stages (from the request, or the interpreter's brief, §4).
2. Ask first whether any agent is needed; then take the smallest count with a
   measurable benefit, within the active cap.
3. Run `nj-delegate` §3 per stage and paste its budget line verbatim:
   `Tier: <tier> because <reasoning type>; effort: <level>; budget: uncached input ≤ <N>, output ≤ <M>, model calls ≤ <K>, files/context read ≤ <F>; tool_calls ≤ <T> (runaway cap only).`
   Derived class budgets: FRONTIER ≤ 150k uncached input, STANDARD ≤ 65k,
   ECONOMY ≤ 12k. The tier → runtime map is
   `../nj-delegate/reference/runtime-map.md`, not part of the brief's policy.
4. **FRONTIER is the Lead's call (owner, 2026-09-17).** The Lead may dispatch a
   FRONTIER worker whenever the stage needs one; no fixed cap. The
   routing test is unchanged: writing to a written spec is not FRONTIER, nor is a
   review (scoring is STANDARD; FRONTIER reads only the disputed cells as its own
   short run), nor is authoring, Arabic included.
5. Measured (`PROJ-tests/artifacts/ops/model-routing-audit-2026-09-16.md`;
   the owner: *lowest-cost tier that is good enough + effort*): on 2026-09-15,
   **14 of 22 FRONTIER runs — 61 % of FRONTIER spend, 28 % of the whole day —
   were scoring, verification, authoring or apply-a-known-rule stages a lower
   tier would have done**, at the same rework and partial rates. Those per-run
   tokens are estimated from tool calls, not counter-measured, and are labelled
   so wherever quoted.
6. **Budget check after every batch:** any run over 1.5× its class budget gets a
   one-line *cause* note in the ledger (context too wide / duplicate reads /
   environment rework / capability); the next same-class brief is tightened.
   Three long runs in one class means the class was wrong. A tier is raised only
   when capability was the cause.
7. Launch every independent stage **in one message, before waiting on any**;
   the Lead is then SUPERVISORY-IDLE. Every worker, builders and editors
   included, is dispatched with `run_in_background: true` — `Agent` calls in that one
   message, one wake per batch; completion is the trigger, nobody polls (owner,
   2026-10-11, supersedes 2026-09-29; `../nj-delegate/reference/runtime-map.md` § Waiting
   and § Claude Code mechanics). Then run `relay.py digest <run-id>` once and inspect only the
   smallest extra gate/diff evidence risk requires.

## 4. The interpreter — called on a trigger

One ECONOMY interpreter per session, spawned the first time a message from
the owner is long, mixes Arabic and English, or changes a brief already running,
then kept alive via `SendMessage` — never respawned per message, never polled,
never run on agent notifications, wake-ups, hook output or the Lead's own
turns. It sits between the owner and the Lead: it turns that message into a brief.
Measured cost when it ran on every message: ≈45k tokens/message (2026-09-16).

- **Low effort by design:** read the message once, write the brief, stop. No
  advice, no execution.
- Jobs: (a) translate and summarise the raw message into
  `templates/interpreter-brief.md` (DELIVERABLE / LANGUAGE(S) / AUDIENCE /
  DONE-WHEN / CONSTRAINTS / UNCERTAINTIES-TO-CONFIRM / EXPLICIT-DO-NOTS,
  ≤ 120 words); (b) compress a worker digest when asked.
- It writes only `<project>/.agent-ops/briefs/<run-id>.md`.
- **Any other standing per-stage helper call** is held to the same test: keep it
  only where evidence shows a quality, cost or reliability gain; otherwise make
  it conditional on a named trigger, and record the decision in the ledger note.

Fallback: if `SendMessage` fails, spawn one fresh interpreter and continue — one
respawn, not a retry loop.

## 5. Measurement and adjustment

After each batch the director appends one row per run to
`<project>/.agent-ops/ledger.md` via `relay.py ledger`. **The row is the
measurement schema** — every field nullable, nothing invented:

| field | note |
|---|---|
| `runtime` | the provider/model runtime id actually used (not the tier) |
| `tier` | DETERMINISTIC / FREE-LOCAL / ECONOMY / STANDARD / FRONTIER |
| `effort` | low / medium / high actually used (`ledger --effort`); `relay.py route` groups by it, blank = high |
| `task-class`, `role` | what the stage was, and director/worker/interpreter |
| `cached-in`, `uncached-in`, `output`, `reasoning` | token counters |
| `model-calls`, `tool-calls`, `workers`, `retries` | counts |
| `duration` | minutes |
| `exec-status`, `verify-status`, `final-status` | **three separate fields** |
| `defects`, `escalations` | found, and tier escalations used |
| `cost`, `basis` | `basis` is `actual` or `estimated` — **never mixed** |
| `lead-defects` | briefs whose `[V]` claim a worker disproved (`nj-delegate` §0.2) |

**Validation happens at write time, not at analysis time** `[GATE: relay.py]`. `ledger`
refuses — and does not write — a row whose `tier` is outside the tier set, whose
`exec-status` is empty or not one of ok/partial/failed, whose numeric fields are not
integers, or whose `--cost` arrives without `--basis`. The rejection names the field.

**Two honest blanks, and no third option.** `NOT_MEASURED` means the worker could not measure
it; `NOT_VISIBLE` means the runtime hides it. Both are legal in non-numeric fields only. **An
estimate may never occupy a numeric field** — it goes in the note, labelled. A v2 worker
reported *~120–140* tool calls against a true 213; that row is worse than a blank, because a
blank is honest and a guess is evidence.

**`relay.py verify <project>`** audits the whole corpus: one line per invalid row (row number,
field, why), then the KPI block from `nj-delegate` §0.15, exiting non-zero on any invalid row
or breached trigger. **A task is not complete until its rows pass it.**

**Batch row — calibration telemetry (v2).** One row per task, appended to
`<project>/.agent-ops/batches.md` by `relay.py batch <project> <run-id> …`. The
run-id is the TASK_ID; any flag not passed is written `NOT_VISIBLE` — never
guessed.

| group | fields |
|---|---|
| identity | `task-class`, `governance-version` (default `nj-governance-v4`) |
| Lead | `lead-runtime`, `lead-tier`, `lead-effort` |
| workers | `worker-count`, `peak-concurrent` — per worker (`runtime`, `tier`, `role`, tokens, retries, duration) is the ledger row above; `effort`, `ownership_scope`, `start_time`, `end_time`, `delegations` ride in the result JSON |
| wakes | `lead-wakeups`, `wake-reasons` (§0.4 names), `invalid-status-wakeups`, `model-polls`, `lead-passes-while-active` |
| parallelism | `parallelism-considered` y/n, `parallelism-used` y/n, `parallelism-reason`, `serial-deps` |
| topology | `w2w-delegations` (expected 0), `nested-spawns` (illegal nested spawns, expected 0; `batch --spawns "sonnet>haiku@2,…"` computes it and a legal Sonnet→Haiku helper is not counted) |
| v3 additions | `lead-defects`, `wake-ratio` (= lead-wakeups / worker-count, 2 dp, `NOT_VISIBLE` if either input is missing), `cascade-attempts`, `cascade-escalations`, `false-challenges` (a challenge the source did not support — counted so the challenge path cannot be gamed in one direction), `estimate-min` and `estimate-tokens` (the prediction made **before** the task ran, scored against the actual by `relay.py verify`; absent means no forecast was recorded, never zero) |
| quality | `model-passes`, `verification-result`, `review-findings`, `escalations`, `duration-min`, `note` |

What this runtime shows today: the `Agent` result gives `subagent_tokens`,
`tool_uses` and `duration_ms` per worker (a total — cached / uncached / output /
reasoning split is `NOT_VISIBLE`); the Lead's own token counters are
`NOT_VISIBLE` from inside the session; wake counts and topology are counted by
the Lead from its own turns and the workers' `delegations` field.

- **Optimisations are proved, not asserted** (nj-delegate §12): baseline of the
  same task class in this ledger; accept only if cost, context, frontier
  attention, duplicate work or model calls fall **without** correctness,
  testing, review, evidence or safety falling. Total input tokens alone is not
  the metric.
- An agent that needed rework **twice for the same cause** → write the lesson
  through `nj-learn` into the skill that owns the subject, and update the brief
  template.
- Revise tier routing from the ledger: promote a class that keeps failing for
  *capability*, demote one that never needed the tier. Rework rate for
  environment-sensitive workflows is read on its own, never mixed with reasoning
  failures.
- `relay.py stale` finds result files older than 7 days — sweep them via
  `safe-delete` so a run-id's digest never mixes stale and current results.

## 6. Errors: two questions, then skip and mark

(owner, 2026-09-14; cap revised 2026-09-16.) Retry loops were the single largest
token sink measured (nj-delegate §11.1).

**Attempt cap = budget and progress, not a count (2026-09-16 19:40).** A worker
keeps going while (1) its budget has room (stop at 80 % and say so), (2) every
attempt is a *different*, cause-classified fix, and (3) the evidence moved — a
new gate line, a different refusal, a later failing step. The old fixed counts
(one fix, ≤ 2–3 rehearse cycles, two recordings per locale) are no longer
ceilings; they are the point at which the worker must show what changed. Quality
gates are never relaxed to fit a budget.

0. **Classify the cause first** — CAPABILITY_LIMIT · CONTEXT_DEFECT ·
   IMPLEMENTATION_DEFECT · TOOL_FAILURE · ENVIRONMENT_FAILURE · TEST_FAILURE ·
   AMBIGUOUS_REQUIREMENT · AUTHORIZATION_BLOCKER · **LEAD_DEFECT** (`nj-delegate` §0.12)
   — and fix that. A LEAD_DEFECT is not the worker's to fix: it returns
   `CHALLENGE: <claim> — <counter-evidence>` (§0.2), stops that line of work, and the Lead
   re-checks the source before re-dispatching. A correct challenge is a success; it costs the
   worker none of its two questions. Never resend the same prompt, never escalate the tier by hand: the Lead
   runs `relay.py route <project> --class C --failed "<gate line>" --cause <class>`, which
   prints ESCALATE (haiku → sonnet only, once, CAPABILITY_LIMIT / IMPLEMENTATION_DEFECT /
   TEST_FAILURE only; row `escalations=1`) or STOP — there is no Opus worker target (v4); a failed
   Sonnet stage is the Lead's decision. `relay.py route <project> --class C` alone
   prints the learned start model + effort per task-class from ledger.md. Never spawn another worker
   because the first failed.
1. Fix at the cheapest checkpoint. When an attempt repeats the previous evidence
   or the budget is at 80 %, or the next fix would touch files it does not own,
   **stop**.
2. Write the problem into the result JSON (`status: partial`, a leftover line
   starting `QUESTION 1/2:` with the exact error line, what was tried, and the
   two options the worker sees) and end the turn.
3. The director answers once via `SendMessage`; the worker applies it with one
   more attempt. Still failing → `QUESTION 2/2:` the same way.
4. After the second answer fails, the worker **skips and marks**: leftover line
   `SKIPPED: <item> — <error line>`; the gates file keeps the red line verbatim;
   it moves to the next item. No third question, no third retry.
5. Two questions per worker per batch, not per item. A worker out of questions
   skips and marks on the first failed fix.

`worker-rules.md` R6 carries this; the brief does not repeat it. A worker that
retries past it is stopped and its run is written to the ledger as `rework y`.

## Files

- `scripts/relay.py` — `init`, `digest`, `ledger`, `batch`, `claim`, `slots`, `leakscan`, `verify`, `estimate`, `sweep`, `route`, `stale`; the
  only channel a worker result, ledger row, batch row or path claim goes through. `ledger`
  and `batch` validate and refuse; `claim` enforces single-writer; `verify` audits the corpus
  and the KPIs.
- `../nj-delegate/scripts/check_governance.py` — `--brief` (contract, evidence grades,
  verifier; v4 briefs: exactly one of the hierarchy clause — Sonnet lead — or the no-spawn
  clause — Haiku helper — and not the retired no-delegation clause), `--run` (no overlapping
  owned paths), `--selftest` (negative controls).
- `../tests/test_v3.py` — the v3 suite behind the ledger / batch / claim / verify gates.
- `tests/test_v4.py` — the v4 suite: slots, legal spawns, route, helpers-required, leakscan, brief
  clauses (`PYTHONUTF8=1 python nj-agent-ops/tests/test_v4.py`).
- `templates/interpreter-brief.md` — the interpreter's system brief.
- `templates/result.schema.json` — worker-result JSON schema, including the
  nullable `usage` measurement block.
- `../nj-delegate/templates/worker-brief.md` — the brief skeleton; add the run-id
  and result-file path to its "Deliverables" heading.
