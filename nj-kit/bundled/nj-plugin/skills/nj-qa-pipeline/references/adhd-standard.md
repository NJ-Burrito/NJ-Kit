# ADHD-friendly output standard (owner, 2026-10-11)

Applies to EVERYTHING the QA skills produce: reports, PDFs, HTML pages, terminal output, AGENT.md / AI-RUN-NOTES.md, Jira comments, and worker receipts.

| Rule | In practice |
|---|---|
| Verdict first | one status line + count chips at the very top: `3 ❌ · 5 ✅ · 2 محجوب`; red items first |
| One idea per card | short headings, paragraphs <= 2 lines, bullets not prose, bold only the key words |
| State = colour + icon + word | ✅ passed · ❌ failed · ⚠ warning · ➖ skipped · ⛔ blocked · 🏁 reached the end; never colour alone |
| Detail collapsed | evidence, logs, network excerpts inside closed `<details>`; one picture per claim |
| Next step per item | a «الخطوة التالية» line on every card / row: the exact command or the person to ask |
| Navigation | sticky mini TOC (or progress bar) on long HTML; section tabs + page numbers in PDF |
| Layout | generous spacing, line length <= ~70ch, no table wider than the page, plain words over jargon |
| Time | durations HH:MM:SS (HH:MM in summaries) |
| Language | match the deliverable (Arabic RTL for the portal's reports); bilingual pairs change together |

## Worker receipt (<= 25 lines)
STATUS / FINDING (counts) / EVIDENCE (paths) / FILES-SYMBOLS / RISK / NEXT ACTION · `delegations: n` (the helper count, from the spawn log). Everything else goes to the detail file.

## Jira comments
Arabic, one verdict line first (`تم التحقق على staging بتاريخ …` or `ما زال غير منعكس`), steps in a short numbered list, expected vs actual in two lines, screenshot attached.

## Check before saying done
Open the page / PDF page 1 and read only the first screen: can you tell the verdict, the count and the first thing to fix without scrolling?
