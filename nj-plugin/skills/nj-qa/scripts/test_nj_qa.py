"""Offline proof of the NJ-QA rules: python -X utf8 test_nj_qa.py"""
import datetime as dt, json, os, pathlib, subprocess, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import jira_refresh
import nj_qa
import evidence_name as en

EV = "زر-الإرسال-لا-يستجيب-طلب-تسجيل-منتج-2026-11-09-14.35.png"
EV_MISSING = "زر-الإرسال-لا-يستجيب-طلب-تسجيل-منتج-2026-11-09-14.36.png"

D = dt.date.fromisoformat
# Jordan's weekend: filed Thursday, Friday and Saturday do not count, Sunday does
assert nj_qa.working_days_between(D("2026-11-05"), D("2026-11-07")) == 0
assert nj_qa.working_days_between(D("2026-11-05"), D("2026-11-08")) == 1
assert nj_qa.working_days_between(D("2026-11-08"), D("2026-11-08")) == 0

me, other = nj_qa.ME, "Someone Else"
assert nj_qa.classify("In QA", me, D("2026-11-08"), D("2026-11-08"))["verdict"] == "too-new"
assert nj_qa.classify("In QA", me, D("2026-11-01"), D("2026-11-09"))["action"] == "reopen"
assert nj_qa.classify("In QA", other, D("2026-11-01"), D("2026-11-09"))["action"] == "comment with mentions"
assert nj_qa.classify("Dev completed", me, D("2026-11-01"), D("2026-11-09"))["action"] == "comment with mentions"
assert nj_qa.classify("To Do", me, D("2026-11-01"), D("2026-11-09"))["verdict"] == "not-delivered"
assert nj_qa.classify("In QA", me, D("2026-11-01"), D("2026-11-09"), delivered=D("2026-11-09"))["verdict"] == "too-new"
assert nj_qa.PATCH_SIGNS.search("await page.route('**/apply', r => r.fulfill({}))") and not nj_qa.PATCH_SIGNS.search("await page.goto(url)")

ok = {"routes": [{"id": "R1"}], "notes": [{"id": "N1", "route": "R1", "side": "applicant", "stage_order": 1}]}
assert nj_qa.plan_problems(ok) == []
assert nj_qa.plan_problems({"routes": [{"id": "R1"}, {"id": "R2"}], "notes": ok["notes"]})  # empty route
assert nj_qa.plan_problems({"routes": [{"id": "R1"}], "notes": ok["notes"] * 2})  # duplicate note
assert nj_qa.plan_problems({"routes": [{"id": "R1"}], "notes": [{"id": "N1", "route": "R9", "side": "applicant", "stage_order": 1}]})

