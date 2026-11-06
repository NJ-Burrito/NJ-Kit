# Reference preparation: registers, length, transcripts, quality, children

Companion to `voice-engineering.md` section 2 (the cleaning steps). Research date 2026-11-07.

## 1. One reference per register, where the engine benefits

A cloning engine copies the reference's room, level, noise and bandwidth, and follows its delivery to a degree. So a
character who must sound calm, tender and angry may need a reference per register. No 2025-2026 source measures this for
Chatterbox (gap): start with ONE reference per voice and add a register only where the owner's ear says the single
reference cannot reach it. Engines that take style from text (tags, instructions) do not need it.

| Rule | Detail |
|---|---|
| Length | 5 to 8 s of clean speech per reference clip. The engine's README example is a 10 s file and states no minimum; 5 s is our own flag, not a sourced limit. Under about 5 s: flagged for the owner's ear, not dropped (the shortest clip used in the previous cast was 3.05 s and stayed the one to listen to first) |
| Count | one per register where it helps; name them `<voice>/<register>` (neutral, calm, angry, ...). Same speaker, same mic, same room across registers |
| Transcript | a text file beside each clip, `<clip>.txt`, taken from the source's own transcript or the recording script. Never from ASR |
| Registry | one folder per voice: `<voice>/<register>.wav`, `<voice>/<register>.txt`, `<voice>/provenance.json`, plus one `voices.json` listing id, register, sha256, licence, consent record id. Layout idea from a local-TTS skill's reference bank (file tree only, read 2026-11-07) with the sha256, licence and consent fields added, which that source lacks |
| Language | the reference's language and accent must match the language tag, or the output can inherit the reference accent (engine README). Check the accent from the source's own label; the owner's ear confirms |
| Settings | defaults until a take proves otherwise; record any exception and its reason in the casting record |

## 2. REF-QUALITY rules from the previous casting (16 roles, 8 speakers plus narrator, 2026-10)

1. **Clean before you judge.** Measure the edge-cleaned clip you will clone, not the clip the judge scored: room tone at the
   edges flattered floor and SNR, and 3 of 7 ear picks failed after the clean. On a fail, walk to the next passing candidate.
2. **Never loosen a gate to pass a clip.** Limits: 2 up-votes and no down-vote (community sources), no full-scale sample,
   floor at most -53 dBFS, SNR at least 35 dB, crest at least 18 dB, top band at least -58 dB, decay at most 0.15 s, zero
   samples at most 2%, floor at least -75 dBFS, centroid at least 400 Hz, hum at most 40 dB.
3. **Reject gated or denoised clips even when they pass the old numbers.** A narrator reference with 6.4% digital-zero samples,
   floor -88.4 dBFS and centroid 334 Hz passed the first gate and sounded noisy and boxy; the zero-share, floor-minimum and
   centroid checks were added. Keep a banned list keyed by clip id, file hash and speaker hash; a banned voice is banned for
   every series.
4. **A short reference is flagged, not dropped.** Give each role at least about 4.5 s of clean speech where the scout allows.
5. **Settings stay at the defaults** (0.5 / 0.5) until a take proves otherwise; any per-character exception is recorded with
   its reason.
6. **Every role gets a generation cap keyed to its reference hash**, refitted before the first take of a new reference; an
   unmeasured reference falls back to the conservative 5 letters per second.
7. **Pace is fitted from the take the owner approved**, not from the first sample.
8. **Text changes are new lines and a bad voice is banned and superseded**, never patched per episode. Keep superseded clips on
   disk; regenerate the casting table from the casting record so it is never stale.
9. **Scout early and budget a longer cast than before**: sixteen roles need about twice the references, bands and caps; each
   pick may walk the ranking.
10. **Plan the script for character lines**: the narrator covering nearly every line fails the calm-narrator check; give
    characters their own voices.

## 3. Child voices: never clone a child

An adult actor performs the child register as ordinary recorded speech (with their own consent record), or a licensed
non-cloned voice is used. Reasons found 2026-11-07: some platforms bar cloning under 18 even with a guardian's consent;
guardian consent is a weak basis (verifiable consent, a narrow written scope, a retention and reuse limit are needed, and a
checkbox is not enough for commercial use); advocacy letters of June 2026 argue parental approval should not be a blanket
licence. This is not law and was not checked against a regulator text: legal review before any commercial use.

## Sources

- Chatterbox README (reference language and accent, example reference length), fetched 2026-11-07.
- Local neural TTS skill file tree (reference bank layout), fetched via the GitHub API 2026-11-07; text read as data, not run.
- Internal record of the 2026-10 casting (limits, failures, rules) and the 2026-11-07 licensed-talent survey (child voices).
