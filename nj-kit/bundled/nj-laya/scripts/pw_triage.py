#!/usr/bin/env python3
"""Regex-only triage of Playwright failures. stdlib only (per nj-laya rule 13/3).

Classifies each failure text into one of:
  locator-changed, timeout-env, auth-session, assertion, unclassified

Reads either:
  - a Playwright JSON reporter file (--report path/to/results.json), or
  - a directory of test-results/**/error-context.md files (--dir path/to/test-results)

Only the "unclassified" bucket is a Laya candidate (nj-laya rule 13), and only
after >=30 real failures exist.
"""
import argparse
import json
import re
import sys
from pathlib import Path

# ponytail: ordered regex table, first match wins. Add a rule before falling
# back to Laya — that's the whole point of this script.
RULES = [
    ("locator-changed", re.compile(r"(strict mode violation|resolved to \d+ elements|"
                                    r"no element (found|matching)|selector.*not found)", re.I)),
    ("timeout-env", re.compile(r"(timeout \d+ms exceeded|net::ERR_|ECONNREFUSED|"
                                r"page\.goto|navigation timeout)", re.I)),
    ("auth-session", re.compile(r"(401|403|unauthoriz|session expired|login required|"
                                 r"recaptcha)", re.I)),
    ("assertion", re.compile(r"(expect\(.*\)\.|assertion.*failed|toEqual|toBe\(|"
                              r"received.*expected)", re.I)),
]


def classify(text: str) -> str:
    for label, rx in RULES:
        if rx.search(text):
            return label
    return "unclassified"


def _texts_from_json_report(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    out = []

    def walk(suite):
        for spec in suite.get("specs", []):
            for test in spec.get("tests", []):
                for result in test.get("results", []):
                    if result.get("status") in ("failed", "timedOut"):
                        err = result.get("error", {}) or {}
                        msg = err.get("message") or json.dumps(result.get("errors", []))
                        out.append({"id": spec.get("title", "?"), "text": msg})
        for sub in suite.get("suites", []):
            walk(sub)

    for suite in data.get("suites", []):
        walk(suite)
    return out


def _texts_from_dir(path: Path):
    out = []
    for f in path.rglob("error-context.md"):
        out.append({"id": str(f.parent.name), "text": f.read_text(encoding="utf-8", errors="replace")})
    return out


def triage(items):
    buckets = {"locator-changed": [], "timeout-env": [], "auth-session": [], "assertion": [], "unclassified": []}
    for it in items:
        buckets[classify(it["text"])].append(it["id"])
    return buckets


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path, help="Playwright JSON reporter file")
    ap.add_argument("--dir", type=Path, help="directory to search for error-context.md")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return _self_test()

    if args.report:
        items = _texts_from_json_report(args.report)
    elif args.dir:
        items = _texts_from_dir(args.dir)
    else:
        ap.error("need --report, --dir, or --self-test")
        return 2

    buckets = triage(items)
    print(json.dumps(buckets, indent=2, ensure_ascii=False))
    if len(buckets["unclassified"]) >= 30:
        print(f"# {len(buckets['unclassified'])} unclassified failures >= 30 — "
              f"Laya candidate per nj-laya rule 13", file=sys.stderr)
    return 0


def _self_test():
    cases = [
        ("strict mode violation: locator resolved to 2 elements", "locator-changed"),
        ("Timeout 30000ms exceeded while waiting for locator", "timeout-env"),
        ("net::ERR_CONNECTION_REFUSED at https://portal", "timeout-env"),
        ("401 Unauthorized: session expired", "auth-session"),
        ("expect(received).toBe(expected) // received: 1, expected: 2", "assertion"),
        ("some unrelated stack trace with no known shape", "unclassified"),
    ]
    ok = True
    for text, want in cases:
        got = classify(text)
        assert got == want, f"FAIL: {text!r} -> {got}, want {want}"
    buckets = triage([{"id": f"t{i}", "text": t} for i, (t, _) in enumerate(cases)])
    assert sum(len(v) for v in buckets.values()) == len(cases)
    print("pw_triage self-test: OK (6/6 rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