with tempfile.TemporaryDirectory() as t:
    base = pathlib.Path(t)
    good = {"agent": "a", "route": "R1", "build": "v1 2026-11-09", "notes": [{"id": "N1", "verdict": "fixed", "seen": "s", "interpretation": "i", "evidence": [EV]}]}
    assert nj_qa.report_problems(good, base)  # evidence file absent
    (base / EV).write_bytes(b"x")
    assert nj_qa.report_problems(good, base) == []
    assert nj_qa.report_problems({**good, "build": ""}, base)
    assert nj_qa.report_problems({**good, "notes": [{"id": "N1", "verdict": "passed", "seen": "s", "interpretation": "i"}]}, base)
    assert nj_qa.report_problems({**good, "notes": [{"id": "N1", "verdict": "blocked", "seen": "s", "interpretation": "i"}]}, base)

    # the 2-agent limit, a no-progress block not counting, and one send-back, through the real CLI
    run = base / "run"
    def cli(*args):
        return subprocess.run([sys.executable, "-X", "utf8", str(pathlib.Path(__file__).parent / "nj_qa.py"), *args, "--run", str(run)], capture_output=True, text=True).returncode
    start = lambda name: cli("lease-start", "--agent", name, "--role", "tester", "--route", "R1", "--notes", "N1")
    # the gate: no crew before a request is proven fileable; a harvester needs no gate
    assert start("early") == 2
    assert cli("lease-start", "--agent", "early-h", "--role", "harvester") == 0 and cli("lease-end", "--agent", "early-h", "--status", "done") == 0
    assert cli("preflight", "--status", "fail", "--evidence", "refused") == 0 and start("early") == 2
    assert cli("preflight", "--status", "nonsense", "--evidence", "x") == 2 and cli("preflight", "--status", "pass") == 2
    assert cli("preflight", "--status", "pass", "--evidence", "ticket 1") == 2
    assert cli("preflight", "--status", "pass", "--evidence", "12345678901") == 0
    assert start("a1") == 0
    assert cli("lease-end", "--agent", "a1", "--status", "blocked", "--no-progress") == 2, "a reason is required"
    assert cli("lease-end", "--agent", "a1", "--status", "blocked", "--no-progress", "--reason", "OTP wait") == 0
    assert start("a2") == 0 and cli("lease-end", "--agent", "a2", "--status", "timeout") == 0
    assert start("a3") == 0 and cli("lease-end", "--agent", "a3", "--status", "timeout") == 0
    assert start("a4") == 2, "third counted agent must be refused"
    assert cli("sendback", "--agent", "a2") == 0
    assert cli("sendback", "--agent", "a2") == 2
    assert cli("lease-check") == 0
    assert start("a5") == 2 and cli("lease-left", "--agent", "a5") == 3, "refused agent holds no lease"
    assert cli("lease-start", "--agent", "a6", "--role", "tester", "--route", "R2", "--notes", "N2") == 0
    assert cli("lease-end", "--agent", "a6", "--status", "done") == 0
    assert cli("lease-end", "--agent", "a6", "--status", "timeout", "--no-progress", "--reason", "late") == 2, "no re-closing"
    assert cli("lease-end", "--agent", "a6", "--status", "timeout") == 2, "a second lease-end is refused, whatever its flags"
    assert cli("lease-end", "--agent", "never-started", "--status", "done") == 2, "no lease, no end"
    assert cli("preflight", "--status", "pass", "--evidence", "12345678902") == 2, "no preflight after crew"
    assert cli("lease-start", "--agent", "h1", "--role", "harvester") == 0
    assert cli("lease-left", "--agent", "h1") == 0
    # healing: a rule reaches the other service in the run and every later brief; a repeat is flagged; a bad call is refused
    assert cli("lesson", "--cause", "script", "--rule", "type phones into input[type=tel]") == 0
    assert cli("lesson", "--cause", "script", "--rule", "type phones into input[type=tel]") == 3
    assert cli("lesson", "--cause", "nonsense", "--rule", "x") == 2
    assert cli("lesson", "--cause", "script") == 2
    assert (base / "lessons.jsonl").exists() and (run / "lessons.jsonl").exists()
    other = base / "other"
    other.mkdir()
    assert [e["rule"] for e in nj_qa.read_lessons(other)] == ["type phones into input[type=tel]"]
    out = subprocess.run([sys.executable, "-X", "utf8", str(pathlib.Path(__file__).parent / "nj_qa.py"), "lease-start", "--run", str(other), "--agent", "z", "--role", "harvester"], capture_output=True, text=True).stdout
    assert "LESSONS: 1" in out, out
    assert nj_qa.preview_problems({"notes": [{"id": "N1", "status": "✅"}]}, base)
    (base / EV).write_bytes(b"x")
    assert nj_qa.preview_problems({"notes": [{"id": "N1", "status": "✅", "image": EV, "headline": "h", "test_action": "t", "expected": "e"}], "outside": [{"title": "x", "leader": "kept"}]}, base) == []

with tempfile.TemporaryDirectory() as t:
    base = pathlib.Path(t)
    (base / "reports" / "s").mkdir(parents=True)
    (base / "tester").mkdir()
    (base / "reports" / "s" / "report.json").write_text(json.dumps({"findings": [{}, {}, {}, {}]}), encoding="utf-8")
    (base / "tester" / "review-input.json").write_text(json.dumps({"tickets": [{"id": "T1", "summary": "a"}, {"id": "T2", "summary": "b"}, {"id": "T3", "summary": "c"}, {"id": "T4", "summary": "طلب بيانات للمطوّر"}]}, ensure_ascii=False), encoding="utf-8")
    (base / "tester" / "decisions-from-edge.json").write_text(json.dumps({"items": [{"kind": "t", "id": "T1", "decision": "approve"}, {"kind": "t", "id": "T2", "decision": "reject"}, {"kind": "t", "id": "T4", "decision": "approve"}]}), encoding="utf-8")
    assert nj_qa.findings_funnel(base) == {"found": 4, "kept": 3, "approved": 1, "rejected": 1, "questioned": 0, "undecided": 1}, nj_qa.findings_funnel(base)

