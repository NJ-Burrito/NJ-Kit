#!/usr/bin/env python3
"""shotlist.py - the gate and the animatic for nj-animation-direction.

  check    <shotlist.json>               lint the shot list against the direction rules; exit 1 on any FAIL
  animatic <shotlist.json> --out a.mp4   still boards + push-ins + scratch VO/music -> one animatic (ffmpeg)
  --selftest                             builds a toy shot list, breaks it on purpose, renders a 2-shot animatic

Every finding names the shot, the frame and the KB entry the rule rests on (kb/*.md).
Timing is integer frames at project fps (AN-066); seconds are display only.
"""
from __future__ import annotations

import json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

EMOTIONS = {"happy", "sad", "angry", "scared", "afraid", "nervous", "excited", "upset", "worried", "anxious",
            "surprised", "confused", "frustrated", "proud", "jealous", "lonely", "bored", "shocked", "terrified"}
COMMON_FPS = {12, 15, 23.976, 24, 25, 29.97, 30, 48, 50, 59.94, 60}
SIZES = {"EWS", "WS", "FS", "MWS", "MS", "MCU", "CU", "ECU", "OTS", "POV", "INSERT"}
TRANSITIONS = {"cut", "dissolve", "wipe", "fade", "j-cut", "l-cut", "match-cut", "smash-cut"}
CROSS_OK = {"neutral", "in-shot", "cutaway"}
ZOOM_MOVES = {"push-in", "pull-out", "zoom-in", "zoom-out", "none", ""}
WPM = {"ar": (110, 120), "en": (130, 160)}  # house Arabic narration band; English is a synthesis of AN-056 (one vendor ~150)
MARKS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")  # tashkeel is not a character to read
CAMERA_WORDS = re.compile(r"\b(push[- ]?in|pull[- ]?out|pan|tilt|dolly|zoom|crane|close[- ]?up|wide shot|cut to)\b", re.I)


def D(x) -> dict:
    return x if isinstance(x, dict) else {}


def L(x) -> list:
    return x if isinstance(x, list) else []


