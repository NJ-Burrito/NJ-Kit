#!/usr/bin/env python3
"""NJ Governance v4 hook (stdlib only). One entry point for every Claude Code hook the method uses.

  gov4_hook.py agent|git|bash|write|mcp|workflow|start|stop-team|stop-helper|session-start|ticket|reap  < hook-json
  (bash = git then ticket in one process, A10)
  gov4_hook.py selftest            gov4_hook.py --trace [sub]  (log-only, never blocks, D3)

Exit codes: 0 allow, 2 deny (stderr is the reason shown to the model). Modes (gov4_registry.get_mode):
off = inert, audit (default) = log the would-deny and exit 0, enforce = deny. Fail policy: an internal
exception denies only an Agent spawn in enforce mode; every other hook allows and raises ALERT-hook.flag.

Identity (spec section 2, tested in this order): job (NJ_ROLE=job) > agent (agent_id in the payload) >
lead (session registered by `session-start` in leads.json, no agent_id) > unknown.
Start-up budget: stdlib only, heavy modules (subprocess, check_governance) load lazily.
"""
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import gov4_registry as reg  # noqa: E402

WIN = os.name == "nt"
GIT_RE = re.compile(r"(?<![A-Za-z0-9])git(?![A-Za-z0-9])", re.I)
LI_RE = re.compile(r"li\.py", re.I)
WRITE_VERB_RE = re.compile(r"\b(push|merge|rebase|reset|tag|update-ref|remote|config|fetch|pull|cherry-pick|worktree|checkout|"
                           r"switch|branch|commit|clean|stash|apply|revert|restore|gc|prune|hooksPath)\b", re.I)
SECRET_RE = re.compile(r"\.config[/\\]linkedin|\.credentials|\.git-credentials|cmdkey|vaultcmd|Windows[/\\]Credentials|"
                       r"git\s+credential|credential[- ]?manager", re.I)
GIT_ENV_RE = re.compile(r"(?<![A-Za-z0-9_])GIT_[A-Z0-9_]+\s*=|\$env:GIT_\w+|\[Environment\]::SetEnvironmentVariable\(\s*['\"]GIT_", re.I)
LI_VERBS = {"post", "comment", "like", "due"}
GOV4_SCRIPTS = {"gov4.py", "gov4_registry.py", "gov4_snapshot.py"}
GOV4_NAMES = {"gov4", "gov4_registry", "gov4_snapshot"}
# marker text in the first lines of each gov4 script: a renamed or copied file is still recognised (SB-03)
GOV4_MARKERS = {"the Lead's command line": "gov4.py", "machine registry and shared state": "gov4_registry.py",
                "non-git flow": "gov4_snapshot.py"}
GOV4_READ_SUBS = {"status", "live", "queue", "review", "doctor", "preflight", "selftest", "enforce-ready", "board", "digest",
                  "version", "list", "show", "help", "--help", "-h", "--version"}
KNOWN_GOV4_SUBS = set(reg.WRITE_SUBS) | GOV4_READ_SUBS | {"snapshot", "rollback", "live", "enforce-ready"}
# Core environment names that switch governance off for a child process are always flagged. Other NJ_* names and the
# home-like names are flagged when the command also touches git, gh, li.py, gov4 or claude (a test run may set NJ_HOME).
CORE_ENV = r"NJ_MODE_OVERRIDE|NJ_TICKETS?|NJ_TICKET_FORCE|NJ_ROLE|NJ_SOFT|NJ_WAVE_OVERRIDE|NJ_WRITE_ALLOW|HOME|USERPROFILE"
ANY_ENV = r"NJ_[A-Z0-9_]+|HOME|USERPROFILE|HOMEDRIVE|HOMEPATH|XDG_[A-Z_]+|APPDATA|LOCALAPPDATA"


def _env_re(names):
    return re.compile(r"(?<![A-Za-z0-9_])(?:" + names + r")\s*=|\$env:(?:" + names + r")(?![A-Za-z0-9_])|"
                      r"\[Environment\]::SetEnvironmentVariable\(\s*['\"](?:" + names + r")|\bsetx\s+(?:" + names + r")\b", re.I)


CORE_ENV_RE = _env_re(CORE_ENV)
ANY_ENV_RE = _env_re(ANY_ENV)
CTX_RE = re.compile(r"(?<![A-Za-z0-9])git(?![A-Za-z0-9])|\bgh\b|li\.py|gov4|\bclaude\b|engage_daily|comments_watch|connect_weekly", re.I)
DYN_EXEC_RE = re.compile(r"\[(?:(?:System\.)?Diagnostics\.)?Process\]\s*::\s*Start|ProcessStartInfo|\.StartInfo\b|"
                         r"New-Object\s+(?:-TypeName\s+)?['\"(]?(?:(?:System\.)?Diagnostics\.)?Process\b|\[scriptblock\]\s*::\s*Create|"
                         r"\bInvoke-Expression\b|\bInvoke-Command\b|\biex\b|\bSet-Alias\b|\bNew-Alias\b|"
                         r"(?<![A-Za-z0-9_-])(?:sal|nal)\s+\w+\s+\w|(?<![A-Za-z0-9_-])alias\s+\w+=", re.I)
# H7 (TV-3 residual): Start-Process and its aliases launch a program the scanner may not see by name. For agent, job and
# unknown callers, any such launch that names git, gh or li.py in an argument, or builds its arguments at run time, is denied.
PS_LAUNCH_RE = re.compile(r"(?<![A-Za-z0-9_.$-])(?:Start-Process|saps)(?![A-Za-z0-9_-])|(?:^|[;&|(]\s*)start\s", re.I)
PS_LAUNCH_TARGET_RE = re.compile(r"(?<![A-Za-z0-9])(?:git|gh)(?:\.exe)?(?![A-Za-z0-9])|li\.py", re.I)
NO_VERIFY_RE = re.compile(r"(?<![A-Za-z0-9-])--no-verify(?![A-Za-z0-9-])", re.I)
PS_DYN_HEAD_RE = re.compile(r"(?:^|[;&|(\s])[&.]\s*[(\$]")
NJ_STATE_RE = re.compile(r"\.claude[/\\]+nj(?![A-Za-z0-9_-])|\.git[/\\]+hooks(?![A-Za-z0-9_-])", re.I)
OBF_RE = re.compile(r"['\"]\s*\+\s*['\"]|\bchr\(|\.join\(|base64|b64decode|fromhex|\\x[0-9a-f]{2}|\\u[0-9a-f]{4}|getattr\(|"
                    r"__import__|fromCharCode|\[::-1\]|\.decode\(", re.I)
SPAWN_RE = re.compile(r"subprocess|os\.system|os\.popen|\bPopen\b|child_process|execSync|spawnSync|\bspawn\(|\bexec[lv]p?e?\(|"
                      r"Start-Process|\bsystem\(", re.I)
_Q = r"""\\?["']"""
INLINE_WRITE_RES = [
    re.compile(r"\bopen\(\s*[rRbBuUf]*" + _Q + r"([^\"']+)" + _Q + r"\s*,\s*" + _Q + r"[^\"']*[wax+][^\"']*" + _Q),
    re.compile(r"Path\(\s*[rR]?" + _Q + r"([^\"']+)" + _Q + r"\s*\)\s*\.\s*(?:write_text|write_bytes|touch|unlink|rename|replace|mkdir|rmdir)"),
    re.compile(r"\bos\.(?:remove|unlink|rename|replace|rmdir|removedirs|makedirs|mkdir|truncate)\(\s*[rR]?" + _Q + r"([^\"']+)"),
    re.compile(r"\bshutil\.(?:copy|copy2|copyfile|move|copytree)\([^,()]*,\s*[rR]?" + _Q + r"([^\"']+)"),
    re.compile(r"\bshutil\.rmtree\(\s*[rR]?" + _Q + r"([^\"']+)"),
    re.compile(r"\bfs\.(?:writeFileSync|writeFile|appendFileSync|appendFile|unlinkSync|rmSync|renameSync|copyFileSync)\(\s*" + _Q + r"([^\"']+)"),
    re.compile(r"\[(?:System\.)?IO\.File\]\s*::\s*(?:Write|Append|Create|Open|Copy|Move|Delete|Replace|Set)\w*\(\s*" + _Q + r"([^\"']+)", re.I),
]
SHELLS = {"sh", "bash", "zsh", "dash", "ash", "ksh", "fish", "pwsh", "powershell", "cmd", "busybox"}
WRAPPERS = {"env", "command", "builtin", "exec", "nohup", "time", "sudo", "doas", "nice", "xargs", "timeout", "start-process", "saps",
            "start", "call", "invoke-expression", "iex", "invoke-command", "icm", "wsl", "stdbuf", "setsid", "eval", "runas",
            "invoke-item", "ii", "&", ".", "parallel", "watch", "flock", "strace", "ionice", "chrt", "taskset", "nsenter",
            "foreach-object", "where-object", "%", "?"}
INTERP = {"python", "python3", "py", "pythonw", "node", "nodejs", "deno", "bun", "ruby", "perl", "php", "lua", "cscript", "wscript"}
COPY_CMDS = {"cp", "mv", "copy", "move", "xcopy", "robocopy", "rsync", "ln", "copy-item", "move-item", "install"}
WRITE_FILE_CMDS = {"tee", "set-content", "add-content", "out-file", "new-item", "touch", "mkdir", "md", "ni", "sc", "ac"}
REMOVE_CMDS = {"rm", "del", "erase", "rd", "rmdir", "remove-item", "ri"}

GIT_READ = {"status", "diff", "log", "show", "rev-parse", "merge-tree", "ls-files", "ls-tree", "cat-file", "blame", "rev-list",
            "show-ref", "diff-tree", "diff-index", "diff-files", "name-rev", "describe", "shortlog", "grep", "check-ignore",
            "for-each-ref", "count-objects", "whatchanged", "help", "version", "var", "range-diff", "cherry", "ls-remote",
            "merge-base", "annotate", "show-branch", "verify-commit", "check-attr", "fsck", "diff-pairs"}
GIT_OWN_OPS = {"commit", "restore", "rm", "mv", "apply", "reset", "checkout", "stash", "add"}


def tmpdirs():
    out = {os.environ.get(k, "") for k in ("TEMP", "TMP", "TMPDIR")}
    out.discard("")
    return {npath(x) for x in out} | {"/tmp"}


# ------------------------------------------------------------------ paths ---

def npath(path, base=None):
    """Absolute, real (junctions and symlinks followed), forward slashes, no trailing slash."""
    if path is None or path == "":
        return ""
    s = str(path)
    if WIN:
        m = re.match(r"^/([A-Za-z])(/.*)?$", s)
        if m:
            s = f"{m.group(1).upper()}:{m.group(2) or '/'}"
    s = os.path.expanduser(s)
    if base and not os.path.isabs(s):
        s = os.path.join(base, s)
    s = os.path.realpath(os.path.abspath(s))
    return s.replace("\\", "/").rstrip("/") or "/"


def K(s):
    return s.lower() if WIN else s


def under(child, parent):
    c, pa = K(child), K(parent).rstrip("/")
    return c == pa or c.startswith(pa + "/")


_GLOBS = {}


def glob_re(pattern):
    if pattern not in _GLOBS:
        out, i = [], 0
        pat = pattern.replace("\\", "/")
        while i < len(pat):
            ch = pat[i]
            if pat.startswith("**/", i):
                out.append("(?:.*/)?")
                i += 3
                continue
            if pat.startswith("**", i):
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*" if ch == "*" else "[^/]" if ch == "?" else re.escape(ch))
            i += 1
        _GLOBS[pattern] = re.compile("".join(out) + r"\Z", re.I if WIN else 0)
    return _GLOBS[pattern]


def match_glob(pattern, rel):
    return bool(glob_re(pattern).match(rel.replace("\\", "/")))


def worktree_root(cwd):
    s = (cwd or "").replace("\\", "/")
    m = re.match(r"^(.*?/\.claude/worktrees/[^/]+)", s, re.I)
    return m.group(1) if m else None


