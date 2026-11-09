---
name: nj-jira-to-automation
description: 'Turn a Jira ticket (or a service''s open Bugs) into a runnable automation: analyse into notes, check each on the portal, write one standalone test per note (jiraCheck / jiraSkipped / noteEnv), mark filed-request notes blocked, resume on a ticket, run once. Triggers: automate this jira ticket, note to test, per-note test, jira-checks, bug to automation. Arabic: حوّل التذكرة إلى أتمتة، اختبار لكل ملاحظة، فحوص Jira، ملاحظة محجوبة.'
---

# nj-jira-to-automation: ticket -> notes -> checks -> one run

Needs a suite built like `nj-automation-suite` (lib/jira.ts, tools/gen-jira-spec.ts). Reading Jira itself is `nj-jira`. Each stage leaves a file, so a revision re-runs one stage.

| # | Stage | Checkpoint file | Gate |
|---|---|---|---|
| 1 | harvest (nj-jira §3) | `<RUN>/<KEY>.md`, `attachments/` | only open Bugs of THIS service |
| 2 | notes | `<RUN>/notes.md` (N1..Nn) | count written; none dropped/merged |
| 3 | staging check, each note once | `<RUN>/latest-ticket.json` + `evidence/` | every note has a verdict |
| 4 | checks | `<svc>/jira-checks.ts` | every note appears EXACTLY once: check or skipped |
| 5 | generate | `<card>.jira.spec.ts` (generated, never hand-edited) | `tsc --noEmit` 0; `--list` shows one test per note |
| 6 | explain + agent notes | `jira/explain.json`, `AGENT.md`, README-service section | every id has `{plain, notReflected, fix}` |
| 7 | ONE non-filing run | `reports/jira-results.jsonl`, per-service Jira HTML | verdicts compared with stage 3 |

## Evidence-bound, four-layer checks (owner, 2026-11-03, HARD RULE)
**Nothing in a check comes from guessing.** Every desk name, button caption, field label, task key, action key and expected text traces to ONE of: (a) the ticket's own words (quoted, with KEY · date · author), (b) the workflow export (BPMN task / flow keys), (c) what the live portal showed in a harvest (screenshot + DOM + network, saved in `<RUN>/evidence.json`). A value with no source is not written into a check: the note stays `OBSERVED` («يحتاج دليلاً: <what is missing>») until a harvest supplies it.
- **Harvest before checks (stage 3b):** one read-only pass (or the one filed request) records for every note's target: the desk's task key from the API (e.g. `lastTask`) next to its on-screen Arabic name, every button caption next to its action key (DOM attribute or the request it sends), field labels and control names, output text. File: `<RUN>/evidence.json`, each entry with screenshot path + where it was read. Checks bind to task/action KEYS (stable) and use names only as a second layer.
- **Four layers per note, each independent; PASS only when all agree:**
  1. **Visual**: viewport screenshot with a red ring on the exact element (or its absence area), in-viewport asserted.
  2. **Code / inspect**: the DOM attribute or API answer (task key, action key, `formcontrolname`, disabled flag, the response body that carries the value).
  3. **Locator**: Playwright locator by role + caption / control name, `toBeVisible` / `toBeEnabled` / count.
  4. **Names**: the exact wording from the ticket (Arabic folding helper), and for outputs the PDF text.
  A layer that cannot apply to a note says why in the result detail; a disagreement between layers is ❌ with each layer's reading.
- **Never-ran guard:** every automatic note must produce a verdict. A note whose desk/stage was never reached is ❌ «لم يصل الفحص إلى شاشته» listing the desks met; silence is never a pass.
- **Assert the scope, not the page:** look for a text inside the desk's own panel, section or button bar, never `body` text (values typed by the applicant must not satisfy a check).
- **Oracle from the source:** the expected value is the ticket's, never what the screen shows today; a fix flips ❌ to ✅ by itself.

`<RUN>` = `services/<dir>/<card>/jira-open-bugs-<date>/`. Do not read the service's older analysis (`jira/`, `latest-ticket-*`, old README Jira parts, an old `jira-checks.ts`): rename the old file `jira-checks.prev-<date>.ts` or recycle it, write the new one from `notes.md` only.

