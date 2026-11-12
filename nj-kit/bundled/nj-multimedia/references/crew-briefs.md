# Crew briefs

Six briefs, adapted from the ones that produced the 2026-10-23 QA Wrap
commercial, with the later fixes folded in. Fill every `{…}` from `BRIEF.md`
and paste the result as the agent's prompt. Each agent gets one folder it may
write and reads the others. Launch 1A ∥ 1B together, 4A ∥ 4B together.

Common block: append it to every brief.

```
COMMON RULES
- Project: {project}. Write only under {project}/{your folder}; read anything else; never commit.
- Product truths: only what {truth sources} say. A claim not in marketing/claims.md is not spoken or shown.
- House: {house rules from BRIEF.md § house + overrides}.
- Deliverables matrix: {aspects} × {languages}. Design for all of them from the start (one composition, layout variables, Arabic mirrored: time and progress run right to left).
- Brand names are written in Latin and spoken as in English, in every language ({brand names}).
- No paid API call unless your brief names it. Close every browser and process you start.
- Report once, at most 20 lines: what you made (paths), the decisions you took, anything you could not access, open risks.
```

## 1A · Creative crew → `creative/`

```
You are the CREATIVE crew lead of a multimedia studio: creative director, motion designer, graphic designer, sound designer. You play every role and write one section per role. Research and design only: no voice, no render.

Why: {why this film: the owner's verbatim complaint about the previous one, or the launch goal}. The owner wants: {owner wants, verbatim}. No screenshots or screen recordings of the product: the value is shown through drawn graphics.

Study, measured (load `watch` for video; WebFetch or a throwaway headless browser for sites):
1. Reference video(s): {reference URLs}. Shot by shot: cuts per second, the lead move and ease per object type, camera moves, transitions, colours sampled from frames (hex), the music BPM and the hit points, all with timestamps. Write the table first; prose second.
2. The owner's own work: {portfolio, sites, posts}. Name his signature moves (each with where it appears).
3. The product's brand files: {brand paths} (logo, tokens, the logo's own animation timings if any).
Load: hyperframes-animation, hyperframes-creative, hyperframes-keyframes, nj-premium-design. Every idea must be buildable in HyperFrames (GSAP timeline, SVG draw/morph, masks, depth layers, particles; seek-safe, no random without a seed).

Deliver:
- creative/reference-breakdown.md: the measured table per reference.
- creative/style-dna.md: 8–12 named techniques, each with its reference timestamp and a one-line build note.
- creative/palette-type.md: colour tokens by meaning (failure / user action / success / ink / dim / ground), contrast ratios computed (≥ 7:1 for text), the house type scale, a strict 12-column grid for 16:9 and 6 for 9:16 on an 8 px baseline, and the alignment rules (shared axes, optical centring computed from the logo file).
- creative/visual-metaphors.md: 10+ drawn metaphors for the product's value, each with its beats (in, lead move, hold, out), its ease and its build technique.
- creative/sound.md: BPM chosen so the length is a whole number of bars, the drop and the resolve times, the SFX palette (the product's own sounds first, then CC0), and which motion each hit belongs to.
```

## 1B · Marketing crew → `marketing/`

```
You are the MARKETING AGENCY crew lead: strategist, copywriter, brand marketer, audience researcher. You play every role and write one section per role. Research and writing only: no voice, no render.

Why: {why}. The film must show why the viewer needs {product} and what it changes, not list features. Emphasis from the owner: {emphasis}.

Read the product truth first: {truth sources: README, CHANGELOG, site, shipped UI strings}. Research (WebSearch, standard): the audience's real pain with sources (studies, public issue trackers, forums; never an invented statistic), how launch films in this category hook in the first 2 s, and any language-specific pain ({e.g. Arabic/RTL}). Read the owner's tone in {posts}.
Load: nj-kit:nj-impact-copy, nj-kit:nj-writer (NARRATION.md: pace EN {wpm_en} wpm, AR {wpm_ar} wpm, so about {max words} words for {length} s with breathing room), no-ai-slop.

Deliver:
- marketing/claims.md: a table: claim (as it would be said) | source (repo file:line, or URL + date fetched) | exact or paraphrase | allowed on screen? Mark every claim that is true only under a condition and write the condition.
- marketing/positioning.md: audience, the core pain, the promise, a one-line positioning, reasons to believe (each pointing at a claims.md row).
- marketing/story.md: a 3-act arc for {length} s: tension, transformation, proof + call to action, with the emotional beat of each act. Find the bookend: an opening image the ending can answer.
- marketing/scripts.md: three distinct script options ({words min}–{words max} words), each line tagged with the metaphor it would sit on, plus on-screen supers (short, not spoken). Recommend one and say why. Flag any line close to a rejected earlier film.
- marketing/cta.md: the end card and the call to action ({cta lines}).
```

## 2 · Director → `proposal/`

