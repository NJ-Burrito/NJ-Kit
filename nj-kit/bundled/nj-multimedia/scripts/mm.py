#!/usr/bin/env python
"""NJ-MULTIMEDIA helper: stage gates, pre-voice fit, render probe, contact sheets. Stdlib + ffmpeg/ffprobe.

  python mm.py init <project>                    layout + BRIEF.md
  python mm.py gate <project> <stage 0-7>        GO / NO-GO for starting <stage>; appends STAGES.log
  python mm.py fit <script.json>                 per-line spoken length vs window, before any voice call; writes fit.txt
  python mm.py probe <mp4> [--duration S] [--size WxH] [--fps 30] [--lufs -14] [--lufs-tol 1.5] [--pair other.mp4] [--no-log]
  python mm.py sheet <mp4|png-folder> <out.jpg> [--every 2] [--cols 5]
  python mm.py selftest
Exit 0 = pass, 1 = fail. Set PYTHONUTF8=1 on Windows.
"""
import json, math, pathlib, re, shutil, subprocess, sys, tempfile, datetime

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
DIRS = ["creative", "marketing", "proposal", "boards", "audio", "build", "review", "out", "release"]

# stage -> files that must exist before the stage may start (paths relative to project; * = glob must match >= 1)
NEEDS = {
    0: [],
    1: ["BRIEF.md"],
    2: ["creative/style-dna.md", "creative/palette-type.md", "creative/visual-metaphors.md", "creative/sound.md",
        "marketing/positioning.md", "marketing/story.md", "marketing/scripts.md", "marketing/claims.md"],
    3: ["proposal/PROPOSAL.md", "proposal/storyboard.md", "proposal/script.json", "proposal/DEVIL.md", "proposal/fit.txt"],
    4: ["boards/*.png", "APPROVAL.md"],
    5: ["audio/timing.json", "audio/mix.wav", "build/index.html"],
    6: ["review/REVIEW.md"],
    7: ["out/*.mp4", "out/probe.log"],
}


def die(msg):
    print(msg)
    sys.exit(1)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


# ---------------------------------------------------------------- init / gate
def init(project):
    p = pathlib.Path(project)
    for d in DIRS:
        (p / d).mkdir(parents=True, exist_ok=True)
    brief = p / "BRIEF.md"
    if not brief.exists():
        shutil.copy(SKILL / "templates" / "BRIEF.md", brief)
    gi = p / ".gitignore"
    if not gi.exists():
        gi.write_text("out/\naudio/**/*.wav\nreview/frames/\n*.mp4\n", encoding="utf-8")
    print(f"INIT {p} ({', '.join(DIRS)}); fill BRIEF.md, then: mm.py gate {p} 1")


