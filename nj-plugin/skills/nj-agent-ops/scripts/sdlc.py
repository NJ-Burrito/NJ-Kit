#!/usr/bin/env python3
"""SDLC agent team monitor (stdlib only), machine-wide. Commands: status, board, rotate <stage>, hook.

Project root: --project <dir>, else (hook only) the "cwd" of the SubagentStop payload, else the
current directory. A path inside .claude/worktrees/<x> is always mapped to the main checkout, so state
(work/sdlc/<stage>/STATE.md, BOARD.txt, ROTATE flags) is read and written in MAIN, where the v4
SubagentStop hook (gov4_hook.py stop-team) copies each agent's DETAIL state. State lives under
<root>/work/sdlc/<stage>/ (created on first use). The board shows `live N/cap` from the registry
(gov4_registry.py) when it is next to this script. `rotate` refuses unless the retiring instance stopped
at a clean commit (branch tip == HEAD it recorded, worktree clean); --force skips that check.

Context size of a live stage agent = usage of its LAST assistant message in its
subagent transcript: input_tokens + cache_creation_input_tokens + cache_read_input_tokens.
Transcripts: ~/.claude/projects/<slug>/<session>/subagents/agent-*.jsonl (+ .meta.json
with agentType). A stage agent is one whose agentType (or description) is sdlc-<stage>.
"""
import argparse
import glob
import json
import os
import re
import shutil
import sys
import time

STAGES = ["requirements", "design", "build", "test", "review", "release"]
THRESHOLD = 400000
IDLE_SECS = 30 * 60
HERE = os.path.dirname(os.path.abspath(__file__))


def main_root(path):
    """The main checkout of a path: strips .claude/worktrees/<name>[/...] (agents run in worktrees)."""
    p = os.path.abspath(path)
    m = re.match(r"^(.*?)[\\/]\.claude[\\/]worktrees[\\/][^\\/]+", p, re.I)
    return os.path.normpath(m.group(1)) if m else p


ROOT = main_root(os.getcwd())
STATE_DIR = os.path.join(ROOT, "work", "sdlc")


def set_project(path):
    """Point the module at a project root (state dir and transcript slug follow it); worktrees map to main."""
    global ROOT, STATE_DIR
    ROOT = main_root(path)
    STATE_DIR = os.path.join(ROOT, "work", "sdlc")


def registry_line():
    """`live N/cap` from the machine registry; `live ?/?` when gov4_registry.py is not next to this script."""
    try:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import gov4_registry
        return gov4_registry.live_line()
    except Exception:  # noqa: BLE001  (a board must render without the registry)
        return "live ?/?"


def projects_dir(root=None):
    root = root or ROOT
    base = os.environ.get("SDLC_PROJECTS_DIR")
    if base:
        return base
    home = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    slug = re.sub(r"[^A-Za-z0-9]", "-", root).lower()
    if os.path.isdir(home):
        for d in os.listdir(home):
            if d.lower() == slug:
                return os.path.join(home, d)
    return os.path.join(home, slug)


def context_tokens(path):
    """Context tokens of the last assistant message carrying usage: (tokens, model) or (0, None)."""
    last = (0, None)
    try:
        with open(path, encoding="utf8", errors="replace") as f:
            for line in f:
                if '"usage"' not in line:
                    continue
                try:
                    m = json.loads(line).get("message")
                except ValueError:
                    continue
                u = m.get("usage") if isinstance(m, dict) else None
                if u:
                    t = (u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                         + u.get("cache_read_input_tokens", 0))
                    last = (t, m.get("model"))
    except OSError:
        pass
    return last


def stage_of(meta):
    for key in ("agentType", "description"):
        v = str(meta.get(key, "")).strip().lower()
        m = re.match(r"sdlc-([a-z]+)", v)
        if m and m.group(1) in STAGES:
            return m.group(1)
    return None


