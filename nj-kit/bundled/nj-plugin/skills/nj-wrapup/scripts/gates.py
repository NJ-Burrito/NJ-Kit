#!/usr/bin/env python3
"""nj-wrapup step 2 gate: no not-fixed row is filed until every gate has a cited verdict.
Reads plan.json (or the plan.md table) -> gates.json + claims.json. Exit != 0 blocks filing.

  PYTHONUTF8=1 python gates.py --plan plan.json|plan.md --out DIR [--results tracker.json] | --selftest

Plan row (json) / column (md): note, verdict, action, root_cause, also (other notes of the same root cause), then ONE
cell per gate, each `pass: <evidence>` | `n/a: <reason>` | `stop: <reason>` (hold: = stop:), never empty, never bare:
  known-not-a-bug · latest-dated-statement · design-lookup · cross-service-pattern · data-account-cause · dev-comments-live-status
action: file | existing | open-item | held | untestable-task | fixed
Refuses: an empty/bare gate cell on a `file` row; a `file` row with any `stop` cell (names the gate); a `held` row with no
stop cell and no `risk`; a `file` row without root_cause; two `file` rows on one root_cause (merge them: one row, `also: [...]`);
with --results, a not-fixed note with no plan row. claims.json = one entry per root cause: lanes claim by it, never by note id.
"""
from __future__ import annotations
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import utf8, nat, load_results

GATES = ("known-not-a-bug", "latest-dated-statement", "design-lookup", "cross-service-pattern",
         "data-account-cause", "dev-comments-live-status")
STOP = ("stop", "hold")


def load_plan(path):
    txt = open(path, encoding="utf-8").read()
    if path.lower().endswith(".json"):
        d = json.loads(txt)
        return d.get("rows", d) if isinstance(d, dict) else d
    rows, head = [], None
    for ln in txt.splitlines():
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if head is None:
            head = [re.sub(r"[\s_]+", "-", c.lower()).replace("root-cause", "root_cause") for c in cells]
        elif not all(re.fullmatch(r":?-+:?", c) for c in cells if c):
            r = dict(zip(head, cells))
            r["also"] = [x for x in re.split(r"[,\s]+", r.get("also", "")) if x]
            rows.append(r)
    return rows


def cell(r, g):
    v = (r.get("gates") or {}).get(g, r.get(g))
    return str(v).strip() if v is not None else ""


def verdict(v):
    """-> (kind, text): kind in pass/n/a/stop/empty/bare."""
    m = re.match(r"(?i)\s*(pass|n/a|stop|hold)\s*[:\-–]?\s*(.*)", v or "", re.S)
    if not m:
        return ("empty" if not (v or "").strip() else "bare"), v or ""
    k, t = m.group(1).lower(), m.group(2).strip()
    k = "stop" if k == "hold" else k
    return (k if len(t) >= 4 else "bare"), t


def check(rows, results=None):
    errs, out, claims = [], [], {}
    fr = {}
    for r in rows:
        n, act = str(r.get("note")), str(r.get("action", "")).lower()
        res = {"note": n, "action": act, "stopped_by": [], "problems": []}
        if act == "file" or act == "held":
            for g in GATES:
                k, t = verdict(cell(r, g))
                if k == "stop":
                    res["stopped_by"].append(g)
                elif k in ("empty", "bare") and act == "file":
                    res["problems"].append(f"gate '{g}' is {'empty' if k == 'empty' else 'without a cited reason'}")
        if act == "file":
            for g in res["stopped_by"]:
                res["problems"].append(f"gate '{g}' says stop ({verdict(cell(r, g))[1][:60]}) but the row is headed for filing")
            if not r.get("root_cause"):
                res["problems"].append("no root_cause id (lanes claim by root cause)")
            else:
                fr.setdefault(r["root_cause"], []).append(n)
                claims.setdefault(r["root_cause"], {"root_cause": r["root_cause"], "notes": []})["notes"] += [n, *(r.get("also") or [])]
        if act == "held" and not res["stopped_by"] and not r.get("risk"):
            res["problems"].append("held with no stop cell and no risk flag: a held row names the gate or flag that holds it")
        errs += [f"{n}: {p}" for p in res["problems"]]
        out.append(res)
    for rc, ns in sorted(fr.items()):
        if len(ns) > 1:
            errs.append(f"root cause '{rc}' has {len(ns)} plan rows to file ({', '.join(ns)}): merge into ONE row (note + also:[...])")
    if results:
        covered = {str(x) for r in rows for x in [r.get("note"), *(r.get("also") or [])]}
        notes, _ = load_results(results)
        errs += [f"{n}: not-fixed note has no plan row" for n, v in sorted(notes.items(), key=lambda x: nat(x[0]))
                 if str(v.get("verdict", "")).lower() == "not-fixed" and n not in covered]
    return {"status": "fail" if errs else "pass", "errors": errs, "rows": out}, list(claims.values())


