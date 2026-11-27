#!/usr/bin/env python3
"""NJ Governance v4: non-git flow (spec section 4, "Non-git folders"; clause 0.24). Stdlib only.

  gov4_snapshot.py begin  <project> --run <rid> [--accept-drift]
  gov4_snapshot.py diff   <project> --run <rid>
  gov4_snapshot.py apply  <project> --run <rid> [--no-receipts "<reason>"]
  gov4_snapshot.py commit <project> --run <rid> [-m "<message>"] [--no-gates "<reason>"]
  gov4_snapshot.py selftest

`gov4.py snapshot ...` delegates here. Nothing is ever created inside the project folder.

begin   sha256 manifest (excluding node_modules, .venv, target, build, .idea, dist, .git, __pycache__, .agent-ops,
        .claude/worktrees), THEN a zip in <sources>/<proj>-pre-<rid>.zip, the claims of the run
        (.agent-ops/claims/<rid>.json written by `relay.py claim`) copied into the run record, and a shadow bare
        repo <shadow>/<proj>.git used with --work-tree=<project>. Refuses when the tree drifted from the last
        committed manifest (unreviewed changes), unless --accept-drift.
diff    the tree against the run manifest. Every change must lie in the union of claims; each receipt's files
        (.agent-ops/results/<rid>/*.json) must lie in that agent's claim and the union of receipts must equal the diff.
apply   the same checks; an empty change set is a no-op; otherwise the changes are staged in the shadow repo.
commit  gates first (the project's .nj/gates.json via the caller, or --no-gates "<reason>" which is logged), then the
        shadow commit; the committed manifest becomes the new drift baseline.

Locations: <sources> = $NJ_SOURCES_DIR or D:/projects/_sources; <shadow> = $NJ_SHADOW_DIR or
D:/projects/_shadow. The run record <sources>/<proj>-pre-<rid>.manifest.json holds manifest, claims and state.
"""
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import zipfile

EXCLUDE_DIRS = {"node_modules", ".venv", "target", "build", ".idea", "dist", ".git", "__pycache__", ".agent-ops"}
EXCLUDE_PATHS = (".claude/worktrees",)
DEFAULT_SOURCES = "D:/projects/_sources"
DEFAULT_SHADOW = "D:/projects/_shadow"
NT = os.name == "nt"


def sources_dir():
    return os.environ.get("NJ_SOURCES_DIR") or DEFAULT_SOURCES


def shadow_dir():
    return os.environ.get("NJ_SHADOW_DIR") or DEFAULT_SHADOW


def norm(p):
    return str(p).replace("\\", "/")


def proj_name(root):
    return re.sub(r"[^A-Za-z0-9_.-]", "-", os.path.basename(os.path.abspath(root).rstrip("/\\")) or "project")


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


# ------------------------------------------------------------------ glob ---

def glob_re(pat):
    pat = norm(pat).lstrip("./") if norm(pat).startswith("./") else norm(pat)
    out, i = "", 0
    while i < len(pat):
        c = pat[i]
        if c == "*":
            if pat[i:i + 2] == "**":
                if pat[i:i + 3] == "**/":
                    out += "(?:.*/)?"
                    i += 3
                    continue
                out += ".*"
                i += 2
                continue
            out += "[^/]*"
        elif c == "?":
            out += "[^/]"
        else:
            out += re.escape(c)
        i += 1
    return out


def glob_match(pat, path):
    """Path glob with ** support. A pattern without a wildcard also matches everything below it."""
    pat, path = norm(pat), norm(path)
    if pat.startswith("./"):
        pat = pat[2:]
    if path.startswith("./"):
        path = path[2:]
    if NT:
        pat, path = pat.lower(), path.lower()
    rx = glob_re(pat)
    if re.fullmatch(rx, path):
        return True
    if not any(ch in pat for ch in "*?"):
        base = pat.rstrip("/")
        return path == base or path.startswith(base + "/")
    if pat.endswith("/"):
        return bool(re.fullmatch(glob_re(pat.rstrip("/")) + "(?:/.*)?", path))
    return False


def in_union(patterns, path):
    return any(glob_match(p, path) for p in patterns)


# ---------------------------------------------------------------- manifest ---

