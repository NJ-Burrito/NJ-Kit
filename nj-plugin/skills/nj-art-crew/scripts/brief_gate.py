#!/usr/bin/env python3
"""brief_gate: fail a crew brief that is not ready to launch.

    python brief_gate.py <brief.md> [<brief.md> ...]   # findings, then PASS or FAIL
    python brief_gate.py --selftest                    # proves each check still fires

Checks (per brief): no unfilled <FIELD> left from templates/crew-brief.md; the five sections WHERE, READ FIRST,
QUALITY BAR, BUILD AND CHECK, REPORT exist; one "Edit ONLY `<file>`" line; a render command ("ONLY with: `...`");
the safety words (NEVER run, never push). Across briefs: no two crews own the same file.
"""
import re
import sys
from pathlib import Path

SECTIONS = ["WHERE", "READ FIRST", "QUALITY BAR", "BUILD AND CHECK", "REPORT"]
FIELD = re.compile(r"<[A-Z][A-Z0-9 .,/'_:-]{2,}>")
EDIT = re.compile(r"Edit ONLY `([^`]+)`")
RENDER = re.compile(r"ONLY with:\s*`([^`]+)`")


def norm(p: str) -> str:
    return p.replace("\\", "/").strip().lower()


def check(name: str, text: str) -> tuple[list[str], str | None]:
    errs = []
    for i, line in enumerate(text.splitlines(), 1):
        for m in FIELD.finditer(line):
            errs.append(f"{name}:{i}: unfilled field {m.group(0)}")
    for s in SECTIONS:
        if not re.search(rf"^{re.escape(s)}\b", text, re.M):
            errs.append(f"{name}: missing section {s}")
    edits = EDIT.findall(text)
    if len(edits) != 1:
        errs.append(f"{name}: need exactly one 'Edit ONLY `<file>`' line, found {len(edits)}")
    if not RENDER.search(text):
        errs.append(f"{name}: no render command ('See your work ONLY with: `...`')")
    for word in ("NEVER run", "never push"):
        if word.lower() not in text.lower():
            errs.append(f"{name}: safety rule missing: {word!r}")
    return errs, (norm(edits[0]) if len(edits) == 1 else None)


def run(paths: list[Path]) -> int:
    errs, owners = [], {}
    for p in paths:
        e, f = check(p.name, p.read_text(encoding="utf-8"))
        errs += e
        if f:
            if f in owners:
                errs.append(f"{p.name}: file {f} is also owned by {owners[f]} (two crews, one file)")
            owners[f] = p.name
    for e in errs:
        print("FAIL", e)
    print(f"{'FAIL' if errs else 'PASS'}: {len(paths)} brief(s), {len(errs)} finding(s)")
    return 1 if errs else 0


GOOD = """You are the crew for ONE piece of Demo (web). Your piece: **fan** (variants: 0, 1).

WHERE
- Edit ONLY `src/fan.js`. Never push, never merge.

READ FIRST
- design/contract.md

QUALITY BAR
- Light from top-left.

BUILD AND CHECK
- See your work ONLY with: `node render.js --render fan out/`.
- NEVER run the real deploy.

REPORT (at most 25 lines): STATUS.
"""


def selftest() -> int:
    bad = {
        "unfilled": GOOD.replace("Demo", "<PROJECT>"),
        "section": GOOD.replace("QUALITY BAR", "BAR"),
        "no-edit": GOOD.replace("Edit ONLY `src/fan.js`", "Edit the fan"),
        "no-render": GOOD.replace("ONLY with:", "with:"),
        "no-safety": GOOD.replace("NEVER run", "do not run"),
    }
    ok = not check("good", GOOD)[0]
    print(("ok  " if ok else "BAD ") + "good brief passes")
    for k, t in bad.items():
        hit = bool(check(k, t)[0])
        ok &= hit
        print(("ok  " if hit else "BAD ") + f"{k} fails")
    import contextlib
    import io
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        a, b = Path(d) / "a.md", Path(d) / "b.md"
        a.write_text(GOOD, encoding="utf-8")
        b.write_text(GOOD, encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            dup = run([a, b]) == 1 and run([a]) == 0
    ok &= dup
    print(("ok  " if dup else "BAD ") + "same file in two briefs is detected")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--selftest"]:
        sys.exit(selftest())
    if not args:
        print(__doc__)
        sys.exit(2)
    sys.exit(run([Path(a) for a in args]))
