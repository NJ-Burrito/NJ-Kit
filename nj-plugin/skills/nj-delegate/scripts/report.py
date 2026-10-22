#!/usr/bin/env python3
"""
report.py — the last thing a worker runs.

Scripts communicate between models: the worker writes its whole result to a
file, and only the structured block crosses back to the director (nj-delegate
§11.1 rule 4, revised 2026-09-16). Another worker that needs this worker's
output reads the JSON file named below — never a transcript, never a relayed
paste of its content.

    python report.py --task srs-v34 --worker w1-figure --status ok \
        --finding "figure fits A4 landscape after the wrap fix" \
        --files "a.ts,b.ts" --gates "typecheck PASS; fonts PASS" \
        --artefacts "out/srs.pdf" --leftovers "table 6.2 unsplit" \
        --risk "unsplit table may overflow on a longer service" \
        --next "none" --detail artifacts/srs-v34/detail/w1-figure.md

Writes  <root>/artifacts/<task>/results/<worker>.json and prints the
STATUS / FINDING / EVIDENCE / FILES-SYMBOLS / RISK / NEXT ACTION block the
worker pastes as its report — short by default, no raw logs, no word cap when
detail is genuinely needed. Idempotent: re-running overwrites the same file.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

FIELDS = ("files", "gates", "artefacts", "leftovers")


def split(value: str | None) -> list[str]:
    """Comma- or semicolon-separated list -> clean list. Empty -> []."""
    if not value:
        return []
    raw = value.replace(";", ",").split(",")
    return [item.strip() for item in raw if item.strip()]


def main() -> int:
    p = argparse.ArgumentParser(description="Write one worker's result file.")
    p.add_argument("--task", required=True, help="task slug; the folder under artifacts/")
    p.add_argument("--worker", required=True, help="worker slug; the JSON file name")
    p.add_argument("--status", default="ok", choices=["ok", "partial", "blocked", "failed"])
    p.add_argument("--files", default="", help="paths touched, comma-separated")
    p.add_argument("--gates", default="", help="gate lines verbatim, semicolon-separated")
    p.add_argument("--artefacts", default="", help="paths the director may open")
    p.add_argument("--leftovers", default="", help="what was not done, one item each")
    p.add_argument("--detail", default="", help="path to the file holding everything else")
    p.add_argument("--finding", default="", help="what is true now, one or two lines")
    p.add_argument("--risk", default="", help="what could still be wrong, and for whom")
    p.add_argument("--next", dest="next_action", default="",
                   help="the single next executable step, or 'none'")
    p.add_argument("--root", default=".", help="repo root that holds artifacts/ (default: cwd)")
    a = p.parse_args()

    for bad in ("/", "\\", ".."):
        if bad in a.task or bad in a.worker:
            print(f"FAIL  --task/--worker must be plain slugs (got {a.task!r}, {a.worker!r})")
            return 2

    out_dir = Path(a.root).resolve() / "artifacts" / a.task / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{a.worker}.json"

    record = {
        "worker": a.worker,
        "task": a.task,
        "status": a.status,
        "files": split(a.files),
        "gates": split(a.gates),
        "artefacts": split(a.artefacts),
        "leftovers": split(a.leftovers),
        "detail": a.detail.strip(),
        "finding": a.finding.strip(),
        "risk": a.risk.strip(),
        "next_action": a.next_action.strip(),
        "written": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    out.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")

    if a.detail and not Path(a.detail).exists():
        print(f"WARN  --detail path does not exist: {a.detail}")

    def block(label, values):
        values = values or ["—"]
        print(f"{label + ':':15}{values[0]}")
        for extra in values[1:]:
            print(f"{'':15}{extra}")

    print(f"RESULT FILE: {out}")
    block("STATUS", [record["status"]])
    block("FINDING", [record["finding"]] if record["finding"] else [])
    block("EVIDENCE", record["gates"] + record["artefacts"])
    block("FILES-SYMBOLS", record["files"])
    block("RISK", ([record["risk"]] if record["risk"] else []) + record["leftovers"])
    block("NEXT ACTION", [record["next_action"]] if record["next_action"] else [])
    block("DETAIL", [record["detail"]] if record["detail"] else [])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
