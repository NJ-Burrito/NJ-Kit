#!/usr/bin/env python3
"""heal.py -- self-repair layer: gate fails -> classify -> SAFE repair or exact manual advice -> re-run THAT gate -> log. PYTHONUTF8=1.

    heal.py <stage> [--force-edit]   stage = pages teach entries banks rules pdf
    heal.py report                   heal measurements from audit/heal.jsonl
    heal.py --selftest

Project = BOOK_ROOT or cwd. Exit 0 = gate green (clean or healed); 1 = still failing (manual / refused).
Accuracy rule: heal never weakens a gate. The ONLY auto-repair is glyph-gap (typographic character -> ASCII twin in pages,
backed up first). Claims, keys, quotes, bases and audit results are ADVISE-only; --force-edit on them is REFUSED and logged.
Log: audit/heal.jsonl, one JSON line per run: ts stage class action(clean|healed|manual|refused) regate_rc resolved source note.
"""
import json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("BOOK_ROOT") or os.getcwd())

GATES = {  # stage -> argv after the interpreter (script names resolved in HERE; rules.py in the project or nj-evidence)
    "pages": ["check_pages.py"], "teach": ["check_teach.py"],
    "entries": ["audit_sample.py", "check", "--entries"], "banks": ["audit_sample.py", "check", "--banks"],
    "rules": ["@rules.py", "check"], "pdf": ["check_report.py"],
}
SAFE = {"‟": "“", "→": "->", "←": "<-", "≥": ">=", "≤": "<=", "≈": "~"}  # meaning-preserving
# (class, stage, regex on gate output, advice). First match wins. The advise classes are never auto-edited.
CLASSES = [
    ("glyph-gap", "pdf", r"glyphs: not covered", "SAFE chars (%s) are mapped in pages, backed up; other chars: replace by hand with a Thmanyah-covered form. Then rebuild the report and run `check_pages.py --stamp` for the twin."),
    ("tounicode", "pdf", r"(?i)tounicode|pdftotext|extract", "Arabic PDF extraction broken: re-extract with poppler `pdftotext`; if copy-text is wrong, repair the ToUnicode map via pdf-typography, rebuild, re-run check_report.py."),
    ("rtl-title", "pdf", r"(?i)locate_pages|title.*(not found|match)|bookmark", "RTL title not matched: fix build_report.locate_pages to compare titles in logical order (strip bidi marks), rebuild, re-run check_report.py."),
    ("bank-basis", "banks", r"(?i)miss|FAIL", "Each missed item: rewrite `basis:` so it names the fact that picks the key (page-template section 4), basis first, then the item; never edit the key. Redraw only per the stop rule (no third draw)."),
    ("verifier-weak", "entries", r"(?i)weak", "Verifier says claim is wider than its quote: amend the claim NARROWER or leave it draft/retract and add a new entry; never keep the wide claim."),
]
ADVISE_ONLY = {"tounicode", "rtl-title", "bank-basis", "verifier-weak"}


def gate_cmd(stage, root):
    a = list(GATES[stage])
    if a[0] == "@rules.py":
        p = root / "scripts" / "rules.py"
        a[0] = str(p if p.is_file() else HERE.parents[1] / "nj-evidence" / "scripts" / "rules.py")
    else:
        a[0] = str(HERE / a[0])
    return [sys.executable] + a


def run_gate(stage, root):
    p = subprocess.run(gate_cmd(stage, root), cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env=dict(os.environ, PYTHONUTF8="1", BOOK_ROOT=str(root)), timeout=1800)
    return p.returncode, p.stdout + p.stderr


def classify(stage, out):
    for cls, st, rx, advice in CLASSES:
        if st == stage and re.search(rx, out):
            return cls, advice
    return "unknown", "No known class: read the gate output; if it recurs, add a row to reference/known-failures.md and a class here."


def fix_glyphs(root, out):
    """SAFE repair: replace uncovered chars that have an ASCII twin, in the pages trees. -> (changed files, chars left for hand)."""
    chars = re.findall(r"U\+[0-9A-F]{4,6} (\S)", out)
    todo = {c: SAFE[c] for c in chars if c in SAFE}
    left = [c for c in chars if c not in SAFE]
    cfg = json.loads((root / "book.json").read_text(encoding="utf-8"))
    changed = []
    bak = root / ".agent-ops" / "heal" / "backup" / time.strftime("%Y%m%d-%H%M%S")
    for d in {cfg.get("pages"), cfg.get("twin")} - {None}:
        for f in sorted((root / d).rglob("*.md")):
            t = f.read_text(encoding="utf-8")
            n = t
            for c, r in todo.items():
                n = n.replace(c, r)
            if n != t:
                dst = bak / f.relative_to(root)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst)
                f.write_text(n, encoding="utf-8")
                changed.append(f.relative_to(root).as_posix())
    return changed, left


