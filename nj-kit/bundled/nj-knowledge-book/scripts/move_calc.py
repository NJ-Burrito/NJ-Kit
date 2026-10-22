#!/usr/bin/env python3
"""move_calc.py -- migrate `calc:` lines out of the learner-facing banks into the answer keys. (stdlib) PYTHONUTF8=1 assumed.

    move_calc.py             dry run: say what would move
    move_calc.py --apply     move it (atomic file writes), then run check_teach.py
    move_calc.py --selftest

A `calc:` line under a question's stem shows the method (`60 / (60 + 20)`). check_teach fails it; the calc belongs in the question's
block of <slug>.key.md, after its key line and its why-not / rubric / calc / basis lines. This moves every `calc:` line of
<practice>/*.md and <practice-twin>/*.md (book.json "practice" / "practice_twin", default practice-<suffix of twin>) into the
matching question's block of the sibling .key.md, removes it from the questions file and changes NOTHING else (bytes, line endings,
order). Idempotent: a second run finds nothing; a calc already present in the key block with the same text is simply dropped from the
questions file. Listed, never applied: a question with no key line in the key file, a missing key file, a different calc already in the
key block. Exit 1 when anything was listed.
"""
import os, re, sys, tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_pages as cp
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = cp.ROOT
CALC = re.compile(r"^\s*(?:[-*]\s*)?calc\s*:\s*(.*?)\s*$", re.I)
QHEAD = re.compile(r"^###\s+(\S+)\s*$")


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def write_atomic(p, text):
    fd, tmp = tempfile.mkstemp(dir=str(Path(p).parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    os.replace(tmp, p)


def key_block(lines, qid):
    """(index of qid's key line, index just after its block) or None. The block = the key line + its why-not / rubric / calc / basis /
    indented continuation lines."""
    for i, ln in enumerate(lines):
        m = cp._KEYLINE.match(ln.rstrip("\r\n")) or cp._ESSAYKEY.match(ln.rstrip("\r\n"))
        if m and m.group(1) == qid and not cp._KEYEXTRA.match(ln.rstrip("\r\n")):
            j = i + 1
            while j < len(lines):
                body = lines[j].rstrip("\r\n")
                if cp._KEYEXTRA.match(body) or (body[:1] in (" ", "\t") and body.strip()):
                    j += 1
                else:
                    break
            return i, j
    return None


def move_pair(qtext, ktext):
    """-> (new questions text, new key text, moved, [(qid, reason)] listed)."""
    qlines = qtext.splitlines(keepends=True)
    klines = ktext.splitlines(keepends=True) if ktext is not None else None
    nl = "\r\n" if ktext and "\r\n" in ktext else "\n"
    fence, cur, found = False, None, []
    for i, ln in enumerate(qlines):
        s = ln.lstrip()
        if s.startswith("```") or s.startswith("~~~"):
            fence = not fence
            continue
        if fence:
            continue
        h = QHEAD.match(ln.rstrip("\r\n"))
        if h:
            cur = h.group(1)
            continue
        m = CALC.match(ln.rstrip("\r\n"))
        if m and cur:
            found.append((cur, m.group(1), i))
    drop, moved, listed = set(), 0, []
    for qid, val, i in found:
        if klines is None:
            listed.append((qid, "no key file beside the questions file")); continue
        blk = key_block(klines, qid)
        if blk is None:
            listed.append((qid, "no key line for this question in the key file")); continue
        start, end = blk
        have = [CALC.match(klines[k].rstrip("\r\n")) for k in range(start + 1, end)]
        have = [m.group(1) for m in have if m]
        if have:
            if val in have:
                drop.add(i)  # already there: the questions file just forgets it
                continue
            listed.append((qid, f"the key block already holds a different calc ('{have[0]}')")); continue
        if not klines[end - 1].endswith("\n"):
            klines[end - 1] += nl
        klines.insert(end, f"calc: {val}{nl}")
        drop.add(i); moved += 1
    new_q = "".join(ln for i, ln in enumerate(qlines) if i not in drop)
    return new_q, ("".join(klines) if klines is not None else None), moved, listed


def bank_dirs(cfg, root):
    dirs = [cfg.get("practice") or "practice"]
    tw = cp.twin_bank_dir(cfg)
    if tw:
        dirs.append(tw)
    return [Path(root) / d for d in dirs if (Path(root) / d).is_dir()]


def run(root, cfg, apply):
    """-> (files_changed, calc_moved, listed [(file, qid, reason)])."""
    files = moved = 0
    listed_all = []
    for d in bank_dirs(cfg, root):
        for q in sorted(d.glob("*.md")):
            if q.name.startswith("_") or q.name.endswith(".key.md"):
                continue
            qtext = read(q)
            if not any(CALC.match(l.rstrip("\r\n")) for l in qtext.splitlines()):
                continue
            kp = q.with_suffix(".key.md")
            ktext = read(kp) if kp.is_file() else None
            nq, nk, n, listed = move_pair(qtext, ktext)
            listed_all += [(str(q.relative_to(root)), qid, why) for qid, why in listed]
            if nq == qtext and (nk == ktext):
                continue
            files += 1 + (nk != ktext)
            moved += n
            print(f"{'moved ' if apply else 'would move'} {n} calc line(s): {q.relative_to(root)} -> {kp.relative_to(root)}")
            if apply:
                if nk != ktext:
                    write_atomic(kp, nk)  # key file first: a crash between the two leaves the calc in BOTH files, never in neither
                write_atomic(q, nq)
    return files, moved, listed_all


def selftest():
    import shutil
    d = Path(tempfile.mkdtemp())
    try:
        (d / "practice").mkdir(); (d / "practice-ar").mkdir()
        cfg = {"practice": "practice", "twin": "knowledge-ar"}
        q_en = ("# Bank\r\n\r\n### Q-1\r\nobjective: T-1\r\nlevel: K3\r\n- calc: 60 / (60 + 20)\r\nstem: Rate?\r\na) 75% b) 25% c) 80%\r\n\r\n"
                "### Q-2\r\nobjective: T-1\r\nlevel: K1\r\nStem two?\r\na) x b) y c) z\r\n\r\n### Q-3\r\nobjective: T-1\r\nlevel: K3\r\ncalc: 2 + 2\r\nFour?\r\na) 4 b) 5 c) 6\r\n"
                "```text\r\ncalc: not a real one inside a fence\r\n```\r\n")
        k_en = "# Key\r\n\r\nQ-1: a -- because\r\nwhy-not: b = x; c = y\r\nQ-2: b\r\nQ-3: a\r\nbasis: KB#5\r\n"
        (d / "practice" / "bk.md").write_bytes(q_en.encode()); (d / "practice" / "bk.key.md").write_bytes(k_en.encode())
        (d / "practice-ar" / "bk.md").write_bytes(q_en.replace("Rate?", "kam?").encode()); (d / "practice-ar" / "bk.key.md").write_bytes(k_en.encode())
        # a bank with problems: no key block for Q-1, a conflicting calc for Q-2, and a bank with no key file
        (d / "practice" / "bad.md").write_text("### Q-1\ncalc: 1 + 1\nS?\n### Q-2\ncalc: 3 + 3\nS?\n", encoding="utf-8")
        (d / "practice" / "bad.key.md").write_text("Q-2: a\ncalc: 9 + 9\n", encoding="utf-8")
        (d / "practice" / "nokey.md").write_text("### Q-1\ncalc: 1 + 1\nS?\n", encoding="utf-8")
        snap = {p.name: p.read_bytes() for p in (d / "practice").glob("*") } | {"ar-" + p.name: p.read_bytes() for p in (d / "practice-ar").glob("*")}
        files, moved, listed = run(d, cfg, apply=False)
        assert files == 4 and moved == 4 and len(listed) == 3, (files, moved, listed)  # 2 calc in bk.md + 2 in practice-ar/bk.md; 3 listed in bad / nokey
        assert snap == {p.name: p.read_bytes() for p in (d / "practice").glob("*")} | {"ar-" + p.name: p.read_bytes() for p in (d / "practice-ar").glob("*")}, "the dry run changed a file"
        files, moved, listed = run(d, cfg, apply=True)
        assert (files, moved) == (4, 4) and sorted(w for _, _, w in listed) == sorted(["no key line for this question in the key file", "the key block already holds a different calc ('9 + 9')", "no key file beside the questions file"]), listed
        nq = (d / "practice" / "bk.md").read_bytes().decode()
        nk = (d / "practice" / "bk.key.md").read_bytes().decode()
        assert nq == q_en.replace("- calc: 60 / (60 + 20)\r\n", "").replace("calc: 2 + 2\r\n", ""), "everything but the two calc lines must be byte-identical (CRLF kept, the fenced calc untouched)"
        assert "calc: not a real one inside a fence" in nq
        assert nk == "# Key\r\n\r\nQ-1: a -- because\r\nwhy-not: b = x; c = y\r\ncalc: 60 / (60 + 20)\r\nQ-2: b\r\nQ-3: a\r\nbasis: KB#5\r\ncalc: 2 + 2\r\n", repr(nk)
        assert (d / "practice-ar" / "bk.key.md").read_bytes().decode() == nk, "the twin bank moves the same way"
        assert (d / "practice" / "bad.md").read_text(encoding="utf-8").count("calc:") == 2 and (d / "practice" / "nokey.md").read_text(encoding="utf-8").count("calc:") == 1, "listed calc lines stay where they are"
        b = cp.load_bank(d / "practice" / "bk.md")
        assert [q["calc"] for q in b["questions"]] == ["60 / (60 + 20)", "", "2 + 2"] and not any(q["calc_in_stem"] for q in b["questions"]), "parse_bank reads the moved calc from the key block"
        assert [q["calc"] for q in cp.load_bank(d / "practice-ar" / "bk.md")["questions"]] == ["60 / (60 + 20)", "", "2 + 2"]
        files, moved, listed = run(d, cfg, apply=True)
        assert (files, moved) == (0, 0) and len(listed) == 3, "idempotent: a second run moves nothing (the three problem cases are listed again)"
        assert not list((d / "practice").glob("*.tmp")), "no temp file left behind"
        # a calc already in the key block (same text) is just dropped from the questions file
        (d / "practice" / "dup.md").write_text("### Q-1\ncalc: 5 + 5\nS?\n", encoding="utf-8")
        (d / "practice" / "dup.key.md").write_text("Q-1: a\ncalc: 5 + 5\n", encoding="utf-8")
        files, moved, listed = run(d, cfg, apply=True)
        assert "calc:" not in (d / "practice" / "dup.md").read_text(encoding="utf-8") and (d / "practice" / "dup.key.md").read_text(encoding="utf-8") == "Q-1: a\ncalc: 5 + 5\n" and moved == 0
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("selftest ok"); return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    try:
        cfg = cp.load_cfg()
    except cp.ConfigError as e:
        print(f"FAIL {e}"); return 1
    apply = "--apply" in argv
    files, moved, listed = run(ROOT, cfg, apply)
    for f, qid, why in listed:
        print(f"LISTED {f} {qid}: {why}")
    print(f"move_calc: {files} file(s) {'changed' if apply else 'would change'}, {moved} calc line(s) {'moved' if apply else 'to move'}, {len(listed)} listed not moved"
          + ("" if apply or not moved else "  (dry run: --apply to move)"))
    return 1 if listed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
