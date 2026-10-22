#!/usr/bin/env python3
"""Per-beat speech-against-silence check. Exit 1 if any beat FAILs.

    uv run density.py beats.json
    uv run density.py --demo        # self-check

beats.json:
  {"target": 60.0, "wpm": 140, "lang": "en", "lead_in": 1.0, "tail": 0.5,
   "beats": [{"n": 1, "dur": 4.0, "line": "It just did it again.",
              "tail": 2.2}]}     # per-beat tail overrides the default

`words` may be given instead of `line`. The end-card beat gets "tail": 2.2.

wpm: **always explicit, always from `nj-writer/NARRATION.md`'s Matrix** (via
`narration_brief.py`'s tailored rule sheet for the genre/language/destination
row) -- this script does not guess or default one. It used to carry its own
`DEFAULT_WPM = {"en": 140, "ar": 120}` fallback; that duplicated, and
sometimes disagreed with, the Matrix's per-genre bands (commercial en runs
150-170, educational en 130-150 -- neither is 140). Reconciled 2026-09-21:
the duplicate constant is gone; a missing "wpm" is a hard FAIL naming where
to get it, for every language, not a silent English default and not only an
Arabic-specific error as before.
"""
import json
import sys


def resolve_wpm(spec):
    """Explicit wpm only -- this is picture-sync arithmetic, not the source
    of the number. Get it from narration_brief.py's tailored sheet
    (nj-writer/NARRATION.md's Matrix row for the beat's genre/language/
    destination) and pass it in "wpm"."""
    if "wpm" in spec:
        return spec["wpm"]
    raise SystemExit(
        "FAIL: beats.json has no \"wpm\". Run "
        "nj-writer/scripts/narration_brief.py <brief.md> for the Matrix row's "
        "wpm_min/wpm_max, average them (or pick within the band by ear), and "
        "state it here explicitly -- density.py does not default one for "
        "any language.")


def check(spec):
    wpm = resolve_wpm(spec)
    if not wpm or wpm <= 0:
        raise SystemExit(f"FAIL: wpm must be > 0, got {wpm!r}")
    lead = spec.get("lead_in", 1.0)
    dtail = spec.get("tail", 0.5)
    rows, total_dur, total_speech, ok = [], 0.0, 0.0, True
    for b in spec["beats"]:
        if "dur" not in b:
            raise SystemExit(f"FAIL: beat {b.get('n', '?')} has no \"dur\"")
        words = b.get("words", len(b.get("line", "").split()))
        speech = words / (wpm / 60.0)
        tail = b.get("tail", dtail)
        need = 0.0 if words == 0 else speech + lead + tail
        margin = b["dur"] - need
        passed = margin >= 0
        ok &= passed
        total_dur += b["dur"]
        total_speech += speech
        rows.append((b.get("n", len(rows) + 1), b["dur"], words, speech,
                     need, b["dur"] - speech, margin, passed))
    return rows, total_dur, total_speech, ok


def report(spec):
    rows, total_dur, total_speech, ok = check(spec)
    print(f"wpm {resolve_wpm(spec)} (lang {spec.get('lang', 'en')}), "
          f"lead-in {spec.get('lead_in', 1.0)} s, tail {spec.get('tail', 0.5)} s")
    print("| # | Dur | Words | Speech | Required | Silence | Verdict |")
    print("|---|---|---|---|---|---|---|")
    for n, dur, w, sp, need, sil, m, p in rows:
        v = f"**PASS** (+{m:.2f})" if p else f"**FAIL** ({m:.2f})"
        if w == 0:
            v = "**PASS** (silent by design)"
        print(f"| {n} | {dur:.1f} | {w} | {sp:.2f} | {need:.2f} | {sil:.2f} | {v} |")
    n_pass = sum(1 for r in rows if r[7])
    print(f"| | **{total_dur:.1f}** | | **{total_speech:.2f}** | | "
          f"**{total_dur - total_speech:.2f}** | **{n_pass}/{len(rows)}** |")

    target = spec.get("target")
    if target is not None and abs(total_dur - target) > 1e-6:
        print(f"\nFAIL: durations sum to {total_dur:.3f}, target is {target}")
        ok = False
    tight = [r[0] for r in rows if r[7] and r[2] and r[6] < 0.25]
    if tight:
        print(f"\nTIGHT (< +0.25 s, needs a written pre-approved trim): {tight}")
    print("\nOK" if ok else "\nFAILED")
    return 0 if ok else 1


def demo():
    # research/116 rev 3: 11 beats, 60.0 s, 89 words, 11/11 PASS.
    spec = {"target": 60.0, "wpm": 140, "beats": [
        {"n": 1, "dur": 4.0, "words": 5}, {"n": 2, "dur": 4.3, "words": 6},
        {"n": 3, "dur": 2.7, "words": 0}, {"n": 4, "dur": 5.5, "words": 8},
        {"n": 5, "dur": 6.5, "words": 11}, {"n": 6, "dur": 7.5, "words": 14},
        {"n": 7, "dur": 6.5, "words": 10}, {"n": 8, "dur": 5.0, "words": 8},
        {"n": 9, "dur": 5.5, "words": 9}, {"n": 10, "dur": 4.5, "words": 7},
        {"n": 11, "dur": 8.0, "words": 11, "tail": 2.2}]}
    rows, dur, speech, ok = check(spec)
    assert ok, "rev 3 must pass 11/11"
    assert abs(dur - 60.0) < 1e-9 and abs(speech - 38.14) < 0.01
    assert abs(rows[5][6]) < 1e-9, "beat 6 passes at exactly +0.00"

    # research/113 rev 1: 9 beats, 50.5 s, 105 words, 5 beats break.
    rev1 = {"target": 50.5, "wpm": 140, "beats": [
        {"n": 1, "dur": 3.2, "words": 8}, {"n": 2, "dur": 3.0, "words": 8},
        {"n": 3, "dur": 2.8, "words": 7}, {"n": 4, "dur": 8.0, "words": 12},
        {"n": 5, "dur": 8.0, "words": 14}, {"n": 6, "dur": 7.5, "words": 14},
        {"n": 7, "dur": 7.5, "words": 20}, {"n": 8, "dur": 4.5, "words": 7},
        {"n": 9, "dur": 6.0, "words": 15, "tail": 2.2}]}
    rows, dur, speech, ok = check(rev1)
    assert not ok and sum(1 for r in rows if not r[7]) == 5
    assert abs(speech - 45.0) < 0.01, "105 words @140 wpm = 45.0 s, not 38"
    no_wpm = {"lang": "ar", "beats": [{"n": 1, "dur": 8.0, "words": 12}]}
    try:
        resolve_wpm(no_wpm)
        raise AssertionError("must FAIL with no explicit wpm, any language")
    except SystemExit as exc:
        assert "narration_brief.py" in str(exc)
    assert resolve_wpm({"wpm": 155, "lang": "ar", "beats": []}) == 155

    print("demo: ok — rev3 11/11 PASS, rev1 5 beats FAIL, speech 45.0 s, "
          "missing-wpm FAILs (no default, any language)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "--demo":
        sys.exit(demo())
    with open(sys.argv[1], encoding="utf-8") as fh:
        sys.exit(report(json.load(fh)))
