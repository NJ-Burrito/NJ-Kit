# Team topology — NJ Governance v4 (on-demand)

The reference behind `SKILL.md` §0.3, §0.17–0.21 and §0.28. The data form is
`nj-agent-ops/templates/roles.json`; if the two differ, `roles.json` wins and `check_governance.py` fails.
Model names, ids, aliases, prices and effort per role: `runtime-map.md` only (D21).

## The tree

```
Lead (Opus Lead, medium, 1 per interactive session, outside the 20)
 ├─ team agent  (Sonnet)  nj-agent · sdlc-requirements · sdlc-design · sdlc-build · sdlc-test · sdlc-release · researcher-*
 │    └─ helper (Haiku)   nj-helper-reader · nj-helper-runner · nj-helper-writer · crew-* (writers enabled, D24)
 ├─ reviewer    (Sonnet, high)  nj-reviewer · sdlc-review (may spawn helper-reader/runner) · council-* seats (leaf)
 └─ (job)       headless Task Scheduler work, not under a Lead
```

Depth 2: the platform withholds `Agent` from a helper (`disallowedTools: Agent, SendMessage`,
`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=2`). Nobody instructs a sibling. The Lead spawns team agents and
reviewers only, with explicit model and effort; it never spawns a helper directly.

## Role matrix

| Role | Edit / Write | Git | Reports to | Woken by |
|---|---|---|---|---|
| Lead | only `handoff.md`, `work/lead/**`, `work/governance/**`, the memory directory | read-only directly; every write through `gov4.py` with a ticket | Nader (one report, AskUserQuestion for decisions) | team-agent completion, flag files, command exit, Nader; never a helper, never polling |
| Team agent | its OWNED_PATHS inside its worktree (git) or its claimed paths (non-git); protected and live paths denied. `requirements` and `design` have no Bash; `test` and `release` write only under tests/ and release/; researchers write inside their OWNED_PATHS (decision D16), not the renderer | code writers (`nj-agent`, `sdlc-build`): add, commit (trailers) on their own `worktree-<run>-<role>-<n>` branch; document writers, `sdlc-test`, `sdlc-release`: never commit (D23); all: status, diff, log, show, restore of own paths, own stash, read-only merge-tree and rev-parse | the Lead only: one receipt of ≤ 25 lines as text, with BRANCH, HEAD, GATES@HEAD, a DETAIL block | the Lead's Agent call; `AMEND:` messages |
| Reviewer | none | read-only verbs | the Lead: file:line findings, correctness and stated-requirement gaps only | the Lead, after the author's receipt and gate lines exist |
| Helper | reader none; runner none (gate output returned as text); writer (enabled, D24) a sub-partition inside the parent's OWNED_PATHS | none (runner: read-only status, diff, log, show) | its parent only: at most 10 lines | the parent's Agent call |
| Job | `NJ_WRITE_ALLOW` (broad on purpose: a mistake guard, not a boundary) minus protected paths | none | the launching script, via a JSON file; non-zero exit if the output file is missing | Task Scheduler |
| Unknown caller | unrestricted and logged (v3 behaviour) so nothing is silently locked out | git writes, outward actions and `gov4.py` write subcommands denied | n/a | n/a |

The platform removes from every subagent: AskUserQuestion, Workflow, EnterPlanMode, ExitPlanMode,
ScheduleWakeup, EndConversation.

## Identity table (clause 0.28)

Decided in this order; the first that matches wins.

| # | state | how it is known | grade |
|---|---|---|---|
| 1 | `agent` | the hook input carries `agent_id` | [V] S2: subagent Bash hooks 2/2 |
| 2 | `job` | `NJ_ROLE=job` in the environment, set only by `claude_run.py` | [V] design; e2e pending |
| 3 | `lead` | the session was registered by the `SessionStart` hook in `~/.claude/nj/leads.json` (source startup/resume/clear, entrypoint in `roles.json` `lead_entrypoints`) and the call has no `agent_id` | main-thread `agent_id` absent [V] headless n=1; interactive [A] S2 |
| 4 | `unknown` | anything else: an unmigrated headless script, a second tool | by definition |

An agent wrongly seen as Lead would be write-restricted, so that failure is visible. The remaining risk
is a wrongly seen Lead obtaining a ticket; the interactive S1/S2 (background and resumed agents) rule it out.

## Tickets

`PreToolUse(Bash|PowerShell)` for a registered Lead and a `gov4.py` write subcommand writes a single-use
ticket (nonce, sha256 of the normalised argv, 60 s expiry) to `~/.claude/nj/tickets.json` and prefixes the
command with the nonce through `updatedInput` [V] S2 3/3. `gov4.py` refuses write subcommands without a
valid ticket (exit 3), burns every nonce found in `NJ_TICKET` after the first match, and sets the git-hook
token only inside its own subprocess. Agents cannot obtain a ticket (the hook mints only for the Lead) and
the `reference-transaction` and `pre-push` hooks reject updates of main, master, tags and remote refs
without the token. Tickets are checked only in enforce (D27). Exempt from the ticket: `mode off`, a human at a terminal, tickets-mode habit. If
`updatedInput` ever stopped working, the ticket layer falls back to HABIT and the deny rules plus git
hooks stay. Method files in the live tree are protected paths after activation; `gov4.py unlock`
(one hour, after Nader approves through AskUserQuestion) opens them.

