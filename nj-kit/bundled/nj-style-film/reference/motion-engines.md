# Motion engines — which one draws a scene

Source: a four-row table the owner brought on 2026-09-21 (Theatre.js, Remotion + Tailwind,
GSAP + SVG, Manim). Each was judged against the standing rules: free besides Claude
tokens, runs on the CPU-only laptop, fits the HyperFrames pipeline, costs no extra
stage. **Revision, same day:** the owner asked for all four by name after Theatre.js and
Remotion were written up as "out" — both reversed below to "in", each with the
limits and the when-not-to-use line that verdict earns.

**The default does not change:** a scene is HTML + GSAP inside the one
`index.html`. An engine is chosen per scene, at the storyboard, by putting a tag
at the start of the scene's `Visual Description` field — `[engine: svg]`,
`[engine: manim]`, `[engine: theatre]`, `[engine: remotion]`. No tag means the
default. The tag is the only place the choice is made; nothing is switched
during the build. Most films need none of the four.

| engine | verdict | use it when the scene is | cost |
| --- | --- | --- | --- |
| HTML + GSAP | default | kinetic type, UI frames, cards, counters | none |
| GSAP + SVG | **in — already installed** | a logo intro, a vector icon that draws or morphs, a path the eye follows | one extra skill read |
| Manim | **in — installed 2026-09-21** | a diagram that explains: node graphs, flows, axes, a structure that builds itself | one pre-render per scene |
| Theatre.js | **in — smoke-tested 2026-09-21** | a hand-curved move too fiddly to keyframe by number (a bespoke ease on one hero element) | one authoring pass outside the build, in-page at render, no pre-render |
| Remotion + Tailwind | **in — smoke-tested 2026-09-21, licence confirmed 2026-09-21** | a data-driven template scene: same layout, many rows (a stat card per number, a name card per person) | one pre-render per scene, npm install once per project (~267 pkgs, 37 s measured) |

## `[engine: svg]` — GSAP + SVG

GSAP is HyperFrames' default runtime and has been free in full, plugins included
(DrawSVG, MorphSVG, MotionPath), since 2025. Nothing to install.

- Read `hyperframes-keyframes` for the scene — it owns SVG draw, morph, paths and
  masks. Allowed under `normal` and `best`; under `cheap` draw the mark with CSS
  and skip the tag.
- The SVG is inline in `index.html`, one element per part, so timing addresses
  parts and a redraw never touches the timeline.
- Text inside an SVG is converted to outlines only for a logo. Arabic words stay
  HTML text over the SVG: the visual gate checks HTML text for face coverage and
  cannot see inside a path.

## `[engine: manim]` — Manim Community

What it buys: you write relations (`next_to`, `arrange`, `Arrow(a.get_right(), …)`)
and it places the elements, so a twelve-node diagram does not cost twelve hand-set
coordinates. It renders a clip; HyperFrames still owns the film.

Measured on this machine (i5-1334U, no GPU), 2026-09-21: install
`uv tool install manim --with fonttools` 12 s; a 2.5 s scene at 1920×1080, 60 fps,
transparent VP9 WebM rendered in **18 s**. Version 0.21.0, MIT, no LaTeX needed
unless the scene sets mathematics. `--with fonttools` is not optional: the
template's font-loading step imports `fontTools` directly (devil #7 — the
first manim scene on reel 2 hit `ModuleNotFoundError` because the install line
and the template were never reconciled). Run this once, before stage 0, and
log it: `python <SKILL_DIR>/scripts/gate.py <project> engines` writes a
`GO engines` row to `STAGES.log` with elapsed time, the same ledger a numbered
stage uses — so the pre-stage's real cost (327 s / 70% of the gated run on
reel 2) is a grep, not a guess.

1. Copy `templates/manim_scene.py` to `<project>/manim/scene_<n>.py`, replace the body.
   Font files load straight from `<repo>/brand/fonts/thmanyah/otf/*.otf` — tracked
   in the repo since 2026-09-21 (the owner's personal grant from the typeface's
   project manager, `brand/fonts/thmanyah/README.md`). **No WOFF2→TTF conversion
   step**: Pango reads the OTF directly. The grant is personal to the owner — these
   font files are never copied into anything published for others to reuse.
