#!/usr/bin/env python3
"""check_report.py -- gate for the built report (HTML + PDF). Every number it compares is DERIVED, never a literal.

    check_report.py [--twin]
    check_report.py --selftest

Project = BOOK_ROOT env or cwd; book.json as for build_report.py.
Exit 0 only if every check ran and none failed. Exit 1 = a FAIL line. Exit 3 = a SKIP line (a check that could not run:
pymupdf / fontTools missing, or poppler missing) -- the last line then says INCOMPLETE, never PASS.
  titles     every page title from the SOURCE files is in the BODY of the PDF (the TOC pages are skipped, so a deleted chapter
             whose title still sits in the TOC fails); a twin must have exactly the source's page list
  words      pdftotext words / (source words + front-matter words + footer words) within 0.95-1.06
  svg        inline <svg> in the HTML == mermaid fences in the source pages (a book with none must have none)
  fonts      every pdffonts row is Thmanyah (hard-coded and not overridable)
  outline    PDF bookmarks >= parts + pages (pymupdf; SKIP if not importable)
  toc        every printed TOC number equals the page where that title really starts in the PDF (off-by-one fails)
  links      every href="#id" in the HTML has a target
  ids        no duplicate id attribute in the HTML
  rtl        --twin (ar): <html dir="rtl" lang="ar">; every inline SVG holds Arabic text, and an LTR book's SVGs hold none
  glyphs     every visible codepoint is covered by a Thmanyah cmap (fontTools; SKIP if not importable)
  audit      audit/entries.md and audit/banks.md pass for the topics built (n, misses, 95 % upper bound printed)
  glance     (optional) each glance row's must_appear strings occur in its source page
"""
import json, os, re, shutil, subprocess, sys, unicodedata
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_pages as cp
import audit_sample as au
import build_report as br
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = cp.ROOT
FONT_DIR = Path.home() / ".claude" / "skills" / "pdf-typography" / "fonts" / "licensed"
ALLOWED = ["thmanyah"]  # the house rule: Thmanyah only. Cairo/Arial/Times fall out because nothing else is allowed.
INVISIBLE = re.compile("[​-‏‪-‮⁦-⁩﻿︎️­]")


def key(s):
    return "".join(c for c in unicodedata.normalize("NFKC", s).lower() if c.isalnum())


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def src_words(md):
    """Words a reader of the source sees: markdown-only tokens (fences, rules, table pipes/separators, heading #) dropped."""
    n = 0
    for ln in md.split("\n"):
        s = ln.strip()
        if s.startswith("```") or re.fullmatch(r"[|:\-\s]+", s) or s.startswith("<!--"):
            continue
        for tok in s.split():
            if re.fullmatch(r"#{1,6}|\||>+", tok):
                continue
            n += 1
    return n


def html_words(html_text):
    t = re.sub(r"<(script|style)\b.*?</\1>", " ", html_text, flags=re.S)
    return len(re.sub(r"<[^>]+>", " ", t).split())


def front_words(html):
    """Words in the sections build_report marks data-front (cover, TOC, Method, dividers...)."""
    n = 0
    for m in re.finditer(r'<section\b[^>]*data-front="1"[^>]*>(.*?)</section>', html, re.S):
        n += html_words(m.group(1))
    return n


def dup_ids(html):
    ids = re.findall(r'<[^>]+\sid="([^"]+)"', re.sub(r"<style\b.*?</style>", "", html, flags=re.S))
    return sorted({i for i in ids if ids.count(i) > 1})


def svg_texts(html):
    return [re.sub(r"<[^>]+>", " ", s) for s in re.findall(r"<svg\b.*?</svg>", html, re.S)]


def fonts_bad(pdffonts_text):
    rows = [r for r in pdffonts_text.splitlines()[2:] if r.strip()]
    bad = [r.split()[0] for r in rows if not any(a in r.split()[0].split("+")[-1].lower() for a in ALLOWED)]
    return len(rows), bad


def dead_links(html):
    """href="#x" with no element id x."""
    body = re.sub(r"<style\b.*?</style>", "", html, flags=re.S)
    ids = set(re.findall(r'\sid="([^"]+)"', body))
    return sorted({h for h in re.findall(r'href="#([^"]*)"', body) if h not in ids})


def toc_entries(html):
    """[(id, title text, printed number)] in TOC order."""
    import html as H
    sec = re.search(r'<ol class="toc">(.*?)</ol></section>', html, re.S)
    out = []
    for m in re.finditer(r'<a href="#([^"]+)">(.*?)</a>(?:</b>)?<span class="lead"></span><span class="pg">(\d+)</span>', sec.group(1) if sec else "", re.S):
        out.append((m.group(1), H.unescape(re.sub(r"<[^>]+>", "", m.group(2))).strip(), int(m.group(3))))
    return out


