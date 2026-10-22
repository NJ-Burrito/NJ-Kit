#!/usr/bin/env python3
"""tests/test_v3.py -- plain-assert suite for relay.py v3 + check_governance.py v3.

Run: PYTHONUTF8=1 uv run --no-project python tests/test_v3.py
Stdlib only. No pytest. Every non-trivial rejection branch gets its own test,
asserting both the exit code and that nothing was written on rejection.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELAY = ROOT / "nj-agent-ops" / "scripts" / "relay.py"
CHECK = ROOT / "nj-delegate" / "scripts" / "check_governance.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

PASSED = 0
FAILED = 0
FAIL_MSGS = []


def check(name, cond, detail=""):
    global PASSED, FAILED
    if cond:
        PASSED += 1
    else:
        FAILED += 1
        FAIL_MSGS.append(f"{name}: {detail}")


def run(*args, cwd=None):
    env = dict(os.environ, PYTHONUTF8="1")
    p = subprocess.run([sys.executable, *[str(a) for a in args]],
                        capture_output=True, text=True, encoding="utf-8",
                        env=env, cwd=cwd)
    return p.returncode, p.stdout, p.stderr


def tmp_project():
    d = Path(tempfile.mkdtemp(prefix="njv3_"))
    return d


# ------------------------------------------------------- relay ledger -----

LEDGER_OK = ["--agent", "a1", "--stage", "s1", "--status", "ok",
             "--runtime", "sonnet"]


def ledger_call(project, run_id, extra):
    return run(RELAY, "ledger", project, run_id, *LEDGER_OK, *extra)


def ledger_row_count(project, run_id):
    p = Path(project) / ".agent-ops" / "ledger.md"
    if not p.exists():
        return 0
    lines = p.read_text(encoding="utf-8").splitlines()
    return sum(1 for ln in lines if ln.startswith("| ") and run_id in ln)


def test_ledger_accepts_clean_row():
    proj = tmp_project()
    rc, out, err = ledger_call(proj, "run1", [])
    check("ledger clean row accepted", rc == 0 and "ledger ok" in out, out + err)
    check("ledger clean row written", ledger_row_count(proj, "run1") == 1)
    shutil.rmtree(proj, ignore_errors=True)


def test_ledger_rejects_bad_tier():
    proj = tmp_project()
    rc, out, err = ledger_call(proj, "run1", ["--tier", "GOLD"])
    check("bad tier rejected: exit 1", rc == 1, out + err)
    check("bad tier rejected: message", "ledger REJECTED: tier=GOLD" in out, out)
    check("bad tier rejected: nothing written", ledger_row_count(proj, "run1") == 0)
    shutil.rmtree(proj, ignore_errors=True)


def test_ledger_rejects_empty_status():
    proj = tmp_project()
    rc, out, err = run(RELAY, "ledger", proj, "run1", "--agent", "a1",
                        "--stage", "s1", "--status", "", "--runtime", "sonnet")
    check("empty status rejected: exit 1", rc == 1, out + err)
    check("empty status rejected: message", "exec-status=" in out, out)
    check("empty status rejected: nothing written", ledger_row_count(proj, "run1") == 0)
    shutil.rmtree(proj, ignore_errors=True)


def test_ledger_rejects_bad_status():
    proj = tmp_project()
    rc, out, err = ledger_call(proj, "run1", ["--status", "done"])
    # NB status also feeds --status of the base call; override via full custom call
    rc, out, err = run(RELAY, "ledger", proj, "run1", "--agent", "a1",
                        "--stage", "s1", "--status", "done", "--runtime", "sonnet")
    check("bad status rejected: exit 1", rc == 1, out + err)
    check("bad status rejected: nothing written", ledger_row_count(proj, "run1") == 0)
    shutil.rmtree(proj, ignore_errors=True)


def test_ledger_rejects_non_integer_numeric_field():
    proj = tmp_project()
    rc, out, err = ledger_call(proj, "run1", ["--tool-calls", "many"])
    check("non-integer tool-calls rejected: exit 1", rc == 1, out + err)
    check("non-integer tool-calls rejected: message",
          "tool-calls=many" in out and "not an integer" in out, out)
    check("non-integer tool-calls rejected: nothing written",
          ledger_row_count(proj, "run1") == 0)
    shutil.rmtree(proj, ignore_errors=True)


def test_ledger_rejects_not_measured_in_numeric_field():
    proj = tmp_project()
    rc, out, err = ledger_call(proj, "run1", ["--tool-calls", "NOT_MEASURED"])
    check("NOT_MEASURED in numeric field rejected: exit 1", rc == 1, out + err)
    check("NOT_MEASURED in numeric field rejected: nothing written",
          ledger_row_count(proj, "run1") == 0)
    shutil.rmtree(proj, ignore_errors=True)


def test_ledger_accepts_not_measured_in_note():
    proj = tmp_project()
    rc, out, err = ledger_call(proj, "run1", ["--note", "NOT_MEASURED"])
    check("NOT_MEASURED in note (non-numeric) accepted", rc == 0, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_ledger_rejects_cost_without_basis():
    proj = tmp_project()
    rc, out, err = ledger_call(proj, "run1", ["--cost", "1.50"])
    check("cost without basis rejected: exit 1", rc == 1, out + err)
    check("cost without basis rejected: message", "--basis" in out, out)
    check("cost without basis rejected: nothing written",
          ledger_row_count(proj, "run1") == 0)
    shutil.rmtree(proj, ignore_errors=True)


def test_ledger_accepts_cost_with_basis():
    proj = tmp_project()
    rc, out, err = ledger_call(proj, "run1", ["--cost", "1.50", "--basis", "actual"])
    check("cost with basis accepted", rc == 0, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_ledger_rejects_bad_rework_on_non_ok():
    proj = tmp_project()
    rc, out, err = run(RELAY, "ledger", proj, "run1", "--agent", "a1",
                        "--stage", "s1", "--status", "failed",
                        "--runtime", "sonnet", "--rework", "maybe")
    check("bad rework on failed status rejected: exit 1", rc == 1, out + err)
    check("bad rework on failed status rejected: nothing written",
          ledger_row_count(proj, "run1") == 0)
    shutil.rmtree(proj, ignore_errors=True)


def test_ledger_rejects_missing_rework_on_failed():
    proj = tmp_project()
    rc, out, err = run(RELAY, "ledger", proj, "run1", "--agent", "a1",
                        "--stage", "s1", "--status", "partial",
                        "--runtime", "sonnet")
    check("missing rework on partial status rejected: exit 1", rc == 1, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_ledger_ok_status_allows_blank_rework():
    proj = tmp_project()
    rc, out, err = ledger_call(proj, "run1", [])  # status ok, no --rework
    check("blank rework on ok status accepted", rc == 0, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_ledger_rejects_missing_runtime():
    proj = tmp_project()
    rc, out, err = run(RELAY, "ledger", proj, "run1", "--agent", "a1",
                        "--stage", "s1", "--status", "ok")
    check("missing runtime rejected: exit 1", rc == 1, out + err)
    check("missing runtime rejected: nothing written", ledger_row_count(proj, "run1") == 0)
    shutil.rmtree(proj, ignore_errors=True)


# ------------------------------------------------------------ claim -------

def test_claim_first_writer_ok():
    proj = tmp_project()
    rc, out, err = run(RELAY, "claim", proj, "run1", "--agent", "A",
                        "--paths", str(proj / "nj-agent-ops" / "scripts"))
    check("first claim ok", rc == 0 and "claim ok" in out, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_claim_exact_overlap_rejected():
    proj = tmp_project()
    p = str(proj / "nj-agent-ops" / "scripts")
    run(RELAY, "claim", proj, "run1", "--agent", "A", "--paths", p)
    rc, out, err = run(RELAY, "claim", proj, "run1", "--agent", "B", "--paths", p)
    check("exact-path claim overlap rejected", rc == 1 and "REJECTED" in out, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_claim_prefix_overlap_rejected():
    proj = tmp_project()
    parent = str(proj / "nj-delegate")
    child = str(proj / "nj-delegate" / "scripts")
    run(RELAY, "claim", proj, "run1", "--agent", "A", "--paths", parent)
    rc, out, err = run(RELAY, "claim", proj, "run1", "--agent", "B", "--paths", child)
    check("prefix claim overlap rejected", rc == 1, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_claim_separator_and_case_variant_overlap_rejected():
    proj = tmp_project()
    a = str(proj / "nj-agent-ops" / "scripts")
    b = str(proj / "NJ-AGENT-OPS").replace("\\", "/") + "/Scripts"
    run(RELAY, "claim", proj, "run1", "--agent", "A", "--paths", a)
    rc, out, err = run(RELAY, "claim", proj, "run1", "--agent", "B", "--paths", b)
    check("separator+case variant overlap rejected", rc == 1, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_claim_disjoint_paths_both_succeed():
    proj = tmp_project()
    a = str(proj / "nj-agent-ops" / "scripts")
    b = str(proj / "nj-delegate" / "scripts")
    run(RELAY, "claim", proj, "run1", "--agent", "A", "--paths", a)
    rc, out, err = run(RELAY, "claim", proj, "run1", "--agent", "B", "--paths", b)
    check("disjoint claims both succeed", rc == 0, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_claim_same_agent_no_self_conflict():
    proj = tmp_project()
    a = str(proj / "nj-agent-ops" / "scripts")
    run(RELAY, "claim", proj, "run1", "--agent", "A", "--paths", a)
    rc, out, err = run(RELAY, "claim", proj, "run1", "--agent", "A", "--paths", a)
    check("same agent re-claiming its own path does not conflict", rc == 0, out + err)
    shutil.rmtree(proj, ignore_errors=True)


# ----------------------------------------------------------- verify -------

def test_verify_clean_fixture_passes():
    proj = tmp_project()
    (proj / ".agent-ops").mkdir(parents=True)
    shutil.copy(FIXTURES / "ledger_clean.md", proj / ".agent-ops" / "ledger.md")
    rc, out, err = run(RELAY, "verify", proj)
    check("verify: clean fixture exits 0", rc == 0, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_verify_dirty_fixture_fails():
    proj = tmp_project()
    (proj / ".agent-ops").mkdir(parents=True)
    shutil.copy(FIXTURES / "ledger_dirty.md", proj / ".agent-ops" / "ledger.md")
    rc, out, err = run(RELAY, "verify", proj)
    check("verify: dirty fixture (PROJ ledger sample) exits non-zero", rc == 1, out + err)
    check("verify: dirty fixture flags legacy column-count rows",
          "column-count" in out, out)
    check("verify: dirty fixture flags bad tier (task-class value in tier column)",
          "tier=economy" in out, out)
    shutil.rmtree(proj, ignore_errors=True)


def test_verify_wake_ratio_computed_and_breach_flagged():
    proj = tmp_project()
    (proj / ".agent-ops").mkdir(parents=True)
    shutil.copy(FIXTURES / "ledger_clean.md", proj / ".agent-ops" / "ledger.md")
    run(RELAY, "batch", proj, "t1", "--lead-wakeups", "5", "--worker-count", "2")
    rc, out, err = run(RELAY, "verify", proj)
    check("wake-ratio computed as 2.50 and breaches >1.5", "2.50" in out and "BREACH" in out,
          out + err)
    check("wake-ratio breach makes verify exit non-zero", rc == 1, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_verify_wake_ratio_not_visible_when_missing_input():
    proj = tmp_project()
    (proj / ".agent-ops").mkdir(parents=True)
    shutil.copy(FIXTURES / "ledger_clean.md", proj / ".agent-ops" / "ledger.md")
    run(RELAY, "batch", proj, "t1", "--lead-wakeups", "1")  # no worker-count
    rc, out, err = run(RELAY, "verify", proj)
    check("wake-ratio NOT_VISIBLE surfaces when an input is missing",
          "NOT_VISIBLE" in out, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_batch_wake_ratio_cell_not_visible_in_file():
    proj = tmp_project()
    run(RELAY, "batch", proj, "t1", "--lead-wakeups", "1")
    rows = (Path(proj) / ".agent-ops" / "batches.md").read_text(encoding="utf-8").splitlines()
    check("batches.md row written", any("t1" in r for r in rows))
    shutil.rmtree(proj, ignore_errors=True)


def test_batch_wake_ratio_cell_computed_in_file():
    proj = tmp_project()
    run(RELAY, "batch", proj, "t1", "--lead-wakeups", "3", "--worker-count", "2")
    text = (Path(proj) / ".agent-ops" / "batches.md").read_text(encoding="utf-8")
    check("batches.md row contains computed wake-ratio 1.50", "1.50" in text, text)
    shutil.rmtree(proj, ignore_errors=True)


# ---------------------------------------------------- check_governance ----

GOOD_BRIEF = """some preamble text

