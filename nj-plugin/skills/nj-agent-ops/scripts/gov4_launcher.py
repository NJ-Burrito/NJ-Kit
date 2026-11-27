#!/usr/bin/env python3
"""NJ Governance v4 hook launcher (stdlib only, tiny on purpose).

settings.json runs  <python> -I -X utf8 ~/.claude/nj/gov4_launcher.py <sub>  for every hook. The launcher reads
$NJ_HOME/bin/CURRENT (a directory name under bin/, or an absolute path), runs bin/<cur>/gov4_hook.py with the
same argv and stdin, and falls back to bin/PREVIOUS when the current copy cannot be imported or crashes.
If both fail it ALLOWS the call and raises ALERT-hook.flag, EXCEPT in enforce mode when the caller is an agent
(agent_id in the payload) or a job (NJ_ROLE=job) and the raw command text contains git or li.py: then it denies
(exit 2), so a broken hook can neither stop all work nor silently open git. Audit mode (the default) and off never
block. A CURRENT or PREVIOUS pointer outside ~/.claude/nj/bin is ignored (D28). The settings.json hook command wraps
this file in a guard that exits 0 when the file itself is missing (D26), so a deleted launcher blocks nothing.

  gov4_launcher.py <sub>        run the hook      gov4_launcher.py --selftest     self-check (no ~/.claude writes)
"""
import io
import json
import os
import re
import sys
import time

GIT_RE = re.compile(r"(?<![A-Za-z0-9])git(?![A-Za-z0-9])|li\.py", re.I)


def home():
    return os.environ.get("NJ_HOME") or os.path.join(os.path.expanduser("~"), ".claude", "nj")


def _read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _norm(path):
    return os.path.normcase(os.path.realpath(path))


def inside_bin(d):
    """D28: bin/CURRENT and bin/PREVIOUS may point only at a folder inside ~/.claude/nj/bin (resolved, junctions followed);
    an absolute path elsewhere would run an agent-chosen script in every future hook."""
    b = _norm(os.path.join(home(), "bin"))
    n = _norm(d)
    return n == b or n.startswith(b + os.sep)


def targets():
    h = home()
    out = []
    for name in ("CURRENT", "PREVIOUS"):
        v = _read(os.path.join(h, "bin", name))
        if v:
            d = v if os.path.isabs(v) else os.path.join(h, "bin", v)
            if not inside_bin(d):
                alert(f"bin/{name} points outside {os.path.join(h, 'bin')}: ignored ({v[:120]})")
                continue
            t = os.path.join(d, "gov4_hook.py")
            if t not in out:
                out.append(t)
    return out


def mode():
    m = (os.environ.get("NJ_MODE_OVERRIDE") or _read(os.path.join(home(), "mode")) or "audit").lower()
    return m if m in ("off", "audit", "enforce") else "audit"


