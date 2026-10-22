# nj-wrapup TRIAL 1 — dry run on PROJ-1234 (2026-10-15)

Skill under test: `skills/nj-wrapup/SKILL.md` + `references/email-template.md` (mtime 2026-10-16 00:18, i.e. written AFTER the session it is tested on).
Method: followed the skill literally from §1; ground truth read from `jira/filed-L1..L4.{md,json}`, Jira GET (read-only, 24 issues), `tracker.json`, `logic/results.md`, `portal|backoffice/results.md`, the QA message, the two boss-email HTML files, nj-rank items PROJ-1234..5108. Nothing written outside this folder. Delegations: 0 (the reading was ten small files; a Haiku batch would have cost more than it saved).

## Verdict
The skill reproduces the delivered result almost exactly: same 27-note classification, same 16 new tickets + 3 existing, same 4 filing lanes, same 6 nj-rank items. Its weak points are (1) the cases where the owner's decision and the design check disagree, (2) partial notes, (3) one wrong count, (4) mandatory helper/agent fan-out that this session did not need, (5) a closed-ticket title rule the delivered tickets do not follow.

## Step 1 — inputs
`tracker.json` holds the 27 rows. The skill asks for per-note columns "request serial, environment, date, design-check line"; the tracker has none of these as fields (serial is one global value, the design-check line sits in the `thread` text). The Lead would have to assemble them from threads. Partials were already resolved by the owner on 2026-10-15 22:39 (N1, N3, N4, N23, N24 -> fixed; N15, N17, N18, N22 -> not-fixed), so the "resolve partials first" gate passes.

## Step 2 — the plan (`jira/plan.md`, never existed in the real session)
| Result | Notes | Action |
|---|---|---|
| fixed (10) | N1 N2 N3 N4 N6 N14 N23 N24 N25 N27 | nothing; numbers in email |
| not-fixed, open ticket covers it (3) | N5 -> PROJ-1234 · N8 -> PROJ-1234 · N13 -> PROJ-1234 (BA) | existing, cite, do not file |
| not-fixed, nothing open covers it (8) | N30, N10, N12, N15, N16, N17, N18, N22 | new Bug each |
| of those, covering ticket Done but defect present | N17 + N22 (PROJ-1234 Done), blocker (PROJ-1234/3523 Done) | Bug titled «لم يُصلح رغم إغلاق <key>» (rule) — delivered tickets do not carry that title |
| untestable (6) | N7 N20 N21 N26 N28 N29 | one Task each, label `untestable` |
| process blocker (1) | signing 500 on 25202600116 | Bug High, network + console |
| output finding not in notes (1) | «الوارد بتاريخ ---» | pattern-check one other service, then Bug (= PROJ-1234; delivered did exactly this) |
Result: 10 Bugs (9 + blocker) + 6 Tasks = 16 new, 3 existing. Identical to ground truth. If the owner's *original* verdicts (N5, N8, N16 "put as untestable") were used instead of the post-logic-check ones, the skill would file 3 extra Tasks for notes that have an open Bug (N5, N8) or a new Bug (N16): double filing. The table does not say which verdict wins.

## Step 3 — lane split the skill would choose
Rule: disjoint lanes by screen/stage, 3-5 items, + one Tasks lane.
| Lane | Items | Delivered |
|---|---|---|
| L1 portal + output | N5 N8 N30 C | L1 (same) |
| L2 intake / distribution / not-cosmetic | N10 N12 N13 N15 N16 | L2 (same) |
| L3 committee-decision screen + blocker | N17 N18 N22 BLOCKER | L3 (same) |
| L4 Tasks | N7 N20 N21 N26 N28 N29 | L4 (same) |
4 Sonnet leads, each "must" brief Haiku helpers (delegations >= 1 required). Delivered: all four leads reported `delegations: 0`, finished in about 10 minutes (files 23:50-23:55). The mandatory helper clause is the only structural difference.

