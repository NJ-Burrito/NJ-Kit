#!/usr/bin/env python
"""sfx_prep.py -- trim, fade, loudness-match one SFX file to its category
target, write the result plus one manifest row. stdlib + ffmpeg only.

Usage:
  python sfx_prep.py --in RAW.wav --category impact --id impact-crush-01 \
      --tags "paper,crush" --source-url URL --licence CC0 \
      --licence-url URL --attribution "" --commercial-ok true \
      --out-dir DIR --manifest DIR/manifest.json

Refuses (exit 1) a file with a blank licence, licence_url, source_url or
retrieved date -- provenance is not optional.

  python sfx_prep.py --selftest
"""
import argparse, hashlib, json, os, re, subprocess, sys, tempfile, shutil
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
PRACTICE = os.path.join(HERE, "..", "reference", "sfx-practice.md")

# Category -> target level, in dBFS RMS, NOT integrated LUFS. Most one-shot
# SFX are shorter than the EBU R128 400ms gating block, so `loudnorm`/ebur128
# report a meaningless -70 LUFS floor on them (measured below, selftest and
# real seed both hit this) -- see reference/sfx-practice.md Finding 2 for the
# citation trail. RMS-dBFS is the metric that stays valid at any duration.
# House defaults unless noted in sfx-practice.md.
CATEGORY_TARGETS = {
    "impact": -18.0,
    "whoosh": -20.0,
    "tick": -26.0,
    "paper": -22.0,
    "riser": -24.0,
    "ambience": -30.0,
    "stinger": -16.0,
}

REQUIRED = ["source_url", "licence", "licence_url", "retrieved"]


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def ffprobe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def measure_rms_peak(path):
    """RMS mean volume + true peak via volumedetect. Valid at any duration,
    unlike ebur128 integrated loudness (needs >=400ms to gate at all)."""
    proc = subprocess.run(
        ["ffmpeg", "-i", path, "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    err = proc.stderr
    mean = re.findall(r"mean_volume:\s*(-?[\d.]+|-inf)\s*dB", err)
    peak = re.findall(r"max_volume:\s*(-?[\d.]+|-inf)\s*dB", err)
    rms = float(mean[-1]) if mean and mean[-1] != "-inf" else -90.0
    pk = float(peak[-1]) if peak and peak[-1] != "-inf" else -90.0
    return rms, pk


def prep(in_path, out_path, category):
    """Trim leading silence, apply short fades, RMS-match to the category
    target with a peak safety limiter. Returns (rms_in, rms_out, peak_out)."""
    target = CATEGORY_TARGETS.get(category)
    if target is None:
        raise ValueError("unknown category: %s (add it to CATEGORY_TARGETS "
                          "and reference/sfx-practice.md together)" % category)
    rms_in, _ = measure_rms_peak(in_path)
    dur = ffprobe_duration(in_path)
    fade_out_start = max(0.0, dur - 0.02)
    # Pass 1: trim + fade guard, no gain yet, to measure the RMS we're
    # actually going to scale from (post-trim, so leading silence doesn't
    # skew the reading).
    trim_af = (
        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.01,"
        "afade=t=in:d=0.005,"
        "afade=t=out:st=%.3f:d=0.02"
    ) % fade_out_start
    tmp_trim = out_path + ".trim.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", in_path, "-af", trim_af, "-ar", "48000", tmp_trim],
        capture_output=True, text=True, check=True,
    )
    # Soft-knee compression before the gain match (devil-sfx obj.5): raw
    # source files vary in crest factor, so a flat RMS match alone still
    # leaves >2dB category spread on percussive material. A gentle 2:1
    # soft-knee squeezes the loud outliers toward the mean RMS before the
    # match, which is what actually holds the spread down. The gain is
    # measured AFTER compression, not before -- compressing then scaling
    # from the pre-compression level under-hits the target by exactly the
    # compressor's own gain reduction (measured this run, ~2-9dB, category-
    # dependent on how much material sits above the threshold).
    tmp_comp = out_path + ".comp.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", tmp_trim, "-af",
         "acompressor=threshold=-24dB:ratio=2:attack=5:release=80:knee=6dB",
         "-ar", "48000", tmp_comp],
        capture_output=True, text=True, check=True,
    )
    rms_compressed, _ = measure_rms_peak(tmp_comp)
    gain_db = target - rms_compressed
    # alimiter as a peak safety net at -1 dBTP; it only engages if the gain
    # would otherwise clip, so it doesn't colour material that's already safe.
    subprocess.run(
        ["ffmpeg", "-y", "-i", tmp_comp, "-af",
         "volume=%.2fdB,alimiter=limit=0.891:attack=1:release=50" % gain_db,
         "-ar", "48000", out_path],
        capture_output=True, text=True, check=True,
    )
    os.remove(tmp_trim)
    os.remove(tmp_comp)
    rms_out, peak_out = measure_rms_peak(out_path)
    return rms_in, rms_out, peak_out


