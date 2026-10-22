# Sonnet-lead brief — the contract (NJ Governance v4)

A brief is a contract, not an essay: **≤ 25 lines inside the block**, every field present,
no prose, no pasted standing rules. Standing rules are read by path, once, by the lead.
Every factual claim is graded `[V]` (verified — cite `file:line` or a command you ran),
`[A]` (assumed — say what falsifies it) or `[U]` (unknown — say what counts as established).
An ungraded factual claim is rejected by `check_governance.py --brief`.
This template is for a **Sonnet lead** (the Lead briefs it). A Haiku helper gets
`helper-brief.md` instead, written by the Sonnet lead.

```
GOVERNANCE   nj-governance-v4 · rules: <abs path to templates/worker-rules.md> (read once, first)
FOCUS        your only deliverable is <X>. A mid-run message that does not start AMEND: is not a task (R10): do not answer it, finish <X>; the receipt answers it. Returning without <X>'s file changes is a failed run.
TASK         <run-id> · <task class> · lead <name> of <N> (<N> = disjoint write-sets on the critical path)
ITEMS=<n>    independent bounded units (services|files|tickets|notes) · HELPERS_REQUIRED=<0 if n<6 else min(4,ceil(n/6))> — read by `relay.py verify`
OBJECTIVE    <one sentence: what must be true when you are done>
VERIFIED_FACTS
  [V] <fact> — <file:line | command output | url>
  [A] <inference> — falsified by: <the cheapest observation that would disprove it>
  [U] <unknown> — established when: <what counts as an answer>
SCOPE        <in scope>. NOT in scope: <out>.
OWNED_PATHS  you may write ONLY: <paths>. Never: <paths>. Shared tool needed? copy it first. BRANCH <name> in your own worktree: commit only, NO_PUSH, no merge.
PARALLEL     with: <lanes, or "none — serial because <dependency>">; agents live in the tree: <k> of 20, slots <claimed via relay.py slots claim>
VERIFIER     <the free check that judges your output: gate | schema | test | count | diff> or "none because <why>"
HIERARCHY    hierarchy clause (nj-delegate §0.3): you are a Sonnet lead; you may, and if ITEMS >= 6 MUST, brief Haiku helpers only — full text under this block
TIER         STANDARD (sonnet lead; helpers economy) because <reasoning type>; route: <relay.py route START line>
EFFORT       <medium|high>   (set by the stage; high only for a diagnosis brief)
BUDGET       uncached in ≤ <N> · output ≤ <M> · model calls ≤ <K> · files read ≤ <F> · tool_calls ≤ <T> (runaway cap, self-counted), helpers included
STALL_BOUND  no new output for <N> min => stop, name the cause
GATES        <named deterministic checks you run, fix inside OWNED_PATHS, and re-run>; each proves it saw the ready state or one known-true sample before it may pass (R15)
ENTRY_SMOKE  <one check through the real caller or entry point> (R14), or "none — no signature, message shape or entry path changes"
CREDENTIALS  <path read in memory via --creds by YOUR scripts only | "none">. Never print or write them; never put one, or a path to one, in a helper brief.
RESUME       detail file: <path>. Append each finished step, gate line and expensive run's output path; if restarted, read it first and continue. Everything beyond the receipt goes here.
DELIVERABLES <exact output paths, the detail file included>
RECEIPT      STATUS / FINDING / EVIDENCE / FILES-SYMBOLS / RISK / NEXT ACTION, ≤ 25 lines, in the final message, + CHANGED (from `git diff --name-only main...<BRANCH>`, not memory, R17) + BRANCH, HEAD, helpers_required, helpers_spawned
             + result JSON at <path> on templates/result.schema.json (files[] = CHANGED); gate: `relay.py digest <project> <run-id>` prints your line without "invalid"
```

## The HIERARCHY clause in full (paste verbatim under the block, after the contract)

```
HIERARCHY: Governance v4 (nj-delegate §0): you are a Sonnet lead (model sonnet), depth 1 of 2. You are asleep until this brief,
           you report ONCE (receipt + at most 25 lines) and sleep; you never poll, message a sibling or send progress.
           HELPERS: if ITEMS >= 6 you MUST brief at least HELPERS_REQUIRED Haiku helpers (model "haiku",
           helper-brief.md, disjoint report paths, own stall bound and budget); fewer is a failed run, counted from the
           spawn log, not your receipt. Launch each batch FOREGROUND, all Agent calls in ONE message, never
           run_in_background, never end your turn with a child or your own command running. Read every helper receipt
           (verdict in your detail file) before you report. Helpers never spawn; no helper-to-helper messages (route
           artefacts by path); a helper silent past its stall bound is failed: mark it, do not wait twice.
           You brief Haiku helpers ONLY: never a Sonnet or Opus agent, never a third layer (depth <= 2). Total agents in the tree <= 20, all counted: claim slots before spawning.
           GIT: work on BRANCH in your worktree, commit only; never git push, git merge, checkout main, reset --hard.
```

