GOVERNANCE   nj-governance-v4 · rules: nj-agent-ops/templates/worker-rules.md (R18, R19 first)
FOCUS        return the count of REQUIRED_BRIEF_FIELDS entries. You spawn nothing and instruct nobody. A message not starting AMEND: is not a task (R10).
TASK         v4-squad · extract · helper count-1 · PARENT build-1
OBJECTIVE    Return the number of names in REQUIRED_BRIEF_FIELDS and the line it is defined on.
VERIFIED_FACTS
  [V] the list is defined in the gate script — nj-delegate/scripts/check_governance.py
  [A] it is a single Python list literal — falsified by: the grep showing two definitions
OWNED_PATHS  none — read-only
VERIFIER     `grep -n "REQUIRED_BRIEF_FIELDS" nj-delegate/scripts/check_governance.py` shows the same line number
BUDGET       tool_calls ≤ 6 · stall: no new output for 3 min => stop, name the cause
RECEIPT      at most 10 lines of text: the count and the line number first, then the command you ran and its exit code

## Why this file exists

It is the positive control for `check_governance.py --brief --helper`: a read-only extract helper, the shape a team
agent hands to a Haiku reader or runner. The nine fields, 10 lines, the words *you spawn nothing*, a tool-call ceiling
under 40 and a parent that is a team agent (`build-1`, the agent in `squad-brief.example.md`) are what the helper gate
checks. A writer helper would give `OWNED_PATHS` a sub-path inside the parent's `HELPERS` partition instead of `none`.