## Step 3 — drafts (titles; prefix «اجازة تداول مستحضر تجميلي/تجميلي صيدلاني: »)
Bugs: N30 عبارة «مهلة 3 أشهر…» غير موجودة في البطاقة وشاشات مقدم الطلب · C كتاب الموافقة يطبع «الوارد بتاريخ ---» · N10 شاشة «استلام الطلب» بلا حقل «اللجنة» الإجباري · N12 «توزيع اللجنة» لا يدعم الأعضاء الخارجيين · N15 «المتطلب البديل» يعرض «مستلزم طبي» بدل «مستلزم» · N16 لا مسار «عدم اعتباره» يرجع للمقدم والمؤقتات تلغي ولا ترفض · N17 خيار «تحويل إلى وحدة التصنيف الأولي» غير موجود — لم يُصلح رغم إغلاق PROJ-1234 · N18 لا أزرار/خيارات لتنفيذ «إرجاع» و«تحويل إلى وحدة تصنيف» · N22 تسمية الأزرار «التحويل الى رئيس القسم»/«نواقص» بدل «إرسال إلى رئيس القسم»/«استكمال نواقص» — لم يُصلح رغم إغلاق PROJ-1234 · BLOCKER (High) فشل التوقيع الرقمي «سند» 500 SIGNING_FAILED — لم يُصلح رغم إغلاق PROJ-1234.
Tasks: N7 14-day SMS · N20 قوالب «عدم اعتباره»/«التصنيف الأولي» · N21 «نواقص» + مهلة 3 أشهر · N26 CPNB عند رقم التشغيلة · N28 «وذلك بسبب» · N29 «كتاب المحلي — تصنيف أو مستلزم». (Task summary pattern is not defined by the skill; delivered used «ملاحظة n غير قابلة للفحص على Staging — …».)

### Example Bug (N17) — per bug-template.md
Summary: `اجازة تداول مستحضر تجميلي: خيار «تحويل إلى وحدة التصنيف الأولي» غير موجود في شاشة توصية اللجنة — لم يُصلح رغم إغلاق PROJ-1234`
Fields: Type Bug · Environment `Staging` · labels `env-staging` · assignee shahed.suleiman · estimate 2h/2h · Relates PROJ-1234 + PROJ-1234 (nearest Story, tell the owner).
```
h3. البيئة
* البيئة: Staging (${BACKOFFICE_URL})، الإصدار v0.2.0-149-stg، تاريخ الفحص 2026-10-15.
* الصفحة / الخطوة: المكتب الخلفي ← «توصية اللجنة». الحساب: موظف (<staging-user>)؛ الطلب من وكيل منشأة. الطلب 25202600114.
h3. خطوات إعادة الإنتاج
# تقديم طلب جديد ودفعه.
# تمريره: استلام الطلب ← الدفع ← توزيع اللجنة ← الاطلاع على الطلب (مرتين).
# فتح «توصية اللجنة» والنظر إلى «قرار اللجنة» وشريط الأزرار.
h3. النتيجة المتوقعة
المصدر (PROJ-1234 · 2026-06-02 · project Soft، البند 17): «في شاشة قرار اللجنة: … موافقة / رفض / عدم اعتباره مستحضراً تجميلياً / نواقص / تحويل إلى وحدة التصنيف الأولي.»
h3. النتيجة الفعلية (Staging، 2026-10-15)
خيارات «قرار اللجنة»: «موافقة» | «رفض» | «عدم اعتباره مستحضر تجميلي» فقط؛ «نواقص» زر وليس خياراً؛ لا يوجد «تحويل إلى وحدة التصنيف الأولي».
h3. قرار المختبِر
المالك (2026-10-15 22:39): «انها مشكلة لا توجد جميع الازرار».
h3. فحص التصميم
تقرير Flowable: بوابة COMMITTEE_RECOMMENDATION فيها APPROVE / COMPLETION_WITH_DEFICIENCIES / REJECT فقط.
h3. تذاكر مرتبطة
PROJ-1234 (Done، 2026-09-23) عالجت زر «عدم اعتباره» فقط — العيب قائم رغم إغلاقها. لا تذكرة مفتوحة تغطيه (JQL 2026-10-15).
h3. الأدلة المرفقة
* N17-committee-options-hl.png (مقصوصة، بلا بيانات شخصية) · N17-page-text.txt
----
اكتُشف أثناء التحقق من ملاحظات PROJ-1234 (البند 17)
```

