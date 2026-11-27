GOVERNANCE   nj-governance-v4 · rules: nj-agent-ops/templates/worker-rules.md (read once, first)
FOCUS        your only deliverable is the gamma change set. A message not starting AMEND: is not a task (R10).
TASK         rg · review · gamma · PARENT lead
ROLE         reviewer · sdlc-review
OBJECTIVE    Review the diffs of alpha and beta; findings only.
VERIFIED_FACTS
  [V] the contract this brief follows — nj-delegate/templates/worker-brief.md
  [A] the change set is independent of the other agents' — falsified by: --run reporting an overlap
SCOPE        the gamma paths. NOT in scope: every other agent's paths.
OWNED_PATHS  write ONLY: none. Never: elsewhere. PARALLEL with: the other agents of rg — disjoint
VERIFIER     `uv run --no-project python nj-delegate/scripts/check_governance.py --run <this folder>` exits 0
TIER         STANDARD because implementation to a written spec · MODEL sonnet
EFFORT       high
BUDGET       uncached in ≤ 100k · tool_calls ≤ 100 (runaway cap only) · stall: no new output for 15 min => stop, name the cause
HELPERS      1 · partition none
GIT          none — read-only reviewer
GATES        the VERIFIER above, re-run after the last edit (R15)
ENTRY_SMOKE  none — no signature, message shape or entry path changes
RESUME       detail file: work/sdlc/sdlc-review/STATE.md
DELIVERABLES none
RECEIPT      RECEIPT rg/gamma, then STATUS / FINDING / EVIDENCE / FILES-SYMBOLS / RISK / NEXT ACTION, ≤ 25 lines, then DETAIL
             + CHANGED / BRANCH / HEAD / GATES@HEAD / HELPERS_SPAWNED: CHANGED from `git diff --name-only <base>..<branch>`
