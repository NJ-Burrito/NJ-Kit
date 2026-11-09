"""UAT Task lifecycle (standard 2026-10-22). Uses the same data file as uat_preview.py.

  task.py create DATA --assignee USER [--service S3] [--dry-run]
      one Task per service BEFORE testing: label phase2-uat, estimate 2h/2h, In Progress -> filed-tasks.json beside DATA
  task.py close DATA --service S3 --task PROJ-N --filed filed-bugs-S3.json [--dry-run]
      counts line «N بنداً: ❌ x (y ملاحظات + z جديدة) · ✅ w», البلاغات = one `* KEY — defect` line per Bug, then Done
--dry-run prints the payloads and calls nothing.
"""
import argparse, json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import _jira as J
import uat_preview as U


def counts_line(s, d):
    total, fails, new, passes, _todo = U.counts(s, d)
    return f"{total} بنداً: ❌ {len(fails)} ({len(fails) - len(new)} ملاحظات + {len(new)} جديدة) · ✅ {len(passes)}"


def closed_body(base, counts, filed, notes=()):
    """base = current Task description: keep its 🧪 header, then counts + one entry per note (page/item/verbatim quote/Bug key), then البلاغات."""
    head = base.split("h3. 🐞 البلاغات")[0].strip("\n").split("\n")[0]
    lines = [f"* {o['key']} — {o['summary'].split('»:', 1)[-1].strip()}" for o in filed]
    return "\n".join([head, f"* {counts}", "", *notes, "", "h3. 🐞 البلاغات", *lines])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["create", "close"]); ap.add_argument("data")
    ap.add_argument("--assignee"); ap.add_argument("--service"); ap.add_argument("--task"); ap.add_argument("--filed"); ap.add_argument("--counts")
    ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--no-transition", action="store_true")
    a = ap.parse_args()
    d = U.load(a.data)
    svcs = [s for s in d["services"] if not a.service or s["key"] == a.service]
    root = pathlib.Path(a.data).resolve().parent
    if a.cmd == "create":
        if not a.assignee:
            sys.exit("--assignee required")
        out = []
        for s in svcs:
            f = {"project": {"key": "PROJ"}, "issuetype": {"name": "Task"}, "summary": U.task_summary(s, d), "description": U.task_wiki(s, d),
                 "labels": [J.STAGE_LABEL], "assignee": {"name": a.assignee}, "timetracking": J.EST}
            if a.dry_run:
                print(json.dumps({"service": s["key"], "fields": f, "then": "transition In Progress"}, ensure_ascii=False, indent=1))
                continue
            j = J.Jira()
            term = J.jql_phrase(U.task_summary(s, d))
            hit = [i["key"] for i in j.call("POST", "/rest/api/2/search", {"jql": f'project={j.project} AND type = Task AND summary ~ "{term}"', "fields": ["summary"]})["issues"]
                   if i["fields"]["summary"] == f["summary"]]
            if hit:
                print(s["key"], hit[0], "exists"); out.append({"service": s["key"], "key": hit[0], "new": False}); continue
            k = j.call("POST", "/rest/api/2/issue", {"fields": f})["key"]
            j.transition(k, "In Progress")
            g = j.call("GET", f"/rest/api/2/issue/{k}")["fields"]
            out.append({"service": s["key"], "key": k, "new": True, "status": g["status"]["name"], "label": g["labels"], "assignee": g["assignee"]["name"]})
            print(out[-1])
        if not a.dry_run:
            (root / "filed-tasks.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        else:
            print(f"DRY-RUN ok: {len(svcs)} Task payloads, no Jira call")
        return
    if not (a.service and a.task and a.filed):
        sys.exit("close needs --service --task --filed")
    s = svcs[0]
    filed = json.loads(pathlib.Path(a.filed).read_text(encoding="utf-8"))
    if a.dry_run:
        print(closed_body(U.task_wiki(s, d), a.counts or counts_line(s, d), filed, U.task_notes_lines(s, d, filed))); print(f"-> PUT {a.task} description, transition Done\nDRY-RUN ok, no Jira call"); return
    j = J.Jira()
    body = closed_body(j.call("GET", f"/rest/api/2/issue/{a.task}")["fields"]["description"], a.counts or counts_line(s, d), filed, U.task_notes_lines(s, d, filed))
    j.call("PUT", f"/rest/api/2/issue/{a.task}", {"fields": {"description": body}})
    if not a.no_transition:
        j.transition(a.task, "Done")
    g = j.call("GET", f"/rest/api/2/issue/{a.task}")["fields"]
    print(g["status"]["name"], "bugs listed:", sum(o["key"] in g["description"] for o in filed), "/", len(filed))


if __name__ == "__main__":
    try:
        main()
    except J.JiraError as e:
        sys.exit(f"JIRA ERROR: {e}")