snap = lambda **k: {"summary": "s", "status": "To Do", "assignee": "x", "description": "d", "comments": {}, "attachments": [], "updated": "", **k}
assert jira_refresh.diff({"A": snap()}, {"A": snap()}) == []
lines = jira_refresh.diff({"A": snap(), "B": snap()}, {"A": snap(status="In QA", comments={"9": "t"}, description="new"), "C": snap()})
assert sum(x.startswith("🆕 C") for x in lines) == 1 and any("➖ B" in x for x in lines) and any("In QA" in x for x in lines) and any("💬" in x for x in lines) and any("description" in x for x in lines)
# ---- the hub's gates (docs/ARCHITECTURE.md sections 3.2, 6, 12): review.json v1, tamper scan, budget stop, publish
def note(**k):
    return {"id": "N1", "title": "t", "stage_order": 1, "side": "applicant", "route": "R1", "headline": "h", "test_action": "a", "expected": "e",
            "current": "c", "verdict": "fixed", "evidence": [{"path": f"evidence/{EV}", "caption": "c", "kind": "shot"}], "source": "s", **k}


def review(*notes, findings=()):
    return {"v": 1, "run": "r", "service": {"key": "PROJ-1", "name_ar": "x"}, "state": "draft", "label": "phase2-uat", "build": "b",
            "notes": list(notes), "findings": list(findings), "tickets": []}


def nj(run, *args, env=None):
    r = subprocess.run([sys.executable, "-X", "utf8", str(pathlib.Path(__file__).parent / "nj_qa.py"), *args, "--run", str(run)], capture_output=True, text=True, encoding="utf-8", env={**os.environ, **(env or {})})
    return r.returncode, r.stdout


