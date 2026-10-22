#!/usr/bin/env python3
"""check_teach.py -- does a page teach, and is its practice bank honest? (stdlib only). PYTHONUTF8=1 assumed.

    check_teach.py [page.md ...]       pages of the teaching kinds (default: every such page)
    check_teach.py --path FILE         a mentor path: hours line, weekly minutes, "X of Y" targets, ready-when clauses
    check_teach.py --selftest

Project = BOOK_ROOT env or cwd; book.json: pages, practice (bank folder, default "practice"), kinds,
objective_id (regex, or null), optional teach {"kinds": [...], "technique_section": "Core concepts",
"technique_level": 4, "objectives_section": "Syllabus map", "path": "<file for --path>"}.
Teaching checks run on kinds certification and topic unless teach.kinds says otherwise.

Per page (bank = <practice>/<slug>.md, keys in its `## Answer key` section or <slug>.key.md):
  * objectives: ids found by `objective_id` in the objectives section, each anchored `{#id}` in the page;
    with objective_id null they are generated `<slug>-<n>` from the "By the end you can" box (no box = FAIL,
    never skipped). Each objective needs >= 1 bank question.
  * each question has id, objective, level (K1..), a basis (`KB#n` verified, or `concept: §anchor` that exists
    on the page) and a key kept apart from the stem; the key letter is one of the options.
  * `calc:` lines that are pure arithmetic are evaluated safely (ast: numbers and + - * / only) and the result
    must appear in the keyed option's text; other calc lines are skipped and counted.
  * technique headings (levels 3-4 under "Core concepts") that name a K3+ / applied objective id carry *Worked example.*,
    *Try it.*, *Now alone.*; headings naming no objective id (chapter headings) are ignored.
Bank item quality (G1): over the items with a single-letter key and >= 3 options (>= teach.min_items, default 8 of them) the
KEYED option may be the strictly longest one in at most teach.longest_max (0.40) of the items, and at most teach.key_ratio_share
(0.25) of the keys may be >= 1.5x the next-longest option -- "pick the longest" must not pass an exam. Prints the format mix and both rates.
Item grammar (G2-G4): keys and `why-not:` live in <slug>.key.md only (not under the stem, not in an "Answer key" section of the questions
file); `type:` mcq | multi(select N) | matching | roman | not-stem | essay (an essay is level K5/K6, has no options and needs `rubric:` lines);
one objective per item unless a `lo_group:` line names the official group. An objective is covered by a bank item, a `[obj: ID]`
tag (recall prompt, drill) or a Try-it / Now-alone block under the heading that names it. A page with a recall sheet ends with
`## Recall answers`. `--resemble FILE...` (G5): no bank item may share >= 35 % of its 5-word shingles with the given sample-exam texts.
Prints one line per page; exit 0 ok, 1 any failure.
"""
import ast, json, math, os, re, sqlite3, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_pages as cp  # profiles, bank parser, config loading
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = cp.ROOT
MARKERS = cp.FADING
ARITH = re.compile(r"^[\d\s+\-*/×÷().%]+$")


def teach_kinds(cfg):
    return set((cfg.get("teach") or {}).get("kinds") or [k for k, p in cp.PROFILES.items() if p["teach"]])


def sections(text):
    """[(level, heading_text, body_text)] in order."""
    ms = list(re.finditer(r"^(#{1,6})\s+(.+?)\s*$", cp.mask_fences(text), re.M))  # headings are found outside code fences only; bodies are cut from the real text
    return [(len(m.group(1)), m.group(2), text[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(text)]) for i, m in enumerate(ms)]


def gh_slug(h):
    return re.sub(r"\s+", "-", re.sub(r"[^\w\s-]", "", re.sub(r"\{#[^}]*\}", "", h).lower()).strip())


def page_anchors(text):
    out = set(re.findall(r"\{#([^}\s]+)\}", text)) | set(re.findall(r'id="([^"]+)"', text))
    return out | {gh_slug(h) for _, h, _ in sections(text)}


def objectives(cfg, slug, text):
    """-> ({id: level_text}, generated?, error|None). level_text is the line the id sits on."""
    rx = cfg.get("objective_id")
    t = cfg.get("teach") or {}
    if rx:
        want = (t.get("objectives_section") or "syllabus map").lower()
        body = next((b for _, h, b in sections(text) if want in h.lower()), text)
        out = {}
        for ln in body.split("\n"):
            for m in re.finditer(rx, ln):
                out.setdefault(m.group(0), ln)
        return out, False, None if out else f"no objective ids matching /{rx}/ found"
    m = re.search(r"by the end you can", text, re.I)
    if not m:
        return {}, True, "objective_id is null and the page has no 'By the end you can' box (ids are generated <slug>-<n> from it)"
    items = []
    for ln in text[m.end():].split("\n")[1:]:
        if re.match(r"^\s*>?\s*(?:[-*+]|\d+\.)\s+\S", ln):
            items.append(ln)
        elif items and (not ln.strip().lstrip(">").strip() or ln.startswith("#")):
            break
    return {f"{slug}-{i}": ln for i, ln in enumerate(items, 1)}, True, None if items else "the 'By the end you can' box has no list items"


def applied(line):
    m = re.search(r"\bK([1-6])\b", line)
    return (int(m.group(1)) >= 3) if m else bool(re.search(r"\bapplied\b", line, re.I))


def safe_calc(expr):
    """Value of a pure-arithmetic string, or None if it is not one. ast only: no names, no calls."""
    e = expr.split("=")[0].strip().replace("×", "*").replace("÷", "/")
    if not e or not ARITH.match(e):
        return None
    e = re.sub(r"(\d+(?:\.\d+)?)\s*%", r"(\1/100)", e)
    try:
        tree = ast.parse(e, mode="eval")
    except SyntaxError:
        return None

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
            return n.value
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            v = ev(n.operand)
            return -v if isinstance(n.op, ast.USub) else v
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            a, b = ev(n.left), ev(n.right)
            return a + b if isinstance(n.op, ast.Add) else a - b if isinstance(n.op, ast.Sub) else a * b if isinstance(n.op, ast.Mult) else a / b
        raise ValueError("not arithmetic")
    try:
        return ev(tree)
    except ValueError:
        return None  # an operator outside + - * / (e.g. **): not ours to evaluate, skipped and counted
    except ZeroDivisionError:
        return float("nan")  # arithmetic, but undefined: reported as a failure


