# Worked example

One real pass, start to finish, so the method is legible rather than abstract. The document was a
26-page e-service requirements specification, revision 3, in Arabic, describing a food product
registration service on a Flowable-based government platform.

## Phase 0 — Frame

Type: requirements specification. Describes: one e-service on a live platform. Single document, not
a revision comparison. Reader: the authoring team, for rework before sign-off.

## Phase 1 — Ladder

| Tier | Source | Obtained |
|---|---|---|
| 1 | `service-catalogue.csv`, the service's row | yes |
| 2 | `<service>.bpmn20.xml` | yes |
| 3 | `messages_ar.txt` for the owning microservice | yes |
| 4 | the running application | no |
| 5 | glossary harvested from the live UI in an earlier pass | partial |

Tier 4 missing, so any check needing the live screen became a reservation. Tier 5 still settled
two label questions.

## Phase 2 — Mechanical

Identifier sequences were contiguous, `FR-01`..`FR-16`, `BR-01`..`BR-06`, `US-01`..`US-05`, with no
gaps and no dangling references. **This became the first row of the confirmed-correct section**,
which is exactly what it is for.

The unit list produced a near-duplicate candidate: the same unit written two ways inside one
dropdown. Confirmed on the page, it became a finding.

## Phase 3 — Judgement, check by check

**Optional-field check (A1).** Every field the document called optional was searched for in the
message catalogue. The catalogue's block for this service, inferred from field names because the
blocks carry no headers, confirmed roughly fifteen fields the document had marked correctly. It
also showed one field the document made conditional that the platform requires unconditionally,
and one enforced rule the document never mentions at all.

**Promise check (C1).** The document promised notifications at five events. The process model
contains exactly one notification call, on the return-to-applicant path. Written as a count and a
location, this was the single most consequential finding.

**Output check (C3).** The registry said the service produces nothing and cannot print a
certificate. The document's own service card agreed. Its scope paragraph, three pages earlier,
said the service exists to obtain approvals for issuing the output. Boilerplate, and false.

**Timer check (C2).** The document said a returned request is auto-cancelled "after the period
defined in the service settings". The model reads a named configuration key. Naming the key turned
an untestable sentence into a testable one.

**Omissions (G1).** Walking the model element by element surfaced a listener updating a committee
date on one transition. The document never mentions a committee anywhere.

**Internal contradictions (D1).** Eight, found by cross-reading, all confirmable without leaving
the document. The strongest: a rule requiring the applicant to see the officer's return notes,
against a field whose default value hides those notes from the applicant.

**System defects (E1).** One role key carried a stray space that its two sibling keys did not.
Not a document defect; reported in its own section for whoever owns the platform.

## Phase 4 — Confirm

Extraction of this document mangled Arabic in the usual way, so every count rested on Latin
identifiers, on error codes, and on table structure. That limitation went into the reservations
section verbatim rather than being hidden.

## Phase 5 — Report

Delivered in Arabic, matching the document, with identifiers left in Latin. Order as in the client's eight sections;
severity and confidence scored per `report-template.md`. The confirmed-correct table ran to nine rows and it is the reason the
false-and-contradictory tables were accepted rather than argued.

## What the pass cost, and where the value was

| Where the findings came from | Share |
|---|---|
| Comparing the document against tiers 1 to 3 | most of the consequential ones |
| Cross-reading the document against itself | the most quickly accepted ones |
| Walking the executing artefact looking for what is absent | the most valuable ones |
| Reading the document front to back | almost none |

That last row is the reason Phase 3 is organised by check and not by page.
