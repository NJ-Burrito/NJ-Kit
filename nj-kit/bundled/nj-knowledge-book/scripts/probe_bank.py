#!/usr/bin/env python3
"""probe_bank.py -- stem-less probe for practice banks: can the items be answered from the OPTIONS alone? (stdlib). PYTHONUTF8=1 assumed.

    probe_bank.py make  [slug ...]    write audit/probe/<slug>.txt: question ids and options, NO stems, NO keys
    probe_bank.py score [slug ...]    read audit/probe/<slug>.ans (one `Q-id: letter` per line, written by a blind prober that saw only
                                      the .txt), print a table and write audit/probe/SCORE.md
    probe_bank.py --selftest

Project = BOOK_ROOT env or cwd; banks are <practice>/*.md (book.json "practice", default "practice") with keys in <slug>.key.md.
Only single-answer items count: type mcq / not-stem / roman, a one-letter key, at least 3 options (multi-select, matching and
essay items are skipped). Chance for an item is 1/len(options). A bank whose keyed hits exceed 2x the summed chance is GUESSABLE:
its items can be answered from the options alone (length cues, absurd distractors), so it measures test-wise guessing, not knowledge.
book_status.py shows probe=ok | GUESSABLE | none per bank (none = no .ans yet).
"""
import os, re, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_pages as cp
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = cp.ROOT


def probe_dir(root=None):
    return Path(root or ROOT) / "audit" / "probe"


def bank_paths(cfg, root=None, want=()):
    return [p for p in cp.bank_files(cfg, root) if not want or p.stem in want]


def single(q, keys):
    """A single-answer item the probe can score."""
    k = keys.get(q["id"], "")
    return (q.get("type") or "mcq").split("(")[0].lower() in ("mcq", "not-stem", "roman") and len(k) == 1 and len(q["options"]) >= 3


def make_text(bank):
    lines = []
    for q in bank["questions"]:
        if single(q, bank["keys"]):
            lines.append(q["id"])
            lines += [f"  {k}) {v}" for k, v in sorted(q["options"].items())]
    return "\n".join(lines) + "\n"


def score_bank(bank, ans_text):
    """-> (items, hits, chance_sum, flag). flag: GUESSABLE when hits > 2 x chance, else ok."""
    got = dict(re.findall(r"^\s*([\w.\-]+)\s*:\s*([a-h])\b", ans_text, re.M))
    items = [q for q in bank["questions"] if single(q, bank["keys"])]
    hits = sum(1 for q in items if got.get(q["id"]) == bank["keys"][q["id"]])
    chance = sum(1 / len(q["options"]) for q in items)
    return len(items), hits, chance, ("GUESSABLE" if hits > 2 * chance else "ok")


def status(root, slug, cfg=None):
    """'ok' | 'GUESSABLE' | 'none' (no .ans for the bank, or nothing to score) -- what book_status.py shows as probe=."""
    root = Path(root)
    ans = probe_dir(root) / f"{slug}.ans"
    if not ans.is_file():
        return "none"
    cfg = cfg or {}
    bf = root / (cfg.get("practice") or "practice") / f"{slug}.md"
    if not bf.is_file():
        return "none"
    n, hits, chance, flag = score_bank(cp.load_bank(bf), ans.read_text(encoding="utf-8"))
    return flag if n else "none"


def cmd_make(cfg, want):
    out = probe_dir()
    out.mkdir(parents=True, exist_ok=True)
    for p in bank_paths(cfg, ROOT, want):
        text = make_text(cp.load_bank(p))
        (out / f"{p.stem}.txt").write_text(text, encoding="utf-8", newline="\n")
        print(f"{p.stem}: {sum(1 for l in text.splitlines() if l and not l.startswith(' '))} items -> {out / (p.stem + '.txt')}")
    return 0


def cmd_score(cfg, want):
    rows = ["| bank | items | keyed | rate | chance | flag |", "|---|---|---|---|---|---|"]
    bad = 0
    for p in bank_paths(cfg, ROOT, want):
        ans = probe_dir() / f"{p.stem}.ans"
        if not ans.is_file():
            rows.append(f"| {p.stem} | - | - | - | - | NO ANSWERS |")
            continue
        n, hits, chance, flag = score_bank(cp.load_bank(p), ans.read_text(encoding="utf-8"))
        bad += flag == "GUESSABLE"
        rows.append(f"| {p.stem} | {n} | {hits} | {hits / (n or 1):.0%} | {chance / (n or 1):.0%} | {flag if n else 'NO SINGLE-ANSWER ITEMS'} |")
    probe_dir().mkdir(parents=True, exist_ok=True)
    (probe_dir() / "SCORE.md").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(rows))
    return 1 if bad else 0