def num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def check(sl: dict) -> list[tuple[str, str, str]]:
    """Return (level, where, message) rows; level is FAIL or WARN."""
    out: list[tuple[str, str, str]] = []
    add = lambda lvl, where, msg: out.append((lvl, where, msg))
    p = D(sl.get("project"))
    fps = p.get("fps")
    if not num(fps) or fps <= 0:
        add("FAIL", "project", f"fps {fps!r}: set the project frame rate (AN-015, AN-066)")
        return out
    if fps not in COMMON_FPS:
        add("WARN", "project", f"fps {fps} is unusual; fine if deliberate (limited animation runs on 12 or 15)")
    shots = L(sl.get("shots"))
    if not shots:
        add("FAIL", "shots", "no shots")
        return out
    beats = L(sl.get("beats"))
    beat_ids = {str(D(b).get("id")) for b in beats}
    if not beats:
        add("WARN", "beats", "no beat sheet: stage 1 skipped (EX-006, EX-007)")

    ids, prev_end, durs, sides = set(), 0, [], {}
    for i, s in enumerate(shots):
        s = D(s)
        sid = str(s.get("id", f"#{i}"))
        if sid in ids:
            add("FAIL", sid, "duplicate shot id")
        ids.add(sid)
        if not re.fullmatch(r"Sc\d{2,}_Sh\d{2,}[a-z]?", sid):
            add("WARN", sid, "name shots ScNN_ShNN so they sort (AN rule 36)")
        st, du = s.get("start_f"), s.get("dur_f")
        if not (isinstance(st, int) and isinstance(du, int)) or isinstance(st, bool) or isinstance(du, bool):
            add("FAIL", sid, "start_f and dur_f must be integer frames (AN-066)")
            continue
        overlap = D(s.get("transition_in")).get("dur_f", 0)
        overlap = overlap if isinstance(overlap, int) else 0
        if st != prev_end - overlap:
            add("FAIL", f"{sid}@f{st}", f"starts at {st}, previous shot ends at {prev_end}: gap or overlap without transition_in.dur_f")
        prev_end = max(prev_end, st + du)
        durs.append(du)
        if du < 2:
            add("FAIL", f"{sid}@f{st}", "shorter than 2 frames (AN rule 37)")
        for key, why in (("beat", "every shot ties to a story beat (AN-050, AN-063)"),
                         ("job", "one job per shot (AN-050)"), ("action", "what the camera can record (AN-026)")):
            if not str(s.get(key, "")).strip():
                add("FAIL", sid, f"missing '{key}': {why}")
        if beats and str(s.get("beat", "")).split(":")[0].split()[0:1] and str(s.get("beat", "")).split(":")[0].split()[0] not in beat_ids:
            add("WARN", sid, f"beat '{s.get('beat')}' does not start with a beat id from the beat sheet {sorted(beat_ids)}")
        if s.get("size") not in SIZES:
            add("FAIL", sid, f"size {s.get('size')!r} not one of {sorted(SIZES)}")
        if s.get("size") in {"EWS", "WS"} and "establish" in str(s.get("beat", "")).lower() and du < 2 * fps:
            add("WARN", sid, "establishing shot under 2 s (AN-020, one editor's practice)")
        cam = D(s.get("camera"))
        move = str(cam.get("move") or "none")
        if move != "none" and not str(cam.get("motivation", "")).strip():
            add("FAIL", sid, f"camera '{move}' with no motivation: move only for action, blocking or emotion (AN-045, AN-046)")
        if move not in ZOOM_MOVES:
            add("WARN", sid, f"camera '{move}': the animatic renders zoom only, so this shot plays static there")
        for k in ("from_scale", "to_scale"):
            if k in cam and (not num(cam[k]) or cam[k] <= 0):
                add("FAIL", sid, f"camera.{k} {cam[k]!r} must be a positive number")
        tr = D(s.get("transition_out")).get("type") if isinstance(s.get("transition_out"), dict) else s.get("transition_out")
        if i < len(shots) - 1 and tr not in TRANSITIONS:
            add("FAIL", sid, f"transition_out {tr!r}: decide every adjacent pair (AN-044, AN-050)")
        scene, side = sid.split("_")[0], s.get("axis_side")
        if side == "N":
            sides.pop(scene, None)  # a neutral on-axis shot frees the next shot to take either side (AN-038)
        elif side:
            crossing = s.get("cross_line")
            if scene in sides and sides[scene] != side and crossing not in CROSS_OK:
                add("FAIL", sid, f"crosses the 180-degree line ({sides[scene]}->{side}) without cross_line in {sorted(CROSS_OK)} (AN-036..AN-039)")
            sides[scene] = side
        text = MARKS.sub("", str(s.get("on_screen_text", ""))).strip()
        if text and len(text) / (du / fps) > 20:
            add("WARN", sid, f"on-screen text {len(text) / (du / fps):.1f} chars/s; the subtitle benchmark is 20 (AN-029)")
        boards = L(s.get("board"))
        if boards and du < len(boards):
            add("FAIL", sid, f"{len(boards)} boards in {du} frames: fewer frames than boards")
        out += acting(s, sid, fps)

    out += beat_rows(beats)
    target = p.get("target_seconds")
    if num(target) and abs(prev_end - target * fps) > fps:
        add("FAIL", "project", f"runtime {prev_end / fps:.2f} s vs target {target} s (AN-026)")
    if num(target) and target <= 30 and num(D(shots[0]).get("dur_f")) and D(shots[0])["dur_f"] > 3 * fps:
        add("WARN", str(D(shots[0]).get("id", "#0")), "short ad: first cut later than 0:03 (AN-026, one vendor)")
    if len(durs) >= 4 and len(set(durs)) == 1:
        add("WARN", "pace", "every shot is the same length: vary pace on purpose (AN-024, AN-058)")
    tracks = D(sl.get("tracks"))
    for kind in ("vo", "music", "sfx"):
        for v in L(tracks.get(kind)):
            v = D(v)
            if not (v.get("src") and isinstance(v.get("dur_f"), int)):
                add("FAIL", str(v.get("id", kind)), f"{kind} clip needs src and integer dur_f")
                continue
            if kind != "vo":
                continue
            lang = str(v.get("lang") or p.get("lang") or "en")[:2]
            lo, hi = WPM.get(lang, WPM["en"])
            words, secs = len(str(v.get("text", "")).split()), v["dur_f"] / fps
            if words and secs and not lo <= words / secs * 60 <= hi:
                add("WARN", str(v.get("id", "vo")), f"VO {words / secs * 60:.0f} wpm, band for '{lang}' is {lo}-{hi}")
    return out


