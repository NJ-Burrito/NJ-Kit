"""Tiny Jira REST v2 client for file_bugs.py / task.py. Credentials: ~/.claude/secrets/jira.json (block `jira`), never printed."""
import base64, json, os, sys, urllib.error, urllib.request, uuid

STAGE_LABEL = "phase2-uat"  # same value as nj-rank/scripts/nj_rank.py STAGE_LABEL; change both only when the owner names a new stage
ALLOWED = (".png", ".jpg", ".jpeg", ".mp4", ".webm", ".gif", ".md", ".pdf")
BLOCKER_PRIORITY = "Critical"  # the owner 2026-10-22: Blocker severity => Jira priority Critical (name confirmed via GET /priority)


def priority_for(severity, priority):
    return BLOCKER_PRIORITY if severity == "Blocker" else priority


EST = {"originalEstimate": "2h", "remainingEstimate": "2h"}


class JiraError(Exception):
    pass


class Jira:
    def __init__(self):
        c = json.load(open(os.path.expanduser("~/.claude/secrets/jira.json"), encoding="utf-8"))["jira"]
        self.base, self.project, self.user, self._pw = c["baseUrl"].rstrip("/"), c["projectKey"], c["user"], c["password"]
        self._auth = "Basic " + base64.b64encode(f"{self.user}:{self._pw}".encode()).decode()

    def call(self, method, path, data=None):
        h = {"Authorization": self._auth, "Accept": "application/json", "Content-Type": "application/json", "X-Atlassian-Token": "no-check"}
        r = urllib.request.Request(self.base + path, method=method, headers=h, data=json.dumps(data).encode() if data is not None else None)
        try:
            x = urllib.request.urlopen(r).read()
            return json.loads(x) if x else {}
        except urllib.error.HTTPError as e:  # 400 carries the required/invalid fields (create-meta is 404 on this server)
            raise JiraError(f"{e.code} {path}: {e.read().decode()[:600].replace(self._pw, '***')}") from None

    def attach(self, key, path):
        bd, fn = uuid.uuid4().hex, os.path.basename(path)
        body = (f'--{bd}\r\nContent-Disposition: form-data; name="file"; filename="{fn}"\r\nContent-Type: application/octet-stream\r\n\r\n').encode() \
            + open(path, "rb").read() + f"\r\n--{bd}--\r\n".encode()
        h = {"Authorization": self._auth, "X-Atlassian-Token": "no-check", "Content-Type": "multipart/form-data; boundary=" + bd}
        urllib.request.urlopen(urllib.request.Request(f"{self.base}/rest/api/2/issue/{key}/attachments", data=body, headers=h, method="POST")).read()

    def transition(self, key, name):
        t = self.call("GET", f"/rest/api/2/issue/{key}/transitions")["transitions"]
        ids = [x["id"] for x in t if x["name"].lower() == name.lower()]
        if not ids:
            raise JiraError(f"{key}: no transition '{name}' (have {[x['name'] for x in t]})")
        self.call("POST", f"/rest/api/2/issue/{key}/transitions", {"transition": {"id": ids[0]}})


def jql_phrase(text):
    """Lucene operators break `~`: strip them, then match the summary exactly in code (rest-recipes Pitfalls)."""
    return "".join(" " if c in '[](){}:·"\\+-!^~*?|&/' else c for c in text).strip()


def attachable(path):
    return os.path.splitext(path)[1].lower() in ALLOWED
