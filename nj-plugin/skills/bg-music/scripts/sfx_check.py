#!/usr/bin/env python
"""sfx_check.py -- gate a cue list against reference/sfx-practice.md rules.

Cue list JSON: [{"t": 12.30, "id": "impact-crush-01", "category": "impact"}, ...]
Manifest JSON: as written by sfx_prep.py (list of rows with id/category/lufs_out).
Optional word-times JSON: [{"start": 12.1, "end": 12.5}, ...] speech windows
a cue may not land inside (the voice-protection check).

Exit 0: clean. Exit 1: at least one rule broken, printed one per line.

  python sfx_check.py --cues cues.json --manifest manifest.json [--words words.json]
  python sfx_check.py --selftest
"""
import argparse, json, sys, tempfile, os, shutil

NJ_LIBRARY_DEFAULT = os.path.join(os.path.expanduser("~"), "Desktop", "ENSERA", "library")


def load_manifest_from_library(library_root=None):
    """Cutover 2026-09-21: the SFX manifest now lives in library\\INDEX.json
    (kind=='sfx'), not a hand-built rows file. Build the same shape
    check() already reads (id/category/lufs_out/duration_s/tags), one row
    per canonical id AND one row per alias so either resolves."""
    root = library_root or os.environ.get("NJ_LIBRARY", NJ_LIBRARY_DEFAULT)
    idx_path = os.path.join(root, "INDEX.json")
    with open(idx_path, encoding="utf-8") as f:
        idx = json.load(f)
    rows = []
    for r in idx:
        if r.get("kind") != "sfx":
            continue
        row = {"id": r["id"], "category": r.get("category"), "tags": r.get("tags") or []}
        m = r.get("measured") or {}
        if "lufs_out" in m:
            row["lufs_out"] = m["lufs_out"]
        if "duration_s" in r:
            row["duration_s"] = r["duration_s"]
        rows.append(row)
        for alias in r.get("aliases") or []:
            arow = dict(row)
            arow["id"] = alias
            rows.append(arow)
    return rows

# House defaults; keep in lockstep with reference/sfx-practice.md.
MAX_CUES_PER_SECOND = 2          # density ceiling before a run of cues reads as noise
MAX_CUES_PER_10S = 6             # countable budget (devil-sfx obj.8): replaces "usually/
                                  # sometimes" -- a normal film (30 cuts/min = 0.5/s) stays
                                  # under MAX_CUES_PER_SECOND but this is the number that
                                  # actually bites a dense scene
MAX_CUES_PER_BEAT = 1            # at most one SFX per PROJECT.md beat, unless the beat IS
                                  # the scene/story-turn boundary (always-rule, exempt below)
MIN_REPEAT_GAP_S = 8.0           # same sample id may not repeat inside this window
CATEGORY_CEILING_DBFS = {        # RMS dBFS ceiling per category (sfx_prep targets + 2dB headroom)
    "impact": -16.0, "whoosh": -18.0, "tick": -24.0,
    "paper": -20.0, "riser": -22.0, "ambience": -28.0, "stinger": -14.0,
}
CATEGORY_FLOOR_DBFS = {          # RMS dBFS floor per category (sfx_prep targets - 6dB headroom,
    "impact": -24.0, "whoosh": -26.0, "tick": -32.0,   # devil-sfx obj.4: undershoot was the
    "paper": -28.0, "riser": -30.0, "ambience": -36.0, "stinger": -22.0,  # real, uncaught fault.
}                                 # Widened a further 3dB, 2026-09-21 (devil #reel2): a peak
                                  # limiter undershoots a short transient in near-silence, and
                                  # the manifest carries no per-file duration field yet to gate
                                  # this on "<400ms" only -- LEFT for the library-move worker to
                                  # add duration_s so the exemption can be scoped to short files
                                  # instead of loosened for every category (sfx-practice.md).
SHORT_FLOOR_MARGIN_DB = 3.0       # cutover 2026-09-21: the 3dB widening above is now SCOPED to
                                  # sounds under SHORT_SOUND_MAX_S using the manifest row's
                                  # duration_s; a row at/above that length, or with no
                                  # duration_s on file, gets the tighter pre-widening floor
                                  # (CATEGORY_FLOOR_DBFS + this margin).
