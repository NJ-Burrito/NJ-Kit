#!/usr/bin/env python3
"""nj-rank: register finished work, keep evidence paths, file it to Jira as Done Tasks.

stdlib only. Jira REST v2 over urllib with an injectable opener (tests mock it).
Subcommands: register | log | import | preview | file | close-mine | link | whoami.
Credential order: env JIRA_BASE_URL/JIRA_USER/JIRA_PASS > env NJ_RANK_SECRETS file >
~/.claude/secrets/jira.json. The password is never printed, stored or put in a file.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from collections import Counter
from pathlib import Path

DEFAULT_ROOT = os.path.join(os.path.expanduser("~"), "Desktop", "NJ-Rank")
DESKTOP_COPY = os.path.join(os.path.expanduser("~"), "Desktop", "NJ-Rank preview.html")
DEFAULT_SECRETS = Path.home() / ".claude" / "secrets" / "jira.json"
SEVEN_ZIP = r"C:\Program Files\7-Zip\7z.exe"
WORK_TYPES = {"srs", "user-manual", "user-manual-remake", "staff-manual",
              "automation-tests", "jira-filing", "segment"}
TIME_SOURCES = {"mtime", "stage-time", "log", "transcript"}
REQUIRED = ("project", "session", "title", "description", "work_type", "finished")
ALLOWED_EXT = (".png", ".jpg", ".jpeg", ".mp4", ".webm", ".gif", ".md", ".pdf")  # .pdf added same day for the official output letters  # the owner, 2026-10-19: nothing else is uploaded


LOCAL_EXT = (".html", ".htm")  # registered + archived in evidence.7z, never uploaded (e.g. the UAT preview.html)


def check_attachable(path):
    if Path(path).suffix.lower() not in ALLOWED_EXT:
        raise NjRankError(f"refused to attach {Path(path).name}: allowed evidence types are {', '.join(ALLOWED_EXT)} "
                          "(put text in a .md, or keep the file local)")


UPLOAD_DEFAULT =10 * 1024 * 1024  # used only if attachment/meta is unreadable
UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


# Current SDLC stage label, same on every Bug/Task (the owner 2026-10-19). Change only when the owner names a new stage.
STAGE_LABEL = "phase2-uat"

BANNED_TICKET_LINE = re.compile(r"\*(Verdict|Source):\*", re.I)


def refuse_verdict_source(body):
    """the owner 2026-10-20: no ticket body carries a *Verdict:* or *Source:* line."""
    if BANNED_TICKET_LINE.search(body or ""):
        raise NjRankError("ticket body contains a *Verdict:* or *Source:* line (refused, the owner 2026-10-20)")


class NjRankError(Exception):
    pass


class JiraError(NjRankError):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


# ---------- long paths and file helpers ----------

def longpath(path):
    """Absolute Windows path with the extended-length prefix, so paths over 260 chars work.

    Every filesystem call on evidence or root paths goes through this; stored paths stay plain.
    """
    p = os.path.abspath(str(path))
    if sys.platform != "win32" or p.startswith("\\\\?\\"):
        return p
    if p.startswith("\\\\"):
        return "\\\\?\\UNC\\" + p[2:]
    return "\\\\?\\" + p


def read_text(path):
    with open(longpath(path), encoding="utf-8") as fh:
        return fh.read()


def write_text(path, text):
    os.makedirs(longpath(Path(path).parent), exist_ok=True)
    with open(longpath(path), "w", encoding="utf-8") as fh:
        fh.write(text)


def read_json(path):
    return json.loads(read_text(path))


def write_json(path, obj):
    write_text(path, json.dumps(obj, ensure_ascii=False, indent=2))


# ---------- config ----------

def load_config(env=None, secrets_path=None):
    env = os.environ if env is None else env
    if env.get("JIRA_BASE_URL") and env.get("JIRA_USER") and env.get("JIRA_PASS"):
        return {"baseUrl": env["JIRA_BASE_URL"].rstrip("/"), "user": env["JIRA_USER"],
                "password": env["JIRA_PASS"], "projectKey": env.get("JIRA_PROJECT_KEY", "PROJ")}
    path = Path(env["NJ_RANK_SECRETS"]) if env.get("NJ_RANK_SECRETS") else Path(secrets_path or DEFAULT_SECRETS)
    if not path.exists():
        raise NjRankError("no Jira credentials: set JIRA_BASE_URL/JIRA_USER/JIRA_PASS or create the secrets file")
    data = json.loads(path.read_text(encoding="utf-8"))
    j = data.get("jira", data)
    missing = [k for k in ("baseUrl", "user", "password") if not j.get(k)]
    if missing:
        raise NjRankError("secrets file lacks: " + ", ".join(missing))  # field names only
    return {"baseUrl": j["baseUrl"].rstrip("/"), "user": j["user"], "password": j["password"],
            "projectKey": j.get("projectKey", "PROJ")}


# ---------- not-a-bug rule (the owner 2026-10-22; mirrored in the tracker's core.ts) ----------

NOT_A_BUG_RE = re.compile(r"not[ -](?:a[ -])?bug|won'?t fix|rejected|invalid|works as designed|by design|ليس خطأ|ليست مشكلة|مرفوض", re.I)


def is_not_bug(status, resolution=""):
    return bool(NOT_A_BUG_RE.search(status or "") or NOT_A_BUG_RE.search(resolution or ""))


def not_bug_of(issue):
    """Who set the not-a-bug status/resolution (changelog), when, and their latest comment (else the first comment at/after the change)."""
    f = issue.get("fields") or {}
    if not is_not_bug((f.get("status") or {}).get("name"), (f.get("resolution") or {}).get("name")):
        return None
    hs = [h for h in (issue.get("changelog") or {}).get("histories", [])
          if any(i.get("field") in ("status", "resolution") and NOT_A_BUG_RE.search(f"{i.get('toString') or ''} {i.get('to') or ''}")
                 for i in h.get("items", []))]
    hs.sort(key=lambda h: h.get("created", ""))
    h = hs[-1] if hs else {}
    by, at = (h.get("author") or {}).get("displayName", "-"), h.get("created", "")
    cs = (f.get("comment") or {}).get("comments", [])
    mine = [c for c in cs if (c.get("author") or {}).get("displayName") == by]
    c, src = (mine[-1], "author") if mine else (next((x for x in cs if x.get("created", "") >= at), None), "after-change")
    return {"by": by, "at": at, "comment": (c or {}).get("body", ""), "commentAt": (c or {}).get("created", ""),
            "src": src if c else "none"}


NB_CHIP = "<span class='nbchip'>🚫 ليس Bug</span>"


def nb_block(nb):
    e = html.escape
    note = {"after-change": " <small>(latest comment after the change, not by the decision maker)</small>",
            "none": " <small>(the decision maker left no comment)</small>"}.get(nb["src"], "")
    body = f"«{e(nb['comment'])}»" if nb["comment"] else "<i>(no comment)</i>"
    return f"<div class='nbq' dir='auto'>💬 <b>{e(nb['by'])}</b> — {e(nb['at'][:16].replace('T', ' '))}: {body}{note}</div>"


# ---------- Jira client ----------

class Jira:
    def __init__(self, cfg, opener=None, sleep=time.sleep):
        self.cfg = cfg
        self.opener = opener or urllib.request.build_opener()
        self.sleep = sleep
        raw = f'{cfg["user"]}:{cfg["password"]}'.encode("utf-8")
        self._token = base64.b64encode(raw).decode("ascii")

    def mask(self, text):
        out = str(text)
        for secret in (self._token, self.cfg["password"]):
            if secret:
                out = out.replace(secret, "***")
        return out

    def _req(self, method, path, body=None, raw=None, ctype=None):
        headers = {"Authorization": "Basic " + self._token, "Accept": "application/json",
                   "X-Atlassian-Token": "no-check"}
        data = raw
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif raw is not None:
            headers["Content-Type"] = ctype
        url = self.cfg["baseUrl"] + path
        err = None
        for attempt in range(4):
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with self.opener.open(req, timeout=60) as resp:
                    txt = resp.read().decode("utf-8", "replace")
                return json.loads(txt) if txt.strip() else None
            except urllib.error.HTTPError as e:
                snippet = e.read().decode("utf-8", "replace")[:300]
                err = JiraError(e.code, self.mask(f"{method} {path} -> HTTP {e.code}: {snippet}"))
                if e.code == 429 or e.code >= 500:
                    self.sleep(1.5 * (attempt + 1))
                    continue
                raise err
            except urllib.error.URLError as e:
                err = JiraError(0, self.mask(f"{method} {path} -> {e.reason}"))
                self.sleep(1.5 * (attempt + 1))
        raise err

    def myself(self):
        return self._req("GET", "/rest/api/2/myself")["name"]

    def search(self, jql, fields):
        issues, start = [], 0
        while True:
            data = self._req("POST", "/rest/api/2/search",
                             {"jql": jql, "fields": fields, "startAt": start, "maxResults": 100})
            page = data.get("issues", [])
            issues += page
            start += len(page)
            if not page or start >= data.get("total", 0):
                return issues

    def upload_limit(self):
        try:
            return int(self._req("GET", "/rest/api/2/attachment/meta").get("uploadLimit") or UPLOAD_DEFAULT)
        except JiraError:
            return UPLOAD_DEFAULT

    def create_task(self, project, summary, description, assignee, label=None):
        refuse_verdict_source(description)
        fields = {"project": {"key": project}, "issuetype": {"name": "Task"}, "summary": summary,
                  "description": description, "assignee": {"name": assignee}}
        if label:
            fields["labels"] = [label]  # stage label, see STAGE_LABEL
        try:
            data = self._req("POST", "/rest/api/2/issue", {"fields": fields})
        except JiraError as e:
            if e.status != 400:
                raise
            fields["timetracking"] = {"originalEstimate": "1h"}  # the one retry the brief allows
            data = self._req("POST", "/rest/api/2/issue", {"fields": fields})
        return data["key"]

    def attach(self, key, path):
        check_attachable(path)  # the one gate every upload passes (owner, 2026-10-19)
        boundary = uuid.uuid4().hex
        name = Path(path).name.replace('"', "")
        head = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
                f"Content-Type: application/octet-stream\r\n\r\n").encode("utf-8")
        with open(longpath(path), "rb") as fh:
            body = head + fh.read() + f"\r\n--{boundary}--\r\n".encode("ascii")
        return self._req("POST", f"/rest/api/2/issue/{key}/attachments", raw=body,
                         ctype=f"multipart/form-data; boundary={boundary}")

    def add_comment(self, key, text):
        return self._req("POST", f"/rest/api/2/issue/{key}/comment", {"body": text})

    def done_transition_id(self, key):
        ts = (self._req("GET", f"/rest/api/2/issue/{key}/transitions") or {}).get("transitions", [])
        for t in ts:
            if ((t.get("to") or {}).get("statusCategory") or {}).get("key") == "done":
                return t["id"]
        for t in ts:
            if (t.get("name") or "").lower() == "done":
                return t["id"]
        raise NjRankError(f"{key}: no transition to a Done status from its current state")

    def transition_done(self, key):
        self._req("POST", f"/rest/api/2/issue/{key}/transitions",
                  {"transition": {"id": self.done_transition_id(key)}})

    def link(self, a, b, kind="Relates"):
        """Link a to b (Relates by default) via REST v2 issueLink; the 201 reply has no body."""
        return self._req("POST", "/rest/api/2/issueLink", {"type": {"name": kind},
                         "inwardIssue": {"key": a}, "outwardIssue": {"key": b}})

    def get_full(self, key):
        """Read-only: status, resolution, assignee, comments and changelog (status sync + not-a-bug block)."""
        return self._req("GET", f"/rest/api/2/issue/{key}?fields=summary,assignee,status,resolution,updated,comment&expand=changelog")

    def get_issue(self, key):
        return self._req("GET", f"/rest/api/2/issue/{key}?fields=summary,assignee,status,attachment,issuetype,reporter")


def esc_jql(text):
    return text.replace("\\", "\\\\").replace('"', '\\"')


def find_exact_tasks(jira, project, title):
    # Jira's text search rejects Lucene operators ([ ] ( ) : ...): search on the plain words, then keep exact matches only
    words = re.sub(r"[+\-&|!(){}\[\]^~*?\\:/\"'·]", " ", title).split()
    jql = f'project = "{project}" AND issuetype = Task AND summary ~ "{esc_jql(" ".join(words))}"'
    return [i["key"] for i in jira.search(jql, ["summary"]) if i["fields"].get("summary") == title]


def verify_filed(issue, me, n_attached):
    f = issue.get("fields", {})
    problems = []
    if (f.get("assignee") or {}).get("name") != me:
        problems.append("assignee is not " + me)
    if ((f.get("status") or {}).get("statusCategory") or {}).get("key") != "done":
        problems.append("status is not Done")
    if len(f.get("attachment") or []) != n_attached:
        problems.append(f"attachments {len(f.get('attachment') or [])} != {n_attached}")
    return problems


# ---------- local store ----------

def safe_title(text):
    t = UNSAFE.sub("", str(text))
    t = re.sub(r"\s+", " ", t).strip().rstrip(". ")
    return t[:80].rstrip(" .") or "untitled"


def now_iso():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def dedupe_key(item):
    head = " ".join((item.get("service_ar") or item["title"]).split())
    return f'{item["project"]}|{head}|{item["work_type"]}'


def load_registry(root):
    p = Path(root) / "registry.jsonl"
    if not os.path.exists(longpath(p)):
        return []
    return [json.loads(line) for line in read_text(p).splitlines() if line.strip()]


def save_registry(root, rows):
    p = Path(root) / "registry.jsonl"
    # HARD RULE (the owner 2026-11-02): rows are his KPI record; clearing touches evidence only, a row is never dropped
    lost = {r["id"] for r in load_registry(root)} - {r["id"] for r in rows}
    if lost:
        raise NjRankError(f"refused: the work log never loses rows ({len(lost)} would be removed)")
    os.makedirs(longpath(p.parent), exist_ok=True)
    tmp = p.with_suffix(".jsonl.tmp")
    write_text(tmp, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    os.replace(longpath(tmp), longpath(p))
    write_preview(root)  # the owner 2026-10-12: the HTML preview is always current, unasked


def read_item(folder):
    return read_json(Path(folder) / "item.json")


def update(root, ident, **changes):
    rows = load_registry(root)
    for r in rows:
        if r["id"] == ident:
            r.update({k: v for k, v in changes.items() if k in r})
            folder = Path(r["folder"])
            doc = read_item(folder)
            doc.update(changes)
            write_json(folder / "item.json", doc)
            break
    else:
        raise NjRankError(f"no registry row {ident}")
    save_registry(root, rows)


def _task_key(v):
    if v and not re.fullmatch(r"[A-Z][A-Z0-9]*-\d+", str(v).strip()):
        raise NjRankError(f"existing_task is not a Jira key: {v!r}")
    return str(v).strip() if v else None


def normalise(raw):
    if not isinstance(raw, dict):
        raise NjRankError("item must be a JSON object")
    missing = [k for k in REQUIRED if not str(raw.get(k) or "").strip()]
    if missing:
        raise NjRankError("missing: " + ", ".join(missing))
    if raw["work_type"] not in WORK_TYPES:
        raise NjRankError(f"work_type {raw['work_type']!r} not one of {sorted(WORK_TYPES)}")
    ts = raw.get("time_source") or None
    if ts is not None and ts not in TIME_SOURCES:
        raise NjRankError(f"time_source {ts!r} not one of {sorted(TIME_SOURCES)}")
    for k in ("finished", "started"):
        if raw.get(k):
            try:
                dt.datetime.fromisoformat(raw[k])
            except ValueError:
                raise NjRankError(f"{k} is not ISO 8601: {raw[k]!r}")
    evidence = raw.get("evidence") or []
    if not isinstance(evidence, list):
        raise NjRankError("evidence must be a list of absolute paths")
    for p in evidence:
        if not Path(p).is_absolute():
            raise NjRankError(f"evidence path not absolute: {p}")
        if not os.path.isfile(longpath(p)):
            raise NjRankError(f"evidence missing on disk: {p}")
    kept = []
    for p in evidence:
        if Path(p).suffix.lower() in ALLOWED_EXT + LOCAL_EXT:
            kept.append(p)
        else:
            print(f"skipped (not evidence): {p} - allowed types are {', '.join(ALLOWED_EXT)}")
    evidence = kept
    item = {k: (raw.get(k) or None) for k in ("service_ar", "directorate_ar", "slug", "started",
                                              "finished", "time_source", "lane", "jira_project", "label")}
    item.update(project=raw["project"].strip(), session=raw["session"].strip(),
                title=raw["title"].strip(), description=raw["description"].strip(),
                work_type=raw["work_type"], evidence=[str(Path(p)) for p in evidence],
                jira_keys=list(raw.get("jira_keys") or []), existing_task=_task_key(raw.get("existing_task")), attach_evidence=bool(raw.get("attach_evidence")))
    return item


def register(root, raw):
    item = normalise(raw)
    key = dedupe_key(item)
    rows = load_registry(root)
    for r in rows:
        if r["dedupe_key"] == key:
            return "duplicate", r
    ident = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
    stamp = dt.datetime.fromisoformat(item["finished"]).strftime("%Y-%m-%d_%H%M")
    folder = Path(root) / safe_title(item["project"]) / safe_title(item["session"]) / stamp / safe_title(item["title"])
    if os.path.exists(longpath(folder / "item.json")):
        folder = folder.parent / f"{folder.name} [{ident}]"
    os.makedirs(longpath(folder), exist_ok=True)
    size = sum(os.stat(longpath(p)).st_size for p in item["evidence"])
    rec = {"n": max([r["n"] for r in rows], default=0) + 1, "id": ident, "status": "pending",
           "project": item["project"], "session": item["session"], "service_ar": item["service_ar"],
           "work_type": item["work_type"], "title": item["title"], "finished": item["finished"],
           "evidence_count": len(item["evidence"]), "evidence_bytes": size, "folder": str(folder),
           "dedupe_key": key, "jira_key": None, "jira_url": None, "error": None,
           "existing_task": item["existing_task"]}
    doc =dict(item, **{k: rec[k] for k in ("n", "id", "status", "dedupe_key", "folder", "evidence_bytes")},
               registered_at=now_iso(), jira_key=None, jira_url=None, archive=None,
               attached=[], too_big=[], error=None, staged=[])
    write_json(folder / "item.json", doc)
    rows.append(rec)
    save_registry(root, rows)
    write_text(Path(root) / ".last-registered", now_iso())
    return "added", rec


def import_jsonl(root, files):
    counts = Counter()
    for f in files:
        for lineno, line in enumerate(read_text(f).splitlines(), 1):
            if not line.strip():
                continue
            try:
                status, _ = register(root, json.loads(line))
                counts[status] += 1
            except (NjRankError, ValueError, KeyError) as e:
                counts["invalid"] += 1
                print(f"invalid {Path(f).name}:{lineno}: {e}")
    return counts


# ---------- preview ----------

METRICS_JS = (Path(__file__).with_name("metrics_tab.js")).read_text(encoding="utf-8")  # 📈 Metrics tab (Flint charts)
BUG_FIXED, BUG_DEV = {"done", "closed", "resolved"}, {"dev completed", "in qa", "ready for qa", "in progress"}


def bug_outcome(b):
    s = (b.get("status") or "").strip().lower()
    if b.get("nb") or is_not_bug(s):
        return "Not a bug"
    return "Fixed" if s in BUG_FIXED else "Dev done / in QA" if s in BUG_DEV else "Open"


def metrics_data(rows, bugs, label, team=None):
    """Rows the Metrics tab aggregates in the browser (the owner 2026-11-05): one entry per finished item / filed Bug,
    plus the weekly QA-team pull (team_metrics.py → <root>/team-metrics.json) when it exists."""
    work = [{"d": r["finished"][:10], "p": r["project"], "w": label.get(r["work_type"], r["work_type"])}
            for r in rows if r.get("finished")]
    bl = [{"d": (b.get("filed") or "")[:10], "s": b.get("status") or "", "g": bug_outcome(b),
           "svc": b.get("service") or "—"} for b in bugs]
    return json.dumps({"work": work, "bugs": bl, "team": team or None}, ensure_ascii=False)


def load_team(root):
    p = Path(root) / "team-metrics.json"
    try:
        return read_json(p) if os.path.exists(longpath(p)) else None
    except (OSError, ValueError):
        return None  # a broken team file never blocks the work-log preview

def preview_html(rows, counts, total_mb, bugs=(), tstat=None, team=None):
    """the owner's rule (2026-10-12): an HTML preview is always opened before anything is filed.
    ADHD-friendly: verdict first, tiles, one collapsible group per work type, icon + word states."""
    e = html.escape
    icon = {"pending": "⏳", "filed": "✅", "exists": "🔁", "failed": "❌"}
    label = {"srs": "SRS", "user-manual": "User manual", "user-manual-remake": "User manual (Kore remake)",
             "staff-manual": "Staff manual", "automation-tests": "Automation tests",
             "jira-filing": "Jira filing", "segment": "Pipelines & tools"}
    done = counts.get("filed", 0) + counts.get("exists", 0)
    verdict = ("All filed" if done == len(rows) else
               f"{counts.get('failed', 0)} failed — needs a look" if counts.get("failed") else
               f"{counts.get('pending', 0)} waiting to be filed")
    tiles = "".join(f"<div class='tile {e(k)}'><b>{v}</b><span>{icon.get(k, '•')} {e(k)}</span></div>"
                    for k, v in sorted(counts.items()))
    groups = {}
    tstat = tstat or {}
    nbk = lambda r: bool((tstat.get(r.get("jira_key") or "") or {}).get("nb"))
    for r in sorted(rows, key=lambda r: not nbk(r)):
        groups.setdefault(r["work_type"], []).append(r)
    sections = []
    for wt, items in sorted(groups.items(), key=lambda kv: (-sum(nbk(r) for r in kv[1]), -len(kv[1]))):
        mb = sum(r["evidence_bytes"] for r in items) / 1048576
        cards = []
        for r in items:
            jira = (f"<a href='{e(r['jira_url'])}' target='_blank'>{e(r['jira_key'])}</a>"
                    if r.get("jira_url") else "<span class='muted'>not filed</span>")
            err = f"<div class='err'>{e(r['error'])}</div>" if r.get("error") else ""
            ts = tstat.get(r.get("jira_key") or "") or {}
            if ts.get("status"):
                jira += f" · Jira: <b>{e(ts['status'])}</b>" + (f" ({e(ts['resolution'])})" if ts.get("resolution") else "")
            nbx = (NB_CHIP + nb_block(ts["nb"])) if ts.get("nb") else ""
            q = (r["title"] + " " + (r["service_ar"] or "") + " " + (r.get("jira_key") or "")).lower()
            cards.append(
                f"<article class='card {e(r['status'])}{' nb' if nbx else ''}' data-q='{e(q)}' data-st='{e(r['status'])}' data-wt='{e(wt)}' data-pj='{e(r['project'])}' "
                f"data-nb='{1 if nbx else 0}' data-n='{r['n']}' data-fin='{e(r['finished'] or '')}' data-mb='{r['evidence_bytes']}' data-t='{e(r['title'].lower())}'>"
                f"<div class='st'>{icon.get(r['status'], '•')} {e(r['status'])}</div>"
                f"<div class='main'>{nbx}<div class='t' dir='auto'>{e(r['title'])}</div>"
                f"<div class='meta'><span class='pj'>{e(r['project'])}</span><span>#{r['n']}</span><span>🗓 {e((r['finished'] or '-')[:16].replace('T', ' '))}</span>"
                f"<span>📎 {r['evidence_count']} files · {r['evidence_bytes'] / 1048576:.1f} MB</span>"
                f"<span>🔗 {jira}</span></div>{err}</div></article>")
        sections.append(f"<details open data-tab='work' data-wt='{e(wt)}'><summary><span>{e(label.get(wt, wt))}</span>"
                        f"<em>{len(items)} tasks · {mb:.0f} MB</em></summary>"
                        f"<div class='grid'>{''.join(cards)}</div></details>")
    st_chips = "".join(f"<button type='button' class='chip' data-k='st' data-v='{e(k)}'>{icon.get(k, '•')} {e(k)} <i>{v}</i></button>"
                       for k, v in sorted(counts.items()))
    wt_chips = "".join(f"<button type='button' class='chip' data-k='wt' data-v='{e(wt)}'>{e(label.get(wt, wt))} <i>{len(items)}</i></button>"
                       for wt, items in sorted(groups.items(), key=lambda kv: -len(kv[1])))
    live = "true" if counts.get("pending") else "false"  # auto-reload every 15 s while work is in flight
    pj_chips = "".join(f"<button type='button' class='chip' data-k='pj' data-v='{e(k)}'>📁 {e(k)} <i>{v}</i></button>"
                       for k, v in Counter(r["project"] for r in rows).most_common())
    nb_total = sum(1 for b in bugs if b.get("nb")) + sum(1 for r in rows if nbk(r))
    nb_top = f"<div class='nbtop'>🚫 ليس Bug: {nb_total}</div>" if nb_total else ""
    bcount = Counter(b["status"] for b in bugs)
    bst_chips = "".join(f"<button type='button' class='chip' data-k='bst' data-v='{e(k)}'>🐞 {e(k)} <i>{v}</i></button>"
                        for k, v in sorted(bcount.items()))
    mdata = metrics_data(rows, bugs, label, team).replace("</", "<\\/")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>nj-rank preview</title>
<script>try{{const t=localStorage.getItem('njr-theme');if(t==='light'||t==='dark')document.documentElement.dataset.theme=t}}catch(e){{}}</script><style>
.card.nb{{border:2px solid #c0392b;border-inline-start:5px solid #c0392b;box-shadow:0 0 0 4px #c0392b,0 0 22px 6px rgba(192,57,43,.55);margin:6px 0}}.nbchip,.nbtop{{background:#c0392b;color:#fff;border-radius:8px;padding:2px 10px;font-weight:700;display:inline-block}}.nbq{{background:rgba(192,57,43,.12);border-radius:8px;padding:6px 10px;margin:6px 0;direction:rtl}}

:root{{--bg:#f6f5f2;--card:#fff;--ink:#1b1b1f;--muted:#6b6b75;--line:#e4e2dc;--accent:#5b4bdb;--ok:#138a52;--wait:#b7791f;--bad:#c53030;--dup:#2b6cb0;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#141417;--card:#1d1d22;--ink:#ececf1;--muted:#9a9aa6;--line:#2c2c33;--accent:#8b7cff;--ok:#3ecf8e;--wait:#f6c453;--bad:#ff6b6b;--dup:#63b3ed;color-scheme:dark}}}}
:root[data-theme=dark]{{--bg:#141417;--card:#1d1d22;--ink:#ececf1;--muted:#9a9aa6;--line:#2c2c33;--accent:#8b7cff;--ok:#3ecf8e;--wait:#f6c453;--bad:#ff6b6b;--dup:#63b3ed;color-scheme:dark}}
.tile b,.mtile b,.chip i,.tabs i,.meta{{font-variant-numeric:tabular-nums}}
#theme{{margin-inline-start:auto;min-width:118px}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:13px/1.5 'Thmanyah Serif Text',Georgia,serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:28px 16px 60px}}
h1{{font-family:'Thmanyah Serif Display',Georgia,serif;font-weight:900;font-size:28px;margin:0}}
.verdict{{font-size:16px;color:var(--accent);margin:4px 0 18px}}
.tiles{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}}
.tile{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 18px;min-width:130px}}
.tile b{{display:block;font-size:24px}}.tile span{{color:var(--muted)}}
.tile.filed b{{color:var(--ok)}}.tile.pending b{{color:var(--wait)}}.tile.failed b{{color:var(--bad)}}.tile.exists b{{color:var(--dup)}}
.bar{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px;position:sticky;top:0;z-index:2;background:var(--bg);padding:8px 0}}
.bar input{{flex:1;min-width:220px}}
input,select,button{{padding:10px 14px;border-radius:12px;border:1px solid var(--line);background:var(--card);color:var(--ink);font:inherit}}
button{{cursor:pointer}}button:hover{{border-color:var(--accent)}}
.chips{{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:10px}}
.lbl{{color:var(--muted);font-size:11px;min-width:80px}}
.chip{{padding:6px 12px;border-radius:999px;font-size:12px}}.chip i{{font-style:normal;color:var(--muted);margin-inline-start:4px}}
.chip.on{{background:var(--accent);border-color:var(--accent);color:#fff}}.chip.on i{{color:#fff}}
.count{{color:var(--muted);font-size:11px;margin:6px 0 14px}}
.pj{{background:var(--line);color:var(--ink);border-radius:999px;padding:0 8px}}
.tabs{{display:flex;gap:8px;margin:0 0 14px}}.tabs button{{font-weight:700;border-radius:12px}}.tabs button.on{{background:var(--accent);color:#fff;border-color:var(--accent)}}
.tabs i{{font-style:normal;opacity:.75;margin-inline-start:4px}}
body:not([data-tab=work]) [data-tab=work],body:not([data-tab=bugs]) [data-tab=bugs],body:not([data-tab=metrics]) [data-tab=metrics],body[data-tab=metrics] .bar,body[data-tab=metrics] #count{{display:none!important}}
.mbar{{display:grid;grid-template-columns:auto repeat(3,150px);gap:10px;align-items:center;margin-bottom:14px}}.mbar button{{font-weight:700}}.mbar button.on{{background:var(--accent);border-color:var(--accent);color:#fff}}
.mstory{{background:var(--card);border:1px solid var(--line);border-inline-start:6px solid var(--accent);border-radius:16px;padding:16px 20px;margin-bottom:22px}}
.mstory h3,.mh{{margin:0 0 10px;font:700 18px 'Thmanyah Serif Display',Georgia,serif}}.mh{{margin-top:8px}}
.mstory p{{display:grid;grid-template-columns:30px 1fr;gap:8px;margin:0 0 10px;font-size:16px;line-height:1.6}}.mstory .si{{font-size:18px}}
.good{{color:var(--ok)}}.bad{{color:var(--bad)}}.hint{{color:var(--muted);font-size:11px;margin:0 0 8px}}.mstory p.hint{{display:block;margin:6px 0 0}}
.mcompare{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:22px}}
.board{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px 16px}}.board h4{{margin:0;font-size:15px}}
.brow{{display:grid;grid-template-columns:30px 110px 1fr 52px;gap:8px;align-items:center;padding:7px 6px;border-radius:10px;font-variant-numeric:tabular-nums}}
.brow.me{{background:color-mix(in srgb,var(--accent) 14%,transparent);font-weight:700}}.brow .rk{{text-align:center}}.brow b{{text-align:end}}
.brow .nm small{{display:block;color:var(--muted);font-size:10px;font-weight:400}}
.bt{{height:12px;background:var(--line);border-radius:6px;overflow:hidden}}.bt i{{display:block;height:100%;background:var(--muted);border-radius:6px}}.brow.me .bt i{{background:var(--accent)}}
.mcard{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:12px;overflow-x:auto;margin-bottom:14px}}.say{{margin:0 0 6px;font-size:14px}}
.mgrid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:0 14px 14px}}.mgrid .mcard{{margin:0;min-height:300px}}.mcard.wide{{grid-column:1/-1}}
.mmore{{margin-top:8px}}.mempty{{color:var(--muted)}}#m-msg{{color:var(--muted);margin:6px 0}}
@media (max-width:900px){{.mgrid,.mcompare{{grid-template-columns:1fr}}.mbar{{grid-template-columns:1fr 1fr 1fr}}.mbar .lbl{{grid-column:1/-1}}}}
.card.bug{{border-inline-start-color:var(--bad)}}.card.bug.done,.card.bug.closed,.card.bug.not-a-bug,.card.bug.resolved{{border-inline-start-color:var(--ok)}}
.card.bug.in-qa,.card.bug.ready-for-qa,.card.bug.in-progress{{border-inline-start-color:var(--dup)}}
details{{background:var(--card);border:1px solid var(--line);border-radius:16px;margin-bottom:14px;overflow:hidden}}
summary{{cursor:pointer;padding:14px 18px;display:flex;justify-content:space-between;font-family:'Thmanyah Serif Display',Georgia,serif;font-weight:700;font-size:16px}}
summary em{{font-style:normal;color:var(--muted);font-size:12px;font-weight:400}}
.grid{{display:grid;gap:10px;padding:0 14px 14px}}
.card{{display:flex;gap:14px;border:1px solid var(--line);border-inline-start:4px solid var(--wait);border-radius:12px;padding:10px 14px}}
.card.filed{{border-inline-start-color:var(--ok)}}.card.failed{{border-inline-start-color:var(--bad)}}.card.exists{{border-inline-start-color:var(--dup)}}
.st{{min-width:92px;color:var(--muted);font-size:11px;padding-top:2px}}.main{{flex:1;min-width:0}}
.t{{font-weight:700;font-size:14px}}.meta{{display:flex;gap:16px;flex-wrap:wrap;color:var(--muted);font-size:11px}}
.meta a{{color:var(--accent)}}.muted{{opacity:.7}}.err{{color:var(--bad);font-size:11px;margin-top:4px}}
@media (max-width:640px){{.card{{flex-direction:column;gap:4px}}}}
</style></head><body><div class="wrap">
<h1>nj-rank preview</h1><div class="muted">Updated {e(now_iso()[:19].replace('T', ' '))}{' · refreshes every 15 s' if live == 'true' else ''}</div>{nb_top}<div class="verdict">{e(verdict)} · {len(rows)} tasks · {total_mb / 1024:.2f} GB of evidence</div>
<nav class="tabs"><button type="button" data-go="work" class="on">🗂 Work log <i>{len(rows)}</i></button>
<button type="button" data-go="bugs">🐞 Jira Bugs <i>{len(bugs)}</i></button>
<button type="button" data-go="metrics">📈 Metrics</button>
<button type="button" id="theme" title="Switch light / dark">🌓 Auto</button></nav>
<section data-tab="metrics" id="njr-metrics"><div class="mbar" id="m-period"><span class="lbl">🗓 Looking at</span>
<button type="button" data-p="7">Last 7 days</button><button type="button" data-p="28">Last 4 weeks</button><button type="button" data-p="84">Last 12 weeks</button></div>
<div class="mstory" id="m-story"></div>
<h3 class="mh">🏁 How you compare with the QA team</h3><div class="mcompare" id="m-compare"></div>
<h3 class="mh">📈 Your trend</h3><div id="m-msg"></div><div id="m-trend"></div>
<details id="m-more" class="mmore"><summary><span>🔎 More detail (optional)</span><em>by person, project, work type, service</em></summary><div class="mgrid" id="m-grid"></div></details></section>
<div data-tab="work"><div class="tiles">{tiles}</div></div>
<div class="bar"><input id="q" type="search" placeholder="🔎 Search title, service or Jira key…">
<select id="sort"><option value="fin-d">Newest first</option><option value="fin-a">Oldest first</option>
<option value="t-a">Title A→Z</option><option value="t-d">Title Z→A</option><option value="mb-d">Largest evidence</option>
<option value="mb-a">Smallest evidence</option><option value="n-a"># ascending</option></select>
<button id="tog" type="button">Collapse all</button><button id="reset" type="button">Reset</button></div>
<div data-tab="work"><div class="chips"><span class="lbl">Status</span>{st_chips}</div>
<div class="chips"><span class="lbl">Work type</span>{wt_chips}</div>
<div class="chips"><span class="lbl">Project</span>{pj_chips}</div></div>
<div data-tab="bugs"><div class="chips"><span class="lbl">Bug status</span>{bst_chips}</div></div>
<div class="count" id="count"></div>
{''.join(sections)}{bugs_html(bugs)}</div>
<script>
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const q=$('#q'),sort=$('#sort');
function on(kind){{return new Set($$('.chip[data-k="'+kind+'"].on').map(b=>b.dataset.v))}}
function apply(){{
  const v=q.value.trim().toLowerCase(),st=on('st'),wt=on('wt'),bst=on('bst'),pj=on('pj'),tab=document.body.dataset.tab;let shown=0;
  const [key,dir]=sort.value.split('-'),m=dir==='a'?1:-1;
  $$('.grid').forEach(g=>{{
    const cs=[...g.children];
    cs.sort((a,b)=>{{const z=(b.dataset.nb|0)-(a.dataset.nb|0);if(z)return z;let x=a.dataset[key],y=b.dataset[key];if(key==='n'||key==='mb'){{x=+x;y=+y}}return (x>y?1:x<y?-1:0)*m}});
    const isBug=g.closest('details').dataset.tab==='bugs';
    cs.forEach(c=>{{const ok=(!v||c.dataset.q.includes(v))&&(isBug?(!bst.size||bst.has(c.dataset.bst)):((!st.size||st.has(c.dataset.st))&&(!wt.size||wt.has(c.dataset.wt))&&(!pj.size||pj.has(c.dataset.pj))));
      if(ok&&(isBug?'bugs':'work')===tab)shown++;
      c.style.display=ok?'':'none';g.appendChild(c)}});
    const d=g.closest('details');d.style.display=cs.some(c=>c.style.display!=='none')?'':'none';
  }});
  $('#count').textContent='Showing '+shown+' of '+(tab==='bugs'?{len(bugs)}:{len(rows)});
}}
function go(t){{document.body.dataset.tab=t;$$('.tabs button').forEach(b=>b.classList.toggle('on',b.dataset.go===t));history.replaceState(null,'','#'+t);apply();if(t==='metrics')window.njMetrics()}}
$$('.tabs button[data-go]').forEach(b=>b.onclick=()=>go(b.dataset.go));
const TH={{'':'🌓 Auto',light:'☀ Light',dark:'🌙 Dark'}},thb=$('#theme');thb.textContent=TH[document.documentElement.dataset.theme||''];
thb.onclick=()=>{{const order=['','light','dark'],cur=document.documentElement.dataset.theme||'',nx=order[(order.indexOf(cur)+1)%3];
  if(nx)document.documentElement.dataset.theme=nx;else delete document.documentElement.dataset.theme;
  try{{localStorage.setItem('njr-theme',nx)}}catch(e){{}}thb.textContent=TH[nx];if(document.body.dataset.tab==='metrics')window.njMetrics()}};
document.body.dataset.tab=['#bugs','#metrics'].includes(location.hash)?location.hash.slice(1):'work';$$('.tabs button').forEach(b=>b.classList.toggle('on',b.dataset.go===document.body.dataset.tab));
$$('.chip').forEach(b=>b.onclick=()=>{{b.classList.toggle('on');apply()}});
q.oninput=apply;sort.onchange=apply;
$('#tog').onclick=e=>{{const open=e.target.textContent==='Expand all';$$('details').forEach(d=>d.open=open);e.target.textContent=open?'Collapse all':'Expand all'}};
$('#reset').onclick=()=>{{q.value='';sort.value='fin-d';$$('.chip.on').forEach(b=>b.classList.remove('on'));apply()}};
function save(){{sessionStorage.setItem('njr',JSON.stringify({{q:q.value,s:sort.value,c:$$('.chip.on').map(b=>b.dataset.k+':'+b.dataset.v),y:scrollY}}))}}
try{{const st=JSON.parse(sessionStorage.getItem('njr')||'null');if(st){{q.value=st.q;sort.value=st.s;
  st.c.forEach(k=>{{const [a,b]=k.split(':');$$('.chip').forEach(c=>{{if(c.dataset.k===a&&c.dataset.v===b)c.classList.add('on')}})}});setTimeout(()=>scrollTo(0,st.y),0)}}}}catch(e){{}}
apply();
if({live}){{setInterval(()=>{{save();location.reload()}},15000)}}
</script>
<script type="application/json" id="njr-mdata">{mdata}</script>
<script>{METRICS_JS}
if(document.body.dataset.tab==='metrics')window.njMetrics();</script>
</body></html>"""



