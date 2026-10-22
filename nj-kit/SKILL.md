---
name: nj-kit
description: 'the owner''s portable toolkit: installs his skills, MCP servers, hooks and house style into a new repo or machine. Triggers: set up my skills here, bootstrap this repo, make this project like my other one, a missing skill.'
---

# The toolkit, portable

One folder that reproduces this setup somewhere else. Drop it in, run one
command, get the same behaviour: the same skills, the same MCP servers, Thmanyah,
Arabic that survives extraction, and a typecheck that runs when a turn ends.

## Where it is

| | |
| --- | --- |
| **Real location** | `~/.claude/skills/nj-kit` |
| **Desktop copy** | `<NJ_KIT_ROOT>` — **an extracted copy of the zip**, refreshed after every export (client rule, 2026-09-10). It was a junction into `~/.claude/skills/nj-kit` until then; it is now a real folder, so editing in it edits *nothing live* |
| **Carryable copy** | `<NJ_KIT_ROOT>.zip` — ~210 KB, rebuilt automatically whenever anything changes |

Take the **zip** to another machine. **Edit the kit at its real location**,
`~/.claude/skills/nj-kit` — the Desktop folder is now output, not the thing
itself, and an edit made there is overwritten by the next export.

If the Desktop path is ever a junction again, remove **the link only** — in
PowerShell, `(Get-Item '<NJ_KIT_ROOT>').Delete()` on the reparse
point. Never delete through it: `Remove-Item -Recurse` on a junction walks into
`~/.claude/skills/nj-kit` and takes the real kit with it.

## It keeps itself current

A `Stop` hook in `~/.claude/settings.json` runs `export.py --if-changed --zip`
after every turn, so adding, editing or deleting a skill updates the manifest,
the bundled copies and the zip without anyone remembering to. It prints one line
when it did something and stays silent otherwise.

**The change test is a set comparison, not a timestamp scan**, and that
distinction cost a bug worth keeping in mind: `find -newer` sees additions and
edits but is blind to deletions — a removed skill leaves no file newer than
anything, so the manifest went on advertising a skill that was gone and
`bundled/` kept shipping it. Anything asking "did the toolkit change?" has to
compare what is there against what was recorded.

## The rule: when you create or change a skill, update this

The hook covers what a machine can derive. Three things it cannot, and they are
the parts that make the kit worth having:

| Re-syncs itself | Needs a person, every time |
| --- | --- |
| the skill roster | **`house_style`** — Thmanyah only, poppler-only extraction, the document rules |
| bundled copies + zip | **`tooling`** — a new binary a skill depends on |
| MCP servers, from `~/.claude.json` | **every `why` note** — a new entry arrives marked `TODO:` |
| Stop hooks, from user settings | **`KNOWN_SOURCES` in `export.py`** — see below |
| | **`project_skills`** — a skill that lives in a repo, which nothing here scans |

So, on creating or adjusting a skill, in the same turn:

1. **If it came from a public repo, add it to `KNOWN_SOURCES` in
   `scripts/export.py`.** Otherwise it is classified as ours and *bundled* —
   which still works, but it freezes a copy that never updates and bloats the
   zip. The classification is deliberately biased that way: a skill wrongly
   bundled works, one wrongly assumed public vanishes on the next machine.
2. **Replace any `TODO:` in the manifest.** A server or hook that appears
   without a reason is a line nobody can evaluate later — "why is Playwright
   pinned to real Chrome?" has an answer, and losing it means the next person
   removes the flag and rediscovers reCAPTCHA the hard way.
3. **If the change is a house decision — a font, an extractor, a document
   convention — put it in `house_style`.** That block is what makes the output
   match; the skill list alone does not.
4. **If it changed how something must be done, say so where the doing happens.**
   A note in the manifest that contradicts a skill's own SKILL.md loses to the
   skill, so fix the skill.
5. **If the skill belongs to a repository, record it under `project_skills` and
   link it — never copy it.** `export.py` scans one directory, the one the kit
   sits in, so a repo-resident skill is invisible to the roster and to the Stop
   hook's change test. That is not a gap to close by copying: a copy drifts from
   the tracked original the moment either side is edited, and the drift is
   silent — the agent reads the copy while the reviewer reads the commit. Add
   the name to `PROJECT_SKILLS` in `export.py` (which keeps it out of
   `bundled/`) and write its entry, with a real `why`, into the manifest by
   hand.

