# Revising, cutting, and holding one voice

## 1. The recycled-line audit

A rewrite that reuses the dead draft's sentences is not a rewrite. Run this
before delivering any revision, and **put it in the file**.

```bash
# the previous version's strings, in full
git show HEAD:extension/tools/film/storyboard/qa-wrap.storyboard.json
```

Procedure:

1. Quote the previous version's lines **in full** in the new document. Not
   "audited, clean" — the next reviser must be able to re-run it without a git
   command.
2. For each new line, find its closest contact among the old ones.
3. List every contact with a verdict, **including the ones you cleared**. An
   audit that silently drops its nearest miss is not an audit (`research/116` C12
   — a two-word "One press" overlap went unlisted in rev 2 and had to be
   disclosed in rev 3).

Verdicts:

| Overlap | Verdict |
|---|---|
| Whole sentence, or a sentence one word off | **REUSE** — rewrite |
| A distinctive phrase (3+ words, the memorable part) | **REUSE** — rewrite |
| A shared token in an opposite claim ("proof is gone" vs "proof you never had to write") | CLEARED — list it |
| Two-word function run ("one press") | CLEARED — list it |

Watch the swaps too: when the audit kills a line, the obvious alternative is
often *also* burned by a different old line. "Nothing leaves this machine" was
unusable for exactly that reason. The replacement must be genuinely new.

## 2. Cutting to length

Cut in this order. Stop at the first rung that gets you to time.

1. **Redistribute seconds** (see `timing.md`). No words leave. Try this first,
   always.
2. **Cut a whole line whose picture already says it.** The best cut in the
   archive: beat 3's line went, its 2.8 s of picture stayed, and the film
   gained its first silence in the nine seconds whose whole justification was
   silence. A line you can delete without losing information was a caption on
   the picture, not a line.
3. **Cut a claim that has a picture problem anyway.** Two faults, one cut.
4. **Cut the second sentence of an over-stuffed beat** — the one that explains
   the first.
5. **Shorten a surviving line.** Last, because this is where death by a
   thousand trims starts.

Never: cut the turn, cut the end card's ask, cut the tail, or shave every beat
by a word each. The last is how a piece dies evenly — nothing is visibly wrong
and nothing lands.

### The cost line

Every cut is delivered with what it costs. No cost line = a cut nobody can
review.

```
CUT  beat 7, second sentence — "The page shows the path, in both our languages."
     20 -> 11 words; beat 7 stops being starved (+1.8 s spare).
COST The bilingual claim leaves the script, and decision 105 fought for it.
     This is a real loss.
MITIGATION The sheet is still on screen and still bilingual — the film shows it
     instead of asserting it over an illegible plate.
ALT  Grow beat 7 to 10.0 s, taking 2.5 s from beats 5 and 6. Never from beat 9.
```

Where a beat has **no** spare word, write that down and name the remedy — a
re-take, a boundary move — rather than shaving it. "There is no trim here,
re-take it" is more useful to an editor at 2 a.m. than silence.

## 3. The voice sheet

One consistent voice across the piece, and across the set — the commercial is
read by the same voice as the other films (decision 98). Describe it in six
fields so a second writer or a recorder can match it without hearing a take:

| Field | Example |
|---|---|
| **Person & tense** | first person, present, one tester |
| **Register** | tired, unhurried, no announcer lift |
| **Rate** | 140 wpm, mandated; if the take is under, the shortfall goes to silence |
| **Sentence length** | 4–12 words; fragments allowed; no subordinate clauses |
| **Forbidden** | gendered pronouns (grepped, fails the build); superlatives; questions to camera |
| **Signature move** | the concrete act stands in for the feeling ("typed it twice, deleted it twice") |

Two enforcement notes:

- Make the machine-checkable field machine-checked. The pronoun rule became a
  grep over the caption track, the SRT and the direction sheet; any hit fails
  the build. Scope it to the film's own strings — a treatment that *quotes* the
  old captions as audit evidence must not fail its own gate.
- **Do not rewrite a line that already passes** in order to satisfy a general
  instruction to "refine". Lines 1–7, 10 and 11 of rev 3 were left untouched
  because each passed its density row and each was won against a named
  objection. Re-litigating settled copy is how a revision regresses
  (`research/116` C15). Spend the revision on what was named.

## 4. Bilingual revision

The pair is the unit. A fix to the English side that leaves the Arabic stale is
worse than the original error, because now the two disagree and the disagreement
is invisible until someone bilingual watches. Revise both sides in the same
pass, re-run **both** timing tables, and re-run the recycled-line audit on both.
Proofread with `arabic-english-proofreading` before delivery; `PYTHONUTF8=1`.
