GOVERNANCE   nj-governance-v4 · rules: nj-agent-ops/templates/worker-rules.md (R18, R19 first)
FOCUS        return the list asked for in OBJECTIVE. You spawn nothing and instruct nobody. A message not starting AMEND: is not a task (R10).
TASK         re · extract · helper alpha-h1 · PARENT alpha
OBJECTIVE    Return the names it finds, one per line.
VERIFIED_FACTS
  [V] the contract this brief follows — nj-delegate/templates/helper-brief.md
  [A] the answer fits in 10 lines — falsified by: the result running longer
OWNED_PATHS  demo/alpha/sub/one/**
VERIFIER     `grep -c "" <the file you read>` matches the count you return
BUDGET       tool_calls ≤ 10 · stall: no new output for 3 min => stop, name the cause
RECEIPT      at most 10 lines of text: the answer first, then the command you ran and its exit code