Then `python scripts/export.py --zip` if you want the change carried
immediately rather than at the end of the turn.

```bash
python scripts/install.py --check      # what is missing, changes nothing
python scripts/install.py              # private install (default)
python scripts/install.py --scope project --commit   # share with the repo
```

## Social media starts with Agent Reach (owner, 2026-10-01)

Binding rule, recorded in `manifest.json` `house_style.social_media` and the
`tooling.optional` entry: for any social-media read, run `agent-reach doctor`,
then use the channel it reports. Logged-out only; never `agent-reach transcribe`
(audio goes to Groq/OpenAI). Instagram is the exception: its channel needs a
logged-in Chrome, so use yt-dlp + ffmpeg + local faster-whisper
(`--with "av>=15,<16"`). Recipe: ENSERA `documentation/10-Instagram-Reels-Review/agent-reach-install.md`.
Not in `KNOWN_SOURCES` - that list is for skills, and Agent Reach is a `uv tool`.

## Private by default, and why that is the default

**Eight people share one Claude account.** That matters less than it sounds for
skills, and more than it sounds for everything else, so the two need separating:

- **Skills are files on a disk, not account state.** Anything under
  `~/.claude/skills/` is yours because it is on your machine. A teammate signed
  into the same account on their laptop cannot read it, edit it, or know it
  exists. That is why `--scope user` is the default.
- **Account state is genuinely shared.** claude.ai skill sync, uploaded
  sessions, artifacts — all eight see those. This cannot be fixed from inside a
  client; the only defence is not to publish, which is what the privacy block
  below turns off.

`--scope project` puts the skills in the repo instead. That is right for a team
convention and wrong for a private toolkit, so it adds `.claude/skills/` to
`.gitignore` unless you pass `--commit` to say you meant to share it. Your own
rule — nothing of yours reaches the team except through a commit you made on
purpose — is exactly what that flag is.

## What `install.py` does

1. **Checks tooling** — `pdftotext`, `pandoc`, `node`, `python`, and optionally
   `duckdb`. It looks past `PATH` into the usual Windows install locations,
   because a shell opened before an installer ran reports things as missing that
   are installed; "restart your shell" and "go install it" are different
   answers and it gives the right one.
2. **Installs the skills.** Ours are copied from `bundled/` — no registry has
   them. The third-party ones are re-fetched from source by `npx skills add`, so
   a new machine gets current versions rather than a stale snapshot. The
   **project** skills are neither: they are linked to the repo that owns them,
   and skipped with a message when that repo is not on this machine.
3. **Re-applies the trimmed descriptions** from `description-overrides.json`
   via `scripts/apply-descriptions.py`. A fetched third-party skill arrives with
   upstream's long description, and descriptions are the only cost paid in
   *every* session (the 2026-09-18 audit: 5,463 words down to ~1,675), so
   without this step a fresh install silently gives the saving back. The step is
   non-fatal: a description 40 words too long is a token cost, not a broken
   install. `python scripts/apply-descriptions.py --check` reports drift after
   any later skill update.
4. **Applies the privacy settings** to user scope (see below).
5. **Adds the MCP servers** — playwright with real Chrome and a persistent
   profile, context7. (Figma removed 2026-10-10; MCP env values are never exported.)
   **Installs the hooks** (2026-10-10) into user settings.json, backup first; paths are rewritten to this machine's home, and a hook whose script is not on this machine is skipped and named.

Nothing is written without a backup beside it, and `--check` does none of it.

## The privacy block

Written to `~/.claude/settings.json`, which is per-machine. **Teammates are
unaffected — they keep controlling each other's sessions exactly as before.**

| setting | what it stops |
| --- | --- |
| `disableRemoteControl` | anyone driving this machine's sessions from claude.ai |
| `remoteControlAtStartup` | the bridge opening itself each session |
| `crossSessionInbound: refuse` | inbound `SendMessage` from any other session |
| `isolatePeerMachines` | peer sessions on other machines reaching this one |
| `autoUploadSessions` | this machine's transcripts appearing on claude.ai |
| `syncClaudeAiSkills` / `syncClaudeAiPlugins` | account-level skills mixing with local ones |

