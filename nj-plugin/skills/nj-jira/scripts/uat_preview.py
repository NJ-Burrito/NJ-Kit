"""UAT notes -> notes.md + preview.html + bugs-<svc>.json (standard 2026-10-22, references/uat-notes-standard.md).

usage: PYTHONUTF8=1 python uat_preview.py DATA.(json|py) [--out DIR]

DATA keys: title (page title), round ("UAT2"), round_desc, default_tab (index), services, results, extra
 (in a .py module: TITLE, ROUND, ROUND_DESC, DEFAULT_TAB, SERVICES, RESULTS, EXTRA).
 services: [{key, title, jira_name?, notes:["📄 screen header" | (id, severity, priority, defect, where, steps[], expected, source)]}]
   severity Blocker|Major|Minor ; priority High|Medium|Low (Jira names; Blocker is always filed as Critical)
 results : {svc: {note id: (state fail|pass, actual, [evidence files under evidence/<svc>/])}} ; missing id = not checked
 extra   : {svc: [note-tuple(8) + (state, actual, [files])]}  new findings outside the email notes (ids <svc>-N<n>)
refs    : {note id: {doc, page, item, quote[, related:[{page,item,quote}]]}} source reference (the owner 2026-10-25) -> the last Bug block
           «📄 المرجع» + a line in the Task + the preview. quote = verbatim from the source docx (python-docx), page from its PDF export.
           New finding (no doc): {session, evidence, quote} (quote = the owner's verbatim line). No ref => no block.
Evidence paths in the output are relative to --out (default: the data file's folder).
"""
import html, importlib.util, json, pathlib, sys

esc = html.escape
SEV_AR = {"Blocker": "🔴 يوقف الطلب", "Major": "🟠 رئيسي", "Minor": "⚪ بسيط"}
KEYS = ("TITLE", "ROUND", "ROUND_DESC", "DEFAULT_TAB", "SERVICES", "RESULTS", "EXTRA", "REFS")


