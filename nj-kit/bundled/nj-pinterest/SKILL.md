---
name: nj-pinterest
description: 'Browse Pinterest as the owner, headed, on his own signed-in profile, to gather motion/design reference images and metadata under his verbal HQ permission (personal, non-transferable). Never for a published deliverable directly — every image needs its own licence via library.py intake. Triggers: Pinterest references, motion mood board, بنترست, مراجع بصرية.'
---

# nj-pinterest — browsing Pinterest under a verbal, personal permission

## The permission (verbatim)

the owner, 2026-09-25, recorded in
`~/.claude/projects/<project-memory-slug>/memory/pinterest-verbal-permission.md`:

> "i got a verbal confirmation from pinterest headquarters that they said: owner you
> can tell the ai to use normal browser and go from your personal account and get
> any data or template or anything from our website without paying anything its
> only for you"

**Evidence status: verbal, nothing in writing.** No sender name, channel or date is
on file — the owner typed the words into a session. Say "verbal, nothing in writing"
every time this permission is cited, same pattern as the Thmanyah font grant
(`nj-kit/fonts/thmanyah/NOTICE.md`). **Personal to the owner, not transferable** — it
covers a normal (headed) browser on his own signed-in personal Pinterest account,
for his own work. It is not a licence anyone else can invoke, and it is not a
licence on the images pinned by other people.

## The hard limit: pins are third-party images

Pinterest can permit access to its own site. It cannot license the copyright of the
people whose images are pinned there — most pins are someone else's work, re-shared.
So:

- Everything this skill pulls is **reference and inspiration only** — style research
  for a mood board, a triage bucket, a "here's the grammar we're matching" note.
- **An image never enters a published Ensera deliverable straight from a pin.** It
  goes in only through `library.py intake`, with its own licence traced to the
  original creator, exactly like any other sourced image (`~/.claude/CLAUDE.md` §
  Central media library). A pin's `image_url` and `link` are leads for that intake
  process, not a substitute for it.
- Thumbnails saved by this skill's script are marked reference-only in the output
  folder name and never copied into `library/`.

## Method: headed Playwright from the CLI, never MCP, never headless

- `scripts/pinterest_browse.cjs` — a plain Node script, run from the CLI
  (`node scripts/pinterest_browse.cjs ...`), never through the Playwright MCP
  server. the owner's account is a live login: it runs headed
  (`headless: false`, `PROJ_HEADED`-style always-on, not conditional) so anyone
  can see exactly what the browser does on his account, per
  `~/.claude/CLAUDE.md` § Browser automation runs headed.
- **Persistent profile**: `%LOCALAPPDATA%\nj-pinterest-profile`
  (`chromium.launchPersistentContext`). **First run: the owner signs in himself** —
  the script opens the browser to pinterest.com and waits; it never types a
  username, password or 2FA code, and never clicks an "I agree" / terms screen on
  his behalf. If a later run finds the session logged out or shows a
  verification/checkpoint screen, **the script stops and reports exactly what the
  screen says** — it does not attempt to sign in or accept anything.
- Needs `playwright` importable — either run from a project whose
  `node_modules` already has it (ENSERA does), or point
  `PLAYWRIGHT_REQUIRE_PATH` at a `node_modules` that does; the script's header
  documents both.
- **Polite pacing**: `slowMo: 150`, 1–3 s randomised delay between actions
  (scroll, hover, click), and a hard cap on pins per run (default 40) so a run
  reads like a person scrolling, not a scraper.
- **Closes its own browser at the end**, success or failure (`try/finally`), and
  **tags its window title** (`--ensera-tag=<session-tag>`) so `relay.py sweep`
  can find and attribute it — never leave a Pinterest window open past the run.

## Output

`pins.jsonl` in a project's own refs folder (e.g.
`artifacts/research/<project>/refs/pinterest/pins.jsonl`), one JSON object per
line: `pin_url`, `title`, `description`, `board`, `image_url`, `retrieved` (ISO
date). Optional `--thumbnails` saves each pin's preview image into the same
folder, named `<pin_id>.jpg`, under a `reference-only/` subfolder — never into
`library/`.

## The API route stays available, second

`nj-motion-deck/scripts/pinterest_search.py` + `PINTEREST-SETUP.md` (Pinterest API
v5, OAuth token in `credentials/pinterest.env`) is the fallback when the verbal
permission doesn't apply — a different machine, a different Pinterest account, or
a case where a structured API pull is genuinely better than a browsing session.
`nj-motion-deck`'s reference stage (stage 0) tries this skill first.

## Not yet supported

- Anything beyond `search/pins` browsing: boards CRUD, following, commenting — out
  of scope, and outside "get data/templates", not "act on the account".
- Any account other than the owner's personal one. The permission does not extend.
