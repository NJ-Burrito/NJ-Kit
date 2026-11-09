"""File the Bugs of one UAT service from bugs-<svc>.json (written by uat_preview.py). Standard 2026-10-22.

usage: PYTHONUTF8=1 python file_bugs.py bugs-S3.json --task PROJ-5182 --assignee <jira user> [--dup-term TEXT] [--dry-run] [--no-ref]
(refuses a Bug without the «📄 المرجع» block, the owner 2026-10-25)

Per Bug: duplicate JQL check (exact summary) -> create (label phase2-uat, assignee, priority, estimate 2h/2h)
-> attachments (allowlist) -> Relates to --task -> GET-verify. Writes filed-bugs-<svc>.json + filing-log-<svc>.md beside
the input. Severity has no Jira field here -> it goes to the log, never the description. --dry-run prints payloads, no Jira call.
Re-title each Bug from the result BEFORE running (summary in the json = what failed, not the draft guess).
"""
import argparse, json, os, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import _jira as J


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bugs"); ap.add_argument("--task", required=True); ap.add_argument("--assignee", required=True)
    ap.add_argument("--dup-term"); ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--no-ref", action="store_true", help="Bug not from a notes document")
    a = ap.parse_args()
    src = pathlib.Path(a.bugs)
    bugs = json.loads(src.read_text(encoding="utf-8"))
    svc = re.sub(r"^bugs-|\.json$", "", src.name)
    root = src.parent
    for b in bugs:  # gates that need no Jira
        miss = [e for e in b["evidence"] if not (root / e).is_file()]
        bad = [e for e in b["evidence"] if not J.attachable(e)]
        if miss or bad:
            sys.exit(f"{b['id']}: evidence missing {miss} / not allowed {bad} (allowed {J.ALLOWED})")
        if re.search(r"\*(Verdict|Source):\*|Priority:|Severity:", b["description"]):
            sys.exit(f"{b['id']}: description carries a metadata/Verdict/Source line")
        if not a.no_ref and "h3. 📄 المرجع" not in b["description"]:
            sys.exit(f"{b['id']}: no «📄 المرجع» block (add `refs` to the data file and re-run uat_preview.py; --no-ref only for non-notes Bugs)")

    def fields(b, pri):
        return {"project": {"key": "PROJ"}, "issuetype": {"name": "Bug"}, "summary": b["summary"], "description": b["description"],
                "labels": [J.STAGE_LABEL], "assignee": {"name": a.assignee}, "priority": {"name": pri}, "timetracking": J.EST}

    if a.dry_run:
        for b in bugs:
            print(json.dumps({"id": b["id"], "severity(log only)": b["severity"], "fields": fields(b, J.priority_for(b["severity"], b["priority"])),
                              "attach": b["evidence"], "link": f"Relates -> {a.task}"}, ensure_ascii=False, indent=1))
        print(f"DRY-RUN ok: {len(bugs)} Bug payloads, no Jira call")
        return

    j = J.Jira()
    pri = {p["name"].lower(): p["name"] for p in j.call("GET", "/rest/api/2/priority")}
    term = a.dup_term or J.jql_phrase(re.match(r"«([^»]*)»", bugs[0]["summary"]).group(1))[:40]
    out = []
    for b in bugs:
        s = j.call("POST", "/rest/api/2/search", {"jql": f'project={j.project} AND type = Bug AND summary ~ "{term}"', "fields": ["summary"]})
        ex = [i["key"] for i in s["issues"] if i["fields"]["summary"] == b["summary"]]
        if ex:
            key, new = ex[0], False
        else:
            key, new = j.call("POST", "/rest/api/2/issue", {"fields": fields(b, pri[J.priority_for(b["severity"], b["priority"]).lower()])})["key"], True
            for e in b["evidence"]:
                j.attach(key, str(root / e))
            j.call("POST", "/rest/api/2/issueLink", {"type": {"name": "Relates"}, "inwardIssue": {"key": key}, "outwardIssue": {"key": a.task}})
        g = j.call("GET", f"/rest/api/2/issue/{key}")["fields"]
        links = [(l.get("outwardIssue") or l.get("inwardIssue"))["key"] for l in g["issuelinks"]]
        ok = (g["summary"] == b["summary"] and g["labels"] == [J.STAGE_LABEL] and (g["assignee"] or {}).get("name") == a.assignee
              and len(g["attachment"]) == len(b["evidence"]) and a.task in links)
        out.append({"id": b["id"], "key": key, "new": new, "priority": b["priority"], "severity": b["severity"], "summary": b["summary"],
                    "n_ev": len(b["evidence"]), "verified": ok})
        print(b["id"], key, "new" if new else "exists", "verified" if ok else "VERIFY-FAILED")
    (root / f"filed-bugs-{svc}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    log = ["| note | key | priority | severity | story (Relates) | assignee | attachments | verified |", "|---|---|---|---|---|---|---|---|"]
    log += [f"| {o['id']} | {o['key']} | {o['priority']} | {o['severity']} | {a.task} | {a.assignee} | {o['n_ev']} | {o['verified']} |" for o in out]
    (root / f"filing-log-{svc}.md").write_text("\n".join(log) + "\n", encoding="utf-8")
    sys.exit(0 if all(o["verified"] for o in out) else 1)


if __name__ == "__main__":
    try:
        main()
    except J.JiraError as e:
        sys.exit(f"JIRA ERROR (required fields appear in the 400 body): {e}")
