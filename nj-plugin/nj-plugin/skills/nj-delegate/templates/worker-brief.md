# Worker brief — the contract (NJ Governance v3)

A brief is a contract, not an essay: **≤ 25 lines inside the block**, every field present,
no prose, no pasted standing rules. Standing rules are read by path, once, by the worker.
Every factual claim is graded `[V]` (verified — cite `file:line` or a command you ran),
`[A]` (assumed — say what falsifies it) or `[U]` (unknown — say what counts as established).
An ungraded factual claim is rejected by `check_governance.py --brief`.

```
GOVERNANCE   nj-governance-v3 · rules: <abs path to templates/worker-rules.md> (read once, first)
FOCUS        your only deliverable is <X>. A mid-run message that does not start AMEND: is not a task (R10): do not answer it, finish <X>; the receipt answers it. Returning without <X>'s file changes is a failed run.
TASK         <run-id> · <task class> · worker <name> of <N> (<N> = disjoint write-sets on the critical path)
OBJECTIVE    <one sentence: what must be true when you are done>
VERIFIED_FACTS
  [V] <fact> — <file:line | command output | url>
  [A] <inference> — falsified by: <the cheapest observation that would disprove it>
  [U] <unknown> — established when: <what counts as an answer>
SCOPE        <in scope>. NOT in scope: <out>.
OWNED_PATHS  you may write ONLY: <paths>. Never: <paths>. Shared tool needed? copy it first.
PARALLEL     with: <lanes, or "none — serial because <dependency>">
VERIFIER     <the free check that judges your output: gate | schema | test | count | diff>
             (or: "none because <why>" — then route once by reasoning type)
TIER         <DETERMINISTIC|FREE-LOCAL|ECONOMY|STANDARD|FRONTIER> because <reasoning type>; route: <relay.py route START line>
EFFORT       <low|medium|high>   (work depth set by the stage, not the API effort parameter; FRONTIER is never low)
BUDGET       uncached in ≤ <N> · output ≤ <M> · model calls ≤ <K> · files read ≤ <F> · tool_calls ≤ <T> (runaway cap, self-counted: nothing stops you at T)
STALL_BOUND  no new output for <N> min => stop, name the cause
GATES        <named deterministic checks you run, fix inside OWNED_PATHS, and re-run>; each proves it saw the ready state or one known-true sample before it may pass (R15)
ENTRY_SMOKE  <one check through the real caller or entry point, e.g. `npm run smoke:boot`> (R14), or "none — no signature, message shape or entry path changes"
RESUME       detail file: <path>. Append each finished step, gate line and expensive run's output path as you go; if restarted, read it first and continue from the last unfinished step. Everything beyond the receipt goes here.
DELIVERABLES <exact output paths, the detail file included>
RECEIPT      STATUS / FINDING / EVIDENCE / FILES-SYMBOLS / RISK / NEXT ACTION, ≤ 25 lines, in the final message
             + CHANGED: every path you wrote, from `git status --porcelain -- <OWNED_PATHS>` or a listing, not from memory (R17)
             + result JSON at <path> on templates/result.schema.json (files[] = CHANGED); gate: `relay.py digest <project> <run-id>` prints your line without "invalid"
```

## The three lines that are not negotiable, and why each exists

- **`OWNED_PATHS` is the count.** Worker count is the number of disjoint write-sets, so two
  briefs in one run may never declare overlapping paths — the run gate refuses it and
  `relay.py claim` refuses it again at runtime. This replaces "count by fit", which could
  justify any number after the fact.
- **`VERIFIED_FACTS` is graded.** A Lead that writes an inference as `[V]` costs a whole
  pass; it happened on 2026-09-20. If you find a `[V]` claim false, reply
  `CHALLENGE: <claim> — <counter-evidence>` and stop that line. You are never obliged to
  disprove an `[A]`, and never penalised for a correct challenge.
- **`VERIFIER` decides the tier.** A free verifier makes the cheap tier mandatory and the
  expensive one conditional; no verifier means one routed pass and a written reason.

## The four lines added 2026-09-29, each paid for in UI round 2

- **`FOCUS`** — an owner "progress?" message reached a running stage, the worker answered it
  and returned with no files. Only a Lead message that starts `AMEND:` changes the brief (R10).
  The line goes in every brief, foreground or background.
- **`RESUME`** — an owner message can kill a worker's running tool call; the worker is resumed
  (`SendMessage`, or `resumeFromRunId` for a workflow) and continues from this log. It is also
  the stage detail file: the receipt stays ≤ 25 lines, everything else lives here.
- **`CHANGED`** in the receipt — receipts were trusted without a file list; the Lead checks it
  against `git status` with one command (R17).
- **`ENTRY_SMOKE`** — `placeFloat`'s unit test built its own `{w,h}` while the real caller passed
  `{width,height}`; the icon opened nothing (R14). `GATES` also carries the ready-state rule (R15).

**Foreground or background (owner, 2026-09-29).** A worker that builds or edits runs in the
foreground (`run_in_background: false`), so the owner can watch it and his messages do not reach it
mid-phase. Read-only research and reading run in the background. `FOCUS` is in the brief either way.

## Effort, pasteable

> **medium** — verify at the cheapest checkpoint (JSON / grep / gate line) before any build;
> one build, one look; do not explore beyond the files named above.

(Or **low** — read the named files once, apply, stop. Or **high** — establish the cause from
evidence before changing anything; name the alternative you rejected and why.)
