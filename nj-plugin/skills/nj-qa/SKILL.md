---
name: nj-qa
description: "NJ-QA: the owner's agent-crew method for testing a service's Jira notes on the live system, with one Opus leader per service, Haiku harvesters, one Sonnet tester per route and Haiku scavengers hunting unlisted defects, ending in a preview he decides on. Use ONLY when the owner names it: NJ-QA, nj-qa, run NJ-QA on these tickets, اختبر بطريقة NJ-QA. Any other notes testing stays in plain mode (nj-jira, nj-qa-pipeline)."
---

# NJ-QA: test a service's notes with an agent crew

> **What ships here:** the method, the route protocol and the gate scripts (`scripts/nj_qa.py`, `tokens.py`, `jira_refresh.py`, `creds.py`, with tests). The review hub app, its MCP server (`mcp/cli.mjs`) and the `nj-qa-*` agent definitions are the author's own and are not part of this kit: define your own agent types (or use general-purpose agents) and read `review.json` with any viewer. Credentials come from your own `NJQA_DATA/credentials/local.json`, never from the kit.

The owner's method (2026-11-09). It runs only when he names it; everything else stays in plain mode. Inside a run the hierarchy below is his explicit order, and the leader's review of agent reports is part of the method, so the plain-mode rule and the "no re-checking" rule do not apply here.

The method exists to test every note in one go: notes are ordered by the stage where the system can first show them, then walked on as few fresh tickets as possible, with nobody idle while somebody else works.

## The crew

| Role | Model | Agent type | Life | Count |
|---|---|---|---|---|
| Director | Opus 5.5 (this session) | - | no limit | 1, directs the leaders |
| Leader | Opus 5.5 | `nj-qa-leader` | no limit | 1 per service |
| Harvester | Haiku 5.5 | `nj-qa-harvester` | 30 min | 1 per service: Flowable, then applicant screens, then back office |
| Tester | Sonnet 5.5 | `nj-qa-tester` | 30 min | 1 per route of notes |
| Scavenger | Haiku 5.5 | `nj-qa-scavenger` | 30 min | as the leader decides |

- **At most 2 services at once.** A third starts when one finishes.
- **Everyone runs in parallel.** A leader sends each batch as one message, so its agents all run at once. Inside a batch they pass facts through files (`harvest/`, `tracker-live.md`), so nobody waits on anybody.
- **Everyone sleeps until triggered:** an agent, a timer, a task or an event. Nobody polls. A script waits so that no model has to (a background command, `Monitor`).
- **Harness limit (rehearsed 2026-11-09):** an agent's own Agent calls block it until the whole batch returns, even with `run_in_background`, and it cannot message them meanwhile. A leader therefore wakes once per batch, not once per worker, and reviews in batches. Workers enforce their own 30 minutes with `lease-left`.

## Director: what this session does

1. **Refresh the tickets:** `python -X utf8 scripts/jira_refresh.py KEY ... --out <RUN> --prev <last harvest> --creds <credentials file>`. Read `changes.md`; a new sub-task or changed note goes into the preview before testing.
2. **Prepare each service folder** `<RUN>/<KEY>/`: `raw/`, `attachments/`, and `decisions.md` holding every decision the owner has already made on these notes. Leaders treat those as settled.
3. **Create the service Task** when the project's standard asks for one (for example `nj-jira/references/uat-notes-standard.md` §2, JQL dedupe first). Leaders never write to Jira.
4. **Start one leader per service**, in the background, with the service folder path.
5. **Approve each route plan** when a leader reports it: check it against the route protocol below, and let work continue at once. The plan stays visible to the owner in the preview, and he can interrupt at any time.
6. **Start one Batch Monitor per batch** (`nj-qa-batch-monitor`, Haiku, background, no time limit; brief: RUN, batch n, the service keys, the session folder, the CLI path). Its watcher keeps the hub's live data current and raises a Windows notification for every OTP or missing-data request, so the `needs-nader-*.md` files reach the owner without a model polling. The director's own `Monitor` until-loop on `needs-nader-*.md` stays as the fallback. Tell him immediately, naming the service in Arabic.
7. **Receive each leader's review.** The leader publishes `<S>/review.json` with `nj_qa.py publish` (patch scan, preview check, thumbnails). Tell the owner the service is ready (or open the review hub); he decides in the hub, one click per item. Read his decisions and open questions through MCP (`read_decisions`, answer a question with `set_decision` and `answer`), and export what to file with `export_decisions` (`bugs-approved`). Then act on exactly those, with the project's filing tools, and run the tracker.
8. **Close out:** promote lessons that apply beyond one service from `<RUN>/lessons.jsonl` into `references/lessons.md`; nothing left running (browsers, agents, background commands); `nj-rank` against the service Task; the five-item message if he asks.

