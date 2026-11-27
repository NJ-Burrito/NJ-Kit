#!/usr/bin/env python3
"""NJ Governance v4: the Lead's command line (spec sections 2-4, 9, 11, 13, 14). Stdlib only.

Imports gov4_registry.py and gov4_snapshot.py (and runs relay.py) by explicit path from this folder (or $NJ_HOME/bin/CURRENT).

READ-ONLY (no ticket):  status | queue | review <name> [--unstaged] | preflight <name> | live ... | doctor ... | selftest
                        | enforce-ready | snapshot diff | version
TICKETS (D27): checked only in ENFORCE. In audit gov4.py logs a would-refuse and proceeds; in off nothing is checked; a human at a terminal
  never needs one. NJ_MODE_OVERRIDE, NJ_TICKETS, NJ_HOME, CLAUDE_HOME and NJ_ROLES_JSON are ignored unless the caller is a human at a
  terminal or a marked scratch run (NJ_GOV4_SELFTEST + <NJ_HOME>/selftest.marker under the temp dir), and never for NJ_ROLE=job. There is
  no 'habit' bypass: the tickets-mode file and NJ_TICKETS=habit do nothing here.
WRITE (a valid single-use ticket from the PreToolUse hook in enforce, or a human at a terminal, or mode audit|off):
  checkpoint [project] [-m msg]         one local commit of the whole tree on the default branch (never pushes)
  merge <name> [--project P] [--reviewed-by X] [--no-gates "<reason>"] [--full-gates]
                                        run it detached (a background command): head-sha re-verification, _integration
                                        worktree (+ .worktreeinclude files), --no-ff merge with trailers, post_merge gates,
                                        ff-only into main; refuses dirty overlap, live-paths changes, no gates; DONE-<name>.flag
  push [project] [--dry-run]            git push --atomic origin <main>, never forced, after a clean sweep
  sweep [project] [--tag T] [--keep X] [--allow-queued]   relay.py sweep + worktrees, branches, registry, pause flag, processes
  live acquire --job --ttl-min N [--name X] | heartbeat <id> | release <id> | --reconcile | --pause [why] | --resume
  wave 5|10|20        20 needs relay.py verify clean at a peak of 10 or more with 0 rate-limit incidents (decision D4)
  mode off|audit|enforce [--settings-file F]   enforce also writes the git-write and `gh pr` deny rules and onFailure: block on the Agent hook
                                        into settings.json; audit and off remove them again (D20, D26)
  enforce-ready [--record item] | unlock [--minutes N] [--reason R] [--revoke] | unlock --help
  install-repo [project] (bakes the state path into the git hooks) | install-bin
  install-settings [--settings-file F] [--fragment F] [--python P] [--nj-home D] [--mode audit|enforce] [--against PRE] [--dry-run]
                                        deterministic deep merge of the hooks fragment + env, effort medium, baseRef, model/secret denies,
                                        allow and ask into settings.json; keeps every pre-v4 key; one sdlc.py hook; atomic write
  snapshot begin|diff|apply|commit | smoke-attest | rollback [--selftest|--create-snapshot]
READ-ONLY extras: doctor --settings [--settings-file F] [--mode audit|enforce] [--against settings.json.pre-v4]

Exit codes: 0 ok, 1 refused or failed, 2 usage, 3 ticket refused, 75 live registry full.
"""
import fnmatch
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
GOV = "nj-governance-v4"
NT = os.name == "nt"
TRAILER_CO = "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
GATE_TIMEOUT_S = 900


# --------------------------------------------------------------- imports ---

def _candidates(name):
    c = [os.path.join(HERE, name + ".py")]
    nj = os.environ.get("NJ_HOME") or os.path.join(os.path.expanduser("~"), ".claude", "nj")
    try:
        cur = open(os.path.join(nj, "bin", "CURRENT"), encoding="utf-8").read().strip()
        c.append(os.path.join(cur if os.path.isabs(cur) else os.path.join(nj, "bin", cur), name + ".py"))
    except OSError:
        pass
    return c


def load_module(name):
    if name in sys.modules:
        return sys.modules[name]
    for path in _candidates(name):
        if os.path.isfile(path):
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            return mod
    raise ImportError(f"{name}.py not found beside gov4.py or in NJ_HOME/bin/CURRENT")


reg = load_module("gov4_registry")


def snap():
    return load_module("gov4_snapshot")


def out(*a):
    print(*a, flush=True)


def norm(p):
    return str(p).replace("\\", "/")