def gate(project, stage):
    p = pathlib.Path(project)
    if stage not in NEEDS:
        die(f"NO-GO unknown stage {stage} (0-7)")
    missing = []
    for rel in NEEDS[stage]:
        if "*" in rel:
            if not list(p.glob(rel)):
                missing.append(rel)
        elif not (p / rel).is_file() or (p / rel).stat().st_size == 0:
            missing.append(rel)
    faults = []
    if stage >= 1 and (p / "BRIEF.md").is_file():
        req = [l.strip() for l in (p / "BRIEF.md").read_text(encoding="utf-8").splitlines() if re.search(r":\s*REQUIRED\s*$", l)]
        faults += [f"BRIEF slot empty: {r}" for r in req]
    if stage >= 2 and (p / "marketing/claims.md").is_file():
        rows = [l for l in (p / "marketing/claims.md").read_text(encoding="utf-8").splitlines() if l.startswith("|") and not re.match(r"^\|[\s:|-]+\|?$", l)]
        body = rows[1:]
        if not body:
            faults.append("claims.md has no claim rows")
        for r in body:
            cells = [c.strip() for c in r.strip("|").split("|")]
            if len(cells) < 2 or not cells[1] or cells[1].lower() in ("?", "tbd", "todo", "none", "-"):
                faults.append(f"claim without source: {cells[0][:60]}")
    if stage >= 3 and (p / "proposal/fit.txt").is_file() and "FIT PASS" not in (p / "proposal/fit.txt").read_text(encoding="utf-8"):
        faults.append("proposal/fit.txt is not FIT PASS")
    if stage >= 4 and (p / "APPROVAL.md").is_file() and not re.search(r"(?im)^approved:\s*\S", (p / "APPROVAL.md").read_text(encoding="utf-8")):
        faults.append("APPROVAL.md has no 'approved: <date> <who>' line")
    if stage >= 6 and (p / "review/REVIEW.md").is_file() and not re.search(r"(?im)^verdict:\s*PASS", (p / "review/REVIEW.md").read_text(encoding="utf-8")):
        faults.append("review/REVIEW.md has no 'verdict: PASS'")
    if stage >= 7 and (p / "out/probe.log").is_file():
        log = (p / "out/probe.log").read_text(encoding="utf-8")
        for mp4 in p.glob("out/*.mp4"):
            last = [l for l in log.splitlines() if l.split(" ")[1:2] == [mp4.name]]
            if not last or not last[-1].startswith("PASS"):
                faults.append(f"no passing probe for out/{mp4.name}")
    ok = not missing and not faults
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"{stamp} stage {stage} {'GO' if ok else 'NO-GO'}"
    with open(p / "STAGES.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)
    for m in missing:
        print(f"  missing: {m}")
    for x in faults:
        print(f"  fault: {x}")
    return ok


# ---------------------------------------------------------------- fit
WORD = re.compile(r"[\w\u0600-\u06FF]+(?:['’][\w]+)?")
STOP = re.compile(r"[.!?؟؛;:]")


def fit_versions(data):
    if isinstance(data, list):
        return data
    if "versions" in data:
        return data["versions"]
    return [data]


def fit(path):
    path = pathlib.Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    out, bad = [], 0
    for v in fit_versions(data):
        lang = v.get("lang", "en")
        wpm = float(v.get("wpm") or (115 if lang == "ar" else 150))
        length = float(v["length"])
        sil = v.get("silences", [])
        lines = sorted(v["lines"], key=lambda l: l["start"])
        words_total, speech = 0, 0.0
        out.append(f"[{lang}] {len(lines)} lines, {wpm:g} wpm target, {length:g} s")
        prev_end = 0.0
        for l in lines:
            text = l["text"]
            w = len(WORD.findall(text))
            stops = len(STOP.findall(text.rstrip(" .!?؟")))
            est = w * 60.0 / wpm + stops * 0.4
            win = float(l["end"]) - float(l["start"])
            words_total += w
            speech += win
            ratio = est / win if win > 0 else 99
            verdict = "ok"
            if win <= 0 or ratio > 1.15:
                verdict, bad = "FAIL too long for window (cut words or widen)", bad + 1
            elif ratio > 1.0:
                verdict = "warn tight (atempo will absorb up to the cap)"
            elif ratio < 0.6:
                verdict = "warn loose (take will sit in air or need stretching; add words or narrow)"
            if l["start"] < prev_end - 1e-6:
                verdict, bad = "FAIL overlaps previous line", bad + 1
            if l["end"] > length + 1e-6:
                verdict, bad = "FAIL ends after film length", bad + 1
            for a, b in sil:
                if l["start"] < b and l["end"] > a:
                    verdict, bad = f"FAIL crosses silence {a}-{b}", bad + 1
            prev_end = float(l["end"])
            out.append(f"  {l.get('id', '?'):>4} {l['start']:6.2f}-{l['end']:6.2f}  win {win:5.2f}s  est {est:5.2f}s  {w:2d} w {stops} stop  {verdict}")
        pace = words_total / speech * 60 if speech else 0
        out.append(f"  pace inside line windows: {pace:.0f} wpm (target {wpm:g}); words {words_total}")
    out.append("FIT PASS" if not bad else f"FIT FAIL ({bad} line faults)")
    text = "\n".join(out)
    print(text)
    (path.parent / "fit.txt").write_text(text + "\n", encoding="utf-8")
    return not bad


# ---------------------------------------------------------------- probe
def ffprobe(mp4):
    r = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(mp4)])
    if r.returncode:
        die(f"FAIL ffprobe: {r.stderr.strip()[:300]}")
    return json.loads(r.stdout)


def lufs(mp4):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp4), "-af", "ebur128=framelog=quiet", "-f", "null", "-"])
    m = re.findall(r"I:\s+(-?[\d.]+)\s+LUFS", r.stderr)
    return float(m[-1]) if m else None


