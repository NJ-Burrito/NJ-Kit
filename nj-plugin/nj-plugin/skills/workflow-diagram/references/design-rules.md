# Design rules — the full catalogue and sourcing

Open this when re-deriving or re-justifying a rendering choice (colour, line weight, symbol, label placement) rather than trusting memory. Referenced from SKILL.md § Design rules.

## Design rules — researched, 2026-09-08

The client asked for «the design and colouring … easy for the human eye to
navigate, using professional design guidelines», and these are the guidelines
that were looked up rather than remembered. Each rule carries its source. What
they change in the renderer is recorded under «The house standard» below; what
they do **not** change is the content — the ledger and the gates still decide
what is on the sheet.

### Symbols and notation

| # | Rule | Source |
|---|---|---|
| D1 | A process is a **rectangle**, a decision a **diamond**, and a start or an end a **terminator of its own shape** — not a rectangle in a different colour. | ISO 5807:1985 (paywalled; symbol set as summarised at [useworkspace.dk](https://www.useworkspace.dk/en/blog/iso-5807-flowchart-symbols-guide) and [Wikipedia: Flowchart](https://en.wikipedia.org/wiki/Flowchart)) |
| D2 | A task's **type marker** sits as a small glyph in the task's leading corner: a head for a user task, a **cog** for a service task. It is the standard way to separate human from automatic, and it is what a swimlane-free chart uses in place of lanes. | [Visual Paradigm: BPMN task types](https://skills.visual-paradigm.com/docs/bpmn-fundamentals-for-beginners/bpmn-process-modeling/bpmn-task-types-manual-service-user/) |
| D3 | The **gateway carries the question and each outgoing flow carries the answer**; a two-outcome gateway may take a yes/no question with «نعم»/«لا» on its gates. Converging gateways stay unlabelled. | Bruce Silver, [Method & Style: gateways and end states](https://www.methodandstyle.com/blog/gateways-end-states-example-bpmn-style/); [Trisotech BPMN style rules](https://www.trisotech.com/bpmn-style-rules/) |
| D4 | With **more than one end event, each is labelled with its own end state**; with one, it is left unlabelled. | [Trisotech BPMN style rules](https://www.trisotech.com/bpmn-style-rules/) |
| D5 | Model **left to right** in occurrence order, and do not put an outgoing flow on the left of a symbol or an incoming one on its right. | [Camunda: creating readable process models](https://docs.camunda.io/docs/components/best-practices/modeling/creating-readable-process-models/) |
| D6 | **BPMN assigns colour no meaning at all** — «BPMN in Color» is a non-normative interchange extension, not part of the spec — so colour may only ever be a *redundant secondary* channel: a light tint for the happy path, a header tint for human vs technical. | [bpmn-miwg/bpmn-in-color](https://github.com/bpmn-miwg/bpmn-in-color); [Trisotech: BPMN modelling best practices](https://www.trisotech.com/bpmn-modeling-best-practices/) |

### Colour, contrast and colour-blindness

| # | Rule | Source |
|---|---|---|
| D7 | **Colour is never the only channel.** Pair it with shape, pattern, glyph or wording. | WCAG 2.2 SC 1.4.1, [Understanding Use of Color](https://w3c.github.io/wcag21/understanding/use-of-color.html) |
| D8 | Text needs **4.5:1** against its background (3:1 only at 18pt / 14pt-bold and above). | WCAG SC 1.4.3, [Understanding Contrast (Minimum)](https://www.w3.org/TR/UNDERSTANDING-WCAG20/visual-audio-contrast-contrast.html) |
| D9 | A **graphical object needed to understand the content — a shape's outline, a line in a diagram — needs 3:1**, unrounded. | WCAG SC 1.4.11, [Understanding Non-text Contrast](https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html) |
| D10 | Relative luminance is `L = 0.2126R + 0.7152G + 0.0722B` on linearised channels (`c ≤ 0.04045 ? c/12.92 : ((c+0.055)/1.055)^2.4`); contrast is `(L₁+0.05)/(L₂+0.05)`. Compute it; never eyeball it. | [W3C relative luminance](https://www.w3.org/TR/WCAG21/relative-luminance.html) |
| D11 | For **fills that carry dark labels**, use Paul Tol's `light` qualitative scheme — it exists for exactly that: «to fill labelled cells with more and lighter colours … keeping black labels clearly readable». | Paul Tol, *Colour Schemes*, SRON/EPS/TN/09-002, [sronpersonalpages.nl/~pault](https://sronpersonalpages.nl/~pault/) |
| D12 | Alternate warm and cool; separate two warms or two cools by brightness; avoid the yellow-green band; prefer dark blue and orange over sky blue and yellow for **thin** objects. | Okabe & Ito, *Color Universal Design*, [jfly.uni-koeln.de/color](https://jfly.uni-koeln.de/color/) |
| D13 | Categorical colours should sit at least **CIEDE2000 ΔE ≈ 10** apart to stay discriminable across a page (a JND is ≈ 1). | [Palettailor, arXiv:2009.02969](https://arxiv.org/pdf/2009.02969); [Colorgorical](https://gramaz.io/pdf/gramazio-2016-ccd.pdf) |
| D14 | Give a light fill a **darker outline of the same hue** — it holds the shape's boundary at 3:1 even when the fill itself cannot, and preserves the element's extent for anyone who cannot read the fill. | [UK Government Analysis Function: data visualisation colours](https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-colours-in-charts/) |

### Line, weight and label

| # | Rule | Source |
|---|---|---|
| D15 | A drawing uses **two or three line weights**, drawn from the 0.18 / 0.25 / 0.35 / 0.5 / 0.7 / 1.0 / 1.4 / 2.0 mm series (ratio 1:√2), and thick-to-thin is **at least 2:1**. | ISO 128-2 (paywalled), as reported by [Wikipedia: ISO 128](https://en.wikipedia.org/wiki/ISO_128) and [CADD Rafter](https://caddrafter.us/line-weights-and-annotation-standards/) |
| D16 | Weight encodes importance: heaviest for the primary run, lighter for secondary, **dashed for what is hidden, optional or not currently active**. | [CADD Rafter](https://caddrafter.us/line-weights-and-annotation-standards/); Tufte's data-ink, [EDAV notes](https://jtr13.github.io/cc19/tuftes-principles-of-data-ink.html) |
| D17 | An **arrowhead is sized off its own stroke**, not off the page — SVG's `markerUnits` defaults to `strokeWidth` for this reason; InDesign's own heads run 4.5–5× the stroke. | [vanseodesign: SVG markers](https://vanseodesign.com/web-design/svg-markers/); [Adobe InDesign ArrowHead API](https://developer.adobe.com/indesign/dom/api/a/ArrowHead) |
| D18 | Clear space between parallel lines is **never less than twice the heaviest line's width**, floor ≈ 0.7 mm; and parallel runs are kept short. | McGill, *Principles of dimensioning* (403 on direct fetch; figure via search cache — treat as reported, not re-verified) |
| D19 | A label must be legible, unambiguously attached to what it names, and **must not overlap other content**; names are neither clustered nor mechanically spread. | Imhof's rules, as set out in [Automated Names Placement (CartoGIS)](https://cartogis.org/docs/proceedings/archive/auto-carto-9/pdf/automated-names-placement-in-a-non-interactive-environment.pdf) |
| D20 | A text **halo/casing** is at most about **a quarter of the type size**; beyond that it reads as a blob. | [Esri, «Polishing your halo»](https://www.esri.com/about/newsroom/arcuser/polishing-your-halo); [Axis Maps: labeling](https://www.axismaps.com/guide/labeling) |
| D21 | Print labels do not go below about **6–7 pt**, and a size hierarchy carries importance. | [Axis Maps: labeling and text hierarchy](https://www.axismaps.com/guide/labeling) |

### Grouping and Arabic type

| # | Rule | Source |
|---|---|---|
| D22 | **Common region is the strongest grouping cue there is** — «a clear boundary … can overpower other grouping principles such as proximity or similarity». Reach for a tint band or an enclosure when whitespace cannot do the job, and only then. | [NN/g: The principle of common region](https://www.nngroup.com/articles/common-region/); Palmer 1992, via [IxDF](https://ixdf.org/literature/topics/gestalt-principles) |
| D23 | Arabic **looks smaller than Latin at the same nominal size** and is often set 1–2 pt larger to read as equal. | [Alex Strick van Linschoten, «Why do Arabic fonts appear so small?»](https://alexstrick.com/personal/2017-03-12-why-are-arabic-fonts-so-small.html) |
| D24 | Arabic needs more vertical room — dots, ascenders and tashkeel run past the Latin envelope: **≈1.7–1.85× line height for body**, against ≈1.5–1.6 for Latin. (Which is why this renderer's measured glyph box is **1.82×**.) | [UAE Design System 2.0, typography](https://designsystem.gov.ae/guidelines/typography) |
| D25 | Cairo runs 200–1000; use **300–400 for dense labels** and 600+ only for headings — heavy Arabic loses its counters at small sizes. | [Google Fonts: Cairo](https://fonts.google.com/specimen/Cairo) |
| D26 | Inside a small shape, **centre** Arabic rather than right-aligning it: right alignment misreads against a mirrored geometry. Mixed Latin and digits must follow the bidi algorithm. | [DTP Labs: RTL typography guide](https://www.dtplabs.com/blog/rtl-typography-complete-guide-arabic-hebrew-farsi); [rtlstyling.com](https://rtlstyling.com/posts/rtl-styling/) |
| D27 | A diacritic renders **attached to its base letter** and never breaks to a line of its own — a floor on vertical clearance in a tight layout. | [W3C, Arabic & Persian Layout Requirements](https://www.w3.org/TR/alreq/) |

### What the figure does with them

- **D1/D4** — a start and every ending is a **stadium** (`rx = h/2`) at the
  heaviest outline on the sheet, carrying a **✓** (approval), a **✕** (refusal
  or cancellation) or a head (the opening). Three channels for the one question
  a reader comes to the chart to answer, so **D7** is satisfied without relying
  on green-versus-red at all.
- **D2** — a `system` box carries a cog, every human task a head-and-shoulders.
- **D6/D7/D16** — three classes of connector, each differing in **colour and
  weight and dash together**: forward 2.1 solid `#44433F`; return 1.4 dashed
  `9 4` `#8A4A12`; refusal 1.4 dotted `2.6 3.2` `#AF1F31`. Thick-to-thin is
  2.1 : 1.05 = **exactly 2:1** (**D15**), and there are three weights, not more.
- **Unobserved is a second channel, not a fourth class** — *and it is never
  applied to the forward path.* A **return** or a **refusal** the model defines
  and no walk has travelled keeps its class's hue, at the thin weight and a
  fine `4 3.5` dash, in that hue's `pale` — each blended toward paper as far as
  it goes and still holding **D9** (3.08, 3.08, 3.09 to 1). Drawing all of them
  one flat grey was tried for a day: on a service where most refusals are
  undemonstrated it turned the whole middle of the chart one colour.
- **The black main line is solid, always — the owner, 2026-09-15.** «in the diagram
  اتلاف مستحضرات a dotted line going from التدقيق بعد الإجراءات and it's
  supposed to be a black solid line not dotted — that was my issue in the SRS.
  And it occurs in استشارة فنية.» The **forward chain is `#44433F`, solid, at
  2.1, end to end**, whatever the evidence says, because it is the model's own
  path and the model is authoritative about what connects to what. A reader
  does not read a broken line as «undemonstrated»; they read it as «these two
  stages are not connected», and that is the one thing the figure must never
  say by accident. «Unobserved» is still on the sheet — it is the **box's** own
  tint and its lighter dashed outline, and the legend row, which now names a
  stage rather than a path: «مرحلة يعرّفها النموذج ولم تُشاهَد على الموقع».
  Twenty-four of the thirty-eight documents had a pale fine-dashed spine on
  2026-09-15; `tools/srs/spine-solid.mjs` is the gate that keeps them solid.
- **A staff desk the packer could not fit on the chain is still on the chain.**
  The same night's second cause: `classify()` called any edge from the main
  band into the band **above** a return, which is right for the applicant's
  rework lane («إشعار مقدم الطلب» → «تعديل الطلب من مقدم الطلب» → «انتهاء مهلة
  الاستكمال») and wrong for a **detached desk** the chain branches out to —
  رئيس الشعبة on `cosmetic-medical-disposal`, رئيس قسم الأنظمة والخدمات and
  رئيس القسم on `technical-consultation`, التفتيش on `monitoring-side-effects`,
  اللجنة on three more. A detached row has no spine index, so «backwards» has
  to be measured as **reach from the start over the model's own edges**; a
  staff desk the model reaches later is forward, and only a staff desk the
  model reaches earlier is a return.
- **D17** — one marker per class per state, `markerWidth` 6.6 in the default
  `strokeWidth` units, so a return's head is smaller than the forward path's in
  exactly the proportion its line is lighter.
- **D19/D20** — every caption is now cased, not only the ones standing on a
  wire: `paint-order="stroke fill"` with a 3.2 white stroke at 14 px type —
  under D20's quarter-size ceiling — in **one** text node, so the collision gate
  still counts one caption and `caption-check` still reads one string.
- **D22** — each run of two or more consecutive spine columns belonging to the
  applicant gets a tinted band behind it (`#F6F4EE`, hairline `#DCD6C6`). One
  band per grid row; the chain wraps, and a band that spanned the wrap would
  enclose every corridor between the two rows.
- **D18** — the corridor's edge padding went 16 → 18. Not the lane pitch: at 18
  units against a 2.1 stroke that was already eight times the rule.
- **D26/D27** — unchanged, because they were already right: `direction="rtl"`,
  `text-anchor="middle"`, and a measured glyph box of 1.82× (**D24**).

The full derivation — the CIEDE2000 dichromacy measurement that justified
replacing the reference chart's own pale tints, and the search that anchored
the replacement on Tol's `light` scheme — is in `reference/palette.md`. Open
it before re-measuring or re-justifying a role's colour; the resulting values
are in "The palette — one hue per role" below.

