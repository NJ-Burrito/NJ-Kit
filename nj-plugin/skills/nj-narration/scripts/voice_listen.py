"""voice_listen.py <wav> [--full full.wav] [--no-models] [--gender-hint male|female] -> JSON on stdout.

Describe a SOURCE voice clip by numbers. Local, CPU only, no cloud, no ASR.
Every attribute is {"value", "basis": measured|model|inferred, "confidence": high|med|low}.
The script never says anything was listened to: values are measurements or model outputs, words are inference.

Scope: SOURCE clips only (a candidate reference, a harvested slice). It is never run on a generated take to accept,
reject or re-voice it: the one-take rule stands (references/listening.md).

Not used by design: an age/gender model with a non-commercial licence, any ASR, any cloud service, any hosted LLM.
The child gate is a VETO ONLY: acoustics can block a clip, never clear it. Provenance is the real gate.

Environment (all optional):
  VOICE_LISTEN_CACHE   cache folder for model files (also sets HF_HOME and UTMOSV2_CHACHE when they are unset)
  VOICE_LISTEN_DNSMOS  folder holding sig_bak_ovr.onnx (DNSMOS P.835)
Optional packages (imported lazily, each missing one is reported in tool_errors, never fatal):
  numpy soundfile librosa pyloudnorm praat-parselmouth (GPL-3.0: your licence call) torch transformers
  audiobox_aesthetics utmosv2 onnxruntime
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
import warnings

DIALECT_ID = "badrex/mms-300m-arabic-dialect-identifier"   # CC-BY-4.0, 5-way, TV-trained
DIALECT_LICENCE = "CC-BY-4.0"
AUDIOBOX_ID = "facebook/audiobox-aesthetics"                # CC-BY-4.0
UTMOS_ID = "sarulab-speech/UTMOSv2"                         # MIT badge; trained on synthetic-speech ratings
DNSMOS_FILE = "sig_bak_ovr.onnx"                            # code MIT; model-file licence UNVERIFIED
DNSMOS_LEN = 144160                                         # 9.01 s at 16 kHz
TOOL = "voice_listen.py v1"

np = sf = librosa = None  # filled by _deps()


def _deps():
    """Import the numeric stack on first use so `--help` works on a bare interpreter."""
    global np, sf, librosa
    if np is not None:
        return
    cache = os.environ.get("VOICE_LISTEN_CACHE")
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")  # CPU only
    if cache:
        os.environ.setdefault("HF_HOME", os.path.join(cache, "huggingface"))
        os.environ.setdefault("UTMOSV2_CHACHE", os.path.join(cache, "utmosv2"))  # sic: the package spells it so
    warnings.filterwarnings("ignore")
    import numpy as _np
    import soundfile as _sf
    import librosa as _lb
    np, sf, librosa = _np, _sf, _lb


def A(value, basis, conf, **extra):
    d = {"value": value, "basis": basis, "confidence": conf}
    d.update(extra)
    return d


def _r(x, n=2):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), n)


def load_mono(path, sr=None, max_s=None):
    y, s = sf.read(path, always_2d=True)
    y = y.mean(1).astype(np.float32)
    if max_s:
        y = y[: int(max_s * s)]
    if sr and s != sr:
        y = librosa.resample(y, orig_sr=s, target_sr=sr)
        s = sr
    return y, s


# ---------------------------------------------------------------- measured layer
def measured(path, max_s=120):
    try:
        import pyloudnorm as pyln
    except ImportError:
        pyln = None
    y, sr = load_mono(path, max_s=max_s)
    dur = len(y) / sr
    out = {"seconds_analysed": A(_r(dur), "measured", "high")}
    try:
        import parselmouth
        from parselmouth.praat import call
    except ImportError:
        out["parselmouth_missing"] = "praat-parselmouth not installed: no F0, formants, jitter, shimmer, HNR; the child gate has no input"
        _generic(y, sr, out, pyln)
        return out
    snd = parselmouth.Sound(y.astype(np.float64), sampling_frequency=sr)
    pitch = snd.to_pitch_ac(time_step=0.01, pitch_floor=75, pitch_ceiling=600)
    f0 = pitch.selected_array["frequency"]
    v = f0 > 0
    if v.sum() < 10:
        out["f0"] = A(None, "measured", "low", note="almost no voiced frames")
        _generic(y, sr, out, pyln)
        return out
    fv = f0[v]
    p10, p50, p90 = np.percentile(fv, [10, 50, 90])
    conf = "high" if dur >= 5 and v.mean() > 0.2 else "med"
    out["f0_median_hz"] = A(_r(p50, 1), "measured", conf)
    out["f0_range_hz_p10_p90"] = A([_r(p10, 1), _r(p90, 1)], "measured", conf)
    out["f0_range_semitones_p10_p90"] = A(_r(12 * np.log2(p90 / p10)), "measured", conf)
    out["voiced_fraction"] = A(_r(v.mean(), 3), "measured", "high")
    # formants on voiced, loud frames (Burg); ceiling by register (5500 above 165 Hz median, else 5000)
    ceiling = 5500 if p50 > 165 else 5000
    fmt = snd.to_formant_burg(time_step=0.01, max_number_of_formants=5, maximum_formant=ceiling,
                              window_length=0.025, pre_emphasis_from=50)
    inten = snd.to_intensity(minimum_pitch=75, time_step=0.01)
    ts = pitch.xs()
    ivals = np.array([inten.get_value(t) or np.nan for t in ts])
    loud = ivals > np.nanpercentile(ivals, 50)
    F = {1: [], 2: [], 3: []}
    for t, ok_v, ok_l in zip(ts, v, loud):
        if not (ok_v and ok_l):
            continue
        for k in (1, 2, 3):
            x = fmt.get_value_at_time(k, t)
            if x and np.isfinite(x):
                F[k].append(x)
    fm = {k: (float(np.median(F[k])) if len(F[k]) > 20 else None) for k in F}
    fconf = "med" if dur >= 5 else "low"  # formants come from running speech, not sustained vowels
    for k in F:
        out[f"F{k}_hz"] = A(_r(fm[k], 0), "measured", fconf)
    # vocal-tract length L = (2n-1) c / (4 Fn), c = 35000 cm/s, mean of F2 and F3.
    # F1 is excluded: in running speech it tracks vowel height and nasality (an F1 value read 24 cm on an adult woman).
    if fm[2] and fm[3]:
        Ls = [(2 * n - 1) * 35000 / (4 * fm[n]) for n in (2, 3)]
        out["vtl_cm_estimate"] = A(_r(float(np.mean(Ls)), 1), "measured", "low",
                                   per_formant_F2_F3=[_r(x, 1) for x in Ls],
                                   note="running-speech formants; rough reference adult F 14-15 cm, M 16-17 cm, child 11-13 cm (approximate, unverified)")
    try:
        pp = call(snd, "To PointProcess (periodic, cc)", 75, 600)
        out["jitter_local"] = A(_r(call(pp, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3), 4), "measured", "med")
        out["shimmer_local"] = A(_r(call([snd, pp], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6), 4), "measured", "med")
    except Exception as e:
        out["jitter_shimmer_error"] = str(e)[:120]
    try:
        h = snd.to_harmonicity_cc(time_step=0.01, minimum_pitch=75)
        hv = h.values[0]
        hv = hv[hv > -100]
        out["hnr_db"] = A(_r(np.median(hv), 1), "measured", "high")
    except Exception as e:
        out["hnr_error"] = str(e)[:120]
    _generic(y, sr, out, pyln)
    out["_internal"] = {"f0": float(p50), "F": dict(fm), "vtl": out.get("vtl_cm_estimate", {}).get("value"), "dur": dur}
    return out


def _generic(y, sr, out, pyln=None):
    """Measurements that need only librosa / numpy: centroid, loudness, clipping, crude SNR."""
    S = np.abs(librosa.stft(y, n_fft=2048))
    cen = librosa.feature.spectral_centroid(S=S, sr=sr)[0]
    rms = librosa.feature.rms(S=S, frame_length=2048)[0]
    m = rms > np.percentile(rms, 50)
    out["spectral_centroid_hz"] = A(_r(np.median(cen[m[: len(cen)]]), 0), "measured", "high")
    try:
        out["lufs"] = A(_r(pyln.Meter(sr).integrated_loudness(y), 1), "measured", "high")
    except Exception:
        out["lufs"] = A(None, "measured", "low", note="pyloudnorm missing or failed")
    pk = float(np.max(np.abs(y)) + 1e-12)
    out["peak_dbfs"] = A(_r(20 * np.log10(pk), 2), "measured", "high")
    out["clipping_pct"] = A(_r(100 * float(np.mean(np.abs(y) >= 0.999)), 4), "measured", "high")
    r = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    if len(r) > 20:
        out["snr_db_estimate"] = A(_r(20 * np.log10(np.percentile(r, 90) / (np.percentile(r, 10) + 1e-9))), "measured", "low",
                                   note="90th/10th percentile frame RMS; clips with no pauses read low")


# ---------------------------------------------------------------- child gate (veto only)
def child_gate(m, gender_hint=None):
    """Heuristic veto. The thresholds are a reading of published ranges and are NOT validated on Arabic: UNVERIFIED.
    Verdicts: 'blocked: child signal' | 'no acoustic child signal'. Never 'adult confirmed'. Ages 13-16 count as child."""
    it = m.get("_internal")
    note = "veto only; a real child can pass and a small adult voice or a performer can be blocked. Ages 13-16 count as child. Provenance is the real gate."
    if not it:
        return {"verdict": "no acoustic child signal", "points": 0, "reasons": ["insufficient measurements"], "note": note}
    pts, why = 0, []
    f0, F, vtl = it["f0"], it["F"], it["vtl"]
    if f0 >= 300:
        pts += 1
        why.append(f"F0 median {f0:.0f} Hz >= 300")
    elif f0 >= 230 and (F.get(1) or 0) >= 600 and gender_hint == "male":
        pts += 1
        why.append(f"male-labelled with F0 {f0:.0f} Hz and F1 >= 600")
    if gender_hint == "male" and f0 >= 190:
        pts += 1
        why.append(f"male-labelled F0 {f0:.0f} Hz >= 190")
    if F.get(3) and F[3] >= 3100:
        pts += 1
        why.append(f"F3 {F[3]:.0f} Hz >= 3100")
    if F.get(1) and F[1] >= 650:
        pts += 1
        why.append(f"F1 {F[1]:.0f} Hz >= 650")
    if vtl is not None:
        if vtl <= 13.0:
            pts += 2
            why.append(f"VTL {vtl} cm <= 13.0")
        elif vtl <= 13.8:
            pts += 1
            why.append(f"VTL {vtl} cm <= 13.8")
    blocked = pts >= 3 or (pts >= 2 and f0 >= 300)
    return {"verdict": "blocked: child signal" if blocked else "no acoustic child signal", "points": pts, "reasons": why,
            "basis": "measured", "confidence": "low", "note": note}


# ---------------------------------------------------------------- models (each wrapped; a failure is recorded, not fatal)
class Models:
    _dial = None
    _abx = None
    _utmos = None
    _dns = None

    @classmethod
    def dialect(cls, wavs16):
        import torch
        from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
        torch.set_num_threads(4)
        if cls._dial is None:
            cls._dial = (AutoFeatureExtractor.from_pretrained(DIALECT_ID),
                         AutoModelForAudioClassification.from_pretrained(DIALECT_ID).eval())
        fe, m = cls._dial
        ps = []
        for w in wavs16:
            with torch.no_grad():
                ps.append(m(**fe(w, sampling_rate=16000, return_tensors="pt")).logits.softmax(-1)[0].numpy())
        p = np.mean(ps, 0)
        lab = m.config.id2label
        return [(lab[int(i)], float(p[i])) for i in np.argsort(-p)]

    @classmethod
    def audiobox(cls, y, sr):
        import torch
        from audiobox_aesthetics.infer import initialize_predictor
        if cls._abx is None:
            cls._abx = initialize_predictor()
        # fed as a tensor: file loading would need torchcodec
        r = cls._abx.forward([{"path": torch.from_numpy(y)[None], "sample_rate": sr}])[0]
        return {k: float(v) for k, v in r.items()}

    @classmethod
    def utmos(cls, path):
        import utmosv2
        if cls._utmos is None:
            cls._utmos = utmosv2.create_model(pretrained=True, device="cpu")
        return float(cls._utmos.predict(input_path=path, device="cpu"))

    @classmethod
    def dnsmos(cls, y16):
        import onnxruntime as ort
        folder = os.environ.get("VOICE_LISTEN_DNSMOS", "")
        model = os.path.join(folder, DNSMOS_FILE)
        if not os.path.isfile(model):
            raise FileNotFoundError(f"{DNSMOS_FILE} not found (set VOICE_LISTEN_DNSMOS to the folder that holds it)")
        if cls._dns is None:
            cls._dns = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
        a = y16.copy()
        while len(a) < DNSMOS_LEN:
            a = np.concatenate([a, a])
        res = []
        for st in range(0, max(1, len(a) - DNSMOS_LEN + 1), 16000):
            res.append(cls._dns.run(None, {"input_1": a[st: st + DNSMOS_LEN].astype(np.float32)[None]})[0][0])
        s, b, o = np.mean(res, 0)
        P = lambda x, c: float(np.polyval(c, x))  # P.835 polynomial fit from the DNSMOS reference code
        return {"SIG": P(s, [-0.08397278, 1.22083953, 0.0052439]), "BAK": P(b, [-0.13166888, 1.60915514, -0.39604546]),
                "OVRL": P(o, [-0.06766283, 1.11546468, 0.04602535])}


def quality_and_dialect(y, sr, out, use_models=True, full_path=None):
    errs = {}
    if not use_models:
        return errs
    y16 = librosa.resample(y, orig_sr=sr, target_sr=16000)
    t = time.time()
    try:
        if full_path:  # up to 6 windows of 8 s spread over the longer file
            yf, _ = load_mono(full_path, sr=16000)
            n = 8 * 16000
            k = min(6, max(1, len(yf) // n))
            starts = np.linspace(0, max(0, len(yf) - n), k).astype(int)
            wins = [yf[s: s + n] for s in starts if len(yf[s: s + n]) > 3 * 16000]
        else:
            wins = [y16[: 12 * 16000]]
        top = Models.dialect(wins)
        conf = "med" if top[0][1] >= 0.8 else "low"
        out["dialect"] = A(top[0][0], "model", conf, top2=[{"label": a, "p": _r(b, 3)} for a, b in top[:2]],
                           windows=len(wins), model=DIALECT_ID, licence=DIALECT_LICENCE,
                           note="5-way (MSA/Egyptian/Gulf/Levantine/Maghrebi); trained on TV speech, so read speech drifts to MSA; clip %.1f s" % (len(y) / sr))
    except Exception as e:
        errs["dialect"] = f"{type(e).__name__}: {str(e)[:200]}"
    try:
        r = Models.audiobox(y, sr)
        out["audiobox_aesthetics"] = A({k: _r(v) for k, v in r.items()}, "model", "med", model=AUDIOBOX_ID, licence="CC-BY-4.0",
                                       note="CE content enjoyment, CU usefulness, PC complexity, PQ production quality (1-10)")
    except Exception as e:
        errs["audiobox_aesthetics"] = f"{type(e).__name__}: {str(e)[:200]}"
    try:
        r = Models.dnsmos(y16)
        out["dnsmos_p835"] = A({k: _r(v) for k, v in r.items()}, "model", "med", model="Microsoft DNSMOS P.835",
                               licence="code MIT; model-file licence UNVERIFIED")
    except Exception as e:
        errs["dnsmos_p835"] = f"{type(e).__name__}: {str(e)[:200]}"
    try:
        tmp = os.path.join(tempfile.gettempdir(), f"utmos_{os.getpid()}.wav")
        sf.write(tmp, y, sr)
        try:
            v = Models.utmos(tmp)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        out["utmosv2"] = A(_r(v), "model", "low", model=UTMOS_ID, licence="MIT badge",
                           note="trained on synthetic-speech ratings; on a human source clip read it as a clean-speech score only")
    except Exception as e:
        errs["utmosv2"] = f"{type(e).__name__}: {str(e)[:200]}"
    out["_model_seconds"] = _r(time.time() - t, 1)
    return errs


def analyse(path, full_path=None, use_models=True, gender_hint=None):
    _deps()
    y, sr = load_mono(path)
    res = {"file": os.path.basename(path), "clip_seconds": _r(len(y) / sr), "tool": TOOL,
           "scope": "SOURCE clips only; never a judge of generated takes",
           "not_used": ["age/gender model with a non-commercial licence", "any ASR", "any cloud", "any hosted LLM"]}
    if len(y) / sr < 3:
        res["warning"] = "clip under 3 s: model outputs unreliable"
    m = measured(path)
    res["measured"] = {k: v for k, v in m.items() if k != "_internal"}
    res["child_gate"] = child_gate(m, gender_hint)
    it = m.get("_internal")
    if it:  # wording is the agent's inference from numbers, not an observation
        f0 = it["f0"]
        res["inferred"] = {"pitch_register_words": A("high" if f0 > 260 else "mid" if f0 > 170 else "low", "inferred", "med",
                                                     derived_from="f0_median_hz, absolute bands")}
    res["models"] = {}
    errs = quality_and_dialect(y, sr, res["models"], use_models, full_path)
    if errs:
        res["tool_errors"] = errs
    res["reminder"] = "numbers and model outputs, not listening; needs a human ear"
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("wav", help="a SOURCE clip (never a generated take)")
    ap.add_argument("--full", help="optional longer file of the same voice, for multi-window dialect")
    ap.add_argument("--no-models", action="store_true", help="measurements and child gate only")
    ap.add_argument("--gender-hint", choices=["male", "female"])
    a = ap.parse_args(argv)
    print(json.dumps(analyse(a.wav, a.full, not a.no_models, a.gender_hint), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
