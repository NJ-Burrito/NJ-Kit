# SFX palettes by visual style

A palette names which sound *world* a style draws from, and what is banned.
Chosen by `PROJECT.md`'s `style:` field (per the mix.py patch). Add a palette
here whenever a new visual style is recorded — same file, new `##` section,
same shape.

## paper-punch

Flat paper cut-out collage, hard-snap stop-motion cadence, sticker-word
punches (brief description, `sfx-0921` brief). Sound world is **physical**:
paper, tape, scissors, card, a pencil, a stamp, a slide projector — never
synthetic UI blips (that is the "out of place" complaint's direct fix).

| action | layer(s) | seed source (fixed 2026-09-21) |
|---|---|---|
| beat/scene change | paper crumple or tear (body); card-slide transient dropped | `paper-paper-crushed-*`, `paper-paper-ripped-1` |
| hero word punch | short paper snap/tap | `paper-stationery-*` (short ones, <0.3s) — 22 of these carry the `unidentified-tool` tag, still unaudited; needs the owner's ear (`artifacts/production/sfx-ab/`) |
| hard cut, story turn | book close/snap (body) | `paper-hard-cut-book-close-01` (Wikimedia Commons, public domain, `sfx-fetch-0921`) |
| reveal / logo payoff | book-page-flip (body) | `paper-page-turn-01`, `paper-page-turn-02` (OpenGameArt CC0, `sfx-fetch-0921`) |
| rare, high-value beat only | tool dropped on desk (body) | `stinger-drop-tool-desk-01` (Wikimedia Commons, public domain, `sfx-fetch-0921`) — category spread gate: 2.1dB, over the 2dB ceiling (see report); kept because it is a real physical source, not a banned pack |
| repeated UI-adjacent tick (use sparingly — density rule caps this) | retractable pen click (body) | `tick-pen-click-01` (Wikimedia Commons, public domain, `sfx-fetch-0921`) — category spread gate: 3.0dB, over the 2dB ceiling (RMS-match undershoot on a short transient in silence, a known `sfx_prep.py` limiter ceiling; see report) |
| ambience | quiet library room tone (bed) | `ambience-quiet-room-01` (Wikimedia Commons, **CC BY 3.0** — `attribution_text` carries the credit line verbatim, `sfx-fetch-0921`) |
| scissors snip | scissors on paper (body) | `paper-scissors-snip-02` (OpenGameArt CC0, `sfx-fetch-0921`) |
| card slide on a table | card-on-table slide/cut (body) | `paper-card-slide-01`, `paper-card-slide-02` (OpenGameArt CC0, `sfx-fetch-0921`) |
| tape pull | sticky tape pull (body) | `paper-tape-pull-01` (Wikimedia Commons, public domain, `sfx-fetch-0921`) |
| pencil scribble | pencil writing/scribble (body) | `paper-pencil-scribble-01` (Wikimedia Commons, public domain, `sfx-fetch-0921`) |
| quiet room tone | see ambience row above | `ambience-quiet-room-01` |

An EMPTY row means: the agent places no `sfx()` call for that action rather
than reach for a banned pack. Kenney stays fully allowed for `kinetic-type`
below — it is only banned as a *physical-world* stand-in in `paper-punch`.
Machine count of `paper-punch` slots resolving to a banned pack after this
edit: **0** (gate in `sfx-fix-2026-09-21.md`).

**Banned in this style:** bright synthetic UI blips as the primary sound for
an action (the six current `nj-style-film` generated files fail this test
directly); anything whose `brightness` in `sfx-analysis.json` reads "bright"
used as a repeated/dense cue (fatigue, see `sfx-analysis.md`'s own rule).

## kinetic-type

Text-driven, no physical set — motion graphics register (word slides in,
snaps to place, punches out). Sound world is **clean and UI-adjacent but
matched, not raw**: the existing bundled Kenney `interface/`+`ui/` families
already fit (`sfx-analysis.md` calls these "low HF risk" — the safest
general picks table there is directly usable), run through `sfx_prep.py` so
they sit at the category levels in `sfx-practice.md` instead of their raw
Kenney gain.

| action | layer(s) | seed source |
|---|---|---|
| word lands | click/tick (low-risk per `sfx-analysis.md`) | `tick-click_*`, `tick-click1..4` |
| hard transition | impactSoft (low/medium HF risk) | `impact-impactsoft_*` |
| reveal | impactBell (medium risk, used sparingly) | `stinger-impactbell_heavy_*` |

**Banned in this style:** anything tagged `highFrequencyRisk: high` in
`sfx-analysis.json` used as a repeated cue (`casino/`, most of `ui/` — see
that file's family summary: `ui/` is 32/48 high-risk).

## Adding a new palette

1. Name the style, one line, from the same source the visual style itself
   came from (a reference reel, `brand/DESIGN.md`, a `PROJECT.md`).
2. List the action → layer → seed-source table above; every seed-source id
   must resolve via `library.py find --alias <old-id>` against `%NJ_LIBRARY%/INDEX.json`
   (post-cutover 2026-09-21 — the old seed id is kept as that record's alias, so no
   palette line above needs rewriting) — do not invent an id that has no file.
3. Name what's banned, specifically (a tag, a brightness value, a category),
   not "avoid bad sounds".