**Be clear about the limit.** These stop *your machine* participating. They do
not make a shared login private: anyone with the credentials can sign in
somewhere else and use the account. If the work genuinely needs to be
inaccessible to the other seven, it needs a separate login, not a setting.

## House style — the part that makes output match

Recorded in `manifest.json` so a fresh machine inherits the decisions, not just
the files:

- **Thamanya Serif (Thmanyah / ثمانية) is the house face** (owner, 18 Sept 2026),
  weights 300–900. **The kit ships no font files.** Optional: point `NJ_HOUSE_FONT_SOURCE`
  (export.py) or `NJ_HOUSE_FONT_DIR` (install.py) at a folder of cuts you are licensed
  to use; `install.py` then installs them per-user, so every project and every renderer
  finds `thmanyah serif display` / `thmanyah serif text` / `thmanyah sans` by name.
  Without the variables the font steps are skipped and nothing fails. The publisher's
  licence governs the files; never publish or redistribute them. No arrows, ticks, `≈` or emoji in the
  face: draw them as SVG. **Cairo is banned**:
  never proposed, never a fallback, in any project. Every Cairo mention further
  down this file (the workflow figure, PROJ PDFs, the film toolchain,
  `fetch-fonts.mjs Cairo`) is a dated record of how those pieces were built
  before the switch, not a current instruction.
- **Extract PDFs with poppler (`pdftotext`) — never pymupdf or pdfium.** They
  drop Arabic words silently, and two of them agreeing is one shared bug rather
  than confirmation. Measured on one nine-word sentence: pypdf 0/9, pymupdf 6/9,
  poppler 9/9. This is the single most important line in the manifest; ignoring
  it is how a sound font gets blamed for corrupt text.
- **`PYTHONUTF8=1` on Windows.** cp1252 cannot read or print one Arabic
  character, and several third-party scripts crash on it rather than degrade.
  **A script that prints a path also reconfigures its own stdout** —
  `sys.stdout.reconfigure(encoding="utf-8")` — because the env var does not
  cover a script launched by a tool that hands it an inherited cp1252 console.
  `check-pdf.py` and `trash.py` were both patched on 2026-09-06, and
  `check-pdf`'s crash had been masking the finding it was trying to print.
- Documents are A4, bilingual Arabic/English, tagged, and their text must
  survive being copied out.

### Film (added 2026-09-06)

Every line below is a rejection the owner made *after* a full render, and a render
costs an hour of workers — so these belong in the film bible's acceptance list,
tested by the critic before anyone looks at frames.

- **Captions are the spoken words**, verbatim, chunked, on screen while they are
  said. Card copy that paraphrases the voice reads as the caption talking about
  something else.
- **The picture shows what the voice names, at the moment it names it.** A
  feature spoken over a different panel is a fault, not a style choice.
- **Narration rules moved to `nj-writer/NARRATION.md`, 2026-09-21** (the "one
  voice request per line, fixed settings, `--rate=-6%` never `--rate -6%`"
  rule that used to live here — NARRATION.md §2 reconciles it with
  `voice.py`'s Gemini-TTS engine, where expressiveness comes from the writing
  and a per-line direction string, not a DSP flag). This entry stays only as
  the dated pointer.
- **Narration voice = Kore registered styles, 2026-10-01:** registry `nj-writer/voice-styles.json`, rules `NARRATION.md` §11, gate `nj-writer/scripts/voice_style_gate.py`; first use in any project runs `voice_style.py list` (`house_style.tts_engine`).
- **Arabic tashkeel KB, 2026-10-01:** `nj-writer/reference/arabic-tashkeel/` (`README.ar.md`, `kb/rules/tashkeel.md` R-TASHKEEL-001..009, `evidence/` raw runs); the verifier `tashkeel_verify.py` (gemini-3.6-flash) was REMOVED 2026-10-03 — hard rule: gemini-3.1-flash-tts-preview is the only model a voice pipeline calls, one take, no verify. Portal wording stays as written; tashkeel goes in `tts_text` only; the gate now allows the source's own marks (fails over 50% marked) and rejects a split shadda or a control character. PROJ: `normalizeTtsAr` in `src/manual/narrate.ts` (Kore lines only).
- **Masters at −14 LUFS integrated, −1 dBTP.** Verify with `ebur128`, and with
  `silencedetect` for gaps.
