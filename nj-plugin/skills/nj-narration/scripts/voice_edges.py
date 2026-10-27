# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy"]
# ///
"""Word-safe edge cleaner for TTS takes and reference clips (nj-narration).

The problem (the owner, 2026-10-26): "when the voicing of a sentence starts, a small window sometimes appears before or
after with noise only, no words; it is distracting and makes the sound quality poor". Remove it WITHOUT cutting a
sound or a word short.

    uv run --with numpy voice_edges.py measure <wav> [...]              span + noise-only lead/tail, gate (exit 1 on a fail)
    uv run --with numpy voice_edges.py clean <in.wav> <out.wav>         cut noise-only edges, guards kept, fades inside guards
        [--no-pad]          no digital-silence pads (use for a REFERENCE clip; pads are for takes)
        [--text "..."]      the line's text; with --letters-per-s it marks a model run-on after the text is surely spoken
        [--letters-per-s N] the voice's slowest plausible rate (measured slowest / margin; see tts_guards.py)
    any command: [--profile sound_profile.json]  numbers from `take.edge` and `checks.edge_noise` (the calibration schema)

Deterministic, numpy only, no model. Calibrated on a production pipeline (2026-10-26), which is the reference
implementation and its proof (work/sound-chain/edge-proof/proof.md: 33 takes, noise-only tail 5450 ms -> 0 ms,
speech samples identical in 33 of 33).

How the speech span is found (20 ms frames, 10 ms hop, four features):
  1. energy       frame level and its distance under the loud part (p95 of the frames near the top)
  2. F0 voicing   normalised autocorrelation in the F0 range (Boersma window correction, Praat's 0.45 threshold) AND a
                  share of energy in the formant band, so mains hum or a low drone is not "voiced"; and within
                  `core_f0_max_st` semitones of the speaker's median pitch
  3. flatness +   a fricative frame (s, sh, f, th; Arabic s sh f th z) piles energy above the split frequency with a
  4. zero-cross   high zero-crossing rate; a hiss is flat across the band and is not a fricative
The CORE is voiced runs (gaps up to `run_gap_s` bridged), stray runs far under the loud part dropped. The core is then
EXTENDED outward through attached frames (loud, energetic and voice-shaped, fricative, or a periodic decay such as a
final m / n / h) across gaps of at most `attach_bridge_s`. That is the span. The cleaner keeps a guard before and after
it, puts equal-power fades INSIDE the guards only, and never scales or removes one sample of the span.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import wave
from pathlib import Path

import numpy as np

# Defaults = the calibration profile `take.edge` and `checks.edge_noise` of 2026-10-26 (each reasoned there).
DEFAULT_EDGE = {
    "frame_s": 0.02, "hop_s": 0.01, "periodicity_win_s": 0.04, "f0_range_hz": [60, 400],
    "voicing_threshold": 0.45,          # Praat's voicing threshold on the normalised autocorrelation
    "voiced_below_p95_db": 30, "voiced_band_hz": [250, 4000], "voiced_min_band_share_db": -15.0,
    "core_f0_max_st": 8.0,              # a voiced frame far from the speaker's own pitch is a drone or a squeal
    "run_gap_s": 0.4, "min_run_s": 0.04, "stray_below_p95_db": 12,
    "silent_p95_dbfs": -50.0, "ref_window_db": 40.0, "loud_below_p95_db": 18,
    "attach_below_p95_db": 30, "attach_min_band_share_db": -10.0, "attach_max_flatness": 0.3,
    "decay_below_p95_db": 40.0,
    "fricative": {"hi_split_hz": 3000, "below_p95_db": 38, "min_hi_db": 8.0, "min_zcr": 0.25, "max_flatness": 0.35},
    "attach_bridge_s": 0.04, "attach_max_lead_s": 0.3, "attach_max_tail_s": 0.35,
    "lead_guard_s": 0.1,                # kept before the first phoneme (a soft onset)
    "tail_guard_s": 0.2,                # kept after the last phoneme (decay of a final h, a release, a fricative tail)
    "fade_in_s": 0.02, "fade_out_s": 0.06,
    "lead_pad_s": 0.08, "tail_pad_s": 0.15,
    "active_below_p95_db": 50, "active_min_dbfs": -70.0,
}
DEFAULT_LIMITS = {"max_lead_ms": 30, "max_tail_ms": 50}   # noise-only sound allowed beyond the guards (VOICE-EDGE-NOISE)

LETTER = re.compile(r"[A-Za-zء-غف-يٱÀ-ɏЀ-ӿ]")


def load_profile(path: str | None) -> tuple[dict, dict]:
    """-> (edge params, check limits). A profile in the calibration schema overrides the defaults key by key."""
    E, C = json.loads(json.dumps(DEFAULT_EDGE)), dict(DEFAULT_LIMITS)
    if path:
        p = json.loads(Path(path).read_text(encoding="utf-8"))
        E.update({k: v for k, v in (p.get("take", {}).get("edge") or {}).items() if not k.endswith("why")})
        C.update({k: v for k, v in (p.get("checks", {}).get("edge_noise") or {}).items() if not k.endswith("why")})
    return E, C


# ------------------------------------------------------------------ audio io (mono float64)
def read_wav(path) -> tuple[np.ndarray, int]:
    try:
        import soundfile as sf  # optional: reads float, 24-bit, flac
        x, rate = sf.read(str(path), dtype="float64", always_2d=True)
        return x[:, 0].copy(), int(rate)
    except ImportError:
        pass
    data = Path(path).read_bytes()          # minimal RIFF reader: PCM 16/24/32-bit and float32 (what TTS engines write)
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError(f"{path}: not a RIFF/WAVE file (convert with ffmpeg first)")
    i, fmt, raw = 12, None, None
    while i + 8 <= len(data):
        cid, size = data[i:i + 4], int.from_bytes(data[i + 4:i + 8], "little")
        body = data[i + 8:i + 8 + size]
        if cid == b"fmt ":
            fmt = body
        elif cid == b"data":
            raw = body
        i += 8 + size + (size & 1)
    if fmt is None or raw is None:
        raise ValueError(f"{path}: no fmt or data chunk")
    tag, ch, rate = int.from_bytes(fmt[0:2], "little"), int.from_bytes(fmt[2:4], "little"), int.from_bytes(fmt[4:8], "little")
    sw = int.from_bytes(fmt[14:16], "little") // 8
    if tag == 0xFFFE and len(fmt) >= 26:
        tag = int.from_bytes(fmt[24:26], "little")
    raw = raw[:len(raw) - len(raw) % (sw * ch)]
    if tag == 3 and sw == 4:
        return np.frombuffer(raw, "<f4").astype("float64")[::ch].copy(), rate
    if tag == 3 and sw == 8:
        return np.frombuffer(raw, "<f8")[::ch].copy(), rate
    if sw == 2:
        a = np.frombuffer(raw, "<i2").astype("float64") / 32768.0
    elif sw == 4:
        a = np.frombuffer(raw, "<i4").astype("float64") / 2147483648.0
    elif sw == 3:
        b = np.frombuffer(raw, np.uint8).reshape(-1, 3)
        v = (b[:, 0].astype(np.int32) | (b[:, 1].astype(np.int32) << 8) | (b[:, 2].astype(np.int32) << 16))
        a = np.where(v >= 1 << 23, v - (1 << 24), v).astype("float64") / 8388608.0
    else:
        raise ValueError(f"{path}: {8 * sw}-bit wav needs `--with soundfile`")
    return a[::ch].copy(), rate


def write_wav16(path, x: np.ndarray, rate: int) -> None:
    pcm = np.clip(np.round(np.asarray(x) * 32768), -32768, 32767).astype("<i2")   # x 32768 mirrors the read: 16-bit in stays bit-identical
    tmp = Path(str(path) + ".tmp")
    with wave.open(str(tmp), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    tmp.replace(path)


# ------------------------------------------------------------------ frame features
def _frames(x: np.ndarray, n: int, hop: int) -> np.ndarray:
    if len(x) < n:
        x = np.pad(x, (0, n - len(x)))
    k = 1 + (len(x) - n) // hop
    return x[np.arange(n)[None, :] + hop * np.arange(k)[:, None]]


def features(x, rate: int, E: dict) -> dict:
    x = np.asarray(x, dtype="float64")
    hop, win = max(1, int(round(rate * E["hop_s"]))), max(2, int(round(rate * E["frame_s"])))
    fr = _frames(x, win, hop)
    nf = len(fr)
    rms = np.sqrt(np.mean(fr ** 2, axis=1))
    db = np.where(rms > 1e-6, 20 * np.log10(np.maximum(rms, 1e-12)), -120.0)
    nfft = 1 << max(6, (win - 1).bit_length())
    S = np.abs(np.fft.rfft(fr * np.hanning(win), nfft, axis=1)) ** 2 + 1e-20
    f = np.fft.rfftfreq(nfft, 1.0 / rate)
    fb = (f >= 100) & (f <= min(8000, rate / 2))
    flat = np.exp(np.mean(np.log(S[:, fb]), axis=1)) / np.mean(S[:, fb], axis=1)
    split = E["fricative"]["hi_split_hz"]
    hi_db = 10 * np.log10(S[:, f >= split].sum(axis=1) / S[:, (f >= 100) & (f < split)].sum(axis=1))
    b0, b1 = E["voiced_band_hz"]
    band_db = 10 * np.log10(S[:, (f >= b0) & (f <= b1)].sum(axis=1) / S[:, f >= 40].sum(axis=1))
    zcr = np.mean(np.abs(np.diff(np.signbit(fr).astype(np.int8), axis=1)), axis=1)
    pw = max(win, int(round(rate * E["periodicity_win_s"])))
    off = (pw - win) // 2
    fp = _frames(np.pad(x, (off, pw)), pw, hop)[:nf]
    fp = fp - fp.mean(axis=1, keepdims=True)
    wp = np.hanning(pw)
    n2 = 1 << (2 * pw - 1).bit_length()
    ac = np.fft.irfft(np.abs(np.fft.rfft(fp * wp, n2, axis=1)) ** 2, n2, axis=1)[:, :pw]
    aw = np.fft.irfft(np.abs(np.fft.rfft(wp, n2)) ** 2, n2)[:pw]
    lo_lag = max(1, int(rate / E["f0_range_hz"][1]))
    hi_lag = min(pw // 2, int(rate / E["f0_range_hz"][0]))
    rn = (ac[:, lo_lag:hi_lag + 1] / np.maximum(ac[:, :1], 1e-20)) / np.maximum(aw[lo_lag:hi_lag + 1] / aw[0], 1e-6)
    period = np.clip(rn.max(axis=1), -1.0, 1.0)
    f0 = rate / (lo_lag + np.argmax(rn, axis=1))
    live = db[db > -100]
    top = db[db >= db.max() - E["ref_window_db"]] if len(db) else db   # loud part from frames near the top only, so a
    p95 = float(np.percentile(top, 95)) if len(top) else -120.0       # long noise tail does not move the reference
    floor = float(np.percentile(live, 10)) if len(live) else -120.0
    return {"db": db, "flat": flat, "hi_db": hi_db, "band_db": band_db, "zcr": zcr, "period": period, "f0": f0,
            "hop": hop, "win": win, "p95": p95, "floor": floor, "n": nf}


# ------------------------------------------------------------------ the speech span
def speech_span(x, rate: int, E: dict, done_after_s: float | None = None) -> dict:
    """Onset and offset of the words. Raises ValueError on silent audio or no voiced speech.
    done_after_s: by then (after the first word) the text is surely spoken; a voiced run that STARTS later, after a pause
    of at least run_gap_s, is a model run-on and is dropped. Without it no run is dropped for its position."""
    F = features(x, rate, E)
    db, p95, floor, hop, win = F["db"], F["p95"], F["floor"], F["hop"], F["win"]
    if p95 < E["silent_p95_dbfs"]:
        raise ValueError("audio is silent")
    voiced = (F["period"] >= E["voicing_threshold"]) & (db >= p95 - E["voiced_below_p95_db"]) & \
             (F["band_db"] >= E["voiced_min_band_share_db"])
    strong = voiced & (db >= p95 - E["loud_below_p95_db"])
    ref = F["f0"][strong] if strong.sum() >= 5 else F["f0"][voiced]
    med_f0 = float(np.median(ref)) if len(ref) else 0.0
    pitch_ok = (np.abs(12 * np.log2(np.maximum(F["f0"], 1e-6) / med_f0)) <= E["core_f0_max_st"]) if med_f0 > 0 \
        else np.ones(len(db), bool)
    voiced &= pitch_ok
    gap_f = max(1, int(round(E["run_gap_s"] / E["hop_s"])))
    runs, cur, last = [], None, None
    for i in np.nonzero(voiced)[0]:
        if cur is not None and i - last <= gap_f:
            cur[1] = int(i)
        else:
            cur = [int(i), int(i)]
            runs.append(cur)
        last = i
    min_run = max(1, int(round(E["min_run_s"] / E["hop_s"])))
    kept, dropped, runon = [], 0, 0
    for a, b in runs:
        v = np.sort(db[a:b + 1][voiced[a:b + 1]])
        p90 = v[min(len(v) - 1, int(len(v) * .9))]
        if p90 >= p95 - E["stray_below_p95_db"] and int(voiced[a:b + 1].sum()) >= min_run:
            kept.append((a, b))
        else:
            dropped += 1
    if not kept:
        raise ValueError("no voiced speech found")
    if done_after_s is not None:
        lim_f = kept[0][0] + done_after_s * rate / hop
        keep2 = [kept[0]]
        for a, b in kept[1:]:
            if a > lim_f and a - keep2[-1][1] > gap_f:
                runon += 1
                continue
            keep2.append((a, b))
        kept = keep2
    fr = E["fricative"]
    loud = db >= p95 - E["loud_below_p95_db"]
    attached = (db >= p95 - E["attach_below_p95_db"]) & (F["band_db"] >= E["attach_min_band_share_db"]) & \
               (F["flat"] <= E["attach_max_flatness"])
    fric = (db >= p95 - fr["below_p95_db"]) & (F["hi_db"] >= fr["min_hi_db"]) & (F["zcr"] >= fr["min_zcr"]) & \
           (F["flat"] <= fr["max_flatness"])
    decay = (F["period"] >= E["voicing_threshold"]) & pitch_ok & (db >= p95 - E["decay_below_p95_db"])
    sound = loud | attached | fric | decay
    bridge = max(0, int(round(E["attach_bridge_s"] / E["hop_s"])))

    def extend(i0, step, max_s):
        lim = int(round(max_s / E["hop_s"]))
        edge, i, gap, quiet = i0, i0 + step, 0, 0
        while 0 <= i < len(db):
            if sound[i]:
                if not loud[i]:
                    quiet += 1 + gap
                    if quiet > lim:
                        break
                edge, gap = i, 0
            else:
                gap += 1
                if gap > bridge:
                    break
            i += step
        return edge

    c0, c1 = kept[0][0], kept[-1][1]
    on_f, off_f = extend(c0, -1, E["attach_max_lead_s"]), extend(c1, +1, E["attach_max_tail_s"])
    act = np.nonzero((db >= p95 - E["active_below_p95_db"]) & (db > E["active_min_dbfs"]))[0]
    a0 = int(act[0]) if len(act) else on_f
    a1 = int(act[-1]) if len(act) else off_f
    t = lambda i: i * hop / rate  # noqa: E731
    onset_s, offset_s = t(on_f), t(off_f) + win / rate
    first_s, last_s = t(min(a0, on_f)), t(max(a1, off_f)) + win / rate
    return {"onset_s": round(onset_s, 4), "offset_s": round(offset_s, 4), "span_s": round(offset_s - onset_s, 4),
            "first_sound_s": round(first_s, 4), "last_sound_s": round(last_s, 4),
            "lead_window_s": round(max(0.0, onset_s - first_s), 4), "tail_window_s": round(max(0.0, last_s - offset_s), 4),
            "p95_db": round(p95, 1), "floor_db": round(floor, 1), "f0_median_hz": round(med_f0, 1),
            "dropped_runs": dropped, "runon_runs": runon, "seconds": round(len(x) / rate, 4)}


def noise_edges(x, rate: int, E: dict, done_after_s: float | None = None) -> dict:
    s = speech_span(x, rate, E, done_after_s)
    s["lead_noise_ms"] = round(max(0.0, s["lead_window_s"] - E["lead_guard_s"]) * 1000)
    s["tail_noise_ms"] = round(max(0.0, s["tail_window_s"] - E["tail_guard_s"]) * 1000)
    return s


def edge_problems(x, rate: int, E: dict, C: dict) -> list[str]:
    """VOICE-EDGE-NOISE. Empty list = clean edges. Same detector as the cleaner."""
    try:
        s = noise_edges(x, rate, E)
    except ValueError as e:
        return [f"no speech span: {e}"]
    out = []
    if s["lead_noise_ms"] > C["max_lead_ms"]:
        out.append(f"noise-only lead-in {s['lead_noise_ms']} ms before the first word (limit {C['max_lead_ms']})")
    if s["tail_noise_ms"] > C["max_tail_ms"]:
        out.append(f"noise-only tail {s['tail_noise_ms']} ms after the last word (limit {C['max_tail_ms']})")
    return out


# ------------------------------------------------------------------ the cleaner
def fade(n: int, out: bool) -> np.ndarray:
    t = (np.arange(n) + 0.5) / max(1, n)
    return np.cos(0.5 * math.pi * t) if out else np.sin(0.5 * math.pi * t)


def clean(x, rate: int, E: dict, done_after_s: float | None = None, pad: bool = True) -> tuple[np.ndarray, dict]:
    """Keep span + guards; equal-power fades inside the guards only, and only where something was cut. -> (y, record)."""
    x = np.asarray(x, dtype="float64")
    s = speech_span(x, rate, E, done_after_s)
    n = len(x)
    start = max(0, int(round((s["onset_s"] - E["lead_guard_s"]) * rate)))
    end = min(n, int(round((s["offset_s"] + E["tail_guard_s"]) * rate)))
    body = x[start:end].copy()
    on = int(round(s["onset_s"] * rate)) - start
    off = int(round(s["offset_s"] * rate)) - start
    fi = min(int(round(E["fade_in_s"] * rate)), max(0, on)) if start > 0 else 0
    fo = min(int(round(E["fade_out_s"] * rate)), max(0, len(body) - off)) if end < n else 0
    if fi:
        body[:fi] *= fade(fi, out=False)
    if fo:
        body[len(body) - fo:] *= fade(fo, out=True)
    if pad:
        body = np.concatenate([np.zeros(int(round(E["lead_pad_s"] * rate))), body, np.zeros(int(round(E["tail_pad_s"] * rate)))])
    span_a, span_b = int(round(s["onset_s"] * rate)), int(round(s["offset_s"] * rate))
    lp = int(round(E["lead_pad_s"] * rate)) if pad else 0
    identical = bool(np.array_equal(x[span_a:span_b], body[lp + span_a - start:lp + span_b - start]))
    rec = {"cut_lead_ms": round(start * 1000 / rate), "cut_tail_ms": round((n - end) * 1000 / rate),
           "fade_in_ms": round(fi * 1000 / rate), "fade_out_ms": round(fo * 1000 / rate), "padded": pad,
           "span_samples_identical": identical, "span": s, "method": "nj-narration voice_edges.clean"}
    return body, rec


def letters_of(text: str) -> int:
    return len(LETTER.findall(text)) or len(text)


# ------------------------------------------------------------------ cli
def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("cmd", choices=["measure", "clean"])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--profile")
    ap.add_argument("--no-pad", action="store_true")
    ap.add_argument("--text")
    ap.add_argument("--letters-per-s", type=float)
    a = ap.parse_args(argv)
    E, C = load_profile(a.profile)
    done = letters_of(a.text) / a.letters_per_s if a.text and a.letters_per_s else None
    if a.cmd == "measure":
        bad = 0
        for p in a.paths:
            x, r = read_wav(p)
            try:
                s = noise_edges(x, r, E, done)
            except ValueError as e:
                s = {"error": str(e)}
            pr = edge_problems(x, r, E, C)
            bad += bool(pr)
            print(json.dumps({"file": p, **s, "problems": pr}, ensure_ascii=False))
        return 1 if bad else 0
    if len(a.paths) != 2:
        print("clean needs <in.wav> <out.wav>", file=sys.stderr)
        return 2
    src, dst = a.paths
    if Path(src).resolve() == Path(dst).resolve():
        print("refused: the output would overwrite the input (keep the raw take forever)", file=sys.stderr)
        return 2
    x, r = read_wav(src)
    y, rec = clean(x, r, E, done, pad=not a.no_pad)
    write_wav16(dst, y, r)
    rec["problems_after"] = edge_problems(y, r, E, C)
    print(json.dumps(rec, ensure_ascii=False))
    return 1 if rec["problems_after"] or not rec["span_samples_identical"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
