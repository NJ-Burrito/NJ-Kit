# nj-researcher

Researches a subject **before** the plan step and leaves a sourced file the plan
reads. 307 curated sources across AI, software, security, medicine, law,
finance, science, data, standards, government, reference and journalism —
Arabic and Jordan/MENA included, not bolted on.

**It is cheap on purpose.** The source list lives in SQLite and is queried by a
script. A lookup costs ~60–300 tokens; loading the whole list would cost ~9–15k.
That is the whole design.

## The five commands

```bash
# 1. what do we already have on this?
PYTHONUTF8=1 python scripts/sources.py query --topic "clinical trial" --limit 6
PYTHONUTF8=1 python scripts/sources.py query --topic "labour" --region jordan --lang ar

# 2. is this source any good?
PYTHONUTF8=1 python scripts/sources.py check --url "https://example.com/report"

# 3. keep a new one you have actually looked at
PYTHONUTF8=1 python scripts/sources.py add --name "..." --url "..." --domain data \
  --tier 1 --lang ar --region jordan --state verified \
  --for "what it is authoritative for" --why "why it earns that tier"

# 4. write the checkpoint file the plan reads
PYTHONUTF8=1 python scripts/sources.py export --topic "labour" --region jordan --out research/jordan.md

# 5. what is in the box
PYTHONUTF8=1 python scripts/sources.py stats
```

Also: `cost --topic X` prints what a lookup costs vs loading everything;
`candidate` / `candidates` / `promote` record and admit sources found by web
search; `seed --reset` rebuilds from `data/seed.tsv`.

## Reading a result

```
#103 t1 ClinicalTrials.gov [medicine/en/global] https://clinicaltrials.gov/
    FOR: what a trial pre-registered vs what it later reported
```

`t1`–`t4` is the tier (1 = the body that makes the fact, 4 = aggregator, never
cite). A **`?` before the name means the URL has not been confirmed** — 83 of
the 307 seeded rows are like this. Confirm before citing.

`FOR:` is the scope. A source is authoritative *for that*, not in general.

## What it deliberately does not do

- **Does not plan.** It hands the plan step a file.
- **Does not publish.** The ENSERA gate still applies: tier-1/2 primary, or two
  genuinely independent sources on different hosts, plus a retrieval date and a
  verifier who is not the author.
- **Does not decide truth.** `check` reads structure — host, TLD, path, whether
  it is a bare homepage or a press release — and then prints the questions a
  script cannot answer (who funds it, is it independent of your other source,
  is it inside its field's decay window).
- **Does not guess.** No match means "no match". `unsure` is a valid verdict and
  a fabricated URL is the one unrecoverable error.
- **Does not crawl on a schedule.** Freshness is checked per use.

The judgement rules — tiers, peer review, funding, recency half-lives,
independence, prestige vs authority — are in `references/RUBRIC.md`. They are
written down so they can be argued with.