- **No product warnings in frame** — grant notes, storage notes, amber cards.
  Only the story's deliberate failure may look like an error.
- **Tutorials live on their own page**, never stacked inside settings.

### Browser-extension testing (added 2026-09-06)

- **One headed suite at a time**, and the stress suite alone. Parallel headed
  runs fight over the profile and the focus, and the failures they invent are
  not the product's.
- **Classic scripts on one page share a global scope.** A top-level `const`
  declared in two of them throws "Identifier has already been declared" and the
  whole page dies. Scope per file (IIFE) or declare once — unit tests never see
  this; only a behavioural page-render check does.
- **A real `activeTab` grant is obtainable under Playwright**: dispatch the
  manifest's own keyboard shortcut through CDP `Input.dispatchKeyEvent`, which
  fires `chrome.commands.onCommand`. Measured dead routes: `action.openPopup`,
  the CDP Extensions domain, `chrome.test`, and both `--auto-select-*` flags.

### The workflow figure (added 2026-09-06)

- **One A4 landscape sheet, reached by search.** Type size, band count and the
  gap between stages trade against each other; search the three together and
  score the printed point size. Never scale a finished figure down — split it,
  or grow the sheet.
- **Cairo only, family list ending at `sans-serif`.** A named system fallback
  turns a missing glyph into a silently embedded Segoe UI. So captions use only
  glyphs Cairo has: no «←»/«→» — write «إلى».
- **Load faces with `<link>`, not `@import`.** Inside `page.setContent()`,
  `@import` never fetches, so weeks of measurements were taken in a fallback
  face and reported clean. Assert `document.fonts.check()` before measuring.
- **Measure, do not average.** Cairo's advance width per character runs 0.34–0.62
  of the type size depending on the string; reserve with `size*(0.42*len+1.2)`.
  An Arabic line's glyph box is 1.82× the type size.
- **Shapes mean things.** Rectangles are stages, diamonds are questions, green
  terminators are start and end; the answer rides in a ring on the arrow, and a
  return never crosses the page.


### Transcribing a video (added 2026-09-07)

`manifest.json` → `house_style.video_transcription`. The rule in one line:
**read the frames, never a scrape of the page the video sits on.**

Measured on an Instagram reel on 2026-09-07: a web fetch of the reel's page
returned **17 of its 20 on-screen items, in the wrong order, with the source's
own red ✗ marks silently dropped** — which inverted the meaning of three of
them — and reported one item as unreadable. A 3× `lanczos` crop of the same
region made all twenty legible. A list that arrives already-transcribed is a
draft, not a source.

- `yt-dlp --dump-json` for provenance, `yt-dlp -f best` for the file. A public
  reel needs no login and none is used.
- `select='gt(scene,0.2)'` first, and again at `0.05`. **Zero cuts is the
  useful answer**: a talking-head reel with a caption layer accumulates its
  list, so the final frame is the whole thing.
- **Time each item by masked difference against the final frame**, not by
  `argmax` of the frame-to-frame difference. `argmax` puts an item wherever the
  speaker's head crossed that row — it was 3 and 7 seconds early on two of
  twenty. The check that the geometry was right is that the result comes out
  monotonic.
- **The audio never leaves the machine.** There is no local STT here, and where
  a reel burns in word-by-word captions, montaging that strip at each landing
  time corroborates the list for free.
- Recycle the download and the frames with `safe-delete` when the transcript is
  written. **The transcript is the checkpoint**, not the video.

### The film toolchain

`ffmpeg` (**GPLv3** — a producer-side tool, never shipped inside a product, or
the product inherits the licence), Gemini 3.1 Flash TTS via OpenRouter for narration, **Playwright
driving real Chrome** for frame capture and every extension suite, `fontTools`
for the Cairo faces, and `PYTHONUTF8=1` on every python call. Remotion is
installed as documentation and is **not** what builds these films.

