#!/usr/bin/env python3
"""Weekly QA-team comparison for the nj-rank «📈 Metrics» tab (the owner 2026-11-05).

Pulls, for every member in <root>/team.json, the Jira Bugs they reported in ALL projects
(whatever Jira returns), keeps one row per Bug (date, project, outcome),
writes <root>/team-metrics.json + a dated copy under <root>/team-metrics-history/, then
rebuilds preview.html. Read-only on Jira. stdlib only.

Why Bugs only: every member files Bugs by hand, so counts compare like for like. The owner's
Tasks are auto-filed by nj-rank (one per work item), so ranking Tasks would not be fair.

Run:  PYTHONUTF8=1 python team_metrics.py [--root DIR]
Schedule it weekly with your OS scheduler (cron, Task Scheduler) if you want the tab kept fresh.
"""
import argparse
import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import nj_rank as nr  # noqa: E402

# Written to <root>/team.json on first run; edit that file to list your team.
DEFAULT_TEAM = [
    {"name": "You", "user": "you@example.com", "me": True},
    {"name": "Teammate", "user": "teammate@example.com"},
]


def bug_row(issue):
    f = issue["fields"]
    status = (f.get("status") or {}).get("name") or ""
    res = (f.get("resolution") or {}).get("name") or ""
    b = {"status": status, "nb": nr.is_not_bug(status, res)}
    return {"d": (f.get("created") or "")[:10], "p": (f.get("project") or {}).get("key") or "?", "g": nr.bug_outcome(b)}


def fetch(jira, team):
    out = []
    for m in team:
        jql = f'reporter = "{nr.esc_jql(m["user"])}" AND issuetype = Bug ORDER BY created ASC'
        bugs = [bug_row(i) for i in jira.search(jql, ["project", "status", "resolution", "created"])]
        out.append({"name": m["name"], "me": bool(m.get("me")), "bugs": bugs})
        print(f'{m["name"]}: {len(bugs)} bugs')
    return out


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=nr.DEFAULT_ROOT)
    a = ap.parse_args(argv)
    root = Path(a.root)
    team_cfg = root / "team.json"
    if not team_cfg.exists():
        nr.write_json(team_cfg, DEFAULT_TEAM)  # edit this file to add or remove people
    team = nr.read_json(team_cfg)
    members = fetch(nr.Jira(nr.load_config()), team)
    doc = {"fetched_at": nr.now_iso(), "members": members}
    nr.write_json(root / "team-metrics.json", doc)
    hist = root / "team-metrics-history"
    os.makedirs(hist, exist_ok=True)
    nr.write_json(hist / f"{dt.date.today().isoformat()}.json", doc)
    nr.write_preview(root)
    print(f"OK team metrics: {len(members)} people, {sum(len(m['bugs']) for m in members)} bugs, preview rebuilt")


if __name__ == "__main__":
    main()
