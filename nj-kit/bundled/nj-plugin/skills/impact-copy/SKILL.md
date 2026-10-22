---
name: impact-copy
description: 'House style since 17 Sept 2026: impact-first, metric-driven copy for commercials, captions, brag docs, release notes. Every line is a bold anchor, a separator, then an outcome with one true number. Triggers: impact-first, metric-driven, scannable, brag style, make it commercial.'
---

# Impact-first copy

The reader skims. Give them the value in under two seconds per line, or they
move on.

## The line

```
**Anchor (what it does)** | outcome with one number
```

- **Anchor:** 2–4 words, bold, a verb or a noun cluster that names the action
  or the feature. Front-load the keyword: it is the first thing the eye lands on.
- **Separator:** a colon or a pipe. One visual break so the eye can tell *what
  was done* from *what it was worth* without reading either.
- **Outcome:** at most 8 words, one metric, no adjectives doing the metric's
  job. The number comes as early as the grammar allows.
- One idea per line. Never two outcomes on one line; split them.
- Parallel form across the list: every line the same shape, same tense, same
  separator.

Good:

```
**Full-page capture** | one click, zero setup
**Nineteen tools** | one popup, two languages
**Filed to Jira** | every defect in under a minute
**Scaled Enterprise ARR** | +$14.2M net-new by restructuring APAC outbound
```

Bad, and why:

```
Our powerful capture tool lets you easily grab full pages   (no anchor, no number, adjectives instead of proof)
Increased revenue significantly through various initiatives   ("significantly" is not a metric)
Full-page capture: one click, and it also masks data and files to Jira   (three ideas on one line)
```

## The number rule

**Every number is true and has a source line.** For a product: count the
tools, formats, languages, steps, seconds from the repo (README, roadmap,
changelog, catalogue, manifest) and write the source next to the line in the
script or the detail file. For a person: the figure comes from a record the
person can show. Never invent revenue, percentages, customer counts or
time-savings. A line with no honest number gets a concrete fact instead ("no
account needed", "runs offline") — a fact beats a fake metric, and a fake
metric kills the whole list.

## Where the shape comes from

- **Laszlo Bock's X-Y-Z formula** (Google, 2014): "Accomplished X, as measured
  by Y, by doing Z." The anchor is X, the outcome carries Y, Z last if at all.
- **NN/g eyetracking** (F-pattern, 2006, revisited 2017): users read about
  20–28 % of the words and scan the first words of each line down the left
  edge — so the left edge carries the meaning.
- **NN/g "Concise, Scannable, Objective"** (1997): highlighted keywords, one
  idea per paragraph, half the word count, no marketese.

## In a film

- A caption is the spoken words, so the narration line takes the same shape:
  the anchor is said first, the number second. Say numbers as words the voice
  can pronounce ("nineteen tools", not "19x").
- One text card per line; the anchor appears first, the outcome a beat later
  (staggered reveal). Never more than two lines on screen at once.
- The picture at that moment shows the thing the anchor names.

## Checklist before delivery

1. Every line: bold anchor, separator, outcome — same shape throughout.
2. Every number: true, sourced, written next to the line in the working file.
3. Anchor ≤ 4 words, outcome ≤ 8 words, one idea.
4. Keyword first on the left edge; no filler, no adjectives standing in for proof.
5. Read only the bold anchors top to bottom: do they alone tell the story? If not, reorder.

## Lesson: initialisms in TTS (Kokoro / espeak-ng, 17 Sept 2026)

espeak-ng decides whether "QA" is an initialism from the token that follows
it. "QA Wrap runs…" is read as letters; "QA Wrap." / "QA Wrap," / "QA Wrap —"
is read as "kah wrap". Dotted spellings ("Q.A. Wrap") add audible pauses.
Fix the sentence, not the spelling: put the product name before a verb and
never at a stop. Verify with the tokenizer's phonemize output (kjˌuːˈeɪ ɹˈæp),
because the worker cannot listen. Measured in QA Wrap research/77 §14.