def project_root(cwd):
    """Main checkout / project folder of a cwd: strips .claude/worktrees/<x>; else nearest .git or .agent-ops parent."""
    cwd = (cwd or os.getcwd()).replace("\\", "/")
    m = re.match(r"^(.*?)/\.claude/worktrees/[^/]+", cwd, re.I)
    if m:
        return m.group(1)
    d = cwd
    for _ in range(12):
        if os.path.exists(os.path.join(d, ".git")) or os.path.isdir(os.path.join(d, ".agent-ops")):
            return d
        nd = os.path.dirname(d)
        if nd == d or not nd:
            break
        d = nd
    return cwd


def git_dir_of(d):
    """Resolve a checkout's git dir by reading .git (file or dir); None when not a repo."""
    g = os.path.join(d, ".git")
    if os.path.isdir(g):
        return g
    try:
        with open(g, encoding="utf-8") as f:
            m = re.match(r"gitdir:\s*(.+)", f.read().strip())
        if m:
            t = m.group(1).strip()
            return t if os.path.isabs(t) else os.path.normpath(os.path.join(d, t))
    except OSError:
        pass
    return None


def in_git_repo(cwd):
    d = (cwd or "").replace("\\", "/")
    for _ in range(14):
        if d and os.path.exists(os.path.join(d, ".git")):
            return True
        nd = os.path.dirname(d)
        if not nd or nd == d:
            return False
        d = nd
    return False


def current_branch(d):
    """Branch name read from HEAD without running git; None when detached or not a repo."""
    cur = (d or "").replace("\\", "/")
    for _ in range(14):
        gd = git_dir_of(cur) if cur else None
        if gd:
            try:
                with open(os.path.join(gd, "HEAD"), encoding="utf-8") as f:
                    m = re.match(r"ref:\s*refs/heads/(.+)", f.read().strip())
                return m.group(1) if m else None
            except OSError:
                return None
        nd = os.path.dirname(cur)
        if not nd or nd == cur:
            return None
        cur = nd
    return None


def run(cmd, cwd=None, timeout=15):
    import subprocess
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except (OSError, subprocess.SubprocessError) as e:
        return 127, "", str(e)


# ---------------------------------------------------------------- context ---

class Ctx:
    pass


def make_ctx(sub, payload, raw=""):
    c = Ctx()
    c.sub, c.pl, c.raw = sub, payload if isinstance(payload, dict) else {}, raw
    c.tool = c.pl.get("tool_name") or ""
    c.tin = c.pl.get("tool_input") if isinstance(c.pl.get("tool_input"), dict) else {}
    c.cwd = c.pl.get("cwd") or os.getcwd()
    c.agent_id = c.pl.get("agent_id") or ""
    c.agent_type = c.pl.get("agent_type") or ""
    c.session = c.pl.get("session_id") or ""
    c.mode = reg.get_mode()
    if os.environ.get("NJ_ROLE") == "job":
        c.ident = "job"
    elif c.agent_id:
        c.ident = "agent"
    elif reg.is_lead(c.session):
        c.ident = "lead"
    else:
        c.ident = "unknown"
    c.info, c.src = reg.type_info(c.agent_type) if c.agent_id else (None, None)
    c.role = (c.info or {}).get("role") if c.info else None
    c.project = project_root(c.cwd)
    return c


def log_dec(ctx, rule, reason, action):
    reg.log_decision({"sub": ctx.sub, "ident": ctx.ident, "tool": ctx.tool, "rule": rule, "action": action, "mode": ctx.mode,
                      "reason": reason[:300], "agent_id": ctx.agent_id, "agent_type": ctx.agent_type,
                      "cmd": (ctx.tin.get("command") or ctx.tin.get("file_path") or "")[:200]})


def finish(ctx, findings):
    """findings = [(rule, reason, soft)]. Returns the exit code; audit logs and allows."""
    if not findings:
        return 0
    hard = [f for f in findings if not f[2]]
    deny = hard or (findings if reg.soft_active() else [])
    for rule, reason, soft in findings:
        log_dec(ctx, rule, reason, ("deny" if ctx.mode == "enforce" and (rule, reason, soft) in deny else
                                    "soft-would-deny" if soft and not deny else "would-deny"))
    if deny and ctx.mode == "enforce":
        sys.stderr.write("NJ governance (gov4) refused this call. " + "; ".join(f"{r}: {t}" for r, t, _ in deny) + "\n")
        return 2
    return 0


# -------------------------------------------------------------- tokeniser ---

class Unparseable(Exception):
    pass


class Tok(str):
    dyn = False


class Seg:
    def __init__(self):
        self.toks, self.redirs, self.hd = [], [], []


def _match_paren(s, i):
    depth = 0
    n = len(s)
    j = i
    while j < n:
        if s[j] == "(":
            depth += 1
        elif s[j] == ")":
            depth -= 1
            if depth == 0:
                return j
        j += 1
    raise Unparseable("unterminated $(")


def tokenise(cmd, escape=True, ps=False, bs_all=False):
    """Split a shell or PowerShell command line into segments. Raises Unparseable on unbalanced quoting."""
    segs, subs = [], []
    cur = Seg()
    buf = []
    state = {"has": False, "dyn": False, "redir": False}
    i, n = 0, len(cmd)

    def endtok():
        if state["has"]:
            t = Tok("".join(buf))
            t.dyn = state["dyn"]
            (cur.redirs if state["redir"] else cur.toks).append(t)
            state["redir"] = False
        buf.clear()
        state["has"] = False
        state["dyn"] = False

    def endseg():
        nonlocal cur
        endtok()
        if cur.toks or cur.hd:
            segs.append(cur)
        cur = Seg()

    while i < n:
        ch = cmd[i]
        if ch in " \t\r":
            endtok()
            i += 1
        elif ch in "\n;":
            endseg()
            i += 1
        elif ch == "&":
            if cmd.startswith("&>", i):
                endtok()
                i += 2
                if i < n and cmd[i] == ">":
                    i += 1
                state["redir"] = True
                continue
            endseg()
            i += 2 if cmd.startswith("&&", i) else 1
        elif ch == "|":
            endseg()
            i += 2 if cmd.startswith("||", i) else 1
        elif ch in "(){}" and not (buf and buf[-1] == "$"):
            endseg()
            i += 1
        elif ch == "<" and cmd.startswith("<<", i) and not cmd.startswith("<<<", i):
            if buf and "".join(buf).isdigit():
                buf.clear()
                state["has"] = False
            endtok()
            j = i + 2
            if j < n and cmd[j] == "-":
                j += 1
            while j < n and cmd[j] in " \t":
                j += 1
            m = re.match(r"""(['"]?)([A-Za-z0-9_\-.]+)\1""", cmd[j:])
            delim = m.group(2) if m else ""
            k = cmd.find("\n", j)
            body = ""
            if delim and k >= 0:
                lines = cmd[k + 1:].split("\n")
                got = []
                end = len(cmd)
                pos = k + 1
                for ln in lines:
                    if ln.strip() == delim:
                        end = pos + len(ln)
                        break
                    got.append(ln)
                    pos += len(ln) + 1
                body = "\n".join(got)
                cur.hd.append(body)
                cmd = cmd[:k] + "\n" + cmd[end:]
                n = len(cmd)
                i = j + len(m.group(0)) if m else j
                continue
            i = j + (len(m.group(0)) if m else 0)
        elif ch in "<>":
            if buf and "".join(buf).isdigit():
                buf.clear()
                state["has"] = False
            endtok()
            i += 1
            while i < n and cmd[i] in "<>":
                i += 1
            if i < n and cmd[i] == "&":
                i += 1
                while i < n and (cmd[i].isdigit() or cmd[i] == "-"):
                    i += 1
                continue
            state["redir"] = True
        elif ch == "'":
            j = cmd.find("'", i + 1)
            if j < 0:
                raise Unparseable("unterminated '")
            buf.append(cmd[i + 1:j])
            state["has"] = True
            i = j + 1
            while i < n and cmd[i] == "'":          # PowerShell '' escape
                k = cmd.find("'", i + 1)
                if k < 0:
                    raise Unparseable("unterminated '")
                buf.append("'" + cmd[i + 1:k])
                i = k + 1
        elif ch == '"':
            j = i + 1
            part = []
            while True:
                if j >= n:
                    raise Unparseable('unterminated "')
                c2 = cmd[j]
                if c2 == "\\" and escape and j + 1 < n and cmd[j + 1] in '"\\$`':
                    part.append(cmd[j + 1])
                    j += 2
                    continue
                if c2 == "`" and j + 1 < n and ps and cmd[j + 1] in '"`$':
                    part.append(cmd[j + 1])
                    j += 2
                    continue
                if c2 == "$" and j + 1 < n and cmd[j + 1] == "(":
                    e = _match_paren(cmd, j + 1)
                    subs.append(cmd[j + 2:e])
                    state["dyn"] = True
                    part.append(cmd[j:e + 1])
                    j = e + 1
                    continue
                if c2 == "$" and j + 1 < n and (cmd[j + 1].isalpha() or cmd[j + 1] in "_{"):
                    state["dyn"] = True
                if c2 == '"':
                    break
                part.append(c2)
                j += 1
            buf.append("".join(part))
            state["has"] = True
            i = j + 1
        elif ch == "`":
            k = cmd.find("`", i + 1)
            if k > 0 and not ps:
                subs.append(cmd[i + 1:k])
                buf.append(cmd[i:k + 1])
                state["dyn"] = True
                state["has"] = True
                i = k + 1
            elif i + 1 < n:
                buf.append(cmd[i + 1])
                state["has"] = True
                i += 2
            else:
                i += 1
        elif ch == "$" and i + 1 < n and cmd[i + 1] == "(":
            e = _match_paren(cmd, i + 1)
            subs.append(cmd[i + 2:e])
            buf.append(cmd[i:e + 1])
            state["dyn"] = True
            state["has"] = True
            i = e + 1
        elif ch == "\\" and escape and i + 1 < n and (bs_all or cmd[i + 1] in " \"'\\$"):
            buf.append(cmd[i + 1])
            state["has"] = True
            i += 2
        else:
            if ch == "$" or (ch == "%" and not buf):
                state["dyn"] = True
            buf.append(ch)
            state["has"] = True
            i += 1
    endseg()
    return segs, subs


def bname(tok):
    b = str(tok).replace("\\", "/").rsplit("/", 1)[-1].lower()
    for ext in (".exe", ".cmd", ".bat", ".ps1", ".com"):
        if b.endswith(ext):
            return b[:-len(ext)]
    return b


class GArgs(list):
    """argv after a gov4 script; .script names which one it was (gov4.py, gov4_registry.py, gov4_snapshot.py)."""
    script = "gov4.py"


PY_RE = re.compile(r"^(?:python[0-9.]*|py|pythonw|pypy[0-9.]*)$")
RUNNERS = {"uv", "uvx", "pipx", "poetry", "pdm", "hatch", "rye"}
UV_VALUE_FLAGS = {"--with", "--python", "-p", "--project", "--directory", "--env-file", "--extra", "--group", "--index",
                  "--index-url", "--with-requirements", "--package", "--from", "--config-file", "--cache-dir"}
CD_CMDS = {"cd", "chdir", "pushd", "set-location", "sl"}
WRITE_ALL_CMDS = {"ren", "rename", "rename-item", "rni", "clear-content", "clc", "set-itemproperty", "sp", "attrib", "icacls",
                  "takeown", "cacls", "unlink", "shred"}
SKIP1_CMDS = {"chmod", "chown", "chgrp", "setfacl"}


def operands(args, value_flags=()):
    """Non-option arguments, skipping the value that follows each flag in value_flags."""
    out, a, i = [], [str(x) for x in args], 0
    while i < len(a):
        x = a[i]
        if x == "--":
            out.extend(a[i + 1:])
            break
        if x in value_flags:
            i += 2
            continue
        if x.startswith("-") and len(x) > 1:
            i += 1
            continue
        out.append(x)
        i += 1
    return out


