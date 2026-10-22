#!/usr/bin/env python3
"""nj-wrapup gate: join results + filed-*.json, GET every key, write trace.json + trace.md.
Exit 0 only if every check holds. Non-zero blocks emails, rank titles and the QA message.

  PYTHONUTF8=1 python reconcile.py --results tracker.json --filed "jira/filed-*.json" --out DIR
         [--creds FILE] [--claim bugs=10 --claim tasks=6 ...] [--legacy] [--offline] | --selftest

Credentials: env JIRA_BASE_URL/JIRA_USER/JIRA_PASS or --creds FILE. Never printed.
--legacy: sessions filed before v2 (no severity line, no Task code anchor) -> those two checks become warnings.
--claim: a number someone intends to publish (email, rank title); it must equal the computed one.
Claim names: bugs(=new_bugs, blocker excluded) notes fixed not_fixed untestable blocked withdrawn existing new_bugs blocker tasks
             new_total bugs_incl_blocker held
"""
from __future__ import annotations
import argparse, json, os, re, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import utf8, nat, load_creds, jira_get, load_filed, load_results

VERDICTS = ("fixed", "not-fixed", "untestable", "blocked", "withdrawn")
CLOSED = ("done", "closed", "resolved", "not bug", "rejected", "won't fix", "won't do", "duplicate")
NEG = ("not bug", "rejected", "won't fix", "won't do", "duplicate", "cannot reproduce", "invalid")  # a developer already ruled: not a defect
FIELDS = "summary,issuetype,status,resolution,assignee,reporter,labels,priority,issuelinks,attachment,description,created"


def kind(row, notes):
    if row["action"] in ("held", "open-item", "existing"):
        return row["action"]
    t = row.get("type")
    if row.get("kind") == "blocker" or str(row["note"]).upper().startswith("BLOCK"):
        return "blocker"
    if t == "Task" or (t is None and notes.get(row["note"], {}).get("verdict") == "untestable"):
        return "task"
    return "bug"