SHORT_SOUND_MAX_S = 0.4
VOICE_GUARD_S = 0.08             # a cue may not start inside a speech window
                                  # unless it is >= this far from either window edge


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check(cues, manifest_rows, words=None, beats=None, allow_unaudited=False):
    problems = []
    by_id = {r["id"]: r for r in manifest_rows}
    cues = sorted(cues, key=lambda c: c["t"])

    # 0. devil #9 (REGRESSED): the unaudited-tag guard was specced after reel 1
    # and never built -- paper-stationery-01 (unidentified-tool) shipped for
    # the second reel running. A cue whose manifest row carries the
    # unidentified-tool tag, or any tag containing "unaudited", fails unless
    # --allow-unaudited is passed -- the flag is the record that a human chose
    # it, not the check disappearing.
    if not allow_unaudited:
        for c in cues:
            row = by_id.get(c["id"])
            if row is None:
                continue
            tags = row.get("tags") or []
            if isinstance(tags, str):
                tags = [tags]
            if "unidentified-tool" in tags or any("unaudited" in str(t).lower() for t in tags):
                problems.append("UNAUDITED t=%.2f: '%s' carries an unaudited/unidentified-tool tag "
                                 "-- pass --allow-unaudited to ship it anyway" % (c["t"], c["id"]))

    # 1. density: no more than MAX_CUES_PER_SECOND in any rolling 1s window,
    # and no more than MAX_CUES_PER_10S in any rolling 10s window (devil-sfx
    # obj.8 -- the 1s cap alone never fires on a normal-paced film; the 10s
    # budget is the countable rule that actually bites).
    times = [c["t"] for c in cues]
    for t in times:
        count = sum(1 for tt in times if t <= tt < t + 1.0)
        if count > MAX_CUES_PER_SECOND:
            problems.append("DENSITY t=%.2f: %d cues within 1s (max %d)" %
                             (t, count, MAX_CUES_PER_SECOND))
            break  # one report per contiguous violation is enough
    for t in times:
        count = sum(1 for tt in times if t <= tt < t + 10.0)
        if count > MAX_CUES_PER_10S:
            problems.append("DENSITY_10S t=%.2f: %d cues within 10s (max %d)" %
                             (t, count, MAX_CUES_PER_10S))
            break

    # 1b. per-beat budget: at most MAX_CUES_PER_BEAT cues inside one beat
    # window, unless the beat is itself a scene/story-turn boundary (the
    # "always" rule in sfx-practice.md is exempt from its own cap).
    if beats:
        for b in beats:
            in_beat = [c for c in cues if b["start"] <= c["t"] < b["end"]]
            if not b.get("boundary") and len(in_beat) > MAX_CUES_PER_BEAT:
                problems.append("BEAT_BUDGET beat=%.2f-%.2f: %d cues (max %d)" %
                                 (b["start"], b["end"], len(in_beat), MAX_CUES_PER_BEAT))

    # 2. same-sample repeat gap
    last_seen = {}
    for c in cues:
        cid = c["id"]
        if cid in last_seen and c["t"] - last_seen[cid] < MIN_REPEAT_GAP_S:
            problems.append("REPEAT t=%.2f: '%s' repeats after %.2fs (min %.1fs)" %
                             (c["t"], cid, c["t"] - last_seen[cid], MIN_REPEAT_GAP_S))
        last_seen[cid] = c["t"]

    # 3. category level ceiling + floor (needs manifest lufs_out per row).
    # devil-sfx obj.4: category comes from the MANIFEST ROW ONLY, never the
    # cue -- a cue used to be able to declare any category and inherit that
    # category's (looser) ceiling regardless of what the file actually is.
    for c in cues:
        row = by_id.get(c["id"])
        if row is None:
            problems.append("UNKNOWN t=%.2f: cue id '%s' not in manifest" % (c["t"], c["id"]))
            continue
        cat = row.get("category")
        ceiling = CATEGORY_CEILING_DBFS.get(cat)
        floor = CATEGORY_FLOOR_DBFS.get(cat)
        duration_s = row.get("duration_s")
        if floor is not None and not (duration_s is not None and duration_s < SHORT_SOUND_MAX_S):
            floor = floor + SHORT_FLOOR_MARGIN_DB  # not a short sound (or unknown) -> tighter floor
        level = row.get("lufs_out")
        if ceiling is not None and level is not None and level > ceiling:
            problems.append("LEVEL t=%.2f: '%s' at %.1f dBFS exceeds %s ceiling %.1f" %
                             (c["t"], c["id"], level, cat, ceiling))
        if floor is not None and level is not None and level < floor:
            problems.append("LEVEL_LOW t=%.2f: '%s' at %.1f dBFS under %s floor %.1f" %
                             (c["t"], c["id"], level, cat, floor))

    # 4. protected voice window -- guard widens the window equally on both
    # edges (devil-sfx obj.1: the old test narrowed the END edge instead).
    if words:
        for c in cues:
            for w in words:
                if w["start"] - VOICE_GUARD_S < c["t"] < w["end"] + VOICE_GUARD_S:
                    problems.append("VOICE_WINDOW t=%.2f: '%s' lands inside speech %.2f-%.2f" %
                                     (c["t"], c["id"], w["start"], w["end"]))
                    break

    return problems