class Scan:
    def __init__(self, ident, ctx, raw):
        self.ident, self.ctx, self.raw = ident, ctx, raw
        self.F = []          # (rule, reason)
        self.gov4 = []       # arg lists after a gov4 script: one reading per command, one entry per invocation (tickets)
        self.gov4_any = []   # the same over every reading of a backslash (findings only)
        self.targets = []    # file-system targets (best effort)
        self.depth_hit = False
        self.ps = getattr(ctx, "tool", "") == "PowerShell"
        self.base = npath(ctx.cwd) if getattr(ctx, "cwd", None) else ""
        self.cwd = self.base          # directory after the cd / pushd / Set-Location seen so far; None = not known
        self.stack = []
        self._repo = None
        self._paths = 0

    def add(self, rule, reason):
        self.F.append((rule, reason))

    def in_repo(self):
        if self._repo is None:
            self._repo = in_git_repo(self.ctx.cwd)
        return self._repo

    def tgt(self, t):
        """Record a write target; a relative one is resolved against the directory a preceding cd moved to (SB-05)."""
        t = str(t)
        if self.cwd != self.base and self.cwd and not os.path.isabs(t) and not t.startswith(("~", "$")):
            t = npath(t, self.cwd)
        self.targets.append(t)

    def path_check(self, tok):
        """D28 and CD-3: a non-Lead command may not name ~/.claude/nj, .git/hooks or a secret path as any argument.
        Relative names are resolved against the tracked cd directory, wildcards by their literal prefix."""
        t = str(tok)
        if self._paths > 80 or not t or t.startswith("$") or t in ("-", ".", ".."):
            return
        if "=" in t and not re.match(r"^[A-Za-z]:", t) and "/" not in t.split("=", 1)[0]:
            t = t.split("=", 1)[1]
            if not t:
                return
        self._paths += 1
        cwd = self.cwd or self.base or os.getcwd()
        wild = any(c in t for c in "*?[")
        dirs = nj_state_dirs()
        pats = secret_patterns()
        if wild:
            lit = re.split(r"[*?\[]", t, 1)[0]
            pre = K(abs_lite(lit, cwd))
            for d in dirs:
                par = K(d).rsplit("/", 1)[0]
                if K(d).startswith(pre) and len(pre) > len(par) + 1:
                    self.add("nj-state", f"{t} can expand to {d}")
                    return
            for pt in pats:
                lp = K(re.split(r"[*?\[]", pt, 1)[0])
                par = lp.rstrip("/").rsplit("/", 1)[0]
                if lp.startswith(pre) and len(pre) > len(par) + 1:
                    self.add("secret-path", f"{t} can expand to a secret path")
                    return
            return
        ap = npath(t, cwd)
        for d in dirs:
            if under(ap, d):
                self.add("nj-state", f"{t} is inside the governance state {d}")
                return
        if "/.git/hooks" in K(ap) + "/" and (K(ap) + "/").split("/.git/hooks", 1)[1][:1] in ("/", ""):
            self.add("nj-state", f"{t} is inside .git/hooks")
            return
        for pt in pats:
            if match_glob(pt, ap):
                self.add("secret-path", f"{t} is a secret path")
                return


def nj_state_dirs():
    out = []
    for d in (os.path.join(os.path.expanduser("~"), ".claude", "nj"), reg.home()):
        n = npath(d)
        if n and n not in out:
            out.append(n)
    return out


def secret_patterns():
    pats = []
    for pt in reg.read_roles().get("secret_paths", []) or ["~/.config/linkedin/**", "~/.claude/.credentials*", "~/.git-credentials"]:
        pt = pt.replace("\\", "/")
        if pt.startswith("~"):
            pt = npath("~") + pt[1:]
        pats.append(pt)
    return pats


def abs_lite(p_, cwd):
    p_ = os.path.expanduser(p_.replace("\\", "/"))
    if not os.path.isabs(p_) and not re.match(r"^[A-Za-z]:", p_):
        p_ = os.path.join(cwd, p_)
    return os.path.normpath(p_).replace("\\", "/")


def first_non_dash(args):
    for a in args:
        if not str(a).startswith("-"):
            return str(a)
    return None


def gov4_is_read(args):
    """True for a read-only gov4 invocation. Derived from the registry's needs_ticket mirror (SB-10) plus the hook-only
    writes (live acquire|release|heartbeat, the registry CLI writes); an unknown gov4.py subcommand counts as a write."""
    script = getattr(args, "script", "gov4.py")
    if reg.hook_write(args, script):
        return False
    if script != "gov4.py":
        return True
    pos = [str(a) for a in args if not str(a).startswith("-")]
    return not pos or pos[0] in KNOWN_GOV4_SUBS


def scan(cmd, st, depth=0):
    if depth > 6:
        st.add("git-unparseable", "command nesting deeper than 6")
        return
    # Two readings of a backslash outside quotes: a Windows path separator (literal) and a POSIX escape (g\it = git).
    # Both are scanned when the command has a backslash, so neither spelling hides a git call from the other reading.
    variants = [False, True] if ("\\" in cmd and not st.ps) else [False]
    ok = False
    outer = st.gov4
    chosen = None                     # gov4.py calls of ONE reading only: the last one that parsed (POSIX escapes for bash)
    saved = (st.cwd, list(st.stack))
    for bs_all in variants:
        st.gov4 = []
        st.cwd, st.stack = saved[0], list(saved[1])
        try:
            segs, subs = tokenise(cmd, True, st.ps, bs_all)
        except Unparseable:
            try:
                segs, subs = tokenise(cmd, False, st.ps, bs_all)
            except Unparseable as e:
                if not ok and bs_all == variants[-1] and (GIT_RE.search(cmd) or LI_RE.search(cmd)):
                    st.add("git-unparseable", f"cannot parse a command that mentions git or li.py ({e})")
                continue
        ok = True
        for s in subs:
            scan(s, st, depth + 1)
        for seg in segs:
            scan_seg(seg, st, depth)
        chosen = st.gov4
        st.gov4_any.extend(st.gov4)
    st.gov4 = outer + (chosen or [])
    if depth > 0:
        st.cwd, st.stack = saved[0], saved[1]       # a nested shell's cd does not leak out of it


def decode_ps(b64):
    import base64
    try:
        return base64.b64decode(b64).decode("utf-16-le")
    except Exception:
        return None


def lit_base(tok):
    """The literal last path part of a command-name token that holds a variable ($HOME/bin/uv -> uv), or None when the
    name itself is assembled at run time ($a$b, $(printf g%s it), $g)."""
    last = str(tok).replace("\\", "/").rsplit("/", 1)[-1]
    if not last or re.search(r"[$`(){}%*?\[+]", last):
        return None
    return last


def script_kind(arg, st):
    """'gov4.py' | 'gov4_registry.py' | 'gov4_snapshot.py' | None for a script path: by name, by the resolved real path
    (a symlink or junction) and by the first lines of the file (a renamed copy) -- SB-03."""
    a = str(arg)
    b = a.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if b in GOV4_SCRIPTS:
        return b
    if not b.endswith(".py") or "$" in a:
        return None
    try:
        ap = npath(a, st.cwd or st.base)
        rb = ap.rsplit("/", 1)[-1].lower()
        if rb in GOV4_SCRIPTS:
            return rb
        if os.path.isfile(ap) and os.path.getsize(ap) < 800000:
            with open(ap, "rb") as f:
                head = f.read(900).decode("utf-8", "replace")
            if "NJ Governance v4" in head:
                for mk, kind in GOV4_MARKERS.items():
                    if mk in head:
                        return kind
    except OSError:
        pass
    return None


