#!/usr/bin/env python3
"""rules.py -- query layer over kb/rules/*.md (stdlib only). PYTHONUTF8=1 assumed.
Project root = BOOK_ROOT env or cwd; db and rules dir from <project>/kb/kb.json.

The pack files under kb/rules/ are the source of truth; this script only
parses and indexes them so an agent can fetch one rule without reading the
whole tree. A malformed rule block is a hard error, not a skip -- a rule
that silently drops out of the index is the failure mode that matters here.

    rules.py get R-REEL-012            print that one rule block
    rules.py find "caption"            id + rule line for every match in rule/when/tags
    rules.py list [--pack reel] [--strength binding] [--tag instagram]
    rules.py for --task "<free text>"  match text against When + Tags, ranked, top 10
    rules.py index                     regenerate kb/rules/INDEX.md
    rules.py check                     validate the whole tree; exit 2 on any failure
    rules.py --selftest                run the built-in demo() self-check

Rule block format (fixed field names, order, markup -- see
.agent-ops/briefs/mkb-0922d-rules.md "The rule format"):

    ### R-REEL-012 . Caption safe area
    **Rule:** <imperative sentence>
    **When:** <trigger>
    **Because:** #341, #345
    **Strength:** binding|advisory
    **Decay:** evergreen|volatile, recheck YYYY-MM-DD
    **Tags:** a, b, c
"""
from __future__ import annotations
import argparse, collections, datetime as dt, math, os, re, sqlite3, sys, tempfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import json
# Project = BOOK_ROOT env or cwd; db and rules dir come from <project>/kb/kb.json
# ({"db": "kb/qa.db", "rules": "kb/rules"}); defaults keep a bare project working.
ROOT = os.path.abspath(os.environ.get("BOOK_ROOT") or os.getcwd())
try:
    with open(os.path.join(ROOT, "kb", "kb.json"), encoding="utf-8") as _f:
        CFG = json.load(_f)
except FileNotFoundError:
    CFG = {}
RULES_DIR = os.path.join(ROOT, CFG.get("rules", "kb/rules"))
INDEX_NAME = "INDEX.md"
DB = os.path.join(ROOT, CFG.get("db", "kb/qa.db"))

HEADER_RE = re.compile(r"^### (R-[A-Z]+-\d{3}) · (.+?)\s*$")
FIELD_SPECS = [
    ("Rule", re.compile(r"^\*\*Rule:\*\* (.+)$")),
    ("When", re.compile(r"^\*\*When:\*\* (.+)$")),
    ("Because", re.compile(r"^\*\*Because:\*\* (.+)$")),
    ("Strength", re.compile(r"^\*\*Strength:\*\* (binding|advisory)$")),
    ("Decay", re.compile(r"^\*\*Decay:\*\* (evergreen|volatile, recheck \d{4}-\d{2}-\d{2})$")),
    ("Tags", re.compile(r"^\*\*Tags:\*\* (.+)$")),
]


class RuleError(Exception):
    """A rule block does not match the fixed format. Never caught silently."""


def today():
    return dt.date.today().isoformat()


# ---------- parsing ----------

def _find_blocks(path):
    """Split a pack file into (header_lineno, lines) per '### R-...' block."""
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    idxs = [i for i, l in enumerate(lines) if l.startswith("### ")]
    out = []
    for j, start in enumerate(idxs):
        end = idxs[j + 1] if j + 1 < len(idxs) else len(lines)
        out.append((start, lines[start:end]))
    return out


def _parse_block(slice_lines, path, header_lineno):
    header = slice_lines[0]
    m = HEADER_RE.match(header)
    if not m:
        raise RuleError(f"{path}:{header_lineno + 1}: malformed header line: {header!r}")
    rid, title = m.group(1), m.group(2)

    content = []
    for l in slice_lines[1:]:
        if l.startswith("#"):
            break
        if l.strip() == "":
            continue
        content.append(l)

    if len(content) < len(FIELD_SPECS):
        raise RuleError(f"{path}: rule {rid}: missing required field(s) -- found {len(content)} of {len(FIELD_SPECS)}")
    if len(content) > len(FIELD_SPECS):
        raise RuleError(f"{path}: rule {rid}: unexpected extra line(s) after Tags -- found {len(content)}, expected {len(FIELD_SPECS)}")

    parsed = {"id": rid, "title": title, "file": path, "lineno": header_lineno + 1}
    for pos, ((name, rx), line) in enumerate(zip(FIELD_SPECS, content), start=1):
        mm = rx.match(line)
        if not mm:
            raise RuleError(f"{path}: rule {rid}: expected **{name}:** as field {pos}/{len(FIELD_SPECS)}, got: {line!r}")
        parsed[name.lower()] = mm.group(1)

    because_ids = [int(x) for x in re.findall(r"#(\d+)", parsed["because"])]
    if not because_ids:
        raise RuleError(f"{path}: rule {rid}: Because must cite at least one #id")
    parsed["because_ids"] = because_ids
    parsed["tags_list"] = [t.strip().lower() for t in parsed["tags"].split(",") if t.strip()]
    decay = parsed["decay"]
    dm = re.search(r"recheck (\d{4}-\d{2}-\d{2})", decay)
    parsed["recheck"] = dm.group(1) if dm else None
    parsed["raw"] = "\n".join([header] + content)
    return parsed


