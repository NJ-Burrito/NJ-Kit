# Skill security review — 6 September 2026

Every folder under `~/.claude/skills/`: **53 skills**, 45 from 24 third-party
authors, 8 ours (7 skills + `nj-kit` itself).

Method: the house reviewer — `nj-security-review/scripts/audit.py --json` for the
mechanical pass over every text file, then `skill-inspector`'s semantic workflow
(purpose fit, permission fit, sensitive access, external transmission, execution
risk, persistence, prompt risk, trigger risk, supply chain, user control) read by
hand over every folder that carried a script, a hook, a host or a finding.
Nothing was installed, modified, removed, or executed. `skillspector` is not on
this machine, so the static line is `audit.py` only — stated plainly, as the
skill-inspector fallback requires.

Mechanical totals, for the record: **2 critical, 102 high, 98 medium, 2 note**
across 53 skills. Both "criticals" are source comments in `graphify` describing
bugs its authors fixed ("silently executes", "was silently installing"), and 87
of the 102 highs are one file, `graphify/install.py`. A scanner cannot tell a
comment from an instruction; that is why every one was read.

**Verdicts: 5 REVIEW · 16 SAFE WITH CAVEATS · 32 SAFE.**

The bright line applied, as instructed: *anything that downloads or executes
remote content, reads credentials, or instructs disabling a safety boundary is
REVIEW.* It is applied without exception, including to our own toolkit — a
rubric that hands its author a clean sheet is a rubric that will miss somebody
else's payload.

---

## REVIEW — read these before the next machine is set up

### 1. `graphify` — graphify-labs/graphify (Apache-2.0)

The largest surface installed, by a wide margin, and the only one where the
skill folder is a whole application rather than instructions.