def run_target(toks, st):
    """(script basename, args after it, gov4 kind or None) when this segment RUNS a script: python x.py ..., uv run python
    x.py ..., uv run x.py, python -m gov4 ..., ./gov4.py. Naming a file as an operand (git add gov4.py, wc -l gov4.py,
    python -m py_compile gov4.py) is not a run (SB-11)."""
    t = [str(x) for x in toks]
    if not t:
        return None
    first = t[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
    b0 = bname(t[0])
    if first in GOV4_SCRIPTS or b0 in GOV4_NAMES:
        k = first if first in GOV4_SCRIPTS else b0 + ".py"
        return k, t[1:], k
    i = None
    if PY_RE.match(b0):
        i = 1
    elif b0 in RUNNERS:
        j = 1
        while j < len(t) and t[j].startswith("-"):
            j += 2 if t[j] in UV_VALUE_FLAGS else 1
        if j < len(t) and t[j] in ("run", "x", "tool"):
            j += 1
        elif b0 != "uvx":
            return None
        while j < len(t) and t[j].startswith("-"):
            j += 2 if t[j] in UV_VALUE_FLAGS else 1
        if j >= len(t):
            return None
        if PY_RE.match(bname(t[j])):
            i = j + 1
        else:
            return t[j].replace("\\", "/").rsplit("/", 1)[-1].lower(), t[j + 1:], script_kind(t[j], st)
    if i is None:
        return None
    while i < len(t):
        x = t[i]
        if x in ("-X", "-W", "-Q"):
            i += 2
            continue
        if x == "-m":
            mod = t[i + 1].lower() if i + 1 < len(t) else ""
            return mod + ".py", t[i + 2:], (mod + ".py" if mod in GOV4_NAMES else None)
        if x == "-c":
            return None
        if x.startswith("-"):
            i += 1
            continue
        return x.replace("\\", "/").rsplit("/", 1)[-1].lower(), t[i + 1:], script_kind(x, st)
    return None


def outward_scripts():
    return {x.lower() for x in reg.read_roles().get("outward_actions", {}).get("sibling_scripts",
            ["engage_daily.py", "comments_watch.py", "connect_weekly.py"])}


LI_CODE_RE = re.compile(r"\bimport\s+li\b|\bfrom\s+li\s+import|require\(\s*['\"][^'\"]*[/\\]li(?:\.py|\.js)?['\"]\s*\)|"
                        r"\bli\.(?:post|post_draft|comment|like|due|publish|reply|delete|react)\w*\s*\(", re.I)


def scan_seg(seg, st, depth):
    toks = list(seg.toks)
    for r in seg.redirs:
        st.tgt(r)
        st.path_check(r)
    while toks and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0]) or re.match(r"^\$env:[A-Za-z_]\w*=", toks[0], re.I)):
        name = re.match(r"^(?:\$env:)?([A-Za-z_]\w*)=", toks[0], re.I).group(1)
        if name.upper().startswith("GIT_"):
            st.add("git-env", f"{name} set for a command")
        toks.pop(0)
    if not toks:
        return
    head = toks[0]
    base = bname(head)
    for t in toks[1:]:
        st.path_check(t)
    # cd / pushd / Set-Location: git and file writes that follow are judged where they really run (SB-05)
    if not head.dyn and base in CD_CMDS:
        args = [str(t) for t in toks[1:] if not str(t).startswith("-") or str(t) == "-"]
        tgt = args[0] if args else "~"
        prev = st.cwd
        if tgt == "-" or any(getattr(t, "dyn", False) for t in toks[1:]):
            st.cwd = None
        elif st.cwd is None:
            st.cwd = npath(tgt) if os.path.isabs(os.path.expanduser(tgt)) else None
        else:
            st.cwd = npath(tgt, st.cwd)
        if base == "pushd":
            st.stack.append(prev)
        return
    if not head.dyn and base == "popd":
        st.cwd = st.stack.pop() if st.stack else st.base
        return
    lower = [str(t).replace("\\", "/").rsplit("/", 1)[-1].lower() for t in toks]
    # gov4 scripts and the posting scripts: only a RUN counts, found by name, resolved path or file head (SB-03, SB-06, SB-11)
    if not head.dyn or lit_base(head):
        rt = run_target(toks, st)
        if rt:
            name, args, kind = rt
            if kind:
                ga = GArgs(args)
                ga.script = kind
                st.gov4.append(ga)
            elif name in outward_scripts() and not {"--dry-run", "--help", "-h"}.intersection(args):
                st.add("outward-li", f"{name} posts, comments or likes as Nader: Lead or scheduler only (use --dry-run)")
    for idx, b in enumerate(lower):
        if b == "li.py":
            args = [str(t).lower() for t in toks[idx + 1:]]
            hit = LI_VERBS.intersection(args)
            if hit:
                st.add("outward-li", f"li.py {sorted(hit)[0]} is Lead or scheduler only")
            break
    if head.dyn:
        lit = lit_base(head)
        if lit is None:
            if st.in_repo() or CTX_RE.search(st.raw) or "gov4" in st.raw.lower():
                st.add("dynamic-head", f"command name {str(head)[:30]!r} is built at run time and cannot be checked")
            return
        base = bname(lit)
    if base in ("claude", "claude-code") or (base in ("node", "npx", "bunx", "pnpm", "npm") and any(
            re.search(r"claude-code|claude[/\\]cli|@anthropic-ai", str(t), re.I) for t in toks[1:])):
        rest_ = {str(t) for t in toks[1:]}
        if not rest_ or not rest_ <= {"--version", "-v", "--help", "-h"}:
            st.add("claude-launch", "a child Claude process escapes the hooks (model, permission and role rules): the Lead starts those")
        return
    if base == "git":
        scan_git(toks[1:], st)
        return
    if base.startswith("git-") and len(base) > 4:
        scan_git([base[4:]] + [str(t) for t in toks[1:]], st)        # git-receive-pack, git-push, git-lfs ...
        return
    if base == "gh":
        scan_gh(toks[1:], st)
        return
    if base in COPY_CMDS:
        args = [str(t) for t in toks[1:] if not str(t).startswith("-")]
        if args:
            st.tgt(args[-1])
        return
    if base in WRITE_FILE_CMDS:
        for t in toks[1:]:
            if not str(t).startswith("-"):
                st.tgt(t)
        return
    if base in REMOVE_CMDS:
        for t in toks[1:]:
            if not str(t).startswith("-"):
                st.tgt(t)
        return
    if base in ("sed", "gsed"):
        a = [str(t) for t in toks[1:]]
        if any(re.match(r"^-[A-Za-z]*i", x) for x in a if not x.startswith("--")) or any(x.startswith("--in-place") for x in a):
            ops = operands(a, ("-e", "-f", "--expression", "--file"))
            given = any(x in ("-e", "-f") or x.startswith(("--expression", "--file")) for x in a)
            for x in (ops if given else ops[1:]):
                st.tgt(x)
        return
    if base == "perl":
        a = [str(t) for t in toks[1:]]
        if any(re.match(r"^-[A-Za-z]*i", x) for x in a if not x.startswith("--")):
            ops = operands(a, ("-e", "-E"))
            for x in (ops if any(x in ("-e", "-E") for x in a) else ops[1:]):
                st.tgt(x)
    elif base in SKIP1_CMDS:
        for x in operands(toks[1:])[1:]:
            st.tgt(x)
        return
    if base in WRITE_ALL_CMDS or base == "truncate":
        for x in operands(toks[1:], ("-s", "--size", "-r", "--reference")):
            if not (x.startswith("/") and "/" not in x[1:] and len(x) <= 12):
                st.tgt(x)
        return
    if base == "dd":
        for t in toks[1:]:
            if str(t).startswith("of="):
                st.tgt(str(t)[3:])
        return
    if base in SHELLS:
        args = [str(t) for t in toks[1:]]
        code = None
        for j, a in enumerate(args):
            al = a.lower()
            if base == "cmd" and al in ("/c", "/k", "/r"):
                code = " ".join(args[j + 1:])
                break
            if base in ("pwsh", "powershell") and al in ("-command", "-c", "-cmd"):
                code = " ".join(args[j + 1:])
                break
            if base in ("pwsh", "powershell") and al in ("-encodedcommand", "-enc", "-e", "-ec") and j + 1 < len(args):
                code = decode_ps(args[j + 1])
                if code is None:
                    st.add("git-unparseable", "cannot decode -EncodedCommand")
                break
            if base not in ("cmd", "pwsh", "powershell") and re.match(r"^-[a-zA-Z]*c[a-zA-Z]*$", a) and j + 1 < len(args):
                code = args[j + 1]
                break
        if code is not None:
            scan(code.strip().strip('"'), st, depth + 1)
        for hd in seg.hd:
            scan(hd, st, depth + 1)
        return
    if base in ("find", "fd"):
        for j, t in enumerate(toks):
            if str(t) in ("-exec", "-execdir", "-ok", "-okdir", "-x", "-X", "--exec", "--exec-batch"):
                sub = Seg()
                sub.toks = toks[j + 1:]
                scan_seg(sub, st, depth + 1)
        return
    if base in WRAPPERS:
        rest = toks[1:]
        for j, t in enumerate(rest):                  # exec -a x git push, sudo -u x git push: try every suffix
            ts = str(t)
            b2 = bname(ts)
            if ts.startswith("-") or ts.isdigit():
                continue
            if b2 in SHELLS or b2 in WRAPPERS or b2 in INTERP or b2 in ("git", "gh") or b2.startswith("git-") \
                    or re.match(r"^python[0-9.]*$", b2) or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", ts) or b2 in RUNNERS \
                    or b2 in ("claude", "claude-code") or b2 in GOV4_NAMES or ts.lower().endswith(tuple(GOV4_SCRIPTS)):
                sub = Seg()
                sub.toks = rest[j:]
                scan_seg(sub, st, depth + 1)
                break
        for t in rest:
            if " " in str(t) and (GIT_RE.search(str(t)) or LI_RE.search(str(t))):
                scan(str(t), st, depth + 1)
        return
    if base in INTERP or PY_RE.match(base):
        args = [str(t) for t in toks[1:]]
        code = None
        for j, a in enumerate(args):
            if a in ("-c", "-e", "--eval", "-p", "--print", "-r", "-E") and j + 1 < len(args):
                code = args[j + 1]
                break
        if code is None:
            for hd in seg.hd:
                code = (code or "") + "\n" + hd
        if code is not None:
            if GIT_RE.search(code):
                if WRITE_VERB_RE.search(code):
                    st.add("git-write", "inline interpreter code runs a git write verb")
                if LI_RE.search(code) and LI_VERBS.intersection(w.lower() for w in re.findall(r"[A-Za-z]+", code)):
                    st.add("outward-li", "inline interpreter code runs li.py outward verbs")
            elif LI_RE.search(code):
                st.add("outward-li", "inline interpreter code mentions li.py")
            if LI_CODE_RE.search(code):
                st.add("outward-li", "inline interpreter code imports li and posts, comments or likes")
            if re.search(r"gov4_registry|gov4_hook|gov4_launcher|gov4_snapshot|gov4\.py|\bgov4\b|runpy", code, re.I):
                st.add("gov4-write", "inline interpreter code reaches gov4 or the governance registry: the Lead uses gov4.py with a ticket")
            if SPAWN_RE.search(code) and OBF_RE.search(code) and (st.in_repo() or CTX_RE.search(code)):
                st.add("dynamic-exec", "inline code spawns a process with a name or argument built at run time")
        return


def scan_gh(args, st):
    a = [str(x) for x in args]
    pos = [x for x in a if not x.startswith("-")]
    s1 = pos[0] if pos else None
    s2 = pos[1] if len(pos) > 1 else None
    ok = {("pr", "view"), ("pr", "list"), ("pr", "status"), ("pr", "diff"), ("pr", "checks"), ("issue", "view"),
          ("issue", "list"), ("run", "view"), ("run", "list"), ("auth", "status"), ("repo", "view"), ("release", "view"),
          ("release", "list"), ("status", None), ("--version", None), ("version", None)}
    if s1 is None:
        return
    if s1 == "api":
        method = None
        for j, x in enumerate(a):
            if x in ("-X", "--method") and j + 1 < len(a):
                method = a[j + 1].upper()
        if method not in (None, "GET") or any(x in ("-f", "-F", "--field", "--raw-field", "--input") for x in a):
            st.add("gh-write", "gh api with a write method or body")
        return
    if (s1, s2) in ok or (s1, None) in ok:
        return
    st.add("gh-write", f"gh {s1} {s2 or ''}".strip() + " is not a read-only gh form (Lead merges and pushes through gov4.py)")


def parse_git(args):
    o = {"C": [], "c": [], "gitdir": False, "worktree": False, "sub": None, "rest": []}
    noarg = {"--no-pager", "-p", "--paginate", "-P", "--bare", "--no-replace-objects", "--literal-pathspecs", "--glob-pathspecs",
             "--noglob-pathspecs", "--icase-pathspecs", "--no-optional-locks", "--exec-path", "--html-path", "--man-path",
             "--info-path", "--no-lazy-fetch", "--version", "--help", "-h"}
    i, n = 0, len(args)
    while i < n:
        a = str(args[i])
        if a == "-C":
            o["C"].append(str(args[i + 1]) if i + 1 < n else "")
            i += 2
        elif a.startswith("-C") and len(a) > 2:
            o["C"].append(a[2:])
            i += 1
        elif a == "-c":
            o["c"].append(str(args[i + 1]) if i + 1 < n else "")
            i += 2
        elif a.startswith("-c") and len(a) > 2 and not a.startswith("--"):
            o["c"].append(a[2:])
            i += 1
        elif a.startswith("--config-env"):
            o["c"].append(a)
            i += 1 if "=" in a else 2
        elif a.startswith("--git-dir"):
            o["gitdir"] = True
            i += 1 if "=" in a else 2
        elif a.startswith("--work-tree"):
            o["worktree"] = True
            i += 1 if "=" in a else 2
        elif a.startswith("--namespace") or a.startswith("--super-prefix"):
            i += 1 if "=" in a else 2
        elif a in noarg or a.startswith("--exec-path="):
            i += 1
        elif a.startswith("-"):
            i += 1
        else:
            break
    if i < n:
        o["sub"] = str(args[i])
        o["rest"] = [str(x) for x in args[i + 1:]]
    return o


def scan_git(args, st):
    o = parse_git(args)
    ident, ctx = st.ident, st.ctx
    if o["c"]:
        st.add("git-c", "git -c / --config-env is denied")
    if o["gitdir"] or o["worktree"]:
        st.add("git-dir", "--git-dir / --work-tree is denied")
    eff = st.cwd or ctx.cwd
    for d in o["C"]:
        tgt = npath(d, eff)
        wt = worktree_root(ctx.cwd.replace("\\", "/"))
        if not (under(tgt, npath(wt)) if wt else K(tgt) == K(npath(ctx.cwd))):
            st.add("git-C", f"git -C {d} points at another directory")
        eff = tgt
    sub, rest = o["sub"], o["rest"]
    # SB-05: a cd / pushd / Set-Location before the git call moved it; judge the directory it really runs in
    moved = st.cwd is None or (st.cwd != st.base and not o["C"])
    if moved and sub is not None and sub not in GIT_READ:
        wt = worktree_root(ctx.cwd.replace("\\", "/"))
        home_ = npath(wt) if wt else npath(ctx.project)
        if st.cwd is None or not under(st.cwd, home_):
            st.add("git-C", f"git {sub} runs in {st.cwd or 'a directory a cd made unknown'}, outside this agent's own tree")
    if sub in GIT_READ and any(r.startswith("--output") for r in rest):
        st.add("git-write", f"git {sub} --output writes a file")
    if "--no-verify" in rest or (sub == "commit" and any(re.match(r"^-[a-zA-Z]*n[a-zA-Z]*$", r) for r in rest)):
        st.add("no-verify", "--no-verify is denied")
    if sub is None:
        return
    allowed = git_allowed(sub, rest, ident, ctx, eff)
    if allowed:
        st.add("git-write", allowed)


