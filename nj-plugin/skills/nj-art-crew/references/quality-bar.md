# The quality bar: template and a worked example

"Make it beautiful" is not a brief. A bar is a list a crew can check its sheet against. The lead fills this in once per run
and pastes it into every crew brief. Three parts: the reference, the rules, the budget.

## Template

```
REFERENCE    <the piece the owner liked: file, how to render it>. Yours must look at least this rich, in the same world.
LIGHT        one direction for everything: <top-left | ...>.
MAIN OBJECTS each has <N>+ tone gradients, a specular highlight, a soft contact shadow, and rim light where it helps.
DEPTH        layered: background, object, foreground particles. No flat single-colour main shapes.
MATERIALS    each reads as itself: <list: water as water, glass as glass, metal as metal, grime as grime>.
VARIANTS     clearly different in intensity: <what changes between the lowest and the highest>.
MOTION       anticipation before big moves, one primary motion at a time, follow-through, arcs, a small final flourish.
FIXED        <what may not move: see the contract file>.
BUDGET       <performance limits: effects to avoid on animated layers, element count, frame rate>.
ART          third-party only if CC0 or MIT, credited at the top of the file; no emoji; project house rules apply.
```

Rules for filling it:
- Every line must be something a person can tick on a sheet. "Elegant" is not tickable; "3+ gradients, a highlight" is.
- Name the materials of this piece. Generic lists make generic art.
- Say what differs between variants (colour, amount, speed, density), or crews make four copies of the same thing.
- Keep the performance budget honest: pick limits from the project's lowest-end target.

## Worked example: a utility that plays a short animation while it cleans up a PC

Four pieces (a toilet for RAM, an exhaust fan for CPU, a mirror for GPU, a shower for "all"), four variants each, a
.NET Framework 4 / C# 5 WPF app, vector only. The owner liked the RAM toilet scene; the first pass of the other three was
"bad". The bar the crews got:

```
REFERENCE    the RAM toilet scene, rendered with /render light|full|clogged. At least that rich, same world.
LIGHT        from the top-left everywhere.
MAIN OBJECTS 3+ tone gradients, a specular highlight, a soft contact shadow, rim light where it helps.
DEPTH        background wall (tiles), object, foreground particles. No flat single-colour main shapes.
MATERIALS    porcelain as porcelain, chrome as chrome, water as water, foam as foam, steam as soft translucent puffs,
             glass with a reflection, grime as grime.
VARIANTS     four tiers of intensity (the fan: Breeze, Vent, Overheat, Meltdown: more steam, a warning lamp, then a
             jam and a bang at the top tier).
MOTION       anticipation, one primary motion at a time, follow-through, arcs, a small flourish at the end.
FIXED        every beat time in the contract file (a sound track is cut to them), canvas size, the progress text.
BUDGET       no blur or shadow effects on animated layers; cache static groups; animate transforms and opacity;
             a few hundred elements at most; 60 fps; C# 5 only.
ART          vector only, own drawing, no emoji.
```

What the crews returned: each piece in its own file, two render-review rounds, one commit per branch. What the lead's one
check then caught and fixed: a plunger handle crossing the shower head, red "load" bars left on screen after the glass
was clean, and a marker too small to read.
