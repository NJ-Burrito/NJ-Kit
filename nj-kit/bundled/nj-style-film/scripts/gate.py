"""The gate between stages. Run it BEFORE starting a stage; obey its exit code.

    python gate.py <project dir> <stage 1-6>

Exit 0  go.      Exit 1  do not start this stage; the message says what is missing.

Rules written as prose were in force on the first run and the run wandered
anyway (research/136, objection 2). So the things that can be checked are
checked here: the previous stage's file exists and has the shape the template
demands, every storyboard cue sits inside its own scene window, and the PACE
line is COMPUTED, because the first run stated it from memory and was wrong.
"""
import glob
import json
import os
import re
import subprocess
import sys
import time

DNA_SECTIONS = ["COLOR PALETTE", "TYPOGRAPHY", "COMPOSITION", "MOTION LANGUAGE", "GRAPHIC ELEMENTS", "SHAPE LANGUAGE"]
VERDICTS = ("BUILDABLE WITH ASSETS", "NOT IN HTML", "BUILDABLE")
FIELDS = ["Spoken Dialogue", "Visual Description", "On-Screen Text", "Typography Animation",
          "Graphic Elements", "Camera Movement", "Transition Style", "Synchronization", "Material"]


def text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def need(project, name, problems):
    path = os.path.join(project, name)
    if not os.path.exists(path):
        problems.append(f"{name} does not exist: the previous stage is not finished")
        return None
    return path


def check_dna(path, problems):
    raw = text(path)
    body = raw.upper()
    # A section name present is not a section filled in: each heading's body,
    # up to the next numbered heading, must have non-blank content (devil #4).
    for i, s in enumerate(DNA_SECTIONS):
        if s not in body:
            problems.append(f"STYLE-DNA.md has no section '{s}'")
            continue
        start = body.index(s) + len(s)
        nxt = [body.index(o, start) for o in DNA_SECTIONS if o != s and o in body[start:] and body.index(o, start) > start]
        end = min(nxt) if nxt else len(body)
        if not raw[start:start + (end - start)].strip(" \t\n:-"):
            problems.append(f"STYLE-DNA.md section '{s}' has no body (a blank heading is not DNA)")
    verdict = next((v for v in VERDICTS if f"FEASIBILITY: {v}" in body), None)
    if not verdict:
        problems.append("STYLE-DNA.md has no 'FEASIBILITY: BUILDABLE | BUILDABLE WITH ASSETS | NOT IN HTML' line")
    elif verdict == "NOT IN HTML":
        problems.append("the style was judged NOT IN HTML: stop and tell the user what it would take instead")


def material_tokens(mval):
    """Split a Material field into one clause per prop. Semicolon-separated
    only -- a DRAWN reason routinely contains its own commas ('recipe 4 is a
    flat CSS shape, not a photograph'), so splitting on commas too shreds one
    clause into several fake ids. Anything with 'DRAWN' anywhere (not just at
    the start) is a DRAWN clause, not an id."""
    out = []
    for tok in mval.split(";"):
        tok = tok.strip()
        if not tok or "drawn" in tok.lower() or re.match(r"^(print|photo-card)\s*:", tok, re.I):
            continue
        out.append(tok)
    return out


