"""
deck-v3 data prep: copy the APPROVED words and the figure data into the Remotion
project, unchanged, and prove it.

    PYTHONUTF8=1 python prep_data.py

Sources (never edited here):
  ../ar/deck/remotion/src/slides.json        Arabic slides + notes (approved by the owner)
  ../ar/deck/remotion/src/lang/en.json       English slides + notes
  artifacts/research/kac-sentinel/ar/figure-labels-ar.json   approved Arabic figure labels
  artifacts/research/kac-sentinel/finance/model.json          F5 series
  artifacts/research/kac-sentinel/satdemo/map.png             F1 raster
Gate: exits 1 unless every copied deck file is byte-identical to its source.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
KAC = REPO / "artifacts" / "research" / "kac-sentinel"
SRC = HERE.parent / "ar" / "deck" / "remotion" / "src"
DST = HERE / "remotion" / "src" / "data"
PUB = HERE / "remotion" / "public"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    DST.mkdir(parents=True, exist_ok=True)
    (PUB / "fonts").mkdir(parents=True, exist_ok=True)
    pairs = [(SRC / "slides.json", DST / "ar.json"), (SRC / "lang" / "en.json", DST / "en.json")]
    for s, d in pairs:
        shutil.copyfile(s, d)

    labels_ar = json.loads((KAC / "ar" / "figure-labels-ar.json").read_text(encoding="utf-8"))
    model = json.loads((KAC / "finance" / "model.json").read_text(encoding="utf-8"))["role_a_analytics_subcontractor"]

    def both(fid: str, key: str) -> dict:
        return {"en": key, "ar": labels_ar[fid][key]}

    fig = {
        "F1": {k: both("F1", v) for k, v in {
            "title": "F1 — NDVI corridor scan, KAC reach near Kraymeh, 2025-08-19",
            "note": "Single scene, cloud-masked, 1.8% of AOI > 0.4 NDVI. Demo, not detection.",
            "credit": "Contains modified Copernicus Sentinel data 2025"}.items()},
        "F3": {"title": both("F3", "F3 — What the research killed"),
               "head": [both("F3", "claim"), both("F3", "what we found")],
               "rows": [[both("F3", a), both("F3", b)] for a, b in [
                   ("The boat", "37 gates, siphon, power ~19x short"),
                   ("The $650 price", "thrusters alone = $460; total >>$650"),
                   ("Canal-wide network", "\"node\" = level gauge; 920-2,750 needed"),
                   ("JOD 1.93 valuation", "irrigation cost JD 0.201, ~10x lower"),
                   ("\"Detection is the gap\"", "JVA already found 35,403 violations")]]},
        "F5": {"title": both("F5", "F5 — Role A cumulative cash flow, 5-year, by scenario (JD)"),
               "names": {k: both("F5", k) for k in ("low", "base", "high")},
               "year": both("F5", "year"),
               "series": {k: model[k]["cumulative"] for k in ("low", "base", "high")},
               "note": {"en": "NPV base JD {base_npv} (fee JD 30,000 vs 50% cap JD 21,708 — conflict); NPV high JD {high_npv}; NPV low JD {low_npv}",
                        "ar": labels_ar["F5"]["NPV base JD {base_npv} (fee JD 30,000 vs 50% cap JD 21,708 — conflict); NPV high JD {high_npv}; NPV low JD {low_npv}"]},
               "npv": {k: f"{model[k]['npv']:,.0f}" for k in ("low", "base", "high")}},
        "F8": {"title": both("F8", "F8 — Phase 0 plan (at most 90 days, JD 1,000 cash cap)"),
               "head": [both("F8", k) for k in ("step", "days", "owner", "cash")],
               "rows": [{"step": both("F8", s), "days": both("F8", d), "from": a, "to": b,
                         "owner": both("F8", o), "cash": both("F8", c)} for s, d, a, b, o, c in [
                   ("Introduction to JVA", "1-30", 1, 30, "Ensera leadership", "0"),
                   ("Desk checks (5 items)", "1-30", 1, 30, "the owner", "0"),
                   ("Sentinel-2 corridor demo", "running", 0, 90, "satdemo worker", "0"),
                   ("JVA Internal Control meeting", "30-60", 30, 60, "the owner + leader", "travel"),
                   ("2-day range test", "45-75", 45, 75, "the owner + CTO", "$79-140"),
                   ("Go/no-go memo", "90", 90, 90, "the owner", "0")]],
               "kill": both("F8", "Kill if: no JVA meeting by day 60 (K0.1) • no material recurrence at cleared sites (K0.2) • no alert-to-action MoU (K0.3) • log not shared (K0.4) • range <200m or false alarms too high (K0.5) • KfW ToR already covers monitoring (K0.6)")},
    }
    (DST / "figures.json").write_text(json.dumps(fig, ensure_ascii=False, indent=1), encoding="utf-8")

    # F1 raster: crop matplotlib's axes/colourbar off, keep the NDVI pixels only.
    from PIL import Image
    Image.open(KAC / "satdemo" / "map.png").convert("RGB").crop((207, 50, 955, 662)).save(PUB / "ndvi.png")

    for f in ("thmanyahserifdisplay-Medium.otf", "thmanyahserifdisplay-Bold.otf", "thmanyahserifdisplay-Black.otf",
              "thmanyahseriftext-Regular.otf", "thmanyahseriftext-Medium.otf", "thmanyahseriftext-Bold.otf"):
        shutil.copyfile(REPO / "brand" / "fonts" / "thmanyah" / "otf" / f, PUB / "fonts" / f)

    bad = [str(d) for s, d in pairs if sha(s) != sha(d)]
    print("WORDS_GATE", "FAIL " + ", ".join(bad) if bad else "OK: ar.json and en.json byte-identical to the approved sources")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
