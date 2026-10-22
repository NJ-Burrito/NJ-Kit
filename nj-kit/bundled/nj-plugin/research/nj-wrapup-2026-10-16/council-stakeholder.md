# Council vote: nj-wrapup v2 — POV: boss reading on a phone + QA team printing (Arabic-first, Jordan)

Read: proposals.md, devil.md, research.md (grep), trial-1/2/3, SKILL.md, email-template.md, the real AR/EN boss emails (PROJ-1234) and the QA message.

What I saw in the real artefacts (basis for the votes):
- Boss email carries internal detail: the raw endpoint «GET /services/general/sanad-auth/callback/sign_auth → 500», the error string «SIGN_HERE not found in PDF», two staging request serials, an assignee's personal name, a «What I did» block of 7 lines before the first red item. Numbers are right but only reconcilable by the reader: subject says "10 Bugs + 6 Tasks", chips say "16 new tickets", the table says "9 new bugs" (the 10th is the blocker, shown elsewhere).
- Trial-2: 8 of 16 filed items later became Not Bug, and the email had already told the boss. That is the worst trust failure in the set.
- QA message: good scan shape (file, stage, number, ❌/➖/✅/ℹ️). Gaps: header says «جاهزة للطباعة» while file 1 has a known defect (date «---»); no "what you do now / until when"; the test username <staging-user> is named; trial-2 shows the skill would send defective or other-session outputs "for printing".

| P# | Vote | One-line reason | Amended text (if AMEND) |
|---|---|---|---|
| P1 | APPROVE | Double filing or double registration produces two emails with two different numbers. | |
| P2 | AMEND | Router must also pick the message shape, otherwise a non-testing or zero-defect session still gets the full test email. | Add a column "Messages": notes-test = boss email AR+EN + QA message (only if outputs exist); re-check = short «نتيجة إعادة الفحص» (closed N / reopened M); multi-service = verdict + table by service + «ما يلزم»; non-testing = short «شغل منجز» only if someone outside asked; zero-defect = 3 lines, no QA message. |
| P3 | APPROVE | Cost rule only; nothing outward changes. Keep P10 mandatory at every size so a Lead-direct filing is still read back. | |
| P4 | AMEND | Fine, but the message templates are the part people read, so they must move to the profile with their wording rules, not stay generic English. | Core keeps only "outward message = generated from trace.md". `profile-PROJ.md` owns: AR template, EN template, QA-message template, deny-list (see N-stake-1), sign-off, who sends (owner, never us). |
| P5 | APPROVE | Strongest item for trust: 8 of 16 became Not Bug after the boss was told. Add the pre-classify result to the email only as "n checked against design before filing". | |
| P6 | AMEND | Right, but the outward effect is missing: held rows must not appear in the email as filed or as failed. | After "ONE AskUserQuestion batch", held rows are shown in the email as «بانتظار قرار» (count only, no key) until decided; the email is generated only after the batch is answered or the rows are explicitly dropped. |
| P7 | AMEND | the owner's verdict wins, but the email must follow the final filed class, never the disputed one. | Add: "The email and QA message state the final class only. A verdict-vs-design conflict is shown to the owner, never to the boss." |
| P8 | AMEND | Grouping is good for the reader (one defect, not four), but the headline count must say which unit it counts. | Add: email counts = distinct defects, plus one line «يؤثر على n خدمة». The subject never mixes units: write "n defects (m tickets)" or one unit only. |
| P9 | APPROVE | Fixes the real fault: three different numbers (10 / 9 / 16) in one email. Make it hard: the email cannot be rendered without trace.md. | Add two assertions: AR count == EN count; every number in the subject appears in the body with the same meaning. Stamp «حتى HH:MM». |
| P10 | APPROVE | Keys the boss clicks must exist, be the right type and assigned. Self-reports are not evidence. | |
| P11 | AMEND | Right as classification; the boss needs these as asks, not as a silent "open". | Blocked-by-data/environment rows go to «ما يلزم» as: what is missing, who provides it, by when (or «الموعد: لم يُحدَّد»). One plain line each; the exact error stays in the Jira/ session file, not the email. |
| P12 | APPROVE | One wording everywhere avoids the boss reading "signing failed" as a defect when it was an environment fault. | |
| P13 | APPROVE | Stops Tasks that no developer can act on; the boss sees fewer, truer "Tasks for the developer". Email shows "بانتظار شرط" as its own short line. | |
| P14 | APPROVE | A re-check session's whole result is closed/reopened counts; the email needs that shape. | |
| P15 | APPROVE | Internal learning loop, no outward risk, reduces future Not-Bug embarrassment. | |
| P16 | APPROVE | `close-mine` would mark developer Tasks Done while the boss email lists them open: a visible contradiction. | |
| P17 | AMEND | Fields yes; the email must not use tracker jargon. | Email says «الأولوية: عالية / متوسطة / منخفضة» (one term), never "severity"/"priority" pairs, never the field names. |
| P18 | AMEND | Neutral body wording protects the dev relationship, but the boss needs the one fact that matters: it came back. | Jira title/body neutral as proposed. Email may state the fact without blame: «عاد بعد إغلاق PROJ-xxxx». No «رغم». |
| P19 | AMEND | Direction right (summary first, exit statement, «ما يلزم» last), but not enough for a phone reader and it leaves the leak rules vague. | (1) First 6 lines = the whole message: verdict, counts, blocker (or «لا عائق»), «جاهز / غير جاهز لـ… لأن…», what I need from you. (2) Everything else collapsed under one-line headings, red before green. (3) Cap: 35 lines per language. (4) Write both to Desktop `.txt` and paste in chat (checkpoint rule), paths only in the reply to the owner, never in the email. (5) Deny-list gate per N-stake-1. (6) «ما يلزم» is last and uses N-stake-3. (7) "What I did" max 3 lines, below the findings. |
| P20 | AMEND | Fine for the session; the open-requests table is for the owner and the QA team, not the boss. | Open staging requests (serials, desk) go in the close report to the owner and, if useful, the QA message. The boss email says only «طلبات اختبار مفتوحة على Staging: n» with no serials. |
| P21 | APPROVE | Hand-typed header counts were wrong; delete them. | |
| P22 | APPROVE | Preview before filing is a gate for people who read it; do not override it from a skill. | |

