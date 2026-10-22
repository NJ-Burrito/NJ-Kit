"""Offline fixtures for the --selftest of discover/reconcile/render.
Built from the real 2026-10-15 session (PROJ-997): 27 notes, 16 new keys, 3 existing, 6 rank items.
Verdicts and keys are copied from tracker.json / jira/filed-L1..L4.json; text is shortened."""
from __future__ import annotations
import json, os

VERDICT = {  # note -> verdict (tracker.json, 27 rows)
 **{n: "fixed" for n in "N1 N2 N3 N4 N6 N14 N23 N24 N25 N27".split()},
 **{n: "not-fixed" for n in "N30 N5 N8 N10 N12 N13 N15 N16 N17 N18 N22".split()},
 **{n: "untestable" for n in "N7 N20 N21 N26 N28 N29".split()}}

def _bug(note, key, **kw):
    return dict(note=note, action="filed", key=key, type="Bug", assignee="<jira-user>",
                links=["PROJ-997", "PROJ-598"], attachments=["a.png", "a.txt"], **kw)

# the four on-disk shapes: L1 {rows}, L2 list, L3 {NOTE:{..}}, L4 {NOTE:{..}} (L4 rows lack type/links)
L1 = {"lead": "L1", "rows": [
  dict(note="N5", action="existing", key="PROJ-1369", type="Bug", status="To Do", attachments=[], reason="open Bug covers it"),
  dict(note="N8", action="existing", key="PROJ-1370", type="Bug", status="To Do", attachments=[], reason="open Bug covers it"),
  _bug("N30", "PROJ-2087"), _bug("C", "PROJ-2088")]}
L2 = [_bug("N10", "PROJ-2093"), _bug("N12", "PROJ-2094"), _bug("N15", "PROJ-2095"), _bug("N16", "PROJ-2096"),
      dict(note="N13", action="existing", key="PROJ-1564", attachments=[])]
L3 = {n: _bug(n, k) for n, k in (("N17", "PROJ-2089"), ("N18", "PROJ-2090"), ("N22", "PROJ-2091"))}
L3["BLOCKER"] = _bug("BLOCKER", "PROJ-2092", kind="blocker", priority="High")
L4 = {n: {"note": n, "action": "created", "key": k, "anchor": "BPMN timer node", "assignee": "<jira-user>"} for n, k in
      (("N7", "PROJ-2097"), ("N20", "PROJ-2098"), ("N21", "PROJ-2099"), ("N26", "PROJ-2100"), ("N28", "PROJ-2101"), ("N29", "PROJ-2102"))}

def results():
    return {"notes": {n: {"note": n, "verdict": v, "evidence": "shots/%s.png" % n} for n, v in VERDICT.items()},
            "blockers": [{"title": "signing fails"}]}

def issue(key):
    """Mock of GET /rest/api/2/issue/<key> as the real session left it (strict v2 fields included)."""
    n = int(key.split("-")[1])
    existing = n in (1369, 1370, 1564)
    task = 2097 <= n <= 2102
    blocker = n == 2092
    labels = [] if existing else ["env-staging"] + (["untestable", "wrapup"] if task else [])
    desc = "" if existing else ("الخطورة (Severity): %s\nبيئة: Staging" % ("Blocker" if blocker else "Major"))
    f = {"summary": "S " + key, "issuetype": {"name": "Task" if task else "Bug"}, "status": {"name": "To Do"},
         "assignee": None if existing else {"name": "<jira-user>"}, "reporter": {"name": "<jira-user>"},
         "labels": labels, "priority": {"name": "High" if blocker else "Medium"}, "description": desc,
         "issuelinks": [] if existing else [{"outwardIssue": {"key": "PROJ-997"}}, {"inwardIssue": {"key": "PROJ-598"}}],
         "attachment": [] if existing else [{"filename": "x"}] * (1 if task else 2), "created": "2026-10-15T20:00:00.000+0300"}
    return f

def mock_get(path):
    if "/issue/" in path:
        key = path.split("/issue/")[1].split("?")[0]
        n = int(key.split("-")[1])
        if n > 6900: return 404, None
        return 200, {"key": key, "fields": issue(key)}
    if "/search" in path:
        keys = ["PROJ-%d" % (n - 3000) for n in range(5087, 5103)]
        return 200, {"issues": [{"key": k, "fields": issue(k)} for k in keys]}
    return 404, None
mock_get.user = "<jira-user>"

def write(tmp):
    """Write fixtures under tmp; return dict of paths."""
    os.makedirs(os.path.join(tmp, "jira"), exist_ok=True)
    def w(rel, obj):
        p = os.path.join(tmp, rel)
        json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        return p
    return {"results": w("tracker.json", results()),
            "filed": os.path.join(tmp, "jira", "filed-L*.json"),
            "files": [w("jira/filed-L1.json", L1), w("jira/filed-L2.json", L2), w("jira/filed-L3.json", L3), w("jira/filed-L4.json", L4)]}