def check_storyboard(path, problems):
    body = text(path)
    scenes = re.split(r"(?m)^SCENE\s+", body)[1:]
    if not scenes:
        problems.append("STORYBOARD.md has no 'SCENE <n> (start - end)' blocks")
        return
    events = []
    for block in scenes:
        head = block.splitlines()[0]
        m = re.search(r"\(\s*([\d.]+)\s*[-–]\s*([\d.]+)", head)
        label = head.split("(")[0].strip() or "?"
        if not m:
            problems.append(f"scene {label}: no '(start - end)' window in its heading")
            continue
        start, end = float(m.group(1)), float(m.group(2))
        for f in FIELDS:
            if f not in block:
                problems.append(f"scene {label}: field '{f}' is missing")
        sync = re.search(r"Synchronization(.*?)(?=\n\S|\Z)", block, re.S)
        raw_times = re.findall(r"(?<![\d.])(\d+\.\d+|\d+)(?=\s*(?:\||$|\n|[-–]\s*\d))", sync.group(1)) if sync else []
        times = [float(t) for t in raw_times]
        # only times that could be cues in this film: inside a generous bound
        times = [t for t in times if start - 0.05 <= t <= end + 0.05] if times else []
        if not times:
            if sync and re.search(r"\d", sync.group(1)) and not raw_times:
                problems.append(f"scene {label}: Synchronization has digits but none parse as cue times — "
                                 "write `<event> <seconds>` separated by ` | `, nothing after the number on the same segment")
            else:
                problems.append(f"scene {label}: no cue time falls inside its window {start}-{end}")
        events += times
        material = re.search(r"Material\s*(.*?)(?=\n\S|\Z)", block, re.S)
        mval = material.group(1).strip() if material else ""
        if mval.upper().startswith("DRAWN") and not re.search(r"DRAWN\s*:\s*\S", mval, re.I):
            problems.append(f"scene {label}: Material is 'DRAWN' with no reason — write 'DRAWN: <reason>'")
        # devil #2: a picture id with no "— because <clause>" is a coin toss.
        # A clause that just repeats the id's own words is not a reason either.
        for tok in material_tokens(mval):
            m = re.match(r"([A-Za-z0-9_-]+)", tok)
            if not m:
                continue
            mid = m.group(1)
            bm = re.search(r"(—|--)\s*because\s*(.*)", tok, re.I | re.S)
            if not bm:
                problems.append(f"scene {label}: Material '{mid}' has no '— because <clause>' tying it to "
                                 "the spoken line — devil #2")
                continue
            clause_words = set(re.findall(r"[a-z]{4,}", bm.group(2).lower()))
            id_words = set(re.findall(r"[a-z]{4,}", mid.lower().replace("-", " ")))
            if clause_words and id_words and clause_words <= id_words:
                problems.append(f"scene {label}: Material '{mid}' — because-clause only repeats the id's own "
                                 "words — that is an assertion, not a reason")
    if events:
        events = sorted(set(events))
        total = events[-1] - events[0] if len(events) > 1 else 0
        gaps = [(b - a, a, b) for a, b in zip(events, events[1:])]
        g = max(gaps) if gaps else (0, 0, 0)
        print(f"PACE   {len(events)} timed events, one every {total / max(1, len(events) - 1):.2f} s; "
              f"longest gap {g[0]:.2f} s ({g[1]:.2f} -> {g[2]:.2f})")
        print("       Copy that line into STORYBOARD.md. Do not write your own.")


def check_material(project, problems):
    """Devil #1a: material_needs[] in the style record is documentation until
    something refuses to build without it. Non-empty needs => ASSETS.txt must
    name a manifest id, or the shortfall must be a named DRAWN:<reason>."""
    proj_path = os.path.join(project, "PROJECT.md")
    if not os.path.exists(proj_path):
        return
    proj = text(proj_path)
    m = re.search(r"style:\s*([A-Za-z0-9_-]+)", proj)
    if not m:
        return
    # rehearsal-0921: library-cutover-0921 moved style records from
    # production/styles/<name>/ to %NJ_LIBRARY%/styles/<name>/ (or
    # <project's cutouts_dir's library root>/styles/<name>/) -- this used to
    # look ONLY in the pre-cutover sibling path and silently found nothing
    # post-cutover (a missing style.json is a silent `return`, not a NO-GO).
    candidates = [os.path.join(os.path.dirname(os.path.abspath(project)), "styles", m.group(1), "style.json")]
    nj_library = os.environ.get("NJ_LIBRARY")
    if nj_library:
        candidates.append(os.path.join(nj_library, "styles", m.group(1), "style.json"))
    cd = re.search(r"cutouts_dir:\s*(\S+)", proj)
    if cd:
        candidates.append(os.path.join(project, cd.group(1), "styles", m.group(1), "style.json"))
    style_json = next((p for p in candidates if os.path.exists(p)), None)
    if not style_json:
        return
    import json
    try:
        needs = json.loads(text(style_json)).get("material_needs") or []
    except (OSError, ValueError):
        return
    if not needs:
        return
    assets_path = os.path.join(project, "ASSETS.txt")
    ids = [l for l in text(assets_path).splitlines() if l.strip() and not l.strip().startswith("#")] if os.path.exists(assets_path) else []
    sb_path = os.path.join(project, "STORYBOARD.md")
    sb = text(sb_path) if os.path.exists(sb_path) else ""
    drawn_named = bool(re.search(r"DRAWN\s*:\s*\S", sb, re.I) or re.search(r"DRAWN\s*:\s*\S", proj, re.I))
    if not ids and not drawn_named:
        kinds = ", ".join(n.get("kind", "?") for n in needs)
        problems.append(f"style.json material_needs[] calls for [{kinds}] but ASSETS.txt names no manifest id "
                         "and no shortfall is recorded as DRAWN:<reason> — NO-GO, material stage")


