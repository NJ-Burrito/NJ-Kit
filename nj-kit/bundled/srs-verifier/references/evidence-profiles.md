# Evidence ladders and the profile file

The method is fixed. The ladder is not. This file gives the ladder per document type — **which
sources outrank the document, in order** — and the schema of the `profile.json` that hands those
sources to `scripts/doc_scan.py`.

The *checks* live elsewhere: `checks-by-doctype.md` for the six document types the skill profiles,
`check-catalogue.md` for the cross-type library. This file is only about **where the truth is
kept**.

---

## How to build a ladder for an unfamiliar domain

Ask, in this order:

1. **Who decides the truth if there is a dispute?** That is tier 1. Usually a registry, a
   contract, a statute, or a signed schema. It is rarely a document written by the same team.
2. **What executes?** Code, a process model, a config, a machine. Tier 2. It cannot lie about what
   it does, only about what it was meant to do.
3. **What enforces behaviour at the boundary?** Validation messages, constraints, permission
   tables, enums. Tier 3. This is where "optional" claims go to die, and it is the highest-yield
   source in most audits.
4. **What does the user actually meet?** The running UI, the shipped device, the delivered
   training. Tier 4. It settles what the other tiers leave silent.
5. **Everything else is corroboration.** Prior documents, tickets, release notes, interviews.
   Tier 5.

If two tiers disagree, that is a finding to escalate, never one for you to settle.

**When a tier does not exist**, say so and name every check it disables. A document audited with
tiers 1 and 5 only is a consistency review, and must be labelled as one. `doc_scan.py` prints the
declared ladder and marks each source FOUND or MISSING; the missing list is the seed of section 8.

---

## Ladders by document type

**Requirements specification (SRS, BRD, functional spec)**

| Tier | Source |
|---|---|
| 1 | Service/product registry row: outputs, fees, SLA, audience, channels, attachments, owning unit |
| 2 | Process model (BPMN/DMN/state machine) or the code path that implements the flow |
| 3 | Validation message catalogue and enum registry: mandatory fields, allowed values, literal texts |
| 4 | The running application |
| 5 | Prior revisions, tickets, UAT evidence |

Identifiers: `FR-\d+` `NFR-\d+` `BR-[A-Z0-9-]+` `US-\d+` `AC-\d+` and error codes. Latin
identifiers survive text extraction; build every automated comparison on them.

**End-user or staff manual**

| Tier | Source |
|---|---|
| 1 | The shipped product at a pinned version |
| 2 | UI strings, labels and message catalogue of that build |
| 3 | Permission matrix: which role can actually see each screen and button |
| 4 | Release notes for the version the manual claims to cover |
| 5 | Support tickets naming steps that do not work |

A manual with no "applies to build X" line cannot be audited, and that is itself the first finding.

**Training material / course**

| Tier | Source |
|---|---|
| 1 | Learning objectives of record, and the assessment or certification criteria |
| 2 | The system or procedure being taught, at the version trainees will use |
| 3 | The governing policy or regulation, where the training conveys obligations |
| 4 | Observed delivery: recordings, trainer notes, exercise results |
| 5 | Prior cohorts' feedback and failure analysis |

**API / technical reference**

| Tier | Source |
|---|---|
| 1 | The schema: OpenAPI, GraphQL SDL, protobuf, published contract |
| 2 | Handler source and middleware: auth, validation, rate limits |
| 3 | Error catalogue and status-code map |
| 4 | Live responses from the documented environment |
| 5 | Changelog, deprecation notices, SDKs |

**SOP / policy / runbook** — not covered by `checks-by-doctype.md`, so its checks are here.

| Tier | Source |
|---|---|
| 1 | The regulation, standard or contract the procedure implements |
| 2 | The system enforcing the steps, where one exists |
| 3 | Records the procedure produces: logs, sign-offs, audit trail |
| 4 | How the work is actually done, observed |
| 5 | Incident reports and prior audits |

Checks: every step has a named accountable role, not a passive voice · every decision names its
criteria and its threshold · escalation paths terminate · every required record is produced by a
step that exists · frequencies and deadlines stated in units, not adverbs ("promptly",
"regularly", "as needed" are each a finding) · the exception path documented, not only the normal
path · the procedure executable by the staffing that exists.

**Data dictionary / schema documentation** — also not in `checks-by-doctype.md`.

| Tier | Source |
|---|---|
| 1 | Live DDL or migration history |
| 2 | Application-layer validation |
| 3 | Enum and reference tables |
| 4 | Actual data profile: nullability, cardinality, observed ranges |
| 5 | Prior dictionary versions |

Checks: nullability against the column · types and lengths · every enum's values and count ·
defaults · uniqueness and foreign keys · units on every quantity · every field's provenance stated
(entered, derived, integrated or system-set) · derived fields carrying their formula.

---

## profile.json — the schema

One profile per project, kept **next to the documents it serves**, never inside the skill.
`profile.example.json` at the skill root is a filled copy; the PROJ one is
`<project>/.claude/srs-verifier.profile.json`. Every key is optional: supply what the domain has.

| Key | What it does |
|---|---|
| `name`, `doc_type`, `notes` | Documentation. `notes` is where the domain's quirks go |
| `root` | Base for relative paths; defaults to the profile file's own directory |
| `evidence_ladder` | `{tier: {path, settles}}` — `path` may be a glob. `doc_scan.py` prints each tier FOUND/MISSING. Use `{note: "..."}` for a tier with no path, such as a live UI |
| `live_ui` | `base_url`, optional `backoffice_url`, and `credentials_at` — **the location only**. The scanner prints the location and never opens it. No secret is ever read, printed or pasted into a report |
| `documents` | `under_audit` glob and `reports_to` directory |
| `id_patterns` | `{kind: regex}` — the identifiers this domain uses. Drives inventory, duplicate and cross-reference checks |
| `sequential_ids` | Which of those kinds should form one contiguous series (gap detection) |
| `cross_ref_patterns` | Patterns treated as references; any that never appears at the start of a line or a cell is dangling |
| `optionality_markers` | `optional` / `mandatory` word lists, in the document's languages. The optional list drives the highest-yield check in the set |
| `promise_markers` | Words that promise a notification, deadline, output or certificate |
| `vague_terms` | Untestable wording, per domain and language |
| `testable_verbs` | Verbs that make a requirement checkable; their absence flags a requirement-shaped line |
| `required_table_columns` | The template's columns, verbatim. A missing column is where value lists and limits went |

Regexes are JSON strings, so backslashes are doubled: `"FR-\\d{1,4}"`.

If you find yourself editing `SKILL.md` to add a project rule, it belongs in a profile instead, or
the skill stops travelling.