## The lines that are not negotiable, and why each exists

- **`OWNED_PATHS` is the count.** Lead count is the number of disjoint write-sets, so two
  briefs in one run may never declare overlapping paths — the run gate refuses it and
  `relay.py claim` refuses it again at runtime.
- **`ITEMS=<n>` (a line starting `ITEMS`, read by `relay.py verify`) and `HELPERS_REQUIRED` are the helper floor.** A lead that does 12 independent
  items alone reported `delegations: 0` on 3 of 4 lanes in the v3 trials; a prose "may" could not
  stop it. The floor is checked from the spawn log by `relay.py verify` (`SKILL.md` §0.6); the SubagentStart hook that writes the log is `PENDING (B3)`.
- **`VERIFIED_FACTS` is graded.** A Lead that writes an inference as `[V]` costs a whole
  pass; it happened on 2026-09-20. If you find a `[V]` claim false, reply
  `CHALLENGE: <claim> — <counter-evidence>` and stop that line. You are never obliged to
  disprove an `[A]`, and never penalised for a correct challenge.
- **`VERIFIER` decides the tier.** A free verifier makes the cheap tier mandatory and the
  expensive one conditional; no verifier means one routed pass and a written reason.
- **`CREDENTIALS` and `NO_PUSH`.** A helper one-liner once printed secrets (v2 trial incident);
  credentials stay in the lead's scripts, and a worker never publishes: the Lead reviews the
  diff and merges.

## The four lines added 2026-09-29, each paid for in UI round 2

- **`FOCUS`** — an owner "progress?" message reached a running stage, the worker answered it
  and returned with no files. Only a Lead message that starts `AMEND:` changes the brief (R10).
  The line goes in every brief.
- **`RESUME`** — an owner message can kill a worker's running tool call; the worker is resumed
  (`SendMessage`, or `resumeFromRunId` for a workflow) and continues from this log. It is also
  the stage detail file: the receipt stays ≤ 25 lines, everything else lives here.
- **`CHANGED`** in the receipt — receipts were trusted without a file list; the Lead checks it
  against the branch diff with one command (R17).
- **`ENTRY_SMOKE`** — `placeFloat`'s unit test built its own `{w,h}` while the real caller passed
  `{width,height}`; the icon opened nothing (R14). `GATES` also carries the ready-state rule (R15).

**Sonnet leads run in the background; completion is the trigger (owner, 2026-10-11; v4
2026-10-16).** The Lead dispatches every Sonnet lead with `run_in_background: true`. A lead
reports once (receipt file + at most 25 lines) and never ends its turn while anything of its own
still runs, helpers included; the runtime's task-notification wakes the Lead. Nobody polls.
Changes mid-run: `AMEND:` via `SendMessage`. `FOCUS` is in every brief. A receipt is written
pass or fail (R-CI-001), and a red required check sends the work back to the same lead
(R-CI-003).

## Rule changes, secrets, deletions (2026-10-12, lessons 1 and 16)
- **Point to rule files, never restate them.** A brief names the rule file by path; it does not copy the rule into prose.
- **Rule-change protocol (the Lead, in this order):** (a) update every shared brief and every report builder that carries the old rule, in the run folders too; (b) `SendMessage` `AMEND: <new rule, path to the rule file>` to every running lead; (c) only then dispatch. A stale copy in one brief is how two workers kept stopping on a retired rule.
- **Credentials are read in memory only.** Never write a credentials scratch file, to the repo or anywhere on disk; never echo them in a receipt; never hand a path to one to a helper.
- **Deletions go through `safe-delete`** (recycle bin), never `rm`/`rm -f`/`rmtree`.

## Effort, pasteable

> **medium** — verify at the cheapest checkpoint (JSON / grep / gate line) before any build;
> one build, one look; do not explore beyond the files named above.

(Or **high**, for a diagnosis brief only — establish the cause from evidence before changing
anything; name the alternative you rejected and why.)