def git_allowed(sub, rest, ident, ctx, eff):
    """None when this git call is allowed for the caller, else the reason."""
    r = reg.read_roles().get("git", {})
    role = ctx.role if ident == "agent" else None
    if ident == "agent" and role in ("reviewer", "helper"):
        base = set(r.get("reviewer_allow" if role == "reviewer" else "helper_allow", []))
        if role == "reviewer":
            base |= {"ls-files", "ls-tree", "cat-file", "blame", "rev-list", "show-ref", "diff-tree", "merge-base", "name-rev",
                     "describe", "grep", "for-each-ref", "shortlog"}
        return None if sub in base else f"git {sub} is outside this {role}'s read-only list"
    if sub in GIT_READ:
        return None
    flags = set(rest)
    pos = [x for x in rest if not x.startswith("-")]
    if sub == "branch":
        wv = {"-d", "-D", "-m", "-M", "-c", "-C", "-f", "-u", "--set-upstream-to", "--unset-upstream", "--delete", "--move",
              "--copy", "--edit-description", "--force", "-t", "--track", "--create-reflog"}
        listing = flags & {"-l", "--list", "--contains", "--merged", "--no-merged", "--points-at", "--show-current"}
        if flags & wv or (pos and not listing):
            return "git branch creates, moves or deletes a branch"
        return None
    if sub == "tag":
        listing = flags & {"-l", "--list", "-n", "--contains", "--points-at", "--merged", "--no-merged"}
        if flags & {"-a", "-s", "-d", "-f", "-m", "-u", "--delete", "--force", "--annotate", "--sign"} or (pos and not listing):
            return "git tag creates or deletes a tag"
        return None
    if sub == "remote":
        return None if not rest or pos[:1] in (["show"], ["get-url"]) or flags <= {"-v", "--verbose"} and not pos else \
            "git remote changes remotes"
    if sub == "reflog":
        return None if not pos or pos[0] in ("show", "exists") else "git reflog expire/delete"
    if sub == "worktree":
        return None if pos[:1] == ["list"] else "git worktree add/remove/move/prune is Lead-only (gov4.py)"
    if sub == "stash" and pos[:1] in (["list"], ["show"]):
        return None
    if sub == "config":
        return "git config is denied"
    if ident != "agent":
        return f"git {sub} is a git write: the Lead uses gov4.py with a ticket; jobs and unknown callers never write"
    # agent in a worktree or main checkout: add anywhere; the rest only on its own worktree-* branch
    if sub == "add":
        return None
    if sub in GIT_OWN_OPS:
        br = current_branch(eff)
        if not br or not br.startswith("worktree-"):
            return f"git {sub} is allowed only on the agent's own worktree-* branch (current: {br or 'none'})"
        if sub == "reset" and flags & {"--hard", "--merge", "--keep"}:
            return "git reset --hard/--merge/--keep is denied"
        if sub == "checkout" and ("--" not in rest or flags & {"-b", "-B", "-f", "--force", "--orphan", "--detach"}):
            return "git checkout is allowed only as 'checkout -- <paths>'"
        if sub == "stash" and pos[:1] in (["branch"], ["clear"], ["create"], ["store"]):
            return f"git stash {pos[0]} is denied"
        return None
    return f"git {sub} is a git write denied for agents"


# --------------------------------------------------------- shell findings ---

_NL = {"agent", "job", "unknown"}
_ALL = {"agent", "job", "unknown", "lead"}
IDENT_APPLIES = {
    "git-write": _ALL, "git-c": _ALL, "git-dir": _ALL, "git-C": _ALL, "git-env": _ALL, "no-verify": _ALL,
    "git-hookspath": _ALL, "gh-write": _ALL, "secret-path": _ALL,
    "outward-li": _NL, "gov4-write": _NL, "git-unparseable": _NL, "shell-escape": {"agent", "job"},
    # v4 hardening: a command may not rewrite the controls or reach them in a form the scanner cannot read
    "env-override": _NL, "dynamic-head": _NL, "dynamic-exec": _NL, "nj-state": _NL, "claude-launch": _NL,
}


def scan_all(ctx, cmd):
    st = Scan(ctx.ident, ctx, cmd)
    scan(cmd, st)
    if GIT_RE.search(cmd):
        if GIT_ENV_RE.search(cmd):
            st.add("git-env", "GIT_* environment variable")
        if re.search(r"core\.hooksPath", cmd, re.I):
            st.add("git-hookspath", "core.hooksPath is denied")
    if CORE_ENV_RE.search(cmd) or (ANY_ENV_RE.search(cmd) and CTX_RE.search(cmd)):
        st.add("env-override", "NJ_*, HOME or USERPROFILE is set from a command line: governance overrides are the Lead's, not a command's")
    if SECRET_RE.search(cmd):
        st.add("secret-path", "the command names a secret or credential path")
    if NJ_STATE_RE.search(cmd):
        st.add("nj-state", "the command names ~/.claude/nj or .git/hooks (governance state is read and changed only by gov4.py)")
    if DYN_EXEC_RE.search(cmd):
        st.add("dynamic-exec", "Invoke-Expression, iex, Set-Alias, Process.Start and similar run a command the scanner cannot read")
    if PS_LAUNCH_RE.search(cmd) and (PS_LAUNCH_TARGET_RE.search(cmd) or OBF_RE.search(cmd) or "$" in cmd):
        st.add("dynamic-exec", "Start-Process (saps, start) naming git, gh or li.py, or building its arguments at run time, launches a program the scanner cannot read")
    if NO_VERIFY_RE.search(cmd) and (GIT_RE.search(cmd) or LI_RE.search(cmd) or PS_LAUNCH_TARGET_RE.search(cmd)):
        st.add("no-verify", "--no-verify is denied anywhere in a git command")
    if st.ps and PS_DYN_HEAD_RE.search(cmd) and (st.in_repo() or CTX_RE.search(cmd)):
        st.add("dynamic-head", "a call operator on an expression or variable runs a command name built at run time")
    for rx in INLINE_WRITE_RES:
        for m in rx.finditer(cmd):
            st.tgt(m.group(1).replace("\\\\", "\\"))
    for args in st.gov4_any + st.gov4:
        sub = first_non_dash(args)
        if not gov4_is_read(args):
            st.add("gov4-write", f"{getattr(args, 'script', 'gov4.py')} {sub} needs a Lead ticket")
    return st


def shell_findings(ctx, st):
    out = []
    seen = set()
    for rule, reason in st.F:
        if ctx.ident in IDENT_APPLIES.get(rule, set()) and (rule, reason) not in seen:
            seen.add((rule, reason))
            out.append((rule, reason, False))
    return out


def escape_findings(ctx, st):
    """Best-effort target check for shell writes by agents and jobs (the merge-time check is the solid layer)."""
    out = []
    if ctx.ident not in ("agent", "job") or not st.targets:
        return out
    here = npath(ctx.cwd)
    skip = {t for t in tmpdirs() if not under(here, t)}
    if ctx.pl.get("scratchpad_dir"):
        skip.add(npath(ctx.pl.get("scratchpad_dir")))
    for t in st.targets:
        if t.lower() in ("nul", "/dev/null", "$null", "&1", "-") or t.startswith("$"):
            continue
        tp = npath(t, ctx.cwd)
        if any(under(tp, s) for s in skip if s):
            continue
        why = write_reason(ctx, tp)
        if why:
            out.append(("shell-escape", f"shell write to {t}: {why}", False))
            break
    return out


# ------------------------------------------------------------ write rules ---

def protected(norm):
    n = K(norm)
    segs = n.split("/")
    h = K(npath("~"))
    if ".git" in segs:
        return "inside .git"
    if under(n, h + "/.claude"):
        return "inside ~/.claude"
    for i, sg in enumerate(segs):
        if sg == ".claude" and i + 1 < len(segs):
            nx = segs[i + 1]
            if nx.startswith("settings") or nx in ("hooks", "agents"):
                return f"protected .claude/{nx}"
    if segs[-1] == "claude.md":
        return "CLAUDE.md"
    if n.endswith("nj-agent-ops/templates/roles.json"):
        return "roles.json"
    r = reg.read_roles()
    for pat in r.get("protected_paths", []) or []:       # CD-3: roles.json is the single source, read here
        if roles_pattern_hits(pat, norm):
            return f"protected path {pat} (roles.json)"
    for tree in (r.get("method_trees", []) or []) + extra_protected():
        if tree and under(n, K(npath(tree))):
            return f"protected method tree {tree}"
    return None


def roles_pattern_hits(pat, norm):
    """A roles.json protected_paths pattern against a normalised absolute path: ~ expands to the home, a pattern with a
    drive or leading slash is absolute, any other pattern matches at any depth (.git, .claude/settings*, CLAUDE.md)."""
    pat = pat.replace("\\", "/")
    if pat.startswith("~"):
        pat = npath("~") + pat[1:]
    elif not (re.match(r"^[A-Za-z]:/", pat) or pat.startswith("/")):
        pat = "**/" + pat
    if pat.endswith("/**"):
        return match_glob(pat, norm) or match_glob(pat[:-3], norm)
    return match_glob(pat, norm) or match_glob(pat + "/**", norm)


def extra_protected():
    try:
        with open(reg.p("protected-extra.txt"), encoding="utf-8") as f:
            return [npath(x.strip()) for x in f if x.strip() and not x.startswith("#")]
    except OSError:
        return []


def split_globs(s):
    return [x.strip() for x in re.split(r"[,;\n]", s or "") if x.strip()]


def rel_to(norm, root):
    return norm[len(npath(root)) + 1:] if under(norm, npath(root)) and K(norm) != K(npath(root)) else ""


def matches_any(norm, patterns, roots):
    for pat in patterns:
        pat = pat.replace("\\", "/")
        if pat.startswith("~"):
            hp = npath("~")
            if match_glob(hp + pat[1:], norm):
                return True
            continue
        if re.match(r"^[A-Za-z]:/", pat) or pat.startswith("/"):
            if match_glob(pat, norm):
                return True
            continue
        for r in roots:
            rel = rel_to(norm, r)
            if rel and match_glob(pat, rel):
                return True
            if K(norm) == K(npath(r) + "/" + pat):
                return True
    return False


def live_patterns(project):
    try:
        with open(os.path.join(project, ".nj", "live-paths.txt"), encoding="utf-8") as f:
            return [x.strip() for x in f if x.strip() and not x.startswith("#")]
    except OSError:
        return []


def claim_patterns(project):
    import glob
    out = []
    for f in glob.glob(os.path.join(project, ".agent-ops", "claims", "*.json")):
        for rec in reg.read_json(f, []) or []:
            out.extend(rec.get("paths", []))
    return out


def write_reason(ctx, norm):
    """None when ctx may write norm (a real normalised path), else the reason. Used by Edit|Write and shell writes."""
    ident = ctx.ident
    prot = protected(norm) if ident in ("agent", "job", "unknown") else None
    if prot and ident == "unknown" and under(K(norm), K(npath("~")) + "/.claude/projects") and "/memory/" in K(norm):
        prot = None                       # a session whose registration failed keeps its auto-memory
    if prot and not reg.unlock_valid():
        return f"protected path ({prot}); needs a valid unlock.json"
    if ident == "unknown":
        return None
    sp = ctx.pl.get("scratchpad_dir")
    if sp and under(norm, npath(sp)):
        return None                       # the session scratchpad is ephemeral and outside every project
    roots = [ctx.cwd, ctx.project]
    if ident == "lead":
        allow = reg.read_roles().get("lead", {}).get("write_allow") or reg.read_roles().get("lead_write_allow", [])
        if matches_any(norm, allow, roots):
            return None
        return "the Lead writes only handoff.md, work/lead/**, work/governance/** and its memory (clause 0.20)"
    if ident == "job":
        allow = split_globs(os.environ.get("NJ_WRITE_ALLOW", ""))
        if matches_any(norm, allow, roots):
            return None
        return "a job writes only inside NJ_WRITE_ALLOW" + ("" if allow else " (unset)")
    # agent
    info = ctx.info or {}
    if ctx.role in ("reviewer", "helper") or info.get("writes") == "none":
        return f"{ctx.agent_type or 'this agent'} is read-only in roles.json"
    if info.get("enabled") is False:
        return f"{ctx.agent_type} is disabled in roles.json"
    wt = worktree_root(ctx.cwd)
    main = npath(ctx.project)
    if wt:
        if not under(norm, npath(wt)):
            return "outside this agent's worktree"
        rel = rel_to(norm, wt)
        live = live_patterns(main)
        if rel and any(match_glob(g, rel) for g in live) and os.path.exists(os.path.join(main, rel)):
            return f"{rel} is a live path (.nj/live-paths.txt): never owned by a writer"
    else:
        claims = claim_patterns(main) + reg.agent_owned(ctx.agent_id)      # D23: main-checkout writers own their OWNED_PATHS
        if not claims:
            return "no relay.py claim or recorded OWNED_PATHS covers this path (agents without a worktree work inside claims)"
        if not matches_any(norm, [c if any(ch in c for ch in "*?") else c.rstrip("/") + "/**" for c in claims] + claims, [main]):
            return "outside the union of active claims"
        rel = rel_to(norm, main)
        if rel and any(match_glob(g, rel) for g in live_patterns(main)):
            return f"{rel} is a live path (.nj/live-paths.txt)"
    scope = info.get("edit_scope")
    if scope:
        rel = rel_to(norm, wt or main)
        if not any(match_glob(g, rel) for g in scope):
            return f"{ctx.agent_type} edits only {scope}"
    return None