def open_file(path):
    if os.name == "nt":
        os.startfile(str(path))  # noqa: the preview is always shown to the owner


def load_bugs(root):
    """Jira Bug trackers merged into the preview (the owner 2026-10-12). Config: <root>/trackers.json."""
    cfg = Path(root) / "trackers.json"
    if not os.path.exists(longpath(cfg)):
        return []
    bugs = []
    try:
        trackers = read_json(cfg)
    except (OSError, ValueError):
        return []  # a broken tracker config never blocks the work-log preview
    for t in trackers:
        try:
            tickets = read_json(t["tickets"])
            latest = read_json(t["latest"]) if t.get("latest") and os.path.exists(longpath(t["latest"])) else {}
        except (OSError, ValueError):
            continue
        for tk in tickets:
            live = latest.get(tk["key"]) or {}
            bugs.append({"tracker": t.get("name", ""), "key": tk["key"],
                         "status": live.get("status") or tk.get("status") or "unknown",
                         "service": tk.get("service") or "", "directorate": tk.get("directorate") or "",
                         "summary": live.get("summary") or tk.get("note") or "", "nb": live.get("nb"),
                         "assignee": live.get("assignee") or "", "updated": live.get("updated") or "",
                         "filed": tk.get("filedAt") or "", "story": tk.get("story") or "",
                         "url": f"{t.get('baseUrl', '').rstrip('/')}/browse/{tk['key']}"})
    return bugs