def load_manifest(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_manifest(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def add_one(args):
    missing = [k for k in REQUIRED if not getattr(args, k.replace("-", "_"))]
    if missing:
        print("REFUSED: blank required field(s): %s" % ", ".join(missing))
        return 1
    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, "%s.wav" % args.id)
    lufs_in, lufs_out, peak_out = prep(args.in_, out_path, args.category)
    row = {
        "id": args.id,
        "path": os.path.relpath(out_path, os.path.dirname(args.manifest)).replace("\\", "/"),
        "sha256": sha256_of(out_path),
        "category": args.category,
        "tags": [t.strip() for t in args.tags.split(",") if t.strip()],
        "source_url": args.source_url,
        "licence": args.licence,
        "licence_url": args.licence_url,
        "attribution_text": args.attribution or "",
        "commercial_ok": args.commercial_ok.lower() == "true",
        "retrieved": args.retrieved,
        "lufs_in": round(lufs_in, 1),
        "lufs_out": round(lufs_out, 1),
        "peak_out": round(peak_out, 1),
    }
    rows = load_manifest(args.manifest)
    rows = [r for r in rows if r["id"] != args.id] + [row]
    save_manifest(args.manifest, rows)
    print("OK %s -> %s  I:%.1f->%.1f LUFS peak:%.1f" %
          (args.id, row["path"], lufs_in, lufs_out, peak_out))
    return 0


def selftest():
    tmp = tempfile.mkdtemp(prefix="sfxprep_")
    try:
        raw = os.path.join(tmp, "raw.wav")
        # 0.3s tone with 0.2s leading silence, at a known peak level
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi",
             "-i", "anullsrc=r=48000:cl=mono:d=0.2",
             "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=0.3",
             "-filter_complex", "[0][1]concat=n=2:v=0:a=1,volume=-3dB",
             raw],
            capture_output=True, check=True,
        )
        out = os.path.join(tmp, "out.wav")
        lufs_in, lufs_out, peak_out = prep(raw, out, "impact")
        assert os.path.exists(out), "prep produced no output file"
        assert abs(lufs_out - CATEGORY_TARGETS["impact"]) <= 1.0, \
            "loudness-match missed target: got %.1f want %.1f" % (lufs_out, CATEGORY_TARGETS["impact"])
        assert peak_out <= -1.9, "true-peak guard failed: %.1f" % peak_out
        dur_out = ffprobe_duration(out)
        assert dur_out < 0.45, "leading silence not trimmed: %.3fs" % dur_out

        # manifest round-trip + refusal path
        manifest = os.path.join(tmp, "manifest.json")

        class A: pass
        a = A()
        a.in_ = raw; a.category = "impact"; a.id = "selftest-1"
        a.tags = "test"; a.source_url = "https://example.test"
        a.licence = "CC0"; a.licence_url = "https://example.test/licence"
        a.attribution = ""; a.commercial_ok = "true"
        a.retrieved = str(date.today()); a.out_dir = tmp; a.manifest = manifest
        rc = add_one(a)
        assert rc == 0, "valid add_one refused"
        rows = load_manifest(manifest)
        assert len(rows) == 1 and rows[0]["id"] == "selftest-1", "manifest row missing"
        assert rows[0]["sha256"] and rows[0]["licence_url"], "provenance fields empty"

        a2 = A()
        for k, v in vars(a).items():
            setattr(a2, k, v)
        a2.id = "selftest-2"
        a2.licence = ""  # blank licence must be refused
        rc2 = add_one(a2)
        assert rc2 == 1, "blank licence was NOT refused"
        rows2 = load_manifest(manifest)
        assert len(rows2) == 1, "refused row leaked into manifest"

        print("SELFTEST OK: prep, loudness-match, manifest round-trip, blank-licence refusal all pass")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--in", dest="in_")
    ap.add_argument("--category")
    ap.add_argument("--id")
    ap.add_argument("--tags", default="")
    ap.add_argument("--source-url", dest="source_url", default="")
    ap.add_argument("--licence", default="")
    ap.add_argument("--licence-url", dest="licence_url", default="")
    ap.add_argument("--attribution", default="")
    ap.add_argument("--commercial-ok", dest="commercial_ok", default="false")
    ap.add_argument("--retrieved", default="")
    ap.add_argument("--out-dir", dest="out_dir")
    ap.add_argument("--manifest")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    for req in ("in_", "category", "id", "out_dir", "manifest"):
        if getattr(args, req) is None:
            ap.error("--%s is required" % req.replace("_", "-"))
    sys.exit(add_one(args))


if __name__ == "__main__":
    main()
