# Report template — bilingual Markdown skeleton

Read from `website-fine-print/SKILL.md` at write-time, once the audit itself
is done. This is the exact skeleton to fill in — Arabic heading, English
beneath, in the house SRS shape. Save through the normal filing route as a
**Document**.

## The report

One Markdown file, bilingual headings in the house SRS shape — Arabic heading,
English beneath it. Save it through the normal filing route as a **Document**.

````markdown
# التدقيق القانوني للموقع — «الأحرف الصغيرة»
# Website fine-print audit

| | |
| --- | --- |
| الموقع · Site | https://example.com |
| الصفحة المفحوصة · Page under test | /checkout |
| التاريخ · Date | 2026-09-06 |
| الأداة · Tool | QA Wrap 18 — Check the fine print + Check accessibility |
| النطاق · Scope | القانوني والخصوصية · Legal and privacy — Y/N · الأساسيات التقنية · Site hygiene — Y/N |
| المدقق · Auditor | |

> **حدود هذا التقرير · The limit of this report.** This records what the site
> **declares** and what the browser **observed**, and the gap between them. It is
> not a legal opinion and not a certificate of compliance. Whether a gap is
> unlawful is a question for counsel in a named jurisdiction. Every row marked
> MANUAL was not checked by any tool and is waiting on a named person.

## ١ — الخلاصة · Summary

| | عدد · Count |
| --- | --- |
| فجوات · GAP | 0 |
| بانتظار قرار بشري · MANUAL | 0 |
| مُعلن ومطابق · DECLARED and consistent | 0 |

جملتان، واحدة لكل سطح · Two sentences, one per surface:

- **القانوني والخصوصية · Legal and privacy:** *This page loads from N other
  companies and set M cookies before consent was asked.*
- **الأساسيات التقنية · Site hygiene:** *This page scrolls sideways at N of 4
  phone widths, has M links that go nowhere, and still carries K strings of
  placeholder text.*

> **ملاحظة على النطاق · A note on scope.** لا شيء في قسم «الأساسيات التقنية»
> مسألة قانونية؛ هي أعراف ومعايير تقنية، ويُذكر ذلك صراحةً حتى لا يُقرأ نقصٌ
> في أيقونة الموقع كمخالفة.
> Nothing in the site-hygiene section is a legal matter. Those rows are
> conventions and technical standards, labelled as such, so that a missing
> favicon is never read as a compliance breach.

## ٢ — القابل للفحص الآلي · Machine-checkable

### ٢-١ صفحات السياسات · Policy pages

| البند · Item | DECLARED | OBSERVED | الحالة · Status |
| --- | --- | --- | --- |
| سياسة الخصوصية · Privacy policy | /privacy — 200, updated 2025-11 | linked from footer | DECLARED |
| الشروط والأحكام · Terms & conditions | | | GAP — 404 |
| سياسة الكوكيز · Cookies policy | | | |
| سياسة الاسترجاع · Refund policy | | | |

### ٢-٢ توقيت موافقة الكوكيز · Cookie-consent timing

| اللحظة · Moment | ms | ما حدث · What happened |
| --- | --- | --- |
| تحميل الصفحة · Page start | 0 | |
| أول تخزين · First storage write | | cookie `_ga`, origin google-analytics.com |
| ظهور اللافتة · Banner painted | | |
| الموافقة · Consent given | | |

**مسار الرفض · Reject path:** what still happened after declining.

### ٢-٣ موافقة النماذج · Form consent
### ٢-٤ تقليل البيانات · Data minimisation
### ٢-٥ التتبّع · Tracking
### ٢-٦ التضمينات الخارجية · Third-party embeds
### ٢-٧ بيانات الجهة · Business details

*(same four-column shape: البند · DECLARED · OBSERVED · الحالة)*

## ٣ — الأساسيات التقنية للموقع · Site hygiene

> عُرف أو معيار تقني، لا التزام قانوني. المرجع هنا هو التوقّع المكتوب في
> العمود «المتوقَّع»، لا ما يعلنه الموقع عن نفسه.
> Convention or technical standard, not a legal obligation. The benchmark in
> this section is the written expectation in the *Expected* column, not
> anything the site declares about itself.

### ٣-١ التمرير الأفقي والفيض على الجوال · Horizontal scroll and mobile overflow

| العرض · Width | تمرير أفقي · Scrolls sideways | العناصر الفائضة · Overflowing elements | الحالة · Status |
| --- | --- | --- | --- |
| 320 px | | | |
| 360 px | | | |
| 390 px | | | |
| 414 px | | | |

### ٣-٢ الروابط المكسورة والميتة · Broken and dead links

