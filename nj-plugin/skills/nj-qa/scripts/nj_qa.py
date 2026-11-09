"""NJ-QA run state: the rules a model must not be trusted to count. Stdlib only.

usage: python -X utf8 nj_qa.py <cmd> --run SERVICE_RUN_DIR [...]
  plan-check                  every note in exactly one route, one tester per route; writes plan.md
  preflight --status pass|form-only|fail --evidence TEXT
                              records whether a real request could be filed; testers and scavengers need pass or form-only
                              (pass needs the filed request's 11-digit serial as the evidence)
  lease-start --agent A --role leader|tester|harvester|scavenger [--route R] [--notes N1,N2]
                              refuses a third agent on a note (exit 2) and any new agent once the service's budget is at stop; prints the deadline
  lease-end --agent A --status done|timeout|blocked [--no-progress --reason TEXT]
                              --no-progress = stopped by an outside block; does not use up the note's limit.
                              A lease ends once: a second lease-end for it is refused.
  lease-left --agent A        minutes left; prints REPORT-NOW and exits 3 with 3 minutes or less to go
  lease-check                 lists expired leases; exit 1 if any
  sendback --agent A          allows one correction per report; exit 2 on the second
  report-check FILE           validates an agent report before the leader reads it
  classify --status S --reporter R --created YYYY-MM-DD [--today YYYY-MM-DD]
                              verdict and proposed Jira action for a note that still fails
  lesson --cause script|data|route|timing|tooling|brief|requirement --rule "..." [--evidence PATH]
                              records a healing rule for this service and the whole run; a repeat of a rule is flagged
  lessons                     prints every rule the next agent must follow (lease-start prints them too)
  preview-check               review.json (v1): every verdict has evidence, headline, test action and expected result; criteria agree with the verdict
  tamper-scan                 scripts that alter staging traffic: marks the notes they reached `tampered` and cannot-test
  publish                     tamper-scan, preview-check, thumbs, then review-ready or review-blocked (the hub shows either)
  phase --phase P             hub: the service's phase (intake|planning|preflight|testing|reviewing|paused|complete|partial)
  wave-start --n N            hub: a leader's spawn round begins
  wall-close --wall ID --outcome corrected|blocked|system-defect
  findings                    the findings funnel: outside the notes, found, kept by the leader, approved by the owner
  status                      live leases
"""
import argparse, datetime as dt, json, os, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
LEASE_MIN = 30
LEADER_LEASE_MIN = 240
REPORT_AT_MIN = 3
MAX_AGENTS_PER_NOTE = 2
MAX_SENDBACKS = 1
BUDGET_K, STOP_K = 2500, 3000  # fresh tokens per service, in thousands
VERDICTS = {"fixed", "not-fixed", "too-new", "not-delivered", "blocked", "dropped", "no-system-change", "cannot-test"}
NOT_DELIVERED = {"to do", "open", "in progress", "backlog", "reopened", "re opened"}
PHASES = {"intake", "planning", "preflight", "testing", "reviewing", "paused", "complete", "partial"}
WALL_OUTCOMES = {"corrected", "blocked", "system-defect"}
CRITERION_RESULTS = {"pass", "fail", "blocked", "n/a"}
FINDING_DECISIONS = {"kept", "merged", "dropped"}
ROLES = {"leader", "tester", "harvester", "scavenger"}
CAUSES = {"script", "data", "route", "timing", "tooling", "brief", "requirement"}
PATCH_SIGNS = re.compile(
    r"\.route\(|\.fulfill\(|route\.continue\([^)]*(postData|headers)|continue\(\s*\{[^}]*postData|"
    r"Fetch\.(enable|fulfillRequest|continueRequest)|page\.unroute|setExtraHTTPHeaders")
