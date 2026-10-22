"""Offline tests for nj_rank. Mock HTTP opener, fake 7z runner. Never touches Jira or the real root.

Run: PYTHONUTF8=1 python -m unittest test_nj_rank -v   (from this folder)
"""
import io
import json
import os
import re
os.environ["NJ_RANK_NO_OPEN"] = "1"  # tests never open a browser
import shutil
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nj_rank as nr  # noqa: E402

HOST = "https://jira.example.test"
ME = "owner.test"
PASSWORD = "Hunter2-SECRET-xyz"
CFG = {"baseUrl": HOST, "user": ME, "password": PASSWORD, "projectKey": "PROJ"}


class FakeResp:
    def __init__(self, payload):
        self._b = b"" if payload is None else json.dumps(payload).encode("utf-8")

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeOpener:
    """Routes by (method, path). handler(method, path, body) -> (status, payload)."""

    def __init__(self, handler, events):
        self.handler = handler
        self.events = events

    def open(self, req, timeout=None):
        path = req.full_url[len(HOST):]
        body = req.data
        status, payload = self.handler(req.get_method(), path, body)
        self.events.append(f"{req.get_method()} {path.split('?')[0]}")
        if status >= 400:
            raise urllib.error.HTTPError(req.full_url, status, "err", {},
                                         io.BytesIO(json.dumps(payload).encode("utf-8")))
        return FakeResp(payload)


def no_sleep(_):
    return None


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="njrank-"))
        self.root = self.tmp / "root"
        self.ev_dir = self.tmp / "evidence"  # outside root, like real delivery outputs
        self.ev_dir.mkdir()
        self.events = []

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def evidence(self, name, size=100):
        p = self.ev_dir / name
        p.write_bytes(b"x" * size)
        return str(p)

    def raw(self, **over):
        d = {"project": "PROJ", "session": "backfill-2026-10-12", "title": "SRS · تسجيل منتج غذائي",
             "description": "SRS built in Arabic and English. PDF and DOCX delivered.",
             "service_ar": "تسجيل منتج غذائي", "work_type": "srs",
             "finished": "2026-10-01T14:05:00+03:00", "started": None, "time_source": "mtime",
             "evidence": [self.evidence("a.png"), self.evidence("a.md", 50)], "jira_keys": ["PROJ-1015"], "attach_evidence": True}
        d.update(over)
        return d


class TestRegister(Base):
    def test_register_dedupe_and_arabic_folder(self):
        status, rec = nr.register(self.root, self.raw())
        self.assertEqual(status, "added")
        folder = Path(rec["folder"])
        self.assertTrue((folder / "item.json").exists())
        self.assertEqual(folder.parent.name, "2026-10-01_1405")
        self.assertIn("تسجيل منتج غذائي", folder.name)
        self.assertEqual(rec["evidence_count"], 2)
        # same (project, service, work_type) with another title is still a duplicate
        status2, _ = nr.register(self.root, self.raw(title="other title"))
        self.assertEqual(status2, "duplicate")
        rows = nr.load_registry(self.root)
        self.assertEqual([r["status"] for r in rows], ["pending"])

    def test_import_counts_invalid_and_duplicate(self):
        good = json.dumps(self.raw())
        bad = json.dumps(self.raw(work_type="not-a-type", service_ar="other"))
        f = self.tmp / "in.jsonl"
        f.write_text("\n".join([good, bad, good]) + "\n", encoding="utf-8")
        counts = nr.import_jsonl(self.root, [str(f)])
        self.assertEqual(counts["added"], 1)
        self.assertEqual(counts["duplicate"], 1)
        self.assertEqual(counts["invalid"], 1)

    def test_missing_evidence_rejected(self):
        with self.assertRaises(nr.NjRankError):
            nr.register(self.root, self.raw(evidence=[str(self.ev_dir / "nope.png")]))

    def test_preview_counts(self):
        nr.register(self.root, self.raw())
        nr.register(self.root, self.raw(service_ar="خدمة ثانية", title="SRS · خدمة ثانية"))
        out = nr.write_preview(self.root)
        self.assertEqual(out["items"], 2)
        self.assertEqual(out["pending"], 2)
        text = (self.root / "preview.md").read_text(encoding="utf-8")
        self.assertIn("خدمة ثانية", text)
        self.assertEqual(text.count("| pending |"), 2)

    def test_safe_title_strips_and_trims(self):
        self.assertEqual(nr.safe_title('a<b>:c"d/e\\f|g?h*i'), "abcdefghi")
        self.assertEqual(len(nr.safe_title("ب" * 200)), 80)