def run(results, filed_glob, get=None, claims=None, legacy=False):
    notes, blockers = load_results(results)
    rows = load_filed(filed_glob)
    mm, warn = [], []
    bad = mm.append
    # 1. verdict denominators
    cnt = {v: 0 for v in VERDICTS}
    for n, r in notes.items():
        v = str(r.get("verdict", "")).lower()
        if v in cnt:
            cnt[v] += 1
        else:
            bad(f"{n}: verdict '{v}' is not one of {'/'.join(VERDICTS)} (resolve partials first)")
        if v == "fixed" and not r.get("evidence"):
            bad(f"{n}: fixed without retest evidence path")
    N = len(notes)
    if sum(cnt.values()) != N:
        bad(f"notes {N} != fixed+not-fixed+untestable+blocked+withdrawn {sum(cnt.values())}")
    # 2. classify rows, coverage
    for r in rows:
        r["kind"] = kind(r, notes)
    new = [r for r in rows if r["kind"] in ("bug", "blocker", "task")]
    keys = [r["key"] for r in new if r.get("key")]
    for k in sorted({k for k in keys if keys.count(k) > 1}):
        bad(f"{k}: new key claimed by more than one row")
    rc = {}
    for r in new:
        if r["kind"] in ("bug", "blocker") and r.get("root_cause"):
            rc.setdefault(r["root_cause"], set()).add(r.get("key") or r["note"])
    for c_, ks in sorted(rc.items()):
        if len(ks) > 1:
            bad(f"root cause '{c_}' filed as {len(ks)} Bugs ({', '.join(sorted(ks))}): one Bug per root cause, list the other notes/services in it")
    by_note = {}
    for r in rows:
        for n in [r["note"], *(r.get("also") or [])]:  # a merged row (one root cause) covers every note it lists
            by_note.setdefault(n, []).append(r)
    for n, r in sorted(notes.items(), key=lambda x: nat(x[0])):
        v = str(r.get("verdict", "")).lower()
        rs = by_note.get(n, [])
        if v == "not-fixed" and not any(
                x["kind"] in ("bug", "existing") or (x["kind"] in ("held", "open-item") and x.get("reason")) for x in rs):
            bad(f"{n}: not-fixed with no Bug key, existing key or recorded reason")
        if v == "untestable":
            if not any(x["kind"] == "task" or (x["kind"] in ("open-item", "held") and x.get("reason")) for x in rs):
                bad(f"{n}: untestable with no Task key or open-item reason")
            if any(x["kind"] == "bug" for x in rs):
                bad(f"{n}: untestable note filed as Bug")
        if v == "fixed" and any(x["kind"] in ("bug", "task") for x in rs):
            bad(f"{n}: fixed note has a new ticket")
        for x in rs:
            if x["kind"] == "task" and v != "untestable":
                bad(f"{n}: Task filed for a {v or '?'} note")
            if x["kind"] in ("held", "open-item") and not x.get("reason"):
                bad(f"{n}: {x['kind']} row without reason")
    extra = sorted({r["note"] for r in rows if r["note"] not in notes and r["kind"] != "blocker"}, key=nat)
    n_block = sum(1 for r in new if r["kind"] == "blocker")
    if blockers is not None and len(blockers) != n_block:
        bad(f"blockers recorded {len(blockers)} != blocker Bugs filed {n_block}")
    # 3. GET every key
    fetched = {}
    if get:
        for r in rows:
            k = r.get("key")
            if not k or k in fetched:
                continue
            st, d = get(f"/rest/api/2/issue/{k}?fields={FIELDS}")
            if st != 200 or not d:
                bad(f"{k}: GET returned {st}")
                fetched[k] = None
            else:
                fetched[k] = d["fields"]
        for r in rows:
            k, f = r.get("key"), fetched.get(r.get("key"))
            if not k or f is None:
                continue
            t, st = f["issuetype"]["name"], f["status"]["name"]
            if r["kind"] == "existing":
                if st.lower() in CLOSED:
                    bad(f"{k}: existing ticket is {st}, it does not cover an open defect")
                continue
            if r["kind"] not in ("bug", "blocker", "task"):
                continue
            res = ((f.get("resolution") or {}).get("name") or "").lower()
            if (st.lower() in NEG or res in NEG) and not r.get("reopened"):
                bad(f"{k}: new ticket is already {st}" + (f" / resolution {res}" if res else "")
                    + ": a developer ruled it not a defect; hold it, or mark the row reopened:true after the owner re-rules")
            elif st.lower() in CLOSED and not r.get("reopened"):
                warn.append(f"{k}: new ticket is already {st}; confirm it is a real fix before counting it open")
            want = "Task" if r["kind"] == "task" else "Bug"
            if t != want:
                bad(f"{k}: type {t}, expected {want}")
            asg = (f.get("assignee") or {}).get("name")
            if not asg:
                bad(f"{k}: no assignee")
            elif not r.get("assignee"):
                (warn if legacy else mm).append(f"{k}: filed row names no assignee (owner names it per filing; never a default)")
            elif r["assignee"] != asg:
                warn.append(f"{k}: reassigned after filing ({r['assignee']} -> {asg}); the email names teams, not people")
            lab = f.get("labels") or []
            if not any(x.startswith("env-") for x in lab):
                bad(f"{k}: no env-* label")
            if r["kind"] == "task" and "untestable" not in lab:
                bad(f"{k}: Task without label untestable")
            if r["kind"] == "task" and "wrapup" not in lab:
                (warn if legacy else mm).append(f"{k}: Task without label wrapup (nj-rank close-mine would not skip it)")
            linked = {(x.get("outwardIssue") or x.get("inwardIssue") or {}).get("key") for x in f.get("issuelinks") or []}
            for lk in r.get("links") or []:
                if lk not in linked:
                    bad(f"{k}: missing link to {lk}")
            na = len(f.get("attachment") or [])
            if na == 0:
                bad(f"{k}: no attachment (no evidence, no filing)")
            elif r.get("attachments") and na != len(r["attachments"]):
                bad(f"{k}: {na} attachments in Jira, {len(r['attachments'])} in the filed row")
            if getattr(get, "user", None) and (f.get("reporter") or {}).get("name") != get.user:
                bad(f"{k}: reporter is not the API user")
            if t == "Bug":
                pr = (f.get("priority") or {}).get("name")
                if not pr:
                    bad(f"{k}: Bug without priority")
                if r["kind"] == "blocker" and pr != "High":
                    bad(f"{k}: blocker Bug priority is not High")
                if not re.search(r"(الخطورة|Severity)[^:：]{0,24}[:：]\s*\S+", f.get("description") or ""):
                    (warn if legacy else mm).append(f"{k}: no severity line «الخطورة (Severity): …» in the description")
            if r["kind"] == "task" and not r.get("anchor"):
                (warn if legacy else mm).append(f"{k}: Task has no concrete code anchor (file/config/BPMN node/variable)")
    seen = {}
    for r in new:
        s_ = (fetched.get(r.get("key")) or {}).get("summary")
        if s_ and r.get("key"):
            seen.setdefault(re.sub(r"\W+", " ", s_).strip().lower(), set()).add(r["key"])
    for s_, ks in seen.items():
        if len(ks) > 1:
            warn.append(f"identical summaries on {', '.join(sorted(ks))}: same root cause filed twice?")
    # 4. counts and claims
    c = {"notes": N, **{v.replace("-", "_"): cnt[v] for v in VERDICTS},
         "existing": len({r["key"] for r in rows if r["kind"] == "existing"}),
         "new_bugs": sum(1 for r in new if r["kind"] == "bug"), "blocker": n_block,
         "tasks": sum(1 for r in new if r["kind"] == "task"), "held": sum(1 for r in rows if r["kind"] == "held"),
         "open_items": sum(1 for r in rows if r["kind"] == "open-item")}
    c["new_total"] = c["new_bugs"] + c["blocker"] + c["tasks"]
    c["bugs"] = c["new_bugs"]  # alias: Bugs excluding the blocker
    c["bugs_incl_blocker"] = c["new_bugs"] + c["blocker"]
    c["not_covered"] = c["blocked"] + c["untestable"]
    for name, val in (claims or {}).items():
        if name not in c:
            bad(f"claim '{name}' is not a reconcile count")
        elif c[name] != int(val):
            bad(f"claim {name}={val} but trace says {c[name]}")
    crit = [("every note has a verdict", sum(cnt.values()) == N),
            ("every not-fixed has a key or a recorded reason", not any("not-fixed with no" in m for m in mm)),
            ("every new ticket has evidence, priority and severity",
             not any(("attachment" in m or "priority" in m or "severity" in m) for m in mm + warn)),
            ("every blocker is listed", not any("blocker" in m for m in mm))]
    trows = []
    for r in rows:
        f = fetched.get(r.get("key")) or {}
        trows.append({"note": r["note"], "key": r.get("key"), "kind": r["kind"], "action": r["action"],
                      "type": (f.get("issuetype") or {}).get("name") or r.get("type"),
                      "status": (f.get("status") or {}).get("name") or r.get("status"),
                      "summary": f.get("summary") or r.get("summary"),
                      "assignee": (f.get("assignee") or {}).get("name") or r.get("assignee"),
                      "reason": r.get("reason"), "source": r["_src"], "service": r.get("service"),
                      "root_cause": r.get("root_cause")})
    return {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"), "status": "fail" if mm else "pass", "mismatches": mm,
            "warnings": warn, "counts": c, "extra_notes": extra,
            "exit_criteria": [{"criterion": a, "met": b} for a, b in crit],
            "verdicts": {n: str(r.get("verdict")) for n, r in sorted(notes.items(), key=lambda x: nat(x[0]))},
            "rows": trows, "online": bool(get), "legacy": legacy}


