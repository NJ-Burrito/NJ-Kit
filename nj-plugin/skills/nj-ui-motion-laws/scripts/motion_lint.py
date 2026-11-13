#!/usr/bin/env python3
"""Lint UI motion against nj-ui-motion-laws: M1 >300ms, M2 linear, M3 transition: all, M4 no reduced-motion.

    python motion_lint.py <file or folder> ...   # findings, then PASS or FAIL
    python motion_lint.py --selftest
"""
import re
import sys
from pathlib import Path

EXT = {".css", ".scss", ".less", ".html", ".vue", ".svelte", ".jsx", ".tsx", ".js", ".ts"}
SKIP = {"node_modules", ".git", "dist", "build", ".next", "vendor"}
DECL = re.compile(r"(?:transition|animation)(?:-duration|-timing-function)?\s*[:=]\s*([^;}\n]+)", re.I)
DUR = re.compile(r"(?<![\w.-])(\d*\.?\d+)(ms|s)\b")
MAX_MS = 300


def lint_text(name, text):
    out, animates = [], False
    for i, line in enumerate(text.splitlines(), 1):
        if "motion-ok" in line:
            for _ in DECL.finditer(line):
                animates = True
            continue
        for m in DECL.finditer(line):
            animates = True
            v = m.group(1)
            for item in v.split(","):  # first time per item is the duration, the second is a delay
                d = DUR.search(item)
                ms = d and float(d.group(1)) * (1000 if d.group(2) == "s" else 1)
                if ms and ms > MAX_MS and "infinite" not in item:  # loops are ambient, not response time
                    out.append(f"{name}:{i} M1 {ms:g}ms > {MAX_MS}ms (L9 snappy timing)")
            if re.search(r"\blinear\b", v) and "infinite" not in v:
                out.append(f"{name}:{i} M2 linear easing (L6 slow in and slow out)")
            if re.match(r"\s*['\"]?all\b", v) and "transition" in m.group(0).lower():
                out.append(f"{name}:{i} M3 transition: all, name the properties")
        if re.search(r"@keyframes|\.animate\(", line):
            animates = True
    return out, animates, "prefers-reduced-motion" in text


def lint(paths):
    files = []
    for p in map(Path, paths):
        if p.is_dir():
            files += [f for f in p.rglob("*") if f.suffix in EXT and not SKIP & set(f.parts)]
        elif p.suffix in EXT:
            files.append(p)
    out, animates, guarded = [], False, False
    for f in files:
        o, a, g = lint_text(str(f), f.read_text(encoding="utf-8", errors="replace"))
        out += o
        animates |= a
        guarded |= g
    if animates and not guarded:
        out.append("M4 motion without any prefers-reduced-motion rule in the scanned files")
    return out, len(files)


def selftest():
    cases = [
        ("a{transition:transform 200ms ease-out}", []),
        ("a{transition:transform 450ms ease}", ["M1"]),
        ("a{transition:opacity .5s linear}", ["M1", "M2"]),
        ("a{transition: all 150ms}", ["M3"]),
        ("a{animation: spin 1s linear infinite}", []),
        ("a{transition: opacity 200ms ease 1600ms, transform .2s}", []),
        ("a{transition: opacity 200ms, transform .4s ease}", ["M1"]),
        ("a{animation-duration: 0.2s}", []),
        ("a{transition: transform 600ms} /* motion-ok: page */", []),
        ("style={{ transition: 'all 200ms' }}", ["M3"]),
    ]
    bad = 0
    for css, want in cases:
        got = [x.split()[1] for x in lint_text("t", css)[0]]
        if got != want:
            bad += 1
            print(f"FAIL {css!r}: got {got}, want {want}")
    _, a, g = lint_text("t", "@keyframes x{} @media (prefers-reduced-motion: reduce){}")
    bad += not (a and g)
    print(f"selftest {len(cases) + 1 - bad}/{len(cases) + 1}")
    return bad


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if "--selftest" in sys.argv:
        bad = selftest()
        print("FAIL" if bad else "PASS")
        return 1 if bad else 0
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    out, n = lint(sys.argv[1:])
    print(*out, sep="\n") if out else None
    print(f"{n} files, {len(out)} findings")
    print("FAIL" if out else "PASS")
    return 1 if out else 0


if __name__ == "__main__":
    sys.exit(main())