## Window colours (cosmetic, for the owner's eyes)

Machine rule, skill `agent-halo`. Every agent sets `NJ_QA_ROLE` and `AGENT_NAME` (its name plus the ticket key) when running a browser script and `freshWindow` draws the halo and the agent type at the top: Scavenger blue, Tester orange, Leader green, Director red, Harvester purple, any other agent silver with its agent-map name. The text reads «TESTER: tester-r1 PROJ-4285». It has no effect on the process: clicks pass through, page text never includes it, and `page.screenshot` and `locator.screenshot` hide it, including whole-window captures (`lib/halo.ts`, proof in `selftest/halo-check.ts`). Other capture methods are allowed and may show it.

## Harvest order (owner, 2026-11-09)

Services get updated, so each run re-harvests in this order, reporting each stage before the next:

1. **The Flowable:** the model from the Flowable modeler export (read only, office network), plus the service settings from «إدارة النظام» → «انواع الطلبات» → the service's edit (pen) button, read only. That screen holds no process model.
2. **«شاشات مقدم الطلب»** for the same service.
3. **The back office** screens.

Each stage lists what differs from the stored copy. Testers don't wait for it: they start from what exists and take in differences as they appear.

## Route protocol (the owner's words, the core of the method)

**First, order the notes by stage,** so the first note the system can show is checked first and the whole list is tested in one go.

**Then handle notes that have different routes:**
- **On the applicant side** (مقدم الطلب), where the note can be checked before submitting: try both routes, then move on with the route that has the next notes to test.
- **On back-office desks,** in different stages: desks usually have buttons that move the ticket back and forth, so keep routing the same ticket and test them all on one ticket.
- **A note that needs a ticket to finish on a specific route or end at a specific desk:** take a dummy fast route that only tests that note, then file another ticket and work the other routes' notes on it.

**Take one main route to the very end once per service,** to prove the service submits and completes correctly, pressing «التوقيع الرقمي» and waiting for the owner's OTP. Otherwise press it only when a note needs the signed result. This run-only rule overrides the standing "never press it" rule.

Tests always use fresh tickets filed in this run, because fixes do not apply to older requests. Notes on the same stage go to the same tester: a tester works only its own route.

## Reporting to the owner

The director reports in the VS Code chat, in the fixed shape from the global «Reports to the owner» rule: result first, the same blocks in the same order, one emoji plus word per state, and this table on every report:

`# | Stage | Status | Est. finish (clock) | Opus | Sonnet | Haiku | Stage total`

Under each service's table, the **results line**: notes tested with their verdict counts, then the **findings funnel**, defects found outside the notes: found by agents → kept by the leader → approved by the owner (`nj_qa.py findings`).

One table per service, never mixed, with that service's stages and its own totals row, spent as `spent → ~est.`, and estimates marked `~`. Add a batch table across services only at the end of the batch or when he asks. Real figures: `python -X utf8 scripts/tokens.py <session dir> --run <RUN> --service <KEY>`; without `--service` it gives the batch view. Leaders never write to him directly; his view of a run is this table, the `needs-nader` requests, the walls, and the preview.

## Token budget (owner, 2026-11-09)

The first run cost about 10M tokens for 2 services. The target is 2M to 3M per service, so:

