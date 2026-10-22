#!/usr/bin/env python3
"""nj-wrapup gate: render boss emails (AR + EN), the QA-team message and the nj-rank titles ONLY from a
passing trace.json (reconcile.py), then lint them. Refuses (exit 1) if the trace is missing, failed, offline,
stale, or any lint rule fires. Nothing is written when it refuses.

  PYTHONUTF8=1 python render.py --trace trace.json --context context.json --out DIR
        [--copy-to DESKTOP_DIR] [--max-age-min 180] [--recheck [--creds FILE]] | --selftest | --lint FILE [--deny word,...]
  PYTHONUTF8=1 python render.py --work-summary work.json --out DIR [--copy-to DESKTOP_DIR]    (non-testing session: no trace)

--recheck: GET every new key again at render time; a key whose live status is Not Bug/Duplicate/Won't Do refuses the render.
Years typed in outward text must be the session year or appear in a cited ticket summary (the v1 email said 2031, Jira 2027).
work.json (non-testing work; same lint, AR numbers == EN numbers, <= 12 lines): {"title":{"ar","en"},"date",
   "done":[{"ar","en"}], "outputs":[{"ar","en"}], "open":[{"ar","en"}], "needs":[{"ar","en","date"}],
   "recipient": null | "name"  (an email form, with subject + sign-off, only when a recipient is named),
   "rank_items":[{"work_type","title"}], "deny":[]}

context.json (all free text comes from here; every count comes from the trace):
  {"ticket","service_ar","service_en","env","date",
   "lines":   {"KEY": {"ar": "...", "en": "..."}},          one-line defect per new key
   "blocker": {"ar": "...", "en": "..."},                   one plain line, no endpoint/status/body
   "risk":    {"ar": "...", "en": "..."},                   residual risk (optional)
   "services": [{"id": "svc", "ar": "...", "en": "..."}],   multi-service run: filed rows carry "service": id; one line per service
   "needs":   [{"ar": "who: what", "en": "who: what", "date": "YYYY-MM-DD" | null}],   max 5
   "outputs": [{"ar": "...", "verdict": "print|print-known-defect|do-not-print", "stage": "final|draft|preview",
                "filed_this_session": true, "key": "KEY"}],
   "rank_items": [{"work_type": "segment", "title": "..."}],
   "deny": ["extra words that must not appear outward"]}
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, re, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import utf8, nat, load_creds, jira_get
from reconcile import NEG

MAX_LINES = 35
LINT = [  # (name, regex) -- anything that must never reach the boss or the QA team
    ("url", r"https?://|www\."), ("api-path", r"/(?:services|rest|api|callback)/[\w\-/.]+"),
    ("file-path", r"[A-Za-z]:\\|\\\\|\b[\w\-]+\.(?:png|pdf|json|txt|ts|py|md|html)\b"),
    ("request-serial", r"\b\d{9,}\b"), ("http-status", r"\b[45]\d\d\b"), ("raw-error-body", r"[{}]|\b[A-Z]{3,}_[A-Z_]{3,}\b"),
    ("token", r"\b[A-Za-z0-9_\-]{32,}\b|eyJ"), ("test-account", "|".join(re.escape(t.strip()) for t in os.environ.get("NJ_LEAK_TERMS", "").split(",") if t.strip()) or r"(?!)"),
    ("internal-wording", r"(?i)not bug risk|\bconflict\b|\binferred\b")]
VERDICT_WORD = {"print": "اطبع", "print-known-defect": "اطبع مع العلم بالخلل", "do-not-print": "لا تطبع"}


def lint(text, deny=()):
    out = []
    for name, rx in LINT:
        for m in re.finditer(rx, text):
            out.append(f"{name}: «{m.group(0)}»")
    for w in deny:
        if w and w.lower() in text.lower():
            out.append(f"deny-list: «{w}»")
    return out


def nums(text):
    t = re.sub(r"PROJ-\d+|[مN]\d+|\d{2}:\d{2}|\d{4}-\d{2}-\d{2}", " ", text)
    return sorted(re.findall(r"\d+", t.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))), key=int)


def trace_gate(t, max_age):
    if t.get("status") != "pass":
        return "trace status is not pass"
    if not t.get("online"):
        return "trace was not verified online (keys not GET-checked)"
    age = (dt.datetime.now() - dt.datetime.fromisoformat(t["generated"])).total_seconds() / 60
    return f"trace is {age:.0f} min old (max {max_age}); run reconcile again so keys are re-GET at send time" if age > max_age else None


def build(t, ctx):
    c, rows = t["counts"], t["rows"]
    N, nb, bl, nt, ne = c["notes"], c["new_bugs"], c["blocker"], c["tasks"], c["existing"]
    crit = t["exit_criteria"]
    met = sum(e["met"] for e in crit)
    unmet = [e["criterion"] for e in crit if not e["met"]]
    ready = not (c["not_fixed"] or c["untestable"] or c["blocked"] or bl or unmet)
    num = lambda n: re.sub(r"\D", "", n) if re.fullmatch(r"N\d+", str(n)) else str(n)
    def line(key, lang):
        v = ctx.get("lines", {}).get(key, {}).get(lang)
        return v or next((r["summary"] for r in rows if r["key"] == key and r["summary"]), key)
    def pick(kinds):
        seen, out = set(), []
        for r in sorted(rows, key=lambda r: nat(r["note"])):
            if r["kind"] in kinds and r["key"] and r["key"] not in seen:
                seen.add(r["key"]); out.append(r)
        return out
    fixed = sorted((num(n) for n, v in t["verdicts"].items() if v == "fixed"), key=nat)
    blk = next(iter(pick(("blocker",))), None)
    asof = t["generated"][11:16]
    needs = ctx.get("needs", [])[:5]
    L = {}
    for lang in ("ar", "en"):
        ar = lang == "ar"
        T = (lambda a, e: a if ar else e)
        n_ = lambda r: (T("م", "N") + num(r["note"])) if re.fullmatch(r"N\d+", str(r["note"])) else r["note"]
        lines = [
            T("النتيجة: ", "Result: ") + (T("جاهزة", "READY") if ready else T("غير جاهزة للانتقال إلى الخطوة التالية", "NOT READY to move to the next step")),
            T(f"من {N} ملاحظة: {c['fixed']} مُصلحة · {c['not_fixed']} لم تُصلح · {c['untestable']} غير قابلة للفحص · {c['blocked']} محجوبة",
              f"Of {N} notes: {c['fixed']} fixed · {c['not_fixed']} not fixed · {c['untestable']} untestable · {c['blocked']} blocked"),
            T("العائق: ", "Blocker: ") + (f"{blk['key']} — {ctx.get('blocker', {}).get(lang) or line(blk['key'], lang)}" if blk else T("لا يوجد", "none")),
            T(f"التذاكر الجديدة: {nb} Bug + {bl} عائق + {nt} Task = {c['new_total']} · {ne} موجود مسبقاً", f"New tickets: {nb} Bugs + {bl} blocker + {nt} Tasks = {c['new_total']} · {ne} already existing"),
            T(f"غير مغطّى بالفحص: {c['not_covered']} من {N} (غير قابلة للفحص + محجوبة)", f"Not covered by testing: {c['not_covered']} of {N} (untestable + blocked)"),
            T(f"معايير الخروج: {met} من {len(crit)} متحققة", f"Exit criteria: {met} of {len(crit)} met") + (" — " + "; ".join(unmet) if unmet else ""),
            ""]
        svcs = ctx.get("services") or []
        if svcs:
            lines.append(T(f"حسب الخدمة ({len(svcs)}):", f"By service ({len(svcs)}):"))
            for sv in svcs:
                ks = sorted({r["key"] for r in rows if r.get("service") == sv["id"] and r["kind"] in ("bug", "blocker", "task") and r["key"]}, key=nat)
                lines.append(f"• {sv[lang]} — " + (T(f"{len(ks)} تذكرة جديدة", f"{len(ks)} new tickets") if ks else T("لا تذاكر جديدة", "no new tickets")))
            lines.append("")
        bugs = pick(("bug",))
        if bugs:
            lines += [T(f"Bugs جديدة ({nb}):", f"New Bugs ({nb}):")] + [f"• {r['key']} — {n_(r)}: {line(r['key'], lang)}" for r in bugs]
        ex = pick(("existing",))
        if ex:
            lines.append(T(f"موجودة مسبقاً ({ne}، لم تُكرَّر): ", f"Already reported ({ne}, not duplicated): ") + " · ".join(f"{r['key']} ({n_(r)})" for r in ex))
        tk = pick(("task",))
        if tk:
            lines.append(T(f"Tasks للمطوّر ({nt}): ", f"Tasks for the developer ({nt}): ") + " · ".join(f"{n_(r)} {r['key']}" for r in tk))
        lines.append(T(f"مُصلحة ({c['fixed']}): ", f"Fixed ({c['fixed']}): ") + " · ".join(fixed))
        risk = ctx.get("risk", {}).get(lang) or T("لا شيء مسجَّل", "none recorded")
        if c["held"]:
            risk += T(f" · {c['held']} قيد التحقق الداخلي", f" · {c['held']} under internal review")
        lines.append(T("المخاطر المتبقية: ", "Residual risk: ") + risk)
        if needs:
            lines.append(T("ما يلزم:", "What is needed:"))
            for n in needs:
                d = n.get("date") or ""
                lines.append("• " + n[lang] + " — " + (T("الموعد: ", "Date: ") + d if d else T("الموعد: لم يُحدَّد — أحتاج تحديده", "Date: not set — needs to be set")))
        lines += ["", T(f"الحالة حتى {asof} على {ctx['env']}.", f"Status as of {asof} on {ctx['env']}."), T("المالك", "the owner")]
        sv_ar = " + ".join(s_["ar"] for s_ in svcs) if svcs else ctx["service_ar"]
        sv_en = " + ".join(s_["en"] for s_ in svcs) if svcs else ctx["service_en"]
        subj = T(f"نتائج فحص {ctx['ticket']} — {sv_ar} — {c['new_total']} تذكرة جديدة" + (f" (منها {bl} عائق)" if bl else ""),
                 f"Test results {ctx['ticket']} — {sv_en} — {c['new_total']} new tickets" + (f" ({bl} blocker)" if bl else ""))
        L[lang] = (subj, lines)
    return L


def qa_message(t, ctx):
    keys = {r["key"] for r in t["rows"] if r["key"]}
    outs, errs = ctx.get("outputs", []), []
    for o in outs:
        if o["verdict"] not in VERDICT_WORD:
            errs.append(f"output verdict '{o['verdict']}' invalid")
        if o["verdict"] != "do-not-print":
            if o.get("stage") != "final" or not o.get("filed_this_session"):
                errs.append(f"«{o['ar']}»: only final-stage outputs of requests filed in this session may be printed")
        if o["verdict"] == "print-known-defect" and o.get("key") not in keys:
            errs.append(f"«{o['ar']}»: defect key {o.get('key')} is not in the trace")
    pr = [o for o in outs if o["verdict"] != "do-not-print"]
    lines = ["جاهز للطباعة" if pr else "لا يوجد ملف جاهز للطباعة حالياً",
             f"الخدمة: {ctx['service_ar']} — {ctx['ticket']} — {ctx['env']} — {ctx['date']}", ""]
    for o in outs:
        lines.append("• " + o["ar"] + " — " + VERDICT_WORD.get(o["verdict"], "؟") + (f": {o['key']}" if o["verdict"] == "print-known-defect" else ""))
    lines += ["", "ما المطلوب منكم الآن:"]
    lines.append(f"• اطبعوا {len(pr)} من {len(outs)} ملفات فقط، كما هو مبيَّن أعلاه." if pr else "• لا تطبعوا شيئاً الآن.")
    kd = sorted({o["key"] for o in outs if o["verdict"] == "print-known-defect"})
    lines.append("• لا شيء آخر قبل إصلاح " + " و".join(kd) + "؛ سيصلكم ما بعده فور الإصلاح." if kd else "• لا شيء آخر مطلوب حالياً.")
    return lines, errs


def render(t, ctx, max_age=180, get=None):
    why = trace_gate(t, max_age)
    if why:
        return None, [why]
    probs = []
    ids = {s_["id"] for s_ in ctx.get("services") or []}
    for r in t["rows"]:
        if ids and r["kind"] in ("bug", "blocker", "task") and r.get("service") not in ids:
            probs.append(f"{r['key']}: service '{r.get('service')}' is not in context.services")
        if get and r.get("key") and r["kind"] in ("bug", "blocker", "task"):  # re-GET at render time, not trace time
            st, d = get(f"/rest/api/2/issue/{r['key']}?fields=status,resolution")
            f = (d or {}).get("fields") or {}
            live = ((f.get("status") or {}).get("name") or "").lower(), ((f.get("resolution") or {}).get("name") or "").lower()
            if st != 200:
                probs.append(f"{r['key']}: live GET returned {st}")
            elif live[0] in NEG or live[1] in NEG:
                probs.append(f"{r['key']}: live status is now {live[0]}: the email would count a ticket a developer ruled out")
    L = build(t, ctx)
    deny = list(ctx.get("deny", [])) + [p for r in t["rows"] if r.get("assignee") for p in re.split(r"[._@]", r["assignee"].split("@")[0]) if len(p) > 3]
    keys = {r["key"] for r in t["rows"] if r["key"]}
    for key in ctx.get("lines", {}):
        if key not in keys:
            probs.append(f"context cites {key} which is not in the trace")
    okyears = {t["generated"][:4], str(ctx.get("date", ""))[:4]} | set(re.findall(r"(?<!-)\b20\d\d\b", " ".join(str(r.get("summary") or "") for r in t["rows"])))
    for lang, (subj, lines) in L.items():
        txt = "\n".join([subj] + lines)
        probs += [f"{lang}: {p}" for p in lint(txt, deny)]
        probs += [f"{lang}: year {y} is not the session year nor in a cited ticket summary" for y in sorted(set(re.findall(r"(?<!-)\b20\d\d\b", txt)) - okyears)]
        if len(lines) > MAX_LINES:
            probs.append(f"{lang}: {len(lines)} body lines > {MAX_LINES}")
        for k in re.findall(r"PROJ-\d+|[A-Z]+-\d+", txt):
            if k not in keys and k != ctx["ticket"]:
                probs.append(f"{lang}: cites {k} which is not in the trace")
        head = "\n".join(lines[:6])
        if not re.search(r"جاهز|READY", head) or not re.search(r"\d", lines[1]) or not re.search(r"العائق|Blocker", head) or not re.search(r"معايير|Exit", head):
            probs.append(f"{lang}: first 6 lines must carry verdict, counts, blocker and exit criteria")
    if nums("\n".join([L["ar"][0]] + L["ar"][1])) != nums("\n".join([L["en"][0]] + L["en"][1])):
        probs.append("AR and EN counts differ")
    for n in ctx.get("needs", []):
        if not (n.get("ar") and n.get("en")):
            probs.append("a «needs» entry lacks AR or EN text")
    if len(ctx.get("needs", [])) > 5:
        probs.append("more than 5 «needs» lines")
    qa, errs = qa_message(t, ctx)
    probs += errs + [f"qa: {p}" for p in lint("\n".join(qa), deny)]
    titles = []
    for it in ctx.get("rank_items", []):
        c = t["counts"]
        ti = (f"رفع النتائج إلى Jira: {c['bugs_incl_blocker']} Bugs (منها {c['blocker']} عائق) + {c['tasks']} Tasks"
              if it["work_type"] == "jira-filing" else it["title"])
        titles.append({"work_type": it["work_type"], "title": ti})
    if probs:
        return None, probs
    return {"email-ar.txt": "الموضوع: " + L["ar"][0] + "\n\n" + "\n".join(L["ar"][1]) + "\n",
            "email-en.txt": "Subject: " + L["en"][0] + "\n\n" + "\n".join(L["en"][1]) + "\n",
            "qa-message-ar.txt": "\n".join(qa) + "\n",
            "rank-titles.json": json.dumps(titles, ensure_ascii=False, indent=1)}, []


def work_summary(w):
    """Non-testing session: no trace, no Jira counts. Counts are list lengths; same lint, parity, line cap."""
    probs, L = [], {}
    for lang in ("ar", "en"):
        ar = lang == "ar"
        T = (lambda a, e: a if ar else e)
        g = lambda k: [x[lang] for x in w.get(k) or [] if x.get(lang)]
        lines = [f"{w['title'][lang]} — {w['date']}",
                 T(f"أُنجز ({len(g('done'))}): ", f"Done ({len(g('done'))}): ") + " · ".join(g("done"))]
        if w.get("outputs"):
            lines.append(T(f"المخرجات ({len(g('outputs'))}): ", f"Outputs ({len(g('outputs'))}): ") + " · ".join(g("outputs")))
        lines.append(T(f"مفتوح ({len(g('open'))}): ", f"Open ({len(g('open'))}): ") + (" · ".join(g("open")) or T("لا شيء", "none")))
        for n in (w.get("needs") or [])[:5]:
            d = n.get("date") or ""
            lines.append(T("يلزم: ", "Needed: ") + n[lang] + " — " + (T("الموعد: ", "Date: ") + d if d else T("الموعد: لم يُحدَّد — أحتاج تحديده", "Date: not set — needs to be set")))
        if w.get("recipient"):
            lines += ["", T("المالك", "the owner")]
        L[lang] = lines
    deny = list(w.get("deny", []))
    for lang, lines in L.items():
        txt = "\n".join(lines)
        probs += [f"{lang}: {p}" for p in lint(txt, deny)]
        probs += [f"{lang}: year {y} is not the session year" for y in sorted(set(re.findall(r"(?<!-)\b20\d\d\b", txt)) - {str(w["date"])[:4]})]
        if len(lines) > 12:
            probs.append(f"{lang}: {len(lines)} lines > 12 (a work summary is a short note)")
    if nums("\n".join(L["ar"])) != nums("\n".join(L["en"])):
        probs.append("AR and EN counts differ")
    if len(w.get("needs") or []) > 5:
        probs.append("more than 5 «needs» lines")
    for it in w.get("rank_items") or []:
        if it.get("work_type") == "jira-filing":
            probs.append("jira-filing rank item needs a trace: a work summary files no Jira tickets")
    if probs:
        return None, probs
    pre = (lambda lang, subj: f"{'الموضوع' if lang == 'ar' else 'Subject'}: {subj}\n\n") if w.get("recipient") else (lambda *_: "")
    return {"work-summary-ar.txt": pre("ar", w["title"]["ar"]) + "\n".join(L["ar"]) + "\n",
            "work-summary-en.txt": pre("en", w["title"]["en"]) + "\n".join(L["en"]) + "\n",
            "rank-titles.json": json.dumps(w.get("rank_items") or [], ensure_ascii=False, indent=1)}, []


def selftest():
    import _fixture as fx, reconcile
    with tempfile.TemporaryDirectory() as tmp:
        p = fx.write(tmp)
        t = reconcile.run(p["results"], p["filed"], fx.mock_get)
        t["online"] = True
        ctx = {"ticket": "PROJ-997", "service_ar": "إجازة تداول مستحضر تجميلي", "service_en": "Cosmetic product marketing permit",
               "env": "Staging", "date": "2026-10-15",
               "lines": {"PROJ-2087": {"ar": "عبارة المهلة غير موجودة في البطاقة", "en": "The grace-period sentence is missing from the card"}},
               "blocker": {"ar": "فشل التوقيع الرقمي عند المدير العام ويمنع الموافقة النهائية", "en": "Digital signing fails at the General Manager and blocks final approval"},
               "needs": [{"ar": "المطوّر: إصلاح العائق أولاً", "en": "Developer: fix the blocker first", "date": None}],
               "outputs": [{"ar": "كتاب الموافقة الموقّع", "verdict": "print-known-defect", "stage": "final", "filed_this_session": True, "key": "PROJ-2088"},
                           {"ar": "معاينة رئيس القسم", "verdict": "do-not-print", "stage": "preview", "filed_this_session": True}],
               "rank_items": [{"work_type": "jira-filing", "title": "x"}, {"work_type": "segment", "title": "فحص البوابة"}]}
        files, probs = render(t, ctx)
        assert not probs, probs
        ar, en = files["email-ar.txt"], files["email-en.txt"]
        assert len(ar.splitlines()) <= MAX_LINES + 3 and "9 Bug + 1 عائق + 6 Task = 16" in ar and "9 Bugs + 1 blocker + 6 Tasks = 16" in en and "Of 27 notes" in en
        assert "10 Bugs (منها 1 عائق) + 6 Tasks" in files["rank-titles.json"] and "اطبع مع العلم بالخلل: PROJ-2088" in files["qa-message-ar.txt"]
        # refusals
        assert render(dict(t, status="fail"), ctx)[1] == ["trace status is not pass"]
        assert "not verified online" in render(dict(t, online=False), ctx)[1][0]
        old = dict(t, generated="2020-01-01T00:00:00")
        assert "min old" in render(old, ctx)[1][0]
        # the v1 boss email carried an endpoint, a status+error body, serials, a personal name; the v1 QA message carried an account name
        v1 = ("الخطأ: GET /services/general/sanad-auth/callback/sign_auth → 500 {\"error\":\"SIGNING_FAILED\"}\n"
              "الطلب 123456789012 — المعيّن: assignee-name — الحساب test-account-name — C:\\Users\\x\\a.png")
        found = {x.split(":")[0] for x in lint(v1, ["assignee-name", "test-account-name"])}
        assert {"api-path", "http-status", "raw-error-body", "request-serial", "deny-list", "file-path"} <= found, found
        # lint hits inside the context are caught before anything is written
        bad = json.loads(json.dumps(ctx)); bad["blocker"]["en"] += " (500 SIGNING_FAILED)"
        assert any("http-status" in x for x in render(t, bad)[1])
        # an unprintable output cannot be marked print
        bad = json.loads(json.dumps(ctx)); bad["outputs"][1]["verdict"] = "print"
        assert any("only final-stage" in x for x in render(t, bad)[1])
        # AR/EN count drift
        bad = json.loads(json.dumps(ctx)); bad["risk"] = {"ar": "٣ مخاطر", "en": "two risks"}
        assert any("counts differ" in x for x in render(t, bad)[1])
        # fix 7: year lint (v1 said 2031, Jira said 2027) and live re-GET (v1 counted 6 Bugs that were already Not Bug)
        t["rows"][5]["summary"] = "الخطأ في سنة 2027"
        bad = json.loads(json.dumps(ctx)); bad["risk"] = {"ar": "ينتهي في 2031", "en": "ends in 2031"}
        assert any("year 2031" in x for x in render(t, bad)[1])
        ok = json.loads(json.dumps(ctx)); ok["risk"] = {"ar": "ينتهي في 2027", "en": "ends in 2027"}
        assert not render(t, ok)[1]
        def live(key, name):
            def g(path):
                st, d = fx.mock_get(path)
                if key in path: d["fields"]["status"] = {"name": name}
                return st, d
            return g
        assert not render(t, ctx, get=live("PROJ-2089", "In QA"))[1]
        assert any("PROJ-2089: live status is now not bug" in x for x in render(t, ctx, get=live("PROJ-2089", "Not Bug"))[1])
        # multi-service: services[] drives the subject and a per-service block; a row from an unlisted service is refused
        tm = json.loads(json.dumps(t))
        for i, r in enumerate(tm["rows"]):
            r["service"] = "a" if i % 2 else "b"
        cm = dict(ctx, services=[{"id": "a", "ar": "خدمة أ", "en": "Service A"}, {"id": "b", "ar": "خدمة ب", "en": "Service B"}])
        f2, p2 = render(tm, cm)
        assert not p2 and "Service A + Service B" in f2["email-en.txt"] and "By service (2):" in f2["email-en.txt"] and "حسب الخدمة (2):" in f2["email-ar.txt"], p2
        next(r for r in tm["rows"] if r["kind"] == "bug")["service"] = "zzz"
        assert any("not in context.services" in x for x in render(tm, cm)[1])
        # fix 6: non-testing session renders from work.json alone, same lint
        w = {"title": {"ar": "إعادة بناء مهارة الإغلاق", "en": "Wrap-up skill rebuild"}, "date": "2026-10-16",
             "done": [{"ar": "ثمانية إصلاحات", "en": "eight fixes"}], "outputs": [{"ar": "ملف المهارة", "en": "the skill folder"}],
             "open": [], "needs": [{"ar": "المالك: مراجعة", "en": "the owner: review", "date": None}],
             "rank_items": [{"work_type": "segment", "title": "إعادة بناء"}]}
        wf, wp = work_summary(w)
        assert not wp and len(wf["work-summary-en.txt"].splitlines()) <= 12 and "Subject" not in wf["work-summary-en.txt"], wp
        assert "Subject: Wrap-up skill rebuild" in work_summary(dict(w, recipient="boss"))[0]["work-summary-en.txt"]
        assert any("http-status" in x for x in work_summary(dict(w, open=[{"ar": "خطأ ٥٠٠ 500", "en": "error 500"}]))[1])
        assert any("year 2031" in x for x in work_summary(dict(w, open=[{"ar": "في 2031", "en": "in 2031"}]))[1])
        assert any("counts differ" in x for x in work_summary(dict(w, done=[{"ar": "ثلاثة 3", "en": "two 2"}]))[1])
        assert any("jira-filing" in x for x in work_summary(dict(w, rank_items=[{"work_type": "jira-filing", "title": "x"}]))[1])
    print("render selftest: PASS (emails AR+EN <=35 lines, parity ok, v1 leaks caught: endpoint/status/body/serial/name/<admin-user>/path, "
          "refuses failed/offline/stale trace, QA print rules, rank title 10 Bugs (1 blocker) + 6 Tasks; year 2031 vs 2027 refused, "
          "live Not Bug refused, multi-service subject+block, --work-summary renders without a trace and lints)")


def main():
    utf8()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trace"); ap.add_argument("--context"); ap.add_argument("--out"); ap.add_argument("--copy-to")
    ap.add_argument("--max-age-min", type=int, default=180); ap.add_argument("--lint"); ap.add_argument("--deny", default="")
    ap.add_argument("--selftest", action="store_true"); ap.add_argument("--work-summary"); ap.add_argument("--recheck", action="store_true")
    ap.add_argument("--creds")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.work_summary:
        if not a.out:
            ap.error("--out is required")
        files, probs = work_summary(json.load(open(a.work_summary, encoding="utf-8")))
        return emit(files, probs, a)
    if a.lint:
        pr = lint(open(a.lint, encoding="utf-8").read(), a.deny.split(","))
        print("\n".join(pr) or "lint: clean")
        sys.exit(1 if pr else 0)
    if not (a.trace and a.context and a.out):
        ap.error("--trace, --context and --out are required")
    if not os.path.exists(a.trace):
        sys.exit("render refused: trace.json missing (run reconcile.py first)")
    files, probs = render(json.load(open(a.trace, encoding="utf-8")), json.load(open(a.context, encoding="utf-8")), a.max_age_min,
                          jira_get(load_creds(a.creds)) if a.recheck else None)
    emit(files, probs, a)


def emit(files, probs, a):
    if probs:
        print("render refused:")
        for p in probs:
            print(" -", p)
        sys.exit(1)
    for d in filter(None, (a.out, a.copy_to)):
        os.makedirs(d, exist_ok=True)
        for n, s in files.items():
            if d == a.out or n.endswith(".txt"):
                open(os.path.join(d, n), "w", encoding="utf-8").write(s)
    print("render: wrote " + ", ".join(files) + f" to {a.out}" + (f" (+ .txt copies in {a.copy_to})" if a.copy_to else ""))


if __name__ == "__main__":
    main()
