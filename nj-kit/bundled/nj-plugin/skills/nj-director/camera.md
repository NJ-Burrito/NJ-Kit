# Camera, staging and the move

## Staging first, camera second

Block the objects, then place the camera. Coverage is communicated as a shot
list, a floor plan with drawn positions, or a board (Yamdu, *Camera Coverage*) —
in an animated composition the floor plan is a **depth plan**: for each beat,
what sits in foreground, midground and background, and what moves between them.
Deep staging across three planes is the composition tool; parallax is what makes
it read as depth (lateral from a sideways move, forward from a move along Z,
rotational from an orbit).

**Write the depth plan as a table before the camera plan.** Objects with no plane
assigned end up drawn flat and the move buys you nothing.

## The line of action

The axis of action exists in animation too: the viewer builds a mental map from
the first framing and every later framing is judged against it. Mark the axis on
the depth plan, note which side every camera position falls on, and if you cross
it, **mark it as a deliberate cross and name the bridging shot** that carries the
viewer across (a close-up, a cutaway, or a move that crosses on screen so the
cross is witnessed rather than discovered). An unmarked cross is the fault; a
declared one is a choice.

## What a move means

A move is a sentence about attitude, not a decoration. Pick the move from the
meaning, then write the meaning in the plan so a reviewer can disagree with it.

| Move | What the viewer reads |
|---|---|
| Locked / static | The world is fixed; watch the thing that moves. Dread, attention, inevitability |
| Slow push-in (dolly in) | Closer physically and emotionally; interiority, tension rising |
| Pull-out | Distance, release, context arriving — and, at an ending, abandonment |
| Lateral dolly / track | Parallax; the world has depth and we are travelling through it |
| Orbit / arc | Examining an object from outside; it is a thing with sides |
| Crane / boom | Scale and power; who is above whom |
| Whip / snap | A hard join; only ever motivated |

Two more from lens grammar, which applies to a virtual camera the moment you give
it a perspective: a **wide** framing exaggerates depth and makes the move feel
faster; a **long** framing flattens planes together and makes the same distance
feel slow and compressed. The effect follows the camera-to-subject distance, not
the focal number — so in a composition it follows your Z and your perspective
origin.

**Speed.** Fix a screen-relative rate (e.g. ≈ 28 px/s) and keep it constant, then
scale the path distance when the duration changes. The rate is what decides
whether type stays readable at every moment; it is the number the artwork premise
rests on, so it belongs in the plan as a number.

## Hold, or cut

Hold. Then defend it.

Tarkovsky's position is that film's substance is time passing inside the shot,
not the join between shots; cutting before the viewer has processed the frame
costs the feeling the frame was built for. Murch's counter-discipline is the
Rule of Six — an ideal cut serves, in descending order: **emotion (51 %), story,
rhythm, eye-trace, planarity, spatial continuity**. Give up spatial continuity
before planarity, planarity before eye-trace, and never give up emotion.

**Defend a hold in one line, in the plan:** what the viewer is doing during the
hold. If the answer is "waiting", cut. If the answer is "reading the labels" /
"watching the evidence arrive" / "noticing nothing happens", hold.

**Cut only when you can name which of the six it serves**, and check eye-trace:
where the eye is on the last frame before and the first frame after.

A structural advantage worth knowing: **a film with no shot boundaries cannot
suffer caption-drift**, because there is no boundary for a caption to drift
across. One continuous move through rebuilt artwork structurally cures the fault
that killed three earlier cuts-based versions of the QA Wrap commercial. That is
a real reason to prefer the long move, not a style preference.

## The camera plan a renderer cannot misread

Write it as **position keyframes derived from one normalised path parameter**,
never as a speed or rate change.

```
p ∈ [0,1] , monotonically increasing, no repeated key
x     = -1150 * p
rotY  =    10 * p
scale = 1 + 0.06 * p
```

A "60 % speed dip" written as `timeScale` is stateful: seek to t=46 and you get a
different frame than a linear render. Written as **a slower position segment on
the same curve**, it is visually identical and pure. "Speed" is the wrong noun and
whoever builds it will implement it literally (research/114, objection 5).

Determinism, from the renderer's own contract: no `Date.now()`, no
`requestAnimationFrame`, no unseeded `Math.random()`, no mid-render fetch, fixed
fps/width/height, finite length, `frame → time = floor(frame)/fps`. `seekFrame(n)`
must give the same pixels regardless of seek order.

**The keyframe table is derived, not eyeballed.** Compute the linear-equivalent
duration (sum the eased segments at their effective rates), get the full rate as
`1 / that`, and every key is `previous + rate × segment`. Print the working so a
reviser re-checks it in one line.

**Determinism check inside the render run:** render 4–5 sample times by seek and
by linear playback; frames must be byte-identical. Divergence means stateful
animation crept back in. This is a machine gate, not self-verification.

## Motion that reads

The Disney principles (Thomas & Johnston, *The Illusion of Life*) that actually
bind a UI composition:

- **Staging** — one idea per beat, and the eye is led to it. Two competing
  motions in one beat means neither is seen.
- **Anticipation** — a thing that is about to move gives a small opposite cue
  first. Without it, arrivals look like pop-ins.
- **Slow in / slow out** — nothing in the physical world starts or stops
  instantly; entrances ease **out** (fast in, settle gently), exits ease **in**.
- **Follow-through / settle** — an arriving element overshoots slightly and
  settles. A stack of plates that snaps dead is a diagram; one that settles over
  ~1.2 s is an event.
- **Secondary action** — a small parallel motion (a drift, a breath of 0.4 px on
  a "locked" frame) keeps a held shot alive instead of frozen.
- **Timing** — the count of frames is the performance. Same path, different
  duration, different meaning.

Durations, from shipped design systems (Material, Carbon): micro-interaction
100–200 ms, standard transition 200–350 ms, dramatic entrance 350–600 ms, and
**exits 20–30 % faster than entrances** — a panel that lingers on the way out
reads as lag, not polish (and QA Wrap ships that asymmetry deliberately, decision
111). Standard easing `cubic-bezier(0.4, 0, 0.2, 1)`.

## Type inside a moving camera

A 3D transform rasterises text once and scales it, so small UI type shimmers or
softens across a long move. **Before any asset is drawn**, build the throwaway
stub: one `preserve-3d` parent, three planes, the real face at your smallest and
largest sizes, the real curve. Seek to three or four times across the move and
read the type. If it softens, those labels are drawn as SVG paths, not live text.
Under an hour, no assets, and it is the only test that can invalidate the artwork
premise rather than the schedule.

## Product presence

The extension **is** the product: fifteen seconds with the product off screen is
a quarter of a 60 s film spent on something else, and it shipped once because a
scene override was silently throwing away captures that already existed
(decision 104). Brand-presence research says the same from the other side —
recall improves markedly when the brand appears within the first seconds, and
distinctive assets (the mark, the palette, a sonic cue) carry attribution.

Rules:

- The product appears by the end of the opening block, and the opening block is
  ≤ 20 % of the runtime.
- No beat asserts a count the picture is forbidden to show. "Nineteen tools" over
  five tiles is a violation, and the fix is to cut the number or draw nineteen.
- Never name an object that has receded, is edge-on, or is banned by the artwork
  spec. Illegible at the named moment is the same failure as absent.
