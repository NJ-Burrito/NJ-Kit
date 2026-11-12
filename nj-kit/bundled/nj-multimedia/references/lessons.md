# Lessons from the reference runs

QA Wrap commercial: v1, a screenshot film (rejected 2026-10-23); v2, the crew
film «Cannot Reproduce → Proof Attached» (accepted the same day); then the
9:16 and Arabic cuts (2026-10-23) and the 2026-11-10 rebuild of the lost
source. Each row says which stage of this skill prevents the problem.

| # | What happened | Cost | Fixed in |
|---|---|---|---|
| 1 | v1 read a feature list over screenshots; the owner called it "unacceptable" | a whole film | Stage 1–2: story arc + drawn metaphors; screenshots banned |
| 2 | v1's end-card byline sat off-centre under the logo | a rejection note | `data-axis` + `frame_probe.mjs` 1 px gate |
| 3 | After the render: a stray mark inside the logo at 0:28, the logo boxed at the end, the CTA read "ree" not "free" | a fix round after the owner watched | Stage 2 devil pass + stage 5 sheets with review §B7–B8 |
| 4 | Line 1 came out off-pace and had to be voiced again (against the one-take rule) | a voice call + remix + render | Stage 2 `mm.py fit` before any voice |
| 5 | 9:16 and Arabic were ordered after the master shipped | a third production round; the Arabic version differed from the English for weeks (states at 17, 19, 25, 27 s; caption timing) | Stage 0 deliverables matrix; one composition for every aspect and language |
| 6 | The film's working folder was git-ignored and later deleted; the HyperFrames source was lost and rebuilt by eye in November (SSIM 0.957) | a day of crew work | The project lives in the repo; the source is committed at stage 7 |
| 7 | The shipped English captions rendered in a fallback face (looked like IBM Plex) while the CSS said Thmanyah | a house-rule breach nobody saw | `frame_probe.mjs` reads Chrome's real platform fonts |
| 8 | Global SSIM 0.957 hid real differences (pills 30 % smaller, no dim state, stamp 0.5 s late) | a false "matches" | Foreground-weighted SSIM + pair sheets for any match-the-reference work |
| 9 | Split captions ghosted over each other at 15.5 s and 31.5 s | visible fault in the shipped film | Review §B3, the swap-frame check |
| 10 | The poster or banner was an afterthought (the video showed nothing before it played) | an extra round | Stage 7: a designed poster frame per deliverable |
| 11 | The Arabic voice gate refused the Latin brand name in the TTS text | a wall mid-voicing | Brand names are Latin in every language from the brief; the gate allows `latin_brands` |
| 12 | Takes came out slow for the registered styles; the tempo cap had to be raised mid-run | rulings mid-production | Pace band + tempo cap 1.7 in BRIEF; deterministic fitting order in the sound brief |
| 13 | The strongest beat ("ASKED FOR SINCE 2008") came from a sourced public ticket; risky lines ("one press installs it", "always recording") were caught by marketing | quality, kept | Stage 1 `claims.md`, a source per claim |
| 14 | The accepted film's rule of one continuous stage with no cuts (0 scene cuts measured) gave it its "alive" feel | quality, kept | `craft.md` §1 |