def md(t):
    c = t["counts"]
    L = [f"# trace — {t['status'].upper()} ({t['generated']})", "",
         f"Keys verified online: {'yes' if t['online'] else 'NO (offline)'} · legacy mode: {t['legacy']}", "",
         "## Exit criteria"]
    L += [f"- [{'x' if e['met'] else ' '}] {e['criterion']}" for e in t["exit_criteria"]]
    L += ["", "## Counts (denominator = notes)", "| item | n |", "|---|---|"] + [f"| {k} | {v} |" for k, v in c.items()]
    L += ["", "## note -> key", "| note | verdict | rows |", "|---|---|---|"]
    byn = {}
    for r in t["rows"]:
        byn.setdefault(r["note"], []).append(f"{r['key'] or r['kind']} ({r['kind']})")
    for n, v in t["verdicts"].items():
        L.append(f"| {n} | {v} | {', '.join(byn.get(n, [])) or '-'} |")
    for n in t["extra_notes"]:
        L.append(f"| {n} | (not in notes) | {', '.join(byn.get(n, []))} |")
    L += ["", "## key -> notes", "| key | type | status | notes |", "|---|---|---|---|"]
    byk = {}
    for r in t["rows"]:
        if r["key"]:
            byk.setdefault(r["key"], [r["type"], r["status"], []])[2].append(r["note"])
    for k, (ty, st, ns) in byk.items():
        L.append(f"| {k} | {ty} | {st} | {', '.join(ns)} |")
    L += ["", "## mismatches"] + ([f"- {m}" for m in t["mismatches"]] or ["none"])
    if t["warnings"]:
        L += ["", "## warnings"] + [f"- {m}" for m in t["warnings"]]
    return "\n".join(L) + "\n"