### Least-cost execution and delegation — NJ Governance v3 (2026-09-22)

**`nj-delegate/SKILL.md` §0 is the one canonical statement; this is a pointer,
not a copy.** v3 in one breath: the main session is the **Lead**, the sole
orchestrator; workers own a bounded phase, report once and never delegate to or
instruct each other; the Lead wakes on events and nothing polls through a
model; deterministic tools and existing evidence come first, then the least
expensive reliable tier; **minimum-sufficient workers for the critical path —
zero, one or many, no quota — with useful parallelism looked for**; compact
briefs, artefact handoff by path, risk-based review, budgets as ceilings,
batch telemetry via `relay.py batch`. Model names live only in
`nj-delegate/reference/runtime-map.md`. `nj-agent-ops` is the transport and
keeps the trigger-based interpreter (§4 there); `nj-supervise` (in the nj-kit
plugin since 2026-09-29, no longer a personal skill) holds the brief clauses and
artefact checks. Every worker, builders and editors included, is dispatched in
the background (`run_in_background: true`) and its completion is the trigger that
wakes the Lead (owner, 2026-10-11; supersedes the 2026-09-29 foreground rule);
every brief carries a `FOCUS` line; a worker report is a receipt of at most 25
lines plus the stage detail file. `nj-delegate/scripts/check_governance.py` is the
gate that keeps superseded wording from coming back.


## Keeping the kit current

```bash
python scripts/export.py            # re-snapshot from what is actually installed
python scripts/export.py --dry-run  # see the diff first
python scripts/export.py --zip      # ...and rebuild <NJ_KIT_ROOT>.zip
```

### Zip, then extract to `<NJ_KIT_ROOT>`

**Client rule, 2026-09-10.** After every `export.py --zip`, expand the zip into
`<NJ_KIT_ROOT>/` so that folder is a real extracted copy of what
was shipped — not a junction, not a stale one. It is the copy someone opens to
check what actually went into the zip, and a junction shows the live kit
instead, which is exactly the thing the check is supposed to catch.

```powershell
$zip = '<NJ_KIT_ROOT>.zip'; $dst = '<NJ_KIT_ROOT>'
$i = Get-Item $dst -ErrorAction SilentlyContinue
if ($i -and $i.Attributes -band [IO.FileAttributes]::ReparsePoint) { $i.Delete() }  # the LINK only
elseif ($i) { $env:PYTHONUTF8 = '1'; python "$HOME\.claude\skills\safe-delete\scripts\trash.py" $dst }  # recycle bin, restorable
Expand-Archive $zip -DestinationPath (Split-Path $dst) -Force   # the zip's root entry is nj-kit\
```

`$i.Delete()` on the reparse point removes the link and leaves the target. Do
not reach for `Remove-Item -Recurse` on a junction — it deletes through it.

Run it after adding or removing a skill. The manifest is a description of this
machine, and a description that is not refreshed becomes fiction — the failure
mode is a teammate or a future you installing a roster that no longer matches
what makes the output right.

`export.py` also re-copies our own skills into `bundled/`, skipping
`node_modules`, `__pycache__` and font vaults so the kit stays small enough to
carry around.

## Account or machine switch

Changing the Claude account email does not touch `~/.claude` on the same
machine. This section is for a new machine, a profile reset or a fresh
`~/.claude`. Added 2026-10-04.

**Carried by the zip** (`bundled/`, `manifest.json`):

| What | Where in the zip | Restored by |
| --- | --- | --- |
| Our skills | `bundled/<skill>/` | `install.py` |
| Plugin nj-kit (nj-method, nj-delegate, nj-agent-ops, nj-supervise, nj-writer, ...) | `bundled/nj-plugin/` (source `<NJ_PLUGIN_ROOT>` was missing on 2026-10-04, so the installed cache copy 1.3.4 is bundled) | `install.py` copies it to `<NJ_PLUGIN_ROOT>`, then the two `claude plugin` commands below |
| Standing instructions | `bundled/CLAUDE.md` | `install.py` (never overwrites a differing file) |
| Auto-memory, every project | `bundled/memory/<project-dir>/` | `install.py` (never over a newer file) |
| Hooks and statusLine | `manifest.json` `hooks` (live from settings.json) | `install.py` |
| MCP config, third-party roster, house fonts | `manifest.json`, `fonts/` | `install.py` |

