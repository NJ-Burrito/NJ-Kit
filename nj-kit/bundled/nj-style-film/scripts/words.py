"""Word times without a speech recogniser (whisper is not installed here).

Each line's take is cut at its longest internal silences, one per punctuation
mark, so every PHRASE starts where it is really spoken. Inside a phrase the
words share the time by letter count. Good to about a tenth of a second, which
is what a word pop needs; not good enough for lip sync.

    PYTHONUTF8=1 python words.py   ->  words.json
"""
import itertools
import json
import os
import re
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 24000
WIN = 240  # 10 ms


def silences(pcm, floor=350, least=0.12):
    n = len(pcm) // 2
    s = struct.unpack("<%dh" % n, pcm[:n * 2])
    quiet = [max(abs(v) for v in s[i:i + WIN]) < floor for i in range(0, n - WIN, WIN)]
    runs, start = [], None
    for i, q in enumerate(quiet + [False]):
        if q and start is None:
            start = i
        elif not q and start is not None:
            if start > 5 and i < len(quiet) - 5 and (i - start) * WIN / SR >= least:
                runs.append((start * WIN / SR, i * WIN / SR))
            start = None
    return runs


def main():
    beats = json.load(open(os.path.join(HERE, "beats.json"), encoding="utf-8"))["beats"]
    starts = [float(m.group(1)) * 3600 + float(m.group(2)) * 60 + float(m.group(3).replace(",", "."))
              for m in re.finditer(r"(?m)^(\d+):(\d+):([\d,]+) -->", open(os.path.join(HERE, "narration.srt"), encoding="utf-8").read())]
    out = []
    for b, t0 in zip(beats, starts):
        pcm = open(os.path.join(HERE, "vo", "%02d.pcm" % b["n"]), "rb").read()
        dur = len(pcm) / 2 / SR
        phrases = [p.strip() for p in re.split(r"(?<=[.,:?!])\s+", b["line"]) if p.strip()]
        # Which pauses are the punctuation? The set, in order, nearest to where the
        # letter count says the marks should fall. "The longest" picked a breath
        # after "A secret" over the comma after "withheld".
        load = [len(re.sub(r"\W", "", p)) + 1.5 * len(p.split()) for p in phrases]
        want = [dur * sum(load[:k + 1]) / sum(load) for k in range(len(phrases) - 1)]
        sets = list(itertools.combinations(silences(pcm), len(want)))
        if sets:
            gaps = list(min(sets, key=lambda c: sum(abs((g[0] + g[1]) / 2 - w) for g, w in zip(c, want))))
        else:  # fewer pauses than commas: fall back to one window
            phrases, gaps = [b["line"]], []
        edges = [0.04] + [x for g in gaps for x in g] + [dur - 0.05]
        for k, phrase in enumerate(phrases):
            a, z = edges[2 * k], edges[2 * k + 1]
            ws = phrase.split()
            weight = [len(re.sub(r"\W", "", w)) + 1.5 for w in ws]
            t = a
            for w, wt in zip(ws, weight):
                d = (z - a) * wt / sum(weight)
                out.append({"line": b["n"], "word": w, "start": round(t0 + t, 2), "end": round(t0 + t + d, 2)})
                t += d
        print(b["n"], len(phrases), "phrases,", len(gaps), "pauses found")
    json.dump(out, open(os.path.join(HERE, "words.json"), "w", encoding="utf-8"), indent=0)


if __name__ == "__main__":
    main()