def h_write(ctx):
    ti = ctx.tin
    target = ti.get("file_path") or ti.get("notebook_path") or ti.get("path") or ""
    if not target:
        return 0
    norm = npath(target, ctx.cwd)
    why = write_reason(ctx, norm)
    if ctx.ident == "unknown":
        if why:                           # SB-08: unregistered sessions are not trusted with protected paths
            return finish(ctx, [("write", why, False)])
        log_dec(ctx, "unknown-write", f"unrestricted outside protected paths (v3 behaviour): {norm}", "allow-logged")
        return 0
    return finish(ctx, [("write", why, False)] if why else [])


# ----------------------------------------------------------- bash / ticket ---

def command_of(ctx):
    c = ctx.tin.get("command")
    return c if isinstance(c, str) else ""


def h_git(ctx):
    cmd = command_of(ctx)
    if not cmd:
        return 0
    st = scan_all(ctx, cmd)
    f = shell_findings(ctx, st) + escape_findings(ctx, st)
    return finish(ctx, f)


def h_bash(ctx):
    """git + ticket in ONE process (A10): the scan first; a deny ends it, else the Lead's ticket rewrite."""
    code = h_git(ctx)
    return code if code else h_ticket(ctx)


def h_ticket(ctx):
    # D27/A8: tickets exist only in enforce. Audit and off neither rewrite the command nor answer ask.
    # tickets-mode habit = the S2 fallback: no rewrite, gov4.py does not demand one.
    if ctx.ident != "lead" or ctx.mode != "enforce" or reg.ticket_mode() != "hook":
        return 0
    cmd = command_of(ctx)
    if not cmd or "gov4" not in cmd.lower():
        return 0
    st = Scan(ctx.ident, ctx, cmd)
    scan(cmd, st)
    writes = [a for a in st.gov4 if not gov4_is_read(a)]
    if not writes:
        return 0
    nonces = []
    for a in writes:
        n = reg.mint_ticket(a)
        if not n:
            reg.alert("registry", "ticket could not be minted (state unwritable): gov4.py will refuse", ctx.project)
            return 0
        nonces.append(n)
    val = ",".join(nonces)
    if ctx.tool == "PowerShell":
        new = f"$env:NJ_TICKET='{val}'; {cmd}"
    else:
        new = f"export NJ_TICKET='{val}'; {cmd}"
    ti = dict(ctx.tin)
    ti["command"] = new
    sub = first_non_dash(writes[0])
    decision = "allow" if sub == "merge" else "ask"
    log_dec(ctx, "ticket", f"minted {len(nonces)} for gov4.py {sub}", "ticket")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                             "permissionDecisionReason": "NJ ticket attached (single use, 60 s)",
                                             "updatedInput": ti}}))
    return 0


# -------------------------------------------------------------------- mcp ---

def mcp_read_ok(name, patterns):
    import fnmatch
    return any(fnmatch.fnmatchcase(name, pt) for pt in patterns)


def h_mcp(ctx):
    """D29: mcp__linkedctl__* is deny-by-default for everyone but the Lead, except the read tools in roles.json
    outward_actions.mcp_read_allow (*_get, *_list, stats_*, whoami, auth_status). Writes such as auth_revoke are covered."""
    r = reg.read_roles().get("outward_actions", {})
    if ctx.ident == "lead":
        return 0
    prefix = r.get("mcp_prefix", "mcp__linkedctl__")
    if ctx.tool.startswith(prefix):
        allow = r.get("mcp_read_allow", ["*_get", "*_list", "stats_*", "whoami", "auth_status"])
        if not mcp_read_ok(ctx.tool[len(prefix):], allow):
            return finish(ctx, [("outward-mcp", f"{ctx.tool} is Lead or scheduler only (only read tools are open)", False)])
    elif ctx.tool in r.get("mcp", []):
        return finish(ctx, [("outward-mcp", f"{ctx.tool} is Lead or scheduler only", False)])
    return 0


def h_workflow(ctx):
    f = []
    if ctx.ident == "agent":
        f.append(("workflow-agent", "Workflow is never used by team agents", True))
    elif reg.counts()["live"] > 0:
        f.append(("workflow-live", "Workflow fan-out only with 0 live agents (matcher not yet proven by S3)", True))
    return finish(ctx, f)


# ----------------------------------------------------------------- agent ---

_CG = {}


def load_cg():
    if "m" in _CG:
        return _CG["m"]
    cands = [os.environ.get("NJ_CHECK_GOVERNANCE", ""), os.path.join(HERE, "check_governance.py"),
             os.path.join(HERE, "..", "..", "nj-delegate", "scripts", "check_governance.py"),
             reg.p("check_governance.py")]
    mod = None
    for c in cands:
        if c and os.path.isfile(c):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("gov4_check_governance", c)
                mod = importlib.util.module_from_spec(spec)
                sys.modules["gov4_check_governance"] = mod
                spec.loader.exec_module(mod)
                for rc in reg.roles_candidates():
                    if rc and os.path.isfile(rc):
                        mod.ROLES_FILE = (lambda path=rc: __import__("pathlib").Path(path))
                        break
                break
            except Exception as e:  # noqa: BLE001
                reg.log_event({"event": "check_governance-import-failed", "err": repr(e)[:200]})
                mod = None
    _CG["m"] = mod
    return mod


def named_md_paths(prompt, cwd):
    """Paths ending .md that a prompt names (absolute with spaces, or relative), resolved against cwd."""
    out = []
    for pat in (r"[A-Za-z]:[/\\][^\n\"'`]*?\.md", r"(?<![\w.])[\w./\\-]+\.md\b"):
        for m in re.finditer(pat, prompt or ""):
            c = m.group(0)
            c = c if os.path.isabs(c) else os.path.join(cwd or os.getcwd(), c)
            if c not in out:
                out.append(c)
    return out


def brief_file_text(prompt, cwd):
    """(path, text, named): the first named .md file that reads; named is True when the prompt names any .md path."""
    cands = named_md_paths(prompt, cwd)
    for c in cands:
        if os.path.isfile(c):
            try:
                with open(c, encoding="utf-8") as f:
                    return c, f.read(), True
            except (OSError, UnicodeDecodeError):
                continue
    return None, None, bool(cands)


def brief_problems(prompt, helper, cwd=None):
    cg = load_cg()
    if cg is None:
        return None
    try:
        v = cg.brief_violations(prompt, helper=helper)
        if v and any(x[0] == "contract-block" and "no contract block" in str(x[2]) for x in v):
            bpath, txt, _ = brief_file_text(prompt, cwd)
            if bpath:
                cg._BRIEF_DIR = __import__("pathlib").Path(bpath).resolve().parent
                v = cg.brief_violations(txt, helper=helper)
        return [f"{a}={str(b)[:40]}: {c}" for a, b, c in v]
    except Exception as e:  # noqa: BLE001
        reg.log_event({"event": "brief-check-error", "err": repr(e)[:200]})
        return None


def git_dirty(root, paths):
    code, out, _ = run(["git", "-C", root, "status", "--porcelain", "--"] + paths, timeout=10)
    return out.strip() if code == 0 else ""


def main_owned_patterns(owned, cwd):
    """OWNED_PATHS of a brief as absolute forward-slash patterns (a directory gets /**)."""
    out = []
    for o in owned or []:
        o = str(o).strip().replace("\\", "/")
        if not o:
            continue
        hasw = any(ch in o for ch in "*?")
        ap = o if hasw and (re.match(r"^[A-Za-z]:/", o) or o.startswith("/")) else None
        if ap is None:
            ap = npath(re.sub(r"/\*\*?$|/\*$", "", o), cwd) + ("/**" if o.endswith(("/", "*")) or not os.path.splitext(o)[1] else "")
        out.append(ap)
    return out


def _lit_prefix(pat):
    pre = re.split(r"[*?\[]", str(pat).replace("\\", "/"), 1)[0].rstrip("/")
    return K(pre) + "/"


def owned_overlap(a, b):
    """True when two OWNED_PATHS pattern lists may touch the same file; unknown (empty) lists overlap everything."""
    if not a or not b:
        return True
    for x in a:
        for y in b:
            px, py = _lit_prefix(x), _lit_prefix(y)
            if px.startswith(py) or py.startswith(px):
                return True
    return False


