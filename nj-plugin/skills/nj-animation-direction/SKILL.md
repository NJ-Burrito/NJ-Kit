---
name: nj-animation-direction
description: 'Direct animation before anyone animates it: beat sheet with pressure arithmetic, blocking in numbers, shot list with character-acting briefs (objective, action, obstacle, thinking beat, end state), a gated animatic built from stills and scratch sound, review checklists, then hand-off rules for GSAP/HyperFrames, Rive state machines, Theatre.js and Remotion. Use for: direct this animation, shot list, character acting, animatic, story reel, beat map, blocking, lip-sync timing, Rive or Theatre.js direction, review a playblast. Arabic: إخراج الرسوم المتحركة، تمثيل الشخصية، أنيماتيك، لوحة القصة، قائمة اللقطات، توقيت المشاهد.'
---

# nj-animation-direction: direct first, animate second

This skill makes the decisions an animation director makes, and leaves the drawing
and rendering to the engines (`nj-hyperframes`, Remotion, Rive, Theatre.js,
`nj-style-film`, `nj-multimedia`). It exists because no public skill teaches
character acting, animatics, or how to direct Rive and Theatre.js (a GitHub search
of 61 candidates the owner ran on 2026-11-13; summary in `kb/04-existing-skills.md`).

Every rule here cites a KB entry in `kb/`: 312 entries, each with its source and a
confidence label (quote, paraphrase, search snippet or inference), read on demand,
never loaded whole. `CA` = character acting, `AN` = animatics and shot grammar,
`RT` = Rive and Theatre.js, `EX` = what the best existing skills teach.

## Response size (over-production is this skill's most common failure, EX-005)

| Asked for | Deliver |
| --- | --- |
| One shot or one acting note | the shot block + at most 3 lines of why |
| A shot list / animatic | `shotlist.json` passing the gate, plus the animatic if boards exist |
| "Direct the whole film" | the full pipeline below, one checkpoint file per stage |

## The pipeline (checkpoints are files)

| # | Stage | Checkpoint file | Gate |
| --- | --- | --- | --- |
| 0 | Intake: options, not open questions | `brief.md` | AskUserQuestion, one blocking question at most (EX-022, EX-057) |
| 1 | Arc + beat sheet | `beats` in `shotlist.json` | pressure adds up, every change has an agent (EX-006, EX-007) |
| 2 | Blocking in numbers | `blocking.md` | every move `start -> motion -> end`, metres and seconds (EX-001, EX-009) |
| 3 | Shot list + acting briefs | `shotlist.json` | `scripts/shotlist.py check` = PASS |
| 4 | Animatic | `animatic.mp4` | `scripts/shotlist.py animatic` (refuses a failing list) |
| 5 | Animatic review | `review-animatic.md` | checklist in `kb/02-animatics.md` § Animatic checklist; one outcome |
| 6 | Hand-off to the engine | engine brief | engine rules below |
| 7 | Motion-pass review | `review-motion.md` | playblast checklist `kb/01-character-acting.md` R-F |

Start from `templates/shotlist.example.json`. Timing is integer frames at the
project fps; seconds are for display only (AN-066).

## shotlist.json fields

| Field | Meaning |
| --- | --- |
| `project.fps`, `width`, `height`, `target_seconds`, `lang` | frame rate (any positive number), frame size, runtime target, `ar` or `en` for the VO band |
| `beats[]`: `id`, `turn`, `state_in`, `state_out`, `deltas[]{delta, agent}` | pressure arithmetic (EX-007) |
| `shots[]`: `id` (`ScNN_ShNN`), `beat` (starts with a beat id), `job`, `action`, `size` | one job and one beat per shot |
| `start_f`, `dur_f` | integer frames; the next shot starts at the end, minus `transition_in.dur_f` for a planned overlap |
| `transition_out.type`, `transition_in{type, dur_f}` | the decided transition; the animatic draws overlaps as a cut at the overlap start |
| `axis_side` (`A`, `B`, or `N` for a neutral on-axis shot), `cross_line` (`neutral`, `in-shot`, `cutaway`) | the 180-degree line per scene (`Sc01`) |
| `camera{move, motivation, from_scale, to_scale}` | the animatic renders zoom moves only (push-in, pull-out) |
| `board[]` | still images, split evenly over the shot |
| `characters[]`, `acting{objective, action, obstacle, thought_before, end_state, listener, holds[]{start_f, dur_f, moving}, expression_changes[]{f, during_fast_move}}` | the acting brief; hold frames are absolute |
| `on_screen_text`, `dialogue`, `sfx[]{src, at_f, dur_f, gain_db}` | text on screen, a line, sounds pinned to the shot |
| `tracks.vo[]`, `music[]`, `sfx[]`: `{id, src, start_f, dur_f, gain_db, text, lang}` | the soundtrack, frames on the timeline |

Stage templates: `templates/brief.md`, `blocking.md`, `review-animatic.md`,
`review-motion.md`. Needs Python 3.10+, and ffmpeg and ffprobe for the animatic.

## Hard rules (append-only numbering; break one only with a written note, EX-075)