### Example untestable Task (N21)
Summary: `اجازة تداول مستحضر تجميلي: ملاحظة 21 غير قابلة للفحص على Staging — رسالة «نواقص» ومهلة 3 أشهر` · first line «Environment: Staging» · labels `untestable`, `env-staging`.
```
(1) الملاحظة حرفياً — PROJ-1234 البند 21: «في قرار اللجنة: … وعند النواقص: عمل نواقص وإرفاق المطلوب وإرساله، ثم إعلام صاحب الطلب برسالة نصية تتضمن مهلة 3 أشهر تحت طائلة المساءلة القانونية وإلا يُلغى.»
(2) ما جُرّب — الطلب 25202600114، مكتب «توصية اللجنة»، 2026-10-15، Staging: ظهر زر «نواقص» وقائمة «النواقص المطلوبة»؛ لم يُضغط الزر حتى لا يُعاد الطلب لمقدمه.
(3) لماذا لا يمكن فحصها — رسالة SMS غير ظاهرة في الواجهة، ومهلة 3 أشهر لا يمكن انتظارها، والضغط يُنهي مسار الطلب الوحيد.
(4) فحص التصميم — BPMN: إجراء missings → addCompletePeriod → sendCustomMessage2 (SMS) → complete-by-applicant ومؤقت حدّي ينتهي بـ autoCancel(…,'complete_period'). تنبيه: المؤقت يقرأ ${document_delivery_period} (متغير مهلة الاستلام) بينما المستمع يسمّي complete_period.
(5) على المطوّر التحقق في الكود — addCompletePeriod يكتب قيمة 3 أشهر في المتغير الذي يقرؤه المؤقت؛ نص sendCustomMessage2 يحوي «تحت طائلة المساءلة القانونية».
(6) كيف يفحصها QA لاحقاً — بعد التأكد: ضغط «نواقص» على طلب جديد، قراءة SMS، ضبط المهلة لقيمة قصيرة في المتغير ومراقبة الإلغاء.
```

## Step 4-5 — register, outputs
Register: tracker replies (done in the real session, 📤 lines on every note) — ok. `npm run jira:add/jira:track`: `PROJ-tests/` has no `services/` folder and no `jira:add` script, and `PROJ-1234` is in no tickets file: delivered session did not run it; the skill does not say where the repo root with the script is, so the dry run cannot run it either.
Outputs: three PDFs under `Delivery\QA Outputs\مديرية الاجهزة الطبية و المستلزمات\اجازة تداول مستحضر تجميلي-تجميلي صيدلاني\` named by request serial 25202600114, plus `1- … 3-` on Desktop; QA message `.txt` with ❌/➖/✅/ℹ️ — the skill's description matches the delivered message line for line. Ambiguity: `<serial>` is the request serial in the folder, the document number (25202600023) in the message.

## Step 6 — nj-rank
Six items as the skill's example: portal (PROJ-1234) · back office (5104) · signature + outputs (5105) · design check + blocker (5106) · Jira upload (5107) · tool built, tracker.html (5108), all `service_ar` null. Exact match. Skill prescribes 1 Sonnet lead + 1 Haiku per item = 12 agents; delivered took ~2 minutes (23:55-23:57).

## Step 7 — boss email the skill would write (plain text, two code blocks)
**الموضوع:** نتائج فحص ملاحظات PROJ-1234 — اجازة تداول مستحضر تجميلي/تجميلي صيدلاني — 9 Bugs + 6 Tasks + عائق
```
مرحباً،

فحصت ملاحظات اختبار القبول لخدمة «اجازة تداول مستحضر تجميلي/تجميلي صيدلاني» — PROJ-1234 — على Staging بتاريخ 15-10-2026.

📊 النتيجة: 27 ملاحظة
✅ 10 مُصلحة · ❌ 11 لم تُصلح · ➖ 6 غير قابلة للفحص
📤 16 تذكرة جديدة في Jira · ⛔ 1 عائق

━━━━━━━━━━━━
⛔ العائق (أولوية High)
━━━━━━━━━━━━
PROJ-1234 — التوقيع الرقمي «سند» يفشل على الطلب 25202600116
الخطأ: 500 «SIGN_HERE not found in PDF» (نفسه في PROJ-1234 و3523 المغلقتين)
الأثر: لا موافقة نهائية؛ النصف الثاني من الملاحظة 4 لم يُفحص.

━━━━━━━━━━━━
❌ Bugs جديدة (9)
━━━━━━━━━━━━
• PROJ-1234 — م10: لا حقل «اللجنة» في الاستلام
• PROJ-1234 — م12: توزيع اللجنة بلا أعضاء خارجيين
• PROJ-1234 — م15: «مستلزم طبي» بدل «مستلزم»
• PROJ-1234 — م16: لا مسار «عدم اعتباره» والمؤقتات تلغي ولا ترفض
• PROJ-1234 — م17: «تحويل إلى وحدة التصنيف الأولي» مفقود
• PROJ-1234 — م18: لا أزرار لتنفيذ المهمة
• PROJ-1234 — م22: تسمية الأزرار
• PROJ-1234 — م30: عبارة «مهلة 3 أشهر» غير موجودة
• PROJ-1234 — مخرج: «الوارد بتاريخ ---»