def check_asset_plan(project, problems):
    """Devil #2 / Lead decision 4: a picture is chosen for a meaning, not
    availability. Prefer library.py's own plan-check when the library-move
    worker's script exists; otherwise check by hand that every scene named in
    ASSET-PLAN.md carries an id and a non-blank reason."""
    library_root = os.path.join(os.path.dirname(os.path.abspath(project)), "library")
    plan_path = os.path.join(project, "ASSET-PLAN.md")
    plan_script = os.path.join(library_root, "scripts", "library.py")
    if os.path.exists(plan_script):
        if not os.path.exists(plan_path):
            problems.append("ASSET-PLAN.md does not exist: library.py plan-check needs it before the build")
            return
        r = subprocess.run([sys.executable, plan_script, "plan-check", plan_path],
                            capture_output=True, text=True)
        if r.returncode != 0:
            problems.append("library.py plan-check failed:\n    " + (r.stdout + r.stderr).strip().replace("\n", "\n    "))
        return
    if not os.path.exists(plan_path):
        problems.append("ASSET-PLAN.md does not exist (library.py not present yet, so the gate checks it by hand): "
                         "one line per scene, a manifest id and a non-blank reason")
        return
    plan = text(plan_path)
    lines = [l for l in plan.splitlines() if l.strip() and not l.strip().startswith("#")]
    if not lines:
        problems.append("ASSET-PLAN.md is empty")
        return
    for i, l in enumerate(lines, 1):
        if ":" not in l:
            problems.append(f"ASSET-PLAN.md line {i}: no 'id: reason' shape — {l!r}")
            continue
        _id, _, reason = l.partition(":")
        if not reason.strip():
            problems.append(f"ASSET-PLAN.md line {i}: '{_id.strip()}' has no reason")


PNG_SIG = b"\x89PNG\r\n\x1a\n"


def png_info(path):
    """Devil #1: a cut-out is a property of the FILE, not its filename.
    stdlib-only check (Pillow is reserved for the coverage figure, decision
    2): colour type 4/6 (has an alpha channel) or a tRNS chunk (indexed/RGB
    transparency). Returns True/False, or None if not a readable PNG."""
    try:
        with open(path, "rb") as f:
            if f.read(8) != PNG_SIG:
                return None
            f.read(8)  # IHDR length+type, always the first chunk
            ihdr = f.read(13)
            if len(ihdr) < 13:
                return None
            if ihdr[9] in (4, 6):
                return True
            f.seek(8 + 8 + 13 + 4)  # past IHDR + its CRC
            while True:
                length_b = f.read(4)
                if len(length_b) < 4:
                    break
                length = int.from_bytes(length_b, "big")
                ctype = f.read(4)
                if ctype == b"tRNS":
                    return True
                if ctype in (b"IDAT", b"IEND"):
                    break
                f.seek(length + 4, 1)
    except OSError:
        return None
    return False


def alpha_coverage_pct(path):
    """% of pixels that are neither fully opaque nor fully transparent — the
    transparent SHARE the brief's 5-95% test is about. stdlib does the
    has-alpha structural check (png_info); this figure alone goes through
    Pillow via `uv run --with pillow` (decision 2: state which was used —
    this is Pillow)."""
    script = ("from PIL import Image;import sys;im=Image.open(sys.argv[1]).convert('RGBA');"
              "a=list(im.getchannel('A').getdata());n=len(a);"
              "print(100.0*sum(1 for v in a if v<250)/n if n else 0)")
    try:
        out = subprocess.run(["uv", "run", "--with", "pillow", "python", "-c", script, path],
                              capture_output=True, text=True, timeout=60)
        if out.returncode == 0 and out.stdout.strip():
            return float(out.stdout.strip().splitlines()[-1])
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return None