def facts(mp4):
    j = ffprobe(mp4)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    fps = None
    if v and v.get("r_frame_rate"):
        n, d = v["r_frame_rate"].split("/")
        fps = float(n) / float(d) if float(d) else None
    return {"duration": float(j["format"].get("duration", 0)), "w": v and v["width"], "h": v and v["height"], "fps": fps,
            "audio": a is not None, "lufs": lufs(mp4) if a else None}


def probe(mp4, duration=None, size=None, fps=30.0, target=-14.0, tol=1.5, pair=None, log=True):
    mp4 = pathlib.Path(mp4)
    f = facts(mp4)
    fails = []
    frame = 1.0 / (f["fps"] or fps)
    if f["w"] is None:
        fails.append("no video stream")
    if duration is not None and abs(f["duration"] - duration) > frame + 1e-3:
        fails.append(f"duration {f['duration']:.3f} != {duration} (±1 frame)")
    if size:
        w, h = map(int, size.lower().split("x"))
        if (f["w"], f["h"]) != (w, h):
            fails.append(f"size {f['w']}x{f['h']} != {size}")
    if fps and f["fps"] and abs(f["fps"] - fps) > 0.01:
        fails.append(f"fps {f['fps']:.2f} != {fps}")
    if not f["audio"]:
        fails.append("no audio stream")
    elif target is not None and (f["lufs"] is None or abs(f["lufs"] - target) > tol):
        fails.append(f"loudness {f['lufs']} LUFS not within {target}±{tol}")
    if pair:
        g = facts(pathlib.Path(pair))
        if abs(g["duration"] - f["duration"]) > frame + 1e-3:
            fails.append(f"pair duration {g['duration']:.3f} != {f['duration']:.3f}")
        if (g["w"], g["h"]) != (f["w"], f["h"]):
            fails.append(f"pair size {g['w']}x{g['h']} != {f['w']}x{f['h']}")
        if g["audio"] != f["audio"]:
            fails.append("pair audio presence differs")
    summary = f"{mp4.name} {f['w']}x{f['h']} {f['fps'] and round(f['fps'], 2)}fps {f['duration']:.3f}s audio={f['audio']} lufs={f['lufs']}"
    line = ("PASS " if not fails else "FAIL ") + summary + ("" if not fails else " | " + "; ".join(fails))
    print(line)
    if log:
        with open(mp4.parent / "probe.log", "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    return not fails


# ---------------------------------------------------------------- sheet
def sheet(src, out, every=2.0, cols=5):
    src, out = pathlib.Path(src), pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        pngs = sorted(src.glob("*.png"))
        if not pngs:
            die(f"FAIL no PNGs in {src}")
        rows = math.ceil(len(pngs) / cols)
        lst = out.with_suffix(".txt")
        lst.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in pngs), encoding="utf-8")
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
               "-vf", f"scale=384:-2,tile={cols}x{rows}:padding=4:color=0x202020", "-frames:v", "1", str(out)]
    else:
        dur = facts(src)["duration"]
        rows = max(1, math.ceil(dur / every / cols))
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src),
               "-vf", f"fps=1/{every},scale=384:-2,drawtext=text='%{{pts\\:hms}}':x=6:y=6:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6,tile={cols}x{rows}:padding=4:color=0x202020",
               "-frames:v", "1", str(out)]
    r = run(cmd)
    if r.returncode and not src.is_dir():  # drawtext needs a font build; retry without the time stamp
        cmd[cmd.index("-vf") + 1] = f"fps=1/{every},scale=384:-2,tile={cols}x{rows}:padding=4:color=0x202020"
        r = run(cmd)
    if r.returncode or not out.exists():
        die(f"FAIL sheet: {r.stderr.strip()[:300]}")
    print(f"SHEET {out} ({cols}x{rows})")
    return True