def bugs_html(bugs):
    e = html.escape
    if not bugs:
        return "<p class='muted'>No tracker configured (add &lt;root&gt;/trackers.json).</p>"
    groups = {}
    for b in bugs:
        groups.setdefault((b["directorate"], b["service"]), []).append(b)
    out = []
    nbn = lambda it: sum(1 for b in it if b.get("nb"))
    for (d, svc), items in sorted(groups.items(), key=lambda kv: (-nbn(kv[1]), kv[0])):
        items = sorted(items, key=lambda b: not b.get("nb"))
        cards = "".join(
            f"<article class='card bug {e(b['status'].lower().replace(' ', '-'))}{' nb' if b.get('nb') else ''}' data-nb='{1 if b.get('nb') else 0}' data-q='{e((b['key'] + ' ' + svc + ' ' + b['summary']).lower())}' "
            f"data-bst='{e(b['status'])}' data-n='{e(b['key'][5:] if b['key'][4:5] == '-' else b['key'])}' data-fin='{e(b['updated'])}' data-mb='0' data-t='{e(b['summary'].lower())}'>"
            f"<div class='st'>🐞 {e(b['status'])}</div><div class='main'>{NB_CHIP + nb_block(b['nb']) if b.get('nb') else ''}<div class='t' dir='auto'>{e(b['summary'])}</div>"
            f"<div class='meta'><span>🔗 <a href='{e(b['url'])}' target='_blank'>{e(b['key'])}</a></span>"
            f"<span>👤 {e(b['assignee'] or '-')}</span><span>🗓 filed {e(b['filed'][:10])}</span>"
            f"<span>↻ {e(b['updated'][:16].replace('T', ' ') or '-')}</span>"
            f"{'<span>📘 ' + e(b['story']) + '</span>' if b['story'] else ''}</div></div></article>" for b in items)
        out.append(f"<details open data-tab='bugs'><summary><span dir='auto'>{e(svc)}</span><em dir='auto'>{e(d)} · {len(items)} bugs</em></summary>"
                   f"<div class='grid'>{cards}</div></details>")
    return "".join(out)


