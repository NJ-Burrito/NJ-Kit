#!/usr/bin/env python3
"""Apply a tashkeel checker's fixes JSON to narration.ar.json `ttsAr` (stdlib only, no model call).

Usage: PYTHONUTF8=1 python tashkeel_fix_apply.py narration.ar.json fixes.json [--out PATH] [--dry-run]
       python tashkeel_fix_apply.py --selftest
       python tashkeel_fix_apply.py narration.ar.json --stamp     (checker passed with zero fixes)
Receipt (the owner 2026-10-03): a real apply, or --stamp, writes narration.ar.checked.json beside the sidecar:
{"date","fixes","steps":{step id: sha256 of ttsAr}}; flagged steps and a run with any refusal get no receipt. The PROJ
build refuses to voice (cache miss only) an Arabic line whose ttsAr sha is not in it.
Fix entry: {"step","word_before","word_after","rule","why"}; uncertain: {"step","flag":"<note>"} (never applied).
Refused: no/unknown rule, bare letters differ, word_before not found exactly once (whole word) in that step.
Exit 0 = nothing refused, 1 = something refused. Visible `text` is never touched.
"""
import datetime, hashlib, json, os, re, sys, unicodedata

RULES = {f"R-TASHKEEL-{n:03d}" for n in (1, 2, 3, 4, 7, 8, 9)}  # 005/006 retired 2026-10-03
AR = "ء-يٱ-ۓً-ْٰ"  # letters + marks


def rule_ok(r):
    # KB id, or a named proofreading rule written PROOF:<name>
    return isinstance(r, str) and (r in RULES or (r.startswith("PROOF:") and len(r) > 6))


def bare(s):
    return "".join(c for c in unicodedata.normalize("NFC", s) if unicodedata.category(c) != "Mn")


def apply(narr, fixes):
    """Mutates narr; returns [(status, step, detail)]."""
    rows = []
    for f in fixes:
        step = f.get("step")
        if "flag" in f:
            rows.append(("flagged", step, str(f["flag"])))
            continue
        b, a, rule = f.get("word_before"), f.get("word_after"), f.get("rule")
        why = None
        if not rule_ok(rule):
            why = f"no/unknown rule {rule!r}"
        elif step not in narr or "ttsAr" not in narr[step]:
            why = "unknown step"
        elif not b or not a or b == a:
            why = "empty or unchanged word"
        elif bare(b) != bare(a):
            why = "bare letters differ"
        else:
            pat = re.compile(f"(?<![{AR}]){re.escape(b)}(?![{AR}])")
            n = len(pat.findall(narr[step]["ttsAr"]))
            if n != 1:
                why = f"word_before found {n}x"
        if why:
            rows.append(("refused", step, f"{b} -> {a}: {why}"))
        else:
            narr[step]["ttsAr"] = pat.sub(lambda m: a, narr[step]["ttsAr"], count=1)
            rows.append(("applied", step, f"{b} -> {a} [{rule}]"))
    return rows


def selftest():
    n = {"s1": {"text": "x", "ttsAr": "ذَهَبَ الْوَلَدُ إِلَى الْمَدْرَسَةِ وَالْوَلَدُ"}}
    ok = {"step": "s1", "word_before": "ذَهَبَ", "word_after": "ذَهَبُ", "rule": "R-TASHKEEL-003"}
    assert apply(n, [ok])[0][0] == "applied" and n["s1"]["ttsAr"].startswith("ذَهَبُ")
    m = {"s1": {"ttsAr": "ذَهَبَ الْوَلَدُ"}}
    r = lambda **k: apply(json.loads(json.dumps(m)), [{"step": "s1", **k}])[0][0]
    assert r(word_before="ذَهَبَ", word_after="ذَهَبُ") == "refused"  # no rule
    assert r(word_before="ذَهَبَ", word_after="ذَهَبُ", rule="R-TASHKEEL-005") == "refused"  # retired
    assert r(word_before="ذَهَبَ", word_after="ذَهَبُ", rule="R-X") == "refused"
    assert r(word_before="ذَهَبَ", word_after="رَجَعَ", rule="R-TASHKEEL-003") == "refused"  # letters differ
    assert r(word_before="غَيْرِي", word_after="غَيْرُي", rule="R-TASHKEEL-003") == "refused"  # not found
    assert r(word_before="الْوَلَدُ", word_after="الْوَلَدَ", rule="PROOF:case") == "applied"
    dup = {"s1": {"ttsAr": "الْوَلَدُ وَالْوَلَدُ الْوَلَدُ"}}
    assert apply(dup, [{"step": "s1", "word_before": "الْوَلَدُ", "word_after": "الْوَلَدَ", "rule": "R-TASHKEEL-003"}])[0][0] == "refused"  # 2 whole-word hits
    sub = {"s1": {"ttsAr": "وَالْوَلَدُ"}}  # substring of a longer word must not match
    assert apply(sub, [{"step": "s1", "word_before": "الْوَلَدُ", "word_after": "الْوَلَدَ", "rule": "R-TASHKEEL-003"}])[0][0] == "refused"
    assert apply(m, [{"step": "s1", "flag": "unsure"}])[0][0] == "flagged"
    print("selftest ok")


def write_receipt(narr_path, narr, fixes_path, flagged):
    sha = lambda t: hashlib.sha256(t.encode("utf-8")).hexdigest()  # noqa: E731
    steps = {k: sha(v["ttsAr"]) for k, v in narr.items() if "ttsAr" in v and k not in flagged}
    out = os.path.join(os.path.dirname(os.path.abspath(narr_path)), "narration.ar.checked.json")
    rec = {"date": datetime.date.today().isoformat(), "fixes": fixes_path or "stamp (zero fixes)", "steps": steps}
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, ensure_ascii=False, indent=2)
        fh.write(chr(10))
    print(f"receipt: {out} ({len(steps)} steps)")


def main(argv):
    if "--selftest" in argv:
        return selftest() or 0
    args = [x for x in argv if not x.startswith("--")]
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    if out:
        args.remove(out)
    stamp = "--stamp" in argv
    narr_path = args[0]
    fixes_path = args[1] if len(args) > 1 else None
    if not stamp and not fixes_path:
        print(__doc__)
        return 1
    narr = json.load(open(narr_path, encoding="utf-8"))
    fixes = json.load(open(fixes_path, encoding="utf-8")) if fixes_path else []
    rows = apply(narr, fixes)
    for s, st, d in rows:
        print(f"{s:8} | {st} | {d}")
    cnt = {k: sum(r[0] == k for r in rows) for k in ("applied", "refused", "flagged")}
    print(cnt)
    if "--dry-run" not in argv and cnt["applied"]:
        with open(out or narr_path, "w", encoding="utf-8") as fh:
            json.dump(narr, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    if "--dry-run" not in argv and not cnt["refused"] and (stamp or fixes_path):
        write_receipt(out or narr_path, narr, fixes_path, {st for s, st, _ in rows if s == "flagged"})
    return 1 if cnt["refused"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