def scan(pdir=None):
    """Return {stage: [instances newest first]}; instance = dict(path, tokens, mtime, model)."""
    pdir = pdir or projects_dir()
    out = {s: [] for s in STAGES}
    for jl in glob.glob(os.path.join(pdir, "*", "subagents", "agent-*.jsonl")):
        try:
            with open(jl[:-6] + ".meta.json", encoding="utf8") as f:
                meta = json.load(f)
        except (OSError, ValueError):
            meta = {}
        st = stage_of(meta)
        if not st:
            continue
        tok, model = context_tokens(jl)
        out[st].append(dict(path=jl, tokens=tok, mtime=os.path.getmtime(jl), model=model))
    for s in out:
        out[s].sort(key=lambda i: -i["mtime"])
    return out


def rows(pdir=None, now=None):
    now = now or time.time()
    data = scan(pdir)
    res = []
    for s in STAGES:
        insts = data[s]
        state = "yes" if os.path.exists(os.path.join(STATE_DIR, s, "STATE.md")) else "MISSING"
        if not insts:
            res.append(dict(stage=s, tokens=0, flag="-", live="none", instances=0, state=state, model="-"))
            continue
        i = insts[0]
        live = "live" if now - i["mtime"] < IDLE_SECS else "idle"
        flag = "ROTATE" if i["tokens"] >= THRESHOLD else "ok"
        res.append(dict(stage=s, tokens=i["tokens"], flag=flag, live=live, instances=len(insts),
                        state=state, model=i["model"] or "-"))
    return res


def fmt(res):
    h = f"{'stage':<13}{'ctx tokens':>11}  {'flag':<7}{'live':<6}{'inst':>5}  {'state':<8}model"
    lines = [registry_line(), h, "-" * len(h)]
    for r in res:
        lines.append(f"{r['stage']:<13}{r['tokens']:>11}  {r['flag']:<7}{r['live']:<6}"
                     f"{r['instances']:>5}  {r['state']:<8}{r['model']}")
    return "\n".join(lines)


def cmd_status(a):
    res = rows()
    if a.stage:
        res = [r for r in res if r["stage"] == a.stage]
    print(fmt(res))
    return 0


def cmd_board(a):
    res = rows()
    print(fmt(res))
    for r in res:
        sp = os.path.join(STATE_DIR, r["stage"], "STATE.md")
        nxt = ""
        if os.path.exists(sp):
            with open(sp, encoding="utf8") as f:
                txt = f.read()
            m = re.search(r"## next step\s*\n(.*?)(?:\n## |\Z)", txt, re.S)
            nxt = " ".join(m.group(1).split())[:100] if m else ""
        print(f"  {r['stage']:<13}next: {nxt or '(empty)'}")
    return 0


def _git(root, *args):
    import subprocess
    try:
        r = subprocess.run(["git", "-C", root] + list(args), capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=20)
        return r.returncode, r.stdout
    except (OSError, subprocess.SubprocessError):
        return 127, ""


