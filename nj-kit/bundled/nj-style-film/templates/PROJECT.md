# PROJECT — fill this once per film

Copied into every project by `nj-style-film`, stage 0. Write the value after the
colon. Leave a line empty if you have nothing: REQUIRED slots will be asked for,
every other slot falls back to what its `fallback:` line says, and the film says
so in its delivery note. `scripts/intake_check.py` reads the `key: value` lines,
so keep the keys as they are. **Every path in this file is relative to this
file's own folder** (`intake_check.py`'s `base = dirname(PROJECT.md)`), not to
the repo root — a repo-root path needs `../../` from a `production/<project>/` file.

## 1. Cut-outs — the look lives here
An id list or a folder. `%NJ_LIBRARY%/` (post-cutover; was `production/library/`) is the default source: cited by
manifest id (`ASSETS.txt`), never fetched or hot-linked. DRAWN is the fallback
only when the library has no candidate for a kind the style's `material_needs[]`
calls for — name the shortfall, do not draw silently (devil #1).

cutouts_dir: ../library
fallback: every prop is DRAWN in the style's shape language, one element each, swappable later — and named under '## Fallbacks used'

## 2. Source — REQUIRED
The exact file. Never "the latest" or "the one before": a path.

narration_audio:
narration_srt:
fallback_srt: transcribe the audio once with `npx hyperframes transcribe`
language:

## 3. Format — REQUIRED
platform:
aspect:
length_seconds:

## 4. Style reference — REQUIRED (at least one line)
Local files beat links. Stills beat video. Two lines on what you like beat both.
Named a recorded style (`production/styles/<name>/`)? Put its name here — the
gate reads it to find that style's `material_needs[]`.

style:
reference_stills:
reference_video:
what_i_like:
what_to_avoid:

## 5. Product or subject captures
Shot for THIS frame: the aspect above, the theme named in house rules, the
exact screens the narration names.

captures_dir:
fallback: reuse the nearest existing captures, scaled, and say which

## 6. Brand kit
fonts_dir:
palette:
logo:
end_card_lines:
fallback: fonts and palette from the project's own design tokens; end card carries the narration's last line only

## 7. House rules for this film
One per line. These outrank the reference where they collide.

rules:
onscreen_words: spoken-only
fallback_rules: on-screen words are spoken words only; no warnings or errors invented in frame
captions:
fallback_captions: kinetic — on-picture motion-graphic words carry the spoken line; a plain subtitle strip is a SECOND system and is forbidden alongside it. Set "subtitle" only for a talking-head or footage-led piece with no kinetic words in the picture.

## 7b. Finish — house defaults since 20 Sept 2026; change a value only when asked
film_kind: commercial
aspects:
fallback_aspects: commercial = 9x16 AND 16x9 from one film.html; feature short (about 20 s) = 16x9 only
narration_scope:
fallback_scope: the WHOLE product, read as a new user meets it; one feature only when the user names it
kind:
fallback_kind: product-explainer (see bg-music/reference/music-beds.md for the full list)
theme:
fallback_theme: none — bed_pick.py uses `kind` alone
music: auto
fallback_music: auto = bed_pick.py chooses by kind/theme; generated = scripts/bed.py as before; a track id (e.g. `informational/code_box--Tropicorp-Advertisement.mp3`) pins one file
sfx: on
line_gap_seconds: 0.35

## 8. Run shape
budget:
approve:
fallback_budget: normal
fallback_approve: ask

`budget` is `cheap`, `normal` or `best`. `approve` is `ask` (stop after the
storyboard for notes) or `auto` (build as written).

## 9. One-time unlocks on this machine (tick what is true)
Each one removes a failure the first run hit. None is required.

heygen_signed_in:
groq_key:
gemini_key:
fallback: image search off -> slot 1's fallback; no transcript key -> SRT required; no describe key -> contact sheets are read by the agent

## 10. Engines (optional)
engines:
fallback: none — no engine installs run; only tags PROJECT.md names here get a pre-stage install

## Storyboard notes
Filled by you at the stage 3 gate. "go" with nothing here builds it as written.

notes:

## Fallbacks used
Filled by the agent, one line per fallback taken, so the delivery note is honest.

## Parked
Requests that arrived mid-film and are not the film. Done after delivery.