def load(path):
    p = pathlib.Path(path)
    if p.suffix == ".json":
        m = json.loads(p.read_text(encoding="utf-8"))
    else:
        spec = importlib.util.spec_from_file_location("uat_data", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        m = {k.lower(): getattr(mod, k) for k in KEYS if hasattr(mod, k)}
    d = {"title": "ملاحظات UAT", "round": "UAT", "round_desc": "جلسة قبول المستخدم", "default_tab": 0,
         "services": [], "results": {}, "extra": {}, "refs": {}}
    d.update(m)
    for s in d["services"]:
        s["notes"] = [n if isinstance(n, str) else tuple(n) for n in s["notes"]]
    d["results"] = {k: {i: tuple(r) for i, r in v.items()} for k, v in d["results"].items()}
    for k, extra in d["extra"].items():
        s = next(x for x in d["services"] if x["key"] == k)
        s["notes"] += ["🆕 ملاحظات جديدة من الفحص (خارج البريد)"] + [tuple(e[:8]) for e in extra]
        d["results"].setdefault(k, {}).update({e[0]: tuple(e[8:]) for e in extra})
    d["extra"] = {}
    return d


def notes_of(s):
    return [n for n in s["notes"] if isinstance(n, tuple)]


def bug_summary(s, n):
    return f"«{s.get('jira_name', s['title'])}»: {n[3]}"


def ref_block(r):
    """Jira wiki «📄 المرجع» block (the 6th, last block of a notes-based Bug)."""
    q = lambda t: ["{quote}", *t.split("\n"), "{quote}"]
    L = ["h3. 📄 المرجع"]
    if r.get("doc"):
        L += [f"* *الوثيقة:* {r['doc']}", f"* *الموقع:* صفحة {r['page']} · البند {r['item']}", "* *نص الملاحظة كما ورد:*", *q(r["quote"])]
    else:
        L += ["* *الوثيقة:* لا يوجد (ملاحظة جديدة من الفحص)", f"* *المصدر:* {r['session']} · ملف الدليل {r['evidence']}", "* *نص الملاحظة كما ورد:*", *q(r["quote"])]
    for x in r.get("related", []):
        L += [f"* *ملاحظة ذات صلة:* صفحة {x['page']} · البند {x['item']}", *q(x["quote"])]
    return "\n".join(L)


def ref_html(r):
    if not r:
        return ""
    where = f"{esc(r['doc'])} · صفحة {esc(str(r['page']))} · البند {esc(r['item'])}" if r.get("doc") else f"{esc(r['session'])} · ملف الدليل {esc(r['evidence'])}"
    rel = "".join(f"<br>↪ ملاحظة ذات صلة: صفحة {esc(str(x['page']))} · البند {esc(x['item'])}" for x in r.get("related", []))
    return f'<p class="line ref">📄 <b>المرجع:</b> {where}{rel}<br><q style="white-space:pre-line">{esc(r["quote"])}</q></p>'


def bug_wiki(b, res=None, ref=None):
    _id, sev, pri, defect, where, steps, exp, src = b
    actual = res[1] if res and res[0] == "fail" else "⏳ يُعبّأ من نتيجة الاختبار"
    shots = [f"* {{{{{f}}}}}" for f in res[2]] if res and res[0] == "fail" else [f"* {{{{evidence/{_id}-<what-it-shows>.png}}}} ⏳"]
    return "\n".join(["h3. ❌ المشكلة", f"* {defect} — {where}", "",
                      "h3. 🔁 الخطوات", *[f"# {s}" for s in steps], "",
                      "h3. ✅ المتوقع", f"* {exp} ({src})", "",
                      "h3. ❌ الفعلي", f"* {actual}", "",
                      "h3. 🖼️ الدليل", *shots] + (["", ref_block(ref)] if ref else []))


def task_summary(s, d):
    return f"«{s['title']}»: اختبار ملاحظات {d['round']}"


def task_wiki(s, d):
    return "\n".join([f"h3. 🧪 اختبار ملاحظات {d['round']}",
                      f"* {len(notes_of(s))} ملاحظة من {d['round_desc']} على «{s['title']}»",
                      "",
                      "h3. 🐞 البلاغات", "* ⏳ PROJ-XXXX — سطر لكل بلاغ (Relates)"])


def task_notes_lines(s, d, filed=()):
    """Task 🧪 block body: one entry per note: icon, id, title, page+item, Bug key, verbatim quote (the owner 2026-10-25)."""
    keys = {o["id"]: o["key"] for o in filed}
    L = []
    for sc, n, res in sorted(items_of(s, d["results"]), key=lambda x: ("-N" in x[1][0], int(x[1][0].rsplit("-", 1)[-1].lstrip("N") or 0))):
        ic = "⏳" if not res else "✅" if res[0] == "pass" else "🆕" if "-N" in n[0] else "❌"
        r = d["refs"].get(n[0])
        where = ("" if not r else f" · ص{r['page']} · {r['item']}" if r.get("doc") else f" · {r['session']}")
        L.append(f"* {ic} {n[0]} — {n[3]}{where}" + (f" · {keys[n[0]]}" if n[0] in keys else ""))
        if r:
            L += ["{quote}", *r["quote"].split("\n"), "{quote}"]
    return L


def items_of(s, results):
    screen, items, r = "", [], results.get(s["key"], {})
    for n in s["notes"]:
        if isinstance(n, str):
            screen = n.split(" ", 1)[1] if n[:1] in "📄🪪📝🔎📃🔀👤🆕" else n
            continue
        items.append((screen, n, r.get(n[0])))
    return items


def counts(s, d):
    """-> total, fails, new-finding fails (id has -N), passes, todo"""
    it = items_of(s, d["results"])
    fails = [x for x in it if x[2] and x[2][0] == "fail"]
    return (len(it), fails, [x for x in fails if "-N" in x[1][0]],
            [x for x in it if x[2] and x[2][0] == "pass"], [x for x in it if not x[2]])


def cp(t, label):
    return f'<button class="cp" data-t="{esc(json.dumps(t, ensure_ascii=False))}">📋 {label}</button>'


def shots(key, files):
    return "".join(f'<video controls preload="metadata" src="evidence/{key}/{f}" title="{esc(f)}"></video>' if f.endswith((".mp4", ".webm"))
                   else f'<a href="evidence/{key}/{f}" target="_blank"><img src="evidence/{key}/{f}" alt="{esc(f)}"></a>' for f in files)


def jira_box(s, n, res, ref=None):
    bsum, wiki = bug_summary(s, n), bug_wiki(n, res, ref)
    return f'<details class="jira"><summary>📋 نص البلاغ للنسخ إلى Jira</summary><div class="row">{cp(bsum, "انسخ العنوان")} {cp(wiki, "انسخ الوصف")}</div><p class="sum">{esc(bsum)}</p><pre>{esc(wiki)}</pre></details>'


CSS = """:root{color-scheme:dark;--bg:#12161c;--card:#1b212a;--raise:#262e39;--fg:#f4f6f8;--mute:#ccd3dc;--line:#566273;--red:#ffb0a6;--redbg:#431a15;--green:#9de8ba;--greenbg:#12331f;--amber:#ffd98a;--amberbg:#3d2c09}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:18px/1.8 'Thmanyah Serif Text',serif;direction:rtl;text-align:right}
h1,h2,h3,h4{font-family:'Thmanyah Serif Display',serif;margin:.3em 0}
header{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:2px solid var(--line);padding:12px 16px}
header h1{font-size:22px}
.tabs{display:flex;gap:8px;flex-wrap:wrap}
.tab{color:var(--fg);font:inherit;font-size:16px;border:2px solid var(--line);background:var(--card);border-radius:12px;padding:6px 14px;cursor:pointer;display:flex;flex-direction:column;align-items:flex-start}
.tab small{color:var(--mute);font-size:16px}
.tab.on{border-color:var(--fg);background:var(--fg);color:var(--bg)} .tab.on small{color:var(--bg)}
main{max-width:1000px;margin:auto;padding:16px}
.panel{display:none} .panel.on{display:block}
.score{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:8px 0}
.s{border-radius:14px;padding:12px;text-align:center;font-size:17px} .s b{display:block;font-size:40px;line-height:1.1}
.s.fail{background:var(--redbg);color:var(--red)} .s.todo{background:var(--amberbg);color:var(--amber)} .s.pass{background:var(--greenbg);color:var(--green)}
.next{background:var(--card);border:2px dashed var(--line);border-radius:12px;padding:8px 14px}
.grp{margin:22px 0} .grp h3{font-size:22px} .n{background:var(--fg);color:var(--bg);border-radius:99px;padding:0 10px;font-size:16px}
.grp.fail h3{color:var(--red)} .grp.todo h3{color:var(--amber)} .grp.pass h3{color:var(--green)}
.card{background:var(--card);border:1px solid var(--line);border-inline-start:6px solid var(--line);border-radius:12px;padding:12px 16px;margin:12px 0}
.card.fail{border-inline-start-color:var(--red)} .card.pass{border-inline-start-color:var(--green)}
.meta{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.id{font-weight:700;direction:ltr;unicode-bidi:isolate;background:var(--raise);border-radius:6px;padding:0 8px;font-size:16px}
.pill{font-size:16px;background:var(--raise);border-radius:99px;padding:0 10px}
.big{font-size:20px;font-weight:700;margin:8px 0}
.line{margin:4px 0;font-size:16px}
.shots video{width:100%;max-width:520px;border-radius:8px;margin:4px;background:#000}
.shots img{height:120px;border:1px solid var(--line);border-radius:8px;margin:4px}
table.todo{width:100%;border-collapse:collapse;background:var(--card);font-size:16px}
.todo th{background:var(--amberbg);color:var(--amber);text-align:right;padding:8px;position:sticky;top:110px}
.todo td{border-top:1px solid var(--line);padding:8px;vertical-align:top}
.todo tr:nth-child(even) td{background:var(--raise)}
.todo .num{font-weight:700;color:var(--amber);text-align:center}
.jira summary,.task summary{cursor:pointer;color:var(--mute);font-size:16px}
.jira,.task{margin-top:8px}
.task{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 14px}
pre{white-space:pre-wrap;direction:rtl;text-align:right;background:var(--raise);border-radius:8px;padding:10px;font:16px/1.7 'Thmanyah Serif Text',serif}
.sum{font-weight:700;font-size:16px}
.cp{font:inherit;font-size:16px;border:1px solid var(--line);color:var(--fg);background:var(--raise);border-radius:8px;padding:2px 12px;cursor:pointer}
ol{margin:0;padding-inline-start:20px}
@media (max-width:700px){.s b{font-size:30px} .shots img{height:90px} .todo th{position:static}}"""

JS = """const T=[...document.querySelectorAll('.tab')],P=[...document.querySelectorAll('.panel')];
function show(i){T.forEach(t=>t.classList.toggle('on',t.dataset.i==i));P.forEach(p=>p.classList.toggle('on',p.dataset.i==i));try{localStorage.setItem('tab',i)}catch(e){}}
T.forEach(t=>t.onclick=()=>show(t.dataset.i));
let s=__DEFAULT__;try{s=localStorage.getItem('tab')||__DEFAULT__}catch(e){}
show(s);
document.querySelectorAll('.cp').forEach(b=>b.onclick=()=>{navigator.clipboard.writeText(JSON.parse(b.dataset.t));b.textContent='✅ نُسخ'});"""


def build(d, out):
    out = pathlib.Path(out)
    md = [f"# {d['title']} — notes by screen (generated by uat_preview.py; edit the data file)", ""]
    tabs, panels = [], []
    for i, s in enumerate(d["services"]):
        total, fails, _new, passes, todo = counts(s, d)
        if fails:  # filing payload, read by file_bugs.py
            (out / f"bugs-{s['key']}.json").write_text(json.dumps([
                {"id": n[0], "summary": bug_summary(s, n), "description": bug_wiki(n, res, d["refs"].get(n[0])), "severity": n[1], "priority": "Critical" if n[1] == "Blocker" else n[2],
                 "evidence": [f"evidence/{s['key']}/{f}" for f in res[2]]} for sc, n, res in fails], ensure_ascii=False, indent=1), encoding="utf-8")
        md.append(f"## {s['key']} — {s['title']} — ❌ {len(fails)} · ⏳ {len(todo)} · ✅ {len(passes)}")
        for sc, n, res in items_of(s, d["results"]):
            st = ({"fail": "❌", "pass": "✅"}[res[0]]) if res else "⏳"
            md.append(f"- {st} **{n[0]}** [{sc}] {n[3]}" + (f" — الفعلي: {res[1]}" if res else ""))
        md.append("")

        fail_html = "".join(f"""<article class="card fail"><div class="meta"><span class="id">{esc(n[0])}</span><span class="pill">{SEV_AR[n[1]]}</span><span class="pill">📍 {esc(sc)}</span></div>
<p class="big">{esc(n[3])}</p><p class="line"><b>✅ المطلوب:</b> {esc(n[6])}</p><p class="line"><b>❌ الموجود:</b> {esc(res[1])}</p>
<div class="shots">{shots(s['key'], res[2])}</div>{ref_html(d["refs"].get(n[0]))}{jira_box(s, n, res, d["refs"].get(n[0]))}</article>""" for sc, n, res in fails)
        pass_html = "".join(f"""<article class="card pass"><div class="meta"><span class="id">{esc(n[0])}</span><span class="pill">📍 {esc(sc)}</span></div>
<p class="line"><b>المطلوب:</b> {esc(n[6])}</p><p class="line"><b>✅ الموجود:</b> {esc(res[1])}</p>{ref_html(d["refs"].get(n[0]))}<div class="shots">{shots(s['key'], res[2])}</div></article>""" for sc, n, res in passes)
        rows = "".join(f"""<tr><td class="num">{k}</td><td><b>{esc(sc)}</b><br><span class="id">{esc(n[0])}</span></td><td>{esc(n[6])}{ref_html(d["refs"].get(n[0]))}</td><td><ol>{''.join(f'<li>{esc(x)}</li>' for x in n[5])}</ol></td></tr>"""
                       for k, (sc, n, res) in enumerate(todo, 1))
        todo_html = f'<table class="todo"><thead><tr><th>#</th><th>📍 الشاشة / المكتب</th><th>📌 الملاحظة (المطلوب)</th><th>🔍 ماذا تفحص بالضبط</th></tr></thead><tbody>{rows}</tbody></table>' if todo else ""
        task = f"""<details class="task"><summary>📌 تذكرة المهمة (Task) في Jira</summary><div class="row">{cp(task_summary(s, d), "انسخ العنوان")} {cp(task_wiki(s, d), "انسخ الوصف")}</div><pre>{esc(task_wiki(s, d))}</pre></details>"""

        def sec(cls, icon, title, cnt, body):
            return f'<section class="grp {cls}"><h3>{icon} {title} <span class="n">{cnt}</span></h3>{body}</section>' if cnt else ""
        tabs.append(f'<button class="tab" data-i="{i}">{esc(s["title"])}<small>❌ {len(fails)} · ⏳ {len(todo)} · ✅ {len(passes)}</small></button>')
        panels.append(f"""<div class="panel" data-i="{i}">
<div class="score"><div class="s fail"><b>{len(fails)}</b>❌ تحتاج بلاغ</div><div class="s todo"><b>{len(todo)}</b>⏳ لم تُفحص</div><div class="s pass"><b>{len(passes)}</b>✅ مُصلَحة</div></div>
<p class="next">👉 <b>الخطوة التالية:</b> {"افحص جدول ⏳ بالترتيب من الأعلى" if todo else "كل البنود فُحصت — جاهز لرفع البلاغات"}</p>
{sec("todo", "⏳", "لم تُفحص بعد — بترتيب الشاشات", len(todo), todo_html)}
{sec("fail", "❌", "تحتاج بلاغ", len(fails), fail_html)}
{sec("pass", "✅", "مُصلَحة (من صورك)", len(passes), pass_html)}
{task}</div>""")

    t = esc(d["title"])
    page = (f'<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{t}</title>\n'
            f'<style>\n{CSS}\n</style></head><body>\n<header><h1>{t}</h1><div class="tabs">{"".join(tabs)}</div></header>\n'
            f'<main>{"".join(panels)}</main>\n<script>\n{JS.replace("__DEFAULT__", str(int(d["default_tab"])))}\n</script></body></html>')
    (out / "preview.html").write_text(page, encoding="utf-8")
    (out / "notes.md").write_text("\n".join(md), encoding="utf-8")
    return [len(notes_of(s)) for s in d["services"]]


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        sys.exit(__doc__)
    out = pathlib.Path(a[a.index("--out") + 1]) if "--out" in a else pathlib.Path(a[0]).resolve().parent
    out.mkdir(parents=True, exist_ok=True)
    print("notes per service:", build(load(a[0]), out), "->", out)
