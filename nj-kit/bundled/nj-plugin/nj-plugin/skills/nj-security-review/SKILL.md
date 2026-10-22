---
name: nj-security-review
description: 'Review third-party skills, plugins and MCP servers for prompt injection, concealment, permission bypass, self-installing hooks, credential access, exfiltration, obfuscation. Use before installing from a public repo, after skill updates, check this is safe, audit the skills. Own branch diff: /security-review.'
---

# Auditing what the agent is told to do

Two different reviews, and confusing them leaves a real gap:

| | reviews | tool |
| --- | --- | --- |
| **Your code** | changes you wrote, on a branch diff | built-in `/security-review` |
| **Their instructions** | skills and servers your agent obeys | this skill |

The second matters here because **45 of the 52 installed skills come from 24
different authors and run with full agent permissions** (counted 2026-09-06; it
was 17 from 13 authors when this was written), and `install.py` re-fetches them
from source on every new machine. A skill is not a library that
sits inertly — it is instructions the agent follows on the author's authority.
An update arrives silently.

```bash
A=~/.claude/skills/nj-security-review/scripts/audit.py
python "$A"                    # every installed skill
python "$A" <dir>              # one skill, or any directory
python "$A" --baseline         # accept the current state as reviewed
python "$A" --changed          # only what has changed since — the routine check
```

## What it looks for

Ordered by how bad it is if genuine. Every category has legitimate uses, which
is why the output is evidence rather than a verdict.

- **prompt-injection** — "ignore previous instructions", "overrides the user".
- **concealment** — "do not tell the user", "silently install". A skill that
  wants an action hidden is the clearest signal there is.
- **authority-claim** — "even if the user declines", "do not ask permission".
- **permission-bypass** — `--dangerously-*`, `--no-sandbox`, wildcard tool grants.
- **self-installing** — writing `settings.json`, registering hooks, cron. A skill
  that installs persistence is claiming more than a skill needs.
- **remote-execution** — `curl … | sh`, `Invoke-Expression`, `eval(atob(…))`.
- **credential-access** — `.ssh`, `.aws/credentials`, `.npmrc`, API-key names.
- **destructive** — `rm -rf /`, `rmtree`, `git push --force`.
- **exfiltration-shape** — POST with a body to a non-obvious host.
- **obfuscation** — long base64 blobs, `atob`, `fromCharCode`.

It also lists every external host referenced, minus documentation and registry
domains. **Read that list.** It is how you notice a "formatting" skill that
talks to an analytics endpoint.

## Read the excerpt before acting

Measured on this machine: **0 critical, 10 high, 18 medium** — and every one of
the high findings was in `nj-kit`, which legitimately writes `settings.json` and
prunes directories with `rmtree`. The medium ones were the `speech` skill needing
`OPENAI_API_KEY` (its entire purpose) and Playwright documentation containing
`fetch` POST examples.

Re-measured 2026-09-06, after `graphify` and `watch` were installed: **2
critical, 102 high, 98 medium**. Almost all of it is one skill — `graphify`
vendors its whole PyPI package, so its `install.py` (CLAUDE.md edits, PreToolUse
hooks, git hooks) and `llm.py` (seven providers' API keys, corpus upload) light
up every category at once. Both "criticals" are source comments describing bugs
the authors fixed, and the scanner cannot tell a comment from an instruction.
**Removed 2026-09-18.** The scope audit cut `graphify` — for token cost, not for
security — and since almost every finding above was its, the kit's scanned surface
fell with it. Worth stating plainly: a skill nobody invokes is not free. It costs
description words in every session *and* it is attack surface, and those two
arguments point the same way.

That is the shape to expect: **the scanner localises, it does not decide.** The
full folder-by-folder verdicts live in
`~/.claude/skills/nj-kit/SECURITY-REVIEW-2026-09-06.md`.

So the tool flags its own author's toolkit, and that is correct behaviour. A
scanner tuned to produce a clean sheet on the code its author wrote is a scanner
that will also miss somebody else's. **Its job is to put the line in front of
you, not to decide.** Anything that never fires has stopped being a check.

## The routine: baseline, then diff

A one-off audit protects you once. Skills update.

1. `python "$A"` and read it once, properly.
2. `python "$A" --baseline` to record what you accepted.
3. `python "$A" --changed` after any install or update — it reports only skills
   whose content digest moved, marked `CHANGED` or `NEW`.

`install.py` runs the `--changed` audit after fetching, so a fresh machine never
silently installs a version nobody looked at.

## What this does not cover

Said plainly, because a partial audit that feels complete is worse than none:

- **It reads text, not behaviour.** A script that assembles a hostname at
  runtime will not match a URL pattern.
- **It cannot judge intent.** `rmtree` in a cleanup helper and `rmtree` in a
  payload look identical.
- **MCP servers are worse.** Their code lives in `node_modules` after `npx`
  fetches it and is not audited here at all; treat adding a server as the
  higher-trust decision it is, and prefer first-party ones.
- **It is not a substitute for reading a skill you are about to trust** with
  something sensitive.

## Scanning a live web app we own

Different job from auditing skills: this probes a running site. Owned or
authorised targets only; ask before anything not ours.

- **ZAP baseline first** (passive, safe): start Docker Desktop, run
  `docker run --rm -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t <url> -J zap.json -r zap.html`,
  then quit Docker Desktop.
- **Strix second**: `STRIX_TELEMETRY=0 STRIX_LLM=anthropic/<current sonnet id> strix -t <url>`.
  Telemetry off every time; Claude only; no key is configured yet, so ask the owner
  before the first run. It is an active agent: owned targets, never production
  data we cannot lose.
- Treat findings as leads: reproduce each one before it goes in a report.
- Install lines and caveats: `nj-kit` manifest `tooling.optional`, `house_style.web_scan`.
