# Craft: what the director and the motion crew apply

Distilled from the QA Wrap film bible, which measured the accepted 2026-10-23
commercial, and from its directing checklist (sources: Twelve Principles of
Animation, StudioBinder shot guide, AIDA, BBC subtitle guidelines, Netflix
timed-text guide, GSAP docs). Values are the reference film's. Change a value
only on purpose and write down why.

## 1. The stage

- **One continuous stage, no hard cuts.** Beats change by objects arriving,
  transforming (a graphic match: scattered pieces become the logo, a dot
  becomes a card) and leaving. Size changes by scaling the world (push-in or
  pull-out), not by cutting.
- **The world is alive:** an ambient layer (blurred ghost blocks, soft
  background dots, grain) drifts linearly for the whole film. No frame is
  still, and no stretch is empty ground.
- **Light tells the act.** One soft key glow behind the focal side: warm for
  the problem, and a second colour (green) rising when the product acts. The
  turn is a change of light, not a cut.
- **The bookend.** The opening object comes back at the payoff with the
  opposite verdict (CANNOT REPRODUCE → FIXED).
- **Colour means state:** failure, a user action, success. One hero accent per
  beat; everything else stays neutral.

## 2. The shot (per beat)

- One idea per beat. If describing it needs "and", split it.
- Name the focal point first. The strongest contrast, the light, the placement
  and the motion all point at it.
- Size for the job: wide to place, medium to relate, close to isolate. Open
  each act wider, then go closer. Vary size between neighbouring beats.
- Focal object on a third, except stability and the end card (centred).
- Lines (a timeline, a thread, a row of chips) carry the eye to the focus.
- Negative space around the hero. Crowding kills weight.
- Hold the result for at least the reading time of what just appeared.

## 3. Motion grammar: one ease per object type, kept for the whole film

| Object type | Lead move | Ease, duration |
|---|---|---|
| Verdicts, stamps | slam from 1.4× to rest | power4.in, 0.25–0.95 s |
| Things that arrive (chips, buttons, badges) | scale from 0.3–0.5 with overshoot | back.out(1.4–3), 0.3–0.5 s |
| Repositioning, camera-like shifts | translate | power2.inOut, 0.5–1.4 s |
| Time (timeline, caret, clock) | draw | linear |
| Drift (scatter, float) | small translate + rotate | sine.inOut, 2.4–3 s |
| Ambient | slow translate | linear over the whole film |
| Paths (an arc from cause to effect, the logo check) | stroke draw | power2.inOut / out, 0.5–0.7 s |

Rules: one lead move per beat, with secondary motion smaller and later.
Every significant action gets an anticipation of 0.1–0.3 s (a dip, a dim, a
glow). Anything that flies travels on an arc. Parts settle after the body
(follow-through). Beats overlap through timeline labels, so a retime moves a
label, not twenty tweens. Seek-safe: no callbacks, seeded randomness only.

## 4. The arc and the pacing (40 s profile of the accepted film)

| Act | Time | Job |
|---|---|---|
| Hook + problem | 0–9.4 s | felt before explained: the pain the viewer knows |
| Turn | 9.4–10.0 s | half a second of silence, then the drop: the brand appears |
| Proof | 10–33 s | each feature as a step in one rescue, the most important longest |
| Payoff | 33–36 s | the bookend answers the opening |
| CTA | 36–40 s | end card builds, then holds still from about 38.3 s |

13 beats in 40 s: average 3.1 s, shortest 1.4 s, longest 4.5 s (the key
feature). Music at 120 BPM makes 40 s exactly 20 bars, with the drop on bar 6
(10.0 s). Order beats so the proof always follows the doubt.

## 5. Voice and words

- The voice describes what is on screen at that moment, never a different
  thing.
- **Captions are the spoken words**, following the voice: at most two lines,
  broken at phrase boundaries, at least 0.3 s per word. A caption never
  straddles a beat change, and a split caption swaps cleanly (the old line is
  gone before the new one is readable).
- The voice runs through caption changes. The only silences are the ones the
  storyboard names.
- Supers are short graphic words that act their word (STAMP slams, TRACED
  draws). Never print the spoken sentence again as a title.
- An argument, not a list: three claims shown fully beat six named.
- Budget a line by words and full stops before voicing (`mm.py fit`).

## 6. Arabic and RTL

- The on-screen Arabic carries no tashkeel, no tatweel, no Persian letters,
  Arabic punctuation (، ؟) and Western digits. Where a word would be
  ambiguous without vowels, rewrite the line rather than vowel it (e.g.
  `تقرأ` → a verbless line).
- Tashkeel goes in the TTS input only.
- Latin runs (the brand, Jira, URLs, numbers with units) are isolated
  (`unicode-bidi: isolate`) so punctuation lands on the right side.
- Captions and titles align to the inline start (right). Time, travel and
  progress run right to left in every beat, except a beat that demonstrates
  the opposite.
- The Arabic version has the same beats and meaning line by line as the
  English one. A fix to one is made on the other.

## 7. 9:16

A re-layout of the same timeline (the world scaled to about 0.66, captions in
screen space at about 66 % of the height), never a crop. Captions and the CTA
stay out of the bottom 20 % and the right-edge button column of
Reels/Shorts. Text stays at ≥ 28 px equivalent.

## 8. The end card

One shared axis for the logo, the name, the byline, the chips and the URLs,
checked to 1 px (`data-axis="center"`). The logo's optical centre is computed
from the file. The CTA is a verb plus the benefit ("Download QA Wrap. It's
free and open source."). The last frame is a designed poster frame.
