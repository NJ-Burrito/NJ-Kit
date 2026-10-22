---
name: bg-music
description: 'Holds a bundled licence-cleared CC0 SFX library and music beds with cue presets, and sources from Openverse, Jamendo, Freesound, ccMixter, Wikimedia with licence, credit line and retrieval date per track. Triggers: get me music, background track, bed audio, موسيقى خلفية, sound effects too loud, sfx mix, bed by theme, موسيقى حسب الموضوع, مؤثرات صوتية.'
---

# bg-music

A music library you own the right to use, organised by what the video is doing.

## The licence question, answered once

This is the part that costs money when it is got wrong.

| where the music plays | what you may use |
|---|---|
| **Instagram / TikTok post, picked in-app** | the platform's own audio catalogue — commercial hits included. The licence lives with the platform and stops at the platform's edge |
| **The same video exported and re-posted elsewhere, or on a client's channel, or in an ad** | **not** that catalogue. Commercial masters need a sync licence per use |
| **A rendered deliverable — showreel, ad, explainer, website video, deck export** | free-licence music only: CC0 / Public Domain / CC-BY / CC-BY-SA, or a paid library subscription |
| **A brand or client account** | treat as commercial always, even for organic posts |

So a reel naming *"track X by famous band Y"* is telling you what to **tap in
the app**, not what to put in a file. The house rule: **anything that renders
to a file uses this library.** The script refuses NC (non-commercial) and ND
(no-derivatives) licences for exactly that reason — a client video is
commercial, and every edit is a derivative.

CC-BY and CC-BY-SA are free **and conditional**: the credit line must be
published with the video. `ATTRIBUTION.md` is generated for that; shipping
without it is an unlicensed use, legally the same as not having a licence at
all. CC0 and Public Domain need nothing.

## Run it

```bash
python ~/.claude/skills/bg-music/scripts/fetch_music.py --out %NJ_LIBRARY%/music --per-mood 6
python ... --mood deep --per-mood 10 --normalize        # top up one mood
python ... --mood arabic --search "oud taqsim" --per-mood 8
python ... --per-mood 3 --dry-run                       # see what it would take
```

| flag | default | use |
|---|---|---|
| `--out DIR` | required | the library root. One per project, or one shared |
| `--mood NAME` | all | `informational`, `challenge`, `motivational`, `deep`, `arabic`, `corporate`, `cinematic`. Repeatable |
| `--search "…"` | — | extra query, filed under the given mood |
| `--per-mood N` | 6 | how many keepers per mood |
| `--min-seconds N` | 30 | skips one-shots and stingers |
| `--normalize` | off | also writes a `-bed.wav` at `--bed-lufs` |
| `--bed-lufs N` | −23 | bed level, so music never fights a voice at the same gain |
| `--dry-run` | off | list, download nothing |

Re-running is additive and de-duplicated by source URL, so the library grows
instead of being rebuilt.

## What it produces

```
%NJ_LIBRARY%/music/         (post-cutover; was production/music-library/)
  informational/  challenge/  motivational/  deep/ …   ← audio, by mood
  library.json          ← every track: licence, creator, provider, landing page, duration, retrieved date
  ATTRIBUTION.md        ← the credit lines, split into "credit required" and "free, no credit"
```

`library.json` is the machine-readable part: a render script picks a bed by
mood and carries the licence with it, so nothing is published whose provenance
nobody can state. That is the same traceability rule the ENSERA KB uses for
claims, applied to audio.

## The four moods, and where they came from

Taken from a short-form convention (Instagram reel `viewcci`, `DdXP2FTOhfj`),
which sorts sounds by what the video is doing rather than by genre:

| mood | the video is | musical shape |
|---|---|---|
| **informational** | explaining something | steady, low-event, no vocal, nothing that pulls attention off the words |
| **challenge** | building tension to a payoff | percussive, rising, a clear point where it lands |
| **motivational** | making the viewer feel capable | major key, builds, resolves |
| **deep** | reflective, serious, emotional | slow, sparse, atmospheric |

That sorting is the useful part of any "best sounds" list. The track names in
such lists are commercial masters — reference for the *shape*, not files to
fetch. `--search` with a description of the shape ("slow emotional piano",
"driving percussion loop") is how a named track becomes a usable one.

## Rules

1. **Never file a track without its licence.** A file whose provenance is lost
   is a file that cannot be published; delete it rather than guess.
2. **Bed level is −23 LUFS, voice is −16.** Music mixed at voice level buries
   the voice no matter how good the voiceover clean-up was (`voice-clean`).
3. **Check the credit list before every publish** — `ATTRIBUTION.md`, the
   "credit required" block.
4. **Do not download platform audio.** Ripping an in-app sound out of a reel
   does not carry the in-app licence with it.
5. **Preview quality is a real limit.** Freesound results come back as 128 kbps
   previews — fine under a voice, thin as a lead track. Jamendo and Wikimedia
   results are full quality; `library.json` records the provider.

## Choosing a bed for a film

`scripts/bed_pick.py --kind <kind> --length <seconds>` ranks eligible
tracks from `library.json` by the theme->mood table in
`reference/music-beds.md` (product explainer, educational short, event
promo, recruitment, partnership/investor, achievement/announcement,
behind-the-scenes), excludes anything used in the last 5 films
(`history.json`) and any BY-SA track unless `--allow-sharealike`, and
prints the top 3 with reasons. `--path` creates/prints the `-23`-LUFS bed
file; `--commit <film id>` records the pick so the next film doesn't
repeat it. `nj-style-film`'s house finish calls this before falling back
to the generated bed (`bed.py`). Post-cutover: `library.json`/`history.json`
live under `%NJ_LIBRARY%/music/` (env `NJ_LIBRARY`), a projection `library.py
sync` regenerates from `INDEX.json` each run.

## SFX in a reel

SFX get loud, crude and out-of-place for three measured reasons: no
loudness-matching/ducking against the voice bus, one dry sample repeated with
no variation, and a sound world (synthetic UI blips) that doesn't match the
visual style. `reference/sfx-practice.md` has the numbers (per-category
level, ducking, density, timing, repeat gap) with sources or `house default`
marked; `reference/sfx-palettes.md` picks the sound world per visual style
(`paper-punch` first). `scripts/sfx_prep.py` trims/fades/RMS-matches one raw
file into `%NJ_LIBRARY%/sfx/` (post-cutover; was `assets/sfx-seed/`) + a
manifest row (refuses a blank licence). `scripts/sfx_check.py` gates a cue
list against those rules, resolving an id through `library.py find --alias`
against `%NJ_LIBRARY%/INDEX.json`.

## Related

- `voice-clean` — the voice this music sits under, and the loudness targets.
- `hyperframes-audio` — ducking, crossfades and automation once a bed is in a
  HyperFrames composition.
- `media-use` — sourcing or generating audio that does not exist yet (TTS, SFX).

## Tooling

Python stdlib + `certifi` (Windows has no CA bundle for `urllib`, so TLS fails
without it — never fall back to unverified TLS). `ffmpeg` only for
`--normalize`. **No API key, no account, no payment**: Openverse's API is open.