class TestLongPath(unittest.TestCase):
    def test_longpath_prefixes(self):
        if sys.platform != "win32":
            self.skipTest("Windows prefix only")
        self.assertEqual(nr.longpath(r"C:\a\b"), "\\\\?\\C:\\a\\b")
        self.assertEqual(nr.longpath(r"\\srv\share\x"), "\\\\?\\UNC\\srv\\share\\x")
        self.assertEqual(nr.longpath("\\\\?\\C:\\a"), "\\\\?\\C:\\a")

    def test_longpath_is_identity_off_windows(self):
        if sys.platform == "win32":
            self.skipTest("Windows-only branch")
        self.assertEqual(nr.longpath("/a/b"), os.path.abspath("/a/b"))


class TestFiling(Base):
    def routes(self, *, readback_assignee=ME, create_status=201, attach_fail=False):
        def handler(method, path, body):
            base = path.split("?")[0]
            if (method, base) == ("GET", "/rest/api/2/myself"):
                return 200, {"name": ME}
            if (method, base) == ("GET", "/rest/api/2/attachment/meta"):
                return 200, {"uploadLimit": 10_000_000}
            if (method, base) == ("POST", "/rest/api/2/search"):
                return 200, {"issues": [], "total": 0, "startAt": 0}
            if (method, base) == ("POST", "/rest/api/2/issue"):
                if create_status != 201:
                    return create_status, {"errors": {"x": "required"}}
                return 201, {"key": "PROJ-1033"}
            if (method, base) == ("POST", "/rest/api/2/issue/PROJ-1033/attachments"):
                if attach_fail:
                    return 500, {"errorMessages": ["boom"]}
                return 200, []
            if (method, base) == ("GET", "/rest/api/2/issue/PROJ-1033/transitions"):
                return 200, {"transitions": [
                    {"id": "11", "name": "To Do", "to": {"name": "To Do", "statusCategory": {"key": "new"}}},
                    {"id": "31", "name": "Done", "to": {"name": "Done", "statusCategory": {"key": "done"}}}]}
            if (method, base) == ("POST", "/rest/api/2/issueLink"):
                return 201, None
            if (method, base) == ("POST", "/rest/api/2/issue/PROJ-1033/transitions"):
                return 204, None
            if (method, base) == ("GET", "/rest/api/2/issue/PROJ-1033"):
                return 200, {"key": "PROJ-1033", "fields": {
                    "assignee": {"name": readback_assignee}, "status": {"statusCategory": {"key": "done"}},
                    "attachment": [{"id": "1"}, {"id": "2"}]}}
            if (method, base) == ("POST", "/rest/api/2/issue/PROJ-1033/comment"):
                return 201, {}
            raise AssertionError(f"unrouted {method} {path}")
        return handler

    def jira(self, **kw):
        return nr.Jira(CFG, opener=FakeOpener(self.routes(**kw), self.events), sleep=no_sleep)

    def runner(self):
        calls = []

        def run(args):
            calls.append(args)
            self.events.append("7z " + args[1])
            if args[1] == "a":
                arc = next(a for a in args if a.endswith("evidence.7z"))
                Path(arc.replace("\\\\?\\", "")).write_bytes(b"7z")  # fake archive, never an evidence file
            return 0, "ok"
        return run, calls

    def test_file_flow_order_and_archive(self):
        _, rec = nr.register(self.root, self.raw())
        run, calls = self.runner()
        result = nr.file_items(self.root, self.jira(), run=run, sevenzip="7z")
        self.assertEqual(result, {"filed": 1})
        self.assertEqual(self.events, [
            "GET /rest/api/2/myself",
            "GET /rest/api/2/attachment/meta",
            "POST /rest/api/2/search",
            "POST /rest/api/2/issue",
            "POST /rest/api/2/issueLink",
            "POST /rest/api/2/issue/PROJ-1033/attachments",
            "POST /rest/api/2/issue/PROJ-1033/attachments",
            "GET /rest/api/2/issue/PROJ-1033/transitions",
            "POST /rest/api/2/issue/PROJ-1033/transitions",
            "GET /rest/api/2/issue/PROJ-1033",
            "7z a",
            "7z t",
        ])
        doc = nr.read_item(rec["folder"])
        self.assertEqual(doc["jira_key"], "PROJ-1033")
        self.assertTrue(doc["archive"].endswith("evidence.7z"))
        self.assertEqual(nr.load_registry(self.root)[0]["status"], "filed")
        # evidence originals outside root are untouched
        self.assertTrue(all(Path(p).exists() for p in doc["evidence"]))

    def test_readback_failure_keeps_files_and_skips_archive(self):
        _, rec = nr.register(self.root, self.raw())
        run, calls = self.runner()
        result = nr.file_items(self.root, self.jira(readback_assignee="someone.else"), run=run, sevenzip="7z")
        self.assertEqual(result, {"failed": 1})
        self.assertEqual(calls, [])
        row = nr.load_registry(self.root)[0]
        self.assertEqual(row["status"], "failed")
        self.assertIn("assignee", row["error"])
        self.assertTrue(all(Path(p).exists() for p in nr.read_item(rec["folder"])["evidence"]))

    def test_create_retries_once_with_estimate(self):
        _, _ = nr.register(self.root, self.raw())
        run, _ = self.runner()
        opener_bodies = []
        base_handler = self.routes()

        def handler(method, path, body):
            if (method, path) == ("POST", "/rest/api/2/issue"):
                opener_bodies.append(json.loads(body))
                if len(opener_bodies) == 1:
                    return 400, {"errors": {"timetracking": "required"}}
            return base_handler(method, path, body)
        j = nr.Jira(CFG, opener=FakeOpener(handler, self.events), sleep=no_sleep)
        nr.file_items(self.root, j, run=run, sevenzip="7z")
        self.assertEqual(len(opener_bodies), 2)
        self.assertNotIn("timetracking", opener_bodies[0]["fields"])
        self.assertEqual(opener_bodies[1]["fields"]["timetracking"], {"originalEstimate": "1h"})

    def test_create_assigns_api_user_and_task_type(self):
        _, _ = nr.register(self.root, self.raw())
        run, _ = self.runner()
        seen = []
        base_handler = self.routes()

        def handler(method, path, body):
            if (method, path) == ("POST", "/rest/api/2/issue"):
                seen.append(json.loads(body)["fields"])
            return base_handler(method, path, body)
        nr.file_items(self.root, nr.Jira(CFG, opener=FakeOpener(handler, self.events), sleep=no_sleep),
                      run=run, sevenzip="7z")
        self.assertEqual(seen[0]["assignee"], {"name": ME})
        self.assertEqual(seen[0]["issuetype"], {"name": "Task"})
        self.assertEqual(seen[0]["summary"], "SRS · تسجيل منتج غذائي")

    def test_dry_run_writes_nothing(self):
        nr.register(self.root, self.raw())
        run, calls = self.runner()
        result = nr.file_items(self.root, self.jira(), dry_run=True, run=run)
        self.assertEqual(result, {"would-file": 1})
        self.assertFalse(any(e.startswith("POST /rest/api/2/issue") and "search" not in e for e in self.events))
        self.assertEqual(calls, [])

    def test_password_never_in_error_output(self):
        def handler(method, path, body):
            if (method, path) == ("GET", "/rest/api/2/myself"):
                return 401, {"errorMessages": [f"bad credentials for {ME} / {PASSWORD}"]}
            raise AssertionError(path)
        j = nr.Jira(CFG, opener=FakeOpener(handler, self.events), sleep=no_sleep)
        with self.assertRaises(nr.JiraError) as cm:
            j.myself()
        self.assertNotIn(PASSWORD, str(cm.exception))
        self.assertNotIn(j._token, str(cm.exception))
        self.assertIn("***", str(cm.exception))

    def test_retry_on_429_then_success(self):
        sleeps = []
        attempts = {"n": 0}

        def handler(method, path, body):
            attempts["n"] += 1
            if attempts["n"] == 1:
                return 429, {"errorMessages": ["slow down"]}
            return 200, {"name": ME}
        j = nr.Jira(CFG, opener=FakeOpener(handler, self.events), sleep=sleeps.append)
        self.assertEqual(j.myself(), ME)
        self.assertEqual(sleeps, [1.5])

    def test_only_allowlisted_types_attach(self):
        nr.check_attachable("a.PNG"); nr.check_attachable("n.md")
        with self.assertRaises(nr.NjRankError) as cm:
            nr.check_attachable("gate.txt")
        self.assertIn("gate.txt", str(cm.exception))
        self.assertIn(".png", str(cm.exception))

    def test_pdf_allowed_docx_not(self):
        nr.check_attachable("letter.pdf")
        with self.assertRaises(nr.NjRankError):
            nr.check_attachable("letter.docx")

    def test_register_drops_disallowed_keeps_rest(self):
        nr.register(self.root, self.raw(title="Reg · y", service_ar="خدمة تسجيل",
                                        evidence=[self.evidence("g.txt"), self.evidence("o.pdf")]))
        row = nr.load_registry(self.root)[-1]
        doc = json.loads((Path(row["folder"]) / "item.json").read_text(encoding="utf-8"))
        self.assertEqual([Path(e).name for e in doc["evidence"]], ["o.pdf"])

    def test_txt_evidence_stays_local_rest_uploads(self):
        nr.register(self.root, self.raw(title="Mixed · x", service_ar="خدمة مختلطة",
                                        evidence=[self.evidence("gate.txt"), self.evidence("ok.png")]))
        attached = []
        base = self.routes()

        def handler(method, path, body):
            if path.endswith("/attachments"):
                attached.append(body)
            if (method, path) == ("GET", "/rest/api/2/issue/PROJ-1033"):
                return 200, {"key": "PROJ-1033", "fields": {"assignee": {"name": ME},
                             "status": {"statusCategory": {"key": "done"}}, "attachment": [{"id": "1"}]}}
            return base(method, path, body)
        run, _ = self.runner()
        nr.file_items(self.root, nr.Jira(CFG, opener=FakeOpener(handler, self.events), sleep=no_sleep),
                      run=run, sevenzip="7z")
        self.assertEqual(len(attached), 1)
        self.assertNotIn(b"gate.txt", attached[0])

    def test_oversize_evidence_listed_in_comment_not_attached(self):
        big = self.evidence("big.mp4", size=2000)
        nr.register(self.root, self.raw(title="Video · x", service_ar="خدمة كبيرة",
                                        evidence=[big, self.evidence("small.png")]))
        base = self.routes()
        comments, attached = [], []

        def handler(method, path, body):
            if path.endswith("/attachment/meta"):
                return 200, {"uploadLimit": 1000}
            if path.endswith("/comment"):
                comments.append(json.loads(body)["body"])
            if path.endswith("/attachments"):
                attached.append(path)
            if (method, path) == ("GET", "/rest/api/2/issue/PROJ-1033"):
                return 200, {"key": "PROJ-1033", "fields": {"assignee": {"name": ME},
                             "status": {"statusCategory": {"key": "done"}}, "attachment": [{"id": "1"}]}}
            return base(method, path, body)
        run, _ = self.runner()
        nr.file_items(self.root, nr.Jira(CFG, opener=FakeOpener(handler, self.events), sleep=no_sleep),
                      run=run, sevenzip="7z")
        self.assertEqual(len(attached), 1)
        self.assertTrue(any("big.mp4" in c for c in comments))


