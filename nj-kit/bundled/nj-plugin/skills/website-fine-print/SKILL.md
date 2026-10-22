---
name: website-fine-print
description: 'Pre-ship site audit: privacy exposure, hygiene (broken links, overflow, favicon, titles, 404, copyright year), policy claims versus third parties contacted, page-observable security. Triggers: privacy policy, cookie consent, GDPR check, compliance audit, broken links, API keys exposed, security headers, client handover.'
---

# The fine print

A launch checklist for the half of a website nobody tests. Four surfaces, kept
apart because they fail differently, because they are answered by different
people, and because confusing them costs the report its credibility:

- **The legal surface** (Groups A–C) — what the site promises in its policies,
  what it actually does to the visitor's data, and who else it invites onto the
  page.
- **The hygiene surface** (Group D) — whether the thing is finished: does it
  scroll sideways on a phone, do its links go anywhere, is there still
  placeholder text in the footer. **None of this is a legal matter, and the
  report says so.**
- **The policy-text surface** (Group E) — not whether a privacy policy exists
  but whether it says the things it has to say, and whether the processors it
  names are the ones the session actually saw contacted. **Read from the policy
  page itself, never from the home page.**
- **The security surface** (Group F) — the part of a security review a rendered
  page answers for itself. **This is not a security review**, nothing here
  sends adversarial traffic at anybody, and three of its questions are not
  properties of the deployed site at all.

**This audit is not a compliance certificate and must never be handed over as
one.** It reports two things — what the page *declares* and what the page *does*
— and the gap between them. Whether that gap is unlawful is a question for
counsel in a named jurisdiction. Say so in the report, every time. A tester who
believes a clean scan means a compliant site is worse off than one who never
scanned, because they have stopped looking.

## Where the list came from

Four Instagram reels (Alex Yates ×3, `@murphmaxxing` ×1) become Groups A–C (reel 1, points 1–19), Group D (reel 2, **H**1–H20), Group E (reel 3, **L**1–L10), Group F (reel 4, **S**1–S20) — numbering prefixes are kept apart on purpose so a report row can never be traced to the wrong source. These are market signals, not specifications: every point is mapped to the standard it actually touches, or marked *convention, not a standard*. **Read reels from the video frames, never from a page scrape** — a web fetch of reel 2 dropped three of its ✗ marks and reordered the rest.
Full provenance (authors, URLs, dates, transcripts, the frames-not-scrape lesson): `references/provenance.md`.

## The split, which is the whole method

| Group | Points | What the audit does |
| --- | --- | --- |
| **A — machine-checkable** | 1–9, 17 | Checks it. Produces DECLARED, OBSERVED and a GAP line. |
| **B — accessibility** | 10–14, plus the delegated halves of H3, H11, H12, H13, H20 | **Delegates.** Runs the accessibility audit and cites its result. Never re-implements it. |
| **C — judgement calls** | 15, 16, 18, 19, plus the MANUAL tails of H9, H15, H20 | Files a MANUAL note naming who must decide. **Never a tick.** |
| **D — site hygiene** | H1–H20 | Checks the fourteen that are checkable, delegates the accessibility halves to B, files the rest with C. |
| **E — what the policy says** | L1–L10 | Checks the one that is a presence check and the three that are keyword passes over the policy's own text. Nine of its ten carry a judgement half, and those go to C. |
| **F — security a page can answer** | S1–S20 | Checks the nine a rendered page answers for itself. Four need payloads sent at a live system and are **delegated, not improvised**. Three are not properties of the deployed site at all, which is a fifth outcome and has its own row below. |

The reason the third group exists as a group, and not as silence: fake reviews,
unsupported claims, image copyright and local law are facts about the world, not
properties of a document. A tool that omits them lets a clean report imply they
were checked. A tool that ticks them lies. A tool that names them and says *a
person must answer this* is the only honest option, and it is the same line the
accessibility audit already takes with its guided manual checks.

## Every item ends as one of four things

Use these four words literally, in the report and in conversation. They are the
skill's whole vocabulary.

