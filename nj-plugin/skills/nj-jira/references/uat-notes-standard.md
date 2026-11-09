# UAT notes -> Jira: the standard (owner, 2026-10-22)

The default for every client "UAT notes" email batch. A reference run keeps its Tasks and Bugs listed in its own folder. Tools are in `nj-jira/scripts/`; credentials only via `~/.claude/secrets/jira.json`, never printed.

| Step | Tool |
|---|---|
| data file (services, notes, results, extra) | written by hand/agent; JSON or `.py` module, schema in `uat_preview.py` docstring |
| notes.md + preview.html + `bugs-<svc>.json` | `PYTHONUTF8=1 python scripts/uat_preview.py DATA [--out DIR]` |
| Tasks before testing | `scripts/task.py create DATA --assignee <user> [--service S3] [--dry-run]` |
| Bugs | `scripts/file_bugs.py bugs-<svc>.json --task PROJ-N --assignee <user> [--dry-run]` |
| Task close-out | `scripts/task.py close DATA --service S3 --task PROJ-N --filed filed-bugs-S3.json [--dry-run]` |
| work log | `nj-rank register --existing-task PROJ-N --evidence preview.html notes.md ...` |

`--dry-run` prints payloads and never calls Jira. Re-run `uat_preview.py` after every results update; the preview is regenerated from the data file, never edited.

## 1. Intake: client notes email(s) -> notes list
- Every note gets an id: `G<n>` global (system level), `<svc>-<n>` per service, `GF` cross-service rule (e.g. routing fields, all factory services), `<svc>-R` rename, `<svc>-N<n>` new finding from testing.
- Ordered BY SCREEN, start to end: services page -> service card -> submit screen -> staff tasks screen -> back-office desks in Flowable order (`project-tests/reference/flowable`, `lookup.py`) -> output(s) -> request path. Screen headers are plain strings in the `notes` list.
- Global notes: placed once per service where they apply (service-page/tasks-screen globals under the first service only); a later email that updates an earlier note is MERGED into one note (`S3-6+11`), the newer wording wins.
- Each note: severity, priority, defect line, where, numbered steps, expected = verbatim quote + source email/date.
- Items waiting on the client (procedures, a letter image) are marked ⏳ with the request that asked for them.
- Notes for services outside the requested ones are left out (ask once).

## 2. Tasks up front
- One Task per service per work type, created BEFORE testing, status **In Progress**, label `phase2-uat`, assignee the owner, estimate 2h/2h (required on create).
- Summary `«<card title>»: اختبار ملاحظات UAT2`; body = PROJ-5169 layout: `🧪 اختبار ملاحظات UAT2` block (counts line only, no placeholder line) + `🐞 البلاغات` placeholder.

## 3. Preview (HTML): super ADHD-friendly, RTL
- **Dark mode, contrast >= 7:1, fonts +4: body 18px, nothing under 16px (the owner 2026-11-09, permanent for previews; overrides the -2 font rule here only).**
- `dir="rtl"`, Thmanyah Serif, everything right-aligned incl. code/pre; Arabic labels (no English severity words: 🔴 يوقف الطلب / 🟠 رئيسي / ⚪ بسيط).
- One TAB per service (remembers last tab); each tab: 3 big score boxes ❌ تحتاج بلاغ · ⏳ لم تُفحص · ✅ مُصلَحة; one 👉 next-step line.
- ⏳ section = a **4-column table**: # · 📍 الشاشة / المكتب · 📌 الملاحظة (المطلوب) · 🔍 ماذا تفحص بالضبط (numbered steps), in screen order.
- ❌ cards: id + severity pill + 📍 screen, big defect line, ✅ المطلوب / ❌ الموجود, screenshots (thumbs) and recordings (inline `<video>`), Jira text collapsed behind «📋 نص البلاغ للنسخ إلى Jira» with copy buttons.
- ✅ cards: expected + what was seen + shots. Passes inferred from the owner's screenshots are labelled «من صورك — أكّد».
- Task text collapsed at the bottom. notes.md regenerated from the same data.
- Also give the ⏳ list in chat as the same 4-column table.

## 4. Results intake (the owner's findings, per service)
- Map each finding to a note id; a finding that matches no note -> new note `<svc>-N<n>` (the `extra` block of the data file).
- Evidence: copy every shot/recording into `evidence/<svc>/` with a name saying what it shows (`05-submit-hajz-required.png`, `20-resubmit-refused-ighlaq-form-error.mp4`). Allowed: png/jpg/jpeg/mp4/webm/gif/md/pdf.
- Record each note's reference in the data file `refs` at intake (quote verbatim from the docx text, page from its PDF export); it flows into the Bug, the Task and the preview. Also quote the source line verbatim with email author + date + item number when he asks.

## 5. Bugs
- Title: `«<service name AS THE SYSTEM SHOWS IT NOW>»: <the defect actually found>`. **Re-title from the result before filing** (data-file `defect` text; `jira_name` per service = the current system name). The draft title is a guess; the filed one states what failed (lesson: PROJ-5186 / 5189 kept draft titles broader than the finding).
- Description: the 5 blocks of `bug-template.md` (no metadata lines, no Verdict/Source) + the LAST block `📄 المرجع` (document name, page · item, verbatim quote; new finding: session + evidence file + verbatim line). It is generated from the data file `refs` (`{note id: {doc, page, item, quote[, related]}}` / `{session, evidence, quote}`), `file_bugs.py` refuses a Bug without it.
- Fields: label `phase2-uat`, assignee asked each time, priority set (Blocker => Critical), severity in the filing log (the project has no severity field), estimate 2h/2h, attachments = evidence, «Relates» -> the service Task.
- Payload = `bugs-<svc>.json` exported by the generator; the filer reads it, never retypes. Duplicate JQL check first. Verify each Bug by GET (summary, label, assignee, link, attachment count); the filer writes `filed-bugs-<svc>.json` and `filing-log-<svc>.md`.
- Jira create-meta returns 404 on this server: required fields are read from the 400 response (the filer prints it).

## 6. Close-out
- Task: first block line -> counts `«<N> بنداً: ❌ x (y ملاحظات + z جديدة) · ✅ w»`, then under 🧪 EVERY note (NL-1.. then -N): icon ✅/❌/⏳/🆕, id, short title, `ص<n> · <item>`, Bug key where one exists, and the verbatim quote in `{quote}` (new finding: session line) - `task.py close` builds it from `refs`; `🐞 البلاغات` -> one line per Bug `* PROJ-XXXX — <defect>`; transition to **Done** (`task.py close`).
- nj-rank: register the item against the EXISTING Task (`--existing-task`, never a second Task), evidence = preview.html + notes.md + evidence/<svc>, archive `evidence.7z`. `.html` is kept and archived, never uploaded to Jira. The nj-rank preview gate stays.
- Message to send (in chat, Arabic RTL; only the five items of memory `send-message-five-items`), canonical layout (the owner 2026-10-22), tickets one per line sorted Critical -> Low as `KEY · Priority | Severity`:

```
- **الخدمة:** «<الاسم الجديد للخدمة>»
- **مُسنَد من:** <من> (<المصدر، مثل ملاحظات جلسة قبول المستخدم الثانية UAT2>)
- **النتيجة:** <N> بنداً فُحصت
  - ✅ <n> مُصلَحة
  - ❌ <n> غير مُصلَحة
  - 🆕 <n> ملاحظات جديدة
- **الوسم:** phase2-uat
- **التذاكر:**
  - PROJ-XXXX · Critical | Blocker
  - PROJ-XXXX · Medium | Major
```
(Show it in the chat as plain RTL bullets, not in a code block.)