## Helper allowance

Default 3 helpers per team agent, hard maximum 4; helper-writer at most 2 of the 4 (enabled, D24); browser or recorder helper lanes 2 machine-wide. The plan rule is
`S + sum(HELPERS_i) <= wave`. A helper's OWNED_PATHS lie inside its parent's partition (checked by
`check_governance.py --run`, at spawn by the hook and at merge). The parent keeps judgement, integration,
shared state and every commit; it gives helpers work that is bounded, verifiable, on a disjoint
sub-partition, with a free oracle (extract, list, grep, run a gate, count, diff). A failed helper is redone
once by its parent (`REDO-BY-PARENT`); the parent does not return while any helper is live and reports
`HELPERS_SPAWNED`. Helpers share the parent's worktree [V] S5 headless, load no heavy skills, and return at
most 10 lines of text; a CHALLENGE goes up one level.

## Git rights

| Who | May | May not |
|---|---|---|
| code writer | status, diff, log, show, add, commit with trailers `Agent-Id`, `Task-Id`, `Co-Authored-By` (the attribution line the session gives) on its own `worktree-*` branch; restore of own paths; own stash; read-only merge-tree and rev-parse | push, merge, rebase, reset --hard, branch -D, tag, worktree add/remove, update-ref, remote, config, fetch, pull, cherry-pick, checkout or switch of another branch, `--no-verify`, `git -c`, `git -C <other>`, `--git-dir`, `--work-tree`, `GIT_*`, `core.hooksPath`, `gh pr merge|create` |
| document writer, test, release | status, diff, log, show, restore of own paths; no commit: the Lead reviews with `gov4.py review --unstaged` and commits with `gov4.py checkpoint` | everything above, and `add`/`commit` |
| helper | none (runner: read-only) | everything above |
| Lead | read-only git; every write through `gov4.py` (`checkpoint`, `merge`, `push`, `sweep`, …) with a ticket | raw git writes (deny rules apply to the Lead too); force push |
| job | none | all |

Layers (spec section 9): `permissions.deny` for the plain forms; `gov4_hook.py git` (tokenises, unwraps
`sh -c`, `bash -c`, `pwsh -c`, `cmd /c`, absolute git paths; an unparseable git command is denied for
agents, jobs and unknown callers); the git hooks in the shared hooks directory (independent of the hook's
view of the caller, so a Python or Node wrapper around `git push` still hits them; `--no-verify` does not
bypass `reference-transaction`); a dead `pushurl`. The git-hook red team (WP5) let `push --no-verify` and
`git -c core.hooksPath=` through by design: those rest on the deny rules and the hook. These layers guard
against mistakes and injected instructions, not a determined agent; native Windows has no sandbox and the
stored credential is readable by agent shells. A GitHub ruleset on main (after `gh auth login`) is the only
non-bypassable layer. Residual risks: § Residual risks. Outward actions (`li.py post|comment|like|due`, the `mcp__linkedctl__*` write verbs)
are the Lead's or the scheduler's only.

## Concurrency and the ramp

- Ceiling 20 live (Sonnet + Haiku + running jobs; Lead excluded), enforced by the platform cap. The
  registry `~/.claude/nj/live.json` is advisory (board line `live N/20`, alerts, wave planning); a lock
  timeout allows the call and raises `ALERT-registry.flag`; entries with no transcript write for 15 minutes
  are suspect and excluded.
- Operating wave: `gov4.py wave 5|10|20`, default 10. `wave 20` needs `relay.py verify` clean at a peak of
  10 or more with 0 rate-limit incidents (decision D4). The golden set is the precondition for any cost or
  speed claim, not for wave 20.
- Sub-limits: writers 6 (3 until Lead tokens per merge are measured), research 4, reviewers and council 6,
  browser or recorder lanes 2.
- Rate limits: the stop hook reads the transcript tail for 429/529 and writes `pause.flag`; while it exists
  spawns are denied. Resume by `SendMessage` is not relied on until S7; the fallback is a fresh agent from
  the last commit of the surviving branch. Waves of 5 with a 5 s gap; a per-batch token budget is read from
  the ledger at each wave boundary.

## Flat mode (the fallback if nesting is ever disproved)