1. **Beats are pressure changes, not shots** (one source, a convention). State in differs from state out, every delta names its agent, a camera move is never a beat. Choose one arc before the beat map and say why (EX-006, EX-007, EX-038).
2. **Block before you frame.** Bodies in space first, with numbers (`2.4 m -> 0.6 m over 4 s`), then the camera (EX-001, EX-009).
3. **Every character shot carries an acting block:** objective, action (tactic), obstacle, the thought before the action, the end state. Write a provable doing, never a mood: the emotion is the result of the obstacle (CA-001..CA-004, EX-002, EX-003).
4. **Show the thought.** An eye move, brow change or short hold before every decision; eyes lead the head (CA-014, CA-016, CA-023, CA-026).
5. **Never freeze.** A hold over ~16 frames gets breath, drift, a dart or a blink; over 2 s with no movement is a fail (CA-035, CA-036).
6. **Never change expression during a fast move**; put it before or after (CA-042).
7. **One idea at a time, one dominant camera move per shot**, and every move has a motivation in the action, blocking or emotion (CA-050, EX-004, AN-045).
8. **The listener acts.** A two-hander directs the one not talking (CA-028, CA-047, CA-048).
9. **Lip sync is tested, not looked up.** Head or body leads the accent by 3-4 frames, mouth on the modulation; start at level sync and shift 1-3 frames by eye. Sources disagree (Williams: level; Thomas & Johnston: body 3-4 ahead; one blog: 2-8), so never state one number as law (CA-062..CA-065).
10. **Cut by Murch's order:** emotion, story, rhythm, eye-trace, screen plane, 3D space; cut on action; hold the 180-degree side unless a crossing is marked neutral, in-shot or cutaway (AN-031, AN-036..AN-040).
11. **Animatic before animation.** Scratch sound first, time every shot to it, edit slower than feels natural, pad dialogue ~4 frames each end (AN-005, AN-012, AN-019, AN-020). Scratch VO is a human read, a tone or a timed silence; the final Kore voice is made once, after picture lock (one model, one take).
12. **Hold budgets are starting points, not law** (establishing 3-6 s, rarely under 2 s; dialogue 2-4 s; reaction 0.5-1.5 s; one editor and one vendor); VO about 130-160 wpm in English (a synthesis around one vendor's ~150) and 110-120 for the house Arabic narration band; on-screen text benchmarked at 20 characters per second, a subtitle spec (AN-020, AN-024, AN-029, AN-056).
13. **Every adjacent pair has a decided transition**: cut by default; one animation school reads a dissolve as time passing and a wipe as a change of place (AN-044, AN-050).
14. **Diagnose before you rewrite.** Name the failure, find the single upstream decision behind several symptoms, and after three failures of the same shot change the shot, not the prompt (EX-017..EX-019; planning guidance from an AI-video skill, not measured).
15. **Sound is direction.** A frame-pinned sound table; picture lock before sound; re-pin after any length change (EX-077, EX-035).
16. **Never copy the bad parts of other skills:** no auto-launched servers, no pipe-to-shell installs, no paid third-party model calls (house rule: Claude models only; voice = the one Kore model, one take), no wildcard `allowed-tools` (EX section 9).

## Engine hand-off

| Engine | Use when | Rules |
| --- | --- | --- |
| GSAP in `nj-hyperframes` (default) | code-built shots, kinetic type, vector characters | one paused timeline; everything a pure function of `t`; no wall clock (RT-049, RT-052) |
| Remotion | React projects | compute from `useCurrentFrame()`; `Series.Sequence` per shot (AN-067, AN-068, RT-053) |
| Rive | an editor-built rig with states (idle, blink, look, talk, react) | the agent directs, a human rigs; drive by data-binding view-model writes on layers (body, head/eyes, mouth, mood); **no documented seek for a state machine** (RT-022): treat it as unseekable until tested; fixed `advance(1/fps)` steps, a rebuild and replay from frame 0 on any backward seek (O(frame) cost), or pre-render the shot to media; fixed-dt determinism is stated for the C++ runtime only (RT-023); render with `canvas-advanced`; never `@remotion/rive` for state machines (RT-026); check the free-plan splash before client delivery (RT-011, RT-024) |
| Theatre.js | a visual keyframe timeline, 3D camera moves | `@theatre/core` only (studio is AGPL); seek with `sheet.sequence.position = t`, then read `obj.value`; wait for `project.ready`; no public commits since 2024-04, so prefer GSAP when no visual editor is needed (RT-033..RT-038, RT-034) |
| Lottie | a finished After Effects / LottieFiles asset | `autoplay: false, loop: false`; HyperFrames seeks it by time in ms through `window.__hfLottie` (RT-050) |

Pin library versions in every brief; mark anything not run as UNTESTED (RT rules 2, 20).
Code sketches: `kb/03-rive-theatre.md` § Code sketches (built from the cited API, not run).

## What this skill cannot do, and the substitute

| Cannot | Substitute |
| --- | --- |
| Author a Rive rig or Theatre keyframes headlessly | write the rig/state spec for a person; drive what exists (RT-032, RT-041, RT-042) |
| Hear the mix | `nj-sound-judge` before saying how audio sounds |
| Judge "feels right" pacing by number | the checklist questions plus the owner's eye; numbers only flag outliers (AN open Q14) |
| Cite Ed Hooks, Glebas or Block verbatim | not read; use the cited secondary sources (kb open questions) |

## Reading order when a stage needs depth

1. Acting brief or playblast review: `kb/01-character-acting.md` § Rules (R-A..R-F), then the cited entries.
2. Beat map, shot grammar, animatic: `kb/02-animatics.md` § Rules, data shape, checklist.
3. Rive or Theatre: `kb/03-rive-theatre.md` § Rules, then the sketches.
4. Beat arithmetic, blocking numbers, failure codes, density ladder: `kb/04-existing-skills.md` § 11.

## House rules that apply here

Thmanyah only on any text in frame; diagrams flow left to right; viewport-only
screenshots as evidence; narration through `nj-writer` / `nj-narration` with the
one-model, one-take voice rule; credits for adapted ideas in `NOTICE.md`.

## Self-test and evals

`python scripts/shotlist.py --selftest` (gate rules, KB citations exist, a real
animatic render). `evals/evals.json`: prompts with assertions checkable from the
reply text, graded in a separate session (EX-025).
