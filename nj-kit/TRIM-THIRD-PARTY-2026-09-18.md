# Third-party descriptions trimmed to ≤40 words — 18 Sept 2026

Acting on `SKILL-AUDIT-2026-09-18.md` §6: descriptions are the only always-on
token cost, and 23 of the worst offenders are third-party skills.

## What was done

- **Job 1** — the `description:` field of 23 installed third-party skills
  rewritten to ≤40 words. Nothing else changed: no body, no reference file, no
  other frontmatter key. Block scalars (`description: >`) became a single
  double-quoted line; the lines after the closing `---` are byte-identical.
- **Job 2** — the trims recorded as re-appliable data, because `install.py`
  re-fetches these skills from upstream repos that carry the long originals, so
  a hand edit here is lost on the next machine:
  - `description-overrides.json` — 23 entries, each with the trimmed text, its
    word count, and the upstream count, plus a `_note` explaining why it exists.
  - `scripts/apply-descriptions.py` — applies it, idempotent, `--check` reports
    drift and writes nothing, `--skills <dir>` for project scope. It refuses
    politely for a skill that is not installed (an override is a trim of
    something that exists), and it replaces the description's whole *line range*
    rather than the key's line, so a block scalar cannot leave stray prose
    behind.

## Numbers

| | words |
|---|---|
| These 23 skills, upstream | 1,817 |
| These 23 skills, trimmed | 846 |
| Saved, always-on | **971 (−53 %)** |
| All 53 installed skills, before | 4,448 |
| All 53 installed skills, after | 1,979 |

The all-skills figure also carries the parallel trim of the owner's own 21 skills,
which is another worker's file set; the 23-skill rows are this worker's alone.

## Per skill

| skill | upstream | trimmed |
|---|---|---|
| xlsx | 152 | 39 |
| hyperframes-registry | 139 | 39 |
| docx | 125 | 39 |
| hyperframes | 118 | 40 |
| ponytail | 113 | 39 |
| playwright-best-practices | 108 | 33 |
| hyperframes-audio | 103 | 38 |
| media-use | 99 | 40 |
| hyperframes-animation | 84 | 35 |
| hyperframes-cli | 71 | 40 |
| pdf | 69 | 35 |
| ui-ux-pro-max | 67 | 39 |
| hyperframes-keyframes | 59 | 34 |
| ponytail-review | 58 | 38 |
| watch | 58 | 35 |
| doc-coauthoring | 57 | 35 |
| pitch-deck | 55 | 36 |
| simple-issue-description | 55 | 39 |
| skill-creator | 49 | 36 |
| apple-design | 49 | 34 |
| prompt-engineering-patterns | 44 | 31 |
| speech | 44 | 32 |
| no-ai-slop | 41 | 40 |

## Routing decisions worth recording

The rule applied throughout: **a description's job is routing**, so every
distinctive trigger phrase survived and the prose around it went. Specifically:

- **`hyperframes` keeps "Mandatory entry point: read first"** and "HyperFrames is
  the default framework" — those two clauses are the whole entry-point contract,
  and without them the seven skills become a flat set with no first door. What
  was cut is the input list (URL, PR, Figma, footage, music) and the sentence
  about resuming project state and installing the workflow: those describe what
  the skill *does after* it is chosen, which the body says anyway.
- **The six domain skills keep their negative routing.** `hyperframes-audio`
  still ends "Sourcing or generating audio is /media-use; clip timing is
  /hyperframes-core", and `hyperframes-keyframes` still declines broad scene
  strategy implicitly by naming only keyframe work. The entry-point/domain split
  therefore survives in both directions: one skill says "read me first", the rest
  name a narrow domain and hand off by name.
- **`hyperframes-cli` keeps the deprecated-alias line** (`validate`, `inspect`,
  `layout` → `check`). It is the one thing in that description that prevents a
  wasted failing command, and the verb list is what makes it findable at all.
- **`skill-creator` keeps evals, benchmarking and "optimise a skill's
  description"** — the last phrase is what routes *this kind of work* to it.
- **`watch` keeps the name, "like an editor", `report.md` and
  `$WATCH_VAULT_DIR`**, so the SessionStart hook's skill is still findable by
  either its output or its configuration variable. Its `argument-hint`,
  `allowed-tools` and `user-invocable: true` were untouched.
- **`ui-ux-pro-max` is a data set, not prose**, so the description keeps the
  inventory: 79 styles, 192 product palettes, 74 font pairings, 119 UX
  guidelines, 105 icons, 17 GSAP presets, 25 chart types, 22 stacks. Only "and
  reasoning profiles" and the platform gloss were compressed.
- **Quoted user phrases were kept verbatim** where they are the trigger:
  `ponytail` ("be lazy", "yagni", "do less"), `ponytail-review` ("what can we
  delete", "is this over-engineered"), `simple-issue-description` and
  `ponytail-review` keep their `/slash` forms.
- **Negative triggers were kept where they prevent a wrong pick**: `xlsx` "not
  for Word, HTML reports, or Google Sheets APIs", `docx` "not PDFs or
  spreadsheets", `pitch-deck` "not for creating presentations from scratch",
  `speech` "custom voice creation is out of scope".
- No Arabic appears in any of these 23 descriptions, so no Arabic trigger was at
  risk. (The Arabic ones are all in the owner's own skills.)

## How to re-apply on a new machine

```
python ~/.claude/skills/nj-kit/scripts/install.py
python ~/.claude/skills/nj-kit/scripts/apply-descriptions.py
```

`install.py` fetches upstream, `apply-descriptions.py` re-trims. Run the second
after any skill update too — `--check` is the cheap way to find out whether an
upstream refresh has undone the trim.

## Not done

- `description-overrides.json` is not yet wired into `install.py` or `export.py`.
  Calling the applier at the end of `install.py` would make the trim automatic,
  but both files are outside this worker's file set.
- Nothing committed, per the brief.
- Not verified beyond the gates below (house rule: run once, no
  self-verification). The gates are the applier's own `--check` and the word
  count, both machine checks inside the single run.
