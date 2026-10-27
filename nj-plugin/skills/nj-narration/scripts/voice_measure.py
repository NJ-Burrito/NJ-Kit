# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy"]
# ///
"""Signal-only measures, quality gates and a written rubric for voice references and takes (nj-narration).

No model listens, no ASR, no LLM judge: numbers from the waveform only. Numbers are not ears; the human ear decides last.

    uv run --with numpy [--with librosa] voice_measure.py ref  <wav> [...] [--prov p.json] [--rubric r.json] [--edge-fix]
    uv run --with numpy [--with librosa] voice_measure.py take <wav> [...]
    common: [--limits limits.json] [--rate 24000 (needs --with scipy)] [--jsonl out.jsonl]

  ref   REF-QUALITY profile (floor, SNR, crest, clipping, digital silence, centroid, top band, reverb decay, mains hum),
        F0 stats when librosa is present (pyin), the rubric score when --rubric is given. Exit 1 if any clip fails.
  take  TAKE-QUALITY profile (pause noise re the voice, centroid, clipping, hum, digital-silence gaps inside speech).
  --edge-fix  strip exact-zero and sub-floor edges BEFORE measuring (MP3 decode / encoder padding leaves them, e.g.
        Mozilla Common Voice). This fixes the measurement input; it never loosens a limit. Inside of the clip untouched.

Limits default to the calibration project's numbers (REFQ / TAKEQ, 2026-10-24/25: set from clips the owner
approved vs rejected by ear). Recalibrate per project with --limits; never loosen a limit to make a clip pass.
Measure every candidate at the same sample rate (--rate) so the band numbers are comparable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from voice_edges import read_wav  # noqa: E402

REFQ = {
    "min_up_votes": 2, "max_down_votes": 0,   # community-validated clip (Common Voice); a published audiobook has no votes
    "max_clip_samples": 0,                    # any sample at full scale = clipped
    "max_floor_dbfs": -53.0,                  # p10 frame level; above = noisy room
    "min_floor_dbfs": -75.0,                  # below = digital silence: a gate or denoiser ran, not a microphone
    "min_snr_db": 35.0,                       # p90 speech level minus the floor
    "min_crest_db": 18.0,                     # peak minus median speech level; low = hot or squashed
    "min_top_db": -58.0,                      # energy > 8 kHz re 0.1-1 kHz; low = muffled / low-passed
    "max_decay20_s": 0.15,                    # median time for a 20 dB fall after a word; high = reverberant
    "max_zero_frac": 0.02,                    # share of exact-zero samples; high = gate / denoiser fingerprint
    "min_centroid_hz": 400.0,                 # speech power centroid; low = boxy
    "max_hum_db": 40.0,                       # 50/60 Hz line over the pause spectrum; only gross hum
}
TAKEQ = {"max_pause_rel_db": -24.0, "min_centroid_hz": 400.0, "max_clip_samples": 20, "max_hum_db": 40.0,
         "max_gate_gaps": 0}
WIN_S, HOP_S, SPEECH_BELOW_P95_DB, PAUSE_BELOW_P95_DB, ZERO_RUN_S = 0.020, 0.010, 30, 18, 0.020
EDGE_FLOOR_DBFS = -75.0


def frame_db(x, rate):
    hop, win = int(rate * HOP_S), int(rate * WIN_S)
    n = 1 + max(0, len(x) - win) // hop
    fr = x[np.arange(win)[None, :] + hop * np.arange(n)[:, None]] if len(x) >= win else np.pad(x, (0, win - len(x)))[None, :]
    rms = np.sqrt(np.mean(fr ** 2, axis=1))
    return np.where(rms > 1e-9, 20 * np.log10(np.maximum(rms, 1e-12)), -180.0), hop, win, fr


def _pct(a, q):
    a = np.sort(np.asarray(a))
    return float(a[min(len(a) - 1, int(len(a) * q))])


def hum_db(x, rate, db, hop):
    """Strongest of 50/100/150 and 60/120/180 Hz over the neighbouring pause spectrum (dB). None if < 0.4 s of pause."""
    live = np.nonzero(db > -80)[0]
    if len(live) < 12:
        return None
    quiet = np.sort(live[np.argsort(db[live])[:max(1, len(live) // 4)]])
    seg = np.concatenate([x[i * hop:i * hop + hop] for i in quiet])[:rate]
    if len(seg) < rate * 0.4:
        return None
    seg = seg * np.hanning(len(seg))
    n = np.arange(len(seg))
    pw = lambda f: float(np.abs(np.dot(seg, np.exp(-2j * math.pi * f * n / rate))) ** 2)  # noqa: E731
    best = -99.0
    for base in (50.0, 60.0):
        for m in (1, 2, 3):
            fc = base * m
            pk = max(pw(fc + d) for d in (-1.5, -0.75, 0.0, 0.75, 1.5))
            nb = sorted(pw(fc + d) for d in (-20, -16, -12, -8, 8, 12, 16, 20))
            best = max(best, 10 * math.log10((pk + 1e-30) / (nb[len(nb) // 2] + 1e-30)))
    return round(best, 1)


def ref_profile(x, rate):
    db, hop, win, fr = frame_db(x, rate)
    p95 = _pct(db, .95)
    p10 = _pct(db, .10)
    sp = np.nonzero(db >= p95 - SPEECH_BELOW_P95_DB)[0]
    sl = db[sp]
    peak = float(np.max(np.abs(x))) or 1e-9
    nfft = 1 << max(9, (win - 1).bit_length())
    S = np.abs(np.fft.rfft(fr[sp[::2]] * np.hanning(win), nfft, axis=1)) ** 2
    f = np.fft.rfftfreq(nfft, 1 / rate)
    m = f >= 100
    cen = float((S[:, m] * f[m]).sum() / max(S[:, m].sum(), 1e-30))
    lo = S[:, (f >= 100) & (f < 1000)].sum()
    top = S[:, f >= 8000].sum()
    drops, i = [], 0
    while i < len(db) - 3:                       # reverb proxy: time for a 20 dB fall after a word
        if db[i] > p95 - 10 and db[i + 1] <= p95 - 10:
            base, j = db[i + 1], i + 1
            while j < len(db) and db[j] > base - 20 and j - i < 40:
                j += 1
            if j < len(db) and db[j] <= base - 20:
                drops.append((j - i - 1) * HOP_S)
            i = j
        else:
            i += 1
    drops.sort()
    med = _pct(sl, .5)
    return {"floor_dbfs": round(p10, 1), "snr_db": round(_pct(sl, .9) - p10, 1), "speech_median_dbfs": round(med, 1),
            "peak_dbfs": round(20 * math.log10(peak), 1), "crest_db": round(20 * math.log10(peak) - med, 1),
            "clip_samples": int(np.sum(np.abs(x) >= 0.999)), "zero_frac": round(float(np.mean(x == 0.0)), 4),
            "centroid_hz": round(cen), "hum_db": hum_db(x, rate, db, hop),
            "top_db": round(10 * math.log10((top + 1e-20) / (lo + 1e-20)), 1),
            "decay20_s": round(drops[len(drops) // 2], 3) if drops else None, "seconds": round(len(x) / rate, 2)}


def ref_problems(p, prov=None, q=REFQ):
    out = []
    if prov is not None and prov.get("validation") != "published-audiobook" and (
            int(prov.get("up_votes", 0)) < q["min_up_votes"] or int(prov.get("down_votes", 0)) > q["max_down_votes"]):
        out.append(f"not validated: {prov.get('up_votes', 0)} up / {prov.get('down_votes', 0)} down votes")
    checks = [
        (p["clip_samples"] > q["max_clip_samples"], f"{p['clip_samples']} sample(s) at full scale (clipped)"),
        (p["floor_dbfs"] > q["max_floor_dbfs"], f"noise floor {p['floor_dbfs']} dBFS (limit {q['max_floor_dbfs']})"),
        (p["floor_dbfs"] < q["min_floor_dbfs"], f"floor {p['floor_dbfs']} dBFS is digital silence (gate/denoiser ran)"),
        (p["snr_db"] < q["min_snr_db"], f"SNR {p['snr_db']} dB (limit {q['min_snr_db']})"),
        (p["crest_db"] < q["min_crest_db"], f"crest {p['crest_db']} dB: hot or squashed (limit {q['min_crest_db']})"),
        (p["top_db"] < q["min_top_db"], f"muffled: top band {p['top_db']} dB (limit {q['min_top_db']})"),
        (p["decay20_s"] is not None and p["decay20_s"] > q["max_decay20_s"], f"reverberant: decay20 {p['decay20_s']} s"),
        (p["zero_frac"] > q["max_zero_frac"], f"gated/denoised: {p['zero_frac'] * 100:.1f}% exact zeros"),
        (bool(p["centroid_hz"]) and p["centroid_hz"] < q["min_centroid_hz"], f"boxy: centroid {p['centroid_hz']} Hz"),
        (p["hum_db"] is not None and p["hum_db"] > q["max_hum_db"], f"mains hum {p['hum_db']} dB"),
    ]
    return out + [msg for bad, msg in checks if bad]


def take_profile(x, rate):
    db, hop, win, _ = frame_db(x, rate)
    p95 = _pct(db, .95)
    sp = np.nonzero(db >= p95 - SPEECH_BELOW_P95_DB)[0]
    pause_rel, gaps = None, 0
    if len(sp):
        a, b = sp[0], sp[-1]
        g = db[a:b + 1]
        g = g[g < p95 - PAUSE_BELOW_P95_DB] - p95
        if len(g) >= 3:
            pause_rel = round(_pct(g, .5), 1)
        z = (x[a * hop:(b + 1) * hop + win] == 0.0).astype(np.int8)
        edges = np.diff(np.concatenate([[0], z, [0]]))
        runs = np.nonzero(edges == -1)[0] - np.nonzero(edges == 1)[0]
        gaps = int(np.sum(runs >= ZERO_RUN_S * rate))
    rp = ref_profile(x, rate)
    return {"pause_rel_db": pause_rel, "centroid_hz": rp["centroid_hz"], "clip_samples": rp["clip_samples"],
            "hum_db": rp["hum_db"], "gate_gaps": gaps, "seconds": rp["seconds"]}


def take_problems(p, q=TAKEQ):
    checks = [
        (p["pause_rel_db"] is not None and p["pause_rel_db"] > q["max_pause_rel_db"], f"noise between words: pauses {p['pause_rel_db']} dB re voice"),
        (bool(p["centroid_hz"]) and p["centroid_hz"] < q["min_centroid_hz"], f"boxy take: centroid {p['centroid_hz']} Hz"),
        (p["clip_samples"] > q["max_clip_samples"], f"{p['clip_samples']} samples at full scale"),
        (p["hum_db"] is not None and p["hum_db"] > q["max_hum_db"], f"mains hum {p['hum_db']} dB"),
        (p["gate_gaps"] > q["max_gate_gaps"], f"{p['gate_gaps']} digital-silence gap(s) inside the speech"),
    ]
    return [msg for bad, msg in checks if bad]


def edge_fix(x, rate):
    """Strip leading/trailing exact zeros, then leading/trailing 10 ms frames under -75 dBFS. Inside untouched."""
    a, b = 0, len(x)
    nz = np.nonzero(x != 0.0)[0]
    if len(nz):
        a, b = int(nz[0]), int(nz[-1]) + 1
    zl, zt = a, len(x) - b
    hop = max(1, int(rate * 0.010))
    lvl = lambda s, e: 20 * math.log10(max(1e-9, float(np.sqrt(np.mean(x[s:e] ** 2)))))  # noqa: E731
    while b - a > hop and lvl(a, a + hop) < EDGE_FLOOR_DBFS:
        a += hop
    while b - a > hop and lvl(b - hop, b) < EDGE_FLOOR_DBFS:
        b -= hop
    return x[a:b], {"cut_lead_ms": round(a * 1000 / rate), "cut_tail_ms": round((len(x) - b) * 1000 / rate),
                    "zero_lead_ms": round(zl * 1000 / rate), "zero_tail_ms": round(zt * 1000 / rate)}


def f0_stats(x, rate):
    """librosa pyin 60-450 Hz on a 16 kHz copy. f0_floor_share > 0.15 = pyin pinned at its floor: an artefact, not a voice."""
    try:
        import librosa
    except ImportError:
        return {"note": "librosa not installed: run with --with librosa for F0"}
    y = np.asarray(x, dtype="float32")
    if rate != 16000:
        y = librosa.resample(y, orig_sr=rate, target_sr=16000)
    f0, _, _ = librosa.pyin(y, fmin=60, fmax=450, sr=16000, frame_length=1024, hop_length=160)
    v = f0[~np.isnan(f0)]
    out = {"voiced_frac": round(float(np.mean(~np.isnan(f0))), 3)}
    if len(v) < 10:
        return {**out, "f0_median_hz": None}
    st = 12 * np.log2(v / np.median(v))
    ok = ~np.isnan(f0[1:]) & ~np.isnan(f0[:-1])
    steps = np.abs(12 * np.log2(f0[1:][ok] / f0[:-1][ok]))
    return {**out, "f0_median_hz": round(float(np.median(v)), 1),
            "f0_p10_p90_hz": [round(float(np.percentile(v, 10)), 1), round(float(np.percentile(v, 90)), 1)],
            "f0_sd_st": round(float(st.std()), 2), "f0_iqr_st": round(float(np.percentile(st, 75) - np.percentile(st, 25)), 2),
            "f0_floor_share": round(float(np.mean(v < 66.0)), 3), "f0_octave_jumps": int(np.sum(steps > 9.0)),
            "f0_step_st": round(float(np.median(steps)), 3) if len(steps) else None}


# ------------------------------------------------------------------ rubric
def _lin(v, lo, hi):
    return 0.0 if v is None else max(0.0, min(1.0, (v - lo) / (hi - lo)))


def _band(v, full_lo, full_hi, zero_lo, zero_hi):
    if v is None:
        return 0.0
    if full_lo <= v <= full_hi:
        return 1.0
    return _lin(v, zero_lo, full_lo) if v < full_lo else _lin(v, zero_hi, full_hi)


def score(metrics: dict, rubric: dict) -> tuple[float, dict]:
    """rubric = {"criteria": {name: {"metric", "weight", "band": [full_lo, full_hi, zero_lo, zero_hi]} or
    "lin": [zero_at, full_at], optional "zero_if": {"metric", "gt"|"lt"}, "require": {"metric", "between": [lo, hi]}}}."""
    parts = {}
    for name, c in rubric["criteria"].items():
        v = metrics.get(c["metric"])
        r = _band(v, *c["band"]) if "band" in c else _lin(v, *c["lin"])
        if "require" in c:
            rv = metrics.get(c["require"]["metric"])
            lo, hi = c["require"]["between"]
            r = r if (rv is not None and lo <= rv <= hi) else 0.0
        z = c.get("zero_if")
        if z:
            zv = metrics.get(z["metric"]) or 0
            if ("gt" in z and zv > z["gt"]) or ("lt" in z and zv < z["lt"]):
                r = 0.0
        parts[name] = round(r * c["weight"], 2)
    return round(sum(parts.values()), 2), parts


# ------------------------------------------------------------------ cli
def _resample(x, rate, to):
    if not to or to == rate:
        return x, rate
    from math import gcd
    from scipy.signal import resample_poly
    g = gcd(rate, to)
    return resample_poly(x, to // g, rate // g), to


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="signal-only voice measures (no model)")
    ap.add_argument("cmd", choices=["ref", "take"])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--prov")
    ap.add_argument("--rubric")
    ap.add_argument("--limits")
    ap.add_argument("--edge-fix", action="store_true")
    ap.add_argument("--rate", type=int)
    ap.add_argument("--jsonl")
    a = ap.parse_args(argv)
    lim = json.loads(Path(a.limits).read_text(encoding="utf-8")) if a.limits else {}
    chk = lim.get("checks", {})               # accepts {"refq":..,"takeq":..} or a full sound profile (checks.refq / checks.takeq)
    drop = lambda d: {k: v for k, v in (d or {}).items() if not k.endswith("why")}  # noqa: E731
    rq = {**REFQ, **drop(lim.get("refq") or chk.get("refq"))}
    tq = {**TAKEQ, **drop(lim.get("takeq") or chk.get("takeq"))}
    rub = json.loads(Path(a.rubric).read_text(encoding="utf-8")) if a.rubric else None
    prov = json.loads(Path(a.prov).read_text(encoding="utf-8")) if a.prov else None
    bad, rows = 0, []
    for p in a.paths:
        x, rate = read_wav(p)
        x, rate = _resample(x, rate, a.rate)
        row = {"file": p, "sha256": hashlib.sha256(Path(p).read_bytes()).hexdigest(), "rate": rate}
        if a.edge_fix:
            before = ref_problems(ref_profile(x, rate), None, rq) if a.cmd == "ref" else None
            x, row["edge_fix"] = edge_fix(x, rate)
            row["problems_before_edge_fix"] = before
        if a.cmd == "ref":
            prof = ref_profile(x, rate)
            row.update(profile=prof, problems=ref_problems(prof, prov, rq), f0=f0_stats(x, rate))
            if rub:
                flat = {**prof, **row["f0"]}
                row["score"], row["score_parts"] = score(flat, rub)
        else:
            prof = take_profile(x, rate)
            row.update(profile=prof, problems=take_problems(prof, tq))
        row["pass"] = not row["problems"]
        bad += not row["pass"]
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False))
    if a.jsonl:
        Path(a.jsonl).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
