| date | run-id | agent | runtime | tier | effort | task-class | role | stage | cached-in | uncached-in | output | reasoning | model-calls | tool-calls | workers | retries | duration-min | exec-status | verify-status | final-status | defects | escalations | cost | basis | rework | note | estimate-min |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
<!-- Measurement schema revised 2026-09-16 (nj-agent-ops SKILL.md section 5).
     Rows before that date carry only the first 8 legacy cells
     (date, run-id, agent, runtime[was model], stage, status, tool calls, rework)
     and are read positionally against THAT header, not this one.
     An empty cell means NOT MEASURED. 'basis' says whether cost/token cells
     are actual or estimated; the two are never mixed in one row. -->
| 2026-09-14 | env-2026-09-14 | standard | opus | standard | ok | - | n |
| 2026-09-14 | env-2026-09-14 | delevary | sonnet | delevary | ok | - | n |
| 2026-09-14 | env-2026-09-14 | docx | opus | docx | ok | - | n |
| 2026-09-14 | env-2026-09-14 | readiness | sonnet | readiness | ok | - | n |
| 2026-09-14 | env-2026-09-14 | rules | sonnet | rules | ok | - | n |
| 2026-09-14 | docx-fix-2026-09-14 | docx-layout | opus | docx-layout | partial | 147 | y |
| 2026-09-14 | docx-fix-2026-09-14 | opus-cap | haiku | opus-cap | ok | 11 | n |
| 2026-09-19 | PROJ-manual-089 | worker | sonnet | economy |  | manual-fix | worker | title+rebuild |  |  |  |  |  |  | 0 | 0 | ~20 | ok | not-verified | delivered | unfiltered-list(accepted) | 0 |  | estimated | n | trade-product-license-after-classification: set flow.title.ar + document.serviceName, rebuilt AR/EN, gated, delivered |  |
| 2026-09-19 | PROJ-manual-090 | worker | sonnet | economy |  | manual-fix | worker | rebuild+redeliver |  |  |  |  |  |  | 0 | 0 | ~15 | ok | verified | delivered | unfiltered-list(accepted) | 0 |  | estimated | n | PROJ-trust-mark: source title already correct, but delivered PDF/MP4 predated pdf.ts serviceName read and reannotate.ts mask fixes; rebuilt AR/EN (--reuse-recording --overwrite), gates 19/19, delivered, confirmed via pdftotext on delivered cover |  |
| 2026-09-14 | v4-rollout-b1 | interpreter | haiku | interpret | ok | 2 | n |
| 2026-09-14 | v4-rollout-b1 | docx-fix | sonnet | docx-fix | partial | 53 | y |
| 2026-09-14 | v4-rollout-b1 | pilot | sonnet | pilot | ok | 70 | n |
| 2026-09-14 | v4-rollout-b2 | build-a | sonnet | build | partial | 33 | y |
| 2026-09-14 | v4-rollout-b2 | build-b | sonnet | build | partial | 40 | y |
| 2026-09-14 | v4-rollout-b2 | build-c | sonnet | build | partial | 31 | y |
| 2026-09-14 | v4-rollout-b2 | build-d | sonnet | build | partial | 38 | y |
| 2026-09-14 | v4-rollout-b3 | page-breaks | opus | page-breaks | ok | 103 | n |
| 2026-09-14 | v4-rollout-b3 | deliver-registry | sonnet | deliver-registry | ok | 17 | n |
| 2026-09-14 | v4-rollout-b3 | card-conflicts | sonnet | card-conflicts | partial | 18 | y |
| 2026-09-14 | v4-rollout-b3 | verify-fixes | sonnet | verify-fixes | partial | 54 | y |
| 2026-09-14 | v4-rollout-b3 | docx-pages | sonnet | docx-pages | partial | 61 | y |
| 2026-09-14 | v4-rollout-b4 | card-check | sonnet | card-check | ok | 57 | n |
| 2026-09-14 | v4-rollout-b4 | invoice-rows | sonnet | invoice-rows | ok | 102 | n |
| 2026-09-14 | v4-rollout-b4 | docx-anchor | sonnet | docx-anchor | ok | 27 | n |