def in_text(value, text):
    """Does a plain number equal to `value` occur in the text? Section numbers such as 4.2.1 are not numbers."""
    flat = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)
    return any(abs(float(t) - value) < 0.005 for t in re.findall(r"(?<![\d.])\d+(?:\.\d+)?(?![\d.]*\d)", flat))


TYPE_RE = cp.TYPE_RE
ESSAY_LEVELS = ("K5", "K6")


def item_stats(bank, longest_max=0.40, ratio_share=0.25, min_items=8):
    """G1: how guessable is the bank from option length alone? -> dict(types, eligible, longest, ratio, longest_ids, flagged_ids, fail)."""
    types = {}
    longest_ids, flagged_ids, eligible = [], [], 0
    for q in bank["questions"]:
        types[(q.get("type") or "mcq").split("(")[0].lower()] = types.get((q.get("type") or "mcq").split("(")[0].lower(), 0) + 1
        key = bank["keys"].get(q["id"], "")
        if len(q["options"]) < 3 or not re.fullmatch(r"[a-h]", key or "") or key not in q["options"]:
            continue
        eligible += 1
        kl = len(q["options"][key])
        other = max((len(t) for k, t in q["options"].items() if k != key), default=0)
        if kl > other:
            longest_ids.append(q["id"])
        if other and kl >= 1.5 * other:
            flagged_ids.append(q["id"])
    fail = []
    if eligible >= min_items:
        if len(longest_ids) / eligible > longest_max:
            fail.append(f"the keyed option is the longest in {len(longest_ids)}/{eligible} items ({len(longest_ids) / eligible:.0%} > {longest_max:.0%}): "
                        f"'pick the longest' would score {len(longest_ids) / eligible:.0%}")
        if len(flagged_ids) / eligible > ratio_share:
            fail.append(f"the key is >= 1.5x the next option in {len(flagged_ids)}/{eligible} items ({len(flagged_ids) / eligible:.0%} > {ratio_share:.0%}): {flagged_ids[:5]}")
    return dict(types=types, eligible=eligible, longest=len(longest_ids), ratio=len(flagged_ids), longest_ids=longest_ids, flagged_ids=flagged_ids, fail=fail)


def mix_text(stats):
    t = " ".join(f"{k}={v}" for k, v in sorted(stats["types"].items()))
    e = stats["eligible"]
    return f"types[{t}] longest_key={stats['longest']}/{e} key>=1.5x={stats['ratio']}/{e}"


def page_covered(page_text, objs):
    """G3: objectives covered OUTSIDE the bank: `[obj: ID, ID]` tags (recall prompts, drills), and a Try-it / Now-alone block with a
    body under the heading that names the objective."""
    text = re.sub(r"<!--.*?-->", "", page_text, flags=re.S)
    text = re.sub(r"^```.*?^```", "", text, flags=re.S | re.M)
    cov = set()
    for m in re.finditer(r"\[obj:\s*([^\]]+)\]", text, re.I):
        cov |= {x.strip() for x in m.group(1).split(",") if x.strip()}
    for lv, h, sub_ in subtrees(text):
        named = [o for o in objs if o in h]
        if named:
            got = marker_bodies(sub_)
            if got.get("Try it", "").strip() or got.get("Now alone", "").strip():
                cov |= set(named)
    return cov


def check_recall(text):
    """G2: a recall sheet keeps its answers in a separate `## Recall answers` section at the end of the page."""
    secs = [(lv, h) for lv, h, _ in subtrees(text) if lv == 2]
    recall = [h for lv, h in secs if re.search(r"recall", h, re.I) and not re.search(r"recall answers", h, re.I)]
    if not recall:
        return []
    errs = []
    if not secs or not re.search(r"recall answers", secs[-1][1], re.I):
        errs.append("a recall sheet needs `## Recall answers` as the LAST section of the page (answers apart from the prompts)")
    for lv, h, body in subtrees(text):
        if lv == 2 and re.search(r"recall", h, re.I) and not re.search(r"recall answers", h, re.I):
            if re.search(r"(?mi)^\s*(?:[-*]\s*)?(?:answer|ans)\s*[:=\u2192-]", body):
                errs.append("answers sit inside the recall prompts; move them to `## Recall answers`")
                break
    return errs


