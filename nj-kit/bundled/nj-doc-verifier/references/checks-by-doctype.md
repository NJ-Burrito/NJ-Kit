# Checks by document type — the profile table, expanded

One concrete worked example per check. The examples are illustrative shapes,
not real findings: reproduce the *method*, never the example's values.

Read the matching section only. The SRS section is the client's §3
(`method-ar.md`) with examples attached; the rest generalise the same moves to
other document types.

- [1. SRS / requirements](#1-srs--requirements)
- [2. User and staff manuals](#2-user-and-staff-manuals)
- [3. Training material](#3-training-material)
- [4. Markdown docs and README](#4-markdown-docs-and-readme)
- [5. API reference](#5-api-reference)
- [6. Release notes](#6-release-notes)
- [7. The `[+]` standards checks, applied](#7-the--standards-checks-applied)

---

## 1. SRS / requirements

Sources, in order: catalogue row → process model (`.bpmn20.xml`) → message
registry (`messages_ar`) → live UI.

### 1.1 Every field written «اختياري» / optional

Search the message registry for `ERROR_xxxxx = <field>: حقل إجباري`. If it is
there, the document is wrong: the system refuses submission without it.

> **Example.** The document's field table marks «رقم السجل التجاري» optional.
> `messages_ar.txt` carries `ERROR_00452 = رقم السجل التجاري: حقل إجباري`.
> Finding: *wrong* — cite the error code and the table row.

Error codes arrive in consecutive blocks per service, and a block may carry no
heading. Infer the block boundary from the field contents themselves, and if
the boundary is uncertain **say so in the finding** rather than silently
choosing one.

### 1.2 Every value list vs the enum

Search `com.example.app.<EnumName>.*`. Compare the count and the wording.

> **Example.** The document lists 6 «فئات المنشآت»; the enum has 7. One missing
> value is a real defect, not a rounding. Separately: the document writes
> "(30 يوماً)" beside a category and no source anywhere states 30. **Every
> number with no source is a finding** — parenthesised numbers a document adds
> to a list are the classic case.

### 1.3 Every promised notification

Count `notificationService.*` calls in the model and locate them.

> **Example.** The document promises "the applicant is notified at every
> stage". The model has 3 calls, at submission, at rejection and at issuance —
> not at the two review desks. Phrase the finding with the count and the
> positions, not as "the claim is exaggerated".

### 1.4 Every stated duration or deadline

Demand the timer: `boundaryEvent` / `timerEventDefinition`.

> **Example.** The document states an SLA of 5 working days at the technical
> review. No boundary timer on that `userTask`. Finding: a commitment with no
> enforcement mechanism. Where a timer *does* exist, name its configuration
> key so the reader can change it.

### 1.5 Every mention of an output or certificate

> **Example.** The document has a section "الشهادة الصادرة". The catalogue row
> says `OUTPUT_TYPE = NOTHING` and `CAN_PRINT_CERT = False`. There is no
> output; the whole section is wrong, not just its wording.

### 1.6 Every conditional requirement

Confirm the condition exists in the model or the UI.

> **Example.** "If the applicant is a foreign company, an authorisation letter
> is required." No gateway, no conditional field, no `(req)` attachment
> conditioned on customer type. Finding: unverified at best, invented at worst
> — say which, and why.

### 1.7 Every role and action key, matched literally

Match `candidateGroups` and gateway conditions character for character, and
report defects **in the keys themselves**.

> **Example.** The document writes `Role_ TechReview_FPR` with a space inside
> the key; the model has `Role_TechReview_FPR`. Also: stage 3 calls the action
> `${action=='approve'}` and stage 5 `${action=='Approve'}`. Both are findings
> against the system, not typos in the document.

### 1.8 Internal contradiction

The document against itself. The shapes that keep recurring:

- A section says «لا يوجد شعبة» while a whole stage is assigned to «رئيس الشعبة»
- A business rule makes a field a precondition; the field table marks it optional
- A decision offers the value «رفض» with no «رفض» action key anywhere
- A «النوع» column says «مقدم الطلب» inside a requirement about staff
- A gap in the identifier sequence (FR-11, FR-13, no FR-12)
- One unit spelled two ways («كغم» and «كجم»)
- A mandatory field whose unit field is optional

### 1.9 Template conformance

Compare the table columns against the approved template.

> **Example.** The field tables are missing «قيود الحقل» and «القيمة
> الافتراضية». That is not cosmetic: those two columns are where the
> constraint and the default live, and without them nobody can build or test
> the field.

### 1.10 The missing

The hardest direction — from the system towards the document.

> **Examples.** An integration that has a screen and no requirement. A
> `serviceTask` call in the model that the document never mentions. A rule in
> the message registry with no counterpart. A duration declared in the
> catalogue row and absent from the document.

---

## 2. User and staff manuals

Sources, in order: the live UI → the i18n / message registry → the model (who
may see and do what) → the catalogue.

| Check | Worked example |
|---|---|
| **Every path reachable, by the stated role** | The manual routes the reviewer through **الطلبات ← قيد المراجعة ← فتح**. Signed in as that role, «قيد المراجعة» is not in the menu — the tab exists only for the desk supervisor. Finding: wrong role, and the step is unreachable as written |
| **Every label verbatim** | The manual says press **حفظ**; the button reads **حفظ ومتابعة**. Quote the UI, in its own wording and capitalisation, and never use a label as a verb ("press **Submit**", not "submit the form using Submit") |
| **Every field name matched to the form** | The manual calls a field «اسم المنتج التجاري»; the form's `formcontrolname` and its Arabic label say «الاسم التجاري للمنتج». A reader searching the screen for the manual's phrase finds nothing |
| **Screenshots current** | A screenshot still shows the pre-redesign header, a removed **تصدير** button, or a field the build renamed. Check the theme, the logo, the menu order — not only the highlighted control |
| **Prerequisites real** | "You need an activated account and an establishment licence." The model requires neither for this step; the second is required three steps later. State where it is actually enforced |
| **Every step's result true** | Step 7 claims "a confirmation message appears with the request number". The system shows the number on the next screen and no message. One step, one action, and the stated outcome observed |
| **No step for a screen that no longer exists** | An entire subsection documents a payment screen the flow now skips for exempt categories |
| **Nothing secret in frame** | A real national ID, name, licence number, serial or a deployment tag legible in a screenshot is a defect regardless of the text around it |

---

## 3. Training material

Sources: a real run of the live system → the manual it teaches → the model.

| Check | Worked example |
|---|---|
| **Every exercise reproducible end to end** | Exercise 2 asks the trainee to reject a request from the technical desk. That desk's role has no reject action in the model — the exercise cannot be completed and no trainee will report it as a bug |
| **Every "expected result" observed** | "You will see the status change to «مرفوض»." It changes to «معاد للمقدّم». The expected result was written from the design, not from a run |
| **Sample data still exists** | The workbook uses establishment `12345` and product code `FPR-DEMO`; neither is in the environment any more |
| **Timings realistic** | "This step takes about a minute" against a queue that takes a working day |
| **No live side effects unannounced** | An exercise that files a real request on a staging deployment that is a real deployment — a fee, a queue and a record that cannot be undone. Either say so loudly or move the exercise |

---

## 4. Markdown docs and README

Sources: the repo (code, configs, scripts) → the CI workflow → the running app.

| Check | Worked example |
|---|---|
| **Every command run once** | `npm run harvest -- --service FPR` — the script is `harvest:service` and the flag is `--code`. Paste it into a terminal; do not read it approvingly |
| **Every flag and env var exists** | The README documents `PROJ_DEBUG=1`; nothing in the source reads it. Grep the parser, not the prose |
| **Defaults match the code's defaults** | Documented timeout 30 s; the constant is 15 s |
| **Every path and link resolves** | A link to `docs/setup.md` after the file moved to `docs/getting-started.md`; an image with a path that 404s |
| **Install works on a clean checkout** | The steps assume a `.env` that only exists on the author's machine, or a global tool the prerequisites never name |
| **Versions current** | "Requires Node 16" while `engines` says `>=20`; a badge pinned to a released version two majors back |

---

## 5. API reference

Sources: the schema/spec → the handler code → one live call.

| Check | Worked example |
|---|---|
| **Endpoint, method and path in the router** | Documented `POST /api/v1/requests/submit`; the router has `POST /api/v1/requests` and no `/submit` |
| **Parameter name, type, required-ness, default** | `page_size` documented optional, default 50; the handler requires it and defaults to 20 when absent. Three findings in one row |
| **Every documented error producible** | A documented `409 DUPLICATE_REQUEST` that no code path raises — either dead documentation or a missing guard. Both are findings |
| **Every response field returned** | The example response shows `certificateUrl`; the serialiser omits it unless the request is issued. Document the condition or drop the field |
| **Auth scopes real** | "Requires scope `requests:write`" against a middleware that checks a role, not a scope |
| **Deprecations marked in both places** | Deprecated in code with no note in the doc, or vice versa |

---

## 6. Release notes

Sources: the commit/PR range and the issue tracker → the diff → the deployed build.

| Check | Worked example |
|---|---|
| **Every claimed change is in the diff** | "Fixed the Arabic PDF export" with no commit touching the export path in the range |
| **Every breaking change flagged** | A renamed response field shipped under "improvements" |
| **Nothing shipped that the notes omit** | A migration that changes a default is in the diff and absent from the notes — the omission is the finding |
| **Version and date match the tag** | The notes head v3.2 dated the 6th; the tag is v3.2.1 dated the 8th |

---

## 7. The `[+]` standards checks, applied

Numbers are the sources in `references/sources.md`.

| Check | What it catches, concretely |
|---|---|
| **Singular** [2] | «يجب أن يقوم النظام بإرسال إشعار وتحديث الحالة» — two requirements in one id. Neither can be accepted, refused or tested separately. Split |
| **Verifiable** [1][2] | "The screen must load quickly" / «بسرعة مناسبة». Ask: what test proves this? No answer means no requirement. Demand a number and a tolerance |
| **No escape clauses** [2] | "attachments including but not limited to…" — the list is unbounded, so the requirement can never be met or breached. Demand the closed list |
| **Owner in the subject** [2] | "The request is reviewed within 3 days" — by whom? Passive with no owner is a commitment nobody made |
| **Bounded values** [2] | "response under 2 s" with no load, percentile or tolerance |
| **Score twice** [1] | Every requirement individually fine, and the set still missing the rejection path entirely. Set-level failure is invisible from a per-row read |
| **Trace both ways** [3] | FR-22 has no source need behind it and no test in front of it. It is an orphan: nobody asked for it and nobody checks it |
| **Widows** [3] | A screen documented in section 5 that no FR requires — undeclared scope, and usually where the surprises live |
| **Name the verification method** [6] | "The system is secure" — by test, demonstration, inspection or analysis? No inferable path means the claim is decorative |
| **One action per step, location first** [5] | "Press Submit in the Requests tab after selecting the row" → three actions, in the wrong order, in one step |
| **Labels verbatim** [5] | Covered in the manual profile; it is the single most common manual defect |
| **Run it once** [4] | Covered in the README profile; untested samples and stale screenshots are the two most common developer-doc defects |
| **Version match** [6] | Auditing the v3.0 document against the build that shipped v3.2. Every finding in such a pass is unattributable — establish this before anything else |
