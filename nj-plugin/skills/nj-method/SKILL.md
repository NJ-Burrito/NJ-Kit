---
name: nj-method
description: 'A default method for every request: analyse the ask, look up installed skills before improvising, plan with named checkpoints, execute, review against what was asked. Its routing table answers which skill applies, Arabic or English. Checkpoints are files, not messages.'
---

# The method

**This is the default way of working, set in `~/.claude/CLAUDE.md`** — every
session, every message, not only large jobs.

Six steps. The value is not the sequence — it is that each step leaves something
on disk, so a change at step 5 does not cost steps 1–4 again.

## Proportionality is part of the method

Step 1 is allowed to conclude "this is trivial" and answer directly; that *is*
the method running. Two things are never skipped, whatever the size:

- **targeted routing** — use the known relevant skill/tool instead of
  improvising, and without loading the whole catalogue;
- **the review against what was asked**, before saying it is done.

A method performed rather than followed costs attention and buys nothing.

## The session does the work (plain mode, 2026-10-30)

The main session analyses, routes, plans, builds, fixes, runs the scripts and
reviews, itself, on the normal model (Sonnet 5.5 unless the owner sets
another). There is no Lead/worker split, no helper tier, no receipts, relay,
ledger or interpreter. `nj-delegate`, `nj-agent-ops`, `nj-supervise` and
`nj-director` run only when the owner names them.

Order of work:

1. **Deterministic first**: scripts, CLI, parsers, tests, static analysis and
   focused greps when no model judgement is needed.
2. **Reuse evidence**: existing handoffs, gate logs, diffs, prior artefacts.
3. **Do it in this context.** A subagent is used only when the task really
   needs parallel work (independent pieces, a broad search, or a crew a skill
   defines, such as `nj-multimedia` or a named `nj-qa` run). Its brief carries
   exact paths, commands, constraints and the standing rules it needs;
   evidence already extracted is handed over by path; it leaves a checkpoint
   on disk; the session checks the smallest diff or gate line that settles a
   claim, never repeats the subagent's exploration.

Pick effort from the reasoning the stage needs (2026-09-16: lowest cost that
is good enough), and keep quality gates independent of whoever produced the
output.

## 1. Analyse before reaching for anything

Name the deliverable, its language(s), its audience, and what "done" means. A
ministry submission, a client manual and an internal note are three different
documents from the same facts. State the reading if it is ambiguous rather than
picking silently.

## 2. Use relevant skills and tools — do not load the catalogue