def parse_pack_strict(path):
    """All blocks in one pack file, or raise RuleError on the first bad one."""
    return [_parse_block(sl, path, start) for start, sl in _find_blocks(path)]


def pack_files(rules_dir=RULES_DIR):
    if not os.path.isdir(rules_dir):
        return []
    return sorted(
        os.path.join(rules_dir, f) for f in os.listdir(rules_dir)
        if f.endswith(".md") and f != INDEX_NAME
    )


def all_rules_strict(rules_dir=RULES_DIR):
    """Every rule in every pack. Raises RuleError (with sys.exit) on any malformed block."""
    out = []
    for p in pack_files(rules_dir):
        out.extend(parse_pack_strict(p))
    return out


def pack_name(path):
    return os.path.splitext(os.path.basename(path))[0]


# ---------- db ----------

def db_ro(db_path=DB):
    if not os.path.exists(db_path):
        raise RuleError(f"kb database not found: {db_path}")
    uri = "file:" + db_path.replace(os.sep, "/") + "?mode=ro"
    return sqlite3.connect(uri, uri=True, timeout=60)


# ---------- check ----------

def run_check(rules_dir=RULES_DIR, db_path=DB):
    """Validate the whole rule tree. Returns a list of violation strings (empty = clean)."""
    violations = []
    files = pack_files(rules_dir)
    parsed_all = []
    seen_ids = {}

    for path in files:
        blocks = _find_blocks(path)
        if not blocks:
            violations.append(f"{path}: empty pack (no rule blocks found)")
            continue
        expected_prefix = f"R-{pack_name(path).upper()}-"
        for start, sl in blocks:
            try:
                r = _parse_block(sl, path, start)
            except RuleError as e:
                violations.append(str(e))
                continue
            if not r["id"].startswith(expected_prefix):
                violations.append(f"{path}: rule {r['id']} does not match pack prefix {expected_prefix}")
            if r["id"] in seen_ids:
                violations.append(f"{path}: duplicate ID {r['id']} (already defined in {seen_ids[r['id']]})")
            else:
                seen_ids[r["id"]] = path
            if r["decay"].startswith("volatile") and r["recheck"] is None:
                violations.append(f"{path}: rule {r['id']} is volatile with no recheck date")
            elif r["recheck"] and r["recheck"] < today():
                violations.append(f"{path}: rule {r['id']} recheck date {r['recheck']} has passed (today {today()})")
            parsed_all.append(r)

    because_ids = sorted({bid for r in parsed_all for bid in r["because_ids"]})
    if because_ids:
        try:
            con = db_ro(db_path)
        except RuleError as e:
            violations.append(str(e))
            con = None
        if con is not None:
            status_by_id = {}
            for bid in because_ids:
                row = con.execute("SELECT status FROM entries WHERE id=?", (bid,)).fetchone()
                status_by_id[bid] = row[0] if row else None
            con.close()
            for r in parsed_all:
                for bid in r["because_ids"]:
                    st = status_by_id[bid]
                    if st is None:
                        violations.append(f"{r['file']}: rule {r['id']}: Because #{bid} absent from the kb database")
                    elif st != "verified":
                        violations.append(f"{r['file']}: rule {r['id']}: Because #{bid} not verified (status={st})")

    return violations


# ---------- commands ----------

def cmd_get(a):
    for p in pack_files():
        for r in parse_pack_strict(p):
            if r["id"] == a.id:
                print(r["raw"]); return
    sys.exit(f"no such rule: {a.id}")


def cmd_find(a):
    needle = a.text.lower()
    hits = 0
    for r in all_rules_strict():
        hay = " ".join([r["rule"], r["when"], r["tags"]]).lower()
        if needle in hay:
            print(f"{r['id']}  {r['rule']}")
            hits += 1
    if not hits:
        print("(no matches)")


