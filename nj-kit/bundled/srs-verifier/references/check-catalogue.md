# Check catalogue

Work check by check, not page by page. Each entry gives what to do, why it pays, and how to write
the finding. `[TYPE]` tags say where a check applies: `SPEC` `MANUAL` `TRAINING` `API` `SOP`
`DATA` `ANY`.

Writing rule that applies to all of them: **state the count and the location, never the
impression.** "Promises five notifications, one mechanism exists, at the return-to-applicant
path" is a finding. "Notifications seem over-stated" is not.

---

## A. Claims about enforcement

### A1. Every "optional" — test it [ANY]
Search the enforced-behaviour tier for a rule that requires the item. In software, an error or
validation message naming the field. In a procedure, a regulation making the step mandatory.

If it is enforced, the document is **false**, not imprecise: the system rejects submission without
it. This single check has produced five findings in one pass on one document.

Watch the block boundaries. Message catalogues group codes per service or module without headers.
Infer the block from the field names themselves, and if the boundary is uncertain, say so in the
finding rather than dropping it.

### A2. Every "mandatory" — test the converse [ANY]
Rarer but real: a document inventing an obligation the system does not enforce. It produces
process theatre and support tickets. Same method, opposite direction.

### A3. Conditional obligations — check the condition is reachable [SPEC][SOP][API]
"Mandatory when X" requires X to be a value the reader can determine. If X is never defined,
never displayed, or set by a system the reader cannot see, the rule is untestable.

---

## B. Enumerations and values

### B1. Every list — compare count and wording [ANY]
Against the enum registry, reference table, or authoritative list. One missing value is a real
defect: it is a dropdown option users cannot pick or a case staff will not handle.

Caveat honestly: shared registries often hold the superset for a whole product family, and a
document may legitimately show a filtered subset. Report the gap as **possible** with the caveat,
not as certain, unless you have the per-context filter.

### B2. Numbers added in parentheses [ANY]
`Refrigerated (4°C)` · `Country list (245)` · `Frozen (-18)`. Registries carry names, not
thresholds. Every number the document adds without a source is a finding, because someone will
build a validation rule on it.

### B3. Duplicates and near-duplicates within one list [ANY]
The same unit spelled two ways, the same status under two names. Catches copy-paste assembly and
is verifiable from the document alone, so it is cheap and undeniable.

### B4. Units on every quantity [ANY]
A required quantity whose unit field is optional is a defect. So is a threshold with no unit.

---

## C. Promises

### C1. Notifications [SPEC][MANUAL][API]
Count the sending mechanisms in the executing artefact and note where each sits. Compare against
the events the document promises. Write the finding as a count and a location.

### C2. Deadlines, timeouts and SLAs [SPEC][SOP][API]
A declared duration needs an enforcement mechanism: a timer, a scheduled job, a monitored queue.
No mechanism means an obligation with nothing behind it. Where a mechanism exists, **name the
configuration key it reads** — documents habitually say "as configured in service settings"
without naming the setting, which makes the rule untestable.

Check whether the declared value is a platform default before treating it as a real commitment. A
value repeated across most rows of a registry is a default, and saying so is more useful than
quoting it.

### C3. Outputs, certificates and deliverables [SPEC][SOP]
If the registry says no output is produced, every sentence implying one is false, however many
times it repeats and however boilerplate it looks. Boilerplate is the usual source.

### C4. Guarantees in user-facing text [MANUAL][TRAINING]
"You will receive", "the system will confirm", "your request will be reviewed within". Each is a
promise a reader will rely on. Each needs its mechanism.

---

## D. Structure and internal consistency

### D1. Internal contradiction [ANY]
The highest-acceptance findings: no external evidence needed, so nobody argues. Recurring shapes:

- A section says a unit or role does not exist, while another gives it a full stage.
- A rule requires displaying something, and the field's default value hides it.
- A rule makes a field a precondition while the field table calls it optional.
- A decision field offers a value that no available action can express.
- A column carries a value from the wrong vocabulary (a role where a module belongs).
- Two sections list different counts of the same set of things.
- A workflow diagram shows fewer terminal states than the text defines.
- A status vocabulary with no status for a state the document spends a page on.

### D2. Identifier hygiene [ANY]
Gaps in a sequence, duplicates, references pointing at nothing, items defined and never
referenced. Mechanical; run the scanner.

### D3. Copy-paste residue [ANY]
The clearest tell is a role name surviving into another role's section: a rule in the supervisor's
table that still says "the auditor". Also: another service's name, another product's screenshot,
a constraint referencing a field that section does not have.

### D4. Template conformance [SPEC][DATA]
Compare table columns against the approved template. A missing "constraints" or "default" column
is not cosmetic. Those columns are where value lists and limits live, so their absence is the
**cause** of many other gaps. Say that when reporting it.

### D5. Terminology drift [ANY]
The same actor named three ways across one document. Pick the tier-1 or tier-4 term as correct and
list the deviations in one row rather than one per occurrence.

