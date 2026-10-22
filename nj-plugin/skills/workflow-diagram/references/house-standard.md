# The house standard — every measured number

Open this when implementing or checking exact geometry: canvas, shape sizes, connector weights/dashes, the palette, caption placement, subtitle wording. Referenced from SKILL.md § The house standard.

## The house standard — measured, not chosen

The design language is read off the reference chart the client's own side drew,
`<project>/cosmetic_import_invoice_workflow_people_only (4).svg`. Every number
here was measured in that file. Do not re-decide any of them.

### Canvas

| | |
|---|---|
| Ground | `#FFFFFF`, edge to edge |
| Reference canvas | 1689 × 910 (ratio 1.856) |
| Process direction | **left → right** |
| Text direction | **right → left** — `direction="rtl"` on every `<text>` |
| Typeface | Cairo. The reference used Segoe UI; the document's face wins |

**Cairo here is the client's own already-established document face, recorded, not a
recommendation.** Cairo is banned house-wide for ENSERA and every other
project (`~/.claude/CLAUDE.md`: "never propose it, never fall back to it, in
any project or deliverable") — if this skill is ever pointed at a non-PROJ
deliverable with no face of its own already set, the new document inherits
Thmanyah, never Cairo. The measured Cairo-specific facts below (D25's weight
range, the advance-width numbers under "Measure the face", the missing arrow
glyphs in the failure catalogue) are about rendering *this* client's existing
choice correctly, not an endorsement of the face itself.

### Shapes

Three outline weights and no more, which is what ISO 128 allows on one drawing
(**D15**): the terminator is heaviest because it is what the reader is looking
for, the task the middle, the gate the lightest because it is furniture. An
unobserved element takes 0.7 of its own class.

| Element | Geometry | Type |
|---|---|---|
| Task box | `rx="10"`, `stroke-width="1.3"`, height **64** with a subtitle, **56** without; width from its own text, 140 min / 320 max | title **17 px, weight 500**; subtitle **14 px** in the box's own line colour |
| Terminator — start *and* end | a **stadium**: the same box at `rx = h/2`, 140 × 56, `stroke-width="1.9"`, carrying **✓** / **✕** / a head on its centre line inside the left cap | 17 px / 500 |
| «إجراء» decision | diamond, half-width and half-height **34**, `fill="#FFFFFF"`, `stroke="#7C7B75"`, `stroke-width="1.1"` | **13 px**, the gate outline |
| A stage that *is* a question | the same diamond, grown to its own text | 14 px |
| Task-type badge | leading (left) top corner at `+10,+10`, stroke **1.15**, in the skin's own line colour: **cog** r 2.2/4.4 for a system step, **head-and-shoulders** for a human task, **clock** r 4.1 beside it where the model hangs a boundary timer | — |
| Chart title | bottom, at the **right** margin (the reference put it left; it carried no `direction` and reads as Latin) | **19 px, weight 500**, `#2C2C2A` |
| Legend entry | chip **24 × 16** `rx="4"` (a terminator's is a stadium) carrying that role's badge, **or** a 21-unit sample of the line itself at its own weight, dash and head; pitch **26** stacked, text at **+10**, **18** to the next entry | **14 px**, `#3F3E3A` |

Two-line box, measured: title baseline at `cy − 11`, subtitle at `cy + 13`.
Reproduced as a text block of `lines × 21 + 24` centred in the box.

### Connectors

A connector says two things at once: **what class of line it is**, in hue and
weight and dash together, and **whether anybody has ever travelled it**, in
weight and dash and paleness. See «Design rules» above for why it is two
channels and not four classes.

| Class | Ink | Pale (unwalked) | Weight | Dash |
|---|---|---|---|---|
| Forward — the main path | `#44433F` | **never pale — 2026-09-15** | **2.1** | solid, always |
| Return to an earlier stage | `#8A4A12` | `#AC8C80` | 1.4 | `9 4` |
| Refusal or cancellation | `#AF1F31` | `#C38185` | 1.4 | `2.6 3.2` |
| …any of them, unwalked | — | — | 1.05 | `4 3.5` |

| | |
|---|---|
| Head | an **open chevron**, not a filled triangle: `marker` `viewBox="0 0 10 10"`, `refX="8"`, `refY="5"`, `markerWidth/Height="6.6"`, `orient="auto-start-reverse"`, path `M2 1 L8 5 L2 9`, round caps. `markerUnits` is left at its default `strokeWidth`, so the head is **proportional to its own line** (**D17**), and there is one marker per class per state because a marker inherits nothing — a red line ending in a grey point is what happens otherwise |
| Departure | starts **on** the source's outline |
| Arrival | stops **4 px short** of the target's outline, so the chevron lands on it |
| Clear space between two shapes on the line | **45 px**, uniform |
| Corridor lane pitch / edge padding | **18** / **18** |
| Corners | orthogonal, rounded at radius 9 |
| Label | **14 px**, `#3F3E3A`, ~**13 px** off its own line; `text-anchor="middle"` above or below a horizontal run, `start`/`end` beside a vertical one; **always** cased — `paint-order="stroke fill"`, white, 3.2 wide, one text node |

**A diamond is met on its slope.** The reference gets three connectors out of
one «إجراء» without any of them touching: an exit at horizontal offset `d` from
the centre leaves at `y = cy ∓ hh·(1 − |d|/hw)` — a real point on the outline,
with the line still square to the shape. This is the mechanism that makes
«multiple arrows may leave or enter a stage from different sides» possible at
all, and it applies to rectangles too (offset along the face).

### The palette — one hue per role

**Replaced 2026-09-08 — the values and every contrast ratio are in the table
under «Design rules» above, with the ΔE measurement that justified it.** The
reference's own tints stay recorded there as the thing that was measured; they
are not what the renderer draws any more.

| Role | Fill | Line | Legend |
|---|---|---|---|
| Staff desk | `#ADCBBE` | `#065A44` | مرحلة الموظف |
| Applicant's own step | `#F3F0E9` | `#67655E` | مرحلة مقدم الطلب |
| Applicant's rework task | `#F3B3A2` | `#853311` | استكمال من مُقدّم الطلب |
| Payment | `#F4E7B2` | `#8B5A05` | دفع من مُقدّم الطلب |
| Something the system does alone | `#B3E4FA` | `#0F648F` | خطوة ينفذها النظام |
| End by refusal or cancellation | `#FFC9D2` | `#AF1F31` | نهاية بالإلغاء أو الرفض |
| End by approval | `#D6E1A0` | `#3F680F` | نهاية بالاعتماد |

**The legend names a box by what it is in the document, not by what BPMN calls
the node** (the client, 2026-09-09). A desk **is a stage** — «مرحلة الموظف»,
«مرحلة مقدم الطلب» — and «مهمة» is reserved for what the holder of a stage does
inside it without moving the request: a comment, an attachment, a concealment, a
recommendation. Those live in the stage's own data dictionary, never on the
drawing. The legend said «مهمة موظف» / «مهمة مقدّم الطلب» until that day and
contradicted the same client's own «إجراء vs مهمة» rule.

The system row is **not** in the reference — it draws people only — so it is the
cool end of the scheme, added because our services have system steps and an
unexplained colour is worse than an extra legend line. A system box also carries
a small **cog** in its trailing top corner, every human task a **head**, and any
stage the model hangs a boundary timer on a **clock**: a reader should not have
to consult the legend to know that a step runs by itself, that a person stands
behind it, or that it can expire (**D2**).

A run of two or more consecutive applicant columns also stands in a **tinted
band** — `#F6F4EE`, hairline `#DCD6C6`, `5 4` dash, one per grid row. Who does
what is a property of a box; **where the portal stops and the institution
starts** is a boundary, and a boundary is what common region draws (**D22**).

A role is in the legend only if a **box on this sheet is painted in it**. A
decision carries a role without ever showing it — every diamond is drawn in
paper with the gate outline — so «some shape has this skin» put a «خطوة ينفذها
النظام» swatch on six enquiry charts for a colour that appeared exactly once in
the whole SVG: on the swatch.

The legend lists **only the roles the chart actually drew**, in that order, and
sits under the title at the right margin, one row where it fits and wrapping
upward where it does not.

**And only the line classes it actually drew.** A chart that uses four weights
of line and explains none of them has four unexplained symbols on it, which the
failure catalogue below already lists as its own class of defect — and a colour
chip cannot say «dashed, and lighter». So each class registers the same way a
role does, from the drawing rather than from the fact that the feature exists,
and it is shown as **a piece of the line itself**: its own weight, its own dash,
its own head. Each role chip carries that role's own **badge**, so the cog and
the head and the ✓ and the ✕ are taught in the key rather than guessed at.

The key is the drawing's own furniture and it grows: register a new row and the
sheet gets taller, which on a height-bound figure is type size straight off the
page. The probe that decides how many rows it takes must therefore count the
**line** rows too — it counted roles only for a day, under-measured by a row,
and ran the key off the bottom of the sheet.

`tools/srs/legend-sample.ts` draws the whole key on its own sheet from a
synthetic flow that touches every role and every class exactly once. It is the
specimen; it cannot drift, because the figure draws it.

> **Closed, 2026-09-07, rebuilt 2026-09-08:** these fills and lines are not
> steps on the SRS ramps, so `tools/srs/palette-check.py` (standard rule 15)
> reported every one of them. The fix was one block in
> `manuals/templates/assets/palette.json` — a `flow` ramp holding the twenty-one
> role values, the six connector inks and pales, the diamond's outline, the
> caption ink, the title ink and the region band — because that checker allows
> any value on any declared ramp. Declare the ramp when you take these colours
> to a new project, and remember that **shrinking a ramp breaks the check**:
> folding two near-identical greys into one left the chart title and the legend
> ink homeless and the gate reported them on all four documents at once.

### A caption is never dropped

Every edge the model names carries its name on the sheet. The placer searches
beside the edge's own segments, longest first, at the ordinary offset; then
allows the caption to stand on **its own** wire and knock a hole in it; then
walks the offset outwards to ten times that and draws a hairline **leader**
back to the segment it names. What it will not do at any tier is sit on a box
or on another caption. «No seat, so it is not drawn» shipped five unlabelled
arrows across four services, and an unlabelled arrow on a chart of returns is
not a cosmetic loss — the reader cannot tell which answer it is.

Check it by counting, not by looking, and compare **whole strings**: a
`contains` test matches «إرسال» inside the diamond «إرسال الطلب؟» and passes an
arrow with no caption at all.

### The subtitle says who, and only what is evidenced

| Role | Subtitle |
|---|---|
| Staff desk, `candidateGroups` | `مجموعة مرشحة` |
| Staff desk, `assignee` + round-robin | `موظف مُعيَّن آلياً` — **2026-09-07.** Every desk read «مجموعة مرشحة», and for التدقيق in `food-product-registration` that is the opposite of what the model says: it is assigned to an *individual*, chosen by the system. Read the assignment; never the lane. |
| A desk with a mandatory decision field | the above, then ` · ` then the field — `موظف مُعيَّن آلياً · تنسيب قرار المدقق` |
| The routing step | `تنفيذ آلي · الحالة: <status>` where a walk read one |
| An ending | none, unless the walk read the portal's own status for it: `الحالة: موافق عليه` |
| System | `تنفيذ آلي` |
| Applicant, payment, rework | `مُقدّم الطلب`, and `مُقدّم الطلب – مهلة زمنية للإلغاء` **only when the stage actually carries a way out that cancels or expires** |
| Start and end nodes | none |

The timer half of that subtitle is a claim about the service. It is derived from
the stage's own branches (`إلغاء`, `انتهاء مدة`, `مهلة`) and never written by
hand.