def cmd_list(a):
    rows = [r for r in all_rules_strict() if (not a.pack or pack_name(r["file"]) == a.pack)]
    if a.strength:
        rows = [r for r in rows if r["strength"] == a.strength]
    if a.tag:
        rows = [r for r in rows if a.tag.lower() in r["tags_list"]]
    if not rows:
        print("(no rules)"); return
    for r in rows:
        print(f"{r['id']}  [{r['strength']}]  {r['title']}  decay={r['decay']}")


def _words(text):
    return set(re.findall(r"\w+", text.lower()))


def rule_words(r):
    return _words(" ".join([r["when"], r["tags"], r["rule"], r["title"]]))


def rank_for(task, rules):
    """Rules ranked against free-text `task` by IDF-weighted cosine overlap.

    A term that appears in every rule has idf 0 and contributes nothing, so
    stopwords drop out of the score by themselves -- no hand-written list. The
    cosine normalisation is what stops a long `When` clause winning on length.
    Corpus is the rules passed in; computed per query, nothing cached.
    """
    df = collections.Counter()
    for r in rules:
        df.update(rule_words(r))
    n = len(rules) or 1
    idf = {t: math.log(n / c) for t, c in df.items()}
    task_terms = _words(task) & idf.keys()
    tnorm = math.sqrt(sum(idf[t] ** 2 for t in task_terms)) or 1.0
    scored = []
    for r in rules:
        words = rule_words(r)
        rnorm = math.sqrt(sum(idf[t] ** 2 for t in words)) or 1.0
        score = sum(idf[t] ** 2 for t in task_terms & words) / (tnorm * rnorm)
        if score > 0:
            scored.append((score, r))
    scored.sort(key=lambda t: (-t[0], t[1]["id"]))
    return scored


def cmd_for(a):
    scored = rank_for(a.task, all_rules_strict())
    if not scored:
        print("(no matches)"); return
    for score, r in scored[:10]:
        # printed 0-100 so the first column stays an integer, as before
        print(f"{round(score * 100)}  {r['id']}  {r['when']}")


def cmd_index(a):
    files = pack_files()
    os.makedirs(RULES_DIR, exist_ok=True)
    out = os.path.join(RULES_DIR, INDEX_NAME)
    with open(out, "w", encoding="utf-8") as f:
        f.write("# kb/rules/INDEX.md\n\n")
        f.write("<!-- generated by `python scripts/rules.py index` -- do not hand-edit -->\n\n")
        if not files:
            f.write("(no pack files yet)\n")
        for p in files:
            rules = parse_pack_strict(p)
            f.write(f"## {pack_name(p)}\n\n")
            if not rules:
                f.write("(empty pack)\n\n"); continue
            for r in rules:
                f.write(f"- {r['id']} -- {r['when']}\n")
            f.write("\n")
    print(f"wrote {out}")


def cmd_check(a):
    violations = run_check()
    for v in violations:
        print(v)
    print(f"{len(violations)} violation(s)")
    if violations:
        sys.exit(2)
    print("ok")


# ---------- selftest ----------