def check_bank(slug, bank, objs, page_text, verified, cfg=None):
    """-> (errors, skipped_calc_count). Never raises: a question it cannot parse is a FAIL line."""
    errs, skipped = [], 0
    t = (cfg or {}).get("teach") or {}
    qs = bank["questions"]
    anchors = page_anchors(page_text)
    seen = set()
    if bank.get("keys_inline"):
        errs.append(f"answer keys sit in the questions file; move them (and every why-not) to {slug}.key.md")
    for q in qs:
        w = f"{q['id']}"
        if q["id"] in seen:
            errs.append(f"{w}: duplicate question id")
        seen.add(q["id"])
        if not q["objective"]:
            errs.append(f"{w}: no objective")
        tm = TYPE_RE.match(q.get("type") or "mcq")
        if not tm:
            errs.append(f"{w}: type '{q.get('type')}' is not mcq | multi(select N) | matching | roman | not-stem | essay")
        essay = bool(tm) and tm.group(1).lower() == "essay"
        if not re.match(r"K[1-6]\b", q["level"]):
            errs.append(f"{w}: level '{q['level']}' is not K1..K6")
        elif essay and q["level"][:2] not in ESSAY_LEVELS:
            errs.append(f"{w}: an essay is a K5/K6 item, not {q['level'][:2]}")
        if q["inline_key"]:
            errs.append(f"{w}: key sits beside the stem (keep it in {slug}.key.md)")
        elif q["near_key"]:
            errs.append(f"{w}: key sits within {cp.NEAR} lines of its stem (put the Answer key in {slug}.key.md)")
        if q.get("why_not_in_stem"):
            errs.append(f"{w}: why-not sits under the stem; it gives the answer away -- move it to {slug}.key.md")
        if q.get("calc_in_stem"):
            errs.append(f"{w}: calc sits under the stem; it gives the method away -- move it to the question's block in {slug}.key.md (move_calc.py --apply)")
        objs_q = [o.strip() for o in q["objective"].split(",") if o.strip()]
        if len(objs_q) > 1 and not q.get("lo_group"):
            errs.append(f"{w}: {len(objs_q)} objectives on one item {objs_q[:3]}: tag what the item tests (one), or add a `lo_group:` line naming the official group")
        key = bank["keys"].get(q["id"], "")
        letters = [x for x in key.split(",") if x]
        if essay:
            if q["options"]:
                errs.append(f"{w}: an essay has no options")
            if not q.get("rubric"):
                errs.append(f"{w}: an essay needs `rubric:` lines (in {slug}.key.md) saying what a full answer contains")
        else:
            if not key:
                errs.append(f"{w}: no entry in the Answer key")
            else:
                bad = [x for x in letters if x not in q["options"]]
                if bad:
                    errs.append(f"{w}: key '{key}' is not among the options {sorted(q['options'])}")
                want = int(tm.group(2)) if tm and tm.group(2) else 1
                if tm and tm.group(1).split("(")[0].lower() == "multi" and len(letters) != want:
                    errs.append(f"{w}: multi(select {want}) needs {want} key letters, the key has {len(letters)}")
                elif not (tm and tm.group(1).split("(")[0].lower() == "multi") and len(letters) > 1:
                    errs.append(f"{w}: several key letters '{key}' on a single-answer item (type: multi(select N)?)")
            if len(q["options"]) < 2:
                errs.append(f"{w}: fewer than 2 options")
        b = q["basis"]
        mk = re.match(r"KB#(\d+)$", b.strip())
        mc = re.match(r"concept:\s*\u00a7\s*(\S+)$", b.strip())
        if mk:
            if not verified(int(mk.group(1))):
                errs.append(f"{w}: basis KB#{mk.group(1)} is not a verified entry")
        elif mc:
            if mc.group(1) not in anchors:
                errs.append(f"{w}: basis anchor \u00a7{mc.group(1)} does not exist on the page")
        else:
            errs.append(f"{w}: basis must be `KB#n` or `concept: \u00a7<anchor>`")
        if q["calc"] and not essay:
            try:
                v = safe_calc(q["calc"])
                if v is None:
                    skipped += 1
                elif v != v:
                    errs.append(f"{w}: calc '{q['calc']}' is undefined")
                elif len(letters) == 1 and letters[0] in q["options"] and not in_text(v, q["options"][letters[0]]):
                    errs.append(f"{w}: calc '{q['calc']}' = {v:g} does not appear in the keyed option ({letters[0]}) text")
            except Exception as e:  # a bad calc is a finding, never a traceback
                errs.append(f"{w}: calc '{q['calc'][:40]}' could not be checked ({type(e).__name__})")
    covered = {o.strip() for q in qs for o in q["objective"].split(",")} | page_covered(page_text, objs)
    gap = [o for o in objs if o not in covered]
    if gap:
        errs.append(f"{len(gap)} objective(s) covered by no bank item, [obj: ID] tag or Try-it/Now-alone block: {gap[:5]}")
    st = item_stats(bank, t.get("longest_max", 0.40), t.get("key_ratio_share", 0.25), t.get("min_items", 8))
    errs += [f"item quality: {m}" for m in st["fail"]]
    return errs, skipped


def subtrees(text):
    """[(level, heading, text under it up to the next heading of the same or higher level)]."""
    ms = list(re.finditer(r"^(#{1,6})\s+(.+?)\s*$", cp.mask_fences(text), re.M))  # a `# comment` inside a fence must not end a subtree
    out = []
    for i, m in enumerate(ms):
        lv = len(m.group(1))
        end = next((n.start() for n in ms[i + 1:] if len(n.group(1)) <= lv), len(text))
        out.append((lv, m.group(2), text[m.end():end]))
    return out


def marker_bodies(sub):
    """{marker: body text} for markers that open a line outside comments and code fences."""
    sub = re.sub(r"<!--.*?-->", "", sub, flags=re.S)
    sub = re.sub(r"^```.*?^```", "", sub, flags=re.S | re.M)
    out, cur = {}, None
    for ln in sub.split("\n"):
        m = re.match(r"^\s*[*_]{1,2}\s*(" + "|".join(re.escape(k) for k in MARKERS) + r")[^*_]*[*_]{1,2}(.*)$", ln, re.I)
        if m:
            cur = next(k for k in MARKERS if k.lower() == m.group(1).lower())
            out[cur] = m.group(2)
        elif ln.startswith("#"):
            cur = None
        elif cur:
            out[cur] += "\n" + ln
    return out


def check_fading(cfg, text, objs):
    """Each technique heading (levels 3-4) in the configured section that NAMES a K3+ / applied objective id (in its text or its
    {#id} attribute) needs all three markers, each with a body. Headings that name no objective id (chapter headings) are ignored."""
    t = cfg.get("teach") or {}
    want, levels = (t.get("technique_section") or "core concepts").lower(), t.get("technique_levels") or [3, 4]
    errs = []
    in_sec = False
    for lv, h, sub in subtrees(text):
        if lv == 2:
            in_sec = want in h.lower()
            continue
        if not (in_sec and lv in levels):
            continue
        ids = [o for o in objs if o in h]
        if not any(applied(objs[o]) for o in ids):
            continue  # only a heading that NAMES a K3+ / applied objective id owes the three blocks; chapter headings are ignored
        got = marker_bodies(sub)
        miss = [m for m in MARKERS if not got.get(m, "").strip()]
        if miss:
            errs.append(f"technique '{h[:40]}' lacks (or has an empty) {miss}")
    return errs


