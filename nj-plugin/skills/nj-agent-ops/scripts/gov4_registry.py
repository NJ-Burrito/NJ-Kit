#!/usr/bin/env python3
"""NJ Governance v4: machine registry and shared state (stdlib only).

Library for gov4_hook.py and gov4.py (WP5); also a small CLI:
  gov4_registry.py live status|list|reconcile|acquire --job --ttl-min N [--name X]|heartbeat [id|--id id]|release [id|--id id]
  gov4_registry.py mode [off|audit|enforce] | wave [5|10|20] | soft [on|off] | pause [clear]
  gov4_registry.py selftest

State root: $NJ_HOME, else ~/.claude/nj (never created implicitly: if the default directory does not
exist every write is skipped, so nothing lands in ~/.claude before the installer made it).
Files: live.json (entries + reservations), leads.json, tickets.json, unlock.json, mode, wave,
soft-enforce.flag, pause.flag, decisions.jsonl, events.jsonl, ALERT-<kind>.flag, *.lock.

The registry is ADVISORY (spec section 3 item 2): the platform cap CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS
is the 20-enforcer. A lock timeout allows the call and raises ALERT-registry.flag.

Ticket contract (used by gov4_hook.py `ticket` and by gov4.py write subcommands):
  mint_ticket(args)            args = the argv AFTER the gov4.py script path, exactly as the shell split it
  consume_ticket(env_value, args)  env_value = $NJ_TICKET (comma separated nonces); single use; True/False
  argv_sha(args) = sha256("\\x1f".join(args))
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
GOV = "nj-governance-v4"
_ROLES_CACHE = {}


# ---------------------------------------------------------------- paths ---

def home():
    return os.environ.get("NJ_HOME") or os.path.join(os.path.expanduser("~"), ".claude", "nj")


def home_ok():
    """True when state may be written: an explicit NJ_HOME, or the default directory already exists."""
    return bool(os.environ.get("NJ_HOME")) or os.path.isdir(home())


def p(name):
    return os.path.join(home(), name)


def now():
    return float(os.environ.get("NJ_NOW") or time.time())


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write_json(path, obj):
    """Atomic write (temp + replace); returns False when state may not be written."""
    if not home_ok():
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.{token_hex(3)}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    for i in range(20):
        try:
            os.replace(tmp, path)
            return True
        except PermissionError:
            time.sleep(0.01 * (i + 1))
    try:
        os.remove(tmp)
    except OSError:
        pass
    return False


def append_jsonl(name, rec):
    if not home_ok():
        return False
    try:
        os.makedirs(home(), exist_ok=True)
        with open(p(name), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def log_decision(rec):
    rec = dict(rec)
    rec.setdefault("ts", round(now(), 3))
    return append_jsonl("decisions.jsonl", rec)


def log_event(rec):
    rec = dict(rec)
    rec.setdefault("ts", round(now(), 3))
    return append_jsonl("events.jsonl", rec)


def alert(kind, msg, project=None):
    """ALERT-<kind>.flag in the state root and, when a project is given, in <project>/work/governance/."""
    body = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n"
    done = []
    pdir = os.path.join(project, "work", "governance") if project and os.path.isabs(project) and os.path.isdir(project) else None
    for d in (home() if home_ok() else None, pdir):
        if not d:
            continue
        try:
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, f"ALERT-{kind}.flag"), "a", encoding="utf-8") as f:
                f.write(body)
            done.append(d)
        except OSError:
            pass
    log_event({"event": "alert", "kind": kind, "msg": msg[:300]})
    return done


# ---------------------------------------------------------------- roles ---

def roles_candidates():
    env = os.environ.get("NJ_ROLES_JSON")
    c = [env] if env else []
    c += [os.path.join(HERE, "roles.json"), os.path.join(HERE, "..", "templates", "roles.json"), p("roles.json")]
    return c


def token_hex(n):
    return os.urandom(n).hex()


def read_roles():
    for c in roles_candidates():
        if c and os.path.isfile(c):
            key = (c, os.path.getmtime(c))
            if key not in _ROLES_CACHE:
                _ROLES_CACHE.clear()
                _ROLES_CACHE[key] = read_json(c, {}) or {}
            return _ROLES_CACHE[key]
    return {}


def type_info(name):
    """Return (info dict, source) for a subagent type: 'type' | 'pattern' | 'builtin' | None."""
    r = read_roles()
    name = (name or "general-purpose")
    t = r.get("types", {})
    if name in t:
        return t[name], "type"
    import fnmatch
    for pat in r.get("patterns", []):
        if fnmatch.fnmatchcase(name, pat.get("match", "")):
            info = dict(pat)
            m = info.get("maps_to")
            if m and m in t:
                base = dict(t[m])
                base.update({k: v for k, v in info.items() if k not in ("enabled",)})
                base["enabled"] = t[m].get("enabled", True)
                info = base
            return info, "pattern"
    if name in r.get("builtin_allow", []):
        return {"role": "reviewer", "model": r.get("builtin_models", {}).get(name, "haiku"), "builtin": True,
                "writes": "none"}, "builtin"
    return None, None


def family(model):
    m = str(model or "").lower()
    for f in ("opus", "sonnet", "haiku", "fable"):
        if f in m:
            return f
    return "inherit" if m in ("inherit", "default") else (m or None)


# ----------------------------------------------------------------- mode ---

def untrusted_caller():
    """True for a process that belongs to a headless job (NJ_ROLE=job, set by claude_run). Its command line is model
    controlled, so the environment overrides below (NJ_MODE_OVERRIDE, NJ_TICKETS) are ignored for it (D27, SB-02/SB-03)."""
    return (os.environ.get("NJ_ROLE") or "").strip().lower() in ("job", "agent")


def get_mode(env_ok=True):
    """off|audit|enforce. NJ_MODE_OVERRIDE is a test and operator override for the hook process itself (the platform
    sets that environment, an agent cannot). A child process that a model-written command starts (gov4.py, the git
    hooks) must call get_mode(env_ok=False) or get_mode_for_cli(): the override is then ignored for jobs and agents."""
    m = (os.environ.get("NJ_MODE_OVERRIDE") or "").strip().lower() if env_ok else ""
    if m in ("off", "audit", "enforce"):
        return m
    try:
        with open(p("mode"), encoding="utf-8") as f:
            m = f.read().strip().lower()
        if m in ("off", "audit", "enforce"):
            return m
    except OSError:
        pass
    return "audit"


def get_mode_for_cli():
    """Mode as seen by gov4.py and other children of a model-written command: the env override counts only for a
    caller that is not a job or an agent (D27)."""
    return get_mode(env_ok=not untrusted_caller())


def set_mode(m):
    if m not in ("off", "audit", "enforce"):
        raise ValueError("mode must be off|audit|enforce")
    return _write_text("mode", m + "\n")


def get_wave():
    v = os.environ.get("NJ_WAVE_OVERRIDE")
    if not v:
        try:
            with open(p("wave"), encoding="utf-8") as f:
                v = f.read().strip()
        except OSError:
            v = None
    try:
        n = int(v)
        if n in (5, 10, 20):
            return n
    except (TypeError, ValueError):
        pass
    return int(read_roles().get("waves", {}).get("default", 10))


def set_wave(n):
    if int(n) not in (5, 10, 20):
        raise ValueError("wave must be 5|10|20")
    return _write_text("wave", f"{int(n)}\n")


def soft_active():
    """Soft denials (per-parent allowance, wave, Workflow) only deny once switched on."""
    if os.environ.get("NJ_SOFT") == "enforce":
        return True
    return os.path.exists(p("soft-enforce.flag"))


def set_soft(on):
    if on:
        return _write_text("soft-enforce.flag", f"{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    try:
        os.remove(p("soft-enforce.flag"))
    except OSError:
        pass
    return True


def _write_text(name, text):
    if not home_ok():
        return False
    os.makedirs(home(), exist_ok=True)
    tmp = p(name) + f".{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, p(name))
    return True


def pause_flag():
    return p("pause.flag")


def paused():
    return os.path.exists(pause_flag())


def set_pause(reason):
    if not home_ok():
        return False
    ok = _write_text("pause.flag", f"{time.strftime('%Y-%m-%d %H:%M:%S')} {reason}\n")
    log_event({"event": "pause", "reason": reason[:200]})
    return ok


def clear_pause():
    try:
        os.remove(pause_flag())
    except OSError:
        pass
    return True


# ----------------------------------------------------------------- lock ---

def _reclaim_s():
    try:
        return float(os.environ.get("NJ_LOCK_RECLAIM_S") or read_roles().get("limits", {}).get("registry_lock_reclaim_s", 10))
    except ValueError:
        return 10.0


def _lock_timeout():
    try:
        return float(os.environ.get("NJ_LOCK_TIMEOUT_S") or 3.0)
    except ValueError:
        return 3.0


def _lock_age(path):
    try:
        with open(path, encoding="utf-8") as f:
            parts = f.read().split()
        return now() - float(parts[1])
    except (OSError, ValueError, IndexError):
        try:
            return time.time() - os.path.getmtime(path)
        except OSError:
            return 0.0


class locked:
    """Create-exclusive lock holding 'pid timestamp'; reclaimed once older than the reclaim time.
    `with locked(name) as ok:` -> ok True when held, False on timeout (callers allow the call and raise
    ALERT-registry.flag). Plain class (not contextlib) to keep hook start-up small."""

    def __init__(self, name="live.lock", timeout=None):
        self.name, self.timeout, self.held, self.path = name, timeout, False, None

    def __enter__(self):
        if not home_ok():
            return False
        self.path = path = p(self.name)
        os.makedirs(home(), exist_ok=True)
        deadline = time.time() + (_lock_timeout() if self.timeout is None else self.timeout)
        delay = 0.002
        while True:
            try:
                fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, (f"{os.getpid()} {now()}" + chr(10)).encode())
                os.close(fd)
                self.held = True
                return True
            except FileExistsError:
                if _lock_age(path) > _reclaim_s():
                    try:
                        os.remove(path)
                    except OSError:
                        pass
                    log_event({"event": "lock-reclaimed", "lock": self.name})
                    continue
            except PermissionError:
                pass
            if time.time() >= deadline:
                return False
            time.sleep(delay)
            delay = min(delay * 1.5, 0.03)

    def __exit__(self, *exc):
        if self.held:
            for i in range(200):                    # Windows: a waiter probing the file blocks the delete for a moment
                try:
                    os.remove(self.path)
                    break
                except FileNotFoundError:
                    break
                except OSError:
                    time.sleep(0.002)
            self.held = False
        return False


# --------------------------------------------------------------- leads ---

def register_lead(session_id, cwd="", entrypoint="", source="", permission_mode=""):
    if not session_id:
        return False
    with locked("leads.lock") as ok:
        if not ok:
            return False
        d = read_json(p("leads.json"), {}) or {}
        s = d.setdefault("sessions", {})
        t = now()
        for k in [k for k, v in s.items() if t - float(v.get("ts", 0)) > 30 * 86400]:
            s.pop(k, None)
        s[session_id] = {"ts": t, "cwd": cwd, "entrypoint": entrypoint, "source": source}
        if permission_mode:
            s[session_id]["permission_mode"] = str(permission_mode)      # CD-5: gov4.py doctor reads the real mode from here
        return write_json(p("leads.json"), d)


def refresh_lead_mode(session_id, permission_mode):
    """Update the stored permission_mode of a registered Lead when a later payload reports a different one (no write otherwise)."""
    if not session_id or not permission_mode:
        return False
    d = read_json(p("leads.json"), {}) or {}
    cur = d.get("sessions", {}).get(session_id)
    if cur is None or cur.get("permission_mode") == permission_mode:
        return False
    with locked("leads.lock") as ok:
        if not ok:
            return False
        d = read_json(p("leads.json"), {}) or {}
        cur = d.get("sessions", {}).get(session_id)
        if cur is None:
            return False
        cur["permission_mode"] = str(permission_mode)
        cur["ts"] = now()
        return write_json(p("leads.json"), d)


def is_lead(session_id):
    if not session_id:
        return False
    d = read_json(p("leads.json"), {}) or {}
    return session_id in d.get("sessions", {})


# -------------------------------------------------------------- unlock ---

def unlock_valid():
    d = read_json(p("unlock.json"), None)
    if not isinstance(d, dict):
        return False
    exp = d.get("expires_ts", d.get("expires"))
    if isinstance(exp, str):
        try:
            exp = time.mktime(time.strptime(exp[:19], "%Y-%m-%dT%H:%M:%S"))
        except ValueError:
            return False
    try:
        return float(exp) > now()
    except (TypeError, ValueError):
        return False


# ------------------------------------------------------------- tickets ---

def argv_sha(args):
    import hashlib
    return hashlib.sha256("\x1f".join(args).encode("utf-8")).hexdigest()


def mint_ticket(args, ttl=None):
    ttl = ttl or int(read_roles().get("limits", {}).get("ticket_ttl_s", 60))
    nonce = token_hex(16)
    with locked("tickets.lock") as ok:
        if not ok:
            return None
        d = read_json(p("tickets.json"), {}) or {}
        t = now()
        lst = [x for x in d.get("tickets", []) if x.get("exp", 0) > t and not x.get("used")]
        lst.append({"nonce": nonce, "sha": argv_sha(args), "exp": t + ttl, "used": False})
        d["tickets"] = lst
        if not write_json(p("tickets.json"), d):
            return None
    return nonce


def ticket_mode():
    """'hook' (default: PreToolUse mints tickets through updatedInput, proven by S2 headless 3/3) or 'habit'
    (the fallback if the interactive S2 shows updatedInput does not work: no rewrite, gov4.py skips the ticket
    check; the git deny rules and git hooks stay). The file `tickets-mode` (written by the Lead) sets it.
    SB-03: the environment variable NJ_TICKETS counts only outside enforce, and for a job or agent neither the
    variable nor the file counts: one env var must never switch the ticket check off."""
    if untrusted_caller():
        return "hook"
    m = ""
    if get_mode() != "enforce":
        m = (os.environ.get("NJ_TICKETS") or "").strip().lower()
    if not m:
        try:
            with open(p("tickets-mode"), encoding="utf-8") as f:
                m = f.read().strip().lower()
        except OSError:
            m = ""
    return "habit" if m == "habit" else "hook"


# Which gov4.py invocations need a Lead ticket. MIRROR of gov4.py needs_ticket (test_sdlc checks the two cannot drift).
WRITE_SUBS = {"checkpoint", "merge", "push", "sweep", "mode", "wave", "unlock", "install-repo", "install-bin", "smoke-attest",
              "install-settings"}
LIVE_SLOT_SUBS = ("acquire", "release", "heartbeat")      # registry slots: job wrappers only, never a model (SB-09)


def needs_ticket(argv):
    argv = [str(a) for a in argv]
    if not argv:
        return False
    sub, rest = argv[0], argv[1:]
    if sub in WRITE_SUBS:
        return not (sub in ("mode", "wave") and not [a for a in rest if not a.startswith("-")])
    if sub == "snapshot":
        return bool(rest) and rest[0] in ("begin", "apply", "commit")
    if sub == "rollback":
        return "--selftest" not in rest
    if sub == "live":
        return any(a in rest for a in ("--pause", "--resume"))
    if sub == "enforce-ready":
        return "--record" in rest
    return False


def hook_write(argv, script="gov4.py"):
    """True when a MODEL-written command running this gov4 script is a write: ticket-needing subcommands plus, for
    the hook only, live acquire|release|heartbeat (a model never holds a job slot) and the registry CLI writes."""
    argv = [str(a) for a in argv]
    pos = [a for a in argv if not a.startswith("-")]
    if script == "gov4_registry.py":
        if not pos:
            return False
        c = pos[0]
        if c in ("mode", "wave", "soft"):
            return len(pos) > 1
        if c == "pause":
            return len(pos) > 1 and pos[1] == "clear"
        if c == "live":
            return len(pos) > 1 and pos[1] in LIVE_SLOT_SUBS
        return False
    if script == "gov4_snapshot.py":
        return bool(pos) and pos[0] in ("begin", "apply", "commit")
    if needs_ticket(argv):
        return True
    if pos and pos[0] == "snapshot" and (len(pos) < 2 or pos[1] not in ("diff", "status")):
        return True                       # hook only: a bare or unknown snapshot word fails closed
    return bool(pos) and pos[0] == "live" and len(pos) > 1 and pos[1] in LIVE_SLOT_SUBS


def consume_ticket(env_value, args):
    """Single use: True once for a nonce whose argv hash matches and that has not expired.
    In ticket mode 'habit' there is nothing to consume and the answer is True (see ticket_mode)."""
    if ticket_mode() == "habit":
        return True
    nonces = [x.strip() for x in str(env_value or "").split(",") if x.strip()]
    if not nonces:
        return False
    sha = argv_sha(args)
    with locked("tickets.lock") as ok:
        if not ok:
            return False
        d = read_json(p("tickets.json"), {}) or {}
        t = now()
        hit = False
        for x in d.get("tickets", []):
            if x["nonce"] in nonces and not x.get("used") and x.get("exp", 0) > t and x.get("sha") == sha:
                x["used"] = True
                hit = True
                break
        if hit:
            write_json(p("tickets.json"), d)
        return hit


# ------------------------------------------------------------ registry ---

def _load():
    d = read_json(p("live.json"), None)
    if not isinstance(d, dict):
        d = {}
    d.setdefault("entries", [])
    d.setdefault("reservations", [])
    return d


def _stale_s():
    return float(read_roles().get("limits", {}).get("registry_stale_min", 15)) * 60


def agent_transcript(session_transcript, session_id, agent_id):
    if not (session_transcript and session_id and agent_id):
        return ""
    return os.path.join(os.path.dirname(session_transcript), session_id, "subagents", f"agent-{agent_id}.jsonl")


def _reconcile(d, t):
    """In-place: drop expired reservations/jobs, mark/unmark suspect entries. Returns a stats dict."""
    st = {"reservations_dropped": 0, "jobs_expired": 0, "suspect": 0, "recovered": 0}
    keep = []
    for r in d["reservations"]:
        if r.get("expires", 0) > t:
            keep.append(r)
        else:
            st["reservations_dropped"] += 1
    d["reservations"] = keep
    out = []
    for e in d["entries"]:
        if e.get("kind") == "job":
            if e.get("expires", 0) <= t:
                st["jobs_expired"] += 1
                continue
            e["suspect"] = False
        else:
            tp = e.get("transcript")
            last = e.get("last_seen", e.get("started", t))
            if tp:
                try:
                    last = max(last, os.path.getmtime(tp))
                except OSError:
                    pass
            e["last_seen"] = last
            was = e.get("suspect", False)
            e["suspect"] = (t - last) > _stale_s()
            st["suspect"] += 1 if e["suspect"] else 0
            if was and not e["suspect"]:
                st["recovered"] += 1
        out.append(e)
    d["entries"] = out
    return st


def _active(d):
    return [e for e in d["entries"] if not e.get("suspect")]


def counts(d=None):
    d = d or _load()
    act = _active(d)
    return {"live": len(act), "agents": sum(1 for e in act if e.get("kind") != "job"),
            "jobs": sum(1 for e in act if e.get("kind") == "job"), "pending": len(d["reservations"]),
            "suspect": sum(1 for e in d["entries"] if e.get("suspect")), "wave": get_wave()}


def live_line():
    """`live N/cap` as shown on the board (cap = operating wave)."""
    c = counts(_load())
    return f"live {c['live']}/{c['wave']}" + (f" (+{c['pending']} pending)" if c["pending"] else "") + \
        (f" ({c['suspect']} suspect)" if c["suspect"] else "")


def snapshot():
    """Read-only view (no lock): counts plus the raw entries."""
    d = _load()
    c = counts(d)
    c["entries"] = d["entries"]
    c["reservations"] = d["reservations"]
    return c


def mutate(fn, project=None):
    """Run fn(d, t) under the lock on the loaded registry, after an automatic reconcile; save.
    Returns (True, result) or (False, None) when the lock timed out (an ALERT-registry.flag is raised)."""
    if not home_ok():
        return False, None
    with locked("live.lock") as ok:
        if not ok:
            alert("registry", "live.json lock timeout: call allowed without registry update", project)
            return False, None
        d = _load()
        t = now()
        _reconcile(d, t)
        res = fn(d, t)
        write_json(p("live.json"), d)
        return True, res


def reconcile(project=None):
    return mutate(lambda d, t: counts(d), project)[1]


def reserve(caller, subagent_type, role, tool_use_id, session_id, project="", main_writer=False, ttl=90, owned=None):
    """owned = the OWNED_PATHS patterns of a main-checkout writer (D23); the entry keeps them so the write hook can
    confine the agent and a second main-checkout writer is refused only when its paths overlap."""
    def fn(d, t):
        rid = token_hex(4)
        d["reservations"].append({"rid": rid, "caller": caller or "lead", "subagent_type": subagent_type or "general-purpose",
                                  "role": role, "tool_use_id": tool_use_id, "session": session_id, "project": project,
                                  "main_writer": bool(main_writer), "owned": list(owned or []), "ts": t, "expires": t + ttl})
        return rid
    return mutate(fn, project)[1]


def convert(agent_id, agent_type, session_id, session_transcript="", project=""):
    """SubagentStart: FIFO-convert the oldest matching reservation of this session into a live entry."""
    def fn(d, t):
        match = None
        for r in sorted(d["reservations"], key=lambda r: r["ts"]):
            if r.get("session") == session_id and (r.get("subagent_type") == agent_type or not agent_type):
                match = r
                break
        if match:
            d["reservations"].remove(match)
        info, _ = type_info(agent_type)
        e = {"id": agent_id, "kind": "agent", "agent_type": agent_type, "role": (info or {}).get("role") or (match or {}).get("role"),
             "parent": match["caller"] if match else None, "session": session_id,
             "project": (match or {}).get("project") or project, "started": t, "last_seen": t,
             "transcript": agent_transcript(session_transcript, session_id, agent_id),
             "main_writer": bool((match or {}).get("main_writer")), "owned": list((match or {}).get("owned") or []),
             "matched": bool(match)}
        d["entries"] = [x for x in d["entries"] if x.get("id") != agent_id] + [e]
        return e
    return mutate(fn, project)[1]


def release(agent_id, project=None):
    def fn(d, t):
        n = len(d["entries"])
        d["entries"] = [x for x in d["entries"] if x.get("id") != agent_id]
        return n - len(d["entries"])
    return mutate(fn, project)[1]


def agent_owned(agent_id):
    """OWNED_PATHS patterns recorded for a live agent (main-checkout writers); [] when none or unknown."""
    for e in _load()["entries"]:
        if e.get("id") == agent_id:
            return list(e.get("owned") or [])
    return []


def children_of(agent_id):
    d = _load()
    return [e for e in _active(d) if e.get("parent") == agent_id] + \
           [r for r in d["reservations"] if r.get("caller") == agent_id]


def acquire_job(name, ttl_min, project=None):
    """Return (ok, info). ok False with reason 'full' when the operating cap is reached."""
    def fn(d, t):
        c = counts(d)
        if c["live"] + c["pending"] >= c["wave"]:
            return {"ok": False, "reason": "full", "live": c["live"], "pending": c["pending"], "wave": c["wave"]}
        jid = "job-" + token_hex(4)
        d["entries"].append({"id": jid, "kind": "job", "name": name or "job", "role": "job", "started": t,
                             "last_seen": t, "ttl_s": ttl_min * 60, "expires": t + ttl_min * 60, "suspect": False})
        return {"ok": True, "id": jid, "ttl_min": ttl_min}
    ok, res = mutate(fn, project)
    if not ok:                              # registry unusable: a job must not be stopped by it
        return True, {"ok": True, "id": None, "note": "registry unavailable: allowed without a slot"}
    return res["ok"], res


def heartbeat(jid, project=None):
    def fn(d, t):
        for e in d["entries"]:
            if e.get("id") == jid:
                e["last_seen"] = t
                if e.get("kind") == "job":
                    e["expires"] = t + e.get("ttl_s", 900)
                return True
        return False
    ok, res = mutate(fn, project)
    return bool(res) if ok else True


# ----------------------------------------------------------------- CLI ---

def _arg_id(rest):
    if "--id" in rest:
        i = rest.index("--id")
        return rest[i + 1] if i + 1 < len(rest) else None
    return next((a for a in rest if not a.startswith("-")), None)


def _owns_slot(jid):
    """A job that knows its own slot (NJ_JOB_ID, set by claude_run) may touch only that slot (SB-09)."""
    mine = os.environ.get("NJ_JOB_ID")
    return not mine or mine == jid


def live_main(argv, out=print):
    """`gov4.py live ...` implementation for WP5. Returns the exit code (75 = operating cap reached)."""
    sub = argv[0] if argv else "status"
    rest = argv[1:]
    if sub in ("status", "list"):
        s = snapshot()
        if "--json" in rest or sub == "list":
            out(json.dumps(s, indent=1))
        else:
            out(live_line())
        return 0
    if sub == "reconcile":
        out(json.dumps(reconcile() or {}))
        return 0
    if sub == "acquire":
        if "--job" not in rest:
            out("acquire: only --job slots are handed out by the CLI")
            return 2
        ttl = 15
        if "--ttl-min" in rest:
            try:
                ttl = int(float(rest[rest.index("--ttl-min") + 1]))
            except (ValueError, IndexError):
                out("acquire: --ttl-min needs a number")
                return 2
        name = rest[rest.index("--name") + 1] if "--name" in rest and rest.index("--name") + 1 < len(rest) else "job"
        cap = int(read_roles().get("limits", {}).get("job_ttl_max_min", 240))
        ttl = min(max(1, ttl), cap)                  # SB-09: a slot can never be held for days
        ok, info = acquire_job(name, ttl)
        out(json.dumps(info))
        return 0 if ok else 75
    if sub == "heartbeat":
        jid = _arg_id(rest)
        if not jid:
            out("heartbeat: id missing")
            return 2
        if not _owns_slot(jid):
            out("heartbeat: that slot belongs to another job")
            return 2
        heartbeat(jid)
        return 0
    if sub == "release":
        jid = _arg_id(rest)
        if not jid:
            out("release: id missing")
            return 2
        if not _owns_slot(jid):
            out("release: that slot belongs to another job")
            return 2
        release(jid)
        return 0
    out(f"unknown live subcommand: {sub}")
    return 2


def selftest():
    import tempfile
    import threading
    import subprocess
    failures = []

    def check(name, cond):
        if not cond:
            failures.append(name)
            print("FAIL", name)

    tmp = tempfile.mkdtemp(prefix="gov4reg-")
    old = {k: os.environ.get(k) for k in ("NJ_HOME", "NJ_LOCK_RECLAIM_S", "NJ_LOCK_TIMEOUT_S", "NJ_NOW", "NJ_MODE_OVERRIDE", "NJ_WAVE_OVERRIDE")}
    os.environ["NJ_HOME"] = tmp
    for k in ("NJ_NOW", "NJ_MODE_OVERRIDE", "NJ_WAVE_OVERRIDE"):
        os.environ.pop(k, None)
    try:
        check("default mode is audit", get_mode() == "audit")
        os.environ["NJ_MODE_OVERRIDE"] = "enforce"
        check("override wins", get_mode() == "enforce")
        os.environ.pop("NJ_MODE_OVERRIDE")
        set_mode("enforce")
        check("mode file", get_mode() == "enforce")
        set_mode("audit")
        check("wave default 10", get_wave() == 10)
        set_wave(5)
        check("wave file", get_wave() == 5)
        set_wave(10)

        # reserve -> FIFO convert -> release by agent_id
        reserve("lead", "nj-agent", "agent", "tu1", "S1", "proj")
        reserve("lead", "nj-agent", "agent", "tu2", "S1", "proj")
        reserve("A1", "nj-helper-reader", "helper", "tu3", "S1", "proj")
        c = counts()
        check("3 pending", c["pending"] == 3 and c["live"] == 0)
        e1 = convert("A1", "nj-agent", "S1")
        e2 = convert("H1", "nj-helper-reader", "S1")
        check("FIFO parent lead", e1 and e1["parent"] == "lead")
        check("helper parent A1", e2 and e2["parent"] == "A1")
        check("1 pending left", counts()["pending"] == 1 and counts()["live"] == 2)
        check("children_of A1", [x["id"] for x in children_of("A1")] == ["H1"])
        release("H1")
        check("release by agent_id", counts()["live"] == 1 and not children_of("A1"))

        # suspect: transcript silent for 15 minutes is excluded from the count
        base = time.time()
        os.environ["NJ_NOW"] = str(base + 16 * 60)
        reconcile()
        c = counts()
        check("suspect excluded", c["live"] == 0 and c["suspect"] == 1)
        os.environ.pop("NJ_NOW")
        d = _load()
        d["entries"] = []
        d["reservations"] = []
        write_json(p("live.json"), d)

        # reservation TTL 90 s
        reserve("lead", "nj-agent", "agent", "tu9", "S1", "proj")
        os.environ["NJ_NOW"] = str(base + 120)
        reconcile()
        check("reservation expires", counts()["pending"] == 0)
        os.environ.pop("NJ_NOW")

        # jobs: acquire / heartbeat / release / full -> 75
        out = []
        check("acquire ok", live_main(["acquire", "--job", "--ttl-min", "5", "--name", "x"], out.append) == 0)
        jid = json.loads(out[-1])["id"]
        check("heartbeat ok", live_main(["heartbeat", "--id", jid], out.append) == 0)
        set_wave(5)
        for i in range(4):
            acquire_job(f"j{i}", 5)
        check("full -> 75", live_main(["acquire", "--job", "--ttl-min", "5"], out.append) == 75)
        check("full says reason", json.loads(out[-1]).get("reason") == "full")
        check("release ok", live_main(["release", jid], out.append) == 0)
        check("acquire after release", live_main(["acquire", "--job", "--ttl-min", "5"], out.append) == 0)
        set_wave(10)
        check("live line", live_line().startswith("live "))

        # lock: stale lock is reclaimed; timeout allows with ALERT-registry.flag
        os.environ["NJ_LOCK_RECLAIM_S"] = "1"
        with open(p("live.lock"), "w") as f:
            f.write(f"99999 {time.time() - 30}\n")
        ok, _ = mutate(lambda d, t: 1)
        check("stale lock reclaimed", ok)
        os.environ["NJ_LOCK_RECLAIM_S"] = "600"
        os.environ["NJ_LOCK_TIMEOUT_S"] = "0.2"
        with open(p("live.lock"), "w") as f:
            f.write(f"{os.getpid()} {time.time()}\n")
        ok, _ = mutate(lambda d, t: 1)
        check("lock timeout does not mutate", not ok)
        check("ALERT-registry.flag raised", os.path.exists(p("ALERT-registry.flag")))
        os.remove(p("live.lock"))
        os.environ["NJ_LOCK_RECLAIM_S"] = "1"
        os.environ["NJ_LOCK_TIMEOUT_S"] = "5"

        # killed holder: a real process takes the lock, is killed, the lock is reclaimed
        code = ("import os,sys,time;sys.path.insert(0,%r);import gov4_registry as g;"
                "cm=g.locked('live.lock');cm.__enter__();print('HELD',flush=True);time.sleep(60)" % HERE)
        pr = subprocess.Popen([sys.executable, "-X", "utf8", "-c", code], stdout=subprocess.PIPE, text=True,
                              env=dict(os.environ, NJ_HOME=tmp))
        check("holder took the lock", pr.stdout.readline().strip() == "HELD")
        pr.kill()
        pr.wait()
        t0 = time.time()
        ok, _ = mutate(lambda d, t: 1)
        check("killed holder lock reclaimed", ok and time.time() - t0 < 4)
        os.environ["NJ_LOCK_RECLAIM_S"] = "10"

        # 25 racing threads never corrupt live.json
        d = _load()
        d["entries"] = []
        d["reservations"] = []
        write_json(p("live.json"), d)
        errs = []

        def worker(i):
            try:
                for k in range(3):
                    reserve("lead", "nj-agent", "agent", f"t{i}-{k}", "S1", "proj")
                    convert(f"AG{i}-{k}", "nj-agent", "S1")
            except Exception as ex:  # noqa: BLE001
                errs.append(repr(ex))
        os.environ["NJ_LOCK_TIMEOUT_S"] = "30"
        ths = [threading.Thread(target=worker, args=(i,)) for i in range(25)]
        [t.start() for t in ths]
        [t.join() for t in ths]
        d = read_json(p("live.json"), None)
        check("race: json intact", isinstance(d, dict) and not errs)
        check("race: 75 entries", d and len(d["entries"]) == 75 and not d["reservations"])
        os.environ["NJ_LOCK_TIMEOUT_S"] = "3"

        # tickets: single use, bound to argv, expiry
        n = mint_ticket(["merge", "feature-a"])
        check("ticket minted", bool(n))
        check("ticket wrong argv refused", not consume_ticket(n, ["merge", "other"]))
        check("ticket consumed once", consume_ticket(n, ["merge", "feature-a"]))
        check("ticket not twice", not consume_ticket(n, ["merge", "feature-a"]))
        n2 = mint_ticket(["push"])
        os.environ["NJ_NOW"] = str(time.time() + 120)
        check("ticket expires in 60 s", not consume_ticket(n2, ["push"]))
        os.environ.pop("NJ_NOW")
        n3 = mint_ticket(["a"])
        n4 = mint_ticket(["b"])
        check("comma list picks the matching nonce", consume_ticket(f"{n3},{n4}", ["b"]))

        # leads, unlock, pause
        register_lead("SESS", "cwd", "claude-vscode", "startup")
        check("lead registered", is_lead("SESS") and not is_lead("OTHER"))
        check("no unlock", not unlock_valid())
        write_json(p("unlock.json"), {"expires_ts": time.time() + 3600})
        check("unlock valid", unlock_valid())
        write_json(p("unlock.json"), {"expires_ts": time.time() - 1})
        check("unlock expired", not unlock_valid())
        check("not paused", not paused())
        set_pause("selftest 429")
        check("pause set", paused())
        clear_pause()
        check("pause cleared", not paused())

        # nothing is written when the default home does not exist
        os.environ.pop("NJ_HOME")
        fake = os.path.join(tmp, "nope")
        saved = os.path.expanduser
        os.path.expanduser = lambda s: fake if s == "~" else saved(s)
        try:
            check("no implicit home", not home_ok() and not os.path.exists(os.path.join(fake, ".claude")))
            check("write skipped", write_json(p("x.json"), {}) is False)
        finally:
            os.path.expanduser = saved
        os.environ["NJ_HOME"] = tmp

        # roles lookup
        i, src = type_info("nj-agent")
        check("type nj-agent", i and i["role"] == "agent" and src == "type")
        i, src = type_info("researcher-kb")
        check("pattern researcher writes OWNED_PATHS", i and i.get("writes") == "OWNED_PATHS" and "Write" in i.get("tools", []))
        i, src = type_info("Explore")
        check("builtin Explore", src == "builtin" and i["model"] == "haiku")
        check("unknown type", type_info("zzz-unknown")[0] is None)
        check("crew-* enabled via nj-helper-writer (D24)", type_info("crew-writer")[0].get("enabled") is True)
        check("family", family("claude-opus-5-5[1m]") == "opus" and family("sonnet") == "sonnet")
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    print("registry selftest:", "FAIL " + ", ".join(failures) if failures else "ok")
    return 1 if failures else 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    c = argv[0]
    if c == "selftest":
        return selftest()
    if c == "live":
        return live_main(argv[1:])
    if c == "mode":
        if len(argv) > 1:
            set_mode(argv[1])
        print(get_mode())
        return 0
    if c == "wave":
        if len(argv) > 1:
            set_wave(argv[1])
        print(get_wave())
        return 0
    if c == "soft":
        if len(argv) > 1:
            set_soft(argv[1] == "on")
        print("on" if soft_active() else "off")
        return 0
    if c == "pause":
        if len(argv) > 1 and argv[1] == "clear":
            clear_pause()
        print("paused" if paused() else "clear")
        return 0
    print("unknown command", c, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