def toc_mismatches(html, texts, marker_key):
    """Entries whose printed number differs from the page where the title starts in the PDF (or cannot be found)."""
    ent = toc_entries(html)
    if not ent:
        return ["no TOC entries with page numbers"]
    found = br.locate_pages(texts, [("x", t) for _, t, _ in ent], marker_key)
    if found is None:
        return ["the first part divider is not in the PDF text"]
    return [f"'{t[:30]}' printed {n}, starts on {f}" for (_, t, n), f in zip(ent, found) if f != n]


def verdict(lines):
    """-> (final line, exit code). A SKIP is never a pass."""
    if any(l.startswith("FAIL") for l in lines):
        return f"FAIL {sum(l.startswith('FAIL') for l in lines)} check(s)", 1
    if any(l.startswith("SKIP") for l in lines):
        return f"INCOMPLETE {sum(l.startswith('SKIP') for l in lines)} check(s) skipped -- install what the SKIP lines name; this is not a pass", 3
    return "PASS", 0


def glyph_gaps(visible_text):
    """Codepoints in the text that no Thmanyah font covers -> (sorted list, error|None)."""
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return [], "fontTools not importable"
    files = sorted(FONT_DIR.glob("Thmanyah*.ttf"))
    if not files:
        return [], f"no Thmanyah fonts in {FONT_DIR}"
    cov = set()
    for f in files:
        cov |= set(TTFont(str(f), lazy=True).getBestCmap())
    need = {ord(c) for c in INVISIBLE.sub("", visible_text) if unicodedata.category(c) not in ("Cc", "Cf", "Zs", "Zl", "Zp") or c == " "}
    return sorted(f"U+{c:04X} {chr(c)}" for c in need - cov if chr(c) not in " \n\t"), None


def visible_text(html):
    t = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.S)
    import html as H
    return H.unescape(re.sub(r"<[^>]+>", " ", t))


