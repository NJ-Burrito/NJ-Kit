#!/usr/bin/env python3
"""build_report.py -- pages -> one HTML -> one PDF per language (pandoc + mmdc + the pdf-typography renderer).

    build_report.py [--twin] [--no-render]
    build_report.py --selftest

Project = BOOK_ROOT env or cwd; book.json: title, slug, lang, pages, parts [[title, [globs|files]]], front (markdown or
null), rules (dir of rule packs, optional), banks {"print": true}, glance/glance_headers (optional), twin + twin_title /
twin_parts / twin_report / twin_lang / twin_front (for --twin), report (output dir, default "report").
Output: <report>/<slug>.html, .md, .pdf (--twin: <twin_report>/<slug>-ar.*, rtl, Arabic labels).

Order of work, each step a gate:
  1. REFUSES unless both audits (`audit_sample.py check`: entries.md and banks.md) pass for the topics it builds; the
     Method page prints its n, misses and 95 % upper bound. No audit, no report.
  2. every page file must be in a part (nothing silently dropped); explicit entries keep their order, globs are sorted.
  3. mermaid fences -> mmdc -> inline SVG (so the book's faces apply); SVG ids are made unique per diagram.
  4. every page's HTML ids/hrefs get a per-page prefix (p1-, p2-, ...): no duplicate ids across the book.
  5. one function swaps glyphs Thmanyah lacks (arrows, >=, box drawing) in ALL visible paths: pages, TOC, titles,
     footer, SVG labels. check_report.py measures the gap with fontTools.
  6. print -> read each title's page from the PDF text (matched in heading ORDER, not by id) -> write the numbers
     into the TOC -> print again; if the numbers moved, one more print, else FAIL. Fonts: Thmanyah only (hard-coded).
  7. renderPdf({outline:true}); a PDF without bookmarks is reported (older renderer ignores the option).
  8. banks (<practice>/*.md) print as a "Practice banks" part (opt out: banks.print=false); answer keys are a separate part
     after them. The cover prints the OLDEST `retrieved` date of the cited facts.
Needs pandoc, node + playwright chromium (via pdf-typography), mmdc (only when a page has a mermaid fence), poppler.
"""
import html as H
import json, math, os, re, shutil, sqlite3, subprocess, sys, tempfile, unicodedata
from datetime import date
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_pages as cp
import audit_sample as au
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = cp.ROOT
HOME = Path.home()
RENDERER = HOME / ".claude" / "skills" / "pdf-typography" / "scripts" / "render-pdf.mjs"
REPAIR = HOME / ".claude" / "skills" / "pdf-typography" / "scripts" / "repair-tounicode.py"
FONTS = ["Thmanyah Serif Display", "Thmanyah Sans"]  # Thmanyah only, everywhere -- not configurable
MMDC_BLOCK = re.compile(r"```mermaid\n(.*?)```", re.S)

GLYPH_STANDINS = [("→", "›"), ("≥", ">="), ("≤", "<="), ("≈", "~"), ("²", "<sup>2</sup>"), ("₂", "<sub>2</sub>"),
                  ("─", "-"), ("│", "|"), ("├", "+"), ("└", "`")]


def pages_phrase_ar(n):
    if n == 1:
        return "صفحة واحدة في هذا الجزء."
    if n == 2:
        return "صفحتان في هذا الجزء."
    return f"{n} صفحات في هذا الجزء." if n <= 10 else f"{n} صفحة في هذا الجزء."


LABELS = {
    "en": dict(key_head=("Question", "Key", "Why not", "Calc", "Basis"), toc="Table of contents", glance="At a glance", method="Method", banks="Practice banks", keys="Answer keys",
               appendix="Appendix — Rules of work", appendix_note="The rule packs, rendered as cards.", how="How to read this",
               oldest="Oldest source retrieved", pages_in_part=lambda n: f"{n} page(s) in this part.",
               kind_entries="fact", kind_banks="practice-question",
               disclosed=("Disclosed audit miss: the {kind} audit sampled {n} items and missed {misses} ({ids}). The 95% upper bound on that audit's miss rate is "
                          "{upper}%. Accepted by {by}."),
               method_text=("Every fact on these pages is stored in a database with the source it came from, a verbatim quote read from "
                            "the fetched file, a retrieval date and a verifier who is not its author. An independent auditor then "
                            "re-checked a random sample of {n} items (facts and practice questions) against the raw files: "
                            "{misses} missed. The 95% upper bound on the miss rate is {upper}%. "
                            "This shows that a sampled quote is real and supports its claim; it does not show that the source itself is right.")),
    "ar": dict(key_head=("السؤال", "المفتاح", "لماذا لا", "الحساب", "الأساس"), toc="فهرس المحتويات", glance="لمحة عامة", method="المنهجية", banks="بنوك الأسئلة", keys="مفاتيح الإجابة",
               appendix="الملحق: قواعد العمل", appendix_note="حزم القواعد معروضة بطاقات، وتبقى بلغتها الأصلية.", how="كيف تقرأ هذه القاعدة",
               oldest="أقدم مصدر جرى جلبه", pages_in_part=pages_phrase_ar,
               kind_entries="الحقائق", kind_banks="أسئلة التدريب",
               disclosed=("إفصاح عن خطأ في التدقيق: شمل تدقيق {kind} عينة من {n} عنصرا وأخطأ في {misses} منها ({ids}). "
                          "والحد الأعلى لنسبة الخطأ في هذا التدقيق بثقة 95% هو {upper}%. اعتمد القبول: {by}."),
               method_text=("كل حقيقة في هذه الصفحات محفوظة في قاعدة بيانات مع مصدرها، ومقتطف حرفي قرئ من الملف المجلوب، وتاريخ الجلب، "
                            "ووكيل متحقق ليس هو كاتبها. ثم أعاد مدقق مستقل فحص عينة عشوائية من {n} عنصرا (حقائق وأسئلة تدريب) "
                            "على الملفات الخام: الأخطاء المكتشفة {misses}. والحد الأعلى لنسبة الخطأ بثقة 95% هو {upper}%. "
                            "هذا يثبت أن المقتطف المفحوص حقيقي ويدعم الحقيقة، ولا يثبت أن المصدر نفسه صحيح.")),
}

