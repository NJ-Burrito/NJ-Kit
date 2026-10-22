#!/usr/bin/env python3
"""
collect.py — the director runs this ONCE, after every worker has reported.

Reads every <root>/artifacts/<task>/results/*.json written by report.py and
prints one line per worker. That single tool call replaces reading N reports:
the detail stays in the files, the decision comes off this table
(nj-delegate §6, client rule R2, 2026-09-14).

    python collect.py --task srs-v34
    python collect.py --task srs-v34 --json     # machine-readable, same data

Exit code 0 when every worker is "ok", 1 when any is partial/blocked/failed or
no result files exist — so the one line the director reads is trustworthy.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def one_line(rec: dict) -> str:
    gates = "; ".join(rec.get("gates") or []) or "—"
    left = "; ".join(rec.get("leftovers") or []) or "none"
    art = ", ".join(rec.get("artefacts") or []) or "—"
    return (
        f"{rec.get('worker','?'):<18} {rec.get('status','?'):<8} "
        f"files={len(rec.get('files') or []):<3} gates={gates} | "
        f"artefacts={art} | leftovers={left} | detail={rec.get('detail') or '—'}"
    )


def main() -> int:
    p = argparse.ArgumentParser(description="Print every worker's one-line result.")
    p.add_argument("--task", required=True)
    p.add_argument("--root", default=".", help="repo root that holds artifacts/ (default: cwd)")
    p.add_argument("--json", action="store_true", help="print the records as JSON instead")
    a = p.parse_args()

    d = Path(a.root).resolve() / "artifacts" / a.task / "results"
    files = sorted(d.glob("*.json")) if d.exists() else []
    if not files:
        print(f"NO RESULTS  {d}")
        return 1

    records, bad = [], []
    for f in files:
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            bad.append(f"{f.name}: {exc}")
            continue
        records.append(rec)

    if a.json:
        print(json.dumps(records, ensure_ascii=False, indent=1))
    else:
        for rec in records:
            print(one_line(rec))
        for line in bad:
            print(f"UNREADABLE  {line}")

    not_ok = [r for r in records if r.get("status") != "ok"] 
    print(f"{len(records)} workers, {len(records) - len(not_ok)} ok, "
          f"{len(not_ok)} needing attention, {len(bad)} unreadable")
    return 1 if (not_ok or bad) else 0


if __name__ == "__main__":
    raise SystemExit(main())
