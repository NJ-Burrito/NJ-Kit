# HyperFrames: what fails a first build

Not the contract — that is `hyperframes-core`. This is the subset that actually
cost a lint or a check on the first run, plus the patterns that passed.

**Version stamp: HyperFrames CLI 0.8.58, GSAP 3.15.0, ffmpeg 8, updated
2026-09-21 (rehearsal-0921; was CLI 0.8.48 / GSAP 3.14.2 — confirmed nothing
below needed a change for either point release: the skeleton, lint names, and
GSAP seek-safe patterns all still held on this rehearsal's real build).** If
`npx hyperframes --version` says otherwise and anything here disagrees with
`hyperframes-core`, `hyperframes-core` wins; fix this file after.

## Skeleton that passes

```html
<div id="root" data-composition-id="main" data-start="0" data-duration="52.01"
     data-width="1080" data-height="1920">
  <div id="cam" class="clip" data-start="0" data-duration="52.01" data-track-index="1">
    <section id="s1" class="clip scene" data-start="2.6" data-duration="3.57" data-track-index="2">…</section>
  </div>
  <audio id="vo" src="assets/voice.m4a" data-start="0" data-duration="52.01"
         data-track-index="10" data-volume="1"></audio>
</div>
<script>
  // The page must define this before it is called from a tween, or the build
  // fails with "sfx is not defined" (devil #11). The mix (voice+bed+SFX) is
  // ONE <audio> — this stub is a marker for scripts/mix.py to read, not a
  // second playback path.
  function sfx(t, name) {}
  const tl = gsap.timeline({ paused: true });
  /* …all tweens… */
  window.__timelines["main"] = tl;   // LAST, key = data-composition-id
  tl.seek(0);
</script>
```

`#root` is `width:100%;height:100%` — canvas size is `data-width`/`data-height`.
Root `data-duration` is the render length; set it to the audio's duration.

## Errors hit, and the fix

| finding | cause | fix |
| --- | --- | --- |
| `template_literal_selector` (error) | `` document.querySelectorAll(`${host} .num`) `` | pass a NodeList in from a hardcoded string selector |
| `content_overlap` (error) | a word drawn twice on purpose (torn halves) | `data-layout-allow-overlap` on both spans |
| `content_overlap` (error) | a tab sitting on a hero word | move it; hero boxes are taller than their glyphs at `line-height: .9` |
| `panel_out_of_canvas` (warning) | full-bleed ground plane wider than the canvas | `data-layout-allow-overflow` |
| contrast fail | white text on a mid-tone accent box | ink on light accents, white only on dark ones; decide in the DNA |
| `font_family_without_font_face` | a named family with no local `@font-face` | `@font-face` to a file in `assets/`, woff2 |
| silent render | `<audio>` with no `id` | every `<audio>` has an `id` |
| `video_nested_in_timed_element` (error) | an engine clip (Manim/Remotion WebM) placed as a `<video>` INSIDE its own timed `<section class="clip scene">` | the video is a sibling `.clip` at the same track level, not a child, of the scene it plays under |
| `sfx is not defined` (error) | `sfx(12.3, "swish")` called in a tween before the page defines the function | the skeleton above declares `function sfx(){}` before any timeline code runs |
| `html_dir_attribute_breaks_render` (error, rehearsal-0921) | `<html dir="rtl">` for an Arabic film | remove `dir` from `<html>`; put `direction: rtl` on `#root` (or any text container) instead — bidi still shapes correctly |
| `hero_boxes.mjs` times out on `window.__timelines` (rehearsal-0921) | it opens the built page via a bare `file://` URL, bypassing the HyperFrames dev server/render runtime that would otherwise create `window.__timelines` | the page's own script must declare `window.__timelines = window.__timelines || {}` before first use — harmless under a real render, required for any headless tool that opens the file directly |
| `hero_boxes.mjs` throws `CSS is not defined` (rehearsal-0921, fixed in the script) | `` `#${CSS.escape(scene.id)}` `` runs in hero_boxes.mjs's own Node process, not the page — `CSS` is a browser global | use the id directly (`` `#${scene.id}` ``): HyperFrames ids are already restricted to `[\w-]`, no escaping needed |
| entrance/exit gate flagged `#root`/`#cam` themselves (rehearsal-0921, fixed in `gate.py`) | `check_entrances_exits`'s regex scanned the WHOLE page; the contract skeleton's own `#root`/`#cam` carry `id`+`data-start` too, and neither is ever choreographed | `gate.py` now scopes the scan to each `<section class="...scene...">`'s own inner HTML |
| the id-attribute regex matched `data-composition-id="main"` as `id="main"` (rehearsal-0921, fixed in `gate.py`) | `\bid="..."` treats the boundary before `-id=` as a word boundary too, since `-` is a non-word char | use `(?<![\w-])id="..."` (negative lookbehind for a word char OR hyphen) everywhere an id attribute is matched by regex |
| `bed_pick.py --commit <id>` looked like it staged the file (rehearsal-0921) | it only appends to its own `history.json` rotation record — no file copy | `ffmpeg -i <picked-file> <project>/hf/assets/bed.wav` yourself; that is the one extra path `mix.py` resolves besides beside-itself |
| `mix.py` crashed `sfx id 'SFX-000004' not in bg-music manifest and not a legacy name` (rehearsal-0921, fixed in `mix.py`) | `load_seed_manifest()` only read the pre-cutover `bg-music/assets/sfx-seed/manifest.json`; library-cutover-0921 moved SFX rows into `%NJ_LIBRARY%/INDEX.json` and nothing merged the two | `mix.py` now also loads `%NJ_LIBRARY%/INDEX.json`'s `kind==sfx` rows (id/category/lufs_out/path, plus aliases), tagged with which root their `path` is relative to |
| `sfx_check.py --manifest` still only reads the pre-cutover seed manifest (rehearsal-0921, NOT fixed — bg-music is not owned here) | same cutover gap as above, in a file this skill does not own | build a rows file yourself: `[{"id":r["id"],"category":r["category"],"lufs_out":r["measured"]["lufs_out"]} for r in INDEX.json if r["kind"]=="sfx"]`, pass it as `--manifest`; NEXT ACTION for bg-music's owner is to do this natively |
| `mix.py <index.html>` failed `narration.wav: No such file` even though it existed in the project (rehearsal-0921) | `mix.py` reads/writes `narration.wav`/`bed.wav` beside ITS OWN file (`HERE`), not the caller's cwd or the project — running it from the shared skill dir looks for the file there | copy `mix.py` into the project first, exactly like `voice.py`/`words.py`, and run it from there — SKILL.md's Sound row said "run mix.py" but never said to copy it; fixed |
| cool palette's `ground-warm` (coral, `#FF6B6B`) used as HERO TEXT colour on a cream ground (rehearsal-0921, judgement not code) | style.json's own contrast table only certifies coral as a GROUND with ink text on it (6.08:1) — coral was never meant to be text | hero word colour: ink on a cream/light scene, `amber` (`#F5C451`, 10.37:1) on a dark/navy scene — never coral as text |
| cool palette's ground-warm at high frame share reads as an error/warning colour (rehearsal-0921, judgement, unresolved) | style.json's own note: "coral is declared 'data series 4 / negative'... at the reference's 70% ground share it reads as the error colour" | for `palette: cool`, keep coral's ground share low (an accent, not the dominant background) or use `palette: warm` (petra) instead — the owner's call, not this skill's to make silently |
| `ASSET-PLAN.md` failed `plan-check` for no visible reason (rehearsal-0921) | `plan-check` needs a `visual_era: <value>` header line (e.g. `modern / near-future`) before its scene lines, else it WARNs every record `unknown`-vs-declared instead of checking era at all; its scene-line shape is `- scene: <label> \| id: <manifest id> \| claim: yes\|no \| relevance: literal\|associative\|decorative \| reason: <clause>` — NOT the free-text `id: reason` shape `gate.py`'s own hand-check fallback uses (that fallback only runs when `library.py` is absent) | write both exactly as `plan-check` expects; SKILL.md's Material section said neither before this rehearsal |
| stage 4's build gate failed `material_needs[] ... ASSETS.txt names no manifest id` although `ASSET-PLAN.md` was filled and passed `plan-check` (rehearsal-0921) | `gate.py`'s `check_material` reads a SEPARATE file, `<project>/ASSETS.txt` (one manifest id per line) — not `ASSET-PLAN.md` — to confirm `style.json`'s `material_needs[]` was answered | write `ASSETS.txt` too; SKILL.md never named it before this rehearsal |
| a hero cutout's tone-to-palette filter (`toneCool`) alone did not clear the 15-luminance hero/ground separation on a second scene, even after `contrast()`/`brightness()` CSS filter boosts (rehearsal-0921, SKIPPED after 2 fix attempts — content judgement, not code) | the source photograph's own midtones sit close to its ground's luminance; a duotone table map plus a flat CSS `contrast()`/`brightness()` push moved the separation 5.7 → 11.1 → 10.9 (plateaued, second attempt did not clearly improve on the first) | next attempt: a solid-colour card/backing panel behind the hero before toning (not just a filter on the photo), or pick a cutout with more built-in tonal range for that scene's hero role |

Accepted warnings under a one-file build: `composition_file_too_large`,
`timeline_track_too_dense`, `nested_structure_needs_subcomposition`,
`duplicate_media_discovery_risk` (same image used in two scenes).

## GSAP patterns that are seek-safe

- **A `fromTo` renders its FROM state when it is created.** Good for "hidden until
  it pops" (`scale: 0`). Bad for anything on a shared element: a camera
  `fromTo({rotation:-2}…)` at 2.6 s tilts the film from 0 s. Add
  `immediateRender: false`, or use `to`.
- Never a CSS `transform` on an element GSAP also transforms. Position with
  `left/top` px; set initial transforms inside the tween.
- Never tween `visibility`/`autoAlpha`/`display` on a `.clip`. Tween a child.
- No `repeat: -1`. `repeat: Math.max(0, Math.floor(dur / cycle) - 1)`.
- Text that changes (a counter) is a STACK of elements shown one at a time with
  `tl.set(el, {opacity:1}, t)` / `{opacity:0}` — a `textContent` change is not seekable.
- Draw-on strokes: set `strokeDasharray`/`strokeDashoffset`, tween the offset to 0.
- Stop-motion feel: `ease: "steps(n)"`.
- No `Date.now()`, no unseeded `Math.random()`; an SVG `feTurbulence` needs a fixed `seed`.
- `<use href="#symbol">` is fine for shared drawings, but you cannot tween inside
  it. Anything animated per-part is built inline.

## Commands, in the order they are used

```bash
npx hyperframes init hf --non-interactive --example=blank --skill=general-video
npx hyperframes lint                 # fast, after the first HTML pass
npx hyperframes check                # the gate: lint + layout + motion + contrast
npx hyperframes snapshot --at 2.2,4.8,8.9   # writes contact-sheet-N.jpg — read THOSE
npx hyperframes render --output ../film.mp4
```

A lint ERROR switches the layout and contrast audits off: `0 samples` after a
lint error means nothing ran, not that nothing is wrong.
