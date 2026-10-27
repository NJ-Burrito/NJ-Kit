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