def now_ts():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write_json(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def write_text(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def glob_match(pat, path):
    return snap().glob_match(pat, path)


def in_union(pats, path):
    return any(glob_match(p, path) for p in pats)


def run(cmd, cwd=None, env=None, timeout=600, input=None):
    try:
        r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, input=input)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout after {timeout}s"
    except OSError as e:
        return 127, "", f"{type(e).__name__}: {e}"


def find_bash():
    e = os.environ.get("NJ_BASH")
    if e and os.path.isfile(e):
        return e
    rc, o, _ = run(["git", "--exec-path"], timeout=30)
    if rc == 0 and o.strip():
        base = os.path.abspath(os.path.join(o.strip(), "..", "..", ".."))
        for c in (os.path.join(base, "bin", "bash.exe"), os.path.join(base, "usr", "bin", "bash.exe"),
                  os.path.join(base, "bin", "bash"), os.path.join(base, "usr", "bin", "bash")):
            if os.path.isfile(c):
                return c
    return shutil.which("bash") or shutil.which("sh") or "bash"


def safe_delete(path):
    """Recycle bin through the safe-delete skill; never rm -rf."""
    script = os.path.join(os.path.expanduser("~"), ".claude", "skills", "safe-delete", "scripts", "trash.py")
    if not os.path.isfile(script):
        return False
    rc, _, _ = run([sys.executable, "-X", "utf8", script, path], timeout=120)
    return rc == 0 and not os.path.exists(path)


# ------------------------------------------------------------------ git ---

_IDENT = {}


def git_env(root):
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    if root not in _IDENT:
        rc, o, _ = run(["git", "-C", root, "config", "user.name"], timeout=30)
        _IDENT[root] = bool(o.strip())
    if not _IDENT[root]:
        for k, v in (("GIT_AUTHOR_NAME", "nj-gov4"), ("GIT_AUTHOR_EMAIL", "gov4@localhost"),
                     ("GIT_COMMITTER_NAME", "nj-gov4"), ("GIT_COMMITTER_EMAIL", "gov4@localhost")):
            env.setdefault(k, v)
    return env


def git(root, *args, input=None, timeout=600):
    return run(["git", "-C", root] + list(args), env=git_env(root), timeout=timeout, input=input)


def repo_root(path):
    rc, o, _ = git(path, "rev-parse", "--show-toplevel", timeout=30)
    return norm(o.strip()) if rc == 0 and o.strip() else None


def current_branch(root):
    rc, o, _ = git(root, "symbolic-ref", "--short", "-q", "HEAD", timeout=30)
    return o.strip() if rc == 0 else ""


def main_branch(root):
    cur = current_branch(root)
    if cur in ("main", "master"):
        return cur
    for b in ("main", "master"):
        if git(root, "rev-parse", "--verify", "-q", f"refs/heads/{b}", timeout=30)[0] == 0:
            return b
    return None


def rev(root, ref):
    rc, o, _ = git(root, "rev-parse", "--verify", "-q", ref + "^{commit}", timeout=30)
    return o.strip() if rc == 0 else None


class GitToken:
    """The git-hook token exists only inside the gov4 process: a file in $NJ_HOME/git-tokens/<nonce> holding an
    expiry epoch, and NJ_GIT_TOKEN=<nonce> in this process's environment (inherited by its git children)."""

    def __enter__(self):
        self.tok = reg.token_hex(16)
        self.path = None
        if reg.home_ok():
            d = os.path.join(reg.home(), "git-tokens")
            try:
                os.makedirs(d, exist_ok=True)
                for n in os.listdir(d):
                    try:
                        if time.time() - os.path.getmtime(os.path.join(d, n)) > 3600:
                            os.remove(os.path.join(d, n))
                    except OSError:
                        pass
                self.path = os.path.join(d, self.tok)
                with open(self.path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(f"{int(time.time()) + 900}\n")
            except OSError:
                self.path = None
        os.environ["NJ_GIT_TOKEN"] = self.tok
        return self

    def __exit__(self, *a):
        os.environ.pop("NJ_GIT_TOKEN", None)
        if self.path:
            try:
                os.remove(self.path)
            except OSError:
                pass


def clean_env():
    env = dict(os.environ)
    for k in ("NJ_GIT_TOKEN", "NJ_TICKET"):
        env.pop(k, None)
    return env


# -------------------------------------------------------------- tickets ---

WRITE_SUBS = {"checkpoint", "merge", "push", "sweep", "mode", "wave", "unlock", "install-repo", "install-bin", "install-settings", "smoke-attest"}


def needs_ticket(argv):
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


ENV_OVERRIDES = ("NJ_MODE_OVERRIDE", "NJ_TICKETS", "NJ_HOME", "CLAUDE_HOME", "NJ_ROLES_JSON")


def _is_console(f):
    """A real terminal. On Windows os.isatty() is also true for NUL (`</dev/null >/dev/null`), so ask the console API."""
    try:
        if not f or not f.isatty():
            return False
        if not NT:
            return True
        import ctypes
        import msvcrt
        mode = ctypes.c_uint32()
        return bool(ctypes.windll.kernel32.GetConsoleMode(ctypes.c_void_p(msvcrt.get_osfhandle(f.fileno())), ctypes.byref(mode)))
    except (OSError, ValueError, AttributeError, ImportError):
        return False


def human_tty():
    return _is_console(sys.stdin) and _is_console(sys.stdout)


def selftest_marker_ok():
    """A scripted caller (the selftests, the acceptance runs) proves it owns a scratch state root: NJ_GOV4_SELFTEST names a
    nonce that sits in <NJ_HOME>/selftest.marker, and NJ_HOME lies under the temp directory. An agent can forge this; it
    only redirects gov4.py to a scratch state root (D28: no sandbox on Windows), and the hook flags NJ_* assignments."""
    tok, nj = os.environ.get("NJ_GOV4_SELFTEST"), os.environ.get("NJ_HOME")
    if not tok or not nj:
        return False
    try:
        with open(os.path.join(nj, "selftest.marker"), encoding="utf-8") as f:
            if f.read().strip() != tok:
                return False
        tmp = os.path.normcase(os.path.realpath(tempfile.gettempdir()))
        return os.path.normcase(os.path.realpath(nj)).startswith(tmp + os.sep)
    except OSError:
        return False


def env_trusted():
    """D27: the state-redirecting environment (mode override, ticket habit, NJ_HOME, CLAUDE_HOME) is honoured only for a
    human at a terminal or a marked scratch run, never for a job, an agent or an unknown caller (SB-02, SB-03)."""
    if os.environ.get("NJ_ROLE") == "job":
        return False
    return human_tty() or selftest_marker_ok()


def sanitize_env():
    """Drop the overrides above for an untrusted caller; returns the names dropped."""
    if env_trusted():
        return []
    gone = [k for k in ENV_OVERRIDES if os.environ.get(k)]
    for k in gone:
        os.environ.pop(k, None)
    return gone


def consume_real_ticket(env_value, args):
    """Single-use, argv-bound nonce check. Unlike reg.consume_ticket it has no 'habit' shortcut (SB-03): a caller cannot
    switch the check off with NJ_TICKETS or the tickets-mode file."""
    nonces = [x.strip() for x in str(env_value or "").split(",") if x.strip()]
    if not nonces:
        return False
    sha = reg.argv_sha(args)
    with reg.locked("tickets.lock") as ok:
        if not ok:
            return False
        d = reg.read_json(reg.p("tickets.json"), {}) or {}
        t = reg.now()
        hit = False
        for x in d.get("tickets", []):
            if x.get("nonce") in nonces and not x.get("used") and x.get("exp", 0) > t and x.get("sha") == sha:
                x["used"] = True
                hit = True
                break
        if hit:
            reg.write_json(reg.p("tickets.json"), d)
        return hit


def ticket_ok(argv):
    """Write subcommands need a single-use ticket bound to this argv (spec section 2), but only in ENFORCE (D27): in audit
    gov4.py logs a would-refuse and proceeds, in off it checks nothing. A human at a terminal never needs one."""
    if not needs_ticket(argv):
        return True
    mode = reg.get_mode()
    if mode == "off":
        return True
    if os.environ.get("NJ_TICKET_FORCE") != "1" and human_tty():
        return True
    good = consume_real_ticket(os.environ.get("NJ_TICKET"), argv)
    if good:
        # The hook may mint more than one nonce for one command (it did for a quoted script path in the round-trip test);
        # they all belong to this call, so burn the rest: a replay of the same rewritten command must fail.
        for _ in range(8):
            if not consume_real_ticket(os.environ.get("NJ_TICKET"), argv):
                break
        return True
    if mode != "enforce":
        # events.jsonl, not decisions.jsonl: `mode enforce` must not invalidate the decisions-reviewed evidence by logging its own would-refuse
        reg.log_event({"event": "ticket-would-refuse", "sub": argv[0], "mode": mode, "reason": f"gov4.py {argv[0]} had no valid ticket (enforce would refuse)"})
        return True
    return False


# --------------------------------------------------------------- merge queue ---

def mq_dir(root):
    return os.path.join(root, "work", "merge-queue")


def find_ticket(root, name):
    d = mq_dir(root)
    if not os.path.isdir(d):
        return None, None
    for f in sorted(os.listdir(d)):
        if not f.endswith(".json"):
            continue
        stem = f[:-5]
        if stem == name or re.fullmatch(r"\d+-" + re.escape(name), stem):
            p = os.path.join(d, f)
            data = read_json(p, None)
            if isinstance(data, dict):
                return p, data
    return None, None


def save_ticket(path, data):
    write_json(path, data)


def done_flag(root, name, ok, text):
    d = mq_dir(root)
    os.makedirs(d, exist_ok=True)
    write_text(os.path.join(d, f"DONE-{name}.flag"), f"{'OK' if ok else 'REFUSED'} {name} {now_ts()} {text}\n")
    if ok:
        try:
            os.remove(os.path.join(d, f"READY-{name}.flag"))
        except OSError:
            pass


def load_patterns(root, ref, relpath):
    rc, o, _ = git(root, "show", f"{ref}:{relpath}", timeout=60)
    if rc != 0:
        p = os.path.join(root, relpath)
        o = open(p, encoding="utf-8").read() if os.path.isfile(p) else ""
    return [ln.strip() for ln in o.splitlines() if ln.strip() and not ln.strip().startswith("#")]


def diff_status(root, base, tip):
    rc, o, e = git(root, "diff", "--name-status", "--no-renames", "-z", base, tip, timeout=120)
    if rc != 0:
        return None
    toks = o.split("\0")
    res = {}
    i = 0
    while i + 1 < len(toks):
        st, path = toks[i], toks[i + 1]
        if not st:
            break
        res[norm(path)] = st[0]
        i += 2
    return res


def changed_problems(declared, diff_paths, root):
    ch = []
    for t in declared or []:
        t = norm(t)
        if re.match(r"^[A-Za-z]:/|^/", t):
            r = norm(os.path.relpath(t, root)) if t.lower().startswith(norm(root).lower()) else t
            ch.append(r)
        else:
            ch.append(t[2:] if t.startswith("./") else t)
    pats = [c for c in ch if any(x in c for x in "*?")]
    exact = {c for c in ch if c not in pats}
    dset = set(diff_paths)
    missing = sorted(p for p in dset if p not in exact and not in_union(pats, p))
    extra = sorted(e for e in exact if e not in dset) + [p for p in pats if not any(glob_match(p, d) for d in dset)]
    return missing, extra


def claim_paths(root, run_id, agent):
    d = read_json(os.path.join(root, ".agent-ops", "claims", f"{run_id}.json"), None)
    if not isinstance(d, list):
        return None
    return [p for c in d if c.get("agent") == agent for p in c.get("paths", [])]


def branch_checks(root, tk):
    """Everything both `review` and `merge` verify about a queued branch. Returns an info dict with 'problems'."""
    info = {"problems": [], "notes": []}
    mb = main_branch(root)
    if not mb:
        info["problems"].append("no main/master branch in this repository")
        return info
    branch, head = tk.get("branch"), (tk.get("head") or "").lower()
    tip = rev(root, f"refs/heads/{branch}") if branch else None
    info.update(main=mb, branch=branch, tip=tip, head=head)
    if not tip:
        info["problems"].append(f"branch {branch} does not exist")
        return info
    base_rc, base, _ = git(root, "merge-base", mb, tip, timeout=60)
    base = base.strip() if base_rc == 0 else None
    info["base"] = base
    if not re.fullmatch(r"[0-9a-f]{7,40}", head) or not tip.startswith(head[:40]) and not head.startswith(tip[:len(head)]):
        info["problems"].append(f"head-sha mismatch: receipt {head[:12] or '?'} but tip of {branch} is {tip[:12]}")
    receipt = read_json(tk.get("receipt") or "", None) if tk.get("receipt") else None
    info["receipt"] = receipt
    if isinstance(receipt, dict):
        rh = str(receipt.get("head") or "").lower()
        if re.fullmatch(r"[0-9a-f]{7,40}", rh) and not (tip.startswith(rh) or rh.startswith(tip)):
            info["problems"].append(f"head-sha mismatch: receipt file {rh[:12]} but tip of {branch} is {tip[:12]}")
    if not base:
        info["problems"].append(f"no merge base between {mb} and {branch}")
        return info
    names = diff_status(root, base, tip)
    if names is None:
        info["problems"].append("git diff failed")
        return info
    info["names"] = names
    missing, extra = changed_problems(tk.get("changed"), names, root)
    info["changed_missing"], info["changed_extra"] = missing, extra
    if missing or extra:
        info["problems"].append(f"CHANGED mismatch with git diff --name-only {base[:8]}..{branch}: "
                                f"undeclared {missing[:4]} declared-but-absent {extra[:4]}")
    cp = claim_paths(root, tk.get("run", ""), tk.get("name", ""))
    if cp is None or not cp:
        info["notes"].append("no claim recorded for this agent; diff-versus-claim not checked")
        info["claim"] = None
    else:
        outside = sorted(p for p in names if not in_union(cp, p))
        info["claim"] = cp
        if outside:
            info["problems"].append(f"{len(outside)} path(s) outside the claim {cp[:3]}: {outside[:4]}")
    live = load_patterns(root, mb, ".nj/live-paths.txt")
    bad_live = []
    for p, st in names.items():
        if st != "A" and in_union(live, p):
            if git(root, "cat-file", "-e", f"{mb}:{p}", timeout=30)[0] == 0:
                bad_live.append(f"{st} {p}")
    info["live_bad"] = bad_live
    if bad_live:
        info["problems"].append(f"diff modifies/deletes live path(s) the tools write: {bad_live[:4]}")
    rr = load_patterns(root, mb, ".nj/review-required.txt")
    req = sorted(p for p in names if in_union(rr, p))
    info["review_required"] = req or (["more than 15 files"] if len(names) > 15 else [])
    return info


def dirty_paths(root):
    rc, o, _ = git(root, "status", "--porcelain", "-z", "--untracked-files=all", timeout=120)
    if rc != 0:
        return []
    toks = o.split("\0")
    res, i = [], 0
    while i < len(toks):
        t = toks[i]
        i += 1
        if len(t) < 4:
            continue
        res.append(norm(t[3:]))
        if t[0] in "RC" and i < len(toks):
            res.append(norm(toks[i]))
            i += 1
    return res


# ------------------------------------------------------------------ gates ---

def load_gates(root, ref):
    rc, o, _ = git(root, "show", f"{ref}:.nj/gates.json", timeout=60)
    if rc != 0:
        return None
    try:
        d = json.loads(o)
    except ValueError:
        return {"_invalid": True}
    return d if isinstance(d, dict) else {"_invalid": True}


def each_items(glob, paths, base_dir):
    n = len(norm(glob).strip("/").split("/"))
    found = []
    for p in paths:
        cand = "/".join(p.split("/")[:n])
        if len(p.split("/")) >= n and glob_match(glob, cand) and cand not in found and os.path.exists(os.path.join(base_dir, cand)):
            found.append(cand)
    return found


def run_gates(cwd, doc, diff_paths, subset="post_merge"):
    """Run gates from a .nj/gates.json (schema v1: version, env, full[], post_merge). Returns (ok, lines)."""
    full = doc.get("full") or []
    byid = {g.get("id"): g for g in full}
    if subset == "full":
        sel = list(full)
    else:
        sel = []
        for gid in doc.get("post_merge") or []:
            if gid not in byid:
                return False, [f"{gid} FAIL: named in post_merge but not defined in full[]"]
            sel.append(byid[gid])
    env = clean_env()
    env.update({str(k): str(v) for k, v in (doc.get("env") or {}).items()})
    env.setdefault("PYTHONUTF8", "1")
    bash = find_bash()
    lines, ok = [], True
    for g in sel:
        gid, cmd = g.get("id", "?"), g.get("cmd")
        if not cmd:
            lines.append(f"{gid} FAIL: no cmd")
            ok = False
            continue
        when = g.get("when")
        if when and not any(in_union(when, p) for p in diff_paths):
            lines.append(f"{gid} SKIP (no changed path matches when)")
            continue
        runs = [(gid, cmd)]
        if g.get("each"):
            items = each_items(g["each"], diff_paths, cwd)
            if not items:
                lines.append(f"{gid} SKIP (no changed path matches each)")
                continue
            runs = [(f"{gid}[{it}]", cmd.replace("{path}", it).replace("{slug}", it.rstrip("/").split("/")[-1])) for it in items]
        for label, c in runs:
            rc, so, se = run([bash, "-c", c], cwd=cwd, env=env, timeout=int(g.get("timeout", GATE_TIMEOUT_S)))
            if rc == 0:
                lines.append(f"{label} PASS")
            else:
                first = next((ln.strip() for ln in (se + "\n" + so).splitlines() if ln.strip()), "")[:160]
                lines.append(f"{label} FAIL rc={rc}: {first}")
                ok = False
    return ok, lines


def expand_include(main_root, patterns):
    """Files for .worktreeinclude: glob patterns over the main checkout (git-ignored must-haves such as fonts)."""
    files = []
    for pat in patterns:
        pat = norm(pat).lstrip("/")
        static = re.split(r"[*?]", pat)[0]
        start = os.path.join(main_root, static.rsplit("/", 1)[0] if "/" in static else "") if static else main_root
        if not os.path.isdir(start):
            start = os.path.join(main_root, os.path.dirname(static)) if static else main_root
        for dp, dns, fns in os.walk(start):
            dns[:] = [d for d in dns if d not in (".git", "node_modules")]
            for fn in fns:
                rel = norm(os.path.relpath(os.path.join(dp, fn), main_root))
                if glob_match(pat, rel) and rel not in files:
                    files.append(rel)
    return files


# ---------------------------------------------------------------- commands ---

def resolve_project(args_proj):
    p = args_proj or os.getcwd()
    r = repo_root(p)
    return r


def parse_opts(rest, valued, flags=()):
    """Tiny parser: returns (positionals, options). `valued` options take a value; `flags` are booleans."""
    pos, opts, i = [], {}, 0
    while i < len(rest):
        a = rest[i]
        if a in valued:
            opts[a] = rest[i + 1] if i + 1 < len(rest) else ""
            i += 2
            continue
        if a in flags:
            opts[a] = True
        elif a.startswith("-") and a != "-":
            opts[a] = True
        else:
            pos.append(a)
        i += 1
    return pos, opts


def cmd_checkpoint(rest):
    pos, o = parse_opts(rest, {"-m", "--message"})
    root = resolve_project(pos[0] if pos else None)
    if not root:
        out("checkpoint: not a git repository (non-git folders use `snapshot begin`)")
        return 2
    mb = main_branch(root)
    if not mb or current_branch(root) != mb:
        out(f"checkpoint: refused, the checkout is on '{current_branch(root) or 'detached HEAD'}', not the default branch")
        return 1
    dirty = dirty_paths(root)
    if not dirty:
        out("checkpoint: clean, nothing to commit")
        return 0
    msg = o.get("-m") or o.get("--message") or f"checkpoint: {len(dirty)} path(s) before dispatch ({time.strftime('%Y-%m-%d')})"
    with GitToken():
        paths = [p for p in dirty if not p.startswith((".claude/worktrees/", ".agent-ops/"))]
        rc, so, se = git(root, "add", "-A", "--pathspec-from-file=-", "--pathspec-file-nul",
                         input="\0".join(":(literal)" + p for p in paths) + "\0")
        if rc != 0:
            out(f"checkpoint: git add failed: {se.strip()[:200]}")
            return 1
        if git(root, "diff", "--cached", "--quiet")[0] == 0:
            out("checkpoint: nothing staged (only ignored paths changed)")
            return 0
        rc, so, se = git(root, "commit", "-q", "-m", f"{msg}\n\n{TRAILER_CO}")
        if rc != 0:
            out(f"checkpoint: git commit failed: {(se or so).strip()[:300]}")
            return 1
    out(f"checkpoint ok: {rev(root, 'HEAD')[:10]} ({len(dirty)} paths). Nothing was pushed.")
    reg.log_event({"event": "checkpoint", "project": root, "paths": len(dirty)})
    return 0


def cmd_queue(rest):
    pos, o = parse_opts(rest, {"--project"})
    root = resolve_project(o.get("--project") or (pos[0] if pos else None)) or os.getcwd()
    d = mq_dir(root)
    rows = []
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith(".json"):
                t = read_json(os.path.join(d, f), None)
                if isinstance(t, dict) and ("--all" in o or t.get("state", "queued") == "queued"):
                    rows.append(t)
    if "--json" in o:
        out(json.dumps(rows, indent=1))
        return 0
    if not rows:
        out("queue: empty")
        return 0
    for t in rows:
        out(f"{t.get('name', '?'):<28} {t.get('state', 'queued'):<16} {t.get('branch', '?')} {str(t.get('head', ''))[:8]} "
            f"{len(t.get('changed') or [])} changed  run {t.get('run', '?')}")
    return 0


def helper_rollup(root, tk):
    rdir = os.path.join(root, ".agent-ops", "results", tk.get("run", ""))
    n = 0
    if os.path.isdir(rdir):
        for f in os.listdir(rdir):
            d = read_json(os.path.join(rdir, f), None)
            if isinstance(d, dict) and d.get("parent") == tk.get("name"):
                n += 1
    return n


def cmd_review(rest):
    pos, o = parse_opts(rest, {"--project"})
    root = resolve_project(o.get("--project"))
    if not root:
        out("review: not a git repository")
        return 2
    L = []
    if "--unstaged" in o:
        dirty = dirty_paths(root)
        mb = main_branch(root) or "main"
        live = load_patterns(root, mb, ".nj/live-paths.txt")
        L.append(f"UNSTAGED in {root}: {len(dirty)} path(s) on branch {current_branch(root) or 'detached'}")
        tops = {}
        for p in dirty:
            tops.setdefault(p.split("/")[0], []).append(p)
        for top, ps in sorted(tops.items(), key=lambda kv: -len(kv[1]))[:14]:
            L.append(f"  {top:<24} {len(ps):>4}  e.g. {ps[0][:60]}")
        lp = [p for p in dirty if in_union(live, p)]
        L.append(f"live-path writes (tools): {len(lp)} of {len(dirty)}; other: {len(dirty) - len(lp)}")
        L.append("next: gov4.py checkpoint (a job in the main checkout never commits)")
        L = L[:30]
        out("\n".join(L))
        return 0
    if not pos:
        out("review: <name> required (or --unstaged)")
        return 2
    path, tk = find_ticket(root, pos[0])
    if not tk:
        out(f"review: no ticket named {pos[0]} in {mq_dir(root)}")
        return 1
    info = branch_checks(root, tk)
    rec = info.get("receipt") if isinstance(info.get("receipt"), dict) else None
    L.append(f"REVIEW {tk.get('run')}/{tk.get('name')}  state={tk.get('state', 'queued')}  branch={tk.get('branch')}")
    if rec:
        L.append(f"receipt: status={rec.get('status')} role={rec.get('role')} model={rec.get('model')} "
                 f"helpers_spawned={rec.get('helpers_spawned')} parent={rec.get('parent')}")
    else:
        L.append("receipt: file MISSING or unreadable (" + str(tk.get("receipt")) + ")")
    if info.get("tip"):
        L.append(f"head: receipt {str(tk.get('head'))[:8]} / tip {info['tip'][:8]} -> "
                 + ("OK" if not any("head-sha" in p for p in info["problems"]) else "MISMATCH"))
    names = info.get("names") or {}
    if "names" in info:
        L.append(f"CHANGED: {len(tk.get('changed') or [])} declared, {len(names)} in git diff -> "
                 + ("OK" if not (info.get("changed_missing") or info.get("changed_extra")) else
                    f"MISMATCH undeclared {info['changed_missing'][:3]} absent {info['changed_extra'][:3]}"))
        if info.get("claim"):
            out_c = [p for p in names if not in_union(info["claim"], p)]
            L.append("diff vs claim: " + ("OK" if not out_c else f"{len(out_c)} OUTSIDE {out_c[:3]}"))
        else:
            L.append("diff vs claim: no claim recorded")
        L.append("live paths: " + ("OK (adds allowed, D15)" if not info.get("live_bad") else f"REFUSED {info['live_bad'][:3]}"))
        rr = info.get("review_required") or []
        L.append("reviewer: " + (f"REQUIRED ({rr[:3]}) -> merge needs --reviewed-by" if rr else "not required"))
        gl = (rec or {}).get("gates_at_head") or (rec or {}).get("gates") or []
        if gl:
            L.append(f"gates@head {str(tk.get('head'))[:8]}:")
            for g in gl[:5]:
                L.append("  " + str(g)[:110])
        else:
            L.append("gates@head: none recorded in the receipt")
        rc, ss, _ = git(root, "diff", "--shortstat", info["base"], info["tip"], timeout=60)
        L.append("diffstat: " + (ss.strip() or "empty"))
        rc, ns, _ = git(root, "diff", "--numstat", "--no-renames", info["base"], info["tip"], timeout=60)
        top = []
        for ln in ns.splitlines():
            a, b, p = (ln.split("\t") + ["", "", ""])[:3]
            try:
                top.append((int(a) + int(b), p))
            except ValueError:
                top.append((0, p))
        for n, p in sorted(top, reverse=True)[:4]:
            L.append(f"  {n:>5} lines  {p[:80]}")
    hr = helper_rollup(root, tk)
    L.append(f"helpers: {(rec or {}).get('helpers_spawned', '?')} spawned, {hr} result file(s) naming this agent as parent")
    for n in info.get("notes", []):
        L.append("note: " + n)
    probs = info["problems"]
    L.append("VERDICT: " + ("ready (gates run at merge)" if not probs else "BLOCKED: " + "; ".join(p[:90] for p in probs[:2])))
    if len(L) > 30:
        L = L[:29] + [f"... {len(L) - 29} more line(s) cut"]
    out("\n".join(L))
    return 0 if not probs else 1


def cmd_preflight(rest):
    pos, o = parse_opts(rest, {"--project"})
    root = resolve_project(o.get("--project"))
    if not root or not pos:
        out("preflight: <name> required, inside a git repository")
        return 2
    path, tk = find_ticket(root, pos[0])
    if not tk:
        out(f"preflight: no ticket named {pos[0]}")
        return 1
    mb = main_branch(root)
    rc, so, se = git(root, "merge-tree", "--write-tree", "--name-only", mb, f"refs/heads/{tk.get('branch')}", timeout=120)
    if rc == 0:
        out(f"preflight ok: {tk.get('branch')} merges cleanly into {mb}")
        return 0
    files = [ln for ln in so.splitlines()[1:] if ln.strip() and not ln.startswith(("CONFLICT", "Auto-merging"))][:8]
    if rc == 1:
        tk["state"] = "dequeued-conflict"
        tk["conflict_ts"] = now_ts()
        tk["conflict_files"] = files
        save_ticket(path, tk)
        out(f"preflight CONFLICT: {tk.get('branch')} vs {mb}: {files}. Ticket dequeued; a fresh agent rebases (the Lead never hand-resolves).")
        return 1
    out(f"preflight failed: git merge-tree rc={rc}: {(se or so).strip()[:200]}")
    return 1


def remove_worktree(root, path):
    """git worktree remove --force; on a Windows lock failure rename to _stale-<ts> (retried on the next sweep)."""
    rc, _, e = git(root, "worktree", "remove", "--force", path, timeout=120)
    if rc == 0 and not os.path.exists(path):
        return True, "removed"
    if os.path.isdir(path):
        stale = f"{path}_stale-{int(time.time())}"
        try:
            os.rename(path, stale)
            git(root, "worktree", "prune", timeout=60)
            return True, f"locked ({e.strip()[:60]}); renamed to {os.path.basename(stale)}"
        except OSError as ex:
            return False, f"locked and not renamable: {ex}"
    git(root, "worktree", "prune", timeout=60)
    return True, "pruned"


def cmd_merge(rest):
    pos, o = parse_opts(rest, {"--project", "--reviewed-by", "--no-gates"})
    root = resolve_project(o.get("--project"))
    if not root or not pos:
        out("merge: <name> required, run inside the project's main checkout (or --project P)")
        return 2
    name = pos[0]
    path, tk = find_ticket(root, name)
    if not tk:
        out(f"merge: no ticket named {name} in {mq_dir(root)}")
        return 1
    lock = os.path.join(mq_dir(root), ".merge.lock")
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, f"{os.getpid()} {now_ts()}\n".encode())
        os.close(fd)
    except FileExistsError:
        if time.time() - os.path.getmtime(lock) < 3600:
            out("merge: another merge is running (work/merge-queue/.merge.lock)")
            return 1
        write_text(lock, f"{os.getpid()} {now_ts()}\n")
    except OSError as e:
        out(f"merge: cannot take the merge lock: {e}")
        return 1
    integ = None
    try:
        return _merge_locked(root, name, path, tk, o, [integ])
    finally:
        try:
            os.remove(lock)
        except OSError:
            pass


def _refuse(root, name, path, tk, why, state="refused"):
    out(f"merge REFUSED ({name}): {why}")
    tk["state"] = state if tk.get("state") not in ("merged",) else "merged"
    tk["refused"] = {"ts": now_ts(), "why": why}
    save_ticket(path, tk)
    done_flag(root, name, False, why)
    reg.log_event({"event": "merge-refused", "name": name, "why": why[:200]})
    return 1


def _merge_locked(root, name, path, tk, o, _holder):
    if tk.get("state", "queued") not in ("queued", "refused", "gate-failed"):
        return _refuse(root, name, path, tk, f"ticket state is '{tk.get('state')}', not queued", tk.get("state"))
    mb = main_branch(root)
    if not mb or current_branch(root) != mb:
        return _refuse(root, name, path, tk, f"the main checkout is on '{current_branch(root) or 'detached HEAD'}', not {mb}")
    info = branch_checks(root, tk)
    if info["problems"]:
        return _refuse(root, name, path, tk, "; ".join(info["problems"])[:600])
    names = info["names"]
    dirty = set(dirty_paths(root))
    overlap = sorted(p for p in names if p in dirty)
    if overlap:
        return _refuse(root, name, path, tk, f"dirty paths in main overlap the diff: {overlap[:5]}")
    reviewer = o.get("--reviewed-by")
    if info["review_required"] and not reviewer:
        return _refuse(root, name, path, tk, f"a reviewer is mandatory ({info['review_required'][:3]}): pass --reviewed-by <name>")
    gates = load_gates(root, mb)
    no_gates = o.get("--no-gates")
    if gates is None:
        if not no_gates or no_gates is True:
            return _refuse(root, name, path, tk, f"no .nj/gates.json on {mb}; gates cannot be skipped silently: pass --no-gates \"<reason>\" (logged)")
        reg.log_event({"event": "merge-no-gates", "name": name, "reason": str(no_gates)[:200]})
    elif gates.get("_invalid"):
        return _refuse(root, name, path, tk, ".nj/gates.json is not valid JSON")
    elif no_gates:
        return _refuse(root, name, path, tk, ".nj/gates.json exists: gates are never cut (--no-gates is only for projects without a gate list)")
    main_sha = rev(root, mb)
    wt = os.path.join(root, ".claude", "worktrees", "_integration")
    if os.path.exists(wt):
        ok, why = remove_worktree(root, wt)
        if not ok or os.path.exists(wt):
            return _refuse(root, name, path, tk, f"stale _integration worktree cannot be cleared: {why}")
    os.makedirs(os.path.dirname(wt), exist_ok=True)
    result_sha = None
    with GitToken():
        try:
            rc, so, se = git(root, "worktree", "add", "--detach", wt, main_sha, timeout=300)
            if rc != 0:
                return _refuse(root, name, path, tk, f"git worktree add failed: {se.strip()[:200]}")
            inc = load_patterns(root, mb, ".worktreeinclude")
            copied = 0
            for rel in expand_include(root, inc):
                dst = os.path.join(wt, rel)
                if not os.path.exists(dst):
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(os.path.join(root, rel), dst)
                    copied += 1
            trailers = [f"Task-Id: {tk.get('run')}/{name}", f"Agent-Id: {name}"]
            if reviewer and reviewer is not True:
                trailers.append(f"Reviewed-by: {reviewer}")
            for g in ((info.get("receipt") or {}).get("gates_at_head") or [])[:6]:
                trailers.append("Gate-at-head: " + str(g)[:150].replace("\n", " "))
            trailers.append(TRAILER_CO)
            msg = f"Merge {tk.get('branch')} ({name})\n\n" + "\n".join(trailers)
            rc, so, se = git(wt, "merge", "--no-ff", "-q", "-m", msg, info["tip"], timeout=300)
            if rc != 0:
                git(wt, "merge", "--abort", timeout=60)
                tk["state"] = "dequeued-conflict"
                return _refuse(root, name, path, tk, f"merge conflict in the integration worktree: {(se or so).strip()[:200]}", "dequeued-conflict")
            result_sha = rev(wt, "HEAD")
            gate_lines = []
            if gates is not None:
                ok, gate_lines = run_gates(wt, gates, sorted(names), "full" if "--full-gates" in o else "post_merge")
                if not ok:
                    tk["gate_lines"] = gate_lines
                    return _refuse(root, name, path, tk, "gates failed at merge (main untouched): "
                                   + "; ".join(l for l in gate_lines if "FAIL" in l)[:400], "gate-failed")
            rc, so, se = git(root, "merge", "--ff-only", "-q", result_sha, timeout=300)
            if rc != 0:
                return _refuse(root, name, path, tk, f"fast-forward of {mb} failed (main moved since the merge started? re-run): {(se or so).strip()[:200]}")
        finally:
            if os.path.exists(wt):
                remove_worktree(root, wt)
    tk["state"] = "merged"
    tk["merged"] = {"sha": result_sha, "ts": now_ts(), "gates": gate_lines, "reviewed_by": reviewer if reviewer is not True else None,
                    "no_gates": no_gates if no_gates and no_gates is not True else None, "worktreeinclude_copied": copied}
    save_ticket(path, tk)
    done_flag(root, name, True, f"merged {result_sha[:10]} into {mb}; gates: {', '.join(gate_lines) or 'none (--no-gates)'}")
    reg.log_event({"event": "merge", "name": name, "sha": result_sha, "files": len(names)})
    out(f"merge ok: {name} -> {mb} {result_sha[:10]} ({len(names)} files, {copied} worktreeinclude file(s) copied)")
    for ln in gate_lines:
        out("  gate " + ln)
    return 0


# ------------------------------------------------------------ sweep / push ---

def parse_worktrees_z(text):
    ents, cur = [], None
    for tok in text.split("\0"):
        if not tok:
            if cur:
                ents.append(cur)
            cur = None
            continue
        key, _, val = tok.partition(" ")
        if key == "worktree":
            if cur:
                ents.append(cur)
            cur = {"path": norm(val), "branch": "", "head": "", "locked": False, "prunable": False}
        elif cur is not None:
            if key == "branch":
                cur["branch"] = val.replace("refs/heads/", "", 1)
            elif key == "HEAD":
                cur["head"] = val
            elif key == "locked":
                cur["locked"] = True
            elif key == "prunable":
                cur["prunable"] = True
    if cur:
        ents.append(cur)
    return ents


def process_list():
    if os.environ.get("NJ_SWEEP_NO_PROCS") == "1":
        return []
    rows = []
    if NT:
        ps = ["powershell", "-NoProfile", "-NonInteractive", "-Command",
              "Get-CimInstance Win32_Process | ForEach-Object { \"$($_.ProcessId)|$($_.Name)|$($_.CommandLine)\" }"]
        rc, o, _ = run(ps, timeout=60)
    else:
        rc, o, _ = run(["ps", "-eo", "pid,comm,args"], timeout=30)
    if rc != 0:
        return rows
    for ln in o.splitlines():
        if NT:
            parts = ln.split("|", 2)
            if len(parts) == 3 and parts[0].strip().isdigit():
                rows.append((int(parts[0]), parts[1], parts[2]))
        else:
            parts = ln.split(None, 2)
            if len(parts) == 3 and parts[0].isdigit():
                rows.append((int(parts[0]), parts[1], parts[2]))
    return rows


def do_sweep(root, tags, kept, allow_queued, say, released=()):
    """Returns the list of leftovers; cleans what is safe to clean. Never kills a process."""
    left = []
    is_git = bool(root and repo_root(root))
    queued = set()
    if is_git:
        for f in (os.listdir(mq_dir(root)) if os.path.isdir(mq_dir(root)) else []):
            if f.endswith(".json"):
                t = read_json(os.path.join(mq_dir(root), f), {})
                if isinstance(t, dict) and t.get("state", "queued") == "queued":
                    queued.add(t.get("branch"))
    wt_paths = []
    keep_norm = {norm(k).lower().rstrip("/") for k in kept}
    if is_git:
        mb = main_branch(root)
        git(root, "worktree", "prune", timeout=60)
        rc, o, _ = git(root, "worktree", "list", "--porcelain", "-z", timeout=60)
        ents = parse_worktrees_z(o) if rc == 0 else []
        for e in ents[1:]:
            wt_paths.append(e["path"])
            ident = {e["path"].lower().rstrip("/"), e["branch"].lower(), os.path.basename(e["path"]).lower()}
            if ident & keep_norm:
                say(f"sweep note: worktree {e['path']} deliberately kept")
                continue
            if allow_queued and e["branch"] in queued:
                say(f"sweep note: worktree {e['path']} ({e['branch']}) is queued for merge")
                continue
            clean = not git(e["path"], "status", "--porcelain", timeout=60)[1].strip() if os.path.isdir(e["path"]) else True
            merged = bool(mb and e["head"] and git(root, "merge-base", "--is-ancestor", e["head"], mb, timeout=60)[0] == 0)
            if merged and clean:
                ok, why = remove_worktree(root, e["path"])
                if ok:
                    say(f"sweep cleaned: worktree {e['path']} (merged, {why})")
                    if e["branch"].startswith("worktree-"):
                        git(root, "branch", "-d", e["branch"], timeout=60)
                    continue
                left.append(f"worktree {e['path']} merged but not removable: {why}")
                continue
            if merged and not clean:
                left.append(f"worktree {e['path']} ({e['branch']}) is merged but has uncommitted changes")
            else:
                left.append(f"worktree {e['path']} ({e['branch'] or 'detached'}) holds unmerged work: merge it through gov4.py or --keep it")
        rc, o, _ = git(root, "branch", "--no-merged", mb, "--list", "worktree-*", timeout=60) if mb else (1, "", "")
        on_wt = {e["branch"] for e in ents[1:]} if rc == 0 else set()
        for ln in o.splitlines():
            b = ln.strip().lstrip("*+ ").strip()
            if b and b not in on_wt and b.lower() not in keep_norm and not (allow_queued and b in queued):
                left.append(f"branch {b} holds unmerged commits and has no worktree: merge it through gov4.py, delete it, or --keep it")
        rc, o, _ = git(root, "branch", "--merged", mb, timeout=60) if mb else (1, "", "")
        for ln in o.splitlines():
            b = ln.strip().lstrip("*+ ").strip()
            if b.startswith("worktree-") and b != mb:
                if git(root, "branch", "-d", b, timeout=60)[0] == 0:
                    say(f"sweep cleaned: merged branch {b}")
        wtdir = os.path.join(root, ".claude", "worktrees")
        if os.path.isdir(wtdir):
            for n in os.listdir(wtdir):
                if "_stale-" in n:
                    p = os.path.join(wtdir, n)
                    if safe_delete(p):
                        say(f"sweep cleaned: stale folder {n} (recycle bin)")
                    else:
                        left.append(f"stale folder {p} could not be removed yet (retried on the next sweep)")
    try:
        reg.reconcile(root)
        s = reg.snapshot()
        if s.get("agents"):
            left.append(f"registry: {s['agents']} live agent(s) (live.json): " + ", ".join(
                f"{e.get('agent_type')}:{str(e.get('id'))[:8]}" for e in s["entries"] if e.get("kind") != "job" and not e.get("suspect"))[:200])
        if s.get("pending"):
            left.append(f"registry: {s['pending']} pending spawn reservation(s)")
    except Exception as ex:  # noqa: BLE001
        say(f"sweep note: registry unreadable ({type(ex).__name__})")
    if reg.paused():
        left.append("pause.flag is set (rate limit seen): clear it with `gov4.py live --resume` once the window recovers")
    if wt_paths:
        me = os.getpid()
        pats = [p.lower().rstrip("/") for p in wt_paths]
        for pid, nm, cmd in process_list():
            if pid == me:
                continue
            c = norm(cmd).lower()
            if any(p in c for p in pats):
                left.append(f"process {nm} pid={pid} mentions a worktree (named, not killed)")
    relay = os.environ.get("NJ_RELAY") or os.path.join(HERE, "relay.py")
    if os.path.isfile(relay) and root and os.path.isdir(root):
        cmd = [sys.executable, "-X", "utf8", relay, "sweep", root]
        for t in tags:
            cmd += ["--tag", t]
        for p in wt_paths:
            cmd += ["--kept-worktree", p]
        for r_ in released:
            cmd += ["--released", r_]
        rc, so, se = run(cmd, timeout=120)
        for ln in so.splitlines():
            if ln.startswith("sweep LEFTOVER:"):
                left.append("relay: " + ln.split(":", 1)[1].strip())
    return left


def cmd_sweep(rest):
    pos, o = parse_opts(rest, {"--tag", "--keep", "--project", "--released"})
    # repeated --tag/--keep/--released
    released = [rest[i + 1] for i, a in enumerate(rest) if a == "--released" and i + 1 < len(rest)]
    tags = [rest[i + 1] for i, a in enumerate(rest) if a == "--tag" and i + 1 < len(rest)]
    kept = [rest[i + 1] for i, a in enumerate(rest) if a == "--keep" and i + 1 < len(rest)]
    root = resolve_project(o.get("--project") or (pos[0] if pos else None)) or norm(os.path.abspath(o.get("--project") or (pos[0] if pos else os.getcwd())))
    with GitToken():
        left = do_sweep(root, tags, kept, "--allow-queued" in o, out, released)
    for ln in left:
        out("sweep LEFTOVER: " + ln)
    out(f"sweep: {len(left)} leftover(s)" + ("" if left else " - nothing of this session survives"))
    return 1 if left else 0


def merged_runs(root):
    """Run ids whose queue tickets are all merged or discarded: their claims are finished work, not leftovers."""
    runs, open_ = set(), set()
    d = mq_dir(root)
    for f in (os.listdir(d) if os.path.isdir(d) else []):
        if f.endswith(".json"):
            t = read_json(os.path.join(d, f), {})
            if isinstance(t, dict) and t.get("run"):
                (runs if t.get("state") in ("merged", "discarded") else open_).add(t["run"])
    return sorted(runs - open_)


def cmd_push(rest):
    pos, o = parse_opts(rest, {"--project", "--remote"})
    for bad in ("--force", "-f", "--force-with-lease", "--mirror", "--delete", "--no-verify", "--tags"):
        if bad in rest or any(a.startswith(bad + "=") for a in rest):
            out(f"push: refused, {bad} is never allowed (no force push, no --no-verify)")
            return 1
    root = resolve_project(o.get("--project") or (pos[0] if pos else None))
    if not root:
        out("push: not a git repository")
        return 2
    mb = main_branch(root)
    remote = o.get("--remote") or "origin"
    if not mb or current_branch(root) != mb:
        out(f"push: refused, the checkout is not on the default branch")
        return 1
    rc, url, _ = git(root, "config", "--get", f"remote.{remote}.url", timeout=30)
    if rc != 0 or not url.strip():
        out(f"push: remote '{remote}' has no url")
        return 1
    dirty = dirty_paths(root)
    if dirty:
        out(f"push: refused, {len(dirty)} uncommitted path(s) in main (run checkpoint or review --unstaged first)")
        return 1
    with GitToken():
        left = do_sweep(root, [], [], True, lambda s: None, merged_runs(root))
        if left:
            for ln in left:
                out("sweep LEFTOVER: " + ln)
            out("push: refused, the sweep is not clean")
            return 1
        cmd = ["push", "--atomic"] + (["--dry-run"] if "--dry-run" in o else []) + [remote, mb]
        rc, so, se = git(root, "-c", f"remote.{remote}.pushurl=", "-c", f"remote.{remote}.pushurl={url.strip()}", *cmd, timeout=600)
    if rc != 0:
        out(f"push failed: {(se or so).strip()[:300]}")
        return 1
    out(f"push ok: {mb} -> {remote}" + (" (dry run)" if "--dry-run" in o else ""))
    reg.log_event({"event": "push", "project": root, "remote": remote})
    return 0


# --------------------------------------------------------- live / modes ---

def cmd_live(rest):
    if "--reconcile" in rest:
        return reg.live_main(["reconcile"])
    if "--pause" in rest:
        why = " ".join(a for a in rest if a != "--pause") or "paused by the Lead"
        ok = reg.set_pause(why)
        out("pause.flag set: spawns are denied until `live --resume`" if ok else "pause.flag could not be written (no NJ home)")
        return 0 if ok else 1
    if "--resume" in rest:
        reg.clear_pause()
        out("pause.flag cleared")
        return 0
    return reg.live_main(rest)


def peak_from_verify(text):
    m = re.search(r"peak live subagents:\s*(\d+)", text)
    inc = re.search(r"429/529 incidents:\s*(\d+)", text)
    return (int(m.group(1)) if m else None), (int(inc.group(1)) if inc else None)


def cmd_wave(rest):
    pos, o = parse_opts(rest, {"--project"})
    if not pos:
        out(f"wave: {reg.get_wave()} (platform ceiling 20)")
        return 0
    try:
        n = int(pos[0])
    except ValueError:
        out("wave: 5|10|20")
        return 2
    if n not in (5, 10, 20):
        out("wave: 5|10|20")
        return 2
    if n == 20:
        project = o.get("--project") or os.getcwd()
        relay = os.environ.get("NJ_RELAY") or os.path.join(HERE, "relay.py")
        rc, so, se = run([sys.executable, "-X", "utf8", relay, "verify", project], timeout=180)
        peak, inc = peak_from_verify(so)
        why = []
        if rc != 0:
            why.append(f"relay.py verify is not clean (exit {rc})")
        if peak is None or peak < 10:
            why.append(f"no clean run at a peak of 10 or more (peak {peak if peak is not None else 'NOT_VISIBLE'})")
        if inc is None or inc != 0:
            why.append(f"429/529 incidents {inc if inc is not None else 'NOT_VISIBLE'}, need 0")
        if why:
            out("wave 20 REFUSED (decision D4): " + "; ".join(why))
            return 1
    ok = reg.set_wave(n)
    out(f"wave set to {n}" if ok else "wave could not be written (no NJ home)")
    return 0 if ok else 1


def audit_since():
    p = reg.p("audit-since")
    try:
        v = open(p, encoding="utf-8").read().strip()
        try:
            return float(v)
        except ValueError:
            return time.mktime(time.strptime(v[:19], "%Y-%m-%dT%H:%M:%S"))
    except (OSError, ValueError):
        pass
    try:
        return os.path.getmtime(reg.p("mode"))
    except OSError:
        return None


def enforce_ready(project=None, say=out):
    res = []
    ev = read_json(reg.p("enforce-evidence.json"), {}) or {}
    since = audit_since()
    hours = (time.time() - since) / 3600 if since else None
    need = float(os.environ.get("NJ_AUDIT_HOURS", "20"))
    res.append(("audit day elapsed", hours is not None and hours >= need,
                f"{hours:.1f} h of audit (need {need:.0f})" if hours is not None else "no audit start recorded (audit-since or mode file missing)"))
    wp8 = bool(ev.get("wp8_migrated"))
    if project:
        cr = os.path.join(project, "scripts", "linkedin", "claude_run.py")
        sites = ["build_week.py", "comments_watch.py", "connect_weekly.py", "engage_daily.py"]
        miss = []
        for s in sites:
            fp = os.path.join(project, "scripts", "linkedin", s)
            try:
                if "claude_run" not in open(fp, encoding="utf-8").read():
                    miss.append(s)
            except OSError:
                miss.append(s)
        wp8 = wp8 or (os.path.isfile(cr) and not miss)
    res.append(("WP8 migrated", wp8, "claude_run.py present and used by the call sites" if wp8 else "no evidence (pass --project, or --record wp8)"))
    e2e = bool(ev.get("job_e2e_passed"))
    if project:
        d = read_json(os.path.join(project, "work", "job-e2e.json"), None)
        if isinstance(d, dict) and d.get("rc", d.get("returncode")) in (0, "0") and d.get("ok", True):
            e2e = True
    res.append(("job_e2e passed", e2e, "job e2e evidence found" if e2e else "no evidence (work/job-e2e.json or --record job_e2e)"))
    try:
        n_dec = sum(1 for _ in open(reg.p("decisions.jsonl"), encoding="utf-8"))
    except OSError:
        n_dec = 0
    dr = ev.get("decisions_reviewed") or {}
    reviewed = isinstance(dr, dict) and int(dr.get("lines", -1)) >= n_dec and dr.get("lines") is not None
    res.append(("decisions reviewed", reviewed, f"{n_dec} decision line(s); reviewed up to {dr.get('lines') if isinstance(dr, dict) else None}"))
    return res


def cmd_enforce_ready(rest):
    pos, o = parse_opts(rest, {"--project", "--record", "--note"})
    if o.get("--record"):
        item = o["--record"]
        ev = read_json(reg.p("enforce-evidence.json"), {}) or {}
        if item == "wp8":
            ev["wp8_migrated"] = {"ts": now_ts(), "note": o.get("--note", "")}
        elif item == "job_e2e":
            ev["job_e2e_passed"] = {"ts": now_ts(), "note": o.get("--note", "")}
        elif item == "decisions":
            try:
                n = sum(1 for _ in open(reg.p("decisions.jsonl"), encoding="utf-8"))
            except OSError:
                n = 0
            ev["decisions_reviewed"] = {"ts": now_ts(), "lines": n, "note": o.get("--note", "")}
        else:
            out("enforce-ready --record: wp8|job_e2e|decisions")
            return 2
        write_json(reg.p("enforce-evidence.json"), ev)
        out(f"recorded {item}")
        return 0
    res = enforce_ready(o.get("--project"))
    for name, ok, why in res:
        out(f"{'PASS' if ok else 'FAIL'} {name}: {why}")
    allok = all(ok for _, ok, _ in res)
    out("enforce-ready: " + ("READY" if allok else "NOT READY"))
    return 0 if allok else 1


def cmd_mode(rest):
    pos, o = parse_opts(rest, {"--project", "--settings-file"})
    if not pos:
        out(f"mode: {reg.get_mode()}")
        return 0
    m = pos[0]
    if m not in ("off", "audit", "enforce"):
        out("mode: off|audit|enforce")
        return 2
    if m == "enforce":
        res = enforce_ready(o.get("--project"))
        bad = [n for n, ok, _ in res if not ok]
        if bad:
            out("mode enforce REFUSED, enforce-ready fails: " + ", ".join(bad))
            return 1
    spath = o.get("--settings-file") or os.path.join(claude_home(), "settings.json")
    if m == "enforce" and os.path.isfile(spath) and not isinstance(read_json(spath, None), dict):
        out(f"mode enforce REFUSED: {spath} is not valid JSON, so the git deny rules cannot be written")
        return 1
    if not reg.home_ok():
        os.makedirs(reg.home(), exist_ok=True)
    if m == "audit" and not os.path.exists(reg.p("audit-since")):
        write_text(reg.p("audit-since"), now_ts() + "\n")
    reg.set_mode(m)
    ok, note = apply_mode_to_settings(spath, m)       # D20/D26: git deny rules and onFailure exist only in enforce
    out(f"mode set to {m}" + (" (hooks inert; env and defaults stay until rollback)" if m == "off" else "") + f"; {note}")
    if not ok:
        out(f"mode {m}: WARNING, {note}; fix settings.json by hand")
    return 0


def cmd_unlock(rest):
    if any(a in ("-h", "--help", "help") for a in rest):
        out("usage: gov4.py unlock [--minutes N] [--reason R] | --revoke   (writes unlock.json, opens the protected paths, expires by itself)")
        return 0
    pos, o = parse_opts(rest, {"--minutes", "--reason"})
    stray = [a for a in pos]
    bad = [a for a in rest if a.startswith("-") and a not in ("--minutes", "--reason", "--revoke")]
    if stray or bad:
        out("unlock: unknown argument(s) " + " ".join(stray + bad) + " (nothing written); see gov4.py unlock --help")
        return 2
    if "--revoke" in o:
        try:
            os.remove(reg.p("unlock.json"))
        except OSError:
            pass
        out("unlock revoked")
        return 0
    cap = int(reg.read_roles().get("limits", {}).get("unlock_ttl_min", 60))
    try:
        mins = min(int(o.get("--minutes", cap)), cap)
    except ValueError:
        out("unlock: --minutes needs a number")
        return 2
    if not reg.home_ok():
        os.makedirs(reg.home(), exist_ok=True)
    exp = time.time() + mins * 60
    write_json(reg.p("unlock.json"), {"expires_ts": exp, "expires": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(exp)),
                                      "reason": o.get("--reason", ""), "minutes": mins, "written": now_ts()})
    reg.log_event({"event": "unlock", "minutes": mins, "reason": str(o.get("--reason", ""))[:100]})
    out(f"unlock written: protected paths open for {mins} min (until {time.strftime('%H:%M', time.localtime(exp))}). It expires by itself.")
    return 0


