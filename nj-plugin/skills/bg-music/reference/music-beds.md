# Choosing a bed by theme (rule 4, worker run music-0921)

Voice safety uses the numbers already fixed in `SKILL.md` and
`sfx-practice.md`: voice **-16 LUFS**, bed **-24 LUFS** ducked ~8 dB further
under speech (`mix.py`'s own loudnorm/sidechain graph) — not restated here as
a second convention.

## Kind of work -> mood

| Ensera work | style | primary mood | secondary | BPM / energy | lift point |
|---|---|---|---|---|---|
| product explainer | paper-punch | informational | corporate | 90-110, low-event, no vocal | end-card line only |
| educational short | paper-punch | informational | deep | 85-105, steady | last third, small lift into end card |
| event promo | kinetic-type | challenge | motivational | 115-135, rising | the reveal beat, then hold |
| recruitment / call for students | kinetic-type | motivational | challenge | 110-128, builds & resolves | on the call-to-action line |
| partnership / investor piece | paper-punch | corporate | cinematic | 90-115, steady, no vocal | the numbers/ask slide |
| achievement / announcement | kinetic-type | motivational | cinematic | 100-120, builds | the announcement line itself |
| behind-the-scenes | paper-punch | deep | informational | 70-95, sparse, atmospheric | none — stays low throughout |

House judgement (not sourced): the promo/recruitment/announcement row maps to
`challenge`/`motivational` because those are the two moods built for rising
tension and payoff (`bg-music/SKILL.md`'s own mood table, sourced from
Instagram reel `DdXP2FTOhfj`, 2026-09-17) — Ensera has no dated study of its
own audience, so this is pattern-matching the shape to the job, stated as
judgement, not measurement.

## When `arabic` is right, when it is cliché

Sourced: Skiptrace / ad-music trade commentary on "ethnic tagging" (using a
region's traditional instrumentation as a genre-signifier rather than because
the piece is about that culture) is a recognised criticism in music-supervision
practice — retrieved 2026-09-21, house paraphrase, no single canonical URL
citable stdlib-only in this pass; treat as house judgement pending a dated
primary source.

House rule, stated plainly: `arabic` (oud-led, 5 tracks, 3 of which are
BY-SA and therefore `auto_pick: false`, see rule 3) is right when the film's
**subject** is Jordanian/Arab identity, heritage, or a piece speaks IN Arabic
to an Arab audience about something specific to that context — not as a
default "we are a Jordanian company" wallpaper on an unrelated explainer.
Used as decoration on, say, a generic SaaS product demo, it reads as the
exact cliché the trade criticism above names. `bed_pick.py` therefore never
auto-picks `arabic` as a *primary* mood in the table above; it is available
by explicit `--mood arabic` only.

## Sources
- `bg-music/SKILL.md` mood table, Instagram reel `DdXP2FTOhfj`, retrieved/dated 2026-09-17 (existing).
- CC BY-SA share-alike / adaptation guidance: `creativecommons.org/faq/`, retrieved 2026-09-21 (see `library/_inbox/legacy/production-music-library/README.md`, post-cutover 2026-09-21).
- Ethnic-tagging criticism: house paraphrase of general music-supervision trade commentary, retrieved 2026-09-21, no single citable primary source found in this pass — flagged, not treated as measured.
