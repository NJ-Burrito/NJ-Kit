# Worked example — the QA Wrap commercial, v4 to rev 3

Real files: `research/110`, `112` (concepts), `113` (treatment), `114` (devil
pass), `115`/`116` (revisions), `research/56` decisions 95–120. This is the
whole method on one 50.5 s film.

## Step 1 — the treatment says it is fine

> Nine beats, 50.5 s. 105 words of verbatim narration at 140 wpm ≈ 45 s of
> speech. The placement rule puts roughly 38 s of speech into 50.5 s, leaving
> ~12 s of deliberate silence.

Everything the concept was sold on — "held", "quiet", "dread" — rested on those
12 seconds.

## Step 2 — the arithmetic, per beat

105 / (140/60) = **45.0 s of speech in 50.5 s. Silence = 5.5 s, not 12.5 s.**
105 words in 38 s needs **166 wpm** — an announcer read the same paragraph
forbade in the same sentence. Placement moves speech; it does not shorten it.
The person recording the voice would have worked from the wrong number.

With the treatment's own lead-in (1.0 s) and the end card's 2.2 s tail:

| # | Words | Speech s | +lead-in (+tail) | Beat s | Slack | Verdict |
|---|---|---|---|---|---|---|
| 1 | 8 | 3.43 | 4.43 | 3.2 | −1.23 | crammed |
| 2 | 8 | 3.43 | 4.43 | 3.0 | −1.43 | crammed |
| 3 | 7 | 3.00 | 4.00 | 2.8 | −1.20 | crammed |
| 4 | 12 | 5.14 | 6.14 | 8.0 | +1.86 | healthy |
| 5 | 14 | 6.00 | 7.00 | 8.0 | +1.00 | ok |
| 6 | 14 | 6.00 | 7.00 | 7.5 | +0.50 | ok |
| 7 | 20 | 8.57 | 9.57 | 7.5 | **−2.07** | **starved** |
| 8 | 7 | 3.00 | 4.00 | 4.5 | +0.50 | ok |
| 9 | 15 | 6.43 | 9.63 | 6.0 | **−3.63** | **starved** |

**Five of nine beats break under the treatment's own rule**, and the three
worst are the three the concept is sold on: the dread, the bilingual reveal,
the end card. Total slack is **+5.5 s** — the script is not over-written, it is
mis-distributed. That distinction decides the fix.

## Step 3 — violations table (words vs picture)

| Beat | Line names | On screen at that second | Verdict |
|---|---|---|---|
| 2 | typed twice, deleted twice | type-then-delete ×2 | clean |
| 4 | **"Nineteen tools"** | five tiles; nineteen forbidden by the artwork spec | **VIOLATION** |
| 6 | "Nine tabs" | nine plates | clean *if labels legible* → ask `nj-director` |
| 7 | **"in both our languages"** | the sheet at near edge-on | **VIOLATION — illegible when named** |
| 9 | **"never leaves your browser"** | no browser is drawn anywhere in the film | **VIOLATION** |

Three free to fix in text the same day. One needed a director's answer, asked
as a question, not guessed.

## Step 4 — claims

"Nineteen tools" was a true number the film had decided never to show → cut.
"In minutes, accurately" → **UNVERIFIABLE**, cut, not softened: we control the
input file, not the model. The credential scenario → **NOT BUILT**; the product
is deliberately built the other way in five files, so drawing it would be
fiction. It became a client decision, not a line.

## Step 5 — the ask that did not exist

Beat 9 was specified as "one line at `--t-body`" and **the line's text was never
written**. There was no ask anywhere in the script; a URL in an artwork spec is
not a call to action. And beat 9 was the most over-committed beat, so it was the
one most likely to be trimmed under schedule pressure — which is exactly how the
previous film lost its end card (decision 108).

Fix: the end-card strings written verbatim into the treatment, plus an assertion
handed to the director that fails the build if wordmark, sub-line, URL and
project line are not all in the final frame. Rev 3 ends: *"QA Wrap. Proof you
never had to write. Get it free."* — claim, proof, ask, twelve words.

## Step 6 — cuts, with costs

1. Beat 7's second sentence. 20 → 11 words, beat passes with 1.8 s spare.
   **Cost:** the bilingual claim leaves the script, and decision 105 fought for
   it. Mitigation: the sheet is on screen and bilingual — show it instead of
   asserting it over an edge-on plate. Alternative: grow beat 7 to 10.0 s off
   beats 5/6 slack — never off beat 9.
2. "Nineteen tools" → 8 words. **Cost:** the only hard number, which
   `impact-copy` wants. Restorable the day nineteen tiles are drawn.
3. Beat 3's line goes, its 2.8 s of picture stays. **Cost:** the three-step
   dread becomes two steps plus an action. **Gain:** the first silence in the
   film, in the nine seconds whose whole justification is silence. Rev 3 keeps
   beat 3 as *(no line — silence)*.
4. Nothing else. Beats 6 and 8 are the film; the timing fixes do not touch them.

## Step 7 — the rejected alternative, argued fairly

**Keep all 105 words and run 56 s.** It loses nothing: five or six seconds
distributed to the failing beats fixes every timing objection, and the camera
move just runs longer. Rejected because ~50 s is a client-facing figure, the
brief pins 48–52 s, and decision 106 already chose *shorten the film* over
*slow the read* — the owner judges the performance by ear, so the read rate is not
available as a timing control. **Written down and ruled on, not silently
dropped.** A rejected alternative with no ruling comes back at the edit.

## What the rev-3 script looked like

> 1. It just did it again.
> 2. Typed it twice. Deleted it twice.
> 3. *(no line — silence)*
> 4. One press, and the session starts keeping itself.
> 5. Every click, every request, every console error — caught while it happens.
> 6. And then it lands. Nine tabs, one session, in the order it actually happened.
> 7. The path is on the page, in both our languages.
> 8. Walk it once. Shift-click what the test touches.
> 9. Every pick, timestamped and exported — the agent stops guessing.
> 10. One link. That's the whole message now.
> 11. QA Wrap. Proof you never had to write. Get it free.

Short sentences, fragments, one idea each, concrete acts instead of stated
feelings, one number per line, an ask at the end — and every line with a row in
the density table and a row in the violations table.