# -------------------------------------------------------------- install ---

def githooks_src():
    for d in (os.path.join(HERE, "..", "githooks"), os.path.join(HERE, "githooks")):
        if os.path.isfile(os.path.join(d, "reference-transaction")):
            return os.path.abspath(d)
    return None


def read_bytes(p):
    with open(p, "rb") as f:
        return f.read()


BAKE_TOKEN = b"NJ_STATE_DIR='@@NJ_STATE_DIR@@'"


def copy_if_changed(src, dst, executable=False, bake=None):
    """bake: absolute state path written into the git hooks in place of the @@NJ_STATE_DIR@@ placeholder (SB-02): the hooks
    never read NJ_HOME or any other variable to find the mode."""
    data = read_bytes(src).replace(b"\r\n", b"\n") if src.endswith(("reference-transaction", "pre-push")) else read_bytes(src)
    if bake:
        data = data.replace(BAKE_TOKEN, ("NJ_STATE_DIR='%s'" % bake).encode("utf-8"))
    try:
        if read_bytes(dst) == data:
            return False
    except OSError:
        pass
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + f".{os.getpid()}.tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, dst)
    if executable and not NT:
        os.chmod(dst, 0o755)
    return True


DEAD_PUSHURL = "NJ-GOVERNANCE-pushurl-disabled-use-gov4-push"


def cmd_install_repo(rest):
    pos, o = parse_opts(rest, {"--project", "--hooks-dir"})
    root = resolve_project(o.get("--project") or (pos[0] if pos else None))
    if not root:
        out("install-repo: not a git repository")
        return 2
    src = githooks_src()
    if not src:
        out("install-repo: githooks/ not found beside the scripts")
        return 1
    hd = norm(os.path.abspath(o.get("--hooks-dir") or os.path.join(reg.home(), "githooks")))
    state = norm(os.path.abspath(reg.home()))
    if "'" in state or "\n" in state:
        out(f"install-repo: refused, the state path {state!r} holds a quote or newline and cannot be baked into the hooks")
        return 1
    changed = []
    for h in ("reference-transaction", "pre-push"):
        if copy_if_changed(os.path.join(src, h), os.path.join(hd, h), True, bake=state):
            changed.append(h)
    rc, cur, _ = git(root, "config", "--local", "--get", "core.hooksPath", timeout=30)
    cur = norm(cur.strip())
    if cur and cur.rstrip("/").lower() != hd.rstrip("/").lower() and "--force-hooks-path" not in o:
        out(f"install-repo: refused, core.hooksPath is already {cur} (another hook manager?); pass --force-hooks-path to replace it")
        return 1
    notes = []
    for key, val in (("core.hooksPath", hd), ("core.longpaths", "true")):
        rc, c, _ = git(root, "config", "--local", "--get", key, timeout=30)
        if c.strip() != val:
            git(root, "config", "--local", key, val, timeout=30)
            notes.append(f"{key}={val}")
    rc, url, _ = git(root, "config", "--local", "--get", "remote.origin.url", timeout=30)
    if rc == 0 and url.strip():
        rc, pu, _ = git(root, "config", "--local", "--get", "remote.origin.pushurl", timeout=30)
        if pu.strip() != DEAD_PUSHURL:
            git(root, "config", "--local", "remote.origin.pushurl", DEAD_PUSHURL, timeout=30)
            notes.append("remote.origin.pushurl=dead")
    out(f"install-repo ok: hooks {hd} " + ("updated " + ",".join(changed) if changed else "unchanged") + "; config "
        + (", ".join(notes) if notes else "unchanged"))
    return 0


INSTALL_FILES = [
    ("gov4_hook.py", "scripts"), ("gov4_registry.py", "scripts"), ("gov4.py", "scripts"), ("gov4_snapshot.py", "scripts"),
    ("relay.py", "scripts"), ("sdlc.py", "scripts"), ("roles.json", "templates"), ("check_governance.py", "check_governance"),
]


def plugin_root():
    return os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def install_sources():
    out_files = []
    for n, kind in INSTALL_FILES:
        if kind == "scripts":
            cands = [os.path.join(HERE, n)]
        elif kind == "templates":
            cands = [os.path.join(HERE, "..", "templates", n), os.path.join(HERE, n)]
        else:
            cands = [os.path.join(plugin_root(), "skills", "nj-delegate", "scripts", n), os.path.join(HERE, n)]
        p = next((c for c in cands if os.path.isfile(c)), None)
        if p:
            out_files.append((n, os.path.abspath(p)))
    return out_files


def cmd_install_bin(rest):
    pos, o = parse_opts(rest, set())
    files = install_sources()
    names = {n for n, _ in files}
    for need in ("gov4_hook.py", "gov4_registry.py", "roles.json"):
        if need not in names:
            out(f"install-bin: {need} not found")
            return 1
    h = hashlib.sha256()
    for n, p in sorted(files):
        h.update(n.encode() + b"\0" + read_bytes(p) + b"\0")
    gh = githooks_src()
    if gh:
        for n in sorted(os.listdir(gh)):
            h.update(b"githooks/" + n.encode() + b"\0" + read_bytes(os.path.join(gh, n)).replace(b"\r\n", b"\n") + b"\0")
    sha8 = h.hexdigest()[:8]
    dest = os.path.join(reg.home(), "bin", sha8)
    if "--dry-run" in o:
        out(f"install-bin dry run: would copy {len(files)} files to {dest}")
        return 0
    os.makedirs(dest, exist_ok=True)
    n_new = 0
    for n, p in files:
        n_new += 1 if copy_if_changed(p, os.path.join(dest, n)) else 0
    if gh:
        for n in os.listdir(gh):
            n_new += 1 if copy_if_changed(os.path.join(gh, n), os.path.join(dest, "githooks", n), True) else 0
    launcher = os.path.join(HERE, "gov4_launcher.py")
    if os.path.isfile(launcher):
        copy_if_changed(launcher, os.path.join(reg.home(), "gov4_launcher.py"))
        # H8: the launcher selftest (doctor hooks-interpreter) imports the hook and the registry from the launcher's own folder
        for n, p in files:
            if n in ("gov4_hook.py", "gov4_registry.py"):
                copy_if_changed(p, os.path.join(reg.home(), n))
    cur_p, prev_p = os.path.join(reg.home(), "bin", "CURRENT"), os.path.join(reg.home(), "bin", "PREVIOUS")
    try:
        cur = open(cur_p, encoding="utf-8").read().strip()
    except OSError:
        cur = ""
    if cur != sha8:
        if cur:
            write_text(prev_p, cur + "\n")
        write_text(cur_p, sha8 + "\n")
    out(f"install-bin ok: bin/{sha8} ({len(files)} files, {n_new} written), CURRENT={sha8} PREVIOUS={cur or 'none'}")
    return 0


# --------------------------------------------------------------- snapshot ---

def cmd_snapshot(rest):
    if not rest:
        out("snapshot: begin|diff|apply|commit <project> --run <rid>")
        return 2
    sub = rest[0]
    runner = None
    if sub == "commit":
        _, o = parse_opts(rest[1:], {"--run", "-m", "--no-gates"})
        proj = next((a for a in rest[1:] if not a.startswith("-") and a not in o.values()), os.getcwd())
        rid = o.get("--run")

        def runner(root):
            rec = read_json(snap().record_path(os.path.abspath(root), rid), {}) or {}
            ap = rec.get("applied") or {}
            paths = list(ap.get("added", [])) + list(ap.get("modified", [])) + list(ap.get("deleted", []))
            doc = read_json(os.path.join(root, ".nj", "gates.json"), None)
            if not isinstance(doc, dict):
                return False, ["gates.json unreadable"]
            return run_gates(os.path.abspath(root), doc, paths, "post_merge")
    return snap().main(rest, gates_runner=runner, out=out)


def cmd_smoke_attest(rest):
    sm = os.path.abspath(os.environ.get("NJ_SMOKE_DIR") or os.path.join(HERE, "..", "smoke"))
    rs = os.path.join(sm, "run_smoke.py")
    res = os.path.join(sm, "RESULTS.md")
    if not os.path.isfile(rs) or not os.path.isfile(res):
        out("smoke-attest: smoke/run_smoke.py or RESULTS.md missing")
        return 1
    rc, so, se = run([sys.executable, "-X", "utf8", rs, "verify-results", "--allow-pending"], timeout=120)
    out((so or se).strip()[:300])
    if rc != 0:
        out("smoke-attest REFUSED: verify-results is not OK (RESULTS.md hand-edited or stale)")
        return 1
    text = open(res, encoding="utf-8").read()
    m = re.search(r"TRACE-CHAIN sha256:([0-9a-f]{64}) files=(\d+)", text)
    att = {"results_sha256": sha256_file(res), "trace_chain": m.group(1) if m else None, "trace_files": int(m.group(2)) if m else None,
           "attested_by": "lead", "ts": now_ts(),
           "pass_lines": len(re.findall(r"^S\d PASS ", text, re.M)), "pending": len(re.findall(r"^S\d PENDING-INTERACTIVE ", text, re.M))}
    write_json(os.path.join(sm, "ATTEST.json"), att)
    out(f"smoke-attest ok: {att['pass_lines']} PASS line(s), {att['pending']} pending, sha {att['results_sha256'][:12]}")
    return 0


# ---------------------------------------------------------------- doctor ---

def claude_home():
    return os.environ.get("CLAUDE_HOME") or os.path.join(os.path.expanduser("~"), ".claude")


REQ_DENY_AGENT = ["Agent(model:opus)", "Agent(model:fable)", "Agent(model:claude-opus-5-5)", "Agent(model:claude-opus-5-5[1m])"]
REQ_DENY_GIT = ["push", "merge", "rebase", "tag", "update-ref", "reset --hard", "branch -D", "worktree add", "worktree remove"]
REQ_DENY_GH = ["gh pr merge", "gh pr create"]
REQ_DENY_SECRET = [".config/linkedin", ".git-credentials"]
REQ_HOOKS = {"PreToolUse": ["agent", "git", "ticket", "write", "mcp"], "SubagentStart": ["start"],
             "SubagentStop": ["stop-team", "stop-helper"], "SessionStart": ["session-start"]}

# D20: deny rules block in every mode and in already-open sessions, so the audit activation writes only the model and secret
# denies; the git-write and `gh pr` denies belong to enforce (`mode enforce` writes them, `mode audit|off` removes them).
DENY_SECRET = ["Read(~/.config/linkedin/**)", "Bash(* ~/.config/linkedin/*)", "Read(~/.claude/.credentials*)", "Read(~/.git-credentials)",
               "Bash(* ~/.git-credentials*)"]
DENY_AUDIT = REQ_DENY_AGENT + DENY_SECRET
DENY_ENFORCE = ([f"{t}(git {v} *)" for t in ("Bash", "PowerShell") for v in REQ_DENY_GIT]
                + [f"{t}({v} *)" for t in ("Bash", "PowerShell") for v in REQ_DENY_GH])
ALLOW_RULES = ["Bash(python * gov4.py status*)", "Bash(python * gov4.py live*)", "Bash(python * gov4.py review*)", "Bash(python * gov4.py doctor*)",
               "Bash(python * gov4.py preflight*)", "Bash(python * gov4.py selftest*)", "Bash(python * gov4.py merge *)"]
ASK_RULES = ["Bash(python * gov4.py push *)", "PowerShell(python * gov4.py push *)"]
LEAD_MODEL_KEY = "claude-opus-5-5"


def launcher_sub(cmd):
    """The launcher subcommand (agent, git, ticket ...) a hook command runs, or None when it is not a launcher command."""
    m = re.search(r"gov4_launcher\.py\s+(?:--)?([a-z][a-z-]*)", cmd or "")
    if m:
        return m.group(1)
    if "gov4_launcher" in (cmd or ""):
        g = re.search(r"sys\.argv\s*=\s*\[[^,\]]+,\s*['\"]([a-z][a-z-]*)['\"]\]", cmd)     # the D26 guard form: python -c "...sys.argv=[p,'agent']..."
        if g:
            return g.group(1)
        m = re.search(r"([a-z][a-z-]*)[\"']*\s*$", cmd)
        return m.group(1) if m else None
    return None


def hook_sig(cmd):
    sub = launcher_sub(cmd)
    if sub:
        return ("launcher", sub)
    if re.search(r"sdlc\.py[\"']?\s+hook\b", cmd or ""):
        return ("sdlc-hook", "")
    return ("exact", cmd or "")


def split_command(cmd):
    """(interpreter, launcher path) of a launcher hook command; either may be None."""
    m = re.match(r"""\s*(?:"([^"]+)"|'([^']+)'|(\S+))""", cmd or "")
    interp = next((g for g in (m.groups() if m else ()) if g), None)
    lm = re.search(r"""(?:"([^"]*gov4_launcher\.py)"|'([^']*gov4_launcher\.py)'|([^\s"']*gov4_launcher\.py))""", cmd or "")
    launcher = next((g for g in (lm.groups() if lm else ()) if g), None)
    return interp, launcher


def lead_permission_mode():
    """CD-5: (mode, source) of the Lead's real permission mode, or None. The Lead registration (leads.json, written by the
    SessionStart hook from the hook payload's permission_mode) wins; the VS Code setting claudeCode.initialPermissionMode is the
    fallback hint. Never raises."""
    d = read_json(reg.p("leads.json"), {}) or {}
    best = None
    for sid, v in (d.get("sessions") or {}).items():
        if isinstance(v, dict) and v.get("permission_mode"):
            if best is None or float(v.get("ts", 0)) >= float(best[1].get("ts", 0)):
                best = (sid, v)
    if best:
        return str(best[1]["permission_mode"]), f"Lead registration {str(best[0])[:8]}"
    cands = [os.environ.get("NJ_VSCODE_SETTINGS")] if os.environ.get("NJ_VSCODE_SETTINGS") else []
    appdata = os.environ.get("APPDATA")
    if appdata:
        cands += [os.path.join(appdata, "Code", "User", "settings.json"), os.path.join(appdata, "Code - Insiders", "User", "settings.json")]
    for c in cands:
        try:
            raw = open(c, encoding="utf-8").read()
            m = re.search(r'"claudeCode\.initialPermissionMode"\s*:\s*"([A-Za-z]+)"', raw)
            if m:
                return m.group(1), "VS Code setting claudeCode.initialPermissionMode"
        except OSError:
            pass
    return None


_UNSET = object()


def doctor_settings(s, real=False, mode=None, lead_mode=_UNSET):
    """mode: the governance mode the settings must fit (D20): enforce needs the git/gh deny rules and onFailure block on the
    Agent hook; audit and off must not carry them (they would block the Lead). Default: audit."""
    R = []
    mode = mode or "audit"

    def add(level, area, msg):
        R.append((level, area, msg))
    if not isinstance(s, dict) or not s:
        add("FAIL", "settings", "settings are empty or unreadable")
        return R
    # Lead effort
    eff = []
    for k, v in (s.get("modelSettings") or {}).items():
        if "opus" in str(k).lower() and isinstance(v, dict) and "effortLevel" in v:
            eff.append((f"modelSettings.{k}.effortLevel", v["effortLevel"]))
    if "effortLevel" in s:
        eff.append(("effortLevel", s["effortLevel"]))
    if not eff:
        add("FAIL", "effort", "Lead effort is not set: modelSettings.claude-opus-5-5.effortLevel must be medium")
    for k, v in eff:
        if str(v).lower() == "medium":
            add("PASS", "effort", f"{k} = medium")
        else:
            add("FAIL", "effort", f"{k} = {v}; the Lead runs at medium (xhigh and max are denied)")
    env = s.get("env") or {}
    roles = reg.read_roles()
    forb = roles.get("env_forbidden") or ["CLAUDE_CODE_EFFORT_LEVEL", "CLAUDE_CODE_SUBAGENT_MODEL_FORCE",
                                          "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"]
    hit = [k for k in forb if k in env]
    add("FAIL" if hit else "PASS", "env-forbidden", ("set: " + ", ".join(hit)) if hit else "no forbidden env keys")
    req = roles.get("env_required") or {"CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "2", "CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS": "20",
                                        "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet", "PYTHONUTF8": "1"}
    miss = [k for k in req if k not in env]
    wrong = [f"{k}={env[k]} (want {v})" for k, v in req.items() if k in env and str(env[k]) != str(v)]
    add("FAIL" if (miss or wrong) else "PASS", "env-required",
        ("missing " + ", ".join(miss) if miss else "") + ("; " if miss and wrong else "") + ("wrong " + ", ".join(wrong) if wrong else "")
        if (miss or wrong) else "required env keys present")
    uc = [k for k in list(s) + list(env) if "ultracode" in str(k).lower() and str((s.get(k) if k in s else env.get(k))).lower() not in ("false", "0", "off", "", "none")]
    add("FAIL" if uc else "PASS", "ultracode", ("ultracode is on (" + ", ".join(uc) + "): it removes the 20 cap") if uc else "ultracode off")
    if real and lead_mode is _UNSET:
        lead_mode = lead_permission_mode()
    if lead_mode is _UNSET:
        pm = ((s.get("permissions") or {}).get("defaultMode") or "default")
        src = "permissions.defaultMode"
    elif lead_mode:
        pm, src = lead_mode
    else:
        pm, src = None, ""
    if pm is None:
        add("WARN", "permission-mode", "unknown: no Lead registration records permission_mode and no VS Code setting names one (decision D2: the "
            "Lead may run in bypassPermissions; GATE tags are only valid for the mode the smoke proved)")
    elif pm in ("bypassPermissions", "acceptEdits", "auto"):
        add("WARN", "permission-mode", f"{src} = {pm} (decision D2: WARN, not FAIL; GATE tags are only valid for the mode the smoke proved)")
    else:
        add("PASS", "permission-mode", f"{src} = {pm}")
    br = (s.get("worktree") or {}).get("baseRef")
    add("PASS" if br == "head" else "FAIL", "worktree.baseRef", f"{br!r}" + ("" if br == "head" else " (must be 'head': worktrees branch from the checkpoint)"))
    # hooks
    hooks = s.get("hooks") or {}
    pairs = []                      # (interpreter, launcher) per launcher hook command
    if not isinstance(hooks, dict) or not hooks:
        add("FAIL", "hooks", "no hooks block")
    else:
        found = {}
        direct = []
        unpinned = []
        agent_fail = []
        for ev, groups in hooks.items():
            for g in groups if isinstance(groups, list) else []:
                for h in (g.get("hooks") or []) if isinstance(g, dict) else []:
                    cmd = h.get("command", "") if isinstance(h, dict) else ""
                    sub = launcher_sub(cmd)
                    if sub:
                        found.setdefault(ev, set()).add(sub)
                        if not re.match(r"""^\s*["']?([A-Za-z]:[\\/]|/|~)""", cmd):
                            unpinned.append(sub)
                        pairs.append(split_command(cmd))
                        if sub == "agent":
                            agent_fail.append(h.get("onFailure"))
                    elif "gov4_hook.py" in cmd:
                        direct.append(ev)
        # A10: one `bash` launcher hook runs both the git scan and the ticket step; the older split (git + ticket) is accepted too
        missing = [f"{ev}:{sub}" for ev, subs in REQ_HOOKS.items() for sub in subs
                   if sub not in found.get(ev, set()) and not (ev == "PreToolUse" and sub in ("git", "ticket") and "bash" in found.get(ev, set()))]
        add("FAIL" if missing else "PASS", "hooks", ("not wired through gov4_launcher.py: " + ", ".join(missing)) if missing else "all governance hooks go through the launcher")
        if direct:
            add("WARN", "hooks", "gov4_hook.py called directly (bypasses the launcher fallback): " + ", ".join(sorted(set(direct))))
        if unpinned:
            add("WARN", "hooks", "interpreter path not absolute for: " + ", ".join(sorted(set(unpinned))))
        # D26: onFailure block exists only in enforce (a broken launcher must never block in audit or off)
        if mode == "enforce":
            ok = bool(agent_fail) and all(x == "block" for x in agent_fail)
            add("PASS" if ok else "FAIL", "agent-onfailure", "Agent hook blocks on failure (enforce)" if ok else "enforce needs onFailure: block on the Agent hook (gov4.py mode enforce writes it)")
        else:
            on = any(x == "block" for x in agent_fail)
            add("WARN" if on else "PASS", "agent-onfailure", f"onFailure: block on the Agent hook in {mode} mode (a broken launcher would block spawns; gov4.py mode {mode} removes it)" if on
                else f"no onFailure block in {mode} mode")
        bad = [k for k in ("WorktreeCreate", "WorktreeRemove") if k in hooks]
        add("FAIL" if bad else "PASS", "worktree-hooks", ("installed (forbidden, they replace native creation): " + ", ".join(bad)) if bad else "no WorktreeCreate/WorktreeRemove hook")
        wf = "workflow" in found.get("PreToolUse", set())
        add("PASS" if wf else "WARN", "hooks-workflow", "Workflow matcher wired" if wf else "Workflow matcher not wired (active after S3 shows it fires)")
        stub = sorted({i for i, _ in pairs if i and "windowsapps" in i.replace("\\", "/").lower()})
        if stub:
            add("FAIL", "hooks-interpreter", "the pinned interpreter is the WindowsApps stub (it is not a real Python): " + ", ".join(stub))
    # deny / ask
    perms = s.get("permissions") or {}
    deny = [str(x) for x in (perms.get("deny") or [])]
    miss = [r for r in REQ_DENY_AGENT if r not in deny]
    for sec in REQ_DENY_SECRET:
        if not any(sec in d for d in deny):
            miss.append(f"a deny rule for {sec}")
    git_miss = []
    for tool in ("Bash", "PowerShell"):
        for v in REQ_DENY_GIT:
            if not any(d.startswith(f"{tool}(git {v}") for d in deny):
                git_miss.append(f"{tool}(git {v} *)")
    for v in REQ_DENY_GH:
        if not any(d.startswith(f"Bash({v}") for d in deny):
            git_miss.append(f"Bash({v} *)")
    if mode == "enforce":
        miss += git_miss
    add("FAIL" if miss else "PASS", "deny-rules", ("missing: " + ", ".join(miss[:10]) + (f" (+{len(miss) - 10} more)" if len(miss) > 10 else "")) if miss else f"{len(deny)} deny rules, all required present")
    if mode != "enforce":
        present = [d for d in deny if re.match(r"(Bash|PowerShell)\((git (%s)|gh pr (merge|create))\b" % "|".join(re.escape(v) for v in REQ_DENY_GIT), d)]
        add("WARN" if present else "PASS", "deny-rules-git", (f"{len(present)} git/gh deny rule(s) are active in {mode} mode and block the Lead's own git writes in "
            f"every open session (D20); gov4.py mode {mode} removes them") if present else f"no git/gh deny rules in {mode} mode (D20)")
    ask = [str(x) for x in (perms.get("ask") or [])]
    add("PASS" if any("gov4.py push" in a for a in ask) else "WARN", "ask-rules", "gov4.py push sits under an ask rule" if any("gov4.py push" in a for a in ask) else "no ask rule for gov4.py push (spec: until two clean pushes)")
    if real:
        seen = set()
        for interp, launcher in pairs:
            if (interp, launcher) in seen or not interp:
                continue
            seen.add((interp, launcher))
            if "windowsapps" in interp.replace("\\", "/").lower():
                continue
            if not os.path.isfile(interp):
                add("FAIL", "hooks-interpreter", f"pinned interpreter does not exist: {interp}")
                continue
            if not launcher or not os.path.isfile(launcher):
                add("FAIL" if mode == "enforce" else "WARN", "hooks-launcher", f"launcher file does not exist: {launcher} (run gov4.py install-bin; hooks fail open until then)")
                continue
            rc, so, se = run([interp, "-I", "-X", "utf8", launcher, "--selftest"], timeout=20)
            ok = rc == 0 and "ok" in (so or "")
            add("PASS" if ok else "FAIL", "hooks-interpreter", f"{interp} runs the launcher selftest" if ok else
                f"{interp} did not run the launcher selftest (rc {rc}): {((so or '') + (se or '')).strip()[-160:]}")
    return R


