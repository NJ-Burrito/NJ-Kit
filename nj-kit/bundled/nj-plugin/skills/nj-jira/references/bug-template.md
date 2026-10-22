# Bug template (wiki markup) - THE canonical method

Source layout: **PROJ-1234** (filed 2026-10-19, the latest Bug; the owner: "it's good and ADHD friendly"). Read-only reference; never edit that ticket.

Summary: `«<service card title>: <the defect in one line>»`
Label: `phase2-uat` - the current SDLC stage label, the same on every Bug/Task of every service (owner, 2026-10-19). Lives in ONE place: `nj-jira/SKILL.md` § Jira stage label. It is a Jira field, never a body line. Add, never replace.

Description = ONLY these five blocks, in this order, each <= 3 short lines (short, not over-detailed; the owner 2026-10-20). Where/location goes inside المشكلة in one line.

```
h3. ❌ المشكلة
* <what happens, and where: portal/back office -> page/tab -> request NUMBER>

h3. 🔁 الخطوات
# <step 1, one line>
# <step 2>

h3. ✅ المتوقع
* <what the screen must do> (quote «verbatim line» + KEY - date - author when the expectation is quoted)

h3. ❌ الفعلي
* <what the screen does now, copied exactly, banner text in «»>

h3. 🖼️ الدليل
* {{evidence/<what-it-shows>.png}} (a few words)
```

Rules for the body: NO Priority / Severity / Labels / Assignee / Related / Environment lines, no «Related» and no «Severity / priority» section (PROJ-1234 carried them; that is retired - they are Jira fields and links only). Evidence unmasked (Jira evidence is never masked). No credentials, national IDs, tokens or real personal data in the template or the ticket text: placeholders only. A failed call may appear as `{{code}}` (no tokens or cookies). NO `*Verdict:*` line and NO `*Source:*` line, and no [JIRA]/[ASSUMED] label, in any ticket (Bug or Task, draft or filed; the owner 2026-10-20) - those labels live in QA analyses/reports only; nj-rank's `refuse_verdict_source` refuses such a body. DROPPED / NO SYSTEM CHANGE notes: put the quote `<KEY> - <comment id> - <author> - <date>: «<verbatim Arabic line>»` in «Expected» / «Actual».

## ADHD-friendly shape (owner, 2026-10-18/19)
- Start with the labelled blocks above (no Verdict line). Numbered steps, bullets, no paragraphs.
- Evidence files are named by what they show (`<note-id>-<what-it-shows>.png`), never `screenshot1.png`.

## Description holds none of the metadata (owner, 2026-10-19)
The Bug DESCRIPTION never contains Priority, Severity, Labels, Assignee, related/linked tickets, Environment/build lines, nor a «Related» or «Severity / priority» section. They are set only as Jira fields and links (Environment field, Relates link, labels). Lineage and "not a duplicate" reasoning go to the Relates link and the filing log, not the body. Fields are still set on every Bug.

## Fields
- Type Bug; assignee = the developer the owner names (integration/infrastructure faults — Sanad, payment gateway, 5xx not tied to a form — go to the operations owner instead); estimate 2h/2h; reporter = the owner's account (the API session).
- «Relates» to the service Story (the Story whose title is the service). If no Story carries the exact name, link the nearest sibling Story and say so in the filing log.
- Severity (impact) and Priority (urgency) are set explicitly on every Bug, never left to the default by accident. Set only fields the Jira project really has (read the create-meta first); if there is no Severity field, record it in the filing log (never in the description). The table gives defaults; the Lead may deviate with a reason in the filing log:

| Case | Severity | Priority |
|---|---|---|
| Process blocker: the request cannot proceed past a step (reproducible 5xx with an error body, e.g. signing failure) | Blocker | High |
| Missing branch, option or route (wrong behaviour, a workaround exists) | Major | Medium |
| Label, wording, order | Minor | Low–Medium (Low for pure order/spacing; Medium for a wrong label the user acts on) |
| Anything else / unsure | Major | Medium (default) |

  High is for true blockers only: priority inflation makes developers ignore it.
- Lineage (earlier key, its Done date, what it changed) goes in the «Relates» link and the filing log, neutral wording, never blaming («رغم إغلاق», «لم يُصلح»); not in the description.
- Cite the ticket + date + author the expectation comes from inside «Expected» (the quoted line), never as a *Source:* line.

## Evidence rules (the owner's method, approved 2026-10-18; use for every Bug and Task)
1. Viewport screenshots only (never fullPage); the target is scrolled into view and asserted inside the viewport.
2. A red ring (injected CSS outline, removed after) on the exact point. PDF letters: `pdftoppm` ~150 dpi, crop to the sentence, ring it.
3. Jira evidence is unmasked (the owner 2026-10-19); masking is for SRS / user / training manuals only.
4. One shot per fact (two if far apart).
5. File names say what they show: `01-send-refused-termination-date-required.png`.
6. Allowed evidence types are screenshots (.png .jpg .jpeg), videos (.mp4 .webm), .gif, .md and .pdf (official output letters), nothing else; .docx .txt .json .log are refused (owner, 2026-10-19). `.txt` / `.json` / `.log` / API-text excerpts are not evidence and the uploader refuses them: page text may be saved locally for findings, never put on a ticket. A failed call may appear in the description as `{{code}}` (no tokens or cookies).
7. The «🖼️ Evidence» block lists every shot by name. Also keep `issue-KEY.png` (the filed ticket) for the tracker.
Tools: `scripts/evidence-shot.ts` (`evidenceShot`: scroll, mask, ring, assert, shoot, unring) and `scripts/ring-pdf.py` (PDF page -> ringed crop).

## Filing log row
`| source note | new key | url | story (Relates) | assignee | attachments |` appended to `filed.md`; one `drafts.md` per round keeps the text you filed.