# ---------------------------------------------------------------- selftest
def selftest():
    t = pathlib.Path(tempfile.mkdtemp(prefix="mm-selftest-"))
    try:
        proj = t / "film"
        init(proj)
        assert not gate(proj, 1), "gate 1 must refuse a brief with REQUIRED slots"
        b = proj / "BRIEF.md"
        b.write_text(re.sub(r":\s*REQUIRED", ": filled", b.read_text(encoding="utf-8")), encoding="utf-8")
        assert gate(proj, 1), "gate 1 must pass a filled brief"
        assert not gate(proj, 2), "gate 2 must refuse without crew files"
        good = {"length": 6.0, "lang": "en", "wpm": 150, "silences": [[3.0, 3.4]], "lines": [
            {"id": "L01", "start": 0.3, "end": 2.6, "text": "Cannot reproduce. Closed."},
            {"id": "L02", "start": 3.4, "end": 6.0, "text": "Your bug was real. Proof attached."}]}
        sp = proj / "proposal" / "script.json"
        sp.write_text(json.dumps(good), encoding="utf-8")
        assert fit(sp), "good script must fit"
        bad = dict(good, lines=[{"id": "L01", "start": 0.3, "end": 1.0, "text": "Every failure links to the click that caused it."},
                                {"id": "L02", "start": 2.8, "end": 3.6, "text": "Press."}])
        sp.write_text(json.dumps(bad), encoding="utf-8")
        assert not fit(sp), "too-long line and silence crossing must fail"
        ar = {"length": 4.0, "lang": "ar", "lines": [{"id": "L01", "start": 0.2, "end": 3.0, "text": "كان الخلل حقيقيا، لكن الدليل ضاع."}]}
        sp.write_text(json.dumps(ar, ensure_ascii=False), encoding="utf-8")
        assert fit(sp), "arabic line at 115 wpm must fit"
        mp4 = proj / "out" / "t.mp4"
        r = run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=30:duration=4",
                 "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=4", "-af", "volume=-12dB",
                 "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(mp4)])
        assert r.returncode == 0, r.stderr
        assert probe(mp4, duration=4.0, size="640x360", target=None), "probe must pass the synthetic clip"
        assert not probe(mp4, duration=5.0, size="640x360", target=None), "probe must fail a wrong duration"
        assert not probe(mp4, duration=4.0, size="1920x1080", target=None), "probe must fail a wrong size"
        assert probe(mp4, duration=4.0, pair=mp4, target=None), "pair with itself must pass"
        assert sheet(mp4, proj / "review" / "sheet.jpg", every=1, cols=2)
        assert (proj / "review" / "sheet.jpg").stat().st_size > 1000
        fx, fp = HERE / "fixtures" / "probe-fixture.html", HERE / "frame_probe.mjs"
        g = run(["node", str(fp), str(fx), "--times", "0,1.5", "--font", "Arial", "--out", str(t / "fg")])
        if "playwright not found" in g.stdout:
            print("SKIP frame_probe (set PLAYWRIGHT_DIR to test it)")
        else:
            assert g.returncode == 0, "frame_probe must pass the good fixture:\n" + g.stdout
            b = run(["node", str(fp), str(fx), "--times", "0,1.5", "--font", "Arial", "--hash", "bad", "--out", str(t / "fb")])
            assert b.returncode == 1 and "off 3px" in b.stdout and "tashkeel" in b.stdout, "frame_probe must catch axis + tashkeel:\n" + b.stdout
            f = run(["node", str(fp), str(fx), "--times", "0", "--font", "Thmanyah", "--out", str(t / "ff")])
            assert f.returncode == 1 and "font not house" in f.stdout, "frame_probe must catch a non-house face:\n" + f.stdout
            print("frame_probe: good PASS, axis/tashkeel/font faults caught")
        print("SELFTEST PASS")
        return True
    finally:
        shutil.rmtree(t, ignore_errors=True)


def main(a):
    if not a:
        die(__doc__)
    cmd, rest = a[0], a[1:]

    def opt(name, default=None, cast=str):
        if name in rest:
            i = rest.index(name)
            v = rest[i + 1]
            del rest[i:i + 2]
            return cast(v)
        return default

    if cmd == "init":
        init(rest[0]); return 0
    if cmd == "gate":
        return 0 if gate(rest[0], int(rest[1])) else 1
    if cmd == "fit":
        return 0 if fit(rest[0]) else 1
    if cmd == "probe":
        d = opt("--duration", None, float); s = opt("--size"); fr = opt("--fps", 30.0, float)
        lu = opt("--lufs", "-14"); tol = opt("--lufs-tol", 1.5, float); pr = opt("--pair")
        nolog = "--no-log" in rest
        rest[:] = [x for x in rest if x != "--no-log"]
        return 0 if probe(rest[0], d, s, fr, None if lu == "none" else float(lu), tol, pr, not nolog) else 1
    if cmd == "sheet":
        ev = opt("--every", 2.0, float); cols = opt("--cols", 5, int)
        return 0 if sheet(rest[0], rest[1], ev, cols) else 1
    if cmd == "selftest":
        return 0 if selftest() else 1
    die(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