# ------------------------------------------------------- install-settings ---

def _deep_merge(dst, src):
    """dst <- src: dicts merge key by key, lists union (order kept, no duplicates), scalars from src win. Keys starting with '_' are notes."""
    for k, v in src.items():
        if str(k).startswith("_"):
            continue
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_merge(dst[k], v)
        elif isinstance(v, list) and isinstance(dst.get(k), list):
            have = [json.dumps(x, sort_keys=True) for x in dst[k]]
            for x in v:
                if json.dumps(x, sort_keys=True) not in have:
                    dst[k].append(json.loads(json.dumps(x)))
                    have.append(json.dumps(x, sort_keys=True))
        else:
            dst[k] = json.loads(json.dumps(v))
    return dst


def _quote_if_needed(val, before):
    if re.search(r"""[\s()&;]""", val) and not (before and before[-1] in "\"'"):
        return '"' + val + '"'
    return val


def fill_placeholders(obj, python, nj_home):
    if isinstance(obj, dict):
        return {k: fill_placeholders(v, python, nj_home) for k, v in obj.items()}
    if isinstance(obj, list):
        return [fill_placeholders(v, python, nj_home) for v in obj]
    if isinstance(obj, str):
        def home_sub(m):
            return _quote_if_needed(nj_home + m.group(1), obj[:m.start()])
        t = re.sub(r"__NJ_HOME__([^\s\"']*)", home_sub, obj)
        return re.sub(r"__PYTHON__", lambda m: _quote_if_needed(python, t[:m.start()]), t)
    return obj


def _merge_hooks(cur, frag, notes):
    for ev, groups in (frag or {}).items():
        cg = cur.setdefault(ev, [])
        for g in groups:
            m = g.get("matcher") if isinstance(g, dict) else None
            for fh in (g.get("hooks") or []):
                sig = hook_sig(fh.get("command", ""))
                locs = [(gi, hi) for gi, grp in enumerate(cg) for hi, ch in enumerate(grp.get("hooks") or [])
                        if (hook_sig(ch.get("command", "")) == sig if sig[0] != "exact" else ch.get("command") == fh.get("command"))]
                same = [(gi, hi) for gi, hi in locs if cg[gi].get("matcher") == m]
                if sig[0] == "sdlc-hook":
                    if locs:
                        extra = locs[1:]
                        for gi, hi in sorted(extra, reverse=True):
                            del cg[gi]["hooks"][hi]
                        if extra:
                            notes.append(f"removed {len(extra)} duplicate sdlc.py SubagentStop hook(s)")
                        continue
                elif sig[0] == "exact" and locs:
                    continue
                elif sig[0] == "launcher" and same:
                    gi, hi = same[0]
                    if cg[gi]["hooks"][hi] != fh:
                        notes.append(f"updated {ev} launcher hook {sig[1]}")
                    cg[gi]["hooks"][hi] = json.loads(json.dumps(fh))
                    for gj, hj in sorted(locs, reverse=True):
                        if (gj, hj) != (gi, hi):
                            del cg[gj]["hooks"][hj]
                    continue
                for gi, hi in sorted(locs, reverse=True):         # launcher hook under another matcher: move it
                    del cg[gi]["hooks"][hi]
                tgt = next((grp for grp in cg if grp.get("matcher") == m and grp.get("hooks") is not None), None)
                if tgt is None:
                    tgt = {k: v for k, v in g.items() if k != "hooks"}
                    tgt["hooks"] = []
                    cg.append(tgt)
                tgt["hooks"].append(json.loads(json.dumps(fh)))
                notes.append(f"added {ev} hook {sig[1] or sig[0]}")
        cur[ev] = [grp for grp in cg if grp.get("hooks")]
    return cur


def set_enforce_extras(s, enforce):
    """D20/D26: the git-write and gh deny rules and the Agent hook's onFailure: block exist only in enforce."""
    perms = s.setdefault("permissions", {})
    deny = list(perms.get("deny") or [])
    if enforce:
        for r in DENY_ENFORCE:
            if r not in deny:
                deny.append(r)
    else:
        deny = [r for r in deny if r not in DENY_ENFORCE]
    if deny or "deny" in perms:
        perms["deny"] = deny
    if not perms:
        s.pop("permissions", None)
    for ev, groups in (s.get("hooks") or {}).items():
        for g in groups if isinstance(groups, list) else []:
            for h in (g.get("hooks") or []) if isinstance(g, dict) else []:
                if isinstance(h, dict) and launcher_sub(h.get("command", "")) == "agent":
                    if enforce:
                        h["onFailure"] = "block"
                    else:
                        h.pop("onFailure", None)
    return s


def merge_settings(cur, frag, python, nj_home, mode):
    """Deterministic deep merge of the hooks fragment plus the D20 blocks into the current settings. Returns (new, notes).
    Nothing the current file holds is dropped, except the intended changes (required env values, effort medium, baseRef head,
    a duplicated sdlc.py hook, the enforce-only rules when the mode is not enforce)."""
    new = json.loads(json.dumps(cur if isinstance(cur, dict) else {}))
    notes = []
    frag = fill_placeholders(frag, python, nj_home)
    roles = reg.read_roles()
    env_req = dict(roles.get("env_required") or {"CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "2", "CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS": "20",
                                                "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet", "PYTHONUTF8": "1"})
    for k in (roles.get("env_forbidden") or []):
        if k in (new.get("env") or {}):
            notes.append(f"env.{k} is forbidden and stays (remove it by hand): doctor will FAIL")
    blocks = {"env": env_req, "modelSettings": {LEAD_MODEL_KEY: {"effortLevel": "medium"}}, "worktree": {"baseRef": "head"},
              "permissions": {"deny": list(DENY_AUDIT), "allow": list(ALLOW_RULES), "ask": list(ASK_RULES)}}
    before = json.dumps(new, sort_keys=True)
    hooks_frag = frag.pop("hooks", None)
    _deep_merge(new, {k: v for k, v in frag.items() if k not in blocks})
    for k, v in blocks.items():
        if k in frag and isinstance(frag[k], dict):
            v = _deep_merge(json.loads(json.dumps(v)), frag[k])
        if isinstance(new.get(k), dict) or k not in new:
            _deep_merge(new.setdefault(k, {}), v)
    if "effortLevel" in new and str(new["effortLevel"]).lower() != "medium":
        new["effortLevel"] = "medium"
    if hooks_frag:
        new["hooks"] = _merge_hooks(new.get("hooks") if isinstance(new.get("hooks"), dict) else {}, hooks_frag, notes)
    set_enforce_extras(new, mode == "enforce")
    if json.dumps(new, sort_keys=True) != before and not notes:
        notes.append("settings updated")
    return new, notes


def _flat_hooks(s):
    out_ = set()
    for ev, groups in ((s or {}).get("hooks") or {}).items():
        for g in groups if isinstance(groups, list) else []:
            for h in (g.get("hooks") or []) if isinstance(g, dict) else []:
                if isinstance(h, dict):
                    out_.add((ev, g.get("matcher"), h.get("command")))
    return out_


def _preserved(pre, cur, path, allowed, problems):
    if isinstance(pre, dict):
        if not isinstance(cur, dict):
            problems.append(f"{path or '/'}: was an object, now {type(cur).__name__}")
            return
        for k, v in pre.items():
            if str(k).startswith("_"):
                continue
            sub = f"{path}.{k}".lstrip(".")
            if k not in cur:
                if sub not in allowed:
                    problems.append(sub + ": key dropped")
                continue
            if k == "hooks" and path == "":
                continue
            _preserved(v, cur[k], sub, allowed, problems)
    elif isinstance(pre, list):
        if not isinstance(cur, list):
            problems.append(f"{path}: was a list, now {type(cur).__name__}")
            return
        have = [json.dumps(x, sort_keys=True) for x in cur]
        for x in pre:
            if json.dumps(x, sort_keys=True) not in have and not (path == "permissions.deny" and x in DENY_ENFORCE):
                problems.append(f"{path}: entry dropped: {json.dumps(x)[:80]}")
    else:
        if pre != cur and path not in allowed:
            problems.append(f"{path}: {pre!r} became {cur!r}")


def doctor_against(cur, pre):
    """A4: every key and value of the pre-v4 settings is still there, except the intended changes; the sdlc.py SubagentStop hook
    appears exactly once. Returns doctor result rows."""
    R = []
    if not isinstance(pre, dict) or not pre:
        return [("FAIL", "against", "the pre-v4 settings are empty or unreadable")]
    if not isinstance(cur, dict):
        return [("FAIL", "against", "the settings are unreadable")]
    allowed = {f"env.{k}" for k in (reg.read_roles().get("env_required") or {})} | {f"modelSettings.{LEAD_MODEL_KEY}.effortLevel", "effortLevel", "worktree.baseRef"}
    problems = []
    _preserved(pre, cur, "", allowed, problems)
    lost = sorted((h for h in _flat_hooks(pre) if h not in _flat_hooks(cur)), key=str)
    for ev, m, cmd in lost:
        problems.append(f"hooks.{ev}[{m}]: hook dropped: {str(cmd)[:80]}")
    R.append(("FAIL" if problems else "PASS", "against", ("; ".join(problems[:8]) + (f" (+{len(problems) - 8} more)" if len(problems) > 8 else "")) if problems
              else "every pre-v4 key and value is preserved (intended changes aside)"))

    def n_sdlc(d):
        return sum(1 for ev, groups in (d.get("hooks") or {}).items() for g in groups if isinstance(g, dict) for h in (g.get("hooks") or [])
                   if hook_sig(h.get("command", ""))[0] == "sdlc-hook")
    got, want = n_sdlc(cur), (1 if n_sdlc(pre) else 0)
    R.append(("PASS" if got == want else "FAIL", "against-sdlc-hook", f"sdlc.py hook appears {got} time(s), want {want}"))
    return R


def pick_python(arg):
    cand = arg or sys.executable
    cand = norm(os.path.abspath(cand)) if cand else ""
    if "windowsapps" in cand.lower():
        return None, f"{cand} is the WindowsApps stub; pass --python with a real interpreter"
    if not os.path.isfile(cand):
        return None, f"interpreter {cand} does not exist"
    return cand, ""


def default_fragment():
    for d in (os.path.join(HERE, "..", "..", "..", "install"), os.path.join(HERE, "..", "install"), HERE):
        f = os.path.join(d, "settings-v4.fragment.json")
        if os.path.isfile(f):
            return os.path.abspath(f)
    return None


def _write_settings(path, obj):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def cmd_install_settings(rest):
    pos, o = parse_opts(rest, {"--settings-file", "--fragment", "--python", "--nj-home", "--mode", "--against"})
    path = o.get("--settings-file") or os.path.join(claude_home(), "settings.json")
    mode = o.get("--mode") or "audit"
    if mode not in ("audit", "enforce"):
        out("install-settings: --mode audit|enforce (the activation is audit)")
        return 2
    cur = read_json(path, None) if os.path.exists(path) else {}
    if cur is None:
        out(f"install-settings: refused, {path} is not valid JSON (nothing written)")
        return 1
    fp = o.get("--fragment") or default_fragment()
    frag = read_json(fp, None) if fp else None
    if not isinstance(frag, dict):
        out(f"install-settings: fragment {fp} not found or not valid JSON")
        return 1
    python, why = pick_python(o.get("--python"))
    if not python:
        out("install-settings: refused, " + why)
        return 1
    nj_home = norm(os.path.abspath(o.get("--nj-home") or reg.home()))
    new, notes = merge_settings(cur, frag, python, nj_home, mode)
    pre_p = o.get("--against") or path + ".pre-v4"
    pre = read_json(pre_p, None) if os.path.isfile(pre_p) else (cur if cur else None)
    R = [r for r in doctor_settings(new, real=False, mode=mode, lead_mode=None) if r[1] != "permission-mode"]
    if pre:
        R += doctor_against(new, pre)
    bad = [r for r in R if r[0] == "FAIL"]
    if not os.path.isfile(os.path.join(nj_home, "gov4_launcher.py")):
        notes.append(f"WARN launcher {nj_home}/gov4_launcher.py is not installed yet (run gov4.py install-bin); the hooks fail open until it is")
    for n in notes:
        out("install-settings: " + n)
    if bad:
        for l, a, m in bad:
            out(f"  {l} {a}: {m}")
        out("install-settings: refused, the merged settings fail the doctor checks (nothing written)")
        return 1
    if json.dumps(new, sort_keys=True) == json.dumps(cur, sort_keys=True):
        out(f"install-settings: unchanged ({path} already holds the merged settings for mode {mode})")
        return 0
    if "--dry-run" in o:
        out(f"install-settings dry run: would write {path} (mode {mode}, python {python}, state {nj_home})")
        return 0
    if os.path.isfile(path) and not os.path.exists(path + ".pre-v4") and not o.get("--against"):
        shutil.copy2(path, path + ".pre-v4")
        out(f"install-settings: kept the current settings as {path}.pre-v4")
    _write_settings(path, new)
    out(f"install-settings ok: {path} (mode {mode}); every pre-v4 key preserved, hooks pinned to {python}")
    return 0


def apply_mode_to_settings(path, m):
    """`gov4.py mode <m>`: write or remove the enforce-only rules in settings.json (D20, D26). Returns (ok, note)."""
    if not os.path.isfile(path):
        return True, f"{path} not found; no permission rules to change"
    s = read_json(path, None)
    if not isinstance(s, dict):
        return False, f"{path} is not valid JSON"
    before = json.dumps(s, sort_keys=True)
    set_enforce_extras(s, m == "enforce")
    if json.dumps(s, sort_keys=True) == before:
        return True, f"{path}: git deny rules and onFailure already fit mode {m}"
    _write_settings(path, s)
    return True, f"{path}: git/gh deny rules and the Agent onFailure block " + ("added" if m == "enforce" else "removed")


FM_KEYS = {"name", "description", "tools", "disallowedTools", "model", "effort", "color", "maxTurns", "omitClaudeMd",
           "permissionMode", "skills", "mcpServers", "hooks", "memory", "background", "initialPrompt"}


def parse_frontmatter(text):
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    fm, key = {}, None
    for ln in lines[1:]:
        if ln.strip() == "---":
            return fm
        m = re.match(r"^([A-Za-z][A-Za-z0-9_]*)\s*:\s*(.*)$", ln)
        if m and not ln.startswith((" ", "\t")):
            key = m.group(1)
            fm[key] = m.group(2).strip().strip("'\"")
        elif key and ln.strip().startswith("- "):
            fm[key] = (fm[key] + "," if fm[key] else "") + ln.strip()[2:].strip()
    return None


def lint_agents(adir):
    R = []
    if not os.path.isdir(adir):
        return [("FAIL", "agents", f"{adir} does not exist")]
    names = sorted(f for f in os.listdir(adir) if f.endswith(".md"))
    if not names:
        return [("FAIL", "agents", f"no agent definitions in {adir}")]
    for f in names:
        stem = f[:-3]
        fm = parse_frontmatter(open(os.path.join(adir, f), encoding="utf-8").read())
        probs = []
        if fm is None:
            R.append(("FAIL", "agent:" + stem, "no readable frontmatter"))
            continue
        unknown = sorted(set(fm) - FM_KEYS - {"isolation"})
        if unknown:
            probs.append("unknown key(s) (silently ignored by the platform): " + ", ".join(unknown))
        if "isolation" in fm:
            probs.append("isolation key present (isolation is chosen on the Agent call)")
        if fm.get("name") and fm["name"] != stem:
            probs.append(f"name '{fm['name']}' differs from the file name")
        model = str(fm.get("model", "")).lower()
        if model not in ("sonnet", "haiku"):
            probs.append(f"model '{fm.get('model', '')}' (must be sonnet or haiku; never opus, inherit or missing)")
        if fm.get("effort") and str(fm["effort"]).lower() not in ("low", "medium", "high"):
            probs.append(f"effort {fm['effort']} (xhigh and max are denied for workers)")
        tools = [t.strip() for t in re.split(r"[,\s]+", fm.get("tools", "")) if t.strip()]
        tools = [re.sub(r"\(.*", "", t) for t in tools]
        dis = [t.strip() for t in re.split(r"[,\s]+", fm.get("disallowedTools", "")) if t.strip()]
        info, _ = reg.type_info(stem)
        role = (info or {}).get("role")
        if info and info.get("model") and model in ("sonnet", "haiku") and info["model"] != model:
            probs.append(f"model {model} differs from roles.json ({info['model']})")
        if role == "helper" or stem.startswith(("nj-helper-", "crew-")):
            if "tools" in fm and any(t in tools for t in ("Agent", "SendMessage")):
                probs.append("helper lists Agent or SendMessage in tools")
            if not all(x in dis for x in ("Agent", "SendMessage")) and "tools" not in fm:
                probs.append("helper must carry disallowedTools: Agent, SendMessage")
            if "tools" in fm and not all(x in dis for x in ("Agent", "SendMessage")) and not tools:
                probs.append("helper has an empty tools list and no disallowedTools")
        if role == "reviewer" or stem.startswith("council-"):
            bad = [t for t in tools if t in ("Edit", "Write", "NotebookEdit", "SendMessage")]
            if bad:
                probs.append("reviewer is read-only but lists " + ", ".join(bad))
        R.append(("FAIL", "agent:" + stem, "; ".join(probs)) if probs else ("PASS", "agent:" + stem, f"model {model}"))
    return R


ROOT_FILES = [
    "skills/nj-agent-ops/SKILL.md", "skills/nj-delegate/SKILL.md", "skills/nj-delegate/reference/runtime-map.md",
    "skills/nj-delegate/scripts/check_governance.py", "skills/nj-agent-ops/scripts/relay.py",
    "skills/nj-agent-ops/scripts/gov4.py", "skills/nj-agent-ops/scripts/gov4_snapshot.py", "skills/nj-agent-ops/scripts/gov4_hook.py",
    "skills/nj-agent-ops/scripts/gov4_registry.py", "skills/nj-agent-ops/scripts/gov4_launcher.py", "skills/nj-agent-ops/templates/roles.json",
]


def marketplace_version(root):
    d = read_json(os.path.join(root, ".claude-plugin", "marketplace.json"), None)
    try:
        return str(d["plugins"][0]["version"])
    except (TypeError, KeyError, IndexError):
        return None


def doctor_cache(source, cache_dir, kit):
    R = []
    if not source or not os.path.isdir(source):
        return [("FAIL", "cache", f"plugin source {source} not found")]
    ver = marketplace_version(source)
    R.append(("PASS" if ver else "FAIL", "version", f"marketplace.json version {ver}"))
    roots = [("source", source)]
    if cache_dir:
        if not os.path.isdir(cache_dir):
            R.append(("FAIL", "cache", f"plugin cache {cache_dir} not found (version dir must equal {ver})"))
        else:
            roots.append(("cache", cache_dir))
    kit_ok = bool(kit and os.path.isdir(kit))
    if kit_ok:
        roots.append(("kit", kit))
    else:
        R.append(("WARN", "kit", f"kit copy {kit} not found"))
    for label, r in roots:
        v = marketplace_version(r)
        if v and ver and v != ver:
            R.append(("FAIL", "version", f"{label} marketplace.json is {v}, source is {ver}"))
        pj = read_json(os.path.join(r, ".claude-plugin", "plugin.json"), None)
        if isinstance(pj, dict) and pj.get("version") and ver and str(pj["version"]) != ver:
            R.append(("FAIL", "version", f"{label} plugin.json is {pj['version']}, marketplace.json is {ver}"))
        nested = os.path.join(r, "nj-plugin")
        if os.path.isdir(os.path.join(nested, "skills")):
            R.append(("FAIL" if label != "kit" else "WARN", "nested", f"{label} holds a nested stale copy {nested} (remove after Nader confirms)"))
    base = dict(roots)
    bad = 0
    for rel in ROOT_FILES:
        sp = os.path.join(source, rel)
        if not os.path.isfile(sp):
            continue
        h0 = sha256_file(sp)
        for label, r in roots[1:]:
            tp = os.path.join(r, rel)
            if not os.path.isfile(tp):
                R.append(("FAIL" if label == "cache" else "WARN", "hash", f"{rel}: missing in {label}"))
                bad += 1
            elif sha256_file(tp) != h0:
                R.append(("FAIL" if label == "cache" else "WARN", "hash", f"{rel}: {label} differs from source"))
                bad += 1
    if not bad:
        R.append(("PASS", "hash", f"{len(ROOT_FILES)} tracked files equal across {', '.join(l for l, _ in roots)}"))
    return R


def parse_tags(text):
    """clause id -> (tag, script) from SKILL.md lines such as '0.11 ... [GATE: gov4.py]'."""
    tags = {}
    for ln in text.splitlines():
        for m in re.finditer(r"(?<![\w.])(0\.\d{1,2})(?![\d.]*\d)", ln):
            t = re.search(r"\[(GATE|LINT|HABIT)(?::\s*([^\]]+))?\]", ln)
            if t and m.group(1) not in tags:
                tags[m.group(1)] = (t.group(1), (t.group(2) or "").strip())
    return tags


def mutation_status(path):
    d = read_json(path, None)
    res = {}
    if isinstance(d, dict):
        if isinstance(d.get("killed"), list) or isinstance(d.get("survived"), list):
            for k in d.get("killed") or []:
                res[k] = True
            for k in d.get("survived") or []:
                res[k] = False
        for key in ("mutants", "results"):
            v = d.get(key)
            if isinstance(v, dict):
                for k, x in v.items():
                    res[k] = (x is True) or (isinstance(x, str) and x.lower() == "killed") or (isinstance(x, dict) and bool(x.get("killed") or str(x.get("status", "")).lower() == "killed"))
            elif isinstance(v, list):
                for x in v:
                    if isinstance(x, dict) and x.get("id"):
                        res[x["id"]] = bool(x.get("killed")) or str(x.get("status", "")).lower() == "killed"
    elif isinstance(d, list):
        for x in d:
            if isinstance(x, dict) and x.get("id"):
                res[x["id"]] = bool(x.get("killed")) or str(x.get("status", "")).lower() == "killed"
    return res


def evidence_binding(path, root):
    """TV-2: mutation and redteam evidence must say which code it vouches for. The file carries
    "guarded_sha256": {"<path relative to the plugin root>": "<sha256 of the file when the run happened>"}; the evidence counts
    only while every listed file still has that hash. Returns (ok, problem)."""
    d = read_json(path, None)
    if not isinstance(d, dict):
        return False, f"{os.path.basename(path)} missing or unreadable"
    g = d.get("guarded_sha256")
    if not isinstance(g, dict) or not g:
        return False, f"{os.path.basename(path)} records no guarded_sha256 (the run is not bound to the code it tested)"
    stale = []
    for rel, want in sorted(g.items()):
        fp = os.path.normpath(os.path.join(root, rel))
        if os.path.relpath(fp, root).startswith("..") or not os.path.isfile(fp):
            stale.append(f"{rel} (missing)")
        elif sha256_file(fp) != str(want).lower():
            stale.append(rel)
    if stale:
        return False, f"{os.path.basename(path)} is older than the code it vouches for: " + ", ".join(stale[:5]) + (f" (+{len(stale) - 5})" if len(stale) > 5 else "") + " changed since the run"
    return True, ""