def warn_boundary_punctuation(cues, scene_starts):
    """Devil #10: the per-beat budget bound (right rule, wrong number) but
    nothing caught every cue landing on a cut instead of an action inside the
    scene -- sfx-practice.md's fix (item 3, 'which actions get a sound').
    Warning, not a NO-GO: some short scenes legitimately cut-punctuate only."""
    if not cues or not scene_starts:
        return None
    near = sum(1 for c in cues if any(abs(c["t"] - s) <= 0.1 for s in scene_starts))
    pct = 100.0 * near / len(cues)
    if pct > 60.0:
        return ("WARN   %.0f%% of cues fall within 0.1s of a scene boundary -- sound design is "
                 "reading as scene-change punctuation, not actions inside the scene "
                 "(sfx-practice.md 'which actions get a sound')" % pct)
    return None


def selftest():
    manifest = [
        {"id": "a", "category": "impact", "lufs_out": -18.0},
        {"id": "b", "category": "tick", "lufs_out": -26.0},
        {"id": "c", "category": "impact", "lufs_out": -10.0},  # over ceiling
        {"id": "d", "category": "impact", "lufs_out": -30.0},  # under floor (too quiet)
        {"id": "e", "category": "paper", "lufs_out": -22.0},   # prepped, on target -- must pass
    ]
    # negative control 1: clean cue list must pass
    clean = [{"t": 0.0, "id": "a", "category": "impact"},
             {"t": 2.0, "id": "b", "category": "tick"}]
    assert check(clean, manifest) == [], "clean list flagged: %r" % check(clean, manifest)

    # negative control 2: density
    dense = [{"t": 0.0, "id": "a"}, {"t": 0.2, "id": "b"}, {"t": 0.4, "id": "a"}]
    p = check(dense, manifest)
    assert any("DENSITY" in x for x in p), "density violation missed"

    # negative control 3: repeat gap
    repeat = [{"t": 0.0, "id": "a"}, {"t": 1.0, "id": "a"}]
    p = check(repeat, manifest)
    assert any("REPEAT" in x for x in p), "repeat violation missed"

    # negative control 4: category ceiling
    loud = [{"t": 0.0, "id": "c"}]
    p = check(loud, manifest)
    assert any("LEVEL" in x for x in p), "level ceiling violation missed"

    # negative control 4b: too-quiet fails the floor (devil-sfx obj.4 --
    # this is the fault that used to be uncatchable)
    quiet = [{"t": 0.0, "id": "d"}]
    p = check(quiet, manifest)
    assert any("LEVEL_LOW" in x for x in p), "level floor (too-quiet) violation missed"

    # negative control 4d: cutover 2026-09-21 -- the 3dB floor widening is scoped to
    # sounds under SHORT_SOUND_MAX_S. A short (duration_s<0.4) transient in the
    # widened-but-not-tightened band must PASS; a long sound at the same level, or one
    # with no duration_s on file, must FAIL the tighter floor.
    manifest_dur = manifest + [
        {"id": "f", "category": "impact", "lufs_out": -23.0, "duration_s": 0.12},  # short transient
        {"id": "g", "category": "impact", "lufs_out": -23.0, "duration_s": 1.5},   # sustained, same level
        {"id": "h", "category": "impact", "lufs_out": -23.0},                      # no duration_s on file
    ]
    short_ok = [{"t": 0.0, "id": "f"}]
    assert check(short_ok, manifest_dur) == [], "short transient under the widened floor wrongly flagged"
    long_bad = [{"t": 0.0, "id": "g"}]
    p = check(long_bad, manifest_dur)
    assert any("LEVEL_LOW" in x for x in p), "sustained sound at the same level should fail the tighter floor"
    unknown_dur_bad = [{"t": 0.0, "id": "h"}]
    p = check(unknown_dur_bad, manifest_dur)
    assert any("LEVEL_LOW" in x for x in p), "missing duration_s should default to the tighter floor"

    # positive control: a properly prepped file on its category target passes
    prepped = [{"t": 0.0, "id": "e"}]
    assert check(prepped, manifest) == [], "prepped on-target file wrongly flagged: %r" % check(prepped, manifest)

    # negative control 4c: cue-declared category is ignored -- ceiling comes
    # from the manifest row only (devil-sfx obj.2)
    spoofed = [{"t": 0.0, "id": "c", "category": "ambience"}]  # id 'c' is really impact, -10dB
    p = check(spoofed, manifest)
    assert any("LEVEL" in x for x in p), "cue-declared category spoofed the ceiling"

    # negative control 5: voice window, both edges
    words = [{"start": 1.0, "end": 1.5}]
    inword = [{"t": 1.2, "id": "a"}]
    p = check(inword, manifest, words)
    assert any("VOICE_WINDOW" in x for x in p), "voice-window violation missed"
    near_end = [{"t": 1.55, "id": "a"}]  # 0.05s past the end, inside the widened guard
    p = check(near_end, manifest, words)
    assert any("VOICE_WINDOW" in x for x in p), "voice-window end-edge guard missed (devil-sfx obj.1)"

    # negative control 6: 10s density budget
    ten = [{"t": float(i), "id": "a"} for i in range(7)]  # 7 cues inside 10s, max 6
    p = check(ten, manifest)
    assert any("DENSITY_10S" in x for x in p), "10s density budget missed"

    # negative control 7: per-beat budget
    beats = [{"start": 0.0, "end": 5.0, "boundary": False}]
    twice = [{"t": 1.0, "id": "a"}, {"t": 2.0, "id": "b"}]
    p = check(twice, manifest, beats=beats)
    assert any("BEAT_BUDGET" in x for x in p), "per-beat budget missed"

    # negative control 8: cutover 2026-09-21 -- a cue id that exists only as
    # an alias (library.py's INDEX.json rows) must resolve like the canonical id.
    alias_manifest = manifest + [{"id": "impact-crush-01", "category": "impact", "lufs_out": -18.0}]
    alias_only = [{"t": 0.0, "id": "impact-crush-01"}]
    assert check(alias_only, alias_manifest) == [], "alias-only id failed to resolve"

    print("SELFTEST OK: clean pass + density(1s/10s)/repeat/level(ceiling+floor)/"
          "category-spoof/voice-window(both edges)/beat-budget/alias-resolve all detected")
    return 0


