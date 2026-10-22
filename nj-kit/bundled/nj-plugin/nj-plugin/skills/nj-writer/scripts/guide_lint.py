#!/usr/bin/env python
"""guide_lint.py — checks NARRATION.md itself, stdlib only:
  1. every prose rule bullet ("- **...") ends with a recognised tag
  2. every [f##] id cited exists in narration-knowledge-2026-09-21.json
  3. no id is used as `hard_threshold` unless its own use_as == hard_threshold
  4. the Matrix json block parses

Prints one TOTALS line at the end; that line is the gate.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _matrix import load_matrix  # noqa: E402

KNOWLEDGE_PATH = (
    Path(__file__).resolve().parents[4]
    / "ENSERA" / "artifacts" / "research" / "narration-knowledge-2026-09-21.json"
)

TAG_RE = re.compile(
    r"\[(?:f\d+(?:\s*—\s*hard_threshold)?(?:,\s*f\d+)*"
    r"|house default[^\]]*"
    r"|the owner,\s*2026-09-21"
    r"|measured\s*2026-09-21[^\]]*"
    r"|needs_voiced_ab[^\]]*)\]",
    re.I,
)
ID_RE = re.compile(r"f(\d+)")
HARD_RE = re.compile(r"\[f(\d+)\s*—\s*hard_threshold\]", re.I)
BULLET_RE = re.compile(r"^\s*-\s+\*\*")


def load_knowledge():
    if not KNOWLEDGE_PATH.exists():
        # fall back: caller may pass a path via env or the file may have moved
        candidates = list(Path.home() / "Desktop" / "ENSERA" / "artifacts" / "research".glob("narration-knowledge-*.json"))
        if not candidates:
            raise FileNotFoundError(f"knowledge file not found: {KNOWLEDGE_PATH}")
        path = candidates[0]
    else:
        path = KNOWLEDGE_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    findings = {f["id"]: f for f in data["findings"]}
    return findings


def lint(md_path, findings):
    text = Path(md_path).read_text(encoding="utf-8")
    # only lint prose bullets before the Matrix heading (the matrix's own
    # numeric fields are validated separately via their own _source suffix)
    prose = re.split(r"^## Matrix \(machine-readable\)", text, flags=re.M)[0]
    lines = prose.splitlines()

    # group each "- **" bullet with its wrapped continuation lines (until the
    # next bullet, a blank line, or a heading)
    bullets = []
    cur = None
    for l in lines:
        if BULLET_RE.match(l):
            if cur is not None:
                bullets.append(cur)
            cur = l
        elif cur is not None:
            if not l.strip() or l.startswith("#"):
                bullets.append(cur)
                cur = None
            else:
                cur += " " + l.strip()
    if cur is not None:
        bullets.append(cur)

    untagged = [l for l in bullets if not TAG_RE.search(l)]
    unknown_ids = set()
    hard_threshold_misuse = []
    for l in bullets:
        for m in ID_RE.finditer(l):
            fid = "f" + m.group(1)
            if fid not in findings:
                unknown_ids.add(fid)
    for m in HARD_RE.finditer(prose):
        fid = "f" + m.group(1)
        use_as = findings.get(fid, {}).get("use_as")
        if use_as != "hard_threshold":
            hard_threshold_misuse.append(f"{fid} used as hard_threshold but use_as={use_as!r}")

    matrix_ok = True
    matrix_err = None
    try:
        load_matrix(md_path)
    except Exception as e:  # noqa: BLE001
        matrix_ok = False
        matrix_err = str(e)

    return {
        "bullets": len(bullets),
        "untagged": untagged,
        "unknown_ids": sorted(unknown_ids),
        "hard_threshold_misuse": hard_threshold_misuse,
        "matrix_ok": matrix_ok,
        "matrix_err": matrix_err,
    }


def main(argv):
    md_path = argv[1] if len(argv) > 1 else str(
        Path(__file__).resolve().parent.parent / "NARRATION.md"
    )
    findings = load_knowledge()
    r = lint(md_path, findings)
    if r["untagged"]:
        print("UNTAGGED RULE LINES:")
        for l in r["untagged"]:
            print("  " + l.strip()[:100])
    if r["unknown_ids"]:
        print("UNKNOWN IDS: " + ", ".join(r["unknown_ids"]))
    if r["hard_threshold_misuse"]:
        print("HARD-THRESHOLD MISUSE: " + "; ".join(r["hard_threshold_misuse"]))
    if not r["matrix_ok"]:
        print("MATRIX PARSE ERROR: " + str(r["matrix_err"]))
    print(
        "TOTALS: bullets=%d untagged=%d unknown_ids=%d hard_threshold_misuse=%d matrix_parses=%s"
        % (
            r["bullets"],
            len(r["untagged"]),
            len(r["unknown_ids"]),
            len(r["hard_threshold_misuse"]),
            r["matrix_ok"],
        )
    )
    ok = not r["untagged"] and not r["unknown_ids"] and not r["hard_threshold_misuse"] and r["matrix_ok"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
