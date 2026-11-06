# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy"]
# ///
"""Offline tests for nj-narration scripts. `uv run --with numpy scripts/test_nj_narration.py` -> exit 0 = all pass."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tts_guards as G  # noqa: E402
import voice_edges as VE  # noqa: E402
import voice_measure as VM  # noqa: E402

R = 24000
rng = np.random.default_rng(7)


def vowel(sec, f0=110.0, amp=0.3):
    t = np.arange(int(sec * R)) / R
    y = sum(np.sin(2 * np.pi * f0 * k * t) / k for k in range(1, 25))
    env = np.minimum(1, np.minimum(t, t[::-1]) / 0.02)
    return amp * y / np.max(np.abs(y)) * env


def fricative(sec, amp=0.05):
    n = rng.standard_normal(int(sec * R))
    s = np.fft.rfft(n)
    f = np.fft.rfftfreq(len(n), 1 / R)
    s[f < 4000] = 0
    y = np.fft.irfft(s, len(n))
    return amp * y / np.max(np.abs(y))


def hiss(sec, amp=0.004):
    return amp * rng.standard_normal(int(sec * R))


def line():
    """noise lead 0.6 s | 'word' (vowel + vowel + final fricative) | 2.5 s hiss + hum run-on"""
    floor = lambda s: 0.0005 * rng.standard_normal(int(s * R))  # noqa: E731
    t = np.arange(int(1.0 * R)) / R
    drone = 0.02 * np.sin(2 * np.pi * 55 * t)
    speech = np.concatenate([vowel(0.5), floor(0.08), vowel(0.6, 100), fricative(0.12)])
    return np.concatenate([hiss(0.6), speech, hiss(1.5), drone]), 0.6, 0.6 + len(speech) / R


def test_edges():
    E, C = VE.load_profile(None)
    x, s0, s1 = line()
    assert VE.edge_problems(x, R, E, C), "noise window not detected"
    y, rec = VE.clean(x, R, E, pad=False)
    sp = rec["span"]
    assert sp["onset_s"] <= s0 + 0.03, sp
    assert sp["offset_s"] >= s1 - 0.03, f"final fricative cut: {sp['offset_s']} < {s1}"
    assert rec["span_samples_identical"]
    assert rec["cut_tail_ms"] > 2000, rec
    assert not VE.edge_problems(np.concatenate([np.zeros(2400), y, np.zeros(3600)]), R, E, C)


def test_io_roundtrip():
    x, _, _ = line()
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "a.wav"
        VE.write_wav16(p, x, R)
        a, r = VE.read_wav(p)
        q = Path(d) / "b.wav"
        VE.write_wav16(q, a, r)
        assert p.read_bytes() == q.read_bytes(), "16-bit round trip is not bit-identical"


def test_edge_fix_and_zero_frac():
    x = np.concatenate([np.zeros(int(0.07 * R)), vowel(2.0) + 0.002 * rng.standard_normal(2 * R), np.zeros(int(0.03 * R))])
    x[: int(0.07 * R)] = 0.0
    before = VM.ref_profile(x, R)["zero_frac"]
    y, rec = VM.edge_fix(x, R)
    assert rec["zero_lead_ms"] == 70 and rec["zero_tail_ms"] == 30, rec
    assert VM.ref_profile(y, R)["zero_frac"] < before


def test_rubric():
    rub = {"criteria": {"pitch": {"metric": "f0_median_hz", "weight": 20, "band": [90, 115, 75, 150],
                                  "zero_if": {"metric": "f0_floor_share", "gt": 0.15}}}}
    assert VM.score({"f0_median_hz": 100, "f0_floor_share": 0.0}, rub)[0] == 20
    assert VM.score({"f0_median_hz": 100, "f0_floor_share": 0.3}, rub)[0] == 0
    assert VM.score({"f0_median_hz": 132.5}, rub)[0] == 10


def test_caps_and_eos():
    t = "ب" * 54
    assert G.token_cap(t, 7.08) == 273 and G.token_cap(t) == 295

    class A:
        eos_idx = 3

        def __init__(self):
            self.alignment, self.completed_at = np.zeros((0, 1)), None

        def step(self, logits, next_token=None):
            return logits.copy()

    G.install_eos_guard(A, 30)
    G.install_eos_guard(A, 30)
    a = A()
    a.completed_at, a.alignment = 10, np.zeros((39, 1))
    assert a.step(np.zeros(5))[3] == 0
    a.alignment = np.zeros((40, 1))
    o = a.step(np.zeros(5))
    assert o[3] > 0 > o[0] and a.nj_forced_eos


# ---------------------------------------------------------------- 2026-11 additions: fixtures, clicks, declick, preflight
def take_fixture(seed=5):
    """A clean, speech-like synthetic take (no downloaded audio): 0.5 s floor | 2 s voiced with syllable dips | 0.5 s floor.
    Harmonics shaped around 900 Hz with a chirp phase so the waveform is not a pulse train. Passes TAKE-QUALITY."""
    g = np.random.default_rng(seed)
    t = np.arange(int(2.0 * R)) / R
    y = sum(np.exp(-((k * 110 - 900) / 700) ** 2) * np.sin(2 * np.pi * 110 * k * t + np.pi * k * k / 30) for k in range(1, 30))
    y = 0.3 * y / np.max(np.abs(y))
    am = np.convolve((np.sin(2 * np.pi * 2.2 * t) > -0.2).astype(float), np.ones(480) / 480, "same")
    env = np.minimum(1, np.minimum(t, t[::-1]) / 0.03) * am
    floor = lambda n: 0.0008 * g.standard_normal(n)  # noqa: E731
    return np.concatenate([floor(R // 2), y * env + floor(len(y)), floor(R // 2)]), g


def test_fixture_is_clean():
    x, _ = take_fixture()
    p = VM.take_profile(x, R)
    assert VM.take_problems(p) == [] and p["clicks"] == 0, (VM.take_problems(p), p["clicks"])


def test_known_bad_fixtures():
    """Each synthetic fault must trip its own TAKE-QUALITY check (every FAIL path exercised; no limit loosened)."""
    x, g = take_fixture()
    n = len(x)
    S = np.fft.rfft(x)
    S[np.fft.rfftfreq(n, 1 / R) > 300] = 0
    gap = x.copy()
    gap[int(1.0 * R):int(1.0 * R) + 1500] = 0.0
    cases = {
        "full scale": np.clip(x * 6, -1, 1),                   # clipped
        "boxy": np.fft.irfft(S, n),                            # low-passed at 300 Hz
        "noise between words": x + 0.011 * g.standard_normal(n),  # hiss lifts the pauses
        "digital-silence gap": gap,                            # a gate ran inside the speech
    }
    for key, bad in cases.items():
        msgs = VM.take_problems(VM.take_profile(bad, R))
        assert any(key in m for m in msgs), f"{key}: not refused ({msgs})"


def test_click_metric():
    x, _ = take_fixture()
    inside, pause = x.copy(), x.copy()
    inside[int(1.5 * R)] += 0.4
    pause[int(0.2 * R)] += 0.4
    assert VM.click_stats(x, R)["clicks"] == 0
    a, b = VM.click_stats(inside, R), VM.click_stats(pause, R)
    assert (a["clicks_in_speech"], a["clicks_in_pause"]) == (1, 0), a
    assert (b["clicks_in_speech"], b["clicks_in_pause"]) == (0, 1), b
    assert VM.take_problems(VM.take_profile(inside, R)) == []                  # report-only by default
    q = {**VM.TAKEQ, "max_clicks": 0}
    assert any("click" in m for m in VM.take_problems(VM.take_profile(inside, R), q))
    xl, _, _ = line()                                                         # a sawtooth-like pitch pulse train is not a click
    assert VM.click_stats(xl, R)["clicks"] == 0


def test_declick_only_outside_span():
    import voice_declick as DC
    E, _ = VE.load_profile(None)
    x, _ = take_fixture()
    x[int(1.5 * R)] += 0.4                       # inside the speech
    x[int(2.9 * R)] += 0.4                       # in the tail floor, outside the guarded span
    assert VM.click_stats(x, R)["clicks"] == 2
    fake = lambda v, r: np.median(np.lib.stride_tricks.sliding_window_view(np.pad(v, 2, mode="edge"), 5), axis=1)  # noqa: E731
    # (a median filter rewrites spikes everywhere, speech included: the splice must put the speech span back)
    y, rec = DC.declick(x, R, E, repair=fake)
    assert y is not None and rec["result"] == "kept", rec
    assert rec["span_samples_identical"] and rec["clicks_after"] == 1 and VM.click_stats(y, R)["clicks_in_speech"] == 1, rec
    assert DC.declick(take_fixture()[0], R, E, repair=fake)[0] is None        # nothing to repair: nothing written
    import shutil
    if shutil.which("ffmpeg"):                                               # the real filter, same contract
        y2, rec2 = DC.declick(x, R, E)
        assert y2 is None or (rec2["span_samples_identical"] and rec2["clicks_after"] < rec2["clicks_before"]), rec2
        print("    ffmpeg adeclick:", rec2["result"])
    else:
        print("    SKIP ffmpeg adeclick (ffmpeg not on PATH)")


def test_preflight():
    import voice_preflight as PF
    assert PF.parse_nvidia_smi("3621\n5000\n") == [3621.0, 5000.0] and PF.parse_nvidia_smi("N/A\n") == []
    assert PF.check(4.0, 8.0, 3.6, 6.0)[0] == 0
    assert PF.check(3.0, 8.0, 3.6, 6.0)[0] == 1 and PF.check(None, 8.0, 3.6, None)[0] == 2   # unreadable = refuse, not guess


def test_lufs_oracle():
    """pyloudnorm (MIT, BS.1770-4, no true peak) as an independent meter against ffmpeg ebur128. Skips cleanly if absent."""
    import shutil
    import subprocess
    try:
        import pyloudnorm as pyln
    except ImportError:
        print("    SKIP pyloudnorm not installed (run with --with pyloudnorm)")
        return
    ff = shutil.which("ffmpeg")
    if not ff:
        print("    SKIP ffmpeg not on PATH")
        return
    r48 = 48000
    n = np.random.default_rng(11).standard_normal(5 * r48)
    s = np.fft.rfft(n)
    s /= np.maximum(1.0, np.sqrt(np.fft.rfftfreq(len(n), 1 / r48) / 100.0))        # pink-ish
    y = np.fft.irfft(s, len(n))
    y = 0.1 * y / np.sqrt(np.mean(y ** 2))
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "o.wav"
        VE.write_wav16(p, y, r48)
        a, _ = VE.read_wav(p)
        mine = pyln.Meter(r48).integrated_loudness(a)
        out = subprocess.run([ff, "-nostats", "-i", str(p), "-af", "ebur128", "-f", "null", "-"],
                             capture_output=True, text=True, timeout=60).stderr
        ff_i = float(out.rsplit("I:", 1)[1].split("LUFS")[0])
    assert abs(mine - ff_i) <= 0.1, f"pyloudnorm {mine:.2f} vs ffmpeg ebur128 {ff_i:.2f}"


if __name__ == "__main__":
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print("PASS", name)
            except AssertionError as e:
                fails += 1
                print("FAIL", name, e)
    sys.exit(1 if fails else 0)