```
GOVERNANCE   v3 · rules: r.md (read once, first)
FOCUS        your only deliverable is the test file
TASK         t1 · class · worker A of 2
OBJECTIVE    do the thing
VERIFIED_FACTS
  [V] fact one — cited.py:12
  [A] inference one — falsified by: a failing test
SCOPE        in. NOT in scope: out.
OWNED_PATHS  you may write ONLY: {paths}. Never: elsewhere.
PARALLEL     with: none — serial because sole writer
VERIFIER     tests/test_v3.py
TIER         STANDARD because implementation to spec
EFFORT       high
BUDGET       uncached in <= 100k
STALL_BOUND  15 min
GATES        tests/test_v3.py green
ENTRY_SMOKE  none — no signature, message shape or entry path changes
RESUME       detail file: progress.md
DELIVERABLES tests/test_v3.py
RECEIPT      STATUS / FINDING / EVIDENCE / FILES-SYMBOLS / RISK / NEXT ACTION
             + CHANGED: from git status
```
"""


def write_brief(path, paths="nj-plugin-v3\\\\tests\\\\"):
    p_ = Path(path); p_.parent.mkdir(parents=True, exist_ok=True)
    (p_.parent / "cited.py").write_text("# cited by the fixture brief", encoding="utf-8")
    Path(path).write_text(GOOD_BRIEF.format(paths=paths), encoding="utf-8")


def test_brief_clean_passes():
    d = tmp_project()
    f = d / "A.md"
    write_brief(f)
    rc, out, err = run(CHECK, "--brief", f)
    check("clean brief passes check_governance --brief", rc == 0, out + err)
    shutil.rmtree(d, ignore_errors=True)


def test_brief_missing_field_rejected():
    d = tmp_project()
    f = d / "A.md"
    text = GOOD_BRIEF.format(paths="x").replace("OBJECTIVE    do the thing\n", "")
    f.write_text(text, encoding="utf-8")
    (f.parent / "cited.py").write_text("# cited", encoding="utf-8")
    rc, out, err = run(CHECK, "--brief", f)
    check("brief missing OBJECTIVE rejected", rc == 1 and "OBJECTIVE" in out, out + err)
    shutil.rmtree(d, ignore_errors=True)


def test_brief_2026_09_29_fields_required():
    """FOCUS, ENTRY_SMOKE, RESUME and the receipt's CHANGED line (UI round 2 lessons)."""
    cases = {
        "FOCUS": ("FOCUS        your only deliverable is the test file\n", ""),
        "ENTRY_SMOKE": ("ENTRY_SMOKE  none — no signature, message shape or entry path changes\n", ""),
        "RESUME": ("RESUME       detail file: progress.md\n", ""),
        "RECEIPT": ("             + CHANGED: from git status\n", ""),
    }
    for field, (old, new) in cases.items():
        d = tmp_project()
        f = d / "A.md"
        f.write_text(GOOD_BRIEF.format(paths="x").replace(old, new), encoding="utf-8")
        (f.parent / "cited.py").write_text("# cited", encoding="utf-8")
        rc, out, err = run(CHECK, "--brief", f)
        check(f"brief without {field} line rejected", rc == 1 and field in out, out + err)
        shutil.rmtree(d, ignore_errors=True)


