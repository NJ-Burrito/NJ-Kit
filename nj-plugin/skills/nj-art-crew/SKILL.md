---
name: nj-art-crew
description: 'Raise animations, illustrations and screens to a high visual bar by launching one design crew per piece. Each crew owns one piece in its own git worktree, works to a written quality bar taken from the best piece the owner already liked, keeps fixed constraints (timing cut to sound, size, performance), renders its own work off screen and reviews it up to 3 rounds; the lead merges, checks every variant once and fixes what is off. Includes brief_gate.py, which fails a crew brief with unfilled fields or two crews on one file. Use when the owner says: art crew, crew it, a crew on each one, make the animations better, high-quality assets, design it like the good one, the design looks bad. Arabic: طاقم تصميم، فريق لكل واحدة، حسّن الرسوم، جودة عالية مثل اللي عجبني.'
---

# nj-art-crew: one crew per piece, a bar to beat, eyes on every frame

Use this when visual work is "not good enough" and the owner can point at one piece that is good. It is a run
for the lead (the session talking to the owner); the crews are sub-agents, one per piece. It needs a git repo,
a way to spawn background sub-agents, and a project that can render its output without a person watching.

It comes from a real run (see Origin): the first pass was judged "bad"; the second, built as below, was "I like
it so much". The difference was five conditions, not more effort. Leave one out and quality falls back.

## The five conditions

1. **One crew per piece.** A piece is one animation, illustration or screen. Pieces must live in separate files
   before any crew starts; if they share a file, split it (one file per piece, shared helpers stay in a host
   file) and commit the split. Two crews never edit the same file.
2. **A bar to beat.** Name the piece the owner liked ("at least this rich, in the same world") and write the bar
   down in checkable terms: `references/quality-bar.md` has the template and a worked example.
3. **Fixed rules.** A contract file lists what may not move (timings a soundtrack is cut to, canvas size, public
   API, an honest-progress element), the performance budget, the language and toolchain limits, and the
   project's own house rules (fonts, colours, directories). Crews restyle everything else.
4. **Eyes on their own work.** Each crew can SEE its output without touching anyone's screen: an off-screen
   renderer that writes frames and a contact sheet. If the project has none, building it is step 1.
   `references/renderers.md` covers WPF/WinForms, web, video and static images or SVG.
5. **The lead checks every result once.** After merging, the lead renders every variant, looks at every sheet
   once and fixes what is off itself, one fix per fault. `references/lead-checklist.md`.

## Run it

1. **Prepare** (lead, one commit that every crew starts from):
   - Split pieces into one file each. Add or confirm the off-screen renderer and that it works for every variant.
   - Make the renderer safe: it is chosen by a flag that must come first, and an unknown argument does nothing
     (see Safety).
   - Write `design/<name>.md`, the contract (`templates/contract.md`), with the fixed beats per variant.
   - Fill the bar from `references/quality-bar.md`. If the owner named no reference piece, ask once which existing
     piece they like most; without a reference there is no bar, and the run will not beat their taste.
2. **Worktrees** (lead): one per crew, made by hand, outside the repo:
   `git worktree add -b crew/<piece> <dir>/<piece> <commit>`. Use one spelling of the path everywhere; automatic
   worktrees can refuse on a drive-letter case mismatch (see `references/failure-modes.md`).
3. **Brief** each crew from `templates/crew-brief.md`. Fill every field. Run the gate before launching:
   `python scripts/brief_gate.py <brief>...` must print PASS (no unfilled `<FIELD>`, every required section, no
   two briefs owning the same file).
4. **Launch all crews in one message**, in the background, so they run in parallel. Give each only its own brief.
5. **While they work, do nothing for them.** Answer no questions about taste. If a crew reports a slip that could
   hurt the owner (it ran a real action), check the damage, warn the other crews at once, and fix the cause in the
   product, not only in the brief.
6. **Merge** each `crew/<piece>` branch as it reports. With one file per crew there are no conflicts. Build,
   render every variant, run the tests (`references/lead-checklist.md`).
7. **Close everything**: remove the worktrees and merged branches (to the recycle bin where the machine has one),
   stop hung commands the crews started, and move crew bookkeeping (status files, receipts) out of the repo
   next to the renders.
8. **Report** to the owner: per piece one line on what changed; the sheet paths; what was not seen live
   (smoothness on a real screen, sound sync by ear) and the one action that checks it.

## Safety rules that go into every brief

- **Only the off-screen entry point.** A crew never runs the product's real actions (a send, a delete, a deploy,
  a flush), never shows anything on the owner's screen and never touches the installed copy.
- **Put the render switch first, always; an unknown argument must do nothing.** In the origin run a crew started
  the program with a bare scene name instead of the render switch. The program treated it as a request to
  install itself and run the real action, so a test build overwrote the installed app. Fix the product, not only
  the crews: the entry point must refuse unknown arguments, and install or destructive actions must need an
  explicit flag. Do this in step 1; it is part of making the renderer safe.
- Edit one file; commit only on your own branch; never push, merge or edit another worktree. A change a shared
  file needs goes in the report.
- Never kill a process you did not start; stop every one you did.
- Third-party art only if CC0 or MIT, credited in a comment at the top of the file. Prefer drawing your own.
- Temp files and renders go outside the repo. The project's own house rules (fonts, drives, encoding, naming) go
  into the contract and are repeated in the brief.

## Judging a sheet (what every crew and the lead do)

Look at the contact sheet like an art director, frame by frame, and write down faults before fixing:

- Does anything cross, clip or hide something it should not? (a prop over another object, a handle cut off)
- Does colour tell the true story? (warning red left on after the problem is fixed)
- Does every main object have depth: gradient, highlight, contact shadow, layering?
- Does each moment read at the frame it is meant for? (a marker that cannot be seen is not a marker)
- Do the variants differ clearly in intensity, in the same world?
- Is the last frame a settled, finished state?

Up to 3 render, review, fix rounds per crew; stop earlier when a sheet shows no fault. A fourth round is polishing.

## Gates

| Gate | Command | Passes when |
|---|---|---|
| Brief gate | `python scripts/brief_gate.py <brief>...` | no unfilled field, all sections, one file per crew |
| Gate self-test | `python scripts/brief_gate.py --selftest` | the gate still catches each fault |
| Project build and tests | the project's own | clean build, tests green, every variant rendered |

Scripts live in this skill's folder (`scripts/`); run them from there or give the full path.

## Origin

Built from the NJ-Flush 1.3 scenes (2026-11-27, owner Nader Alzghoul): twelve animations, four crews, one lead.
The renderer was `/render <variant> <dir>` for scenes and `/render-ui` for the panel; each crew did two render
rounds. Details of the faults seen that night are in `references/failure-modes.md`. Companion skills for the
motion rules a crew should read: `nj-ui-motion-laws`, `nj-animation-direction`.

## What to say (for the owner)

"Art crew on each one" is enough. The long form: "Launch a crew on each one. Show them the best one we have as the
bar, have them render and review their own work up to 3 times, then check the results and fix what is off."
