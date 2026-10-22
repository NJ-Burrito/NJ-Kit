---
name: workflow-diagram
description: 'Draw or fix an SRS workflow figure «مخطط سير العمل» from evidence: one box per element the model walks, left-to-right, an «إجراء» decision after any multi-exit task. Triggers: flowchart, swimlane, diagram wrong, unreadable, cluttered, incomplete, missing branch, return loop.'
---

# The workflow figure

A workflow diagram in a requirements document is not decoration. It is the
claim the whole document is checked against: *this is who does what, in this
order, and these are the ways it can end.* If the figure and chapter 6 disagree,
the figure is what a reviewer believes, because it is the thing they can read in
one pass.

So it is **derived, never drawn**. The same evidence produces the same picture
every time, which is the only property that makes a diagram reviewable at all.
A hand-tuned figure is out of date the moment the service changes and nobody
can tell by looking.

## Standard v5 summary (2026-09-15)

The current figure rules for the 8 in-scope PROJ services are consolidated in
`artifacts/srs/PROJ/srs-standard-v5.md` §3 — starts at «إرسال الطلب», compact
style (box ≥ 21.5 mm), derived from the service's own Flowable model, one
connected forward chain (no island/dangling/doubled edge), the solid black
`#44433F` spine that never dashes even for an unwalked stage (unobserved is
the box's tint/outline only), returns as their own lanes with one «إعادة
تقديم الطلب» bubble, no invented boxes, every edge labelled, full-size row
wrapping, and the legend line naming each class — with the gate that enforces
each rule. Read that file's §3 for the one-page version; the sections below
are the full evidence and history behind it.

## The three rules that outrank everything

Every diagram bug this project has shipped was one of these being broken.

1. **Every decision shows both answers.** A gateway with only the happy path is
   worse than no gateway: it asserts there is no other way out. If a desk offers
   «رفض», the figure shows where رفض goes.
2. **Every stage is named in the portal's own words.** Not a paraphrase, not a
   translation, not what the old SRS called it. The button says «إرسال لرئيس
   القسم»; the edge says «إرسال لرئيس القسم».
3. **Every return is independent and visible.** A return that curls back onto
   the line it came from, or that shares a corridor with the return beside it,
   has told the reader nothing. Each one gets its own lane, its own label and
   its own ending.
4. **One chain, and nothing drawn with no way into it** — client (owner),
   2026-09-15. «the main black arrow is not fully connected — it's like two
   loops instead of one.» The sheet must be walkable from the start terminator
   to every shape on it. `flowable-to-desks.ts` walks the model along the
   **order-1 exit of each gateway**, so a routing gateway's other arm never
   joins the spine: on `technical-consultation` the whole
   «رئيس قسم الأنظمة والخدمات → فني قسم الأنظمة والخدمات» branch of
   `REQUIRED_SECTION` arrived `detached` and was drawn with no edge into it
   from anywhere a reader could start. Every legibility gate passed — an island
   collides with nothing. `figure-compact.ts` now walks back through the struck
   rows to the nearest **reachable** surviving row and gives it the branch (a
   gateway's condition key is not a button, so that edge takes no caption, the
   same as the start arrow), and `flow-fidelity.mjs` fails on any shape the
   sheet cannot reach from «إرسال الطلب». Test **reachability**, never
   in-degree: the island had an incoming edge on every shape in it, from its
   own rework bubble. A shape the *model* gives no inbound flow at all
   (`license-trade-cosmetics`'s «اللجنة») is reported, never repaired — the
   figure may not invent a route.
5. **A rework bubble's way back carries the applicant's own word.** The
   «إعادة تقديم الطلب» bubble's return edge was pushed with an empty label, so
   every compact sheet in the set carried one unlabelled black arrow per bubble
   running into a desk — ten of them across seven services, and the client read
   the first he met as «a direct black arrow». The caption is «إعادة الإرسال» /
   «إتمام الطلب», read off the struck applicant row, never composed.

There used to be another — «nothing is scaled down to fit», with a 7 pt floor
and a rule that a figure which would not fit *carries less*. **Both are gone**,
at the client's instruction, 2026-09-07: «better the diagram and make it more
readable; you can change the sizes of the fonts and the bubbles, don't follow
the size rule … size the figure as much as you want since we can zoom.» The
drawing is a vector with whatever intrinsic size it needs, scaled onto one A4
landscape page. Nothing is dropped from the chart to make it fit. What is
searched is the **shape** of the drawing, not its content — see «One page, by
proportion» below.


## References

Open these on demand — each is verbatim content moved out of this file so the
spine stays short. None of it changed; only the location did.

- `references/design-rules.md` — the full D1–D27 symbol/colour/line/type rule
  catalogue with sources, and "what the figure does with them". Open before
  re-deriving or re-justifying any rendering choice.
- `references/house-standard.md` — every measured number: canvas, shape
  geometry, connector weights/dashes/heads, the palette, caption placement,
  the subtitle table. Open when implementing or checking exact geometry.
- `references/layout-sizing.md` — the one-page-by-proportion search, the
  row-wrap rule and its worked examples, and payment placement. Open when a
  figure will not fit or a wrap decision is being made.
- `references/evidence-ledger.md` — the ledger disposition table, the
  select-one-merge failure history, the reconciliation line, the per-element
  source table, the walk-as-source rule, the precondition/timer/caption-dictionary
  sections, and the old-SRS rule. Open when tracing where an element's wording
  or existence comes from.
- `references/measure-face.md` — the three numbers to measure in a real type
  face before trusting fit (advance width, glyph box, text-anchor direction).
  Open before assuming a new face behaves like Cairo did.
- `references/failures.md` — full failure catalogue: every symptom that has
  shipped, its cause, its fix, and what was tried and abandoned. Open when a
  symptom mid-build matches one of its rows.
- `references/palette.md` — the CIEDE2000 dichromacy measurement and the
  search that anchored the palette on Tol's `light` scheme. Open before
  re-measuring or re-justifying a role's colour.

## The layout, in ten lines

0. **The chart is the model, not a summary of it.** Every `userTask`, every
   `serviceTask`, every `endEvent` and every named flow the process model holds
   is on the sheet — the desks *and* what runs between them: the routing step
   that hands the request to a role, the notification, the bill, the draft, the
   ready-to-sign mark. Client instruction, 2026-09-07: «make sure the diagram
   matches Flowable and every decision option and route includes everything;
   you forgot a lot of steps such as التوزيع الآلي». A chart of the people only
   is a chart of half the service, and it passes every legibility check ever
   written — a missing stage collides with nothing. Prove it with a gate that
   counts the model's own elements against the sheet's shapes
   (`tools/srs/flow-fidelity.mjs` in the PROJ pipeline), not by eye.
1. Read the rows into a **chain**: one box per stage, plus a small «إجراء»
   diamond after any stage with more than one way out. A stage whose own name
   ends in «؟» *is* the diamond, and so is a decision the system makes for
   itself — a gateway no task owns, which carries no name a reader could use
   and is drawn as a bare «إجراء».
1b. **The chain starts when the request is sent** — client (owner),
   2026-09-15. «مخطط سير العمل» begins «عند إرسال الطلب»: the start terminator
   **is** the submission event, labelled **«إرسال الطلب»**, and nothing the
   applicant does before pressing it is a box — not signing in, the service
   card, the undertaking, the lookup that pre-fills the form, a «تحقق» gate,
   filling the panels, attaching, a fee paid before submit, nor any
   «تقديم الطلب» applicant stage. The first drawn box after the terminator is
   the first post-submission element the model walks: the routing step where
   there is one, otherwise the first desk. Everything the applicant does
   **after** submitting is unchanged — the rework task, «إرجاع لمقدم الطلب»,
   «إعادة الإرسال», and a payment step that follows submission all stay, drawn
   exactly as before. Only the drawing changes: §2.11, chapter 3 and chapter 6
   keep every row, and the omitted pre-submission stage takes its own ledger
   disposition (`not-a-stage`, reason «مرحلة سابقة لإرسال الطلب») so that
   «decided against» is still told apart from «went missing».

2. Cut the chain into **grid rows**, balanced (25 over 4 is 7+6+6+6, never
   7+7+7+4), every row running left → right; the wrap is an explicit arrow, not
   a lettered ring.
3. Columns are **shared by every grid row**, so the gaps between them are clear
   vertical strips from the top of the drawing to the bottom.
4. Terminators hang in a **band below** the chain; the applicant's rework task
   and the endings it reaches sit in a **band above** it, each at the column its
   own traffic averages out at.
5. Between the bands and the line lie **channels** — horizontal corridors that
   contain no shapes at all.
6. Every horizontal run of every connector takes a **lane in a channel**; every
   vertical run takes a **lane in a gutter**. A lane is granted only when
   nothing on it already holds that extent.
7. So a connector is: port → stub → channel lane → gutter lane → channel lane →
   stub → port; adjacent stages on one grid row skip all of it and run straight.
8. Geometry and routing settle **together** — the corridors decide how wide the
   gutters are, which decides where the shapes stand, which decides the
   corridors. Take the largest count seen; it converges in three passes.
9. Two stubs can still land in one column, because a stub is anchored to its
   shape and has no lane to choose. So the router **measures its own output**
   for runs within 6 px of each other and pushes a port aside until there are
   none.
10. Labels last, against the finished drawing: the midpoints of the edge's own
    segments, longest first, offset to either side; the first rectangle that
    clears every shape, every caption and every **other** connector wins. A
    caption may stand on its own line, with a knockout, and on nothing else.

## Build order

1. **Collect.** Panels, per-desk action bars, fee rows, output name, route.
2. **Fold captions before matching.** The portal writes «إرسال» at one desk and
   «ارسال» at the next. Fold `أإآٱ→ا`, `ى→ي`, `ة→ه` before comparing. An
   allowlist missing a variant stops a walk; a never-press list missing one
   presses «ارجاع» and sends a live request backwards.
3. **Classify each action** into onward / refuse / return, by matching the
   folded caption. Keep the **original** string for the label.
4. **Build the rows** — applicant rows, then routing, then one row per desk.
5. **Place payment** by the observed route, not the desk ordering.
6. **Render**, then **gate** — `flow-collisions.mjs` (legible),
   `flow-fidelity.mjs` (complete, against the model **and the walk**),
   `caption-check.mjs` (in the site's own words), `spine-solid.mjs` (the
   forward chain solid black at full weight, and no desk reachable only by a
   dashed line) — then rasterise the sheet and
   look at it. `diagram-audit.mjs <service>` regenerates the three-source
   comparison table automatically, and its «اتفاق ثلاثي: N من M» line is the
   number to quote when someone asks whether the figure got better.

## Verify before you call it done

```bash
npx tsx src/srs/build.ts <service> --from 1     # --only 3 will not pick up a new walk
node tools/srs/ledger-check.mjs   <service>     # every element has a disposition, and the document carries it
node tools/srs/flow-collisions.mjs <service>    # legible
node tools/srs/flow-fidelity.mjs  <service>     # complete — model AND walk AND every automatic step
node tools/srs/caption-check.mjs  <service>     # the site's own words
node tools/srs/diagram-audit.mjs  <service>     # the three-source table, and the agreement count
python tools/srs/palette-check.py <service>    # every colour drawn is on a ramp
```

And **look at it**, because none of the above can:

```bash
npx tsx tools/srs/design-shot.ts  after <service…>   # the figure straight out of checkpoint 2
node  tools/srs/figure-shot.mjs   artifacts/srs/PROJ/audit/design/*-after.svg
npx tsx tools/srs/legend-sample.ts                   # the key on its own sheet
```

Read the PNGs and answer five questions. They are the design's acceptance test
and they are not things a gate can ask: **can a reader follow the main path
end to end; spot every return; tell a human task from a system one; tell a path
somebody has walked from one only the model claims; and read every label.**

`ledger-check.mjs` also prints the ledger as a table — element | Flowable |
old SRS | walk | back office | disposition — which is the per-service audit to
hand a reviewer.

`flow-fidelity.mjs` gained a check for the **assignment step** on 2026-09-07.
Every `serviceTask` is a node and was always counted; the round-robin
assignment is not a node — the model states it as
`flowable:assignee = ${…getAssigneeRoundRobin(…)}` on a userTask — so there was
nothing for a node check to count, and the figure's synthetic `route-<task id>`
box was checked by nobody. It now requires that box **and** the same step in
chapter 3 and chapter 6, because a stage is not only a shape: «التوزيع الآلي»
was on the sheet the whole time it was missing from chapter 6.

**`--from 1`, not `--only 3`**, whenever a walk, a control dump or the caption
dictionary has changed: the applicant rows, the verify gates and the desk
subtitles are all decided in stage 2, and re-rendering checkpoint 3 keeps the
old ones.

The gate reads back the rectangle the generator declared for every shape and
caption (`data-el` / `data-box`) and every connector's own path
(`data-el="edge"` / `data-from` / `data-to` / `d`), and fails on:

- **overlap** — two solid things sharing space;
- **crossing** — a connector through a box, or through a caption that is not
  its own;
- **alongside** — two connectors **parallel within 6 px** for any distance worth
  seeing. This is the fault the eye reads as one thick line, and the reason a
  return stops being independent;
- **outside** — anything drawn beyond the frame.

It **counts, and does not fault, right-angle crossings**. A chart with skips and
returns cannot be planar; a reader has followed a right-angled crossing since
the first flowchart. What they cannot follow is two lines running together. If
the count runs away — past about two per connector — the layout has gone wrong
even though the gate is green, so read the number.

`scripts/check-flow.mjs` still lints a standalone `flow.json` for structure: a
branch pointing at a row that does not exist, a decision with no alternative
answer, a duplicate node id, an end node with no tone, a node with no lane, an
empty or `-` label, an untranslated action key, a label long enough to have been
truncated.

**An absent `onward` is an error; an empty one is a decision.** A flow derived
from an old SRS with no walk behind it deliberately sets `onward: ''` — no
screen has been seen, and captioning that edge «موافقة» would invent a button.
That is correct, and the linter warns rather than fails, on the condition that
an open question names the gap.


## Any other diagram (architecture, sequence, org chart, timeline)

This skill builds one kind of figure. For every other kind there is no house
builder, and these four checks are the floor (2026-09-20, adapted from
cathrynlavery/diagram-design @ dc1ace4, MIT, `SKILL.md:143-160, 352-409, 445-475`;
its fonts and palette are not imported — the project's tokens apply):

- **Refuse the defaults by name**: dark background with cyan or purple glow,
  drop shadows, three equal-width summary cards, identical boxes that erase
  hierarchy.
- **One grid.** Node widths, gaps, padding and radii all come from a 4 px grid;
  a measurement off the grid is a fault, not a style.
- **Complexity budget: 9 nodes, 12 arrows.** Above 9 nodes it is two diagrams.
- **Remove test before shipping**: would a table or a paragraph do the job — then
  do not draw; can a node, an arrow or a label be removed or two nodes merged
  without losing meaning — then remove it; accent colour on at most 2 elements;
  the legend covers every type used and nothing else; the `<svg>` carries
  `role="img"` with a filled `<title>` (first child) and `<desc>`.

### Mermaid for the other diagrams (since 2026-10-01)

For an architecture, sequence, ER, state or timeline diagram **drawn from code**,
write Mermaid text from the code and render it with `mmdc` (@mermaid-js/mermaid-cli
12.0.0, MIT, global npm). The hand-built workflow figure above stays authoritative
for the workflow figure: Mermaid does not replace it, and the four checks above still apply.

```
mmdc -i d.mmd -o d.svg -c <NJ_PLUGIN_ROOT>/skills/workflow-diagram/mermaid/mermaid-config.json -C <NJ_PLUGIN_ROOT>/skills/workflow-diagram/mermaid/mermaid.css -b "#F3F8F9" -s 2
```

Config `mermaid/mermaid-config.json` carries the brand palette (from `brand/tokens.json`);
`mermaid/mermaid.css` loads Thmanyah Sans from ENSERA `brand/fonts/thmanyah/` by file URL.
Extension `.png` or `.pdf` gives those. The fonts are referenced, not embedded: do not
paste an SVG that embeds them into anything public (licence: no redistribution).
**Arabic caveat:** labels render joined and in Thmanyah, and an all-Arabic diagram
works with `flowchart RL`. Mixed Latin and Arabic in one label follows the bidi
algorithm, so check word order. Edge labels sit on the line, so `visual_gate`'s
overlap check flags them: run it on the SVG wrapped in minimal HTML, and read overlap
hits on edge labels as inherent, not a fault. Smoke outputs and notes:
ENSERA `documentation/10-Instagram-Reels-Review/mermaid/mermaid.md`.

## When someone says "the diagram is wrong"

Ask which of the three rules it breaks — a missing answer, a renamed stage, or a
return you cannot follow. It is almost always one of them, and each has a
different fix. Then check the failure catalogue above by symptom before reading
any code.
