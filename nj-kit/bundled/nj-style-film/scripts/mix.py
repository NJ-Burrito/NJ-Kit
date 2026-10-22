"""Voice + music bed + SFX -> one track the film plays.

    PYTHONUTF8=1 python mix.py <index.html> [<index.html> ...]

Reads narration.wav beside this file. bed.wav is resolved beside this file OR
in the first page's assets/ folder (devil #8: it used to have to sit only
beside this script, undocumented outside this line); `--bed <path>` overrides
both. Also reads the SFX cues from the
composition itself: every `sfx(12.3, "swish")` or `sfx(12.3, "tick", -4)` call
in index.html is one sound at that second (gain in dB, default 0). The call is
a no-op in the page; it sits next to the tween it belongs to, so the sound and
the motion cannot drift apart. Writes mix.wav, and assets/mix.m4a beside every
index.html named.

Levels (bg-music rule): voice -16 LUFS, bed -24 LUFS and ducked a further
~8 dB under speech, whole mix -14 LUFS, true peak -1 dB. SFX are loudness-
matched per category (bg-music/reference/sfx-practice.md), ducked under the
voice with a fast attack/short release, and carry a shared short room
reverb -- fixed per the devil-sfx pass (artifacts/ops/devil-sfx-2026-09-21.md);
the original patch (artifacts/production/sfx-style-film-patch-2026-09-21.md)
had three fatal defects (wrong-sign gain, an unparseable filter graph, ids
that did not resolve) -- see artifacts/production/sfx-fix-2026-09-21.md.

`sfx(t, name)` still accepts the six old synthetic names (mapped below to a
category, at SFX_TRIM_DB, unchanged) so films that predate the bg-music seed
still mix. A name that resolves in the bg-music manifest instead picks its
file and category from there.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

import numpy as np
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
SFX_DIR = os.environ.get("SFX_DIR", os.path.expanduser("~/.claude/skills/nj-style-film/assets/sfx"))
SEED_DIR = os.environ.get(
    "SFX_SEED_DIR",
    os.path.join(os.environ.get("NJ_PLUGIN_ROOT", os.path.join(os.path.expanduser("~"), "Desktop", "nj-plugin")), "skills", "bg-music", "assets", "sfx-seed"),
)
SEED_MANIFEST = os.path.join(SEED_DIR, "manifest.json")
SR = 48000

# Old six-name -> category map (backward compatibility only; these files
# stay flat-trimmed at their historical level, not category-matched).
SFX_TRIM_DB = -5.0
LEGACY_CATEGORY = {
    "logo": "stinger", "reveal": "riser", "sting": "stinger",
    "success": "stinger", "swish": "whoosh", "tick": "tick",
}

# Per-category target, RMS dBFS (bg-music/reference/sfx-practice.md). This
# is the target a manifest file was already prepped TO (sfx_prep.py); the
# per-cue gain below is therefore RELATIVE (target - the file's own
# measured level), never this table applied a second time as an absolute
# trim -- that was devil-sfx obj.1, an ~18dB-too-quiet bug.
SFX_CATEGORY_DB = {
    "impact": -18.0, "whoosh": -20.0, "tick": -26.0, "paper": -22.0,
    "riser": -24.0, "ambience": -30.0, "stinger": -16.0,
}
SFX_DUCK_DB = -3.5   # under voice, shallower/faster than the bed's ~8 dB


def load_seed_manifest():
    """rehearsal-0921: this used to read ONLY the pre-cutover bg-music seed
    manifest and return {} (silently, no error) once library-cutover-0921
    moved SFX into %NJ_LIBRARY%/INDEX.json -- any real library id
    (`SFX-000004`, resolved by `library.py find`) then fell through to
    `elif name in LEGACY_CATEGORY` and crashed with 'not in bg-music
    manifest and not a legacy name', on the very first real film to use a
    library.py SFX id instead of a legacy synthetic name. Merge in
    %NJ_LIBRARY%/INDEX.json's kind==sfx rows, reshaped to the same
    id/category/lufs_out/path shape `load()` and `cue_gain_db()` expect;
    each row is tagged `_base` so `load()` knows which root its `path` is
    relative to."""
    out = {}
    if os.path.exists(SEED_MANIFEST):
        with open(SEED_MANIFEST, encoding="utf-8") as f:
            rows = json.load(f)
        for r in rows:
            r["_base"] = SEED_DIR
            out[r["id"]] = r
    nj_library = os.environ.get("NJ_LIBRARY", os.path.join(os.path.expanduser("~"), "Desktop", "ENSERA", "library"))
    index_path = os.path.join(nj_library, "INDEX.json")
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as f:
            recs = json.load(f)
        for r in recs:
            if r.get("kind") != "sfx":
                continue
            row = {"id": r["id"], "category": r.get("category"),
                   "lufs_out": (r.get("measured") or {}).get("lufs_out"),
                   "path": r.get("path"), "_base": nj_library}
            out.setdefault(row["id"], row)
            for alias in r.get("aliases", []) or []:
                out.setdefault(alias, row)
    return out


def cues(html, manifest):
    body = open(html, encoding="utf-8").read()
    found = re.findall(r'\bsfx\(\s*([\d.]+)\s*,\s*"(\w[\w-]*)"(?:\s*,\s*(-?[\d.]+))?\s*\)', body)
    out = []
    for t, name, db in found:
        row = manifest.get(name)
        if row is not None:
            out.append((float(t), name, row["category"], float(db or 0), row))
        elif name in LEGACY_CATEGORY:
            out.append((float(t), name, LEGACY_CATEGORY[name], float(db or 0), None))
        else:
            raise SystemExit("sfx id %r not in bg-music manifest and not a legacy name" % name)
    return sorted(out)


def load(name, row):
    """row is None for a legacy six-name file (was nj-style-film/assets/sfx,
    now %NJ_LIBRARY%/sfx/), or a library row resolved via
    `library.py find --alias <old-id>` against %NJ_LIBRARY%/INDEX.json."""
    if row is None:
        path = os.path.join(SFX_DIR, name + ".wav")
    else:
        path = os.path.join(row.get("_base", SEED_DIR), row["path"])
    sr, x = wavfile.read(path)
    x = x.astype(np.float64) / (32768.0 if x.dtype == np.int16 else 1.0)
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    if sr != SR:
        raise SystemExit("%s is %d Hz, expected %d" % (name, sr, SR))
    return x


def cue_gain_db(name, t, category, cue_db, row):
    """Deterministic per-cue gain: category target minus this file's own
    measured level (relative -- devil-sfx obj.1), plus the cue's own db
    argument, plus a deterministic +-1.5dB jitter seeded from (id, time) so
    re-renders are bit-identical (brief decision 2: no `random` module, no
    dict-order dependence)."""
    seed = int(hashlib.sha256(("%s%.3f" % (name, t)).encode()).hexdigest(), 16)
    gain_jitter = ((seed % 300) / 100.0 - 1.5)
    if row is None:
        return cue_db + SFX_TRIM_DB + gain_jitter
    target_db = SFX_CATEGORY_DB.get(category, -22.0)
    measured_db = row.get("lufs_out", target_db)
    return cue_db + (target_db - measured_db) + gain_jitter


def build_sfx_track(events, dur):
    """events: sorted list of (t, name, category, cue_db, row). Pure
    function of its inputs (no wall-clock, no random) so two calls with the
    same events produce byte-identical output -- brief decision 2's
    determinism proof."""
    track = np.zeros((int((dur + 1) * SR), 2))
    cache = {}
    for t, name, category, cue_db, row in events:
        key = name if row is None else (name, row["path"])
        x = cache.setdefault(key, load(name, row))
        a = int(t * SR)
        n = min(len(x), len(track) - a)
        if n > 0:
            gain_db = cue_gain_db(name, t, category, cue_db, row)
            track[a:a + n] += x[:n] * 10 ** (gain_db / 20)
    return track


def find_bed(pages, explicit):
    """Devil #8: 'beside this file' was read only by someone already
    debugging. Resolve bed.wav here or in the first page's assets/, or take
    --bed <path>; fail with the two places actually checked."""
    if explicit:
        if not os.path.exists(explicit):
            raise SystemExit("--bed %s does not exist" % explicit)
        return explicit
    here_bed = os.path.join(HERE, "bed.wav")
    if os.path.exists(here_bed):
        return here_bed
    if pages:
        page_bed = os.path.join(os.path.dirname(os.path.abspath(pages[0])), "assets", "bed.wav")
        if os.path.exists(page_bed):
            return page_bed
    raise SystemExit("bed.wav not found beside mix.py (%s) or in %s/assets/ -- pass --bed <path>"
                      % (HERE, os.path.dirname(os.path.abspath(pages[0])) if pages else "<page>"))


def main():
    args = sys.argv[1:]
    bed_path = None
    if "--bed" in args:
        i = args.index("--bed")
        bed_path = args[i + 1]
        args = args[:i] + args[i + 2:]
    pages = args
    if not pages:
        raise SystemExit(__doc__)
    bed_path = find_bed(pages, bed_path)
    manifest = load_seed_manifest()
    events = cues(pages[0], manifest)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "csv=p=0", os.path.join(HERE, "narration.wav")]).decode())
    track = build_sfx_track(events, dur)
    wavfile.write(os.path.join(HERE, "sfx.wav"), SR, (np.clip(track, -1, 1) * 32767).astype(np.int16))
    print("sfx   %d cues: %s" % (len(events), ", ".join(
        "%s x%d" % (n, sum(1 for e in events if e[1] == n)) for n in sorted({e[1] for e in events}))))

    # asplit=3 gives the voice bus three independent copies: [v] into the
    # final mix, [key]/[key2] as separate sidechain keys for the bed duck and
    # the SFX duck respectively -- an ffmpeg label may only be read once, so
    # the two ducks each need their own key (devil-sfx obj.2: the original
    # patch tried to read [key] twice and re-split downstream, which does
    # not parse -- "Cannot find a matching stream").
    graph = (
        "[0:a]aresample=48000,loudnorm=I=-16:TP=-2:LRA=7,aformat=channel_layouts=stereo,"
        "asplit=3[v][key][key2];"
        "[1:a]loudnorm=I=-24:TP=-3:LRA=9[b0];"
        "[b0][key]sidechaincompress=threshold=0.02:ratio=5:attack=20:release=420:makeup=1[b];"
        "[2:a][key2]sidechaincompress=threshold=0.02:ratio=3:attack=5:release=150:makeup=1[sfx_duck];"
        "[sfx_duck]aecho=0.6:0.4:60:0.25[sfx_wet];"
        "[v][b][sfx_wet]amix=inputs=3:normalize=0:duration=first,"
        "alimiter=limit=0.89,loudnorm=I=-14:TP=-1:LRA=9[m]"
    )
    out = os.path.join(HERE, "mix.wav")
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(HERE, "narration.wav"),
                           "-i", bed_path, "-i", os.path.join(HERE, "sfx.wav"),
                           "-filter_complex", graph, "-map", "[m]", "-ar", "48000", out])
    for page in pages:
        dst = os.path.join(os.path.dirname(os.path.abspath(page)), "assets", "mix.m4a")
        subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", out, "-c:a", "aac", "-b:a", "256k", dst])
        print("mix  ->", dst)


if __name__ == "__main__":
    main()