| | |
| --- | --- |
| **What is on disk** | 222 files, 4.7 MB, 86 executable scripts. The PyPI package `graphifyy` vendored whole — not the "thin driver" the manifest claimed until today. |
| **Install-time action** | `install.py` **appends a registration block to `~/.claude/CLAUDE.md`** (and `.claude/CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, VS Code instructions — six always-on surfaces), **registers Claude `PreToolUse` hooks** (`hook-guard search`, `hook-guard read`), **merges a `BeforeTool` hook into `.gemini/settings.json`**, and `hooks.py` installs **git `post-commit` and `post-checkout` hooks** that launch a detached rebuild on every commit. It also `shutil.rmtree`s several directories during install/uninstall. |
| **Credential read** | `llm.py` reads `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`/`GOOGLE_API_KEY`, `DEEPSEEK_API_KEY`, `MOONSHOT_API_KEY`, `AZURE_OPENAI_API_KEY`+`AZURE_OPENAI_ENDPOINT`, `OLLAMA_API_KEY`, and every matching `*_BASE_URL` override. |
| **Network egress** | `api.anthropic.com`, `api.openai.com`, `generativelanguage.googleapis.com`, `api.deepseek.com`, `api.moonshot.ai`, Azure OpenAI, any `OLLAMA_BASE_URL`, plus `app.graphify.com`; `git clone` of arbitrary repo URLs the user passes; `cdn.jsdelivr.net`/`unpkg.com`/`d3js.org` in the generated HTML viewer. **The payload is the corpus** — the summarisation step sends the indexed source to whichever backend is configured. |
| **Prompt risk** | None found. No injection, concealment or authority-claim language in `SKILL.md`. The two "critical" hits are comments. |
| **Purpose fit** | Genuine. Every power above is doing the job the description promises. The problem is the size of the job, not a mismatch. |

**Why REVIEW, and what to do:** the reasons are all defensible and there are too
many of them to hold in your head at install time. **`graphify install` has never
been run on this machine and must not be run without re-reading `install.py`
first** — that command, not the skill, is what edits `CLAUDE.md` and registers
the hooks. Using the CLI to build and query a graph (`graphify query`,
`graphify affected`) touches none of it. A `*_BASE_URL` override redirects the
corpus to an arbitrary host, so treat those env vars as sensitive. If a
summarisation backend is ever configured, know that the code being indexed
leaves the machine.

### 2. `watch` — taoufik123-collab/claude-watch (MIT)

| | |
| --- | --- |
| **What is on disk** | 28 files, 15 scripts, and **its own `hooks/hooks.json`** declaring a `SessionStart` hook (`hooks/scripts/check-setup.sh`). Not registered on this machine — user `settings.json` carries no such entry — because the skill was installed without the plugin wrapper. |
| **Install-time action** | `setup.py` installs `yt-dlp` and `ffmpeg` on first run: `brew install` on macOS, `winget install` on Windows, printed commands on Linux. It scaffolds `~/.config/watch/.env` at mode `0600`. |
| **Credential read** | `GROQ_API_KEY` then `OPENAI_API_KEY`, from the environment or `~/.config/watch/.env`. `SKILL.md` instructs the agent to *ask the user for a key with `AskUserQuestion` and write it into that file* when one is missing. |
| **Network egress** | downloads arbitrary video via `yt-dlp`; **uploads the extracted audio** to `api.groq.com/openai/v1/audio/transcriptions` or `api.openai.com/v1/audio/transcriptions` for Whisper. |
| **Filesystem reach** | writes into an Obsidian vault resolved from `$WATCH_VAULT_DIR`, or auto-detected at `~/Second brain/`, `~/Documents/Obsidian/`, `~/Obsidian/`. |
| **Prompt risk** | None. Steps 4.4/4.5 (vault staging, ingest) are gated and skip cleanly when no vault is found. |

**Why REVIEW, and what to do:** it downloads remote content, reads keys, writes
keys, and sends user media to a third party — four of the bright lines at once,
all disclosed and all purpose-fit. Keep the `SessionStart` hook unregistered.
Set `WATCH_VAULT_DIR` explicitly rather than letting it guess, or it may write
into a folder you did not mean. Use `--no-whisper` for anything confidential:
that is the flag that keeps the audio on this machine.

### 3. `nj-kit` — **ours**

Flagged by its own rubric, which is the correct outcome.

`install.py` runs **`npx skills add`**, which downloads and executes a package
from the npm registry and fetches 45 skills' worth of instructions from 24
GitHub owners; it writes the privacy block into `~/.claude/settings.json`;
`export.py` `shutil.rmtree`s stale bundles. The audit scores it 9 high — every
one a true positive. It is the only skill here whose *purpose* is to change what
the agent will obey on the next machine.

**What to do:** nothing changes; the mitigation is the one already in place —
`install.py` runs `audit.py --changed` after fetching, so a version nobody looked
at is never installed silently. Worth restating: **the third-party skills are
re-fetched from source, so their content is whatever the author pushed since you
last looked.** That is the design (a stale copy is worse) and it is exactly why
the `--changed` baseline exists.

### 4. `find-skills` — vercel-labs/skills (1 file, no scripts)

Prompt-only, and still a supply-chain surface: it instructs the agent to run
`npx skills find` and **`npx skills add <package>` — installing arbitrary skills
from GitHub — in response to an ordinary question** like "how do I make my React
app faster?". Its own examples are phrased that way. Nothing malicious in the
text; the risk is structural. Anything it installs arrives unaudited, and a
skill is instructions the agent follows on the author's authority.

**What to do:** treat `npx skills add` as a decision, not a step. Run
`python nj-security-review/scripts/audit.py <new-skill-dir>` before the first use
of anything it fetches, then `--baseline`.

### 5. `speech` — openai/skills (Apache-2.0)

Reads `OPENAI_API_KEY` and sends the text to be spoken to the OpenAI Audio API
(`scripts/text_to_speech.py`, 10 medium findings, all the same key). That is the
skill's entire and clearly stated purpose, the key is user-supplied, and there is
no second destination — a textbook SAFE WITH CAVEATS on intent. It is listed here
only because the rule is a bright line and credential-read crosses it.

**What to do:** in practice, nothing. **The house TTS is `edge-tts`** (no key, no
account), so `speech` is unused here. If it is ever used, remember the text of
the narration leaves the machine.

---

## SAFE WITH CAVEATS

| Skill | Source | Caveat |
| --- | --- | --- |
| `pdf-typography` | **ours** | `scripts/fetch-fonts.mjs` fetches CSS and font binaries from `fonts.googleapis.com`/`fonts.gstatic.com` with a legacy UA. Data, never executed. Carries a `node_modules` with Playwright, so its real surface is that dependency tree, not the 11 scripts. |
| `nj-security-review` | **ours** | `audit.py` is read-only and never executes what it reads, but its pattern catalogue quotes every attack string it hunts, so it excludes itself from scanning (`SELF`). It therefore cannot audit itself — read it by hand, as was done here. |
| `task-observer` | rebelytics/one-skill-to-rule-them-all | **Trigger hijack by design.** `SKILL.md` line 12: "invoke this skill before the FIRST tool call of any session". `references/environments.md` walks the user through adding a `SessionStart` hook and a `CLAUDE.md` line to enforce it. Nothing is self-installed and no network is touched (the six external hosts are citation links in `README.md`), but it is asking for standing attention in every session — grant that deliberately or not at all. |
| `skill-creator` | anthropics/skills | Spawns `claude -p` as a subprocess (`run_eval.py`, `improve_description.py`, `generate_review.py`) — an agent invoking an agent, with your auth. Also packages and installs skills. Local, documented, bounded. |
| `remotion-best-practices` | remotion-dev/skills | 137 files of documentation across a router plus 11 sibling folders; no scripts run against this machine. `remotion-upgrade/REFERENCE.md` tells the agent to run `npx skills update` on twelve packages at once — a re-fetch of remote instructions. The API keys it names (`ELEVENLABS_API_KEY`, `REMOTION_MAPBOX_TOKEN`, `REMOTION_MAPTILER_KEY`) are example code, not reads. Not used by the house film pipeline. |
| `playwright-best-practices` | currents-dev | 59 files, **zero scripts** — documentation only. The credential-shaped env names (`ADMIN_PASSWORD`, `API_TOKEN`, `ADMIN_EMAIL`) and the `fetch` POST examples that raise 4 medium/2 high findings are all sample test code. |
| `docx` · `xlsx` | anthropics/skills | 61 and 53 files; execute `soffice` (LibreOffice) as a subprocess over documents you hand them, and shell out for redlining validation. Local, purpose-fit, no egress. |
| `pdf` | anthropics/skills | 8 scripts, no egress. Two caveats: it instructs `pip install pytesseract pdf2image` for OCR, and **its stock text extraction is pypdf/pdfplumber, which lose Arabic words silently** — the house guard note is patched into its `SKILL.md` locally and *must be re-added after any re-fetch* (`manifest.house_style.arabic_pdf_guard`). |
| `mcp-builder` | anthropics/skills | Reference code contains `requests.get`, `httpx`, `axios.post` against `api.example.com`, plus `EXAMPLE_API_KEY`. Examples for servers you write, not calls this skill makes. |
| `ui-ux-pro-max` | nextlevelbuilder | 72 files, 17 scripts — all local search over a bundled offline dataset (styles, palettes, fonts, guidelines). `subprocess` appears only in its own test suite. The `evil.example` host is an XSS documentation example. |
| `tlc-spec-driven` | tech-leads-club | 5 validation scripts; the Verifier phase creates temporary git worktrees and injects mutations into a scratch copy. It is explicit that it never uses `git stash` and restores porcelain — but it does drive git on your repo. |
| `cco` | egorfedorov/claude-context-optimizer | **Inert as installed.** `SKILL.md` is a plugin skill whose every command is `node ${CLAUDE_PLUGIN_ROOT}/src/…`; only `SKILL.md` is on disk, so `CLAUDE_PLUGIN_ROOT` does not resolve and nothing runs. `allowed-tools: [Bash, Read]` is appropriately narrow. Harmless, and also non-functional — decide whether to complete or drop it. |
| `design-taste-frontend` · `framer-motion-animator` · `i-have-adhd` | leonxlnx, patricio0312rev, ayghri | Prompt-only, but each instructs `npm install` of project dependencies. Ordinary developer advice; listed so the install-time column is honest. |

## SAFE — 32 skills

No scripts that run against this machine, no network egress, no credential or
environment read, no install-time action, and no injection, concealment,
authority-claim or permission-bypass language.

**Ours (5):** `arabic-english-proofreading` (2 offline python scripts),
`nj-learn`, `nj-method`, `safe-delete` (one script; subprocess to the Windows
Shell, which is the only call that yields a restorable Recycle Bin item),
`workflow-diagram` (one offline `.mjs`).

**Third-party (30):** `brandkit`, `chrome-extension-development`,
`competitive-landscape`, `competitor-analysis`, `doc-coauthoring`,
`frontend-design`, `high-end-visual-design`, `image-to-code`,
`keyword-clustering`, `keyword-research`, `link-prospecting`, `local-seo`,
`minimalist-ui`, `no-ai-slop`, `ponytail`, `ponytail-review`,
`professional-proofreader`, `prompt-engineering-patterns`,
`redesign-existing-projects`, `seo-audit`, `seo-coach`, `seo-project-setup`,
`simple-issue-description`, `skill-inspector`, `test-fixing`, `theme-factory`,
`web-design-guidelines`. Ten of those are the single-file `every-app/open-seo`
set; five are `leonxlnx/taste-skill`.

Two specifically re-checked because a prior review raised them:

- **`ponytail` / `ponytail-review`** (dietrichgebert/ponytail, MIT) — 1 file each,
  0 scripts, no hosts, no findings. The optional plugin tier that writes a
  `statusLine` into `~/.claude/settings.json` **is not installed**; only the
  prompt text is. Confirms the September 5 verdict.
- **`local-seo`** and **`ui-ux-pro-max`** — their single `note`-level findings each
  are negated protective sentences ("do not run a grid without telling the user
  the cost first"). Kept and demoted by the scanner, correctly.

---

## One finding outside `~/.claude/skills/`

Reported because the review asked what runs without being asked, and this does.

User `settings.json` registers a **`SessionStart` hook** and a **`statusLine`
command**, both running node out of `~/.claude/.claude-manager/`. Neither comes
from any skill and neither was recorded anywhere until today. Both bundles were
read (they are minified, so they were read as bundles):

- `session-start-tap.js` — reads the session JSON on stdin; records `sessionId`,
  `ppid`, `cwd` and **`transcriptPath`** into `active-sessions.json`. `require`s
  only `fs`, `path`, `os`. No network.
- `statusline-tap.js` — reads the statusline JSON (model, context %, `$` cost,
  rate limits), persists it to `statusline.json` and `usage-history.json`, and
  **chain-spawns the previously configured statusLine command via
  `spawnSync(cmd, {shell: true})`**, so anything it inherited also runs on every
  render. `require`s `fs`, `path`, `os`, `child_process`. No network.

There is also a `~/.claude/.claude-manager-snapshots/` tree holding copies of
`settings.json`. Nothing here is malicious on the evidence — no egress, no
credential read — but a settings-writing, transcript-path-recording,
command-chaining pair of hooks from an unnamed tool is exactly what the manifest
exists to make visible.

**Fixed in the same pass:** `export.py`'s `live_hooks()` read only the `Stop`
event, so it had been blind to every hook the kit did not itself install. It now
records every hook event plus `statusLine`, and both entries above are in
`manifest.json` with a written reason.

---

## What was not done

- **No skill was modified, removed, or had its install step run.** The only files
  changed in this pass are `nj-kit`'s own (`manifest.json`, `SKILL.md`,
  `scripts/export.py`) and the stale roster figures in
  `nj-security-review/SKILL.md`.
- **`skillspector` was not run** — it is not installed, and installing it was out
  of scope. The static line is `audit.py` alone, so confidence on obfuscated or
  runtime-assembled behaviour is lower than a two-tool review would give.
- **The audit reads text, not behaviour.** A hostname assembled at runtime
  matches no URL pattern, and `rmtree` in a cleanup helper is indistinguishable
  from `rmtree` in a payload. Both were resolved by reading, but only where a
  finding pointed.
- **MCP servers are not covered here.** `playwright`, `context7` and `figma` are
  fetched by `npx` into `node_modules` at run time and none of that code was
  audited. Adding a server remains the higher-trust decision.

## The routine from here

```bash
A=~/.claude/skills/nj-security-review/scripts/audit.py
python "$A" --baseline      # accept this reviewed state
python "$A" --changed       # after any install or update — the only cheap check
```

A one-off audit protects you once. The baseline is what makes the next one cost
a minute instead of an afternoon.

---

## Addendum — `website-fine-print`, added later the same day

A skill written here, not fetched. Audited with the same tool and the same
rubric before it was bundled, because "we wrote it" is a claim about provenance,
not a security property — and the kit's whole argument is that the check is
what makes the claim worth anything.

| | |
| --- | --- |
| **Source** | **ours.** No `KNOWN_SOURCES` entry, deliberately: the nineteen-point list it is built on is public (an Instagram reel, cited in the skill and transcribed in `research/46-reel-brief.md`), but the method — the machine-checkable / delegated / judgement split, the DECLARED · OBSERVED · GAP · MANUAL vocabulary, the bilingual report and the standards mapping — exists in no repository. Bundled, so it travels. |
| **Files** | 1 — `SKILL.md`. No `scripts/`, no `references/`, no assets. |
| **Scripts or hooks** | **None.** Nothing to execute, nothing registered. |
| **Network egress** | **None.** Five hosts are *referenced* in prose, all as citations the reader opens by hand: `gdpr-info.eu`, `eur-lex.europa.eu`, `www.edpb.europa.eu`, `www.wipo.int`, `www.instagram.com` (the reel's own URL, as provenance). No fetch, no curl, no script that could reach them. |
| **Credential or environment read** | **None.** |
| **Install-time action** | **None.** No pip, npm, npx, curl or winget anywhere in the file. |
| **Prompt-injection patterns** | **None.** `audit.py` returns **0 findings** across all ten categories — no injection, concealment, authority-claim, permission-bypass, self-installing, remote-execution, credential-access, destructive, exfiltration-shape or obfuscation match, not even a demoted `note`. Digest `49ef718555df3639`, recorded as `NEW` against the 2026-09-06 baseline. |
| **Semantic review** | Purpose fit is exact: it is instructions for a human-plus-agent audit and asks for no capability. **Trigger risk is the only thing worth naming** — the description fires on "privacy policy", "cookie consent", "GDPR check" and "compliance audit", which are broad phrases. That is intended (they are the words people actually use when they need it) and it is bounded: worst case a reading skill loads when it was not needed, and it holds no tool grant that could act on the mistake. |
| **One content risk, and it is not a code risk** | The skill quotes an Instagram reel. It handles that correctly — the text is framed as *content to evaluate*, not as instruction, it is labelled "a market signal, not a specification", and the reel's own opening line ("Hey Claude, I don't want my vibecoded website to get sued") is quoted as reported speech rather than obeyed. That framing is the reason this passes rather than a technicality: quoted third-party text addressed to an assistant is exactly the shape prompt injection takes, and the skill names it before using it. |

**Verdict: SAFE.** Prompt-only, zero scripts, zero egress, zero credential
access, and a clean scan.

**Revised totals for this review: 5 REVIEW · 16 SAFE WITH CAVEATS · 33 SAFE, over
54 skills** (45 third-party, 9 ours including `nj-kit`).

One caution that belongs to the *use* of the skill rather than its safety: the
audit it produces is not a compliance certificate, and the skill says so twice in
its own text. Do not let a report generated from it leave the building as one.

### 2026-09-07 — `website-fine-print` re-rated after the Group D extension

**Still SAFE.** The skill grew a second source and a fourth group — twenty
site-hygiene points from a second Instagram reel (`DcKiRe3TvdB`, transcribed at
`research/48-reel-2-brief.md`) — and grew nothing else that a security review
cares about: **still one file, still zero scripts, zero hooks, zero credential
or environment reads, zero install-time actions, and `audit.py` still returns 0
findings across all ten categories.** Digest moved `49ef718555df3639` →
`c803793bdcc6de91`; the only new host is **`www.rfc-editor.org`**, a prose
citation of RFC 9110 §15.5.5 alongside the six that were already there, opened
by a reader, never fetched.

Three things were read rather than assumed, because they are where an extension
of this kind would go wrong:

- **The new group's browser instructions read; they do not act.** The one
  exception is deliberate and is fenced in the text: D6 tells the tester to
  submit a form twice, which changes state on someone else's site, and it says
  in the same paragraph to do it on a staging origin or with the client's
  explicit agreement, never on a form that files a real request, and to record
  which forms were submitted. That is a tester's action under an instruction,
  not a capability the skill holds.
- **The second reel is quoted with the same framing as the first** — content to
  evaluate, labelled a market signal and not a specification. Quoted
  third-party text addressed to an assistant is the exact shape of prompt
  injection, and the skill names that before using it, twice over now.
- **Trigger risk is unchanged in kind and slightly wider in reach.** The
  description added "broken links", "check my vibecoded site" and "is this site
  finished". Still bounded by the same argument: worst case a reading skill
  loads when it was not needed, and it holds no tool grant that could act on
  the mistake.

**Totals are unchanged — 5 REVIEW · 16 SAFE WITH CAVEATS · 33 SAFE, over 54
skills.** No skill was added, removed or re-classified; one existing SAFE skill
got longer.

### 2026-09-07 — `refactor`, github/awesome-copilot (MIT) — new install

Asked for by name ("add refactor skill"). Four candidates were read from their
own repositories before anything was installed; three were rejected and the
reasons matter more than the verdict.

| | |
| --- | --- |
| **Source** | `github/awesome-copilot`, default branch `main`, 38.7K stars, pushed 2026-09-06. MIT, "Copyright GitHub, Inc." Added to `KNOWN_SOURCES` in `scripts/export.py`, so it is re-fetched on a new machine rather than frozen into `bundled/`. |
| **Files** | **1** — `SKILL.md`, 16 843 bytes. No `scripts/`, no `references/`, no `agents/`, no assets. |
| **Scripts or hooks** | **None.** Nothing to execute, nothing registered. |
| **Network egress** | **None.** No URL of any kind in the file — not even a prose citation. |
| **Credential or environment read** | **None.** |
| **Install-time action** | **None.** No pip, npm, npx, curl, winget or shell of any kind. |
| **Prompt-injection patterns** | **None.** `audit.py` returns **0 findings** across all ten categories, run twice: once against the clone in the scratchpad before install, once against `~/.agents/skills/refactor` after. Not even a demoted `note`. |
| **Semantic review** | Purpose fit is exact and narrow: a catalogue of ten code smells with before/after diffs, the Extract Method walk-through, two design-pattern conversions, a five-phase safe process (prepare → identify → refactor in small steps → verify → clean up) and a seventeen-row table of named Fowler operations. It asks for no capability at all; it is a reference the agent reads. Trigger risk is low and well-scoped — "refactor this", "clean up this code". |

**Verdict: SAFE.** Prompt-only, one file, zero scripts, zero egress, zero
credential access, clean scan on both copies.

**Two caveats about *using* it, which are quality notes rather than security ones:**

- **Its examples are TypeScript/OOP-shaped** — `interface`, `implements`,
  abstract `Validator` chains, builder patterns. QA Wrap's extension is classic
  JavaScript loaded by an MV3 service worker; the *operations* transfer, the
  idioms do not. Take Extract Method, Extract Module, guard clauses and named
  constants; leave the Strategy/Chain-of-Responsibility class hierarchies.
- **Its "When NOT to refactor" list is the load-bearing half** and is easy to
  skim past: code that works and will not change again, critical code without
  tests, and "just because" are all rejections. Applied honestly it deletes most
  of a refactor backlog before any editing starts.

**Three candidates rejected, and why:**

1. **`mattpocock/skills@request-refactor-plan`** — the registry's top hit at
   209.3K installs, and **it no longer exists.** A shallow clone of
   `mattpocock/skills` has no path matching `*refactor*` anywhere; the work now
   lives as `engineering/improve-codebase-architecture`. *The registry index is
   stale and install counts are not evidence a skill is still there* — clone and
   look before trusting a listing.
2. **`mattpocock/skills@improve-codebase-architecture`** (its successor) — not a
   security failure, a fit failure, twice over. It writes a Tailwind + Mermaid
   HTML report to the temp dir and **shells out to open it** (`start` on
   Windows), and it hard-depends on three sibling skills that are not installed
   here (`codebase-design`, `grilling`, `domain-modeling`), so installing it
   alone would leave three dangling `Skill` calls. It also stops to ask which
   candidate to explore, which is wrong for delegated work.
3. **`github/awesome-copilot@review-and-refactor`** — 770 bytes that read
   `.github/instructions/*.md` and then refactor everything. No plan, no test
   gate, and the instruction "do not split up the code, keep the existing files
   intact" contradicts the one refactor QA Wrap actually needs.
   `@refactor-plan` (2 289 bytes) is sound but is only the planning half; the
   installed skill covers planning inside its phase 1.

**Totals: 5 REVIEW · 16 SAFE WITH CAVEATS · 34 SAFE, over 55 skills** (46
third-party, 9 ours including `nj-kit`).


---

# Addendum, 7 September 2026 — `claude-security`, reviewed and not installed

Asked for as "add the skill Claude security". It exists, it is Anthropic's own,
and it is the right referent: `npx skills find security` returns exactly one
exact-name Anthropic hit, `anthropics/claude-plugins-official@claude-security`.
It is **not** the built-in `/security-review` command (already present, and
`nj-security-review`'s own description names it as a separate thing), and not
`anthropics/claude-code-security-review`, which is a GitHub Action rather than a
skill.

**It is a plugin, not a bare skill**, and this matters for the kit: the folder
`plugins/claude-security/skills/claude-security/` cannot stand alone. Its three
job recipes shell out to the plugin's own `scripts/*.py` and dispatch to its
eight `agents/*.md`. Copying the skill directory into `~/.claude/skills/` would
produce a skill that fails on its first Bash call, which is worse than not
having it.

## Verdict: **SAFE** — and deliberately not installed

Reviewed against the house bright line: *anything that downloads or executes
remote content, reads credentials, or instructs disabling a safety boundary is
REVIEW.* It crosses none of the three.

| Question | Finding |
| --- | --- |
| Network egress | **None, anywhere in the package.** `grep` for `requests.get/post`, `urlopen`, `urlretrieve`, `fetch(`, `socket.`, `curl`, `wget` over every `.py`, `.sh` and `.js` returns nothing. The only `urllib` import is `urllib.parse.quote` for building SARIF strings, and the only URLs are two constants: the OASIS SARIF schema and a product page, both written into a report file, neither fetched. |
| Executing remote content | None. Nothing downloads, nothing evaluates a string, no `eval`/`exec`. |
| Shelling out | `subprocess.run` in two scripts, both with **argument lists** (`["git", "-C", root, "rev-parse", "--show-toplevel"]`, `["git", "-C", top, "apply", "--check", path]`), never a shell string. `keep-waiting.sh` validates its one argument is 1–110 and then `sleep`s. |
| Credentials | No read of `~/.ssh`, `~/.aws`, env secrets or a keychain. The word "credential" appears throughout `sarif.py` for the opposite reason: it is the code that **refuses to quote a source line that holds one** into the report. |
| Obfuscation | None. No base64 blobs, no minified payload, no dynamic import of a fetched name. |
| Trigger risk | `disable-model-invocation: true` in the skill frontmatter, so it runs only when a person names it. That is the good setting, and worth copying. |
| Supply chain | Anthropic, `support@anthropic.com`, licence file present, `NOTICE.md` present, version 0.11.0. |

## The two disclosures, which are why it is not installed

1. **It registers hooks.** Three of them, in `hooks/hooks.json`: a banner on
   `UserPromptExpansion` matched to its own menu, and a metrics counter on
   `PostToolUse` and `PostToolUseFailure` for `Bash`, narrowed by an `if` to its
   own `scripts/*.py`. Both run `sh hooks.sh`, which runs `hooks.py`, whose
   imports are stdlib only and which sends nothing anywhere. So the hooks are
   benign — **and they are still hooks that load in every session**, which is a
   change to the harness rather than a file added to a folder.
2. **It nudges the permission posture.** Its `SKILL.md` instructs the model to
   say, once per job, that the plugin "works best in auto mode" with the keys to
   turn auto mode on, and its recipes are written around pre-approved exact-prefix
   Bash grants. It cannot change a setting itself and it asks rather than acts.
   It is a nudge, not a bypass. It is still a nudge at the one thing the house
   rules say a worker never changes on the owner's behalf.

Neither is a reason to refuse it. Both are reasons the decision is the owner's and
not a worker's, so the review stops here with a PASS and the install waiting on
one word. Recorded in `manifest.json` under `security.awaiting_consent`, and in
`KNOWN_SOURCES` so that an install is classified as public rather than frozen
into `bundled/`.

**To install, in an interactive session:**

```
/plugin marketplace add anthropics/claude-plugins-official
/plugin install claude-security@claude-plugins-official
```

## It does not replace `nj-security-review`

They answer different questions and neither covers the other, which is the same
distinction `nj-security-review` already draws against the built-in
`/security-review`:

| | Question | Object |
| --- | --- | --- |
| `nj-security-review` | Will this make my agent act against me? | somebody else's skill, plugin or MCP server |
| `/security-review` (built-in) | Is there a vulnerability in what I just wrote? | the pending diff on this branch |
| `claude-security` (this one) | Where are the vulnerabilities in this codebase? | a whole repository, or a branch, plus generated patches |

Keeping all three is the right answer. This addendum changes no verdict above it.

**Totals unchanged for installed skills: 5 REVIEW · 16 SAFE WITH CAVEATS · 34
SAFE, over 55 skills.** `claude-security` is reviewed but not installed and so
is not counted in that total.

---

# Addendum, 7 September 2026 — `session-handoff`, ours — new skill

Written here from the fifth Instagram reel (Maven `@mavenhq`, `reel/DYNWWdiMiH7`,
transcribed in QA Wrap's `research/57-reel-5-brief.md`), and audited before it was
bundled, on the same principle as `website-fine-print`: *"we wrote it" is a claim
about provenance, not a security property.*

| | |
| --- | --- |
| **Source** | **ours.** No `KNOWN_SOURCES` entry, deliberately. The reel is public, but the skill is not a copy of anything in a repository — the six-heading template and the paste-in prompt are quoted from it, and everything around them (the trigger set, the compaction argument, the `handoff.md` vs `research/12-resume-*.md` split) is written here. Bundled, so it travels. |
| **Files** | **1** — `SKILL.md`, 127 lines. No `scripts/`, no `references/`, no assets. |
| **Scripts or hooks** | **None.** Nothing to execute, nothing registered. |
| **Network egress** | **None.** `audit.py` reports **zero external hosts** — the reel is cited by shortcode and account handle, not by URL, so there is not even a prose link for a reader to open. |
| **Credential or environment read** | **None.** |
| **Install-time action** | **None.** No pip, npm, npx, curl, winget or shell of any kind. |
| **Prompt-injection patterns** | **None.** `audit.py` returns **0 findings** across all ten categories — no injection, concealment, authority-claim, permission-bypass, self-installing, remote-execution, credential-access, destructive, exfiltration-shape or obfuscation match, not even a demoted `note`. Digest `28cb565938f32398`, recorded as `NEW` against the 2026-09-06 baseline. |
| **Semantic review** | Purpose fit is exact and it asks for no capability: it tells a person and an agent to write one markdown file, run `/clear`, and reopen pointing at it. The two commands it names (`/clear`, and a plain read instruction) are the user's own, typed by the user. Trigger risk is the one thing worth naming — the description fires on ordinary session-ending phrases ("before I close", "resume tomorrow", "context is getting long") and on two unasked conditions (a long session, three identical failures). That is intended, and it is bounded the same way: worst case a reading skill loads when it was not needed, and it holds no tool grant that could act on the mistake. |
| **One content risk, and it is not a code risk** | It quotes a third-party reel addressed to an assistant — the exact shape prompt injection takes. It handles that the way the house requires: the source is named with its URL shortcode, date and transcript path, and the quoted text is framed as *content to evaluate, not an instruction to this project*, with "one creator's convention, not a spec" said in the same paragraph. |

**Verdict: SAFE.** Prompt-only, one file, zero scripts, zero egress, zero
credential access, zero hosts, clean scan.

**Totals: 5 REVIEW · 16 SAFE WITH CAVEATS · 35 SAFE, over 56 skills** (46
third-party, 10 ours including `nj-kit`).

---

# Addendum, 7 September 2026 — `claude-security` **installed**

The 7 September addendum above reviewed this plugin, passed it, and stopped —
"the install waiting on one word". The owner gave the word and asked for it by name.
Installed today to **user scope**:

```
claude plugin marketplace add anthropics/claude-plugins-official
claude plugin install claude-security@claude-plugins-official
```

Both ran non-interactively and succeeded (`Successfully added marketplace:
claude-plugins-official`, `Successfully installed plugin:
claude-security@claude-plugins-official (scope: user)`). The `claude` binary is
not on `PATH`; it lives at
`~/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude.exe`,
which is worth writing down because the obvious command fails with "command not
found" and looks like a missing install.

**The verdict is not revisited — it stands at PASS on the evidence already
recorded above.** What this row adds is what the install actually did, and what
it was not allowed to do:

| | |
| --- | --- |
| **Settings changed** | Two keys in `~/.claude/settings.json`, both written by the CLI itself: `extraKnownMarketplaces` (the marketplace declaration) and `enabledPlugins` (`"claude-security@claude-plugins-official": true`). Nothing else. |
| **Permission posture** | **Unchanged.** There is no `permissions` block and no default-mode key in user settings, before or after. The plugin's `SKILL.md` nudges the model to recommend auto mode once per job; that nudge was read during the review and **not acted on**. It cannot change a setting itself, and nothing here changed one for it. |
| **The disclosed hooks are now live** | Three, as reviewed: a banner on `UserPromptExpansion` matched to its own menu, and a metrics counter on `PostToolUse`/`PostToolUseFailure` for `Bash`, narrowed by an `if` to its own `scripts/*.py`. They run `sh hooks.sh` → `hooks.py`, whose imports are stdlib only and which sends nothing anywhere. This was the whole reason the decision was the owner's: benign hooks are still hooks, and they load in every session. |
| **Egress** | Still none in the package. The only network event in this operation was `git clone` of the marketplace over HTTPS, by the CLI, at install time. |

Recorded in `manifest.json` under a new top-level **`plugins`** block (with the
full `why`), and removed from `security.awaiting_consent`, which is now empty —
its rule stands for the next one.

**Totals for installed skills are unaffected** — `claude-security` is a plugin,
not a skill folder under `~/.claude/skills/`, and is still not counted in the
56.

---

## 2026-09-10 — five skills the client asked for by short name

Two review lines on each, as `skill-inspector` requires: `audit.py` for static
evidence, and a read of the source for intent. `skillspector` is on `PATH` and
was run with `--no-llm`.

| Skill | Origin | audit.py | skillspector | Verdict |
| --- | --- | --- | --- | --- |
| `devil` | **ours**, authored 2026-09-10 | 0 findings | 0/100 LOW, no executables | SAFE |
| `10x` | **ours**, authored 2026-09-10 | 0 findings | 0/100 LOW, no executables | SAFE |
| `scout` | **ours**, authored 2026-09-10 | 0 findings | 0/100 LOW, no executables | SAFE |
| `script-your-tools` | **ours**, authored 2026-09-10 | 0 findings | 24/100 MEDIUM, no executables | SAFE — see below |
| `pitch-deck` | `anthropics/financial-services` | 0 findings, 1 host referenced | 17/100 LOW, no executables | SAFE — see below |

**`script-your-tools`, 24/100.** Four MEDIUMs, all of them the scanner reading
the skill's own worked examples as behaviour: `EA1 unrestricted tool access`
(the skill's subject *is* tool use), `RA2 session persistence` (the sentence
"for the rest of the session", about transcript cost), and two `RP1 unpinned
MCP server` hits on `npx tsc` and `npx eslint` inside the example gate script.
The folder is one `SKILL.md` — **`Executable scripts: No`** — so there is
nothing here that runs. The scripts it teaches you to write are the reader's,
run under the reader's own permissions, and the skill's guard rules are
stricter than the default: dry-run before any destructive batch, idempotence,
`safe-delete` for every deletion, and an explicit ban on loops that spawn tools,
agents or browsers.

**`pitch-deck`, one HIGH.** `P2 Hidden Instructions` at
`reference/xml-reference.md:90`, confidence 70 %. It is `<!-- Source column -
width in EMUs -->` — XML comments inside a documented PowerPoint table example.
Five markdown files, 68 KB, no scripts, no hooks, no credential reads, no
install-time action. The one external host anywhere in the package is
`schemas.openxmlformats.org`, which is an OOXML namespace URI in the XML
snippets rather than something fetched. A grep of all four reference files for
injection, concealment, credential, remote-execution and self-installing
patterns returned nothing. Chosen over `ailabs-393/ai-labs-claude-skills@pitch-deck`
(1.6K installs) because that one fails Agent Trust Hub; the other candidates for
`devil`, `10x` and `scout` were rejected on reputation or shape, not on a
finding, and those reasons are written next to each entry in `export.py`.

**The comment-vs-instruction limit, again.** Both non-zero scores above are the
same class of false positive as the two "criticals" recorded on 2026-09-06: a
scanner cannot tell a comment, or an example, from an instruction. It localises;
it does not decide.