def excluded_rel(rel):
    rel = norm(rel)
    return any(rel == x or rel.startswith(x + "/") for x in EXCLUDE_PATHS)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def scan(root):
    """{relpath: {"sha256", "size"}} for every file under root except excluded directories."""
    root = os.path.abspath(root)
    out = {}
    for dp, dns, fns in os.walk(root):
        rel_dir = norm(os.path.relpath(dp, root))
        rel_dir = "" if rel_dir == "." else rel_dir
        dns[:] = sorted(d for d in dns if d not in EXCLUDE_DIRS and not excluded_rel((rel_dir + "/" + d).lstrip("/")))
        for fn in sorted(fns):
            rel = (rel_dir + "/" + fn).lstrip("/")
            full = os.path.join(dp, fn)
            if os.path.islink(full) or not os.path.isfile(full):
                continue
            try:
                out[rel] = {"sha256": sha256_file(full), "size": os.path.getsize(full)}
            except OSError:
                out[rel] = {"sha256": "unreadable", "size": -1}
    return out


def compare(old, new):
    added = sorted(set(new) - set(old))
    deleted = sorted(set(old) - set(new))
    modified = sorted(k for k in set(old) & set(new) if old[k]["sha256"] != new[k]["sha256"])
    return added, modified, deleted


# ------------------------------------------------------------------- state ---

def write_json_atomic(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def record_path(root, rid):
    return os.path.join(sources_dir(), f"{proj_name(root)}-pre-{rid}.manifest.json")


def zip_path(root, rid):
    return os.path.join(sources_dir(), f"{proj_name(root)}-pre-{rid}.zip")


def current_path(root):
    return os.path.join(sources_dir(), f"{proj_name(root)}.current.manifest.json")


def shadow_path(root):
    return os.path.join(shadow_dir(), f"{proj_name(root)}.git")


def open_runs(root):
    out = []
    pref = f"{proj_name(root)}-pre-"
    try:
        names = os.listdir(sources_dir())
    except OSError:
        return out
    for n in sorted(names):
        if n.startswith(pref) and n.endswith(".manifest.json"):
            d = read_json(os.path.join(sources_dir(), n), {})
            if d.get("state") in ("begun", "applied"):
                out.append(d.get("run"))
    return out


def rel_to_root(root, p):
    """An absolute path inside the project root (either slash style, any drive-letter case) becomes project-relative;
    an absolute path outside the root is returned unchanged (and therefore matches no relative change: refused)."""
    q = norm(p)
    if q.startswith("./"):
        q = q[2:]
    if not (re.match(r"^[A-Za-z]:/", q) or q.startswith("/")):
        return q
    r = norm(os.path.abspath(root)).rstrip("/")
    cmp_q, cmp_r = (q.lower(), r.lower()) if (NT or re.match(r"^[A-Za-z]:/", q)) else (q, r)
    if cmp_q == cmp_r:
        return "."
    if cmp_q.startswith(cmp_r + "/"):
        return q[len(r) + 1:]
    return q


def norm_claims(root, claims):
    out = []
    for c in claims if isinstance(claims, list) else []:
        if isinstance(c, dict):
            c = dict(c)
            c["paths"] = [rel_to_root(root, x) for x in c.get("paths", [])]
            out.append(c)
    return out


def claims_of(root, rid):
    d = read_json(os.path.join(root, ".agent-ops", "claims", f"{rid}.json"), [])
    return norm_claims(root, d)


def receipts_of(root, rid):
    out = []
    rdir = os.path.join(root, ".agent-ops", "results", rid)
    if os.path.isdir(rdir):
        for n in sorted(os.listdir(rdir)):
            if n.endswith(".json"):
                d = read_json(os.path.join(rdir, n), None)
                if isinstance(d, dict) and d.get("agent"):
                    out.append(d)
    return out


# ------------------------------------------------------------------- git ---

def git_env():
    env = dict(os.environ)
    for k, v in (("GIT_AUTHOR_NAME", "nj-gov4"), ("GIT_AUTHOR_EMAIL", "gov4@localhost"),
                 ("GIT_COMMITTER_NAME", "nj-gov4"), ("GIT_COMMITTER_EMAIL", "gov4@localhost")):
        env.setdefault(k, v)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    return env


def shadow_git(root, args, check=True):
    g = shadow_path(root)
    cmd = ["git", f"--git-dir={g}", f"--work-tree={os.path.abspath(root)}", "-c", "core.bare=false",
           "-c", "core.autocrlf=false", "-c", "core.quotepath=false", "-c", "core.safecrlf=false"] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=git_env())
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {(r.stderr or r.stdout).strip()[:300]}")
    return r