def write_preview(root):
    rows = load_registry(root)
    # projects or item ids the owner removed from the preview, e.g. ["Personal", "8023998ee53a"]; the registry row itself stays (KPI hard rule)
    hide_cfg = Path(root) / "preview-hide.json"
    if os.path.exists(longpath(hide_cfg)):
        try:
            hidden = set(read_json(hide_cfg))
            rows = [r for r in rows if r["project"] not in hidden and r["id"] not in hidden]
        except (OSError, ValueError):
            pass
    lines = ["# nj-rank preview", "",
             "| # | project | service | work type | title | finished | evidence | status |",
             "|---|---|---|---|---|---|---|---|"]
    total_mb = 0.0
    for r in rows:
        mb = r["evidence_bytes"] / (1024 * 1024)
        total_mb += mb
        cells = [str(r["n"]), r["project"], r["service_ar"] or "-", r["work_type"],
                 r["title"], r["finished"] or "-", f"{r['evidence_count']} / {mb:.1f} MB", r["status"]]
        lines.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
    write_text(Path(root) / "preview.md", "\n".join(lines) + "\n")
    counts = Counter(r["status"] for r in rows)
    tpath = Path(root) / "task-status.json"
    page = preview_html(rows, counts, total_mb, load_bugs(root), read_json(tpath) if os.path.exists(longpath(tpath)) else {},
                        load_team(root))
    write_text(Path(root) / "preview.html", page)
    if Path(root).resolve() == Path(DEFAULT_ROOT).resolve():
        write_text(Path(DESKTOP_COPY), page)  # the owner 2026-10-12: a copy on the Desktop
    return {"items": len(rows), "evidence_mb": round(total_mb, 1), **dict(counts)}


