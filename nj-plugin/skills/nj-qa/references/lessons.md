# NJ-QA lessons from earlier runs

Leaders read this before planning. Each line came from a real wall. The director adds the run's lessons here at close-out, and keeps only those that apply beyond one service.

- **Phone fields (2026-11-09):** A custom phone-input component held the country dropdown's search box before the real box in the DOM. Type into `input[type="tel"]` and read the value back. Fixed in `lib/journey.ts` (`mainBox`) and `lib/addtable.ts`.
- **Read back every value (2026-11-09):** a value typed into the wrong box raises no error until «إرسال» refuses it. Read the field after typing, so the wall shows up where it happened.

## From the first run (2026-11-09, PROJ-5494 and PROJ-4285)

**Getting through the portal**
- **Filing data:** before sending a tester to file a service, ask whether the data can reach send. Test-sheet licences go stale, and the back office's read-only licence inquiries show what is valid. A licence must belong to the applicant's institute.
- **Disabled radios:** a disabled radio hides a branch, and the signed-in account can decide which request type is enabled. Confirm that a type was really selected before saying a field is absent.
- **Revealed controls:** before reporting that no path leads somewhere, read every control a decision reveals.
- **Reopened lists:** a searchable list keeps its last filter text, so «لا يوجد نتائج» may be our own doing. Clear the filter first.
- **Toasts:** a helper that waits for the screen to close misses the toast. Read refusals at once.

**«التوقيع الرقمي»**
- A spinner is not the OTP screen. Read what opened before asking the owner for anything, and ask only when the OTP box is on screen.
- Judge the result from the «المخرج» row, not from a text diff, and never press it twice on a ticket.

**Evidence**
- A letter's shot must show the letter itself, not the desk behind it.
- Name accounts by sheet row in reports and walls, never by number.

**Running as an agent**
- **Don't end on a background job:** never end your turn on a background watcher, because the leader sees you as finished and the report never comes. Wait in the foreground with `timeout`.
- **The Bash limit:** a command over 180 seconds moves to the background even with a longer timeout. Run shorter steps.
- **CDP ports:** never hard-code one. A tester attached to another tester's Chrome this way. Use `freshWindow`.
- **Suite hooks:** a suite hook's throw is swallowed and «إرسال» is still pressed, so to stop before sending, use the fill step and decide.
- **Read-only workers:** stop as soon as `tracker-live.md` says no ticket was filed, rather than waiting out the deadline.
- **Evidence names are Arabic, `<المشكلة>-<الخدمة>-<التاريخ>-<الوقت>` (owner, 2026-11-09):** issue, service, `YYYY-MM-DD`, `HH.MM` in 24 hours, ≤150 characters, `-2` for a repeat in the same minute. Generate it with `evidence_name.py` / `evidenceName()`, never by hand; `report-check` and `preview-check` refuse anything else. Forward only: existing files keep their names.