EVAL_VALUE = re.compile(r"\.value\s*=(?!=)")  # `.value =` inside an evaluate(...) writes a field the way no user does
SERIAL = re.compile(r"^\d{11}$")
SERIAL_IN = re.compile(r"(?<!\d)\d{11}(?!\d)")
NEEDS_EVIDENCE = {"fixed", "not-fixed", "too-new"}
ME = "Nader Alzghoul"
WEEKEND = {4, 5}  # Friday, Saturday in Jordan (Monday = 0)
SCRIPT_EXT = {".ts", ".mjs", ".js"}


def now():
    fixed = os.environ.get("NJQA_NOW")  # tests pin the clock
    return dt.datetime.fromisoformat(fixed) if fixed else dt.datetime.now().replace(microsecond=0)


def read_json(p, default=None):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


# ---------------------------------------------------------------- lessons
def lesson_files(run):
    """This service, then the whole run, so the other service learns too."""
    return [run / "lessons.jsonl", run.parent / "lessons.jsonl"]


def read_lessons(run):
    seen, out = set(), []
    for f in lesson_files(run):
        for line in (f.read_text(encoding="utf-8").splitlines() if f.exists() else []):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if "rule" not in e or e.get("repeat_of") or e["rule"] in seen:
                continue
            seen.add(e["rule"])
            out.append(e)
    return out


# ---------------------------------------------------------------- ledger
def load_events(run):
    """Unknown or partial lines are skipped: a writer may be mid-append."""
    f = run / "ledger.jsonl"
    out = []
    for x in (f.read_text(encoding="utf-8").splitlines() if f.exists() else []):
        try:
            e = json.loads(x)
        except ValueError:
            continue
        if isinstance(e, dict) and "ev" in e:
            out.append(e)
    return out


def log(run, **e):
    e["at"] = now().isoformat()
    line = (json.dumps(e, ensure_ascii=False) + "\n").encode("utf-8")
    fd = os.open(str(run / "ledger.jsonl"), os.O_WRONLY | os.O_APPEND | os.O_CREAT)  # one write of one whole line
    try:
        os.write(fd, line)
    finally:
        os.close(fd)


def live_leases(events):
    open_ = {}
    for e in events:
        if e["ev"] == "lease-start":
            open_[e["agent"]] = e
        elif e["ev"] == "lease-end":
            open_.pop(e["agent"], None)
    return open_


def agents_used(events, note):
    """Agents that count against a note's limit: an outside block with no progress does not count."""
    free = {e["agent"] for e in events if e["ev"] == "lease-end" and e.get("no_progress")}
    return [e["agent"] for e in events if e["ev"] == "lease-start" and e.get("role") == "tester" and note in e.get("notes", []) and e["agent"] not in free]


def budget_state(run):
    """The service's budget state from <RUN>/tokens.json (written by tokens.py --json): ok | warn | stop, or None when unmeasured."""
    t = read_json(run.parent / "tokens.json", {}) or {}
    return ((t.get("services") or {}).get(run.name) or {}).get("state")


# ---------------------------------------------------------------- Jira verdict
def working_days_between(created, today):
    """Working days after the filing day, up to and including today."""
    n, d = 0, created
    while d < today:
        d += dt.timedelta(days=1)
        if d.weekday() not in WEEKEND:
            n += 1
    return n


def classify(status, reporter, created, today, delivered=None):
    """A note still failing on staging. `delivered` = when the developer handed it over (Dev completed / In QA), from the changelog.
    the owner decides whether the proposed action is carried out."""
    if status.strip().lower() in NOT_DELIVERED:
        return {"verdict": "not-delivered", "action": "none yet: the developer hasn't delivered it", "why": f"status {status}"}
    if working_days_between(delivered or created, today) < 1:
        return {"verdict": "too-new", "action": "retest after one working day", "why": "delivered less than one working day ago"}
    if status.strip().lower() == "in qa" and reporter == ME:
        return {"verdict": "not-fixed", "action": "reopen", "why": "In QA and reported by the owner"}
    return {"verdict": "not-fixed", "action": "comment with mentions", "why": "not In QA, or reported by someone else"}


