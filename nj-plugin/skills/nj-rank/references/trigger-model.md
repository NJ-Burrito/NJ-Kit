# nj-rank trigger model

Who runs nj-rank, when, and how results come back. Governance: nj-governance-v4 (`nj-delegate` section 0).

## Lead

- Model: Opus 5.5, effort medium. Sole orchestrator and decision authority.
- Asleep until triggered: the owner's message, a worker's completion notification, or a hook.
- Never polls. Never waits inside a turn for a worker.
- Does not run `nj_rank.py` itself. A Sonnet worker runs `nj_rank.py log` when the owner starts new work and `nj_rank.py file` after a batch of registrations; the Lead briefs it and reviews its receipt.

## Workers

- Model: Sonnet 5.5 runs `nj_rank.py` (one worker per run, in the background). Haiku 5.5 helpers do bounded collection only, one foreground batch inside their Sonnet worker.
- Up to 20 agents live at once, ALL counted (Sonnet workers + Haiku helpers + any other): a ceiling, never a quota; slots via `relay.py slots`. Sonnet workers run in the background (`run_in_background: true`).
- Asleep until briefed. Each Sonnet worker reports once: a receipt file plus at most 25 lines (STATUS / FINDING / EVIDENCE / FILES-SYMBOLS / RISK / NEXT ACTION).
- The worker's completion notification is the trigger. Nobody polls.
- No peer messages. A Sonnet worker briefs only its own Haiku helpers (depth 2: Lead -> Sonnet -> Haiku); helpers never spawn and report only to their Sonnet worker. Artefacts pass by path, through the Lead or the owning Sonnet worker.
- Mid-run changes go to a running worker as `AMEND:` via `SendMessage`. A message that does not start `AMEND:` is not a task.

## Artefacts by path

- Collection lanes write `<project>/work/<run>/lanes/<lane>.jsonl` and `<lane>.detail.md`.
- The Sonnet worker runs `nj_rank.py import <lane>.jsonl` on those files and reports the count to the Lead. Nothing is passed in conversation.
- Filing results live in the registry (`<root>\registry.jsonl`) and each item's `item.json`.

## Safety rules that apply to every trigger

- No Jira write without a read-back. A filing counts only after the GET confirms assignee, Done and attachment count.
- The password never leaves the secrets file, env, or process memory: not in logs, receipts, skills or items.
- Deletions go to the Recycle Bin.
