# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy"]
# ///
"""Gated click repair with ffmpeg `adeclick`, allowed ONLY outside the guarded speech span (nj-narration).

    uv run --with numpy python voice_declick.py take.wav take.declicked.wav [--profile sound_profile.json]

adeclick rewrites samples (AR-model interpolation), so it must never touch a word. Contract:
  1. measure clicks (voice_measure.click_stats); none found -> write nothing, exit 0, say so;
  2. run ffmpeg adeclick on a copy, then take the repaired samples ONLY outside [onset - lead_guard, offset + tail_guard];
     every sample inside that span is copied back from the original, so span_samples_identical is true by construction;
  3. keep the result only if the click count fell; otherwise write nothing and report why.
It is a repair of one take, run once: not a re-voice, not a best-of-N. The input is never overwritten.
Needs ffmpeg on PATH. Output is 16-bit mono WAV like the rest of the skill.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice_edges as VE  # noqa: E402
import voice_measure as VM  # noqa: E402

ADECLICK = "adeclick=w=55:o=75:a=2:t=2:b=2:m=a"     # ffmpeg defaults, spelled out; docs: ffmpeg.org/ffmpeg-filters.html


def splice_outside(orig, repaired, a: int, b: int):
    """Repaired samples everywhere except [a, b): that range is copied back from the original."""
    n = min(len(orig), len(repaired))
    out = np.array(repaired[:n], dtype="float64")
    a, b = max(0, a), min(n, b)
    out[a:b] = np.asarray(orig[:n], dtype="float64")[a:b]
    return out


def guarded_span(x, rate, E):
    s = VE.speech_span(x, rate, E)
    a = max(0, int(round((s["onset_s"] - E["lead_guard_s"]) * rate)))
    b = min(len(x), int(round((s["offset_s"] + E["tail_guard_s"]) * rate)))
    return a, b, s


def run_adeclick(src: Path, dst: Path) -> None:
    ff = shutil.which("ffmpeg")
    if not ff:
        raise RuntimeError("ffmpeg not found on PATH")
    subprocess.run([ff, "-v", "error", "-y", "-i", str(src), "-af", ADECLICK, "-c:a", "pcm_s16le", str(dst)],
                   check=True, capture_output=True, text=True, timeout=120)


def declick(x, rate, E, repair=None):
    """-> (y or None, record). `repair(x, rate) -> y` defaults to ffmpeg adeclick (tests pass a fake)."""
    before = VM.click_stats(x, rate)
    rec = {"clicks_before": before["clicks"], "method": "nj-narration voice_declick (ffmpeg adeclick outside the guarded span)"}
    if before["clicks"] == 0:
        return None, {**rec, "result": "no clicks found: nothing written"}
    a, b, span = guarded_span(x, rate, E)
    if repair is None:
        with tempfile.TemporaryDirectory() as d:
            src, dst = Path(d) / "in.wav", Path(d) / "out.wav"
            VE.write_wav16(src, x, rate)
            run_adeclick(src, dst)
            y, r2 = VE.read_wav(dst)
    else:
        y, r2 = repair(x, rate), rate
    if r2 != rate:
        return None, {**rec, "result": f"rate changed {rate} -> {r2}: nothing written"}
    y = splice_outside(x, y, a, b)
    rec.update(guard_start_s=round(a / rate, 4), guard_end_s=round(b / rate, 4),
               span_samples_identical=bool(np.array_equal(np.asarray(x)[a:b], y[a:b])),
               clicks_in_speech_before=before["clicks_in_speech"])
    after = VM.click_stats(y, rate)
    rec["clicks_after"] = after["clicks"]
    if len(y) != len(x) or not rec["span_samples_identical"] or after["clicks"] >= before["clicks"]:
        return None, {**rec, "result": "repair rejected (count did not fall, or length or span changed): nothing written"}
    return y, {**rec, "result": "kept"}


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description="adeclick outside the guarded speech span only")
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--profile")
    a = ap.parse_args(argv)
    if Path(a.src).resolve() == Path(a.dst).resolve():
        print("refusing to overwrite the input", file=sys.stderr)
        return 2
    E, _ = VE.load_profile(a.profile)
    x, rate = VE.read_wav(a.src)
    y, rec = declick(x, rate, E)
    if y is not None:
        VE.write_wav16(a.dst, y, rate)
    print(json.dumps(rec, ensure_ascii=False))
    return 0 if (y is not None or rec["clicks_before"] == 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