class TestCloseMine(Base):
    def handler_factory(self, record):
        issues = [
            {"key": "PROJ-1001", "fields": {"summary": "task mine", "issuetype": {"name": "Task"},
                                         "status": {"name": "To Do"}, "reporter": {"name": ME},
                                         "assignee": None}},
            {"key": "PROJ-1002", "fields": {"summary": "a bug", "issuetype": {"name": "Bug"},
                                         "status": {"name": "To Do"}, "reporter": {"name": ME},
                                         "assignee": None}},
        ]

        def handler(method, path, body):
            base = path.split("?")[0]
            if (method, base) == ("POST", "/rest/api/2/search"):
                q = json.loads(body)["jql"]
                record["jql"] = q
                return 200, {"issues": issues, "total": 2, "startAt": 0}
            if (method, base) == ("GET", "/rest/api/2/issue/PROJ-1001/transitions"):
                return 200, {"transitions": [{"id": "31", "name": "Done",
                                              "to": {"name": "Done", "statusCategory": {"key": "done"}}}]}
            if (method, base) == ("POST", "/rest/api/2/issue/PROJ-1001/transitions"):
                record["transitions"] = record.get("transitions", 0) + 1
                return 204, None
            if (method, base) == ("GET", "/rest/api/2/issue/PROJ-1001"):
                return 200, {"key": "PROJ-1001", "fields": {"status": {"statusCategory": {"key": "done"}}}}
            raise AssertionError(f"unrouted {method} {path}")
        return handler

    def test_dry_run_counts_tasks_only_and_writes_nothing(self):
        record = {}
        j = nr.Jira(CFG, opener=FakeOpener(self.handler_factory(record), self.events), sleep=no_sleep)
        result = nr.close_mine(self.root, j, apply=False)
        self.assertEqual(result, {"open_tasks": 1, "skipped_non_task": 1, "skipped_protected": 0, "would_close": 1})
        self.assertNotIn("transitions", record)
        self.assertIn("currentUser()", record["jql"])
        self.assertIn("issuetype = Task", record["jql"])
        self.assertTrue((self.root / "close-mine-preview.md").exists())

    def test_apply_transitions_only_tasks(self):
        record = {}
        j = nr.Jira(CFG, opener=FakeOpener(self.handler_factory(record), self.events), sleep=no_sleep)
        result = nr.close_mine(self.root, j, apply=True)
        self.assertEqual(result["closed"], 1)
        self.assertEqual(record["transitions"], 1)


