# Sizing, wrapping and payment placement

Open this when a figure will not fit one page, when deciding row count / wrapping, or placing the payment step. Referenced from SKILL.md.

## One page, by proportion — not by carrying less

A chain drawn on one line is five times wider than the page is tall, so the page
scales it to a third of the size two grid rows would have printed at. The number
of grid rows is therefore **searched**, and scored on the size a box title
actually prints at:

```
pt = 17 · min(269mm/W, 148mm/H) · 72/25.4 − 0.35 · (captions that found no room)
```

Only that. No type floor, no splitting, nothing dropped. Measured across the
five hardest services in the set: 4.97 pt (22 stages, 9 desks, 41 connectors),
5.14, 5.98, 7.06, 12.07. The client zooms; what they cannot do is untangle a
figure whose returns cross.

## The chain wraps to reach a readable size — the owner, 2026-09-15

> «in the service تغيير موزع مستحضر تجميلي the diagram is so wide — why not
> stack it so it fits and be in a readable size! do that to the other SRSs too.»

«Readable» now has a **number**, and it is measured off the one figure the
service owner signed off: `artifacts/srs/PROJ/figure-frozen/
food-product-registration.svg` is 1711 × 460, fits the 269 × 140 mm art box at
0.1572, and prints its 140-unit box **22.0 mm** wide with the title at 7.58 pt.
The floor in `workflow-figure.ts` is `REFERENCE_BOX_MM = 21.5` — the approved
sheet's own size, less the 0.3 mm that service has drifted since the freeze,
because a floor above what the approved figure itself rebuilds at would wrap
the approved figure.

The rule, in three parts:

1. **Fewest grid rows that reach the floor wins.** A compact sheet is read as
   one line and a wrap costs the reader a corridor plus the work of finding
   where the line resumes, so a chain that is already readable on one row stays
   on one row. Below the floor the ordinary score still decides, so a chain too
   long to be readable at any row count gets the best sheet available.
2. **Nothing shrinks.** A box is 140 × 56 units at every row count; the row
   count is the only thing that moves. `flow-collisions.mjs` gained an
   **`undersize`** fault for any `<rect data-el="node">` under that, because a
   shrink is the fix somebody reaches for next time a figure will not fit and
   it collides with nothing.
3. **Restart, not boustrophedon.** Every grid row runs in the same direction
   and the wrap is an explicit orthogonal arrow — out of the end of the row, one
   lane in the corridor between the rows, back to the start of the next — and it
   carries the model's own caption like any other edge. Boustrophedon was
   rejected on the skill's own rules, not on taste: **D5** forbids an outgoing
   flow on the left of a symbol, rule 3 above requires columns **shared by every
   grid row** (a row that ran backwards would have no shared columns and no
   clear vertical gutters), and the common-region band is «one band per grid
   row» for the same reason. A row that reads the other way also breaks the one
   thing the reader is given: every row starts where the last one started.

### The straight shortcut that made it look impossible

The search already varied the row count, and it already scored on printed type
size — and it kept choosing **one row** for `change-distributor`, at 10.8 mm.
The cause was not the score. `route()` drew the drop from an «إجراء» onto the
ending beneath it **without checking the run was clear**: right on a one-row
sheet, where the ending stands directly under the diamond with nothing between,
and wrong the moment the chain wraps, because the terminator band is one band
for the whole sheet while the diamonds are spread over the grid rows. At three
rows that vertical ran through five desks. A collision costs the search three
points of type, so five of them bought the single wide row.

It is the same test `nextTo()` already applies to a satellite assembly, and it
is now applied here: **a shortcut is only a shortcut while the slot is empty.**
When it is not, the edge falls through to the corridor router and takes a
gutter like anything else. That one guard took every wrapped candidate to zero
collisions, and the search then chose the wrap on its own.

| service | one row | chosen | box mm |
|---|---|---|---|
| change-distributor | 3490 × 500 | **2 rows** | 10.8 → **18.4** |
| monitoring-side-effects | 1811 × 369 | **2 rows** | 20.8 → **34.5** |
| license-trade-cosmetics | 3274 × 471 | **3 rows** | 20.6 → **21.0** |
| food-product-registration | 1738 × 471 | 1 row, unchanged | 21.7 |
| personal-import-invoice, technical-consultation, cosmetic-medical-disposal | — | 1 row, unchanged | 24.1 / 27.4 / 23.6 |
| invoice-name-approval, clinical-study-approval | — | 2 / 3 rows, unchanged | 24.3 / 19.7 |

`change-distributor` and `clinical-study-approval` do not reach the floor at any
row count; they take the best sheet available and that is stated rather than
hidden. Nothing was scaled: the figure is fitted to the 269 × 140 mm art box as
it always was, and no wrapped layout exceeded the sheet height.

## Payment is not a desk

The back office lists «الدفع» among the stages, which made the document print
«قبل مرحلة التدقيق» in the fee table, the business rule and the requirement
alike. It is drawn where it *happens*, in the applicant's own colour, with a
colour of its own because it is the one step that can time out.

Derive the position from the observed route — and when the service owner states
the order, the owner wins. An observation beats a sentence carried over from
another service; it does not beat the owner of the service telling you what
their own service does.

