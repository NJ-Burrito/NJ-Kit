---
name: srs-verifier
description: 'Audit a document against the system it describes (SRS, requirements, user or staff manual «دليل المستخدم»، «دليل الموظف», README, API reference, release notes). Triggers: verify, audit, review, «تدقيق الوثيقة»، «راجع الوثيقة»، «هل الوثيقة مطابقة», stale screenshots, untestable requirements.'
---

# Verifying a document against the built system

## The one question

**Does the document say what the system does?**

Not: is it well written. Not: are the commas right. A document can be
immaculate prose and still be wrong in every claim it makes, and that is the
failure this skill exists to catch. Language review is a different job —
`arabic-english-proofreading` owns it. Do not spend this pass on it.

The client's own method, in Arabic, is `references/method-ar.md`. **It is the
core and it is verbatim — read it before the first check and never edit it.**
Everything below generalises it to other document types and adds what the
standards literature contributes; the additions are marked `[+]` so the
client's method stays separable from ours.

## The pass, in order

Six steps. Each one leaves something the next reads, so a revision re-runs one
step instead of all six.

| # | Step | What it produces |
|---|---|---|
| 0 | **Frame** — document type, what it claims to describe, one document or two revisions, what the reader will do with the audit | The audit's own boundary, written down |
| 1 | **Ladder** — list the sources that outrank the document, with paths, and mark the ones you could not get | The profile's `evidence_ladder`, and the seed of section 8 |
| 2 | **Mechanical** — `scripts/doc_scan.py` with the profile | `candidates.csv`. Candidates, never findings |
| 3 | **Judgement** — work check by check from the profile table below, not page by page | The findings, each with its citation |
| 4 | **Confirm** — anything decisive is seen at the source: the rendered page, the model element, the registry row | The right to write the row |
| 5 | **Report** — the client's eight sections | The deliverable |

Reading the document front to back finds almost nothing. Step 3 is organised by
check for that reason; `references/worked-example.md` gives one full pass with
the share of findings each step actually produced.

## Rule one: do not audit the document by itself

Reading a document on its own produces stylistic notes only. The findings worth
money come from comparing it against the sources of the system that exists,
because **the document is the suspect, not the reference.**

### The evidence hierarchy (do not reorder)

| # | Source | What it settles |
|---|---|---|
| 1 | **Authoritative configuration / catalogue** — service registry, `request-types`, product config, `package.json`, OpenAPI spec, feature flags | The definition: outputs, fees, durations, categories, channels, attachments, owning body, version |
| 2 | **The executable model or the code** — `.bpmn20.xml`, the router, the controller, the workflow YAML, the migration | What the system actually *does*: steps, roles, actions, timers, notifications, terminal states |
| 3 | **Message / enum / i18n registries** — `messages_ar`, `en.json`, validation schemas, DB enums | Allowed values, mandatory fields with their codes, the wording of messages, verbatim |
| 4 | **The live UI or the running system** — the portal, the CLI's `--help`, the deployed endpoint | What the user actually sees when the model is silent |
| 5 | **The document under audit** | Nothing. It carries no authority. It is the thing being examined |

Three consequences, and they are the whole discipline:

- **A conflict between two higher sources is a discovery, not a puzzle to
  solve.** Document it, escalate it, and keep auditing. Deciding which of them
  is right is someone else's authority.
- **A missing source is stated, not guessed around.** Write the finding as
  «غير متحقَّق منه» / *unverified*. Absence of evidence is neither a verdict of
  wrong nor a verdict of right, and converting it into either is the fastest
  way to lose the client's trust in the whole report.
- **[+] Version-match first.** Confirm the system release you are checking and
  the document version on the cover are the same release. An as-built check
  against a mismatched build is not a weak check — it is invalid, and every
  finding in it is unattributable [6].

## Before you start: collect the sources

Do not begin auditing before you know which sources exist and which are
missing. List them, with paths, at the top of your notes; the report's
reservations section is built from that list.

For a client SRS specifically, that is: the service row in
`service-catalogue.csv` (or a `request-types` call) giving `OUTPUT_TYPE`,
`CAN_PRINT_CERT`, `FEES`, `SLA`, `CUSTOMER_TYPES`, `CHANNELS`, `WALK_IN`,
`DEPT_CODE`, `ATTACHMENTS` with `(req)`/`(opt)`; the process model
`<service>.bpmn20.xml`; `messages_ar.txt` for the owning microservice; and any
earlier as-built documentation for the same or a sibling service. From the
process model extract, specifically: `userTask` → stages and roles ·
`candidateGroups`/`assignee` → role keys · `conditionExpression` → action keys
· `serviceTask` + `expression` → real integrations and notifications ·
`boundaryEvent` + timer → deadlines and escalation, with the config key name ·
`executionListener` → terminal states · `endEvent` → the count and names of
final paths. §2 of `references/method-ar.md` is the authority on this.