class TestCloseMineGuards(Base):
    """Wrap-up Tasks (label untestable/wrapup) and trace keys must never be closed by close-mine."""

    def issues(self):
        def mk(key, labels):
            return {"key": key, "fields": {"summary": "t " + key, "issuetype": {"name": "Task"},
                                           "status": {"name": "To Do"}, "reporter": {"name": ME},
                                           "assignee": None, "labels": labels}}
        return [mk("PROJ-1001", []), mk("PROJ-1002", ["untestable"]), mk("PROJ-1003", ["WrapUp"]),
                mk("PROJ-1004", ["other"]), mk("PROJ-1005", [])]

    def jira(self, record):
        issues = self.issues()

        def handler(method, path, body):
            base = path.split("?")[0]
            if (method, base) == ("POST", "/rest/api/2/search"):
                record["fields"] = json.loads(body)["fields"]
                return 200, {"issues": issues, "total": len(issues), "startAt": 0}
            m = re.match(r"/rest/api/2/issue/(PROJ-\d)(/transitions)?$", base)
            if m and method == "GET" and m.group(2):
                return 200, {"transitions": [{"id": "31", "name": "Done",
                                              "to": {"name": "Done", "statusCategory": {"key": "done"}}}]}
            if m and method == "POST" and m.group(2):
                record.setdefault("closed", []).append(m.group(1))
                return 204, None
            if m and method == "GET":
                return 200, {"key": m.group(1), "fields": {"status": {"statusCategory": {"key": "done"}}}}
            raise AssertionError(f"unrouted {method} {path}")
        return nr.Jira(CFG, opener=FakeOpener(handler, self.events), sleep=no_sleep)

    def test_apply_skips_labels_and_protected_keys(self):
        record = {}
        out = nr.close_mine(self.root, self.jira(record), apply=True, protect={"PROJ-1005"})
        self.assertEqual(record["closed"], ["PROJ-1001", "PROJ-1004"])
        self.assertIn("labels", record["fields"])
        self.assertEqual((out["closed"], out["skipped_protected"]), (2, 3))

    def test_dry_run_lists_skips_with_reason(self):
        record = {}
        out = nr.close_mine(self.root, self.jira(record), apply=False, protect={"PROJ-1005"})
        self.assertEqual(out["would_close"], 2)
        self.assertNotIn("closed", record)
        md = (self.root / "close-mine-preview.md").read_text(encoding="utf-8")
        self.assertIn("label untestable", md)
        self.assertIn("label wrapup", md)
        self.assertIn("protected (session trace)", md)

    def test_load_protect_from_trace_file_env_and_list(self):
        trace = self.tmp / "trace.json"
        trace.write_text(json.dumps({"filed": [{"key": "PROJ-1006"}], "x": "see PROJ-1007"}), encoding="utf-8")
        self.assertEqual(nr.load_protect(str(trace)), {"PROJ-1006", "PROJ-1007"})
        self.assertEqual(nr.load_protect("PROJ-1001, PROJ-1002"), {"PROJ-1001", "PROJ-1002"})
        self.assertEqual(nr.load_protect(None), set())

    def test_cli_env_protect_reaches_close_mine(self):
        record = {}
        rc = nr.main(["close-mine", "--apply"], root=self.root, opener=FakeOpener(
            self.jira(record).opener.handler, self.events),
            env={"JIRA_BASE_URL": HOST, "JIRA_USER": ME, "JIRA_PASS": PASSWORD,
                 "NJ_RANK_PROTECT": "PROJ-1001 PROJ-1005"})
        self.assertEqual(rc, 0)
        self.assertEqual(record["closed"], ["PROJ-1004"])

    def test_registry_tasks_are_protected(self):
        """verify-v2 fix 5: Tasks nj-rank itself filed (registry jira_key) survive close-mine even without a trace."""
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "registry.jsonl").write_text(json.dumps({"id": "x", "n": 1, "jira_key": "PROJ-1001", "status": "filed"}) + chr(10), encoding="utf-8")
        record = {}
        out = nr.close_mine(self.root, self.jira(record), apply=True, protect={"PROJ-1005"})
        self.assertEqual(record["closed"], ["PROJ-1004"])
        self.assertIn("protected (nj-rank registry)", (self.root / "close-mine-preview.md").read_text(encoding="utf-8"))

    def test_cli_apply_needs_protect_and_none_is_dry_run(self):
        record = {}
        env = {"JIRA_BASE_URL": HOST, "JIRA_USER": ME, "JIRA_PASS": PASSWORD}
        op = lambda: FakeOpener(self.jira(record).opener.handler, self.events)
        self.assertEqual(nr.main(["close-mine", "--apply"], root=self.root, opener=op(), env=env), 2)
        self.assertNotIn("closed", record)
        self.assertEqual(nr.main(["close-mine", "--apply", "--protect", "none"], root=self.root, opener=op(), env=env), 0)
        self.assertNotIn("closed", record)  # none = dry run, nothing transitioned