def ensure_shadow(root):
    g = shadow_path(root)
    if not os.path.isdir(g):
        os.makedirs(os.path.dirname(g), exist_ok=True)
        r = subprocess.run(["git", "init", "--bare", "-q", "-b", "main", g], capture_output=True, text=True, env=git_env())
        if r.returncode != 0:
            raise RuntimeError(f"git init --bare failed: {r.stderr.strip()[:200]}")
    ex = os.path.join(g, "info", "exclude")
    os.makedirs(os.path.dirname(ex), exist_ok=True)
    want = "\n".join(sorted(f"{d}/" for d in EXCLUDE_DIRS) + [f"/{p}/" for p in EXCLUDE_PATHS]) + "\n"
    try:
        have = open(ex, encoding="utf-8").read()
    except OSError:
        have = ""
    if have != want:
        with open(ex, "w", encoding="utf-8", newline="\n") as f:
            f.write(want)
    return g


def shadow_commit(root, message):
    """Stage everything in the shadow repo and commit when something changed. Returns the sha, or None."""
    shadow_git(root, ["add", "-A", "."])
    if shadow_git(root, ["diff", "--cached", "--quiet"], check=False).returncode == 0:
        return None
    shadow_git(root, ["commit", "-q", "-m", message])
    return shadow_git(root, ["rev-parse", "HEAD"]).stdout.strip()


# ---------------------------------------------------------------- commands ---

def make_zip(root, rid, manifest):
    zp = zip_path(root, rid)
    os.makedirs(os.path.dirname(zp), exist_ok=True)
    tmp = zp + f".{os.getpid()}.tmp"
    pn = proj_name(root)
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in sorted(manifest):
            z.write(os.path.join(root, rel), f"{pn}/{rel}")
    os.replace(tmp, zp)
    return zp


def cmd_begin(root, rid, accept_drift, out):
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        out(f"snapshot begin: {root} is not a directory")
        return 2
    if os.path.isdir(os.path.join(root, ".git")):
        out("snapshot begin: this is a git repository; use checkpoint, worktrees and merge (the snapshot flow is for non-git folders)")
        return 2
    if os.path.exists(record_path(root, rid)):
        out(f"snapshot begin: run {rid} already has a record ({record_path(root, rid)}); use a new run id")
        return 1
    others = [r for r in open_runs(root) if r != rid]
    if others:
        out(f"snapshot begin: refused, run {others[0]} is still open for {proj_name(root)} (commit it first)")
        return 1
    manifest = scan(root)
    cur = read_json(current_path(root), None)
    if cur and not accept_drift:
        a, m, d = compare(cur.get("files", {}), manifest)
        if a or m or d:
            out(f"snapshot begin: DRIFT refused, the tree changed since the last committed manifest "
                f"(+{len(a)} ~{len(m)} -{len(d)}: {', '.join((a + m + d)[:5])}); review it, or pass --accept-drift")
            return 1
    zp = make_zip(root, rid, manifest)                       # zip FIRST (spec section 4 item 2)
    g = ensure_shadow(root)
    base = shadow_commit(root, f"baseline before run {rid}\n\nTask-Id: {rid}")
    rec = {"project": proj_name(root), "root": norm(root), "run": rid, "ts": now_iso(), "state": "begun",
           "files": manifest, "claims": claims_of(root, rid), "zip": norm(zp), "shadow": norm(g),
           "baseline_commit": base, "excludes": sorted(EXCLUDE_DIRS)}
    write_json_atomic(record_path(root, rid), rec)
    if not cur:
        write_json_atomic(current_path(root), {"project": proj_name(root), "run": rid, "ts": now_iso(), "files": manifest})
    out(f"snapshot begin ok: {len(manifest)} files, zip {zp}, shadow {g}, claims {len(rec['claims'])}")
    return 0