| الرابط · Link | الوجهة · href | الموضع · Where | السبب · Reason | الحالة · Status |
| --- | --- | --- | --- | --- |
| | | التذييل · Footer | 404 / `#` / مكرّر · duplicate | |

### ٣-٣ هوية الصفحة · Page identity

| الصفحة · Page | العنوان · Title | فريد · Unique | الوصف · Meta description | الأيقونة · Favicon | الحالة · Status |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

### ٣-٤ صفحة «غير موجود» · The 404 page

| الإشارة · Signal | المتوقَّع · Expected | المرصود · OBSERVED | الحالة · Status |
| --- | --- | --- | --- |
| رمز الحالة · Status code | 404 | | |
| هوية الصفحة · The site's own shell | نعم · yes | | |

**تحذير الـ 404 الزائف · Soft-404 caveat:** إن أعاد الخادم 200، فأرقام ٣-٢ أقل
من الحقيقة. If the server answers 200, the counts in ٣-٢ understate.

### ٣-٥ وزن الصور · Image weight

| الصورة · Image | البايتات · Bytes | الأصلي · Natural px | المعروض · Painted px | النسبة · Ratio | الصيغة · Format |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

**الوزن الكلي للصور · Total image weight:** — KB

### ٣-٦ عناصر التفاعل · Interactive elements

*(ثلاث خانات لكل صف: المرصود آليًا، والمُحال لإمكانية الوصول، والمتروك لقرار
بشري. خانة فارغة تعني «لا يوجد ما يُقرَّر»، لا «لم يُنظر فيه».)*
*(three cells per row: the machine half, the delegated half, the human half. An
empty cell means there was nothing to decide, not that nobody looked.)*

| البند · Item | المرصود · OBSERVED | مُحال · Delegated (SC) | بشري · MANUAL |
| --- | --- | --- | --- |
| قائمة الجوال · Mobile menu | | 2.1.1, 4.1.2 | |
| الأزرار · Buttons | | 4.1.2 | |
| رسائل النجاح · Success messages | | 4.1.3 | |
| رسائل الخطأ · Error messages | | 3.3.1, 3.3.3 | |

**النماذج التي أُرسلت فعليًا · Forms actually submitted:** — (وبإذن مَن · with
whose agreement)

### ٣-٧ النصوص النائبة وسنة حقوق النشر · Placeholder text and the copyright year

| النص · String | الموضع · Where | نص أم سمة · Text or attribute | الحالة · Status |
| --- | --- | --- | --- |
| | | | GAP |

| سنة حقوق النشر · Copyright year | المرصود · OBSERVED | السنة الحالية · Current year | الحالة · Status |
| --- | --- | --- | --- |
| | | | |

### ٣-٨ الشعار ووسائل التواصل القابلة للنقر · Clickable logo, phone and email

| البند · Item | النص الظاهر · Visible text | الوجهة · href | يتطابقان · Match | الحالة · Status |
| --- | --- | --- | --- | --- |
| الشعار · Logo | — | | | |
| الهاتف · Phone | | `tel:` | | |
| البريد · Email | | `mailto:` | | |

**عدم التطابق أخطر من غياب الرابط · A mismatch outranks a missing link:** رقم
غير مرتبط مجرد إزعاج؛ أما `tel:`/`mailto:` يخالف النص الظاهر فيرسل الزائر إلى
جهة لم يقرأها. An unlinked number is an inconvenience; a `tel:`/`mailto:` that
disagrees with the visible text sends the visitor somewhere they never read.

## ٣ب — نص سياسة الخصوصية · What the privacy policy says

> يُملأ هذا القسم من صفحة السياسة نفسها، لا من الصفحة الرئيسية. إن لم تُفتح
> صفحة السياسة فاكتب «لم يُقرأ» ولا تكتب فجوة لم تُقَس.
> Filled in from the policy page itself, never from the home page. If the
> policy page was not opened, write *not read* rather than a GAP that was
> never measured.

| الإفصاح · Disclosure | مقتبس من النص · Quoted from the text | الحالة · Status |
| --- | --- | --- |
| يذكر جمع البيانات الشخصية · Says it collects personal data | | |
| يذكر المعالجة الآلية أو الذكاء الاصطناعي · Mentions automated or AI processing | | |
| يسمّي الجهات التي تشارك معها البيانات · Names who it shares data with | | |

### ٣ب-١ مطابقة السياسة بما استُدعي فعلا · The policy against who the page called

| المضيف الذي استُدعي · Host contacted | مذكور في السياسة · Named in the policy | الحالة · Status |
| --- | --- | --- |
| | | |

