"""Tests for nj_guard.py, run through its real entry point (JSON on stdin, JSON decision on stdout).

    python -m unittest discover -s nj-kit/tests
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parent.parent / "bundled" / "claude-v4" / "hooks" / "nj_guard.py"


def run(payload: dict) -> dict | None:
    r = subprocess.run([sys.executable, "-I", str(GUARD)], input=json.dumps(payload),
                       capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)["hookSpecificOutput"] if r.stdout.strip() else None


def sub(tool, **ti):
    return {"agent_id": "a1", "agent_type": "sonnet-lead", "tool_name": tool, "tool_input": ti}


def helper(tool, **ti):
    return {"agent_id": "h1", "agent_type": "haiku-helper", "tool_name": tool, "tool_input": ti}


@unittest.skipUnless(GUARD.exists(), 'this kit lineage does not bundle nj_guard.py')
class GitRule(unittest.TestCase):
    def test_bash_push_denied(self):
        self.assertEqual(run(sub("Bash", command="git push origin main"))["permissionDecision"], "deny")

    def test_powershell_push_denied(self):
        # regression: the guard only looked at tool == "Bash"
        self.assertEqual(run(sub("PowerShell", command="git push origin main"))["permissionDecision"], "deny")
        self.assertEqual(run(sub("PowerShell", command="& git merge feature"))["permissionDecision"], "deny")
        self.assertEqual(run(sub("PowerShell", command="gh pr merge 12"))["permissionDecision"], "deny")

    def test_commit_allowed(self):
        self.assertIsNone(run(sub("PowerShell", command="git commit -m x")))
        self.assertIsNone(run(sub("Bash", command="git status")))

    def test_main_thread_never_blocked(self):
        self.assertIsNone(run({"tool_name": "PowerShell", "tool_input": {"command": "git push"}}))


@unittest.skipUnless(GUARD.exists(), 'this kit lineage does not bundle nj_guard.py')
class SecretRule(unittest.TestCase):
    def denied(self, tool, **ti):
        out = run(helper(tool, **ti))
        return bool(out) and out["permissionDecision"] == "deny"

    def test_house_credential_paths_denied(self):
        # regression: ~/.config/linkedin/li.env did not match
        self.assertTrue(self.denied("Read", file_path="C:\\Users\\x\\.config\\linkedin\\li.env"))
        self.assertTrue(self.denied("Read", file_path="/home/x/.config/pinterest/pinterest.env"))
        self.assertTrue(self.denied("Bash", command="cat ~/.config/linkedin/li.env"))
        self.assertTrue(self.denied("PowerShell", command="Get-Content $HOME\\.config\\linkedin\\li.env"))

    def test_old_patterns_still_denied(self):
        self.assertTrue(self.denied("Read", file_path="/repo/.env"))
        self.assertTrue(self.denied("Read", file_path="/repo/.env.local"))
        self.assertTrue(self.denied("Grep", path="/repo/credentials/", pattern="x"))
        self.assertTrue(self.denied("Read", file_path="C:/Users/x/.claude/secrets/a"))
        self.assertTrue(self.denied("Read", file_path="/home/x/.git-credentials"))
        self.assertTrue(self.denied("Read", file_path="/home/x/.ssh/id_rsa"))

    def test_normal_paths_allowed(self):
        self.assertFalse(self.denied("Read", file_path="/repo/src/environment.ts"))
        self.assertFalse(self.denied("Read", file_path="/repo/README.md"))
        self.assertFalse(self.denied("Bash", command="python -m unittest"))

    def test_only_helpers_get_the_secret_rule(self):
        self.assertIsNone(run(sub("Read", file_path="/home/x/.config/linkedin/li.env")))


@unittest.skipUnless(GUARD.exists(), 'this kit lineage does not bundle nj_guard.py')
class FailOpen(unittest.TestCase):
    def test_garbage_input_allows(self):
        r = subprocess.run([sys.executable, "-I", str(GUARD)], input="not json", capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
