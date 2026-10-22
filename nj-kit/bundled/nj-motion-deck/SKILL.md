---
name: nj-motion-deck
description: 'Animated slide decks with Remotion: references → triage → style pick → devil rounds → build. One motion clip per slide in an autoplay PPTX, plus a real-text PDF twin, Arabic RTL and English. Triggers: animated slides, motion deck, Remotion slides, remake this deck beautifully, عرض تقديمي متحرك.'
---

# Motion decks with Remotion

The method that produced the project QA deck and the KAC Recurrence Map deck v4
(24–25 Sept 2026). **the owner rated deck-v3's look −3/10** (2026-09-25) — an earlier
version of this file called that look "super beautiful and perfect"; it was wrong,
and the line is gone. **The look for any deck comes from that deck's own
`STYLE-DNA.md`, chosen in stage 2 below, never carried over from a previous deck's
components, palette or copy.** The reliability still comes from the gates in the
build pipeline; most of what makes a deck "ugly" is skipping one of them.

**Worked example (front stages + build):**
`<ENSERA-root>\artifacts\research\kac-sentinel\v4\` (refs/, board/,
devil/) and `delivery\kac-recurrence-map\deck-v4\` — read `v4/board/STYLE-DNA.md`
and `v4/devil/devilB.md` before touching a new deck's storyboard; they show what a
completed stage 2–6 pass looks like, not what to copy into the new deck.

## Stages 0–6: references to an approved storyboard

Run before the build pipeline. Each stage's checkpoint is a file the next stage
reads — do not carry a decision forward only in conversation.

| # | Stage | Checkpoint on disk | Gate |
|---|---|---|---|
| 0 | References | `refs/refs.jsonl` — **primary route: `nj-pinterest`** (headed browse on the owner's own signed-in profile, under his verbal HQ permission — read that skill first); fallback: the Pinterest API (`scripts/pinterest_search.py`) when `credentials/pinterest.env` holds `PINTEREST_TOKEN`; otherwise free public sources (Behance, design blogs, Are.na, etc.), read directly, never scraped through Laya | ≥40 rows, each with `url` + `description` |
| 1 | Triage | `refs/triage.json` — Laya first, `scripts/laya_ask.mjs`, scored against a 15-row hand-labelled subset | **accuracy ≥ 0.70 → keep Laya's buckets. Below 0.70 → `LAYA-VERDICT: TRASH`, re-triage the full set with Haiku** (`refs/triage-haiku.json`); report both numbers, never only the one that passed |
| 2 | Style pick | `refs/STYLES.md` — 3 candidate styles (grid, type, colour, motion grammar, transitions, chart language, image treatment, refs, fit, risk) + one recommendation, built from direct reads of the descriptions, never from a failed Laya bucketing | a human (or a devil round, see stage 6) can point at 2–3 refs per candidate and see why |
| 3 | Story + claims ledger | the script/words file (`script-en.md` or equivalent) + `claims-ledger.md`, one row per number on a slide with its source and status (verified / draft / our estimate / our design choice) | every number on a slide face traces to a ledger row |
| 4 | Devil A | `devil/devilA.md` — challenges the claims ledger against live sources, the story's load-bearing assumptions, and every planned image's licence and relevance | verdict line (`SHIP` / `SHIP-WITH-EDITS` / `REWORK`) + a numbered, mandatory edit list |
| 5 | Storyboard + styleframes | `board/STYLE-DNA.md` (the one page a builder reads before a slide) + `board/storyboard.md` (per-slide layout, text, motion, RTL) + 4 representative styleframe PNGs | STYLE-DNA cites `brand/tokens.json` for every colour/type value; styleframes pass `visual_gate.mjs` |
| 6 | Approval | the owner reviews the storyboard + styleframes ("rehearse, then approve" — `~/.claude/CLAUDE.md`), **unless he has explicitly delegated approval for this run** (e.g. asked for a finished result overnight while asleep) — then a second devil round (`devil/devilB.md`) stands in as the approval proxy, scored against the brief's own gates (theme/graphics/animation/flow/pitch/evidence/Arabic), with a mandatory fix list | the owner's go, or devilB's `BUILD-WITH-FIXES` / `REWORK` verdict, on file before stage 1 of the build pipeline below starts |

**Laya inside its envelope only.** Style-bucket triage is an 8-option classification
over free-text descriptions — read `nj-laya/SKILL.md`'s decision table first. It is
right at the edge of Laya's ADOPT-NARROW envelope (≤10 options); measured on kacs-v4
(2026-09-25) it scored 0.40 on 15 hand-labelled refs, so it failed its own gate and
the ECONOMY tier did the full triage. That is the expected outcome, not a bug to chase — run the
Laya gate anyway each time, because a cheap check that fails fast is still cheaper
than skipping straight to the ECONOMY model on faith. Never let Laya's raw bucket assignment reach
a slide un-reviewed (nj-laya rule 2: suggest-only).

**Pinterest.** Primary route is `nj-pinterest` — a headed Playwright browse on
the owner's own signed-in profile, under his verbal, personal, non-transferable
permission from Pinterest HQ ("verbal, nothing in writing"). `scripts/pinterest_search.py`
+ `scripts/PINTEREST-SETUP.md` (the API route) still ship in this skill as the
second path: the owner registers the Pinterest app and drops the token himself
(`credentials/pinterest.env`, gitignored) — a worker or the Lead never creates the
account either way. Without either route available, stage 0 falls back to free
public sources; the API script exits 3 with that instruction rather than failing
silently.

## The build pipeline (stage 7 on): checkpoints are files

| # | Stage | Checkpoint on disk | Gate that must pass |
|---|---|---|---|
| 1 | Words | approved JSON (or `findings.json`) | words gate: the copy in the project is byte-identical to the source (`scripts/prep_data.py`) |
| 2 | Glyphs and colours | `gates.py` output | glyph gate (every typed char exists in the font), contrast gate (4.5:1, or 3:1 large) |
| 3 | Scenes | `remotion/src/*.tsx` | `npx tsc --noEmit` is clean |
| 4 | Stills | the last frame of 8–12 representative slides, tiled into one sheet | one look at the sheet, fix, then re-still only what changed |
| 5 | Clips | `clips/<ID>.mp4`, and `posters/<ID>.png` as the last frame | a render log with no `FAIL` |
| 6 | PDF twin | `out/<name>.pdf` | poppler: `pdfinfo` page count, `pdffonts` shows the house face embedded, `pdftotext` returns the words |
| 7 | PPTX | `out/<name>.pptx` | `postprocess-deck.ps1` prints "autoplay + fade on N of N", and the pptx skill's `validate.py` passes |
| 8 | Visual QA | PowerPoint's own slide export, tiled | one pass, report what it shows |

Render stills before videos, and videos only after the stills sheet is right. A still costs
seconds. A full render of 62 clips costs about 40 minutes on the i5 laptop.

## Design rules: the constants across every deck's own style

These hold regardless of which `STYLE-DNA.md` a deck lands on. **What changes per
deck — grid density, colour ground, motion grammar, chart language, image treatment —
comes only from that deck's own STYLE-DNA (stage 5), never from a previous deck.**
Reusing a rejected deck's look was exactly how deck-v3 landed at −3/10.

1. **One idea per slide, set large.** Never shrink the type below 24 px (28 px if the
   deck's STYLE-DNA sets a higher floor). If it doesn't fit, split the layout.
2. **Structure beats paragraphs.** A line shaped like `**Label** | value` becomes a
   numbered card: a big accent "01", the label in display bold, and the value in
   text. A single sentence becomes one large paragraph with its numbers set heavier.
3. **Every slide has one visual that means something.** A ring that counts to 90 for
   a 90-day test, a scan sweep over a real satellite raster, a strike-through for
   what the review killed. Decorative motion that carries no meaning is not allowed.
4. **Charts are native, never matplotlib screenshots.** Build them in SVG: polylines
   with `pathLength=1` and `strokeDashoffset`, counters that interpolate the value,
   bars that grow. Check every data-on-data contrast ratio; never guess one.
5. **One ground colour says what kind of thing is on screen.** Deck v4 used navy for
   real evidence and paper for argument; a different deck may draw the line
   differently, but STYLE-DNA states the rule once and every slide obeys it.
6. **Motion grammar is whatever STYLE-DNA sets, applied without exception.** Deck v4:
   elements enter over 10 frames, ease `cubic-bezier(0.2,0.8,0.2,1)`, build finishes
   within 45 frames of the slide's start, then holds at least 60 frames (2 s) before
   the next cut — the 2 s floor is a brief requirement, not a deck-specific choice.
   Count-ups only for numbers that are actually counted, never for a static fact
   dressed as a count (devilB, kacs-v4, F7/F8: "110 km" and "JD 1K" are not counts).
7. **Evidence stays on the slide and states its status in words, not just a marker.**
   A footer or chip line names source, date, and status (verified / one source / our
   estimate / our design choice) — the exact form is a STYLE-DNA choice; a deck
   should not silently copy another deck's evidence-chip component (devilA, kacs-v4:
   reusing deck-v3's chip system on a hook slide read as "unverified" before the owner
   spoke).
8. **Arabic is first-class.** Use `direction: rtl` on the slide. Entrances slide in
   from the reading side. Arabic line-height 1.4–1.75 (never Latin metrics). Latin
   terms and numbers in `<bdi>` or isolated chips; keep Western digits when the
   project says so. Time axes, real geography and real photos stay LTR/un-mirrored
   even inside an RTL slide — record which the project chose. Run
   `arabic-english-proofreading` before the storyboard locks (dual numbers, month
   names for the actual audience's Arabic, calques — kacs-v4 devilB caught "يوم 2"
   instead of "يومين" and Egyptian month names for a Jordanian room; the pair is the
   unit, so an Arabic fix without its English counterpart is unfinished).
9. **The house face comes from nj-kit** (`fonts/thmanyah/`). Load it with `FontFace`
   from `public/fonts` behind `delayRender`, so the render never falls back silently.
   Thmanyah has no ≤ ≈ → ✓ ✕ or emoji: draw ticks and arrows as SVG (`Mark` in
   `kit-qa-example.tsx`), and give only `≤` an Arial fallback, where the project
   accepted that.

## Traps already paid for: do not rediscover them

| Symptom | Cause | Fix |
|---|---|---|
| PowerPoint says "the file is corrupt" after you add autoplay | Hand-written `<p:timing>` with a `<p:video>` media node | Let PowerPoint write it: `scripts/postprocess-deck.ps1` (COM: MediaPlay effect "with previous" plus a fade transition). Never hand-edit timing XML. |
| `addMedia() cover value lacks a base64 header` | pptxgenjs wants the poster as a data URI | `'data:image/png;base64,' + fs.readFileSync(png).toString('base64')` |
| `remotion still --image-format=pdf` fails | Remotion 4.0.528 has no PDF still | Build the PDF twin from `templates/pdf/`: the same components render as plain DOM at their last frame (`FrameOverride`), Chrome prints them with `--print-to-pdf`, and the text stays real |
| PDF pages are cropped or shifted | `@remotion/player`'s `<Thumbnail>` mis-scales in print | Don't use Thumbnail for print. Use `FrameOverride` with direct rendering. |
| `useCurrentFrame() can only be called inside a composition` in the PDF | `AbsoluteFill` and `Img` in 4.0.5xx read the timeline | Use `Fill` (a plain div) and `Pic` (Img in video, img in PDF) from `theme.ts` |
| pypdf returns scrambled Arabic | pypdf's bidi handling | Use poppler (`pdftotext`, `pdffonts`, `pdftoppm`) only. The winget copy is under `%LOCALAPPDATA%\Microsoft\WinGet\Packages\oschwartz10612.Poppler*` |
| Wrong picture on a slide | A screenshot was cropped from the wrong file index | Read the image you crop, and name crops after what they show |
| Arabic deck shows the wrong charts | The Arabic JSON carried different figure ids from the English one | Figure ids are layout, not words. Map them from the language whose headings they match, and log it. |
| Clips fail to bundle halfway through a batch | `npm i` ran while the renders were running | Install everything before the batch starts |
| LibreOffice and pdftoppm are missing, so there's no visual QA | Not installed on this machine | Export slides with PowerPoint itself: `Presentations.Open(...).Slides(i).Export(png)` |
| Contrast fix values are wrong in a report | The ratio was guessed | Compute every ratio with `gates.py contrast`, and never write one from memory |
| `laya_ask.mjs` runs but its `main()` never fires on Windows | `import.meta.url === 'file://' + argv[1]` never matches Windows path formatting (backslashes, missing leading slash) | Compare against `pathToFileURL(process.argv[1]).href` instead (fixed in `nj-laya/scripts/laya_ask.mjs`, kacs-v4 2026-09-25) |
| A stale clip, rendered before a code fix, ships silently | The PPTX build reused `clips/<ID>.mp4` without checking it was built from the current source | Before building the PPTX, compare every clip's mtime against the newest file under `remotion/src` and re-render anything older. 4 stale clips shipped once on deck-v4. |
| `visual_gate.mjs` looks clean past the first few slides | It stops counting at 5 overlap failures, so every slide after the first bad one is never checked | Run an uncapped overlap probe (`scripts/overlap_probe.mjs`) across every slide, or gate per slide instead of per batch |
| The repo root `package.json` changes underneath a deck build | `npm install` run inside a scratch subfolder walked up and found the repo root instead | Install with `npm install --prefix <project folder>`. Never `git checkout` root files to "undo" it — that discards whatever else changed there since. |
| A python process the deck build didn't start gets killed | `taskkill /IM python.exe` kills every python process on the machine, not just the one this build launched | Stop servers by the PID you recorded when you started them, never by image name |
| A worker declines "build the whole deck" as too large | Nothing bounds the ask | Brief the build as checkpoints: CP1 scaffold + 2 slides + the full rehearsal chain (words→glyphs→scene→still→clip→PDF→PPTX end to end on 2 slides); CP2 core slides; CP3 backups + credits + all stills; a devil look at the CP3 stills; then the full render |
| A STANDARD builder's visuals score 3–6/10 against the storyboard | Matching a storyboard's exact layout and motion under judgement, not just building it, is a FRONTIER-tier call | Escalate the visual fix pass to FRONTIER in writing (`CAPABILITY_LIMIT`), don't re-run the same tier hoping for a better roll |
| The PDF twin's page count doesn't match the PPTX's clip count | The PDF prints one page per *slide*; the PPTX has one clip per *click step*, and some slides (S04-style) have several | Expected, not a bug — state both counts in the report so nobody "fixes" the mismatch |

## Commands

```bash
# 0  references + triage (Pinterest optional, credentials/pinterest.env)
PYTHONUTF8=1 python ~/.claude/skills/nj-motion-deck/scripts/pinterest_search.py "editorial infographic motion design"
node ~/.claude/skills/nj-laya/scripts/laya_ask.mjs --question "..." --options "A,B,C" --out refs/triage-row.json
# 1  scaffold (new subfolder, never inside an existing project root)
npx create-video@latest --yes --blank --no-tailwind remotion && cd remotion && npm i
# copy templates/src/* into remotion/src and templates/pdf/* into remotion/pdf (pdf.html -> public/)
# 2  gates
PYTHONUTF8=1 uv run --with fonttools python ~/.claude/skills/nj-motion-deck/scripts/gates.py glyphs public/fonts/*.otf -- src/data/*.json
PYTHONUTF8=1 python ~/.claude/skills/nj-motion-deck/scripts/gates.py contrast F3F8F9 0B1F2A 4D6270 F3F8F9
# 4  stills (last frame) — tile them, look once
npx remotion still AR-02 ../stills/AR-02.png --frame=-1
# 5  clips + posters, in the background, one command
for id in ...; do npx remotion render $id ../clips/$id.mp4 --codec=h264 --crf=18 --muted; npx remotion still $id ../posters/$id.png --frame=-1; done
# 6  PDF twin
npx esbuild pdf/pdf.tsx --bundle --outfile=public/pdf.js --jsx=automatic --loader:.json=json --define:process.env.NODE_ENV='"production"' --minify
python -m http.server 8765 --bind 127.0.0.1 --directory public   # stop it afterwards
chrome --headless=new --window-size=1920,1080 --no-pdf-header-footer --virtual-time-budget=20000 --print-to-pdf=out/deck.pdf "http://127.0.0.1:8765/pdf.html?lang=ar"
# 7  PPTX
PPTX_NODE_MODULES=<folder with pptxgenjs> node build-pptx.js ar
pwsh -File postprocess-deck.ps1 out/deck_AR.pptx
python <pptx skill>/scripts/office/validate.py out/deck_AR.pptx
```

## Before you report done

- Every gate line is in the report, quoted — including the stage 0/1 gates (refs row
  count, Laya accuracy, which classifier's buckets shipped).
- The local HTTP server, headless Chrome and any PowerPoint COM instance you started are stopped (`relay.py sweep`).
- Say which approved words were **not** touched, and which layout facts you changed (figure ids, axis direction).
- Name the devil verdicts on file (devilA, devilB or the owner's own approval) and whether every mandatory edit was applied.
- Name the output paths. An old deliverable is never overwritten; the new build goes into a new folder.