**هذا هو الطرح الوحيد في هذا القسم · This is the one subtraction in this
section.** الصفوف الثلاثة أعلاه فحص وجود؛ أما هذا الصف فيقارن ما رصدته الجلسة
بما تعترف به السياسة، والخلاف بينهما هو الاكتشاف. The three rows above are
presence checks; this row measures what the session observed against what the
policy admits, and the disagreement is the finding.

> **حدّ هذا القسم · The limit of this section.** وجود الكلمات ليس كفايتها.
> The presence of the words is not their sufficiency: whether a disclosure is
> accurate and adequate for what the site actually does is a legal reading,
> and a keyword pass is not one.

## ٣ج — الأمان بقدر ما تُظهره الصفحة · Security, as far as a page can say

> **هذا ليس تدقيقا أمنيا ولا يجوز تسليمه على أنه كذلك.** لا شيء في هذا القسم
> التزام قانوني: CORS قاعدة متصفح، وترويسات الأمان إرشاد OWASP.
> **This is not a security review and must never be handed over as one.**
> Nothing in this section is a legal obligation: CORS is a browser rule and
> the security headers are OWASP guidance. Say *convention*, or say *OWASP*,
> and never say *required*.

| البند · Item | المرصود · OBSERVED | المتوقَّع · Expected | الحالة · Status |
| --- | --- | --- | --- |
| التشفير والمحتوى المختلط · HTTPS and mixed content | | https, and no plain-http subresource | |
| مفاتيح مكشوفة · Keys reaching the browser | | none in source or in a query string | |
| خصائص الكوكيز · Cookie flags | | `Secure` on https, and a `SameSite` value | |
| رمز مانع للتزوير · Anti-forgery token | | a token on every posting form | |
| نموذج غير مشفّر · A form posting over http | | none | |

**ما لا تلتقطه الجلسة · What the session does not capture:** ترويسات الاستجابة
(CSP، HSTS، `X-Content-Type-Options`، `Referrer-Policy`، CORS) لا تُسجَّل هنا،
فاقرأها بـ `curl -I` وقل ذلك صراحة بدل الاستنتاج. Response headers are not
recorded here. Read them with `curl -I` and say so plainly rather than
inferring them.

**ما لا يُرسَل أبدا · What is never sent:** لا تُرسَل أي حمولة عدائية إلى أي
موقع. صلاحيات المستخدمين وتنقية المدخلات وXSS والحقن كلها تحتاج اختبارا نشطا
بإذن مكتوب وعلى أداة مخصّصة، وتُحال في القسم ٥. No adversarial payload is sent
at anybody. User permissions, input sanitising, XSS and injection all need
active testing with written permission on dedicated tooling, and they are
delegated in section ٥.

## ٤ — إمكانية الوصول · Accessibility

مُحال إلى تدقيق إمكانية الوصول · Delegated to the accessibility audit.
**N violations · M guided checks outstanding.** See `<link to that report>`.
لا يُعاد فحص أي قاعدة هنا · No rule is re-checked here.

الإحالات من قسم «الأساسيات التقنية» · Delegated out of the site-hygiene
section: 1.4.10, 1.4.4, 2.5.8, 2.1.1, 2.4.4, 3.3.1, 3.3.3, 4.1.2, 4.1.3.

> **الاستثناء الوحيد · The one exception.** لا يفحص axe معيار الانسياب 1.4.10،
> فالقياس بقي في ٣-١ والحكم وحده أُحيل إلى هنا.
> axe does not test reflow (1.4.10), so the measurement stayed in ٣-١ and only
> the judgement was delegated here. Neither side may assume the other did it.

## ٥ — بانتظار قرار بشري · Awaiting a human decision

| البند · Item | السؤال · The question | المسؤول · Owner | MANUAL |
| --- | --- | --- | --- |
| المراجعات · Reviews | Is every testimonial real and evidenced? | | MANUAL |
| الادعاءات · Claims | Evidence for each superlative on the page? | | MANUAL |
| حقوق الصور · Image rights | Licence and receipt for every asset? | | MANUAL |
| صحة بيانات الجهة · Truth of business details | Name, address, contact current? | | MANUAL |
| القوانين المحلية · Local law | Which jurisdictions, reviewed by whom? | | MANUAL |
| روابط تنقّل بلا استخدام · Unused nav | This route works and nothing links to it — should it exist? | | MANUAL |
| سلوك الأزرار والرسائل · Behaviour of buttons and messages | Does each do and say what it should? | | MANUAL |
| تجربة الجوال · Mobile experience | After the rows above are clean, does it work on a phone? | | MANUAL |

## ٦ — المراجع · Standards touched

*(the table from the skill, trimmed to the rows this audit actually raised.
Site-hygiene rows carry «عُرف · convention» where no standard applies — that
cell is never left blank.)*
````
