"""Harvest Jira tickets with their sub-tasks and report what changed since the last harvest.

usage: python -X utf8 jira_refresh.py KEY [KEY ...] --out RUN_DIR [--prev DIR_WITH_raw] [--creds credentials.json]
Writes RUN_DIR/<ROOT KEY>/raw/<KEY>.json, attachments/<KEY>/NN-name (files over 25 MB are listed, not fetched)
and RUN_DIR/<ROOT KEY>/changes.md. Read-only on Jira. Credentials are never printed.
Credentials: env JIRA_BASE_URL/JIRA_USER/JIRA_PASS, else block "jira" of --creds or JIRA_CREDENTIALS_FILE.
"""
import argparse, base64, json, os, pathlib, re, time, urllib.error, urllib.request

MAX_ATT = 25 * 1024 * 1024


def client(creds_path):
    base, user, pw = os.environ.get("JIRA_BASE_URL"), os.environ.get("JIRA_USER"), os.environ.get("JIRA_PASS")
    if not (base and user and pw):
        path = creds_path or os.environ.get("JIRA_CREDENTIALS_FILE")
        if not path:
            raise SystemExit("no Jira credentials: set JIRA_* or pass --creds")
        c = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))["jira"]
        base, user, pw = c["baseUrl"], c["user"], c["password"]
    head = {"Authorization": "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode(), "Accept": "application/json"}
    base = base.rstrip("/")

    def get(url, raw=False):
        url = base + url if url.startswith("/") else url
        for n in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=head), timeout=120) as r:
                    b = r.read()
                    return b if raw else json.loads(b)
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and n < 3:
                    time.sleep(1.5 * (n + 1))
                    continue
                raise SystemExit(f"Jira {e.code} on {url.split('?')[0]}")
    return get


def snapshot(issue):
    f = issue["fields"]
    return {
        "summary": f["summary"], "status": f["status"]["name"], "updated": f["updated"][:16],
        "assignee": (f.get("assignee") or {}).get("displayName", "—"),
        "description": f.get("description") or "",
        "comments": {c["id"]: c["created"][:16] for c in (f.get("comment") or {}).get("comments") or []},
        "attachments": sorted(a["filename"] for a in f.get("attachment") or []),
    }


def diff(old, new):
    """old/new: {key: snapshot}. -> list of change lines; empty = nothing changed."""
    out = []
    for k in sorted(set(new) - set(old)):
        out.append(f"🆕 {k} new: [{new[k]['status']}] {new[k]['summary']}")
    for k in sorted(set(old) - set(new)):
        out.append(f"➖ {k} no longer under this ticket: {old[k]['summary']}")
    for k in sorted(set(old) & set(new)):
        o, n = old[k], new[k]
        if o["status"] != n["status"]:
            out.append(f"🔁 {k} status: {o['status']} -> {n['status']}")
        if o["assignee"] != n["assignee"]:
            out.append(f"👤 {k} assignee: {o['assignee']} -> {n['assignee']}")
        if o["summary"] != n["summary"]:
            out.append(f"✏️ {k} summary: {o['summary']} -> {n['summary']}")
        if o["description"] != n["description"]:
            out.append(f"✏️ {k} description changed")
        added = sorted(set(n["comments"]) - set(o["comments"]))
        if added:
            out.append(f"💬 {k} new comments: {', '.join(added)}")
        files = sorted(set(n["attachments"]) - set(o["attachments"]))
        if files:
            out.append(f"📎 {k} new attachments: {', '.join(files)}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keys", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--prev")
    ap.add_argument("--creds")
    a = ap.parse_args()
    get = client(a.creds)
    for root in a.keys:
        seen, q = {}, [root]
        while q:
            k = q.pop(0)
            if k in seen:
                continue
            seen[k] = get(f"/rest/api/2/issue/{k}?expand=renderedFields,changelog")
            q += [s["key"] for s in seen[k]["fields"].get("subtasks") or []]
        d = pathlib.Path(a.out) / root
        (d / "raw").mkdir(parents=True, exist_ok=True)
        for k, i in seen.items():
            (d / "raw" / f"{k}.json").write_text(json.dumps(i, ensure_ascii=False, indent=1), encoding="utf-8")
            for n, att in enumerate(i["fields"].get("attachment") or [], 1):
                if att["size"] > MAX_ATT:
                    print(f"  {k}: not fetched, over 25 MB: {att['filename']}")
                    continue
                t = d / "attachments" / k
                t.mkdir(parents=True, exist_ok=True)
                name = re.sub(r'[<>:"/\\|?*]', "_", att["filename"])
                (t / f"{n:02d}-{name}").write_bytes(get(att["content"], raw=True))
        lines = []
        prev = pathlib.Path(a.prev) / root / "raw" if a.prev else None
        if prev and prev.exists():
            old = {p.stem: snapshot(json.loads(p.read_text(encoding="utf-8"))) for p in prev.glob("*.json")}
            lines = diff(old, {k: snapshot(i) for k, i in seen.items()})
        (d / "changes.md").write_text("\n".join(lines) or "no changes", encoding="utf-8")
        print(f"{root}: {len(seen)} tickets, {len(lines)} changes")
        for ln in lines:
            print("  " + ln)


if __name__ == "__main__":
    main()