2. Render, one command per scene, duration equal to the scene window in CUES.md:
   ```bash
   PYTHONUTF8=1 manim render -qh -t --format webm --disable_caching scene_<n>.py Scene<n>
   ```
3. Copy the WebM into `hf/assets/` and place it as a framework-owned video clip
   per `hyperframes-core`. `ffprobe` it first: duration, 1920×1080, `alpha_mode=1`.

**Four faults the first run hit — the template guards all four:**

- **A weight with no registered file falls back to a system face, silently.** Only
  the Bold TTF was registered; text asking for the regular weight came out in a
  different Arabic face with no warning. The template's `WEIGHT` names the weight
  of the file it registers; a second weight means converting and registering a
  second file. There is no machine check here that Pango used the house face —
  registration is asserted, use is judged by eye on the stage 5 sheet.

- **`Text()` drops Arabic words silently.** `Text("قرار")` produced zero glyphs and
  zero width with no error; `Text("بيانات")` was fine. Thmanyah shapes some letter
  pairs into one glyph and `Text` cannot reconcile the count. **Every string goes
  through `MarkupText`**, and the template's `word()` asserts width > 0 so a dropped
  word stops the render instead of shipping.
- **`arrange(RIGHT)` lays an Arabic flow out backwards.** A sequence read right to
  left is arranged with `LEFT`, and arrows run from `get_left()` to `get_right()`.
- **A transparent `.mov` does not play in Chrome.** Alpha is `--format webm` only.

Not verified: that HyperFrames' renderer keeps the WebM's alpha when it composites.
If the first film shows a black box, render the scene opaque instead — drop `-t`,
set `config.background_color` to the scene's background token — and place it full-frame.

Colours and sizes come from the project's STYLE-DNA, as they do for HTML scenes.
Manim's defaults (its blue, its red, its serif) are as generic as any template's.

## `[engine: theatre]` — Theatre.js, in-page

What it buys: a hand-curved hero move where the feel of the curve matters more
than its numbers. the owner is not required to touch it — **the agent authors the
move itself**, writing keyframes and easing straight into the state JSON — but
he may open the page afterwards to scrub and nudge it if he wants to.
HyperFrames has no Theatre.js adapter (its seven are GSAP, Lottie, Three.js,
Anime.js, CSS, WAAPI, TypeGPU) — this is not adapter work, it is one more clip
driven by a second library instead of GSAP alone. **Choose it over GSAP only**
for that one hero move; everything else stays GSAP.

**Licence, checked on npm 2026-09-21:** `@theatre/core` is `Apache-2.0` — free,
no threshold. `@theatre/studio` is `AGPL-3.0-only` (npm registry, both packages
at version 0.7.2, retrieved 2026-09-21). AGPL matters when a program is
*distributed*; Studio runs only on the owner's own machine and never ships — its
output (a state JSON) is a data file, not a derivative program. Keep Studio out
of the skill zip and out of `hf/` all the same: **`@theatre/core` only ships
in the render.**

**Authoring is agent-first, Studio is an optional second look:**
1. The agent writes `<project>/theatre_state.json` directly (position, value,
   `handles` per keyframe — the shape `templates/theatre_scene.html` reads).
2. The film loads `templates/theatre_scene.html` (**core only**) with that
   JSON, inlined. Position is driven from the film's own GSAP timeline via a
   proxy tween (`ease: "none"`, `onUpdate` posts the position across) — seek-
   safe and deterministic, no ticker, no independent clock inside the iframe.
3. **Optional, after delivery:** open `templates/theatre_author.html` in a
   browser. It plays the same move with Studio's panel around it — drag a
   point on the curve to change it, then press **Export project state** (top
   left); the file it saves replaces `<project>/theatre_state.json`. If
   the owner never opens it, nothing is lost; the delivered film already has the
   agent's version. Opening it and changing nothing costs one re-render, not
   two.

**Honest limit:** the state-JSON shape above was read from the bundled source,
never from a real Studio export. The first time the owner exports a changed file,
compare its `sheetsById` and `sequence.length` keys once against what the
agent wrote, before trusting the diff.

