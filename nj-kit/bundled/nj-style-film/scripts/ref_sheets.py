"""Stage 2: a reference video in, a few contact sheets out.

    python ref_sheets.py <video file or URL> <out dir>

Watching a reference frame by frame is the most expensive way to learn its
motion language. This cuts it into timestamped sheets of 20 frames (2 per
second, 10 s per sheet) and says which THREE to read: the hook, the middle and
the close. Read more only if the budget row allows.

A URL is downloaded with yt-dlp first. A local file is used as it is.
`-fps_mode vfr`, not `-vsync`: ffmpeg 8 removed the old flag, and that is what
broke the first run.
"""
import glob
import os
import subprocess
import sys

FRAMES_PER_SECOND = 2      # enough to see an entrance and its settle
TILE = "10x2"              # 20 frames = 10 s of film per sheet
THUMB_WIDTH = 200          # 10 across = 2000 px, the width an image read keeps legible


def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)

    if src.startswith(("http://", "https://")):
        target = os.path.join(out, "reference.mp4")
        got = run(["yt-dlp", "-q", "--no-playlist", "-f", "mp4/best", "-o", target, src])
        if got.returncode != 0 or not os.path.exists(target):
            print("download failed. Ask for the reference as a local file; do not retry.\n" + got.stdout[-400:])
            return 1
        src = target
    if not os.path.exists(src):
        print(f"no such file: {src}")
        return 1

    probe = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src])
    try:
        duration = float(probe.stdout.strip())
    except ValueError:
        print("ffprobe could not read a duration:\n" + probe.stdout[-300:])
        return 1

    pattern = os.path.join(out, "sheet-%02d.jpg")
    vf = (f"fps={FRAMES_PER_SECOND},scale={THUMB_WIDTH}:-2,"
          "drawtext=text='%{pts\\:hms}':x=4:y=4:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.6,"
          f"tile={TILE}")
    made = run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", vf, "-fps_mode", "vfr", pattern])
    sheets = sorted(glob.glob(os.path.join(out, "sheet-*.jpg")))
    if not sheets:
        # drawtext needs a font; without one, the sheets are still worth having.
        vf = f"fps={FRAMES_PER_SECOND},scale={THUMB_WIDTH}:-2,tile={TILE}"
        made = run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", vf, "-fps_mode", "vfr", pattern])
        sheets = sorted(glob.glob(os.path.join(out, "sheet-*.jpg")))
    if not sheets:
        print("ffmpeg made no sheets:\n" + made.stdout[-400:])
        return 1

    pick = sorted({0, len(sheets) // 2, len(sheets) - 1})
    print(f"{duration:.1f} s -> {len(sheets)} sheets, 10 s each, in {out}")
    print("Read these three and stop:")
    for i in pick:
        print(f"  {sheets[i]}   ({i * 10}-{min(duration, (i + 1) * 10):.0f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
