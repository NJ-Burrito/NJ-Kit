# Ticket sections: what a wrap-up ticket carries

**Bug: use `nj-jira/references/bug-template.md`** (environment, severity + priority table, neutral lineage line, steps, expected, actual, evidence, «أين يُفحص», «لماذا ليس تكراراً», «الشروط المسبقة», «إعادة الفحص»). This file adds only what differs per type.

## Differences per type
| | Bug | Bug (process blocker) | Task (untestable) |
|---|---|---|---|
| Labels | `env-<env>` | `env-<env>` | `env-<env>`, `untestable`, `wrapup` |
| Priority | per the bug-template table | High | Medium default |
| Extra content | | failing-call evidence per nj-qa-pipeline §3c (serial type, timestamp, endpoint, HTTP status, one-line error body, screenshots, console, exact time, what it blocks) | the six sections below |
| Links | Relates: source ticket + service Story | same | same, plus "is blocked by" the key that blocks the test |
| `filed-<lane>.json` row | note, key, type, assignee, links, attachments | adds `kind: blocker` | adds `anchor` (reconcile.py fails a Task without one) |

## Task (untestable): six sections
A Task is filed ONLY when it names a concrete code anchor: a file / class, config key, BPMN node, variable, or template key the developer can open. Without one it is an open item in the report, not a Task.
1. The note, verbatim, cited (`<ticket> · <date> · <author>`, item number).
2. What was tried: request serial type, desk, date, environment.
3. Why it could not be tested at that time (timer cannot elapse, SMS not visible in the UI, path not produced by this request, template not in the repo, blocked by `<key>`).
4. What the design check found (node / variable / ticket cited; "no design pointer found" stated openly).
5. Exactly what the developer must verify in code: the **anchor** (file / class / variable / node / template key) and the expected value.
6. How QA tests it once possible (confirmation steps and regression neighbours, as in the Bug's «إعادة الفحص»).

First description line: «Environment: <env>» when the Task screen has no Environment field (profile).
