---
name: nj-evidence
description: Stand up or query a gated, script-verified knowledge base — a KB of facts plus a rules layer derived only from verified facts, each rule citing the entry ids it rests on. Use to build a fact database, verify a claim, check where a number came from, find rules for a project, decide if a source is independent enough to publish on, or set up fact-gating in a new repo. Triggers: build a fact database, verify this claim, where did this number come from, rules for this project, is this source good enough, set up the evidence gate, قاعدة معرفة, قاعدة حقائق, تحقق من المعلومة, من أين هذا الرقم, قواعد هذا المشروع. For a multi-page book or PDF on top of the KB, use nj-knowledge-book.
---

# nj-evidence

Named by the owner, 2026-09-22, first built in the ENSERA repo. Two layers:

1. **KB** — every fact is an entry tied to at least one source, with a status
   (`draft` / `recheck` / `verified`). Nothing ships off a `draft` entry.
2. **Rules** — short, queryable packs of binding/advisory defaults, each rule
   citing the KB entry ids it rests on (`Because: #<id>`). A rule with no
   verified entry behind it cannot exist — the gate refuses it.

Works in a repo with **no KB yet**: `kb.py init` creates the schema, then
add sources and entries as you go. The rules layer is optional and can be
skipped entirely if a project only needs the fact gate.

## Why the gate is in code, not in an agent's discipline

Three things this method assumes will happen, because they already have:

- **A rule outlives its evidence.** A source goes stale, an entry gets
  demoted, but the rule built on it keeps being quoted. Discipline says
  "remember to check" — code says `rules.py check` fails the build until the
  citation is fixed. In ENSERA this caught a rule ("24 fps always") that had
  no evidence at all once the gate demanded a citation.
- **Absence gets guessed instead of recorded as a gap.** An agent asked "does
  this platform want captions burned in?" will produce an answer either way.
  A KB with no `verified` entry for that topic returns nothing — the correct
  response is "not yet known," not a remembered-sounding guess. Rule packs
  carry a `## Not yet supported` section for exactly this: a gap reads as a
  gap, not a plausible sentence.
- **The verifier is never the author.** A model re-reading its own claim
  confirms it far more often than it catches it — that is not a verification
  step, it is the same judgement asked twice. `kb.py verify` requires a
  `--by` different from the entry's author; the schema records both names so
  a self-verification is visible, not just discouraged.
  **The names are self-asserted, so an alias defeats it** (2026-10-15, QA KB
  run: a lead whose helpers were refused authored as `ct-script` and verified
  as `svc2-lead`; 163 entries passed the gate). Briefs must forbid authoring
  under an alias; an agent that cannot get a separate author leaves entries
  `draft` for an independent verifier. The fix there was a Haiku re-check
  against the raw source text: 167/169 held, one paraphrase was demoted.

None of this needs an agent to remember a policy every session. It needs a
script that refuses the shortcut. That's the part worth porting — the
prose alone (this file) does not do it; the two scripts do.

## The two scripts

`scripts/kb.py` — SQLite, stdlib only, one file per repo (`kb/<project>.db`).

```
kb.py init
kb.py add-batch FILE.jsonl     # strict UTF-8, refuses CR, skips duplicates, one transaction
kb.py verify-batch FILE.jsonl  # {id, quote, raw[, derived]} per row, same checks as verify
kb.py add-source --sector <s> --name "<n>" --url <url> --tier 1-4 [--kind rss|page]
kb.py add-entry  --sector <s> --topic "<t>" --claim "<c>" --sources <id,id> --by <author>
kb.py verify ENTRY_ID --by "<verifier, != author>" --quote "<span>" --raw <file> [--derived REASON] [--second-source ID]
kb.py query  --sector <s> [--topic t] [--status verified] [--full]
kb.py stats
kb.py stale [--days 90]
kb.py export --sector <s>      # writes a checkpoint file, not for pasting into context
```

Tiers: 1 official/standards body/primary, 2 peer-reviewed/institutional,
3 reputable specialist media/vendor docs, 4 community/aggregator.

**The quote gate** (2026-10-16): `verify` refuses unless `--raw` is a file
`fetch.py` (nj-knowledge-book) registered in `research/_raw/index.tsv` for one
of the entry's own source URLs, its sha unchanged, the whitespace-normalised
quote occurs in it, and every number in the claim occurs in the quote (else
`--derived REASON`, counted in `stats`). The QA run's 1,057 verifies in 29
minutes were a status flip with no source read; this is what stops that.

**Verified means:** a tier-1/2 primary source, OR two independent sources
(different hosts, no shared authorship chain — a company blog plus its own
about page is one source under two pages, not two), plus a retrieval date
and a named verifier who is not the author.

`scripts/rules.py` — stdlib only, parses `kb/rules/<pack>.md` files.

```
rules.py for --task "<free text>"      # ranked matches against When + Tags — use this first
rules.py get R-<ID>
rules.py list --pack <pack> [--strength binding]
rules.py index                          # regenerates kb/rules/INDEX.md — never hand-edit it
rules.py check                          # exit 2 if any rule cites a missing/non-verified entry
```

Query, don't read end to end: `for --task` before improvising, `get` for one
rule, `list` to browse a pack.

## Rule block format (fixed — a malformed block is a hard error, not a skip)

```
### R-<PACK>-<NNN> · <title>
**Rule:** <imperative sentence>
**When:** <trigger>
**Because:** #<kb-entry-id>, #<kb-entry-id>
**Strength:** binding|advisory
**Decay:** evergreen|volatile, recheck YYYY-MM-DD
**Tags:** a, b, c
```

`binding` = the default action, overridable by the project owner if the
override names the rule ID and the reason. `advisory` = weighed, no override
note needed.

## Standing up the pair in a new project

1. `mkdir kb` and write `kb/kb.json`: `{"db": "kb/<project>.db", "sectors": [...],
   "primary_hosts": {"<host>": 1}}`. Tier 1 is refused for any host not listed.
2. Run the scripts **in place** from this skill, project as cwd (or `BOOK_ROOT`):
   `python <this skill>/scripts/kb.py ...` — never copy them into the project, a
   copy drifts silently (the QA repo's copy did).
3. `PYTHONUTF8=1 python <this skill>/scripts/kb.py init`
4. Add sources and entries as work happens — the KB grows from real research,
   it is never pre-populated speculatively.
5. Start a `cross`-equivalent pack (`kb/rules/cross.md`) with one rule:
   publish only from `verified`. Everything else grows from there, each new
   rule citing the entries that justify it.
6. Every worker brief in the project reads `rules.py for --task "<the task>"`
   before starting, and every publication step runs `kb.py query --status
   verified` (or the specific entry) before the claim goes out.

## Worked example (ENSERA, not itself part of the method)

ENSERA runs five sectors in one `kb/ensera.db` and ten rule packs in
`kb/rules/`. The 2026-09-22 run found three wrong numbers this way — one
entry citing $72B where the source said $172B, one citing "est. 2005" where
the source said 2006, one citing the wrong dollar figure entirely for a
CAN-SPAM penalty — plus two entries citing the wrong source outright. All
five were caught by the gate plus the verifier-is-not-the-author rule; none
by an agent re-reading its own prose. That is the method's whole case: the
gate, not the discipline, is what catches this class of error.