def h_agent(ctx):
    ti = ctx.tin
    if not ti and ctx.tool not in ("Agent", "Task"):
        return 0                      # empty or foreign payload: nothing to judge
    stype = ti.get("subagent_type") or "general-purpose"
    info, src = reg.type_info(stype)
    F = []
    out_update = None
    if reg.paused():
        F.append(("pause", "pause.flag exists (429/529 seen): every spawn is denied until `pause clear`", False))
    if info is None:
        F.append(("type", f"subagent_type {stype!r} is not in roles.json (types, patterns) or builtin_allow", False))
    elif info.get("enabled") is False:
        F.append(("type-disabled", f"{stype} is disabled in roles.json ({info.get('enable_when') or 'see roles.json'})", False))
    model = ti.get("model")
    fam = reg.family(model)
    if model is not None and fam not in ("sonnet", "haiku"):
        F.append(("model", f"model {model!r} is not a worker model (sonnet or haiku only)", False))
    elif model is not None and info and info.get("model") and fam != info["model"]:
        F.append(("model-mismatch", f"{stype} runs on {info['model']} in roles.json, call says {model}", False))
    elif model is None and info is None:
        F.append(("model", "the model cannot be resolved (unknown type, none given)", False))
    elif model is None and src == "builtin":
        ti2 = dict(ti)
        ti2["model"] = info["model"]
        out_update = ti2
    eff = ti.get("effort")
    if isinstance(eff, dict):
        eff = eff.get("level")
    if str(eff or "").lower() in ("xhigh", "max"):
        F.append(("effort", f"effort {eff} is denied for workers (low, medium or high)", False))
    cinfo, _ = reg.type_info(ctx.agent_type) if ctx.ident == "agent" else (None, None)
    crole = (cinfo or {}).get("role")
    if ctx.ident == "agent":
        if crole == "helper":
            F.append(("helper-spawns", "a helper spawns nothing", False))
        elif cinfo is None:
            F.append(("caller-type", f"caller type {ctx.agent_type!r} is not in roles.json and may not spawn", False))
        elif stype not in cinfo.get("may_spawn", []):
            F.append(("spawn-type", f"{ctx.agent_type} may spawn {cinfo.get('may_spawn') or 'nothing'}, not {stype}", False))
    elif ctx.ident == "job":
        F.append(("job-spawns", "a job spawns nothing", False))
    elif ctx.ident == "lead" and info and info.get("role") == "helper":
        F.append(("lead-spawns-helper", "the Lead spawns team agents and reviewers, not helpers", False))
    prompt = ti.get("prompt") if isinstance(ti.get("prompt"), str) else ""
    if info is not None and src != "builtin" and info.get("enabled") is not False:
        probs = brief_problems(prompt, info.get("role") == "helper", ctx.cwd)
        if probs:
            F.append(("brief", "; ".join(probs[:6]), False))
    main_writer = False
    owned_pats = []
    if info and src != "builtin" and info.get("role") == "agent" and info.get("writes") == "OWNED_PATHS":
        main = npath(ctx.project)
        gitrepo = in_git_repo(ctx.cwd)
        if info.get("isolation") == "call" and gitrepo and ti.get("isolation") != "worktree":
            F.append(("no-worktree", f"{stype} writes in a git repo: set isolation: worktree on the Agent call", False))
        if info.get("single_writer_main_checkout"):
            main_writer = True
        cg = load_cg()
        owned = []
        if cg is not None and prompt:
            try:
                owned = cg._owned_paths_from_brief(prompt)
            except Exception:  # noqa: BLE001
                owned = []
        if cg is not None and prompt:
            # a prompt that only names a brief file ("Read your brief first: <path>"): OWNED_PATHS come from that file too
            bpath, btxt, named = brief_file_text(prompt, ctx.cwd)
            if btxt:
                try:
                    owned = owned + [o for o in cg._owned_paths_from_brief(btxt) if o not in owned]
                except Exception:  # noqa: BLE001
                    pass
            elif named and not owned:
                F.append(("brief-file-unreadable", "the prompt names a brief file that cannot be read, so OWNED_PATHS cannot "
                                                   "be checked (dirty base checkout, live paths)", False))
        lp = live_patterns(main)
        rels = []
        for o in owned:
            op = npath(re.sub(r"/\*\*?$|/\*$", "", o.replace("\\", "/")), ctx.cwd)
            if not under(op, main):
                continue
            rel = rel_to(op, main) or ""
            rels.append(rel)
            for g in lp:
                gp = g.split("*")[0].rstrip("/")
                if match_glob(g, rel) or match_glob(g, rel + "/x") or (rel and gp.startswith(rel + "/")):
                    F.append(("owned-live-path", f"OWNED_PATHS {o} lies in .nj/live-paths.txt ({g})", False))
                    break
        if main_writer:
            # D23: a main-checkout writer is the single writer of ITS OWNED_PATHS. A second one is refused only when its
            # paths overlap (or either list is unknown); disjoint document writers may run side by side.
            owned_pats = main_owned_patterns(owned, ctx.cwd)
            snap = reg.snapshot()
            for e in snap.get("entries", []) + snap.get("reservations", []):
                if e.get("main_writer") and not e.get("suspect") and e.get("project") == ctx.project                         and owned_overlap(owned_pats, e.get("owned") or []):
                    F.append(("second-main-writer", f"{e.get('agent_type') or e.get('subagent_type')} already writes the same "
                                                    "OWNED_PATHS in the main checkout", False))
                    break
        if gitrepo and rels and not main_writer and not any(f[0] == "owned-live-path" for f in F):
            lit = [r.split("*")[0].rstrip("/") or "." for r in rels]
            d = git_dirty(main, lit)
            if d:
                F.append(("dirty-owned", f"OWNED_PATHS are dirty in the base checkout (checkpoint first): {d.splitlines()[0][:80]}", False))
    # soft denials: log only until the interactive S3/S4 results are attested (gov4_registry.soft)
    caller = ctx.agent_id or "lead"
    c = reg.counts()
    if c["live"] + c["pending"] + 1 > c["wave"]:
        F.append(("wave", f"live {c['live']} + pending {c['pending']} + 1 exceeds the operating wave {c['wave']}", True))
    if ctx.ident == "agent":
        limit = min(int(reg.read_roles().get("limits", {}).get("helpers_hard_max", 4)), int((cinfo or {}).get("max_helpers", 3) or 3))
        if len(reg.children_of(caller)) + 1 > limit:
            F.append(("helper-allowance", f"{ctx.agent_type} already has {len(reg.children_of(caller))} live helpers (allowance {limit})", True))
    code = finish(ctx, F)
    if code == 0:
        reg.reserve(caller, stype, (info or {}).get("role"), ctx.pl.get("tool_use_id"), ctx.session, ctx.project, main_writer,
                    owned=owned_pats if main_writer else None)
        reg.log_event({"event": "spawn", "caller": caller, "type": stype, "model": model, "mode": ctx.mode})
        if out_update is not None:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow",
                                                     "permissionDecisionReason": "builtin agent forced to its worker model",
                                                     "updatedInput": out_update}}))
    return code


# ------------------------------------------------------------ start / stop ---

def h_start(ctx):
    pl = ctx.pl
    e = reg.convert(pl.get("agent_id"), pl.get("agent_type"), ctx.session, pl.get("transcript_path", ""), ctx.project)
    reg.log_event({"event": "start", "agent_id": pl.get("agent_id"), "agent_type": pl.get("agent_type"),
                   "parent": (e or {}).get("parent")})
    return 0


def tail_rate_limited(pl):
    """429 or 529 in the last 64 KB of the agent transcript (error records only) or in the last message."""
    msg = pl.get("last_assistant_message") or ""
    if re.match(r"\s*(API Error:?\s*)?(429|529)\b", msg) or re.search(r"API Error:?\s*(429|529)\b", msg[:300]):
        return "last message reports 429/529"
    path = pl.get("agent_transcript_path")
    if not path or not os.path.isfile(path):
        return None
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            f.seek(max(0, size - 65536))
            data = f.read().decode("utf-8", "replace")
    except OSError:
        return None
    for line in data.splitlines()[-60:]:
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if not isinstance(d, dict):
            continue
        err = d.get("error") if isinstance(d.get("error"), dict) else None
        is_err = d.get("type") in ("system", "error") or d.get("isApiErrorMessage") or d.get("subtype") == "api_error" or err
        if not is_err:
            continue
        st = (err or {}).get("status") or d.get("status") or d.get("status_code") or d.get("code")
        typ = str((err or {}).get("type") or d.get("error_type") or "")
        if str(st) in ("429", "529") or typ in ("rate_limit_error", "overloaded_error"):
            return f"transcript error record: status {st} {typ}".strip()
    return None


def receipt_core(msg):
    lines = msg.splitlines()
    di = next((i for i, ln in enumerate(lines) if ln.strip() == "DETAIL" or ln.startswith("DETAIL ")), None)
    return "\n".join(lines if di is None else lines[:di]), ("\n".join(lines[di + 1:]).strip() if di is not None else "")


FIELD_RE = r"(?m)^\s*(?:\+\s*)?{}\s*[:=]\s*(.*)$"


def field(core, name):
    m = re.search(FIELD_RE.format(re.escape(name)), core)
    return m.group(1).strip() if m else ""


def changed_list(core):
    m = re.search(FIELD_RE.format("CHANGED"), core)
    if not m:
        return []
    text = m.group(1)
    rest = core[m.end():].splitlines()
    for ln in rest:
        if re.match(r"^\s*(?:\+\s*)?[A-Z][A-Z@_ -]{2,}\s*[:=]", ln) or re.match(r"^\s*(STATUS|FINDING|EVIDENCE|FILES-SYMBOLS|RISK|NEXT ACTION)\b", ln):
            break
        text += "\n" + ln
    text = re.sub(r"\([^)]*\)", " ", text)
    out = []
    for t in re.split(r"[,;\s]+", text):
        t = t.strip("`'\"").replace("\\", "/")
        if t and t.lower() not in ("none", "n/a", "and") and not t.startswith("#") and re.search(r"[A-Za-z0-9_.]", t):
            out.append(t[2:] if t.startswith("./") else t)
    return out


def default_branch(root):
    for b in ("main", "master"):
        code, _, _ = run(["git", "-C", root, "rev-parse", "--verify", "-q", f"refs/heads/{b}"])
        if code == 0:
            return b
    return None


def receipt_problems(ctx, msg):
    """Stop-hook receipt checks. Returns [(rule, reason)] (empty = clean)."""
    cg = load_cg()
    out = []
    if cg is not None:
        try:
            for a, b, c in cg.receipt_violations(msg):
                out.append(("receipt", f"{a}: {c}"))
        except Exception as e:  # noqa: BLE001
            reg.log_event({"event": "receipt-check-error", "err": repr(e)[:200]})
    core, _ = receipt_core(msg)
    branch = field(core, "BRANCH").split()[0] if field(core, "BRANCH") else ""
    head = field(core, "HEAD").split()[0].lower() if field(core, "HEAD") else ""
    root = npath(ctx.project)
    if branch and branch.lower() != "none":
        code, out_sha, _ = run(["git", "-C", root, "rev-parse", "--verify", "-q", f"refs/heads/{branch}"])
        if code != 0:
            out.append(("lostwork", f"branch ref {branch} does not exist: the work is not saved"))
        else:
            sha = out_sha.strip().lower()
            if head and not (sha.startswith(head) or head.startswith(sha)):
                out.append(("head-mismatch", f"receipt HEAD {head[:12]} != tip of {branch} {sha[:12]}"))
            db = default_branch(root)
            if db:
                code, mb, _ = run(["git", "-C", root, "merge-base", db, branch])
                if code == 0:
                    code, names, _ = run(["git", "-C", root, "diff", "--name-only", f"{mb.strip()}..{branch}"])
                    diff = {x.strip().replace("\\", "/") for x in names.splitlines() if x.strip()}
                    ch = []
                    for t in changed_list(core):
                        if re.match(r"^[A-Za-z]:/|^/", t):
                            if under(npath(t), root):
                                ch.append(rel_to(npath(t), root))
                            continue
                        ch.append(t)
                    pats = [c for c in ch if any(x in c for x in "*?{")]
                    exact = {c for c in ch if c not in pats}
                    missing = sorted(diff - exact - {d for d in diff if any(match_glob(p_, d) for p_ in pats)})
                    extra = sorted((exact - diff) | {p_ for p_ in pats if not any(match_glob(p_, d) for d in diff)})
                    if missing or extra:
                        out.append(("changed-mismatch", f"CHANGED differs from git diff --name-only {mb.strip()[:8]}..{branch}: "
                                                         f"missing {missing[:4]} extra {extra[:4]}"))
            code, wl, _ = run(["git", "-C", root, "worktree", "list", "--porcelain"])
            if code == 0:
                wts = re.split(r"\n\n+", wl.strip())
                for blk in wts:
                    if f"branch refs/heads/{branch}" in blk:
                        m = re.match(r"worktree (.+)", blk)
                        if m and os.path.isdir(m.group(1).strip()):
                            c2, st_out, _ = run(["git", "-C", m.group(1).strip(), "status", "--porcelain"])
                            if c2 == 0 and st_out.strip():
                                out.append(("dirty-worktree", f"worktree {m.group(1).strip()[-40:]} has uncommitted changes"))
    kids = reg.children_of(ctx.agent_id) if ctx.agent_id else []
    if kids:
        out.append(("live-children", f"{len(kids)} helper(s) still live: wait for them before the receipt"))
    return out


def write_text(path, text, base=None):
    """Atomic text write. With base, the real path of the target must lie inside base (SB-01): the stop hook builds file
    names from an agent's own words, so every such write is confined and nothing outside the results tree is touched."""
    try:
        if base is not None and not under(npath(path), npath(base)):
            reg.log_event({"event": "write-refused", "path": str(path)[:200], "base": str(base)[:200]})
            return False
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if base is not None and not under(npath(os.path.dirname(path)), npath(base)):
            return False
        tmp = path + f".{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
        return True
    except OSError:
        return False


def safe_name(value, fallback=""):
    """A single file-name part: letters, digits, dot, dash, underscore only; '', '.' and '..' are refused."""
    v = re.sub(r"[^A-Za-z0-9_.-]", "-", str(value or ""))[:80].strip(".-") if value is not None else ""
    return v if v and v not in (".", "..") and not set(v) <= set(".-") else fallback


def status_word(core):
    w = (field(core, "STATUS") or "partial").split()
    w = re.sub(r"[^a-z]", "", (w[0] if w else "").lower())
    if w in ("ok", "done", "success", "pass", "complete", "completed"):
        return "ok"
    if w in ("failed", "fail", "blocked", "error", "stop", "stopped"):
        return "failed"
    return "partial"