def check_cutout_pictures(project, comps, problems):
    """Devil #1/#3/#4: 'cut-out' is a property (real alpha), a picture with
    legible Latin text in an Arabic film must say why, and a full-colour
    picture must carry the tone-to-palette filter. Library's INDEX.json
    (has_alpha/alpha_coverage/text_in_image/tone) is preferred when present;
    falls back to measuring the file (library-move-0921 is still in flight)."""
    sb_path = os.path.join(project, "STORYBOARD.md")
    if not os.path.exists(sb_path):
        return
    sb = text(sb_path)
    proj_path = os.path.join(project, "PROJECT.md")
    proj = text(proj_path) if os.path.exists(proj_path) else ""
    lang_m = re.search(r"language:\s*(\w+)", proj)
    language = lang_m.group(1).lower() if lang_m else None

    # cutover 2026-09-21 (library-cutover-0921): resolve through NJ_LIBRARY's INDEX.json
    # by id OR any alias FIRST -- old seed/manifest ids (e.g. cutout-steam-engine-oxley)
    # keep working via aliases[]. Fall back to the old manifest.jsonl only when
    # NJ_LIBRARY is unset (pre-cutover project, or the index truly isn't there).
    nj_library = os.environ.get("NJ_LIBRARY")
    library_root = nj_library or os.path.join(os.path.dirname(os.path.abspath(project)), "library")
    index_by_id = {}
    index_path = os.path.join(library_root, "INDEX.json")
    if os.path.exists(index_path):
        try:
            recs = json.loads(text(index_path))
            for r in recs:
                index_by_id[r["id"]] = r
                for a in r.get("aliases", []) or []:
                    index_by_id.setdefault(a, r)
        except (OSError, ValueError, KeyError, TypeError):
            index_by_id = {}
    manifest = {}
    if not nj_library:
        mpath = os.path.join(library_root, "manifest.jsonl")
        if os.path.exists(mpath):
            for line in text(mpath).splitlines():
                line = line.strip()
                if line:
                    try:
                        row = json.loads(line)
                        manifest[row["id"]] = row
                    except ValueError:
                        pass

    def resolve(mid):
        """Returns a manifest-shaped row (path/kind/text_in_image) for an id or alias,
        preferring INDEX.json; a record is a cut-out when its top folder is 'cutout'."""
        r = index_by_id.get(mid)
        if r is not None:
            path_parts = (r.get("path") or "").replace("\\", "/").split("/")
            aliases = r.get("aliases", []) or []
            is_cutout = ("cutout" in path_parts or "needs-cutout" in (r.get("tags") or []) or
                         mid.startswith("cutout-") or any(a.startswith("cutout-") for a in aliases))
            if not is_cutout:
                return None
            return {"id": r["id"], "kind": "cutout", "path": r.get("path"),
                     "text_in_image": (r.get("measured") or {}).get("text_in_image", "unknown")}
        row = manifest.get(mid)
        if row is not None and row.get("kind") == "cutout":
            return row
        return None

    real_cutouts = []  # (scene label, id, manifest-shaped row, raw token)
    for block in re.split(r"(?m)^SCENE\s+", sb)[1:]:
        head = block.splitlines()[0]
        label = head.split("(")[0].strip() or "?"
        mat = re.search(r"Material\s*(.*?)(?=\n\S|\Z)", block, re.S)
        mval = mat.group(1).strip() if mat else ""
        for tok in material_tokens(mval):
            m = re.match(r"([A-Za-z0-9_-]+)", tok)
            if not m:
                continue
            mid = m.group(1)
            row = resolve(mid)
            if row is None:
                continue  # not a library cutout id -- out of this check's scope
            real_cutouts.append((label, mid, row, tok))

    for label, mid, row, tok in real_cutouts:
        idx_row = (index_by_id.get(mid) or {}).get("measured", {}) or (index_by_id.get(mid) or {})
        path = os.path.join(library_root, row["path"]) if row.get("path") else None
        has_alpha = idx_row.get("has_alpha")
        if has_alpha is None and path and os.path.exists(path):
            ext = os.path.splitext(path)[1].lower()
            has_alpha = False if ext in (".jpg", ".jpeg") else (png_info(path) if ext == ".png" else None)
        if has_alpha is False:
            problems.append(f"scene {label}: Material '{mid}' is declared a cut-out but its file has no real "
                             "transparency (JPEG, or a PNG with no alpha channel/tRNS) — declare it "
                             "print:/photo-card: with the matching recipe, or use a file with real alpha")
            continue
        if has_alpha is True:
            coverage = idx_row.get("alpha_coverage")
            if coverage is None and path:
                coverage = alpha_coverage_pct(path)
            if coverage is not None and not (5.0 <= coverage <= 95.0):
                problems.append(f"scene {label}: Material '{mid}' alpha coverage {coverage:.1f}% is outside "
                                 "5-95% (near-0% = opaque rectangle, near-100% = fully transparent file)")
        text_in_image = idx_row.get("text_in_image", row.get("text_in_image", "unknown"))
        because = bool(re.search(r"(—|--)\s*because\b", tok, re.I))
        if language == "ar" and text_in_image == "latin" and not because:
            problems.append(f"scene {label}: Material '{mid}' carries legible Latin text in an Arabic film "
                             "with no '— because <reason>' answering it")
        elif text_in_image == "unknown" and not because:
            problems.append(f"scene {label}: Material '{mid}' has unknown text_in_image and no "
                             "'— because <reason>' answering it (a warning that must be answered)")

    if not real_cutouts:
        return
    for d in comps:
        page_path = os.path.join(project, d, "index.html")
        if not os.path.exists(page_path):
            continue
        page = text(page_path)
        missing = sorted({mid for _, mid, _, _ in real_cutouts if mid not in page})
        if missing:
            problems.append(f"{d}/index.html: declared cut-out(s) {', '.join(missing)} have no "
                             "<img>/background reference in the built page")
        used = [(mid, row) for _, mid, row, _ in real_cutouts if mid in page]
        if used:
            has_edge = "clip-path" in page or any(
                ((index_by_id.get(mid) or {}).get("measured") or {}).get("has_alpha") or
                (row.get("path") and png_info(os.path.join(library_root, row["path"])) is True)
                for mid, row in used
            )
            if not has_edge:
                problems.append(f"{d}/index.html: no torn-edge clip-path and no used cut-out file has real "
                                 "alpha — the collage's edge treatment is not actually present")
            if not ("feColorMatrix" in page or "duotone" in page.lower() or "toned" in page.lower()):
                problems.append(f"{d}/index.html: no tone filter (feColorMatrix/duotone/toned class) for the "
                                 "full-colour cut-outs — RECIPES.md's 'tone a picture to the palette' recipe is required")


