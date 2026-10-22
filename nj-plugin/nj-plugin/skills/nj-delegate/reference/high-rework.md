# High-rework workflows — browser, recording, environment-sensitive stages

On-demand. Read before briefing a stage that drives a browser, a recorder, an
external environment or any pipeline whose failures come from the environment
rather than from reasoning. Evidence: 2026-09-16, twelve recording attempts
were lost because four helper steps failed silently and the run continued; the
2026-09-15 manuals stream failed `record-build` four times for the same shape.

1. **No auto-upgrade of tier.** An environment failure is not a reasoning
   failure. Raising the tier buys nothing and costs the tier difference.
   Escalate the *cause* as its own short run (SKILL.md §3(d) rule 1).
2. **Deterministic preprocessing first.** Convert, trim, probe, validate and
   normalise inputs with scripts before any model touches the stage.
3. **Validate inputs and environment before model work.** Every helper the run
   depends on exits non-zero and is checked; a helper that can fail silently is
   wrapped in an exit-code check. A stage may not start on unvalidated inputs.
4. **Separate preparation from reasoning.** Preparation is DETERMINISTIC or
   ECONOMY; only the decision is a higher tier.
5. **Preserve successful intermediate artefacts** — captures, segments, audio,
   partial renders — under stable paths, so a retry resumes.
6. **Retry from the failure point when safe**, never from the top. Never repeat
   a step that already succeeded and whose artefact is on disk.
7. **Measure rework independently**: the ledger's `rework` column and the
   run's `retries` count are about this stage's own failures, not the batch's.
   A workflow whose rework rate is high is fixed by preprocessing and
   validation, not by a stronger model.

## Rehearse before the expensive stage (owner, 2026-09-16)

*Scope (2026-09-29): inside the owner's deliverable pipelines the Owner exception in
`~/.claude/CLAUDE.md` wins — one run, and one private rehearsal only when the pipeline
itself is new or was changed since its last good delivery. Machine gates still run.*

Before any stage whose retry costs minutes or a real request — recording,
filing, rendering a long document — run a light deterministic-first dry run
that exercises the same logic and asserts the same end conditions, at the
cheapest fidelity (no media, no narration, no uploads where avoidable). The
expensive stage starts only when the rehearsal is green. A rehearsal failure
is classified by cause per §retry above, and the fix is proven by
re-rehearsing, not by re-running the expensive stage. Preserve successful
intermediate artefacts (rule 5) regardless of which stage produced them.
Evidence: S-096 («طلب اضافة حجم جديد») took 2h48, five Arabic recording
attempts and one English, about 1h10 lost to faults — a curtain never
lifted, a book row never added, masked rows leaking, buttons pressed by the
wrong locale's caption — that a rehearsal catches before any stills or video
exist. Reference implementation: `PROJ-tests/src/manual/rehearse.ts`, wired
as `npm run manual:rehearse -- --flow <id> --locale <ar|en>` and `--rehearse`
on the build.