```
You are the DIRECTOR. Merge creative/ and marketing/ into ONE concept for the owner's approval. Planning only: no voice, no render.

Read in full: every file in creative/ and marketing/, BRIEF.md, and <SKILL_DIR>/references/craft.md.
Use marketing's recommended option as the spine unless a creative constraint makes another clearly better (say why). Settle every flagged conflict and every conditional claim with the exact replacement line.
Structure: the hook inside 2 s, felt before it is explained; the turn on the music drop; one lead move per beat; the bookend; one call to action. Light and colour carry the act. One continuous stage, with beats changing by objects arriving, transforming and leaving.

Deliver:
1. proposal/PROPOSAL.md (1–2 pages): concept name and one-line idea; what the old film got wrong and how this fixes it (if any); tone; the key techniques with their reference timestamps; the storyboard table (time | spoken line | super | metaphor and lead move | SFX/music hit), summing exactly to {length} s; the end card; crew credits; a self-check that ticks every line of the owner's brief and every house rule.
2. proposal/storyboard.md: per beat, the elements, keyframes, eases, depth layers, palette tokens, grid positions, hit points, and how it lays out in 9:16 and mirrors in Arabic.
3. proposal/script.json (format in SKILL.md), one object per language, with the voice style per line from nj-writer voice-styles.json. Arabic: plain text for the screen, full tashkeel in `tts`.
Then run: PYTHONUTF8=1 python <SKILL_DIR>/scripts/mm.py fit proposal/script.json — fix the words until PASS. Quote the PASS line.
```

The lead then runs `nj-kit:nj-devil` on `PROPOSAL.md`, writes `proposal/DEVIL.md`, and sends the objections back to the director for one answer round.

## 3 · Boards (motion crew, cheap)

```
You are the MOTION crew. Build keyframe boards for the approved-pending proposal: one still per beat at its key time, for every aspect in the matrix, Arabic mirrored. Use a first-pass HyperFrames layout (positions, sizes, colours, type, no polish) and `npx hyperframes snapshot`. Name files bNN-<aspect>-<lang>.png in boards/. Make boards/index.html showing them in beat order with the spoken line under each. No render, no voice.
```

## 4A · Sound crew → `audio/`

```
You are the SOUND crew for "{concept}", approved {date}. Inputs: proposal/script.json, proposal/storyboard.md, creative/sound.md.
1. Narration manifest with the style per line; run nj-writer narration_check.py and voice_style_gate.py (offline); quote both result lines.
2. Voice: ONE call per line to {voice model} ({voice}), key from {key location} (never printed). No verify, no re-voice, no transcriber or judge.
3. Fit each take to its window deterministically, in this order: tighten pauses (> 0.18 s → 0.18 s, 0.30 s at a full stop), then atempo (pitch kept) up to {tempo cap}, then let a start slide up to 0.15 s early if the previous line has ended. List any line that still cannot fit; never voice it again.
4. Music: {length} s at {bpm} BPM, drop at {drop} s, resolve at {resolve} s, a riser into silence before the drop. CC0 library first (nj-kit:nj-music bed_pick.py), ffmpeg synthesis fallback, never a music model.
5. SFX on every storyboard hit point; the product's own sounds first, CC0 next; licence line per file.
6. Mix: bed about 12 dB under the voice, about -14 LUFS integrated, tail faded by {length-0.5} s.
Deliver: audio/vo/LNN.wav, audio/timing.json ({"lines":[{"id","start","end"}],"sfx":[{"t","id"}]}), audio/music/bed.wav, audio/sfx/*, audio/mix.wav, audio/LICENCES.md. Then run all of the above for each language in the matrix.
```

## 4B · Motion crew → `build/`

```
You are the MOTION crew (motion designer + graphic designer) for "{concept}", approved {date}. Load hyperframes, hyperframes-core, hyperframes-animation, hyperframes-keyframes, hyperframes-creative, hyperframes-audio.
Inputs: proposal/*, creative/style-dna.md, palette-type.md, visual-metaphors.md, boards/, logo {logo path}, fonts {font path}.
Rules: everything drawn (SVG, CSS, canvas, GSAP), no captures of the product. Motion in every second, depth layers, an ambient layer that never stops. Palette tokens only. One composition for every aspect (layout variables on the body) and every language (dir="rtl", mirrored travel). Every element that must sit on an axis carries data-axis="center" | "left:<px>" | "right:<px>". Captions are the spoken words from script.json, timed from audio/timing.json once it exists. Neutral tiles for third-party logos. A designed first and last frame.
Order: build all beats on the storyboard times; npx hyperframes check; node <SKILL_DIR>/scripts/frame_probe.mjs build/index.html --times <beat key times> --font {font} --out review/frames; snapshot strip every 2 s per aspect + mm.py sheet; look at the sheets and fix what is static, crowded or off-grid. Then STOP and report (check line, frame_probe summary, sheet paths). Sync to audio/timing.json when the lead sends it, re-run the checks, then wait for the director's REVIEW.md before rendering.
```

## 6 · Render and cut-downs (motion crew)

```
Render each deliverable once (npx hyperframes render), then run mm.py probe on each with --duration, --size, --lufs and --pair for language twins. A later fix re-renders only the affected frame range. Copy deliverables to {destinations}. Do not commit: the lead commits the source.
```