CSS = """
@page { size: A4 portrait; }
:root { --ink:#1d2a2e; --muted:#5d6b70; --accent:#0f5f6b; --line:#d5dee0; --tint:#F3F8F9; }
body { font-family:'Thmanyah Sans', sans-serif; color:var(--ink); background:#fff; font-size:10pt; line-height:1.55; margin:0; text-align:start; }
h1, h2, h3, h4 { font-family:'Thmanyah Serif Display', serif; color:var(--accent); line-height:1.3; }
h1 { font-size:26pt; margin:0 0 10pt; } h2 { font-size:18pt; margin:0 0 8pt; } h3 { font-size:13pt; margin:14pt 0 5pt; } h4 { font-size:11pt; margin:10pt 0 4pt; }
p, li { overflow-wrap:anywhere; }
table { width:100%; table-layout:fixed; border-collapse:collapse; font-size:8.5pt; margin:6pt 0 10pt; }
th, td { overflow-wrap:anywhere; vertical-align:top; border-bottom:0.6pt solid var(--line); padding:3pt 4pt; text-align:start; }
th { background:var(--tint); }
pre { white-space:pre-wrap; word-break:break-word; background:var(--tint); padding:6pt; font-size:8pt; }
code { font-family:'Thmanyah Sans', sans-serif; font-size:0.92em; overflow-wrap:anywhere; }
blockquote { margin:6pt 0; padding:4pt 8pt; background:var(--tint); border-inline-start:2.5pt solid var(--accent); }
.diagram { margin:8pt 0; } .diagram svg { max-width:100% !important; height:auto !important; }
.kb { color:#8a969a; font-size:7pt; }
.card { border:0.6pt solid var(--line); border-radius:3pt; padding:5pt 8pt; margin:6pt 0; break-inside:avoid; }
.card h4 { margin-top:0; }
section.part, section.kb-page { break-before:page; }
section.kb-page h2:first-child { border-bottom:1.5pt solid var(--accent); padding-bottom:4pt; }
.cover { height:240mm; display:flex; flex-direction:column; justify-content:center; }
.cover .sub { font-size:13pt; color:var(--muted); margin-top:6pt; } .cover .date { margin-top:24pt; color:var(--muted); }
.toc, .toc ol { list-style:none; padding:0; margin:0; } .toc ol { padding-inline-start:14pt; flex-basis:100%; }
.toc li { margin:2pt 0; display:flex; flex-wrap:wrap; align-items:baseline; }
.toc a { color:var(--ink); text-decoration:none; } .toc .lead { flex:1; border-bottom:1pt dotted var(--line); margin:0 4pt; min-width:12pt; }
.toc .pg { font-variant-numeric:tabular-nums; color:var(--muted); }
"""
CSS_RTL = """
html { direction:rtl; } body { font-size:10.5pt; line-height:1.7; }
pre, .sourceCode, .ltr-block { direction:ltr; text-align:left; unicode-bidi:isolate; }
.diagram svg { direction:rtl; }
.ltr-block p, .ltr-block li, .ltr-block td, .ltr-block th { line-height:1.55; }
"""


# ---------------------------------------------------------------- bidi (port of pdf-typography rtl.mjs)
LATIN_RUN = re.compile(r"(?:[+\u00b1-](?=\d))?[A-Za-z0-9][A-Za-z0-9 _@#%&/\\.,:;=+*'\"()\[\]{}<>|-]*[A-Za-z0-9)\]}%]|(?:[+\u00b1-](?=\d))?[A-Za-z0-9]")
PAIRS = {")": "(", "]": "[", "}": "{"}


def _trim_unbalanced(run):
    while run and run[-1] in PAIRS and run.count(run[-1]) > run.count(PAIRS[run[-1]]):
        run = run[:-1]
    return run


def bidi(text):
    """Latin runs inside Arabic text are isolated LTR so punctuation stays where it belongs."""
    out, last = [], 0
    for m in LATIN_RUN.finditer(text):
        run = _trim_unbalanced(m.group(0))
        if not run:
            continue
        out.append(H.escape(text[last:m.start()], quote=False))
        out.append(f'<bdi dir="ltr">{H.escape(run, quote=False)}</bdi>')
        last = m.start() + len(run)
    out.append(H.escape(text[last:], quote=False))
    return "".join(out)


SKIP = {"pre", "code", "svg", "bdi", "style", "script"}
VOID = {"br", "hr", "img", "col", "input", "meta", "link", "wbr"}
TAG = re.compile(r"(<[^>]+>)")


