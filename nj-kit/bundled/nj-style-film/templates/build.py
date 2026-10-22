"""One film.html -> one HyperFrames project per aspect.

    PYTHONUTF8=1 python build.py            # writes hf-v/index.html (1080x1920) and hf-h/index.html (1920x1080)

film.html carries {{W}} {{H}} {{ASPECT}} and a /*WORDS*/[] slot; the word
times come from words.json, so a re-voiced line re-times the type by itself.
Assets are staged into both projects from captures/ (page shots cropped to the
960x900 prop box) and from the brand kit.
"""
import json
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ASPECTS = {"hf-v": ("v", 1080, 1920), "hf-h": ("h", 1920, 1080)}
BRAND = os.environ.get("QA_WRAP_BRAND", os.path.join(os.path.expanduser("~"), "Desktop", "QA-Wrap", "work", "film", "collage-2026-09-20", "hf", "assets"))
PAGE_CROPS = {"c05-page-works": "page-works", "c06-page-broken": "page-broken", "c07-mask-aim": "page-mask-aim",
              "c08-masked": "page-masked", "c09-locator-glow": "page-glow", "c10-locator-copied": "page-copied"}
AS_IS = ["c01-popup-asleep", "c02-popup-named", "c03-popup-live", "c12-report-timeline", "c12-report-broke",
         "c12-report-file", "c13-agent-brief", "t-wall-full"]


def main():
    words = json.load(open(os.path.join(HERE, "words.json"), encoding="utf-8"))
    slot = json.dumps([[w["line"], w["word"], w["start"]] for w in words], ensure_ascii=False)
    film = open(os.path.join(HERE, "film.html"), encoding="utf-8").read()
    stage = os.path.join(HERE, "stage")
    os.makedirs(stage, exist_ok=True)
    for src, dst in PAGE_CROPS.items():
        subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(HERE, "captures", src + ".png"),
                               "-vf", "crop=1200:1125:0:290", os.path.join(stage, dst + ".png")])
    for name in AS_IS:
        shutil.copy(os.path.join(HERE, "captures", name + ".png"), stage)
    for name in ("thmanyahsans-Bold.woff2", "thmanyahsans-Medium.woff2", "mark.svg"):
        shutil.copy(os.path.join(BRAND, name), stage)
    for folder, (cls, w, h) in ASPECTS.items():
        assets = os.path.join(HERE, folder, "assets")
        os.makedirs(assets, exist_ok=True)
        for name in os.listdir(stage):
            shutil.copy(os.path.join(stage, name), assets)
        page = film.replace("{{W}}", str(w)).replace("{{H}}", str(h)).replace("{{ASPECT}}", cls).replace("/*WORDS*/[]", slot)
        open(os.path.join(HERE, folder, "index.html"), "w", encoding="utf-8").write(page)
        print("built", folder, "%dx%d" % (w, h))


if __name__ == "__main__":
    main()