| | Meaning |
| --- | --- |
| **DECLARED** | The page says it. A policy page exists at a reachable URL; a banner claims consent is asked. Evidence: URL + status + the sentence quoted. |
| **OBSERVED** | The browser saw it happen. A cookie was set at 0.3 s; nine third-party origins were contacted; the consent box was pre-ticked. Evidence: the request, the cookie, the DOM node. |
| **GAP** | DECLARED and OBSERVED disagree. *The cookie policy names three cookies; the page set eleven.* This is the finding the audit exists to produce. |
| **MANUAL** | Not decidable from the page. Names the question and who must answer it. Never carries a pass. |

A GAP is the product. DECLARED alone is a reading exercise; OBSERVED alone is a
network log. The value is in the subtraction.

### The distinction reel 4 forced, and why it is not a fifth word

Three of reel 4's twenty — keys in a git history, a database access rule, a
cloud billing cap — are **not properties of the deployed site at all**. That is
not the same thing as MANUAL, and collapsing them would cost the vocabulary
something real:

> **MANUAL** means a person reads what the crawler already fetched.
> **Not the crawler's object** means the right thing was never fetched, and no
> cleverness in a browser will reach it.

The fix is different in each case. A MANUAL row is answered by someone opening
the report. A not-the-object row is answered by a *different tool entirely*, and
the row's job is to name that tool: `gitleaks` for the history, the provider
console for the rules, the billing console for the cap. So they stay MANUAL in
the four-word vocabulary — a report with five statuses is a report nobody
learns — but every one of them says which tool, by name, in its own text. A
MANUAL row that names no tool and no person is a shrug, and this skill does not
file shrugs.

---

## Group A — machine-checkable

Full A1–A7 item table (what to look for / how / done looks like, and the
full "in a browser / with tool 18" prose): `references/item-catalogue.md`
and `references/checks.md`.

---

## Group B — accessibility: delegate, do not duplicate

Points 10–14 (fix accessibility, alt text, colour contrast, keyboard-friendly
forms, clear button labels) are **already covered, in more depth than the reel
asks for**, by the existing accessibility audit — QA Wrap's "Check accessibility"
tool: vendored axe-core 4.13.0, 105 rules, plus guided manual checks for the half
of WCAG that is not machine-decidable.

**So this skill runs that audit and cites its result. It does not re-implement a
single rule.** Two reasons, and both have cost time before: a second contrast
checker that disagrees with the first produces an argument instead of a fix, and
a duplicated rule set goes stale on the copy nobody remembers to update.

| Reel point | Where it is already answered | WCAG 2.2 |
| --- | --- | --- |
| 10 Fix accessibility | the whole audit — 105 axe rules + guided checks | — |
| 11 Alt text on images | axe `image-alt`, plus the guided *does the alt text carry meaning* | 1.1.1 |
| 12 Colour contrast | axe `color-contrast` | 1.4.3 |
| 13 Keyboard-friendly forms | guided: keyboard-only operation, visible focus, focus order, keyboard traps | 2.1.1, 2.1.2, 2.4.3, 2.4.7 |
| 14 Clear button labels | axe `button-name`, `link-name`, plus guided *link purpose out of context* | 4.1.2, 2.4.4 |

In the fine-print report these five rows carry a pointer — *see the accessibility
report, N violations, M guided checks outstanding* — and nothing else.

**Group D delegates here too**, on seven more points — see *What Group D hands
to Group B*. One of them, reflow at 1.4.10, is the single case in this skill
where a machine check and a delegated check share a criterion, because axe does
not test reflow: the measurement stays in D1, the judgement comes here, and
both sides say so rather than assuming the other did it.

---

## Group C — judgement calls: a note, never a tick

Four items (15, 16, 18, 19) plus the truth half of 17. Each produces a **MANUAL**
row naming the question and its owner. None can pass, none can fail, and none
may be silently omitted.