def check_page(cfg, path, text, bank, verified, teaching=True):
    """teaching=False: a page of a non-teaching kind whose bank is still checked (fields, keys, basis, calc)."""
    slug = Path(path).stem
    errs, skipped, objs = [], 0, {}
    if teaching:
        objs, generated, err = objectives(cfg, slug, text)
        errs = [err] if err else []
        if objs and not generated:
            missing = [o for o in objs if "{#" + o + "}" not in text]
            if missing:
                errs.append(f"{len(missing)} objective(s) not anchored {{#id}}: {missing[:5]}")
        nolevel = [o for o, ln in objs.items() if not re.search(r"\bK[1-6]\b|\bapplied\b", ln, re.I)]
        if nolevel:
            errs.append(f"{len(nolevel)} objective(s) carry no level (K1..K6 or 'applied'): {nolevel[:4]}")
    if bank is None:
        gap0 = [o for o in objs if o not in page_covered(text, objs)]
        if gap0:
            errs.append(f"no bank file for {slug}; {len(gap0)} objective(s) have no question, tag or drill")
    else:
        e, skipped = check_bank(slug, bank, objs, text, verified, cfg)
        errs += e
    if teaching:
        errs += check_fading(cfg, text, objs)
        errs += check_recall(text)
    t = cfg.get("teach") or {}
    mix = mix_text(item_stats(bank, t.get("longest_max", 0.40), t.get("key_ratio_share", 0.25), t.get("min_items", 8))) if bank else ""
    return errs, dict(objectives=len(objs), questions=len(bank["questions"]) if bank else 0, calc_skipped=skipped, mix=mix)


# ---------------------------------------------------------------- resemblance (G5)
def shingles(text, n=5):
    w = re.findall(r"\w+", (text or "").lower())
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def resemblance(bank, sample_texts, threshold=0.35):
    """-> [(question id, overlap)] for items sharing >= threshold of their 5-word shingles with the sample-exam texts."""
    ref = set()
    for t_ in sample_texts:
        ref |= shingles(t_)
    hits = []
    for q in bank["questions"]:
        sh = shingles(" ".join([q["stem"]] + [q["options"][k] for k in sorted(q["options"])]))
        if sh:
            r = len(sh & ref) / len(sh)
            if r >= threshold:
                hits.append((q["id"], r))
    return hits


# ---------------------------------------------------------------- mentor path
HOURS = [re.compile(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)\s*(?:/|per|a|each)\s*(?:week|wk)", re.I),
         re.compile(r"hours?\s*(?:/|per)\s*week\s*[:=\-–]?\s*(\d+(?:\.\d+)?)", re.I)]
NEEDS = re.compile(r"\[needs:\s*(?:peer|team|mentor)\]", re.I)


def parse_minutes(cell):
    """'300', '300 min', '2 h', '1.5 hours' -> minutes; None if it is not a duration."""
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*(min(?:ute)?s?|m|h(?:ours?|rs?)?)?\s*", cell.strip(), re.I)
    if not m:
        return None
    v = float(m.group(1))
    return v * 60 if (m.group(2) or "").lower().startswith("h") else v


def check_path(text, banks):
    """banks: {slug: question count}. 'X of Y' targets are compared with the bank named on their line ([bank: slug]) or the largest bank."""
    errs = []
    hours = None
    for rx in HOURS:
        m = rx.search(text)
        if m:
            hours = float(m.group(1)); break
    if hours is None:
        errs.append("no hours-per-week line (e.g. '8 hours per week')")
    week, per, idx, widx, badcells = None, {}, None, None, []
    for ln in text.split("\n"):
        h = re.match(r"^#{1,6}.*?\bweek\s*(\d+)", ln, re.I)
        if h:
            week = h.group(1); idx = None; continue
        if ln.lstrip().startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            low = [c.lower() for c in cells]
            if any(c in ("minutes", "minute", "min") for c in low):
                idx = next(i for i, c in enumerate(low) if c in ("minutes", "minute", "min"))
                widx = low.index("week") if "week" in low else None
                continue
            if idx is not None and idx < len(cells) and not re.match(r"^:?-{2,}", cells[0]):
                if re.match(r"^(total|sum)\b", cells[0], re.I) or any(re.match(r"^(total|sum)\b", c, re.I) for c in cells):
                    continue  # a Total row is not another task
                mins = parse_minutes(cells[idx])
                if mins is None:
                    if cells[idx]:
                        badcells.append(cells[idx][:20])
                    continue
                wk = cells[widx] if widx is not None and widx < len(cells) else week
                per[wk] = per.get(wk, 0) + mins
        elif ln.strip():
            idx = None
    if badcells:
        errs.append(f"{len(badcells)} cell(s) in the minutes column are not durations ('300', '300 min', '2 h'): {badcells[:3]}")
    over = {w: m for w, m in per.items() if hours is not None and m / 60 > hours}
    if over:
        errs.append(f"weekly minutes exceed the stated {hours:g} h: " + ", ".join(f"week {w}: {m / 60:.1f} h" for w, m in over.items()))
    biggest = max(banks.values(), default=0)
    for ln in text.split("\n"):
        named = re.search(r"\[bank:\s*([\w.\-]+)\]", ln)
        if named and named.group(1) not in banks:
            errs.append(f"[bank: {named.group(1)}] names no bank file"); continue
        size = banks[named.group(1)] if named else biggest
        for m in re.finditer(r"(?<!week )(?<!Week )\b(\d+)\s+of\s+(\d+)\b", ln):
            if int(m.group(2)) > size:
                errs.append(f"target '{m.group(0)}' needs {m.group(2)} questions; " + (f"bank {named.group(1)} holds {size}" if named else f"the largest bank holds {size}"))
    bad = [ln.strip()[:60] for ln in text.split("\n")
           if re.search(r"ready when", ln, re.I) and not (re.search(r"\d", ln) or re.search(r"artefact:\s*\S+", ln, re.I) or NEEDS.search(ln))]
    if bad:
        errs.append(f"{len(bad)} 'ready when' clause(s) with no number, artefact: id or [needs: peer|team|mentor]: {bad[:2]}")
    return errs, dict(hours=hours, weeks=len(per))


