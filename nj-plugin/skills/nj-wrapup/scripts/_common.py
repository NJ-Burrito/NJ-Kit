"""Shared helpers for nj-wrapup scripts. Stdlib only. Never prints credentials."""
from __future__ import annotations
import base64, glob, json, os, re, sys, urllib.error, urllib.request

def utf8():
    for s in (sys.stdout, sys.stderr):
        try: s.reconfigure(encoding="utf-8")
        except Exception: pass

def nat(k):  # natural sort key: N2 < N10
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", str(k))]

def load_creds(path=None):
    """env JIRA_BASE_URL/JIRA_USER/JIRA_PASS first, else a JSON file (flat or {"jira":{...}})."""
    b, u, p = (os.environ.get(k) for k in ("JIRA_BASE_URL", "JIRA_USER", "JIRA_PASS"))
    if not (b and u and p) and path:
        d = json.load(open(path, encoding="utf-8"))
        d = d.get("jira", d)
        b = b or d.get("baseUrl") or d.get("base_url")
        u = u or d.get("user")
        p = p or d.get("password") or d.get("pass")
    if not (b and u and p):
        raise SystemExit("credentials missing: set JIRA_BASE_URL/JIRA_USER/JIRA_PASS or pass --creds FILE")
    return b.rstrip("/"), u, p

def jira_get(creds):
    """Return get(path)->(status, json|None). Secrets never appear in output."""
    base, user, pw = creds
    auth = "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()
    def get(path):
        req = urllib.request.Request(base + path, headers={"Authorization": auth, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, None
        except Exception as e:  # network: report class only, no URL/headers
            return 0, {"error": type(e).__name__}
    get.user = user
    return get

def load_filed(pattern):
    """Normalise every known filed-*.json shape into a flat list of row dicts.
    Shapes seen 2026-10-15: {rows:[..]} · [..] · {NOTE:{..}} (note id as key)."""
    rows = []
    for f in sorted(glob.glob(pattern)):
        d = json.load(open(f, encoding="utf-8"))
        if isinstance(d, dict) and isinstance(d.get("rows"), list): items = d["rows"]
        elif isinstance(d, list): items = d
        elif isinstance(d, dict): items = [dict(v, note=v.get("note", k)) if isinstance(v, dict) else {"note": k, "key": v} for k, v in d.items()]
        else: items = []
        for r in items:
            if isinstance(r, dict) and r.get("note") is not None:
                r = dict(r); r["_src"] = os.path.basename(f)
                act = str(r.get("action", "")).lower()
                r["action"] = {"created": "filed"}.get(act, act)
                rows.append(r)
    return rows

def rows_of(d, wrappers=("notes", "rows", "tickets")):
    """Any tracker shape -> list of dicts. Shapes: [..] | {notes|rows|tickets: [..] or {ID:{..}}} | {ID:{..}}."""
    if isinstance(d, dict):
        for w in wrappers:
            if w in d:
                return rows_of(d[w], ())
        d = [dict(v, note=v.get("note") or v.get("id") or k) for k, v in d.items() if isinstance(v, dict)]
    return [x for x in d or [] if isinstance(x, dict)]

def load_results(path):
    """-> ({note: row}, blockers|None). Normalises dict-notes, list and {rows}/{tickets} shapes; row id = note|id."""
    d = json.load(open(path, encoding="utf-8"))
    notes = {}
    for x in rows_of(d):
        k = x.get("note") or x.get("id")
        if k is not None:
            notes[str(k)] = x
    return notes, (d.get("blockers") if isinstance(d, dict) else None)