def rtl_html(fragment):
    """Every text node outside code/svg/bdi goes through bidi(); code blocks are isolated LTR."""
    out, skip, pre = [], 0, 0
    for tok in TAG.split(fragment):
        if not tok:
            continue
        if tok.startswith("<"):
            m = re.match(r"<(/?)([a-zA-Z0-9]+)", tok)
            if m:
                closing, name = m.group(1) == "/", m.group(2).lower()
                selfclose = tok.endswith("/>") or name in VOID
                if name in SKIP and not selfclose:
                    skip += -1 if closing else 1
                if name == "pre" and not selfclose:
                    pre += -1 if closing else 1
                    if not closing:
                        tok = re.sub(r"^<pre", '<pre dir="ltr"', tok)
                elif name == "code" and not pre:
                    tok = "</code></bdi>" if closing else '<bdi dir="ltr"><code>'
            out.append(tok)
        else:
            out.append(tok if skip else bidi(H.unescape(tok)))
    return "".join(out)


# ---------------------------------------------------------------- helpers
def key(s):
    return "".join(c for c in unicodedata.normalize("NFKC", s).lower() if c.isalnum())


def tools_missing(need_mermaid=True):
    miss = [t for t in ("pandoc", "node", "pdftotext") + (("mmdc",) if need_mermaid else ()) if not shutil.which(t)]
    if not RENDERER.is_file():
        miss.append("pdf-typography renderer")
    else:
        probe = subprocess.run(["node", "-e", "const {createRequire}=require('module');const r=createRequire(process.argv[1]);"
                                "const c=r('playwright').chromium;process.exit(require('fs').existsSync(c.executablePath())?0:3)",
                                str(RENDERER.parent.parent / "x.js")], capture_output=True, text=True) if shutil.which("node") else None
        if probe is None or probe.returncode != 0:
            miss.append("Chrome (playwright chromium)")
    return miss


def expand_parts(cfg, pages_root):
    """-> ([(part_title, [rel posix paths])], [errors]). Globs sorted; explicit entries keep their order; first part wins."""
    seen, out, errs = set(), [], []
    for title, pats in cfg["parts"]:
        rels = []
        for pat in pats:
            if any(ch in pat for ch in "*?["):
                found = sorted(p.relative_to(pages_root).as_posix() for p in pages_root.glob(pat) if p.is_file() and not p.name.startswith("_"))
                if not found:
                    errs.append(f"part '{title}': pattern '{pat}' matches nothing")
            else:
                if not (pages_root / pat).is_file():
                    errs.append(f"part '{title}': '{pat}' not found under {pages_root}")
                found = [pat]
            rels += [r for r in found if r not in seen]
            seen.update(found)
        out.append((title, rels))
    allp = {p.relative_to(pages_root).as_posix() for p in pages_root.rglob("*.md") if not p.name.startswith("_")}
    if allp - seen:
        errs.append(f"{len(allp - seen)} page(s) in no part (nothing is dropped silently): {sorted(allp - seen)[:6]}")
    return out, errs


def prefix_ids(frag, pre):
    frag = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{pre}-{m.group(1)}"', frag)
    return re.sub(r'href="#([^"]+)"', lambda m: f'href="#{pre}-{m.group(1)}"', frag)


def uniq_svg(svg, pre):
    """Make every id inside one inline SVG (and the references to it) unique to this diagram."""
    for i in sorted(set(re.findall(r'\bid="([^"]+)"', svg)), key=len, reverse=True):
        svg = re.sub(r'(?<![\w-])' + re.escape(i) + r'(?![\w-])', f"{pre}-{i}", svg)
    return svg


def mermaid_cfg_dir():
    for d in (os.environ.get("MERMAID_CFG"), str(HOME / "Desktop" / "nj-plugin" / "skills" / "workflow-diagram" / "mermaid")):
        if d and (Path(d) / "mermaid-config.json").is_file():
            return Path(d)
    return None


def inline_mermaid(md_text, stem, diagrams):
    diagrams.mkdir(parents=True, exist_ok=True)
    svgs = {}

    def repl(m):
        n = len(svgs) + 1
        src, out = diagrams / f"{stem}-{n}.mmd", diagrams / f"{stem}-{n}.svg"
        src.write_text(m.group(1), encoding="utf-8", newline="\n")
        cfgdir = mermaid_cfg_dir()
        cmd = [shutil.which("mmdc") or "mmdc", "-i", str(src), "-o", str(out), "-b", "#F3F8F9", "-q"]
        if cfgdir:
            cmd += ["-c", str(cfgdir / "mermaid-config.json"), "-C", str(cfgdir / "mermaid.css")]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        k = f"MERMAIDPLACEHOLDER{n}X"
        svgs[k] = out.read_text(encoding="utf-8").strip()
        return f"\n\n{k}\n\n"
    return MMDC_BLOCK.sub(repl, md_text), svgs


def pandoc_html(md_text, shift=1):
    return subprocess.run(["pandoc", "-f", "gfm+attributes", "-t", "html5", f"--shift-heading-level-by={shift}"], input=md_text, check=True,
                          capture_output=True, text=True, encoding="utf-8").stdout


def diagram_prefix(pre, k):
    """Unique per diagram: the whole number, so diagrams 1 and 11 never share a prefix."""
    return f"{pre}-d{re.search(r'(\d+)X$', k).group(1)}"


