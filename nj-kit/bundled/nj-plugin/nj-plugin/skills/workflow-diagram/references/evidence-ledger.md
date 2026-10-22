# Evidence ledger, merge rules, captions and sourcing

Open this when tracing where a figure element's wording or existence comes from, resolving a merge conflict between sources, or looking up the caption dictionary / old-SRS rule. Referenced from SKILL.md § Where every part of the figure comes from.

## The ledger is the only input to the figure — 2026-09-07

**Nothing is derived from one source. The figure is drawn from the evidence
ledger, and the ledger is the union of all of them.**

`tools/srs/PROJ/evidence-ledger.ts <service>` folds the four sources —
the process model, the delivered client SRS, the site walk, the back-office
record — into `artifacts/harvest/PROJ/ledger-<service>.json`: one row per
workflow element, carrying which sources have it, what each of them calls it,
and one **disposition** saying what the document did about it.

| Disposition | Means | On the sheet |
|---|---|---|
| `drawn` | on the sheet, and a walk or a record saw it | solid |
| `drawn-unobserved` | the model defines it, no walk reached it | the **box** takes the lighter dashed outline; the forward line into it stays solid black; legend row «مرحلة يعرّفها النموذج ولم تُشاهَد على الموقع» (2026-09-15) |
| `document-only` | the approved SRS names it; model and site do not | **never drawn as a stage** — printed in the reconciliation line under the caption |
| `not-a-stage` | a button that routes nothing, a status, a gateway, a fee, a chapter-3 functional unit | not drawn, with its reason recorded |

A row with **no** disposition is a build failure (`tools/srs/ledger-check.mjs`).
That is the mechanism: a forgotten stage is now a missing value in a file
rather than a silence nobody can see.

### A select-one merge is forbidden

Wherever two sources describe the same element the result is a **union with
provenance**: every field either source states is kept, the stronger source
wins a field they both state (walk › back office › model › delivered document,
for a *caption*; none of them beats another for *existence*), and the row
records who said what.

«التوزيع الآلي» has now gone missing from one document twice, and both times
the cause was a merge that picked:

1. `harvest()` **chose** the walk file over the model file. The walk carries no
   `steps` and no `graph`, so the whole of the model's structure vanished — the
   notification, the rework task, the timer, both stop endings and every return
   branch. A better harvest produced a worse figure.
2. Fixed by spreading one object over the other — which is still a select-one
   merge for every key they *both* have, and they both have `desks`. The walk's
   three desk records replaced the model's three, and with them went
   `autoAssigned`, `assignment`, `roleKey`, `formKey`, `requiresComment` and
   `actionTargets`. Nothing failed. The figure still drew the routing step (it
   reads a different field), chapter 3 still printed its requirement (a third),
   and only chapter 6 went quiet.

Both are the same fault at different depths, and neither was caught, because
four consumers each read their own field out of their own source. **Union at
every level, matched on identity where there is one and on folded whole words
where there is not.**

### The reconciliation line

Where the ledger has any `document-only` element, the figure carries one line
under its caption — above the art, never below it, because on a fold-out
anything after the drawing lands on a second landscape page:

> عناصر وردت في وثيقة المتطلبات المعتمدة ولم تُشاهَد على الموقع ولا في النموذج:
> «…» — لم تُرسم مراحلَ في المخطط، وهي بانتظار تأكيد مالك الخدمة.

The rule that a chart may only carry stages somebody has seen stays exactly as
it was. What changes is that **not drawing something is now stated**: a reader
who remembers a stage from the approved version is told it was looked for and
not found, instead of being left to wonder whether it was missed. Take the room
for that line off the drawing (`reconciliationMm` in `render.ts`), never off the
page count.

## Where every part of the figure comes from

This is the contract. Each element has exactly one source **for its wording**;
whether it is drawn at all is the ledger's answer, not one source's.

| Element | Source | Rule |
|---|---|---|
| The fill step, and its «(N أقسام)» | The **form panels** — the control dump, grouped by panel | The count is the number of panels actually seen. Never a guess, never carried from another service. |
| Attachment step | The attachments panel | Present-and-empty is a finding: draw nothing and say «لا يوجد مرفقات مطلوبة». |
| Applicant's exits | The form's own buttons | «إرسال» / «إلغاء» verbatim. |
| Each desk box | The **desk list** from the back-office walk | One shape per desk, named exactly as the desk list names it. |
| Each edge leaving a desk | The **action bar of that desk** | Forward, refuse, return — each a separate labelled edge, captioned with the button verbatim. A desk that offers no «رفض» draws no refusal. |
| Payment step | The fee rows, plus the observed route | Drawn where it *happens*. See "Payment" above. |
| Output node | The staff view's «اسم المخرج» | Named on the staff screen and nowhere else. If there is none, «لا يوجد مخرج». |
| The role colour | Who performs it | applicant / staff / system. This is the answer to "who does this", so it is never approximate. |
| The **subtitle** under a desk | The task's own **assignment in the model** | `assignee` with `getAssigneeRoundRobin(…)` → «موظف مُعيَّن آلياً»; `candidateGroups` → «مجموعة مرشحة»; an applicant task → «مُقدّم الطلب». Not one string per lane — see «The subtitle says who» below. |
| A **verify gate** — «تحقق من «X»؟» | The control dump's `verify: true` entries, and the walk's `verifyWidgets` | A `taq-*` widget with its own «تحقق» button, drawn as a decision with **both** answers before submit. See «The precondition nobody drew» below. |
| The **boundary timer** | The model's `boundaryEvent`, and the back-office record for its length | Its own shape, carrying the clock. See «A timer is an element» below. |
| The state the applicant is shown | The walk's `portalStatusTexts` and each step's `portalAfter` | «قيد المعالجة» on the routing step, the closing status as the ending's own subtitle. Declared by no other source. |
| The desk's **decision field** | The walk's `deskFields` | «تنسيب قرار المدقق» prints in the desk's subtitle and in chapter 6, marked required. |
| Every edge caption's **wording** | `src/srs/template/captions.json` | The site's form of the model's flow name. See «The caption dictionary» below. |