def test_brief_ungraded_fact_rejected():
    d = tmp_project()
    f = d / "A.md"
    text = GOOD_BRIEF.format(paths="x").replace("[V] fact one", "[X] fact one")
    f.write_text(text, encoding="utf-8")
    (f.parent / "cited.py").write_text("# cited", encoding="utf-8")
    rc, out, err = run(CHECK, "--brief", f)
    check("brief ungraded VERIFIED_FACTS line rejected", rc == 1, out + err)
    shutil.rmtree(d, ignore_errors=True)


def test_brief_v_without_citation_rejected():
    d = tmp_project()
    f = d / "A.md"
    text = GOOD_BRIEF.format(paths="x").replace(" — cited.py:12", "")
    f.write_text(text, encoding="utf-8")
    (f.parent / "cited.py").write_text("# cited", encoding="utf-8")
    rc, out, err = run(CHECK, "--brief", f)
    check("brief [V] without citation rejected", rc == 1 and "VERIFIED_FACTS[V]" in out,
          out + err)
    shutil.rmtree(d, ignore_errors=True)


def test_brief_a_without_falsified_by_rejected():
    d = tmp_project()
    f = d / "A.md"
    text = GOOD_BRIEF.format(paths="x").replace(" — falsified by: a failing test", "")
    f.write_text(text, encoding="utf-8")
    (f.parent / "cited.py").write_text("# cited", encoding="utf-8")
    rc, out, err = run(CHECK, "--brief", f)
    check("brief [A] without 'falsified by' rejected", rc == 1 and "VERIFIED_FACTS[A]" in out,
          out + err)
    shutil.rmtree(d, ignore_errors=True)