def fragment(md_text, pre, stem, diagrams, rtl, shift=1):
    """-> (html, mermaid_count). Ids prefixed, SVG unique, bidi applied, [KB#n] marked."""
    text, svgs = inline_mermaid(md_text, stem, diagrams)
    out = prefix_ids(pandoc_html(text, shift), pre)
    for k, svg in svgs.items():  # before bidi: the placeholder is a Latin run and would be wrapped
        out = re.sub(rf"<p>{k}</p>", lambda _m, s=svg: '<div class="diagram">' + uniq_svg(s, diagram_prefix(pre, k)) + "</div>", out)
    if rtl:
        out = rtl_html(out)
    mark = (r'<bdi dir="ltr" class="kb">[KB#\1]</bdi>' if rtl else r'<span class="kb">[KB#\1]</span>')
    return re.sub(r"\[KB#(\d+)\]", mark, out), len(svgs)


def bank_html(bank, rtl):
    """A practice bank as cards: id, stem, one option per line. Nothing that hints at the answer (no objective / level / basis / calc);
    those print in the answer-key part (keys_html)."""
    T = bidi if rtl else (lambda x: H.escape(x, quote=False))
    out = []
    for q in bank["questions"]:
        opts = "".join(f"<li>{T(o)}</li>" for _, o in sorted(q["options"].items()))
        out.append(f'<div class="card"><h4><bdi dir="ltr">{H.escape(q["id"])}</bdi></h4><p>{T(q["stem"])}</p><ol type="a">{opts}</ol></div>')
    return "".join(out)


def keys_html(bank, rtl, head=("Question", "Key", "Why not", "Calc", "Basis")):
    """The answer-key part, one card per question in reading order (a table reads column by column in the PDF text and breaks the
    heading-first order the TOC relies on): key, why-not (or the rubric), calc and basis -- everything the learner-facing bank hides."""
    T = bidi if rtl else (lambda x: H.escape(x, quote=False))
    L = lambda x: f'<bdi dir="ltr">{H.escape(x)}</bdi>'
    out = []
    for q in bank["questions"]:
        rows = [(head[1], L(bank["keys"].get(q["id"], "?"))),
                (head[2], T(q["why_not"] or " ; ".join(q.get("rubric") or [])) if (q["why_not"] or q.get("rubric")) else ""),
                (head[3], L(q["calc"]) if q.get("calc") else ""), (head[4], L(q["basis"]) if q.get("basis") else "")]
        out.append(f'<div class="card"><h4>{L(q["id"])}</h4>' + "".join(f"<p><b>{T(k)}:</b> {v}</p>" for k, v in rows if v) + "</div>")
    return "".join(out)


def page_title(md_path):
    for line in cp.mask_fences(Path(md_path).read_text(encoding="utf-8")).splitlines():  # a `# comment` in a code fence is not the title
        if line.startswith("# "):
            return line[2:].strip()
    raise SystemExit(f"FAIL no H1 title in {md_path}")


def standins(s, rtl):
    for a, b in GLYPH_STANDINS + [("←", "›" if rtl else "‹")]:
        s = s.replace(a, b)
    return s


def locate_pages(texts, entries, marker_key):
    """Page number (1-based) of every entry, matched in heading ORDER.

    texts   = per-PDF-page text; entries = [(kind, title)] in document order; marker_key = key() of the first part's
    divider phrase, which only the body contains (so the TOC and glance pages are never matched).
    An entry sits on the first page at or after the cursor whose text STARTS with its title; every match moves the cursor
    strictly past that page (each part and page starts a new page), so a part and its first page that share a title
    ('Glossary' / 'Glossary') get consecutive pages."""
    keys = [key(t) for t in texts]
    cur = next((i for i, k in enumerate(keys) if marker_key in k), None)
    if cur is None:
        return None
    out = []
    for kind, title in entries:
        tk = key(title)
        words = [w for w in (key(w) for w in unicodedata.normalize("NFKC", title).split()) if w]
        for i in range(cur, len(keys)):
            head = keys[i][: len(tk) + 2]
            wide = keys[i][: len(tk) + 12]
            if 0 <= head.find(tk) <= 2 or (len(words) >= 2 and all(w in wide for w in words)):  # poppler may reorder an Arabic line (or a Latin title like 'Cypress — 16.2.0' inside RTL)
                out.append(i + 1); cur = i + 1; break
        else:
            out.append(None)
    return out


def oldest_retrieved(cfg, page_texts):
    dbp = cp.db_path()
    if not dbp.exists():
        raise SystemExit(f"FAIL no database at {dbp}")
    ids = sorted({int(i) for t in page_texts for i in re.findall(r"\[KB#(\d+)\]", t)})
    c = sqlite3.connect(f"file:{dbp.as_posix()}?mode=ro", uri=True, timeout=60)
    if ids:
        r = c.execute(f"SELECT MIN(retrieved) FROM entries WHERE id IN ({','.join('?' * len(ids))})", ids).fetchone()[0]
    else:
        r = c.execute("SELECT MIN(retrieved) FROM entries WHERE status='verified'").fetchone()[0]
    c.close()
    return r or "unknown"


def toc_html(parts_info, nums):
    """parts_info = [(part_title, part_id, [(page_title, page_id)])]; nums = {id: page} (None -> placeholder)."""
    pg = lambda i: f'<span class="lead"></span><span class="pg">{nums.get(i) or "000"}</span>'
    rows = []
    for pt, pid, items in parts_info:
        li = "".join(f'<li><a href="#{i}">{t}</a>{pg(i)}</li>' for t, i in items)
        rows.append(f'<li><b><a href="#{pid}">{pt}</a></b>{pg(pid)}<ol>{li}</ol></li>')
    return "".join(rows)


