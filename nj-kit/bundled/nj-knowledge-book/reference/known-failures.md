# Known failures — each has an owner and an action

Rule: a failure that happened twice, or silently once, becomes a script gate.
An agent is for judgement only.

| Failure (first run) | Class | Who acts | Now prevented by | Heal |
|---|---|---|---|---|
| Lead's helpers refused by the 20-slot cap; lead self-extracted, verified under alias `ct-script`: 162 entries passed | resource → spec | lead stops, Lead re-dispatches | slot arithmetic; refused spawn = stop; brief forbids aliases |  |
| 1,057 verifies in 29 min, 99 % within 2 s of each other: status flipped in a loop, never read | spec | verifier | `kb.py verify` needs `--quote` found in `--raw`; blind audit stage 2b |  |
| A paraphrased "quote" not in the syllabus (entry 797) | accuracy | verifier | quote-in-raw check |  |
| CRLF in a hand-made batch file corrupted 6 entries | tooling | script | `kb.py add-batch` refuses `\r` |  |
| All 298 sources self-tiered 1, vendor docs and npm included | spec | Lead at stage 0 | `primary_hosts` allowlist |  |
| Bare-root URLs (a site's home page) cannot support a fact | spec | lead | `add-source` refuses a bare root without `--allow-root REASON` |  |
| 870 of 2,622 numeric prose lines had no cite | accuracy | page author | `check_pages.py` counts; `[calc]` tag for derived values |  |
| arXiv / Reddit 429 on fast fetch; ISO pages 403 | environmental | script | `fetch.py` spacing + backoff + status row; paywalled = "not confirmed" |  |
| Lead challenged a file that existed (`ls` output truncated) | lead-defect | Lead | `test -f` before a challenge |  |
| Mermaid left unrendered (`mmdc` missing) → rebuild | tooling | builder | `selftest.py` checks `mmdc` at stage 0 |  |
| 0 bookmarks in 384 / 389-page PDFs; TOC without page numbers | spec | builder | navigation floor in `check_report.py` |  |
| Fonts gate banned only Cairo/Arial; a Times fallback would pass | spec | builder | every `pdffonts` row must be Thmanyah | pdf/glyph-gap (safe), tounicode, rtl-title (advise) |
| Core page: 4,882 words, 5 questions; mock target 30 of 40 with a 5-question bank | teaching | page author | objectives + bank + `check_teach.py --path` |  |
| Answer keys directly under their questions | teaching | page author | key-distance check |  |
| "not confirmed" vs «غير مؤكد» counts differed on 5 pages | twin | reviser | wider `--pair` |  |
| Translation leads "partly read" helper pages | review depth | Lead | mechanical pair gate is the floor; report says semantic fidelity not verified |  |
| `grep` with an Arabic class matches nothing in Git Bash | environmental | — | Arabic checks in Python only |  |
| The skill's own v0 quoted two wrong figures (163, 546) | accuracy | skill author | every number in this skill is a DB query result with its date |  |
| v1 put the audit after the report that prints it | spec | skill author | audit is stage 2b; report refuses without it |  |
| r3: `--second-source` attached an unrelated source before the quote check; a 1-word quote verified | accuracy | script | raw bound to stored sources; quote ≥ 40 chars with the claim's numbers in order |  |
| r3: a hand-edited `audit/sample.md` passed (rows deleted, padded) | accuracy | script | audit recounted from the DB against the drawn ids and sha |  |
| r3: report printed PASS with checks skipped | spec | script | SKIP exits 3 |  |
| r3: `{#id}` anchors printed as braces (pandoc gfm) and banks printed as one bullet | publishing | script | `gfm+attributes`; banks rendered from the parser |  |
| r3: the template's own bank example failed the checker | spec | skill author | selftest round-trips the template's bank fence |  |
| r3: plan's wave count wrong at other slot counts; 12 → 13 items jumped 1 → 16 workers | orchestration | script | monotone plan, one-wave alternative first |  |
| CTFL rehearsal: 9 of 26 entries needed `derived` because the claim carried "v4.0" | accuracy | script | version token exempt when the source name carries it |  |
| CTFL rehearsal: count and absence claims cannot be quoted | spec | skill author | rule 9: counts are `[calc]`, absences are scripted searches |  |
| CTFL rehearsal: demoting #4 silently broke a rule citing it | accuracy | script | `kb.py demote` lists citing rules/pages, exit 2 |  |
| CTFL rehearsal: audit sampled 0 bank questions (banks written after it) | spec | skill author | separate bank audit, stage 3c |  |
| CTFL rehearsal: exam-table PDF columns interleaved under `pdftotext -layout` | tooling | script | `fetch.py --no-layout` writes both texts |  |
| QA book: 22 of 24 banks answerable from the options alone (60–100 %, chance 25 %) though every length gate passed | teaching | page author | `probe_bank.py` stage 3d; rewrite keyed items, two rounds max, ship the rest flagged on the Method page |  |
| A misdirected verify-batch silently revived 5 retracted entries | accuracy | script | `kb.py verify` refuses a retracted entry |  |
| A lead re-ran its verifier's rows itself under the verifier's name (alias) | accuracy | Lead | independent Haiku re-verify of every row it touched; 2 of 77 demoted |  |
| Bank audit r1 1/92, r2 3/92 misses — every key right (184/184), but the basis named the topic, not the deciding fact; the second failure stopped the book before the PDF | traceability | bank author | page-template §4: basis carries the fact that picks the key; authors write the basis first, then the item | bank-basis (advise) |
| Chapter-summary entries (title + minutes + LO titles) cited on 322 body sentences they do not carry | traceability | page author | cite only an entry whose claim carries the sentence; explanation without a number needs no cite |  |
| v1's quote check accepted a quote from any downloaded file | accuracy | script | `_raw/index.tsv` binds raw file to the entry's own source URL + sha |  |
| Renderer silently ignored `outline` | tooling | pdf-typography | `renderPdf({outline})` patched 2026-10-16, toy PDF toc = 3 entries |  |
| Phase A (2026-10-16): two helper scripts held a sqlite write transaction open while spawning `kb.py`, deadlocking `qa.db` for every group ~40 min | tooling | lead | only `kb.py` writes; reads via `mode=ro` closed before any write; find a stuck holder by the `qa.db-journal` handle, not by guessing |  |
| QA book, final build: Thmanyah glyph gaps (U+201F, arrows, relations) fell back to Times; Arabic PDF ToUnicode broken; RTL title unmatched in `build_report.locate_pages` | tooling | builder | `check_report.py` glyphs gate; hand repairs | pdf/glyph-gap (safe), tounicode, rtl-title (advise) |
| QA book: verifier "weak" (entry 2076) | accuracy | author | claim narrowed or retracted, replaced by 2077 | entries/verifier-weak (advise) |