| Deliverable | Reach for |
| --- | --- |
| Document, SRS, manual | `doc-coauthoring` → `nj-pdf-typography` → `nj-proofread` |
| Arabic anything | `nj-proofread` before delivery, always |
| Workflow figure | `nj-workflow-diagram` |
| Diagram from code (architecture, sequence, ER, state) | `nj-workflow-diagram` § Mermaid: write `.mmd` from the code, render with `mmdc` in Thmanyah and the brand palette |
| Verifying a document against the built system | `nj-doc-verifier` |
| Knowledge book, study guide, certification prep, handbook, mentor path (multi-page, sourced, PDF) | `nj-knowledge-book` (on `nj-evidence`; runs its own 5-POV devil council) |
| Commercial, promo, launch or brand film, ad, teaser, reel made to sell (إعلان، فيديو تسويقي، كوميرشال) | `nj-multimedia` (kit): creative ∥ marketing crews → director + `nj-devil` → one owner stop (proposal + keyframe boards) → sound ∥ motion → `mm.py` / `frame_probe.mjs` gates → render; builds on `hyperframes`, `nj-writer`, `nj-music`, `nj-impact-copy` |
| Video, film, animation (not a commercial) | `hyperframes` (entry point); a narrated style film from references: `nj-style-film` |
| Narration, voiceover | `nj-writer` § voice styles (`NARRATION.md` §11): Kore on Gemini 3.1 Flash TTS via OpenRouter, registered style from `voice-styles.json`, `voice_style_gate.py` before delivery; then `nj-voice-clean` (`nj-kit` `house_style.tts_engine`) |
| Cut recorded footage | faster-whisper transcript → Claude cut list → `auto-editor` / ffmpeg (`house_style.footage_cut`) |
| Scan a web app we own | ZAP baseline (zaproxy docker image), then Strix (Claude, `STRIX_TELEMETRY=0`, owned targets only) — `nj-security-review` § Scanning a live web app we own |
| Image to video | not available on this laptop; animate stills with HyperFrames / Remotion (`house_style.image_to_video`) |
| Music or SFX under a render | `nj-music` |
| QA automation | `playwright-best-practices`, Playwright MCP, the project's own e2e skill |
| Jira: read / analyse a ticket, file Bugs, QA re-check, tracker | `nj-jira` |
| Jira ticket or open Bugs into runnable checks | `nj-jira-to-automation` |
| After testing a service / end of a work session: file Bugs + untestable Tasks + blocker, nj-rank Done Tasks, outputs to QA, boss email AR+EN (سكّر الشغل، ارفع النتائج) | `nj-wrapup` |
| Create an automation-tests folder (portable, reports, PDF, Docker) | `nj-automation-suite` |
| Whole QA round: Jira -> notes -> walks -> Bugs -> re-check -> Docker | `nj-qa-pipeline` |
| Agent crew testing a service's notes, only when the owner names NJ-QA | `nj-qa` |
| An agent opens a browser window, in any project | `nj-agent-halo` |
| Any chart, dashboard, KPI row or report with charts | `nj-chart` |
| UI, design, theming | `frontend-design`, `ui-ux-pro-max`; check with the project's own deterministic gates (layout probe, contrast script, glyph coverage) and `web-design-guidelines` |
| UI with no set direction | name the defaults to avoid (e.g. cream background, italic accent words, "01/02/03" labels, monospace labels, pill buttons) and extend the list from the first result; never just "avoid a generic look" |
| Captions, text cards, feature lists, pitch or summary copy | `nj-impact-copy` — bold anchor, separator, one true number |
| A website before it ships | `nj-site-audit` |
| Social media (Instagram, X, YouTube, TikTok, Reddit…) | `agent-reach doctor`, then that channel; logged-out only, never its `transcribe`; Instagram = yt-dlp + local faster-whisper (`nj-kit` manifest `house_style.social_media`) |
| Library docs | `context7` MCP — current, not remembered |
| Directing animation: shot brief, character acting, animatic, beat timing, Rive / Theatre.js direction | `nj-animation-direction` |
| Nothing fits | `skill-creator`, if the thing is worth keeping |

If a search turns up nothing usable, say so instead of pretending a generic
approach is a considered one.

## 3. Plan, and make the plan inspectable

Short, concrete, ordered. Name the checkpoint each step produces. A plan whose
steps cannot fail separately is not a plan.

## 4. Execute

Follow the plan; deviate out loud when reality disagrees. Verify as you go — a
build that "should work" has not been tested.

## 5. Review against the request, not against the work

Re-read what was asked and check each item off. Say plainly what was not done
and why. Report failures with their output; never round a partial result up.

**Verification the client would otherwise do is a gate in the pipeline, not a
courtesy** (session review 2026-09-17: a day that shipped unverified output came
back as 96 redeliveries against 16 deliveries, all faults a machine gate could
have caught in seconds). "Run once, no self-verification" turns off a *person*
re-checking a machine's output by hand; it does not turn off the machine gates —
a leak assertion, a delivered-copy check, a build's own refusal on bad input —
that are part of the single run.

## 6. Checkpoints

**A checkpoint is a file, not a message.** Any stage that took real effort leaves
an artefact the next stage reads, so a correction re-runs one stage.

- Documents: source → `.md` → styled HTML → PDF. Fixing wording re-runs the
  render, not the research.
- Video: script → storyboard → composition → render. The render is the expensive
  step and must never be where edits are made. A commercial adds the crew
  folders before the script (`nj-multimedia`: `creative/`, `marketing/`,
  `proposal/`, `boards/`, then `audio/` and `build/`).
- Voiceover: script file → audio. Keep the script; regenerate audio freely.
- QA: page objects separate from specs, so a selector fix is one file.
- Anything long: write it down before building on it.

Name where each artefact is when handing work back, so a revision request can
point at a stage. Before any checkpoint that is expensive to redo (a recording, a
filing, a long render), rehearse at the cheapest fidelity first. Inside
The owner's deliverable pipelines the Owner exception in `~/.claude/CLAUDE.md` governs
instead: one run, and one private rehearsal only when the pipeline itself is new or
changed (2026-09-29); the machine gates still run.

## Language

Arabic and English are both first-class. Match the language of the deliverable,
not of the conversation — a request in English can be for an Arabic document. For
bilingual work the pair is the unit: a fix to one side that leaves the other
stale is worse than the original error.