def render_pdf(html_path, pdf_path, footer):
    js = ("import { readFileSync } from 'node:fs';\n"
          f"import {{ renderPdf }} from '{RENDERER.as_uri()}';\n"
          "const [h, o, f] = process.argv.slice(2);\n"
          f"await renderPdf({{ html: readFileSync(h, 'utf8'), out: o, footer: readFileSync(f, 'utf8'), fonts: {json.dumps(FONTS)}, outline: true }});\n")
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "r.mjs").write_text(js, encoding="utf-8")
        (Path(td) / "f.html").write_text(footer, encoding="utf-8")
        r = subprocess.run(["node", str(Path(td) / "r.mjs"), str(html_path), str(pdf_path), str(Path(td) / "f.html")],
                           capture_output=True, text=True, encoding="utf-8", cwd=str(RENDERER.parent))
    if r.returncode != 0:
        raise SystemExit("FAIL render: " + (r.stderr or r.stdout)[-400:])


def pdf_texts(pdf):
    r = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), "-"], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True)
    t = r.stdout.split("\f")
    return t[:-1] if t and not t[-1].strip() else t


def build(cfg, twin=False, render=True, root=None):
    root = Path(root or ROOT)
    lang = (cfg.get("twin_lang") or "ar") if twin else cfg.get("lang", "en")
    rtl = lang == "ar"
    L = LABELS["ar" if rtl else "en"]
    T = bidi if rtl else (lambda s: H.escape(s, quote=False))
    pages_root = root / (cfg["twin"] if twin else cfg["pages"])
    if twin and not cfg.get("twin"):
        raise SystemExit("FAIL --twin needs 'twin' in book.json")
    title = (cfg.get("twin_title") if twin else None) or cfg["title"]
    outdir = root / ((cfg.get("twin_report") or "report-ar") if twin else cfg.get("report", "report"))
    stem = cfg["slug"] + ("-ar" if twin else "")
    diagrams = outdir / "diagrams"
    outdir.mkdir(parents=True, exist_ok=True)

    if twin:
        names = lambda r: {p.relative_to(r).as_posix() for p in r.rglob("*.md") if not p.name.startswith("_")}
        src, tw = names(root / cfg["pages"]), names(pages_root)
        if src != tw:
            raise SystemExit(f"FAIL the twin's page list differs from the source's: missing {sorted(src - tw)[:6]}, extra {sorted(tw - src)[:6]} (an Arabic book must not ship without a chapter)")
    a = au.summarize(root, topics=au.report_topics(cfg, pages_root))  # gate 1: both audits, for the topics this report builds
    if not a["ok"]:
        raise SystemExit(f"FAIL audit gate: {a['msg']}  (run audit_sample.py draw/check first; the report does not build without it)")
    parts, errs = expand_parts(cfg if not twin or not cfg.get("twin_parts") else dict(cfg, parts=[[t, p[1]] for t, p in zip(cfg["twin_parts"], cfg["parts"])]), pages_root)
    if errs:
        raise SystemExit("FAIL parts: " + "; ".join(errs))
    parts = [(cfg["twin_parts"][i] if twin and cfg.get("twin_parts") else t, rels) for i, (t, rels) in enumerate(parts)]

    n_svg = 0
    body, md_chunks, parts_info, texts, pid = [], [], [], [], 0
    entries = []  # (kind, title) in document order, for locate_pages
    for ptitle, rels in parts:
        pid += 1
        part_id = f"part{pid}"
        entries.append(("part", ptitle))
        body.append(f'<section class="part" data-front="1" id="{part_id}"><h1>{T(ptitle)}</h1><p>{T(L["pages_in_part"](len(rels)))}</p></section>')
        md_chunks.append(f"# {ptitle}")
        items = []
        for rel in rels:
            pid += 1
            md_path = pages_root / rel
            text = md_path.read_text(encoding="utf-8")
            texts.append(text)
            frag, k = fragment(text, f"p{pid}", Path(rel).stem, diagrams, rtl)
            n_svg += k
            t = page_title(md_path)
            items.append((T(t), f"p{pid}")); entries.append(("page", t))
            body.append(f'<section class="kb-page" id="p{pid}">{frag}</section>')
            md_chunks.append(text)
        parts_info.append((T(ptitle), part_id, items))

    # banks, then keys as a separate part
    banks_on = (cfg.get("banks") or {}).get("print", True)
    bdir = root / ((cp.twin_bank_dir(cfg) if twin else (cfg.get("practice") or "practice")) or "practice")
    bfiles = [p for p in sorted(bdir.glob("*.md")) if not p.name.startswith("_") and not p.name.endswith(".key.md")] if (banks_on and bdir.is_dir()) else []
    if banks_on and twin and cp.bank_files(cfg, root) and not bfiles:
        raise SystemExit(f"FAIL the twin has no practice banks in {bdir} (set banks.print=false to leave banks out)")
    extras = []
    if bfiles:
        pid += 1; bid = f"part{pid}"
        entries.append(("part", L["banks"]))
        body.append(f'<section class="part" data-front="1" id="{bid}"><h1>{T(L["banks"])}</h1></section>')
        items, keyed = [], []
        for bf in bfiles:
            pid += 1
            qtext = cp.split_key(bf.read_text(encoding="utf-8"))[0]
            bank = cp.load_bank(bf)
            bt = next((l[2:].strip() for l in cp.mask_fences(qtext).splitlines() if l.startswith("# ")), bf.stem)
            items.append((T(bt), f"b{pid}")); entries.append(("page", bt))
            body.append(f'<section class="kb-page" id="b{pid}"><h2>{T(bt)}</h2>{bank_html(bank, rtl)}</section>')
            md_chunks.append(qtext)
            if bank["keys"]:
                keyed.append((bt, f"k{pid}", bank))
        parts_info.append((T(L["banks"]), bid, items))
        if keyed:
            pid += 1; kid = f"part{pid}"
            entries.append(("part", L["keys"]))
            body.append(f'<section class="part" data-front="1" id="{kid}"><h1>{T(L["keys"])}</h1></section>')
            kitems = []
            for bt, i, bank in keyed:
                kitems.append((T(bt), i)); entries.append(("page", bt))
                body.append(f'<section class="kb-page" id="{i}"><h2>{T(bt)}</h2>{keys_html(bank, rtl, L["key_head"])}</section>')
                md_chunks.append("\n".join(f"{q}: {k}" for q, k in bank["keys"].items()))
            parts_info.append((T(L["keys"]), kid, kitems))

    # rule packs appendix
    rdir = root / (cfg.get("rules") or "kb/rules")
    if rdir.is_dir() and any(p for p in rdir.glob("*.md") if p.name != "INDEX.md"):
        pid += 1; aid = f"part{pid}"
        entries.append(("part", L["appendix"]))
        rhtml = []
        for path in sorted(rdir.glob("*.md")):
            if path.name == "INDEX.md":
                continue
            pid += 1
            text = path.read_text(encoding="utf-8")
            frag = fragment(text, f"r{pid}", "rules-" + path.stem, diagrams, False)[0]
            pieces = re.split(r"(?=<h4 )", frag)
            cards = pieces[0] + "".join(f'<div class="card">{p}</div>' for p in pieces[1:])
            cls = ' ltr-block" dir="ltr" lang="en' if rtl else ""
            rhtml.append(f'<section class="kb-page{cls}" id="r{pid}">{cards}</section>')
            md_chunks.append(text)
        body.append(f'<section class="part" data-front="1" id="{aid}"><h1>{T(L["appendix"])}</h1><p>{T(L["appendix_note"])}</p></section>' + "".join(rhtml))
        parts_info.append((T(L["appendix"]), aid, []))

    oldest = oldest_retrieved(cfg, texts)
    front = ""
    front_rel = (cfg.get("twin_front") if twin and cfg.get("twin_front") else cfg.get("front"))
    if front_rel and (root / front_rel).is_file():
        front = f'<section class="kb-page" data-front="1"><h2>{T(L["how"])}</h2>' + fragment((root / front_rel).read_text(encoding="utf-8"), "fr", "front", diagrams, rtl)[0] + "</section>"
    n_items = a["n"]
    disc_txt = [L["disclosed"].format(kind=L["kind_" + d["kind"]], n=d["n"], misses=d["misses"], ids=", ".join(d["ids"]), upper=f"{d['upper'] * 100:.1f}", by=d["decided_by"])
                for d in a.get("disclosures", [])]  # an owner-accepted audit miss is printed, never hidden
    method = (f'<section class="kb-page" data-front="1" id="method"><h2>{T(L["method"])}</h2><p>' +
              T(L["method_text"].format(n=n_items, misses=a["misses"], upper=f"{a['upper'] * 100:.1f}")) + "</p>" +
              "".join(f"<p>{T(t)}</p>" for t in disc_txt) + "</section>")
    glance = ""
    if cfg.get("glance") and not twin and (root / cfg["glance"]).is_file():
        rows = json.loads((root / cfg["glance"]).read_text(encoding="utf-8"))
        head = "".join(f"<th>{T(h)}</th>" for h in cfg.get("glance_headers", []))
        glance = (f'<section class="kb-page" data-front="1"><h2>{T(L["glance"])}</h2><table><tr>{head}</tr>' +
                  "".join("<tr>" + "".join(f"<td>{T(str(c))}</td>" for c in r["cells"]) + "</tr>" for r in rows) + "</table></section>")
    sub = cfg.get("subtitle", "")
    cover = (f'<section class="cover" data-front="1"><h1>{T(title)}</h1>' + (f'<p class="sub">{T(sub)}</p>' if sub else "") +
             f'<p class="date"><bdi dir="ltr">{date.today().isoformat()}</bdi></p><p class="date">{T(L["oldest"])}: <bdi dir="ltr">{oldest}</bdi></p></section>')

    def assemble(nums):
        toc = f'<section class="kb-page" data-front="1"><h2>{T(L["toc"])}</h2><ol class="toc">{toc_html(parts_info, nums)}</ol></section>'
        root_tag = '<html dir="rtl" lang="ar">' if rtl else f'<html lang="{lang}">'
        doc = (f'<!doctype html>{root_tag}<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
               f'<title>{H.escape(title)}</title><style>{CSS}{CSS_RTL if rtl else ""}</style></head><body>'
               + cover + front + toc + glance + method + "".join(body) + "</body></html>")
        return standins(doc, rtl)

    html_path, pdf_path = outdir / f"{stem}.html", outdir / f"{stem}.pdf"
    foot_txt = standins(H.escape(title), rtl)
    footer = (f'<div {"dir=rtl " if rtl else ""}style="width:100%;text-align:center;font-size:8pt;color:#5d6b70">{foot_txt} · <span class="pageNumber"></span></div>')
    md = f"# {title}\n\n{L['oldest']}: {oldest}\n\n## {L['method']}\n\n" + L["method_text"].format(n=n_items, misses=a["misses"], upper=f"{a['upper'] * 100:.1f}") + "".join("\n\n" + t for t in disc_txt) + "\n\n---\n\n" + "\n\n---\n\n".join(md_chunks) + "\n"
    (outdir / f"{stem}.md").write_text(md, encoding="utf-8", newline="\n")
    nums = {}
    html_path.write_text(assemble(nums), encoding="utf-8", newline="\n")
    info = dict(html=html_path, pdf=pdf_path, svg=n_svg, entries=len(entries), pages=sum(1 for e in entries if e[0] == "page"), prints=0, outline=None)
    if not render:
        print(f"built {html_path.name}: {info['pages']} pages, {n_svg} svg, html only")
        return info
    # ---- two-print TOC pass (+ at most one extra print)
    ids_in_order = []
    for pt, part_id, items in parts_info:
        ids_in_order.append(part_id); ids_in_order += [i for _, i in items]
    # entries (kind,title) order equals ids_in_order order; the appendix has no items
    marker = key(L["pages_in_part"](len(parts[0][1])))
    prev = None
    for attempt in range(3):
        render_pdf(html_path, pdf_path, footer)
        info["prints"] += 1
        found = locate_pages(pdf_texts(pdf_path), entries, marker)
        if found is None or None in found:
            raise SystemExit("FAIL TOC: could not locate " + ("the first part divider" if found is None else str([e[1] for e, f in zip(entries, found) if f is None][:4])) + " in the PDF text")
        nums = dict(zip(ids_in_order, found))
        if nums == prev:
            break
        if attempt == 2:
            raise SystemExit("FAIL TOC page numbers did not settle after 3 prints")
        prev = nums
        html_path.write_text(assemble(nums), encoding="utf-8", newline="\n")
    if rtl and REPAIR.is_file():
        subprocess.run([sys.executable, str(REPAIR), str(pdf_path)], check=True, capture_output=True)
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        info["outline"] = len(fitz.open(str(pdf_path)).get_toc())
        if not info["outline"]:
            print("NOTE the renderer wrote 0 bookmarks: it ignores the `outline` option (patch render-pdf.mjs)")
    except ImportError:
        print("NOTE pymupdf not installed: bookmark count not read")
    print(f"built {pdf_path.name}: {info['pages']} pages, {n_svg} svg, {info['prints']} prints, outline={info['outline']}, audit n={a['n']} misses={a['misses']}")
    return info