def alert(msg):
    try:
        os.makedirs(home(), exist_ok=True)
        with open(os.path.join(home(), "ALERT-hook.flag"), "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except OSError:
        pass


def _load_and_run(target, argv, raw):
    """Import target in-process and call main(argv) with stdin=raw. Returns (code, stdout, stderr)."""
    import importlib.util
    d = os.path.dirname(target)
    for k in [k for k in sys.modules if k.startswith("gov4_")]:
        del sys.modules[k]                       # a fallback must not see the failed copy's registry
    sys.path.insert(0, d)
    old = (sys.stdin, sys.stdout, sys.stderr)
    out, err = io.StringIO(), io.StringIO()
    try:
        sys.stdin = io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8")
        sys.stdout, sys.stderr = out, err
        spec = importlib.util.spec_from_file_location("gov4_hook", target)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["gov4_hook"] = mod
        spec.loader.exec_module(mod)
        try:
            code = mod.main(list(argv))
        except SystemExit as e:
            code = e.code
        if code is None:
            code = 0
        if not isinstance(code, int):
            code = 1
        return code, out.getvalue(), err.getvalue()
    finally:
        sys.stdin, sys.stdout, sys.stderr = old
        try:
            sys.path.remove(d)
        except ValueError:
            pass


def command_text(raw):
    try:
        d = json.loads(raw.decode("utf-8", "replace"))
    except ValueError:
        return raw.decode("utf-8", "replace"), {}
    if not isinstance(d, dict):
        return "", {}
    ti = d.get("tool_input") if isinstance(d.get("tool_input"), dict) else {}
    cmd = ti.get("command") if d.get("tool_name") in ("Bash", "PowerShell") else ""
    return (cmd if isinstance(cmd, str) else ""), d


def run(argv, raw):
    """Returns (exit code, stdout, stderr)."""
    last = ""
    for t in targets():
        if not os.path.isfile(t):
            last = f"missing {t}"
            continue
        try:
            code, so, se = _load_and_run(t, argv, raw)
            if last:
                alert(f"hook fell back to {t}: {last}")
            return code, so, se
        except BaseException as e:  # noqa: BLE001  (ImportError, SyntaxError, a crash in main)
            last = f"{t}: {type(e).__name__}: {str(e)[:160]}"
    alert(f"no working hook target ({last or 'bin/CURRENT and bin/PREVIOUS are empty'})")
    cmd, d = command_text(raw)
    ctx_agent = bool(d.get("agent_id")) or os.environ.get("NJ_ROLE") == "job"
    if ctx_agent and GIT_RE.search(cmd) and mode() == "enforce":
        return 2, "", "NJ governance (gov4 launcher): the hook is broken and this agent or job command mentions git or li.py: denied\n"
    return 0, "", ""


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--selftest":
        return selftest()
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if mode() == "off":
        return 0
    try:
        raw = sys.stdin.buffer.read()
    except (AttributeError, OSError, ValueError):
        raw = b""
    if argv[0] == "ticket" and b"gov4" not in raw.lower():
        return 0                      # A10: the ticket hook has nothing to do unless the command names gov4
    code, so, se = run(argv, raw)
    if so:
        sys.stdout.write(so)
    if se:
        sys.stderr.write(se)
    return code


def selftest():
    import shutil
    import tempfile
    failures = []

    def check(name, cond):
        if not cond:
            failures.append(name)
            print("FAIL", name)

    tmp = tempfile.mkdtemp(prefix="gov4launch-")
    saved = {k: os.environ.get(k) for k in ("NJ_HOME", "NJ_ROLE", "NJ_MODE_OVERRIDE")}
    os.environ["NJ_HOME"] = tmp
    os.environ.pop("NJ_ROLE", None)
    here = os.path.dirname(os.path.abspath(__file__))

    def mk(name, body):
        d = os.path.join(tmp, "bin", name)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "gov4_hook.py"), "w", encoding="utf-8") as f:
            f.write(body)

    def point(cur=None, prev=None):
        for n, v in (("CURRENT", cur), ("PREVIOUS", prev)):
            p = os.path.join(tmp, "bin", n)
            if os.path.exists(p):
                os.remove(p)
            if v:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", encoding="utf-8") as f:
                    f.write(v)

    def alerts():
        p = os.path.join(tmp, "ALERT-hook.flag")
        if os.path.exists(p):
            os.remove(p)
            return True
        return False

    def payload(**kw):
        return json.dumps(kw).encode()

    try:
        os.environ["NJ_MODE_OVERRIDE"] = "enforce"
        mk("good", "import sys\ndef main(a):\n    sys.stdout.write('GOOD ' + ' '.join(a) + ' ' + sys.stdin.read())\n    return 0\n")
        mk("deny", "import sys\ndef main(a):\n    sys.stderr.write('no\\n')\n    return 2\n")
        mk("syntax", "def main(a:\n")
        mk("importerr", "import nonexistent_module_gov4\ndef main(a):\n    return 0\n")
        mk("crash", "import sys\ndef main(a):\n    sys.stdout.write('partial output')\n    raise RuntimeError('boom')\n")
        point("good")
        c, o, e = run(["git"], b"PAYLOAD")
        check("current runs and passes stdin/stdout through", c == 0 and o == "GOOD git PAYLOAD")
        point("deny")
        c, o, e = run(["git"], b"{}")
        check("target exit 2 is returned with stderr", c == 2 and e.strip() == "no")
        point("syntax", "good")
        alerts()
        c, o, e = run(["git"], b"x")
        check("syntax error falls back to PREVIOUS", c == 0 and o.startswith("GOOD"))
        check("fallback raises the alert", alerts())
        point("importerr", "good")
        c, o, e = run(["git"], b"x")
        check("import error falls back", c == 0 and o.startswith("GOOD"))
        point("crash", "good")
        c, o, e = run(["git"], b"x")
        check("runtime crash falls back and drops partial output", c == 0 and o.startswith("GOOD") and "partial" not in o)
        point("crash", "syntax")
        c, o, e = run(["git"], b"{}")
        check("both broken allows", c == 0)
        check("both broken raises ALERT-hook.flag", alerts())
        point(None, None)
        c, o, e = run(["git"], b"{}")
        check("no CURRENT allows with alert", c == 0 and alerts())
        point("crash", "crash")
        gp = payload(tool_name="Bash", agent_id="a1", tool_input={"command": "git push origin HEAD"})
        c, o, e = run(["git"], gp)
        check("both broken + agent + git -> deny", c == 2 and "denied" in e)
        c, o, e = run(["git"], payload(tool_name="Bash", agent_id="a1", tool_input={"command": "python scripts/linkedin/li.py post x"}))
        check("both broken + agent + li.py -> deny", c == 2)
        c, o, e = run(["git"], payload(tool_name="Bash", agent_id="a1", tool_input={"command": "echo hello gitignore"}))
        check("both broken + agent + no git -> allow", c == 0)
        c, o, e = run(["git"], payload(tool_name="Bash", tool_input={"command": "git push"}))
        check("both broken + lead (no agent_id) + git -> allow", c == 0)
        os.environ["NJ_ROLE"] = "job"
        c, o, e = run(["git"], payload(tool_name="Bash", tool_input={"command": "git push"}))
        check("both broken + job + git -> deny", c == 2)
        os.environ.pop("NJ_ROLE")
        c, o, e = run(["agent"], payload(tool_name="Agent", agent_id="a1", tool_input={"prompt": "use git worktree-x", "subagent_type": "x"}))
        check("both broken + agent spawn mentioning git in a prompt -> allow", c == 0)
        os.environ["NJ_MODE_OVERRIDE"] = "audit"
        c, o, e = run(["git"], gp)
        check("audit never blocks", c == 0)
        os.environ["NJ_MODE_OVERRIDE"] = "enforce"
        # the real hook through the launcher (a copy under bin/<sha8>/), fixtures from the recorded payloads
        real = os.path.join(tmp, "bin", "real0001")
        os.makedirs(real, exist_ok=True)
        for fn in ("gov4_hook.py", "gov4_registry.py"):
            shutil.copy(os.path.join(here, fn), os.path.join(real, fn))
        rt = os.path.join(here, "..", "templates", "roles.json")
        if os.path.isfile(rt):
            shutil.copy(rt, os.path.join(real, "roles.json"))
        point("real0001", "syntax")
        fx = os.path.join(here, "..", "hook-fixtures")
        if os.path.isdir(fx):
            with open(os.path.join(fx, "agent-git-push.json"), "rb") as f:
                c, o, e = run(["git"], f.read())
            check("real hook via launcher denies agent git push", c == 2 and "git-write" in e)
            with open(os.path.join(fx, "agent-git-status.json"), "rb") as f:
                c, o, e = run(["git"], f.read())
            check("real hook via launcher allows agent git status", c == 0)
            c, o, e = run(["git"], b"{}")
            check("real hook via launcher allows an empty payload", c == 0)
        # D28: a CURRENT or PREVIOUS pointer outside bin/ is never executed
        outside = tempfile.mkdtemp(prefix="gov4outside-")
        with open(os.path.join(outside, "gov4_hook.py"), "w", encoding="utf-8") as f:
            f.write("import sys\ndef main(a):\n    sys.stdout.write('EVIL')\n    return 0\n")
        try:
            alerts()
            point(outside, None)
            c, o, e = run(["git"], b"{}")
            check("absolute CURRENT outside bin/ is ignored", "EVIL" not in o and c == 0)
            check("and raises the alert", alerts())
            point(os.path.relpath(outside, os.path.join(tmp, "bin")), None)
            c, o, e = run(["git"], b"{}")
            check("relative CURRENT that climbs out of bin/ is ignored", "EVIL" not in o and c == 0)
            point(None, outside)
            c, o, e = run(["git"], b"{}")
            check("PREVIOUS outside bin/ is ignored", "EVIL" not in o)
            point("real0001", "syntax")
            c, o, e = run(["git"], b"{}")
            check("a CURRENT inside bin/ still runs", c == 0)
        finally:
            shutil.rmtree(outside, ignore_errors=True)
        os.environ["NJ_MODE_OVERRIDE"] = "off"
        check("mode off: main returns 0 without reading", main(["git"]) == 0)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)
    print("launcher selftest:", "FAIL " + ", ".join(failures) if failures else "ok")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
