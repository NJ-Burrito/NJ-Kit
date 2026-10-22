#!/usr/bin/env python3
"""nj-wrapup step 0: list what ALREADY exists for this session so nothing is filed or registered twice.
Read-only. Writes discover.json; prints one line per source. Exit 0 (it informs, it does not gate).

  PYTHONUTF8=1 python discover.py --project PROJ --date 2026-10-15 --out DIR
        [--work-dir DIR]        folder holding jira/filed-*.json of this session
        [--tracker FILE]        project ticket tracker (json: list or {tickets:[..]}) -> count + keys
        [--outputs-dir DIR]     stored outputs: files modified on --date are listed
        [--handoff FILE ...]    handoff file(s): exists + mtime
        [--session TAG]         nj-rank session tag: only this session's items are listed, other sessions are counted as peers
        [--since ISO]           only items finished at/after this ISO time (a window when no tag exists)
        [--rank-root DIR]       nj-rank root (default env NJ_RANK_ROOT, else ~/Desktop/NJ-Rank)
        [--creds FILE] [--offline] | --selftest
Credentials: env JIRA_BASE_URL/JIRA_USER/JIRA_PASS or --creds FILE. Never printed.
"""
from __future__ import annotations
import argparse, datetime as dt, glob, json, os, re, sys, tempfile, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import utf8, load_creds, jira_get, load_filed, rows_of

KEY = re.compile(r"[A-Z][A-Z0-9]+-\d+")


def day(ts):
    return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def discover(a, get=None):
    out = {"project": a.project, "date": a.date}
    if get:
        jql = f'project = {a.project} AND reporter = currentUser() AND created >= "{a.date}" ORDER BY key'
        st, d = get("/rest/api/2/search?maxResults=200&fields=summary,issuetype,status,labels&jql=" + urllib.parse.quote(jql))
        out["jira_filed_today"] = ([{"key": i["key"], "type": i["fields"]["issuetype"]["name"], "status": i["fields"]["status"]["name"],
                                     "labels": i["fields"].get("labels", []), "summary": i["fields"]["summary"]} for i in d["issues"]]
                                   if st == 200 and d else {"error": f"search returned {st}"})
    else:
        out["jira_filed_today"] = "skipped (offline)"
    if a.work_dir:
        rows = load_filed(os.path.join(a.work_dir, "jira", "filed-*.json"))
        out["filed_json"] = {"files": sorted({r["_src"] for r in rows}), "keys": sorted({r["key"] for r in rows if r.get("key")})}
    if a.tracker and os.path.exists(a.tracker):
        t = json.load(open(a.tracker, encoding="utf-8"))
        t = rows_of(t)  # list | {rows} | {tickets} | {notes} | {ID:{..}}
        keys = sorted({k for x in t for k in KEY.findall(json.dumps(x, ensure_ascii=False))[:1]})
        out["tracker"] = {"path": a.tracker, "tickets": len(t), "keys": keys}
    root = a.rank_root or os.environ.get("NJ_RANK_ROOT") or os.path.expanduser("~/Desktop/NJ-Rank")
    reg = os.path.join(root, "registry.jsonl")
    items, peers = [], 0
    if os.path.exists(reg):
        for line in open(reg, encoding="utf-8"):
            try:
                x = json.loads(line)
            except ValueError:
                continue
            if x.get("project") == a.project and str(x.get("finished", "")).startswith(a.date):
                if (a.session and x.get("session") != a.session) or (a.since and str(x.get("finished", "")) < a.since):
                    peers += 1  # another session's work: counted, never listed, never touched
                    continue
                items.append({k: x.get(k) for k in ("n", "status", "work_type", "title", "jira_key", "session", "finished")})
    out["rank_items_today"] = items
    out["rank_items_other_sessions"] = peers
    if a.outputs_dir and os.path.isdir(a.outputs_dir):
        out["outputs_today"] = sorted(os.path.relpath(p, a.outputs_dir) for p in glob.glob(os.path.join(a.outputs_dir, "**", "*"), recursive=True)
                                      if os.path.isfile(p) and day(os.path.getmtime(p)) == a.date)
    out["handoff"] = [{"path": h, "exists": os.path.exists(h), "mtime": dt.datetime.fromtimestamp(os.path.getmtime(h)).isoformat(timespec="minutes") if os.path.exists(h) else None}
                      for h in a.handoff or []]
    return out


