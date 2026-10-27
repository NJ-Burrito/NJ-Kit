# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy"]
# ///
"""Prevent the noise window at the source: per-voice generation caps and an end-of-speech guard (nj-narration).

    uv run --with numpy tts_guards.py rate "<text>" <raw_take.wav>     letters per second of one raw take (speech span)
    uv run --with numpy tts_guards.py cap "<text>" --slowest 7.08       token cap and done-after time for a line
        [--margin 1.3] [--tokens-per-s 25] [--base-s 1.0] [--default-lps 5.0] [--min 50] [--max 1000]

Why: a token-based TTS (Chatterbox) that never emits end-of-speech runs on to its token cap, and the vocoder turns the
run-on into mumble then hiss: the noise-only tail. the calibration project measured 14 of 50 judge takes ending exactly at the cap.
So: (1) cap each line from its text and the voice's MEASURED slowest rate, divided by a margin so a slow dramatic
reading is never cut; (2) force EOS a fixed time after the engine marks the text complete; (3) clean the edges anyway
(voice_edges.py). Measure the rate once per voice AND per exact reference clip (sha256): a recast falls back to the
default. Formula (the calibration project's gen_cap): cap = tokens_per_s x (base_s + letters / (slowest_lps / margin)).

install_eos_guard() is Chatterbox-specific (chatterbox-tts 0.1.7, multilingual AlignmentStreamAnalyzer); for another
engine find its stop rule first and write the equivalent, never patch blind.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from voice_edges import DEFAULT_EDGE, letters_of, read_wav, speech_span  # noqa: E402


def measured_rate(text: str, wav: str, E: dict | None = None) -> float:
    """Letters of the text / speech span of the RAW take (before any trim). One number per take; keep the slowest."""
    x, r = read_wav(wav)
    s = speech_span(x, r, E or DEFAULT_EDGE)
    return round(letters_of(text) / s["span_s"], 2)


def voice_rate(slowest_lps: float | None, margin: float = 1.3, default_lps: float = 5.0) -> float:
    """Slowest plausible rate: measured slowest / margin, or the conservative default for an unmeasured voice."""
    return slowest_lps / margin if slowest_lps else default_lps


def token_cap(text: str, slowest_lps: float | None = None, margin: float = 1.3, tokens_per_s: int = 25,
              base_s: float = 1.0, default_lps: float = 5.0, min_tokens: int = 50, max_tokens: int = 1000) -> int:
    s = base_s + letters_of(text) / voice_rate(slowest_lps, margin, default_lps)
    return max(min_tokens, min(max_tokens, math.ceil(tokens_per_s * s)))


def done_after_s(text: str, slowest_lps: float | None = None, margin: float = 1.3, default_lps: float = 5.0) -> float:
    """After the first word, by this time the line is surely spoken: a voiced run that starts later, after a pause, is a
    run-on (pass to voice_edges.clean(done_after_s=...))."""
    return letters_of(text) / voice_rate(slowest_lps, margin, default_lps)


def install_eos_guard(analyzer_cls, max_tokens_after_complete: int):
    """Chatterbox: once AlignmentStreamAnalyzer has marked the text complete (`completed_at`), force EOS after at most
    N more speech tokens (the calibration project: 1.2 s = 30 tokens, 6x the package's own 200 ms long-tail rule, so a final word is
    never cut). The package rules stay; this closes the hole where attention rests on the 4th/5th token from the end
    (neither 'long tail' nor 'repetition') while EOS stays suppressed. Idempotent. Unit-test it on a fake analyzer."""
    if getattr(analyzer_cls.step, "_nj_eos_guard", None) == max_tokens_after_complete:
        return analyzer_cls
    orig = getattr(analyzer_cls.step, "_nj_orig", analyzer_cls.step)

    def step(self, logits, next_token=None):
        out = orig(self, logits, next_token=next_token)
        ca = getattr(self, "completed_at", None)
        if ca is not None and int(self.alignment.shape[0]) - int(ca) >= max_tokens_after_complete:
            out = out * 0 - 2 ** 15
            out[..., self.eos_idx] = 2 ** 15
            self.nj_forced_eos = True
        return out

    step._nj_eos_guard, step._nj_orig = max_tokens_after_complete, orig
    analyzer_cls.step = step
    return analyzer_cls


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["rate", "cap"])
    ap.add_argument("text")
    ap.add_argument("wav", nargs="?")
    ap.add_argument("--slowest", type=float)
    ap.add_argument("--margin", type=float, default=1.3)
    ap.add_argument("--tokens-per-s", type=int, default=25)
    ap.add_argument("--base-s", type=float, default=1.0)
    ap.add_argument("--default-lps", type=float, default=5.0)
    ap.add_argument("--min", type=int, default=50)
    ap.add_argument("--max", type=int, default=1000)
    a = ap.parse_args(argv)
    if a.cmd == "rate":
        if not a.wav:
            ap.error("rate needs <raw_take.wav>")
        print(json.dumps({"letters": letters_of(a.text), "letters_per_s": measured_rate(a.text, a.wav)}))
        return 0
    cap = token_cap(a.text, a.slowest, a.margin, a.tokens_per_s, a.base_s, a.default_lps, a.min, a.max)
    print(json.dumps({"letters": letters_of(a.text), "cap_tokens": cap, "cap_s": round(cap / a.tokens_per_s, 2),
                      "done_after_s": round(done_after_s(a.text, a.slowest, a.margin, a.default_lps), 2),
                      "rate_source": "measured" if a.slowest else "default"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