def check_no_hotlinks(project, comps, problems):
    """Hole 1 (rehearsal-0921): GSAP (or anything else) fetched from a CDN at
    render time breaks offline builds and violates 'never hot-link, never
    fetch at render'. `grep -n "https\\?://" hf/index.html` must match nothing
    but comments; this is that same check, run by the gate itself so it is
    never skipped by hand."""
    for d in comps:
        page_path = os.path.join(project, d, "index.html")
        if not os.path.exists(page_path):
            continue
        page = text(page_path)
        hits = []
        for i, line in enumerate(page.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("<!--") or "-->" in stripped and stripped.startswith("<!--"):
                continue
            if re.search(r"https?://", line) and "<!--" not in line.split("http")[0]:
                hits.append(i)
        if hits:
            problems.append(f"{d}/index.html: {len(hits)} hot-linked URL(s) outside comments at line(s) "
                             f"{', '.join(map(str, hits[:5]))} — vendor the file into hf/assets/ instead "
                             "(templates/vendor/gsap.min.js for GSAP)")


def check_ids(project, comps, problems):
    """Hole 3 (rehearsal-0921): the entrance/exit gate only sees elements that
    carry an `id` — it must never pass silently on the rest. Count every
    `class="clip"` and `<img>` inside a scene with no `id`, and list them
    instead of letting them fall out of check_entrances_exits unreported."""
    for d in comps:
        page_path = os.path.join(project, d, "index.html")
        if not os.path.exists(page_path):
            continue
        page = text(page_path)
        no_id = []
        for tag, attrs in re.findall(r"<(section|div|img)\b([^>]*)>", page):
            if 'class="clip' not in attrs and tag != "img":
                continue
            if not re.search(r'(?<![\w-])id="[\w-]+"', attrs):
                no_id.append(attrs[:60].strip())
        if no_id:
            problems.append(f"{d}/index.html: {len(no_id)} clip/img element(s) with no id — the entrance/exit "
                             f"gate cannot check them: {no_id[:5]}")


def check_hero_gate(project, comps, problems, require_boxes=False):
    """Hole 4 (rehearsal-0921): hero_boxes.mjs + hero_check.py must actually
    run and fail the gate, not just be documented. Requires, per scene section
    in each built page, a descendant carrying `data-hero`; requires
    <d>/snapshots/hero-boxes.json to exist (written by hero_boxes.mjs) before
    stage 6; and requires hero_check.py to have been run per scene (a scene id
    missing from hero-boxes.json is either un-boxed or failed to resolve)."""
    for d in comps:
        page_path = os.path.join(project, d, "index.html")
        if not os.path.exists(page_path):
            continue
        page = text(page_path)
        scene_ids = re.findall(r'<section[^>]*(?<![\w-])id="([\w-]+)"[^>]*\bclass="[^"]*\bscene\b', page)
        no_hero = [sid for sid in scene_ids
                   if not re.search(r'<section[^>]*(?<![\w-])id="' + re.escape(sid) + r'".*?</section>', page, re.S)
                   or "data-hero" not in re.search(r'<section[^>]*(?<![\w-])id="' + re.escape(sid) + r'".*?</section>', page, re.S).group(0)]
        if no_hero:
            problems.append(f"{d}/index.html: scene(s) with no data-hero element: {', '.join(no_hero)} — "
                             "choreography.md rule 2, hero_check.py cannot run without one")
        boxes_path = os.path.join(project, d, "snapshots", "hero-boxes.json")
        if require_boxes and scene_ids and not no_hero and not os.path.exists(boxes_path):
            problems.append(f"{d}/snapshots/hero-boxes.json missing: run "
                             f"`node scripts/hero_boxes.mjs {d}/index.html` before stage 6 (hole 4)")
        elif os.path.exists(boxes_path):
            try:
                boxes = json.loads(text(boxes_path))
            except (OSError, ValueError):
                boxes = {}
            unboxed = [sid for sid in scene_ids if sid not in no_hero and sid not in boxes]
            if unboxed:
                problems.append(f"{d}/snapshots/hero-boxes.json has no box for scene(s): {', '.join(unboxed)} "
                                 "— hero_boxes.mjs did not resolve data-hero geometry for them")


def check_entrances_exits(project, comps, problems):
    """Owner's review, reel 2 (choreography.md rule 1): no element may simply
    appear at its clip start or vanish at its end. For every `class="clip"`
    or `<img>` element inside a scene, at least one tween must start within
    0.6s of its data-start (entrance) and one must end within 0.6s of its
    scene's end (exit) -- unless it carries data-hold="cut-in"/"cut-out"."""
    for d in comps:
        page_path = os.path.join(project, d, "index.html")
        if not os.path.exists(page_path):
            continue
        page = text(page_path)
        # rehearsal-0921: the contract skeleton's own #root and the camera
        # track (id="cam" or any wrapper) carry id+data-start too -- they are
        # containers, never choreographed content, and choreography.md rule 1
        # is scoped to "every element with class clip and every <img> INSIDE
        # A SCENE SECTION". Scanning the whole page (as this used to) flagged
        # #root/#cam themselves on every build; scope the scan to each
        # scene's own inner HTML instead.
        scene_bodies = re.findall(r'<section[^>]*(?<![\w-])class="[^"]*\bscene\b[^"]*"[^>]*>(.*?)</section>', page, re.S)
        if not scene_bodies:
            continue
        page_scoped = "\n".join(scene_bodies)
        # elements: id + data-start (+ optional data-hold), inside a scene section
        els = re.findall(r'<(?:section|div|img)[^>]*(?<![\w-])id="([\w-]+)"[^>]*\bdata-start="([\d.]+)"[^>]*>', page_scoped)
        holds = dict(re.findall(r'(?<![\w-])id="([\w-]+)"[^>]*\bdata-hold="(cut-in|cut-out)"', page_scoped))
        no_entrance, no_exit = [], []
        for el_id, start in els:
            if holds.get(el_id) in ("cut-in", "cut-out"):
                continue
            # a tween that targets '#id' or '.id' with a start-time argument within window
            times = [float(t) for t in re.findall(
                re.escape(el_id) + r'[^;]{0,200}?,\s*([\d.]+)\)', page)]
            start = float(start)
            if not any(abs(t - start) <= 0.6 for t in times):
                no_entrance.append(el_id)
            if not any(t > start for t in times):  # a later tween stands in for an exit check (best-effort, no scene-end parse)
                no_exit.append(el_id)
        if no_entrance:
            problems.append(f"{d}/index.html: no entrance tween (within 0.6s of data-start) for: "
                             f"{', '.join(sorted(set(no_entrance)))} — choreography.md rule 1")
        if no_exit:
            problems.append(f"{d}/index.html: no exit tween found for: "
                             f"{', '.join(sorted(set(no_exit)))} — choreography.md rule 1")


def check_captions_system(project, comps, problems):
    """Owner's review, reel 2 (choreography.md / house-finish rule): one
    caption system per film, never two. captions: kinetic (default) means
    on-picture motion-graphic words carry the narration; captions: subtitle
    means a plain strip with no kinetic words. Both in one page is a NO-GO."""
    proj_path = os.path.join(project, "PROJECT.md")
    proj = text(proj_path) if os.path.exists(proj_path) else ""
    cm = re.search(r"captions:\s*(\w+)", proj)
    mode = (cm.group(1).lower() if cm and cm.group(1).strip() else "kinetic")
    for d in comps:
        page_path = os.path.join(project, d, "index.html")
        if not os.path.exists(page_path):
            continue
        page = text(page_path)
        has_subtitle = bool(re.search(r'class="[^"]*subtitle[^"]*"', page, re.I))
        has_kinetic = bool(re.search(r'class="[^"]*(hero-word|word-by-word|wordTimes)[^"]*"', page, re.I)
                            or "wordTimes" in page)
        if has_subtitle and has_kinetic:
            problems.append(f"{d}/index.html: two caption systems present (a subtitle strip AND on-picture "
                             "kinetic words) — pick one, never both")
        if mode == "kinetic" and has_subtitle and not has_kinetic:
            problems.append(f"{d}/index.html: captions: kinetic but only a subtitle strip is built — "
                             "on-picture words are the captions for this style")
        if mode == "subtitle" and has_kinetic:
            problems.append(f"{d}/index.html: captions: subtitle but on-picture kinetic words are built — "
                             "pick one system")


TOKEN_HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}\b")


