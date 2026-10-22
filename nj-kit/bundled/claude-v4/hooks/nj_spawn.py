"""NJ governance v4 spawn log. Stdlib, fail-open (always exit 0).
Modes (argv[1]):
  pre-agent : PreToolUse on the Agent tool. Records WHO is spawning (caller agent_type/id, or 'lead') in a pending queue.
  start     : SubagentStart. Pops the matching pending entry (same session + child type) and appends
              {ts, parent, child_type, model, depth, session, agent_id} to ~/.claude/logs/spawn-log.jsonl
              and, if cwd (or an ancestor) has .agent-ops, to <project>/.agent-ops/spawns.jsonl.
Hook input has NO parent/depth field (SubagentStart: session_id, agent_id, agent_type, cwd, transcript_path);
parent comes from the PreToolUse(Agent) caller fields, matched FIFO by child type (ambiguous only if two parents
spawn the same type in the same instant).
"""
import json, os, sys, time, re
from pathlib import Path

HOME = Path.home() / ".claude"
LOGS = HOME / "logs"
PENDING = LOGS / "pending-spawns.jsonl"
MODELS = {"sonnet-lead": "sonnet", "haiku-helper": "haiku"}
TTL = 600


def who(d):
    t, i = d.get("agent_type"), d.get("agent_id")
    return f"{t}:{i}" if (t or i) else "lead"


def agent_model(child, given):
    if given:
        return given
    f = HOME / "agents" / f"{child}.md"
    try:
        m = re.search(r"^model:\s*(\S+)", f.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1)
    except Exception:
        pass
    return MODELS.get(child, "inherit")


def read_pending():
    out = []
    try:
        for ln in PENDING.read_text(encoding="utf-8").splitlines():
            e = json.loads(ln)
            if time.time() - e["t"] < TTL:
                out.append(e)
    except Exception:
        pass
    return out


def write_pending(items):
    LOGS.mkdir(parents=True, exist_ok=True)
    PENDING.write_text("".join(json.dumps(e) + "\n" for e in items), encoding="utf-8")


def project_ops(cwd):
    p = Path(cwd or ".").resolve()
    for q in [p, *p.parents]:
        if (q / ".agent-ops").is_dir():
            return q / ".agent-ops"
        if q == q.parent:
            break
    return None


def _dbg(d):
    """Raw-input probe: only while the file ~/.claude/logs/DEBUG exists."""
    try:
        from pathlib import Path
        L = Path.home() / ".claude" / "logs"
        if (L / "DEBUG").exists():
            with open(L / "hook-debug.jsonl", "a", encoding="utf-8") as f:
                f.write(json.dumps({"hook": Path(__file__).name, "keys": sorted(d), "agent_id": d.get("agent_id"), "agent_type": d.get("agent_type"), "tool": d.get("tool_name")}) + chr(10))
    except Exception:
        pass


def main():
    mode = sys.argv[1]
    d = json.load(sys.stdin)
    _dbg(d)
    if mode == "pre-agent":
        ti = d.get("tool_input") or {}
        items = read_pending()
        items.append({"t": time.time(), "session": d.get("session_id"), "parent": who(d),
                      "child": ti.get("subagent_type") or "general-purpose", "model": ti.get("model")})
        write_pending(items)
        return
    items = read_pending()
    child = d.get("agent_type") or "unknown"
    hit = next((e for e in items if e.get("session") == d.get("session_id") and e["child"] == child), None)
    if hit:
        items.remove(hit)
        write_pending(items)
    parent = hit["parent"] if hit else "unknown"
    depth = 1 if parent == "lead" else (2 if parent != "unknown" else None)
    row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "parent": parent, "child_type": child,
           "model": agent_model(child, hit and hit.get("model")), "depth": depth,
           "session": d.get("session_id"), "agent_id": d.get("agent_id")}
    line = json.dumps(row, ensure_ascii=False) + "\n"
    LOGS.mkdir(parents=True, exist_ok=True)
    with open(LOGS / "spawn-log.jsonl", "a", encoding="utf-8") as f:
        f.write(line)
    ops = project_ops(d.get("cwd"))
    if ops:
        with open(ops / "spawns.jsonl", "a", encoding="utf-8") as f:
            f.write(line)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # fail-open: never block the Lead
        try:
            sys.stderr.write(f"nj_spawn: {e}\n")
        except Exception:
            pass
    sys.exit(0)
