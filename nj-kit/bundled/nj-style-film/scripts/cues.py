"""Stage 1: an SRT in, the film's clock out.

    python cues.py narration.srt > CUES.md

One row per narration line: when it is spoken, and the SCENE WINDOW that goes
with it. A window runs from the line's start to the next line's start, so the
picture is never empty between sentences; the first window opens at 0 and the
last one closes at --end (default: the last cue's end + 1.5 s, for an end card).
Pass the audio's real duration as --end when you know it.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from voice import END_TAIL  # devil #10: cues.py and voice.py must not disagree
except ImportError:
    END_TAIL = 2.2  # kept in sync by hand if voice.py is not copied into this project yet

TIME = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)")


def seconds(h, m, s, ms):
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")[:3]) / 1000


def parse(text):
    cues = []
    for block in re.split(r"\r?\n\s*\r?\n", text.strip()):
        lines = [l for l in block.splitlines() if l.strip()]
        for i, line in enumerate(lines):
            m = TIME.search(line)
            if m:
                g = m.groups()
                words = " ".join(l.strip() for l in lines[i + 1:])
                cues.append((seconds(*g[:4]), seconds(*g[4:]), words))
                break
    return cues


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--end")]
    end_arg = next((a for a in sys.argv[1:] if a.startswith("--end=")), None)
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    with open(args[0], encoding="utf-8-sig") as fh:
        cues = parse(fh.read())
    if not cues:
        print("no cues found: is this an SRT?", file=sys.stderr)
        return 1

    total = float(end_arg.split("=", 1)[1]) if end_arg else round(cues[-1][1] + 1.5, 2)
    print(f"# CUES — {len(cues)} lines, film length {total:.2f} s\n")
    if cues[0][0] > 1.0:
        print(f"Cold open: 0.00 – {cues[0][0]:.2f} s has no voice. It needs a picture-only hook.\n")
    print("| # | spoken | window | words | text |")
    print("| --- | --- | --- | --- | --- |")
    for i, (start, end, words) in enumerate(cues):
        w_start = 0.0 if i == 0 and cues[0][0] <= 1.0 else start
        w_end = cues[i + 1][0] if i + 1 < len(cues) else total
        print(f"| {i + 1} | {start:.2f}–{end:.2f} | {w_start:.2f}–{w_end:.2f} | {len(words.split())} | {words} |")

    # One film was measured: 43 minutes for 14 scenes. Scaled by scene count and
    # printed here so the estimate is read, never composed - and given once.
    scenes = len(cues) + (1 if cues[0][0] > 1.0 else 0)
    print(f"\nESTIMATE  about {round(43 * scenes / 14)} minutes for {scenes} scenes "
          "(measured on one film; say it once, as an estimate, and do not revise it)")

    gaps = [(cues[i + 1][0] - cues[i][1], cues[i][1], cues[i + 1][0]) for i in range(len(cues) - 1)]
    if gaps:
        g = max(gaps)
        print(f"\nLongest silence: {g[0]:.2f} s ({g[1]:.2f} -> {g[2]:.2f}). A visual event has to land inside it.")

    # Devil #10: voice.py's END_TAIL is where the real wav ends, not the last
    # SRT cue. Print it from the SAME constant voice.py uses, so they cannot drift.
    film_ends = cues[-1][1] + END_TAIL
    print(f"\nFILM ENDS {film_ends:.2f} s  (last cue {cues[-1][1]:.2f} s + END_TAIL {END_TAIL} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