Memory files over 1 MB, binary files, and any file holding a credential-shaped
value are skipped by `export.py` and named in its output. The 2026-10-04 scan
found none.

**Not carried, redo by hand:** the Claude login; claude.ai connectors (
Claude Docs), claude.ai artifacts and cloud sessions; the `TAISCE_TOKEN`
environment variable (taisce MCP); the OpenRouter key (voice pipeline); the GROQ
key. Keys and tokens are never in the kit by design. Project credentials
live in each project's own CLAUDE.md or env file.

**Restore commands** (PowerShell, after extracting the zip to `<NJ_KIT_ROOT>`):

```powershell
$env:PYTHONUTF8 = '1'
python <NJ_KIT_ROOT>/scripts/install.py --check   # report only
python <NJ_KIT_ROOT>/scripts/install.py            # skills, CLAUDE.md, memory, plugin, MCP
claude plugin marketplace add <NJ_PLUGIN_ROOT>
claude plugin install nj-kit@nj-kit
# then set TAISCE_TOKEN, the OpenRouter key and the GROQ key as user environment variables, and sign in to the claude.ai connectors
```

## The media library

One root, `library/` at the top of ENSERA (env `NJ_LIBRARY`), replacing
`production/library/`, `production/music-library/`, `bg-music/assets/`,
`nj-style-film/assets/sfx/` — all retired 2026-09-21 (`manifest.json`'s
`libraries` block has the counts). Kind-first (`images/`, `sfx/`, `music/`,
`styles/`, `fonts/`, `vfx/`). **Search it first; intake only through
`library.py`** (`find`, `intake`, `verify`, `stats`, `sync`, `plan-check`);
projects hold copies with permanent ids, old ids kept as `aliases[]`.
**Research the project and write an `ASSET-PLAN.md` before a storyboard** —
`library.py plan-check` gates it. To build a shareable `nj-library.zip`:
`library.py zip`, excluding `_inbox/`, anything tagged `no-redistribution`,
and `fonts/` — skip the run and report the estimated size instead if it would
take over two minutes. The fonts and any `no-redistribution` asset (a
living-model cut-out, MrCutout.com terms) never go into anything shared.

## Setting up a genuinely new repo

```bash
cd <new repo>
python <path-to>/nj-kit/scripts/install.py --scope project
```

Then, for a TypeScript project, the typecheck Stop hook: the manifest names it,
and `pdf-typography` needs its font vault refilled with
`node scripts/fetch-fonts.mjs Cairo` since `bundled/` deliberately omits fonts.

### Skills that belong to the repo — linked, never copied

Some skills are not portable and should not be: project skills describe one portal, one pipeline and one document standard, they
are tracked by their own repository, and that repo — not this kit — is their authority.
They are listed in `manifest.json` → `project_skills` (empty in the public kit) and **`install.py` links
them**, from `<working directory>/.claude/skills/<name>` to the repo's own copy:

```bash
# what install.py does, and what to do by hand if you are wiring one up
powershell -NoProfile -Command "New-Item -ItemType Junction \
  -Path '<project-root>/.claude/skills/project-e2e' \
  -Target '<project-root>/project-tests/.claude/skills/project-e2e'"
# elsewhere: ln -s <repo>/.claude/skills/<name> <cwd>/.claude/skills/<name>
```

Three things this exists to prevent:

- **A copy drifts, silently.** Two originals means the agent reads one and the
  reviewer reads the other, and nothing announces the divergence.
- **Claude Code loads `.claude/skills` from the working directory, not from a
  subdirectory of it.** Opened at the PROJ root, the three skills inside
  `project-tests` never loaded at all. The junctions created 2026-09-06 are what
  make them load from either directory.
- **`mklink` is the wrong tool under Git Bash** — MSYS rewrites the arguments of
  `cmd //c mklink /J` before cmd sees them, and it fails on valid paths.
  PowerShell's `New-Item -ItemType Junction` works and needs no elevation.

`--scope project` will **not** add `.claude/skills/` to the `.gitignore` of a
repo that already tracks it (`git ls-files` decides). Ignoring a tracked
directory untracks nothing — git keeps the files and quietly stops offering the
next edit, so a skill change goes uncommitted and nobody is told.

