# Full checks — Group A and Group D

Read from `website-fine-print/SKILL.md`. These are the four-part prose
versions (what to look for / in a browser / with tool 18 / done looks like)
that SKILL.md collapses into the Group A and Group D tables — open this file
when a table row's condensed detail isn't enough to run the check.

---

## Group A — machine-checkable, full detail

### A1. Policy pages (points 1, 2, 3, 5)

Privacy policy · Terms and conditions · Cookies policy · Refund policy.

**What to look for.** One reachable page per named policy, linked from the page
under test — not buried, not a 404, not a `mailto:`, not a PDF that fails to
open. The refund policy is commerce-specific: absent on a brochure site is not a
finding, absent on a checkout is.

**In a browser.** Read the footer, then the site map, then search
`site:example.com privacy`. Open each link — a policy link that 404s is the
commonest single finding on this list, because footers outlive the pages they
point at. Note the last-updated date; a privacy policy that predates the
analytics on the page is its own kind of gap.

**With QA Wrap tool 18, "Check the fine print"** (in the `check` group, beside
`links`, `a11y` and `perf`). One pass over the link set that **`lib/links.js`**
already fetches, matched against a list of expected policy names in several
spellings — *privacy*, *cookies*, *terms*, *T&C*, *refund*, *returns*, and their
Arabic equivalents «سياسة الخصوصية», «الشروط والأحكام», «سياسة ملفات تعريف
الارتباط», «سياسة الاسترجاع». The link checker already has the status code, so
presence and reachability come out of the same pass. Do not write a second
crawler.

**Done looks like.** A four-row table: policy · found at · status · last updated.
Every row DECLARED with a URL, or GAP with the reason (missing / 404 / redirects
off-site / no date).

### A2. Cookie consent, and its timing (point 4)

The one item on the list that a browser extension is unusually well placed to
answer, and the one most often got wrong.

**What to look for.** Not *is there a banner* — **was anything stored or read
before the visitor agreed.** ePrivacy Art. 5(3) is about the moment of storage,
so a beautiful banner over a page that already set six analytics cookies is a
worse finding than no banner at all: it is a claim that consent was obtained.
Also check that *reject* is as easy as *accept* (one click, same level), and that
declining actually stops the storing.

**In a browser.** Open DevTools → Application → Storage, clear everything, then
load the page with the Network tab recording and **do not touch the banner**.
Whatever appears in Cookies, Local Storage or IndexedDB in those first seconds
was set without consent. Then click *reject* and watch whether anything new
arrives. Strictly necessary cookies (session, load balancing, CSRF) are lawful
without consent; analytics and advertising are not.

**With tool 18.** QA Wrap's **`document_start` content script is the only thing
on the page early enough to witness the ordering**, and the extension already
records the first request. The check is: timestamp of the first non-essential
cookie or storage write, versus timestamp of the consent interaction. Pair the
result with the cookie jar the extension already reads, so *"the policy names
three cookies, the page sets eleven"* is a produced finding rather than an
exercise for the reader.

**Done looks like.** A timeline, in milliseconds: page start → first storage
write (named, with its origin) → banner painted → consent given. Plus the
reject-path result. GAP if any non-essential write lands before consent.

### A3. Form consent (point 6)

**What to look for.** Any form that collects personal data — email, phone, name,
address, anything free-text that will be stored — has a consent control, and
that control is **unticked by default**. A pre-ticked box is not consent under
GDPR Art. 7 and the EDPB's consent guidelines; neither is a bundled "by
submitting you agree to everything" line that offers no choice. The consent text
must link to the privacy policy and say what the data is for.

**In a browser.** For each form: is there a checkbox; is it `checked` on load;
is it `required`; does its label link to a policy; is marketing consent separate
from the consent needed to deliver the service. Two purposes need two controls.

**With tool 18.** Reachable from **`content/recorder.js`**, which already walks
form fields — the field walk gains a consent classification rather than a new
traversal. Report per form, not per page.

**Done looks like.** One row per form: fields collected · consent control found ·
default state · linked policy · purposes separated. GAP on any pre-ticked box, or
personal data collected with no control at all.

### A4. Data minimisation (point 7)

**What to look for.** Fields the stated purpose does not need. A newsletter
signup asking for a date of birth. A contact form asking for a national ID. A
checkout collecting a phone number it never uses. GDPR Art. 5(1)(c) is
"adequate, relevant and limited to what is necessary"; Art. 25 makes that the
default state, not an option.

**In a browser.** List every field, then ask of each: *what does the stated
purpose do with this?* A field with no answer is the finding. Required fields
carry more weight than optional ones — a required unnecessary field is coercion.

