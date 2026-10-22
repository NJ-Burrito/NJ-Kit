# The council — five points of view, devil mode, three rounds

Agreement is the default failure of a single reviewer. The council puts five
adversarial readers on the work, each through `devil` (restate, load-bearing
assumptions, 3–6 objections ranked by cost-if-true with a kill criterion,
strongest alternative, what survives, verdict), three times, at the cheapest
fidelity that can still fail.

## Pick the five (dynamic, from the book's profile)

**Size:** ≤ 5 items — one `devil` pass on the plan, no council; ≤ 12 items —
three members; larger — five. Always: **auditor** (provenance, independence,
what the gate proves) and **learner** (the reader: does it teach, can they act
on it). Fill the remaining seats from the pool **in this priority order**; a
concern a script already gates (twin structure, fonts) ranks below one no script
can judge:

| Signal in `book.json` / plan | Member |
|---|---|
| a `certification` kind | **examiner** — objective coverage, question quality, exam-table fit |
| a `regulation` kind | **compliance officer** — jurisdiction, effective dates, liability wording |
| a `tool` kind, or code blocks | **practitioner** — would this run on Monday at work? |
| `plan` says leads + waves | **orchestrator** — cost, slots, resume, failure classes |
| `twin` set | **publisher** — twin meaning, term choices, PDF navigation |
| changing this skill | **maintainer** — triggers, portability, config surface, ponytail |
| still short of five | **sceptical owner** — is this worth building at all; the crude version |

## Three rounds (each at cheap fidelity)

| Round | Reviews | Members add |
|---|---|---|
| 1 | `PLAN.md`, `book.json`, one rehearsal page | research: ≥ 4 current sources in their field, URL + the sentence used |
| 2 | the revised rehearsal + the Lead's decisions file | follow-up on their round-1 edits (landed / landed wrong / rejected: accept or object with cost-if-true) + cross-POV conflicts |
| 3 | a first-wave sample (≤ 3 pages, the scripts' gate output) | final red team; only edits that block shipping |

Never run a round on the whole book: a council that reads 37 pages costs more
than the book and finds the same objections a sample does.

## Mechanics

- One brief file `council/COUNCIL.md` for all members (governance header, FOCUS,
  devil rule, output format, budget ≤ 40 tool calls); a per-round addendum.
- Members run in parallel, in the background, Sonnet, medium effort; each writes
  only `council/r<N>/<member>.md`: `## Devil`, `## Proposed edits` (≤ 10, then ≤ 6),
  `## Sources`, `## Verdict` (score /10 + the one change that matters most).
- Members never see each other's round of the same number; from round 2 they read
  the previous round's files by path.
- After each round the Lead writes `council/DECISIONS-r<N>.md`: every edit
  adopted / reduced / rejected, one line of reason each. A rejection is answered
  in the next round, not argued in chat.
- Edits that change a script go to the builder as `AMEND:`; prose edits the Lead
  makes. Scores per member per round go in the ledger — a council whose scores
  do not rise is reviewing the wrong thing.

**Cost:** about 15 agents and ~600 tool calls at the ceilings for a five-member
council — roughly 1.4× the first run's authoring. That is why it reviews samples
and why small books get one devil pass.

## Measured on this skill (2026-10-16)

The council built this skill from v0: round-1 scores 6/5/6/6/5, round 2
7/7/7/7/7, round 3 7/6/7/6/6.5 on the code (it broke 60+ inputs; every blocking
break fixed and turned into a selftest assertion). Round 1 found that v0's own figures were wrong (163 → 162 alias
entries), that verification was a status flip, that the PDFs had no bookmarks
and that nothing gated teaching. Round 2 found a stage-order cycle (audit after
the report that prints it) and an unbound quote check.
