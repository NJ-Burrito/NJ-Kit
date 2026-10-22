#!/usr/bin/env python3
"""selftest.py -- the portability proof: a toy book that differs from the QA book in EVERY constant. PYTHONUTF8=1 assumed.

    selftest.py [--keep]            exit 0 = every assertion ran and held
                                    exit 3 = all non-report assertions held but the report stage was SKIPPED
                                             (pandoc / node / Chrome / mmdc / poppler missing) -- never 0 then
                                    exit 1 = an assertion failed

Builds a temp BOOK_ROOT: db kb/toy.db, sectors eu,us, pages in chapters/, kinds regulation + topic and NO headings key,
no QA vocabulary, one mermaid fence, one glance row, an Arabic twin, a practice bank. A local HTTP server stands in for
the web. Everything runs through the real scripts as subprocesses (kb.py and rules.py from the nj-evidence skill).
Assertions (each a distinct failure):
   1 same-agent verify refused (x-helper wrote, x-lead verifies)      2 a page citing a draft id fails
   3 a page citing too few ids fails                                 4 a page missing a heading fails
   5 a good page passes                                              6 rules.py check exits 2 on a rule citing a draft
   7 build_report + check_report PASS                                8 a tampered glance must_appear fails
   9 report stage SKIP (exit 3) when a tool is missing
 + quote/raw binding (wrong source, tampered file, missing quote), tier-1 allowlist, unknown kind, teach checks,
   twin pair (and its stale en-sha), blind audit (same prefix refused, blanks fail, held passes), report refuses without audit,
   book_status derived from gates, plan for 4/10/37 items, Arabic edition (rtl, duplicate-id gate).
"""
import json, os, re, shutil, subprocess, sys, tempfile, threading, time
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
EVID = HERE.parents[1] / "nj-evidence" / "scripts"
N = 0
SKIPPED = []


def ok(cond, name):
    global N
    N += 1
    if not cond:
        print(f"FAIL assertion {N}: {name}")
        raise SystemExit(1)
    print(f"ok   {N:2} {name}")


DOC = ("Article 33. The controller shall notify the supervisory authority within 72 hours of becoming aware of the breach.\n"
       "This rule applies in the EU since 2018.\nEvery breach must be recorded in a register.\n"
       "Fines reach 2 percent of turnover.\nA restore test is required every 30 days.\n")
DOC2 = "A different document. The retention period is 5 years.\n"


def serve():
    import http.server, socketserver

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def do_GET(self):
            body = (DOC if self.path == "/doc" else DOC2).encode()
            self.send_response(200); self.send_header("Content-Type", "text/plain"); self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body)
    srv = socketserver.TCPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


EU = """# {title}

## 1. {h[0]}
{s[0]} [KB#1]
## 2. {h[1]}
{s[1]} [KB#2]
## 3. {h[2]}
- {s[2]} [KB#1]
- {s[3]} [KB#3]
## 4. {h[3]}
{s[4]} [KB#2]
## 5. {h[4]}
{s[5]} [KB#3]
## 6. {h[5]}
{s[6]} {nc}.
## 7. {h[6]}
{s[7]}
## 8. {h[7]}
*{s[8]}* {s[9]}
## 9. {h[8]}
1. Toy regulation, {url}, retrieved 2026-10-16, [KB#1] [KB#2] [KB#3]
"""
EU_EN = dict(title="Breach Notice Duty", h=["Summary", "Scope and jurisdiction", "Obligations", "Effective dates", "Evidence of compliance", "Pitfalls",
                                            "Mentor notes", "Illustrative case", "Sources"],
             s=["The controller notifies the authority within 72 hours.", "It applies in the EU.", "Notify the authority", "Record every breach",
                "In force since 2018.", "Keep a breach register.", "Waiting for certainty", "Practise the clock.",
                "Illustrative scenario, not a real company.", "A lab loses a laptop."], nc="Some fines are not confirmed")
EU_AR = dict(title="واجب الإبلاغ عن الخرق", h=["ملخص", "النطاق والاختصاص", "الالتزامات", "تواريخ النفاذ", "أدلة الامتثال", "المزالق",
                                              "ملاحظات المرشد", "حالة توضيحية", "المصادر"],
             s=["يبلغ المسؤول الجهة خلال 72 ساعة.", "ينطبق في الاتحاد الأوروبي.", "إبلاغ الجهة", "تسجيل كل خرق",
                "ساري منذ 2018.", "حفظ سجل الخروقات.", "انتظار اليقين", "تدرب على الساعة.",
                "سيناريو توضيحي وليس شركة حقيقية.", "مختبر يفقد حاسوبا محمولا."], nc="بعض الغرامات غير مؤكدة")

US = """# {title}

{box}
{i1}
{i2}

## 1. {h[0]}
{s[0]} [KB#5]
## 2. {h[1]}
{s[1]} [KB#1] [KB#2] [KB#3]

#### {tech} {{#howto-2}}
*Worked example.* {s[2]} 90 / 30 = 3.
*Try it.* {s[3]}
*Now alone.* {s[4]}

```mermaid
{mm}
```
## 3. {h[2]}
1. {s[5]}
## 4. {h[3]}
- {s[6]}
## 5. {h[4]}
{s[7]}
## 6. {h[5]}
1. Toy source, {url}, [KB#5]
"""
US_EN = dict(title="Running a Restore Drill", box="By the end you can", i1="- list the drill steps (K1)", i2="- compute the drill interval (K3)",
             h=["Overview", "Core concepts", "Step by step", "Pitfalls", "Practice", "Sources"], tech="Interval calculation",
             s=["A restore test is needed every 30 days.", "The checks lean on three facts.", "Suppose 90 days pass.", "How many in 120 days?",
                "Compute for 150 days.", "Pick a backup.", "Skipping the test.", "See the bank."],
             mm="flowchart LR\n  A[Notice] --> B[Report]")
US_AR = dict(title="إجراء اختبار الاستعادة", box="By the end you can", i1="- سرد خطوات الاختبار (K1)", i2="- حساب الفاصل الزمني (K3)",
             h=["نظرة عامة", "المفاهيم الأساسية", "خطوة بخطوة", "المزالق", "التدريب", "المصادر"], tech="حساب الفاصل",
             s=["يلزم اختبار استعادة كل 30 يوما.", "تعتمد الفحوص على ثلاث حقائق.", "لنفترض مرور 90 يوما.", "كم اختبارا في 120 يوما؟",
                "احسب لمدة 150 يوما.", "اختر نسخة احتياطية.", "إهمال الاختبار.", "راجع بنك الأسئلة."],
             mm="flowchart RL\n  A[إشعار] --> B[تقرير]")