The Lead launches team agents and Haiku helpers as siblings in one batch. A team agent returns
`helper_requests` (task, owned sub-paths, verifier) in its receipt instead of spawning; the Lead launches
the helpers as a second wave and routes their results by path to the requesting agent. The 20 cap, git
rights, ledger parent field, merge flow and sweep are identical. Clauses 0.3, 0.5 and the helper parts of
0.21 stay HABIT. S0 passed (tree mode), so this is the design only if S0 is disproved.

## Non-git projects

No `.git` is created in any of Nader's folders without asking. Work in place on disjoint OWNED_PATHS,
one writer per path, at most 3 writers (1 for a risky change); `gov4.py snapshot begin|diff|apply|commit`
(manifest, zip into `_sources`, shadow bare repo under `_shadow`). The write hook confines agents to the
union of active claims [V] S9. Isolation `worktree` is refused in a non-git folder [V] S6.

## Activation and modes

Each decision is defined here once; `SKILL.md` and `nj-agent-ops/SKILL.md` cite it.

- **D20 Deny rules wait for enforce.** A permission deny rule blocks in every mode and in sessions that are
  already open. Audit activation therefore writes only: env, `effortLevel` medium, hooks, agents, the
  `Agent` model denies (Opus and its aliases, Fable) and the secret-path denies. The git-write and `gh pr`
  deny rules are written by `gov4.py mode enforce` and removed by `gov4.py mode audit|off`.
- **D21 Model names.** Ids, aliases, versions and prices exist only in `runtime-map.md`, `roles.json` and
  agent frontmatter. Method text may use the role words Nader uses (Opus Lead, Sonnet agent, Haiku helper).
- **D22 No interpreter.** The per-session interpreter is retired in v4 and `roles.json` has no type for it.
  Receipts are digested by the SubagentStop hook and `gov4.py review`; nothing sits between Nader and the Lead.
- **D23 Git flow per type.** Code writers (`nj-agent`, `sdlc-build`) in a git repo run isolated
  (`isolation: worktree`, the Lead's call) and commit on their own `worktree-*` branch. Document writers
  (`sdlc-requirements`, `sdlc-design`, `researcher-*`) and `sdlc-test` / `sdlc-release` run in the main
  checkout as the single writer of their OWNED_PATHS and never commit; the Lead reviews with
  `gov4.py review --unstaged` and commits with `gov4.py checkpoint`. Reviewers write nothing. The brief's GIT
  field says `own worktree-* branch` or `none (main checkout, single writer)`.
- **D24 Helper writers enabled.** `nj-helper-writer` and the project `crew-*` types are enabled: S5 passed
  headless (a helper's cwd equals its parent's worktree).
- **D25 Agent definitions** live in `install/agents/` in staging, never a plugin-root `agents/` (the platform
  loads that folder as plugin agents). Every definition carries `maxTurns`: team 300, reviewer 150, helper 40.
- **D26 Hooks fail open outside enforce.** A missing launcher, missing interpreter, crash or timeout never
  blocks in audit or off; the hook command survives a missing launcher file through a tiny guard that exits
  0 when the file is absent. `onFailure: "block"` on the Agent hook is added by `mode enforce` and removed
  by `mode audit|off`. `doctor --settings` checks that the pinned interpreter really runs the launcher
  selftest and refuses the WindowsApps stub.
- **D27 Tickets only in enforce.** In audit `gov4.py` logs a would-refuse and proceeds; in off nothing. The
  env overrides `NJ_MODE_OVERRIDE`, `NJ_TICKETS` and `NJ_HOME` are ignored when the caller is an agent or a
  job, and the git hooks never read them: they read a state path baked in at `install-repo`. In audit the
  ticket hook neither rewrites commands nor answers ask.

## Residual risks

Stated, not hidden; none is claimed closed.

- **D28 File integrity.** Windows has no sandbox: an agent shell can write any user file, so HMAC or ACL on
  `~/.claude/nj` is out of scope. The hook denies agent, job and unknown shell commands that name
  `~/.claude/nj` or `.git/hooks` in any argument, scans more write forms (`sed -i`, `perl -pi`,
  `Set-Content`, `Add-Content`, `Out-File`, `[IO.File]::Write*`, `truncate`, `dd`, `chmod`) and rejects a
  `bin/CURRENT` pointing outside `~/.claude/nj/bin`. A determined agent can still tamper; review and the
  ledger are the detection.
- **D29 Outward actions.** Linkedin `li.py` is untouched in v4: the hook denies the sibling posting scripts
  by name for agent, job and unknown callers, and the `mcp__linkedctl__*` rule is deny-by-default except
  reads (`*_get`, `*_list`, `stats_*`, `whoami`, `auth_status`). A script an agent writes and runs itself
  that calls the API is not covered.
- Git: the credential is readable by agent shells; only a GitHub ruleset on main is non-bypassable.
- Audit mode never refuses (D26, D27); the interactive half of S1/S2/S7 runs in the first fresh Lead session
  after activation (decision D14).
