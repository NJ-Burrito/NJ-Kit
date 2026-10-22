---
name: nj-method
description: 'the owner''s default method for every request: analyse the ask, look up installed skills before improvising, plan with named checkpoints, execute, review against what was asked. Its routing table answers which skill applies, Arabic or English. Checkpoints are files, not messages.'
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

## Director routes work; workers are not the default

The main session owns analysis, routing, planning, review and the answer, and
may execute bounded deterministic or targeted work itself. **Default worker count
is zero.** A subagent is used only for a measurable benefit: context isolation,
cheaper-model routing, useful parallelism, independent verification, or a
specialised capability.

Order before spawning one:

1. **Deterministic first** — scripts, CLI, parsers, tests, static analysis,
   focused greps when no model judgement is needed.
2. **Reuse evidence** — existing handoffs, gate logs, diffs, prior artefacts.
3. **Bounded direct work** — a few targeted operations when the output is short
   and that is cheaper than briefing a worker. Not broad repository reading.
4. **Delegate only when justified.** `nj-delegate` §0 (NJ Governance v3) is the one
   statement of this — do not restate it here. Two clauses decide it: **§0.0**, the default is
   *no* governance at all when one context can hold the task, and **§0.6**, the worker count is
   the number of disjoint write-sets on the critical path, so it is derived and auditable rather
   than felt. The main session is the sole orchestrator; workers never delegate to each other,
   and a worker may **challenge** a fact the brief got wrong (§0.2).

**Tier choice comes from the REASONING the stage requires**, not from the fact
that code is edited, that the prose is Arabic, or that the output goes to a
client (2026-09-16, the owner: *lowest-cost tier that is good enough + effort*).
Tiers: **DETERMINISTIC / FREE-LOCAL / ECONOMY / STANDARD / FRONTIER** — route to
the least expensive one with demonstrated reliability, and keep quality gates
independent of the tier that produced the output. Every brief names an **effort**
level (`low` / `medium` / `high`, set by the stage, not the tier) and a **token
and context budget**; tool calls are a runaway cap only. **`nj-delegate` §3 is
the single source of truth** for the ladder, the two proved downgrades (scoring
reviews and authoring-to-a-spec are STANDARD), the two upgrades, and the class
budgets — do not restate it here.

When delegation is justified, the brief carries only the context it needs: exact
paths (sections, symbols or line ranges, not whole files), commands,
constraints, budgets, the relevant standing rules. Evidence already extracted is
handed over by path; two workers never rediscover the same structure. The worker
leaves a checkpoint on disk. The director verifies proportionally to risk: the
smallest targeted diff, gate line or evidence needed to adjudicate a material
claim, never a repeat of the worker's exploration.

## 1. Analyse before reaching for anything

Name the deliverable, its language(s), its audience, and what "done" means. A
ministry submission, a client manual and an internal note are three different
documents from the same facts. State the reading if it is ambiguous rather than
picking silently.

## 2. Use relevant skills and tools — do not load the catalogue

| Deliverable | Reach for |
| --- | --- |
| Document, SRS, manual | `doc-coauthoring` → `pdf-typography` → `arabic-english-proofreading` |
| Arabic anything | `arabic-english-proofreading` before delivery, always |
| Workflow figure | `workflow-diagram` |
| Diagram from code (architecture, sequence, ER, state) | `workflow-diagram` § Mermaid: write `.mmd` from the code, render with `mmdc` in Thmanyah and the brand palette |
| Verifying a document against the built system | `srs-verifier` |
| Video, film, animation | `hyperframes` (entry point) |
| Narration, voiceover | `nj-writer` § voice styles (`NARRATION.md` §11): Kore on Gemini 3.1 Flash TTS via OpenRouter, registered style from `voice-styles.json`, `voice_style_gate.py` before delivery; then `voice-clean` (`nj-kit` `house_style.tts_engine`) |
| Cut recorded footage | faster-whisper transcript → Claude cut list → `auto-editor` / ffmpeg (`house_style.footage_cut`) |
| Scan a web app we own | ZAP baseline (zaproxy docker image), then Strix (Claude, `STRIX_TELEMETRY=0`, owned targets only) — `nj-security-review` § Scanning a live web app we own |
| Image to video | not available on this laptop; animate stills with HyperFrames / Remotion (`house_style.image_to_video`) |
| Music or SFX under a render | `bg-music` |
| QA automation | `playwright-best-practices`, Playwright MCP, the project's own e2e skill |
| UI, design, theming | `frontend-design`, `ui-ux-pro-max`; check with the project's own deterministic gates (layout probe, contrast script, glyph coverage) and `web-design-guidelines` |
| UI with no set direction | name the defaults to avoid (e.g. cream background, italic accent words, "01/02/03" labels, monospace labels, pill buttons) and extend the list from the first result; never just "avoid a generic look" |
| Captions, text cards, feature lists, pitch or summary copy | `impact-copy` — bold anchor, separator, one true number |
| A website before it ships | `website-fine-print` |
| Social media (Instagram, X, YouTube, TikTok, Reddit…) | `agent-reach doctor`, then that channel; logged-out only, never its `transcribe`; Instagram = yt-dlp + local faster-whisper (`nj-kit` manifest `house_style.social_media`) |
| Library docs | `context7` MCP — current, not remembered |
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
  step and must never be where edits are made.
- Voiceover: script file → audio. Keep the script; regenerate audio freely.
- QA: page objects separate from specs, so a selector fix is one file.
- Anything long: write it down before building on it.

Name where each artefact is when handing work back, so a revision request can
point at a stage. Before any checkpoint that is expensive to redo (a recording, a
filing, a long render), rehearse at the cheapest fidelity — nj-delegate
`reference/high-rework.md` § "Rehearse before the expensive stage". Inside
The owner's deliverable pipelines the Owner exception in `~/.claude/CLAUDE.md` governs
instead: one run, and one private rehearsal only when the pipeline itself is new or
changed (2026-09-29); the machine gates still run.

## Language

Arabic and English are both first-class. Match the language of the deliverable,
not of the conversation — a request in English can be for an Arabic document. For
bilingual work the pair is the unit: a fix to one side that leaves the other
stale is worse than the original error.