1. **Preflight gate:** the leader files one real request before any crew, and `lease-start` refuses testers and scavengers until it passes. The first run's PROJ-4285 spent 2.9M and filed nothing.
2. **Lighter workers:** the `nj-qa-*` agent types, briefs under 15 lines, facts in files.
3. **One scavenger pass per side,** and a harvester that re-harvests only what changed.
4. **`navigation.md` by default:** every worker adds to it, and every later agent reads it first.

## Limits that scripts enforce

`scripts/nj_qa.py` holds the rules a model should not have to count. Its tests: `python -X utf8 scripts/test_nj_qa.py`.

| Rule | Command |
|---|---|
| One real request filed before any tester or scavenger | `preflight`, `lease-start` |
| Every note in exactly one route, each route has notes | `plan-check` |
| 30 minutes from spawn; the clock never pauses | `lease-start`, `lease-left`, `lease-check` |
| At most 2 agents per note. An outside block with no progress (OTP, staging down) does not use up the limit | `lease-start` refuses the third, `lease-end --no-progress` |
| A report needs a verdict, what was seen, an interpretation, evidence that exists, and the build | `report-check` |
| One send-back per report, then the leader decides and flags the note | `sendback` |
| Still failing: verdict and proposed Jira action | `classify` |
| A healing rule reaches every later brief; a repeat is flagged and counted | `lesson`, `lessons`, `lease-start` |
| A lease ends once; no new agent once the service is at the token stop | `lease-end`, `lease-start` |
| Scripts that alter staging traffic mark their notes `tampered` and `cannot-test` | `tamper-scan` |
| review.json: evidence files, headline, test action, expected result, leader decisions, criteria that agree with the verdict | `preview-check`, `publish` |

## Walls (owner, 2026-11-09)

An agent that hits an error it can't clear with one fix stops pushing. It writes `<S>/walls/<agent>-<n>.md` with the evidence and a handoff, and finishes. The leader works out the cause, corrects it, and sends a replacement with exact instructions in the next batch. A wall from our own tooling with no progress doesn't use up the note's 2-agent limit. The harness limit means the correction comes when the batch returns, so the wait is at most one 30-minute lease. Because agents in a batch are independent, the others keep working meanwhile. The director watches `walls/` too, so the owner can see them.

## Healing (owner, 2026-11-09)

The leader heals the process after every wall, send-back or weak report: names the cause, fixes it at the source where every agent gets it, records a rule (`nj_qa.py lesson`), and re-plans the remaining route. `lease-start` prints every rule for the next brief, the other service in the run gets them too, and a repeated rule comes back as `REPEAT`, meaning the fix must move into shared code. Healing may change how agents get somewhere, never what a note means, a pass, or a verdict. Full rules: the leader's role file. Earlier lessons: `references/lessons.md`, which the director updates at close-out.

## Checks added after the first run's reviews (BA, CEO, devil's advocate, 2026-11-09)

Reviews: `project-tests/work/nj-qa/review-2026-11-09/{ba,ceo,devil}.md`.

| Risk found | Guard |
|---|---|
| A ✅ on the page with no proof behind it | `preview-check`: every verdict needs a screenshot, a headline, the test action and the expected result |
| Agents altering staging traffic to reach a screen | `report-check` searches the agent's scripts; a verdict reached that way must be `cannot-test` |
| The 2-agent limit bypassed by re-closing leases | `--no-progress` needs a reason, works once per note, and never on an ended lease |
| A preflight written after the crew already ran | `preflight` needs an 11-digit serial and refuses once any crew has started |
| Notes the developer hasn't delivered marked as failing | `classify` gives `not-delivered` for To Do, and counts "too new" from the delivery date (`--delivered`) |
| Spending past the target | `tokens.py --service KEY --budget 2500` before each batch: WARN at half, STOP at the cap |
| Every lesson pasted into every brief | `lease-start` points at the lessons file; the brief carries only the ones on its route |
| The halo filmed in a client video, or drawn on a person's Chrome | the keeper skips the manual recorder and anything outside an NJ-QA run |

**Shared code is never edited while agents run.** Fix it between batches, typecheck, and commit, so there's a version to roll back to.

## The review page the owner reads