Tally: APPROVE 13 · AMEND 9 · REJECT 0.

## New proposals

**N-stake-1 Outward deny-list gate (script).** Before the boss email or QA message is accepted, a check fails on: any URL or API path, HTTP status plus error body (one plain-language line is allowed), request serials in the boss email, staff or assignee personal names (use team names), test usernames or logins (<staging-user>), the words "Not Bug risk", "conflict", "inferred", any file path, any token-looking string; and asserts AR/EN count parity and that every key cited was GET-verified at send time. Test: run it on the real 10-15 boss email (expected to fail on endpoint, error string, two serials, a personal name) and on the QA message (expected to fail on <staging-user>).

**N-stake-2 QA message prints only the right document.** Each file gets one verdict word: «اطبع» / «اطبع مع العلم بالخلل: …» / «لا تطبع (مسودة / معاينة)». Only final-stage outputs of requests this session itself filed are eligible; drafts, watermarked previews and anything from another session's or a defective signed request are listed as «للمعلومة، لا تُطبع» or omitted. The header may say «جاهز للطباعة» only if at least one file is «اطبع». Add a last block «ما المطلوب منكم الآن» (print file n; nothing else until PROJ-xxxx is fixed; what will follow and when it will be sent).

**N-stake-3 «ما يلزم» = owner + action + date.** Maximum 5 lines, each «مَن: ماذا — الموعد». The Lead never invents a date: use the one the owner gave, or «الموعد: لم يُحدَّد — أحتاج تحديده». Anything with no owner is a defect of the message, not a footer line. In the AR and EN versions the owners and dates are identical.

## The one thing that must not ship

An outward message (boss email or QA message) written before reconcile (P9) and the Lead's read-back (P10) have passed and before held risky rows (P6) are answered. Shipping the v2 gates without that ordering rule lets the same session tell the boss numbers that Jira later contradicts, which already happened (8 of 16 turned Not Bug; counts 10 / 9 / 16 in one email). If only one thing is built, build "email cannot render without a passing trace.md".
