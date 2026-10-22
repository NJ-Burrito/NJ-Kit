# Page template, practice bank, mentor path

Contents: 1 Generic rules · 2 Certification page (QA example) · 3 Tool page ·
4 Practice bank format · 5 Mentor path rules · 6 What `check_teach.py` checks

## 1. Generic rules (any domain)

- One page per item (certification, tool, regulation, clause family). Headings
  are numbered `## N. <name>` and listed per folder in `book.json` `headings`;
  `check_pages.py` refuses a page missing one.
- Under the title: a status box (current / retired YYYY / renamed to X, with
  `[KB#]`), level, **Last checked** date, and a **By the end you can** box of
  5–8 objective verbs taken from the objective entries.
- "How to study this page" belongs in §2, before the substance, not after
  4,000 words.
- Depth is coverage, not word count: every objective anchored and questioned,
  every applied-level objective (K3+) has a worked example with numbers. Word
  counts are a floor lint (flag < 2,500 words), never a target — they reward padding.
- Objective ids are the issuer's (e.g. `FL-4.2.1`); where none exist they are
  generated `<slug>-<n>` from the "By the end you can" box.
- **Layout that passes the gate** (CTFL rehearsal): in the core-concepts section,
  chapters are **bold lines**, and each objective is its own heading
  `### FL-4.2.1 Equivalence partitioning {#FL-4.2.1}` — anchors render only on
  headings, never inline. Only headings naming a K3+ objective need the three blocks.
- More objectives than exam questions (CTFL: 64 vs 40) is normal: a question may
  list several objectives (`objective: FL-1.4.1, FL-1.4.3`); every objective is
  covered by at least one.
- Example data inside a Worked example / Try it / Now alone block — prose or a pipe
  table after the marker in the same section — is illustrative and exempt from the
  numbers gate; everything after the next heading is checked again.
- Every applied-level (K3+) objective's technique heading ends with three blocks:
  `*Worked example.*` (full, numbers shown) → `*Try it.*` (first steps given,
  learner finishes) → `*Now alone.*` (new data, no scaffold). Keys for the last
  two are in the answer key. Expert-level pages may invert (problem first),
  because worked examples stop helping experienced learners.

## 2. Certification page (QA run's template, `knowledge/_TEMPLATE.md`)

1 At a glance (table: code/version/date · prerequisite · exam questions/points/pass
mark/minutes · training time · outcomes; "not confirmed" in any cell without a
verified entry) · 2 Who it is for, and how to study this page · 3 Syllabus map:
every objective by official id (e.g. `FL-4.2.1`) with K-level, chapter minutes ·
4 Core concepts, each objective anchored `{#FL-4.2.1}` · 5 How it is done in
practice, step by step · 6 Illustrative case study · 7 Pitfalls (≥ 6 rows:
pitfall · why · avoid · early sign) · 8 Mentor notes (juniors' mistakes, how to
show the skill at work) · 9 Exam preparation (hours by chapter, wording traps,
5 taster questions, `### Answer key` at the end of §9 under "cover until
answered", link to the official sample exam) · 10 Sources (name · URL ·
retrieved · KB ids) · **Recall sheet** (10–15 closed-book prompts per chapter,
answers in the key).

## 3. Tool page

1 What it is and when (vs alternatives) · 2 Setup (version checked, Windows + CI)
· 3 Step-by-step (first real task end to end = the worked example) · 4 Core
features with examples · 5 Best practices · 6 Integration (CI, tracker, reports) ·
7 Pitfalls · 8 Mentor notes · 9 Illustrative case study · 10 **Do it yourself**
(exactly 3 tasks, each with `Done when:` + a command and `Expected:` output, no steps)
· 11 **Check yourself** (points at 3 bank questions tagged `TASK-1`..`TASK-3`) ·
12 Sources. Targets must exist (e.g. `https://demo.playwright.dev/todomvc/`), never
`example.test` placeholders. Gate: `check_tool.py` (fenced json/py/js/ts/yaml/bash must parse).
Code blocks are syntactically valid for the version checked; stage 5 runs them.

## 4. Practice bank — `practice/<slug>.md` (outside the page folder)

One block per question, **no key and no why-not in the block**:
```
### Q-<slug>-<nn>
type: mcq
objective: FL-4.2.1 · chapter: 4 · level: K3
stem: ...
a) ... b) ... c) ... d) ...
basis: KB#412
```
`type:` is `mcq`, `multi(select 2)`, `matching`, `roman`, `not-stem` or `essay`;
certification banks mix the formats the official sample exams use (CTFL Sample A:
10 of 40 items are roman lists, select-two, matching or NOT-stems). One objective
per item; an item testing an official LO group adds `lo_group: FL-1.4.1, FL-1.4.3`.
Options are length-balanced: the gate fails a bank where the key is the longest
option in > 40 % of items. Beyond length, run the **stem-less probe** once (a Haiku
sees the options only): items it keys above chance are rewritten. What it caught on
CTFL (47 of 76 keyed): single-swap distractors make the key the "centroid" of the
options (fix: equalise overlaps); "which statement is correct" items are answerable
from topic knowledge (fix: scenario-to-concept items whose options are all true of
*something*); absolute words ("always", "never") mark distractors. Mocks inside one
bank are `## Mock n` headings with their own id ranges. Essay items (Expert exams) have no options, level K5/K6,
and their `rubric:` lines live in the key file. Items must not paraphrase the
official sample exams: `check_teach.py --resemble <sample exam .txt>`.
`basis:` is a verified `KB#n`, or `concept: §<anchor>` for a question that tests
an explained concept — and it must carry **the fact that picks the key**, not just
the topic (the QA book's bank audits missed 1 then 3 items whose keys were right
but whose basis named only the subject; a second failing audit stops the book). `calc:` (applied numeric questions only) is pure arithmetic, evaluated, and its
result must appear in the keyed option. It lives in the **key file**, in the
question's block after its key line — under the stem it would give the method
away (`check_teach` fails it there). `move_calc.py --apply` migrates old banks.

Keys, `why-not:` lines and essay rubrics live only in `practice/<slug>.key.md`
(`Q-<slug>-01: c` then its why-not). A page's Recall sheet keeps its answers in a
final `## Recall answers` section; number prompts and answers with letters (a), b) …)
so the numbers gate does not read them as figures. Bank size = the
official exam's question count for items the reader sits (a KB entry), else one
per objective. Chapter and level counts match the official exam table within ±1.

## 5. Mentor path rules

a. The path states **hours per week** at the top; weekly minutes may not exceed it.
b. From week 3, every week has a 15-minute **Recall** cell: redo an earlier week's
   output closed-book (weeks −1 and −3).
c. From the first technique block, weekly quizzes **mix ≥ 2 earlier topics**.
d. Any "score X of Y" target needs Y questions in the bank, or names the external
   source as a KB entry.
e. The last two weeks before an exam are mocks from the bank; errors logged by objective.
f. Every "ready when" is decidable by the learner alone (a number or an artefact
   id), or tagged `[needs: peer|team|mentor]` with a fallback. Each stage artefact
   has a rubric (criteria × 3 levels).

## 6. `check_teach.py` fails when

an objective has no anchor or no question · a question lacks objective/level/key ·
a key sits within 10 lines of its stem · a technique heading lacks the three
blocks · with `--path`: no hours line, or an "X of Y" target exceeds the bank.
`calc:` lines that are pure arithmetic are evaluated (ast, numbers and operators
only) and must match the keyed option; other `calc:` lines are counted, not run.
A question with no `basis:` fails; concept keys are covered by the audit's bank
sample and the rehearsal's blind-learner probe.
