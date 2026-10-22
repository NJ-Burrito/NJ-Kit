"""hero_check.py -- owner's review, reel 2 (choreography.md rule 2): the hero
of a scene must be unmissable. Given a contact-sheet frame and the hero's
bounding box (read from <d>/snapshots/hero-boxes.json, written by the
snapshot step from each data-hero element's geometry), measures:

  - size share: the hero box's shorter side / the frame's shorter side (>=35%)
  - contrast separation: |mean luminance inside the box - mean luminance in a
    ring just outside it| (>=15, 0-255 scale, house default)

Light-ground fix (prefilm-fix-0921, Lead's decision): when a scene's ground
luminance is above 0.8, the hero sits on a solid dark-paper backing shape
(`data-hero-backing`) instead of the ground directly. When the hero-boxes.json
entry for a scene carries a "backing" box (id/x/y/w/h), the hero is measured
against ITS BACKING (size + contrast) and the backing is separately measured
against the ground ring; BOTH must clear the (unchanged, house default) 15.0
contrast threshold. No backing box -> unchanged hero-vs-ground behaviour.

    PYTHONUTF8=1 uv run --with pillow python hero_check.py <frame.jpg> <hero-boxes.json> <scene-id>

Exit 0: all thresholds cleared. Exit 1: prints which one failed, with numbers.
"""
import json
import sys

MIN_SIZE_SHARE = 0.35
MIN_LUMA_SEPARATION = 15.0


def luminance(px):
    r, g, b = px[0], px[1], px[2]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _mean_luma(im, box):
    x0, y0, x1, y1 = box["x"], box["y"], box["x"] + box["w"], box["y"] + box["h"]
    px = list(im.crop((x0, y0, x1, y1)).getdata())
    return (sum(luminance(p) for p in px) / len(px)) if px else None


def _ring_luma(im, w, h, box):
    x0, y0, x1, y1 = box["x"], box["y"], box["x"] + box["w"], box["y"] + box["h"]
    pad = int(0.15 * min(box["w"], box["h"])) or 1
    ring_box = (max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad), min(h, y1 + pad))
    px = list(im.crop(ring_box).getdata())
    return (sum(luminance(p) for p in px) / len(px)) if px else None


def check(frame_path, box, frame_size=None):
    from PIL import Image
    im = Image.open(frame_path).convert("RGB")
    w, h = im.size if frame_size is None else frame_size
    problems = []
    short_side = min(w, h)
    box_short = min(box["w"], box["h"])
    share = box_short / short_side if short_side else 0
    if share < MIN_SIZE_SHARE:
        problems.append("SIZE hero %.0f%% of frame's shorter side, need >=%.0f%%" % (share * 100, MIN_SIZE_SHARE * 100))

    backing = box.get("backing")
    if backing:
        # Light-ground fix: hero measured against ITS BACKING (not the ground
        # directly); the backing is separately measured against the ground ring.
        hero_luma, back_luma = _mean_luma(im, box), _mean_luma(im, backing)
        if hero_luma is None or back_luma is None:
            problems.append("NO_PIXELS: hero or backing box is empty")
        else:
            sep = abs(hero_luma - back_luma)
            if sep < MIN_LUMA_SEPARATION:
                problems.append("CONTRAST hero/backing luminance separation %.1f, need >=%.1f (hero %.1f, backing %.1f)" %
                                 (sep, MIN_LUMA_SEPARATION, hero_luma, back_luma))
        ground_luma = _ring_luma(im, w, h, backing)
        if back_luma is None or ground_luma is None:
            problems.append("NO_PIXELS: backing box or ground ring is empty")
        else:
            sep_bg = abs(back_luma - ground_luma)
            if sep_bg < MIN_LUMA_SEPARATION:
                problems.append("CONTRAST backing/ground luminance separation %.1f, need >=%.1f (backing %.1f, ground %.1f)" %
                                 (sep_bg, MIN_LUMA_SEPARATION, back_luma, ground_luma))
    else:
        hero_luma, ground_luma = _mean_luma(im, box), _ring_luma(im, w, h, box)
        if hero_luma is None or ground_luma is None:
            problems.append("NO_PIXELS: bounding box or ring is empty")
        else:
            sep = abs(hero_luma - ground_luma)
            if sep < MIN_LUMA_SEPARATION:
                problems.append("CONTRAST hero/ground luminance separation %.1f, need >=%.1f (hero %.1f, ground %.1f)" %
                                 (sep, MIN_LUMA_SEPARATION, hero_luma, ground_luma))
    return problems


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        return 1
    frame_path, boxes_path, scene_id = sys.argv[1], sys.argv[2], sys.argv[3]
    with open(boxes_path, encoding="utf-8") as f:
        boxes = json.load(f)
    box = boxes.get(scene_id)
    if not box:
        print("NO_BOX: %s not in %s" % (scene_id, boxes_path))
        return 1
    problems = check(frame_path, box)
    if problems:
        for p in problems:
            print(p)
        return 1
    print("HERO OK: %s clears size + contrast thresholds" % scene_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