def beat_rows(beats: list) -> list[tuple[str, str, str]]:
    """Beats are pressure changes with an agent, and the curve must add up (EX-006, EX-007; one source, a convention)."""
    rows, prev = [], None
    for b in beats:
        b = D(b)
        bid = str(b.get("id", "beat"))
        deltas = [D(d) for d in L(b.get("deltas"))]
        si, so = b.get("state_in"), b.get("state_out")
        if prev is not None and si != prev:
            rows.append(("FAIL", bid, f"state_in {si} but the previous beat ended at {prev} (EX-007)"))
        if any(not str(d.get("agent", "")).strip() for d in deltas) or not deltas:
            rows.append(("FAIL", bid, "a pressure change with no named agent (EX-006)"))
        if si == so:
            rows.append(("FAIL", bid, "state in equals state out: not a beat (EX-006)"))
        if num(si) and num(so) and all(num(d.get("delta", 0)) for d in deltas) and si + sum(d.get("delta", 0) for d in deltas) != so:
            rows.append(("FAIL", bid, "the pressure curve does not add up: state_in + deltas != state_out (EX-007)"))
        if CAMERA_WORDS.search(str(b.get("turn", ""))):
            rows.append(("FAIL", bid, "a camera term in the beat's turn: camera is not a beat (EX-006)"))
        prev = so
    return rows


def acting(s: dict, sid: str, fps) -> list[tuple[str, str, str]]:
    """Character shots carry an acting block (kb/01-character-acting.md, rules R-A..R-E)."""
    a = s.get("acting")
    chars = L(s.get("characters"))
    if not chars:
        return [("WARN", sid, "acting block but no characters listed: acting checks skipped")] if a else []
    if not isinstance(a, dict):
        return [("FAIL", sid, "character shot without an acting block: objective / action / obstacle (CA-001..CA-003)")]
    rows = []
    for k in ("objective", "action", "obstacle", "thought_before", "end_state"):
        if not str(a.get(k, "")).strip():
            rows.append(("FAIL", sid, f"acting.{k} missing (CA-001..CA-003, CA-014, EX-002)"))
    words = re.findall(r"[a-z]+", str(a.get("objective", "")).lower())
    if words and (words[0] in EMOTIONS or re.search(r"\b(be|feel|feels|look|looks|seem|seems)\s+(" + "|".join(EMOTIONS) + r")\b", " ".join(words))):
        rows.append(("WARN", sid, f"objective '{a['objective']}' reads as a mood: brief the intention, let the emotion follow (CA-004, CA-049); Arabic objectives are not checked"))
    if s.get("dialogue") and len(chars) > 1 and not str(a.get("listener", "")).strip():
        rows.append(("FAIL", sid, "two-hander with no listener direction (CA-028, CA-047, CA-048)"))
    holds = [D(h) for h in L(a.get("holds"))]
    for h in holds:
        d = h.get("dur_f", 0) if num(h.get("dur_f")) else 0
        where = f"{sid}@f{h.get('start_f')}"
        if not h.get("moving") and d > 2 * fps:
            rows.append(("FAIL", where, f"dead hold {d} frames: over 2 s with no movement (CA-035)"))
        elif not h.get("moving") and d > 16 * fps / 24:
            rows.append(("WARN", where, f"still hold {d} frames: add breath, drift, a dart or a blink (CA-035, CA-036)"))
    du = s.get("dur_f", 0)
    if not holds and num(du) and du > 2 * fps and str(D(s.get("camera")).get("move") or "none") == "none":
        rows.append(("WARN", sid, "character shot over 2 s with no holds listed and no camera move: say what keeps it alive (CA-035)"))
    for e in L(a.get("expression_changes")):
        if D(e).get("during_fast_move"):
            rows.append(("FAIL", f"{sid}@f{D(e).get('f')}", "expression changes during a fast move: put it before or after (CA-042)"))
    return rows


def ff(args: list[str]) -> None:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"FAIL ffmpeg: {r.stderr.strip()[-400:]}")


