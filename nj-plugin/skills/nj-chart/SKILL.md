---
name: nj-chart
description: "Charts, dashboards and metric reports that read at a glance, in Arabic or English, light or dark, built on the Flint chart engine (MCP server `flint`). Use for any chart, graph, KPI row, trend, funnel, token or cost breakdown, run report, or dashboard page, including ones that must work offline in a local HTML tool. Triggers: chart, graph, plot, dashboard, metrics, KPI, trend, report with charts, رسم بياني، مخطط، لوحة مؤشرات، تقرير بالرسوم."
---

# nj-chart

nj-chart is how this toolkit makes charts. It is a thin, opinionated layer over **Flint** (Microsoft, MIT licence, https://github.com/microsoft/flint-chart): Flint compiles one semantic chart spec into Vega-Lite, ECharts or Chart.js; nj-chart adds the house rules for reading comfort, bilingual text, themes and offline use.

## Setup (once)
Register the Flint MCP server in Claude Code: `claude mcp add flint -- npx -y flint-chart-mcp@1.0.1`. Its tools appear as `flint` (load them with ToolSearch "+flint" when deferred).

## How to make a chart
1. Call `get_flint_skill` with skill `chart` before writing a spec; `board` for several charts together; `interaction` for hover, brush or linking.
2. Write the spec, run `validate_chart` (or `validate_board`), fix what it reports.
3. Deliver it the way the destination needs:
   - **Chat or a page with live UI:** `show`.
   - **A local or offline HTML tool:** `compile_chart` to the lightest backend that supports what you need (Chart.js for simple, ECharts for rich interaction), and **vendor that library's minified build next to the page with its licence file**. Never load it from a CDN when the page must work offline or under a strict CSP.
   - **A static image or print report:** `render_chart` to SVG and inline it.

## House rules (every chart)
- **One question per chart.** Title says the answer in plain words, then a one-line «💡 how to read it».
- **State = colour + icon + word.** Never colour alone; colour-blind safe.
- **Themes:** take colours from the page's design tokens, both light and dark, checked for contrast (text ≥ 4.5:1).
- **Text:** at least 16 px for anything a person reads; only drawn diagram labels may be smaller.
- **Bilingual:** Arabic text right-to-left, English left-to-right; codes and Latin names stay as they are inside Arabic. Flows and funnels run left to right in both languages.
- **Numbers:** aligned, same units in a row, totals shown, estimates marked `~`.
- **Calm motion:** short, interruptible transitions; respect `prefers-reduced-motion`; do nothing while the page is hidden.
- **Light:** render lazily on scroll, re-render only when the data changes.
- **Interactive charts** link through to the detail they summarise when the host has routes.

## Common forms
| Question | Form |
|---|---|
| How did it change over time? | line or area, with a target line |
| What is it made of? | stacked bar (parts of a whole per period) |
| Which is biggest? | sorted horizontal bar |
| Where did items drop out? | funnel, left to right |
| How far from target? | KPI tile: value, target, ✅/⚠️, sparkline |
| Cost per model per stage | grouped bar or table with a totals row |

## Credits
Chart engine: Flint by Microsoft Corporation, MIT licence. nj-chart adds rules and wiring only; it does not modify or redistribute Flint's code. When a page vendors a compiled backend (Chart.js, ECharts, Vega), ship that project's licence file beside it.