### Python packages: uv, never pip (owner, 2026-09-17)

Every Python install or one-off tool goes through `uv`: `uv pip install <pkg>`,
`uv run <script.py>`, `uvx <tool>`. It is faster, reproducible, and keeps the
global interpreter clean. `install.py --check` reports `uv` like any other
binary; install it with `irm https://astral.sh/uv/install.ps1 | iex`.

## Changelog

- 2026-10-19 (evening): Jira attachment allowlist (the owner): png/jpg/jpeg/mp4/webm/gif/md only; `ALLOWED_EXT` + `check_attachable` in `nj_rank.py` (+ .pdf, per the owner; `register` also drops non-allowed files and prints them; refuses at `attach`, `file_one` keeps others local as `local_only`); tests added; docs in nj-rank, nj-jira (SKILL, bug-template, rest-recipes), nj-qa-pipeline

- 2026-10-19 (later): Jira stage label (the owner): one fixed label `phase2-uat` on every new Bug/Task (supersedes `<stage>-<SERVICE-SLUG>`); single home `STAGE_LABEL` in `nj_rank.py` + `nj-jira/SKILL.md` § Jira stage label; nj-rank defaults to it. `nj-jira/references/bug-template.md` rewritten: canonical Bug layout = PROJ-1234 (Verdict/Source, Where, Steps, Expected, Actual, Evidence; no metadata lines in body; Jira evidence unmasked). Sanad: new account only, kept out of skills (PROJ CLAUDE.md); Automation Tests Sanad OTP wait raised to 30 min.

- 2026-10-19: Jira rules (the owner): nj-rank one Task per (service, work type), never per note; only PROJ work is tasked (`file` skips other projects, test added); nj-jira Bug description carries no Priority/Severity/Labels/Assignee/related/Environment lines or sections (fields and links only).

- 2026-10-16 (later, overnight): `nj-knowledge-book` hardened while upgrading its own first book: stem-less probe (`probe_bank.py`, stage 3c), bank audit 3d, `calc:` in key files (`move_calc.py`), objective-id prefixes, `twin_front`, ordinal labels, whole-word Arabic avoid rules, `kb.py verify` refuses retracted entries; 124-assertion selftest. Lessons in its `reference/known-failures.md`. safe-delete gained the percent-name / directory-watcher note; pdf-typography documents `outline`.

- 2026-10-16: new skill `nj-knowledge-book` (sourced, gated knowledge book: page kinds, teaching gate, quote-bound verification, blind audit, Arabic twin, PDF with outline, `plan`, council stage; 86-assertion selftest) from the QA Engineer repo, built through a 5-POV devil council over 3 rounds. nj-evidence now ships `scripts/kb.py` + `rules.py` (run in place, `kb/kb.json` required) and lost the "build a knowledge base" trigger to it. pdf-typography `renderPdf` gained `outline` (bookmarks). Manifest: skill_notes for both, tooling optional pymupdf.

- 2026-10-09: project skill `project-automation-tests` (pipeline of the Automation Tests suite) listed in manifest `project_skills`, export.py OURS, and junctioned into `<project-root>/.claude/skills`.

- 2026-10-04 (later): nj-kit plugin 1.3.5 — worker-rules R18, never rewrite the owner's working tree (no reset --hard / stash / checkout -- .), after a worker wiped an uncommitted CLAUDE.md. `<NJ_PLUGIN_ROOT>` is back and is the bundled source again.

- 2026-10-04: export.py bundles `~/.claude/projects/*/memory/` (credential-shaped files skipped) and the nj-kit plugin; install.py restores both; new section Account or machine switch. `<NJ_PLUGIN_ROOT>` was missing, so the plugin cache copy is the bundled source.
- 2026-10-18: nj-jira evidence method (the owner): bug-template.md § Evidence rules rewritten (viewport + red ring + minimal mask, no .txt/.json, named shots, «الدليل» lists all); pointers in nj-jira / nj-qa-pipeline / nj-rank SKILL.md; new nj-jira/scripts/evidence-shot.ts + ring-pdf.py (generic, no credentials).
