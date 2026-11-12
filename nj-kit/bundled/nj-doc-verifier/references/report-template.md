# Report template — severity, confidence, and the skeleton

The eight sections are the client's, in `method-ar.md`, and their order does not change. What this
file adds is how a row is scored and how a row is written.

## Severity

Rank by consequence if the document ships unchanged, not by how wrong it feels.

| Level | Meaning |
|---|---|
| **مانع / Blocking** | Someone building or acting on this will produce the wrong thing. Contradicts higher-tier evidence on a behaviour that gets implemented, enforced or relied on |
| **جوهري / Major** | Real defect, recoverable during review. Internal contradictions, missing rules the system enforces, unsupported promises |
| **طفيف / Minor** | Costs time and trust, not correctness. Terminology drift, copy-paste residue, template deviations |
| **ملاحظة / Note** | Improves the document, changes no outcome |

## Confidence

Reported separately from severity. A blocking finding at low confidence is still worth raising,
labelled honestly.

| Level | Meaning |
|---|---|
| **مؤكَّد / Confirmed** | Seen at the source, cited, reproducible by the reader |
| **مُرجَّح / Probable** | Strong evidence, one assumption stated in the row (a message-block boundary, a shared enum) |
| **غير متحقَّق منه / Unverified** | The tier that would settle it was unavailable. Stated as a question, not a verdict |

**Never merge these two columns.** «خاطئ» and «غير متحقَّق منه» collapsing into one score is how an
audit loses its credibility, and it is the client's own rule as much as ours.

## The skeleton

```markdown
# تقرير تدقيق الوثيقة / Document verification report
<document, version, date · system build verified against · sources used and missing>

## 1. الخلاصة / Summary
What the document is, what it claims to describe, what changed if it is a revision, and the shape
of the result in three sentences. Lead with the count of blocking findings.

## 2. المؤكَّد صحته / Confirmed correct
| البند / Item | الدليل / Evidence |
Short, honest, cited. Calibration, not padding.

## 3. خاطئ / Wrong
| البند | ما تقوله الوثيقة | ما يقوله الدليل | الخطورة | الثقة |

## 4. متناقض داخلياً / Internally contradictory
| # | التناقض | الخطورة |

## 5. غامض / Ambiguous
| البند | لماذا | الخطورة |

## 6. ناقص / Missing
| البند | دليل وجوده في النظام | الخطورة |

## 7. ما ساء بالتحديث / Made worse by the update    (version comparison only)
| البند | السابق | الحالي | الخطورة |

## 8. تحفّظات / Reservations
Missing evidence tiers and the checks they disabled · extraction fidelity and what it cost ·
assumptions about source boundaries · every finding left unverified.
```

**Defects in the system rather than the document** — a role key with a stray space, a message that
contradicts its own enum — are real and belong to whoever owns the platform. Put them at the end of
section 8 under a clear heading, or in their own annex; never mix them into sections 3–6, which are
about the document.

## Writing the rows

- One or two lines per row. A finding needing a paragraph is two findings.
- Every row carries its citation in the evidence column: error code, model element, registry
  column, screen, page, clause. A row without one is deleted before delivery.
- **Quote the document's own words** in «ما تقوله الوثيقة». Paraphrase invites the reply that you
  misread it.
- Give counts and locations, never impressions. "Promises five notifications; the model holds one
  call, on the return-to-applicant path" is a finding. "Notifications seem over-stated" is not.
- Where a caveat exists, put it in the row, not in a footnote nobody reads.
- Never propose the correct value unless the evidence supplies it.

## Delivering it

Write the report in the language of the document, with technical identifiers left in Latin exactly
as the system spells them. Lead the covering message with the count of blocking findings and the
one that matters most; the recipient decides how much of the table to read, and should not have to
find that out on page three.
