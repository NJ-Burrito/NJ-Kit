# STYLE-DNA — the strict shape

ALWAYS use this structure. Section names and field names do not change; the
content is whatever the references dictate. Rules, not copies: if a sentence
would only be true of one reference frame, it is not DNA. Each numbered
section needs a non-blank body — a heading with nothing under it fails the
gate (devil #4). The storyboard's own shape now ships as its own file:
`templates/STORYBOARD.md` (devil #5).

```
STYLE DNA
Sources: <each reference, and what it was used for: LOOK or MOTION>
Format:  <WxH, fps, seconds>   Clock: <the narration file>

1. COLOR PALETTE      ground / accent / materials, each with a hex and a share of the frame.
                      End with one proportion rule (e.g. 70/20/8/2).
2. TYPOGRAPHY         faces (from the brand kit, not the reference), weights, how type is
                      treated as an OBJECT in this style, and a Never line.
3. COMPOSITION        axis, zones (top / middle / bottom), what always anchors the frame,
                      platform safe areas in px, the depth layers in order.
4. MOTION LANGUAGE    frame cadence (1s / 2s / steps), entrances, exits, idle, pace
                      (a new event every X–Y s, longest hold Z s), easing per class.
5. GRAPHIC ELEMENTS   3–7 recurring motifs. Each gets a MEANING in this film, one line.
6. SHAPE LANGUAGE     the contrast the style is built on, and how an edge is finished.

Collisions: <where a house rule overrode the reference, one line each, or "none">

FEASIBILITY: <BUILDABLE | BUILDABLE WITH ASSETS | NOT IN HTML> — <one-line reason>

WORD CLASSES
HERO     one per narration line — face, size range, colour, entrance
SUPPORT  face, size range, colour, entrance
PUNCH    the word that turns the sentence — box colours for LOSS and for WIN, entrance
         (check contrast now: light text on a mid-tone box fails; pick ink or white per box)

line  HERO        PUNCH        SUPPORT
1     ...         ...          ...
```

Storyboard shape (nine fields, the Material field, the PACE stage number,
worked example): `templates/STORYBOARD.md`.
