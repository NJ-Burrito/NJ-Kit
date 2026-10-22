# Vendored GSAP — local, never CDN

`gsap.min.js` here is the official npm `gsap` package, core build (no plugins
used by any recipe yet — the paper-punch fold recipes are plain CSS 3D
transforms + GSAP core tweens, no `MorphSVG`/`Draggable`/etc.).

- Fetched once, 2026-09-21, rehearsal-0921: `npm pack gsap` in scratch
  (`<tools>\rehearsal-film\scratch\`), file copied from
  `package/dist/gsap.min.js`.
- **Version installed: 3.15.0.** (`reference/hyperframes-contract.md`'s
  version stamp says 3.14.2 — that file is stale by one point release; not
  fixed here since GSAP 3.14→3.15 has no breaking change to the seek-safe
  patterns this skill uses. Update the stamp next time the contract file is
  touched.)
- **Licence: GSAP's standard licence** — free for this use including all
  plugins, since GSAP's 2025 licence change (Webflow acquisition). No per-seat
  or per-project fee applies to Ensera's use. Re-check only if GSAP's terms
  change again.

## Wiring

- `templates/film.html` and any built `hf/index.html` load
  `assets/gsap.min.js` (relative), never a CDN URL.
- The build step (stage 4, `npx hyperframes init` + hand-build) copies this
  file into `<project>/hf/assets/gsap.min.js` (and `hf-v/assets/`,
  `hf-h/assets/` for the two-aspect film) — same mechanism as any other
  vendored asset (fonts, mark.svg).
- Gate line (added to `SKILL.md` stage 4 and `scripts/gate.py`): a built page
  must resolve zero `http(s)://` URLs outside an HTML comment.
