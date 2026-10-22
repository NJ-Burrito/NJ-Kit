# NJ Governance v4 — binding decisions (the owner 2026-10-16 + Lead)

Sources: the owner's instruction 2026-10-16; his answers (AskUserQuestion, 2026-10-16); design.md (R2); inventory.md (R1, 305 clauses, 98 conflicts).

## Roles
- **Lead** = Opus 5.5, effort medium. Reviews, decides, adjudicates, delivers, git merge (and push only where the project's CLAUDE.md allows a remote push). Writes ONLY admin files: handoff, logs, CLAUDE.md, memory, trackers, and Jira review writes (comments/transitions). Every build/fix/script → a worker. (the owner: "Admin files only".) Lead's diff+gate review before merge is the merge gate, not "self-verification" (run-once exception unaffected).
- **Sonnet lead** = Sonnet 5.5, background, completion is the trigger; owns one bounded phase; runs in its own git worktree where the project is a git repo; commits only, never push/merge; briefs Haiku helpers; reviews each helper receipt; reports once (≤25 lines + receipt).
- **Haiku helper** = Haiku 5.5, one FOREGROUND batch per phase inside a Sonnet lead; mechanical bounded work; no Agent tool (cannot spawn), no git push/merge, no secrets paths; reports once to its Sonnet lead.
- Depth 2 max: Lead → Sonnet lead → Haiku helper (env `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2`).

## Counts
- **≤ 20 agents at a time, ALL counted** (Sonnet leads + Haiku helpers + nj-rank workers + any other). Ceiling, never a quota. Default shape 4 leads × ≤4 helpers. Slots claimed via `relay.py slots`.
- **Helpers required** when the brief declares ITEMS=n: 0 if n<6, else min(4, ceil(n/6)); verified from the SubagentStart spawn log, not the receipt.

## Interpreter
- Kept: every reply opens with «Interpreter:» — **written by the Lead itself**, no Haiku agent spawned (saves a slot). PROJ UserPromptSubmit hook text updated accordingly.

## Git
- PROJ: `git init` (local only, no remote) with a .gitignore for credentials, settings.local.json, fonts, artefacts, recordings, node_modules, Delivery outputs.
- Workers commit on branches/worktrees; Lead reviews `git diff --stat`, then only risk-high diffs, requires green checks, merges.
- Push: only where the project's CLAUDE.md allows it; QA-Wrap's "never git push" stays (project rule).

## Kept from v3
Trigger-only reporting (no polling, no progress chatter, report once), graded facts [V]/[A]/[U] + CHALLENGE, single writers + claims, budgets as ceilings, never leave leftovers + sweep, credentials never printed (helpers never cat/print a creds file), deletions to recycle bin, run-once Owner exception.

## Dropped / superseded
"workers never delegate" (now: Sonnet → Haiku only) · "minimum-sufficient, zero workers often right" for the Lead (Lead never works; workers decide helpers by the ITEMS rule) · Opus as worker escalation tier (escalation haiku → sonnet only; Opus = Lead) · cron watchdog / monitor polling · "Lead does small work" · Sonnet-only templates · "every worker background" for helpers (helpers foreground inside their lead).

## Gates to build (machine-checked)
relay.py: `slots` (claim/release, refuse >20), nested Sonnet→Haiku allowed (no BREACH), NEXT_TIER drop opus, `verify` checks helpers-required vs spawn log, `leakscan` (receipts/briefs vs known secrets) · hooks: SubagentStart spawn log; PreToolUse deny `git push`/`git merge` for non-Lead agents; deny reading secrets paths for helpers · agent definitions `~/.claude/agents/sonnet-lead.md`, `haiku-helper.md` (model, effort, tools) · check_governance.py updated (no-delegation clause → hierarchy clause).

## Side findings to report to the owner
Plaintext TAISCE_TOKEN in <PROJ_ROOT>/.claude/settings.local.json; OpenRouter key + Jira password printed into a local transcript 2026-10-16 → rotate. export.py --if-changed skips CLAUDE.md → always explicit re-export.