# ---------- filing ----------

def compose_description(doc):
    """Task body = the registered description only (PROJ-5169 layout: the owner's own work, 2-3 short
    labelled blocks, one line per Bug key). No time/evidence/agent-count lines (the owner 2026-10-20)."""
    return doc["description"].strip()


def default_run(args):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout + p.stderr


def sevenzip_path():
    if os.environ.get("NJ_RANK_7Z"):
        return os.environ["NJ_RANK_7Z"]
    if os.path.exists(SEVEN_ZIP):
        return SEVEN_ZIP
    found = shutil.which("7z")
    if not found:
        raise NjRankError("7-Zip not found: set NJ_RANK_7Z or install 7z")
    return found


def archive_evidence(folder, files, run, sevenzip):
    arc = Path(folder) / "evidence.7z"
    rc, out = run([sevenzip, "a", "-t7z", "-mx=9", "-spf2", "-bso0", "-bsp0", longpath(arc)]  # -spf2: keep paths, so two README.md never collide
                  + [longpath(f) for f in files])
    if rc != 0:
        raise NjRankError(f"7z a failed ({rc}): {out[-200:]}")
    rc, out = run([sevenzip, "t", longpath(arc)])
    if rc != 0:
        raise NjRankError(f"7z t failed ({rc}): {out[-200:]}")
    return arc


