# Worked example — the QA Engineer knowledge base (2026-10-15)

Project: `<QA-project>`. Not part of the method; the
numbers below were read from `kb/qa.db`, `.agent-ops/ledger.md` and the gate
outputs on 2026-10-16.

| Measure | Value |
|---|---|
| Items | 21 ISTQB certifications (Foundation → Expert) + 11 tools |
| Pages | 37 English + 37 Arabic twins (`check_pages.py` 0 failing; `--pair` 0 failing) |
| KB | 1,049 verified, 2 draft, 7 retracted; 298 sources |
| Rules of work | 80 in 8 packs, `rules.py check` 0 violations |
| Code blocks | 100: 61 run-pass, 36 validated, 3 illustrative, 0 failing |
| PDFs | 384 pp EN, 389 pp AR RTL, Thmanyah, check-pdf PASSED |
| Arabic term map | 807 terms, 15 style rules; no official Arabic ISTQB glossary found |
| Topology | Opus Lead → 6 Sonnet service leads → Haiku helpers; 5 translation leads |

Name mismatches the gate surfaced: CT-SEC is Advanced level, not Specialist,
so the report groups it under Advanced — the kind of fact a guessed page gets wrong.

What the council (2026-10-16) found that the run's gates missed: see
`known-failures.md`. The run's verified entries had no stored quotes, so the
measured audit was never done; the next book on this skill will be the first
with a measured residual error rate.

## The upgrade run (2026-10-16, this skill applied to its own first book)

The QA book was upgraded overnight to the skill's own gates (`<QA-project>\.agent-ops\upgrade\RUN.md`).

| Measure | Value |
|---|---|
| Legacy entries surviving the quote gate (pilot, 30) | 14 (53 % failed: provenance text in claims, counts, two-source claims) |
| KB after the upgrade | 1,982 verified, every one quote-bound; 87 retracted; 317 sources |
| Learning-objective entries (verified, query 2026-10-16) | 620 across 21 syllabi |
| Entry audit | first draw 161/162 (1 miss → batch re-verified) · redraw 162/162, upper95 1.9 % |
| Stem-less probe before rewrite | 22 of 24 banks guessable (60–100 %, chance 25 %) |
| After ≤ 2 rewrite rounds | 17 of 32 banks at or under 2 × chance; 15 flagged on the Method page |
| Arabic revision (two revisers, ~56k words) | serious defects 0.5–0.9 / 1,000 words, all fixed; 2.5 / 1,000 incl. style |
| Council | rounds 1–3 on CTFL → CTFL v2 + Playwright rehearsals → sample pages: 5/6/6/6.5/7 → 7/7/7.5/7/6.5 |
| Incidents | KB deadlock (driver scripts holding sqlite), verifier alias by a lead, misdirected verify-batch reviving 5 retracted entries, chapter-summary entries cited on 322 prose sentences — each now a script gate or a brief clause (`known-failures.md`) |