| Point | The question a person must answer | Owner | Why no tool can |
| --- | --- | --- | --- |
| **15** Remove fake reviews | Is every testimonial from a real, identified customer, and can you evidence it? | the business owner | A tool cannot know a name is invented. Fabricated reviews are an unfair commercial practice under Directive 2005/29/EC as amended by (EU) 2019/2161 — the Omnibus directive made it explicit. |
| **16** Remove unsupported claims | For every superlative on the page — *fastest*, *cheapest*, *number one in the region* — what is the evidence, dated and citable? | marketing + counsel | "Fastest in the region" is a factual claim about the world. Same directive. |
| **17b** Real business details | Are the registered name, address and contact route **true and current**? | the business owner | Presence is checkable (A7); truth is a matter of record, not markup. |
| **18** Copyright on images | For every image, font and icon: what is the licence, who granted it, and where is the receipt? | whoever sourced the assets | Provenance is not in the file. `lib/provenance.js` tracks QA Wrap's *own* artefacts, not the page's. |
| **19** Local laws | Which jurisdictions does this site serve, and has counsel in each reviewed it? | counsel | Jurisdiction is not a page property. The GDPR/ePrivacy framing throughout this skill is European; a site serving Jordan also answers to the Personal Data Protection Law No. 24 of 2023, and other markets differ again. Confirm the current text with counsel — do not cite a law from memory in a client-facing report. |

**The rule for this group, stated once so it is not softened later:** if any of
these five ships as a checkbox that can be ticked, the audit has become a lie
about the five things on it most likely to cost money.

Group D adds its own MANUAL rows under the same rule — listed at *What Group D
files as MANUAL*, and kept there rather than folded in here, because they are a
different weight: a stale copyright range costs nothing, a fake review can cost
a regulator's attention. The rule does not bend for the cheap ones.

---

## Group D — site hygiene

Twenty points, **H1–H20**, from the second reel. Where Groups A–C ask whether a
site is *lawful*, this group asks whether it is *finished*. That is a question
about the document rather than about the world, so it is much more checkable:
**fourteen of the twenty need no human at all.**

### The one adaptation to the vocabulary, and why it is not a loophole

In Group A, DECLARED comes from the page — a policy claims something, the
browser observes something else, and the subtraction is the GAP. **In Group D
there is almost nothing for the page to declare.** A favicon does not promise
to exist.

So here **DECLARED is the convention or the specification**, and a GAP is
OBSERVED measured against that stated expectation. This is legitimate only
while the expectation is written down and objective — a favicon whose href
404s, a `<title>` that is still the framework default, a `©` year that is not
this year. Where the expectation is a matter of taste, the item is **MANUAL**
and says so. If you find yourself raising a GAP against an expectation you have
not written into the report, you are asserting a preference as a defect.

### What this group is not

**Nothing in Group D is a legal exposure, and the report must not imply
otherwise.** A stale copyright year is a credibility signal, not an
infringement — copyright subsists without a notice under Berne. A missing meta
description breaks no rule. Only two real standards are touched: **WCAG**, via
the delegated halves, and **HTTP semantics** for H8. Everything else is
convention, and the report says *convention* where it is convention. That
honesty is what keeps Groups A–C worth reading; a report that dresses a missing
favicon as a compliance finding has spent the credibility it needs for the
cookie timing.

### The split inside the group

| Outcome | Points | Count |
| --- | --- | --- |
| **Machine-checkable** | H1, H2, H4, H5, H6, H7, H8, H9, H10, H14, H16, H17, H18, H19 | **14** |
| **Mixed** — machine part checked, accessibility part to Group B, remainder to C | H3, H11, H12, H13, H15 | **5** |
| **Delegate + judgement only** | H20 | **1** |

**Read the reel's ✗ correctly.** Three points — H1, H14, H15 — carry a red ✗ in
the source, and it means *remove this*, not *check this*. "Horizontal scroll ✗"
is an instruction to get rid of horizontal scrolling. Inverting one of these
turns a finding into its opposite.

---

**Read the reel's ✗ correctly.** Three points — H1, H14, H15 — carry a red ✗
in the source, meaning *remove this*, not *check this*. Inverting one of
these turns a finding into its opposite.

Full D1–D8 item table (what to look for / how / done looks like, and the full
"in a browser / with tool 18" prose): `references/item-catalogue.md` and
`references/checks.md`.

---

### What Group D hands to Group B

Delegated, cited, never re-implemented — the same rule as points 10–14.

| Point | The delegated half | WCAG 2.2 |
| --- | --- | --- |
| H1, H16 | reflow at 320 px without two-dimensional scrolling | 1.4.10 |
| H3 | the mobile-menu disclosure: keyboard operation, name and role | 2.1.1, 4.1.2 |
| H11 | a click target with no accessible name, or no role and tabindex | 4.1.2 |
| H12 | is the success message announced | 4.1.3 |
| H13 | is the error identified and is a correction suggested | 3.3.1, 3.3.3 |
| H17 | the logo link's accessible name | 2.4.4, 4.1.2 |
| H20 | reflow, resize text, target size | 1.4.10, 1.4.4, 2.5.8 |