def recycle(path, run):
    script = ("Add-Type -AssemblyName Microsoft.VisualBasic; "
              "[Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile("
              f"'{str(path).replace(chr(39), chr(39) * 2)}','OnlyErrorDialogs','SendToRecycleBin')")
    rc, out = run(["powershell", "-NoProfile", "-Command", script])
    if rc != 0:
        raise NjRankError(f"recycle failed for {path}")


def cleanup_staged(root, doc, run):
    """Delete only files nj-rank itself staged inside root (recycle bin). Anything else is left alone."""
    removed, kept = 0, []
    root_resolved = Path(root).resolve()
    for p in doc.get("staged") or []:
        target = Path(p).resolve()
        try:
            target.relative_to(root_resolved)
        except ValueError:
            kept.append(p)
            continue
        if os.path.exists(longpath(target)):
            recycle(target, run)
            removed += 1
    return removed, kept


def file_one(root, jira, me, limit, rec, run, sevenzip):
    folder = Path(rec["folder"])
    doc = read_item(folder)
    title = doc["title"]
    project = doc.get("jira_project") or doc["project"]  # work of project X may be filed into Jira project Y
    existing = doc.get("existing_task")  # register against a Task that already exists: never create a second one
    if existing:
        f = jira.get_issue(existing).get("fields", {})
        if (f.get("issuetype") or {}).get("name") != "Task" or (f.get("assignee") or {}).get("name") != me:
            raise NjRankError(f"{existing} is not a Task assigned to the API user (refused)")
    hits = [] if existing else find_exact_tasks(jira, project, title)
    resume = existing or (rec.get("jira_key") if rec.get("jira_key") in hits else None)  # existing Task, or our own half-filed one
    if hits and not resume:
        update(root, rec["id"], status="exists", jira_key=hits[0],
               jira_url=f"{jira.cfg['baseUrl']}/browse/{hits[0]}", error=None)
        return "exists"
    key = resume or jira.create_task(project, title, compose_description(doc), me, doc.get("label") or STAGE_LABEL)
    update(root, rec["id"], jira_key=key, jira_url=f"{jira.cfg['baseUrl']}/browse/{key}")
    have = {a.get("filename") for a in (jira.get_issue(key).get("fields", {}).get("attachment") or [])} if resume else set()
    for k in ([] if resume else doc.get("jira_keys") or []):  # "relates to" every Bug/finding
        try:
            jira.link(key, k)
        except NjRankError as e:
            print(f"link {key} -> {k} failed: {jira.mask(e)}")
    files = [Path(p) for p in doc["evidence"] if os.path.isfile(longpath(p))]
    attached, too_big, local_only = [], [], []
    for p in files:
        if not doc.get("attach_evidence"):  # no attachments of our reports by default (the owner 2026-10-20)
            local_only.append(str(p))
            continue
        if p.suffix.lower() not in ALLOWED_EXT:
            local_only.append(str(p))  # stays on disk (and in evidence.7z), listed in the filing record
            continue
        if os.stat(longpath(p)).st_size > limit:
            too_big.append(str(p))
            continue
        if p.name not in have:
            jira.attach(key, p)
        attached.append(p.name)
    if too_big and not resume:
        jira.add_comment(key, "Evidence above the upload limit, kept on disk (not attached):\n"
                         + "\n".join(too_big))
    status = ((jira.get_issue(key).get("fields", {}).get("status") or {}).get("statusCategory") or {}).get("key") if resume else None
    if status != "done":
        jira.transition_done(key)
    problems = verify_filed(jira.get_issue(key), me, len(have | set(attached)))
    if problems:
        raise NjRankError(f"{key} read-back failed: " + "; ".join(problems))
    archive = str(archive_evidence(folder, files, run, sevenzip)) if files else None
    update(root, rec["id"], status="filed", error=None, archive=archive, attached=attached, too_big=too_big, local_only=local_only)
    return "filed"