Each note reads top-down in fixed blocks: the verdict word and one plain sentence on the row, then 🎯 المطلوب, 🧪 ما فعلناه, 👀 ما رأيناه, a criteria table when a note has several checks, ↩️ any verdict override, 👉 الخطوة التالية, and the evidence. The original note text and interpretations fold away below. When a refusal message is the expected result, «المطلوب» says so, because otherwise a pass reads like a failure.

## KPIs per run (from the CEO review)

Tokens per service (target ≤ 2.5M), notes with a verdict, the findings funnel (found → kept → approved), the owner's interventions (target ≤ 5) and his review minutes, blocked notes by cause, and false verdicts he catches. The director reports them at the end of each batch.

## Verdicts and the deployment rule

Verdicts: `fixed`, `not-fixed`, `too-new`, `not-delivered`, `blocked`, `dropped`, `no-system-change`, `cannot-test`. A note still To Do is `not-delivered`, never a failure.

The model version and its update date are at the bottom of the screen, and every report records them. When a note still fails:
- **Filed at least one working day ago** (Sunday to Thursday, not 24 hours): `not-fixed`.
  - In QA and reported by the owner: propose reopening with a comment.
  - Anything else: propose a comment with mentions.
- **Filed less than one working day ago:** `too-new`, retest later.

These are proposals in the preview. The owner and the director act on them; the leader never files.

## Preview

The hub's «المراجعة / Review» tab, from `<S>/review.json` (contract v1, `docs/ARCHITECTURE.md` 3.3 and 3.4): the exact note text, the evidence from the portal, the tester's and the leader's interpretation, the route and ticket, the verdict and the proposed action, the criteria, a table of every agent finding outside the notes with the leader's decision on it (`findings[]`: one row per reported finding, even when dropped), and the Bug drafts (`tickets[]`). The owner's decisions (approve, edit, reject, question) are saved in his data folder (`decisions/<run>/<KEY>.json`) and read back through MCP. Old runs keep `tester/review-input.json`; `node mcp/cli.mjs import-run <old run dir>` converts them.

## Gates the hub shows (four chips per service)

| Chip | Event in `ledger.jsonl` | Script |
|---|---|---|
| preflight | `preflight {status, serial}` | `nj_qa.py preflight` |
| preview-check | `review-ready` / `review-blocked {problems[]}` | `nj_qa.py publish` |
| patch scan | `tamper-scan {hits[]}` | `nj_qa.py tamper-scan` (inside `publish`) |
| budget | `<RUN>/tokens.json` state | `tokens.py ... --json --out`; `lease-start` refuses at stop (3.0M) |

Other hub events the crew writes: `nj_qa.py phase`, `wave-start`, `wall-close`; `cli.mjs set_agent_status`, `post_event`, `add_wall`. Credentials for scripts: `scripts/creds.py` (`get(group, key)`), never printed.

## Evidence file names (owner, 2026-11-09, forward only)

Every screenshot and video is named in Arabic only, `<المشكلة>-<الخدمة>-<التاريخ>-<الوقت>`: a short specific phrase for the defect or what is proven (never «لقطة»), the service's Arabic portal name, `YYYY-MM-DD`, then `HH.MM` in 24 hours (Windows has no `:`), e.g. `زر-الإرسال-لا-يستجيب-طلب-تسجيل-منتج-2026-11-09-14.35.png`. Hyphens between words, at most 150 characters (the service shortens first, never the issue), no English except a ticket code such as `PROJ-5494` after the issue, `-2` on a second shot of the same issue in the same minute. Never type one by hand: `scripts/evidence_name.py` (CLI and import), or `evidenceName(issue, service, when)` in your suite's `lib/shot.ts`. `report-check` and `preview-check` refuse any other picture or video name and print the file. A run imported from before the rule keeps its old names (`NJQA_LEGACY_EVIDENCE=1`, set by the importer); existing evidence files are never renamed.

## Standing rules that still apply

Screenshots are viewport only, with a red ring on the exact point; Jira evidence is unmasked; real-user triggers, keyboard first; triggered waits, no hard waits; filing never inside the Playwright runner; own Chrome profile and sign-ins one at a time; credentials never printed or copied; Thmanyah only; Arabic RTL; dummy data is never a defect.
