# Claims, proof, and the ask

## The claims table

Every claim in the script gets a row before the script is delivered. No row,
the claim does not ship.

| Claim as spoken | Source (file:line, decision #, or counted thing) | Verdict |
|---|---|---|
| "Nine tabs" | `extension/report/report.html` tab list, Overview → Raw export | BUILT |
| "in both our languages" | EN ↔ AR toggle, decision 105; `core/flow.js` draws bilingual | BUILT |
| "nothing leaves this machine" | `report.html` empty state: "Nothing is uploaded." | BUILT |
| "attach credentials to the locators" | no credential store exists anywhere | **NOT BUILT** — cut |
| "in minutes the AI generates the script, accurately" | we control the input file, not the model | **UNVERIFIABLE** — cut |

Three verdicts only:

- **BUILT** — the thing exists and the source proves it. Speak it.
- **NOT BUILT** — the product does not do this. Cut it, and hand the gap to the
  client as a build decision. Never film fiction.
- **UNVERIFIABLE** — the outcome depends on something outside our control
  (a model, a network, a user's machine). Cut it. Do not soften it into a
  weasel; "usually", "up to", "helps", "virtually", "practically",
  "essentially" are how an unprovable claim gets dressed as a provable one.

The real cut, verbatim (`research/116` G6): *"We control the input file, not the
model. No claim about elapsed time or accuracy can be made in a film we cannot
substantiate."* That sentence is the standard.

## What to say instead of an adjective

Ogilvy's rule, and it is also the house rule: substantiate, or say something
else. A concrete picture beats a superlative:

| Mush | Why it fails | Replacement shape |
|---|---|---|
| "powerful capture tool" | adjective doing a metric's job | the counted thing: "nine tabs, one session" |
| "saves you time" | unfalsifiable, and unowned | the observable act: "one link. That's the whole message now." |
| "accurately" | we don't own the model | name what we *do* own: the file, the order, the timestamps |
| "easy to use" | everyone claims it | show the number of steps: "one press" |

Numbers come with a source or they do not come. A number you have decided
never to show on screen is also out — "Nineteen tools" was spoken over five
tiles the artwork spec forbade expanding, which is a picture violation and a
claim violation at once (`research/114` obj. 4).

## The ask

An end card with a URL is not a call to action. A call to action is **one verb,
one action, and the viewer can tell what happens next.**

- One ask per piece. Two asks is no ask.
- The verb is priced against what the film earned. A 50 s film that showed a
  working product can ask "Get it free". A mood piece can only ask "Learn more"
  — and if that is all you can honestly ask, the film underdelivered.
- Concrete and checkable: a named action on a named surface. "Install it from
  the Chrome Web Store" is checkable; "discover a better way" is not.
- **Write the end-card strings verbatim into the script file** — tagline,
  ask, URL, company line. The v4 commercial shipped having lost all four and no
  gate noticed (decisions 108, 110). Hand `nj-director` the string list to
  assert against the final frame; the assertion is theirs, the strings are yours.
- The end card's silent tail is protected. Seconds never come out of it — that
  tail is the only reason the ask is readable.

## Product copy (not spoken)

Taglines, store listing, release notes, brag docs: `impact-copy` governs — bold
anchor, separator, outcome with one true number. Do not restate it here and do
not invent a second house style. The claims table above still applies: the
number in an impact-copy line is a claim and needs its source row.