---

## E. Match to the executing artefact

### E1. Roles, action keys, statuses, labels — literal comparison [SPEC][API][MANUAL]
Character by character against the model, the code, and the live UI. Findings split two ways:
document wrong, or **system wrong**. Report system defects in their own section: stray spaces
inside role keys, one stage's key formatted unlike its siblings, an action condition with no
corresponding button, a status value that misrepresents the transition it accompanies. They are
not your document's fault and they are the most valuable thing you will hand over.

### E2. Screen and section inventories [SPEC][MANUAL]
Sections a document says a screen shows, against the screen. Also cross-read: sections listed for
a reviewer's screen that nothing on the submitter's screen ever populates.

### E3. Flow paths [SPEC][SOP]
Every transition, its trigger, its guard and its terminal state. Diagram against model, and text
against diagram. The two disagree more often than either disagrees with the model.

### E4. Generalised wording over a specific mechanism [SPEC]
"Returns to the stage of whichever officer returned it" when exactly one stage can return, and the
implementation is wired to that one stage. Not false today, wrong the day a second return path is
added. Report as ambiguous with the mechanism named.

---

## F. Ambiguity and testability

### F1. Vague quantifiers [ANY]
"Promptly", "regularly", "as appropriate", "sufficient", "user-friendly", "as needed". Each is a
requirement nobody can fail. Replace with a number or delete.

### F2. Requirements without a testable verb [SPEC][API][SOP]
"The system supports X" cannot be tested. "The system rejects submission when X is empty" can.

### F3. Control type contradicting behaviour [SPEC][MANUAL]
A checkbox described as "must be answered" is a two-option question, not a checkbox: an unchecked
box is indistinguishable from an unanswered one. Any dependent-field rule built on "when not
checked" then fires by default. Look for this wherever a yes/no drives a conditional field.

### F4. Rules with no stated values [ANY]
A mandatory single-choice field whose options are never listed. A lab, a decision, a category
whose values exist only in someone's head.

### F5. Direction of data flow [SPEC][API]
Integration tables that say a system "sends the name and rank, receives the classification" are
usually reversed. Check which side holds the key and which holds the payload.

---

## G. Omissions

Harder to find and worth more. Come at them from the system, not the document.

### G1. Mechanisms in the artefact absent from the document [SPEC][API][SOP]
Walk the executing artefact and tick off each element against the document. Listeners, hooks,
scheduled jobs and side effects are the usual survivors: a committee-date update, an audit write,
a cache invalidation, a downstream call.

### G2. Rules in the enforced-behaviour catalogue with no counterpart [SPEC][DATA]
"At least one row must be added" style rules live only in message catalogues and almost never make
it into documents.

### G3. Preconditions [ANY]
Something the system requires before the process can start, absent from assumptions and
constraints. Often visible as a single blocking error message.

### G4. Declared attributes never carried into requirements [SPEC]
An integration listed in a partners table that no functional requirement covers, while every
sibling integration got one. Registry attributes such as duration, audience or channel that the
document never mentions.

### G5. Failure and exception paths [MANUAL][SOP][TRAINING]
Documents describe the happy path. Ask what happens on rejection, timeout, partial failure,
concurrent edit, permission denied.

---

## H. Comparing two revisions

### H1. Do not trust filenames or timestamps [ANY]
Compare sizes and content. Two files with one timestamp are often one file twice.

### H2. Check the version number moved [ANY]
Content changed with the cover version unchanged is a finding by itself: nothing tells a reader the
document is different.

### H3. Diff identifier sets, not prose [ANY]
Print added and removed identifiers. Wholesale renumbering without a mapping table breaks
traceability to every prior review, test case and ticket, and that is the finding.

### H4. "Disappeared" is not "deleted" [ANY]
Before reporting a removal, search the content elsewhere. Rules migrate into other columns and
appendices. Reporting a move as a deletion destroys your credibility for the rest of the report.

### H5. Separate three kinds of change [ANY]
Fixed · unchanged · **made worse**. The third is the most valuable and the one nobody looks for.
Typical shape: a rule that made a field a precondition is deleted, the field stays "optional", and
a new integration is added that silently depends on it.

---

## I. Audience-specific checks

### I1. Reachability [MANUAL][TRAINING]
Can the reader reach step 1 from where the previous section left them, with the role they have?

### I2. Executable exercises [TRAINING]
Every exercise run in the training environment with a trainee account. Missing sample data is the
most common real defect in training material.

### I3. Timing arithmetic [TRAINING]
Segment durations summed against the stated session length.

### I4. Objective and assessment coverage, both directions [TRAINING]
Objectives untaught, content untied to an objective, assessed items untaught, emphasised items
unassessed.

### I5. Currency against the delivery date [MANUAL][TRAINING]
Screens, laws and procedures as of when the material is used, not when it was written. Every
screenshot needs a version.

### I6. Examples executed, not read [API][MANUAL]
Every code sample, curl command and payload runs. Documentation examples rot silently.