def recorded_branch(stage, state_text):
    """(branch, head) the retiring instance recorded: newest merge ticket of this stage, else BRANCH/HEAD lines of STATE.md."""
    best = None
    for tk in glob.glob(os.path.join(ROOT, "work", "merge-queue", "*.json")):
        try:
            with open(tk, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            continue
        if d.get("stage") == stage and (best is None or os.path.getmtime(tk) > best[0]):
            best = (os.path.getmtime(tk), d.get("branch"), d.get("head"))
    if best and best[1]:
        return best[1], best[2]
    br = re.search(r"(?mi)^\s*[-*]?\s*`?BRANCH`?\s*[:=]\s*`?(\S+?)`?\s*$", state_text)
    hd = re.search(r"(?mi)^\s*[-*]?\s*`?HEAD`?\s*[:=]\s*`?([0-9a-fA-F]{7,40})", state_text)
    return (br.group(1) if br else None), (hd.group(1) if hd else None)


def clean_commit_problem(stage, state_text):
    """None when the stage stopped at a clean commit (or has no branch: in-place/non-git), else the reason."""
    branch, head = recorded_branch(stage, state_text)
    if not branch or branch.lower() == "none":
        return None
    code, out = _git(ROOT, "rev-parse", "--verify", "-q", f"refs/heads/{branch}")
    if code != 0:
        return f"branch {branch} does not exist: the retiring instance's work is not saved"
    tip = out.strip().lower()
    if head and not (tip.startswith(head.lower()) or head.lower().startswith(tip)):
        return f"HEAD recorded in the handoff ({head[:10]}) is not the tip of {branch} ({tip[:10]}): commit first"
    code, wl = _git(ROOT, "worktree", "list", "--porcelain")
    if code == 0:
        for blk in re.split(r"\n\n+", wl.strip()):
            if f"branch refs/heads/{branch}" in blk:
                m = re.match(r"worktree (.+)", blk)
                if m and os.path.isdir(m.group(1).strip()):
                    c2, st = _git(m.group(1).strip(), "status", "--porcelain")
                    if c2 == 0 and st.strip():
                        return f"worktree of {branch} has uncommitted changes: commit first"
    return None


def role_info(stage):
    try:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import gov4_registry
        return gov4_registry.type_info(f"sdlc-{stage}")[0] or {}
    except Exception:  # noqa: BLE001
        return {}


# used only when gov4_registry.py is not next to this script (the registry is the source: roles.json)
STAGE_FALLBACK = {"build": {"role": "agent", "isolation": "call", "effort": "high"},
                  "review": {"role": "reviewer", "isolation": "none", "effort": "high", "writes": "none"}}


def brief(stage, n):
    """Agent call plus a v4 contract brief for the rotated successor; the Lead fills every <...>."""
    info = role_info(stage) or STAGE_FALLBACK.get(stage, {})
    effort = info.get("effort", "medium")
    role = info.get("role", "agent")
    call_iso = info.get("isolation") == "call"
    iso = ', isolation="worktree"' if call_iso else ""
    # CD-2: ROLE, GIT and the foreground rule come from roles.json (D23): a writer runs in the foreground, a reviewer
    # (writes nothing) may run in the background; a code writer commits on its own branch, a document writer, the test
    # and the release stage write in the main checkout as the single writer and never commit; a reviewer commits nothing.
    writer = role == "agent" and info.get("writes", "OWNED_PATHS") != "none"
    bg = "false" if writer else "true"
    if role == "reviewer":
        git_line = "none (read-only)"
        owned_line = "none (a reviewer writes nothing; the verdict goes in the receipt)"
    elif call_iso:
        git_line = f"worktree-<run>-{stage}-{n} · commit own branch only"
        owned_line = "write ONLY: <Lead fills>. Never: anything outside it."
    else:
        git_line = "none (main checkout, single writer)"
        owned_line = "write ONLY: <Lead fills>. Never: anything outside it."
    sp = os.path.join(STATE_DIR, stage, "STATE.md").replace("\\", "/")
    call = (f'Agent(subagent_type="sdlc-{stage}", model="sonnet", effort="{effort}"{iso}, run_in_background={bg}, '
            f'description="sdlc-{stage} instance {n}", prompt=<the brief below>)')
    body = f"""GOVERNANCE   nj-governance-v4 · rules: nj-agent-ops/templates/worker-rules.md (read once, first)
FOCUS        only your stage. You are instance {n} of sdlc-{stage}, a rotated successor. A message not starting AMEND: is not a task (R10).
TASK         <run> · {stage}-rotation · sdlc-{stage} · PARENT lead
ROLE         {role} · sdlc-{stage}
OBJECTIVE    <Lead fills: continue exactly at the ## next step of the previous instance>
VERIFIED_FACTS
  [V] the previous instance's handoff, six headings, saved by the stop hook into main — {sp}
  [A] the previous instance stopped at a clean commit — falsified by: `sdlc.py rotate {stage}` refusing, or HEAD in the handoff not the branch tip
SCOPE        <Lead fills: task and input paths>. NOT in scope: other stages.
OWNED_PATHS  {owned_line}
VERIFIER     `<Lead fills: a command that exits 0>`
TIER         STANDARD because a rotated stage continues a design that already exists · MODEL sonnet
EFFORT       {effort} — set by the stage definition
BUDGET       tool_calls ≤ 150 (runaway cap only) · rotate at 400k context · stall: no new output for 15 min => stop, name the cause
HELPERS      3 · partition <Lead fills: paths inside OWNED_PATHS | none>
GIT          {git_line}
GATES        <Lead fills: the gate commands, run at HEAD>
ENTRY_SMOKE  <Lead fills, or none because nothing user-facing changes>
RESUME       state: work/sdlc/{stage}/STATE.md (six headings: # goals, ## current state, ## files in flight, ## changed, ## failed attempts, ## next step)
DELIVERABLES <Lead fills>
RECEIPT      RECEIPT <run>/sdlc-{stage}, then STATUS / FINDING / EVIDENCE / FILES-SYMBOLS / RISK / NEXT ACTION, ≤ 25 lines, then DETAIL
             + CHANGED / BRANCH / HEAD / GATES@HEAD / HELPERS_SPAWNED: CHANGED from `git diff --name-only <base>..<branch>` or a listing"""
    return call + "\n--- brief (fill every <...>) ---\n" + body


def cmd_rotate(a):
    s = a.stage
    if s not in STAGES:
        print("unknown stage", s, file=sys.stderr)
        return 2
    d = os.path.join(STATE_DIR, s)
    sp = os.path.join(d, "STATE.md")
    if not os.path.exists(sp):
        print(f"no {sp}; the retiring instance must write its handoff first (the v4 stop hook copies it to main)", file=sys.stderr)
        return 2
    with open(sp, encoding="utf8") as f:
        txt = f.read()
    if not getattr(a, "force", False):
        why = clean_commit_problem(s, txt)
        if why:
            print(f"rotate refused: {why} (--force to override)", file=sys.stderr)
            return 2
    arch = os.path.join(d, "archive")
    os.makedirs(arch, exist_ok=True)
    n = len(glob.glob(os.path.join(arch, "STATE-*.md"))) + 1
    dest = os.path.join(arch, f"STATE-{time.strftime('%Y%m%d-%H%M%S')}-i{n}.md")
    shutil.copy2(sp, dest)
    flag = os.path.join(STATE_DIR, f"ROTATE-{s}.flag")
    if os.path.exists(flag):
        os.remove(flag)
    print(f"archived to {dest}; STATE.md is kept as the successor's input")
    print("Spawn the fresh instance with:")
    print(brief(s, n + 1))
    return 0


def cmd_hook(a):
    """SubagentStop hook, non-blocking: writes work/sdlc/BOARD.txt and ROTATE-<stage>.flag; always exit 0."""
    try:
        payload = {}
        try:
            payload = json.load(sys.stdin)
        except ValueError:
            pass
        if not getattr(a, "project", None) and isinstance(payload, dict) and payload.get("cwd"):
            set_project(payload["cwd"])
        res = rows()
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(os.path.join(STATE_DIR, "BOARD.txt"), "w", encoding="utf8") as f:
            f.write(fmt(res) + "\n")
        for r in res:
            flag = os.path.join(STATE_DIR, f"ROTATE-{r['stage']}.flag")
            if r["flag"] == "ROTATE":
                with open(flag, "w") as f:
                    f.write(f"{r['tokens']} tokens at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            elif os.path.exists(flag):
                os.remove(flag)
        hit = [r["stage"] for r in res if r["flag"] == "ROTATE"]
        if hit:
            print("SDLC: ROTATE needed for " + ", ".join(hit))
    except Exception as e:  # a monitor must never block a stop
        print("sdlc hook error:", e, file=sys.stderr)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="sdlc.py")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project", default=argparse.SUPPRESS, help="project root (default: current directory)")
    p.add_argument("--project", default=None, help="project root (default: current directory)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status", parents=[common])
    s.add_argument("--stage")
    s.set_defaults(f=cmd_status)
    sub.add_parser("board", parents=[common]).set_defaults(f=cmd_board)
    r = sub.add_parser("rotate", parents=[common])
    r.add_argument("stage")
    r.add_argument("--force", action="store_true", help="skip the clean-commit check")
    r.set_defaults(f=cmd_rotate)
    sub.add_parser("hook", parents=[common]).set_defaults(f=cmd_hook)
    a = p.parse_args(argv)
    if getattr(a, "project", None):
        set_project(a.project)
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
