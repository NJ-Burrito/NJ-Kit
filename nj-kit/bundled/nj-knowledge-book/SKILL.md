---
name: nj-knowledge-book
description: Builds a sourced, gated knowledge book on one domain: research checkpoints, a verified fact DB (nj-evidence), numbered pages that cite only verified entries, practice banks that teach, rules of work, an optional Arabic twin and one PDF per language. Use when the deliverable is a multi-page book, study guide, certification-prep set, handbook or mentor path, even if the user only says "everything about X for a new engineer" or «دليل دراسة، كتاب معرفة، دليل للمبتدئ». Not for: a fact DB or one claim check with no pages (nj-evidence), one research note (nj-researcher), one document (doc-coauthoring), a PDF from existing HTML (pdf-typography).
---

# nj-knowledge-book

A book whose every hard fact traces to a quoted span of its own source, whose
pages teach rather than summarise, and whose gates are exit codes. It adapts to
the domain: page kinds, team size and reviewers are derived, not configured.

**Needs:** `nj-evidence` (owns `kb.py`, `rules.py`), pandoc, `mmdc`,
`pdf-typography` (headless Chrome), poppler. pymupdf and fontTools turn two
report checks on; without them those checks print SKIP and the gate exits 3, never 0.
`PYTHONUTF8=1`, uv never pip.

## What the gate proves, and what it does not

Every cited fact is a `verified` entry whose **quote occurs in a file `fetch.py`
downloaded from that entry's own source**, unchanged since, verified by an agent
with a different name than its author. It does not prove the source is right,
that a page sentence keeps the entry's meaning, or that two names are two minds
(independence is by name). The residual error is **measured** by a blind audit
before authoring and printed on the Method page as n, misses and the 95 % upper
bound (0 misses in n → ≤ 3/n). Never write "0 % error".

## Dynamic by default

| What adapts | From | How |
|---|---|---|
| Page template, required headings, teaching checks | `kinds` in `book.json`: certification · tool · regulation · topic · practice | built-in profiles; `headings` / `min_cites` only to override |
| Team size and waves | item count and live slots | `book_status.py plan --slots 20` prints solo, or leads with `MAX_HELPERS` for one wave first and the multi-wave option second, with the arithmetic |
| Objective ids | official ids if the issuer has them, else generated `<slug>-<n>` | never silently skipped |
| Reviewers | the book's profile | council of 5 POVs picked from a pool — `reference/council.md` |
| Twin, banks, samples stages | `twin`, `banks.print`, code blocks present | stage skipped only when its input is absent |

Minimum `book.json`: `{"title", "slug", "pages", "kinds": {"<folder>": "<kind>"}}`.
`kb/kb.json`: `db`, `sectors`, `primary_hosts` (required before any tier-1 source).

## Stages — each leaves a file; each gate is a command

Scripts run in place (`python <skill>/scripts/X.py`), project = cwd or `BOOK_ROOT`.
Phases A → V → B are separate dispatches; the Lead is the hand-off between them.

| # | Phase | Checkpoint | Gate |
|---|---|---|---|
| 0 | Plan | `PLAN.md`, `book.json`, `kb/kb.json` | `selftest.py` exit 0 (3 = named tool missing); `book_status.py plan` |
| 1 | A Extract | `research/<slug>.md`, `_raw/` + `_raw/index.tsv` via `fetch.py` | `fetch.log` has no unhandled 429/403; `kb.py hygiene --apply` (provenance out of claims) |
| 2 | V Verify | entries verified with quote + locator | `kb.py verify-batch` refusals = 0 unexplained |
| 2b | V Audit entries | `audit/entries.md` | `audit_sample.py draw --entries [--topic T]` → `check` exit 0 (recounted from the DB) |
| 3 | B Author | pages on their kind's template | `check_pages.py` 0 failing |
| 3b | B Teach | `practice/<slug>.md` + `.key.md` banks, mentor path | `check_teach.py` (+ `--path`, `--resemble`) 0 failing; tool pages `check_tool.py` |
| 3c | Probe banks | `audit/probe/<slug>.{txt,ans}` | `probe_bank.py make` → a Haiku sees options only, writes `.ans` → `probe_bank.py score` exit 0 (keyed ≤ 2 × chance) |
| 3d | Audit banks | `audit/banks.md` | `audit_sample.py draw --banks` → `check` exit 0 (both audits needed by the report) |
| 4 | Rules | `kb/rules/*.md` | `rules.py check` exit 0 |
| 5 | Samples | `samples/RESULTS.md` per code block | habit, no script: 0 STILL-FAILING in the run's own counts; billable blocks `not run: reason` |
| 6 | Twin | twin pages + banks, term map first; `check_pages.py --stamp` after each revision | `check_pages.py --pair --terms` 0 failing + `arabic-english-proofreading/scripts/scan.py` exit 0 |
| 7 | Report | `report/<slug>.{md,html,pdf}` + Method page | `build_report.py` (refuses without both audits passing), `check_report.py` PASS |

