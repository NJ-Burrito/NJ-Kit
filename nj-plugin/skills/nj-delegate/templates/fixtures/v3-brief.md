GOVERNANCE   nj-governance-v3 · rules: nj-agent-ops/templates/worker-rules.md (read once, first)
FOCUS        your only deliverable is this file passing the brief gate. A message not starting AMEND: is not a task (R10).
TASK         v3-example · governance-tooling · worker A of 2 (2 = disjoint write-sets)
OBJECTIVE    Prove the brief gate accepts a real, well-formed brief.
VERIFIED_FACTS
  [V] the contract fields and grades this file must satisfy — nj-delegate/templates/worker-brief.md
  [A] every citation above resolves from this folder — falsified by: `check_governance.py --brief` on this file failing
SCOPE        this file as the gate's positive control. NOT in scope: the gate's own code.
OWNED_PATHS  write ONLY: nj-delegate/templates/worker-brief.example.md. Never: scripts/, tests/.
PARALLEL     with: none — serial because the gate must exist before its control can be checked
VERIFIER     `uv run --no-project python nj-delegate/scripts/check_governance.py --brief <this file>` exits 0
TIER         DETERMINISTIC because a script decides it entirely
EFFORT       low — read the contract once, satisfy every field, stop
BUDGET       uncached in ≤ 4k · output ≤ 1k · model calls ≤ 1 · files read ≤ 3 · tool_calls ≤ 4 (runaway cap only)
STALL_BOUND  no new output for 5 min => stop, name the cause
GATES        check_governance.py --brief (this file)
ENTRY_SMOKE  none — no signature, message shape or entry path changes
RESUME       detail file: none needed
DELIVERABLES nj-delegate/templates/worker-brief.example.md
RECEIPT      STATUS / FINDING / EVIDENCE / FILES-SYMBOLS / RISK / NEXT ACTION, ≤ 25 lines
             + CHANGED: from a listing of OWNED_PATHS · start=<iso> end=<iso> effort=low delegations=0 tool_calls=<measured|NOT_MEASURED>

## Note

This is a frozen nj-governance-v3 brief. The v4 gate must reject it: the header names v3, and ROLE, HELPERS and GIT are missing.