def change_problems(root, rec, changes):
    """Spec section 4 item 4. Returns a list of problems (empty = clean)."""
    added, modified, deleted = changes
    allc = sorted(set(added) | set(modified) | set(deleted))
    claims = norm_claims(root, rec.get("claims", []))
    union = [p for c in claims for p in c.get("paths", [])]
    problems = []
    outside = [c for c in allc if not in_union(union, c)]
    if outside:
        problems.append(f"{len(outside)} change(s) outside the union of claims: {', '.join(outside[:5])}")
    receipts = receipts_of(root, rec["run"])
    rfiles = set()
    for r in receipts:
        agent = r.get("agent")
        own = [p for c in claims if c.get("agent") == agent for p in c.get("paths", [])]
        files = [rel_to_root(root, f) for f in (r.get("files") or [])]
        bad = [f for f in files if not in_union(own, f)]
        if bad:
            problems.append(f"receipt of {agent}: CHANGED outside its own claim: {', '.join(bad[:4])}")
        rfiles |= set(files)
    if receipts:
        pats = [f for f in rfiles if any(ch in f for ch in "*?")]
        exact = rfiles - set(pats)
        missing = [c for c in allc if c not in exact and not in_union(pats, c)]
        extra = [f for f in exact if f not in allc]
        if missing or extra:
            problems.append(f"union of receipts != manifest diff: missing {missing[:4]} extra {extra[:4]}")
    return problems, bool(receipts)


def load_record(root, rid, out):
    rec = read_json(record_path(root, rid), None)
    if not rec:
        out(f"snapshot: no record for run {rid} ({record_path(root, rid)}); run `snapshot begin` first")
        return None
    return rec


def cmd_diff(root, rid, out, quiet=False):
    root = os.path.abspath(root)
    rec = load_record(root, rid, out)
    if not rec:
        return 2, None, None
    now = scan(root)
    ch = compare(rec["files"], now)
    problems, has_receipts = change_problems(root, rec, ch)
    if not quiet:
        a, m, d = ch
        out(f"snapshot diff {rid}: +{len(a)} ~{len(m)} -{len(d)}"
            + ("" if (a or m or d) else " (empty change set)"))
        for tag, lst in (("A", a), ("M", m), ("D", d)):
            for f in lst[:25]:
                out(f"  {tag} {f}")
        for p in problems:
            out(f"  PROBLEM {p}")
        if not has_receipts and (a or m or d):
            out("  NOTE no receipts in .agent-ops/results/" + rid + " yet")
    return (1 if problems else 0), ch, (problems, has_receipts)


def cmd_apply(root, rid, no_receipts, out):
    root = os.path.abspath(root)
    rc, ch, extra = cmd_diff(root, rid, out, quiet=True)
    if rc == 2:
        return 2
    rec = read_json(record_path(root, rid), {})
    added, modified, deleted = ch
    if not (added or modified or deleted):
        out(f"snapshot apply {rid}: empty change set, nothing to do")
        return 0
    problems, has_receipts = extra
    if problems:
        for p in problems:
            out(f"snapshot apply refused: {p}")
        return 1
    if not has_receipts:
        if not no_receipts:
            out(f"snapshot apply refused: no receipts in .agent-ops/results/{rid}; pass --no-receipts \"<reason>\" to log an exception")
            return 1
        rec.setdefault("exceptions", []).append({"no_receipts": no_receipts, "ts": now_iso()})
    ensure_shadow(root)
    shadow_git(root, ["add", "-A", "."])
    rec["state"] = "applied"
    rec["applied"] = {"ts": now_iso(), "added": added, "modified": modified, "deleted": deleted}
    rec["applied_files"] = scan(root)
    write_json_atomic(record_path(root, rid), rec)
    out(f"snapshot apply ok: {len(added)} added, {len(modified)} modified, {len(deleted)} deleted staged in the shadow repo")
    return 0


def cmd_commit(root, rid, message, no_gates, gates_runner, out):
    root = os.path.abspath(root)
    rec = load_record(root, rid, out)
    if not rec:
        return 2
    if rec.get("state") == "committed":
        out(f"snapshot commit {rid}: already committed ({rec.get('commit')})")
        return 0
    if rec.get("state") != "applied":
        # an empty run needs no apply
        now = scan(root)
        if compare(rec["files"], now) == ([], [], []):
            rec["state"] = "committed"
            rec["commit"] = None
            write_json_atomic(record_path(root, rid), rec)
            out(f"snapshot commit {rid}: empty change set, no-op")
            return 0
        out(f"snapshot commit refused: run {rid} is {rec.get('state')}, run `snapshot apply` first")
        return 1
    now = scan(root)
    a, m, d = compare(rec.get("applied_files", {}), now)
    if a or m or d:
        out(f"snapshot commit refused: the tree changed after apply (+{len(a)} ~{len(m)} -{len(d)}); apply again")
        return 1
    has_gates = os.path.isfile(os.path.join(root, ".nj", "gates.json"))
    gate_note = ""
    if has_gates:
        if no_gates:
            out("snapshot commit refused: the project has .nj/gates.json; gates are never cut (--no-gates is for projects without a gate list)")
            return 1
        if gates_runner is None:
            out("snapshot commit refused: gates cannot run from this entry point; use gov4.py snapshot commit")
            return 1
        ok, lines = gates_runner(root)
        for ln in lines:
            out("  gate " + ln)
        if not ok:
            out("snapshot commit refused: a gate failed; nothing was committed")
            return 1
        gate_note = "; ".join(lines)[:500]
    else:
        if not no_gates:
            out("snapshot commit refused: no .nj/gates.json; pass --no-gates \"<reason>\" (logged)")
            return 1
        rec.setdefault("exceptions", []).append({"no_gates": no_gates, "ts": now_iso()})
        gate_note = f"no gates: {no_gates}"
    msg = (message or f"run {rid}") + f"\n\nTask-Id: {rid}\nGates: {gate_note or 'none'}"
    sha = shadow_commit(root, msg)
    rec["state"] = "committed"
    rec["commit"] = sha
    rec["committed_ts"] = now_iso()
    write_json_atomic(record_path(root, rid), rec)
    write_json_atomic(current_path(root), {"project": proj_name(root), "run": rid, "ts": now_iso(), "files": now})
    out(f"snapshot commit ok: shadow commit {sha or 'none (no content change)'}")
    return 0