### The walk is a source — 2026-09-07

`artifacts/harvest/PROJ/site-walk-<service>.json` — one real request, filed
through the applicant's portal and advanced through every desk — is a **standard
evidence source**, and the strongest one there is. It beats `backoffice:desks`,
which beats `flowable:model`. Its provenance tag is `portal:walk`.

The merge rule, when a walk and a model both exist, is a **union**:

- Every element either source has is on the sheet.
- **The walk's caption wins** where both name the same edge — verbatim, not
  folded, because a reader holds the document beside the screen.
- A model element **no walk reached** is kept, marked `evidence: 'model'`, and
  drawn with a lighter dashed **outline** plus the legend row «مرحلة يعرّفها
  النموذج ولم تُشاهَد على الموقع». Real and undemonstrated are different
  claims; one weight for both says they are the same claim. The **forward line
  into it is still solid black** — see «the black main line is solid, always»
  above.
- With no walk at all, the pipeline's own applicant rows are used and marked
  `evidence: 'template'` — an assumption, stated as one.

«Wins» is not «replaces». For a day, `harvest()` *chose* between the walk file
and the model file, and the walk file carries no `steps` and no `graph` — so the
first `--from 1` after a service was walked silently dropped the notification
step, the rework task, the timer, both stop endings and every return branch. A
better harvest produced a worse figure and nothing said so. Merge; never pick.

### The precondition nobody drew

«رقم كتاب تسجيل المنشأة» is a field with **no `formcontrolname`** and a «تحقق»
button of its own, and without it `food-product-registration` cannot be filed at
all — the service answers ERROR_00811. It was in no source: the model starts at
the submitted request, and the control dump only reported controls that carry a
name. Three sources, and the hardest gate in the service was in none of them.

`dump-form-controls.ts` now emits every `taq-*` host owning its own «تحقق»
button as a field with a **synthetic** control name (`taq-request-serial-input`
→ `requestSerialInput`), `synthetic: true`, `verify: true`. The figure draws each
as a decision «تحقق من «X»؟» before submit, with both answers — «نعم» onward and
«لا — الحقل إجباري» back to the form, because that is what the walk was actually
shown. **A gate no walk has passed is drawn as unseen**: a form can carry more
verify widgets than one filing meets — the customs lookup exists only on the
«مستورد» branch — and drawing them all as observed repeats the error in a new
place.

### A timer is an element, not an adjective

A boundary timer used to be a clock inside the stage and a caption merged onto
the same arrow as the applicant's own «إلغاء الطلب» — «إلغاء الطلب أو انتهاء
المهلة». That one arrow says two different things: a person pressed a button,
and nobody did anything for long enough. The model separates them — an explicit
`cancel` flow, and an interrupting `boundaryEvent` whose listener cancels where
it stands with **no outgoing flow at all**. A merged arrow cannot show that a
request can end with nobody touching it.

So the boundary event gets its own shape, carrying the clock, and the request
travels task → «انتهاء مهلة الاستكمال» → the cancelling end. Its length comes
from the service's back-office record; where that record does not state one
either — and for `food-product-registration` «متغيرات الطلب» is literally «لا
يوجد» — the box says **«مهلة يحددها مدير النظام»** rather than inventing a
number or printing the process variable's name.

### The caption dictionary

`src/srs/template/captions.json` maps each model flow name to the caption the
**site** prints: `approve`→«موافقة», `need-edit`→«إرجاع لمقدم الطلب»,
`return-to-verification`→«إرجاع للتدقيق», `return-to-head-of-section`→«إرجاع
لرئيس الشعبة», `reject`→«رفض», `re-submit`→«إعادة الإرسال», `cancel`→«إلغاء».
A `byService` block holds what a walk read on a real action bar and wins over
the table.

This exists because the converter rendered `return-to-verification` as «إرجاع
**إلى** التدقيق» while the button says «إرجاع **لـ**لتدقيق». Both are ordinary
Arabic, so no gate and no proofreader ever caught it, and a reader holding the
document beside the screen has to decide whether they are the same action —
which is the doubt the figure exists to remove. `nonRouting` in the same file
lists the buttons that route nothing («رجوع», «عرض», «إضافة», «تحميل»).

`tools/srs/caption-check.mjs` fails a build whose figure prints a caption for a
known flow in any other form. It says nothing about captions the dictionary has
no row for — «نعم», «لا», «إرسال» are the figure's own words for answers no
button gives — and it does not require every dictionary row to appear, because
a service with no `reject` flow must not print «رفض».

### The old SRS

Read it for **values**, never for shape:

- ✅ fee figures, the analyst who prepared it, answers the portal no longer shows
- ❌ wording, typography, section order, the stage list, the diagram itself

**And only where the live service confirms it.** An old SRS that names a stage
the walk never saw is an old SRS describing a previous version of the service.
The service panel wins. If the old document says there is a «لجنة فنية» step and
no desk in the walk is one, it does not go in the figure — it goes in the open
questions, addressed to the service owner.

This is the rule that keeps the figure trustworthy: **the diagram may only
contain stages somebody has actually seen.** Naming a chain of approvals nobody
has observed is the one class of error a governance document cannot carry.