def credits_report(cues, manifest_rows):
    """Print the credit line for every cue whose file needs one; exit 1 on a
    blank attribution_text where the licence requires it (brief item 8)."""
    by_id = {r["id"]: r for r in manifest_rows}
    bad = []
    for c in cues:
        row = by_id.get(c["id"])
        if row is None:
            continue
        lic = (row.get("licence") or "").upper()
        text = (row.get("attribution_text") or "").strip()
        if lic and lic != "CC0" and not text:
            bad.append(c["id"])
        elif text:
            print("%s -- %s (%s)" % (c["id"], text, row.get("licence")))
    if bad:
        print("MISSING CREDIT: %s" % ", ".join(sorted(set(bad))))
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--cues")
    ap.add_argument("--manifest", help="rows file; omit to resolve ids/aliases via library\\INDEX.json (kind=sfx)")
    ap.add_argument("--words")
    ap.add_argument("--beats")
    ap.add_argument("--credits", action="store_true",
                     help="print credit lines for the cue list's files and fail on a blank "
                          "attribution_text where the licence needs one; skips the gate checks")
    ap.add_argument("--allow-unaudited", action="store_true",
                     help="ship a cue whose manifest row carries an unaudited/unidentified-tool "
                          "tag anyway (devil #9) -- the flag is the record a human chose it")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    if not args.cues:
        ap.error("--cues is required")
    manifest = load(args.manifest) if args.manifest else load_manifest_from_library()
    if args.credits:
        sys.exit(credits_report(load(args.cues), manifest))
    cues = load(args.cues)
    words = load(args.words) if args.words else None
    beats = load(args.beats) if args.beats else None
    problems = check(cues, manifest, words, beats, allow_unaudited=args.allow_unaudited)
    if problems:
        for p in problems:
            print(p)
        sys.exit(1)
    print("CLEAN: 0 rule breaks")
    sys.exit(0)


if __name__ == "__main__":
    main()