BANK = """# {title}

## Questions
### Q-1
- objective: howto-1
- level: K1
- basis: KB#5
{q1}
a) {a1}
b) {a2}
### Q-2
- objective: howto-2
- level: K3
- basis: concept: §interval-calculation
{q2}
a) 2
b) 3
"""
KEYS = "Q-1: a\nQ-2: b\ncalc: 90 / 30\n"  # the calc lives in the question's block of the key file, never under the stem
RULES = """# Toy rules

## Theme

### R-TOY-001 · Notify fast
**Rule:** Notify the authority within 72 hours.
**When:** A breach is found.
**Because:** #{ids}
**Strength:** binding
**Decay:** evergreen
**Tags:** breach, notice
"""


def main():
    keep = "--keep" in sys.argv
    root = Path(tempfile.mkdtemp(prefix="toybook-"))
    srv = serve()
    port = srv.server_address[1]
    url, url2 = f"http://127.0.0.1:{port}/doc", f"http://127.0.0.1:{port}/doc2"
    env = dict(os.environ, BOOK_ROOT=str(root), PYTHONUTF8="1")

    def run(script, *args, d=HERE):
        p = subprocess.run([sys.executable, str(d / script), *args], env=env, cwd=str(root), capture_output=True, text=True, encoding="utf-8", timeout=600)
        return p.returncode, (p.stdout + p.stderr)

    def w(rel, text):
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8", newline="\n")
        return f

    try:
        # ---- config: nothing here is QA's
        w("kb/kb.json", json.dumps({"db": "kb/toy.db", "sectors": ["eu", "us"], "primary_hosts": {"127.0.0.1": 1}}))
        cfg = {"title": "Toy Rules Book", "slug": "toy-rules", "lang": "en", "pages": "chapters", "twin": "chapters-ar", "terms": "chapters-ar/_terms.md", "twin_title": "كتاب القواعد التجريبي",
               "twin_parts": ["الجزء أ", "الجزء ب"], "kinds": {"eu": "regulation", "us": "topic"}, "objective_id": None, "numbers": "warn",
               "practice": "practice", "rules": "kb/rules", "banks": {"print": True}, "glance": "report/glance.json", "glance_headers": ["Page", "Deadline"],
               "parts": [["Part A", ["eu/*.md"]], ["Part B", ["us/*.md"]]], "front": None}
        w("book.json", json.dumps(cfg, ensure_ascii=False))
        ok(run("kb.py", "init", d=EVID)[0] == 0 and (root / "kb" / "toy.db").exists(), "kb.py reads db/sectors from kb/kb.json (toy.db, no qa.db)")

        # ---- sources: allowlist, fetch, index
        rc, out = run("kb.py", "add-source", "--sector", "eu", "--name", "Toy regulation", "--url", url, "--tier", "1", d=EVID)
        ok(rc == 0, "tier-1 source on an allowlisted host accepted")
        rc, out = run("kb.py", "add-source", "--sector", "eu", "--name", "Other", "--url", f"http://localhost:{port}/doc2", "--tier", "1", d=EVID)
        ok(rc != 0 and "primary_hosts" in out, "tier-1 source on an unlisted host refused")
        ok(run("kb.py", "add-source", "--sector", "eu", "--name", "Second", "--url", url2, "--tier", "1", d=EVID)[0] == 0, "second source added")
        ok(run("fetch.py", url, "--slug", "gdpr", "--spacing", "0.2")[0] == 0 and run("fetch.py", url2, "--slug", "gdpr", "--spacing", "0.2")[0] == 0, "fetch.py fetched both sources")
        idx = (root / "research" / "_raw" / "index.tsv").read_text(encoding="utf-8").strip().split("\n")
        ok(len(idx) == 2 and all(len(r.split("\t")) == 5 for r in idx), "index.tsv holds url/file/sha1/retrieved/status per fetched file")
        raw1 = next(r.split("\t")[1] for r in idx if r.startswith(url + "\t"))
        raw2 = next(r.split("\t")[1] for r in idx if r.startswith(url2 + "\t"))

        # ---- entries and verification
        rows = [dict(sector="eu", topic="gdpr", claim="The controller notifies the authority within 72 hours of becoming aware.", sources=[1], by="eu-helper"),
                dict(sector="eu", topic="gdpr", claim="The rule applies in the EU since 2018.", sources=[1], by="eu-helper"),
                dict(sector="eu", topic="gdpr", claim="Every breach must be recorded in a register.", sources=[1], by="eu-helper"),
                dict(sector="eu", topic="gdpr", claim="Fines reach 2 percent of turnover.", sources=[1], by="eu-helper"),
                dict(sector="us", topic="howto", claim="A restore test is required every 30 days.", sources=[1], by="us-helper")]
        w("b.jsonl", "".join(json.dumps(r) + "\n" for r in rows))
        rc, out = run("kb.py", "add-batch", "b.jsonl", d=EVID)
        ok(rc == 0 and "added=5" in out, "add-batch added five drafts in one transaction")
        ok(run("kb.py", "add-batch", "b.jsonl", d=EVID)[1].count("dup ") == 5, "add-batch is idempotent (dup <id> x5)")
        q = lambda s: s
        ok(run("kb.py", "verify", "4", "--by", "eu-lead", "--quote", "Fines reach 2 percent of turnover.", "--raw", raw1, d=EVID)[0] != 0, "1: x-lead verifying x-helper's entry is refused (same prefix)")
        rc, out = run("kb.py", "verify", "4", "--by", "qa-lead", "--quote", "Fines reach 2 percent of turnover.", "--raw", raw2, d=EVID)
        ok(rc != 0 and "none of this entry's sources" in out, "quote/raw: a file fetched for a DIFFERENT source is refused")
        rc, out = run("kb.py", "verify", "4", "--by", "qa-lead", "--quote", "Fines reach 3 percent of turnover.", "--raw", raw1, d=EVID)
        ok(rc != 0 and "does not occur" in out, "quote/raw: a quote absent from the file is refused")
        vb = [dict(id=1, quote="shall notify the supervisory authority within 72 hours of becoming aware", raw=raw1), dict(id=2, quote="This rule applies in the EU since 2018.", raw=raw1),
              dict(id=3, quote="Every breach must be recorded in a register.", raw=raw1), dict(id=5, quote="A restore test is required every 30 days.", raw=raw1)]
        w("v.jsonl", "".join(json.dumps(r) + "\n" for r in vb))
        rc, out = run("kb.py", "verify-batch", "v.jsonl", "--by", "qa-lead", d=EVID)
        ok(rc == 0 and "held=4 refused=0" in out, "verify-batch held four entries (quote found in the entry's own fetched file)")
        raw_path = root / raw1
        raw_path.write_text(raw_path.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8", newline="\n")
        rc, out = run("kb.py", "verify", "4", "--by", "qa-lead", "--quote", "Fines reach 2 percent of turnover.", "--raw", raw1, d=EVID)
        ok(rc != 0 and "changed since" in out, "quote/raw: a file modified after the fetch is refused (sha1)")
        rc, out = run("fetch.py", url, "--slug", "gdpr", "--refresh", "--spacing", "0.2")
        ok(rc == 0, "re-fetch restores the indexed hash")

        # ---- pages (no 'headings' key anywhere: kinds carry the defaults)
        w("chapters/eu/gdpr.md", EU.format(url=url, **EU_EN))
        w("chapters/us/howto.md", US.format(url=url, **US_EN))
        rc, out = run("check_pages.py")
        ok(rc == 0 and "2 pages, 0 failing" in out, "5: good regulation + topic pages pass with kinds only (no headings key)")
        good = (root / "chapters/eu/gdpr.md").read_text(encoding="utf-8")
        w("chapters/eu/gdpr.md", good.replace("[KB#3]", "[KB#4]", 1))
        rc, out = run("check_pages.py")
        ok(rc == 1 and "non-verified" in out, "2: a page citing a draft id fails")
        w("chapters/eu/gdpr.md", re.sub(r"\[KB#\d\]", "", good))
        rc, out = run("check_pages.py")
        ok(rc == 1 and "need >= 3" in out, "3: a page citing no ids fails (min_cites default 3)")
        w("chapters/eu/gdpr.md", good.replace("## 3. Obligations", "## 3. Other"))
        rc, out = run("check_pages.py")
        ok(rc == 1 and "missing heading 'Obligations'" in out, "4: a page missing a heading fails")
        w("chapters/eu/gdpr.md", good)
        w("book.json", json.dumps(dict(cfg, kinds={"eu": "regulation", "us": "nonsense"})))
        rc, out = run("check_pages.py")
        ok(rc == 1 and "valid kinds" in out and "nonsense" in out, "an unknown kind is a hard error naming the valid kinds")
        w("book.json", json.dumps(cfg, ensure_ascii=False))

        # ---- rules
        w("kb/rules/toy.md", RULES.format(ids="1, #4"))
        rc, out = run("rules.py", "check", d=EVID)
        ok(rc == 2, "6: rules.py check exits 2 on a rule citing a draft entry")
        w("kb/rules/toy.md", RULES.format(ids="1, #3"))
        ok(run("rules.py", "check", d=EVID)[0] == 0, "rules.py check passes when every Because id is verified")

        # ---- teaching checks
        w("practice/howto.md", BANK.format(title="Restore drill questions", q1="Which step comes first?", a1="Pick a backup", a2="Delete it", q2="How many drills in 90 days?"))
        w("practice/howto.key.md", KEYS)
        rc, out = run("check_teach.py")
        ok(rc == 0 and "objectives=2 questions=2" in out, "check_teach passes: generated <slug>-<n> objectives, bank basis, keys apart, fading blocks, calc")
        bank = (root / "practice/howto.md").read_text(encoding="utf-8")
        w("practice/howto.key.md", KEYS.replace("90 / 30", "90 / 45"))
        rc, out = run("check_teach.py")
        ok(rc == 1 and "does not appear in the keyed option" in out, "check_teach: a calc (read from the key block) whose result is not in the keyed option fails")
        w("practice/howto.key.md", KEYS)
        w("practice/howto.md", bank.replace("How many drills in 90 days?", "- calc: 90 / 30\nHow many drills in 90 days?"))
        rc, out = run("check_teach.py")
        ok(rc == 1 and "calc sits under the stem" in out, "C1: a calc line under the stem fails check_teach (it gives the method away)")
        w("practice/howto.key.md", "Q-1: a" + chr(10) + "Q-2: b" + chr(10))  # a key block with no calc yet
        rc, out = run("move_calc.py")
        ok(rc == 0 and "would move 1 calc line(s)" in out and "calc: 90 / 30" in (root / "practice/howto.md").read_text(encoding="utf-8"), "C2: move_calc.py is a dry run by default")
        rc, out = run("move_calc.py", "--apply")
        ok(rc == 0 and "1 calc line(s) moved" in out and "calc:" not in (root / "practice/howto.md").read_text(encoding="utf-8") and (root / "practice/howto.key.md").read_text(encoding="utf-8").count("calc: 90 / 30") == 1, "C2: move_calc.py --apply moves the calc into the key block")
        ok("1 calc line(s) moved" not in run("move_calc.py", "--apply")[1] and run("check_teach.py")[0] == 0, "C2: a second --apply moves nothing, and check_teach passes with the calc in the key block")
        w("practice/howto.key.md", KEYS)
        w("practice/howto.md", bank.replace("- level: K1\n", "- level: K1\n- key: a\n", 1))
        rc, out = run("check_teach.py")
        ok(rc == 1 and "key sits beside the stem" in out, "check_teach: an answer key beside its stem fails")
        w("practice/howto.md", bank.replace("basis: KB#5", "basis: KB#4"))
        ok(run("check_teach.py")[0] == 1, "check_teach: a basis citing a draft entry fails")
        w("practice/howto.md", bank)
        us = (root / "chapters/us/howto.md").read_text(encoding="utf-8")
        w("chapters/us/howto.md", us.replace("*Now alone.* Compute for 150 days.\n", ""))
        rc, out = run("check_teach.py")
        ok(rc == 1 and "lacks" in out, "check_teach: a K3 technique without its three blocks fails")
        w("chapters/us/howto.md", us.replace("By the end you can", "Intro"))
        rc, out = run("check_teach.py")
        ok(rc == 1 and "By the end you can" in out, "check_teach: objective_id null with no box fails, not skipped")
        w("chapters/us/howto.md", us)
        w("path.md", "Plan: 6 hours per week\n## Week 1\n| task | minutes |\n|---|---|\n| read | 200 |\n| drill | 100 |\n- Ready when: 2 of 2 drills pass\n")
        rc, out = run("check_teach.py", "--path", "path.md")
        ok(rc == 0, "check_teach --path: hours line, weekly minutes within hours, X of Y within the bank")
        w("path.md", "Plan: 4 hours per week\n## Week 1\n| minutes |\n|---|\n| 300 |\n- Ready when: 9 of 40 pass\n")
        ok(run("check_teach.py", "--path", "path.md")[0] == 1, "check_teach --path: minutes above the hours line, and 40 > bank, fail")

        # ---- twin (the en-sha stamp is mandatory; figures are compared in order)
        w("chapters-ar/eu/gdpr.md", EU.format(url=url, **EU_AR))
        w("chapters-ar/us/howto.md", US.format(url=url, **US_AR))
        AR_BANK = BANK.format(title="أسئلة اختبار الاستعادة", q1="أي خطوة تأتي أولا؟", a1="اختيار نسخة", a2="حذفها", q2="كم اختبارا في 90 يوما؟")
        w("practice-ar/howto.md", AR_BANK)
        w("practice-ar/howto.key.md", KEYS)
        rc, out = run("check_pages.py", "--pair")
        ok(rc == 1 and out.count("no en-sha stamp") == 2, "F12: unstamped twin pages fail (a stamp is mandatory)")
        ok(run("check_pages.py", "--stamp")[0] == 0, "check_pages.py --stamp writes the en-sha first line from the current source")
        rc, out = run("check_pages.py", "--pair")
        ok(rc == 0 and "3 pairs, 0 failing" in out, "pair: toy twin (stamped pages + practice bank) keeps the fingerprint")
        ar = (root / "chapters-ar/eu/gdpr.md").read_text(encoding="utf-8")
        w("chapters-ar/eu/gdpr.md", ar.replace("- إبلاغ الجهة [KB#1]\n", ""))
        rc, out = run("check_pages.py", "--pair")
        ok(rc == 1 and "list_items" in out, "pair: a dropped list item fails")
        w("chapters-ar/eu/gdpr.md", ar.replace("غير مؤكدة", "مؤكدة"))
        ok(run("check_pages.py", "--pair")[0] == 1, "pair: not-confirmed count mismatch fails")
        sw = ar.replace("72", "@@").replace("2018", "72").replace("@@", "2018")
        w("chapters-ar/eu/gdpr.md", sw)
        rc, out = run("check_pages.py", "--pair")
        ok(rc == 1 and "figures differ" in out, "F12/B5: two figures swapped between sentences fail (order matters)")
        w("chapters-ar/eu/gdpr.md", ar)
        w("practice-ar/howto.key.md", "Q-1: a\nQ-2: a\n")
        rc, out = run("check_pages.py", "--pair")
        ok(rc == 1 and "key letters" in out, "pair: a changed answer-key letter in the twin bank fails")
        w("practice-ar/howto.key.md", KEYS)
        w("practice-ar/howto.md", AR_BANK.replace("a) 2\nb) 3", "a) 3\nb) 2"))
        rc, out = run("check_pages.py", "--pair")
        ok(rc == 1 and "figures in option" in out, "F12/B6: option figures swapped under an unchanged key letter fail")
        w("practice-ar/howto.md", AR_BANK)
        w("chapters/eu/gdpr.md", good.replace("Practise the clock.", "Practise the clock daily."))
        rc, out = run("check_pages.py", "--pair")
        ok(rc == 1 and "stale twin" in out, "pair: editing the English page after the twin was stamped flags a stale twin")
        w("chapters/eu/gdpr.md", good)
        w("chapters-ar/eu/extra.md", ar)
        rc, out = run("check_pages.py", "--pair")
        ok(rc == 1 and "no source page" in out, "F11: a twin file with no source page fails the list equality")
        (root / "chapters-ar/eu/extra.md").unlink()
        rc, out = run("check_pages.py", "--pair", "us/howto.md")
        ok(rc == 0 and "practice-ar/howto.md" in out and "2 pairs" in out, "S10: --pair <prefix> also runs the bank whose slug is the prefix's file stem")
        rc, out = run("check_pages.py", "--pair", "eu/gdpr.md")
        ok(rc == 0 and "1 pairs" in out and "practice-ar" not in out, "S10: a prefix without a matching bank runs no bank")
        ok(run("check_pages.py", "--pair", "chapters-ar/eu/gdpr.md")[1].count("0 pairs") == 1, "S10: a prefix is relative to the twin root, so a project-relative path matches nothing")
        ok("relative to the twin root" in " ".join(run("check_pages.py", "--help")[1].lower().split()), "S10: --help says the prefix is relative to the twin root")
        rc, out = run("check_pages.py", "--pair", "--terms")
        ok(rc == 1 and "FAIL" in out and ("no `avoid`" in out or "not found" in out), "F13: --terms with no term map / no avoid rule fails instead of passing on zero rules")
        w("chapters-ar/_terms.md", "| English | العربية | note | avoid |\n|---|---|---|---|\n| notify | إبلاغ | | إخطار |\n")
        rc, out = run("check_pages.py", "--pair", "--terms")
        ok(rc == 0 and "1 term(s)" in out, "F13: a real avoid rule that is not violated passes")
        w("chapters-ar/eu/gdpr.md", ar.replace("إبلاغ الجهة", "إخطار الجهة"))
        rc, out = run("check_pages.py", "--terms")
        ok(rc == 1 and "avoid" in out, "F13: an avoided term in an Arabic page is caught")
        w("chapters-ar/eu/gdpr.md", ar)
        (root / "chapters-ar/_terms.md").unlink()

        # ---- status and plan
        rc, out = run("book_status.py")
        ok("gdpr" in out and "page=done" in out and "audit: todo" in out, "book_status derives per-slug state and the audit state from the gates")
        rc, out = run("book_status.py", "plan", "--items", "37", "--slots", "20")
        ok("leads = ceil(37 / 6) = 7" in out and "waves = 3, workers = 7 + 37 = 44" in out and "MAX_HELPERS = min(20 // 7 - 1, 6) = 1" in out, "plan prints the arithmetic and the MAX_HELPERS the brief carries (37 items -> 7 leads, 1 helper each in one wave, or 3 waves)")
        ok(run("book_status.py", "plan", "--items", "37", "--slots", "0")[0] == 1, "F7/B3: --slots 0 is a one-line FAIL, not a traceback")
        ok("waves = 7" in run("book_status.py", "plan", "--items", "37", "--slots", "10")[1], "F7/B1: 37 items in 10 slots needs 7 waves")

        # ---- audit
        ok(run("audit_sample.py", "check")[0] == 1, "audit check fails with no sample")
        rc, out = run("audit_sample.py", "draw", "--by", "eu-auditor")
        ok(rc == 1 and "different auditor" in out, "audit draw refuses an auditor sharing a prefix with the entries' author")
        rc, out = run("audit_sample.py", "draw", "--by", "zz-auditor")
        ok(rc == 0 and (root / "audit" / "entries.md").exists() and (root / "audit" / "banks.md").exists(), "S2: a plain draw writes both audits (audit/entries.md, audit/banks.md) for a run that wrote nothing")
        ok(run("audit_sample.py", "check")[0] == 1, "audit check fails while verdicts are blank")
        rc, out = run("build_report.py", "--no-render")
        ok(rc == 1 and "audit gate" in out, "build_report refuses without a passing audit")
        hold = lambda name: w(f"audit/{name}.md", re.sub(r"\| \|\n", "| held |\n", (root / "audit" / f"{name}.md").read_text(encoding="utf-8")))
        hold("entries")
        rc, out = run("audit_sample.py", "check", "--entries")
        ok(rc == 0 and "misses=0" in out and "upper95=" in out, "audit check --entries passes when every row is held and prints the 95% bound")
        rc, out = run("audit_sample.py", "check")
        ok(rc == 1 and "banks:" in out, "S2: check without --entries needs the banks audit too (blank bank verdicts fail)")
        rc, out = run("build_report.py", "--no-render")
        ok(rc == 1 and "audit gate" in out, "S2: build_report refuses with only the entries audit passed")
        hold("banks")
        rc, out = run("audit_sample.py", "check")
        ok(rc == 0 and "entries:" in out and "banks:" in out, "S2: both audits held -> check passes")
        rc, out = run("audit_sample.py", "check", "--topic", "gdpr")
        ok(rc == 0, "S1: check --topic on a whole-database sample passes")
        rc, out = run("audit_sample.py", "draw", "--by", "zz-auditor", "--entries", "--topic", "gdpr", "--seed", "11")
        ok(rc == 0 and "topics=gdpr" in out, "S1: draw --entries --topic gdpr stores the topic in the header")
        ok("topics=gdpr" in (root / "audit" / "entries.md").read_text(encoding="utf-8") and "(1 pages)" not in out, "S1: the sample header carries the topics")
        rc, out = run("audit_sample.py", "check", "--entries", "--topic", "gdpr,howto")
        ok(rc == 1 and "covers topics" in out, "S1: a report that builds another topic is refused by a topic-restricted sample")
        w("audit/entries.md", re.sub(r"\| \|\n", "| held |\n", (root / "audit" / "entries.md").read_text(encoding="utf-8")))
        ok(run("audit_sample.py", "check", "--entries", "--topic", "gdpr")[0] == 0, "S1: the topic-restricted sample passes for its own topic")
        # restore a whole-database entries audit for the report stage below
        ok(run("audit_sample.py", "draw", "--by", "zz-auditor", "--entries")[0] == 0, "whole-database entries sample re-drawn")
        hold("entries")
        ok(run("audit_sample.py", "check")[0] == 0, "both audits pass again")

        # ---- F4 end to end: nothing found, orphan bank
        root0 = Path(tempfile.mkdtemp(prefix="nopages-"))
        (root0 / "kb").mkdir()
        (root0 / "kb" / "kb.json").write_text(json.dumps({"db": "kb/z.db"}))
        (root0 / "book.json").write_text(json.dumps({"title": "T", "slug": "t", "pages": "nope", "kinds": {}}))
        env0 = dict(env, BOOK_ROOT=str(root0))
        for sc in ("check_teach.py", "check_pages.py"):
            p0 = subprocess.run([sys.executable, str(HERE / sc)], env=env0, cwd=str(root0), capture_output=True, text=True, encoding="utf-8")
            ok(p0.returncode == 1 and "no pages found" in p0.stdout, f"F4/B4: {sc} on a mistyped `pages` path exits 1 (it used to say '0 failing')")
        shutil.rmtree(root0, ignore_errors=True)
        w("practice/orphan.md", BANK.format(title="Orphan", q1="x?", a1="p", a2="q", q2="y?"))
        rc, out = run("check_teach.py")
        ok(rc == 1 and "orphan bank" in out, "F4/B3: a bank no page owns fails")
        (root / "practice/orphan.md").unlink()
        rc, out = run("check_pages.py", "chapters/eu/does-not-exist.md")
        ok(rc == 1 and "no such page" in out and "Traceback" not in out, "a path that does not exist is a FAIL line, not a traceback")

        # ---- report stage
        w("report/glance.json", json.dumps([{"page": "eu/gdpr.md", "cells": ["Breach notice", "72 hours"], "must_appear": ["72 hours"]}]))
        miss = []
        try:
            sys.path.insert(0, str(HERE))
            import build_report as br
            miss = br.tools_missing(True)
        except Exception as e:  # pragma: no cover
            miss = [f"build_report import: {e}"]
        if not shutil.which("pdffonts"):
            miss.append("poppler pdffonts")
        miss += [t for t in os.environ.get("NJ_SELFTEST_HIDE", "").split(",") if t]  # 9: prove the SKIP -> exit 3 path
        if miss:
            SKIPPED.extend(miss)
            print(f"SKIP report stage: missing {', '.join(miss)}")
        else:
            t0 = time.time()
            rc, out = run("build_report.py")
            ok(rc == 0 and (root / "report" / "toy-rules.pdf").exists(), "build_report built the English PDF (two-print TOC pass, outline requested)")
            print("     " + out.strip().split("\n")[-1][:200])
            rc, out = run("check_report.py")
            print("     " + "\n     ".join(out.strip().split("\n")))
            ok(rc == 0 and "PASS" in out, "7: check_report PASS on the toy report (derived gates only)")
            ok("words:" in out and "svg: 1 inline diagrams == 1 mermaid fences" in out and "toc: " in out, "check_report derived words/svg/toc from the source")
            hb = (root / "report" / "toy-rules.html").read_text(encoding="utf-8")
            bsec = re.search(r'<section class="kb-page" id="b\d+">.*?</section>', hb, re.S).group(0)
            ksec = re.search(r'<section class="kb-page" id="k\d+">.*?</section>', hb, re.S).group(0)
            ok("90 / 30" not in bsec and "KB#5" not in bsec and "interval-calculation" not in bsec and "howto-1" not in bsec and "How many drills" in bsec and bsec.count("<li>") == 4,
               "C3: the printed bank shows stems and options only (no calc, basis, objective)")
            ok("90 / 30" in ksec and "interval-calculation" in ksec and "KB#5" in ksec and "<b>Key:</b>" in ksec, "C3: the printed answer-key part carries key, calc and basis")
            # ---- T1-T3: an owner-DISCLOSED bank-audit miss -- tolerance 1 / 1 miss passes as DISCLOSED, 2 misses fail, no key fails; the Method page says so
            bj5 = root / "book.json"
            cfg_keep, banks_keep = bj5.read_text(encoding="utf-8"), (root / "audit" / "banks.md").read_text(encoding="utf-8")
            miss1 = banks_keep.replace("| held |\n", "| missed: ambiguous stem |\n", 1)
            w("audit/banks.md", miss1)
            rc, out = run("audit_sample.py", "check")
            ok(rc == 1 and out.startswith("FAIL"), "T1: one miss and no audit_tolerance key fails as before")
            w("book.json", json.dumps(dict(json.loads(cfg_keep), audit_tolerance={"banks": {"max_misses": 1, "decided_by": "owner 2026-10-16"}}), ensure_ascii=False))
            rc, out = run("audit_sample.py", "check")
            ok(rc == 0 and out.startswith("DISCLOSED audit") and "owner 2026-10-16" in out and "upper95=" in out and "misses=1" in out, "T1: tolerance 1 with 1 miss exits 0 and the line starts DISCLOSED: " + out[:120])
            rc, out = run("build_report.py")
            ok(rc == 0, "T2: build_report accepts a DISCLOSED audit " + out[-120:])
            hd = (root / "report" / "toy-rules.html").read_text(encoding="utf-8")
            mp = re.search(r'id="method">.*?</section>', hd, re.S).group(0)
            ok("Disclosed audit miss" in mp and "Accepted by owner 2026-10-16" in mp and "howto.md:Q-" in mp and "95% upper bound" in mp and "missed 1" in mp, "T2: the Method page prints n, misses, upper95, the missed ids and 'Accepted by'")
            ok("Accepted by owner 2026-10-16" in (root / "report" / "toy-rules.md").read_text(encoding="utf-8"), "T2: the markdown edition says so too")
            rc, out = run("check_report.py")
            ok(rc == 0 and "PASS" in out and "audit: " in out and "DISCLOSED" in out, "T3: check_report does not treat DISCLOSED as missing")
            w("audit/banks.md", miss1.replace("| held |\n", "| missed: second |\n", 1))
            rc, out = run("audit_sample.py", "check")
            ok(rc == 1 and out.startswith("FAIL") and "exceed the disclosed tolerance" in out, "T1: two misses against a tolerance of 1 fail")
            ok(run("build_report.py", "--no-render")[0] == 1, "T2: build_report refuses when the misses exceed the tolerance")
            w("book.json", cfg_keep)
            w("audit/banks.md", banks_keep)
            ok(run("build_report.py")[0] == 0 and run("check_report.py")[0] == 0, "the undisclosed report builds and passes again")
            w("report/glance.json", json.dumps([{"page": "eu/gdpr.md", "cells": ["Breach notice", "73 hours"], "must_appear": ["73 hours"]}]))
            rc, out = run("check_report.py")
            ok(rc == 1 and "glance" in out, "8: a tampered glance must_appear fails the report gate")
            w("report/glance.json", json.dumps([{"page": "eu/gdpr.md", "cells": ["Breach notice", "72 hours"], "must_appear": ["72 hours"]}]))
            html = root / "report" / "toy-rules.html"
            h = html.read_text(encoding="utf-8")
            html.write_text(h.replace('id="method"', 'id="part1"', 1), encoding="utf-8")
            rc, out = run("check_report.py")
            ok(rc == 1 and "duplicate" in out, "check_report fails on a duplicate HTML id")
            html.write_text(h, encoding="utf-8")
            # F10/B9: every TOC number shifted by +1 (still sorted, still <= the page count)
            h = html.read_text(encoding="utf-8")
            html.write_text(re.sub(r'class="pg">(\d+)<', lambda m_: f'class="pg">{int(m_.group(1)) + 1}<', h), encoding="utf-8")
            rc, out = run("check_report.py")
            ok(rc == 1 and "toc:" in out and "printed" in out, "F10/B9: a TOC off by one page fails")
            html.write_text(h.replace("</body>", '<a href="#FL-4.2.1">dead</a></body>'), encoding="utf-8")
            rc, out = run("check_report.py")
            ok(rc == 1 and "dead internal link" in out, "F10/B1: a link with no target fails")
            html.write_text(h, encoding="utf-8")
            # F10/B8: a missing optional library is a SKIP -> exit 3, never PASS
            stub = ("import sys, runpy; [sys.modules.__setitem__(m, None) for m in ('fitz', 'pymupdf', 'fontTools', 'fontTools.ttLib')]; "
                    f"sys.path.insert(0, {str(HERE)!r}); sys.argv = ['check_report.py']; runpy.run_path({str(HERE / 'check_report.py')!r}, run_name='__main__')")
            p1 = subprocess.run([sys.executable, "-c", stub], env=env, cwd=str(root), capture_output=True, text=True, encoding="utf-8")
            ok(p1.returncode == 3 and "SKIP" in p1.stdout and "PASS" not in p1.stdout and "INCOMPLETE" in p1.stdout, "F10/B8: SKIP lines -> exit 3 and no PASS line")
            # F10/B11: a chapter's body deleted from the HTML but its title kept in the TOC
            pdf = root / "report" / "toy-rules.pdf"
            keep_pdf = pdf.read_bytes()
            cut = re.sub(r'(<section class="kb-page" id="p2">).*?(</section>)', r'\1\2', h, count=1, flags=re.S)
            ok(cut != h, "the chapter body was found to delete")
            html.write_text(cut, encoding="utf-8")
            br.render_pdf(html, pdf, "<div></div>")
            rc, out = run("check_report.py")
            ok(rc == 1 and "FAIL titles" in out, "F10/B11: a deleted chapter body fails the titles check even though the TOC still names it")
            html.write_text(h, encoding="utf-8")
            pdf.write_bytes(keep_pdf)
            ok(run("check_report.py")[0] == 0, "the restored report passes again")
            # F11/B3: an Arabic book that lacks a chapter is refused at build time
            hidden = root / "chapters-ar" / "us" / "howto.md"
            keep_ar = hidden.read_text(encoding="utf-8")
            hidden.unlink()
            rc, out = run("build_report.py", "--twin")
            ok(rc == 1 and "page list differs" in out, "F11/B3: the Arabic build refuses a twin missing a chapter")
            hidden.write_text(keep_ar, encoding="utf-8", newline="\n")
            rc, out = run("build_report.py", "--twin")
            ok(rc == 0 and (root / "report-ar" / "toy-rules-ar.pdf").exists(), "build_report --twin built the Arabic edition (rtl)")
            rc, out = run("check_report.py", "--twin")
            print("     " + "\n     ".join(out.strip().split("\n")))
            ok(rc == 0 and 'dir="rtl"' in out, "check_report --twin PASS incl. the rtl root and Arabic SVG text")
            print(f"     report stage {time.time() - t0:.0f}s")
        # ---- G7: check_tool.py end to end (a tool page needs Do it yourself + Check yourself + parseable code) -- wired into book_status
        import sqlite3 as _sq
        root5 = Path(tempfile.mkdtemp(prefix="tool-"))
        (root5 / "kb").mkdir()
        (root5 / "kb" / "kb.json").write_text(json.dumps({"db": "kb/t.db", "sectors": ["a"], "primary_hosts": {"x.org": 1}}))
        c5 = _sq.connect(root5 / "kb" / "t.db", timeout=60)
        c5.execute("CREATE TABLE entries(id INTEGER PRIMARY KEY, topic TEXT, claim TEXT, status TEXT)")
        c5.executemany("INSERT INTO entries VALUES(?,?,?,?)", [(i, "pw", f"claim {i}", "verified") for i in (1, 2, 3)])
        c5.commit(); c5.close()
        (root5 / "book.json").write_text(json.dumps({"title": "Tools", "slug": "tools", "pages": "pg", "kinds": {"tool": "tool"}, "practice": "practice"}))
        heads = ["What it is", "Setup", "Step-by-step", "Core features", "Best practices", "Integration", "pitfalls", "Mentor notes", "case study"]
        task = lambda n: f"### Task {n}: step {n}\nDone when:\n```bash\necho task{n}\n```\nExpected: `task{n}`\n"
        tool_page = ("# Playwright toy\n" + "".join(f"## {i}. {h}\n[KB#{(i % 3) + 1}]\ntext\n" for i, h in enumerate(heads, 1))
                     + "```json\n{\"ok\": true}\n```\n## 10. Do it yourself\n" + task(1) + task(2) + task(3)
                     + "## 11. Check yourself\n- Q-pw-01\n- Q-pw-02\n- Q-pw-03\n## 12. Sources\nhttps://x.org/a [KB#1] [KB#2] [KB#3]\n")
        (root5 / "pg" / "tool").mkdir(parents=True)
        pg5 = root5 / "pg" / "tool" / "pw.md"
        pg5.write_text(tool_page, encoding="utf-8")
        (root5 / "practice").mkdir()
        (root5 / "practice" / "pw.md").write_text("".join(f"### Q-pw-0{i}\nobjective: TASK-{i}\nlevel: K2\nbasis: KB#{i}\nWhat does task {i} print?\na) task{i}\nb) nothing\nc) an error\n" for i in (1, 2, 3)), encoding="utf-8")
        (root5 / "practice" / "pw.key.md").write_text("Q-pw-01: a\nQ-pw-02: a\nQ-pw-03: a\n", encoding="utf-8")
        env5 = dict(env, BOOK_ROOT=str(root5))
        run5 = lambda sc, *a: (lambda p_: (p_.returncode, p_.stdout + p_.stderr))(subprocess.run([sys.executable, str(HERE / sc), *a], env=env5, cwd=str(root5), capture_output=True, text=True, encoding="utf-8"))
        rc, out = run5("check_pages.py")
        ok(rc == 0, "G7: the toy tool page passes check_pages (tool headings) " + out[-120:])
        rc, out = run5("check_tool.py")
        ok(rc == 0 and "tasks=3 checks=3" in out and "1 tool page(s), 0 failing" in out, "G7: a tool page with 3 tasks, 3 checks and parseable code passes check_tool")
        rc, out = run5("check_teach.py")
        ok(rc == 0 and "bank of a non-teaching page" in out, "G7: the tool page's bank is still checked by check_teach (fields, keys, basis)")
        rc, out = run5("book_status.py")
        ok("tool=done" in out, "G7: book_status reports the tool stage for kind=tool pages")
        pg5.write_text(tool_page.replace("Expected: `task2`\n", ""), encoding="utf-8")
        rc, out = run5("check_tool.py")
        ok(rc == 1 and "no `Expected:`" in out, "G7: a task without Expected fails check_tool")
        ok("tool=FAIL" in run5("book_status.py")[1], "G7: book_status shows the failing tool stage")
        pg5.write_text(tool_page.replace('{\"ok\": true}', '{\"ok\": true,}'), encoding="utf-8")
        rc, out = run5("check_tool.py")
        ok(rc == 1 and "json block" in out, "G7: a fenced json block that does not parse fails")
        pg5.write_text(tool_page.replace("## 10. Do it yourself\n", "## 10. Exercises\n"), encoding="utf-8")
        ok(run5("check_tool.py")[0] == 1, "G7: a tool page without Do it yourself fails")
        shutil.rmtree(root5, ignore_errors=True)

        # ---- G5: check_teach --resemble against a sample-exam text; G10: kb hygiene dry run through the CLI
        sample = root / "sample-exam.txt"
        sample.write_text("Which step comes first? Pick a backup Delete it. How many drills in 90 days? " * 2, encoding="utf-8")
        rc, out = run("check_teach.py", "--resemble", str(sample))
        ok(rc == 1 and "FAIL" in out and "5-word shingles" in out, "G5: a bank item copied from a sample exam fails --resemble")
        other = root / "other-exam.txt"
        other.write_text("A completely different paragraph about risk based prioritisation in large programmes.", encoding="utf-8")
        ok(run("check_teach.py", "--resemble", str(other))[0] == 0, "G5: an unrelated sample exam passes --resemble")
        rc, out = run("kb.py", "hygiene", d=EVID)
        ok(rc == 0 and "hygiene:" in out and ("dry run" in out), "G10: kb.py hygiene is a dry run by default")

        # ---- H1: every database handle waits for peer writers (timeout=60): statically in every script, and under a real lock
        pat = re.compile(r"(?:sqlite3|_sq)\.conn" + r"ect\(((?:[^()]|\([^()]*\))*?)\)")
        bare = [f"{f.name}: {m.group(0)[:60]}" for f in sorted(list(HERE.glob("*.py")) + list(EVID.glob("*.py"))) for m in pat.finditer(f.read_text(encoding="utf-8")) if "timeout" not in m.group(1)]
        ok(not bare, f"H1: every sqlite3 handle in every script sets a timeout: {bare[:3]}")
        import sqlite3 as _s3, threading as _th
        lockdb = root / "lock.db"
        lc = _s3.connect(lockdb, timeout=60)
        lc.execute("CREATE TABLE entries(id INTEGER PRIMARY KEY, status TEXT)")
        lc.executemany("INSERT INTO entries VALUES(?,?)", [(1, "verified"), (2, "verified"), (3, "draft")])
        lc.commit(); lc.close()

        def hold():
            hc = _s3.connect(lockdb, timeout=60)
            hc.execute("BEGIN EXCLUSIVE")
            time.sleep(6.5)  # longer than sqlite's 5 s default wait
            hc.rollback(); hc.close()
        th = _th.Thread(target=hold); th.start(); time.sleep(0.5)
        sys.path.insert(0, str(HERE))
        import audit_sample as _au
        t0 = time.time()
        n_ver = _au.verified_count(lockdb)
        th.join()
        ok(n_ver == 2 and time.time() - t0 > 4.5, f"H1: a read under a peer's exclusive lock waited and succeeded instead of 'database is locked' ({time.time() - t0:.1f}s)")

        # ---- F15: the minimal 4-key book.json
        import sqlite3
        root3 = Path(tempfile.mkdtemp(prefix="fourkey-"))
        (root3 / "kb").mkdir()
        (root3 / "kb" / "kb.json").write_text(json.dumps({"db": "kb/f.db", "sectors": ["a"], "primary_hosts": {"x.org": 1}}))
        c3 = sqlite3.connect(root3 / "kb" / "f.db", timeout=60)
        c3.execute("CREATE TABLE entries(id INTEGER PRIMARY KEY, topic TEXT, claim TEXT, status TEXT)")
        c3.executemany("INSERT INTO entries VALUES(?,?,?,?)", [(i, "x", f"claim {i}", "verified") for i in (1, 2, 3)])
        c3.commit(); c3.close()
        (root3 / "book.json").write_text(json.dumps({"title": "Four", "slug": "four", "pages": "pg", "kinds": {"reg": "regulation"}}))
        (root3 / "pg" / "reg").mkdir(parents=True)
        (root3 / "pg" / "reg" / "x.md").write_text(EU.format(url="https://x.org/a", **EU_EN), encoding="utf-8")
        env3 = dict(env, BOOK_ROOT=str(root3))
        for sc, want in (("check_pages.py", 0), ("check_teach.py", 0), ("book_status.py", None)):
            p3 = subprocess.run([sys.executable, str(HERE / sc)], env=env3, cwd=str(root3), capture_output=True, text=True, encoding="utf-8")
            ok("Traceback" not in p3.stderr and (want is None or p3.returncode == want), f"F15: {sc} runs on a book.json with only title, slug, pages, kinds")
        shutil.rmtree(root3, ignore_errors=True)

        # ---- F15: the bank fence in reference/page-template.md round-trips through the parser
        sys.path.insert(0, str(HERE))
        import check_pages as cpm, check_teach as ctm
        tpl = HERE.parent / "reference" / "page-template.md"
        if tpl.is_file():
            m_ = re.search(r"## 4\..*?```\n(.*?)```", tpl.read_text(encoding="utf-8"), re.S)
            ok(bool(m_), "page-template.md section 4 holds a bank fence")
            fence = m_.group(1).replace("Q-<slug>-<nn>", "Q-howto-01").replace("KB#412", "KB#5")
            fence = fence.replace("a) ... b) ... c) ... d) ...", "a) 60 b) 62 c) 65 d) 70")
            q = cpm.parse_bank(fence)["questions"][0]
            ok(q["id"] == "Q-howto-01" and q["objective"] == "FL-4.2.1" and q["chapter"] == "4" and q["level"] == "K3" and sorted(q["options"]) == list("abcd")
               and q["basis"] == "KB#5" and q["calc"] == "" and q["type"] == "mcq", f"F15/B1: the template's own bank shape is not parsed: {q}")
            ok(not re.search(r"(?m)^(key|why-not):", fence), "F15/G2: the template's bank block carries no inline key and no why-not")
            e1, _ = ctm.check_bank("howto", cpm.parse_bank(fence + "why-not: a = x\n", "Q-howto-01: c\n"), {}, "", lambda i: i == 5)
            ok(any("why-not sits under the stem" in x for x in e1), "G2: a why-not under the stem is flagged")
            ok(any("calc sits under the stem" in x for x in e1) or "calc:" not in fence, "C1: a calc under the stem (page-template.md's fence shows one) is flagged")
            calc_line = next((l_ for l_ in fence.split("\n") if l_.startswith("calc:")), None)
            fence_nc = re.sub(r"(?m)^calc:.*\n", "", fence)
            calc_val = re.sub(r"\s{2,}\(.*$", "", calc_line[5:].strip()) if calc_line else "26/40*100"
            e2, sk = ctm.check_bank("howto", cpm.parse_bank(fence_nc, "Q-howto-01: c\nwhy-not: a = 60 is the lower boundary; b = 62 rounds; d = 70 is the old mark\ncalc: " + calc_val + "\n"), {}, "", lambda i: i == 5)
            ok(e2 == [] and not sk, f"F15: the template bank with key and why-not in the .key.md passes every bank check, calc evaluated: {e2} skipped={sk}")
        else:
            SKIPPED.append("reference/page-template.md")

        # ---- F15: every script's own --selftest
        for rel in (EVID / "kb.py", EVID / "rules.py", HERE / "check_pages.py", HERE / "check_teach.py", HERE / "build_report.py",
                    HERE / "check_report.py", HERE / "check_tool.py", HERE / "probe_bank.py", HERE / "move_calc.py", HERE / "audit_sample.py", HERE / "book_status.py", HERE / "fetch.py", HERE / "heal.py"):
            p4 = subprocess.run([sys.executable, str(rel), "--selftest"], env=dict(os.environ, PYTHONUTF8="1", BOOK_ROOT=str(root)), cwd=str(root), capture_output=True, text=True, encoding="utf-8", timeout=600)
            ok(p4.returncode == 0, f"F15: {rel.name} --selftest exit 0 (its own F-fix reproductions)" + ("" if p4.returncode == 0 else "\n" + (p4.stdout + p4.stderr)[-600:]))
    finally:
        srv.shutdown()
        if keep:
            print("kept", root)
        else:
            shutil.rmtree(root, ignore_errors=True)
    if SKIPPED:
        print(f"selftest: {N} assertions held; report stage SKIPPED ({', '.join(SKIPPED)}) -> exit 3, not 0")
        return 3
    print(f"selftest: {N} assertions ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