# ---------------------------------------------------------------- plan
def plan_problems(plan):
    """plan = {notes:[{id,stage_order,side,route}], routes:[{id,tester?,ticket_end?}]}"""
    bad, routes = [], {r["id"] for r in plan.get("routes", [])}
    ids = [n["id"] for n in plan.get("notes", [])]
    for i in sorted({x for x in ids if ids.count(x) > 1}):
        bad.append(f"note {i} appears twice")
    for n in plan.get("notes", []):
        if n.get("route") not in routes:
            bad.append(f"note {n['id']} has no valid route ({n.get('route')})")
        if n.get("side") not in ("applicant", "backoffice"):
            bad.append(f"note {n['id']} needs side applicant|backoffice")
        if not isinstance(n.get("stage_order"), int):
            bad.append(f"note {n['id']} needs an integer stage_order")
    used = {n.get("route") for n in plan.get("notes", [])}
    for r in sorted(routes - used):
        bad.append(f"route {r} has no notes")
    return bad


# ---------------------------------------------------------------- tamper scan
def script_files(run):
    """Every script an agent wrote: <S>/scripts/** and the .ts files beside reports under <S>/reports/**."""
    out = []
    for base in (run / "scripts", run / "reports"):
        if base.exists():
            out += [f for f in sorted(base.rglob("*")) if f.is_file() and f.suffix in SCRIPT_EXT]
    return out


def scan_text(text):
    """-> [(line, pattern)] for one script's text."""
    hits = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        m = PATCH_SIGNS.search(line)
        if m:
            hits.append((i, m.group(0).strip()[:40]))
    for m in re.finditer(r"evaluate\w*\(", text):  # a `.value =` within the next 400 characters of an evaluate call
        window = text[m.end(): m.end() + 400]
        v = EVAL_VALUE.search(window)
        if v:
            hits.append((text.count("\n", 0, m.end() + v.start()) + 1, ".value = (in evaluate)"))
    return sorted(set(hits))


def patched(scripts_dir):
    """Scripts that alter staging traffic. Anything reached that way can't support a verdict."""
    hits = []
    d = pathlib.Path(scripts_dir)
    for f in sorted(d.rglob("*")) if d.exists() else []:
        if f.is_file() and f.suffix in SCRIPT_EXT:
            for line, _ in scan_text(f.read_text(encoding="utf-8", errors="ignore")):
                hits.append(f"{f.name}:{line}")
    return hits


def note_ids_hit(file, text, note_ids):
    """Which notes does this script belong to: its name or its text names the note (N3 -> n3b.ts, s3.ts; PROJ-5497 -> 5497)."""
    stem = file.stem.lower()
    found = set()
    for nid in note_ids:
        low = nid.lower()
        num = re.search(r"(\d+)$", low)
        digits = num.group(1) if num else ""
        if re.match(r"^n\d+$", low):
            if re.match(rf"^[ns]{digits}(?!\d)", stem) or re.search(rf"(?<![\w-]){low}(?!\d)", text.lower()):
                found.add(nid)
        elif low in stem or low in text.lower() or (digits and len(digits) >= 4 and digits in stem):
            found.add(nid)
    return found