def selftest():
    import _fixture as fx
    with tempfile.TemporaryDirectory() as tmp:
        p = fx.write(tmp)
        t = run(p["results"], p["filed"], fx.mock_get)
        c = t["counts"]
        assert t["status"] == "pass", t["mismatches"]
        assert (c["notes"], c["fixed"], c["not_fixed"], c["untestable"]) == (27, 10, 11, 6), c
        assert (c["new_bugs"], c["blocker"], c["tasks"], c["new_total"], c["existing"]) == (9, 1, 6, 16, 3), c
        assert c["bugs_incl_blocker"] == 10 and all(e["met"] for e in t["exit_criteria"])
        # the v1 header "10 Bugs + 6 Tasks + 1 blocker" = 17 must be flagged
        t2 = run(p["results"], p["filed"], fx.mock_get, {"bugs": 10, "tasks": 6, "blocker": 1, "new_total": 17})
        assert t2["status"] == "fail" and sum("claim" in m for m in t2["mismatches"]) == 2 and not any("not a reconcile" in m for m in t2["mismatches"]), t2["mismatches"]
        assert run(p["results"], p["filed"], fx.mock_get,
                   {"bugs_incl_blocker": 10, "tasks": 6, "blocker": 1, "new_total": 16})["status"] == "pass"
        # negative cases
        d = fx.results(); d["notes"]["N5"]["verdict"] = "partial"; json.dump(d, open(p["results"], "w"))
        assert any("N5" in m for m in run(p["results"], p["filed"], fx.mock_get)["mismatches"])
        json.dump(fx.results(), open(p["results"], "w"))
        L4 = json.load(open(p["files"][3]))
        L4["N7"]["key"] = "PROJ-1034"; json.dump(L4, open(p["files"][3], "w"))
        assert any("PROJ-1034: GET returned 404" in m for m in run(p["results"], p["filed"], fx.mock_get)["mismatches"])
        L4["N7"]["key"] = "PROJ-1019"; json.dump(L4, open(p["files"][3], "w"))
        m = run(p["results"], p["filed"], fx.mock_get)["mismatches"]
        assert any("claimed by more than one row" in x for x in m) and any("type Bug, expected Task" in x for x in m), m
        L4["N7"]["key"] = "PROJ-1026"; del L4["N29"]; json.dump(L4, open(p["files"][3], "w"))
        assert any("N29: untestable with no Task" in x for x in run(p["results"], p["filed"], fx.mock_get)["mismatches"])
        assert "| N17 | not-fixed | PROJ-1018 (bug) |" in md(t)
        # fix 1: a NEW Bug a developer already closed as Not Bug / Duplicate / Won't Do is a mismatch, not a pass
        L4["N29"] = {"note": "N29", "action": "created", "key": "PROJ-1031", "anchor": "BPMN timer node", "assignee": "jane.doe"}; json.dump(L4, open(p["files"][3], "w"))
        def over(key, **fl):
            def g(path):
                st, d = fx.mock_get(path)
                if d and path.split("/issue/")[-1].startswith(key + "?"):
                    d["fields"].update(fl)
                return st, d
            g.user = fx.mock_get.user
            return g
        for fl in ({"status": {"name": "Not Bug"}}, {"resolution": {"name": "Duplicate"}}, {"status": {"name": "Won't Do"}}):
            m = run(p["results"], p["filed"], over("PROJ-1018", **fl))["mismatches"]
            assert any("PROJ-1018: new ticket is already" in x for x in m), (fl, m)
        L1 = json.load(open(p["files"][0])); L1["rows"][2]["reopened"] = True; json.dump(L1, open(p["files"][0], "w"))
        r = run(p["results"], p["filed"], over("PROJ-1016", status={"name": "Not Bug"}))
        assert r["status"] == "pass", r["mismatches"]  # reopened:true after the owner re-rules
        # fix 3: every tracker shape loads (dict notes / list / {rows} / {tickets})
        base = fx.results()["notes"]
        for shape in (base, list(base.values()), {"rows": list(base.values())}, {"tickets": base}, {"notes": list(base.values())}):
            json.dump(shape, open(p["results"], "w"))
            assert run(p["results"], p["filed"], fx.mock_get)["counts"]["notes"] == 27, shape
        json.dump(fx.results(), open(p["results"], "w"))
        # fix 4: two Bugs on one root cause are refused; one merged row (also: [...]) passes and covers every note
        L3 = json.load(open(p["files"][2]))
        for n in ("N17", "N18"): L3[n]["root_cause"] = "RC-sanad"
        json.dump(L3, open(p["files"][2], "w"))
        m = run(p["results"], p["filed"], fx.mock_get)["mismatches"]
        assert any("root cause 'RC-sanad' filed as 2 Bugs" in x for x in m), m
        L3["N17"]["also"] = ["N18"]; del L3["N18"]; json.dump(L3, open(p["files"][2], "w"))
        t3 = run(p["results"], p["filed"], fx.mock_get)
        assert t3["status"] == "pass" and t3["counts"]["new_bugs"] == 8, t3["mismatches"]
    print("reconcile selftest: PASS (fixture 27 notes -> 9 bugs + 1 blocker + 6 tasks = 16 new, 3 existing; "
          "v1 header 10+6+1=17 flagged; 4 negative cases caught; new Bug Not Bug/Duplicate/Won't Do refused, reopened exempt; "
          "5 tracker shapes load; 2 Bugs on one root cause refused, merged row passes)")


def main():
    utf8()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results"); ap.add_argument("--filed"); ap.add_argument("--out"); ap.add_argument("--creds")
    ap.add_argument("--claim", action="append", default=[]); ap.add_argument("--legacy", action="store_true")
    ap.add_argument("--offline", action="store_true"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.results and a.filed and a.out):
        ap.error("--results, --filed and --out are required")
    get = None if a.offline else jira_get(load_creds(a.creds))
    t = run(a.results, a.filed, get, dict(x.split("=", 1) for x in a.claim), a.legacy)
    os.makedirs(a.out, exist_ok=True)
    json.dump(t, open(os.path.join(a.out, "trace.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(a.out, "trace.md"), "w", encoding="utf-8").write(md(t))
    c = t["counts"]
    print(f"reconcile: {t['status'].upper()} · notes {c['notes']} · new {c['new_total']} "
          f"(bugs {c['new_bugs']} + blocker {c['blocker']} + tasks {c['tasks']}) · existing {c['existing']}")
    for m in t["mismatches"]:
        print("MISMATCH:", m)
    for m in t["warnings"]:
        print("warning:", m)
    sys.exit(1 if t["mismatches"] else 0)


if __name__ == "__main__":
    main()
