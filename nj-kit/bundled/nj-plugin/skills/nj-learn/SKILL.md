---
name: nj-learn
description: 'Capture a lesson the moment work teaches one and write it where it will be read: the owning skill, CLAUDE.md, memory, or the nj-kit manifest. Triggers: a surprise, a tool that lied, a non-obvious failure, a user correction, remember this.'
---

# Learning from the work

Most of what makes this toolkit good was discovered by something going wrong.
Cairo was condemned by an audit that was itself broken. `npx` failed silently on
Windows because it is `npx.cmd`. A change detector was blind to deletions.
None of that is in a manual; all of it cost real time.

A lesson that stays in a transcript is a lesson paid for once and lost. This
skill is the loop: **notice, route, record, verify.**

## 1. Notice — what counts

Record when any of these happen. The bar is "would a competent person have
guessed wrong?", not "was this hard".

- A first attempt failed for a reason that was not obvious in advance.
- A tool reported something untrue — silently wrong output, an exit code that
  lied, "0 tables" on a page with a table.
- An assumption turned out false, especially one that felt safe.
- The user corrected an approach, or repeated an instruction.
- A platform quirk bit: encoding, path, shell, permission.
- **A skill's own instructions were wrong or incomplete.** These are the highest
  value, because the skill will mislead again on its own authority.

Do **not** record: one-off typos, anything already written in the skill that
covers it, or a restatement of general knowledge. A lessons file that fills with
truisms stops being read, and then the real lessons go unread too.

## 2. Route — this is the judgement, and it is the whole skill

Where a lesson goes decides whether it is ever seen again.

| The lesson is about | Put it in | Why there |
| --- | --- | --- |
| How to do a specific craft | **that skill's SKILL.md** | loads exactly when that work starts |
| A trap inside a script | **a comment at the code that has the trap** | the only place someone editing it will look |
| A fact that must be live from the first message | **`~/.claude/CLAUDE.md`** | every session, every project — keep it short, it costs tokens every turn |
| How the user wants to be worked with | **memory, `type: feedback`** | survives sessions, includes the why |
| A toolchain decision — font, extractor, binary | **`nj-kit/manifest.json`** | travels to the next machine |
| Nothing above fits | probably not a lesson yet | let it recur once |

**Prefer the narrowest home that will be read.** `CLAUDE.md` is loaded on every
turn of every session, so a lesson that belongs to one craft costs everybody
tokens for ever if it goes there. A skill's own file is almost always right.

**Write the why, not just the rule.** "Use poppler" is obeyed until someone has
a reason not to. "Use poppler — mupdf and pdfium return Arabic in visual order,
so correct words look missing, and two of them agreeing is one shared bug rather
than confirmation" survives contact with a sceptic.

## 3. Record — recurrence, so a fluke is not mistaken for a rule

Bookkeeping is `scripts/lessons.py`, which does IDs, recurrence counting,
candidate→confirmed promotion and quarantine. It arrived here from
`tlc-spec-driven` on 18 September 2026, when the audit removed that skill: the
dependency was on a foreign skill's script, so the delegation that once avoided
duplication had become a broken path. The store it reads is unchanged —
`~/.claude/.specs/lessons.json` — so every lesson recorded before the move is
still counted.

```bash
L=~/.claude/skills/nj-learn/scripts/lessons.py
python "$L" --root ~/.claude init        # once
python "$L" --root ~/.claude add \
  --feature <skill-or-area-the-lesson-belongs-to> \
  --signal gate_fail \
  --source <file:line, or the command that lied> \
  --text "<one actionable sentence>"
python "$L" --root ~/.claude list        # confirmed lessons
```

Two mappings, because the script was written for a spec workflow:

- `--feature` holds **the skill or area the lesson belongs to**, not a product
  feature. It is what recurrence is counted across.
- `--signal` is effectively always `gate_fail` — "a check failed and taught us
  something". The other values in its enum (`ac_gap`, `surviving_mutant`) belong
  to spec-driven development and would be dishonest labels here.

The store is `~/.claude/.specs/lessons.json`, machine-owned; read
`~/.claude/.specs/LESSONS.md`, never hand-edit either.

**Recording is not the point — routing is.** A lesson recorded but not written
into the skill that needs it will not be there when it matters.

## 4. Verify it stuck

A lesson written and never tested is a belief, not a fix.

- If it can be checked by a script, add the check. `scan.py` and the copy audit
  both began as lessons.
- If it changed a skill, read that section back and ask whether it would have
  prevented the original mistake. If not, rewrite it.
- If the same lesson recurs, the routing was wrong — it went somewhere unread.
  Move it, do not restate it louder.

## When a lesson turns out wrong

Say so and remove it. This has already happened once and mattered: the note that
Cairo displaced letters was recorded from two extractors that shared a bug, and
it very nearly caused the house font to be forked. The correction is now in the
memory that held the error, with the measurements.

`python "$L" --root ~/.claude penalize <id>` quarantines a confirmed lesson that
failed when applied. A lessons store nobody prunes becomes folklore.
