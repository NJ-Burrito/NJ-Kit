# Palette derivation — measured, not chosen

Read from `workflow-diagram/SKILL.md`'s "The house standard" section when the
palette itself needs re-justifying or re-measuring (a new role, a disputed
contrast ratio). The resulting values live in SKILL.md's "The palette — one
hue per role" table; this file is the derivation behind them.

### The palette, and the number that justified replacing it

The reference chart's seven fills sit between 1.14 and 1.15 to 1 against paper.
A tint that pale has almost no chroma, so the channel carrying «who performs
this step» carried nothing for a colour-blind reader. Measured as CIEDE2000
between the fills, under the Machado et al. (2009) severity-1.0 dichromacy
simulations, over the pairs **colour alone has to separate** (the five task
rectangles, plus the two terminators against each other — a terminator's ties
with a rectangle are broken by the stadium and its glyph):

| | normal | protanopia | deuteranopia | tritanopia |
|---|---|---|---|---|
| the reference's fills | 5.72 | **0.35** | **0.80** | 1.17 |
| these fills | 14.29 | 7.12 | 8.54 | 9.42 |

A JND is about 1. Two of the old numbers are below it.

The replacement is anchored on Tol's `light` scheme (**D11**), each anchor
blended toward white by an amount a search chose subject to the contrast
targets, and every role keeps the reference's own reading of it. Line and ink
are each fill's **own hue scaled in linear light** — chromaticity preserved
exactly, luminance placed where the target is, because WCAG luminance is linear
in the channels so «the darkest tone that meets the target» is one division and
not a hunt (**D10**, **D14**).

| Role | Fill | Line | Ink | ink/fill | line/fill | line/paper |
|---|---|---|---|---|---|---|
| Staff desk | `#ADCBBE` | `#065A44` | `#023A2B` | 7.34 | 4.72 | 8.22 |
| Applicant's own step | `#F3F0E9` | `#67655E` | `#383732` | 10.48 | 5.13 | 5.83 |
| Applicant's rework task | `#F3B3A2` | `#853311` | `#571F08` | 7.34 | 4.75 | 8.47 |
| Payment | `#F4E7B2` | `#8B5A05` | `#4E3102` | 9.59 | 4.75 | 5.89 |
| Something the system does | `#B3E4FA` | `#0F648F` | `#053B56` | 8.72 | 4.75 | 6.48 |
| End by refusal or cancellation | `#FFC9D2` | `#AF1F31` | `#6F101C` | 8.23 | 4.75 | 6.86 |
| End by approval | `#D6E1A0` | `#3F680F` | `#243E05` | 8.57 | 4.73 | 6.57 |

Worst title ink on its own fill **7.21** — AAA, where **D8** asks 4.5. Worst
outline on its own fill **4.72** (the subtitle is set in it). Worst outline on
paper **5.83**, where **D9** asks 3. Furniture: connectors 9.90 / 6.84 / 6.86,
their pales 3.08 / 3.08 / 3.09, the «إجراء» outline `#7C7B75` 4.24, the caption
and legend ink `#3F3E3A` 10.71.

The one value that does **not** reach 3:1 is the common-region band's hairline,
`#DCD6C6` at 1.45. That is deliberate and it is inside **D9**'s own exemption:
the band is a redundant grouping cue over information every box already carries
in its fill, and a border dark enough to pass would read as a competing
rectangle around the stages. If the band ever becomes the *only* thing saying
who owns a step, it has to be darkened — and something has gone wrong upstream.

Re-measure any change with two things: `tools/srs/palette-check.py` in the
repo, for «is every colour drawn on a declared ramp», and
`palette-contrast.py` beside this skill, for «does it still read» — it takes a
`{roles, wires}` JSON (`palette-flow.json` here holds what is currently drawn)
and prints the WCAG ratios plus pairwise CIEDE2000 under normal vision and the
three dichromacies, split into the pairs colour must carry alone and the pairs
a shape and a glyph also separate.

```bash
python ~/.claude/skills/workflow-diagram/palette-contrast.py \
       ~/.claude/skills/workflow-diagram/palette-flow.json
```

