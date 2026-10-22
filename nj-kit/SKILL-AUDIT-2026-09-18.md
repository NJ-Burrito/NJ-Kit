# The skill set, resized to our scope — audit and cut list (18 Sept 2026)

The owner: "rework all the skills we have in nj-kit and resize them to only what we
need, make them not dynamic or generic, make them on our needs only and on our
scope of work throughout the projects, so it cuts the token cost and betters the
results."

## 1. What the cost actually is — measured, not assumed

| Layer | Size | When it is paid |
|---|---|---|
| Skill **descriptions** | **5,463 words across 80 skills** | **every session, before any work** |
| `SKILL.md` bodies | 164,263 words | when a skill is invoked |
| Reference files | 669,832 words | when a skill's reference is opened |
| Assets (fonts, music, SFX) | ~48 MB | never — zero tokens |

So the always-on tax is roughly **7,000 tokens of description in every session**,
and disk size is a red herring: `pdf-typography` is 20 MB of fonts and `brag`
17 MB of audio, neither of which costs a token. **Deleting bytes is not the job;
deleting descriptions and genericness is.**

## 2. The lever depends on who owns the skill

The manifest tracks **59 third-party** skills and **20 ours**.

- **Third-party: keep or remove. Never rewrite in place.** `export.py`
  classifies by source and re-fetches from the repo, so an in-place edit is
  either overwritten or freezes a fork that stops getting upstream fixes. A
  third-party skill that is 80 % out of scope is *removed*, and the 20 % worth
  keeping is folded into one of ours as a short section.
- **Ours: rewrite freely.** These are where "on our needs only" is actually
  implementable.

**Removal is cheap and reversible**: the manifest records each skill's source
repo, so any cut here is one `install.py` away from coming back. That is the
argument for cutting hard rather than carefully.

## 3. Scope, stated, so the cut list is arguable

Across QA Wrap, PROJ and the document work, the recurring jobs are: a Chrome
extension and its QA tooling; Playwright automation; Arabic and bilingual SRS,
manuals and ministry submissions; PDFs whose text must survive copy-paste;
films and commercials through the house pipeline; identity, UI and design
review; delegation and session ops. Nothing else has appeared in any project.

## 4. Cut — 24 skills, all third-party, all reinstallable

| Group | Skills | Why |
|---|---|---|
| SEO | `seo-audit`, `seo-coach`, `seo-project-setup`, `keyword-research`, `keyword-clustering`, `local-seo`, `link-prospecting`, `competitive-landscape`, `competitor-analysis` | Nine skills, ~135 description words in every session. No project is a marketing site; not one has been invoked. |
| Competing film framework | `remotion-best-practices` | 36k reference words for a framework the house does not use. Hyperframes is the film pipeline. |
| Never used, very large | `graphify` (166k reference words), `tlc-spec-driven` (18.9k), `task-observer` (25.7k, and its own description demands invocation before the first tool call of *every* session) | The three biggest reference loads in the set, none of them in any project's record. |
| Design duplicates | `design-taste-frontend` (12.9k words), `high-end-visual-design`, `redesign-existing-projects`, `minimalist-ui`, `theme-factory`, `brandkit`, `image-to-code`, `framer-motion-animator` | Eleven design skills collapse to three: `apple-design` (used this month), `ui-ux-pro-max` (searchable data, not prose) and our own `design-gate` (the only one that can fail). |
| Duplicated by ours | `professional-proofreader` | `arabic-english-proofreading` is the house one and handles Arabic faults this does not. |
| Meta | `find-skills`, `skill-inspector`, `cco`, `i-have-adhd` | `skill-creator` covers authoring; the rest are not work. |
| Rejected in practice | `brag` | Four renders, four rejections (three in round 1, one tonight). The house film pipeline is the tool. **Its CC0 audio library moves to `bg-music/assets/` first** — the licence clearance is worth keeping even though the skill is not. |

## 5. Keep, and why each one earns its description

`apple-design`, `ui-ux-pro-max`, `design-gate` · `hyperframes` + its 8 domain
skills · `playwright-best-practices` (his profession) ·
`chrome-extension-development` (QA Wrap is one) · `docx`, `xlsx`, `pdf`,
`pdf-typography` · `arabic-english-proofreading`, `srs-verifier`,
`workflow-diagram` · `caveman`, `impact-copy`, `no-ai-slop`,
`web-design-guidelines` · `media-use`, `bg-music`, `speech`, `voice-clean`,
`watch` · `nj-method`, `nj-delegate`, `nj-agent-ops`, `nj-kit`, `nj-learn`,
`nj-security-review` · `devil`, `10x`, `ponytail-review`, `refactor`,
`test-fixing`, `scout`, `simple-issue-description`, `session-handoff`,
`safe-delete`, `script-your-tools`, `skill-creator`, `website-fine-print`,
`mcp-builder`, `prompt-engineering-patterns`, `doc-coauthoring`, `pitch-deck`,
`ponytail`.

## 6. Trim — descriptions first, because that is the only always-on cost

Target: **≤ 40 words per description**, and the rule that keeps it safe —
**a description's job is routing, so every distinctive trigger phrase stays,
including every Arabic one.** What gets cut is the prose around them. Over-trimming
a description does not save tokens, it stops the skill from ever being found,
which is the expensive failure.

Worst offenders among keepers: `website-fine-print` 231 words,
`srs-verifier` 154, `workflow-diagram` 141, `xlsx` 152, `design-gate` 137,
`script-your-tools` 131, `docx` 125, `arabic-english-proofreading` 119,
`hyperframes` 119, `10x` 118, `voice-clean` 118, `nj-method` 115, `scout` 110,
`devil` 107, `nj-learn` 104, `bg-music` 101, `nj-kit` 100.

## 7. Then bodies, ours only

| Skill | Now | Why it shrinks |
|---|---|---|
| `workflow-diagram` | 12,262 words | One figure convention, repeatedly applied. The generic flowchart theory goes. |
| `website-fine-print` | 12,075 words | Four surfaces, one checklist. |
| `pdf-typography` | 8,867 + 13,874 | One method: self-hosted base64 @font-face, Chrome print, audit. The alternatives-considered material goes. |
| `nj-delegate` | 6,029 words | The measured policy is now three lines: 0 workers by default, 1 normal, 2 recorders, Max only when named. Most of the body argues a question already settled. |
| `srs-verifier` | 3,434 + 9,153 | Held to the document shapes PROJ actually submits. |

Everything trimmed keeps its gates and its measured facts — those are the parts
that were expensive to learn. What goes is generality: options nobody here
picks, frameworks nobody here uses, and the arguments for decisions already made.