def main(argv=None, gates_runner=None, out=print):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        out(__doc__)
        return 0
    sub = argv[0]
    if sub == "selftest":
        return selftest()
    rest = argv[1:]
    pos = [a for a in rest if not a.startswith("-")]

    def opt(name, default=None):
        if name in rest:
            i = rest.index(name)
            return rest[i + 1] if i + 1 < len(rest) else default
        return default
    flagvals = {opt("--run"), opt("--no-receipts"), opt("--no-gates"), opt("-m")}
    pos = [a for a in pos if a not in flagvals]
    root = pos[0] if pos else os.getcwd()
    rid = opt("--run")
    if sub not in ("begin", "diff", "apply", "commit"):
        out(f"unknown snapshot subcommand: {sub} (begin|diff|apply|commit)")
        return 2
    if not rid:
        out(f"snapshot {sub}: --run <rid> is required")
        return 2
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", rid):
        out("snapshot: run id may only contain letters, digits, . _ -")
        return 2
    try:
        if sub == "begin":
            return cmd_begin(root, rid, "--accept-drift" in rest, out)
        if sub == "diff":
            return cmd_diff(root, rid, out)[0]
        if sub == "apply":
            return cmd_apply(root, rid, opt("--no-receipts"), out)
        return cmd_commit(root, rid, opt("-m"), opt("--no-gates"), gates_runner, out)
    except RuntimeError as e:
        out(f"snapshot {sub} failed: {e}")
        return 1


# ----------------------------------------------------------------- selftest ---