def test_brief_bad_verifier_rejected():
    d = tmp_project()
    f = d / "A.md"
    text = GOOD_BRIEF.format(paths="x").replace("VERIFIER     tests/test_v3.py",
                                                  "VERIFIER     none")
    f.write_text(text, encoding="utf-8")
    (f.parent / "cited.py").write_text("# cited", encoding="utf-8")
    rc, out, err = run(CHECK, "--brief", f)
    check("brief bare 'none' VERIFIER rejected", rc == 1 and "VERIFIER" in out, out + err)
    shutil.rmtree(d, ignore_errors=True)


def test_brief_verifier_none_because_accepted():
    d = tmp_project()
    f = d / "A.md"
    text = GOOD_BRIEF.format(paths="x").replace(
        "VERIFIER     tests/test_v3.py",
        "VERIFIER     none because purely mechanical rename")
    f.write_text(text, encoding="utf-8")
    (f.parent / "cited.py").write_text("# cited", encoding="utf-8")
    rc, out, err = run(CHECK, "--brief", f)
    check("brief 'none because <reason>' VERIFIER accepted", rc == 0, out + err)
    shutil.rmtree(d, ignore_errors=True)


def test_brief_over_25_lines_rejected():
    d = tmp_project()
    f = d / "A.md"
    text = GOOD_BRIEF.format(paths="x").replace(
        "GATES        tests/test_v3.py green\n",
        "GATES        tests/test_v3.py green\n" + "EXTRA        line\n" * 15)
    f.write_text(text, encoding="utf-8")
    (f.parent / "cited.py").write_text("# cited", encoding="utf-8")
    rc, out, err = run(CHECK, "--brief", f)
    check("brief over 25 lines rejected", rc == 1 and "contract-block" in out, out + err)
    shutil.rmtree(d, ignore_errors=True)


