---
name: nj-ui-motion-laws
description: The 20 laws of UI motion and UX (Disney's animation principles applied to interfaces, plus Fitts, Hick, Miller, Doherty, Postel, Jakob and frequency of use) as build rules with numbers, a before/after for each, and motion_lint.py that fails slow, linear or unguarded CSS motion. Use when building or reviewing UI animation, micro-interactions, hover/press feedback, loading states, hit areas, menus or forms; "make it feel better", "polish the motion", "why does this feel slow", حركة الواجهة, تحسين التفاعل.
---

# UI motion laws

Twenty laws, each one a rule you can apply and check. Source: Charles Liu's reel
"20 Principles of UX & Animation" (Instagram, 2026-11-12), read frame by frame,
and the works it credits (NOTICE.md). For film or character animation use
`nj-animation-direction`; for spring physics and gestures, `nj-apple-motion`.

## How to use

1. **Build or review** against the table below. Name the law in the code review
   comment (for example, "L9 snappy timing: 450ms on a toggle").
2. **Gate:** `python scripts/motion_lint.py <files or folders>`. It prints one
   line per finding, then PASS or FAIL. Fix and run again; it is the only check.
3. **What the lint cannot see** (staging, arcs, appeal, Hick, Miller, Jakob,
   Doherty under real load) is a review item: walk the "check" column by hand
   for the screens you touched and say which laws you checked.

## The 20 laws

| # | Law | Rule | Before → after (the reel's demo) | Check |
|---|---|---|---|---|
| L1 | Squash and stretch | Things squish on impact and stretch in motion, which gives them weight | rigid icon → icon squashes slightly on press | press scale 0.95 to 0.97, never below 0.9 |
| L2 | Anticipation | A small pull-back before the big move | paper plane flies off → it dips back first | wind-up is 10 to 20% of the move's length |
| L3 | Staging | Direct the eye to one thing at a time | everything animates → one element moves | at most one primary motion per moment |
| L4 | Pose to pose | Set the key poses; let the browser fill the frames between | hand-stepped frames → start, key pose, end keyframes | keyframes, not JS per-frame updates |
| L5 | Follow-through | Parts keep moving after the main body stops, then settle | hard stop → small overshoot and settle | overshoot only on low-frequency elements (L20) |
| L6 | Slow in and slow out | Speed up and slow down; never move at constant speed | `linear` → ease-in-out | no `linear` except spinners and progress (lint M2) |
| L7 | Arcs | Move along curves, not straight lines | item flies straight to cart → along an arc | add-to-cart and fly-to targets use a curved path |
| L8 | Secondary action | A small flourish that backs up the main action | check only → check plus sparkle | the flourish is smaller and later than the main action |
| L9 | Snappy timing | Duration sets the feel; UI animations stay under 300 ms | 600 ms toggle → 200 ms | lint M1: over 300 ms fails unless marked |
| L10 | Exaggerated feedback | Push past real so the moment lands | wrong password: nothing → field shakes | errors and successes get a visible reaction |
| L11 | Solid drawing | Give flat things depth and volume | flat card → card with perspective | `perspective` set when you rotate in 3D |
| L12 | Appeal | The sum of every detail, done with care | "Downloading..." text → a button that morphs into progress | the review lists what was polished |
| L13 | Fitts's law | Bigger, closer targets are faster to hit | small icon far away → large and near the cursor's path | primary action is the largest target in its zone |
| L14 | Bigger hit areas | The clickable area can be bigger than it looks | 24×24 hit area → 44×44 | every tap target is at least 44×44 CSS px (padding or `::before`) |
| L15 | Hick's law | More choices mean slower decisions | ten equal options → few, with one default | each menu shows 7 options or fewer, or groups them |
| L16 | Miller's law | People hold about 7 things in mind; chunk information | a 16-digit card number in one run → four groups of four | numbers longer than 6 digits display in groups |
| L17 | Doherty threshold | Respond within 400 ms or it feels slow | 983 ms until "Saved" → 100 ms (optimistic) | feedback within 100 ms; anything longer than 400 ms shows progress |
| L18 | Postel's law | Accept messy input, give back clean output | rejects a phone typed with spaces → accepts it and normalises | inputs strip spaces, dashes and case before validating |
| L19 | Jakob's law | People expect your app to work like the apps they already use | cart bottom left → cart top right | standard placements: logo top-start, cart and account top-end |
| L20 | Frequency of use | The more often something is used, the less it should animate | command palette animates every open → instant | actions used many times a day, or from the keyboard, have no motion |

Always: honour `prefers-reduced-motion` (lint M4). Reduce motion to an opacity
fade or nothing; never remove the feedback itself (L10, L17).

## motion_lint.py rules

| Code | Fails when | Escape hatch |
|---|---|---|
| M1 | a `transition` or `animation` duration is over 300 ms (L9); delays and `infinite` loops are not counted | `/* motion-ok: <reason> */` on the line, for example page transitions |
| M2 | `linear` timing on a transition or a finite animation (L6) | `infinite` animations such as spinners are allowed |
| M3 | `transition: all` (animates layout and colour by accident) | none; name the properties |
| M4 | the scanned files animate but none has `prefers-reduced-motion` | none |

It reads `.css .scss .less .html .vue .svelte .jsx .tsx .js .ts`. It is a text
scan: values computed in JavaScript are not seen. `--selftest` runs its own
cases.