def animatic(sl: dict, base: Path, out: Path) -> Path:
    """Boards split over each shot's on-screen span; zoom moves by zoompan; VO, music and SFX on the soundtrack.

    A shot is on screen from its start until the next shot starts, so a planned overlap (transition_in) plays as a
    cut at the overlap start: picture and sound stay in sync with the timeline, and dissolves are not drawn.
    """
    p = sl["project"]
    fps, w, h = p["fps"], p.get("width", 1920), p.get("height", 1080)
    shots = sl["shots"]
    tracks = D(sl.get("tracks"))
    clips = [(D(a), k) for k in ("vo", "music", "sfx") for a in L(tracks.get(k))]
    for s in shots:
        for j, x in enumerate(L(s.get("sfx"))):
            x = D(x)
            clips.append(({"id": f"{s['id']}-sfx{j}", "src": x.get("src"), "start_f": s["start_f"] + x.get("at_f", 0),
                           "dur_f": x.get("dur_f", s["dur_f"]), "gain_db": x.get("gain_db", -6)}, "sfx"))
    missing = [str(base / f) for s in shots for f in L(s.get("board"))] + [str(base / str(a.get("src"))) for a, _ in clips]
    missing = [f for f in missing if not Path(f).is_file()]
    if missing or any(not L(s.get("board")) for s in shots):
        raise SystemExit("FAIL animatic: missing board or audio files: " + ", ".join(missing[:5]) if missing else "FAIL animatic: a shot has no board")
    out.parent.mkdir(parents=True, exist_ok=True)
    total_f = max(s["start_f"] + s["dur_f"] for s in shots)
    tmp = Path(tempfile.mkdtemp(prefix="animatic-"))
    try:
        parts = []
        for k, s in enumerate(shots):
            span = (shots[k + 1]["start_f"] if k + 1 < len(shots) else total_f) - s["start_f"]
            boards = s["board"]
            cam = D(s.get("camera"))
            z0, z1 = float(cam.get("from_scale", 1)), float(cam.get("to_scale", 1))
            lo = min(z0, z1)
            z0, z1 = z0 / lo, z1 / lo  # zoompan cannot go below 1: a pull-out starts tight and opens to 1
            each = [span // len(boards)] * len(boards)
            each[-1] += span - sum(each)
            for j, (img, n) in enumerate(zip(boards, each, strict=True)):
                part = tmp / f"{k:03d}_{j:02d}.mp4"
                zoom = f"{z0}+({z1}-{z0})*on/{max(n - 1, 1)}"
                vf = (f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=decrease,pad={w * 2}:{h * 2}:(ow-iw)/2:(oh-ih)/2,"
                      f"zoompan=z='{zoom}':d={n}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps},format=yuv420p")
                ff(["-i", str(base / img), "-vf", vf, "-frames:v", str(n), "-c:v", "libx264", "-r", str(fps), str(part)])
                parts.append(part)
        lst = tmp / "list.txt"
        lst.write_text("".join("file '" + q.as_posix().replace("'", "'\\''") + "'\n" for q in parts), encoding="utf-8")
        picture = tmp / "picture.mp4"
        ff(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(picture)])
        if not clips:
            shutil.move(picture, out)
            return out
        args, chains = ["-i", str(picture)], []
        for n, (a, kind) in enumerate(clips, 1):
            args += ["-i", str(base / a["src"])]
            ms = round(a.get("start_f", 0) / fps * 1000)
            gain = a.get("gain_db", {"vo": 0, "music": -18, "sfx": -6}[kind])
            chains.append(f"[{n}:a]atrim=0:{a['dur_f'] / fps},adelay={ms}:all=1,volume={gain}dB[a{n}]")
        mix = "".join(f"[a{n}]" for n in range(1, len(clips) + 1))
        fc = ";".join(chains) + f";{mix}amix=inputs={len(clips)}:normalize=0[mix]"
        ff([*args, "-filter_complex", fc, "-map", "0:v", "-map", "[mix]", "-c:v", "copy", "-c:a", "aac", "-t", f"{total_f / fps}", str(out)])
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def frames(path: Path) -> int:
    r = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                        "stream=nb_read_frames", "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return int(r.stdout.strip() or 0)


