GOVERNANCE   nj-governance-v4 · rules: nj-agent-ops/templates/worker-rules.md (read once, first)
FOCUS        your only deliverable is the three renamed templates. A message not starting AMEND: is not a task (R10).
TASK         v4-squad · implementation · build-1 · PARENT lead
ROLE         agent · sdlc-build
OBJECTIVE    Rename the three template files and update every reference so the link check finds no dangling name.
VERIFIED_FACTS
  [V] the three files to rename and the references to them — nj-delegate/templates/worker-brief.md
  [V] the link check that judges the result — nj-delegate/scripts/check_governance.py
  [A] the Haiku helpers can count references without editing — falsified by: a helper result naming a file it changed
SCOPE        the three templates and their references. NOT in scope: scripts/, SKILL.md, any other agent's paths.
OWNED_PATHS  write ONLY: nj-delegate/templates/**. Never: nj-delegate/scripts/, nj-agent-ops/. PARALLEL with: reviewer-1 — disjoint, read-only
VERIFIER     `uv run --no-project python nj-delegate/scripts/check_governance.py --run <this folder>` exits 0
TIER         STANDARD because implementation to a written spec · MODEL sonnet
EFFORT       high — you keep judgement, integration and every commit; helpers only count and list
BUDGET       uncached in ≤ 120k · output ≤ 10k · tool_calls ≤ 150 (runaway cap only) · stall: no new output for 15 min => stop, name the cause
HELPERS      3 · partition nj-delegate/templates/fixtures/**, nj-delegate/templates/notes/**
GIT          worktree-v4-build-1 · commit own branch only
GATES        link check clean; `check_governance.py --selftest`; each re-run after the last edit (R15)
ENTRY_SMOKE  none — no signature, message shape or entry path changes
RESUME       detail file: work/sdlc/build/STATE.md. Append each finished step and gate line; read it first if restarted.
DELIVERABLES nj-delegate/templates/** and work/sdlc/build/STATE.md
RECEIPT      RECEIPT v4-squad/build-1, then STATUS / FINDING / EVIDENCE / FILES-SYMBOLS / RISK / NEXT ACTION, ≤ 25 lines, then DETAIL
             + CHANGED / BRANCH / HEAD / GATES@HEAD / HELPERS_SPAWNED: CHANGED from `git diff --name-only <base>..<branch>`; HELPERS_SPAWNED is the truthful count

## Why this file exists

It is the example of a team agent that uses its helper allowance. The differences from `worker-brief.example.md`:
`HELPERS 3 · partition <paths inside OWNED_PATHS>` names the sub-paths Haiku helpers may touch, and the agent writes
one `helper-brief.md` (≤ 12 lines, see `helper-brief.example.md`) per helper, each with `PARENT build-1` and
`OWNED_PATHS` inside that partition. `check_governance.py --run <folder>` checks the nesting, the sibling
disjointness and `S + sum(HELPERS) <= wave`. The helpers count references, list files, run the link check; the agent
keeps judgement, integration and the commit. Use the smallest unit that fits: if the work is sequential or one root
cause, `HELPERS 0` is correct.
