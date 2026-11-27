GOVERNANCE   nj-governance-v4 · rules: nj-agent-ops/templates/worker-rules.md (read once, first)
FOCUS        your only deliverable is the alpha change set. A message not starting AMEND: is not a task (R10).
TASK         rg · implementation · alpha · PARENT lead
ROLE         agent · sdlc-build
OBJECTIVE    Change only the owned paths so the run gate stays green.
VERIFIED_FACTS
  [V] the contract this brief follows — nj-delegate/templates/worker-brief.md
  [A] the change set is independent of the other agents' — falsified by: --run reporting an overlap
SCOPE        the alpha paths. NOT in scope: every other agent's paths.
OWNED_PATHS  write ONLY: demo/alpha/**. Never: elsewhere. PARALLEL with: the other agents of rg — disjoint
VERIFIER     `uv run --no-project python nj-delegate/scripts/check_governance.py --run <this folder>` exits 0
TIER         STANDARD because implementation to a written spec · MODEL sonnet
EFFORT       high
BUDGET       uncached in ≤ 100k · tool_calls ≤ 100 (runaway cap only) · stall: no new output for 15 min => stop, name the cause
HELPERS      2 · partition demo/alpha/sub/**
GIT          worktree-rg-alpha · commit own branch only
GATES        the VERIFIER above, re-run after the last edit (R15)
ENTRY_SMOKE  none — no signature, message shape or entry path changes
RESUME       detail file: work/sdlc/sdlc-build/STATE.md
DELIVERABLES demo/alpha/**
RECEIPT      RECEIPT rg/alpha, then STATUS / FINDING / EVIDENCE / FILES-SYMBOLS / RISK / NEXT ACTION, ≤ 25 lines, then DETAIL
             + CHANGED / BRANCH / HEAD / GATES@HEAD / HELPERS_SPAWNED: CHANGED from `git diff --name-only <base>..<branch>`
