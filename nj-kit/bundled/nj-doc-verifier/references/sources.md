# Sources — document-verification method

Six topics, one source each minimum. Date accessed: 2026-09-09.

## 1. ISO/IEC/IEEE 29148 — requirement verification and quality characteristics

- **ISO 29148 Explained: Requirements Engineering Standard** — Modern Requirements (blog, summarizing ISO/IEC/IEEE 29148:2018).
  https://www.modernrequirements.com/blogs/iso-29148-explained/
  - Individual requirement must be: necessary, complete (every threshold/condition the reader needs is stated), singular (one capability/action, no compound demands), unambiguous (precise, measurable terms not subjective descriptors), correct, verifiable (testable/measurable — bans subjective words like "user-friendly"), appropriate, feasible, implementation-free (states *what*, not *how*).
  - The requirement *set* must additionally be: complete (covers the whole need, no gaps), consistent (no contradictions, uniform terminology), feasible as a whole, comprehensible, and traceable bidirectionally to needs, design and verification artifacts.
  - Use as a two-pass check: score each requirement sentence against the 9 individual traits, then score the document as a whole against the 5 set traits separately — a document can pass every individual check and still fail as a set (e.g. two requirements individually fine but mutually contradictory).

## 2. INCOSE Guide to Writing Requirements — the rules

- **INCOSE Requirements Quality: The 42 Rules, Made Simple** — reqi.io.
  https://reqi.io/articles/incose-requirements-quality-42-rule-guide
  - R2 (Active voice): the responsible entity must be the grammatical subject ("The system shall…", not "…shall be used").
  - R18/R19 (Singularity): one sentence, one thought; reject requirements joined by "and," "or," "then" that bundle independent thoughts.
  - R7 (Vague terms): reject subjective/unverifiable words — "user-friendly," "adequate," "reasonable," "fast" — unless paired with a number.
  - R8/R9 (Escape clauses / open-ended lists): reject "where possible," "as appropriate," "including but not limited to" — these excuse non-compliance or leave scope open; require an explicit, closed list instead.
  - R33/R34 (Quantified, measurable performance): performance values need a stated range/tolerance ("2.0 ± 0.3 seconds"), not a bare adjective ("reliable") or an unbounded single point.

## 3. Requirements traceability matrices — bidirectional traceability, orphans/widows

- **What is a Traceability Matrix? A Guide to Requirements Traceability** — Jama Software.
  https://www.jamasoftware.com/requirements-management-guide/requirements-traceability/traceability-matrix/
  - Bidirectional traceability = forward ("did we build/verify everything we said we would?") + backward ("why does this artifact exist, what requirement justifies it?") kept consistent both ways.
  - Orphan requirement: a requirement row with an empty forward link (no test case, no design element) — flags a coverage gap.
  - Widow/orphan artifact: a test case, design element or documented feature with no backward link to any requirement — flags scope creep or undocumented behaviour.
  - Auditor check: for every requirement row, confirm both a backward source link and a forward verification-evidence link exist; for every downstream artifact (test, screen, feature described in the doc), confirm it traces back to a requirement id; treat unlinked items in either direction as defects, not omissions to fix silently.

## 4. Docs-as-code testing — runnable samples, link checking, CI gates on docs

- **Set Up Automated Tests for Docs** — Let's Treat Docs Like Code (docslikecode.com).
  https://www.docslikecode.com/learn/06-test-docs-as-code/
  - Run a link checker (e.g. Sphinx `linkcheck` builder, `html-proofer`, `htmltest`) against the *built* site, catching both internal and external dead links, as part of the normal build.
  - Store the test scripts inside the docs repository itself, not as a one-off local habit, so any contributor's PR runs the same checks.
  - Wire the checks into CI so they run automatically on every pull request and block or flag merges — treat a docs repo like a code repo with a test suite and a red/green gate.
  - (Complementary, from general docs-as-code practice not covered in depth by this source): executable/doctest-style code samples that run in CI and fail the build on drift, and screenshot-diff tooling to flag stale UI screenshots after an interface change — apply the same "test the artifact, gate the build" logic used for links to these two cases.

## 5. Google developer documentation style guide — procedures and UI-label review checklist

- **Procedures** — Google developer documentation style guide.
  https://developers.google.com/style/procedures
  - One action per numbered step; combine only trivial sequential clicks with ">" (e.g. "Click **File > New > Document**"); reserve numbering for true multi-step procedures, otherwise use a single bullet.
  - State the location/context before the action ("In Google Docs, click…", not "Click… in Google Docs").
  - State prerequisites and the goal up front so the reader can prepare before starting the steps.
  - Where useful, state the expected result of a step in the same step ("Click **Run**. The query results appear.") so the reader can self-check they're still on track.

- **UI elements and interaction** — Google developer documentation style guide.
  https://developers.google.com/style/ui-elements
  - Reproduce on-screen labels verbatim, in bold, matching the UI's own capitalization (except normalize all-caps UI labels to sentence case for readability).
  - Use monospace/code formatting for literal text the user must type into a field, distinct from the bold used for element names.
  - Never treat a UI element name as a verb ("Save the settings" is wrong; "click **Save**" is right) — this is a direct, checkable grep-able rule for a document reviewer.

## 6. "As-built vs as-designed" verification

- **Physical configuration audit** — Wikipedia (summarizing US DoD/ANSI/EIA-649 configuration-management practice).
  https://en.wikipedia.org/wiki/Physical_configuration_audit
  - A Physical Configuration Audit (PCA) is the formal comparison of the "as-built" item against its technical/design documentation, to establish or confirm the product baseline — i.e. the documentation is the thing being put on trial, not the product.
  - Checks include: whether the technical documentation matches the actual delivered design; whether any element redesigned after an earlier functional audit still meets its performance spec; whether the documented production/supporting processes match what was actually used.
  - Software analogue: confirm the design and reference documentation is consistent with the as-built software product — directly transferable to auditing an SRS/manual against a deployed system.

- **Systems Engineering for ITS — Integration and System Verification** — U.S. DOT / FHWA (SEITS guide).
  https://ops.fhwa.dot.gov/seits/sections/section3/3_3_9.html
  - Four verification methods to classify each claim in a document against: Test (measure real inputs/outputs), Demonstration (witness operation without instrumented measurement), Inspection (direct observation of physical/observable characteristics), Analysis (logical/mathematical proof where testing is infeasible).
  - Every requirement/claim in the documentation should be traceable to which of these four methods was used to confirm it, and the result recorded — a document that asserts behaviour with no stated or inferable verification method is a gap.
  - Configuration control must hold through verification: the version of the system verified and the version of the documentation being checked must be the same one, or the audit is meaningless.