## The profile: one file per project, naming that project's evidence

The method travels; the sources do not. Everything local lives in a
`profile.json` kept **next to the documents it serves**, never inside this
skill — the evidence ladder with a path per tier, the identifier patterns, the
optional/mandatory and vague-wording vocabularies in the document's languages,
the template's columns, and the live UI's base URL with the *location* of its
credentials. Nothing reads a credential; the location is all that is ever
printed.

- `profile.example.json` (skill root) — a filled generic copy to adapt.
- `references/evidence-profiles.md` — the ladder per document type and the key-by-key schema.
- PROJ: `<project>/.claude/srs-verifier.profile.json`.

If you find yourself editing this SKILL.md to add a project rule, it belongs in
a profile instead, or the skill stops travelling.

## The mechanical pass: `doc_scan.py`

Machine work first, so the reading time goes to judgement.

```bash
PYTHONUTF8=1 python ~/.claude/skills/srs-verifier/scripts/doc_scan.py "doc.pdf" \
    --profile <project>/.claude/srs-verifier.profile.json --out audit-out/
```

It prints the declared ladder with each source FOUND or MISSING — the missing
ones are section 8, not a silent gap — and writes `candidates.csv`: extraction
distortion, identifier gaps and duplicates, dangling cross-references, repeated
and near-duplicate list values, parenthesised numbers with no registry behind
them, an inventory of every "optional" claim, every promise word with its count,
untestable wording, requirement-shaped lines with no testable verb, and missing
template columns. Two documents diff the revisions.

PDFs go through poppler only, and Arabic is folded with `fold_ar.py`, so the
scanner and the fidelity probe agree on what a broken extraction looks like.

**It emits candidates, not findings.** Every row is confirmed at the source or
dropped. What it cannot do is the whole of the judgement pass: whether an
optional field is actually enforced, whether an enum is complete, whether a
promise has a mechanism, internal contradiction, and the omissions.

## Document types: which sources, which checks

Pick the row, then read the matching section of
`references/checks-by-doctype.md` (and `references/check-catalogue.md` for the
checks that apply to every type), which expands each check with one concrete
worked example. The ten SRS checks are §3 of the client's method and are not
paraphrased away here.

| Document type | Evidence sources, in order | The checks that find things |
|---|---|---|
| **SRS / requirements** | catalogue row → process model → message registry → live UI | The ten checks (§3 method-ar): every "optional" field vs the mandatory-field error codes; every value list vs the enum; every promised notification vs `notificationService.*`; every stated duration vs a timer; every output/certificate vs `OUTPUT_TYPE`/`CAN_PRINT_CERT`; every conditional requirement's condition; every role and action key matched literally; internal contradiction; template conformance; the missing |
| **User / staff manual** | live UI → i18n & message registry → the model (permissions, who sees what) → catalogue | Walk every documented path in the running system and confirm it is reachable by the stated role; every field name, button label and menu item quoted **verbatim** from the UI, not paraphrased; every screenshot showing the current build (check for renamed labels, moved buttons, an old logo or theme); every prerequisite and permission actually required; every step producing the stated result; no step describing a screen that no longer exists |
| **Training material / exercises** | live system (a real run) → the manual it teaches → the model | Every exercise reproducible end to end by the stated role on the stated environment; every "expected result" observed, not assumed; sample data that still exists; timings realistic; nothing that files a real request on a live deployment without saying so |
| **Markdown docs / README** | the repo (code, configs, scripts) → CI workflow → the running app | Every command copy-pasted and run once; every flag and env var present in the code that parses it; every file path and link resolving; every version number current; the install steps working on a clean checkout; documented defaults matching the code's defaults |
| **API reference** | the schema/spec (OpenAPI, GraphQL SDL, proto) → the handler code → a live call | Every endpoint, method and path present in the router; every parameter's name, type, required-ness and default matching the handler; every documented error code producible; every response field returned; auth scopes real; deprecations marked in both places |
| **Release notes** | the commit/PR range and issue tracker → the diff → the deployed build | Every claimed change present in the diff; every breaking change flagged as such; nothing shipped that the notes omit; version and date matching the tag |

Whatever the type, the shape of the work is identical: **claim → source →
verdict → citation.** A finding without a citation is deleted before the report
is written.

## [+] Checks the standards add — apply after the type's own checks

These come from `references/sources.md`; the bracketed number is the source.
They are additions to the client's method, never replacements for it.

**On each individual requirement or instruction**