def selftest():
    failures = []

    def check(cond, label):
        if not cond:
            failures.append(label)
            print(f"  FAIL {label}")

    with tempfile.TemporaryDirectory(prefix="gov4snap-") as tmp:
        os.environ["NJ_SOURCES_DIR"] = os.path.join(tmp, "_sources")
        os.environ["NJ_SHADOW_DIR"] = os.path.join(tmp, "_shadow")
        proj = os.path.join(tmp, "demo")
        for rel, txt in (("src/a.txt", "A"), ("src/b.txt", "B"), ("docs/readme.md", "R"), ("node_modules/x/i.js", "J"),
                         ("build/o.bin", "O")):
            fp = os.path.join(proj, rel)
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            open(fp, "w").write(txt)
        lines = []
        o = lines.append
        check(glob_match("src/**", "src/a/b.txt") and not glob_match("src/*", "src/a/b.txt")
              and glob_match("src", "src/x") and not glob_match("src/a", "src/ab"), "glob semantics")
        m = scan(proj)
        check(sorted(m) == ["docs/readme.md", "src/a.txt", "src/b.txt"], f"scan excludes node_modules/build: {sorted(m)}")
        rc = main(["begin", proj, "--run", "r1"], out=o)
        check(rc == 0, f"begin rc={rc} {lines}")
        zp = zip_path(proj, "r1")
        names = zipfile.ZipFile(zp).namelist() if os.path.exists(zp) else []
        check(len(names) == 3 and not any("node_modules" in n or "build" in n for n in names), f"zip content {names}")
        check(os.path.isdir(shadow_path(proj)) and not os.path.exists(os.path.join(proj, ".git")), "shadow outside, no .git inside")
        check(subprocess.run(["git", f"--git-dir={shadow_path(proj)}", "log", "--oneline"], capture_output=True, text=True).stdout.strip() != "",
              "shadow baseline commit exists")
        # claims for the run
        cd = os.path.join(proj, ".agent-ops", "claims")
        os.makedirs(cd, exist_ok=True)
        json.dump([{"agent": "w1", "paths": ["src/**"]}], open(os.path.join(cd, "r1.json"), "w"))
        rec = read_json(record_path(proj, "r1"))
        rec["claims"] = claims_of(proj, "r1")
        write_json_atomic(record_path(proj, "r1"), rec)
        lines.clear()
        rc = main(["apply", proj, "--run", "r1"], out=o)
        check(rc == 0 and any("empty change set" in l for l in lines), f"empty change set is a no-op {lines}")
        ap = norm(os.path.abspath(proj))
        flip = ap[0].swapcase() + ap[1:]
        check(rel_to_root(proj, ap + "/src/**") == "src/**" and rel_to_root(proj, ap.replace("/", chr(92)) + chr(92) + "src") == "src"
              and rel_to_root(proj, flip + "/src/a.txt") == "src/a.txt" and rel_to_root(proj, ap) == ".", "absolute claim inside the root becomes relative (both slashes, mixed-case drive)")
        check(rel_to_root(proj, "C:/elsewhere/x.txt") == "C:/elsewhere/x.txt" and not glob_match(rel_to_root(proj, "C:/elsewhere/**"), "src/a.txt"), "absolute claim outside the root stays absolute")
        rec = read_json(record_path(proj, "r1"))
        rec["claims"] = [{"agent": "w1", "paths": [flip + "/src/**"]}]
        write_json_atomic(record_path(proj, "r1"), rec)
        open(os.path.join(proj, "src", "a.txt"), "w").write("A2")
        open(os.path.join(proj, "docs", "readme.md"), "w").write("R2")
        lines.clear()
        rc = main(["diff", proj, "--run", "r1"], out=o)
        check(rc == 1 and any("outside the union of claims" in l for l in lines), f"outside-claim change refused {lines}")
        open(os.path.join(proj, "docs", "readme.md"), "w").write("R")
        lines.clear()
        rc = main(["apply", proj, "--run", "r1"], out=o)
        check(rc == 1 and any("no receipts" in l for l in lines), f"apply without receipts refused {lines}")
        rd = os.path.join(proj, ".agent-ops", "results", "r1")
        os.makedirs(rd, exist_ok=True)
        json.dump({"agent": "w1", "files": ["src/a.txt"]}, open(os.path.join(rd, "w1.json"), "w"))
        lines.clear()
        rc = main(["apply", proj, "--run", "r1"], out=o)
        check(rc == 0 and any("apply ok" in l for l in lines), f"apply ok {lines}")
        rec = read_json(record_path(proj, "r1"))
        rec["claims"] = [{"agent": "w1", "paths": ["C:/elsewhere/**"]}]
        write_json_atomic(record_path(proj, "r1"), rec)
        lines.clear()
        rc = main(["diff", proj, "--run", "r1"], out=o)
        check(rc == 1 and any("outside the union of claims" in l for l in lines), f"absolute claim outside the root is refused {lines}")
        rec["claims"] = [{"agent": "w1", "paths": [flip + "/src/**"]}]
        write_json_atomic(record_path(proj, "r1"), rec)
        lines.clear()
        rc = main(["commit", proj, "--run", "r1"], out=o)
        check(rc == 1 and any("--no-gates" in l for l in lines), f"commit needs gates or --no-gates {lines}")
        lines.clear()
        rc = main(["commit", proj, "--run", "r1", "--no-gates", "selftest has no gate list"], out=o)
        check(rc == 0 and any("commit ok" in l for l in lines), f"commit with logged --no-gates {lines}")
        open(os.path.join(proj, "src", "b.txt"), "w").write("DRIFT")
        lines.clear()
        rc = main(["begin", proj, "--run", "r2"], out=o)
        check(rc == 1 and any("DRIFT" in l for l in lines) and not os.path.exists(zip_path(proj, "r2")), f"drift refused before the zip {lines}")
        lines.clear()
        rc = main(["begin", proj, "--run", "r2", "--accept-drift"], out=o)
        check(rc == 0, f"--accept-drift begins {lines}")
    print("gov4_snapshot selftest: " + ("ok" if not failures else f"FAILED ({len(failures)})"))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