def file_items(root, jira, only=None, dry_run=False, retry_failed=False, run=default_run, sevenzip=None,
               link_to=None):
    me = jira.myself()
    limit = jira.upload_limit()
    if not dry_run and sevenzip is None:
        sevenzip = sevenzip_path()
    results = Counter()
    wanted = {"pending", "failed"} if retry_failed else {"pending"}
    for rec in load_registry(root):
        if rec["status"] not in wanted or (only and rec["n"] not in only):
            continue
        if rec["project"].strip().upper() != "PROJ":  # only PROJ work is tasked (owner, 2026-10-19)
            results["skipped-non-proj"] += 1
            print(f"#{rec['n']} skipped (not PROJ, no Jira Task): {rec['title']}")
            continue
        if dry_run:
            hits = find_exact_tasks(jira, read_item(rec["folder"]).get("jira_project") or rec["project"], rec["title"])
            results["would-exists" if hits else "would-file"] += 1
            print(f"#{rec['n']} {'exists' if hits else 'would file'}: {rec['title']}"
                  + (f" (would link to {link_to})" if link_to and not hits else ""))
            continue
        try:
            outcome = file_one(root, jira, me, limit, rec, run, sevenzip)
            results[outcome] += 1
            print(f"#{rec['n']} {outcome}: {rec['title']}")
            if link_to and outcome == "filed":
                try:  # the Task stays filed; a failed link is reported, not retried
                    jira.link(next(r for r in load_registry(root) if r["id"] == rec["id"])["jira_key"], link_to)
                except Exception as e:
                    results["link_failed"] += 1
                    print(f"#{rec['n']} link to {link_to} failed: {jira.mask(e)}")
        except Exception as e:  # item failure: record, keep files, continue
            msg = jira.mask(e)
            update(root, rec["id"], status="failed", error=msg)
            results["failed"] += 1
            print(f"#{rec['n']} failed: {msg}")
    return dict(results)


# ---------- close-mine ----------

KEY_RE = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b")
GUARD_LABELS = {"untestable", "wrapup"}  # Tasks a wrap-up created: close-mine must never close them


def sync_status(root, jira):
    """Read-only: refresh the Jira status of every registry Task into <root>/task-status.json (nothing is transitioned)."""
    out = {}
    for r in load_registry(root):
        k = r.get("jira_key") or r.get("existing_task")  # read-only: a registered-against Task is tracked before it is filed
        if not k or k in out:
            continue
        try:
            i = jira.get_full(k)
        except JiraError as e:
            print(f"{k}: {jira.mask(e)}")
            continue
        f = i.get("fields") or {}
        out[k] = {"status": (f.get("status") or {}).get("name", ""), "resolution": (f.get("resolution") or {}).get("name", ""),
                  "assignee": (f.get("assignee") or {}).get("displayName", ""), "updated": f.get("updated", ""), "nb": not_bug_of(i)}
    write_json(Path(root) / "task-status.json", out)
    return {"tasks": len(out), "not_a_bug": sum(1 for v in out.values() if v["nb"])}


def load_protect(spec):
    """Keys to protect: a file (trace.json or any text; every issue key in it) or a comma/space list."""
    if not spec:
        return set()
    if os.path.isfile(longpath(spec)):
        return set(KEY_RE.findall(read_text(spec)))
    return set(KEY_RE.findall(str(spec)))