1. **Singular.** One thought per requirement. Split anything joined by "and/or"
   or carrying two independent verbs under one "and" — «و/أو» in Arabic is the
   same fault. A compound requirement cannot be tested or refused as a unit [2].
2. **Verifiable.** Reject "user-friendly", "adequate", "reasonable", "fast",
   «مناسب»، «سريع»، «سهل الاستخدام» unless a number and a tolerance are
   attached. If you cannot name the test that would prove it, it is not a
   requirement [1][2].
3. **No escape clauses.** "where possible", "as appropriate", "including but
   not limited to", «حسب الاقتضاء»، «ومنها على سبيل المثال» — each turns a
   requirement into an opinion. Demand a closed list [2].
4. **An owner in the subject.** Active voice, naming the entity that performs
   the action. A passive requirement with no owner is a requirement nobody has
   agreed to [2].
5. **Bounded performance values.** Every number carries a range or tolerance,
   not a bare point value and never an adjective [2].

**On the set as a whole**

6. **Score twice.** Once per requirement against the individual traits
   (necessary, unambiguous, singular, verifiable, feasible, implementation-free),
   once over the whole set against completeness, consistency and traceability.
   A set can fail while every requirement in it passes [1].
7. **Trace both ways.** Each requirement needs a backward link (the need or
   source it came from) and a forward link (a test, a design element, a manual
   step). Either link empty is an **orphan** — report it [3].
8. **Widows.** Each screen, feature or manual step the document describes must
   trace back to a requirement id. One that does not is undeclared scope [3].
9. **Name the verification method.** For each claim of system behaviour, say
   which method would prove it — test, demonstration, inspection, analysis. A
   claim with no inferable verification path is a finding [6].

**On manuals and procedures**

10. **One action per numbered step**, with the location stated before the
    action ("In the **Requests** tab, press **Submit**", never the reverse) [5].
11. **UI labels verbatim**, in the UI's own capitalisation and wording, and
    never used as a verb. Compare against the live screen or the i18n file,
    not against memory [5].
12. **[+] Docs-as-code: run it once.** Every command, snippet and endpoint in
    a README or API doc is executed or called once before the doc is signed
    off; every link is resolved; every screenshot is checked against the
    current build. Untested samples and stale screenshots are the two most
    common defects in developer documentation, and both are cheap to catch and
    invisible to a reader who trusts the page [4].

## Arabic PDFs — read this before any grep

Text extracted from an Arabic PDF is de-shaped and reordered
(`الإلكترونية` → `اإللكرتونية`، `آلاء` → `آالء`). Counting or grepping corrupt
text produces confident wrong findings, which is worse than no finding.

1. **Check fidelity first.** `python scripts/fold_ar.py --check-extraction
   "<file>.pdf"` prints the first 600 characters through poppler and flags the
   known corruption signatures. Compare what it prints against the rendered
   page before trusting any count.
2. **Poppler only** — `pdftotext -enc UTF-8`. pymupdf and pdfium drop Arabic
   words silently; measured 6/9 and 0/9 words against poppler's 9/9 on one
   sentence, and two of them agreeing is one shared bidi bug, not corroboration.
3. **Build the automated comparisons on Latin identifiers**, which survive
   de-shaping: `BR-01`, `FR-14`, `ERROR_00452`, `2018/41`.
4. **Fold Arabic before comparing**: `آأإا→ا`، `ىي→ي`، `ة→ه`, drop the
   diacritics and the tatweel — `python scripts/fold_ar.py` does exactly this
   on stdin. Folded text is for matching only; **quote the original**.
5. **To decide anything, render the page to an image and read it.** Every
   conclusive finding in the report must have been *seen* on the page.

## Comparing two versions

Trust neither the filename nor the date; compare sizes and content, and read
the version on the cover. Compare **identifier sets, not prose**:

```
python scripts/id_diff.py "old.pdf" "new.pdf" --json diff.json
```

It reports removed, added, numbering gaps and — the finding that matters —
suspected **renumbering**, which breaks every traceability link into the
document while each section still looks familiar. Renumbering without a mapping
table is a defect in its own right, not a formatting change.

"Disappeared" does not mean "deleted": search the new document for the text
before reporting a removal. Then separate three things — **what was fixed,
what remains, and what the update made worse.** The third is the most valuable
list in the report and the one nobody else produces.

## Strict rules

- Verify before you report. A plausible finding is not a finding.
- Never invent the correct value. Report the discrepancy, not your guess at it.
- Keep «خاطئ» *wrong* separate from «غير متحقَّق منه» *unverified*.
- Do not resolve a conflict between two sources — document it and escalate.
- Every finding carries its citation: file, line, key, table, page. A finding
  without one is deleted.