class TestLink(TestFiling):
    def routes(self, **kw):
        base = super().routes(**kw)
        self.links = []

        def handler(method, path, body):
            if (method, path) == ("POST", "/rest/api/2/issueLink"):
                self.links.append(json.loads(body))
                return 201, None
            return base(method, path, body)
        return handler

    def test_link_posts_relates(self):
        self.jira().link("PROJ-1033", "PROJ-1015")
        self.assertEqual(self.links, [{"type": {"name": "Relates"},
                                       "inwardIssue": {"key": "PROJ-1033"}, "outwardIssue": {"key": "PROJ-1015"}}])

    def test_file_link_to_links_each_filed_task(self):
        nr.register(self.root, self.raw())
        run, _ = self.runner()
        result = nr.file_items(self.root, self.jira(), run=run, sevenzip="7z", link_to="PROJ-1015")
        self.assertEqual(result, {"filed": 1})
        self.assertEqual(self.links[0]["inwardIssue"]["key"], "PROJ-1033")
        self.assertEqual(self.links[0]["outwardIssue"]["key"], "PROJ-1015")

    def test_non_PROJ_item_is_skipped_without_jira_task(self):
        nr.register(self.root, dict(self.raw(), project="ENSERA"))
        run, _ = self.runner()
        result = nr.file_items(self.root, self.jira(), run=run, sevenzip="7z")
        self.assertEqual(result, {"skipped-non-PROJ": 1})
        self.assertFalse(any(e.startswith("POST /rest/api/2/issue") for e in self.events))

    def test_dry_run_never_links(self):
        nr.register(self.root, self.raw())
        nr.file_items(self.root, self.jira(), dry_run=True, link_to="PROJ-1015")
        self.assertEqual(self.links, [])

    def test_segment_dedupe_with_null_service_falls_back_to_title(self):
        a = nr.register(self.root, self.raw(service_ar=None, work_type="segment", title="Segment · A"))[0]
        b = nr.register(self.root, self.raw(service_ar=None, work_type="segment", title="Segment · B"))[0]
        c = nr.register(self.root, self.raw(service_ar=None, work_type="segment", title="Segment · A"))[0]
        self.assertEqual((a, b, c), ("added", "added", "duplicate"))


