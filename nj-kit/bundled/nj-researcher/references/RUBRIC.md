# The tiering and reliability rubric

This is the judgement layer. `sources.py check` applies the parts a script can
apply (host, TLD, path shape); everything else on this page is a human or model
judgement and must be **written down next to the source**, never assumed.

House rule, inherited from ENSERA's accuracy policy: **no claim of reliability
without a recorded reason.** A tier with no `why` is not a tier, it is a guess.

---

## 1. The four tiers

| tier | what it is | the test |
|---|---|---|
| **1** | **Primary / official record.** The body that *makes* the fact publishes it: the statute, the standard, the registry entry, the filing, the agency's own dataset, the vendor's own API documentation, the paper itself. | If this source vanished, would the fact still exist somewhere else in this form? If no, it is tier 1. |
| **2** | **Peer-reviewed or institutional secondary.** Reports the primary under review: journals, proceedings, systematic reviews, national institutes, IGO reports. | Did someone other than the author check it before publication? |
| **3** | **Reputable specialist press, vendor writing, expert commentary.** Named authors, a corrections policy, real editing — but no review and usually an interest. | Is there a named human who would be embarrassed by an error, and a published correction? |
| **4** | **Aggregator, encyclopaedia, forum, social.** Wikipedia, Statista, Reddit, Stack Overflow, newsletters, Google Scholar. | These are **maps to primaries**. Use them to find the citation. Never be the citation. |

**Tier is not quality.** A tier-1 press release from a company is a primary
record of *what the company said*, and worthless as evidence that what it said
is true. A tier-3 magazine can be more accurate than a tier-1 self-report.

## 2. Primary / secondary / tertiary, said precisely

- **Primary** — the origin of the fact: the trial registration, the court
  opinion, the census table, the source code, the interview transcript, the
  measurement.
- **Secondary** — someone describing or analysing a primary: a journal article
  about a dataset, a news report of a ruling, a systematic review.
- **Tertiary** — a summary of secondaries: encyclopaedias, textbooks, Statista,
  most listicles and most LLM output.

Rule: **cite the primary, use the secondary to find and interpret it, treat the
tertiary as a lead only.** If you cannot get to the primary, say so in the
checkpoint file under "Open questions" — that is the honest failure mode.

## 3. Peer review: what it does and does not buy

Peer review checks that a method is plausible and reported. It does **not**
check that the data exist, that the analysis was run as described, or that the
result replicates. So:

- A preprint (arXiv, bioRxiv, medRxiv, SSRN) is primary and **unreviewed**. The
  word "preprint" goes in the sentence, every time.
- A published paper with **public reviews** (eLife, OpenReview) is stronger
  evidence than a prestigious acceptance, because you can read the objections.
- A **systematic review with a registered protocol** (Cochrane, PROSPERO) beats
  any single study on a settled question, and is worthless on a new one.
- **Retraction check is not optional** for medical or high-stakes claims:
  Crossref/Retraction Watch before citing.

## 4. Editorial independence, funding and conflict of interest

Ask, and record the answer:

1. **Who pays?** Advertiser, state, member companies, a foundation, a paywall,
   the subject of the story itself.
2. **Who could be hurt by the finding?** If the funder is the subject, the
   source is a self-report — still useful, differently weighted.
3. **Is there a declared competing-interests statement?** Its absence in a
   medical or policy source is itself a finding.
4. **Is it advocacy?** EFF, RSF, industry federations and think tanks can be
   rigorous *and* have a position. Record the position; do not discard the
   source for having one.
5. **State media**: authoritative primary for the state's own position
   (Petra for a Jordanian government announcement), not independent about it.

## 5. Recency, and how fast a field decays

A retrieval date is mandatory. The useful life of a fact is field-specific:

| field | half-life | note |
|---|---|---|
| LLM / AI capability, model pricing, API surface | **weeks** | anything over ~3 months is probably wrong |
| software library APIs, security advisories | **months** | pin to a version; a CVE's status changes |
| clinical guidance, drug labels | **1–3 years** | check for a newer guideline revision |
| law and regulation | **until amended** | must check "as amended", not "as enacted" |
| macroeconomic series | **quarterly**, and *revised* | first prints get revised; cite vintage |
| physical constants, historical record, mathematics | **stable** | old is fine; old *interpretation* is not |

A source that has not been re-checked inside its field's window is `stale`, not
`wrong` — say which.

## 6. Prestige is not authority for *this* claim

The most common failure. Nature is authoritative for a peer-reviewed result in
a Nature paper; it is not authoritative for a number quoted in that paper's
introduction, which belongs to whoever measured it. The WHO is authoritative for
its own guidance and not for a country's case count — the national statistics
office is. Google's docs are authoritative for Google's API and not for a
comparison with AWS.

Procedure: name the claim, then ask **who would know this first-hand**, then go
there. Tier the source *for that claim*, not in the abstract. That is why every
row in the registry carries an `authoritative_for` field and the query prints
it.

## 7. Independence: when two sources are one source

Two agreeing sources count as corroboration only if they could have disagreed.
They are **one** source if any of these holds:

- Same host or same publisher group.
- One republishes the other's wire copy (Reuters/AP/AFP syndication is the
  single commonest false corroboration).
- Both trace to the same press release, the same preprint, or the same dataset.
- Shared author, shared lab, shared funder on the specific output.
- Both cite a third source and neither checked it (a "citation cascade" — the
  claim looks well-supported and has exactly one origin).

Test to run: **for each source, name the origin of the number.** If the two
origins are the same, you have one source and you must say so. `check` prints
this as an open question because no script can answer it.

## 8. Verdicts

`check` and `candidate` use four verdicts:

- **accept** — tier 1–2, deep link, origin clear.
- **accept-with-care** — tier 3, or tier 1–2 with an interest to declare.
  Usable with the caveat written into the checkpoint file.
- **reject-as-citation** — tier 4, or PR/self-claim being passed off as
  independent. May still be used to *find* the primary.
- **unsure** — the structure gives no signal. **This is a legitimate answer.**
  It goes in the file as unsure. Inventing confidence here is the one
  unrecoverable error.

## 9. The publication gate (aligned with ENSERA)

Nothing may be published as fact unless it has: a **tier-1/2 primary source, or
two genuinely independent sources on different hosts** (§7), **a retrieval
date**, and **a named verifier who is not the author**. That is the ENSERA KB
gate, and nj-researcher does not weaken it.

## 10. Degrading honestly

When the registry has nothing and `fetch` finds nothing solid, the correct
output is a checkpoint file that says: *the claim could not be sourced; here is
what was searched; here is who would know.* A fabricated URL, a half-remembered
report title, or a confident paraphrase with no link is worse than an empty
file, because it survives review and the empty file does not.