def selftest():
    import shutil, tempfile
    d = Path(tempfile.mkdtemp())
    try:
        (d / "practice").mkdir()
        qs = ""
        keys = ""
        for i in range(1, 11):  # 10 single-answer items with 4 options, a multi-select item and an essay (both skipped)
            qs += f"### Q-{i}\nobjective: t-1\nlevel: K1\nbasis: KB#1\nSecret stem number {i}?\na) one\nb) two\nc) three\nd) four\n"
            keys += f"Q-{i}: {'abcd'[i % 4]}\n"
        qs += "### Q-11\nobjective: t-1\nlevel: K2\ntype: multi(select 2)\nbasis: KB#1\nWhich two?\na) x\nb) y\nc) z\n### Q-12\nobjective: t-1\nlevel: K5\ntype: essay\nbasis: KB#1\nDiscuss.\n"
        keys += "Q-11: a,c\nQ-12: essay\nrubric: names it\n"
        (d / "practice" / "bk.md").write_text(qs, encoding="utf-8")
        (d / "practice" / "bk.key.md").write_text(keys, encoding="utf-8")
        cfg = {"practice": "practice"}
        bank = cp.load_bank(d / "practice" / "bk.md")
        txt = make_text(bank)
        assert "Secret stem" not in txt and "KB#" not in txt and "Q-1\n  a) one" in txt and "Q-11" not in txt and "Q-12" not in txt, txt
        assert txt.count("\n  a) one") == 10, "ten single-answer items, options listed, multi and essay skipped"
        allright = "".join(f"Q-{i}: {'abcd'[i % 4]}\n" for i in range(1, 11))
        n, hits, chance, flag = score_bank(bank, allright)
        assert (n, hits, flag) == (10, 10, "GUESSABLE") and abs(chance - 2.5) < 1e-9, (n, hits, chance, flag)
        wrong = "".join(f"Q-{i}: {'abcd'[(i + 1) % 4]}\n" for i in range(1, 11))
        assert score_bank(bank, wrong)[3] == "ok" and score_bank(bank, wrong)[1] == 0
        edge = "".join(f"Q-{i}: {'abcd'[i % 4] if i <= 5 else 'abcd'[(i + 1) % 4]}\n" for i in range(1, 11))
        assert score_bank(bank, edge)[1] == 5 and score_bank(bank, edge)[3] == "ok", "5 hits = exactly 2x chance is not above it"
        assert score_bank(bank, edge.replace("Q-6: ", "Q-6: ").replace(f"Q-6: {'abcd'[7 % 4]}", f"Q-6: {'abcd'[6 % 4]}"))[3] == "GUESSABLE", "6 hits > 2x chance"
        assert status(d, "bk", cfg) == "none", "no .ans yet"
        (d / "audit" / "probe").mkdir(parents=True)
        (d / "audit" / "probe" / "bk.ans").write_text(allright, encoding="utf-8")
        assert status(d, "bk", cfg) == "GUESSABLE"
        (d / "audit" / "probe" / "bk.ans").write_text(wrong, encoding="utf-8")
        assert status(d, "bk", cfg) == "ok"
        assert status(d, "missing", cfg) == "none"
        # a bank with only 2-option items has nothing to score
        (d / "practice" / "tiny.md").write_text("### Q-1\nobjective: t-1\nlevel: K1\nbasis: KB#1\nS?\na) x\nb) y\n", encoding="utf-8")
        (d / "practice" / "tiny.key.md").write_text("Q-1: a\n", encoding="utf-8")
        (d / "audit" / "probe" / "tiny.ans").write_text("Q-1: a\n", encoding="utf-8")
        assert status(d, "tiny", cfg) == "none", "2-option items are not probe items"
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("selftest ok"); return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if not argv or argv[0] not in ("make", "score"):
        print(__doc__); return 1
    try:
        cfg = cp.load_cfg()
    except cp.ConfigError as e:
        print(f"FAIL {e}"); return 1
    want = tuple(a for a in argv[1:] if not a.startswith("--"))
    return (cmd_make if argv[0] == "make" else cmd_score)(cfg, want)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