❌ موجودة مسبقاً (لم تُكرَّر): PROJ-1234 (م5) · PROJ-1234 (م8) · PROJ-1234 (م13)

━━━━━━━━━━━━
➖ غير قابلة للفحص — Tasks للمطوّر (6)
━━━━━━━━━━━━
• PROJ-1234 — م7 · PROJ-1234 — م20 · PROJ-1234 — م21 (المؤقت يقرأ متغيراً آخر) · PROJ-1234 — م26 · PROJ-1234 — م28 · PROJ-1234 — م29
كل Task تشرح: لماذا لم تُفحص + ما يجب التحقق منه في الكود.

━━━━━━━━━━━━
✅ مُصلحة (10)
━━━━━━━━━━━━
1 · 2 · 3 · 4 (الإضافة التلقائية لم تُفحص) · 6 · 14 · 23 · 24 · 25 · 27

━━━━━━━━━━━━
📄 المخرجات
━━━━━━━━━━━━
كتاب الموافقة الموقّع 25202600023 + نسختا ما قبل التوقيع — أُرسلت لفريق QA للطباعة.

━━━━━━━━━━━━
👉 الخطوة التالية
━━━━━━━━━━━━
1. المطوّر: PROJ-1234 أولاً.
2. المطوّر: الـ9 Bugs ومراجعة الـ6 Tasks في الكود.
3. أنا: بعد إصلاح التوقيع أكمل الملاحظة 4 وأعيد فحص مسارات الرفض/عدم الاعتبار/التصنيف.

جميع التذاكر مُسندة إلى شهد سليمان ومربوطة بـ PROJ-1234 وPROJ-1234، ومع كل واحدة دليلها.
سجل العمل: PROJ-1234 → PROJ-1234

مع التحية،
المالك
```
**Subject (EN):** PROJ-1234 notes tested — Cosmetic / Cosmetic-Pharmaceutical Trading Licence — 9 Bugs + 6 Tasks + 1 blocker
```
Hi,

I tested the PROJ-1234 notes for «اجازة تداول مستحضر تجميلي/تجميلي صيدلاني» on Staging, 15 Oct 2026.

RESULT: 27 notes
✅ 10 fixed · ❌ 11 not fixed · ➖ 6 untestable
📤 16 new Jira tickets · ⛔ 1 blocker

⛔ BLOCKER (High)
PROJ-1234 — Sanad digital signature fails on 25202600116
Error: 500 "SIGN_HERE not found in PDF" (same as closed PROJ-1234 / 3523)
Impact: no final approval; second half of note 4 untested.

❌ NEW BUGS (9)
• PROJ-1234 n10 · 5094 n12 · 5095 n15 · 5096 n16 · 5089 n17 · 5090 n18 · 5091 n22 · 5087 n30 · 5088 output date «---»
❌ Already reported (not duplicated): PROJ-1234 (n5) · PROJ-1234 (n8) · PROJ-1234 (n13)

➖ UNTESTABLE — Tasks for the developer (6)
• PROJ-1234 n7 · 5098 n20 · 5099 n21 · 5100 n26 · 5101 n28 · 5102 n29
Each Task says why it was not tested + what to verify in code.

✅ FIXED (10): 1 · 2 · 3 · 4 (auto-add untested) · 6 · 14 · 23 · 24 · 25 · 27

📄 OUTPUTS: signed approval letter 25202600023 + 2 pre-signature copies — sent to QA for printing.

👉 NEXT
1. Developer: PROJ-1234 first.
2. Developer: the 9 Bugs; review the 6 Tasks in code.
3. Me: after the signing fix, finish note 4 and re-test reject / not-cosmetic / classification paths.

All tickets assigned to Shahed Suleiman, linked to PROJ-1234 and PROJ-1234, evidence attached.
Work log: PROJ-1234 -> PROJ-1234