def close_mine(root, jira, apply=False, protect=()):
    project = jira.cfg["projectKey"]
    protect = set(protect)
    ranked = {r["jira_key"] for r in load_registry(root) if r.get("jira_key")}  # the work-log Tasks nj-rank itself filed
    jql = (f"project = {project} AND issuetype = Task AND "
           "(reporter = currentUser() OR assignee = currentUser()) AND statusCategory != Done")
    issues = jira.search(jql, ["summary", "status", "assignee", "reporter", "issuetype", "labels"])
    tasks = [i for i in issues if (i["fields"].get("issuetype") or {}).get("name") == "Task"]
    todo, skipped = [], []  # skipped = (issue, reason)
    for i in tasks:
        hit = GUARD_LABELS & {x.lower() for x in (i["fields"].get("labels") or [])}
        if hit:
            skipped.append((i, "label " + "/".join(sorted(hit))))
        elif i["key"] in protect:
            skipped.append((i, "protected (session trace)"))
        elif i["key"] in ranked:
            skipped.append((i, "protected (nj-rank registry)"))
        else:
            todo.append(i)

    def row(i, extra=""):
        f = i["fields"]
        return (f"| {i['key']} | {f.get('summary', '')} | {(f.get('status') or {}).get('name', '')} | "
                f"{(f.get('reporter') or {}).get('name', '')} | {(f.get('assignee') or {}).get('name', '-')} |{extra}")
    lines = ["# close-mine preview", "", f"JQL: `{jql}`", "", "## Would close",
             "| key | summary | status | reporter | assignee |", "|---|---|---|---|---|"]
    lines += [row(i) for i in todo]
    lines += ["", "## Skipped (never closed)", "| key | summary | status | reporter | assignee | why |",
              "|---|---|---|---|---|---|"]
    lines += [row(i, f" {why} |") for i, why in skipped]
    write_text(Path(root) / "close-mine-preview.md", "\n".join(lines) + "\n")
    for i, why in skipped:
        print(f"skip {i['key']}: {why}")
    result = {"open_tasks": len(tasks), "skipped_non_task": len(issues) - len(tasks),
              "skipped_protected": len(skipped)}
    if not apply:
        result["would_close"] = len(todo)
        return result
    closed = failed = 0
    for i in todo:
        try:
            jira.transition_done(i["key"])
            issue = jira.get_issue(i["key"])
            if ((issue["fields"].get("status") or {}).get("statusCategory") or {}).get("key") != "done":
                raise NjRankError("read-back: not Done")
            closed += 1
        except Exception as e:
            failed += 1
            print(f"{i['key']} failed: {jira.mask(e)}")
    result.update(closed=closed, failed=failed)
    return result


# ---------- CLI ----------

def build_parser():
    p = argparse.ArgumentParser(prog="nj_rank")
    sub = p.add_subparsers(dest="cmd", required=True)

    def item_flags(sp):
        sp.add_argument("--json", help="item as inline JSON or a path to a .json file")
        sp.add_argument("--project", default="PROJ")
        sp.add_argument("--session")
        sp.add_argument("--title")
        sp.add_argument("--description")
        sp.add_argument("--work-type", dest="work_type")
        sp.add_argument("--service-ar", dest="service_ar")
        sp.add_argument("--directorate-ar", dest="directorate_ar")
        sp.add_argument("--slug")
        sp.add_argument("--started")
        sp.add_argument("--finished")
        sp.add_argument("--time-source", dest="time_source")
        sp.add_argument("--evidence", action="append", default=[])
        sp.add_argument("--jira-key", dest="jira_keys", action="append", default=[])
        sp.add_argument("--lane")
        sp.add_argument("--existing-task", dest="existing_task", metavar="KEY",
                        help="register against this existing Task (no second Task is created); file only attaches/closes it")
        sp.add_argument("--label", help="override the Jira stage label (default STAGE_LABEL)")

    item_flags(sub.add_parser("register"))
    item_flags(sub.add_parser("log"))
    imp = sub.add_parser("import")
    imp.add_argument("files", nargs="+")
    sub.add_parser("preview").add_argument("--no-open", action="store_true")
    f = sub.add_parser("file")
    f.add_argument("--only", help="comma list of registry numbers, e.g. 1,4,9")
    f.add_argument("--dry-run", action="store_true")
    f.add_argument("--retry-failed", action="store_true")
    f.add_argument("--link-to", dest="link_to", metavar="KEY", help="Relates-link each Done Task to this source key")
    c = sub.add_parser("close-mine")
    c.add_argument("--apply", action="store_true")
    c.add_argument("--protect", metavar="FILE_OR_KEYS",
                   help="trace.json (or a key list) whose keys are never closed; env NJ_RANK_PROTECT also works. "
                        "`none` = protect nothing and force a dry run. --apply without any protect is refused. "
                        "Tasks in the nj-rank registry are always protected")
    sub.add_parser("sync", help="read-only: refresh Jira status of every registered Task into task-status.json")
    ln = sub.add_parser("link", help="Relates-link two issues (REST v2 issueLink)")
    ln.add_argument("a")
    ln.add_argument("b")
    ln.add_argument("--type", default="Relates")
    sub.add_parser("whoami")
    return p


def item_from_args(a):
    if a.json:
        text = read_text(a.json) if os.path.isfile(longpath(a.json)) else a.json
        return json.loads(text)
    return {"project": a.project, "session": a.session, "title": a.title, "description": a.description,
            "work_type": a.work_type, "service_ar": a.service_ar, "directorate_ar": a.directorate_ar,
            "slug": a.slug, "started": a.started, "finished": a.finished, "time_source": a.time_source,
            "evidence": a.evidence, "jira_keys": a.jira_keys, "lane": a.lane, "label": a.label, "existing_task": a.existing_task}


def main(argv=None, env=None, opener=None, run=None, root=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    a = build_parser().parse_args(argv)
    env = os.environ if env is None else env
    root = Path(root or env.get("NJ_RANK_ROOT") or DEFAULT_ROOT)
    try:
        if a.cmd in ("register", "log"):
            status, rec = register(root, item_from_args(a))
            print(f"{status}: #{rec['n']} {rec['folder']}")
        elif a.cmd == "import":
            print(dict(import_jsonl(root, a.files)))
        elif a.cmd == "preview":
            print(write_preview(root))
            if not a.no_open and not env.get("NJ_RANK_NO_OPEN"):
                open_file(root / "preview.html")
                write_text(root / ".preview-opened", now_iso())
        else:
            jira = Jira(load_config(env), opener=opener)
            if a.cmd == "whoami":
                print(jira.myself())
            elif a.cmd == "file":
                opened, reg = root / ".preview-opened", root / ".last-registered"
                if not a.dry_run and reg.exists() and (not opened.exists() or opened.stat().st_mtime < reg.stat().st_mtime):
                    raise NjRankError("run `preview` first: the owner sees the HTML preview before anything is filed")
                only = {int(x) for x in a.only.split(",")} if a.only else None
                print(file_items(root, jira, only=only, dry_run=a.dry_run, retry_failed=a.retry_failed,
                                 run=run or default_run, link_to=a.link_to))
            elif a.cmd == "close-mine":
                if a.apply and not (a.protect or env.get("NJ_RANK_PROTECT")):
                    raise NjRankError("close-mine --apply needs --protect <trace.json|keys> (or NJ_RANK_PROTECT); `--protect none` runs a dry run only")
                dry = (a.protect or "").lower() == "none"
                print(close_mine(root, jira, apply=a.apply and not dry,
                                 protect=load_protect(a.protect) | load_protect(env.get("NJ_RANK_PROTECT"))))
            elif a.cmd == "sync":
                print(sync_status(root, jira))
            elif a.cmd == "link":
                jira.link(a.a, a.b, a.type)
                print(f"linked {a.a} {a.type} {a.b}")
        return 0
    except NjRankError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except (ValueError, KeyError, OSError) as e:
        print(f"error: {type(e).__name__}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