def demo():
    """Assert-based self-check: parser round-trip, check() catching a duplicate ID
    and an unverified/absent Because id. Runs against temp dirs; touches no
    real pack file and never writes to the kb database."""

    import sqlite3 as _sq
    _tdir = tempfile.mkdtemp()
    DB_T = os.path.join(_tdir, "t.db")  # entries 1 verified, 2 draft; the project DB is never touched
    _c = _sq.connect(DB_T, timeout=60)
    _c.execute("CREATE TABLE entries(id INTEGER PRIMARY KEY, status TEXT)")
    _c.executemany("INSERT INTO entries VALUES(?,?)", [(1, "verified"), (2, "draft")])
    _c.commit(); _c.close()

    # 1. parser round-trip on one synthetic block
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "demo.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(
                "# Demo pack\n\npreamble line one\npreamble line two\n\n"
                "## Theme\n\n"
                "### R-DEMO-001 · Roundtrip check\n"
                "**Rule:** Do the thing every time.\n"
                "**When:** Any demo task.\n"
                "**Because:** #1, #2\n"
                "**Strength:** binding\n"
                "**Decay:** evergreen\n"
                "**Tags:** a, b\n"
            )
        rules = parse_pack_strict(p)
        assert len(rules) == 1, f"expected 1 rule, got {len(rules)}"
        r = rules[0]
        assert r["id"] == "R-DEMO-001"
        assert r["title"] == "Roundtrip check"
        assert r["rule"] == "Do the thing every time."
        assert r["when"] == "Any demo task."
        assert r["because_ids"] == [1, 2]
        assert r["strength"] == "binding"
        assert r["decay"] == "evergreen"
        assert r["tags_list"] == ["a", "b"]
    print("selftest: parser round-trip ok")

    # 2. check() catches a duplicate ID
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "demo.md")
        block = (
            "### R-DEMO-002 · Dup one\n"
            "**Rule:** Do it.\n**When:** Always.\n**Because:** #1\n"
            "**Strength:** binding\n**Decay:** evergreen\n**Tags:** a\n\n"
        )
        with open(p, "w", encoding="utf-8") as f:
            f.write(block + block.replace("Dup one", "Dup two"))
        violations = run_check(rules_dir=tmp, db_path=DB_T)
        assert any("duplicate" in v.lower() and "R-DEMO-002" in v for v in violations), violations
    print("selftest: check() catches duplicate ID ok")

    # 3. check() catches a Because id that is not verified (here: absent entirely)
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "demo.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write(
                "### R-DEMO-003 · Bad because\n"
                "**Rule:** Do it.\n**When:** Always.\n**Because:** #999999999\n"
                "**Strength:** binding\n**Decay:** evergreen\n**Tags:** a\n"
            )
        violations = run_check(rules_dir=tmp, db_path=DB_T)
        assert any("999999999" in v and ("absent" in v or "not verified" in v) for v in violations), violations
    print("selftest: check() catches unverified Because id ok")
    def _blk(n):
        return ("### R-DEMO-004 · Cite\n**Rule:** Do it.\n**When:** Always.\n**Because:** #%d\n"
                "**Strength:** binding\n**Decay:** evergreen\n**Tags:** a\n") % n
    with tempfile.TemporaryDirectory() as tmp:
        for n, ok in ((2, False), (1, True)):
            with open(os.path.join(tmp, "demo.md"), "w", encoding="utf-8") as f:
                f.write(_blk(n))
            v = run_check(rules_dir=tmp, db_path=DB_T)
            assert (v == []) == ok and (ok or any("not verified" in x for x in v)), v
    print("selftest: draft cite fails, verified cite passes ok")

    # 4. ranking: a rule padded with common words must not outrank a shorter, rarer match
    def _r(rid, when, tags="a"):
        return {"id": rid, "title": rid, "rule": "Do it.", "when": when, "tags": tags}

    filler = "the video deck slide caption export asset file frame"
    corpus = [_r(f"R-DEMO-1{i:02d}", f"Editing a {filler} number {i}.") for i in range(20)]
    rare = _r("R-DEMO-200", "Chromatic aberration is applied.")
    padded = _r("R-DEMO-201", f"Editing a {filler} with captions and every common word above.")
    rules = corpus + [rare, padded]
    task = "chromatic aberration on a video deck slide caption frame"
    order = [r["id"] for _, r in rank_for(task, rules)]
    assert order.index("R-DEMO-200") < order.index("R-DEMO-201"), order[:5]
    # and the raw shared-word count this replaced would have got it backwards
    tw = _words(task)
    assert len(tw & rule_words(padded)) > len(tw & rule_words(rare)), "regression guard is vacuous"
    print("selftest: rank_for prefers the rarer-term match ok")

    print("selftest: PASS")


def main():
    if "--selftest" in sys.argv:
        demo()
        return
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)

    x = sp.add_parser("get"); x.add_argument("id"); x.set_defaults(f=cmd_get)
    x = sp.add_parser("find"); x.add_argument("text"); x.set_defaults(f=cmd_find)
    x = sp.add_parser("list")
    x.add_argument("--pack"); x.add_argument("--strength", choices=["binding", "advisory"]); x.add_argument("--tag")
    x.set_defaults(f=cmd_list)
    x = sp.add_parser("for"); x.add_argument("--task", required=True); x.set_defaults(f=cmd_for)
    sp.add_parser("index").set_defaults(f=cmd_index)
    sp.add_parser("check").set_defaults(f=cmd_check)

    a = ap.parse_args()
    if not os.path.isfile(os.path.join(ROOT, "kb", "kb.json")):
        sys.exit(f"no kb/kb.json in {ROOT} (project = BOOK_ROOT or cwd): it names the database and the rules folder; kb.py init writes a template")
    try:
        a.f(a)
    except RuleError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