def doctor_tags(root, skill_path=None):
    R = []
    sk = os.path.join(root, "skills", "nj-agent-ops")
    deps = read_json(os.path.join(sk, "templates", "clause-deps.json"), None)
    if not deps:
        return [("FAIL", "tags", "templates/clause-deps.json missing")]
    text = ""
    for cand in ([skill_path] if skill_path else []) + [os.path.join(root, "skills", "nj-delegate", "SKILL.md")]:
        if cand and os.path.isfile(cand):
            text = open(cand, encoding="utf-8").read()
            break
    tags = parse_tags(text) if "nj-governance-v4" in text else {}
    src = "SKILL.md"
    if not tags:
        R.append(("WARN", "tags", "SKILL.md is not the v4 text yet (no clause tags); judging the initial tags of clause-deps.json"))
        tags = {cid: (c.get("initial_tag"), c.get("tag_script") or "") for cid, c in deps["clauses"].items()}
        src = "clause-deps.json"
    sm = os.path.join(sk, "smoke")
    results_p = os.path.join(sm, "RESULTS.md")
    attest = read_json(os.path.join(sm, "ATTEST.json"), None)
    chain_ok, results_text = False, ""
    if os.path.isfile(results_p):
        results_text = open(results_p, encoding="utf-8").read()
        rc, so, se = run([sys.executable, "-X", "utf8", os.path.join(sm, "run_smoke.py"), "verify-results", "--allow-pending"], timeout=120) \
            if os.path.isfile(os.path.join(sm, "run_smoke.py")) else (1, "", "run_smoke.py missing")
        chain_ok = rc == 0
        R.append(("PASS" if chain_ok else "FAIL", "smoke-chain", "RESULTS.md matches the trace hash chain" if chain_ok else "verify-results failed: " + (so or se).strip()[-160:]))
    else:
        R.append(("FAIL", "smoke-chain", "smoke/RESULTS.md missing"))
    attested = bool(attest) and isinstance(attest, dict) and chain_ok and results_text and attest.get("results_sha256") == sha256_file(results_p)
    R.append(("PASS" if attested else "FAIL", "smoke-attest", "RESULTS.md attested by the Lead" if attested else "RESULTS.md not attested (gov4.py smoke-attest) or edited after attestation"))
    mut_p = os.path.join(root, "skills", "tests", "MUTATION.json")
    if not os.path.isfile(mut_p):
        mut_p = os.path.join(root, "tests", "MUTATION.json")
    mut = mutation_status(mut_p)
    mut_bound = evidence_binding(mut_p, root) if mut else (True, "")
    rt_p = os.path.join(root, "skills", "tests", "REDTEAM.json")
    if not os.path.isfile(rt_p):
        rt_p = os.path.join(root, "tests", "REDTEAM.json")
    rt_bound = evidence_binding(rt_p, root)
    redteam_ran = None
    for cid in sorted(deps["clauses"], key=lambda x: [int(p) for p in x.split(".")]):
        tag, script = tags.get(cid, (None, ""))
        c = deps["clauses"][cid]
        if tag is None:
            R.append(("FAIL", f"clause {cid}", f"no tag found in {src}"))
            continue
        if tag != "GATE":
            if tag == "LINT" and script and not os.path.isfile(_script_path(root, script)):
                R.append(("FAIL", f"clause {cid}", f"[LINT: {script}] names a script that does not exist"))
            else:
                R.append(("PASS", f"clause {cid}", f"[{tag}] needs no attested evidence"))
            continue
        probs = []
        if not script or not os.path.isfile(_script_path(root, script)):
            probs.append(f"GATE names a missing script '{script}'")
        for s in c.get("smoke", []):
            if not (attested and re.search(rf"^{s} PASS ", results_text, re.M)):
                probs.append(f"{s} has no attested PASS")
        for m in c.get("mutants", []):
            if mut.get(m) is not True:
                probs.append(f"mutant {m} not killed" if m in mut else f"mutant {m} missing from MUTATION.json")
        if c.get("mutants") and mut and not mut_bound[0]:
            probs.append(mut_bound[1])
        if cid == "0.18":
            rt = os.path.join(root, "skills", "tests", "redteam_v4.py")
            rt = rt if os.path.isfile(rt) else os.path.join(root, "tests", "redteam_v4.py")
            if not os.path.isfile(rt):
                probs.append("tests/redteam_v4.py missing")
            else:
                if redteam_ran is None:
                    redteam_ran = run([sys.executable, "-X", "utf8", rt], timeout=600)[0] == 0
                if not redteam_ran:
                    probs.append("redteam_v4.py is not clean")
                if os.path.isfile(rt_p) and not rt_bound[0]:
                    probs.append(rt_bound[1])
        R.append(("FAIL", f"clause {cid}", "GATE without evidence: " + "; ".join(probs)) if probs else ("PASS", f"clause {cid}", "GATE evidence complete"))
    return R


def _script_path(root, name):
    name = (name.split() or [""])[0].rstrip(",")
    for d in (os.path.join(root, "skills", "nj-agent-ops", "scripts"), os.path.join(root, "skills", "nj-delegate", "scripts")):
        for n in (name, name + ".py"):
            if os.path.isfile(os.path.join(d, n)):
                return os.path.join(d, n)
    return os.path.join(root, name)


def cmd_doctor(rest):
    pos, o = parse_opts(rest, {"--settings-file", "--agents-dir", "--source", "--cache-dir", "--kit", "--skill", "--against", "--mode"})
    if "--against" in o and "--settings" not in o:
        o["--settings"] = True
    sel = [k for k in ("--settings", "--agents", "--tags", "--cache") if k in o]
    quiet = "--quiet" in o
    if not sel:
        sel = ["--settings", "--agents", "--cache"]
    R = []
    if "--settings" in sel:
        sf = o.get("--settings-file")
        path = sf or os.path.join(claude_home(), "settings.json")
        dmode = o.get("--mode") or ("audit" if sf else reg.get_mode())
        cur_s = read_json(path, None)
        R += [(l, "settings." + a, m) for l, a, m in doctor_settings(cur_s, real=not sf, mode="enforce" if dmode == "enforce" else "audit")]
        if o.get("--against"):
            R += [(l, "settings." + a, m) for l, a, m in doctor_against(cur_s, read_json(o["--against"], None))]
    if "--agents" in sel:
        R += [(l, "agents." + a, m) for l, a, m in lint_agents(o.get("--agents-dir") or os.path.join(claude_home(), "agents"))]
    if "--cache" in sel:
        source = o.get("--source") or os.environ.get("NJ_PLUGIN_SRC") or (plugin_root() if os.path.isdir(os.path.join(plugin_root(), "skills")) else "D:/projects/nj-plugin")
        ver = marketplace_version(source)
        cache_dir = o.get("--cache-dir") or (os.path.join(claude_home(), "plugins", "cache", "nj-kit", "nj-kit", ver) if ver else None)
        kit = o.get("--kit") or "D:/projects/nj-kit/bundled/nj-plugin"
        R += [(l, "cache." + a, m) for l, a, m in doctor_cache(source, cache_dir, kit)]
    if "--tags" in sel:
        root = o.get("--source") or os.environ.get("NJ_PLUGIN_SRC") or (
            plugin_root() if os.path.isdir(os.path.join(plugin_root(), "skills", "nj-agent-ops")) else "D:/projects/nj-plugin")
        R += [(l, "tags." + a, m) for l, a, m in doctor_tags(root, o.get("--skill"))]
    fails = sum(1 for r in R if r[0] == "FAIL")
    warns = sum(1 for r in R if r[0] == "WARN")
    for lvl, area, msg in R:
        if quiet and lvl == "PASS":
            continue
        out(f"{lvl} {area}: {msg}")
    if not quiet or fails or warns:
        out(f"doctor: {fails} FAIL, {warns} WARN, {len(R) - fails - warns} PASS")
    return 1 if fails else 0


# --------------------------------------------------------------- rollback ---

def allowed_roots():
    ch = os.environ.get("CLAUDE_HOME")
    if not ch:
        return None
    roots = [norm(os.path.abspath(ch)).lower()]
    for x in (os.environ.get("NJ_ROLLBACK_EXTRA_ROOTS") or "").split(os.pathsep):
        if x:
            roots.append(norm(os.path.abspath(x)).lower())
    return roots


def inside(path, roots):
    p = norm(os.path.abspath(path)).lower()
    return any(p == r or p.startswith(r.rstrip("/") + "/") for r in roots)


def tree_hashes(path):
    res = {}
    if os.path.isfile(path):
        return {"": sha256_file(path)}
    for dp, dns, fns in os.walk(path):
        for fn in fns:
            fp = os.path.join(dp, fn)
            res[norm(os.path.relpath(fp, path))] = sha256_file(fp)
    return res


def create_snapshot(items, out_dir=None):
    """items: [{id, dest (absolute), kind: file|dir}] -> snapshot dir with manifest.json. Missing dests are recorded as absent."""
    ts = time.strftime("%Y%m%d-%H%M%S")
    sd = out_dir or os.path.join(reg.home(), f"snapshot-{ts}")
    os.makedirs(sd, exist_ok=True)
    man = {"version": GOV, "ts": now_ts(), "items": []}
    for it in items:
        dest = os.path.abspath(it["dest"])
        rec = {"id": it["id"], "dest": norm(dest), "present": os.path.exists(dest)}
        if rec["present"]:
            rec["kind"] = "dir" if os.path.isdir(dest) else "file"
            srcdir = os.path.join(sd, "items", it["id"])
            if rec["kind"] == "dir":
                shutil.copytree(dest, srcdir, dirs_exist_ok=True)
            else:
                os.makedirs(os.path.dirname(srcdir), exist_ok=True)
                shutil.copy2(dest, srcdir)
            rec["src"] = f"items/{it['id']}"
            rec["files"] = tree_hashes(dest)
        man["items"].append(rec)
    write_json(os.path.join(sd, "manifest.json"), man)
    return sd, man


def restore_snapshot(sd, say):
    man = read_json(os.path.join(sd, "manifest.json"), None)
    if not man:
        say(f"rollback: {sd}/manifest.json missing")
        return False
    roots = allowed_roots()
    qdir = os.path.join(reg.home(), f"rollback-removed-{time.strftime('%Y%m%d-%H%M%S')}")
    ok_all = True
    for it in man["items"]:
        dest = it["dest"]
        if roots is not None and not inside(dest, roots):
            say(f"rollback REFUSED for {it['id']}: {dest} is outside CLAUDE_HOME (scratch mode)")
            ok_all = False
            continue
        if not it.get("present"):
            if os.path.exists(dest):
                q = os.path.join(qdir, it["id"])
                os.makedirs(os.path.dirname(q), exist_ok=True)
                shutil.move(dest, q)
                say(f"rollback: {it['id']} did not exist before; moved to {q}")
            continue
        src = os.path.join(sd, it["src"])
        if it["kind"] == "file":
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if os.path.exists(dest) and sha256_file(dest) != it["files"][""]:
                os.makedirs(qdir, exist_ok=True)
                shutil.copy2(dest, os.path.join(qdir, it["id"] + ".replaced"))
            shutil.copy2(src, dest)
        else:
            os.makedirs(dest, exist_ok=True)
            want = set(it["files"])
            for rel in tree_hashes(dest):
                if rel not in want:
                    q = os.path.join(qdir, it["id"], rel)
                    os.makedirs(os.path.dirname(q), exist_ok=True)
                    shutil.move(os.path.join(dest, rel), q)
            for rel in want:
                s, d = os.path.join(src, rel), os.path.join(dest, rel)
                os.makedirs(os.path.dirname(d), exist_ok=True)
                if not os.path.exists(d) or sha256_file(d) != it["files"][rel]:
                    shutil.copy2(s, d)
            for dp, dns, fns in os.walk(dest, topdown=False):       # empty folders left by the moved files
                if dp != dest and not os.listdir(dp):
                    try:
                        os.rmdir(dp)
                    except OSError:
                        pass
        got = tree_hashes(dest)
        if got != it["files"]:
            say(f"rollback: {it['id']} does not match the snapshot after restore ({len(set(got) ^ set(it['files']))} difference(s))")
            ok_all = False
        else:
            say(f"rollback: {it['id']} restored ({len(it['files'])} file(s)) -> {dest}")
    return ok_all


def latest_snapshot():
    h = reg.home()
    try:
        c = sorted(n for n in os.listdir(h) if n.startswith("snapshot-") and os.path.isfile(os.path.join(h, n, "manifest.json")))
    except OSError:
        return None
    return os.path.join(h, c[-1]) if c else None


def default_items(plugin_src=None, plugin_cache=None, project_claude=None):
    ch = claude_home()
    items = [{"id": "settings", "dest": os.path.join(ch, "settings.json")}, {"id": "claude-md-home", "dest": os.path.join(ch, "CLAUDE.md")},
             {"id": "agents", "dest": os.path.join(ch, "agents")},
             # A3: `claude plugin update` rewrites these two; a rollback that leaves them names a plugin version that is gone
             {"id": "plugins-installed", "dest": os.path.join(ch, "plugins", "installed_plugins.json")},
             {"id": "plugins-marketplaces", "dest": os.path.join(ch, "plugins", "known_marketplaces.json")}]
    for i, p in enumerate(project_claude or []):
        items.append({"id": f"claude-md-project-{i + 1}", "dest": p})
    if plugin_src:
        items.append({"id": "plugin-src", "dest": plugin_src})
    if plugin_cache:
        items.append({"id": "plugin-cache", "dest": plugin_cache})
    return items


def cmd_rollback(rest):
    pos, o = parse_opts(rest, {"--snapshot", "--plugin-src", "--plugin-cache", "--project-claude", "--out"})
    if "--selftest" in o:
        return rollback_selftest()
    if "--create-snapshot" in o:
        pcs = [rest[i + 1] for i, a in enumerate(rest) if a == "--project-claude" and i + 1 < len(rest)]
        sd, man = create_snapshot(default_items(o.get("--plugin-src"), o.get("--plugin-cache"), pcs), o.get("--out"))
        out(f"snapshot written: {sd} ({sum(1 for i in man['items'] if i['present'])} of {len(man['items'])} items present)")
        return 0
    sd = o.get("--snapshot") or latest_snapshot()
    if not sd:
        out(f"rollback: no snapshot-<ts> directory under {reg.home()} (WP9 takes it before activation); out-of-band: install\\restore-pre-v4.cmd")
        return 1
    ok = restore_snapshot(sd, out)
    out("rollback: restore " + ("verified against the snapshot hashes" if ok else "INCOMPLETE"))
    rc = cmd_doctor(["--settings", "--agents"]) if ok else 1
    if ok and rc:
        out("rollback: doctor FAIL lines above are expected when the pre-v4 state is restored (it is not a v4 configuration)")
    return 0 if ok else 1


def rollback_selftest():
    fails = []
    with tempfile.TemporaryDirectory(prefix="gov4-rb-") as tmp:
        ch = os.path.join(tmp, "claude")
        saved = {k: os.environ.get(k) for k in ("CLAUDE_HOME", "NJ_HOME", "NJ_ROLLBACK_EXTRA_ROOTS")}
        os.environ["CLAUDE_HOME"] = ch
        os.environ["NJ_HOME"] = os.path.join(ch, "nj")
        os.environ["NJ_ROLLBACK_EXTRA_ROOTS"] = os.path.join(tmp, "ext")
        try:
            ext = os.path.join(tmp, "ext")
            files = {
                "claude/settings.json": json.dumps({"modelSettings": {"claude-opus-5-5": {"effortLevel": "xhigh"}}}),
                "claude/CLAUDE.md": "global v3\n", "claude/agents/sdlc-build.md": "---\nname: sdlc-build\nmodel: sonnet\n---\nv3\n",
                "claude/agents/old.md": "---\nname: old\nmodel: sonnet\n---\n",
                "claude/plugins/cache/nj-kit/nj-kit/1.3.5/skills/a.txt": "a135\n",
                "ext/nj-plugin/skills/nj-agent-ops/SKILL.md": "v3 skill\n", "ext/nj-plugin/skills/nj-agent-ops/scripts/relay.py": "v3 relay\n",
                "ext/project/CLAUDE.md": "project v3\n",
                "claude/plugins/installed_plugins.json": json.dumps({"plugins": {"nj-kit@nj-kit": [{"version": "1.3.5", "installPath": "cache/nj-kit/nj-kit/1.3.5"}]}}),
                "claude/plugins/known_marketplaces.json": json.dumps({"nj-kit": {"source": {"source": "directory", "path": "D:/x/nj-plugin"}}}),
            }
            for rel, txt in files.items():
                fp = os.path.join(tmp, rel)
                os.makedirs(os.path.dirname(fp), exist_ok=True)
                with open(fp, "w", encoding="utf-8", newline="\n") as f:
                    f.write(txt)
            os.makedirs(os.path.join(ch, "nj"), exist_ok=True)
            items = default_items(os.path.join(ext, "nj-plugin"), os.path.join(ch, "plugins", "cache", "nj-kit", "nj-kit"),
                                  [os.path.join(ext, "project", "CLAUDE.md")])
            before = {i["id"]: tree_hashes(i["dest"]) for i in items}
            sd, man = create_snapshot(items)
            # the activation
            write = lambda rel, txt: (os.makedirs(os.path.dirname(os.path.join(tmp, rel)), exist_ok=True),
                                      open(os.path.join(tmp, rel), "w", encoding="utf-8", newline="\n").write(txt))
            write("claude/settings.json", json.dumps({"hooks": {"x": 1}}))
            write("claude/CLAUDE.md", "global v4\n")
            write("claude/agents/sdlc-build.md", "v4\n")
            write("claude/agents/nj-agent.md", "new v4 agent\n")
            os.remove(os.path.join(ch, "agents", "old.md"))
            write("claude/plugins/cache/nj-kit/nj-kit/1.4.0/skills/a.txt", "a140\n")
            os.remove(os.path.join(ch, "plugins", "cache", "nj-kit", "nj-kit", "1.3.5", "skills", "a.txt"))
            write("ext/nj-plugin/skills/nj-agent-ops/SKILL.md", "v4 skill\n")
            write("ext/nj-plugin/skills/nj-agent-ops/scripts/gov4.py", "new\n")
            write("ext/project/CLAUDE.md", "project v4\n")
            write("claude/plugins/installed_plugins.json", json.dumps({"plugins": {"nj-kit@nj-kit": [{"version": "1.4.0", "installPath": "cache/nj-kit/nj-kit/1.4.0"}]}}))
            os.remove(os.path.join(ch, "plugins", "known_marketplaces.json"))
            msgs = []
            ok = restore_snapshot(sd, msgs.append)
            if not ok:
                fails.append("restore_snapshot returned False: " + "; ".join(msgs)[-300:])
            after = {i["id"]: tree_hashes(i["dest"]) for i in items}
            for k in before:
                if before[k] != after[k]:
                    fails.append(f"{k}: {len(set(before[k].items()) ^ set(after[k].items()))} difference(s) after rollback")
            ip = read_json(os.path.join(ch, "plugins", "installed_plugins.json"), {}) or {}
            if "1.3.5" not in json.dumps(ip) or not os.path.isfile(os.path.join(ch, "plugins", "known_marketplaces.json")):
                fails.append("A3: installed_plugins.json / known_marketplaces.json were not restored with the plugin cache")
            if not any(i["id"] == "plugins-installed" for i in items):
                fails.append("A3: default_items lacks the plugin registry files")
            removed = [n for n in os.listdir(os.path.join(ch, "nj")) if n.startswith("rollback-removed-")]
            if not removed:
                fails.append("nothing quarantined although v4 files were added")
            # a dest outside CLAUDE_HOME is refused in scratch mode
            man2 = json.loads(json.dumps(man))
            man2["items"][0]["dest"] = os.path.join(os.path.expanduser("~"), "gov4-selftest-must-not-exist.json")
            write_json(os.path.join(sd, "manifest.json"), man2)
            msgs2 = []
            if restore_snapshot(sd, msgs2.append) or os.path.exists(man2["items"][0]["dest"]):
                fails.append("scratch mode wrote outside CLAUDE_HOME")
            rc = cmd_doctor_quiet_scratch(ch)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    out("rollback selftest: " + ("ok (zero differences against the original)" if not fails else "FAILED"))
    for f in fails:
        out("  FAIL " + f)
    return 1 if fails else 0


def cmd_doctor_quiet_scratch(ch):
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return cmd_doctor(["--settings", "--agents", "--quiet"])


# ---------------------------------------------------------------- status ---

def cmd_status(rest):
    pos, o = parse_opts(rest, {"--project"})
    out(f"mode {reg.get_mode()} | wave {reg.get_wave()} | {reg.live_line()} | pause {'SET' if reg.paused() else 'clear'} | tickets {'checked' if reg.get_mode() == 'enforce' else 'not checked (enforce only)'}")
    root = resolve_project(o.get("--project"))
    if root:
        d = mq_dir(root)
        n = len([f for f in os.listdir(d) if f.endswith(".json")]) if os.path.isdir(d) else 0
        out(f"project {root}: {n} ticket(s) in the merge queue, branch {current_branch(root) or 'detached'}")
    cur = ""
    try:
        cur = open(os.path.join(reg.home(), "bin", "CURRENT"), encoding="utf-8").read().strip()
    except OSError:
        pass
    out(f"hooks bin/CURRENT: {cur or 'not installed'}")
    return 0


# --------------------------------------------------------------- selftest ---

class T:
    def __init__(self):
        self.fails = []
        self.n = 0

    def check(self, cond, label, detail=""):
        self.n += 1
        if not cond:
            self.fails.append(label)
            out(f"  FAIL {label}" + (f": {str(detail)[-400:]}" if detail else ""))
        return bool(cond)


def sh(cmd, cwd=None, env=None, timeout=300):
    return run(cmd, cwd=cwd, env=env, timeout=timeout)


def selftest_doctor(t):
    base = json.load(open(os.path.join(HERE, "..", "doctor-fixtures", "settings-v4-good.json"), encoding="utf-8"))

    def lv(s, area=None):
        return {(l, a) for l, a, m in doctor_settings(s) if (area is None or a == area)}

    def mut(fn):
        s = json.loads(json.dumps(base))
        fn(s)
        return s
    t.check(not any(l == "FAIL" for l, _, _ in doctor_settings(base)), "doctor: v4-good has no FAIL", [r for r in doctor_settings(base) if r[0] == "FAIL"])
    t.check(("FAIL", "effort") in lv(mut(lambda s: s["modelSettings"]["claude-opus-5-5"].update(effortLevel="xhigh"))), "doctor: xhigh fails")
    t.check(("PASS", "effort") in lv(base), "doctor: medium passes")
    t.check(("FAIL", "env-forbidden") in lv(mut(lambda s: s["env"].update(CLAUDE_CODE_EFFORT_LEVEL="high"))), "doctor: EFFORT_LEVEL fails")
    t.check(("FAIL", "env-forbidden") in lv(mut(lambda s: s["env"].update(CLAUDE_CODE_SUBAGENT_MODEL_FORCE="opus"))), "doctor: SUBAGENT_MODEL_FORCE fails")
    t.check(("FAIL", "env-forbidden") in lv(mut(lambda s: s["env"].update(CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS="1"))), "doctor: AGENT_TEAMS fails")
    t.check(("FAIL", "ultracode") in lv(mut(lambda s: s.update(ultracode=True))), "doctor: ultracode fails")
    t.check(("FAIL", "env-required") in lv(mut(lambda s: s["env"].pop("CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS"))), "doctor: missing env key fails")
    t.check(("FAIL", "env-required") in lv(mut(lambda s: s["env"].update(CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS="500"))), "doctor: wrong env value fails")
    for m in ("bypassPermissions", "acceptEdits", "auto"):
        t.check(("WARN", "permission-mode") in lv(mut(lambda s, m=m: s["permissions"].update(defaultMode=m))), f"doctor: {m} is WARN (D2)")
    t.check(not any(l == "FAIL" for l, a, _ in doctor_settings(mut(lambda s: s["permissions"].update(defaultMode="bypassPermissions"))) if a == "permission-mode"), "doctor: bypass is never FAIL")
    t.check(("FAIL", "hooks") in lv(mut(lambda s: s["hooks"].pop("PreToolUse"))), "doctor: hooks not wired fails")
    t.check(("FAIL", "worktree-hooks") in lv(mut(lambda s: s["hooks"].update(WorktreeCreate=[]))), "doctor: WorktreeCreate fails")
    t.check(("FAIL", "deny-rules") in lv(mut(lambda s: s["permissions"].update(deny=[]))), "doctor: no deny rules fails")
    t.check(("FAIL", "settings") in lv({}), "doctor: empty settings fails")
    v3 = json.load(open(os.path.join(HERE, "..", "doctor-fixtures", "settings-v3.json"), encoding="utf-8"))
    t.check(any(l == "FAIL" for l, _, _ in doctor_settings(v3)), "doctor: the v3 fixture fails")
    # agent lint
    with tempfile.TemporaryDirectory(prefix="gov4-ag-") as d:
        def w(n, txt):
            open(os.path.join(d, n + ".md"), "w", encoding="utf-8", newline="\n").write(txt)
        w("nj-helper-reader", "---\nname: nj-helper-reader\nmodel: haiku\ntools: Read, Grep\ndisallowedTools: Agent, SendMessage\n---\nx\n")
        t.check(all(l == "PASS" for l, _, _ in lint_agents(d)), "lint: good helper passes", lint_agents(d))
        w("nj-helper-reader", "---\nname: nj-helper-reader\nmodel: opus\n---\nx\n")
        t.check(lint_agents(d)[0][0] == "FAIL", "lint: opus fails")
        w("nj-helper-reader", "---\nname: nj-helper-reader\nmodel: inherit\n---\nx\n")
        t.check(lint_agents(d)[0][0] == "FAIL", "lint: inherit fails")
        w("nj-helper-reader", "---\nname: nj-helper-reader\ntools: Read, Agent\nmodel: haiku\n---\nx\n")
        t.check(lint_agents(d)[0][0] == "FAIL", "lint: helper with Agent fails")
        w("nj-helper-reader", "---\nname: nj-helper-reader\nmodel: haiku\nisolation: worktree\ndisallowedTools: Agent, SendMessage\n---\nx\n")
        t.check(lint_agents(d)[0][0] == "FAIL", "lint: isolation key fails")
        w("nj-helper-reader", "---\nname: nj-helper-reader\nmodel: haiku\ndisalowedTools: Agent\ndisallowedTools: Agent, SendMessage\n---\nx\n")
        t.check(lint_agents(d)[0][0] == "FAIL", "lint: misspelt key fails")
        w("nj-helper-reader", "---\nname: nj-helper-reader\n---\nx\n")
        t.check(lint_agents(d)[0][0] == "FAIL", "lint: missing model fails")
    adir = os.path.abspath(os.path.join(HERE, "..", "..", "..", "agents"))
    if os.path.isdir(adir):
        bad = [r for r in lint_agents(adir) if r[0] == "FAIL"]
        t.check(not bad, "lint: the 11 staged agent definitions pass", bad)
    # cache trio
    with tempfile.TemporaryDirectory(prefix="gov4-ca-") as d:
        def mk(root, content, nested=False, ver="1.4.0"):
            for rel in ROOT_FILES[:4]:
                fp = os.path.join(root, rel)
                os.makedirs(os.path.dirname(fp), exist_ok=True)
                open(fp, "w", encoding="utf-8", newline="\n").write(content + rel)
            fp = os.path.join(root, ".claude-plugin", "marketplace.json")
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            json.dump({"plugins": [{"name": "nj-kit", "version": ver}]}, open(fp, "w"))
            if nested:
                os.makedirs(os.path.join(root, "nj-plugin", "skills"), exist_ok=True)
        src, cache, kit = (os.path.join(d, x) for x in ("src", "cache", "kit"))
        for r in (src, cache, kit):
            mk(r, "same")
        t.check(not any(l == "FAIL" for l, _, _ in doctor_cache(src, cache, kit)), "cache: equal trio passes", doctor_cache(src, cache, kit))
        open(os.path.join(cache, ROOT_FILES[0]), "w").write("stale")
        t.check(any(l == "FAIL" and a == "hash" for l, a, _ in doctor_cache(src, cache, kit)), "cache: hash mismatch fails")
        mk(cache, "same")
        mk(cache, "same", ver="1.3.5")
        t.check(any(l == "FAIL" and a == "version" for l, a, _ in doctor_cache(src, cache, kit)), "cache: version mismatch fails")
        mk(cache, "same")
        mk(src, "same", nested=True)
        t.check(any(l == "FAIL" and a == "nested" for l, a, _ in doctor_cache(src, cache, kit)), "cache: nested stale copy fails")
    # tags
    t.check(parse_tags("- **0.11 gates** [GATE: gov4.py]\n- 0.1 lead [HABIT]\n- 0.10 review [HABIT]\n").get("0.1") == ("HABIT", "")
            and parse_tags("0.11 x [GATE: gov4.py]").get("0.11") == ("GATE", "gov4.py"), "tags: parser separates 0.1 from 0.10/0.11")
    with tempfile.TemporaryDirectory(prefix="gov4-tg-") as d:
        sk = os.path.join(d, "skills", "nj-agent-ops")
        os.makedirs(os.path.join(sk, "templates"))
        os.makedirs(os.path.join(sk, "scripts"))
        os.makedirs(os.path.join(sk, "smoke"))
        os.makedirs(os.path.join(d, "skills", "nj-delegate"))
        open(os.path.join(sk, "scripts", "gov4.py"), "w").write("x")
        json.dump({"clauses": {"0.11": {"smoke": ["S3"], "mutants": ["M-a", "M-b"]}}}, open(os.path.join(sk, "templates", "clause-deps.json"), "w"))
        open(os.path.join(d, "skills", "nj-delegate", "SKILL.md"), "w").write("nj-governance-v4\n0.11 gates never cut [GATE: gov4.py]\n")
        r = doctor_tags(d)
        t.check(any(l == "FAIL" and a == "clause 0.11" for l, a, _ in r), "tags: GATE without attested PASS/mutants fails", r)
        os.makedirs(os.path.join(d, "skills", "tests"))
        json.dump({"killed": ["M-a", "M-b"]}, open(os.path.join(d, "skills", "tests", "MUTATION.json"), "w"))
        r = doctor_tags(d)
        t.check(any(l == "FAIL" and a == "clause 0.11" and "attested" in m for l, a, m in r) and not any("mutant" in m for l, a, m in r if a == "clause 0.11"),
                "tags: killed mutants clear the mutant part, smoke still needs attestation", r)
        t.check(any("guarded_sha256" in m for l, a, m in r if a == "clause 0.11"), "TV-2: mutation evidence without guarded_sha256 is not bound and the GATE tag says so", r)
        gp = os.path.join(d, "skills", "tests", "MUTATION.json")
        gsha = sha256_file(os.path.join(sk, "scripts", "gov4.py"))
        json.dump({"killed": ["M-a", "M-b"], "guarded_sha256": {"skills/nj-agent-ops/scripts/gov4.py": gsha}}, open(gp, "w"))
        t.check(evidence_binding(gp, d)[0] and not any("guarded" in m or "older" in m for l, a, m in doctor_tags(d) if a == "clause 0.11"),
                "TV-2: evidence whose guarded hashes match the code is bound")
        open(os.path.join(sk, "scripts", "gov4.py"), "w").write("x changed after the mutation run")
        r = doctor_tags(d)
        t.check(any(l == "FAIL" and a == "clause 0.11" and "older than the code" in m for l, a, m in r) and not evidence_binding(gp, d)[0],
                "TV-2: editing a guarded file after the run voids the GATE tag", r)
        open(os.path.join(sk, "scripts", "gov4.py"), "w").write("x")
        json.dump({"killed": ["M-a", "M-b"], "guarded_sha256": {"../escape.py": gsha}}, open(gp, "w"))
        t.check(not evidence_binding(gp, d)[0], "TV-2: a guarded path outside the plugin root is refused")
    t.check(mutation_status_selftest(), "tags: MUTATION.json shapes")
    real_smoke = os.path.abspath(os.path.join(HERE, "..", "smoke"))
    if os.path.isfile(os.path.join(real_smoke, "run_smoke.py")):
        with tempfile.TemporaryDirectory(prefix="gov4-sa-") as d:
            sk = os.path.join(d, "skills", "nj-agent-ops")
            os.makedirs(os.path.join(sk, "templates"))
            os.makedirs(os.path.join(sk, "scripts"))
            os.makedirs(os.path.join(d, "skills", "nj-delegate"))
            os.makedirs(os.path.join(d, "skills", "tests"))
            shutil.copytree(real_smoke, os.path.join(sk, "smoke"), ignore=shutil.ignore_patterns("__pycache__"))
            open(os.path.join(sk, "scripts", "gov4.py"), "w").write("x")
            json.dump({"clauses": {"0.11": {"smoke": ["S3"], "mutants": ["M-a"]}}}, open(os.path.join(sk, "templates", "clause-deps.json"), "w"))
            open(os.path.join(d, "skills", "nj-delegate", "SKILL.md"), "w").write("nj-governance-v4\n0.11 gates never cut [GATE: gov4.py]\n")
            json.dump({"killed": ["M-a"], "guarded_sha256": {"skills/nj-agent-ops/scripts/gov4.py": sha256_file(os.path.join(sk, "scripts", "gov4.py"))}},
                      open(os.path.join(d, "skills", "tests", "MUTATION.json"), "w"))
            os.environ["NJ_SMOKE_DIR"] = os.path.join(sk, "smoke")
            try:
                buf = []
                rc = cmd_smoke_attest([])
            finally:
                os.environ.pop("NJ_SMOKE_DIR", None)
            t.check(rc == 0 and os.path.isfile(os.path.join(sk, "smoke", "ATTEST.json")), "smoke-attest writes ATTEST.json for a verified RESULTS.md")
            r = doctor_tags(d)
            t.check(any(l == "PASS" and a == "clause 0.11" for l, a, _ in r), "tags: GATE with attested PASS and killed mutant passes", r)
            rp = os.path.join(sk, "smoke", "RESULTS.md")
            txt = open(rp, encoding="utf-8").read()
            open(rp, "w", encoding="utf-8", newline="\n").write(txt.replace("S3 PASS", "S3 PASS ", 1))
            r = doctor_tags(d)
            t.check(any(l == "FAIL" and a == "clause 0.11" for l, a, _ in r) and any(l == "FAIL" and a == "smoke-chain" for l, a, _ in r),
                    "tags: a hand-edited RESULTS.md voids the attestation", r)
            os.environ["NJ_SMOKE_DIR"] = os.path.join(sk, "smoke")
            try:
                rc = cmd_smoke_attest([])
            finally:
                os.environ.pop("NJ_SMOKE_DIR", None)
            t.check(rc == 1, "smoke-attest refuses a hand-edited RESULTS.md")