# ---- --run overlap detection, including a fixture path containing a space ----

def test_run_disjoint_briefs_pass():
    d = tmp_project()
    briefs = d / "briefs with space"
    briefs.mkdir()
    write_brief(briefs / "A.md", paths=str(d / "owned-a") + "\\\\")
    write_brief(briefs / "B.md", paths=str(d / "owned-b") + "\\\\")
    rc, out, err = run(CHECK, "--run", briefs)
    check("run: disjoint OWNED_PATHS across two briefs passes", rc == 0, out + err)
    shutil.rmtree(d, ignore_errors=True)


def test_run_overlapping_briefs_fail():
    d = tmp_project()
    briefs = d / "briefs with space"
    briefs.mkdir()
    shared = d / "owned-shared"
    write_brief(briefs / "A.md", paths=str(shared) + "\\\\")
    write_brief(briefs / "B.md", paths=str(shared / "sub") + "\\\\")
    rc, out, err = run(CHECK, "--run", briefs)
    check("run: overlapping OWNED_PATHS across two briefs fails", rc == 1, out + err)
    check("run: overlap message names both briefs", "A.md" in out and "B.md" in out, out)
    shutil.rmtree(d, ignore_errors=True)


# ------------------------------------------------------------- selftest ---

def test_check_governance_selftest_green():
    rc, out, err = run(CHECK, "--selftest")
    check("check_governance.py --selftest all ok", rc == 0 and "FAIL" not in out, out + err)


def test_check_governance_core_green():
    rc, out, err = run(CHECK)
    check("check_governance.py (core, v3 tree) passes", rc == 0, out + err)





# ---------------------------------------------------------- estimate -----

def test_estimate_thin_class_refuses():
    proj = tmp_project()
    (proj / ".agent-ops").mkdir(parents=True)
    shutil.copy(FIXTURES / "ledger_estimate.md", proj / ".agent-ops" / "ledger.md")
    rc, out, err = run(RELAY, "estimate", proj, "--task-class", "svc-thin")
    check("thin class (n=4) refuses: exit 1", rc == 1, out + err)
    check("thin class refuses: names n and the need",
          "n=4" in out and "need 5" in out, out)
    check("thin class refuses: no number invented (no 'estimate task-class' line)",
          "estimate task-class=" not in out, out)
    shutil.rmtree(proj, ignore_errors=True)


def test_estimate_n5_boundary_returns_a_number():
    """Negative control for the n>=5 gate: one more row than the thin fixture
    and the refusal must stop firing."""
    proj = tmp_project()
    (proj / ".agent-ops").mkdir(parents=True)
    shutil.copy(FIXTURES / "ledger_estimate.md", proj / ".agent-ops" / "ledger.md")
    rc, out, err = run(RELAY, "estimate", proj, "--task-class", "svc-flat")
    check("n=5 boundary accepted: exit 0", rc == 0, out + err)
    check("n=5 boundary accepted: prints n=5", "n=5" in out, out)
    shutil.rmtree(proj, ignore_errors=True)


def test_estimate_median_and_p80_hand_computed():
    proj = tmp_project()
    (proj / ".agent-ops").mkdir(parents=True)
    shutil.copy(FIXTURES / "ledger_estimate.md", proj / ".agent-ops" / "ledger.md")
    rc, out, err = run(RELAY, "estimate", proj, "--task-class", "svc-skew")
    # series 10,15,20,25,100 -> median(p50)=20.0, p80=25+(100-25)*0.2=40.0
    check("estimate median matches hand-computed series", "median=20.0" in out, out)
    check("estimate p80 matches hand-computed series", "p80=40.0" in out, out)
    check("estimate min/max reported", "min=10 max=100" in out, out)
    shutil.rmtree(proj, ignore_errors=True)