Failing gate: `heal.py <stage>` (below). Resume: `book_status.py` marks a stage done only when its gate passes; re-brief
the rest. **Disclosed tolerance (owner only):** `book.json` `audit_tolerance.{banks|entries} = {max_misses, decided_by}` lets an audit pass as `DISCLOSED` (never `ok`); the Method page prints n, misses, the missed ids and who accepted it. Only the owner sets it, after the stop rule fired (QA book, 2026-10-16: banks 91/92). A late addition to the KB is audited with `audit_sample.py draw --entries --topup`, not a redraw.

**Audit misses:** each missed entry is demoted (`kb.py demote` lists, and exits 2
on, every rule and page still citing it — fix those first), its verifier's batch
is re-verified by a different run once, and a new sample is drawn; a second
failing audit stops the book and reports — no third draw. A verifier's "weak"
(claim wider than its quote) means amend the claim narrower or leave it draft —
never keep the wide claim. **Small book (≤ 5 items):** one context, no phases, no council beyond
one devil pass on the plan — the gates still run.

## Healing — `scripts/heal.py <pages|teach|entries|banks|rules|pdf>`

Runs that stage's gate. Green: logs "nothing to heal". Red: classifies the output against known failure classes
(`known-failures.md`, column Heal), applies a SAFE repair or prints the exact manual repair, re-runs only that gate, and
appends one line to `audit/heal.jsonl` (action clean / healed / manual / refused). `heal.py report` prints attempts,
healed, manual, refused, heal rate, stages re-run, open items. **Never weakens a gate:** the only auto-repair is
`glyph-gap` (typographic char to its ASCII twin in pages, backed up to `.agent-ops/heal/backup/`); claims, keys, quotes,
bases and audit results are advise-only, and `--force-edit` on them is refused and logged. Unknown class: manual, then add a row.

## The accuracy rules

1. Hard facts come from the issuer's own page or document and are entries before
   a page states them. Tier 1 = a host in `primary_hosts`, signed off at stage 0;
   vendor docs are tier 1 only for that vendor's own product.
2. Author ≠ verifier ≠ auditor. Names sharing the part before the first hyphen are
   one agent. Briefs forbid aliases. **A lead never verifies its own helpers' entries.**
3. A page cites `[KB#id]` of a verified entry or writes "not confirmed". A prose
   number has a cite, a `[calc]` tag, or sits in a worked-example block (illustrative data).
4. Retired or renamed items are stated as such, with the source.
5. Case studies: "Illustrative scenario, not a real company." Regulated domains
   add "not legal or regulatory advice".
6. Licensed questions and past exams are linked, never copied. Practice questions
   are original; each has a `basis:` and arithmetic `calc:` lines are evaluated.
7. Tool steps come from the vendor's current docs (context7) with the version.
8. No readable tier-1 text (paywall, 403): draft, "not confirmed", the book names the gap.
9. What a quote cannot carry is not an entry: a **count** over entries ("64
   objectives") is a `[calc]` over the verified entries; an **absence** ("no sunset
   notice") is a scripted text search logged in the research note. Version labels
   in a claim are exempt from the number rule when the source's name carries them.

**Owner exception:** verification, audit and council are the accuracy gate the
project requires, not a re-check of a delivered output; they run once each. The
blind-learner probe runs only in the rehearsal.

## Start a new domain

1. `book.json` + `kb/kb.json`; `kb.py init`; `selftest.py`; `book_status.py plan`.
2. One rehearsal page end to end, with a blind-learner probe (a Haiku given only
   the concepts section and the unkeyed questions; disagreement is a defect).
3. Council rounds 1–2 on the plan and the rehearsal page; the owner approves.
4. Fan out by phase; council round 3 on a first-wave sample, before the twin and report.
Never pre-populate the KB speculatively.

## Reference

| File | Read when |
|---|---|
| `reference/page-template.md` | writing or gating a page, a bank, the mentor path |
| `reference/council.md` | stage 0–4 reviews, or changing this skill |
| `reference/orchestra.md` | `plan` says more than solo |
| `reference/arabic-twin.md` | `twin` is set |
| `reference/report.md` | building the PDF |
| `reference/known-failures.md` | before each stage; after any surprise |
| `reference/worked-example-qa.md` | you want the first run's numbers |

Neighbours own their topics: `pdf-typography`, `arabic-english-proofreading`,
`nj-evidence`, `nj-delegate`, `devil`. This skill adds only the book-level gates.