def check(cfg, twin=False, root=None):
    """-> (lines, failures). Each line starts with ok / FAIL / SKIP."""
    root = Path(root or ROOT)
    out, fails = [], 0

    def emit(tag, msg):
        nonlocal fails
        out.append(f"{tag:4} {msg}")
        fails += tag == "FAIL"
    rtl = twin and (cfg.get("twin_lang") or "ar") == "ar"
    pages_root = root / (cfg["twin"] if twin else cfg["pages"])
    outdir = root / ((cfg.get("twin_report") or "report-ar") if twin else cfg.get("report", "report"))
    stem = cfg["slug"] + ("-ar" if twin else "")
    pdf, html_p = outdir / f"{stem}.pdf", outdir / f"{stem}.html"
    if not pdf.is_file() or not html_p.is_file():
        return [f"FAIL no {pdf.name} / {html_p.name} in {outdir} -- run build_report.py"], 1
    html = html_p.read_text(encoding="utf-8")
    text = run(["pdftotext", "-enc", "UTF-8", str(pdf), "-"])
    pdf_pages = len(text.split("\f")) - 1
    pages = sorted(p for p in pages_root.rglob("*.md") if not p.name.startswith("_"))
    bdir = root / ((cp.twin_bank_dir(cfg) if twin else cfg.get("practice")) or "practice")
    banks = [p for p in sorted(bdir.glob("*.md")) if not p.name.startswith("_") and not p.name.endswith(".key.md")] if (cfg.get("banks") or {}).get("print", True) and bdir.is_dir() else []
    rdir = root / (cfg.get("rules") or "kb/rules")
    rules = [p for p in sorted(rdir.glob("*.md")) if p.name != "INDEX.md"] if rdir.is_dir() else []

    # twin: the file list must equal the source's
    if twin:
        names = lambda r: {p.relative_to(r).as_posix() for p in r.rglob("*.md") if not p.name.startswith("_")}
        sset, tset = names(root / cfg["pages"]), names(pages_root)
        emit("FAIL" if sset != tset else "ok", f"twin list: {len(tset)} pages vs {len(sset)} in the source" + (f"; missing {sorted(sset - tset)[:5]}, extra {sorted(tset - sset)[:5]}" if sset != tset else ""))
    # body text: the pages after the first part divider (the TOC repeats every title and must not satisfy the check)
    texts = text.split("\f")
    L = br.LABELS["ar" if rtl else "en"]
    try:
        parts, _ = br.expand_parts(dict(cfg, parts=cfg["parts"]), pages_root)
        marker = key(L["pages_in_part"](len(parts[0][1])))
    except Exception:
        marker = ""
    start = next((i for i, t in enumerate(texts) if marker and marker in key(t)), None)
    body_texts = texts[start:] if start is not None else texts
    if start is None:
        emit("FAIL", "titles: the first part divider is not in the PDF text, so the body cannot be told from the TOC")
    # titles (from the source list, not the built list)
    tk, words = key("".join(body_texts)), {key(w) for w in " ".join(body_texts).split()}
    missing = []
    for p in pages:
        t = next((l[2:].strip() for l in cp.mask_fences(p.read_text(encoding="utf-8")).splitlines() if l.startswith("# ")), None)
        if t is None:
            missing.append(f"{p.name} (no H1)"); continue
        if key(t) not in tk:
            ws = [key(w) for w in t.split() if key(w)]
            if not (len(ws) >= 3 and all(w in words or w in tk for w in ws)):  # poppler may reorder an Arabic line
                missing.append(p.name)
    emit("FAIL" if missing else "ok", f"titles: {len(pages) - len(missing)}/{len(pages)} source page titles found in the PDF text" + (f"; missing {missing[:6]}" if missing else ""))

    # words
    chunks = [p.read_text(encoding="utf-8") for p in pages + banks + rules]
    src = sum(src_words(c) for c in chunks)
    foot = pdf_pages * (len((cfg.get("twin_title") if twin and cfg.get("twin_title") else cfg["title"]).split()) + 2)
    expect = src + front_words(html) + foot
    got = len(text.split())
    ratio = got / expect if expect else 0
    emit("ok" if 0.95 <= ratio <= 1.06 else "FAIL", f"words: pdf {got} / expected {expect} (source {src} + front matter {front_words(html)} + footers {foot}) = {ratio:.3f}, band 0.95-1.06")

    # svg
    fences = sum(len(re.findall(r"^```mermaid\s*$", c, re.M)) for c in chunks)
    svgs = html.count("<svg")
    emit("ok" if svgs == fences else "FAIL", f"svg: {svgs} inline diagrams == {fences} mermaid fences in the source")

    # fonts
    nrows, bad = fonts_bad(run(["pdffonts", str(pdf)]))
    emit("FAIL" if bad or not nrows else "ok", f"fonts: {nrows} pdffonts rows, non-Thmanyah: {bad or 'none'}")

    # outline
    n_parts = len(cfg["parts"]) + (1 if banks else 0) + (1 if banks else 0) + (1 if rules else 0)
    want = n_parts + len(pages) + len(banks)
    try:
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        toc = fitz.open(str(pdf)).get_toc()
        emit("ok" if len(toc) >= want else "FAIL", f"outline: {len(toc)} bookmarks >= {want} (parts + pages)")
    except ImportError:
        emit("SKIP", "outline: pymupdf not importable, bookmarks not counted")

    # toc numbers: each must be the page where that title starts
    mism = toc_mismatches(html, texts, marker) if marker else ["no divider phrase to anchor the body"]
    emit("FAIL" if mism else "ok", f"toc: {len(toc_entries(html))} entries" + ("; all printed numbers equal the PDF page of their title" if not mism else f"; {mism[:3]}"))

    d = dup_ids(html)
    emit("FAIL" if d else "ok", f"ids: {'duplicate ' + str(d[:5]) if d else 'no duplicate id attributes'}")
    dl = dead_links(html)
    emit("FAIL" if dl else "ok", f"links: {'dead internal link(s) ' + str(dl[:5]) if dl else 'every internal link has a target'}")

    # rtl / svg language
    if twin and rtl:
        emit("ok" if '<html dir="rtl" lang="ar">' in html[:300] else "FAIL", 'html root is <html dir="rtl" lang="ar">')
    arabic = re.compile("[؀-ۿ]")
    st = svg_texts(html)
    wrong = [i + 1 for i, t in enumerate(st) if bool(arabic.search(t)) != rtl]
    emit("FAIL" if wrong else "ok", f"svg text: {len(st)} diagram(s) {'all hold Arabic' if rtl else 'hold no Arabic'}" + (f"; wrong in #{wrong[:5]}" if wrong else ""))

    # glyphs
    gaps, err = glyph_gaps(visible_text(html))
    if err:
        emit("SKIP", f"glyphs: {err}")
    else:
        emit("FAIL" if gaps else "ok", f"glyphs: {'no codepoint outside the Thmanyah cmaps' if not gaps else 'not covered: ' + ' '.join(gaps[:12])}")

    a = au.summarize(root, topics=au.report_topics(cfg, pages_root))
    emit("ok" if a["ok"] else "FAIL", "audit: " + a["msg"])

    if cfg.get("glance") and not twin and (root / cfg["glance"]).is_file():
        bad = []
        for r in json.loads((root / cfg["glance"]).read_text(encoding="utf-8")):
            src_p = pages_root / r["page"]
            body = src_p.read_text(encoding="utf-8") if src_p.is_file() else ""
            bad += [f"{r['page']}: '{m}'" for m in r.get("must_appear", []) if m not in body]
        emit("FAIL" if bad else "ok", f"glance: {'all must_appear strings found in their pages' if not bad else bad[:4]}")
    return out, fails