with tempfile.TemporaryDirectory() as t:
    runs = pathlib.Path(t) / "runs" / "R" / "PROJ-1"
    runs.mkdir(parents=True)
    (runs / "evidence").mkdir()
    (runs / "evidence" / EV).write_bytes(b"x")
    # a `fixed` with no evidence is refused; so is a missing file, a missing headline, and a finding with no leader decision
    assert nj_qa.review_problems(review(note(evidence=[])), runs), "fixed with 0 evidence must be refused"
    assert nj_qa.review_problems(review(note(evidence=[{"path": f"evidence/{EV_MISSING}"}])), runs)
    assert nj_qa.review_problems(review(note(headline="")), runs)
    assert nj_qa.review_problems(review(note(), findings=[{"id": "F1", "leader": {}}]), runs)
    assert nj_qa.review_problems(review(note(), findings=[{"id": "F1", "leader": {"decision": "kept"}}]), runs) == []
    assert nj_qa.review_problems(review(note(verdict="blocked", evidence=[], headline="")), runs) == [], "blocked needs no evidence"
    # criteria must agree with the verdict
    assert nj_qa.review_problems(review(note(criteria=[{"text": "c", "result": "fail"}])), runs)
    assert nj_qa.review_problems(review(note(verdict="not-fixed", criteria=[{"text": "c", "result": "pass"}])), runs)
    assert nj_qa.review_problems(review(note(verdict="not-fixed", criteria=[{"text": "c", "result": "fail"}])), runs) == []
    assert nj_qa.review_problems(review(note(tampered={"file": "x", "line": 1, "pattern": "p"})), runs), "no fixed on a tampered path"
    assert nj_qa.review_problems({"v": 2}, runs)
    # Note.block_cause: only on blocked / cannot-test, only data | system | tool
    assert nj_qa.review_problems(review(note(verdict="blocked", evidence=[], headline="", block_cause="data")), runs) == []
    assert nj_qa.review_problems(review(note(verdict="blocked", evidence=[], headline="", block_cause="weather")), runs), "unknown block_cause refused"
    assert nj_qa.review_problems(review(note(block_cause="tool")), runs), "block_cause on a fixed note refused"

    # tamper scan: a script with `fulfill` flags the notes it reached and forces cannot-test; a clean script flags nothing
    (runs / "review.json").write_text(json.dumps(review(note(id="N1"), note(id="N2", verdict="not-fixed"), note(id="N3", verdict="blocked", evidence=[]))), encoding="utf-8")
    (runs / "scripts" / "t-a").mkdir(parents=True)
    (runs / "scripts" / "t-a" / "n1-check.ts").write_text("await page.route('**/apply', r => r.fulfill({ status: 200 }));\n", encoding="utf-8")
    (runs / "scripts" / "t-a" / "n3.ts").write_text("await page.evaluate(() => { document.querySelector('input').value = 'x'; });\nawait page.goto(url);\n", encoding="utf-8")
    (runs / "scripts" / "t-a" / "n2-clean.ts").write_text("await page.goto(url);\nawait page.fill('#a', '1');\n", encoding="utf-8")
    code, out = nj(runs, "tamper-scan")
    assert code == 1 and "tamper-scan: 2 hits" in out, out
    rv = json.loads((runs / "review.json").read_text(encoding="utf-8"))
    by = {n["id"]: n for n in rv["notes"]}
    assert by["N1"]["verdict"] == "cannot-test" and by["N1"]["tester_verdict"] == "fixed" and by["N1"]["tampered"]["pattern"], by["N1"]
    assert "tampered" not in by["N2"] and by["N2"]["verdict"] == "not-fixed", "a clean script's note is untouched"
    assert by["N3"]["verdict"] == "blocked" and by["N3"]["tampered"], "a blocked note stays blocked but shows the patched path"
    ev = nj_qa.load_events(runs)
    assert [e for e in ev if e["ev"] == "tamper-scan"][-1]["hits"], "the guard event carries the hits"
    # publish: the tamper-scan result blocks nothing by itself, but review-blocked carries the problems
    pub = runs.parent / "PROJ-9"
    (pub / "evidence").mkdir(parents=True)
    (pub / "evidence" / EV).write_bytes(b"x")
    (pub / "review.json").write_text(json.dumps(review(note(evidence=[]))), encoding="utf-8")
    code, out = nj(pub, "publish", "--no-thumbs")
    assert code == 2 and "review blocked" in out and nj_qa.load_events(pub)[-1]["ev"] == "review-blocked", out
    assert nj_qa.load_events(pub)[-1]["problems"]
    (pub / "review.json").write_text(json.dumps(review(note(id="N9"))), encoding="utf-8")
    code, out = nj(pub, "publish", "--no-thumbs")
    assert code == 0 and nj_qa.load_events(pub)[-1]["ev"] == "review-ready", out
    assert [e["ev"] for e in nj_qa.load_events(pub)] == ["tamper-scan", "review-blocked", "tamper-scan", "review-ready"], "gates run in order and leave their events"

    # phase, wave-start, wall-close
    assert nj(runs, "phase", "--phase", "nonsense")[0] == 2
    assert nj(runs, "phase", "--phase", "testing")[0] == 0 and nj_qa.load_events(runs)[-1] == {**nj_qa.load_events(runs)[-1], "ev": "hub.phase", "phase": "testing"}
    assert nj(runs, "wave-start", "--n", "2")[0] == 0 and nj(runs, "wave-start", "--n", "x")[0] == 2
    assert nj(runs, "wall-close", "--wall", "t-a-1", "--outcome", "corrected")[0] == 2, "no such wall"
    (runs / "walls").mkdir()
    (runs / "walls" / "t-a-1.md").write_text("**Where:** x\n", encoding="utf-8")
    assert nj(runs, "wall-close", "--wall", "t-a-1", "--outcome", "corrected")[0] == 0
    assert nj(runs, "wall-close", "--wall", "t-a-1", "--outcome", "blocked")[0] == 2, "closed once"
    assert nj(runs, "wall-close", "--wall", "t-a-1", "--outcome", "maybe")[0] == 2

    # budget: lease-start is refused for the service once the run's tokens.json says stop; a warn does not refuse
    (runs.parent / "tokens.json").write_text(json.dumps({"services": {"PROJ-1": {"state": "warn"}}}), encoding="utf-8")
    assert nj(runs, "lease-start", "--agent", "h-1", "--role", "harvester")[0] == 0
    (runs.parent / "tokens.json").write_text(json.dumps({"services": {"PROJ-1": {"state": "stop"}}}), encoding="utf-8")
    code, out = nj(runs, "lease-start", "--agent", "h-2", "--role", "harvester")
    assert code == 2 and "STOP" in out, out
    assert nj(runs, "lease-start", "--agent", "h-2", "--role", "wizard")[0] == 2, "unknown role"
    # the leader holds a lease too, with its own length
    (runs.parent / "tokens.json").write_text("{}", encoding="utf-8")
    code, out = nj(runs, "lease-start", "--agent", "leader-PROJ-1", "--role", "leader", env={"NJQA_NOW": "2026-11-09T10:00:00"})
    assert code == 0 and "DEADLINE 2026-11-09T14:00:00" in out, out

    # preflight: a serial in the event, and non-serial text is refused
    r2 = pathlib.Path(t) / "runs" / "R" / "PROJ-2"
    assert nj(r2, "preflight", "--status", "pass", "--evidence", "the request is filed")[0] == 2
    assert nj(r2, "preflight", "--status", "pass", "--evidence", "12345678901")[0] == 0
    assert nj_qa.load_events(r2)[-1]["serial"] == "12345678901"

    # lessons: a repeat is counted in the lessons file, not duplicated as a rule
    assert nj(r2, "lesson", "--cause", "brief", "--rule", "use tel inputs")[0] == 0
    assert nj(r2, "lesson", "--cause", "brief", "--rule", "use tel inputs")[0] == 3
    assert len(nj_qa.read_lessons(r2)) == 1
    assert sum(1 for x in (r2 / "lessons.jsonl").read_text(encoding="utf-8").splitlines() if '"repeat_of"' in x) == 1

    # the funnel reads review.json and the hub's decisions file
    base = pathlib.Path(t) / "data"
    svc = base / "runs" / "R" / "PROJ-3"
    (svc / "reports" / "a").mkdir(parents=True)
    (svc / "reports" / "a" / "report.json").write_text(json.dumps({"findings": [{}, {}, {}]}), encoding="utf-8")
    rv3 = review(note())
    rv3["tickets"] = [{"id": "T1", "summary": "a"}, {"id": "T2", "summary": "b"}, {"id": "T3", "summary": "طلب بيانات"}]
    (svc / "review.json").write_text(json.dumps(rv3, ensure_ascii=False), encoding="utf-8")
    (base / "decisions" / "R").mkdir(parents=True)
    (base / "decisions" / "R" / "PROJ-3.json").write_text(json.dumps({"v": 1, "items": {"ticket:T1": {"decision": "approve"}, "ticket:T2": {"decision": "question"}}}), encoding="utf-8")
    assert nj_qa.findings_funnel(svc) == {"found": 3, "kept": 2, "approved": 1, "rejected": 0, "questioned": 1, "undecided": 0}, nj_qa.findings_funnel(svc)

    # the ledger skips partial and unknown lines (a writer may be mid-append)
    (r2 / "ledger.jsonl").write_text('{"ev": "preflight", "status": "pass", "evidence": "1"}\n{"ev": "lease-sta\nnot json\n[1]\n', encoding="utf-8")
    assert [e["ev"] for e in nj_qa.load_events(r2)] == ["preflight"]

# the engine of the old scripts still sees patched traffic in a report's folder
assert nj_qa.scan_text("await page.route('**', r => r.continue({ postData: 'x' }))") and not nj_qa.scan_text("await page.goto('/')")
assert nj_qa.scan_text("await page.evaluate(() => { el.value = 'a'; })") and not nj_qa.scan_text("await page.evaluate(() => el.value === 'a')")
print("nj-qa self-check OK")