def finalise_team(ctx, info, msg):
    pl = ctx.pl
    core, detail = receipt_core(msg)
    first = next((ln for ln in core.splitlines() if ln.strip()), "")
    m = re.match(r"^RECEIPT\s+(\S+)/(\S+)\s*$", first.strip())
    # SB-01: run id and name come from the agent's own words. Reduce each to one safe file-name part; a header that
    # cannot be reduced (empty, '.', '..') is treated as no header at all.
    run_id, name = (safe_name(m.group(1)), safe_name(m.group(2))) if m else ("", "")
    if m and not (run_id and name):
        m = None
    root = ctx.project
    results = os.path.join(root, ".agent-ops", "results")
    stage = safe_name(info.get("stage") or name or ctx.agent_type or "agent", "agent")
    status = status_word(core)
    branch = field(core, "BRANCH").split()[0] if field(core, "BRANCH") else "none"
    head = field(core, "HEAD").split()[0] if field(core, "HEAD") else "none"
    hs = field(core, "HELPERS_SPAWNED").split()[0] if field(core, "HELPERS_SPAWNED") else "0"
    saved = {}
    if detail:
        sp = os.path.join(root, "work", "sdlc", stage, "STATE.md")
        if write_text(sp, detail + "\n", base=os.path.join(root, "work", "sdlc")):
            saved["state"] = sp
    if not m:
        write_text(os.path.join(results, "_unlabelled", f"{safe_name(ctx.agent_id, 'agent')}.md"), msg, base=results)
        reg.log_event({"event": "stop-team", "agent_id": ctx.agent_id, "note": "no usable RECEIPT header; text saved"})
        return saved
    entry = next((e for e in reg.snapshot().get("entries", []) if e.get("id") == ctx.agent_id), {})
    parent = entry.get("parent") or "lead"
    gates = [ln.strip() for ln in (field(core, "GATES@HEAD") or "").splitlines() if ln.strip()] or \
            ([field(core, "GATES@HEAD")] if field(core, "GATES@HEAD") else [])
    doc = {"agent": name, "stage": stage, "status": status, "files": changed_list(core), "gates": gates, "artefacts": [],
           "leftovers": [], "detail_path": saved.get("state", "none"), "run_id": run_id, "role": info.get("role"),
           "parent": "lead" if parent in ("lead", None) else str(parent), "model": info.get("model"),
           "helpers_spawned": int(hs) if hs.isdigit() else None, "branch": branch, "head": head,
           "gates_at_head": gates, "governance_version": reg.GOV, "effort": info.get("effort")}
    if status != "ok":
        doc["failure_class"] = "TEAM_FAILURE"
    rp = os.path.join(results, run_id, f"{name}.json")
    if write_text(rp, json.dumps(doc, indent=1, ensure_ascii=False), base=results):
        saved["receipt"] = rp
    relay = os.environ.get("NJ_RELAY") or os.path.join(HERE, "relay.py")
    if os.path.isfile(relay):
        cmd = [sys.executable, "-X", "utf8", relay, "ledger", root, run_id, "--agent", name, "--stage", stage, "--status", status,
               "--role", info.get("role") or "agent", "--model", info.get("model") or "sonnet",
               "--parent", doc["parent"], "--helpers-spawned", str(doc["helpers_spawned"] or 0)]
        if info.get("effort"):
            cmd += ["--effort", info["effort"]]
        if branch.lower() != "none":
            cmd += ["--branch", branch]
            if re.fullmatch(r"[0-9a-fA-F]{7,40}", head):
                cmd += ["--head", head]
        code, so, se = run(cmd, timeout=30)
        if code != 0:
            reg.alert("ledger", f"relay.py ledger failed for {run_id}/{name}: {(se or so).strip()[:200]}", root)
        else:
            saved["ledger"] = True
    if branch.lower() != "none" and status == "ok":
        mq = os.path.join(root, "work", "merge-queue")
        try:
            os.makedirs(mq, exist_ok=True)
            seq = len([x for x in os.listdir(mq) if x.endswith(".json")]) + 1
            tk = os.path.join(mq, f"{seq:03d}-{name}.json")
            ok1 = write_text(tk, json.dumps({"name": name, "run": run_id, "branch": branch, "head": head, "stage": stage,
                                             "changed": changed_list(core), "receipt": saved.get("receipt"),
                                             "queued": time.strftime("%Y-%m-%dT%H:%M:%S"), "state": "queued"}, indent=1), base=mq)
            write_text(os.path.join(mq, f"READY-{name}.flag"), f"{run_id} {branch} {head}\n", base=mq)
            if ok1:
                saved["merge_ticket"] = tk
        except OSError:
            pass
    reg.log_event({"event": "stop-team", "agent_id": ctx.agent_id, "run": run_id, "name": name, "status": status, "saved": list(saved)})
    return saved


def h_stop_team(ctx):
    pl = ctx.pl
    aid = pl.get("agent_id")
    info, src = reg.type_info(pl.get("agent_type"))
    rl = tail_rate_limited(pl)
    if rl:
        reg.set_pause(f"{pl.get('agent_type')} {aid}: {rl}")
        reg.alert("ratelimit", f"429/529 seen: pause.flag set ({rl})", ctx.project)
    if info is None or src == "builtin" or info.get("role") not in ("agent", "reviewer") or info.get("enabled") is False:
        reg.release(aid, ctx.project)
        return 0
    msg = pl.get("last_assistant_message") or ""
    if info.get("role") == "agent":
        probs = receipt_problems(ctx, msg)
        lost = [p_ for p_ in probs if p_[0] == "lostwork"]
        if lost:
            reg.alert("lostwork", lost[0][1] + f" (agent {aid})", ctx.project)
        if probs:
            guard = bool(pl.get("stop_hook_active"))
            if guard:
                reg.alert("receipt", f"{aid} {pl.get('agent_type')} stopped with a receipt problem after one block: " +
                          "; ".join(f"{a}: {b}" for a, b in probs)[:300], ctx.project)
                probs = []
            else:
                code = finish(ctx, [(a, b, False) for a, b in probs])
                if code == 2:
                    return 2
    res = os.path.join(ctx.project, ".agent-ops", "results")
    if info.get("role") == "agent":
        finalise_team(ctx, info, msg)
    else:           # SB-01: a reviewer's RECEIPT text is saved by agent id only; it never names a path
        write_text(os.path.join(res, "_reviews", f"{safe_name(aid, 'reviewer')}.md"), msg, base=res)
    reg.release(aid, ctx.project)
    return 0


def h_stop_helper(ctx):
    pl = ctx.pl
    aid = pl.get("agent_id")
    rl = tail_rate_limited(pl)
    if rl:
        reg.set_pause(f"helper {pl.get('agent_type')} {aid}: {rl}")
        reg.alert("ratelimit", f"429/529 seen: pause.flag set ({rl})", ctx.project)
    msg = pl.get("last_assistant_message") or ""
    if msg:
        res = os.path.join(ctx.project, ".agent-ops", "results")
        write_text(os.path.join(res, "_helpers", f"{safe_name(aid, 'helper')}.txt"), msg, base=res)
    if len([ln for ln in msg.splitlines() if ln.strip()]) > int(reg.read_roles().get("limits", {}).get("helper_result_lines", 10)):
        log_dec(ctx, "helper-result-length", "helper result over 10 lines", "would-deny")
    reg.release(aid, ctx.project)
    reg.log_event({"event": "stop-helper", "agent_id": aid})
    return 0


def h_session_start(ctx):
    r = reg.read_roles()
    ep = os.environ.get("CLAUDE_CODE_ENTRYPOINT", "")
    src = ctx.pl.get("source", "")
    if (os.environ.get("NJ_ROLE") != "job" and not ctx.agent_id and src in r.get("lead_session_sources", ["startup", "resume", "clear"])
            and ep in r.get("lead_entrypoints", ["claude-vscode", "cli"]) and ctx.session):
        reg.register_lead(ctx.session, ctx.cwd, ep, src, ctx.pl.get("permission_mode") or "")
        reg.log_event({"event": "lead-registered", "session": ctx.session, "entrypoint": ep, "source": src})
    # `gov4.py doctor --quiet` (WP5) when installed: a failure is shown to the model and raises an alert flag
    cands = [os.environ.get("NJ_GOV4", ""), os.path.join(reg.home(), "gov4.py"), os.path.join(HERE, "gov4.py")]
    try:
        cur = open(os.path.join(reg.home(), "bin", "CURRENT"), encoding="utf-8").read().strip()
        cdir = cur if os.path.isabs(cur) else os.path.join(reg.home(), "bin", cur)
        if under(npath(cdir), npath(os.path.join(reg.home(), "bin"))):       # D28: a pointer outside bin/ is ignored
            cands.insert(1, os.path.join(cdir, "gov4.py"))
    except OSError:
        pass
    g4 = next((c for c in cands if c and os.path.isfile(c)), None)
    # A9: the doctor never blocks a session and stays quiet outside enforce and for headless jobs. Its answer reaches the
    # model and the project only in enforce; in audit it is logged and flagged in the state root alone.
    if g4 and os.environ.get("NJ_SKIP_DOCTOR") != "1" and os.environ.get("NJ_ROLE") != "job":
        code, so, se = run([sys.executable, "-X", "utf8", g4, "doctor", "--quiet"], timeout=15)
        reg.log_event({"event": "doctor", "rc": code})
        if code != 0:
            msg = ((so or "") + (se or "")).strip()[:600] or f"doctor exited {code}"
            if ctx.mode == "enforce":
                reg.alert("doctor", msg[:300], ctx.project)
                print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                                         "additionalContext": "NJ governance doctor reported: " + msg}}))
            else:
                reg.alert("doctor", msg[:300], None)
    return 0


def h_reap(ctx):
    st = reg.reconcile(ctx.project)
    print(json.dumps({"reconciled": st, "line": reg.live_line(), "paused": reg.paused()}))
    return 0


HANDLERS = {"agent": h_agent, "git": h_git, "write": h_write, "mcp": h_mcp, "workflow": h_workflow, "start": h_start,
            "stop-team": h_stop_team, "stop-helper": h_stop_helper, "session-start": h_session_start, "ticket": h_ticket,
            "bash": h_bash, "reap": h_reap}


def trace(sub, raw):
    path = os.environ.get("NJ_TRACE_FILE") or reg.p("trace.jsonl")
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "sub": sub, "entrypoint": os.environ.get("CLAUDE_CODE_ENTRYPOINT"),
                                "role": os.environ.get("NJ_ROLE"), "stdin": raw[:20000]}, ensure_ascii=False) + "\n")
    except OSError:
        pass


def read_stdin():
    try:
        data = sys.stdin.buffer.read().decode("utf-8", "replace")
    except (AttributeError, OSError, ValueError):
        try:
            data = sys.stdin.read()
        except Exception:  # noqa: BLE001
            data = ""
    return data.lstrip("﻿")


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    traced = "--trace" in argv
    argv = [a for a in argv if a != "--trace"]
    sub = argv[0] if argv else ""
    if sub == "selftest":
        return selftest()
    if sub in ("-h", "--help", "help", ""):
        if traced:
            trace("", read_stdin())
            return 0
        print(__doc__)
        return 0 if sub else 2
    raw = read_stdin()
    if traced:
        trace(sub, raw)
        return 0
    mode = reg.get_mode()
    if sub not in HANDLERS:
        print(f"unknown hook subcommand {sub!r}", file=sys.stderr)
        return 2 if mode == "enforce" else 0         # D26: a typo in settings.json must not block outside enforce
    if mode == "off":
        return 0
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except ValueError:
        payload = {}
    ctx = None
    try:
        ctx = make_ctx(sub, payload, raw)
        if ctx.ident == "lead" and ctx.pl.get("permission_mode"):
            reg.refresh_lead_mode(ctx.session, ctx.pl.get("permission_mode"))
        return HANDLERS[sub](ctx)
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        reg.alert("hook", f"gov4_hook {sub} internal error: {type(e).__name__}: {e}"[:300],
                  project_root((payload or {}).get("cwd")) if isinstance(payload, dict) else None)
        if sub == "agent" and mode == "enforce":
            sys.stderr.write(f"NJ governance (gov4): internal hook error, Agent spawn denied (fail closed): {type(e).__name__}\n")
            return 2
        return 0


def selftest():
    """The hook's tests live in test_sdlc.py (hook_selftest) so this script stays small and fast to start."""
    import test_sdlc
    return test_sdlc.hook_selftest()


if __name__ == "__main__":
    sys.exit(main())