def selftest():
    assert src_words("# H\n| a | b |\n|---|---|\n```\ncode here\n```\n- item one\n> quote") == 9, src_words("# H\n| a | b |\n|---|---|\n```\ncode here\n```\n- item one\n> quote")
    assert dup_ids('<p id="a"></p><p id="b"></p><div id="a"></div><style>#a{}</style>') == ["a"]
    assert dup_ids('<p id="a"></p><p id="p2-a"></p>') == []
    assert svg_texts('<svg><text>x</text></svg><p/><svg><text>ب</text></svg>')[1].strip() == "ب"
    pdffonts = "name type\n----\nABCDEF+ThmanyahSans-Regular  CID TrueType\nABCDEF+ThmanyahSerifDisplay-Bold  CID TrueType\n"
    assert fonts_bad(pdffonts) == (2, [])
    n, bad = fonts_bad(pdffonts + "ABCDEF+Times-Roman  Type 1\nAAAAAA+Arial-Bold  CID TrueType\n")
    assert n == 4 and len(bad) == 2, bad
    assert front_words('<section class="cover" data-front="1"><h1>a b</h1></section><section class="kb-page"><p>x y z</p></section>') == 2
    gaps, err = glyph_gaps("plain text and an arrow → and ≥")
    if err is None:
        assert any("2192" in g for g in gaps) and not any(c in "".join(gaps) for c in "plain"), gaps  # Thmanyah has no arrows
    else:
        print("SKIP selftest glyph cmaps:", err)
    assert 0.95 <= 1.0 <= 1.06 and not (0.95 <= 0.5 <= 1.06)
    # ---- round-3 breaks (F10)
    n, bad = fonts_bad("name\n----\nABCDEF+Cairo-Regular  CID TrueType\nABCDEF+ThmanyahSans-Regular  CID TrueType\nAAAAAA+Arial-Bold  CID\n")
    assert n == 3 and len(bad) == 2, "B10: Cairo/Arial must fail; there is no fonts_allowed to widen the list"
    assert "fonts_allowed" not in open(__file__, encoding="utf-8").read().split("def selftest")[0].split("def check(")[1], "fonts_allowed must not be read"
    assert verdict(["ok a", "SKIP outline: pymupdf not importable", "ok b"]) == ("INCOMPLETE 1 check(s) skipped -- install what the SKIP lines name; this is not a pass", 3), "B8: a SKIP printed PASS"
    assert verdict(["ok a"]) == ("PASS", 0) and verdict(["ok a", "FAIL b", "SKIP c"])[1] == 1
    assert dead_links('<h2 id="p1-x">a</h2><a href="#p1-x">ok</a><a href="#FL-4.2.1">dead</a>') == ["FL-4.2.1"], "B1: a link with no target passed"
    toc = '<ol class="toc"><li><b><a href="#part1">Part One</a></b><span class="lead"></span><span class="pg">3</span><ol><li><a href="#p2">Alpha</a><span class="lead"></span><span class="pg">4</span></li></ol></li></ol></section>'
    texts = ["Cover", "Table of contents\nPart One\nAlpha", "x", "Part One\n1 page(s) in this part.", "Alpha\nbody"]
    assert toc_mismatches(toc, texts, br.key("1 page(s) in this part.")), "B9: a TOC one page off (printed 3/4, real 4/5) passed"
    texts = ["Cover", "Table of contents\nPart One\nAlpha", "Part One\n1 page(s) in this part.", "Alpha\nbody"]
    assert toc_mismatches(toc.replace(">3<", ">3<").replace(">4</span></li>", ">4</span></li>"), texts, br.key("1 page(s) in this part.")) == [], toc_mismatches(toc, texts, br.key("1 page(s) in this part."))
    print("selftest ok"); return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    try:
        cfg = cp.load_cfg()
    except cp.ConfigError as e:
        print(f"FAIL {e}"); return 1
    if not shutil.which("pdftotext") or not shutil.which("pdffonts"):
        print("SKIP poppler (pdftotext, pdffonts) is not installed -- nothing was checked"); print("INCOMPLETE"); return 3
    lines, fails = check(cfg, twin="--twin" in argv)
    print("\n".join(lines))
    last, code = verdict(lines)
    print(last)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