**With tool 18.** The standard is **already in the codebase, pointed the other
way**: `lib/privacy.js` holds QA Wrap's own captures to Art. 5(1)(c) and Art. 25
and never asks it of the page under test. Turning the same test outward is the
whole implementation. Note the honest limit: a tool can list the fields and flag
the high-risk shapes (national ID, date of birth, gender, health, biometrics); it
cannot know the purpose. So this item produces a **table plus a question**, and
the question is answered by a person.

**Done looks like.** Field inventory with a necessity column, high-risk fields
flagged, and one named question per unexplained field. Partly OBSERVED, partly
MANUAL — and labelled as both, not rounded to one.

### A5. Tracking (point 8)

**What to look for.** Which analytics, advertising and fingerprinting endpoints
the page called, on which page load, and whether any fired before consent.
Cross-reference against what the privacy and cookie policies name.

**In a browser.** Network tab, filter to third-party domains, sort by domain.
Look for the usual: analytics beacons, tag managers, pixel endpoints, session
recorders. Session recorders deserve their own line — a tool that replays the
visitor's screen is a different order of collection from a page-view counter, and
policies rarely mention it.

**With tool 18.** The **MAIN-world `fetch`/XHR patch already sees every
request**, so this is a classification pass over data QA Wrap already holds, not
a new capability. It is the cheapest real win on the whole list. Classify by
known endpoint families and report the unknowns as unknown rather than guessing.

**Done looks like.** A list of tracking endpoints with first-contact timestamps,
each marked *named in the policy* / *not named*. GAP on anything unnamed, and a
separate GAP on anything that fired pre-consent.

### A6. Third-party embeds (point 9)

**What to look for.** Iframes, scripts, fonts, maps, chat widgets, video players
and payment frames served from other origins. Each is another company receiving
the visitor's IP address and, for anything with cookies, more than that.

**In a browser.** Count distinct origins in the Network tab. Then say the number
out loud — *this page loads from nine other companies* — because that sentence is
what makes a stakeholder act, and no report currently contains it.

**With tool 18.** **`lib/origins.js` exists and the timeline already carries
origins**; what is missing is the roll-up. Group by origin, name what each one
serves, and flag the ones that set cookies.

**Done looks like.** One row per third-party origin: origin · what it serves ·
sets cookies · named in the policy. Plus the one-sentence count.

### A7. Business details (point 17, the presence half)

**What to look for.** A registered business name, a geographic address, and a
contact route that is not only a form — an email or a phone number. This is
e-commerce law's oldest requirement (Directive 2000/31/EC Art. 5) and the one
vibe-coded sites miss most, because the template shipped with placeholder text.

**In a browser.** Footer, contact page, terms page, imprint. Look for the
literal placeholder strings too — *Your Company*, *123 Main Street*,
*info@example.com*, `Lorem ipsum`. A placeholder is worse than an absence: it
reads as a real detail.

**With tool 18.** A presence check over the same fetched page set as A1, plus a
placeholder-string match. Cheap and high-yield.

**Done looks like.** Three rows — name · address · contact — each DECLARED with
the quoted text and its URL, or GAP. Placeholder text is a GAP, never a pass.

**And the half that is not checkable:** whether those details are *true*. That
goes to Group C.

---

## Group D — site hygiene, full detail

### D1. Horizontal scroll and mobile overflow (H1, H16, and the measurable half of H20)

**What to look for.** The page must not scroll sideways at any width a visitor
will use, and no container may clip content it cannot scroll to. H1 is the
symptom at the tester's width; H16 is the same fault found by sweeping the
widths that actually matter.

**In a browser.** `document.documentElement.scrollWidth > clientWidth + 1` is
the detection; it does not tell you what caused it. Walk for elements whose
`getBoundingClientRect().right > innerWidth` to name the culprit — it is
usually one fixed-width image, one long unbroken string, or one `100vw` inside
a padded parent. Repeat at **320 / 360 / 390 / 414** CSS px. 320 is not
arbitrary: it is the width WCAG 1.4.10 *Reflow* is written against.

**With QA Wrap tool 18.** The measurement **already exists and is wired to the
wrong thing**. `content/rtl-stress.js` runs exactly the right two passes —
measure `scrollWidth > clientWidth + 1` across every element first, then resolve
`getComputedStyle` only for the survivors, and flag only the ones that clip
without being scrollable — but it runs them under the RTL stress mode. Pointing
that pass at a viewport sweep is the whole implementation. Do not write a second
overflow detector.

**Done looks like.** One row per viewport width: width · page scrolls sideways
Y/N · overflowing elements, named by selector · overflow in px. GAP at any width
where the page scrolls sideways. Cite WCAG 1.4.10 once, in Group B's row, not
here.