**Note the one gap in the delegation:** axe does not test reflow (1.4.10), so
H1/H16's *measurement* stays in D1 and only the *judgement* — is the result
acceptable — goes to the accessibility audit's guided checks. This is the one
place in the skill where a machine check and a delegated check share a
criterion, and saying so is what stops both sides assuming the other did it.

### What Group D files as MANUAL

| Point | The question a person must answer | Owner | Why no tool can |
| --- | --- | --- | --- |
| **H9b** Copyright range | Is the *start* year of `© 2019–2026` the year the business began publishing? | the business owner | A fact about the business. Low value — record it and move on. |
| **H15b** Unused nav | This route works and nothing links to it. Should it exist? | whoever owns the site's information architecture | "Unused" beyond the mechanical cases is a decision, not a measurement. |
| **H3b, H11b, H12b, H13b** | Does the menu offer the right routes; does the button do the right thing; do the messages say what actually happened? | product owner | Correct behaviour is defined outside the document. |
| **H20** Mobile optimise | After H1, H3, H16 and the WCAG rows above are clean — does it work on a phone? | a person holding a phone | Whatever is left after the subtraction is taste, and taste does not get a tick. |

---

---

## Group E — what the privacy policy actually says (L1–L10)

Reel 3 is reel 1's cousin, not reel 2's: ten legal worries, each carrying an
invented dollar figure. **The figures are the creator's own invention and cite
no statute, regulation or settlement.** Do not repeat them in a report and do
not let a client read them as exposure estimates. What the list contributes is
one genuinely new idea and four honest reminders of what a scan cannot do.


Full L1–L10 item table: `references/item-catalogue.md`.

### The split, counted

| Outcome | Items | Count |
| --- | --- | --- |
| **Machine-checkable** | L1 | **1** |
| **Mixed** | L2, L3, L4, L6, L8 | **5** |
| **Judgement or delegate only** | L5, L7, L9, L10 | **4** |

**Nine of ten carry a judgement half, and four have nothing else.** That is the
same shape as reel 1 and the opposite of reel 2, for the same reason: this list
asks whether a site is *lawful and honest over time*, which is a question about
the world and about a month, not about the document in front of the crawler.

### The one rule this group adds

**Read the policy's text only when the page in front of you is the policy.**
Running these three keyword passes over a home page answers a question nobody
asked, and answers it wrong. The right instruction to a tester is one sentence:
*open the privacy policy and run the check again.* Where the page is not a
policy page, the row says so rather than reporting a GAP it never measured.

---

## Group F — the security surface a page can answer for itself (S1–S20)

Reel 4 is instructional rather than comic, and it is the only one of the four
that reaches past the document into the stack behind it. **This skill is not a
security review and a report must never be handed over as one.** What it can do
is the nine rows a rendered page and a recorded session answer without sending
a single hostile byte at anybody.


Full S1–S20 item table: `references/item-catalogue.md`.

### The split, counted

| Outcome | Items | Count |
| --- | --- | --- |
| **Machine-checkable** | S1, S2, S4, S14, S15, S16, S17, S18, S19 | **9** |
| **Mixed** | S5, S11, S13 | **3** |
| **Delegate** — active security testing | S6, S7, S8, S9 | **4** |
| **Not the crawler's object at all** | S3, S10, S12 | **3** |
| **Judgement, catch-all** | S20 | **1** |

### The two rules this group adds, and neither is optional

1. **Nothing sends adversarial traffic at anybody.** Six of these twenty (S6 to
   S9, S11, S13) are only provable by sending payloads at a running system.
   Doing that to a third party is a different kind of act from reading what it
   already serves, and it is not this skill's to improvise. If any of them are
   ever run, they run behind an explicit opt-in, scoped to a system the tester
   controls, with written permission, on a scanner built for it. A hand-rolled
   payload list bolted to a QA tool is how a QA engineer becomes a defendant.