def selftest():
    import tempfile
    T2 = {  # 2026-10-12 session: the 8 keys that later became Not Bug -> gate that must hold/stop each (verify-v2.md)
        "5028": ("latest-dated-statement", "dev: PROJ-1011 pt 3 adds the option (4164 newer than 4438)"),
        "5029": ("latest-dated-statement", "dev: PROJ-1010 pt 3 fixed the text"),
        "5030": ("dev-comments-live-status", "covering ticket Not Bug, 0 comments, no reason given"),
        "5032": ("data-account-cause", "needs a facility with a practice licence"),
        "5039": ("known-not-a-bug", "outgoing letter number, withdrawn 2026-10-12"),
        "5040": ("known-not-a-bug", "SIGN_HERE in signature block, no 5xx (nj-qa-pipeline 3c)"),
        "5041": ("known-not-a-bug", "outgoing letter number, withdrawn 2026-10-12"),
        "5042": ("design-lookup", "flowable lookup --q outputs: the second output is not in the BPMN")}
    def row(note, rc, act="file", **gate_over):
        r = {"note": note, "verdict": "not-fixed", "action": act, "root_cause": rc,
             "gates": {g: "pass: checked, nothing covers it" for g in GATES}}
        r["gates"].update(gate_over)
        return r
    def t2(act, stop=True):
        return [row("T" + k, "RC" + k, act, **({g: "stop: " + why} if stop else {})) for k, (g, why) in T2.items()]
    # 1. the 8 Not-Bug keys: stopped (action held) -> gates pass, each names its gate; headed for filing -> each refused with its gate
    r, _ = check(t2("held"))
    assert r["status"] == "pass" and {x["note"][1:]: x["stopped_by"][0] for x in r["rows"]} == {k: v[0] for k, v in T2.items()}, r
    r, _ = check(t2("file"))
    assert r["status"] == "fail" and all(any(f"T{k}:" in e and f"gate '{g}' says stop" in e for e in r["errors"]) for k, (g, _) in T2.items()), r["errors"]
    # 2. 5030 slipped in v2 (no reason anywhere): an empty cell refuses it; a bare 'pass' too
    bare = row("T5030", "RC5030", **{"dev-comments-live-status": ""})
    r, _ = check([bare]); assert r["status"] == "fail" and "gate 'dev-comments-live-status' is empty" in r["errors"][0], r
    r, _ = check([row("T5030", "RC5030", **{"design-lookup": "pass"})]); assert "without a cited reason" in r["errors"][0], r
    # 3. held without a named gate/flag is refused
    r, _ = check([row("T1", "RC1", "held")]); assert r["status"] == "fail" and "held with no stop cell" in r["errors"][0], r
    # 4. 5031 x5 = one root cause: five plan rows refused, one merged row passes and yields ONE claim
    five = [row(f"N{i}", "RC-year-2027") for i in range(1, 6)]
    r, _ = check(five); assert r["status"] == "fail" and any("root cause 'RC-year-2027' has 5 plan rows" in e for e in r["errors"]), r
    one = dict(five[0], also=[f"N{i}" for i in range(2, 6)])
    r, cl = check([one]); assert r["status"] == "pass" and len(cl) == 1 and len(cl[0]["notes"]) == 5, (r, cl)
    # 5. md table form, and --results coverage
    md = ("| note | verdict | action | root_cause | also | " + " | ".join(GATES) + " |\n|" + "---|" * (5 + len(GATES)) + "\n"
          "| N1 | not-fixed | file | RC1 | | " + " | ".join(["pass: ok-checked"] * 6) + " |\n"
          "| N2 | not-fixed | file | RC2 | | " + " | ".join(["pass: ok-checked"] * 5) + " |  |\n")
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "plan.md"); open(p, "w", encoding="utf-8").write(md)
        r, _ = check(load_plan(p)); assert r["status"] == "fail" and r["errors"] == ["N2: gate 'dev-comments-live-status' is empty"], r
        rp = os.path.join(tmp, "t.json"); json.dump({"notes": [{"note": "N1", "verdict": "not-fixed"}, {"note": "N9", "verdict": "not-fixed"}]}, open(rp, "w"))
        r, _ = check(load_plan(p)[:1], rp); assert r["errors"] == ["N9: not-fixed note has no plan row"], r
    print("gates selftest: PASS (T2 keys 5028/5029/5030/5032/5039/5040/5041/5042 each stopped by its named gate: 2x latest-dated-statement, "
          "dev-comments-live-status, data-account-cause, 3x known-not-a-bug, design-lookup; empty/bare cell refused; "
          "5031 x5 plan rows refused -> 1 merged row = 1 claim; md plan parsed; uncovered note refused)")


def main():
    utf8()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan"); ap.add_argument("--out"); ap.add_argument("--results"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.plan and a.out):
        ap.error("--plan and --out are required")
    r, claims = check(load_plan(a.plan), a.results)
    os.makedirs(a.out, exist_ok=True)
    json.dump(r, open(os.path.join(a.out, "gates.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(claims, open(os.path.join(a.out, "claims.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"gates: {r['status'].upper()} · {len(r['rows'])} rows · {len(claims)} root-cause claims · "
          f"{sum(1 for x in r['rows'] if x['stopped_by'])} stopped")
    for e in r["errors"]:
        print("REFUSED:", e)
    sys.exit(1 if r["errors"] else 0)


if __name__ == "__main__":
    main()
