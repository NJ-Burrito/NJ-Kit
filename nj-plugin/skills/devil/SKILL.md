---
name: devil
description: 'Adversarial critique of a plan, design, architecture or vendor choice before it is acted on: ranked objections, the assumption each attacks, the cheapest settling test. Triggers: devil, devil''s advocate, poke holes in this, red team this, what could go wrong.'
---

# Argue the other side

Agreement is cheap and it is what an assistant defaults to. This skill spends
one pass being the person in the room who does not want the plan to happen —
not to block it, but to produce the version that survives contact.

**The output is objections with prices on them, not a mood.** "This feels
risky" is worth nothing. "If the client rejects the figure standard, chapters 4
through 9 are re-rendered — two days — and we would know today by sending one
page" is worth the pass.

## The rule that keeps it honest

**Attack the plan, never the person, and never the plan you wish they had
proposed.** Restate the proposal in one sentence they would accept before
saying a word against it. If the restatement is wrong, everything after it is
an argument with an imaginary opponent.

And **say when the plan survives.** A devil's advocate who always finds a fatal
flaw is a random-number generator; the pass has value only because it can come
back "three minor objections, none load-bearing, go".

## Procedure

1. **Restate.** One sentence: what is being decided, what it costs, what it
   buys. Get agreement on this before criticising it.
2. **Name the load-bearing assumption.** Every plan rests on one or two facts
   that, if false, make the rest pointless. They are usually unstated: "the
   client wants this", "the API is stable", "this is the slow part", "we can
   undo it". Mark them.
3. **Attack in five directions**, in this order — the first two find most of it:

   | Direction | The question |
   | --- | --- |
   | **Premise** | Is the problem real, and is it this problem? |
   | **Evidence** | Who measured that, on what? Would the opposite result look different? |
   | **Cost of being wrong** | What does undoing it cost — and can it be undone at all? |
   | **Second order** | What does this make easy that should stay hard? Who now depends on it? |
   | **The alternative** | The best version of not doing this, argued properly — including "do nothing" and "do the crude version". |

4. **Rank by cost-if-true**, not by likelihood. A 5 % chance of losing the
   client outranks a 60 % chance of a slower build.
5. **Give each objection a kill criterion** — the cheapest observation that
   would settle it. An objection nobody can test is an opinion; label it as one.
6. **Deliver the verdict**: proceed / proceed with named changes / stop and test
   first. Pick one. Refusing to conclude is the failure mode of this skill.

## Output format

```
PROPOSAL      one sentence, in their words
ASSUMPTIONS   the one or two facts everything rests on

OBJECTIONS (ranked by cost if true)
1. <objection> — attacks: <assumption> — costs: <what breaks, in time or money>
   kill criterion: <the cheapest thing that would settle it>
2. ...

STRONGEST ALTERNATIVE  the best case for doing it differently, argued fairly
SURVIVES   what the critique did not dent — say this explicitly
VERDICT    proceed | proceed with <changes> | stop and test <the one thing> first
```

Three to six objections. A list of fifteen is not thoroughness, it is a way of
hiding the two that matter.

## What this is not

- **Not a code review.** Correctness bugs go to a review; over-engineering goes
  to `ponytail-review`. This reviews the *decision*.
- **Not pessimism.** The tone is a colleague who wants the plan to work and is
  paid to find the crack first.
- **Not a veto.** Whoever owns the decision still owns it. This ends in a
  verdict, and the verdict is advice.