**Both packages need bundling for the browser**: their npm builds are
CommonJS, so `import {getProject}` fails against the raw `dist/index.js` (`does
not provide an export named 'getProject'`) — bundle each with
`npx esbuild <pkg>/dist/index.js --bundle --format=esm --outfile=theatre-*.local.js`
once per project, then import the **default export** (`import core from
"./theatre-core.local.js"`), not a named one.

**Smoke test measured 2026-09-21** (`<tools>\engine-smoke\theatre_smoke_test.mjs`,
Playwright from the CLI, `@theatre/core` 0.7.2, served over a throwaway local
HTTP server — `file://` blocks ES-module CORS and blocks `fetch()` of the
state JSON, so a real project's authoring/film pages need a local server or an
inlined/bundled state, never a bare `file://` open):
```
ASSERT theatre smoke: position=0 -> x=0, position=1 -> x=400, differ=true, matches keyframes(0,400)=true
```
**Fault hit and worked around:** the loaded sheet's `sequence.length` did not
reflect the state JSON's declared `"length"` value — seeking by a 0..1
fraction of `sequence.length` landed halfway between keyframes instead of on
the end one. Fixed by driving `sheet.sequence.position` in the sheet's own
raw units (matching the keyframes' `position` numbers) and passing the real
scene duration in from outside (a `?duration=` param / the storyboard's scene
window), never trusting `sequence.length` to carry it. `theatre_scene.html`
implements this.

**When NOT to use it:** any scene a storyboard note can describe in words
(arrange, draw, morph, count) — those cost nothing extra in GSAP or SVG. Not
for a whole film: one authoring pass per tagged scene, not a project-wide
timeline.

## `[engine: remotion]` — Remotion + Tailwind, pre-render

What it buys: same layout, many rows — Remotion is a React component fed
`props.json`, so ten stat cards or ten name cards are ten renders of one
component, not ten hand-built scenes. Same pre-render → alpha WebM → `ffprobe`
→ `hf/assets/` contract Manim uses.

**Licence, checked 2026-09-21** (`https://github.com/remotion-dev/remotion/blob/main/LICENSE.md`):
free for an individual, a non-profit, a company still evaluating it, or **"a
for-profit organization with up to 3 employees"**; a for-profit organisation
past 3 employees needs a paid Company Licence. **Licence confirmed by the owner
2026-09-21: Ensera is 2 people, permanently — under the threshold.** Re-check
the licence if headcount ever passes 3.

**Tailwind**: `@remotion/tailwind-v4` (MIT, npm 2026-09-21, matches the
installed `remotion@4.0.526`) via
`Config.overrideWebpackConfig((c) => enableTailwind(c))` in `remotion.config.ts`
— confirmed against `remotion.dev/docs/tailwind-v4/overview`; do not use the
v3 `enableTailwind` bundler-config API, it is a different page for a different
major version.

**Alpha WebM**: `--codec=vp8 --pixel-format=yuva420p --image-format=png`
(`remotion.dev/docs/transparent-videos`; `vp9` also carries alpha, `vp8` is
what the docs lead with). Documented limitation, not hit here: chunk-boundary
flicker is possible because VP8/VP9 alpha can depend on previous frames.

**Smoke test measured 2026-09-21** (`<tools>\engine-smoke\remotion-smoke\`,
one Arabic string `"قرار"` in the house Thmanyah Bold WOFF2, 2 s composition,
1920×1080):
- `npm install`: 267 packages, 37 s, `node_modules` size and the render's
  `ffprobe` line are in `artifacts/ops/film-engines-2026-09-21.md` (measured
  after the render finished; not repeated here to avoid two numbers drifting).
- House face loaded directly from a local WOFF2 `@font-face` — unlike Manim,
  Chrome (Remotion's renderer) reads WOFF2 natively, no `fonttools` decompress
  step needed.

**When NOT to use it:** a one-off scene with no repeating row structure — the
267-package install and a whole npm project is a bigger cost than drawing it
in HTML. Never the film's default template, never a port of the existing
`templates/film.html`. Remotion Lambda / Cloud Run are cloud, paid, and out of
scope — this is the local-render path only.
