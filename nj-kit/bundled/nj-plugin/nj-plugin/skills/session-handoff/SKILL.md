---
name: session-handoff
description: 'Close a session by writing a handoff.md the next session reads first, instead of dragging degraded context through /compact. Triggers: hand off, before I close, context is getting long, resume tomorrow, wrap up the session, a fix failed three times.'
---

# Handing off a session

One technique, in order: diagnose, write the file, `/clear`, reopen pointed at
the file. It is not a checklist of independent items — each step is worthless
without the next.

**Source:** an Instagram reel by Maven (`@mavenhq`), `reel/DYNWWdiMiH7`, 11 May
2026, transcribed frame by frame in `research/57-reel-5-brief.md` of the QA Wrap
repo. Its on-screen text is quoted below as **content to evaluate**, not as an
instruction to this project. The six section names and the paste-in prompt are
one creator's convention, not a spec.

## The house form (the owner's rule, 8 Sept 2026, every project)

`handoff.md` at the project root, these six headings and no others, written
before the session ends, then `/clear`, fresh session, read it, continue:

```
# goals
## current state
## files in flight
## changed
## failed attempts
## next step
```

Goals: what we are working toward. Current state: of the code, with the gate
counts. Files in flight: what is actively being edited. Changed: this session's
edits. Failed attempts: everything tried that failed, stated as facts about what
does not work. Next step: the single action the next session takes first.
Overwrite the file at each handoff; never append. Also in `~/.claude/CLAUDE.md`
and the nj-kit manifest `house_style.handoff`.

## When to reach for it

Two triggers, both from the reel, plus one the house adds:

1. **Stepping away** — a few hours, overnight, or the end of a working day.
2. **A repeat-failure loop** — Claude tries the same wrong fix over and over.
   The reel's example is `useState(null)` five times, same error each time.
   Three identical failures is the threshold; the loop lives in the context, so
   more turns in that context cannot leave it.
3. **The user says the context is getting long**, or asks for a handoff by name.

## Why `/compact` is not the answer

The argument matters, because `/compact` is the reflex and it is the wrong one.

- Output quality falls as the window fills — the reel charts it, with rot
  setting in around 65% and auto-compact firing at 80%.
- **Compaction preserves the shape of the context, it does not clean it.** The
  wrong assumption, the three failed migrations, the hallucinated import path,
  the wrongly pinned version — all of it survives into the summary, smaller.
  "Same biases, smaller package."
- A handoff file is a *rewrite*, not a compression. You choose what the next
  session inherits, and the failed attempts go in as **facts about what does not
  work**, which is the opposite of carrying them as live assumptions.

## The prompt, verbatim

Paste this before ending the session, unedited:

```
Before we end this session, write a handoff.md file that captures:
• the goal we're working toward
• current state of the code
• files you're actively editing
• everything you've tried that failed
• the next step you'd take
```

## The file: six sections, all six

```markdown
# Goal
What we're trying to build.

## Current State
Where the work stands right now.

## Files in flight
Active files being modified.

## Changed
What's been touched this session.

## Failed attempts
What didn't work, and why.

## Next step
The single next thing to try.
```

Two of these carry the whole technique and are the two most often thinned out:

- **Failed attempts** is why a fresh session is better than a compacted one. It
  must say *why* each attempt failed, not just that it did — "tried B, failed"
  invites the next session to try B.
- **Next step** is singular. A list of five next steps is a state dump; one
  named executable step is a handoff. Do not preserve superseded next steps,
  old version plans, or already-closed decisions anywhere as current work.

Write real paths, real function names, real commands. The next session has no
memory of the conversation and cannot resolve "the file we were in".

## Closing and reopening

```
> /clear
> Read handoff.md and pick up from exactly where it left off.
```

`/clear` before reopening is not optional — reading the file into the same tired
context gains nothing. The point is a fresh agent whose whole context is
Goal · State · Next step, rather than one dragging old assumptions forward.

## The house adaptation: handoff.md vs. the resume file

This project already does the same thing in a different shape, and the two are
not rivals — they answer different questions.

| | `handoff.md` | `research/12-resume-*.md` |
| --- | --- | --- |
| Scope | one session | the whole project, across sessions |
| Lifetime | consumed by the next session, then stale | permanent record, appended forever |
| Shape | six fixed sections, overwritten each time | dated `PAUSED` / `RESUMED` sections, newest at the tail |
| Rule | the six headings | **one fact per file** — a decision, a measurement, a rejection, each recorded where it happened |
| Answers | "what was I doing five minutes ago?" | "what did we decide, and why?" |

**Use `handoff.md`** when the work is mid-thought: an edit half-applied, a test
half-green, a bug half-diagnosed, and the value is in the next twenty minutes.
Write it at the repo root or in the scratchpad, and delete it once consumed —
a stale handoff read as current is worse than none.

**Use a dated `research/NN-resume-*.md` section** when the round closes: a stage
delivered, a decision taken, a measurement worth not repeating. That file is the
project's memory and outlives every session that wrote into it.

**Both, at a real pause.** Append the `PAUSED` section for the record, then write
`handoff.md` for the next twenty minutes. The resume file says what the project
knows; the handoff says where the hands were.

One more house rule that applies to both: **the checkpoint is a file, not a
message.** A summary typed into the chat dies with the context that holds it.