def mutation_status_selftest():
    with tempfile.TemporaryDirectory(prefix="gov4-mu-") as d:
        p = os.path.join(d, "m.json")
        json.dump({"mutants": {"a": {"killed": True}, "b": "survived", "c": "killed"}}, open(p, "w"))
        r = mutation_status(p)
        json.dump({"killed": ["x"], "survived": ["y"]}, open(p, "w"))
        r2 = mutation_status(p)
        return r == {"a": True, "b": False, "c": True} and r2 == {"x": True, "y": False}


def selftest_infra(t, tmp):
    """Mode, wave, unlock, tickets, install-bin, live, enforce-ready, smoke attest on a scratch NJ_HOME."""
    nj = os.path.join(tmp, "nj")
    os.makedirs(nj, exist_ok=True)
    env = dict(os.environ, NJ_HOME=nj, PYTHONUTF8="1")
    env.pop("NJ_MODE_OVERRIDE", None)
    env.pop("NJ_TICKET", None)
    me = [sys.executable, "-X", "utf8", os.path.abspath(__file__)]
    old = os.environ.get("NJ_HOME")
    os.environ["NJ_HOME"] = nj
    reg.set_mode("enforce")          # D27: tickets are checked only in enforce; the ticket tests below run there

    def g(args, ticket=False, e=None, cwd=None):
        ev = dict(env)
        ev.update(e or {})
        if ticket:
            ev["NJ_TICKET"] = reg.mint_ticket(args) or ""
        return sh(me + args, cwd=cwd, env=ev)
    try:
        rc, so, se = g(["mode", "enforce"], ticket=True)
        t.check(rc == 1 and "REFUSED" in so, "mode enforce refused while enforce-ready fails", so + se)
        rc, so, se = g(["mode", "off"])
        t.check(rc == 3, "ticket: write subcommand without a ticket refused (rc 3)", so + se)
        rc, so, se = g(["mode", "off"], ticket=True)
        t.check(rc == 0 and reg.get_mode() == "off", "ticket: a valid ticket is accepted", so + se)
        rc, so, se = g(["mode", "audit"])
        t.check(rc == 0 and reg.get_mode() == "audit", "mode off: hooks inert, so no ticket needed to leave it")
        # A1 / D27: in audit gov4.py logs a would-refuse and proceeds; WP9 (a Lead session with no hooks) must be able to run
        for argv in (["wave", "5"], ["install-bin"], ["mode", "audit"]):
            rc, so, se = g(argv)
            t.check(rc == 0, f"A1: in audit `{' '.join(argv)}` runs without a ticket", so + se)
        try:
            dec = open(os.path.join(nj, "events.jsonl"), encoding="utf-8").read()
        except OSError:
            dec = ""
        t.check('"ticket-would-refuse"' in dec, "A1: audit logs the would-refuse (events.jsonl)", dec[-300:])
        reg.set_mode("off")
        rc, so, se = g(["wave", "10"])
        t.check(rc == 0, "A1: in off nothing is checked", so + se)
        reg.set_mode("enforce")
        rc, so, se = g(["wave", "10"])
        t.check(rc == 3, "A1: enforce still refuses a write without a ticket", so + se)
        tk = reg.mint_ticket(["wave", "5"])
        rc, so, se = g(["wave", "10"], e={"NJ_TICKET": tk})
        t.check(rc == 3, "ticket: bound to the argv hash", so + se)
        rc, so, se = g(["wave", "5"], e={"NJ_TICKET": tk})
        t.check(rc == 0, "ticket: the right argv passes", so + se)
        rc, so, se = g(["wave", "5"], e={"NJ_TICKET": tk})
        t.check(rc == 3, "ticket: single use", so + se)
        pair = f"{reg.mint_ticket(['wave', '5'])},{reg.mint_ticket(['wave', '5'])}"
        rc1 = g(["wave", "5"], e={"NJ_TICKET": pair})[0]
        rc2 = g(["wave", "5"], e={"NJ_TICKET": pair})[0]
        t.check(rc1 == 0 and rc2 == 3, "ticket: two nonces minted for one command cannot be replayed", (rc1, rc2))
        rc, so, se = g(["wave", "20", "--project", tmp], ticket=True, e={"NJ_RELAY": os.path.join(tmp, "nofile.py")})
        t.check(rc == 1 and "REFUSED" in so, "wave 20 refused without a clean peak-10 verify", so + se)
        fake = os.path.join(tmp, "fake_relay.py")
        open(fake, "w").write("import sys\nprint('peak live subagents: 11 (operating cap 10)')\nprint('429/529 incidents: 0 (target 0)')\nsys.exit(0)\n")
        rc, so, se = g(["wave", "20", "--project", tmp], ticket=True, e={"NJ_RELAY": fake})
        t.check(rc == 0 and reg.get_wave() == 20, "wave 20 allowed after a clean run at peak >= 10 and 0 incidents (D4)", so + se)
        open(fake, "w").write("import sys\nprint('peak live subagents: 12')\nprint('429/529 incidents: 1 BREACH')\nsys.exit(1)\n")
        rc, so, se = g(["wave", "20", "--project", tmp], ticket=True, e={"NJ_RELAY": fake})
        t.check(rc == 1, "wave 20 refused with a rate-limit incident", so + se)
        rc, so, se = g(["wave", "10"], ticket=True)
        t.check(rc == 0 and reg.get_wave() == 10, "wave 10 allowed")
        rc, so, se = g(["unlock", "--minutes", "500", "--reason", "selftest"], ticket=True)
        t.check(rc == 0 and reg.unlock_valid(), "unlock written and valid", so + se)
        d = read_json(os.path.join(nj, "unlock.json"), {})
        t.check(d.get("minutes") == 60 and d["expires_ts"] - time.time() <= 3601, "unlock TTL capped at one hour", d)
        rc, so, se = g(["unlock", "--revoke"], ticket=True)
        t.check(rc == 0 and not reg.unlock_valid(), "unlock revoked")
        # live passthrough
        rc, so, se = g(["live", "acquire", "--job", "--ttl-min", "5", "--name", "selftest"])
        jid = (json.loads(so.strip().splitlines()[-1]).get("id") if rc == 0 else None)
        t.check(rc == 0 and jid, "live acquire hands out a job slot, exit 0", so + se)
        rc, so, se = g(["live", "heartbeat", "--id", jid or "x"])
        t.check(rc == 0, "live heartbeat exit 0")
        rc, so, se = g(["live", "release", jid or "x"])
        t.check(rc == 0, "live release exit 0")
        write_text(os.path.join(nj, "wave"), "5\n")
        ids = []
        for i in range(5):
            r_ = g(["live", "acquire", "--job", "--ttl-min", "5"])
            ids.append(r_[0])
        rc, so, se = g(["live", "acquire", "--job", "--ttl-min", "5"])
        t.check(ids == [0] * 5 and rc == 75, "live acquire exits 75 when the operating cap is reached", (ids, rc, so))
        rc, so, se = g(["live", "--pause", "selftest"])
        t.check(rc == 3, "live --pause needs a ticket")
        rc, so, se = g(["live", "--pause", "selftest"], ticket=True)
        t.check(rc == 0 and reg.paused(), "live --pause sets pause.flag", so + se)
        rc, so, se = g(["live", "--resume"], ticket=True)
        t.check(rc == 0 and not reg.paused(), "live --resume clears pause.flag")
        plain2 = os.path.join(tmp, "plain-sweep")
        os.makedirs(plain2)
        rc, so, se = g(["sweep", plain2], ticket=True)
        t.check(rc == 0 and "0 leftover" in so, "sweep: a clean non-git folder exits 0", so + se)
        g(["live", "--pause", "x"], ticket=True)
        rc, so, se = g(["sweep", plain2], ticket=True)
        t.check(rc == 1 and "pause.flag" in so, "sweep: a pause flag is a leftover (exit 1)", so)
        g(["live", "--resume"], ticket=True)
        reg.convert("agent-selftest-1", "nj-agent", "sess-1", "", plain2)
        rc, so, se = g(["sweep", plain2], ticket=True)
        t.check(rc == 1 and "live agent" in so, "sweep: a live registry entry is a leftover (exit 1)", so)
        reg.release("agent-selftest-1", plain2)
        # enforce-ready
        rc, so, se = g(["enforce-ready"])
        t.check(rc == 1 and "NOT READY" in so, "enforce-ready: not ready by default", so)
        for item in ("wp8", "job_e2e", "decisions"):
            g(["enforce-ready", "--record", item], ticket=True)
        write_text(os.path.join(nj, "audit-since"), time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time() - 30 * 3600)) + "\n")
        rc, so, se = g(["enforce-ready"])
        t.check(rc == 0 and "READY" in so, "enforce-ready: ready with a day of audit and all evidence", so + se)
        rc, so, se = g(["mode", "enforce"], ticket=True)
        t.check(rc == 0 and reg.get_mode() == "enforce", "mode enforce allowed once enforce-ready passes", so + se)
        rc, so, se = g(["mode", "audit"], ticket=False)
        t.check(rc == 3, "ticket: leaving enforce needs a ticket too", so + se)
        reg.set_mode("audit")
        # install-bin
        rc, so, se = g(["install-bin"], ticket=True)
        t.check(rc == 0 and "CURRENT=" in so, "install-bin copies hooks to bin/<sha8> and writes CURRENT", so + se)
        cur = open(os.path.join(nj, "bin", "CURRENT")).read().strip()
        t.check(os.path.isfile(os.path.join(nj, "bin", cur, "gov4_hook.py")) and os.path.isfile(os.path.join(nj, "bin", cur, "githooks", "pre-push")), "install-bin: hook files present")
        t.check(os.path.isfile(os.path.join(nj, "gov4_launcher.py")) and os.path.isfile(os.path.join(nj, "gov4_hook.py"))
                and os.path.isfile(os.path.join(nj, "gov4_registry.py")), "install-bin: launcher, hook and registry sit together in the state root (H8)")
        rc, so, se = sh([sys.executable, "-I", "-X", "utf8", os.path.join(nj, "gov4_launcher.py"), "--selftest"], env=dict(env, NJ_HOME=nj), timeout=60)
        t.check(rc == 0, "install-bin: the installed launcher passes its own selftest on a scratch home (H8)", so + se)
        rc, so, se = g(["install-bin"], ticket=True)
        t.check(rc == 0 and "0 written" in so and open(os.path.join(nj, "bin", "CURRENT")).read().strip() == cur, "install-bin idempotent", so)
        rc, so, se = g(["status"])
        t.check(rc == 0 and "mode audit" in so, "status prints", so + se)
        # snapshot via gov4 (non-git) with ticket
        reg.set_mode("enforce")
        proj = os.path.join(tmp, "plain")
        os.makedirs(os.path.join(proj, "src"))
        open(os.path.join(proj, "src", "a.txt"), "w").write("a")
        ev = {"NJ_SOURCES_DIR": os.path.join(tmp, "_sources"), "NJ_SHADOW_DIR": os.path.join(tmp, "_shadow")}
        rc, so, se = g(["snapshot", "begin", proj, "--run", "r9"], e=ev)
        t.check(rc == 3, "snapshot begin needs a ticket", so + se)
        rc, so, se = g(["snapshot", "begin", proj, "--run", "r9"], ticket=True, e=ev)
        t.check(rc == 0, "snapshot begin through gov4.py", so + se)
        rc, so, se = g(["snapshot", "diff", proj, "--run", "r9"], e=ev)
        t.check(rc == 0 and "empty change set" in so, "snapshot diff is read-only and sees an empty change set", so + se)
        rc, so, se = g(["snapshot", "commit", proj, "--run", "r9"], ticket=True, e=ev)
        t.check(rc == 0 and "no-op" in so, "snapshot commit of an empty run is a no-op", so + se)
        # smoke-attest on a scratch copy of the smoke dir is covered by the real one in the acceptance run
    finally:
        if old is None:
            os.environ.pop("NJ_HOME", None)
        else:
            os.environ["NJ_HOME"] = old


