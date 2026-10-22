GOVERNANCE   nj-governance-v4 · rules: nj-agent-ops/templates/worker-rules.md (read once, first)
FOCUS        your only deliverable is this file passing the brief gate. A message not starting AMEND: is not a task (R10).
TASK         v4-example · governance-tooling · lead A of 1 (1 = disjoint write-sets)
ITEMS=1      one bounded unit (this file) · HELPERS_REQUIRED=0 (n<6) — read by `relay.py verify`
OBJECTIVE    Prove the brief gate accepts a real, well-formed brief — and keep proving it as the gate changes.
VERIFIED_FACTS
  [V] the contract fields and grades this file must satisfy — nj-delegate/templates/worker-brief.md
  [V] the gate that reads it, and its selftest — nj-delegate/scripts/check_governance.py
  [V] the standing rules a worker reads instead of having them pasted — nj-agent-ops/templates/worker-rules.md
  [A] every citation above resolves from this folder — falsified by: `check_governance.py --brief` on this file failing
  [U] whether a future field is added to the contract — established when: REQUIRED_BRIEF_FIELDS changes
SCOPE        this file as the gate's positive control. NOT in scope: the gate's own code, any brief under .agent-ops/.
OWNED_PATHS  write ONLY: nj-delegate/templates/worker-brief.example.md. Never: scripts/, tests/, any live brief.
PARALLEL     with: none — serial because the gate must exist before its control can be checked
VERIFIER     `uv run --no-project python nj-delegate/scripts/check_governance.py --brief <this file>` exits 0
HIERARCHY    hierarchy clause (nj-delegate §0.3): you are a Sonnet lead; you may, and if ITEMS >= 6 MUST, brief Haiku helpers only (ITEMS=1: none needed); helpers never spawn
TIER         STANDARD (sonnet lead) because the gate, not the model, decides; route: DETERMINISTIC verifier first
EFFORT       low — read the contract once, satisfy every field, stop
BUDGET       uncached in ≤ 4k · output ≤ 1k · model calls ≤ 1 · files read ≤ 3 · tool_calls ≤ 4 (runaway cap only)
STALL_BOUND  no new output for 5 min => stop, name the cause
GATES        check_governance.py --brief (this file) · check_governance.py --selftest (positive + negative controls)
ENTRY_SMOKE  none — no signature, message shape or entry path changes
RESUME       detail file: none needed — one step; the gate line is the whole record
DELIVERABLES nj-delegate/templates/worker-brief.example.md
RECEIPT      STATUS / FINDING / EVIDENCE / FILES-SYMBOLS / RISK / NEXT ACTION, ≤ 25 lines + CHANGED: from a listing of OWNED_PATHS · start=<iso> end=<iso> effort=low helpers_required=0 helpers_spawned=0 tool_calls=<measured|NOT_MEASURED>

## Why this file exists

It is the **positive control** for `check_governance.py --brief`. A gate that rejects everything
looks exactly like a gate that works, so one known-good artefact must pass it — the same discipline
as "no sweep without one positive sample first". `--selftest` asserts four things about this file:
it passes as written; stripping the citation from its first `[V]` makes it fail; replacing
`VERIFIER` with a bare word makes it fail; and pointing a `[V]` at a file that does not exist makes
it fail.

Two things it demonstrates by being what it is:

- **A real brief is the file, unfenced.** The ``` block in `worker-brief.md` is display markup for
  the template only.
- **Every `[V]` cites something that exists.** The gate resolves the path — relative to the brief's
  own folder, to the tree root, or absolute. This is deliberate: a line number is not proof
  (`no_such_file.ts:12` once passed), and a citation nobody can open is not evidence. A real
  service brief cites its own project's files the same way.
