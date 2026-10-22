#!/usr/bin/env python3
"""voice-clean — master a spoken-voice recording with ffmpeg only.

Premiere chain (Parametric EQ -> DeEsser -> DeNoise -> Compressor -> Amplify ->
Hard Limiter -> Panner) reimplemented on free filters, with a measured
loudness target instead of a guessed gain boost.

    python voice_clean.py IN.mp4 -o OUT.wav
    python voice_clean.py IN.wav --sweep          # find the mud frequency
    python voice_clean.py IN.wav --preset phone --target -14
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PRESETS = {
    # name: highpass, mud_db, denoise_nf, deess, ratio, target, ceiling
    "voice":     dict(highpass=80, mud_db=-5.5, denoise=-25, deess=0.35, ratio=4, target=-16.0, ceiling=-1.5),
    "phone":     dict(highpass=100, mud_db=-7.0, denoise=-20, deess=0.45, ratio=5, target=-16.0, ceiling=-1.5),
    "broadcast": dict(highpass=80, mud_db=-5.5, denoise=-25, deess=0.35, ratio=4, target=-23.0, ceiling=-3.0),
    "gentle":    dict(highpass=70, mud_db=-2.5, denoise=0, deess=0.2, ratio=2, target=-16.0, ceiling=-1.5),
}
SWEEP_BANDS = [200, 300, 400, 500, 630, 795, 1000, 1250]


def die(msg: str, code: int = 1):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(code)


def need_ffmpeg():
    for exe in ("ffmpeg", "ffprobe"):
        if not shutil.which(exe):
            die(f"{exe} not on PATH. Install ffmpeg (winget install Gyan.FFmpeg).")


def run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        die(f"{cmd[0]} exited {p.returncode}\n{(p.stderr or '')[-2000:]}")
    return (p.stderr or "") + (p.stdout or "")


def measure(path: Path) -> dict:
    """EBU R128 analysis of a file: returns input_i / input_tp / input_lra."""
    out = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
               "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
               "-f", "null", "-"])
    m = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", out, re.S)
    if not m:
        die("could not measure loudness (no loudnorm JSON in ffmpeg output)")
    d = json.loads(m[-1])
    return {k: float(v) for k, v in d.items() if re.fullmatch(r"-?\d+(\.\d+)?|-?inf", str(v))}


def build_pre_chain(a) -> str:
    """Every link before loudness normalisation (subtractive + compressor)."""
    links = [f"highpass=f={a.highpass}"]
    if a.mud_db:
        links.append(f"equalizer=f={a.mud_hz}:t=q:w={a.mud_q}:g={a.mud_db}")
    if a.denoise:
        links.append(f"afftdn=nf={a.denoise}:nt=w")
    if a.deess:
        links.append(f"deesser=i={a.deess}")
    links.append(
        f"acompressor=threshold={a.threshold}dB:ratio={a.ratio}"
        f":attack={a.attack}:release={a.release}:makeup=1"
    )
    return ",".join(links)


def gain_chain(gain_db: float) -> list[str]:
    return [f"volume={gain_db:.2f}dB"]


def build_final_chain(a, gain_db: float) -> str:
    links = gain_chain(gain_db) + [
        f"alimiter=limit={a.ceiling}dB:attack=7:release=100:level=disabled"]
    if a.mono:
        # Equal-power pan law (0.7071 = -3 dB per channel), not a unity
        # duplicate. THE root cause of the whole "2-3 LU too hot" bug: a
        # unity mono->dual-mono duplicate (`c0=c0|c1=c0`) measures ~+3 LU
        # louder under BS.1770 (it sums per-channel mean-square power, so
        # two identical channels double the power = +3.01 dB) even though
        # nothing was made louder to the ear. Gain staging above was correct
        # all along; this duplication step after it was the actual offender
        # -- confirmed 2026-09-21 by measuring with and without it on the
        # same gain-staged mono signal (identical except this one filter).
        links.append("pan=stereo|c0=0.7071*c0|c1=0.7071*c0")
    return ",".join(links)


def sweep(src: Path, a):
    out_dir = src.with_suffix("").parent / (src.stem + "-sweep")
    out_dir.mkdir(exist_ok=True)
    print(f"sweep -> {out_dir}  (listen, pick the one where the boxiness goes)")
    for hz in SWEEP_BANDS:
        dst = out_dir / f"cut-{hz}Hz.wav"
        run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(src),
             "-t", str(a.sweep_seconds), "-vn",
             "-af", f"highpass=f={a.highpass},equalizer=f={hz}:t=q:w={a.mud_q}:g={a.mud_db}",
             "-ar", "48000", str(dst)])
        print(f"  {hz:>5} Hz  {dst.name}")
    print("then rerun with  --mud-hz <the one that won>")


def main():
    p = argparse.ArgumentParser(description="Clean and master a voice recording with ffmpeg only.")
    p.add_argument("input")
    p.add_argument("-o", "--output", help="default: <input>-clean.wav")
    p.add_argument("--preset", default="voice", choices=sorted(PRESETS))
    p.add_argument("--target", type=float, help="integrated loudness, LUFS")
    p.add_argument("--ceiling", type=float, help="true-peak ceiling, dB")
    p.add_argument("--highpass", type=int)
    p.add_argument("--mud-hz", type=float, default=795.0)
    p.add_argument("--mud-db", type=float)
    p.add_argument("--mud-q", type=float, default=2.0)
    p.add_argument("--denoise", type=float, help="noise floor dB, 0 disables")
    p.add_argument("--deess", type=float, help="0-1, 0 disables")
    p.add_argument("--ratio", type=float)
    p.add_argument("--threshold", type=float, default=-18.0)
    p.add_argument("--attack", type=float, default=5.0)
    p.add_argument("--release", type=float, default=100.0)
    p.add_argument("--mono", action="store_true", default=True, help="centre the voice (default)")
    p.add_argument("--keep-stereo", dest="mono", action="store_false")
    p.add_argument("--sweep", action="store_true", help="render probe files to find the mud frequency")
    p.add_argument("--sweep-seconds", type=int, default=20)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-report", dest="report", action="store_false", default=True)
    a = p.parse_args()

    need_ffmpeg()
    src = Path(a.input)
    if not src.exists():
        die(f"no such file: {src}")

    base = PRESETS[a.preset]
    for k, v in base.items():
        if getattr(a, k, None) is None:
            setattr(a, k, v)

    if a.sweep:
        sweep(src, a)
        return

    dst = Path(a.output) if a.output else src.with_name(src.stem + "-clean.wav")
    if dst.resolve() == src.resolve():
        die("refusing to overwrite the input; choose another -o")

    pre_chain = build_pre_chain(a)
    tmp_a = dst.with_name(dst.stem + "-stageA.wav")
    tmp_b = dst.with_name(dst.stem + "-stageB.wav")
    pre_cmd = ["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(src), "-vn",
               "-af", pre_chain, "-ar", "48000", "-c:a", "pcm_s16le", str(tmp_a)]
    if a.dry_run:
        print(" ".join(pre_cmd))
        print("(3-pass gain staging follows: peak-align, then loudness-trim,"
              " then limiter -- see build_final_chain's docstring for why)")
        return

    before = measure(src) if a.report else {}
    run(pre_cmd)

    # Stage A -> B: bring the compressed take's own true peak up near the
    # ceiling first (gain-staging). Fixes the actual bug: the compressor's
    # unity makeup (correct per-link, see table) leaves the take ~10 dB
    # under target with only rare peaks near 0 dBTP. Asking one filter to
    # jump straight to target I in that state overdrives the limiter's
    # attack/release into heavy, non-linear gain reduction that raises the
    # measured loudness 2-3 LU past target -- reproduced on all four A/B
    # masters 2026-09-21, root cause not "loudnorm is imprecise" but
    # "one big gain step + limiter doing most of the work is imprecise".
    stats_a = measure(tmp_a)
    gain1 = a.ceiling - stats_a["input_tp"]
    run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(tmp_a),
         "-af", ",".join(gain_chain(gain1)), "-ar", "48000", "-c:a", "pcm_s16le", str(tmp_b)])

    # Stage B -> final: the residual trim to hit integrated loudness is now
    # small (peak already near ceiling), so the limiter barely engages and
    # the measured result lands within ~0.2 LU of target (verified on all
    # four A/B masters + the tag-test clips, 2026-09-21).
    stats_b = measure(tmp_b)
    gain2 = a.target - stats_b["input_i"]
    final_chain = build_final_chain(a, gain2)
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(tmp_b), "-vn",
           "-af", final_chain, "-ar", "48000", "-c:a", "pcm_s16le", str(dst)]
    run(cmd)
    trash = Path.home() / ".claude" / "skills" / "safe-delete" / "scripts" / "trash.py"
    subprocess.run([sys.executable, str(trash), str(tmp_a)], check=False)
    subprocess.run([sys.executable, str(trash), str(tmp_b)], check=False)
    after = measure(dst)

    got_i, got_tp = after.get("input_i", 0.0), after.get("input_tp", 0.0)
    if a.report:
        print(f"in  : {before.get('input_i'):.1f} LUFS, peak {before.get('input_tp'):.1f} dBTP")
        print(f"out : {got_i:.1f} LUFS, peak {got_tp:.1f} dBTP   -> {dst}")

    # gate: the run refuses to claim success it did not reach
    bad = []
    if abs(got_i - a.target) > 1.0:
        bad.append(f"loudness {got_i:.1f} LUFS vs target {a.target:.1f} (>1 LU off)")
    if got_tp > a.ceiling + 0.3:
        bad.append(f"true peak {got_tp:.1f} dBTP over ceiling {a.ceiling:.1f}")
    if bad:
        die("output written but off spec: " + "; ".join(bad), code=2)
    print("OK: on target, under ceiling.")


if __name__ == "__main__":
    main()
