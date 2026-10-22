#!/usr/bin/env python3
"""nj-agent-ops/tests/test_v4.py -- plain-assert suite for the v4 gates in relay.py and
check_governance.py (slots, legal spawns, route, helpers-required, leakscan, clauses).

Run: PYTHONUTF8=1 python nj-agent-ops/tests/test_v4.py     (stdlib only, no pytest)
Secrets: every "secret" here is fake and assembled at runtime; the tests assert they are
never printed.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parents[1]
RELAY = SKILLS / "nj-agent-ops" / "scripts" / "relay.py"
CHECK = SKILLS / "nj-delegate" / "scripts" / "check_governance.py"
sys.path.insert(0, str(RELAY.parent))
import relay  # noqa: E402

PASSED, FAILED, MSGS = 0, 0, []


def check(name, cond, detail=""):
    global PASSED, FAILED
    if cond:
        PASSED += 1
    else:
        FAILED += 1
        MSGS.append(f"{name}: {str(detail)[:300]}")


def run(*args):
    p = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True,
                       encoding="utf-8", env=dict(os.environ, PYTHONUTF8="1"))
    return p.returncode, p.stdout + p.stderr


def proj():
    return Path(tempfile.mkdtemp(prefix="njv4_"))


def slots(p, *a):
    return run(RELAY, "slots", *a[:1], p, *a[1:])


# ------------------------------------------------------------------ slots --

def test_slots_claim_release_list_and_cap():
    p = proj()
    rc, out = slots(p, "claim", "--agent", "a0", "--role", "sonnet")
    check("slots: first claim ok", rc == 0 and "1/20" in out, out)
    for i in range(1, 20):
        rc, out = slots(p, "claim", "--agent", f"a{i}", "--role", "haiku")
    check("slots: 20th claim ok", rc == 0 and "20/20" in out, out)
    before = (p / ".agent-ops" / "slots.json").read_text(encoding="utf-8")
    rc, out = slots(p, "claim", "--agent", "a20", "--role", "haiku")
    check("slots: 21st claim refused", rc == 1 and "REFUSED" in out, out)
    check("slots: refusal writes nothing",
          (p / ".agent-ops" / "slots.json").read_text(encoding="utf-8") == before)
    rc, out = slots(p, "claim", "--agent", "a3", "--role", "haiku")
    check("slots: re-claim by a holder at the cap is a refresh, not a new slot", rc == 0 and "20/20" in out, out)
    rc, out = slots(p, "release", "--agent", "a3")
    check("slots: release frees a slot", rc == 0 and "19/20" in out, out)
    rc, out = slots(p, "claim", "--agent", "a20", "--role", "sonnet")
    check("slots: claim ok after a release", rc == 0 and "20/20" in out, out)
    rc, out = slots(p, "release", "--agent", "nobody")
    check("slots: releasing a non-holder exits 1", rc == 1, out)
    rc, out = slots(p, "list")
    check("slots: list shows count", rc == 0 and "slots: 20/20 active" in out, out)
    rc, out = slots(p, "claim", "--agent", "zz")
    check("slots: claim without a role refused", rc != 0 or "REFUSED" in out, out)
    shutil.rmtree(p, ignore_errors=True)


def test_slots_stale_expiry():
    p = proj()
    (p / ".agent-ops").mkdir()
    old = time.time() - 4 * 3600
    rows = [{"agent": f"old{i}", "role": "haiku", "ts": old} for i in range(20)]
    (p / ".agent-ops" / "slots.json").write_text(json.dumps({"slots": rows}), encoding="utf-8")
    rc, out = slots(p, "claim", "--agent", "fresh", "--role", "sonnet")
    check("slots: stale claims expire with a warning, claim succeeds",
          rc == 0 and "expired stale claim old0" in out and "1/20" in out, out)
    rc, out = slots(p, "list")
    check("slots: expired rows are gone from the ledger", "old0" not in out and "1/20" in out, out)
    # a young claim is NOT expired
    rc, out = slots(p, "list", "--stale-min", "0.0001")
    check("slots: --stale-min bound is honoured", "expired stale claim fresh" in out, out)
    shutil.rmtree(p, ignore_errors=True)


def test_sweep_reports_open_slot():
    p = proj()
    slots(p, "claim", "--agent", "w1", "--role", "haiku")
    rc, out = run(RELAY, "sweep", p)
    check("sweep: an unreleased slot is a leftover", rc == 1 and "slot w1" in out, out)
    slots(p, "release", "--agent", "w1")
    rc, out = run(RELAY, "sweep", p)
    check("sweep: clean after release", rc == 0, out)
    shutil.rmtree(p, ignore_errors=True)


# ----------------------------------------------------- legal delegations --

def test_delegation_legal():
    L = relay.delegation_legal
    check("spawn: sonnet->haiku depth 2 legal", L("sonnet-lead", "haiku", 2))
    check("spawn: haiku->haiku BREACH", not L("haiku-helper", "haiku", 2))
    check("spawn: haiku->sonnet BREACH", not L("haiku-helper", "sonnet", 2))
    check("spawn: sonnet->sonnet BREACH", not L("sonnet-lead", "sonnet", 2))
    check("spawn: sonnet->opus BREACH", not L("sonnet-lead", "opus", 2))
    check("spawn: sonnet->haiku depth 3 BREACH", not L("sonnet-lead", "haiku", 3))
    check("spawn: lead->sonnet legal", L("main", "sonnet", 1))
    check("spawn: lead->haiku legal", L("opus", "haiku", 1))


def test_batch_spawns_counts_only_illegal():
    p = proj()
    rc, out = run(RELAY, "batch", p, "t1", "--spawns", "sonnet>haiku@2,main>sonnet@1")
    row = (p / ".agent-ops" / "batches.md").read_text(encoding="utf-8").splitlines()[-1]
    cells = [c.strip() for c in row.strip("|").split("|")]
    hdr = [c.strip() for c in (p / ".agent-ops" / "batches.md").read_text(encoding="utf-8").splitlines()[0].strip("|").split("|")]
    d = dict(zip(hdr, cells))
    check("batch: legal Sonnet->Haiku writes nested-spawns=0, no WARN",
          rc == 0 and d["nested-spawns"] == "0" and "WARN" not in out, out + row)
    rc, out = run(RELAY, "batch", p, "t2", "--spawns", "sonnet>haiku@2,haiku>haiku@2")
    row = (p / ".agent-ops" / "batches.md").read_text(encoding="utf-8").splitlines()[-1]
    check("batch: Haiku->anything is counted and warned", "illegal spawn haiku>haiku@2" in out and "| 1 |" in row, out + row)
    rc, out = run(RELAY, "verify", p)
    check("verify: an illegal spawn count in batches is a BREACH", rc == 1 and "BREACH" in out, out)
    shutil.rmtree(p, ignore_errors=True)


# ------------------------------------------------------------- NEXT_TIER --

def test_route_no_opus_target():
    check("route: NEXT_TIER is haiku->sonnet only", relay.NEXT_TIER == {"haiku": "sonnet"}, relay.NEXT_TIER)
    d = lambda **k: relay.route_decide([], "x", **k)[0]
    check("route: haiku failure escalates to sonnet",
          d(failed="g", cause="TEST_FAILURE", ran_on="haiku").startswith("ESCALATE sonnet"))
    s = d(failed="g", cause="TEST_FAILURE", ran_on="sonnet")
    check("route: sonnet failure STOPs, never opus", s.startswith("STOP") and "ESCALATE" not in s, s)
    rows = [{"task-class": "x", "runtime": "sonnet", "verify-status": v, "retries": "", "escalations": ""}
            for v in ["ok"] + ["failed"] * 4]
    line = relay.route_decide(rows, "x")[0]
    check("route: poor sonnet first-pass does not start opus", "START sonnet" in line and "opus" not in line.lower(), line)
    rc, out = run(RELAY, "route", proj(), "--class", "x", "--failed", "g", "--cause", "TEST_FAILURE", "--ran-on", "opus")
    check("route: --ran-on opus no longer accepted", rc != 0, out)


# ------------------------------------------------------ helpers-required --

def test_helpers_required_formula():
    f = relay.helpers_required
    got = [f(n) for n in (0, 5, 6, 7, 12, 13, 18, 24, 25, 100)]
    check("helpers: ITEMS n -> 0 if n<6 else min(4,ceil(n/6))", got == [0, 0, 1, 2, 2, 3, 3, 4, 4, 4], got)


def _brief(p, name, task, items):
    d = p / ".agent-ops" / "briefs"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name}.md").write_text(f"GOVERNANCE   nj-governance-v4\nTASK         {task} . class\nITEMS        {items}\n", encoding="utf-8")


def _log(p, recs):
    (p / ".agent-ops").mkdir(parents=True, exist_ok=True)
    (p / ".agent-ops" / "spawns.jsonl").write_text(
        "\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")


def _rec(parent, model="haiku", ctype="haiku-helper"):
    return {"ts": "2026-10-16T10:00:00Z", "parent": parent, "child_type": ctype, "model": model}


def test_verify_helpers_required():
    p = proj()
    _brief(p, "svc1", "svc1", 13)          # needs 3
    _log(p, [_rec("sonnet-lead:svc1")] * 2)
    rc, out = run(RELAY, "verify", p)
    check("verify: 2 helpers < 3 required fails", rc == 1 and "required=3 spawned=2 FAIL" in out, out)
    _log(p, [_rec("sonnet-lead:svc1")] * 3)
    rc, out = run(RELAY, "verify", p)
    check("verify: 3 helpers meets 3 required", rc == 0 and "required=3 spawned=3" in out and "FAIL" not in out, out)
    shutil.rmtree(p, ignore_errors=True)

    p = proj()
    _brief(p, "small", "small", 5)         # needs 0
    rc, out = run(RELAY, "verify", p)
    check("verify: ITEMS<6 needs no helpers and no log", rc == 0 and "required=0" in out, out)
    shutil.rmtree(p, ignore_errors=True)

    p = proj()
    _brief(p, "big", "big", 40)            # needs 4, no log at all
    rc, out = run(RELAY, "verify", p)
    check("verify: required>0 with no spawn log fails", rc == 1 and "no spawn log" in out, out)
    shutil.rmtree(p, ignore_errors=True)

    p = proj()                              # two briefs: spawns attributed by parent token
    _brief(p, "a", "taska", 6)
    _brief(p, "b", "taskb", 6)
    _log(p, [_rec("sonnet-lead:taska")])
    rc, out = run(RELAY, "verify", p)
    check("verify: spawns are attributed per brief", rc == 1 and "helpers taska: ITEMS=6 required=1 spawned=1" in out
          and "helpers taskb: ITEMS=6 required=1 spawned=0 FAIL" in out, out)
    shutil.rmtree(p, ignore_errors=True)

    p = proj()                              # configurable log path
    _brief(p, "c", "taskc", 6)
    alt = p / "elsewhere.jsonl"
    alt.write_text(json.dumps(_rec("sonnet-lead:taskc")) + "\n", encoding="utf-8")
    rc, out = run(RELAY, "verify", p, "--spawn-log", alt)
    check("verify: --spawn-log path is honoured", rc == 0 and "spawned=1" in out, out)
    shutil.rmtree(p, ignore_errors=True)


def test_verify_spawn_log_illegal():
    p = proj()
    _log(p, [_rec("sonnet-lead", "haiku"), _rec("haiku-helper", "haiku")])
    rc, out = run(RELAY, "verify", p)
    check("verify: haiku->haiku in the log is a BREACH", rc == 1 and "spawns.jsonl:2 illegal spawn haiku->haiku" in out, out)
    shutil.rmtree(p, ignore_errors=True)
    p = proj()
    _log(p, [_rec("sonnet-lead", "haiku"), _rec("main", "sonnet", "sonnet-lead")])
    rc, out = run(RELAY, "verify", p)
    check("verify: legal log passes", rc == 0 and "illegal" not in out, out)
    shutil.rmtree(p, ignore_errors=True)


# ---------------------------------------------------------------- leakscan --

def test_leakscan():
    p = proj()
    # fake secrets, built at runtime so this file holds no secret-shaped literal
    k_or = "sk-" + "or-" + "v1-" + "abcdef0123456789"
    k_bearer = "Bear" + "er " + "eyJhbGciOi" + "JIUzI1NiJ9abc"
    k_pw = "pass" + "word=" + "Hunter2" + "xyz"
    k_tok = "TAISCE_" + "TOKEN=" + "abcd1234efgh5678"
    k_jira = "JIRA_" + "PASS=" + "s3cretvalue"
    f = p / "receipt.md"
    f.write_text("\n".join(["clean line", k_or, k_bearer, k_pw, k_tok, k_jira, "clean again"]), encoding="utf-8")
    rc, out = run(RELAY, "leakscan", f)
    check("leakscan: every pattern fires, exit 1", rc == 1 and out.count("leakscan LEAK") == 5, out)
    for name in ("sk-or-", "Bearer", "password=", "token=", "JIRA_PASS"):
        check(f"leakscan: pattern {name} named", f"pattern={name}" in out, out)
    check("leakscan: lines reported", "receipt.md:2 " in out and "receipt.md:6 " in out, out)
    for v in (k_or, k_bearer.split()[1], "Hunter2xyz", "abcd1234efgh5678", "s3cretvalue"):
        check("leakscan: never prints a secret value", v not in out, "value leaked into output")

    g = p / "ok.md"
    g.write_text("Authorization: Bearer ${TAISCE_TOKEN}\npassword=<redacted>\ntokens=1200\n"
                 "token=****\nJIRA_PASS=$JIRA_PASS\nthe password field is required\n", encoding="utf-8")
    rc, out = run(RELAY, "leakscan", g)
    check("leakscan: placeholders and prose are not leaks", rc == 0, out)

    # --secrets-file: literal values, matched by content, reported without the value
    lit = "Zq9-literal-" + "value-77"
    h = p / "report.md"
    h.write_text(f"line one\nthe answer is {lit} here\n", encoding="utf-8")
    sf = p / "secrets.txt"
    sf.write_text(f"# comment\nSOMEKEY={lit}\n", encoding="utf-8")
    rc, out = run(RELAY, "leakscan", h, sf, "--secrets-file", sf)
    check("leakscan: known secret found, file:line + id only",
          rc == 1 and "report.md:2 pattern=known-secret#" in out, out)
    check("leakscan: known secret value never printed", lit not in out, "value leaked")
    check("leakscan: the secrets file itself is not scanned", "secrets.txt" not in out, out)
    sj = p / "secrets.json"
    sj.write_text(json.dumps({"jira": {"pw": lit}}), encoding="utf-8")
    rc, out = run(RELAY, "leakscan", h, "--secrets-file", sj)
    check("leakscan: JSON secrets file leaves read", rc == 1 and "known-secret" in out and lit not in out, out)
    # directory walk
    (p / "sub").mkdir()
    (p / "sub" / "r.json").write_text(k_or, encoding="utf-8")
    rc, out = run(RELAY, "leakscan", p / "sub")
    check("leakscan: directories are walked", rc == 1 and "r.json:1" in out, out)
    shutil.rmtree(p, ignore_errors=True)


# -------------------------------------------------------- check_governance --

def test_check_governance_v4():
    rc, out = run(CHECK, "--selftest")
    check("check_governance --selftest green (incl. v4 clause controls)", rc == 0 and "FAIL" not in out, out)
    check("check_governance selftest runs the v4 controls", out.count("v4 ") >= 6, out)
    rc, out = run(CHECK, "--brief", SKILLS / "nj-delegate" / "templates" / "worker-brief.example.md")
    check("check_governance: v3 example brief still accepted", rc == 0, out)


ALL_TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]


def main():
    for t in ALL_TESTS:
        t()
    for m in MSGS:
        print("FAIL:", m)
    print(f"TESTS v4: {PASSED} passed, {FAILED} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