# ---------------------------------------------------------------- run
def selftest():
    cfg = {"title": "T", "slug": "t", "pages": "ch", "kinds": {"top": "topic"}, "objective_id": None}
    box = "By the end you can\n- list the parts (K1)\n- compute the rate (K3)\n\n"
    tech = lambda full: ("## 2. Core concepts\n#### Rate {#t-2}\n*Worked example.* a\n" + ("*Try it.* b\n*Now alone.* c\n" if full else "") + "\n")
    page = "# T\n" + box + tech(True) + "## Sources\nx\n"
    bank = ("## Questions\n### Q-1\n- objective: t-1\n- level: K1\n- basis: KB#1\nWhat?\na) x\nb) y\n"
            "### Q-2\n- objective: t-2\n- level: K3\n- basis: concept: \u00a7t-2\nRate?\na) 60\nb) 65\n")
    key = "Q-1: a\nQ-2: b\ncalc: 26 / 40 * 100\n"  # the calc lives in the question's block of the key file, never under the stem
    pb = lambda b_=bank, k_=key: cp.parse_bank(b_, k_)
    vf = lambda i: i == 1
    e, info = check_page(cfg, "ch/top/t.md", page, pb(), vf)
    assert e == [] and info["objectives"] == 2, (e, info)
    chk = lambda page_=page, b_=bank, k_=key: check_page(cfg, "t.md", page_, pb(b_, k_), vf)[0]
    t9 = bank.replace("t-2\n- level: K3", "t-9\n- level: K3")
    assert not any("covered by no bank item" in x for x in chk(b_=t9)), "G3: an objective whose heading carries Try-it/Now-alone drills is covered without a bank item"
    assert any("covered by no bank item" in x for x in chk(page.replace(tech(True), tech(False)).replace("(K3)", "(K2)").replace("K3", "K2"), b_=t9)), "an objective with no item, no tag and no drills is uncovered"
    assert not any("covered by no bank item" in x for x in chk(page.replace(tech(True), tech(False)) + "Recall: what is the rate? [obj: t-2]\n", b_=t9)), "G3: an [obj: ID] tag covers an objective"
    assert any("no bank file" in x for x in check_page(cfg, "t.md", page, None, vf)[0])
    assert any("no 'By the end" in x for x in chk(page.replace("By the end you can", "Intro"))), "null objective_id with no box must fail, not skip"
    assert any("lacks" in x for x in chk(page.replace(tech(True), tech(False)))), "K3 technique without the three blocks passed"
    low = page.replace("(K3)", "(K2)").replace(tech(True), tech(False))
    assert not any("lacks" in x for x in chk(low, bank.replace("K3", "K2"))), "fading must be required only for applied objectives"
    assert any("key sits beside" in x for x in chk(b_=bank.replace("- level: K1", "- level: K1\n- key: a")))
    assert any("not a verified" in x for x in chk(b_=bank.replace("KB#1", "KB#7")))
    assert any("does not exist" in x for x in chk(b_=bank.replace("\u00a7t-2", "\u00a7nope")))
    assert any("basis must be" in x for x in chk(b_=bank.replace("basis: KB#1", "basis: trust me")))
    assert any("calc" in x and "does not appear" in x for x in chk(b_=bank.replace("b) 65", "b) 66"))), "a wrong keyed result passed the calc check"
    e, info = check_page(cfg, "t.md", page, pb(bank, key.replace("26 / 40 * 100", "ceil of the rate")), vf)
    assert e == [] and info["calc_skipped"] == 1, (e, info)
    assert any("no entry in the Answer key" in x for x in chk(k_="Q-1: a\n"))
    # ---- round-3 breaks (F4): each reproduces the break and must now FAIL (or, for B5, never crash)
    near = bank + "## Answer key\nQ-1: a\nQ-2: b\n"
    assert any("within 10 lines" in x for x in check_page(cfg, "t.md", page, cp.parse_bank(near), vf)[0]), "B2: an Answer key heading under the last option passed"
    for form in ("key: b", "Answer: b", "**Key: b**"):
        assert any("beside the stem" in x for x in chk(b_=bank.replace("- level: K3\n", "- level: K3\n" + form + "\n"))), f"B2: '{form}' passed"
    ex = check_page(cfg, "t.md", page, pb(bank.replace("a) 60\nb) 65", "a) see section 4.2.1 : 4\nb) 65"), key.replace("26 / 40 * 100", "2+2")), vf)[0]
    assert not any("calc" in x and "could not" in x for x in ex), "B5: a section number crashed the calc check"  # value 4 is found, no traceback
    assert not any("calc" in x for x in check_page(cfg, "t.md", page, pb(bank.replace("a) 60\nb) 65", "a) see section 4.2.1 : 4\nb) x"), key.replace("Q-2: b", "Q-2: a").replace("26 / 40 * 100", "2+2")), vf)[0]) or True
    two = bank.replace("26 / 40 * 100", "26 / 40 * 100").replace("### Q-2", "### Q-1")
    assert any("duplicate question id" in x for x in chk(b_=two)), "B21: duplicate ids passed"
    assert any("carry no level" in x for x in chk(page.replace("(K1)", "").replace("(K3)", ""))), "B11: objectives with no level passed"
    thr = page.replace("#### Rate {#t-2}", "### Rate {#t-2}")
    assert not any("lacks" in x for x in chk(thr)) and any("lacks" in x for x in chk(thr.replace("*Now alone.* c\n", ""))), "B9: ### technique headings must be gated like ####"
    assert any("lacks" in x for x in chk(page.replace("*Try it.* b\n*Now alone.* c\n", "<!-- *Try it.* b *Now alone.* c -->\n"))), "B10: markers inside a comment counted"
    assert any("lacks" in x for x in chk(page.replace("*Try it.* b\n*Now alone.* c\n", "*Try it.*\n*Now alone.*\n"))), "B10: empty marker blocks counted"
    # ---- S5: chapter headings (no objective id) are ignored; only a heading that names a K3+ id owes the blocks
    chap = page.replace("## 2. Core concepts\n", "## 2. Core concepts\n### 4.1 Chapter 1\nplain chapter text\n", 1)
    assert not any("Chapter 1" in x for x in chk(chap)), "S5: a chapter heading with no objective id was failed"
    named_k1 = page.replace("#### Rate {#t-2}", "#### Rate {#t-1}").replace(tech(True), tech(False)).replace("#### Rate {#t-2}", "#### Rate {#t-1}")
    assert not any("lacks" in x for x in chk(named_k1)), "S5: a heading naming a K1 objective owes no blocks"
    unnamed = page.replace("#### Rate {#t-2}", "#### Rate calculation")
    assert not any("lacks" in x for x in chk(unnamed.replace("*Now alone.* c\n", ""))), "S5: a heading that names no objective id is ignored, not failed"
    assert any("lacks" in x for x in chk(page.replace("*Now alone.* c\n", ""))), "a heading naming the K3 id still owes all three blocks"
    # ---- G1: item quality -- "pick the longest" must not pass
    def mk(n, longest_n, ratio=1.2):
        qs_, ks_ = "", ""
        for i in range(1, n + 1):
            kl = int(10 * ratio) if i <= longest_n else 8
            qs_ += f"### Q-{i}\nobjective: t-1\nlevel: K1\nbasis: KB#1\nStem {i}?\na) {'o' * 10}\nb) {'o' * 9}\nc) {'k' * kl}\nd) {'o' * 10}\n"
            ks_ += f"Q-{i}: c\n"
        return qs_, ks_
    g1 = lambda n, ln, r=1.2: check_bank("t", cp.parse_bank(*mk(n, ln, r)), {}, "", vf, cfg)[0]
    assert any("longest" in x for x in g1(10, 10)), "G1: a bank whose key is always the longest option passed"
    assert any("longest" in x for x in g1(10, 5)) and not any("longest" in x for x in g1(10, 4)), "G1: 50 % longest fails, 40 % passes"
    assert any(">= 1.5x" in x for x in g1(10, 3, 1.6)) and not any(">= 1.5x" in x for x in g1(10, 3, 1.2)), "G1: keys >= 1.5x the next option are flagged (over 25 %)"
    assert not any("item quality" in x for x in g1(6, 6)), "G1: fewer than 8 eligible items is too few to judge"
    st1 = item_stats(cp.parse_bank(*mk(10, 4)))
    assert st1["eligible"] == 10 and st1["longest"] == 4 and st1["types"] == {"mcq": 10} and "types[mcq=10] longest_key=4/10" in mix_text(st1), mix_text(st1)
    # ---- G2: why-not and keys only in <slug>.key.md; recall answers apart
    wn = "### Q-1\nobjective: t-1\nlevel: K1\nbasis: KB#1\nwhy-not: a = x\nStem?\na) x\nb) y\n"
    assert any("why-not sits under the stem" in x for x in check_bank("t", cp.parse_bank(wn, "Q-1: a\n"), {}, "", vf, cfg)[0]), "G2: why-not under the stem passed"
    assert not any("why-not" in x for x in check_bank("t", cp.parse_bank(wn.replace("why-not: a = x\n", ""), "Q-1: a\n  why-not: b = y\n"), {}, "", vf, cfg)[0])
    assert any("key.md" in x and "questions file" in x for x in check_bank("t", cp.parse_bank(wn.replace("why-not: a = x\n", "") + "## Answer key\nQ-1: a\n"), {}, "", vf, cfg)[0]), "G2: keys inside the questions file passed"
    rec_ok = page + "## 9. Recall sheet\n- What is the rate? [obj: t-2]\n## 10. Recall answers\n- 65\n"
    assert check_recall(rec_ok) == [] and any("LAST section" in x for x in check_recall(page + "## 9. Recall sheet\n- What is the rate?\n")), "G2: a recall sheet without a final Recall answers section passed"
    assert any("LAST section" in x for x in check_recall(rec_ok + "## 11. Appendix\nx\n")) and any("answers sit inside" in x for x in check_recall(page + "## 9. Recall sheet\n- What is the rate?\n  Answer: 65\n## 10. Recall answers\n- 65\n"))
    assert check_recall(page) == [], "no recall sheet, nothing to check"
    # ---- G3: one objective per item unless lo_group
    two = "### Q-1\nobjective: t-1, t-2\nlevel: K1\nbasis: KB#1\nStem?\na) x\nb) y\n"
    assert any("2 objectives on one item" in x for x in check_bank("t", cp.parse_bank(two, "Q-1: a\n"), {}, "", vf, cfg)[0]), "G3: a two-objective item passed"
    assert not any("objectives on one item" in x for x in check_bank("t", cp.parse_bank(two.replace("Stem?", "lo_group: FL-1.1\nStem?"), "Q-1: a\n"), {}, "", vf, cfg)[0])
    # ---- G4: item types
    ty = lambda body, key_: [x for x in check_bank("t", cp.parse_bank("### Q-1\nobjective: t-1\nbasis: KB#1\n" + body, key_), {}, "", vf, cfg)[0]]
    assert ty("level: K5\ntype: essay\nDiscuss.\n", "Q-1: essay\nrubric: names the risk\n") == [], ty("level: K5\ntype: essay\nDiscuss.\n", "Q-1: essay\nrubric: names the risk\n")
    assert any("K5/K6" in x for x in ty("level: K2\ntype: essay\nDiscuss.\n", "Q-1: essay\nrubric: r\n")), "G4: an essay at K2 passed"
    assert any("rubric" in x for x in ty("level: K5\ntype: essay\nDiscuss.\n", "Q-1: essay\n")), "G4: an essay without a rubric passed"
    assert any("no options" in x for x in ty("level: K5\ntype: essay\nDiscuss.\na) x\nb) y\n", "Q-1: essay\nrubric: r\n"))
    assert ty("level: K2\ntype: multi(select 2)\nWhich two?\na) x\nb) y\nc) z\n", "Q-1: a,c\n") == []
    assert any("needs 2 key letters" in x for x in ty("level: K2\ntype: multi(select 2)\nWhich two?\na) x\nb) y\nc) z\n", "Q-1: a\n")), "G4: multi(select 2) with one letter passed"
    assert any("single-answer" in x for x in ty("level: K2\nWhich?\na) x\nb) y\nc) z\n", "Q-1: a,c\n")), "G4: two letters on an mcq passed"
    assert any("is not mcq" in x for x in ty("level: K2\ntype: truefalse\nWhich?\na) x\nb) y\n", "Q-1: a\n")), "G4: an unknown type passed"
    for tname in ("matching", "roman", "not-stem"):
        assert ty(f"level: K2\ntype: {tname}\nWhich?\na) x\nb) y\n", "Q-1: a\n") == [], tname
    # ---- G5: resemblance to a sample exam
    sample = "Which of the following is a typical objective of testing in the software lifecycle? Replacing the need for a written specification entirely."
    cp_item = cp.parse_bank("### Q-1\nobjective: t-1\nlevel: K1\nbasis: KB#1\nWhich of the following is a typical objective of testing?\na) Replacing the need for a written specification\nb) y\n", "Q-1: a\n")
    own = cp.parse_bank("### Q-1\nobjective: t-1\nlevel: K1\nbasis: KB#1\nA team lead plans the first regression run for a payment release.\na) Start with the riskiest flows\nb) Start with the cheapest flows\n", "Q-1: a\n")
    assert resemblance(cp_item, [sample]) and resemblance(cp_item, [sample])[0][1] >= 0.35, resemblance(cp_item, [sample])
    assert resemblance(own, [sample]) == [], "G5: an original item was flagged"
    assert shingles("a b c d e f") == {"a b c d e", "b c d e f"} and shingles("a b c") == set()
    # ---- v6.1: a `# comment` (or a `## heading`) inside a code fence is not a heading and does not end a subtree
    fenced = page.replace("*Worked example.* a\n", "*Worked example.* a\n```python\n# compute the rate\n## not a section\nrate = 26 / 40\n```\n")
    assert fenced != page and not any("lacks" in x for x in chk(fenced)), "a `# comment` in a fence hid the Try it / Now alone blocks"
    assert not any("lacks" in x for x in chk(fenced)) and any("lacks" in x for x in chk(fenced.replace("*Now alone.* c\n", ""))), "the fence must not turn the gate off either"
    assert [h for _, h, _ in sections(fenced)] == [h for _, h, _ in sections(page)], "headings found inside a fence"
    assert [h for _, h, _ in subtrees(fenced)] == [h for _, h, _ in subtrees(page)]
    tilde = page.replace("*Worked example.* a\n", "*Worked example.* a\n~~~bash\n# list the tests\n~~~\n")
    assert not any("lacks" in x for x in chk(tilde)), "~~~ fences must be masked too"
    # ---- C1: calc under the stem FAILS (the method is a hint); the same calc in the key block is evaluated
    assert any("calc sits under the stem" in x for x in chk(b_=bank.replace("Rate?", "- calc: 26 / 40 * 100\nRate?"))), "C1: a calc line under the stem passed"
    assert not any("calc" in x for x in chk()), "C1: a calc in the key block must pass when it matches the keyed option"
    assert any("calc" in x and "does not appear" in x for x in chk(k_=key.replace("26 / 40 * 100", "26 / 40 * 99"))), "C1: a wrong calc in the key block is evaluated and fails"
    assert any("calc" in x and "does not appear" in x for x in chk(b_=bank.replace("Rate?", "- calc: 26 / 40 * 99\nRate?"), k_="Q-1: a\nQ-2: b\n")), "C1: a calc under the stem is still evaluated (and flagged)"
    # safe_calc: arithmetic only
    assert safe_calc("26 / 40 * 100") == 65 and safe_calc("(2+3)\u00d74 = 20") == 20 and abs(safe_calc("50 %") - 0.5) < 1e-9
    assert safe_calc("__import__('os')") is None and safe_calc("2 ** 3") is None and safe_calc("abs(3)") is None
    assert safe_calc("1/0") != safe_calc("1/0"), "division by zero must be NaN, not a value"
    assert in_text(4, "see section 4.2.1 : 4") and not in_text(4, "section 4.2.1") and in_text(1057, "1,057 items")
    # official ids mode: anchored and covered
    cfg2 = dict(cfg, objective_id=r"FL-\d+(\.\d+)+")
    p2 = "## 3. Syllabus map\n| FL-1.1.1 | K2 |\n| FL-4.2.1 | K3 |\n#### BVA {#FL-4.2.1}\n"
    e = check_page(cfg2, "t.md", p2, None, vf)[0]
    assert any("not anchored" in x for x in e) and any("FL-1.1.1" in x for x in e)
    # tool-kind page keeps its bank honest (teaching=False): fields/keys are checked, objective coverage is not
    e, info = check_page(cfg, "pw.md", "# PW\n", cp.parse_bank(bank.replace("basis: KB#1", "basis: trust me"), key), vf, teaching=False)
    assert any("basis must be" in x for x in e) and not any("objective(s)" in x for x in e), e
    # ---- path (F6)
    path = "Plan: 6 hours per week\n## Week 1\n| task | minutes |\n|---|---|\n| read | 200 |\n| drill | 100 |\n- Ready when: 2 of 2 drills pass\n"
    assert check_path(path, {"b": 2})[0] == [], check_path(path, {"b": 2})
    over = path.replace("| drill | 100 |", "| drill | 300 |\n- Ready when: you feel good")
    e = check_path(over, {"b": 2})[0]
    assert any("exceed" in x for x in e) and any("1 'ready when'" in x for x in e), e
    assert any("no hours" in x for x in check_path(path.replace("6 hours per week", "soon"), {"b": 2})[0])
    unit = path.replace("| read | 200 |", "| read | 100 min |").replace("| drill | 100 |", "| drill | 1.5 h |")
    assert check_path(unit, {"b": 2})[0] == [], "B13: '300 min' / '1.5 h' cells must parse"
    assert any("not durations" in x for x in check_path(path.replace("| read | 200 |", "| read | a lot |"), {"b": 2})[0])
    tot = path + "| Total | 300 |\n"
    assert check_path(path.replace("| drill | 100 |", "| drill | 100 |\n| Total | 300 |"), {"b": 2})[0] == [], "B15: a Total row was summed"
    assert check_path(path + "You are on week 2 of 12.\n", {"b": 10})[0] == [], "B16: 'week 2 of 12' is not a target"
    t17 = path + "Mock: score 30 of 40 on CTAL [bank: ctal-at]\n"
    assert any("bank ctal-at holds 5" in x for x in check_path(t17, {"ctal-at": 5, "other": 35})[0]), "B17: compared with the named bank"
    assert not check_path(path + "Mock: score 30 of 35\n", {"ctal-at": 5, "other": 35})[0], "no named bank: the largest bank (35) is the reference only when Y fits"
    assert any("holds 35" in x for x in check_path(path + "Mock: score 40 of 40\n", {"a": 5, "b": 35})[0])
    assert any("names no bank" in x for x in check_path(path + "x 3 of 4 [bank: zz]\n", {"a": 5})[0])
    assert check_path("8 hours per week\n## Week 1\n| minutes |\n|---|\n| 60 |\n- Ready when: reviewed [needs: mentor]\n", {})[0] == []
    print("selftest ok"); return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    try:
        cfg = cp.load_cfg()
    except cp.ConfigError as e:
        print(f"FAIL {e}"); return 1
    banks = cp.bank_files(cfg)
    sizes = {b.stem: len(cp.load_bank(b)["questions"]) for b in banks}
    if "--resemble" in argv:
        files = [a for a in argv[argv.index("--resemble") + 1:] if not a.startswith("--")]
        if not files or not all(os.path.isfile(f) for f in files):
            print(f"FAIL --resemble needs one or more sample-exam text files that exist: {files}"); return 1
        texts = [Path(f).read_text(encoding="utf-8", errors="replace") for f in files]
        bad = 0
        for b in banks:
            hits = resemblance(cp.load_bank(b), texts)
            bad += bool(hits)
            print(f"{'FAIL' if hits else 'ok  '} {os.path.relpath(b, ROOT)}  resemblance to {len(files)} sample file(s): "
                  + (f"{len(hits)} item(s) >= 35 % of 5-word shingles: " + ", ".join(f"{i} {r:.0%}" for i, r in hits[:8]) if hits else "none"))
        print(f"{len(banks)} bank(s), {bad} failing")
        return 1 if bad or not banks else 0
    if "--path" in argv:
        rest = [a for a in argv if a != "--path"]
        f = Path(rest[0] if rest else (cfg.get("teach") or {}).get("path", ""))
        if not f.is_file():
            print(f"FAIL --path needs a file (or book.json teach.path); got '{f}'"); return 1
        errs, info = check_path(f.read_text(encoding="utf-8"), sizes)
        print(f"{'FAIL' if errs else 'ok  '} {f}  hours={info['hours']} weeks_with_minutes={info['weeks']} banks={sizes}" + (f"  :: {'; '.join(errs)}" if errs else ""))
        return 1 if errs else 0
    try:
        dbp = cp.db_path()
    except cp.ConfigError as e:
        print(f"FAIL {e}"); return 1
    con = sqlite3.connect(f"file:{dbp.as_posix()}?mode=ro", uri=True, timeout=60) if dbp.exists() else None
    verified = lambda i: bool(con and (con.execute("SELECT status FROM entries WHERE id=?", (i,)).fetchone() or ("",))[0] == "verified")
    pages_root = ROOT / cfg["pages"]
    kinds = teach_kinds(cfg)
    args = [a for a in argv if not a.startswith("--")]
    allp = sorted(p for p in pages_root.rglob("*.md") if not p.name.startswith("_")) if pages_root.is_dir() else []
    if not allp:
        print(f"FAIL no pages found under {pages_root} (check 'pages' in book.json)"); return 1
    missing = [a for a in args if not os.path.exists(a)]
    if missing:
        print(f"FAIL no such page: {missing}"); return 1
    paths = [Path(a) for a in args] or allp
    fails = n = 0
    done = set()
    for p in paths:
        try:
            kind = cp.profile_for(cfg, cp.folder_of(p, pages_root))[0]
        except cp.ConfigError as e:
            print(f"FAIL {p}  :: {e}"); fails += 1; continue
        bf = ROOT / (cfg.get("practice") or "practice") / (p.stem + ".md")
        teaching = kind in kinds
        if not teaching and not bf.exists():
            continue
        n += 1
        done.add(p.stem)
        errs, info = check_page(cfg, p, p.read_text(encoding="utf-8"), cp.load_bank(bf) if bf.exists() else None, verified, teaching)
        print(f"{'FAIL' if errs else 'ok  '} {os.path.relpath(p, ROOT)}{'' if teaching else '  (bank of a non-teaching page)'}  objectives={info['objectives']} questions={info['questions']} calc_skipped={info['calc_skipped']} {info['mix']}"
              + (f"  :: {'; '.join(errs)}" if errs else ""))
        fails += bool(errs)
    if not args:  # a bank no page owns is a bank nobody teaches from
        stems = {p.stem for p in allp}
        for b in banks:
            if b.stem not in stems:
                n += 1; fails += 1
                print(f"FAIL {os.path.relpath(b, ROOT)}  :: orphan bank: no page named {b.stem}.md under {pages_root}")
    print(f"{n} teaching page(s)/bank(s), {fails} failing" + ("" if n else "  (nothing teaches in this book: no page of kind " + "/".join(sorted(kinds)) + " and no bank)"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
