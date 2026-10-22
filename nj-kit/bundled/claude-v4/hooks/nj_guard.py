"""NJ governance v4 PreToolUse guard. Stdlib, fail-open (own errors -> allow).
Rule 1: a subagent (input has agent_id, or agent_type in sonnet-lead/haiku-helper) may not run git push / git merge / gh pr merge.
Rule 2: haiku-helper may not Read/Grep/Glob/Bash-touch secrets paths.
The main thread (no agent_id/agent_type) is never blocked: Lead merges.
"""
import json, re, sys

HELPERS = {"sonnet-lead", "haiku-helper"}
GIT = re.compile(r"(?:^|[;&|(`\s])git\s+(?:-[^\s]+(?:\s+[^\s-][^\s]*)?\s+)*(push|merge)\b|\bgh\s+pr\s+merge\b", re.I)
SECRET = re.compile(
    r"(\.claude/secrets|/secrets/|credentials\.json|settings\.local\.json|jira\.local\.json|"
    r"(?:^|/)\.env(?:\.|\b)|test data .*\.html|accounts-[a-z]+|\bjira\.json\b|(?:^|/)credentials/)", re.I)


def deny(reason):
    json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                      "permissionDecisionReason": reason}}, sys.stdout)


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
    d = json.load(sys.stdin)
    _dbg(d)
    atype, aid = d.get("agent_type"), d.get("agent_id")
    if not (atype or aid):
        return  # main thread = Lead
    tool, ti = d.get("tool_name", ""), d.get("tool_input") or {}
    cmd = ti.get("command") or ""
    if tool == "Bash" and GIT.search(cmd):
        return deny("NJ v4: workers commit only; git push/merge belong to the Lead.")
    if atype == "haiku-helper":
        blob = " ".join(str(ti.get(k, "")) for k in ("file_path", "path", "pattern", "command", "glob"))
        if SECRET.search(blob.replace("\\", "/")):
            deny("NJ v4: haiku-helper may not touch credential/secret paths; ask your Sonnet lead.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"nj_guard: {e}\n")
    sys.exit(0)
