# Run outputs, notes and PDFs (skill reference)

| Output | Made by | Content standard |
|---|---|---|
| terminal | `reporter/index.ts` | one line per stage: ✅ passed ❌ failed ⚠ warning ➖ skipped, with a plain reason; REAL request count printed BEFORE a filing run |
| `reports/index.html` | reporter | verdict + chips on top, red first, grouped directorate > service > request > stage, latest result per request kept (a single test never erases others), sticky TOC, collapsed evidence |
| `reports/jira/<service>.html` | reporter after a run | per note: title, what the check does, latest verdict + time, the copyable one-note command; opens by itself (env `NO_OPEN` stops it) |
| `reports/AI-RUN-NOTES.md` | reporter | TL;DR block first (verdict RED/GREEN, counts, "fix first", next step), what ran, failures with suggested class + evidence paths + re-run command, how to read artefacts, triage-class table |
| `services/*/AGENT.md` | `tools/gen-agent-md.ts` | per-service facts for the next agent |
| run-report PDF | `tools/run-report/build.ts --run <run> --title "<t>" --out <name>.pdf [--note "<scope>"]` | reads `services/*/*/<run>/latest-ticket.json`; verdict first, cards, red first, «الخطوة التالية» per card, «الأدلة» block, tab strip per service, page numbers |
| gates | `tools/run-report/gates.ts --run <run> --out <name>.pdf` | (a) every note id in PDF text (b) only Thmanyah, TrueType, no Type 3 (c) Arabic extracts with poppler |
| guide PDF | `tools/build-guide.ts` | the Arabic setup/run guide in `docs/` |

## Triage classes (a failure gets exactly one)
`TEST` fix in the service folder · `PORTAL-KNOWN` already in README-service · `PORTAL-NEW` add with key + evidence (and file a Bug: `nj-jira`) · `LIB` write `lib-defect-<n>.md`, do not edit lib from a service worker · `STAGING` environment (502/503, payment off-network).

## PDF font rules
- Thmanyah Serif Text (body) + Serif Display (headings), TrueType cuts (Chrome emits Type 3 for CFF/OTF and then no font name is visible to the gate). Cairo banned.
- Fonts from `<P>_FONTS_DIR` (default `assets/fonts/thmanyah`); the strict bundled-fonts selftest runs on the host and is skipped in the container when the variable is unset.
- Extract with poppler `pdftotext -enc UTF-8` (never pymupdf/pdfium for Arabic).
- Section tabs + page numbers in the PDF; no table wider than the page.

## ADHD checklist (apply to each output)
verdict line + chips first · red first · one idea per card · <= 2-line paragraphs · icon + word + colour per state · evidence collapsed · next step per item · sticky TOC · HH:MM:SS durations.