2. **Nothing here is a legal exposure and the report must not imply one.** Not
   one of reel 4's twenty maps to a statute. CORS is a browser rule. The
   security headers are OWASP guidance. Say *convention*, or say *OWASP*, and
   never say *required*. The legal surface is Groups A, C and E, and mixing the
   two costs the report its credibility exactly the way mixing in Group D would.

### What Groups E and F file as MANUAL

| Row | The question | Who answers | Why it is not a tick |
| --- | --- | --- | --- |
| **L5** Deletion | Was the erasure request honoured, in the store and in the backups? | the operator | A claim about time. |
| **L7** Testimonials | Did these people say this? | the business | Reel 1's point 15. |
| **L8b** Cancellation | Is the extra friction a dark pattern or an awkward flow? | product owner, with counsel | Intent, not measurement. |
| **L9** Renewal | What arrived before the charge did? | the operator, after a cycle | A claim about a month. |
| **L10** AI safety | Does the assistant answer a person in crisis safely? | a safety reviewer | Delegated, like accessibility. |
| **S3** Keys in git | Is a key in any reachable commit? | `gitleaks` or `trufflehog` | Not the crawler's object. |
| **S10** DB rules | Does the database refuse what the app forgets to? | the provider console | Not the crawler's object. |
| **S12** Spend cap | Does a runaway bill have a ceiling? | the billing console | Not the crawler's object. |
| **S6 to S9** Active testing | Do inputs, permissions, XSS and injection hold under payloads? | a scanner, with permission | This skill does not send them. |
| **S15, S17** Headers | What did the response actually carry? | `curl -I`, or the Network panel | Not captured by a request-only session. |
| **S20** Production | Is this deployment actually configured as production? | a person, over the whole stack | A catch-all, not a check. |

## The report

One Markdown file, bilingual headings in the house SRS shape — Arabic heading,
English beneath it. Save it through the normal filing route as a **Document**.

Full skeleton (summary, machine-checkable tables, site-hygiene tables, policy
text, security, accessibility pointer, MANUAL log, standards references) is in
`references/report-template.md` — open it when writing the report, once the
audit itself is done.


**Empty cells stay empty.** A blank OBSERVED column means nobody looked, and that
is information. Filling it with "n/a" to make the table tidy destroys the only
signal the report has about its own completeness.

---

## References

Open these on demand — each is verbatim content moved out of this file so the
spine stays short. None of it changed; only the location did.

- `references/item-catalogue.md` — the full A1–A7, D1–D8, L1–L10 and S1–S20
  item tables (what to look for / how / done looks like). Open when actually
  running a check on a specific item.
- `references/checks.md` — the full "in a browser / with tool 18" prose behind
  the Group A and Group D tables. Open alongside item-catalogue.md.
- `references/report-template.md` — the full report skeleton. Open once the
  audit is done and you are writing the report.
- `references/standards.md` — every statute, directive, WCAG criterion and RFC
  cited per point, with URLs. Open before quoting one in a client-facing
  report.
- `references/provenance.md` — the four reels' authorship, URLs, dates and
  transcript files, and the frames-not-scrape lesson. Open to verify or trace
  a claim back to its reel.

## The failures to avoid

Each has already happened somewhere on this list's subject matter.

1. **Reporting the banner instead of the timing.** *"Cookie consent: present ✅"*
   is the finding that hides the violation. The question is never whether a
   banner exists; it is what was stored before it was answered.
2. **Ticking a judgement call.** The moment "Remove fake reviews ✅" appears in a
   report, the report asserts something nobody verified, about the item most
   likely to attract a regulator.
3. **Re-implementing accessibility.** Five of the nineteen points are already
   answered, better, by a tool in the same product. A second contrast checker
   that disagrees with the first produces an argument, not a fix.
4. **Letting a hygiene finding wear a legal coat.** *"Compliance issue: missing
   favicon"* is nonsense, and it is contagious — a reader who catches one row
   overreaching discounts the cookie-timing row on the same page. Group D rows
   say *convention* where they are convention, in the row.
5. **Trusting a transcription you did not make.** Reel 2 was first read by a web
   fetch that returned seventeen of twenty items, reordered, with the source's
   own ✗ marks dropped — which inverted three of them. Read the frames. This
   applies to anything arriving pre-summarised, not just to reels.