def selftest_h2(t, tmp):
    """Hardening round H2: D20 settings split, install-settings, doctor --against, D26 interpreter check, D27 env trust,
    SB-14, CD-5, A7 restore script. Runs on scratch state roots only."""
    import io
    import contextlib
    fxdir = os.path.join(HERE, "..", "doctor-fixtures")

    def fx(n):
        return json.load(open(os.path.join(fxdir, n), encoding="utf-8"))

    def cap(fn, *a):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = fn(*a)
        return rc, buf.getvalue()
    nj = os.path.join(tmp, "nj")
    os.makedirs(nj, exist_ok=True)
    old_home = os.environ.get("NJ_HOME")
    os.environ["NJ_HOME"] = nj
    me = [sys.executable, "-X", "utf8", os.path.abspath(__file__)]

    def gm(args, ticket=False, e=None, drop=()):
        ev = dict(os.environ, PYTHONUTF8="1")
        for k in drop:
            ev.pop(k, None)
        ev.update(e or {})
        if ticket:
            ev["NJ_TICKET"] = reg.mint_ticket(args) or ""
        return sh(me + args, env=ev)
    gl = globals()
    real_tty = gl["human_tty"]
    try:
        # ---- D27 / SB-02 / SB-03: who may redirect state ----
        saved = {k: os.environ.get(k) for k in ENV_OVERRIDES + ("NJ_GOV4_SELFTEST", "NJ_ROLE")}
        gl["human_tty"] = lambda: False
        try:
            os.environ.pop("NJ_GOV4_SELFTEST", None)
            for k in ENV_OVERRIDES:
                os.environ[k] = "x"
            dropped = sanitize_env()
            t.check(set(dropped) == set(ENV_OVERRIDES) and not any(os.environ.get(k) for k in ENV_OVERRIDES),
                    "D27: an unmarked non-terminal caller loses NJ_MODE_OVERRIDE, NJ_TICKETS, NJ_HOME, CLAUDE_HOME, NJ_ROLES_JSON", dropped)
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            os.environ["NJ_MODE_OVERRIDE"] = "audit"
            t.check(env_trusted() and sanitize_env() == [] and os.environ.get("NJ_MODE_OVERRIDE") == "audit", "D27: a marked scratch run keeps its overrides")
            os.environ["NJ_ROLE"] = "job"
            t.check(not env_trusted(), "D27: a job is never trusted, marker or not")
            os.environ.pop("NJ_ROLE")
            gl["human_tty"] = lambda: True
            t.check(env_trusted(), "D27: a human at a terminal is trusted")
            os.environ["NJ_ROLE"] = "job"
            t.check(not env_trusted(), "D27: a job at a terminal is still a job")
        finally:
            gl["human_tty"] = real_tty
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            os.environ["NJ_HOME"] = nj
        # end to end: scratch HOME is the default state root; the caller sets every override and no marker
        fh = os.path.join(tmp, "fakehome")
        fnj = os.path.join(fh, ".claude", "nj")
        os.makedirs(fnj, exist_ok=True)
        write_text(os.path.join(fnj, "mode"), "enforce\n")
        evx = {"HOME": fh, "USERPROFILE": fh, "NJ_MODE_OVERRIDE": "off", "NJ_TICKETS": "habit", "NJ_HOME": os.path.join(tmp, "elsewhere"),
               "CLAUDE_HOME": os.path.join(tmp, "elsewhere2")}
        drop = ("NJ_GOV4_SELFTEST", "NJ_TICKET")
        rc, so, se = gm(["mode", "off"], e=evx, drop=drop)
        t.check(rc == 3 and open(os.path.join(fnj, "mode")).read().strip() == "enforce",
                "SB-03/D27: NJ_MODE_OVERRIDE=off + NJ_TICKETS=habit + a redirected NJ_HOME do not switch enforce off", so + se)
        evj = dict(evx, NJ_ROLE="job", NJ_GOV4_SELFTEST="1")
        rc, so, se = gm(["mode", "off"], e=evj, drop=("NJ_TICKET",))
        t.check(rc == 3 and open(os.path.join(fnj, "mode")).read().strip() == "enforce", "D27: a job cannot switch enforce off either", so + se)
        write_text(os.path.join(fnj, "tickets-mode"), "habit\n")
        rc, so, se = gm(["wave", "5"], e={"HOME": fh, "USERPROFILE": fh}, drop=("NJ_GOV4_SELFTEST", "NJ_TICKET", "NJ_HOME", "CLAUDE_HOME"))
        t.check(rc == 3, "SB-03: the tickets-mode 'habit' file no longer disables the ticket check in enforce", so + se)
        os.remove(os.path.join(fnj, "tickets-mode"))
        write_text(os.path.join(fnj, "mode"), "audit\n")
        rc, so, se = gm(["wave", "5"], e={"HOME": fh, "USERPROFILE": fh}, drop=("NJ_GOV4_SELFTEST", "NJ_TICKET", "NJ_HOME", "CLAUDE_HOME"))
        t.check(rc == 0 and "ticket-would-refuse" in open(os.path.join(fnj, "events.jsonl"), encoding="utf-8").read(),
                "A1: audit mode, no hooks, no ticket: the write runs and the would-refuse is logged", so + se)
        # in enforce a tickets-mode habit file does nothing even for a marked run
        reg.set_mode("enforce")
        write_text(os.path.join(nj, "tickets-mode"), "habit\n")
        rc, so, se = gm(["wave", "5"], e={"NJ_TICKETS": "habit"})
        os.remove(os.path.join(nj, "tickets-mode"))
        t.check(rc == 3, "SB-03: NJ_TICKETS=habit and the habit file are ignored by gov4.py in enforce", so + se)
        # on Windows os.isatty() is true for NUL: `</dev/null >/dev/null` must not pass for a human at a terminal
        r_ = subprocess.run(me + ["wave", "5"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=dict(os.environ, PYTHONUTF8="1"))
        t.check(r_.returncode == 3, "D27: stdin and stdout redirected to the null device are not a terminal (enforce still refuses)", r_.returncode)
        # ---- SB-14: unlock parses its arguments before it writes ----
        up = os.path.join(nj, "unlock.json")
        rc, o_ = cap(cmd_unlock, ["--help"])
        t.check(rc == 0 and not os.path.exists(up) and "usage" in o_, "SB-14: unlock --help prints usage and writes nothing", o_)
        rc, o_ = cap(cmd_unlock, ["bogus"])
        t.check(rc == 2 and not os.path.exists(up), "SB-14: unlock with a stray argument writes nothing", o_)
        rc, o_ = cap(cmd_unlock, ["--nope"])
        t.check(rc == 2 and not os.path.exists(up), "SB-14: unlock with an unknown flag writes nothing", o_)
        rc, o_ = cap(cmd_unlock, ["--minutes", "5", "--reason", "selftest"])
        t.check(rc == 0 and os.path.exists(up), "SB-14: a valid unlock still writes", o_)
        cap(cmd_unlock, ["--revoke"])
        # ---- D20: audit shape vs enforce shape ----
        good, enf, pre0 = fx("settings-v4-good.json"), fx("settings-v4-enforce.json"), fx("settings-pre-v4.json")

        def lvl(s, mode, area=None, **kw):
            return {(l, a) for l, a, m in doctor_settings(s, mode=mode, **kw) if area is None or a == area}
        t.check(not any(r in DENY_AUDIT for r in DENY_ENFORCE) and all(a in good["permissions"]["deny"] for a in DENY_AUDIT)
                and not any(r in good["permissions"]["deny"] for r in DENY_ENFORCE), "D20: the audit fixture carries the model and secret denies and no git or gh deny")
        t.check(not any(l == "FAIL" for l, _ in lvl(good, "audit")), "D20: the audit fixture passes the audit doctor")
        t.check(not any(l == "FAIL" for l, _ in lvl(enf, "enforce")), "D20: the enforce fixture passes the enforce doctor", [r for r in doctor_settings(enf, mode="enforce") if r[0] == "FAIL"])
        t.check(("FAIL", "deny-rules") in lvl(good, "enforce") and ("FAIL", "agent-onfailure") in lvl(good, "enforce"), "D20/D26: the audit shape fails the enforce doctor (git denies and onFailure missing)")
        t.check(("WARN", "deny-rules-git") in lvl(enf, "audit") and ("WARN", "agent-onfailure") in lvl(enf, "audit") and not any(l == "FAIL" for l, _ in lvl(enf, "audit")),
                "D20/D26: git denies and onFailure in audit mode are a WARN (they would block the Lead / spawns)")
        # ---- D26: the pinned interpreter really runs the launcher selftest ----
        launcher = norm(os.path.join(HERE, "gov4_launcher.py"))

        def with_cmd(py, lau, base=good):
            s = json.loads(json.dumps(base))
            for ev, groups in s["hooks"].items():
                for g_ in groups:
                    for h in g_["hooks"]:
                        sub = launcher_sub(h["command"])
                        if sub:       # the D26 guard form of the fragment
                            h["command"] = (f'"{py}" -I -X utf8 -c "import os,sys,runpy;p=\'{lau}\';sys.argv=[p,\'{sub}\'];'
                                            f'os.path.isfile(p) and runpy.run_path(p,run_name=\'__main__\')"')
            return s
        if os.path.isfile(launcher):
            r = {(l, a) for l, a, m in doctor_settings(with_cmd(norm(sys.executable), launcher), real=True, mode="audit", lead_mode=None)}
            t.check(("PASS", "hooks-interpreter") in r and ("FAIL", "hooks-interpreter") not in r, "D26: a real interpreter that runs the launcher selftest passes", r)
            r = {(l, a) for l, a, m in doctor_settings(with_cmd(norm(os.path.join(tmp, "no-such-python.exe")), launcher), real=True, mode="audit", lead_mode=None)}
            t.check(("FAIL", "hooks-interpreter") in r, "D26: a pinned interpreter that does not exist fails")
            ws = "C:/Profiles/x/AppData/Local/Microsoft/WindowsApps/python.exe"
            r = {(l, a) for l, a, m in doctor_settings(with_cmd(ws, launcher), mode="audit", lead_mode=None)}
            t.check(("FAIL", "hooks-interpreter") in r, "D26: the WindowsApps stub is refused (even in a settings file)")
            os.makedirs(os.path.join(tmp, "stub"), exist_ok=True)
            write_text(os.path.join(tmp, "stub", "gov4_launcher.py"), "import sys\nsys.exit(3)\n")
            r = {(l, a) for l, a, m in doctor_settings(with_cmd(norm(sys.executable), norm(os.path.join(tmp, "stub", "gov4_launcher.py"))), real=True, mode="audit", lead_mode=None)}
            t.check(("FAIL", "hooks-interpreter") in r, "D26: an interpreter that cannot run the launcher selftest fails")
            r = {(l, a) for l, a, m in doctor_settings(with_cmd(norm(sys.executable), norm(os.path.join(tmp, "missing", "gov4_launcher.py"))), real=True, mode="audit", lead_mode=None)}
            t.check(("WARN", "hooks-launcher") in r and not any(l == "FAIL" for l, a in r if a == "hooks-launcher"), "D26: a missing launcher is a WARN in audit (hooks fail open)")
            r = {(l, a) for l, a, m in doctor_settings(with_cmd(norm(sys.executable), norm(os.path.join(tmp, "missing", "gov4_launcher.py")), base=enf), real=True, mode="enforce", lead_mode=None)}
            t.check(("FAIL", "hooks-launcher") in r, "D26: a missing launcher is a FAIL in enforce")
        t.check(launcher_sub('C:/Py/python.exe -I -X utf8 C:/n/gov4_launcher.py agent') == "agent" and launcher_sub('"C:/P y/python.exe" -I "C:/n/gov4_launcher.py" git') == "git"
                and launcher_sub("python -c \"guard\" C:/n/gov4_launcher.py stop-team") == "stop-team" and launcher_sub("python x.py hook") is None, "launcher_sub reads quoted, unquoted and guard-wrapped commands")
        i_, l_ = split_command('"C:/P y/python.exe" -I -X utf8 "C:/n m/gov4_launcher.py" git')
        t.check(i_ == "C:/P y/python.exe" and l_ == "C:/n m/gov4_launcher.py", "split_command handles quoted paths with spaces", (i_, l_))
        # ---- CD-5: the real permission mode ----
        t.check(("WARN", "permission-mode") in lvl(good, "audit", "permission-mode", lead_mode=None), "CD-5: unknown permission mode is a WARN")
        t.check(("WARN", "permission-mode") in lvl(good, "audit", "permission-mode", lead_mode=("bypassPermissions", "Lead registration abc")), "CD-5: a bypass Lead is a WARN")
        t.check(("PASS", "permission-mode") in lvl(good, "audit", "permission-mode", lead_mode=("default", "Lead registration abc")), "CD-5: a default-mode Lead passes")
        t.check(not any(l == "FAIL" for l, _ in lvl(good, "audit", "permission-mode", lead_mode=None)), "CD-5: never a FAIL")
        lp = os.path.join(nj, "leads.json")
        write_json(lp, {"sessions": {"old11111xx": {"ts": 1, "permission_mode": "default"}, "abc12345xyz": {"ts": 5, "permission_mode": "bypassPermissions"},
                                     "nomode": {"ts": 9}}})
        t.check(lead_permission_mode() == ("bypassPermissions", "Lead registration abc12345"), "CD-5: the newest Lead registration with a permission_mode wins", lead_permission_mode())
        os.remove(lp)
        vs = os.path.join(tmp, "vscode-settings.json")
        write_text(vs, '{"claudeCode.initialPermissionMode": "bypassPermissions", "claudeCode.allowDangerouslySkipPermissions": true}\n')
        os.environ["NJ_VSCODE_SETTINGS"] = vs
        try:
            t.check(lead_permission_mode() == ("bypassPermissions", "VS Code setting claudeCode.initialPermissionMode"), "CD-5: the VS Code setting is the fallback hint", lead_permission_mode())
        finally:
            os.environ.pop("NJ_VSCODE_SETTINGS", None)
        t.check(lead_permission_mode() is None or "VS Code" in lead_permission_mode()[1], "CD-5: no registration and no setting: unknown (None)")
        # ---- A4: install-settings keeps every pre-v4 key ----
        sdir = os.path.join(tmp, "ins")
        os.makedirs(sdir, exist_ok=True)
        sp = os.path.join(sdir, "settings.json")
        pre = json.loads(json.dumps(pre0))
        pre.pop("_about")
        write_json(sp, pre)
        nj_i = norm(os.path.join(sdir, "njhome"))
        base_args = ["--settings-file", sp, "--python", sys.executable, "--nj-home", nj_i]
        rc, o_ = cap(cmd_install_settings, base_args)
        new = read_json(sp, {})
        t.check(rc == 0 and new != pre, "A4: install-settings merges the fragment into a v3 settings file", o_)
        t.check(read_json(sp + ".pre-v4", None) == pre, "A4: the pre-v4 copy is kept when it is missing")
        a_ = doctor_against(new, pre)
        t.check(all(l == "PASS" for l, _, _ in a_), "A4: doctor --against: every pre-v4 key and value is preserved, sdlc hook once", a_)
        t.check(all(new.get(k) == v for k, v in pre.items() if k not in ("env", "modelSettings", "hooks")) and new["env"]["CLAUDE_SECURITY_SCAN_TIP"] == "off",
                "A4: enabledPlugins, marketplaces, privacy and remote-control keys survive")
        t.check(new["modelSettings"]["claude-opus-5-5"]["effortLevel"] == "medium" and new["env"]["PYTHONUTF8"] == "1" and new["worktree"]["baseRef"] == "head",
                "A4: effort medium, required env and baseRef head are written")
        dn = new["permissions"]["deny"]
        t.check(all(r in dn for r in DENY_AUDIT) and not any(r in dn for r in DENY_ENFORCE), "D20: the audit activation writes the model and secret denies only")
        t.check(not any("onFailure" in h for gs in new["hooks"].values() for g_ in gs for h in g_["hooks"]), "D26: no onFailure block is written in audit")
        sd_n = [h for gs in new["hooks"].values() for g_ in gs for h in g_["hooks"] if hook_sig(h["command"])[0] == "sdlc-hook"]
        t.check(len(sd_n) == 1, "A4: the sdlc.py SubagentStop hook appears exactly once", len(sd_n))
        launch = [h["command"] for gs in new["hooks"].values() for g_ in gs for h in g_["hooks"] if launcher_sub(h["command"])]
        t.check(launch and all(split_command(c)[0] == norm(sys.executable) and (split_command(c)[1] or "").startswith(nj_i) for c in launch),
                "A4: every launcher hook is pinned to the interpreter and the state root", launch[:2])
        b1 = open(sp, "rb").read()
        rc, o_ = cap(cmd_install_settings, base_args)
        t.check(rc == 0 and "unchanged" in o_ and open(sp, "rb").read() == b1, "A4: install-settings is idempotent (second run changes nothing)", o_)
        dup = json.loads(json.dumps(new))
        dup["hooks"]["SubagentStop"].append(json.loads(json.dumps(next(g_ for g_ in dup["hooks"]["SubagentStop"] if g_["matcher"] == "sdlc-.*"))))
        write_json(sp, dup)
        rc, o_ = cap(cmd_install_settings, base_args + ["--against", sp + ".pre-v4"])
        n_sd = sum(1 for gs in read_json(sp)["hooks"].values() for g_ in gs for h in g_["hooks"] if hook_sig(h["command"])[0] == "sdlc-hook")
        t.check(rc == 0 and n_sd == 1, "A4: a duplicated sdlc.py hook is merged back to one (no two runs per stop)", (rc, n_sd, o_))
        # a space in the interpreter path is quoted
        pyd = os.path.join(sdir, "py dir")
        os.makedirs(pyd, exist_ok=True)
        fakepy = norm(os.path.join(pyd, "python.exe"))
        write_text(fakepy, "")
        sp2 = os.path.join(sdir, "settings2.json")
        write_json(sp2, pre)
        rc, o_ = cap(cmd_install_settings, ["--settings-file", sp2, "--python", fakepy, "--nj-home", norm(os.path.join(sdir, "nj home"))])
        c2 = [h["command"] for gs in read_json(sp2, {}).get("hooks", {}).values() for g_ in gs for h in g_["hooks"] if launcher_sub(h["command"])]
        t.check(rc == 0 and c2 and all(split_command(c)[0] == fakepy and "nj home" in (split_command(c)[1] or "") for c in c2), "A4: paths with spaces are quoted in the hook commands", (rc, c2[:1], o_))
        # refusals
        write_text(sp2, "{not json")
        rc, o_ = cap(cmd_install_settings, ["--settings-file", sp2, "--python", sys.executable, "--nj-home", nj_i])
        t.check(rc == 1 and open(sp2).read() == "{not json", "A4: an unreadable settings.json is refused and left alone", o_)
        rc, o_ = cap(cmd_install_settings, ["--settings-file", sp, "--python", "C:/Profiles/x/AppData/Local/Microsoft/WindowsApps/python.exe", "--nj-home", nj_i])
        t.check(rc == 1 and "WindowsApps" in o_, "A4/D26: install-settings refuses the WindowsApps stub", o_)
        bad = json.loads(json.dumps(new))
        bad.pop("enabledPlugins")
        t.check(any(l == "FAIL" for l, _, _ in doctor_against(bad, pre)), "A4: doctor --against fails when a pre-v4 key is dropped (the fixture failure the review described)")
        bad = json.loads(json.dumps(new))
        bad["crossSessionInbound"] = "allow"
        t.check(any(l == "FAIL" for l, _, _ in doctor_against(bad, pre)), "A4: doctor --against fails when a pre-v4 value changes")
        bad = json.loads(json.dumps(new))
        bad["hooks"]["SubagentStop"] = [g_ for g_ in bad["hooks"]["SubagentStop"] if g_["matcher"] != "sdlc-.*"]
        t.check(any(l == "FAIL" for l, _, _ in doctor_against(bad, pre)), "A4: doctor --against fails when the sdlc.py hook is gone")
        rc, so, se = gm(["doctor", "--settings", "--settings-file", sp, "--against", sp + ".pre-v4", "--mode", "audit"])
        t.check(rc == 0 and "settings.against:" in so.replace("PASS ", ""), "A4: gov4.py doctor --settings --against passes on the merged file", so + se)
        # ---- A5/A6 (D20): mode enforce adds, mode audit|off removes ----
        write_json(sp, new)
        ok, note = apply_mode_to_settings(sp, "enforce")
        s_e = read_json(sp, {})
        t.check(ok and all(r in s_e["permissions"]["deny"] for r in DENY_ENFORCE) and any(h.get("onFailure") == "block" for gs in s_e["hooks"].values() for g_ in gs for h in g_["hooks"]),
                "A5/D26: enforce adds the git and gh denies and onFailure: block", note)
        t.check(not any(l == "FAIL" for l, _ in lvl(s_e, "enforce", lead_mode=None)), "A5: the enforce result passes the enforce doctor", [r for r in doctor_settings(s_e, mode="enforce") if r[0] == "FAIL"])
        ok, note = apply_mode_to_settings(sp, "audit")
        t.check(ok and read_json(sp, {}) == new, "A5/A6: audit removes exactly what enforce added (round trip equals the audit file)", note)
        apply_mode_to_settings(sp, "enforce")
        ok, note = apply_mode_to_settings(sp, "off")
        t.check(ok and read_json(sp, {}) == new, "A5/A6: off removes them too", note)
        ok, note = apply_mode_to_settings(os.path.join(sdir, "absent.json"), "enforce")
        t.check(ok and "not found" in note, "A5: a missing settings.json is not an error")
        # the command path: audit -> enforce (ready by now) -> audit, on a scratch settings file
        write_json(sp, new)
        reg.set_mode("audit")
        gm(["enforce-ready", "--record", "decisions"])          # the audit lines logged by the tests above count as reviewed
        rc, so, se = gm(["mode", "enforce", "--settings-file", sp])
        s_c = read_json(sp, {})
        t.check(rc == 0 and reg.get_mode() == "enforce" and all(r in s_c["permissions"]["deny"] for r in DENY_ENFORCE), "A5: gov4.py mode enforce writes the git and gh deny rules", so + se)
        rc, so, se = gm(["mode", "audit", "--settings-file", sp], ticket=True)
        t.check(rc == 0 and reg.get_mode() == "audit" and read_json(sp, {}) == new, "A5: gov4.py mode audit removes them again", so + se)
        write_text(sp, "{not json")
        reg.set_mode("audit")
        rc, so, se = gm(["mode", "enforce", "--settings-file", sp])
        t.check(rc == 1 and reg.get_mode() == "audit", "A5: mode enforce is refused when settings.json is unreadable, and the mode does not change", so + se)
        # ---- A7: the out-of-band restore script ----
        cmdp = os.path.abspath(os.path.join(HERE, "..", "..", "..", "install", "restore-pre-v4.cmd"))
        if NT and os.path.isfile(cmdp):
            rh = os.path.join(tmp, "rs-home")

            def wr(rel, txt):
                fp = os.path.join(rh, rel)
                os.makedirs(os.path.dirname(fp), exist_ok=True)
                write_text(fp, txt)
            wr("settings.json", "v4 settings\n")
            wr("settings.json.pre-v4", "v3 settings\n")
            wr("CLAUDE.md", "v4 md\n")
            wr("CLAUDE.md.pre-v4", "v3 md\n")
            wr("agents/sdlc-build.md", "v4 agent\n")
            wr("agents/nj-agent.md", "new v4 agent\n")
            wr("nj/mode", "audit\n")
            wr("nj/snapshot-20261016-000000/items/agents/sdlc-build.md", "OLDER snapshot agent\n")
            wr("nj/snapshot-20261016-010000/items/agents/sdlc-build.md", "v3 agent\n")
            wr("nj/snapshot-20261016-010000/items/plugins-installed", '{"v":"1.3.5"}\n')
            wr("nj/snapshot-20261016-010000/items/plugins-marketplaces", '{"m":"dir"}\n')
            wr("plugins/installed_plugins.json", '{"v":"1.4.0"}\n')
            evr = dict(os.environ, CLAUDE_HOME=rh)
            rc, so, se = sh(["cmd", "/c", cmdp, "/dry"], env=evr)
            t.check(rc == 0 and "DRY RUN" in so and open(os.path.join(rh, "settings.json")).read() == "v4 settings\n" and "snapshot-20261016-010000" in so,
                    "A7: /dry changes nothing and names the newest snapshot", so + se)
            rc, so, se = sh(["cmd", "/c", cmdp], env=evr)
            rd = lambda rel: open(os.path.join(rh, rel), encoding="utf-8").read()
            t.check(rc == 0 and rd("settings.json") == "v3 settings\n" and rd("CLAUDE.md") == "v3 md\n" and rd("settings.json.v4-rolled-back") == "v4 settings\n",
                    "A7: settings.json and CLAUDE.md come back from .pre-v4 (v4 copies kept)", so + se)
            t.check(rd("agents/sdlc-build.md") == "v3 agent\n" and os.path.isfile(os.path.join(rh, "agents", "nj-agent.md")),
                    "A7: with no agents.pre-v4 the agents come from the newest snapshot (nothing is deleted)", so + se)
            t.check(rd("nj/mode").strip() == "off", "A7: the hooks are put to mode off")
            t.check(rd("plugins/installed_plugins.json").strip() == '{"v":"1.3.5"}' and rd("plugins/known_marketplaces.json").strip() == '{"m":"dir"}',
                    "A3/A7: the plugin registry files come back from the snapshot", so + se)
            wr("agents/sdlc-build.md", "v4 agent\n")
            wr("agents.pre-v4/sdlc-build.md", "explicit pre-v4 agent\n")
            rc, so, se = sh(["cmd", "/c", cmdp], env=evr)
            t.check(rc == 0 and rd("agents/sdlc-build.md") == "explicit pre-v4 agent\n", "A7: agents.pre-v4 wins over a snapshot when it exists", so + se)
            rh2 = os.path.join(tmp, "rs-home2")
            os.makedirs(rh2, exist_ok=True)
            for n_, c_ in (("settings.json", "v4\n"), ("settings.json.pre-v4", "v3\n"), ("CLAUDE.md", "v4\n"), ("CLAUDE.md.pre-v4", "v3\n")):
                write_text(os.path.join(rh2, n_), c_)
            os.makedirs(os.path.join(rh2, "agents"), exist_ok=True)
            write_text(os.path.join(rh2, "agents", "a.md"), "keep\n")
            rc, so, se = sh(["cmd", "/c", cmdp], env=dict(os.environ, CLAUDE_HOME=rh2))
            t.check(rc == 0 and open(os.path.join(rh2, "settings.json")).read() == "v3\n" and open(os.path.join(rh2, "agents", "a.md")).read() == "keep\n",
                    "A7: with no snapshot and no agents.pre-v4 it still restores settings and leaves agents alone", so + se)
            os.remove(os.path.join(rh2, "CLAUDE.md.pre-v4"))
            rc, so, se = sh(["cmd", "/c", cmdp], env=dict(os.environ, CLAUDE_HOME=rh2))
            t.check(rc == 1, "A7: a missing .pre-v4 copy stops the script before it changes anything", so + se)
        # ---- A3 default_items list ----
        ids = {i["id"] for i in default_items()}
        t.check({"plugins-installed", "plugins-marketplaces"} <= ids, "A3: the activation snapshot lists installed_plugins.json and known_marketplaces.json", ids)
    finally:
        gl["human_tty"] = real_tty
        reg.set_mode("enforce")
        if old_home is None:
            os.environ.pop("NJ_HOME", None)
        else:
            os.environ["NJ_HOME"] = old_home


def selftest_git(t, tmp):
    nj = os.path.join(tmp, "nj")
    os.makedirs(nj, exist_ok=True)
    reg_env_old = {k: os.environ.get(k) for k in ("NJ_HOME", "NJ_MODE_OVERRIDE", "NJ_SWEEP_NO_PROCS")}
    os.environ["NJ_HOME"] = nj
    os.environ["NJ_SWEEP_NO_PROCS"] = "1"
    os.environ.pop("NJ_MODE_OVERRIDE", None)
    R = norm(os.path.join(tmp, "repo"))
    env = dict(os.environ, PYTHONUTF8="1", GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    env.pop("NJ_TICKET", None)
    me = [sys.executable, "-X", "utf8", os.path.abspath(__file__)]

    def mode_env(e):
        """SB-02/D27: the hooks and gov4.py read the mode from the state file only. The old NJ_MODE_OVERRIDE key in `e` now means
        'put this mode in the scratch state file before the command runs' (a call with no mode key runs in audit)."""
        e = dict(e or {})
        m = e.pop("NJ_MODE_OVERRIDE", None)
        reg.set_mode(m or "audit")
        return e

    def G(*a, cwd=None, e=None, raw=None):
        ev = dict(env)
        ev.update(mode_env(e))
        ev.update(raw or {})
        return sh(["git"] + list(a), cwd=cwd or R, env=ev)

    def g(args, ticket=True, e=None, cwd=None):
        ev = dict(env)
        ev.update(mode_env(e))
        if ticket:
            ev["NJ_TICKET"] = reg.mint_ticket(args) or ""
        return sh(me + args, cwd=cwd or R, env=ev)

    def put(rel, txt, base=None):
        fp = os.path.join(base or R, rel)
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        with open(fp, "w", encoding="utf-8", newline="\n") as f:
            f.write(txt)

    try:
        os.makedirs(R)
        G("init", "-q", "-b", "main")
        put(".gitignore", "assets/fonts/\n.claude/worktrees/\nwork/\n.agent-ops/\n")
        put("README.md", "base\n")
        put("src/app.py", "v1\n")
        put("src/other.py", "o1\n")
        put("drafts/d1/meta.json", "{}\n")
        put("captions/readme.txt", "c\n")
        put(".nj/live-paths.txt", "# live\ndrafts/*/meta.json\nwork/**\n")
        put(".nj/review-required.txt", "captions/**\n")
        put(".worktreeinclude", "assets/fonts/**\n")
        put("assets/fonts/x.ttf", "FONT\n")
        put(".nj/gates.json", json.dumps({"version": 1, "env": {"PYTHONUTF8": "1"}, "full": [
            {"id": "fonts_present", "cmd": "test -f assets/fonts/x.ttf"},
            {"id": "no_bad", "cmd": "test ! -f BAD"},
            {"id": "per_draft", "cmd": "test -f {path}/meta.json && test -n \"{slug}\"", "each": "drafts/*", "when": ["drafts/**"]},
            {"id": "slow_one", "cmd": "exit 1", "slow": True}], "post_merge": ["fonts_present", "no_bad", "per_draft"]}))
        G("add", "-A")
        G("commit", "-q", "-m", "base")
        remote = norm(os.path.join(tmp, "remote.git"))
        sh(["git", "init", "-q", "--bare", "-b", "main", remote], env=env)
        G("remote", "add", "origin", remote)
        G("push", "-q", "origin", "main")
        rc, so, se = g(["install-repo"], ticket=True)
        t.check(rc == 0 and "updated" in so, "install-repo installs hooks and config", so + se)
        hp = G("config", "--get", "core.hooksPath")[1].strip()
        t.check(os.path.isfile(os.path.join(hp, "reference-transaction")) and os.path.isfile(os.path.join(hp, "pre-push")), "install-repo: hooks in the shared directory", hp)
        t.check(G("config", "--get", "remote.origin.pushurl")[1].strip() == DEAD_PUSHURL, "install-repo: dead pushurl")
        rc, so, se = g(["install-repo"], ticket=True)
        t.check(rc == 0 and "unchanged" in so and "config unchanged" in so, "install-repo is idempotent", so)
        t.check(b"\r" not in read_bytes(os.path.join(hp, "reference-transaction")), "hooks have LF endings")
        # ---- git hook layer (enforce) ----
        E = {"NJ_MODE_OVERRIDE": "enforce"}
        rc, so, se = G("commit", "-q", "--allow-empty", "-m", "direct", e=E)
        t.check(rc != 0 and "ticket token" in se, "reference-transaction: a direct commit on main is rejected (enforce)", se)
        t.check(G("rev-parse", "HEAD")[1].strip() == G("rev-parse", "refs/remotes/origin/main")[1].strip(), "rejected commit left main where it was")
        rc, so, se = G("commit", "-q", "--allow-empty", "-m", "direct", "--no-verify", e=E)
        t.check(rc != 0, "reference-transaction: --no-verify does not bypass it", se)
        rc, so, se = G("update-ref", "refs/tags/v1", "HEAD", e=E)
        t.check(rc != 0, "reference-transaction: tags rejected", se)
        rc, so, se = G("commit", "-q", "--allow-empty", "-m", "fake", e=dict(E, NJ_GIT_TOKEN="deadbeef"))
        t.check(rc != 0, "reference-transaction: a made-up token is rejected", se)
        OFF = {"NJ_MODE_OVERRIDE": "off"}
        G("commit", "-q", "--allow-empty", "-m", "unpushed", e=OFF)
        remote_main = sh(["git", "-C", remote, "rev-parse", "main"], env=env)[1].strip()
        rc, so, se = G("-c", "remote.origin.pushurl=", "-c", f"remote.origin.pushurl={remote}", "push", "origin", "main", e=E)
        t.check(rc != 0 and "ticket token" in se and "pushing" in se, "pre-push: a push of main without the token is rejected by the hook", se)
        t.check(sh(["git", "-C", remote, "rev-parse", "main"], env=env)[1].strip() == remote_main, "pre-push: the remote main did not move")
        # SB-02: the hooks read a state path baked in at install-repo time and ignore every environment variable
        hook_txt = read_bytes(os.path.join(hp, "reference-transaction")).decode("utf-8") + read_bytes(os.path.join(hp, "pre-push")).decode("utf-8")
        t.check(f"NJ_STATE_DIR='{norm(os.path.abspath(nj))}'" in hook_txt and "@@NJ_STATE_DIR@@'" not in hook_txt.replace("'@@'*", ""),
                "SB-02: install-repo baked the state path into both hooks", hook_txt[:300])
        t.check(not re.search(r"\$\{?(NJ_HOME|NJ_MODE_OVERRIDE|HOME)\b", hook_txt.split("NJ_STATE_DIR='", 1)[1].split("\n", 1)[1].replace('"$HOME/.claude/nj"', "")),
                "SB-02: the hooks reference no NJ_HOME / NJ_MODE_OVERRIDE / HOME variable after the baked path")
        for raw in ({"NJ_MODE_OVERRIDE": "off"}, {"NJ_HOME": "/nonexistent"}, {"NJ_HOME": norm(os.path.join(tmp, "elsewhere")), "NJ_MODE_OVERRIDE": "off"},
                    {"HOME": "/nonexistent", "USERPROFILE": "/nonexistent"}):
            rc, so, se = G("commit", "-q", "--allow-empty", "-m", "env bypass", e=E, raw=raw)
            t.check(rc != 0 and "ticket token" in se, f"SB-02: reference-transaction ignores env {sorted(raw)}", se)
            rc, so, se = G("-c", "remote.origin.pushurl=", "-c", f"remote.origin.pushurl={remote}", "push", "origin", "main", e=E, raw=raw)
            t.check(rc != 0 and "pushing" in se, f"SB-02: pre-push ignores env {sorted(raw)}", se)
        t.check(sh(["git", "-C", remote, "rev-parse", "main"], env=env)[1].strip() == remote_main, "SB-02: the remote main still did not move")
        G("reset", "-q", "--hard", "refs/remotes/origin/main", e=OFF)
        rc, so, se = G("push", "origin", "main", e=E)
        t.check(rc != 0, "dead pushurl: a bare git push fails", se)
        rc, so, se = G("commit", "-q", "--allow-empty", "-m", "audit", e={"NJ_MODE_OVERRIDE": "audit"})
        t.check(rc == 0, "audit mode allows and logs", se)
        t.check("would-deny" in (open(os.path.join(nj, "decisions.jsonl")).read() if os.path.exists(os.path.join(nj, "decisions.jsonl")) else ""), "audit mode logged the would-deny")
        G("reset", "-q", "--hard", "refs/remotes/origin/main", e={"NJ_MODE_OVERRIDE": "audit"})
        rc, so, se = G("commit", "-q", "--allow-empty", "-m", "off", e={"NJ_MODE_OVERRIDE": "off"})
        t.check(rc == 0, "mode off makes the hook inert", se)
        G("reset", "-q", "--hard", "refs/remotes/origin/main", e={"NJ_MODE_OVERRIDE": "off"})
        rc, so, se = G("checkout", "-q", "-b", "feature-x", e=E)
        t.check(rc == 0, "other branches are not guarded", se)
        G("checkout", "-q", "main", e=E)
        G("branch", "-q", "-D", "feature-x", e=E)
        # ---- agent branches ----
        mkdirp = lambda p: os.makedirs(p, exist_ok=True)
        os.makedirs(os.path.join(R, ".agent-ops", "claims"), exist_ok=True)
        claims = []

        def agent(name, files, changed=None, claim=None, run="r1", head_override=None, start="main"):
            wtp = norm(os.path.join(tmp, "wt-" + name))
            br = f"worktree-{run}-{name}"
            rc, so, se = G("worktree", "add", "-q", "-b", br, wtp, start)
            assert rc == 0, se
            for rel, txt in files.items():
                if txt is None:
                    os.remove(os.path.join(wtp, rel))
                else:
                    put(rel, txt, wtp)
            G("add", "-A", cwd=wtp)
            G("commit", "-q", "-m", f"work {name}", cwd=wtp)
            head = G("rev-parse", "HEAD", cwd=wtp)[1].strip()
            rec_p = os.path.join(R, ".agent-ops", "results", run, f"{name}.json")
            write_json(rec_p, {"agent": name, "status": "ok", "files": list(files), "head": head, "gates_at_head": [f"selftest PASS @{head[:8]}"],
                               "helpers_spawned": 0, "parent": "lead", "role": "agent", "model": "sonnet"})
            claims.append({"agent": name, "paths": claim if claim is not None else list(files)})
            write_json(os.path.join(R, ".agent-ops", "claims", f"{run}.json"), claims)
            mq = os.path.join(R, "work", "merge-queue")
            mkdirp(mq)
            seq = len([x for x in os.listdir(mq) if x.endswith(".json")]) + 1
            write_json(os.path.join(mq, f"{seq:03d}-{name}.json"), {"name": name, "run": run, "branch": br, "head": head_override or head,
                                                                    "stage": "build", "changed": changed if changed is not None else list(files),
                                                                    "receipt": norm(rec_p), "queued": now_ts(), "state": "queued"})
            return wtp, br, head

        main0 = G("rev-parse", "main")[1].strip()
        # B: conflict branch cut from the old main (before A merges)
        agent("conflict", {"src/app.py": "conflicting\n"})
        wA, brA, headA = agent("clean", {"src/app.py": "v2\n", "docs/a.md": "A\n"})
        # C gate fail, D head, E changed, F claim, G live, H dirty, J reviewer, K ticket
        agent("badgate", {"BAD": "x\n"})
        agent("headmis", {"docs/h.md": "h\n"}, head_override="0" * 40)
        wl, brl, headl = agent("late", {"docs/late.md": "l\n"})
        G("commit", "-q", "--allow-empty", "-m", "advance after receipt", cwd=wl)
        agent("changedmis", {"docs/c1.md": "1\n", "docs/c2.md": "2\n"}, changed=["docs/c1.md"])
        agent("outclaim", {"src/x.py": "x\n"}, claim=["docs/**"])
        agent("livemod", {"drafts/d1/meta.json": "{\"changed\":1}\n"})
        agent("liveadd", {"drafts/d2/meta.json": "{}\n", "drafts/d2/caption.txt": "cap\n"})
        agent("dirty", {"src/other.py": "o2\n"})
        agent("reviewme", {"captions/c.txt": "hello\n"})
        # review digest
        rc, so, se = g(["review", "clean"], ticket=False)
        t.check(rc == 0 and len(so.strip().splitlines()) <= 30 and "VERDICT: ready" in so, "review: at most 30 lines, ready verdict", so + se)
        rc, so, se = g(["review", "changedmis"], ticket=False)
        t.check(rc == 1 and "MISMATCH" in so and len(so.strip().splitlines()) <= 30, "review: shows CHANGED mismatch", so)
        rc, so, se = g(["queue"], ticket=False)
        t.check(rc == 0 and "clean" in so and "conflict" in so, "queue lists the tickets", so)
        # no ticket
        rc, so, se = g(["merge", "clean"], ticket=False, e=E)
        t.check(rc == 3 and G("rev-parse", "main")[1].strip() == main0, "merge without a ticket is refused and main is untouched", so + se)
        # A: clean merge (hooks enforce; gov4 holds the token)
        rc, so, se = g(["merge", "clean"], e=E)
        t.check(rc == 0, "merge: clean merge succeeds under enforce", so + se)
        msg = G("log", "-1", "--format=%B", "main")[1]
        t.check("Task-Id: r1/clean" in msg and "Agent-Id: clean" in msg and "Co-Authored-By: Claude Sonnet 5.5" in msg and "Gate-at-head: selftest PASS" in msg, "merge: trailers present", msg)
        t.check(len(G("log", "-1", "--format=%P", "main")[1].split()) == 2, "merge: --no-ff merge commit with two parents")
        t.check(open(os.path.join(R, "docs", "a.md")).read() == "A\n", "merge: file reached the main working tree")
        t.check(os.path.isfile(os.path.join(mq_dir(R), "DONE-clean.flag")) and open(os.path.join(mq_dir(R), "DONE-clean.flag")).read().startswith("OK"), "merge: DONE-clean.flag written")
        t.check(not os.path.exists(os.path.join(R, ".claude", "worktrees", "_integration")), "merge: _integration worktree removed")
        t.check(find_ticket(R, "clean")[1]["state"] == "merged" and "fonts_present PASS" in " ".join(find_ticket(R, "clean")[1]["merged"]["gates"]),
                ".worktreeinclude: fonts copied into _integration (the fonts gate passed there)", find_ticket(R, "clean")[1])
        # reuse of a merged ticket
        rc, so, se = g(["merge", "clean"], e=E)
        t.check(rc == 1, "merge: a merged ticket is not merged twice", so)
        # B: conflict
        rc, so, se = g(["preflight", "conflict"], ticket=False)
        t.check(rc == 1 and find_ticket(R, "conflict")[1]["state"] == "dequeued-conflict", "preflight: conflict exits 1 and dequeues the ticket", so + se)
        rc, so, se = g(["merge", "conflict"], e=E)
        t.check(rc == 1 and not G("rev-parse", "main")[1].strip() == "", "merge: a dequeued conflict is refused", so)
        m1 = G("rev-parse", "main")[1].strip()
        # C
        rc, so, se = g(["merge", "badgate"], e=E)
        t.check(rc == 1 and G("rev-parse", "main")[1].strip() == m1 and not os.path.exists(os.path.join(R, "BAD")), "merge: a failing gate leaves main untouched", so + se)
        t.check("gates failed" in open(os.path.join(mq_dir(R), "DONE-badgate.flag")).read(), "merge: DONE flag names the gate failure")
        t.check(not os.path.exists(os.path.join(R, ".claude", "worktrees", "_integration")), "merge: _integration removed after a gate failure")
        # D
        rc, so, se = g(["merge", "headmis"], e=E)
        t.check(rc == 1 and "head-sha mismatch" in so and G("rev-parse", "main")[1].strip() == m1, "merge: head-sha mismatch (ticket) refused", so)
        rc, so, se = g(["merge", "late"], e=E)
        t.check(rc == 1 and "head-sha mismatch" in so, "merge: branch advanced after the receipt is refused", so)
        # E
        rc, so, se = g(["merge", "changedmis"], e=E)
        t.check(rc == 1 and "CHANGED mismatch" in so, "merge: CHANGED mismatch refused", so)
        # F
        rc, so, se = g(["merge", "outclaim"], e=E)
        t.check(rc == 1 and "outside the claim" in so, "merge: diff outside the claim refused", so)
        # G
        rc, so, se = g(["merge", "livemod"], e=E)
        t.check(rc == 1 and "live path" in so, "merge: modifying a live path refused", so)
        rc, so, se = g(["merge", "liveadd"], e=E)
        t.check(rc == 0 and os.path.isfile(os.path.join(R, "drafts", "d2", "meta.json")), "merge: a NEW file under a live glob is allowed (D15) and the each-gate ran", so + se)
        t.check("per_draft[drafts/d2] PASS" in " ".join(find_ticket(R, "liveadd")[1]["merged"]["gates"]), "merge: each-gate filled {path} and {slug}", find_ticket(R, "liveadd")[1]["merged"])
        # H
        put("src/other.py", "dirty in main\n")
        rc, so, se = g(["merge", "dirty"], e=E)
        t.check(rc == 1 and "dirty paths" in so, "merge: dirty overlap refused", so)
        G("checkout", "--", "src/other.py", e={"NJ_MODE_OVERRIDE": "off"})
        # J
        rc, so, se = g(["merge", "reviewme"], e=E)
        t.check(rc == 1 and "reviewer is mandatory" in so, "merge: a review-required path needs --reviewed-by", so)
        rc, so, se = g(["merge", "reviewme", "--reviewed-by", "nj-reviewer-1"], e=E)
        t.check(rc == 0 and "Reviewed-by: nj-reviewer-1" in G("log", "-1", "--format=%B", "main")[1], "merge: --reviewed-by merges and records the trailer", so + se)
        # sweep
        rc, so, se = g(["sweep", "--allow-queued"], e=E)
        t.check(rc == 1 and "holds unmerged work" in so, "sweep: unmerged worktrees are leftovers (exit 1)", so + se)
        left_before = so
        keeps = []
        for n in ("conflict", "badgate", "headmis", "late", "changedmis", "outclaim", "livemod", "dirty"):
            keeps += ["--keep", f"worktree-r1-{n}"]
        rc, so, se = g(["sweep"] + keeps + ["--released", "r1"], e=E)
        t.check(rc == 0 and "0 leftover" in so, "sweep: kept worktrees pass and merged ones are cleaned", so + se)
        t.check(not os.path.exists(os.path.join(tmp, "wt-clean")) and not os.path.exists(os.path.join(tmp, "wt-liveadd")), "sweep: merged worktrees removed")
        t.check(G("rev-parse", "--verify", "-q", "worktree-r1-clean")[0] != 0, "sweep: merged branch deleted")
        # a worktree-less unmerged branch is still a leftover (sweep must not exit 0 while a branch survives)
        G("worktree", "remove", "--force", norm(os.path.join(tmp, "wt-late")), e={"NJ_MODE_OVERRIDE": "off"})
        rc, so, se = g(["sweep"] + keeps + ["--released", "r1"], e=E)
        t.check(rc == 0, "sweep: --keep also covers a worktree-less branch", so)
        rc, so, se = g(["sweep", "--released", "r1"] + [x for k in keeps for x in [k]][:0], e=E)
        t.check(rc == 1 and "has no worktree" in so, "sweep: an unmerged branch without a worktree is a leftover", so)
        # unstaged review + checkpoint
        put("README.md", "base\nedited by a job\n")
        put("notes/n.txt", "n\n")
        rc, so, se = g(["review", "--unstaged"], ticket=False)
        t.check(rc == 0 and "UNSTAGED" in so and len(so.strip().splitlines()) <= 30, "review --unstaged", so + se)
        rc, so, se = g(["checkpoint"], e=E)
        t.check(rc == 0 and "checkpoint ok" in so and not dirty_paths(R), "checkpoint commits the dirty tree on main under enforce", so + se)
        rc, so, se = g(["checkpoint"], e=E)
        t.check(rc == 0 and "clean" in so, "checkpoint on a clean tree is a no-op", so)
        # push
        rc, so, se = g(["push"], ticket=False, e=E)
        t.check(rc == 3, "push without a ticket refused", so + se)
        rc, so, se = g(["push", "--force"], e=E)
        t.check(rc == 1 and "never allowed" in so, "push --force refused", so)
        rc, so, se = g(["push"], e=E)
        t.check(rc != 0 and ("sweep" in so or "LEFTOVER" in so), "push refused while the sweep shows unmerged worktrees", so + se)
        # clear the leftovers (the Lead merges or discards them; here the test removes them with git directly, in audit)
        for n in ("conflict", "badgate", "headmis", "late", "changedmis", "outclaim", "livemod", "dirty"):
            G("worktree", "remove", "--force", norm(os.path.join(tmp, "wt-" + n)), e={"NJ_MODE_OVERRIDE": "off"})
            G("branch", "-q", "-D", f"worktree-r1-{n}", e={"NJ_MODE_OVERRIDE": "off"})
            pth, tkd = find_ticket(R, n)
            tkd["state"] = "discarded"
            save_ticket(pth, tkd)
        rc, so, se = g(["push"], e=E)
        t.check(rc == 0, "push: atomic push through gov4.py works against a local bare remote", so + se)
        t.check(G("rev-parse", "main")[1].strip() == sh(["git", "-C", remote, "rev-parse", "main"], env=env)[1].strip(), "push: the remote main equals local main")
        # a non-Lead cannot push: no ticket -> rc 3 (done above); a wrapper hitting git directly is stopped by the hook:
        G("commit", "-q", "--allow-empty", "-m", "unpushed2", e=OFF)
        rc, so, se = sh(["python", "-c", "import subprocess;r=subprocess.run(['git','-c','remote.origin.pushurl=','-c','remote.origin.pushurl=" + remote + "','push','origin','main'],capture_output=True,text=True);print(r.returncode, 'pushing' in r.stderr)"],
                        cwd=R, env=dict(env, **mode_env(E)))
        t.check(rc == 0 and so.strip().endswith("True") and not so.strip().startswith("0"), "python wrapper around git push still hits the hook", so + se)
        G("reset", "-q", "--hard", "refs/remotes/origin/main", e=OFF)
        # process listing with a worktree path mentioned
        os.environ.pop("NJ_SWEEP_NO_PROCS", None)
        wsp = norm(os.path.join(tmp, "wt-proc"))
        G("worktree", "add", "-q", "-b", "worktree-r1-proc", wsp, "main", e={"NJ_MODE_OVERRIDE": "off"})
        p = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(25)", wsp])
        try:
            time.sleep(0.5)
            rc, so, se = g(["sweep", "--released", "r1"], e=dict(E, NJ_SWEEP_NO_PROCS=""))
            t.check("mentions a worktree" in so and f"pid={p.pid}" in so, "sweep: a process referencing a worktree is named, not killed", so + se)
            t.check(p.poll() is None, "sweep did not kill the process")
        finally:
            p.kill()
            p.wait()
        G("worktree", "remove", "--force", wsp, e={"NJ_MODE_OVERRIDE": "off"})
        G("branch", "-q", "-D", "worktree-r1-proc", e={"NJ_MODE_OVERRIDE": "off"})
        # ---- no gates file ----
        R2 = norm(os.path.join(tmp, "repo2"))
        os.makedirs(R2)
        env2 = dict(env)
        sh(["git", "init", "-q", "-b", "main"], cwd=R2, env=env2)
        put("a.txt", "a\n", R2)
        sh(["git", "add", "-A"], cwd=R2, env=env2)
        sh(["git", "commit", "-q", "-m", "base"], cwd=R2, env=env2)
        sh(["git", "worktree", "add", "-q", "-b", "worktree-r2-w", norm(os.path.join(tmp, "wt2")), "main"], cwd=R2, env=env2)
        put("b.txt", "b\n", norm(os.path.join(tmp, "wt2")))
        sh(["git", "add", "-A"], cwd=norm(os.path.join(tmp, "wt2")), env=env2)
        sh(["git", "commit", "-q", "-m", "w"], cwd=norm(os.path.join(tmp, "wt2")), env=env2)
        h2 = sh(["git", "rev-parse", "HEAD"], cwd=norm(os.path.join(tmp, "wt2")), env=env2)[1].strip()
        os.makedirs(os.path.join(R2, "work", "merge-queue"))
        write_json(os.path.join(R2, "work", "merge-queue", "001-w.json"), {"name": "w", "run": "r2", "branch": "worktree-r2-w", "head": h2, "changed": ["b.txt"], "state": "queued"})
        rc, so, se = g(["merge", "w"], cwd=R2)
        t.check(rc == 1 and "no .nj/gates.json" in so, "merge: no gates file is refused", so + se)
        rc, so, se = g(["merge", "w", "--no-gates", "selftest repo has no gate list"], cwd=R2)
        t.check(rc == 0 and os.path.isfile(os.path.join(R2, "b.txt")), "merge: --no-gates with a reason is accepted and logged", so + se)
        t.check("selftest repo has no gate list" in open(os.path.join(nj, "events.jsonl")).read(), "merge: the --no-gates reason is logged")
        # push for non-ticket
    finally:
        for k, v in reg_env_old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def selftest_help(t, tmp):
    """H8: `<sub> -h|--help|help` prints usage, exits 0 and changes nothing, for every subcommand, in enforce mode with a snapshot
    present (so a handler that ran, such as rollback, would restore it, and a ticket check would refuse with rc 3)."""
    root = os.path.join(tmp, "hh")
    nj, ch = os.path.join(root, "nj"), os.path.join(root, "claude-home")
    for d_ in (nj, ch, os.path.join(ch, "agents")):
        os.makedirs(d_, exist_ok=True)
    write_text(os.path.join(nj, "selftest.marker"), os.environ["NJ_GOV4_SELFTEST"] + "\n")
    write_text(os.path.join(ch, "settings.json"), '{"model": "before"}\n')
    write_text(os.path.join(ch, "agents", "a.md"), "agent\n")
    old = os.environ.get("NJ_HOME"), os.environ.get("CLAUDE_HOME")
    os.environ["NJ_HOME"], os.environ["CLAUDE_HOME"] = nj, ch
    try:
        create_snapshot(default_items(), os.path.join(nj, "snapshot-20200101-000000"))
        write_text(os.path.join(ch, "settings.json"), '{"model": "after-snapshot"}\n')   # a rollback would put "before" back
        reg.set_mode("enforce")
        env = dict(os.environ, NJ_HOME=nj, CLAUDE_HOME=ch, PYTHONUTF8="1")
        env.pop("NJ_TICKET", None)
        env.pop("NJ_MODE_OVERRIDE", None)
        me = [sys.executable, "-X", "utf8", os.path.abspath(__file__)]
        subs = sorted(COMMANDS) + ["selftest"]
        for flag in ("--help", "-h", "help"):
            for sub in subs:
                before = tree_hashes(root)
                rc, so, se = sh(me + [sub, flag], env=env, timeout=120)
                after = tree_hashes(root)
                t.check(rc == 0 and "usage" in so.lower() and before == after,
                        f"H8: `{sub} {flag}` prints usage, exits 0 and writes nothing",
                        f"rc={rc} changed={sorted(set(before.items()) ^ set(after.items()))[:3]} out={(so + se)[-200:]}")
        # the dangerous shapes: help after other arguments, and the real flags of the write subcommands
        for argv in (["rollback", "--snapshot", nj, "--help"], ["rollback", "--create-snapshot", "--help"], ["install-bin", "--dry-run", "-h"],
                     ["install-settings", "--settings-file", os.path.join(ch, "settings.json"), "--help"], ["mode", "off", "--help"],
                     ["merge", "x", "--project", root, "--help"], ["push", root, "-h"], ["sweep", root, "--help"], ["checkpoint", root, "help"],
                     ["wave", "5", "-h"], ["unlock", "--minutes", "5", "--help"], ["snapshot", "begin", root, "--help"]):
            before = tree_hashes(root)
            rc, so, se = sh(me + argv, env=env, timeout=120)
            t.check(rc == 0 and "usage" in so.lower() and tree_hashes(root) == before and reg.get_mode() == "enforce",
                    f"H8: `{' '.join(argv[:2])} ... {argv[-1]}` is help only", f"rc={rc} out={(so + se)[-200:]}")
        t.check(read_json(os.path.join(ch, "settings.json"), {}).get("model") == "after-snapshot", "H8: no help call rolled settings.json back")
        t.check(not os.path.exists(os.path.join(nj, "events.jsonl")), "H8: help calls wrote no event line")
        t.check(wants_help(["x", "--help"]) and not wants_help(["-m", "help"]) and not wants_help(["x", "y"]), "H8: help detector")
    finally:
        for k, v in zip(("NJ_HOME", "CLAUDE_HOME"), old):
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def selftest():
    t = T()
    with tempfile.TemporaryDirectory(prefix="gov4-self-") as tmp:
        saved = {k: os.environ.get(k) for k in ("NJ_HOME", "NJ_MODE_OVERRIDE", "NJ_TICKETS", "NJ_TICKET", "NJ_GOV4_SELFTEST", "CLAUDE_HOME", "NJ_ROLE")}
        os.environ["NJ_HOME"] = os.path.join(tmp, "nj0")
        os.makedirs(os.environ["NJ_HOME"], exist_ok=True)
        for k in ("NJ_TICKETS", "NJ_MODE_OVERRIDE", "NJ_TICKET", "NJ_ROLE"):
            os.environ.pop(k, None)
        # D27: the scripted runs below own scratch state roots; the marker lets their gov4.py subprocesses keep NJ_HOME / CLAUDE_HOME,
        # which an unmarked non-terminal caller loses. CLAUDE_HOME is scratch too, so no test can touch the real settings.json.
        os.environ["NJ_GOV4_SELFTEST"] = reg.token_hex(8)
        os.environ["CLAUDE_HOME"] = os.path.join(tmp, "claude-home")
        os.makedirs(os.environ["CLAUDE_HOME"], exist_ok=True)
        for d_ in (os.environ["NJ_HOME"], os.path.join(tmp, "nj")):
            os.makedirs(d_, exist_ok=True)
            write_text(os.path.join(d_, "selftest.marker"), os.environ["NJ_GOV4_SELFTEST"] + "\n")
        try:
            sn = snap()
            t.check(sn.glob_match("src/**", "src/a/b") and sn.glob_match("*.py", "x.py") and not sn.glob_match("*.py", "d/x.py")
                    and sn.glob_match("drafts/*/meta.json", "drafts/a/meta.json") and sn.glob_match("**/CLAUDE.md", "CLAUDE.md"), "glob matcher")
            t.check(not needs_ticket(["doctor", "--quiet"]) and needs_ticket(["merge", "x"]) and not needs_ticket(["snapshot", "diff", "p"])
                    and needs_ticket(["snapshot", "begin", "p"]) and not needs_ticket(["live", "acquire"]) and needs_ticket(["live", "--pause"])
                    and not needs_ticket(["rollback", "--selftest"]) and needs_ticket(["rollback"]), "ticket requirement table")
            t.check(parse_worktrees_z("worktree /a\0HEAD abc\0branch refs/heads/main\0\0worktree /b\0HEAD def\0detached\0\0")[1]["path"] == "/b", "worktree list -z parser")
            t.check(peak_from_verify("peak live subagents: 11 (x)\n429/529 incidents: 0 (target 0)") == (11, 0), "verify output parser")
            out("selftest: doctor, lint, cache, tags")
            selftest_doctor(t)
            out("selftest: tickets, modes, wave, live, install-bin, snapshot")
            selftest_infra(t, tmp)
            out("selftest: help flags (H8)")
            selftest_help(t, tmp)
            out("selftest: hardening round H2 (settings merge, D20/D26/D27, A3, A7, CD-5, TV-2)")
            selftest_h2(t, tmp)
            out("selftest: git flows on a temp repo (no network)")
            selftest_git(t, tmp)
            out("selftest: snapshot module")
            t.check(snap().selftest() == 0, "gov4_snapshot selftest")
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
    out(f"gov4 selftest: {t.n - len(t.fails)}/{t.n} checks passed" + ("" if not t.fails else f"; FAILED: {t.fails}"))
    return 1 if t.fails else 0


# ------------------------------------------------------------------ help ---

HELP_WORDS = ("-h", "--help", "help")
TEXT_OPTS = ("-m", "--message", "--reason", "--no-gates", "--reviewed-by")


def wants_help(rest):
    """True when -h, --help or help is among the arguments (an option's text value, such as `-m help`, does not count)."""
    return any(a in HELP_WORDS and (i == 0 or rest[i - 1] not in TEXT_OPTS) for i, a in enumerate(rest))


def usage_lines(sub):
    """The module docstring's usage line(s) for a subcommand: every command line that names it, plus continuation lines."""
    lines = (__doc__ or "").splitlines()
    pat = re.compile(r"(?:^|\|\s*)" + re.escape(sub) + r"(?=[\s|]|$)")
    found = []
    i = 0
    while i < len(lines):
        raw = lines[i]
        txt = re.sub(r"^(?:READ-ONLY[^:]*:|WRITE[^:]*:)\s*", "", raw.strip())
        indented = raw.startswith("  ") or raw.startswith("READ-ONLY") or raw.startswith("WRITE")
        if indented and pat.search(txt):
            found.append(raw.rstrip())
            while i + 1 < len(lines) and len(lines[i + 1]) - len(lines[i + 1].lstrip()) >= 30 and not lines[i + 1].lstrip().startswith("|"):
                i += 1
                found.append(lines[i].rstrip())
        i += 1
    return found


def print_usage(sub):
    found = usage_lines(sub)
    out(f"usage: gov4.py {sub} ...   (help flag: nothing was run and nothing was written)")
    for ln in found:
        out(ln)
    if not found:
        out("(no dedicated usage line; run gov4.py --help for the full list)")
    return 0


# ------------------------------------------------------------------ main ---

COMMANDS = {
    "checkpoint": cmd_checkpoint, "queue": cmd_queue, "review": cmd_review, "preflight": cmd_preflight, "merge": cmd_merge,
    "push": cmd_push, "sweep": cmd_sweep, "live": cmd_live, "wave": cmd_wave, "mode": cmd_mode, "enforce-ready": cmd_enforce_ready,
    "unlock": cmd_unlock, "install-repo": cmd_install_repo, "install-bin": cmd_install_bin, "install-settings": cmd_install_settings, "snapshot": cmd_snapshot,
    "smoke-attest": cmd_smoke_attest, "rollback": cmd_rollback, "doctor": cmd_doctor, "status": cmd_status,
}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    dropped = sanitize_env()
    if os.environ.get("CLAUDE_HOME") and not os.environ.get("NJ_HOME"):
        os.environ["NJ_HOME"] = os.path.join(os.environ["CLAUDE_HOME"], "nj")
    if not argv or argv[0] in ("-h", "--help", "help"):
        out(__doc__)
        return 0
    sub = argv[0]
    if sub == "version" or sub == "--version":
        out(GOV)
        return 0
    if sub == "selftest":
        return print_usage("selftest") if wants_help(argv[1:]) else selftest()
    if sub not in COMMANDS:
        out(f"gov4.py: unknown subcommand '{sub}'. Try --help.")
        return 2
    if wants_help(argv[1:]):
        # H8: a help flag never reaches a handler or the ticket check; nothing is written, not even an event line
        return print_usage(sub)
    if dropped and reg.home_ok():
        reg.log_event({"event": "env-ignored", "sub": sub, "mode": reg.get_mode(), "reason": "untrusted caller set " + ", ".join(dropped)})
    if not ticket_ok(argv):
        out(f"gov4.py {sub}: refused, no valid ticket. In enforce mode write subcommands run from the Lead session (the PreToolUse hook attaches a "
            f"single-use ticket bound to this exact command) or by a human at a terminal; agents, jobs and unknown callers cannot use them.")
        return 3
    try:
        return COMMANDS[sub](argv[1:]) or 0
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
