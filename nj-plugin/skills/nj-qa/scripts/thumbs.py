"""480 px WebP thumbnails for a service's evidence pictures. Needs pillow: uv run --with pillow python -X utf8 thumbs.py --run <S>

<S>/evidence/*.png|jpg|jpeg  ->  <S>/evidence/thumbs/<stem>.webp   (q75, 480 px wide at most, never enlarged)
A thumbnail that is newer than its source is kept. Prints one line: made N, kept M.
"""
import argparse, pathlib, sys

WIDTH, QUALITY = 480, 75
PICTURES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    try:
        from PIL import Image
    except ImportError:
        print("pillow is missing: uv run --with pillow python -X utf8 thumbs.py --run <S>", file=sys.stderr)
        return 3
    ev = pathlib.Path(a.run) / "evidence"
    out = ev / "thumbs"
    made = kept = 0
    for f in sorted(ev.glob("*")) if ev.is_dir() else []:
        if not f.is_file() or f.suffix.lower() not in PICTURES:
            continue
        t = out / (f.stem + ".webp")
        if t.exists() and t.stat().st_mtime >= f.stat().st_mtime:
            kept += 1
            continue
        out.mkdir(exist_ok=True)
        with Image.open(f) as im:
            im = im.convert("RGB") if im.mode not in ("RGB", "RGBA") else im
            if im.width > WIDTH:
                im = im.resize((WIDTH, max(1, round(im.height * WIDTH / im.width))), Image.LANCZOS)
            im.save(t, "WEBP", quality=QUALITY, method=4)
        made += 1
    print(f"made {made}, kept {kept}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