def test_estimate_long_tail_warning_fires_on_skewed_fixture():
    proj = tmp_project()
    (proj / ".agent-ops").mkdir(parents=True)
    shutil.copy(FIXTURES / "ledger_estimate.md", proj / ".agent-ops" / "ledger.md")
    rc, out, err = run(RELAY, "estimate", proj, "--task-class", "svc-skew")
    check("long-tail warning fires on skewed fixture (max/median >= 3)",
          "WARNING: long tail" in out, out)
    shutil.rmtree(proj, ignore_errors=True)


def test_estimate_no_long_tail_warning_on_flat_fixture():
    """Negative control for the skew gate: a flat series must stay silent."""
    proj = tmp_project()
    (proj / ".agent-ops").mkdir(parents=True)
    shutil.copy(FIXTURES / "ledger_estimate.md", proj / ".agent-ops" / "ledger.md")
    rc, out, err = run(RELAY, "estimate", proj, "--task-class", "svc-flat")
    check("no long-tail warning on flat fixture (max/median < 3)",
          "WARNING: long tail" not in out, out)
    shutil.rmtree(proj, ignore_errors=True)


def test_estimate_metric_uncached_in():
    proj = tmp_project()
    (proj / ".agent-ops").mkdir(parents=True)
    shutil.copy(FIXTURES / "ledger_estimate.md", proj / ".agent-ops" / "ledger.md")
    rc, out, err = run(RELAY, "estimate", proj, "--task-class", "svc-tokens",
                        "--metric", "uncached-in")
    # series 100,200,300,400,500 -> median=300.0, p80=420.0
    check("estimate --metric uncached-in uses the token column",
          rc == 0 and "median=300.0" in out and "p80=420.0" in out, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_estimate_nearest_classes_listed_on_refusal():
    proj = tmp_project()
    (proj / ".agent-ops").mkdir(parents=True)
    shutil.copy(FIXTURES / "ledger_estimate.md", proj / ".agent-ops" / "ledger.md")
    rc, out, err = run(RELAY, "estimate", proj, "--task-class", "svc-thin")
    check("thin-class refusal names nearest classes instead of merging",
          "nearest classes:" in out and "svc-skew" in out, out)
    shutil.rmtree(proj, ignore_errors=True)


# ------------------------------------------------- ledger estimate-min ----

def test_ledger_estimate_min_accepts_integer():
    proj = tmp_project()
    rc, out, err = ledger_call(proj, "run1", ["--estimate-min", "20"])
    check("ledger --estimate-min integer accepted", rc == 0, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_ledger_estimate_min_rejects_non_integer():
    """Negative control: estimate-min is validated exactly like every other
    numeric ledger field -- a guess never gets to occupy it unchecked."""
    proj = tmp_project()
    rc, out, err = ledger_call(proj, "run1", ["--estimate-min", "soon"])
    check("ledger --estimate-min rejects non-integer: exit 1", rc == 1, out + err)
    check("ledger --estimate-min rejects non-integer: message",
          "estimate-min=soon" in out and "not an integer" in out, out)
    check("ledger --estimate-min rejects non-integer: nothing written",
          ledger_row_count(proj, "run1") == 0)
    shutil.rmtree(proj, ignore_errors=True)


def test_ledger_estimate_min_rejects_not_measured():
    proj = tmp_project()
    rc, out, err = ledger_call(proj, "run1", ["--estimate-min", "NOT_MEASURED"])
    check("ledger --estimate-min rejects NOT_MEASURED in numeric field: exit 1",
          rc == 1, out + err)
    shutil.rmtree(proj, ignore_errors=True)


# ------------------------------------------------ verify: calibration -----

def test_verify_calibration_hand_computed():
    proj = tmp_project()
    (proj / ".agent-ops").mkdir(parents=True)
    shutil.copy(FIXTURES / "ledger_calibration.md", proj / ".agent-ops" / "ledger.md")
    rc, out, err = run(RELAY, "verify", proj)
    # rows: (est=10,act=15) (est=20,act=22) (est=30,act=28); 4th row has no estimate
    # MAPE = (5/15 + 2/22 + 2/28)/3 *100 = 16.52%; hits(act<=est): only row3 -> 33.33%
    check("calibration n scored excludes the unestimated row", "n scored=3" in out, out + err)
    check("calibration MAPE hand-computed", "MAPE=16.52%" in out, out)
    check("calibration p80 hit hand-computed", "p80 hit=33.33%" in out, out)
    check("calibration bias direction reported", "under-estimating" in out, out)
    check("calibration KPI line breaches (MAPE>30 or hit<80)",
          "estimate calibration: MAPE 16.52%" in out and "BREACH" in out, out)
    shutil.rmtree(proj, ignore_errors=True)


def test_verify_calibration_not_visible_when_nothing_scored():
    """Negative control: no estimate-min anywhere in the ledger must print
    NOT_VISIBLE, never a 0% that reads like a perfect forecaster."""
    proj = tmp_project()
    (proj / ".agent-ops").mkdir(parents=True)
    shutil.copy(FIXTURES / "ledger_clean.md", proj / ".agent-ops" / "ledger.md")
    rc, out, err = run(RELAY, "verify", proj)
    check("calibration prints NOT_VISIBLE with nothing scored",
          "estimate calibration: NOT_VISIBLE" in out, out + err)
    check("calibration never prints a bare 0% MAPE when nothing scored",
          "MAPE=0.00%" not in out, out)
    shutil.rmtree(proj, ignore_errors=True)


def test_telemetry_docs_drift():
    """An undocumented BATCH_FIELD must fail --project. v3 lost this check once already."""
    import re as _re
    doc = ROOT / "nj-agent-ops" / "SKILL.md"
    original = doc.read_text(encoding="utf-8")
    victim = None
    for f in ("false-challenges", "cascade-attempts", "lead-defects"):
        if f"`{f}`" in original:
            victim = f
            break
    if victim is None:
        check("telemetry drift control: a documented field to hide", False, "none found")
        return
    try:
        doc.write_text(original.replace(f"`{victim}`", "`removed-from-docs`", 1), encoding="utf-8")
        rc, out, err = run(CHECK, "--project", str(ROOT))
        check("undocumented telemetry field is caught", rc != 0, (out + err)[-300:])
    finally:
        doc.write_text(original, encoding="utf-8")

# ------------------------------------------------ H1 model-mediated polling

def test_verify_h1_model_polls_breach():
    proj = tmp_project()
    run(RELAY, "batch", proj, "t1", "--model-polls", "3")
    rc, out, err = run(RELAY, "verify", proj)
    check("H1: positive model-polls fails verify", rc == 1, out + err)
    check("H1: breach line names run and value",
          "model-polls=3" in out and "t1" in out, out)
    shutil.rmtree(proj, ignore_errors=True)


def test_verify_h1_model_polls_not_visible_is_legal():
    proj = tmp_project()
    run(RELAY, "batch", proj, "t1")  # model-polls omitted -> NOT_VISIBLE
    rc, out, err = run(RELAY, "verify", proj)
    check("H1: NOT_VISIBLE model-polls does not fail verify",
          "model-polls=" not in out, out + err)
    shutil.rmtree(proj, ignore_errors=True)


# ------------------------------------------------ H2 one receipt per worker

def _write_result(proj, run_id, filename, doc):
    d = Path(proj) / ".agent-ops" / "results" / run_id
    d.mkdir(parents=True, exist_ok=True)
    (d / filename).write_text(json.dumps(doc), encoding="utf-8")


RESULT_OK = {"agent": "a1", "stage": "s1", "status": "ok", "files": [],
             "gates": [], "artefacts": [], "leftovers": [], "detail_path": "d.md"}


def test_verify_h2_duplicate_receipt_breach():
    proj = tmp_project()
    ledger_call(proj, "run1", [])  # ledger row for agent a1
    _write_result(proj, "run1", "a1.json", RESULT_OK)
    _write_result(proj, "run1", "a1-2.json", RESULT_OK)
    rc, out, err = run(RELAY, "verify", proj)
    check("H2: two result files for one agent fails verify", rc == 1, out + err)
    check("H2: breach line names run and agent",
          "results/run1 agent=a1" in out and "2 result files" in out, out)
    shutil.rmtree(proj, ignore_errors=True)


def test_verify_h2_missing_receipt_breach():
    proj = tmp_project()
    ledger_call(proj, "run1", [])  # ledger row for agent a1, no result file
    (Path(proj) / ".agent-ops" / "results" / "run1").mkdir(parents=True)
    rc, out, err = run(RELAY, "verify", proj)
    check("H2: ledger row with no result file fails verify", rc == 1, out + err)
    check("H2: breach line names the missing agent",
          "results/run1 agent=a1" in out and "no result file" in out, out)
    shutil.rmtree(proj, ignore_errors=True)


def test_verify_h2_one_receipt_each_passes():
    proj = tmp_project()
    ledger_call(proj, "run1", [])  # agent a1
    _write_result(proj, "run1", "a1.json", RESULT_OK)
    rc, out, err = run(RELAY, "verify", proj)
    check("H2: exactly one receipt per ledgered agent is clean",
          "results/run1" not in out, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_verify_h2_no_results_dir_is_not_a_breach():
    """Negative control for absence-is-not-a-breach: a run with ledger rows
    but no results/ dir at all was never receipted through this path."""
    proj = tmp_project()
    ledger_call(proj, "run1", [])
    rc, out, err = run(RELAY, "verify", proj)
    check("H2: no results dir at all is not flagged", "results/run1" not in out, out + err)
    shutil.rmtree(proj, ignore_errors=True)


# ------------------------------------------------ H3 classify before retry

def test_verify_h3_unclassified_failure_breach():
    proj = tmp_project()
    ledger_call(proj, "run1", [])
    bad = dict(RESULT_OK, status="failed")
    _write_result(proj, "run1", "a1.json", bad)
    rc, out, err = run(RELAY, "verify", proj)
    check("H3: failed result with no failure_class fails verify", rc == 1, out + err)
    check("H3: breach line names agent and status",
          "agent=a1" in out and "status=failed" in out and "failure_class" in out, out)
    shutil.rmtree(proj, ignore_errors=True)


def test_verify_h3_classified_failure_passes():
    proj = tmp_project()
    ledger_call(proj, "run1", [])
    good = dict(RESULT_OK, status="failed", failure_class="TOOL_FAILURE")
    _write_result(proj, "run1", "a1.json", good)
    rc, out, err = run(RELAY, "verify", proj)
    check("H3: failed result with a valid failure_class is clean",
          "failure_class" not in out, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_verify_h3_ok_status_needs_no_failure_class():
    proj = tmp_project()
    ledger_call(proj, "run1", [])
    _write_result(proj, "run1", "a1.json", RESULT_OK)  # status ok, no failure_class
    rc, out, err = run(RELAY, "verify", proj)
    check("H3: ok status never requires failure_class",
          "failure_class" not in out, out + err)
    shutil.rmtree(proj, ignore_errors=True)


# ------------------------------------------------ H4 overrun needs a cause

def test_verify_h4_overrun_without_note_breach():
    proj = tmp_project()
    ledger_call(proj, "run1", ["--tier", "ECONOMY", "--uncached-in", "20000"])  # > 1.5x12000
    rc, out, err = run(RELAY, "verify", proj)
    check("H4: overrun with empty note fails verify", rc == 1, out + err)
    check("H4: breach line names run, agent, value",
          "run=run1" in out and "agent=a1" in out and "uncached-in=20000" in out, out)
    shutil.rmtree(proj, ignore_errors=True)


def test_verify_h4_overrun_with_note_passes():
    proj = tmp_project()
    ledger_call(proj, "run1", ["--tier", "ECONOMY", "--uncached-in", "20000",
                               "--note", "context too wide, retry classified"])
    rc, out, err = run(RELAY, "verify", proj)
    check("H4: overrun with a note is clean", "uncached-in=20000" not in out, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_verify_h4_under_budget_no_note_needed():
    proj = tmp_project()
    ledger_call(proj, "run1", ["--tier", "ECONOMY", "--uncached-in", "5000"])
    rc, out, err = run(RELAY, "verify", proj)
    check("H4: under-budget row is clean with no note", "uncached-in=5000" not in out, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_verify_h4_no_tier_or_uncached_is_not_a_breach():
    """Negative control: missing tier/uncached-in is skipped, never failed."""
    proj = tmp_project()
    ledger_call(proj, "run1", [])  # no --tier, no --uncached-in
    rc, out, err = run(RELAY, "verify", proj)
    check("H4: absent tier/uncached-in never fails verify", rc == 0, out + err)
    shutil.rmtree(proj, ignore_errors=True)


def test_verify_h4_unbudgeted_tier_skipped():
    """DETERMINISTIC has no entry in CLASS_BUDGETS -- skipped, not failed,
    even at a huge uncached-in with no note."""
    proj = tmp_project()
    ledger_call(proj, "run1", ["--tier", "DETERMINISTIC", "--uncached-in", "999999"])
    rc, out, err = run(RELAY, "verify", proj)
    check("H4: tier with no defined budget is never flagged",
          "uncached-in=999999" not in out, out + err)
    shutil.rmtree(proj, ignore_errors=True)


ALL_TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]  # collected after every def, not before


def main():
    for t in ALL_TESTS:
        t()
    for m in FAIL_MSGS:
        print("FAIL:", m)
    print(f"TESTS: {PASSED} passed, {FAILED} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