def show(o):
    j = o["jira_filed_today"]
    print(f"discover {o['project']} {o['date']}: jira filed today = {len(j) if isinstance(j, list) else j}")
    if "filed_json" in o: print(f"  filed-*.json: {len(o['filed_json']['files'])} files, {len(o['filed_json']['keys'])} keys")
    if "tracker" in o: print(f"  tracker: {o['tracker']['tickets']} tickets")
    print(f"  nj-rank items today: {len(o['rank_items_today'])} (+{o['rank_items_other_sessions']} from other sessions, not listed)")
    if "outputs_today" in o: print(f"  stored outputs today: {len(o['outputs_today'])}")
    for h in o["handoff"]: print(f"  handoff {'found' if h['exists'] else 'missing'}: {h['path']}")


def selftest():
    import _fixture as fx
    with tempfile.TemporaryDirectory() as tmp:
        fx.write(tmp)
        os.makedirs(os.path.join(tmp, "out", "d"))
        open(os.path.join(tmp, "out", "d", "a.pdf"), "w").write("x")
        open(os.path.join(tmp, "handoff.md"), "w").write("x")
        today = day(os.path.getmtime(os.path.join(tmp, "handoff.md")))
        with open(os.path.join(tmp, "registry.jsonl"), "w", encoding="utf-8") as f:
            for n, (fin, st) in enumerate([(today + "T10:00:00+03:00", "filed"), ("2000-01-01T10:00:00+03:00", "filed")], 1):
                f.write(json.dumps({"n": n, "status": st, "project": "PROJ", "finished": fin, "title": "t%d" % n, "work_type": "segment", "jira_key": "PROJ-1001"}) + "\n")
        a = argparse.Namespace(project="PROJ", date=today, work_dir=tmp, tracker=None, outputs_dir=os.path.join(tmp, "out"),
                               handoff=[os.path.join(tmp, "handoff.md"), os.path.join(tmp, "nope.md")], rank_root=tmp, session=None, since=None)
        o = discover(a, fx.mock_get)
        assert len(o["jira_filed_today"]) == 16, o["jira_filed_today"]
        assert o["filed_json"]["keys"].__len__() == 19 and len(o["filed_json"]["files"]) == 4, o["filed_json"]
        assert len(o["rank_items_today"]) == 1 and o["outputs_today"] == [os.path.join("d", "a.pdf")]
        assert [h["exists"] for h in o["handoff"]] == [True, False]
        assert discover(a, None)["jira_filed_today"].startswith("skipped")
        # session scope: 14 rank items of peers on the same day must not appear (verify-v2 T3)
        with open(os.path.join(tmp, "registry.jsonl"), "a", encoding="utf-8") as f:
            for n in range(3, 8):
                f.write(json.dumps({"n": n, "project": "PROJ", "session": "peer-x", "finished": today + "T11:00:00+03:00", "title": "peer"}) + chr(10))
            f.write(json.dumps({"n": 8, "project": "PROJ", "session": "mine", "finished": today + "T12:00:00+03:00", "title": "mine"}) + chr(10))
        a.session = "mine"; o2 = discover(a, None)
        assert [i["title"] for i in o2["rank_items_today"]] == ["mine"] and o2["rank_items_other_sessions"] == 6, o2
        a.session = None; a.since = today + "T11:30:00"; assert len(discover(a, None)["rank_items_today"]) == 1
        # tracker in every shape gives the same keys
        for shape in ([{"k": "PROJ-1001"}, {"k": "PROJ-1002"}], {"rows": [{"k": "PROJ-1001"}, {"k": "PROJ-1002"}]}, {"tickets": {"a": {"k": "PROJ-1001"}, "b": {"k": "PROJ-1002"}}}):
            tp = os.path.join(tmp, "tr.json"); json.dump(shape, open(tp, "w")); a.tracker = tp; a.since = None
            assert discover(a, None)["tracker"]["keys"] == ["PROJ-1001", "PROJ-1002"], shape
    print("discover selftest: PASS (16 Jira keys filed today, 19 keys in 4 filed-*.json, rank items filtered by date and session, peers counted not listed, 3 tracker shapes, outputs + handoff listed)")


def main():
    utf8()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project"); ap.add_argument("--date"); ap.add_argument("--out"); ap.add_argument("--work-dir")
    ap.add_argument("--tracker"); ap.add_argument("--outputs-dir"); ap.add_argument("--handoff", action="append")
    ap.add_argument("--rank-root"); ap.add_argument("--session"); ap.add_argument("--since"); ap.add_argument("--creds"); ap.add_argument("--offline", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.project and a.date and a.out):
        ap.error("--project, --date and --out are required")
    o = discover(a, None if a.offline else jira_get(load_creds(a.creds)))
    os.makedirs(a.out, exist_ok=True)
    json.dump(o, open(os.path.join(a.out, "discover.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    show(o)


if __name__ == "__main__":
    main()
