"""Tests for the redaction, pinning and leak-scan helpers in scripts/export.py.

    python -m unittest discover -s nj-kit/tests
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "export.py"
spec = importlib.util.spec_from_file_location("nj_export", SCRIPT)
ex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ex)

# built at run time so this file itself holds no credential-shaped literal
FAKE_GH = "gh" + "p_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
FAKE_SK = "sk-" + "or-v1-" + "0123456789abcdef0123456789abcdef"


class Redaction(unittest.TestCase):
    def test_mcp_args_secret_flag_value(self):
        self.assertEqual(ex.redact_args(["-y", "pkg@1.0.0", "--api-key", "hunter2hunter2", "--port", "80"]),
                         ["-y", "pkg@1.0.0", "--api-key", "<redacted>", "--port", "80"])

    def test_mcp_args_equals_form_and_token(self):
        self.assertEqual(ex.redact_args(["--token=abc123456789", "--key=zzz"]),
                         ["--token=<redacted>", "--key=<redacted>"])

    def test_url_query_and_userinfo(self):
        out = ex.redact_text("https://mcp.example.com/sse?apikey=SECRETVALUE&x=1")
        self.assertNotIn("SECRETVALUE", out)
        self.assertTrue(out.startswith("https://mcp.example.com/sse?"))
        out = ex.redact_text("https://user:pa55word@host.example/path")
        self.assertNotIn("pa55word", out)

    def test_hook_command_env_and_flags(self):
        cmd = 'MY_API_TOKEN=abcdef123456 python "hook.py" --password hunter2 --mode ok'
        out = ex.redact_command(cmd)
        self.assertNotIn("abcdef123456", out)
        self.assertNotIn("hunter2", out)
        self.assertIn("--mode ok", out)
        self.assertIn('python "hook.py"', out)

    def test_key_shapes(self):
        for secret in (FAKE_GH, FAKE_SK):
            self.assertNotIn(secret, ex.redact_text(f"curl -H 'x: {secret}' https://a.b"))
        self.assertNotIn("abcdefghijklmnopqrstu", ex.redact_text("Authorization: Bea" + "rer abcdefghijklmnopqrstuvwxyz0123"))

    def test_home_directory_is_removed(self):
        home = str(Path.home())
        out = ex.redact_command(f'node "{home}\\.claude\\hooks\\a.js"')
        self.assertNotIn(home, out)
        self.assertIn("~", out)

    def test_plain_text_unchanged(self):
        s = 'bash "~/.claude/hooks/nj-kit-sync.sh"'
        self.assertEqual(ex.redact_command(s), s)


class Pinning(unittest.TestCase):
    def test_latest_becomes_exact(self):
        self.assertIn("@upstash/context7-mcp@4.4.4", ex.pin_npx_args(["-y", "@upstash/context7-mcp@latest"]))
        self.assertIn("@upstash/context7-mcp@4.4.4", ex.pin_npx_args(["-y", "@upstash/context7-mcp"]))

    def test_other_args_untouched(self):
        self.assertEqual(ex.pin_npx_args(["--browser", "chrome"]), ["--browser", "chrome"])

    def test_pins_file_covers_every_third_party_repo(self):
        kit = SCRIPT.parent.parent
        manifest = json.loads((kit / "manifest.json").read_text(encoding="utf-8"))
        pins = json.loads((kit / "pinned-sources.json").read_text(encoding="utf-8"))
        for e in manifest["skills"]["third_party"]:
            sha = pins["repos"].get(e["source"], "")
            self.assertRegex(sha, r"^[0-9a-f]{40}$", e["source"])
            self.assertEqual(e.get("ref"), sha, e["skill"])
        self.assertRegex(pins["skills_cli"], r"^skills@\d+\.\d+\.\d+$")
        for ver in pins["npm"].values():
            self.assertRegex(ver, r"^\d+\.\d+\.\d+$")

    def test_manifest_mcp_args_have_no_latest(self):
        kit = SCRIPT.parent.parent
        manifest = json.loads((kit / "manifest.json").read_text(encoding="utf-8"))
        for name, spec_ in manifest["mcp_servers"].items():
            for a in spec_.get("args", []):
                self.assertFalse(str(a).endswith("@latest"), f"{name}: {a}")


class LeakScan(unittest.TestCase):
    def test_finds_a_key_and_ignores_prose(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "ok.md").write_text("set your token and password in the env\n", encoding="utf-8")
            self.assertEqual(ex.leak_scan(root), [])
            (root / "bad.txt").write_text(f"key = {FAKE_GH}\n", encoding="utf-8")
            hits = ex.leak_scan(root)
            self.assertEqual(len(hits), 1)
            self.assertTrue(hits[0].startswith("bad.txt"))

    def test_repo_kit_is_clean(self):
        self.assertEqual(ex.leak_scan(SCRIPT.parent.parent), [])


class MemoryDefault(unittest.TestCase):
    def test_memory_not_bundled_by_default(self):
        with tempfile.TemporaryDirectory() as d:
            bundled = Path(d)
            (bundled / "memory").mkdir()
            ex.WITH_MEMORY = False
            lines = ex.bundle_memory(bundled)
            self.assertFalse((bundled / "memory").exists())
            self.assertIn("NOT bundled", lines[0])


if __name__ == "__main__":
    unittest.main()
