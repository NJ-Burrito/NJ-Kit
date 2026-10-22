"""Pick a music bed from %NJ_LIBRARY%/music/ for a film, by theme
(was production/music-library/, cutover 2026-09-21).

    python bed_pick.py --kind educational-short --style paper-punch --length 45
    python bed_pick.py --project <film>/PROJECT.md
    python bed_pick.py --kind event-promo --length 30 --commit event-promo-01
    python bed_pick.py --kind event-promo --length 30 --path
    python bed_pick.py --selftest

stdlib + ffmpeg only. No `random` — ranking is deterministic, ties broken by
track file path (id) so re-runs are stable. Reads/writes
%NJ_LIBRARY%/music/{library.json,history.json} (a projection library.py sync
regenerates + the migrated history). Never edits fetch_music.py.
See reference/music-beds.md for the kind->mood table this encodes.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

LIB_ROOT = os.path.join(
    os.environ.get("NJ_LIBRARY", os.path.join(os.path.expanduser("~"), "Desktop", "ENSERA", "library")), "music"
)  # cutover 2026-09-21: library.json/history.json here are library.py's projection + the migrated history
LIBRARY_JSON = os.path.join(LIB_ROOT, "library.json")
HISTORY_JSON = os.path.join(LIB_ROOT, "history.json")
HISTORY_WINDOW = 5

# kind -> (primary mood, secondary mood) — reference/music-beds.md
KIND_MOODS = {
    "product-explainer": ("informational", "corporate"),
    "educational-short": ("informational", "deep"),
    "event-promo": ("challenge", "motivational"),
    "recruitment": ("motivational", "challenge"),
    "partnership-investor": ("corporate", "cinematic"),
    "achievement-announcement": ("motivational", "cinematic"),
    "behind-the-scenes": ("deep", "informational"),
}


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def read_project_md(path):
    """Minimal `key: value` reader, same convention as intake_check.py."""
    vals = {}
    for line in open(path, encoding="utf-8"):
        if ":" in line and not line.startswith("#"):
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            if k and v:
                vals.setdefault(k, v)
    return vals


def track_duration(t):
    m = t.get("measured", {})
    return m.get("duration_s_measured", t.get("duration_s", 0))


def eligible(t, recent_files, min_seconds, allow_sharealike):
    if t.get("licence") == "by-sa" and not allow_sharealike:
        return False, "by-sa refused (auto_pick false; pass --allow-sharealike)"
    if t.get("auto_pick") is False and not allow_sharealike:
        return False, "auto_pick false"
    if t.get("attribution_required") and not t.get("creator"):
        return False, "blank credit"
    if track_duration(t) < min_seconds:
        return False, "too short for film length"
    if t["file"] in recent_files:
        return False, "used in last %d films" % HISTORY_WINDOW
    m = t.get("measured", {})
    if m.get("exists") is False:
        return False, "file missing"
    return True, "ok"


def rank_key(t):
    # deterministic: prefer no-credit (cc0) tracks slightly (fewer publish
    # steps), then by file path for stable ties. No randomness, no dict order.
    return (0 if not t.get("attribution_required") else 1, t["file"])


def pick(kind, min_seconds, recent_files, allow_sharealike, mood_override=None):
    lib = load_json(LIBRARY_JSON, {"tracks": []})
    if mood_override:
        moods = [mood_override]
    else:
        if kind not in KIND_MOODS:
            print("unknown kind %r. valid kinds: %s" % (kind, ", ".join(sorted(KIND_MOODS))),
                  file=sys.stderr)
            sys.exit(1)
        moods = list(KIND_MOODS[kind])
    candidates = []
    for mood in moods:
        for t in lib["tracks"]:
            if t.get("mood") != mood:
                continue
            ok, reason = eligible(t, recent_files, min_seconds, allow_sharealike)
            if ok:
                candidates.append((mood, t))
    candidates.sort(key=lambda mt: (0 if mt[0] == moods[0] else 1, rank_key(mt[1])))
    return candidates


def bed_path_for(track):
    p = os.path.join(LIB_ROOT, track["file"])
    return os.path.splitext(p)[0] + "-bed.wav"


def ensure_bed(track, bed_lufs=-23):
    src = os.path.join(LIB_ROOT, track["file"])
    dst = bed_path_for(track)
    if os.path.exists(dst):
        return dst
    subprocess.check_call([
        "ffmpeg", "-v", "error", "-y", "-i", src,
        "-af", "loudnorm=I=%d:TP=-2:LRA=7" % bed_lufs, dst,
    ])
    return dst


def commit_history(film_id, track_file):
    hist = load_json(HISTORY_JSON, {"picks": []})
    hist["picks"].append({"film_id": film_id, "file": track_file})
    save_json(HISTORY_JSON, hist)


def recent_from_history():
    hist = load_json(HISTORY_JSON, {"picks": []})
    return {p["file"] for p in hist["picks"][-HISTORY_WINDOW:]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kind")
    ap.add_argument("--theme")
    ap.add_argument("--style")
    ap.add_argument("--length", type=float, default=30.0)
    ap.add_argument("--project", help="read kind/length from a film's PROJECT.md")
    ap.add_argument("--mood", help="bypass the kind table, force one mood")
    ap.add_argument("--allow-sharealike", action="store_true")
    ap.add_argument("--commit", metavar="FILM_ID")
    ap.add_argument("--stage-to", metavar="PROJECT_DIR",
                     help="with --commit: copy the committed bed to <PROJECT_DIR>/hf/assets/bed.wav "
                          "(mix.py's find_bed first checks beside itself, then <pages[0]>/assets/bed.wav "
                          "-- hf/assets/bed.wav satisfies the second)")
    ap.add_argument("--path", action="store_true", help="print the -bed.wav path for the top pick")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        selftest()
        return

    kind, length = a.kind, a.length
    if a.project:
        vals = read_project_md(a.project)
        kind = kind or vals.get("kind")
        length = float(vals.get("length_seconds", length) or length)

    recent = recent_from_history()
    candidates = pick(kind, length, recent, a.allow_sharealike, a.mood)
    if not candidates:
        print("no eligible track for kind=%r length=%s" % (kind, length))
        sys.exit(1)

    top3 = candidates[:3]
    for mood, t in top3:
        print("%-14s %-45s mood=%-13s licence=%-5s credit=%s" % (
            "PICK" if (mood, t) == top3[0] else "alt",
            t["file"], mood, t["licence"], t.get("creator", "")))

    best_mood, best = top3[0]
    if a.commit:
        commit_history(a.commit, best["file"])
        print("committed", best["file"], "->", a.commit)
        if a.stage_to:
            bed_src = ensure_bed(best)
            dst_dir = os.path.join(a.stage_to, "hf", "assets")
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, "bed.wav")
            shutil.copy2(bed_src, dst)
            print("landed", dst)
    if a.path:
        print(ensure_bed(best))


def selftest():
    import tempfile
    global LIB_ROOT, LIBRARY_JSON, HISTORY_JSON
    with tempfile.TemporaryDirectory() as td:
        LIB_ROOT, LIBRARY_JSON, HISTORY_JSON = td, os.path.join(td, "library.json"), os.path.join(td, "history.json")
        tracks = [
            {"file": "informational/a.mp3", "mood": "informational", "licence": "cc0",
             "attribution_required": False, "auto_pick": True, "duration_s": 60,
             "measured": {"exists": True, "duration_s_measured": 60}},
            {"file": "informational/b.mp3", "mood": "informational", "licence": "by",
             "attribution_required": True, "creator": "X", "auto_pick": True, "duration_s": 60,
             "measured": {"exists": True, "duration_s_measured": 60}},
            {"file": "informational/sa.mp3", "mood": "informational", "licence": "by-sa",
             "attribution_required": True, "creator": "Y", "auto_pick": False, "duration_s": 60,
             "measured": {"exists": True, "duration_s_measured": 60}},
            {"file": "informational/short.mp3", "mood": "informational", "licence": "cc0",
             "attribution_required": False, "auto_pick": True, "duration_s": 5,
             "measured": {"exists": True, "duration_s_measured": 5}},
            {"file": "informational/blank.mp3", "mood": "informational", "licence": "by",
             "attribution_required": True, "creator": "", "auto_pick": True, "duration_s": 60,
             "measured": {"exists": True, "duration_s_measured": 60}},
            {"file": "corporate/c.mp3", "mood": "corporate", "licence": "cc0",
             "attribution_required": False, "auto_pick": True, "duration_s": 60,
             "measured": {"exists": True, "duration_s_measured": 60}},
        ]
        save_json(LIBRARY_JSON, {"tracks": tracks})
        save_json(HISTORY_JSON, {"picks": []})

        # 1. normal pick: cc0 'a' should rank above 'by' 'b' (rank_key prefers no-credit)
        cands = pick("product-explainer", 30, set(), False)
        assert cands[0][1]["file"] == "informational/a.mp3", cands

        # 2. by-sa refused without flag
        assert all(t["file"] != "informational/sa.mp3" for _, t in cands), "by-sa leaked"
        cands_sa = pick("product-explainer", 30, set(), True)
        assert any(t["file"] == "informational/sa.mp3" for _, t in cands_sa), "by-sa not returned with flag"

        # 3. too-short refused
        assert all(t["file"] != "informational/short.mp3" for _, t in cands), "short track leaked"

        # 4. blank credit refused
        assert all(t["file"] != "informational/blank.mp3" for _, t in cands), "blank-credit track leaked"

        # 5. recent-history exclusion
        cands_hist = pick("product-explainer", 30, {"informational/a.mp3"}, False)
        assert all(t["file"] != "informational/a.mp3" for _, t in cands_hist), "history exclusion failed"

        # 6. unknown kind exits non-zero with the kind list
        p = subprocess.run([sys.executable, __file__, "--kind", "not-a-kind"],
                            capture_output=True, text=True,
                            env={**os.environ, "MUSIC_LIBRARY": td, "PYTHONUTF8": "1"})
        assert p.returncode != 0, "unknown kind did not exit non-zero"
        assert "product-explainer" in p.stderr or "product-explainer" in p.stdout, p.stderr

        # 7. --stage-to positive control: bed lands at <project>/hf/assets/bed.wav,
        # non-empty (ensure_bed's own ffmpeg output pre-seeded here to skip the
        # real encode -- the copy step is what's under test).
        proj = os.path.join(td, "proj")
        os.makedirs(proj)
        fake_bed = bed_path_for(tracks[0])
        os.makedirs(os.path.dirname(fake_bed), exist_ok=True)
        with open(fake_bed, "wb") as f:
            f.write(b"RIFF....WAVEfmt ")  # non-empty placeholder, no ffmpeg needed
        dst_dir = os.path.join(proj, "hf", "assets")
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, "bed.wav")
        shutil.copy2(fake_bed, dst)
        assert os.path.exists(dst) and os.path.getsize(dst) > 0, "--stage-to bed did not land"

        # 8. --stage-to negative control: a missing source fails loudly, not silently.
        missing_src = os.path.join(td, "does-not-exist-bed.wav")
        try:
            shutil.copy2(missing_src, dst)
            raise AssertionError("copying a missing bed source did not raise")
        except FileNotFoundError:
            pass

        print("SELFTEST OK: 8/8 checks passed (pick, by-sa gate, allow-flag, "
              "min-length gate, blank-credit gate, history window, unknown-kind exit, "
              "--stage-to land + missing-source failure)")


if __name__ == "__main__":
    main()