def tamper_scan(run):
    """-> hits [{file, line, pattern, agent, notes[]}]. Marks the notes in review.json `tampered`; a verdict that rested on a
    patched path (fixed, not-fixed, too-new) becomes cannot-test and the tester's verdict is kept in tester_verdict."""
    rp = run / "review.json"
    rv = read_json(rp, None)
    events = load_events(run)
    leases = {}
    for e in events:
        if e["ev"] == "lease-start":
            leases.setdefault(e["agent"], set()).update(e.get("notes", []))
    note_ids = [n["id"] for n in (rv or {}).get("notes", [])]
    hits = []
    for f in script_files(run):
        text = f.read_text(encoding="utf-8", errors="ignore")
        found = scan_text(text)
        if not found:
            continue
        rel = f.relative_to(run)
        agent = rel.parts[1] if len(rel.parts) > 2 else ""
        hit_notes = note_ids_hit(f, text, note_ids)
        if not hit_notes:  # unlabeled script: every note its agent held
            hit_notes = {n for n in leases.get(agent, set()) if n in note_ids}
        for line, pattern in found:
            hits.append({"file": rel.as_posix(), "line": line, "pattern": pattern, "agent": agent, "notes": sorted(hit_notes)})
    if rv:
        changed = False
        first = {}
        for h in hits:
            for nid in h["notes"]:
                first.setdefault(nid, h)
        for n in rv.get("notes", []):
            h = first.get(n["id"])
            if h and not n.get("tampered"):
                n["tampered"] = {"file": h["file"], "line": h["line"], "pattern": h["pattern"]}
                if n.get("verdict") in NEEDS_EVIDENCE:
                    n.setdefault("tester_verdict", n["verdict"])
                    n["verdict"] = "cannot-test"
                changed = True
        if changed:
            rp.write_text(json.dumps(rv, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    log(run, ev="tamper-scan", hits=[{k: v for k, v in h.items() if k != "notes"} for h in hits])
    return hits


# ---------------------------------------------------------------- reports
def report_problems(rep, base):
    bad = []
    run = base.parent.parent if base.parent.name == "reports" else base
    hits = patched(run / "scripts" / rep.get("agent", "")) + patched(base)
    if hits and any(n.get("verdict") in ("fixed", "not-fixed") for n in rep.get("notes", [])):
        bad.append(f"scripts alter staging traffic ({', '.join(hits[:3])}): verdicts reached that way must be cannot-test")
    for field in ("agent", "route", "notes"):
        if field not in rep:
            bad.append(f"missing {field}")
    if rep.get("notes") and not rep.get("build"):
        bad.append("missing build: the model version and update date from the bottom of the screen")
    for n in rep.get("notes", []):
        i = n.get("id", "?")
        if n.get("verdict") not in VERDICTS:
            bad.append(f"{i}: verdict {n.get('verdict')} not allowed")
        if not (n.get("seen") or "").strip():
            bad.append(f"{i}: says nothing about what was seen on screen")
        if not (n.get("interpretation") or "").strip():
            bad.append(f"{i}: no interpretation")
        ev = n.get("evidence") or []
        if n.get("verdict") in NEEDS_EVIDENCE and not ev:
            bad.append(f"{i}: {n.get('verdict')} without evidence")
        for p in ev:
            if not (base / p).exists():
                bad.append(f"{i}: evidence file missing: {p}")
        if n.get("verdict") == "blocked" and not (n.get("blocked_reason") or "").strip():
            bad.append(f"{i}: blocked without the exact reason")
    return bad


# ---------------------------------------------------------------- review.json
def review_problems(rv, run):
    """Contract v1 (docs/ARCHITECTURE.md 3.3, 3.4, 6). Every problem is a line the hub shows."""
    bad = []
    if not isinstance(rv, dict) or rv.get("v") != 1:
        return ["review.json: v must be 1"]
    if rv.get("state") not in ("draft", "filed"):
        bad.append("review.json: state must be draft|filed")
    for n in rv.get("notes", []):
        i = n.get("id", "?")
        v = n.get("verdict")
        if v not in VERDICTS:
            bad.append(f"{i}: verdict {v} not allowed")
            continue
        if v in NEEDS_EVIDENCE:
            ev = n.get("evidence") or []
            if not ev:
                bad.append(f"{i}: {v} with no evidence")
            for e in ev:
                if not (run / e.get("path", "")).is_file():
                    bad.append(f"{i}: evidence file missing: {e.get('path')}")
            for f in ("headline", "test_action", "expected"):
                if not (n.get(f) or "").strip():
                    bad.append(f"{i}: missing {f}")
        crit = n.get("criteria") or []
        for c in crit:
            if c.get("result") not in CRITERION_RESULTS:
                bad.append(f"{i}: criterion result {c.get('result')} not allowed")
        results = [c.get("result") for c in crit]
        if v == "fixed" and any(r in ("fail", "blocked") for r in results):
            bad.append(f"{i}: fixed, but a criterion is {'fail' if 'fail' in results else 'blocked'}")
        if v == "not-fixed" and crit and "fail" not in results:
            bad.append(f"{i}: not-fixed, but no criterion fails")
        if n.get("tampered") and v == "fixed":
            bad.append(f"{i}: fixed on a path a tampered script touched ({n['tampered'].get('file')}:{n['tampered'].get('line')})")
    for f in rv.get("findings", []):
        if (f.get("leader") or {}).get("decision") not in FINDING_DECISIONS:
            bad.append(f"finding {f.get('id', '?')}: no leader decision")
    return bad


def review_of(run):
    return read_json(run / "review.json", None)


def preview_problems(inp, tester_dir):
    """The old review-input.json, kept so a run from before the hub still checks."""
    bad = []
    for n in inp.get("notes", []):
        i = n.get("id", "?")
        if n.get("status") in ("✅", "❌"):
            shots = ([n["image"]] if n.get("image") else []) + list(n.get("images") or [])
            if not shots:
                bad.append(f"{i}: a verdict with no screenshot")
            for s in shots:
                if not (tester_dir / s).exists():
                    bad.append(f"{i}: screenshot missing: {s}")
            for f in ("headline", "test_action", "expected"):
                if not (n.get(f) or "").strip():
                    bad.append(f"{i}: missing {f}")
    for o in inp.get("outside", []):
        if not (o.get("leader") or "").strip():
            bad.append(f"finding «{o.get('title', '?')}»: no leader decision")
    return bad


def run_thumbs(run):
    """480 px WebP thumbs for every evidence picture. Pillow comes from uv, or from the interpreter if it is already there."""
    script = str(HERE / "thumbs.py")
    for cmd in (["uv", "run", "--quiet", "--with", "pillow", "python", "-X", "utf8", script, "--run", str(run)],
                [sys.executable, "-X", "utf8", script, "--run", str(run)]):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        except OSError:
            continue
        if r.returncode == 0:
            return True, r.stdout.strip()
    return False, "thumbs.py failed (needs pillow: uv run --with pillow)"


def publish(run, thumbs=True):
    """-> (ok, problems). Appends review-ready or review-blocked; never a half-ready review."""
    rp = run / "review.json"
    if not rp.exists():
        log(run, ev="review-blocked", problems=["review.json is missing"])
        return False, ["review.json is missing"]
    tamper_scan(run)
    problems = review_problems(read_json(rp, None), run)
    if problems:
        log(run, ev="review-blocked", problems=problems)
        return False, problems
    if thumbs:
        ok, msg = run_thumbs(run)
        if not ok:
            problems = [msg]
            log(run, ev="review-blocked", problems=problems)
            return False, problems
    log(run, ev="review-ready", notes=len(read_json(rp, {}).get("notes", [])))
    return True, []


# ---------------------------------------------------------------- findings
def decision_items(run):
    """{ 'ticket:T1': 'approve', ... } from the hub's decisions file; the old Edge export is the fallback."""
    f = run.parent.parent.parent / "decisions" / run.parent.name / f"{run.name}.json"
    d = read_json(f, None)
    if d:
        return {k: v.get("decision") for k, v in (d.get("items") or {}).items()}
    old = read_json(run / "tester" / "decisions-from-edge.json", {}) or {}
    return {("ticket:" if x.get("kind") in ("t", "ticket") else "note:") + x["id"]: x.get("decision") for x in old.get("items", [])}


def findings_funnel(base):
    """Defects found outside the notes: what agents reported, what the leader kept as Bug drafts, what the owner decided. Data requests are not defects."""
    found = 0
    for f in sorted((base / "reports").glob("*/report.json")):
        found += len((read_json(f, {}) or {}).get("findings") or [])
    src = review_of(base) or read_json(base / "tester" / "review-input.json", {}) or {}
    tickets = src.get("tickets", [])
    kept = {t["id"] for t in tickets if not (t.get("summary") or t.get("defect") or "").startswith("طلب بيانات")}
    dec = decision_items(base)
    tk = {i: dec.get(f"ticket:{i}") for i in kept}
    approved = sum(v in ("approve", "edit") for v in tk.values())
    rejected = sum(v == "reject" for v in tk.values())
    questioned = sum(v == "question" for v in tk.values())
    return {"found": found, "kept": len(kept), "approved": approved, "rejected": rejected, "questioned": questioned,
            "undecided": len(kept) - approved - rejected - questioned}


# ---------------------------------------------------------------- cli
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("file", nargs="?")
    ap.add_argument("--run")
    ap.add_argument("--agent")
    ap.add_argument("--role")
    ap.add_argument("--route")
    ap.add_argument("--notes", default="")
    ap.add_argument("--status")
    ap.add_argument("--no-progress", action="store_true")
    ap.add_argument("--reporter")
    ap.add_argument("--created")
    ap.add_argument("--today")
    ap.add_argument("--delivered")
    ap.add_argument("--reason")
    ap.add_argument("--cause")
    ap.add_argument("--rule")
    ap.add_argument("--evidence")
    ap.add_argument("--phase")
    ap.add_argument("--n")
    ap.add_argument("--wall")
    ap.add_argument("--outcome")
    ap.add_argument("--no-thumbs", action="store_true")
    a = ap.parse_args()

    if a.cmd == "classify":
        today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
        print(json.dumps(classify(a.status, a.reporter, dt.date.fromisoformat(a.created), today, dt.date.fromisoformat(a.delivered) if a.delivered else None), ensure_ascii=False))
        return 0

    if a.cmd == "report-check":
        f = pathlib.Path(a.file)
        bad = report_problems(json.loads(f.read_text(encoding="utf-8")), f.parent)
        for b in bad:
            print("REFUSED:", b)
        if not bad:
            print("report OK")
        return 2 if bad else 0

    if not a.run:
        print(__doc__)
        return 2
    run = pathlib.Path(a.run).resolve()  # `--run .` must still reach the run-level lessons file
    run.mkdir(parents=True, exist_ok=True)
    events = load_events(run)

    if a.cmd == "preflight":
        if a.status not in ("pass", "form-only", "fail") or not (a.evidence or "").strip():
            print("REFUSED: needs --status pass|form-only|fail and --evidence")
            return 2
        if a.status == "pass" and not SERIAL.match(a.evidence.strip()):
            print("REFUSED: pass needs the filed request's 11-digit serial as --evidence")
            return 2
        if any(e["ev"] == "lease-start" and e.get("role") in ("tester", "scavenger") for e in events):
            print("REFUSED: crew already started; a preflight recorded afterwards proves nothing")
            return 2
        m = SERIAL_IN.search(a.evidence)
        log(run, ev="preflight", status=a.status, evidence=a.evidence, serial=m.group(0) if m else None)
        print("ok")
        return 0

    if a.cmd == "lesson":
        if a.cause not in CAUSES or not (a.rule or "").strip():
            print(f"REFUSED: needs --rule and --cause one of {sorted(CAUSES)}")
            return 2
        if any(e["rule"] == a.rule for e in read_lessons(run)):
            line = json.dumps({"repeat_of": True, "rule": a.rule, "service": run.name, "at": now().isoformat()}, ensure_ascii=False) + "\n"
            with (run / "lessons.jsonl").open("a", encoding="utf-8") as h:
                h.write(line)
            print("REPEAT: this rule is already recorded and the mistake came back; change how it is enforced (fix the shared code), not just the brief")
            return 3
        line = json.dumps({"rule": a.rule, "cause": a.cause, "evidence": a.evidence, "service": run.name, "at": now().isoformat()}, ensure_ascii=False) + "\n"
        for f in lesson_files(run):
            with f.open("a", encoding="utf-8") as h:
                h.write(line)
        print("ok")
        return 0

    if a.cmd == "lessons":
        for e in read_lessons(run):
            print(f"- [{e['cause']}] {e['rule']}")
        return 0

    if a.cmd == "plan-check":
        plan = json.loads((run / "plan.json").read_text(encoding="utf-8"))
        bad = plan_problems(plan)
        for b in bad:
            print("REFUSED:", b)
        if bad:
            return 2
        md = ["# Route plan", ""]
        for r in plan["routes"]:
            md += [f"## {r['id']}: {r.get('title', '')}"]
            md += [f"- {n['stage_order']:>3} · {n['side']} · {n['id']}: {n.get('title', '')}" for n in sorted((x for x in plan["notes"] if x["route"] == r["id"]), key=lambda x: x["stage_order"])]
            md.append("")
        (run / "plan.md").write_text("\n".join(md), encoding="utf-8")
        print(f"plan OK: {len(plan['notes'])} notes, {len(plan['routes'])} routes")
        return 0

    if a.cmd == "lease-start":
        notes = [x for x in a.notes.split(",") if x]
        if a.role not in ROLES:
            print(f"REFUSED: --role must be one of {sorted(ROLES)}")
            return 2
        if budget_state(run) == "stop":
            print(f"REFUSED: STOP: the service has reached its token stop ({STOP_K // 1000}.0M). No new agents; finish what is in flight and report.")
            return 2
        if a.role in ("tester", "scavenger"):
            gate = [e for e in events if e["ev"] == "preflight"]
            if not gate or gate[-1]["status"] == "fail":
                print("REFUSED: no passing preflight. File one real request first (`preflight`); on fail, write needs-nader and stop, no crew.")
                return 2
        if a.role == "tester":
            over = {n: agents_used(events, n) for n in notes if len(agents_used(events, n)) >= MAX_AGENTS_PER_NOTE}
            if over:
                print("REFUSED: limit of 2 agents reached; mark these notes blocked:", json.dumps(over, ensure_ascii=False))
                return 2
        deadline = now() + dt.timedelta(minutes=LEADER_LEASE_MIN if a.role == "leader" else LEASE_MIN)
        log(run, ev="lease-start", agent=a.agent, role=a.role, route=a.route, notes=notes, deadline=deadline.isoformat())
        print(f"DEADLINE {deadline.isoformat()}")
        rules = read_lessons(run)
        if rules:
            print(f"LESSONS: {len(rules)} recorded. The brief points the agent at {run / 'lessons.jsonl'} and references/lessons.md; paste only the ones that touch its route.")
        return 0

    if a.cmd == "lease-end":
        if a.agent not in live_leases(events):
            print(f"REFUSED: {a.agent} holds no live lease (it already ended, or never started); a lease ends once")
            return 2
        if a.no_progress:
            if not (a.reason or "").strip():
                print("REFUSED: --no-progress needs --reason naming the outside block (OTP wait, staging down, our tooling)")
                return 2
            start = next((e for e in reversed(events) if e["ev"] == "lease-start" and e["agent"] == a.agent), {})
            freed = {x["agent"] for x in events if x["ev"] == "lease-end" and x.get("no_progress")}
            for n in start.get("notes", []):
                if any(e["ev"] == "lease-start" and n in e.get("notes", []) and e["agent"] in freed for e in events):
                    print(f"REFUSED: note {n} already had one agent freed as no-progress; this one counts")
                    return 2
        log(run, ev="lease-end", agent=a.agent, status=a.status, no_progress=a.no_progress, reason=a.reason)
        print("ok")
        return 0

    if a.cmd == "lease-check":
        late = [e for e in live_leases(events).values() if dt.datetime.fromisoformat(e["deadline"]) <= now()]
        for e in late:
            print(f"EXPIRED {e['agent']} route={e.get('route')} notes={','.join(e.get('notes', []))}")
        return 1 if late else 0

    if a.cmd == "lease-left":
        lease = live_leases(events).get(a.agent)
        if not lease:
            print(f"REPORT-NOW: no live lease for {a.agent}")
            return 3
        left = (dt.datetime.fromisoformat(lease["deadline"]) - now()).total_seconds() / 60
        if left <= REPORT_AT_MIN:
            print(f"REPORT-NOW: {left:.0f} minutes left")
            return 3
        print(f"{left:.0f} minutes left")
        return 0

    if a.cmd == "sendback":
        used = sum(1 for e in events if e["ev"] == "sendback" and e["agent"] == a.agent)
        if used >= MAX_SENDBACKS:
            print(f"REFUSED: {a.agent} was already sent back once; the leader decides now and flags the note")
            return 2
        log(run, ev="sendback", agent=a.agent)
        print("ok")
        return 0

    if a.cmd == "preview-check":
        rv = review_of(run)
        if rv is not None:
            bad = review_problems(rv, run)
        else:
            legacy = read_json(run / "tester" / "review-input.json", None)
            if legacy is None:
                print("REFUSED: no review.json")
                return 2
            bad = preview_problems(legacy, run / "tester")
        for b in bad:
            print("REFUSED:", b)
        print("preview OK" if not bad else f"{len(bad)} problems")
        return 2 if bad else 0

    if a.cmd == "tamper-scan":
        hits = tamper_scan(run)
        for h in hits:
            print(f"HIT {h['file']}:{h['line']} {h['pattern']} -> {','.join(h['notes']) or 'no note'}")
        print(f"tamper-scan: {len(hits)} hits")
        return 1 if hits else 0

    if a.cmd == "publish":
        ok, problems = publish(run, thumbs=not a.no_thumbs)
        for b in problems:
            print("REFUSED:", b)
        print("review ready" if ok else f"review blocked: {len(problems)} problems")
        return 0 if ok else 2

    if a.cmd == "phase":
        if a.phase not in PHASES:
            print(f"REFUSED: --phase must be one of {sorted(PHASES)}")
            return 2
        log(run, ev="hub.phase", phase=a.phase)
        print("ok")
        return 0

    if a.cmd == "wave-start":
        if not (a.n or "").isdigit():
            print("REFUSED: --n must be a number")
            return 2
        log(run, ev="wave-start", n=int(a.n))
        print("ok")
        return 0

    if a.cmd == "wall-close":
        if a.outcome not in WALL_OUTCOMES or not a.wall:
            print(f"REFUSED: needs --wall and --outcome one of {sorted(WALL_OUTCOMES)}")
            return 2
        if not (run / "walls" / f"{a.wall}.md").is_file():
            print(f"REFUSED: no wall walls/{a.wall}.md")
            return 2
        if any(e["ev"] == "wall-close" and e.get("wall") == a.wall for e in events):
            print(f"REFUSED: wall {a.wall} is already closed")
            return 2
        log(run, ev="wall-close", wall=a.wall, outcome=a.outcome)
        print("ok")
        return 0

    if a.cmd == "findings":
        print(json.dumps(findings_funnel(run), ensure_ascii=False))
        return 0

    if a.cmd == "status":
        live = live_leases(events)
        print("live:", ", ".join(f"{k} until {v['deadline'][11:16]}" for k, v in live.items()) or "none")
        return 0

    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
