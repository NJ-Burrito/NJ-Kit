# Haiku-helper brief (NJ Governance v4) — written by a Sonnet lead, ≤ 12 lines

Canonical policy: `nj-delegate/SKILL.md` §0 (not restated here). One bounded mechanical job,
one report file. Send the helpers of a batch in ONE message, foreground, `model: "haiku"`.

```
Governance: nj-governance-v4 · you are a Haiku helper, depth 2 of 2 (agent type haiku-helper).
TASK        <helper-id> of <k> · <one mechanical job: grep | read | extract | count | probe | sync | image log>
MODEL       haiku
INPUT       <exact paths / line ranges / symbols — evidence by path, no whole-repo reads>
WRITE       ONLY <one report path>. Nothing else on disk. Append, do not edit in place.
OUTPUT      <the table / list / counts expected, with its exact columns>; one line per finding, file:line cited
BUDGET      <= 15 tool calls · <= <F> files read · stop and say so at 80% · no new output for <N> min => stop, name the cause
NO_SPAWN:   no-spawn clause (model haiku): you have no Agent tool and never spawn or brief anyone; no git push / git merge / checkout main;
            never read or print a secrets path or file that looks like credentials (~/.claude/secrets, *creds*, .env*);
            never decide, fix or edit outside WRITE; no polling, peer messages or progress; deletions via safe-delete
REPORT      ONE reply, <= 10 lines: STATUS / what you found / report path / anything you could not do. Then stop.
```

If a fact in INPUT looks false, reply `CHALLENGE: <claim> — <counter-evidence>` and stop that
line. The Sonnet lead reads your report file and your receipt before it reports upward; you
never see a sibling's output.