def log(root, **rec):
    rec = dict(ts=time.strftime("%Y-%m-%dT%H:%M:%S"), resolved=rec.get("action") in ("clean", "healed"), source="run", **rec)
    p = root / "audit" / "heal.jsonl"
    p.parent.mkdir(exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def heal(stage, root=ROOT, gate=None, force_edit=False):
    gate = gate or (lambda: run_gate(stage, root))
    rc, out = gate()
    if rc == 0:
        print(f"{stage}: gate green, nothing to heal")
        return log(root, stage=stage, **{"class": "none"}, action="clean", regate_rc=None, note="gate green")
    cls, advice = classify(stage, out)
    if force_edit and cls in ADVISE_ONLY:
        print(f"{stage}: REFUSED. {cls} is a content repair (claims/keys/quotes/basis/audit); heal never edits those.\n  manual: {advice}")
        return log(root, stage=stage, **{"class": cls}, action="refused", regate_rc=None, note="force-edit refused; " + advice)
    if cls == "glyph-gap":
        advice = advice % " ".join(SAFE)
        changed, left = fix_glyphs(root, out)
        if changed:
            rc2, _ = gate()
            print(f"{stage}: glyph-gap, edited {changed}; re-gate rc={rc2}" + (f"; by hand: {left}" if left else ""))
            return log(root, stage=stage, **{"class": cls}, action="healed" if rc2 == 0 else "manual", regate_rc=rc2,
                       note=f"edited {changed}; left {left}; " + ("" if rc2 == 0 else "rebuild output then re-run; ") + advice)
    print(f"{stage}: {cls}, manual repair:\n  {advice}\n--- gate output (tail) ---\n" + out[-800:])
    return log(root, stage=stage, **{"class": cls}, action="manual", regate_rc=None, note=advice)


def report(root=ROOT):
    p = root / "audit" / "heal.jsonl"
    R = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.is_file() else []
    att = [r for r in R if r["action"] != "clean"]
    n = lambda a: sum(r["action"] == a for r in att)
    last = {}
    for r in R:
        last[r["stage"]] = r
    open_ = [r for r in last.values() if not r.get("resolved")]
    s = {"runs": len(R), "attempts": len(att), "healed": n("healed"), "manual": n("manual"), "refused": n("refused"),
         "heal_rate": round(n("healed") / len(att), 2) if att else None,
         "stages_rerun": sum(r.get("regate_rc") is not None for r in R), "open_items": len(open_),
         "by_class": {c: sum(r["class"] == c for r in att) for c in sorted({r["class"] for r in att})},
         "open": [f'{r["stage"]}/{r["class"]}' for r in open_]}
    print(json.dumps(s, ensure_ascii=False, indent=1))
    return s


def selftest():
    d = Path(tempfile.mkdtemp())
    try:
        (d / "pages").mkdir()
        (d / "book.json").write_text('{"pages":"pages"}')
        f = d / "pages" / "a.md"
        f.write_text("say ‟hi” and x ≥ 5 and → and ☃\n", encoding="utf-8")

        def gate():  # stands in for check_report: fails while an uncovered char with an ASCII twin is present
            bad = [c for c in f.read_text(encoding="utf-8") if c in SAFE]
            return (1, "FAIL glyphs: not covered: " + " ".join(f"U+{ord(c):04X} {c}" for c in bad)) if bad else (0, "ok")
        assert classify("pdf", "FAIL glyphs: not covered: U+201F ‟")[0] == "glyph-gap"
        assert classify("banks", "FAIL audit banks misses=3")[0] == "bank-basis" and classify("rules", "x")[0] == "unknown"
        r = heal("pdf", d, gate)
        assert r["action"] == "healed" and r["regate_rc"] == 0, r
        t = f.read_text(encoding="utf-8")
        assert "‟" not in t and ">= 5" in t and "☃" in t, "only SAFE chars are touched"
        assert list((d / ".agent-ops" / "heal" / "backup").rglob("a.md")), "backup missing"
        assert heal("pdf", d, gate)["action"] == "clean"
        assert heal("banks", d, lambda: (1, "FAIL misses=1"), force_edit=True)["action"] == "refused"
        assert heal("banks", d, lambda: (1, "FAIL misses=1"))["action"] == "manual"
        s = report(d)
        assert s["attempts"] == 3 and s["healed"] == 1 and s["manual"] == 1 and s["refused"] == 1 and s["open_items"] == 1 and s["heal_rate"] == 0.33, s
        assert heal("banks", d, lambda: (0, "ok"))["action"] == "clean" and report(d)["open_items"] == 0
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("heal selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        selftest()
    elif a[:1] == ["report"]:
        report()
    elif a and a[0] in GATES:
        sys.exit(0 if heal(a[0], force_edit="--force-edit" in a)["action"] in ("clean", "healed") else 1)
    else:
        print(__doc__)
        sys.exit(2)