def selftest() -> int:
    good = {
        "project": {"fps": 24, "width": 320, "height": 180, "target_seconds": 3},
        "tracks": {"vo": [{"id": "vo01", "src": "vo.wav", "start_f": 0, "dur_f": 48, "text": "one two three four five"}]},
        "beats": [{"id": "B1", "turn": "the kettle threatens her reading time", "state_in": 3, "state_out": 6,
                   "deltas": [{"delta": 3, "agent": "kettle"}]}],
        "shots": [
            {"id": "Sc01_Sh01", "beat": "establish the kitchen", "job": "where are we", "start_f": 0, "dur_f": 48,
             "size": "WS", "axis_side": "A", "action": "kettle on the stove", "board": ["b1.png"],
             "camera": {"move": "push-in", "from_scale": 1.0, "to_scale": 1.2, "motivation": "the kettle starts to shake"},
             "transition_out": {"type": "cut"}},
            {"id": "Sc01_Sh02", "beat": "reaction", "job": "she decides", "start_f": 48, "dur_f": 24, "size": "CU",
             "axis_side": "A", "action": "Mona looks up from the book", "board": ["b2.png"], "characters": ["Mona"],
             "acting": {"objective": "to finish the chapter before the kettle boils", "action": "reads faster",
                        "obstacle": "the kettle whistles", "thought_before": "eyes dart to the stove, blink",
                        "end_state": "book closed on her thumb, eyes on the stove",
                        "holds": [{"start_f": 60, "dur_f": 10, "moving": True}]}},
        ],
    }
    n = 0

    def ok(cond, label):
        nonlocal n
        n += 1
        if not cond:
            print(f"FAIL selftest {n}: {label}")
            raise SystemExit(1)
        print(f"ok   {n} {label}")

    ok(not [r for r in check(good) if r[0] == "FAIL"], "a well-directed shot list passes")
    bad = json.loads(json.dumps(good))
    s1, s2 = bad["shots"]
    s1["camera"]["motivation"] = ""
    s2["acting"]["objective"] = "nervous about the kettle"
    s2["acting"]["holds"] = [{"start_f": 50, "dur_f": 60, "moving": False}]
    s2["axis_side"] = "B"
    s2["start_f"] = 50
    del s2["acting"]["end_state"]
    bad["beats"] = [{"id": "B1", "turn": "push-in on the kettle", "state_in": 3, "state_out": 7, "deltas": [{"delta": 3, "agent": ""}]}]
    rows = check(bad)
    fails = " | ".join(m for lvl, _, m in rows if lvl == "FAIL")
    warns = " | ".join(m for lvl, _, m in rows if lvl == "WARN")
    for needle, label in (("no motivation", "unmotivated camera move fails (AN-045)"),
                          ("dead hold", "a 2.5 s frozen hold fails (CA-035)"),
                          ("180-degree", "an unmarked line cross fails (AN-036)"),
                          ("gap or overlap", "a frame gap between shots fails (AN-066)"),
                          ("end_state missing", "an action with no end state fails (EX-002)"),
                          ("does not add up", "a pressure curve that does not sum fails (EX-007)"),
                          ("no named agent", "a pressure change with no agent fails (EX-006)"),
                          ("camera is not a beat", "a camera term as a beat fails (EX-006)")):
        ok(needle in fails, label)
    ok("reads as a mood" in warns, "an emotion as objective warns, never blocks (CA-004)")
    calm = json.loads(json.dumps(good))
    calm["shots"][1]["acting"]["objective"] = "calm the crowd before the speech"
    ok(not [r for r in check(calm) if "mood" in r[2]], "'calm the crowd' is a doing, not a mood")
    ok(any("fps" in m for lvl, _, m in check({"project": {"fps": 0}, "shots": []}) if lvl == "FAIL"), "a zero fps fails")
    low = json.loads(json.dumps(good))
    low["project"]["fps"] = 12
    for s in low["shots"]:
        s["start_f"] //= 2
        s["dur_f"] //= 2
    ok(not [r for r in check(low) if r[0] == "FAIL"], "12 fps limited animation passes (warn only)")
    neutral = json.loads(json.dumps(good))
    n2 = neutral["shots"][1]
    n2.update({"axis_side": "N", "cross_line": "neutral"})
    third = json.loads(json.dumps(n2))
    third.update({"id": "Sc01_Sh03", "start_f": 72, "axis_side": "B", "cross_line": None})
    n2["transition_out"] = {"type": "cut"}
    neutral["shots"].append(third)
    neutral["project"]["target_seconds"] = 4
    ok(not any("180-degree" in m for _, _, m in check(neutral)), "a neutral on-axis shot frees the next shot to take the other side (AN-038)")
    junk = {"project": {"fps": 24}, "beats": [{"id": "B", "deltas": None}],
            "tracks": {"vo": [{"id": "v", "src": "x.wav", "dur_f": "48"}]},
            "shots": [{"id": "Sc01_Sh01", "start_f": 0, "dur_f": 24, "transition_out": "cut", "transition_in": "dissolve",
                       "characters": ["A"], "acting": {"holds": None, "expression_changes": None}}]}
    try:
        rows = check(junk)
        ok(any(r[0] == "FAIL" for r in rows), "malformed fields give findings, not a traceback")
    except Exception as e:  # noqa: BLE001 - the assertion is that nothing raises
        ok(False, f"malformed fields raised {type(e).__name__}: {e}")
    ar = json.loads(json.dumps(good))
    ar["project"]["lang"] = "ar"
    ar["tracks"]["vo"][0]["text"] = " ".join(["كلمة"] * 4)
    ok(not [r for r in check(ar) if "wpm" in r[2]], "Arabic VO at 120 wpm sits inside the 110-120 band")
    root = Path(__file__).resolve().parent.parent
    kb = "".join(f.read_text(encoding="utf-8") for f in (root / "kb").glob("0*.md"))
    known = set(re.findall(r"\*\*((?:CA|AN|RT|EX)-\d{3})\*\*", kb))
    cited = set()
    for f in (root / "SKILL.md", Path(__file__)):
        txt = f.read_text(encoding="utf-8")
        cited |= set(re.findall(r"\b(?:CA|AN|RT|EX)-\d{3}\b", txt))
        for a, b in re.findall(r"\b((?:CA|AN|RT|EX)-\d{3})\.\.((?:CA|AN|RT|EX)-\d{3})\b", txt):
            cited |= {f"{a[:3]}{i:03d}" for i in range(int(a[3:]), int(b[3:]) + 1)}
    ok(len(known) >= 300 and not cited - known, f"every cited KB id exists ({len(cited)} cited, missing {sorted(cited - known)})")
    if not shutil.which("ffmpeg"):
        print("skip animatic render: ffmpeg not on PATH")
        return 0
    d = Path(tempfile.mkdtemp(prefix="nj-ad-selftest-"))
    try:
        for name, col in (("b1.png", "red"), ("b2.png", "blue")):
            ff(["-f", "lavfi", "-i", f"color=c={col}:s=640x360", "-frames:v", "1", str(d / name)])
        ff(["-f", "lavfi", "-i", "sine=frequency=440:duration=2", str(d / "vo.wav")])
        out = animatic(good, d, d / "animatic.mp4")
        ok(frames(out) == 72, f"the animatic has exactly 72 frames at 24 fps (got {frames(out)})")
        dis = json.loads(json.dumps(good))
        dis["shots"][1].update({"start_f": 36, "transition_in": {"type": "dissolve", "dur_f": 12}})
        dis["shots"][0]["transition_out"] = {"type": "dissolve"}
        dis["project"]["target_seconds"] = 2.5
        ok(not [r for r in check(dis) if r[0] == "FAIL"], "a planned 12-frame dissolve overlap passes the gate")
        out2 = animatic(dis, d, d / "sub" / "dissolve.mp4")
        ok(frames(out2) == 60, f"the overlap animatic keeps the timeline length, 60 frames (got {frames(out2)})")
        pull = json.loads(json.dumps(good))
        pull["shots"][0]["camera"].update({"move": "pull-out", "from_scale": 1.0, "to_scale": 0.8})
        ok(frames(animatic(pull, d, d / "pull.mp4")) == 72, "a pull-out below scale 1 renders")
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print(f"selftest: {n} assertions ok")
    return 0


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--selftest":
        return selftest()
    if argv[0] not in ("check", "animatic") or len(argv) < 2:
        print(__doc__)
        return 2
    path = Path(argv[1])
    try:
        sl = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"FAIL {path}: {e}")
        return 1
    rows = check(sl if isinstance(sl, dict) else {})
    if argv[0] == "check":
        for lvl, where, msg in rows:
            print(f"{lvl} {where}: {msg}")
        fails = sum(r[0] == "FAIL" for r in rows)
        print(f"{'FAIL' if fails else 'PASS'} {path.name}: {fails} fail, {len(rows) - fails} warn")
        return 1 if fails else 0
    if any(r[0] == "FAIL" for r in rows):
        print("FAIL: run check first; an animatic is built only from a shot list that passes")
        return 1
    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv[:-1] else path.with_suffix(".animatic.mp4")
    print(f"OK {animatic(sl, path.parent, out)} ({frames(out)} frames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