class TestConfigAndCli(Base):
    def test_env_beats_secrets_file(self):
        secrets = self.tmp / "jira.json"
        secrets.write_text(json.dumps({"jira": {"baseUrl": "https://file.test", "user": "f",
                                                "password": "fp", "projectKey": "PROJ"}}), encoding="utf-8")
        env = {"JIRA_BASE_URL": "https://env.test/", "JIRA_USER": "e", "JIRA_PASS": "ep"}
        cfg = nr.load_config(env, secrets_path=secrets)
        self.assertEqual(cfg["baseUrl"], "https://env.test")
        self.assertEqual(cfg["user"], "e")
        cfg2 = nr.load_config({"NJ_RANK_SECRETS": str(secrets)}, secrets_path=self.tmp / "none.json")
        self.assertEqual(cfg2["user"], "f")

    def test_cli_register_and_preview(self):
        rc = nr.main(["register", "--project", "PROJ", "--session", "s1", "--title", "Jira filing · x",
                      "--description", "d", "--work-type", "jira-filing", "--finished", "2026-10-02T09:00:00",
                      "--evidence", self.evidence("n.png")], root=self.root)
        self.assertEqual(rc, 0)
        rc = nr.main(["preview"], root=self.root)
        self.assertEqual(rc, 0)
        self.assertTrue((self.root / "preview.md").exists())


class TestRefuseVerdictSource(unittest.TestCase):
    def test_gate(self):
        import nj_rank
        with self.assertRaises(nj_rank.NjRankError):
            nj_rank.refuse_verdict_source("*Verdict:* x")
        with self.assertRaises(nj_rank.NjRankError):
            nj_rank.refuse_verdict_source("*Source:* [JIRA] K-1")
        nj_rank.refuse_verdict_source("h3. Where")


if __name__ == "__main__":
    unittest.main()
