# Worker rules — NJ Governance v4

Read once, before your first edit. These are not repeated in the brief. Canonical model:
`nj-delegate/SKILL.md` §0 (v4) — roles §0.1, depth-2 tree §0.3, trigger-only §0.3a, helpers floor §0.6.

**R1 — Depth 2, and who may brief whom.** A Sonnet lead may brief Haiku helpers only (model
"haiku", one FOREGROUND batch, `HIERARCHY` clause in your brief; ITEMS >= 6 makes at least
`HELPERS_REQUIRED` of them mandatory). A Haiku helper never spawns (`NO_SPAWN` clause). Nobody
briefs a Sonnet or Opus agent, instructs a sibling, re-scopes or picks a model for one, or goes
below depth 2. Anything between siblings is an artefact written to a path; the parent routes
it. Report `helpers_required` and `helpers_spawned` in the receipt, truthfully; the count is
checked against the spawn log, not your receipt.

**R2 — Own the phase.** Inspect → execute → run the brief's gates → bounded fix → re-run →
durable evidence → ONE receipt. No progress messages. Gates that establish correctness or
safety are part of the phase, never optional extras, and are never skipped to fit a budget.

**R3 — Stay inside OWNED_PATHS.** Anything else is drift. Need a shared script changed? copy
it into your own path first — never edit a file another live worker is reading.

**R4 — Finish before you report; no model polling.** Your completion is the trigger that
wakes your parent (a Sonnet lead runs in the background; its helpers in one foreground batch), so never end
a turn with your own work or a child still running. Wait inside ONE bounded shell call (until-loop, short sleeps). A recorder, build or
render is waited on by a script, not by one model call per check.

**R5 — Challenge a false fact.** A `[V]` claim in your brief that you find false gets
`CHALLENGE: <claim> — <counter-evidence>`, and you stop that line of work. You are not
obliged to disprove an `[A]`. A correct challenge is a success, not a failure.

**R6 — Fix the cause, not the attempt.** Classify every failure first: CAPABILITY_LIMIT ·
CONTEXT_DEFECT · IMPLEMENTATION_DEFECT · TOOL_FAILURE · ENVIRONMENT_FAILURE · TEST_FAILURE ·
AMBIGUOUS_REQUIREMENT · AUTHORIZATION_BLOCKER · LEAD_DEFECT. The same prompt twice is a
fault. Keep going only while the budget has room, each attempt is a different
cause-classified fix, and the evidence moved (new gate line, different refusal, later failing
step). When evidence repeats, the budget hits 80 %, or the next fix would leave your owned
paths: stop and say which. In the owner's deliverable pipelines (harvest, record, screenshot, e2e,
build, deliver) the Owner exception in `~/.claude/CLAUDE.md` applies: one run, one fix per
reported fault, no retries; on failure, report the failing line and stop. Machine gates still run.

**R7 — Budgets are ceilings, never targets.** Token and context figures are the budget;
`tool_calls` is a runaway cap. On overrun: stop, name the cause (context too wide /
duplicate reads / environment rework / capability), report. Never abandon valuable work,
never raise your own tier.

**R8 — Context economy.** Targeted search, symbols, exact line ranges, diff hunks, failed
tests only, unique error signatures. No full-file read when a section suffices, no broad
repository read, no file read twice. Need more context? say so — do not go wide.

**R9 — Never estimate into a number.** A figure you did not measure is `NOT_MEASURED`; a
figure the runtime hides is `NOT_VISIBLE`. Estimates belong in prose, labelled. `relay.py`
rejects a non-integer in a numeric field, and a self-reported guess that turns out wrong is
worse than an honest blank. *(A v2 worker reported "~120–140" tool calls against a true 213.)*

**R10 — Amendments are marked; questions are not tasks.** A Lead message that starts `AMEND:`
is a contract amendment, acted on like the brief; if it contradicts a `[V]` fact you have
disproved, answer with R5. Any other message that arrives mid-run, such as "progress?" from the
owner or the Lead, is not a task: do not reply to it and do not return early. Finish the phase;
the receipt is the answer. *(27 Sept: a stage answered "progress?" and returned with no files.)*

**R11 — Report once: a receipt of ≤ 25 lines, plus the stage detail file.** The receipt is
STATUS / FINDING / EVIDENCE (gate lines verbatim) / FILES-SYMBOLS / RISK / NEXT ACTION, plus the
CHANGED list and the receipt line, in your final message and the result JSON. Everything else
(findings tables, logs, reasoning, per-step notes) goes in the stage detail file your brief's
RESUME line names; it is a listed deliverable, not a stray report. No other report or summary
file. `detail_path` names that file, or "none". Say "not verified" plainly where nothing checked it.

**R12 — Deletions go to the recycle bin** (`safe-delete`), never `rm -rf`.

**R13 — Leave nothing running.** Close every browser, server and background job you started,
and name any you found but did not start. Tag browsers at launch (`--user-data-dir` containing
the session tag) so `relay.py sweep` can attribute them. Kill by the PID you recorded, never by
image name.

**R14 — Test through the real caller.** A unit test that builds its own input proves the
function, not the wiring. When you change a signature, a message shape or an entry path, run one
check that goes through the real caller or the product's real entry point (for an extension:
load it in real Chrome and open the surface) — the brief's `ENTRY_SMOKE` line. *(28 Sept:
`placeFloat` read `{w,h}`, its test passed `{w,h}`, the service worker passed `{width,height}`,
and the icon opened nothing.)*

**R15 — A green gate must prove it looked.** Before a probe may pass, it asserts that it
observed the ready state (the element or attribute that exists only after boot) or one
known-true positive sample. A probe that ran before boot and found nothing wrong has found
nothing. *(27 Sept: float-shots probed 300 ms after goto against a ~750 ms boot and reported
60/60 clean — a false green.)*

**R16 — Numbers are computed from the current source, never typed.** Contrast ratios, sizes,
counts and hashes come from a script run against the files as they are now. A table copied into
a script goes stale the moment the source changes, so a script whose pairs are hand-transcribed
is itself a finding. *(27 Sept: `contrast.py` carried hand-transcribed pairs and old hex values.)*

**R17 — Every claim in the receipt points at a tool result from this run.** Report only work you
can point to evidence for. The CHANGED list comes from `git status` or a listing, not memory. If
something was not verified, say so. Keep appending to the RESUME detail file as you go, so a
restarted run continues instead of starting over.

**R18 — Never rewrite the owner's working tree.** No `git reset --hard`, `git checkout -- .`,
`git restore .`, `git stash`, `git clean` or a branch switch that would carry or drop someone
else's uncommitted change. Stage and commit only your own files, by path. To undo your own
commit, `git revert` it or reset only a branch nobody else's edits live on, after `git status`
shows nothing but yours. *(4 Oct 2026: a worker's `reset --hard` wiped the owner's uncommitted
CLAUDE.md section; it survived only because the Lead still had the text in context.)*