- **Start with what is correct.** A report that opens with sixty defects and
  never says what held up reads as an attack and gets argued with instead of
  acted on.

## Report format

Keep the client's eight sections, in this order, bilingual headings. Parallel
items go in tables, one or two lines each.

```markdown
# تقرير تدقيق الوثيقة / Document verification report
<document, version, date · system/build verified against · sources used and missing>

## 1. الخلاصة / Summary
## 2. المؤكَّد صحته / Confirmed correct
## 3. خاطئ / Wrong
| البند / Item | ما تقوله الوثيقة / What the document says | ما يقوله الدليل / What the evidence says |
## 4. متناقض داخلياً / Internally contradictory
## 5. غامض / Ambiguous
## 6. ناقص / Missing
## 7. ما ساء بالتحديث / Made worse by the update   (version comparison only)
## 8. تحفّظات / Reservations
```

Write the report in the language of the document. Section 8 lists every source
that was missing, every block boundary you were unsure of, and every finding
marked unverified — it is what keeps the other seven sections trustworthy.

Score every row twice, in two separate columns: **severity** by the consequence
if the document ships unchanged (blocking / major / minor / note) and
**confidence** by what settled it (confirmed / probable / unverified). Merging
them is how «خاطئ» and «غير متحقَّق منه» quietly become one thing.
`references/report-template.md` carries both scales, the row-writing rules and
the fill-in skeleton. Defects you find in the *system* rather than the document
go at the end of section 8 under their own heading, never mixed into 3–6.

## Self-check before delivery

From §8 of the client's method, plus the additions:

- [ ] Every "optional" field checked against the mandatory-field error codes
- [ ] Every value list compared with its enum
- [ ] Every promised notification, deadline and output has its evidence
- [ ] Extraction fidelity verified before any Arabic count
- [ ] Every conclusive finding seen on a rendered page
- [ ] Every finding carries a citation
- [ ] «خاطئ» separated from «غير متحقَّق منه»
- [ ] No invented number, article or role key
- [ ] What is correct is stated
- [ ] **[+]** Every requirement singular and verifiable; every id traceable both
      ways; every command in a manual or README run once; document version and
      system build confirmed to match

## Running this under nj-delegate

One **Opus** worker — this is a judgement stage: reconciling evidence,
deciding wrong versus unverified. Read `nj-delegate` §4 and §11 before briefing.

- **Read-only.** The worker never edits the document it audits. Fixing what it
  finds is a separate stage with a separate brief, after the client has seen
  the report.
- **The report is a file**, written by the worker to
  `artifacts/verification/<doc>-<date>.md`, and it is the checkpoint — a
  revision re-runs the write, not the audit.
- **Tool-call ceiling in the brief**, and no browser unless the profile needs
  the live UI (manual and training profiles do; SRS usually does not).
- **The worker returns ≤150 words** on the fixed template:

```
FILES / GATES / ARTEFACTS / LEFTOVERS / DETAIL
FILES    — the report path
GATES    — extraction fidelity clean|corrupt; doc_scan candidates + missing tiers;
           findings by section (3/4/5/6 counts)
ARTEFACTS— the report, any diff.json
LEFTOVERS— sources that were missing, findings left unverified
DETAIL   — the report file; the director does not re-derive its numbers
```

## What is in this skill

| Path | What it is |
|---|---|
| `references/method-ar.md` | The client's method, verbatim and unaltered. The core. Read first |
| `references/checks-by-doctype.md` | The profile table expanded, one worked example per check |
| `references/check-catalogue.md` | The cross-type check library (A–I): what to do, why it pays, how to write the finding |
| `references/evidence-profiles.md` | The ladder per document type, and the `profile.json` schema key by key |
| `references/extraction-traps.md` | Corruption signatures, DOCX/PPTX/XLSX/HTML traps, safe counting |
| `references/report-template.md` | Severity and confidence scales, row-writing rules, the skeleton |
| `references/worked-example.md` | One full pass end to end, and where its findings came from |
| `references/sources.md` | The standards the `[+]` additions come from, with what each contributes |
| `profile.example.json` | A filled generic profile to copy next to a project's documents |
| `scripts/doc_scan.py` | The mechanical pass: ladder check, identifiers, lists, promises, template columns, revision diff |
| `scripts/fold_ar.py` | Arabic folding for comparison; `--check-extraction file.pdf` proves a PDF is readable before you grep it |
| `scripts/id_diff.py` | Identifier-set diff of two versions: removed, added, gaps, suspected renumbering |

Run the scripts with `PYTHONUTF8=1` on Windows — cp1252 cannot print a single
Arabic character, and the failure is a crash, not a degradation.