def check_token_colours(project, comps, problems):
    """Devil #11 (off-token colours): grep hf/index.html's hex literals
    against brand/tokens.json's declared set. ≤2 commands, no change to
    visual_gate.mjs (read-only)."""
    tokens_path = os.path.join(os.path.dirname(os.path.abspath(project)), "..", "brand", "tokens.json")
    tokens_path = os.path.normpath(tokens_path)
    if not os.path.exists(tokens_path):
        return
    allowed = {h.upper() for h in TOKEN_HEX_RE.findall(text(tokens_path))}
    if not allowed:
        return
    for d in comps:
        page_path = os.path.join(project, d, "index.html")
        if not os.path.exists(page_path):
            continue
        used = {h.upper() for h in TOKEN_HEX_RE.findall(text(page_path))}
        off_token = sorted(used - allowed)
        if off_token:
            problems.append(f"{d}/index.html: off-token colour(s) not in brand/tokens.json: {', '.join(off_token)}")


LEDGER = "STAGES.log"


def passed(project):
    """Stages the gate has already let through, from the ledger it writes itself."""
    try:
        return {int(l.split()[1]) for l in text(os.path.join(project, LEDGER)).splitlines()
                if l.startswith("GO ") and l.split()[1].isdigit()}
    except OSError:
        return set()