Best regards,
the owner
```

## DIFF against ground truth
| Area | Skill would | Delivered | Diff |
|---|---|---|---|
| Classification | 10 fixed / 11 not-fixed (3 existing) / 6 untestable | same | match (if post-logic-check verdicts are used) |
| Tickets | 16 new + 3 existing | 16 + 3 | match |
| Lanes | 4 | 4 (L1-L4) | match |
| Helpers | >= 1 Haiku per lane, 1 per nj-rank item | 0 | skill adds ~16 agents |
| Closed-ticket title | «لم يُصلح رغم إغلاق <key>» on N17, N22, blocker | none of the 3 titles has it (reason is in the body) | skill stricter |
| Subject count | "9 Bugs + 6 Tasks + عائق" (my reading) | "10 Bugs + 6 Tasks + عائق" | delivered double-counts the blocker (9 + 1 = 10 Bugs); the skill's own header "10 Bugs + 6 Tasks + 1 blocker" repeats the double count |
| Email format | plain text in chat | two HTML files on Desktop | skill is deliberate change; no file copy saved |
| Email content | template blocks | adds "what I did", stat chips, open staging requests (25202600114/115/116) | template lacks these; skill puts the open-request list in the close report only |
| jira:add/track | run by Lead | not run, and not runnable in PROJ-tests | inapplicable as written |
| plan.md, review page | produced | neither exists | extra checkpoint (plan.md useful, review page wasted) |
| Task summary | undefined | «ملاحظة n غير قابلة للفحص…» | gap |
| Bug summary quotes | «<service>: <defect>» | 5087/5088/5093-5096 wrapped in « », 5089-5092 not | skill does not say which |

## Ambiguities (quotes)
1. "new **Bug** «لم يُصلح رغم إغلاق <key>»" — title or body? Conflicts with "Arabic summary «<service>: <defect>»".
2. "**the owner's comments on a note are binding** … Later design evidence that contradicts one is reported to him, never silently applied." vs table row "untestable | one Task per note": N5/N8/N16 were the owner-untestable and the design check flipped them. Report before or after filing? Which verdict is filed?
3. "process blocker (signing fails, …) | new Bug, priority High" vs the standing rule that «التوقيع الرقمي» is never a Bug/blocker and note N27's "inspect only". The delivered Bug rests on the owner's 2026-10-15 decision "a real signing failure is registered as a blocker"; the skill does not carry that condition.
4. "Partials are resolved by the owner's decision before filing" — nothing for a note that is half not-fixed, half untestable (N15 timer, N30 SMS, N4 auto-add, N16).
5. "10 Bugs + 6 Tasks + 1 blocker" (header) and template `<n> Bugs + <n> Tasks [+ عائق]` — is the blocker inside Bugs?
6. "`Delivery\QA Outputs\…\<serial>-<output name>.pdf`" — request serial or document number?
7. "`npm run jira:add … `" — which repo root; PROJ-tests has no such script.
8. "still build the review page for the record" — nj-jira §4b review page needs approved keys; unclear what is built.
9. "delegations ≥ 1 required" for every lane regardless of size.
10. §1 columns "request serial, environment, date, design-check line" are not tracker fields.

## Missing
Untestable halves of partial notes (no Task for N4 auto-add, N15 timer, N30 SMS/deficiency screen; same gap in delivered). Email template: "what I did" and open Staging requests. A Task-summary pattern. A saved copy of the email/QA message as a file (checkpoint rule). A QA-message template.

## Wasted for this session
Mandatory Haiku helpers on 3-6-ticket lanes; one Sonnet lead + one Haiku per nj-rank item (6 small registrations); review page "for the record"; `jira:add` (not runnable); `relay.py sweep` stays useful.

## Cost implied by the skill (estimate, not measured)
Skill as written: Lead plan ~5 min; 4 Sonnet leads + ~8 Haiku helpers ~15 min wall; register/outputs/QA message ~8; nj-rank 6 leads + 6 Haiku ~10; emails ~5; sweep ~3 => ~45 min wall, ~20 agents, roughly 1.0-1.3M tokens. Delivered: 4 leads, 0 helpers, filing ~10 min, nj-rank ~2 min, emails ~5 min => ~25 min, roughly half the agents and tokens, same tickets.

## Suggested edits to the skill
1. Replace the header count with "9 Bugs + 1 blocker Bug + 6 Tasks"; fix template subject line.
2. State precedence: tracker verdict after the design check wins; the owner's "untestable" is overridden only when a covering ticket/Bug results, and the flip is reported in the email, not asked.
3. Closed-ticket rule: "cite in the body, do not change the title".
4. Add a row: partial note -> Bug for the failing half + one Task for the untestable half.
5. Helpers: "optional; use only for lanes > 5 tickets or evidence needing masking".
6. nj-rank: one Sonnet lead for all items.
7. Add to the email template: "what I did" (3 lines) and the open-requests list; add Task summary pattern; name the repo root for `jira:add`.
8. Blocker row: add the condition "only on the owner's decision for this session; otherwise inspect-only".