## Notes -> checks (the three shapes)
- **Testable on card/form** -> `jiraCheck('<KEY> N<n>', title, '<KEY> · <date> · <author>', async () => {...})` in the `hooks.onForm` area. The body asserts exactly what "fixed" means in `notes.md`; locators come from the stage-3 evidence; buttons by caption, keyboard first, Arabic through the folding helper (`has()` / `foldedIncludes`). Returns a short detail string; throws to fail.
- **Needs a filed request or a desk/output** -> put the check at the right `StageHooks` hook (`onSent / onDesk / onFinal / afterPress`) so the filing test runs it when it gets there. In its standalone per-note test it reports **«محجوب: يحتاج طلباً مقدَّماً»** instead of failing, unless `PROJ_RESUME_TICKET=<ticket>` is given: then it opens that ticket and gets a real verdict.
- **Untestable** -> `jiraSkipped(['<KEY> N<n>: لا يمكن فحصه آلياً: <reason>'])`.
- **QA-only notes**: notes run on staging by default; no `noteEnv` entry is needed. The `noteEnv` = 'qa' mechanism stays only as a tool for a future QA-only note.
- Zero open Bugs: `jiraSkipped([])`, empty per-note tests, and say so in the report.

## One standalone test per note
`npx tsx tools/gen-jira-spec.ts "<path fragment matching ONLY this folder>"` writes, beside the service spec, a describe «ملاحظات Jira» with one test `Jira <id> · <title>` per form-note (sign in -> open card/form -> that check only; never presses «إرسال») plus the combined test. Run one note alone:

```
PROJ_JIRA_ENV=staging npx playwright test "services/<dir>/<card>/<card>.jira.spec.ts" -g "Jira <KEY> N<n> ·"
PROJ_JIRA_ENV=staging PROJ_RESUME_TICKET=<ticket> npx playwright test ... -g "Jira <KEY> N<n> ·"
```
Env switches: `PROJ_JIRA_ENV=staging|qa` wins over the service's `jira.config.json`. `PROJ_JIRA_ONLY` (JSON) is what the per-note child uses; not for hand use.

## Running it once
- Take the sign-in lock (`nj-automation-suite`), one non-filing run of the per-note spec, 0 requests filed. Compare each verdict with `latest-ticket.json`: a mismatch is either a WRONG CHECK (fix it once) or a REAL CHANGE (write it down).
- Verdicts append to `reports/jira-results.jsonl` `{env,service,id,mark,detail,at}`; the latest line per service+id wins. Run once, no retry loop: say "not verified" plainly.
- Then the Jira HTML for the service opens by itself (`PROJ_NO_OPEN=1` to stop it) and `npm run jira:track` runs if you filed or re-checked anything.

## Findings feed checks (2026-10-12)
- `npm run findings` runs over each run's captured text. Its rows are candidate evidence for checks: a rule hit becomes a `jiraCheck` assertion only when the note itself names that defect. A rule hit alone never creates a note or a check.
- The scan cannot see UI or role defects (the 3 selftest misses). Mark such a note `needs UI check`; a clean scan does not turn it green.
- `npm run recheck` compares verdicts per build; its fixed and broken rows update the stage-3 verdicts when re-run.

## Pitfalls
- A check that waits on a fixed timeout rots: wait for the outcome (a visible text), ceiling only as safety.
- A note quoted in notes.md but asserted on different words = the wrong test. Assert the verbatim "fixed" shape.
- Failing checks are `expect.soft`: the walk continues; the failure is in the report, with a screenshot taken at the failing step.
- Do not edit `lib/**` from a service worker: write `lib-defect-<n>.md` and continue.
- Before a missing-verify/pledge check: look at `nj-jira/references/<project>.md` § «Known not-a-bug / field behaviour»; never file against a listed behaviour; never generalise a field behaviour from one field to another — verify each field on the live portal before filing a missing-verify/pledge Bug.

## Oracles and self-healing (2026-10-18)
A generated check asserts the note's expected value from its cited source (ticket/comment), never from what the system currently does; a first-run result is a question, not an expectation (R4). Verdicts `PASSED | FAILED | OBSERVED | SKIPPED | HEALED | HEAL-REJECTED`; locator failures only write a heal proposal (observe-only 2026-10-18 -> 2026-11-15), the check still fails. Rules R1-R8 / H1-H7 / G1-G9: `nj-qa-pipeline` section 5 (canonical).

## ADHD output
Verdict + chips first (`✅ n · ❌ n · محجوب n`), red first, one card per note, «الخطوة التالية» per item, the copyable one-note command on each card, detail collapsed. See `nj-qa-pipeline/references/adhd-standard.md`.

## References
`references/check-shapes.md` (code skeleton for each shape) · your project profile (`references/<project>.md`, written by you, not shipped) (account classes, hooks, example services) · siblings: `nj-jira`, `nj-automation-suite`, `nj-qa-pipeline`.