def selftest():
    parts_cfg = {"parts": [["P1", ["a/x.md", "a/y.md"]], ["P2", ["b/*.md"]]]}
    d = Path(tempfile.mkdtemp())
    try:
        for rel in ("a/x.md", "a/y.md", "b/m.md", "b/n.md", "b/_skip.md"):
            (d / rel).parent.mkdir(exist_ok=True); (d / rel).write_text("# T\n")
        p, e = expand_parts(parts_cfg, d)
        assert p == [("P1", ["a/x.md", "a/y.md"]), ("P2", ["b/m.md", "b/n.md"])] and e == [], (p, e)
        (d / "c").mkdir(); (d / "c" / "z.md").write_text("# T\n")
        assert any("in no part" in x for x in expand_parts(parts_cfg, d)[1]), "a page in no part was not reported"
        assert any("not found" in x for x in expand_parts({"parts": [["P", ["a/none.md"]]]}, d)[1])
    finally:
        shutil.rmtree(d, ignore_errors=True)
    assert prefix_ids('<h2 id="x">a</h2><a href="#x">l</a>', "p3") == '<h2 id="p3-x">a</h2><a href="#p3-x">l</a>'
    svg = '<svg id="m"><defs><marker id="a"/></defs><path marker-end="url(#a)"/><style>#m .n{fill:red}</style></svg>'
    u = uniq_svg(svg, "p1-1")
    assert 'id="p1-1-m"' in u and "url(#p1-1-a)" in u and "#p1-1-m .n" in u, u
    ids1 = re.findall(r'id="([^"]+)"', uniq_svg(svg, "p1")) + re.findall(r'id="([^"]+)"', uniq_svg(svg, "p2"))
    assert len(ids1) == len(set(ids1)), "two diagrams share ids"
    assert standins("a → b ≥ c", False) == "a › b >= c" and standins("x ← y", True) == "x › y"
    assert bidi("اكتب (a) و b") .count('<bdi dir="ltr">') == 2
    assert key("Part I — Foundation") == "partifoundation"
    # TOC numbers from heading ORDER: the TOC page repeats every title and must not be matched
    texts = ["Title", "Table of contents\nPart One\nAlpha\nBeta\n", "Alpha\nglance mention of Beta", "Part One\n2 page(s) in this part.", "Alpha\nbody", "see Beta in text\n", "Beta\nbody"]
    ent = [("part", "Part One"), ("page", "Alpha"), ("page", "Beta")]
    assert locate_pages(texts, ent, key("2 page(s) in this part.")) == [4, 5, 7], locate_pages(texts, ent, key("2 page(s) in this part."))
    assert locate_pages(texts[:3], ent, key("2 page(s) in this part.")) is None
    # ---- round-3 breaks (F11)
    assert '<bdi dir="ltr">+25%</bdi>' in bidi("الوقت 60 دقيقة (+25%)"), "B13: a signed percentage lost its sign to the RTL run"
    assert '<bdi dir="ltr">-5</bdi>' in bidi("الفرق -5 فقط") and "<bdi dir=\"ltr\">60</bdi>" in bidi("الوقت 60 دقيقة")
    assert diagram_prefix("p5", "MERMAIDPLACEHOLDER1X") != diagram_prefix("p5", "MERMAIDPLACEHOLDER11X"), "B15: diagrams 1 and 11 share an id prefix"
    ids = [i for n in (1, 11, 2, 12) for i in re.findall(r'id="([^"]+)"', uniq_svg('<svg id="m"><g id="a"/></svg>', diagram_prefix("p5", f"MERMAIDPLACEHOLDER{n}X")))]
    assert len(ids) == len(set(ids)), "B15: svg ids collide between diagrams 1/11 and 2/12"
    locs = locate_pages(["x", "Glossary\n9 page(s) in this part.", "Glossary\nbody", "Zeta\nbody"], [("part", "Glossary"), ("page", "Glossary"), ("page", "Zeta")], key("9 page(s) in this part."))
    assert locs == [2, 3, 4], f"B14: a part and its first page with one title: {locs}"
    bank = cp.parse_bank("### Q-1\nobjective: T-1 \u00b7 chapter: 2 \u00b7 level: K2\nstem: Which one?\na) first b) second\nbasis: KB#5\nwhy-not: a = x\n", "Q-1: b\n")
    bh, kh = bank_html(bank, False), keys_html(bank, False)
    assert bh.count("<li>") == 2 and "Which one?" in bh and "<ol" in bh, f"B2: bank not rendered option-per-line: {bh}"
    assert "T-1" not in bh and "KB#5" not in bh and "K2" not in bh and "basis" not in bh and "26/40" not in bh, f"C3: the learner-facing bank hints at the answer: {bh}"
    bank_c = cp.parse_bank("### Q-1\nobjective: T-1\nlevel: K2\nstem: Rate?\na) 60 b) 65 c) 70\n", "Q-1: b\nwhy-not: a = x\ncalc: 26/40*100\nbasis: KB#5\n")
    kc = keys_html(bank_c, False)
    assert "26/40*100" in kc and "KB#5" in kc and "a = x" in kc and ">b<" in kc.replace("</bdi>", "<").replace('<bdi dir="ltr">', ">"), f"C3: the key part must carry key, why-not, calc and basis: {kc}"
    assert "<b>Calc:</b>" in kc and "<b>Basis:</b>" in kc and "<b>Key:</b>" in kc and "<b>Why not:</b>" in kc and "Rate?" not in kc, kc
    assert "<b>Key:</b>" in kh and ">b<" in kh.replace("</bdi>", "<").replace('<bdi dir="ltr">', ">") and "a = x" in kh, kh
    if shutil.which("pandoc"):
        assert 'id="FL-4.2.1"' in pandoc_html("#### Boundary values {#FL-4.2.1}\n\n[x](#FL-4.2.1)\n") and "{#" not in pandoc_html("#### Boundary values {#FL-4.2.1}\n"), "B1: header attributes printed instead of applied"
    d_ = Path(tempfile.mkdtemp())
    try:
        (d_ / "p.md").write_text("```bash\n# not a title\n```\n# Real title\ntext\n", encoding="utf-8")
        assert page_title(d_ / "p.md") == "Real title", "v6.1: a `# comment` in a fence was taken as the page title"
    finally:
        shutil.rmtree(d_, ignore_errors=True)
    assert 'class="pg">000' in toc_html([("P", "part1", [("A", "p2")])], {}) and 'class="pg">7' in toc_html([("P", "part1", [("A", "p2")])], {"p2": 7})
    # the report refuses without a passing audit (no sample at all)
    d = Path(tempfile.mkdtemp())
    try:
        cfg = {"title": "T", "slug": "t", "pages": "ch", "parts": [["P", ["a.md"]]]}
        (d / "ch").mkdir(); (d / "ch" / "a.md").write_text("# A\n")
        try:
            build(cfg, render=False, root=d); raise AssertionError("built without an audit")
        except SystemExit as ex:
            assert "audit gate" in str(ex), ex
        (d / "audit").mkdir()
        (d / "audit" / "entries.md").write_text("# Audit sample\n<!-- audit: entries=30/100 -->\n| id | claim | quote | raw | verdict |\n|---|---|---|---|---|\n| 1 | c | q | f:1 | missed: no |\n")
        try:
            build(cfg, render=False, root=d); raise AssertionError("built with a missed audit row")
        except SystemExit as ex:
            assert "audit gate" in str(ex), ex
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("selftest ok"); return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    try:
        cfg = cp.load_cfg()
    except cp.ConfigError as e:
        print(f"FAIL {e}"); return 1
    miss = tools_missing(need_mermaid=False) if "--no-render" not in argv else [t for t in ("pandoc",) if not shutil.which(t)]
    if miss:
        print("SKIP missing tools: " + ", ".join(miss) + " -- the report was not built (exit 3 = incomplete, not a failed gate)"); return 3
    try:
        build(cfg, twin="--twin" in argv, render="--no-render" not in argv)
    except SystemExit as e:
        print(e if isinstance(e.code, str) else f"FAIL exit {e.code}"); return 1
    except subprocess.CalledProcessError as e:
        print("FAIL " + (e.stderr or str(e))[-300:]); return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