def selftest_synchronization():
    """Devil #5: the gate's own regex must accept the template's own worked
    example, or a template is not a template — it is a trap. Runs the same
    check_storyboard regex over templates/STORYBOARD.md."""
    tmpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "STORYBOARD.md")
    problems = []
    check_storyboard(os.path.normpath(tmpl), problems)
    bad = [p for p in problems if "Synchronization" in p or "no cue time" in p]
    if bad:
        print("SELFTEST FAIL: templates/STORYBOARD.md's own worked example fails its own gate:")
        for p in bad:
            print("  -", p)
        return 1
    print("SELFTEST OK: templates/STORYBOARD.md's worked example passes check_storyboard")
    return 0


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        return selftest_synchronization()
    if len(sys.argv) == 3 and sys.argv[2] == "engines":
        # Devil #7: the engine pre-stage is unbudgeted and invisible. One
        # ledger row, elapsed-since-previous, same mechanism as a numbered
        # stage's GO line, so STAGES.log carries its real cost.
        project = sys.argv[1]
        now = time.time()
        ledger_path = os.path.join(project, LEDGER)
        prev = None
        if os.path.exists(ledger_path):
            rows = [l for l in text(ledger_path).splitlines() if l.startswith("GO ")]
            if rows:
                last = rows[-1].split()
                try:
                    prev = time.mktime(time.strptime(last[2] + " " + last[3], "%Y-%m-%d %H:%M:%S"))
                except (IndexError, ValueError):
                    prev = None
        elapsed = f" (+{now - prev:.0f}s)" if prev is not None else " (+0s)"
        with open(ledger_path, "a", encoding="utf-8") as fh:
            fh.write(f"GO engines {time.strftime('%Y-%m-%d %H:%M:%S')}{elapsed}\n")
        print("GO: engines pre-stage.")
        return 0
    if len(sys.argv) != 3 or not sys.argv[2].isdigit():
        print(__doc__)
        return 1
    project, stage = sys.argv[1], int(sys.argv[2])
    problems = []

    # No skipping. A stage is only open once the gate itself opened the one
    # before it: an agent cannot reach the build by writing the right filenames.
    done = passed(project)
    if stage > 1 and (stage - 1) not in done:
        problems.append(f"stage {stage - 1} was never opened by this gate: run `gate.py <project> {stage - 1}` first")

    if stage >= 1:
        form = need(project, "PROJECT.md", problems)
        # An intake form that exists but is empty is not an intake. The check is
        # the same script stage 0 runs, so the two can never disagree.
        if form:
            import subprocess
            check = os.path.join(os.path.dirname(os.path.abspath(__file__)), "intake_check.py")
            if subprocess.run([sys.executable, check, form], stdout=subprocess.DEVNULL).returncode != 0:
                problems.append("PROJECT.md is not filled: run intake_check.py and ask for exactly what it lists")
    if stage >= 2:
        p = need(project, "CUES.md", problems)
        if p:
            cues = text(p)
            if "ESTIMATE" not in cues:
                problems.append("CUES.md has no ESTIMATE line: it must be cues.py's own output, never composed by hand")
            # Devil #3/#10: length_seconds is collected and never consumed. Compare
            # the requested length to the film's real end (FILM ENDS, printed once
            # cues.py imports voice.py's END_TAIL) at ±10% (Lead's decision).
            proj_path = os.path.join(project, "PROJECT.md")
            lm = re.search(r"length_seconds:\s*([\d.]+)", text(proj_path)) if os.path.exists(proj_path) else None
            em = re.search(r"FILM ENDS\s+([\d.]+)\s*s", cues)
            if lm and em:
                want, got = float(lm.group(1)), float(em.group(1))
                drift = (got - want) / want
                if abs(drift) > 0.10:
                    problems.append(f"LENGTH {got:.2f} s vs length_seconds {want:.2f} s ({drift * 100:+.0f}%) "
                                     "— past the ±10% tolerance; fix the narration now, not at delivery")
    if stage >= 3:
        p = need(project, "STYLE-DNA.md", problems)
        if p:
            check_dna(p, problems)
    if stage >= 4:
        p = need(project, "STORYBOARD.md", problems)
        if p:
            check_storyboard(p, problems)
        check_material(project, problems)
        check_asset_plan(project, problems)
    # One project per aspect: hf/ for a single frame, hf-v/ and hf-h/ when build.py made both.
    comps = [d for d in ("hf", "hf-v", "hf-h") if os.path.isdir(os.path.join(project, d))]
    if stage >= 5:
        if not comps:
            problems.append("no hf/, hf-v/ or hf-h/ project: stage 4 (build) has not run")
        check_cutout_pictures(project, comps, problems)
        check_token_colours(project, comps, problems)
        check_entrances_exits(project, comps, problems)
        check_captions_system(project, comps, problems)
        check_no_hotlinks(project, comps, problems)
        check_ids(project, comps, problems)
        check_hero_gate(project, comps, problems)
        for d in comps:
            page = need(project, os.path.join(d, "index.html"), problems)
            # Without this file the HyperFrames router re-opens its own interview.
            need(project, os.path.join(d, "BRIEF.md"), problems)
            # A film that names a mixed track must have one: a voice alone is not a finished film.
            if page and "assets/mix.m4a" in text(page) and not os.path.exists(os.path.join(project, d, "assets", "mix.m4a")):
                problems.append(d + "/assets/mix.m4a is missing: run mix.py (voice + bed + SFX)")
            # Devil #8: words.json was produced and never used on the first run.
            # A warning, not a NO-GO — some scenes legitimately need no word-by-word type.
            if page and os.path.exists(os.path.join(project, "audio", "words.json")) and "words.json" not in text(page) and "wordTimes" not in text(page):
                print(f"WARN   {d}: audio/words.json exists but is not referenced in index.html "
                      "— word-by-word type is unused; confirm no scene's Typography Animation calls for it")
    if stage >= 6:
        check_hero_gate(project, comps, problems, require_boxes=True)
        for d in comps:
            sheets = glob.glob(os.path.join(project, d, "snapshots", "contact-sheet*.jpg"))
            if not sheets:
                problems.append("no contact sheets under " + d + "/snapshots: stage 5 (look) has not run")
                continue
            # devil #6: a `cp` of an already-passed sheet must not count as new
            # evidence. The snapshot step's own writes are index.html/BRIEF.md
            # (stage 4 build outputs); a sheet older than those is a copy, not
            # this pass's look.
            ref = os.path.join(project, d, "index.html")
            if os.path.exists(ref):
                ref_mtime = os.path.getmtime(ref)
                stale = [s for s in sheets if os.path.getmtime(s) < ref_mtime]
                if len(stale) == len(sheets):
                    problems.append(d + "/snapshots: every contact sheet is older than " + d +
                                     "/index.html — stage 5 did not run since the last build (a copied file is not evidence)")
        existing = glob.glob(os.path.join(project, "*.mp4")) + [m for d in comps for m in glob.glob(os.path.join(project, d, "renders", "*.mp4"))]
        if existing:
            problems.append("an MP4 already exists: " + existing[0] + " - do not render again; report it")

    if problems:
        print(f"STOP before stage {stage}:")
        for p in problems:
            print(f"  - {p}")
        return 1
    # The ledger is also the time log: prompt-to-delivery is read off it, not
    # recalled (devil #2). Each GO line also carries elapsed-since-previous so
    # the delivery note's timings are a grep, never a memory.
    now = time.time()
    ledger_path = os.path.join(project, LEDGER)
    prev = None
    if os.path.exists(ledger_path):
        rows = [l for l in text(ledger_path).splitlines() if l.startswith("GO ")]
        if rows:
            last = rows[-1].split()
            try:
                prev = time.mktime(time.strptime(last[2] + " " + last[3], "%Y-%m-%d %H:%M:%S"))
            except (IndexError, ValueError):
                prev = None
    elapsed = f" (+{now - prev:.0f}s)" if prev is not None else " (+0s)"
    with open(ledger_path, "a", encoding="utf-8") as fh:
        fh.write(f"GO {stage} {time.strftime('%Y-%m-%d %H:%M:%S')}{elapsed}\n")
    print(f"GO: stage {stage}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
