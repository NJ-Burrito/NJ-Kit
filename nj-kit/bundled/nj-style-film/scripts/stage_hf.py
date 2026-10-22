"""stage_hf.py -- the build carries its own runtime (prefilm-fix-0921, hole 1).

Run once, right after `npx hyperframes init hf ...`, from inside the project
directory (or pass --project). Copies, idempotently:
  - templates/vendor/gsap.min.js -> <project>/hf/assets/gsap.min.js
    (never a CDN URL; check_no_hotlinks in gate.py fails a page that hot-links it)
  - scripts/mix.py, scripts/voice.py, scripts/words.py -> <project>/
    (mix.py reads/writes state beside itself; running it from the shared
    skill dir looks for narration.wav there and fails -- rehearsal-0921 finding 10)

Records one line in <project>/STAGES.log so a re-run is visible, not silent.

    PYTHONUTF8=1 python stage_hf.py --project <project dir>
    PYTHONUTF8=1 python stage_hf.py --project <project dir> --selftest
"""
import argparse
import filecmp
import os
import shutil
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(HERE)
VENDOR_GSAP = os.path.join(SKILL_ROOT, "templates", "vendor", "gsap.min.js")
RUNTIME_SCRIPTS = ["mix.py", "voice.py", "words.py"]


def stage(project):
    landed = []
    assets_dir = os.path.join(project, "hf", "assets")
    os.makedirs(assets_dir, exist_ok=True)
    dst_gsap = os.path.join(assets_dir, "gsap.min.js")
    if not (os.path.exists(dst_gsap) and filecmp.cmp(VENDOR_GSAP, dst_gsap, shallow=False)):
        shutil.copy2(VENDOR_GSAP, dst_gsap)
    landed.append(dst_gsap)
    for name in RUNTIME_SCRIPTS:
        src = os.path.join(HERE, name)
        dst = os.path.join(project, name)
        if not (os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False)):
            shutil.copy2(src, dst)
        landed.append(dst)
    with open(os.path.join(project, "STAGES.log"), "a", encoding="utf-8") as fh:
        fh.write("STAGE assets %s\n" % time.strftime("%Y-%m-%d %H:%M:%S"))
    return landed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=False)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.project:
        ap.error("--project is required")
    landed = stage(a.project)
    print("STAGED: %s" % ", ".join(landed))


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        proj = os.path.join(td, "proj")
        os.makedirs(proj)
        landed1 = stage(proj)
        assert all(os.path.exists(p) and os.path.getsize(p) > 0 for p in landed1), "first stage did not land all files"
        mtimes1 = [os.path.getmtime(p) for p in landed1]
        time.sleep(0.05)
        landed2 = stage(proj)  # idempotent re-run: same content, not re-copied
        mtimes2 = [os.path.getmtime(p) for p in landed2]
        assert mtimes1 == mtimes2, "idempotent re-run touched unchanged files"
        # negative control: delete one, re-run restores it
        os.remove(landed1[0])
        stage(proj)
        assert os.path.exists(landed1[0]), "deleted runtime file was not restored"
        print("SELFTEST OK: stage lands gsap.min.js + mix/voice/words.py, idempotent, restores a deleted file")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
