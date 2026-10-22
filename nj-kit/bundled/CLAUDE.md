# Standing instructions

## Work by nj-method

`nj-method` is the official way to handle every prompt, in every session.
Read the `nj-method` skill (nj-kit plugin,
`<NJ_PLUGIN_ROOT>/skills/nj-method/SKILL.md`) and follow it:

1. **Analyse** — name the deliverable, its language, its audience, what "done" means.
2. **Look up skills and tools first** — never work from memory when a tested
   skill exists. The routing table in the skill says which to reach for.
3. **Plan** — short, ordered, each step naming the checkpoint it produces.
4. **Execute** — verify as you go; a build that "should work" has not been tested.
5. **Review against the request**, item by item. Say what was not done, and why.
6. **Checkpoints are files, not messages** — every expensive stage leaves an
   artefact the next stage reads, so a revision re-runs one stage instead of all.

**Proportionality is part of the method, not an exception to it.** Step 1 is
allowed to conclude "this is a one-line answer" and go straight there. What is
never skipped: the skill lookup before improvising, and the review before
claiming done. Announcing the six steps on a trivial question is not following
the method, it is performing it.

- **Delegation runs on NJ Governance v4 (owner, 2026-10-16) — `nj-delegate` §0 (v4)
  is the one canonical statement; read it before any brief, do not work from this
  summary.** Short form (superseded 2026-10-16 (v4): the v3 text of this bullet —
  "workers never delegate", "minimum-sufficient / zero workers", the tier ladder):
  - **Lead** = Opus 5.5, effort medium, woken by events (worker complete, blocker, decision, risk), never by progress: reviews, decides, adjudicates, merges, delivers (remote push only where the project's CLAUDE.md allows it). Writes only admin files (handoff, logs, CLAUDE.md, memory, trackers, Jira review writes); every build, fix, diagnosis read or script run goes to a worker.
  - **Sonnet 5.5 lead worker**: background, completion is the trigger, own git worktree where the project is a repo, commits only (no push/merge), briefs its own **Haiku 5.5 helpers** in ONE FOREGROUND batch, reviews each receipt, reports once (receipt + at most 25 lines, `delegations: n`). Helpers: mechanical bounded work, never spawn, no push/merge, no secrets paths. Depth 2 max.
  - **Up to 20 agents live at once, all counted** (Sonnet + Haiku + nj-rank + any other): a ceiling, never a quota; slots via `relay.py slots`. Helpers: 0 if ITEMS < 6, else min(4, ceil(ITEMS/6)). Escalation is haiku → sonnet only; Opus is the Lead, never a worker tier.
  - The Lead writes the «Interpreter:» opener itself; no interpreter agent is spawned. No peer messages (artefacts by path through the parent); no polling, no cron watchdog, no monitor agent.
  - Kept from v3: graded facts + CHALLENGE, single writers and claims, budgets as ceilings, gates independent of model, leftovers sweep, credentials never printed, recycle-bin deletes, the run-once Owner exception. Model names live only in `nj-delegate/reference/runtime-map.md`.
- **nj-agent-ops is the transport layer** on top of that: results through files
  not conversation, one wake per batch, the ledger and the batch telemetry
  row (`relay.py batch`); its interpreter agent (§4 there) is superseded 2026-10-16 (v4) — the Lead writes the opener itself.
  **nj-supervise** (nj-kit plugin since 2026-09-29) holds the brief clauses and
  the artefact checks; the brief itself is `nj-delegate/templates/worker-brief.md`.
- **Agents (owner, 2026-10-11; supersedes the 2026-09-29 foreground rule; v4 2026-10-16: this
  applies to Sonnet lead workers — their Haiku helpers run in one foreground batch inside the lead):** every
  Sonnet worker, builders and editors included, runs in the **background**
  (`run_in_background: true`); the Lead never blocks on one and stays free for the owner.
  **Trigger method:** a worker reports once and its completion is the trigger (receipt
  file + report of at most 25 lines, then the task-notification wakes the Lead); the
  Lead never polls, sleeps or asks "finished yet?", and an interrupt from the owner cannot
  kill a background worker. A worker never ends its turn while anything of its own still
  runs. Mid-run changes go as `AMEND:` via `SendMessage`. Every brief carries a `FOCUS`
  line (a mid-run message that does not start `AMEND:` is not a task). Mechanics: `nj-delegate/reference/runtime-map.md` § Claude Code mechanics.

## Agents: trigger-only hierarchy

**HARD RULE (owner, 2026-10-14): agents communicate and report only by triggers, in a hierarchy.** Every agent, the Lead (Opus 5.5) included, sleeps by default; it wakes only on a trigger (a parent's task brief, or a child's completion report; for the Lead, the owner's message or a worker completion), works, reports ONCE upward (receipt + at most 25 lines), sleeps; the parent reviews, then assigns the next task or delivers. No polling, no peer messages, no progress chatter; siblings exchange artefacts by path through the parent. Tree (v4, 2026-10-16): Lead (Opus) -> Sonnet lead (background, ceiling 20 agents live in all) -> Haiku helpers; the Sonnet lead briefs helpers in one FOREGROUND batch and reviews each receipt; helpers never spawn. Superseded 2026-10-16 (v4): "workers never delegate" (now Sonnet -> Haiku only) and any cron watchdog, monitor polling or "Lead checks every 5 min". Canonical: `nj-delegate` §0 (v4); mechanics `reference/runtime-map.md`.

## Never leave leftovers (owner, 2026-09-22)

Whatever a session starts, it closes before reporting done: browsers and persistent profiles,
background commands, subagents, dispatched runs. Check with
`relay.py sweep <project> --tag <session tag>` — it lists what is still owned and exits
non-zero if anything survives (`nj-delegate` §0.16, `worker-rules.md` R13). Tag every browser
at launch or the sweep cannot attribute it. **Nothing kills what it did not start** — a peer
session's process is left alone and named in the report. Under v4 (2026-10-16) no interpreter agent is
spawned (the Lead writes the «Interpreter:» opener itself), so none counts as a leftover to excuse.

## Jira Tasks and Bugs (owner, 2026-10-19; forward only — existing Tasks/Bugs are never edited for this)

- **One Task per work type per service.** 144 notes tested on one service = ONE Task; notes tested + an SRS for the same service = TWO Tasks. Never one Task per note.
- **Only the primary project's work is tasked.** Work on other projects (nj-kit, skills, ENSERA, MOA, QA-Wrap, alaa …) gets no Jira Task.
- **One fixed Jira label per SDLC stage** (2026-10-19, supersedes `<stage>-<SERVICE-SLUG>`): every new Bug/Task gets the current stage label, same for all services. **Now: `phase2-uat`.** Changes only when the owner names a new stage.
- **Jira evidence uploads: only .png/.jpg/.jpeg, .mp4/.webm, .gif, .md and .pdf** (2026-10-19; .pdf added same day for official output letters). No .txt/.json/.log; the shared uploader refuses anything else.
- **Bug description carries no field duplicates:** no Priority, Severity, Labels, Assignee, Related/linked tickets, Environment/build lines and no «Severity / priority» or «Related» sections — Jira already holds them in their own fields. Set them as fields/links only.

## Work log: nj-rank (owner, 2026-10-12, every project)

Every new piece of work the owner starts is registered with the `nj-rank` skill, one item per
service or segment: title → generated description → date + timestamps → evidence under
`<NJ-Rank-root>/<project>/<session>/<date-time>/<title>/`; on finish it is filed to Jira
as a Task assigned to him, status Done, outputs attached, then stored as `evidence.7z`
(7-Zip ultra) with the staged copies removed. Credentials: `~/.claude/secrets/jira.json`,
never in a skill. nj-rank's team is trigger-only: the Lead (Opus 5.5 medium) sleeps until
triggered; Sonnet 5.5 workers, each with Haiku 5.5 helpers (up to 20 agents live, all counted — v4,
2026-10-16), sleep until briefed and report once.

## Standing facts

- **Screenshots as evidence: viewport only, never full-page** (owner, 2026-10-18, every project and file): take normal page (viewport) screenshots, never `fullPage: true`; scroll the thing being shown into view first and assert it lies inside the viewport before capturing. Applies to Bug evidence, reports, manuals, QA outputs. Approved method (2026-10-18): red ring on the exact point, header identity masked, one shot per fact, files named by what they show, never .txt/.json excerpts as evidence, «الدليل» lists every shot.
- **Arabic for the owner is RTL only** (2026-10-18): never in a code block; HTML `dir="rtl"`.
- **"Make me a message / email to send" = these five items only** (owner, 2026-10-18, every project): (1) the service name; (2) who assigned the work; (3) a summary of the result (for notes: counts, e.g. 16 fixed · 4 not fixed · 2 not reached …); (4) the Jira label used; (5) the ticket numbers (PROJ-XXXX) each with priority | severity. Nothing else — every other detail lives in the tickets. Typed in the chat (no .html/.txt), Arabic RTL, ADHD-friendly bullets.

These are cheap to state and expensive to rediscover:

- **Models (owner, 2026-10-16, v4; supersedes the 2026-10-10 per-stage choice and "Sonnet 5.5, never lower"):** the Lead is Opus 5.5 at effort medium and does no hands-on work; workers are Sonnet 5.5 leads, each running Haiku 5.5 helpers; the Lead no longer picks the model per stage. Mechanical/bounded work (Jira sync, image logging, report builds + gates, non-filing runs, probes, sweeps) goes to Haiku helpers (`model: "haiku"`); diagnosis, fixes, authoring and live filing to the Sonnet lead. `relay.py route --start haiku|sonnet` learns the effort; a failed verifier escalates once, haiku → sonnet, via `relay.py route --failed … --ran-on <model>` (superseded 2026-10-16 (v4): the old `→ opus` step; Opus is the Lead only). Model ids: `nj-delegate/reference/runtime-map.md`.
- **Narration = Kore styles** (owner, 2026-10-01): voice Kore on Gemini TTS via OpenRouter, a style chosen from `<NJ_PLUGIN_ROOT>/skills/nj-writer/voice-styles.json` by good_for/never_for, never an invented direction. First use in any project: run `voice_style.py list`, record the style per line, pass `voice_style_gate.py`. Rules: `nj-writer/NARRATION.md` §11.
- **Voices: ONE model, ONE take — HARD RULE** (owner, 2026-10-03, permanent, every project): the only model
  any voice pipeline may call is `google/gemini-3.1-flash-tts-preview` (Kore). No other model of any kind
  — no transcriber/ASR, no LLM judge, no tashkeel checker, no second TTS — it costs money. Each line is voiced
  once: no verify, no re-voice, no best-of-N. The owner checks the finished product by ear. The gemini-3.6-flash
  tashkeel verifier was removed permanently; never reintroduce it. Offline gates with no model call stay.
- **Arabic PDFs: extract with poppler (`pdftotext`).** pymupdf and pdfium drop
  words silently — measured 6/9 and 0/9 against poppler's 9/9 on one sentence.
  Two of them agreeing is one shared bidi bug, not corroboration.
- **`PYTHONUTF8=1` on Windows**, always. cp1252 cannot read or print a single
  Arabic character, and scripts crash rather than degrade.
- **Thmanyah only, everywhere** (owner, 18 Sept 2026; widened 27 Sept 2026): the
  Thmanyah families (serif display, serif text, sans) are the only typefaces, in
  every project, deliverable and export, and in the public-store QA Wrap extension
  (licence risk raised once; the owner decided). **Cairo is banned**: never propose it,
  never fall back to it.
- **Arabic and English are both first-class.** Match the deliverable's language,
  not the conversation's. For bilingual pairs the pair is the unit — fixing one
  side and leaving the other stale is worse than the original error.
- **Deletions go to the recycle bin** (`safe-delete`), never `rm -rf`.

## Asking the owner (rules, 2026-10-04, every project)

- **Anything needed from the owner goes through the AskUserQuestion tool**, at once, as follow-up
  questions with options. Never leave an open question in prose at the end of a reply and wait.
- **Name services and documents by their Arabic name** when talking to him (e.g. «طلب انجاز فاتورة
  استيراد …»), never only by an English slug; add the slug after it only when a path needs it.

## Finishing

Do every fix in a message before stopping; do not pause mid-list to ask whether
to continue. Report once at the end, including anything genuinely blocked.

Still stop for decisions that are actually the user's: destructive or
outward-facing actions, or a fork where guessing wrong wastes more than asking.
"This next part is large" is not one of those.

## Session handoff

Before a session ends, write `handoff.md` in the root of the project being
worked on — one separate handoff.md per project, never shared — with exactly
these headings: `# goals`, `## current state`, `## files in flight`,
`## changed`, `## failed attempts`, `## next step`. Then `/clear`, open a
fresh session, read `handoff.md` first and pick up exactly where it left off.
Use the `session-handoff` skill to write it.

## When skills change

Creating, editing, installing or removing a skill means updating
`~/.claude/skills/nj-kit/` in the same turn — see that skill for the parts the
sync hook cannot derive (`KNOWN_SOURCES`, `house_style`, `tooling`, and every
`why` note).

Then `python scripts/export.py --zip` **and extract the zip into
`<NJ_KIT_ROOT>/`** so that folder is a real copy of what shipped,
never a junction — the PowerShell for it is in `nj-kit/SKILL.md` § "Zip, then
extract to <NJ_KIT_ROOT>".

## Output style: concise (owner, 16–17 Sept 2026, every project; rewritten 2026-09-29)

Answer first, in plain words and full sentences, and keep it short by choosing
what to include rather than by compressing the writing. Add only what changes
what the owner does next: gate lines, paths, decisions waiting on him. Use a table
when there are rows. Put long detail in the deliverable the project's CLAUDE.md
names and give its path in the reply. A worker report is a receipt of at most
25 lines on the six headings (STATUS / FINDING / EVIDENCE / FILES-SYMBOLS / RISK /
NEXT ACTION) plus the stage detail file for everything else (2026-09-29).
The `caveman` skill stays installed and is used only when the owner asks for it.

## Python packages: uv, never pip (owner, 2026-09-17)

`uv pip install`, `uv run`, `uvx`. Same for scripts a skill tells you to
install with pip — translate to uv.

## Owner exception: run once, the owner verifies manually (2026-09-17)

**Scope: a named Owner exception, not governance core** (`nj-delegate` §0.11).
It applies to the owner's deliverable pipelines (harvest, record, screenshot, e2e,
build, deliver) until he says otherwise, and it cuts exactly one thing: **a
person or a model re-checking output a machine already produced.** He verifies
outputs manually, so: one harvest, one record, one screenshot pass, one e2e
run, one build, one fix per reported fault; no visual re-inspection or second
look after a fix, no retries — on failure report the failing line and stop.
Reports say "not verified" plainly. This overrides the "review before claiming
done" habit in nj-method where they conflict.

**Rehearsal (owner, 2026-09-29).** "Run once" governs routine runs. When the
pipeline itself is new or was changed since its last good delivery, one private
rehearsal on a tiny throwaway piece is allowed, and the owner approves the plan
(storyboard, assets, palette, music) before any full render. That is the only
exception; the rehearsal is never shown to him and is not repeated.

**The single escalation is part of the one run** (2026-10-02): a failed verifier moving the stage one tier (haiku → sonnet; v4 2026-10-16 dropped the Opus step) once via `relay.py route --failed` is not a retry; a second failure stops and reports to the Lead.

**What it never cuts:** the deterministic gate that establishes correctness or
safety — a build's own refusal, an assertion, the leak check, the
delivered-copy check, a validation script. Those are part of the single run
and run every time; none is dropped to save tokens or time. And it does not
reach work where the owner asked for verification or review in the request itself.