### D2. Links that go nowhere (H2, H7, H15)

**What to look for.** Three distinct failures that a naive link check collapses
into one:

- **Broken** — the link resolves and the server says 404 or 5xx.
- **Dead** — the link never leaves the page: `href="#"`, `href=""`,
  `href="javascript:void(0)"`. A status check finds none of these, because
  there is no request. **This is the vibe-coded footer, specifically** (H7):
  the template shipped with placeholder anchors and nobody wired them.
- **Unused** (H15) — the link works, and nothing needs it: a duplicate of
  another nav entry, or a route reachable from nowhere else.

**In a browser.** Check the footer first — footers outlive the pages they point
at, and they are where the placeholder anchors survive. Then the nav. Then the
body.

**With tool 18.** `content/links.js` already collects one entry per distinct
URL and already lists `mailto:`, `tel:` and `javascript:` as **skipped rather
than dropped** — which is the honest count, and is also exactly the set D2 and
D8 need. The worker already has the status codes. What is new is the
*classification*: dead-shape hrefs are a finding, not a skip.

**Done looks like.** Three tables — broken · dead · duplicate — each row being
link text · href · where on the page · status or reason. "Unused" beyond the
mechanical cases (H15's tail) is a MANUAL row: whether a working page is dead
weight is a decision about the business.

### D3. Page identity — favicon, title, meta description (H4, H5, H6)

**What to look for.** The three things every page has and a generated site
forgets: an icon, a title that names *this* page, and a description.

**In a browser.** View source on the `<head>`.

- **Favicon (H4):** `link[rel~="icon"]` present *and* its href answers 200; if
  absent, does `/favicon.ico` answer. **A framework default icon is a GAP, not
  a pass** — the Vite and Next starter marks are the single clearest tell that
  nobody finished the page.
- **Title (H5):** non-empty, distinct per URL, and not a starter string —
  *React App*, *Create Next App*, *Vite + React*, *Document*, *Untitled*.
  Uniqueness is the check that needs the crawl set; the rest needs one page.
- **Meta description (H6):** `meta[name="description"]` present, non-empty, not
  byte-identical across pages.

**With tool 18.** A read of the `<head>` on each page in the same fetched set
D2 already walks, plus one extra request for the icon. No new traversal.

**Done looks like.** One row per page: URL · title · title unique Y/N · meta
description present Y/N · favicon status. **Label the whole subsection
*convention, not a standard*** — these are search-engine and browser
conventions, and nothing here cites a law.

### D4. The 404 page (H8)

**What to look for.** Two signals, and **both are required**, which is why this
gets its own subsection.

1. A path that cannot exist returns **status 404**. A site that returns 200 for
   everything has a *soft 404*, and that is the worse finding: it is a wrong
   answer at the protocol level (RFC 9110 §15.5.5), it hides broken links from
   every tool including this one, and it is what a single-page-app fallback
   route does by default.
2. The body is **the site's own page** — its header, its nav, a way back — not
   the host's or the framework's default screen.

**In a browser.** Request something deliberately absurd on the site's own
origin and read the status in the Network tab, not the page. The page can say
"not found" while the status says 200; the status is what matters.

**With tool 18.** One extra request on the origin already under test, and a
string check on the response body for the site's own header or nav text.

**Done looks like.** Two rows: status returned · body is the site's own shell.
GAP on either. A soft 404 is reported as a GAP **and** as a caveat on D2's
results, because it means the broken-link numbers understate.

### D5. Image weight (H10)

**What to look for.** Not "are the images big" — **is any image far larger than
the box it is painted into**. A 3 MB PNG displayed at 400 px is the finding; a
3 MB hero at full width may be fine.

**In a browser.** For each `<img>`: `naturalWidth` against
`getBoundingClientRect().width × devicePixelRatio`. A ratio above ~2 is wasted
bytes. Then the response side: transfer size, content type, and whether a
modern format or a `srcset` was offered at all.

**With tool 18.** **Half of this already exists.** `content/vitals.js` reads
`performance.getEntriesByType('resource')`, rolls transfer bytes up by
`initiatorType`, and already flags responses over 40 KB that arrived
uncompressed. What is missing is the ratio — the DOM half — which is what turns
a byte count into a finding a developer can act on. Bytes alone are a
performance note; bytes *against the painted size* are a defect.

**Done looks like.** One row per oversized image: URL · transfer bytes ·
natural px · painted px · ratio · format. Plus one sentence with the page's
total image weight, because that is the number a stakeholder reacts to.

### D6. Interactive elements (H3, H11, H12, H13)

The mixed group. Each of these four has a machine half, an accessibility half
that goes to Group B, and a judgement half that goes to Group C. **Report all
three parts, or the row implies the whole thing passed.**

**What to look for.**

- **Mobile menu (H3).** At ≤480 px, is there a disclosure control
  (`[aria-expanded]`, `[aria-controls]`), and does the nav become reachable when
  it is operated. *Delegate:* keyboard operation and name/role (2.1.1, 4.1.2).
  *Judgement:* whether it contains the right routes.
- **Broken buttons (H11).** A `<button>` with no listener, no `form` and no
  `type=submit`; an `<a>` whose only href is `#`; an uncaught console error
  raised on click. *Delegate:* a `<div onclick>` with no role or tabindex —
  that is axe's `button-name` territory. *Judgement:* a button that works and
  does the wrong thing.
- **Success messages (H12).** After a valid submit, did anything appear or
  change, and is any of it a live region. *Delegate:* whether it is announced —
  WCAG 4.1.3 *Status Messages*. *Judgement:* whether the wording says what
  actually happened.
- **Error messages (H13).** Submit an invalid value: does an error render, and
  is it bound to its field (`aria-invalid`, `aria-describedby`). *Delegate:*
  3.3.1 *Error Identification*, 3.3.3 *Error Suggestion*. *Judgement:* whether
  the message helps a person fix the input.

**In a browser.** H12 and H13 need the form actually submitted, twice — once
valid, once not. That is the only part of this whole skill that changes state
on someone else's site, so **do it on a staging origin, or with the client's
explicit agreement, and never on a form that files a real request**. Say in the
report which forms were submitted.

**With tool 18.** `content/recorder.js` already walks form fields; the machine
halves are a classification over that walk plus a mutation observation after
submit. Nothing here re-implements an axe rule.

**Done looks like.** One row per element or form, with **three cells**: OBSERVED
(the machine half) · delegated to accessibility (pointer, with the SC number) ·
MANUAL (the question, with an owner). An empty MANUAL cell is a claim that
there was no judgement to make — leave it blank only when that is true.

### D7. Placeholder text and the copyright year (H14, H9)

**What to look for.**

- **Placeholder text (H14).** *Lorem ipsum*, *Your Company*, *123 Main
  Street*, *info@example.com*, *example.com*, *TODO*, *Coming soon*,
  *Placeholder*, `[Your …]` — in rendered text, and also in `alt`, `title` and
  `href`, where it survives longest because nobody sees it. This is **A7's
  placeholder match widened from the business-details block to the whole
  page**: one matcher, two report rows, not two matchers.
- **Copyright year (H9).** Match `©\s*(\d{4})(\s*[–-]\s*(\d{4}))?` in the
  footer and compare the **last** year to the current one. Stale is objective.

**In a browser.** Ctrl-F the rendered page for the strings above, then view
source for the attribute cases.

**With tool 18.** A text pass over the DOM already captured, sharing A7's
string list. Cheap and high-yield — this is usually the fastest finding on the
whole audit.

**Done looks like.** One row per hit: the string · where it appears · in text or
in an attribute. A placeholder is **always a GAP, never a pass**, for the reason
A7 already gives: it reads as a real detail. The copyright year is one row,
OBSERVED against the current year — and whether the *start* year of a range is
right is a business fact, so it goes to Group C as MANUAL and is worth very
little.

### D8. Clickable logo, phone and email (H17, H18, H19)

**What to look for.** Three conventions a visitor relies on without noticing.

- **Logo (H17).** `header img` / `header svg` has an ancestor `<a>` whose href
  resolves to the same-origin root. A `<div onclick>` fails here *and* in the
  accessibility audit.
- **Phone (H18).** Text matching a phone pattern that is **not** inside
  `a[href^="tel:"]`. And for the ones that are: **do the digits in the href
  match the digits on screen?**
- **Email (H19).** The same for `a[href^="mailto:"]`, with the same mismatch
  check.

**The mismatch case is the one worth the effort.** A plain-text phone number is
an inconvenience. A `tel:` or `mailto:` whose target differs from the visible
text sends the visitor somewhere they did not read — that is a finding of a
different order, and it is invisible to every check that only asks *is it a
link*.

**In a browser.** Click the logo. Then search the rendered text for `@` and for
digit runs, and check what each one is wrapped in.

**With tool 18.** The inventory already exists — `content/links.js` lists
`tel:` and `mailto:` as skipped-not-dropped. D8 asks the inverse question of the
*text*: which contact details are on the page and not in that list. Same pass,
opposite direction.

**Done looks like.** One row per contact detail: what it is · visible text ·
href · match Y/N. Plus one row for the logo. GAP on an unlinked detail; GAP,
flagged higher, on a mismatch.
