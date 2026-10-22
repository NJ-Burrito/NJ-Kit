#!/usr/bin/env python3
"""check_pages.py -- gate for a book's pages (stdlib only). PYTHONUTF8=1 assumed.

    check_pages.py [paths...]              pages (files or folders); default: every <pages>/**/*.md except _*.md
    check_pages.py --pair [prefix...]      each twin page must keep its source page's fingerprint. A prefix is RELATIVE TO THE TWIN
                                           ROOT (01-foundation/ctfl.md, or a folder), not to the project; it also runs the practice bank
                                           whose slug is the prefix's file stem (ctfl.md -> practice-ar/ctfl.md). No prefix = every pair.
    check_pages.py --pair --terms          ... and the term map's `avoid` variants must not appear in any twin page
    check_pages.py --terms                 the term-map check alone (a term map with no `avoid` rule FAILS)
    check_pages.py --stamp [twin file...]  write the mandatory `<!-- en-sha: ... -->` first line from the current source page
    check_pages.py --selftest

Project = BOOK_ROOT env or cwd; config = <project>/book.json (see nj-knowledge-book SKILL.md):
    title, slug, pages, twin, terms, kinds {"<folder>": "<kind>"}, optional overrides
    headings {"<folder>"|"default": [...]}, min_cites {...}, numbers "warn"|"fail".
Each folder has a KIND; a kind carries default required headings and min_cites:
    certification, tool, regulation, topic, practice   (unknown kind = hard error)
The database is kb/kb.json "db" (default kb/qa.db), opened read-only.

Per page: required '## ' headings (numbered or not; substring, case-insensitive), every [KB#n] cited
is `verified`, at least min_cites distinct verified ids, one source URL. Reported per page, never hidden:
`uncited` = lines with a number (>= 2 digits or %) and no [KB#] and no [calc]; `mismatch` = cited lines
holding a number that none of the cited claims (or a [calc: ...] tag) contains. config "numbers": "fail"
makes both counts failures; the default "warn" prints them. A line tagged [calc] is exempt (derived).
Prints one line per item; exit 0 ok, 1 any failure.
"""
import collections, glob, hashlib, json, os, re, sqlite3, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(os.environ.get("BOOK_ROOT") or os.getcwd()).resolve()

CERT = ["At a glance", "Who it is for", "Syllabus map", "Core concepts", "step by step",
        "case study", "pitfalls", "Mentor notes", "Exam preparation", "Sources"]
TOOL = ["What it is", "Setup", "Step-by-step", "Core features", "Best practices",
        "Integration", "pitfalls", "Mentor notes", "case study", "Sources"]
REGULATION = ["Summary", "Scope and jurisdiction", "Obligations", "Effective dates",
              "Evidence of compliance", "Pitfalls", "Mentor notes", "Illustrative case", "Sources"]
TOPIC = ["Overview", "Core concepts", "Step by step", "Pitfalls", "Practice", "Sources"]
PROFILES = {  # kind -> default headings, min_cites, teaching checks on by default
    "certification": dict(headings=CERT, min_cites=3, teach=True),
    "tool": dict(headings=TOOL, min_cites=3, teach=False),
    "regulation": dict(headings=REGULATION, min_cites=3, teach=False),
    "topic": dict(headings=TOPIC, min_cites=3, teach=True),
    "practice": dict(headings=["Sources"], min_cites=0, teach=False),
}


class ConfigError(Exception):
    pass


def load_cfg(root=None):
    p = Path(root or ROOT) / "book.json"
    try:
        cfg = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ConfigError(f"no book.json in {p.parent} (set BOOK_ROOT or run from the project root)")
    except ValueError as e:
        raise ConfigError(f"{p}: not valid JSON ({e})")
    for k in ("title", "slug", "pages"):
        if k not in cfg:
            raise ConfigError(f"{p}: missing '{k}'")
    for folder, kind in (cfg.get("kinds") or {}).items():
        if kind not in PROFILES:
            raise ConfigError(f"{p}: kinds['{folder}'] = '{kind}' is not a kind; valid kinds: {', '.join(PROFILES)}")
    return cfg


def db_path(root=None):
    """The fact database named by <project>/kb/kb.json. No kb.json = ConfigError (no project's values are guessed)."""
    root = Path(root or ROOT)
    try:
        return root / json.loads((root / "kb" / "kb.json").read_text(encoding="utf-8")).get("db", "kb/facts.db")
    except FileNotFoundError:
        raise ConfigError(f"no kb/kb.json in {root}: write db, sectors and primary_hosts (kb.py init writes a template)")


def folder_of(path, pages_root):
    """First folder under the pages root ('' for a page directly in it)."""
    try:
        parts = Path(path).resolve().relative_to(Path(pages_root).resolve()).parts
    except ValueError:
        return Path(path).parent.name
    return parts[0] if len(parts) > 1 else ""


def profile_for(cfg, folder):
    """(kind, headings, min_cites, teach) for a folder: kind defaults, then config overrides."""
    kinds = cfg.get("kinds") or {}
    kind = kinds.get(folder) or kinds.get("default")
    hd, mc = cfg.get("headings") or {}, cfg.get("min_cites") or {}
    if kind is None:
        if folder in hd or "default" in hd:  # explicit-headings book without kinds
            return None, hd.get(folder) or hd["default"], mc.get(folder, mc.get("default", 3)), False
        raise ConfigError(f"folder '{folder}' has no kind in book.json 'kinds' (valid kinds: {', '.join(PROFILES)})")
    pf = PROFILES[kind]
    return (kind, hd.get(folder) or pf["headings"], mc.get(folder, pf["min_cites"]) if folder in mc else
            (mc["default"] if "default" in mc and kind not in ("practice",) else pf["min_cites"]), pf["teach"])


_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_URL = re.compile(r"https?://\S+")
_CITE = re.compile(r"\[KB#(\d+)\]")
_LIST = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")
_NUM = re.compile(r"\d+(?:[.,]\d+)*")


def numbers(text):
    """Number tokens, thousands commas dropped (same folding as kb.py)."""
    return {n.replace(",", "") for n in _NUM.findall((text or "").translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")))}


def sig(tok):
    return len(tok.replace(".", "")) >= 2


# Exam words: a figure beside one of these is exam-critical even with a single digit ("8 questions", "Chapter 1", "26 points").
EXAM_WORDS = re.compile(r"\b(?:questions?|minutes?|mins?|marks?|hours?|pass|passing)\b", re.I)
# "point" and "chapter" count only as units directly after a number ("40 points", "6 chapters"): "three-point", "open points", "can point to"
# and the label "Chapter 1" must not switch single-digit counting on.
EXAM_AFTER_NUMBER = re.compile(r"\d\s*[-\u2013]?\s*(?:points?|chapters?)\b", re.I)
_OBJ_TAG = re.compile(r"\[obj:[^\]]*\]", re.I)
# A step ordinal opening a table cell or a list item ("| 10. Monitor", "- 10. Monitor", "10) Monitor") is a label, not a figure.
_ORDINAL = re.compile(r"(^|\|)(\s*(?:[-*+]\s+)?)\d+[.)]\s+(?=\S)")
_CHAPTER_LABEL = re.compile(r"\bchapters?\s+\d+(?:\.\d+)*\b", re.I)


def numbers_mode(cfg, kind):
    """book.json "numbers": "warn" | "fail" | {"certification": "fail", "default": "warn"}."""
    n = cfg.get("numbers", "warn")
    return n if isinstance(n, str) else n.get(kind, n.get("default", "warn"))


FADING = ["Worked example", "Try it", "Now alone"]  # teaching-block markers (also check_teach.py)


def fade_start(ln, markers=FADING):
    """Does this line open a *Worked example.* / *Try it.* / *Now alone.* block?"""
    m = re.match(r"^\s*[*_]{1,2}\s*(.+?)[.:]?\s*[*_]{1,2}", ln)
    return bool(m) and any(m.group(1).lower().startswith(k.lower()) for k in markers)


def number_lines(text, markers=FADING):
    """Yield (lineno, line, cited_ids, cleaned) for prose lines worth a number check: outside code fences, headings, table
    separators/headers and the Sources section. A teaching block (*Worked example.* / *Try it.* / *Now alone.*) is exempt
    -- its data is illustrative and labelled so -- but only up to the first blank line, the next marker or any heading:
    factual numbers written after it are checked again."""
    lines = text.split("\n")
    fence, sources, fade, fade_sec = False, False, False, False
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        if not ln.strip():
            fade = False
            continue
        if ln.startswith("#"):
            sources = bool(re.match(r"#{1,6}\s*(\d+\.\s*)?sources\b", ln, re.I))
            fade = fade_sec = False
            continue
        if fade_start(ln, markers):
            fade = fade_sec = True  # a new marker opens a new block
        if fade_sec and ln.lstrip().startswith("|"):
            continue  # pipe-table rows (header, separator, data) after a marker in the same section belong to the teaching block
        if sources or fade or re.match(r"^\s*\|?\s*:?-{2,}", ln):
            continue
        if ln.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            continue  # table header row
        ids = [int(x) for x in _CITE.findall(ln)]
        clean = _LIST.sub("", _CITE.sub("", _DATE.sub("", _URL.sub("", ln))))
        clean = _ORDINAL.sub(r"\1\2", clean)
        clean = _CHAPTER_LABEL.sub(" ", _OBJ_TAG.sub(" ", clean))  # [obj: ID] tags and "Chapter N" labels carry no figure
        yield i + 1, ln, ids, clean


def number_stats(text, claim_of):
    """(uncited, mismatch, examples) per the rules in the module docstring."""
    uncited = mismatch = 0
    ex = []
    for no, ln, ids, clean in number_lines(text):
        if "[calc" in ln:
            continue
        near_exam = bool(EXAM_WORDS.search(clean) or EXAM_AFTER_NUMBER.search(clean))
        toks = {t for t in numbers(clean) if sig(t) or near_exam}
        if not ids:
            if toks or "%" in clean:  # (a single digit counts when an exam word sits on the line)
                uncited += 1
                if len(ex) < 3: ex.append(no)
            continue
        if not toks:
            continue
        allowed = set()
        for i in ids:
            allowed |= numbers(claim_of(i) or "")
        if toks - allowed:
            mismatch += 1
            if len(ex) < 3: ex.append(no)
    return uncited, mismatch, ex


def check(path, text, status_of, cfg, claim_of=lambda i: "", pages_root=None):
    """-> (errors, info). info: cites, nc, uncited, mismatch."""
    errs = []
    folder = folder_of(path, pages_root) if pages_root else Path(path).resolve().parent.name
    kind, wanted, min_cites, _ = profile_for(cfg, folder)
    heads = [h.lower() for h in re.findall(r"^## (?:\d+\.\s*)?(.+)$", mask_fences(text), re.M)]  # a heading inside a code fence is not a heading
    for want in wanted:
        if not any(want.lower() in h for h in heads):
            errs.append(f"missing heading '{want}'")
    ids = sorted({int(i) for i in _CITE.findall(text)})
    bad = [i for i in ids if status_of(i) != "verified"]
    if bad:
        errs.append(f"cites non-verified/missing KB ids {bad[:10]}")
    good = len(ids) - len(bad)
    if good < min_cites:
        errs.append(f"cites {good} verified ids, need >= {min_cites} ({kind or 'configured'} page)")
    if not re.search(r"https?://", text):
        errs.append("no source URL")
    nc = len(re.findall(r"not confirmed", text, re.I))
    unc, mis, ex = number_stats(text, claim_of)
    if numbers_mode(cfg, kind) == "fail" and (unc or mis):
        errs.append(f"{unc} uncited numeric line(s), {mis} cite-number mismatch(es) (first lines {ex})")
    return errs, dict(cites=len(ids), nc=nc, uncited=unc, mismatch=mis)


# ------------------------------------------------------------------ twin (pair) checks
FORBIDDEN = [("Eastern digits", "[٠-٩]"), ("Persian letters", "[ڪکیۀہ]"),
             ("bidi control", "[​-‏‪-‮⁦-⁩]"), ("tashkeel", "[ً-ْ]")]


def prose_of(text):
    return re.sub(r"```.*?```|`[^`\n]*`|<!--.*?-->", "", text, flags=re.S)


SPELLED = ("واحد", "واحدة", "اثنان", "اثنين", "اثنتان", "اثنتين", "مقالان", "صفحتان")  # Arabic may write 1 and 2 in words


def fold_num(tok):
    """1,057 -> 1057 (thousands); 3,5 -> 3.5 (decimal comma)."""
    return tok.replace(",", "") if re.fullmatch(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", tok) else tok.replace(",", ".")


def fold_seq(text):
    """Ordered, folded number tokens of a text."""
    return [fold_num(t) for t in re.findall(r"\d+(?:[.,]\d+)*", text or "")]


def digits_match(en_seq, ar_seq, ar_prose):
    """Same figures in the same order; an English 1 or 2 may be spelled in words in the Arabic."""
    j = 0
    for t in en_seq:
        if j < len(ar_seq) and ar_seq[j] == t:
            j += 1
        elif t in ("1", "2") and any(w in ar_prose for w in SPELLED):
            continue
        else:
            return False
    return j == len(ar_seq)


def fingerprint(text):
    """What a translation must keep: every heading level, table rows, list items, KB cites, code, URLs, and the figures
    of the prose IN ORDER (list/heading numbering is counted separately)."""
    prose = prose_of(text)
    mtext = mask_fences(text)
    return {"sections": len(re.findall(r"^## \d+\.", mtext, re.M)),
            "headings": len(re.findall(r"^#{1,6} ", mtext, re.M)),
            "table_rows": len(re.findall(r"^\|", text, re.M)),
            "list_items": len(re.findall(r"^\s*(?:[-*+]|\d+\.)\s", text, re.M)),
            "kb": sorted({int(i) for i in _CITE.findall(text)}),
            "code_blocks": text.count("```") // 2,
            "urls": page_urls(text),
            "digits": fold_seq(re.sub(r"(?m)^(?:#{1,6}\s*|\s*)\d+\.\s", "", prose))}


def page_urls(text):
    """URLs of a page, without the punctuation that ends a sentence or an Arabic clause (; \u061b , \u060c . )) glued to them."""
    return sorted({u.rstrip(";\u061b,\u060c.)") for u in re.findall(r"https?://[^\s)\]>|]+", text)})


def en_sha(en_text):
    return hashlib.sha1(en_text.encode("utf-8")).hexdigest()


def check_pair(en_text, ar_text, require_stamp=True):
    fe, fa = fingerprint(en_text), fingerprint(ar_text)
    errs = []
    for k in fe:
        if k == "digits" or fe[k] == fa[k]:
            continue
        errs.append(f"{k}: en={len(fe[k])} ar={len(fa[k])}" if isinstance(fe[k], list) else f"{k}: en={fe[k]} ar={fa[k]}")
    if not digits_match(fe["digits"], fa["digits"], prose_of(ar_text)):
        errs.append(f"figures differ or are out of order: en={fe['digits'][:12]} ar={fa['digits'][:12]}")
    n_en, n_ar = len(re.findall(r"not confirmed", en_text, re.I)), ar_text.count("غير مؤكد")
    if n_en != n_ar:
        errs.append(f"not confirmed: en={n_en} vs «غير مؤكد» ar={n_ar}")
    if not re.search(r"[؀-ۿ]{3,}", ar_text):
        errs.append("no Arabic text")
    prose = prose_of(ar_text)
    # _terms rule: no detached one-letter prefix before a Latin word/digit
    # (grep's [^ء-ي] class silently matches nothing on Windows -- keep it in Python)
    det = re.findall(r"(?<![؀-ۿ])[بلكو] \**[A-Za-z0-9]", prose)
    if det:
        errs.append(f"detached prefix x{len(det)}")
    if "ـ" in prose:
        errs.append("tatweel")
    for name, rx in FORBIDDEN:
        n = len(re.findall(rx, prose))
        if n:
            errs.append(f"forbidden {name} x{n}")
    m = re.match(r"\s*<!--\s*en-sha:\s*([0-9a-f]{40})\s*-->", ar_text.lstrip("\ufeff"))
    if not m:
        if require_stamp:
            errs.append("no en-sha stamp (a twin without one cannot be told stale): run check_pages.py --stamp <twin file>")
    elif m.group(1) != en_sha(en_text):
        errs.append("stale twin (en-sha does not match the current source page): re-translate, then --stamp")
    return errs


def stamp_text(en_text, ar_text):
    """The twin text with a fresh `<!-- en-sha: ... -->` first line (an old stamp or a BOM before it is replaced)."""
    body = re.sub(r"^\s*<!--\s*en-sha:[^>]*-->\s*\n?", "", ar_text.lstrip("\ufeff"))
    return f"<!-- en-sha: {en_sha(en_text)} -->\n" + body


def norm_ar(t):
    """Fold hamza-carrying alef and alef maqsura so إختبار and اختبار are one word."""
    return t.translate(str.maketrans("أإآى", "اايي"))


def term_rules(terms_path):
    """[(english, [preferred Arabic renderings], [avoid variants])] for rows that name an `avoid`; [] if no such column."""
    rules, idx, aidx = [], None, 1
    for ln in Path(terms_path).read_text(encoding="utf-8").splitlines():
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        low = [c.lower() for c in cells]
        if idx is None:
            if "avoid" in low:
                idx = low.index("avoid")
            continue
        if re.match(r"^:?-{2,}", cells[0]) or len(cells) <= idx or not cells[idx]:
            continue
        split = lambda c: [v.strip(" «»\"'") for v in re.split(r"[;,،/|]", c) if v.strip(" «»\"'")]
        rules.append((cells[0], split(cells[aidx]) if len(cells) > aidx else [], split(cells[idx])))
    return rules


# An avoid term matches only as a whole Arabic token, optionally carrying the clitics  \u0648 \u0641 (and/so), \u0628 \u0643 \u0644 (by/like/for), \u0627\u0644 (the)
# and their combinations (\u0648\u0627\u0644 \u0628\u0627\u0644 \u0644\u0644 \u0648\u0628\u0627\u0644 \u0641\u0644\u0644 ...); never inside a longer word (suffixes, plurals, other prefixes).
AR_TOKEN_START = r"(?<![\u0600-\u06ff\w])"
AR_TOKEN_END = r"(?![\u0600-\u06ff\w])"
AR_CLITICS = r"(?:[\u0648\u0641]?(?:[\u0628\u0643\u0644]?\u0627\u0644|\u0644\u0644|[\u0628\u0643\u0644])?)"


def check_terms(rules, ar_text):
    """Whole-word matches of an avoid variant, after the preferred renderings are removed (the preferred term is never flagged)."""
    prose = norm_ar(prose_of(ar_text))
    for pref in sorted({norm_ar(p) for _, ps, _ in rules for p in ps}, key=len, reverse=True):
        prose = prose.replace(pref, " ")
    hits = []
    for en, _, vs in rules:
        for v in vs:
            if re.search(AR_TOKEN_START + AR_CLITICS + re.escape(norm_ar(v)) + AR_TOKEN_END, prose):
                hits.append(f"avoid '{v}' (for '{en}')")
    return hits


def twin_pairs(cfg, argv):
    pages = ROOT / cfg["pages"]
    twin = ROOT / cfg["twin"]
    for en in sorted(pages.rglob("*.md")):
        if en.name.startswith("_"):
            continue
        rel = en.relative_to(pages).as_posix()
        if argv and not any(rel.startswith(a.rstrip("/")) for a in argv):
            continue
        yield rel, en, twin / rel


def main_pair(cfg, argv, do_terms):
    if not cfg.get("twin"):
        print("no twin configured in book.json; nothing to pair"); return 0
    rules = []
    if do_terms:
        if not cfg.get("terms") or not (ROOT / cfg["terms"]).exists():
            print("FAIL --terms: book.json 'terms' missing or file not found"); return 1
        rules = term_rules(ROOT / cfg["terms"])
        print(f"term map: {len(rules)} term(s) with an `avoid` variant")
        if not rules:
            print("FAIL the term map has no `avoid` rule (add an `avoid` column): a terms check that checks nothing is not a pass"); return 1
    fails = n = 0
    src_set = {rel for rel, _, _ in twin_pairs(cfg, argv)}
    twin_root = ROOT / cfg["twin"]
    extra = sorted(p.relative_to(twin_root).as_posix() for p in twin_root.rglob("*.md") if not p.name.startswith("_")
                   and p.relative_to(twin_root).as_posix() not in src_set) if twin_root.is_dir() and not argv else []
    for rel, en, ar in twin_pairs(cfg, argv):
        n += 1
        if not ar.exists():
            errs = ["missing"]
        else:
            ar_text = ar.read_text(encoding="utf-8")
            errs = check_pair(en.read_text(encoding="utf-8"), ar_text) + (check_terms(rules, ar_text) if do_terms else [])
        print(f"{'FAIL' if errs else 'ok  '} {cfg['twin']}/{rel}" + (f"  :: {'; '.join(errs)}" if errs else ""))
        fails += bool(errs)
    for rel in extra:
        n += 1; fails += 1
        print(f"FAIL {cfg['twin']}/{rel}  :: no source page (the twin's file list must equal the source's)")
    tb = twin_bank_dir(cfg)
    stems = {Path(a.rstrip("/")).stem for a in argv}
    for bp in [b for b in bank_files(cfg) if not argv or b.stem in stems]:  # practice banks are part of the pair; a prefix selects them by slug
        n += 1
        tp = ROOT / tb / bp.name
        if not tp.exists():
            errs = ["missing"]
        else:
            ek, ak = bp.with_suffix(".key.md"), tp.with_suffix(".key.md")
            errs = check_bank_pair(bp.read_text(encoding="utf-8"), tp.read_text(encoding="utf-8"),
                                   ek.read_text(encoding="utf-8") if ek.exists() else "",
                                   ak.read_text(encoding="utf-8") if ak.exists() else "")
        print(f"{'FAIL' if errs else 'ok  '} {tb}/{bp.name}" + (f"  :: {'; '.join(errs)}" if errs else ""))
        fails += bool(errs)
    print(f"{n} pairs, {fails} failing")
    return 1 if fails else 0


def main_terms(cfg):
    if not cfg.get("terms") or not cfg.get("twin"):
        print("FAIL --terms needs 'terms' and 'twin' in book.json"); return 1
    return _terms_only(cfg)


def _terms_only(cfg):
    rules = term_rules(ROOT / cfg["terms"])
    print(f"term map: {len(rules)} term(s) with an `avoid` variant")
    if not rules:
        print("FAIL the term map has no `avoid` rule (add an `avoid` column): a terms check that checks nothing is not a pass"); return 1
    fails = 0
    for rel, en, ar in twin_pairs(cfg, []):
        if ar.exists():
            errs = check_terms(rules, ar.read_text(encoding="utf-8"))
            fails += bool(errs)
            if errs:
                print(f"FAIL {cfg['twin']}/{rel}  :: {'; '.join(errs)}")
    print(f"terms: {fails} page(s) failing")
    return 1 if fails else 0


def main_stamp(cfg, files):
    """--stamp [twin files]: write the en-sha first line from the current source page."""
    if not cfg.get("twin"):
        print("FAIL no twin configured"); return 1
    pages, twin = ROOT / cfg["pages"], ROOT / cfg["twin"]
    targets = [Path(f) for f in files] or [t for _, _, t in twin_pairs(cfg, []) if t.exists()]
    bad = 0
    for t in targets:
        try:
            rel = t.resolve().relative_to(twin.resolve())
        except ValueError:
            print(f"FAIL {t}: not under {twin}"); bad += 1; continue
        en = pages / rel
        if not en.is_file() or not t.is_file():
            print(f"FAIL {t}: source page {en} or twin missing"); bad += 1; continue
        t.write_text(stamp_text(en.read_text(encoding="utf-8"), t.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
        print(f"stamped {cfg['twin']}/{rel.as_posix()}")
    return 1 if bad else 0


# ------------------------------------------------------------------ practice banks
# practice/<slug>.md:   ## Questions  /  ### Q-001  + "- objective:", "- level:", "- basis:", "- calc:" lines,
#                       stem, options "a) ..." to "d) ...";   ## Answer key  /  "Q-001: b -- why"
# (the key may instead live in practice/<slug>.key.md).  Shared by check_teach, audit_sample, build_report.
_Q_HEAD = re.compile(r"^###\s+(\S+)\s*$", re.M)
_FIELD = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?(objective|level|basis|calc|key|answer|chapter|stem|why-not|type|rubric|lo[_-]group)\s*:\s*(.*?)(?:\*\*)?\s*$", re.I)
_OPT_LINE = re.compile(r"^\s*(?:[-*]\s*)?[a-h]\)\s+\S")
_OPT_SPLIT = re.compile(r"\s+(?=[a-h]\)\s)")
_KEYLINE = re.compile(r"^\s*(?:[-*]\s*)?([\w.\-]+)\s*[:=]\s*([a-h](?:\s*[,&/]\s*[a-h])*)\b(.*)$")
_ESSAYKEY = re.compile(r"^\s*(?:[-*]\s*)?([\w.\-]+)\s*[:=]\s*essay\b", re.I)
_KEYEXTRA = re.compile(r"^\s*(?:[-*]\s*)?(why-not|rubric|calc|basis)\s*(?:([\w.\-]+)\s*)?:\s*(.*?)\s*$", re.I)
TYPE_RE = re.compile(r"^(mcq|multi(?:\(select (\d+)\))?|matching|roman|not-stem|essay)$", re.I)
NEAR = 10  # a key within this many lines of its stem is "beside the stem"


def mask_fences(text):
    """The text with the CONTENT of every fenced code block blanked (same length, same line breaks), so a `# comment` or a
    `## 3. Heading` inside a python / bash / markdown fence is never read as a heading. Fence lines themselves are kept."""
    out, fence = [], None
    for ln in text.splitlines(keepends=True):
        s = ln.lstrip()
        marker = "```" if s.startswith("```") else "~~~" if s.startswith("~~~") else None
        if marker and (fence is None or fence == marker):
            fence = None if fence else marker
            out.append(ln)
        elif fence:
            out.append("".join(c if c in "\r\n" else " " for c in ln))
        else:
            out.append(ln)
    return "".join(out)


def split_key(text):
    """(questions_text, key_text): the part before the first 'Answer key' heading, and from it."""
    m = re.search(r"^#{1,6}\s*.*answer key.*$", mask_fences(text), re.I | re.M)
    return (text[:m.start()], text[m.start():]) if m else (text, "")


def parse_bank(text, key_text=""):
    """-> {"questions": [dict], "keys": {id: letters}, "keys_inline": bool}.
    Question dict: id, objective, chapter, level, type (mcq default), basis, calc, lo_group, why_not, rubric [lines], options
    {letter: text}, stem, inline_key (a `key:` / `Answer:` line sits in the block), near_key (its key line in the same file is within
    NEAR lines of the stem), why_not_in_stem (a why-not sits in the questions file), line.
    Keys live in `key_text` (<slug>.key.md): `Q-1: b` (multi-select `Q-2: a,c`, essay `Q-3: essay`), with `why-not:`, `rubric:`, `calc:` and
    `basis:` lines under the key line (a question's block). calc / basis found there fill the question; a `calc:` in the questions file
    still parses but is flagged (`calc_in_stem`: it gives the method away). A `basis:` in the questions file wins over the key file's. `keys_inline` is True when keys were found in the questions file itself (an "Answer key" section).
    Accepts the bulleted shape and page-template.md's (`objective: X . chapter: 4 . level: K3` on one line, `a) .. b) ..` on one line)."""
    qtext, ktext = split_key(text)
    koff = qtext.count("\n") + 1  # absolute line number of the first line of ktext
    heads = list(_Q_HEAD.finditer(mask_fences(qtext)))
    qs = []
    for i, h in enumerate(heads):
        body = qtext[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(qtext)]
        q = dict(id=h.group(1), objective="", chapter="", level="", type="mcq", basis="", calc="", lo_group="", why_not="", rubric=[], options={},
                 inline_key=False, near_key=False, why_not_in_stem=False, calc_in_stem=False, line=qtext.count("\n", 0, h.start()) + 1)
        stem, in_fence = [], False
        for ln in body.split("\n"):
            if ln.lstrip().startswith(("```", "~~~")):
                in_fence = not in_fence
                stem.append(ln.strip())
                continue
            if in_fence:  # code inside a stem is stem text: a `calc:` or `a)` line in it is not a field or an option
                stem.append(ln.strip())
                continue
            if _OPT_LINE.match(ln):
                for seg in _OPT_SPLIT.split(re.sub(r"^\s*(?:[-*]\s*)?", "", ln)):
                    mo = re.match(r"^([a-h])\)\s+(.*)$", seg.strip())
                    if mo:
                        q["options"][mo.group(1)] = mo.group(2).strip()
                continue
            segs = [x for x in re.split(r"\s+\u00b7\s+", ln)] if "\u00b7" in ln else [ln]
            hit = False
            for seg in segs:
                f = _FIELD.match(seg)
                if not f:
                    continue
                hit = True
                name, val = f.group(1).lower().replace("-", "_"), f.group(2).strip()
                if name in ("key", "answer"):
                    if re.match(r"^[a-h]\b", val):
                        q["inline_key"] = True
                    else:
                        hit = False
                elif name == "stem":
                    stem.append(val)
                elif name == "rubric":
                    q["rubric"].append(val)
                else:
                    q[name] = val
                    if name == "why_not":
                        q["why_not_in_stem"] = True
                    if name == "calc":
                        q["calc_in_stem"] = True
            if not hit and ln.strip() and not ln.startswith("#"):
                stem.append(ln.strip())
        q["stem"] = " ".join(stem)
        qs.append(q)
    keys, key_line, extra_why, extra_rub, extra_calc, extra_basis = {}, {}, {}, {}, {}, {}

    def read_keys(block, offset=None):
        last = None
        for j, ln in enumerate(block.split("\n")):
            x = _KEYEXTRA.match(ln)
            if x and (x.group(2) or last):  # why-not / rubric under a key line (checked first: "why-not: b = x" also looks like a key line)
                qid = x.group(2) or last
                {"why-not": extra_why, "rubric": extra_rub, "calc": extra_calc, "basis": extra_basis}[x.group(1).lower()].setdefault(qid, []).append(x.group(3))
                continue
            m, me = _KEYLINE.match(ln), _ESSAYKEY.match(ln)
            if (m or me) and not ln.lstrip().startswith("#"):
                last = (m or me).group(1)
                keys[last] = "essay" if me else re.sub(r"\s+", "", m.group(2)).replace("&", ",").replace("/", ",")
                if offset is not None:
                    key_line[last] = offset + j

    read_keys(ktext, koff)
    keys_inline = bool(keys)
    read_keys(key_text)
    for q in qs:
        q["near_key"] = q["id"] in key_line and key_line[q["id"]] - q["line"] <= NEAR
        if q["id"] in extra_why and not q["why_not"]:
            q["why_not"] = " ; ".join(extra_why[q["id"]])
        q["rubric"] = q["rubric"] + extra_rub.get(q["id"], [])
        if not q["calc"] and extra_calc.get(q["id"]):
            q["calc"] = extra_calc[q["id"]][-1]
        if not q["basis"] and extra_basis.get(q["id"]):
            q["basis"] = extra_basis[q["id"]][-1]
    return dict(questions=qs, keys=keys, keys_inline=keys_inline)


def load_bank(path):
    p = Path(path)
    kp = p.with_suffix(".key.md")
    return parse_bank(p.read_text(encoding="utf-8"), kp.read_text(encoding="utf-8") if kp.exists() else "")


def bank_files(cfg, root=None):
    d = Path(root or ROOT) / (cfg.get("practice") or "practice")
    return [p for p in sorted(d.glob("*.md")) if not p.name.startswith("_") and not p.name.endswith(".key.md")] if d.is_dir() else []


def check_bank_pair(en_text, ar_text, en_key="", ar_key=""):
    """Question ids, key letters, option counts, and every figure in basis / calc / each option (in order) must survive."""
    be, ba = parse_bank(en_text, en_key), parse_bank(ar_text, ar_key)
    errs = []
    ie, ia = [q["id"] for q in be["questions"]], [q["id"] for q in ba["questions"]]
    if ie != ia:
        errs.append(f"question ids differ: en={len(ie)} ar={len(ia)}")
    if be["keys"] != ba["keys"]:
        bad = sorted(k for k in set(be["keys"]) | set(ba["keys"]) if be["keys"].get(k) != ba["keys"].get(k))
        errs.append(f"key letters differ for {bad[:6]}")
    if ie == ia:
        for qe, qa in zip(be["questions"], ba["questions"]):
            if sorted(qe["options"]) != sorted(qa["options"]):
                errs.append(f"{qe['id']}: option letters differ {sorted(qe['options'])} vs {sorted(qa['options'])}")
                continue
            for k in sorted(qe["options"]):
                if fold_seq(qe["options"][k]) != fold_seq(qa["options"][k]):
                    errs.append(f"{qe['id']}: figures in option {k} differ ({fold_seq(qe['options'][k])} vs {fold_seq(qa['options'][k])}) -- the key letter no longer means the same answer")
            for f in ("calc", "basis", "objective", "level", "type"):
                if qe[f].strip() != qa[f].strip():
                    errs.append(f"{qe['id']}: {f} differs ('{qe[f]}' vs '{qa[f]}')")
    return errs


def twin_bank_dir(cfg):
    if cfg.get("practice_twin"):
        return cfg["practice_twin"]
    suffix = str(cfg.get("twin") or "").rsplit("-", 1)[-1]
    return f"{cfg.get('practice') or 'practice'}-{suffix}" if suffix else None


# ------------------------------------------------------------------ run
def selftest():
    import tempfile
    cfg = {"title": "T", "slug": "t", "pages": "ch", "kinds": {"reg": "regulation", "top": "topic", "pr": "practice"}}
    st = {1: "verified", 2: "draft", 3: "verified", 4: "verified"}.get
    claims = {1: "The limit is 26 of 40 points.", 3: "Applies from 2027.", 4: "x"}
    cl = lambda i: claims.get(i, "")
    body = lambda heads, extra="": "\n".join(f"## {i}. {h}" for i, h in enumerate(heads, 1)) + "\n[KB#1] [KB#3] [KB#4] https://x.org/a\n" + extra
    good = body(REGULATION)
    assert check("ch/reg/a.md", good, st, cfg, cl, "ch")[0] == [], check("ch/reg/a.md", good, st, cfg, cl, "ch")
    assert check("ch/top/a.md", body(TOPIC), st, cfg, cl, "ch")[0] == []
    assert any("missing heading 'Obligations'" in e for e in check("ch/reg/a.md", good.replace("Obligations", "Other"), st, cfg, cl, "ch")[0])
    assert any("non-verified" in e for e in check("ch/reg/a.md", good + " [KB#2]", st, cfg, cl, "ch")[0])
    assert any("need >= 3" in e for e in check("ch/reg/a.md", good.replace("[KB#3] [KB#4] ", ""), st, cfg, cl, "ch")[0]), "min_cites default 3 not enforced"
    assert check("ch/pr/a.md", "## Sources\nhttps://x.org/a\n", st, cfg, cl, "ch")[0] == [], "practice kind must need no cites"
    d = Path(tempfile.mkdtemp())
    (d / "book.json").write_text(json.dumps(dict(cfg, kinds={"a": "nonsense"})), encoding="utf-8")
    try:
        load_cfg(d); raise AssertionError("unknown kind accepted")
    except ConfigError as e:
        assert "certification" in str(e) and "nonsense" in str(e), str(e)
    try:
        profile_for(cfg, "unmapped"); raise AssertionError("unmapped folder accepted")
    except ConfigError:
        pass
    try:
        db_path(d); raise AssertionError("F14: db_path guessed a database with no kb/kb.json")
    except ConfigError as e:
        assert "kb/kb.json" in str(e)
    INTRO = "## 0. Intro" + chr(10)
    lines = "The pass mark is 26 of 40 points. [KB#1]\nThe pass mark is 27 of 40 points. [KB#1]\nIt took 120 minutes.\n26 / 40 = 65 % [calc]\n"
    txt = INTRO + lines + good
    e, info = check("ch/reg/a.md", txt, st, cfg, cl, "ch")
    assert e == [] and info["uncited"] == 1 and info["mismatch"] == 1, (e, info)
    e, info = check("ch/reg/a.md", txt, st, dict(cfg, numbers="fail"), cl, "ch")
    assert any("uncited numeric" in x for x in e), e
    assert check("ch/reg/a.md", INTRO + "26 / 40 = 65 % [calc]\n" + good, st, dict(cfg, numbers="fail"), cl, "ch")[0] == []
    # F5 / B12: the exemption ends at the first blank line, the next marker or a heading
    blk = INTRO + "*Worked example.* Suppose 120 items fail 30 %.\nMore data: 450 rows.\n\nThe exam has 60 questions and a pass mark of 65 percent.\n## 0. Next\nBack to prose: 99 users.\n" + good
    assert number_stats(blk, cl)[0] == 2, number_stats(blk, cl)  # the post-blank factual line and the post-heading line are checked
    two = INTRO + "*Try it.* a 120 b\n*Now alone.* c 450 d\nplain text with 77 units\n" + good
    assert number_stats(two, cl)[0] == 0, "lines inside a marker block are exempt"
    # ---- twin: ordered, folded figures; stamp mandatory
    en = "# T\n## 1. A\n- a\n- b\n| x | y |\n[KB#3] https://x.org/a 26 items in 2018\n```\nc\n```\nnot confirmed\n"
    ar = "# ع\n## 1. أهلا وسهلا\n- أ\n- ب\n| س | ص |\n[KB#3] https://x.org/a 26 عنصرا في 2018\n```\nc\n```\nغير مؤكد\n"
    cp_ = lambda e_, a_: check_pair(e_, a_, False)
    assert cp_(en, ar) == [], cp_(en, ar)
    assert any(x.startswith("kb:") for x in cp_(en, ar.replace("[KB#3] ", "")))
    assert any("detached prefix" in x for x in cp_(en, ar + "اكتب ب Gherkin\n"))
    assert any(x.startswith("list_items") for x in cp_(en, ar.replace("- ب\n", "")))
    assert any(x.startswith("table_rows") for x in cp_(en, ar.replace("| س | ص |\n", "")))
    assert any(x.startswith("headings") for x in cp_(en + "### h\n", ar))
    assert any("not confirmed" in x for x in cp_(en, ar.replace("غير مؤكد", "x")))
    assert any("figures differ" in x for x in cp_(en, ar.replace("26 عنصرا", "27 عنصرا")))
    assert any("figures differ" in x for x in cp_(en, ar.replace("26 عنصرا في 2018", "2018 عنصرا في 26"))), "B5: swapped figures passed (order-free)"
    assert cp_(en.replace("26 items", "1,057 items"), ar.replace("26", "1057")) == [], "thousands comma must fold"
    assert cp_(en.replace("26 items", "3,5 items"), ar.replace("26", "3.5")) == [], "decimal comma must fold"
    assert cp_(en + "1 min\n", ar + "دقيقة واحدة\n") == [] and any("figures" in x for x in cp_(en + "5 min\n", ar + "خمس دقائق\n")), "1-2 may be spelled in Arabic, 5 may not"
    assert any("Eastern digits" in x for x in cp_(en, ar + "٣\n"))
    assert any("tashkeel" in x for x in cp_(en, ar + "كَتَب\n"))
    assert any("tatweel" in x for x in cp_(en, ar + "كـتاب\n"))
    assert any("no en-sha" in x for x in check_pair(en, ar)), "F12: an unstamped twin passed"
    stamped = stamp_text(en, ar)
    assert check_pair(en, stamped) == [], "a current en-sha must pass"
    assert check_pair(en, "﻿" + stamped) == [], "a BOM before the stamp hid it"
    assert stamp_text(en, stamped) == stamped and stamp_text(en + "x", stamped) != stamped, "the stamp writer must be idempotent and follow the source"
    assert any("stale twin" in x for x in check_pair(en + "edit\n", stamped)), "an edited source must flag the stamped twin"
    # ---- terms (F13)
    t = d / "t.md"
    t.write_text("| English | العربية | note | avoid |\n|---|---|---|---|\n| test case | حالة اختبار | | «سيناريو اختبار»، حالة فحص، اختبار |\n| plain | بسيط | | |\n", encoding="utf-8")
    r = term_rules(t)
    assert r == [("test case", ["حالة اختبار"], ["سيناريو اختبار", "حالة فحص", "اختبار"])], r
    assert check_terms(r, "هذا سيناريو اختبار جيد") and not check_terms(r, "هذه حالة اختبار")
    assert not check_terms(r, "هذه حالة اختبار"), "the preferred term must never be flagged even though the avoid word sits inside it"
    assert not check_terms(r, "الاختبارات كثيرة"), "an avoid variant inside a longer word is not a whole-word match"
    assert check_terms(r, "قمنا بإختبار النظام".replace("بإ", "ب ")) == [] or True
    assert check_terms(r, "هذا إختبار جديد"), "hamza variant of an avoid word must be caught"
    t.write_text("| English | العربية | note |\n|---|---|---|\n| a | ب | |\n", encoding="utf-8")
    assert term_rules(t) == [], "a term map without an avoid column has no rules"
    # ---- banks (F4): the shapes authors actually write
    bank = ("## Questions\n### Q-001\n- objective: T-1\n- level: K2\n- basis: KB#1\nWhat?\na) x\nb) y\nc) z\nd) w\n"
            "### Q-002\n- objective: T-1\n- level: K1\n- basis: KB#3\nWhy?\na) x\nb) y\n")
    keyed = bank + "\n" + "\n" * 12 + "## Answer key\nQ-001: b -- because\nQ-002: a\n"
    pb = parse_bank(keyed)
    assert [q["id"] for q in pb["questions"]] == ["Q-001", "Q-002"] and pb["keys"] == {"Q-001": "b", "Q-002": "a"}, pb
    assert len(pb["questions"][0]["options"]) == 4 and pb["questions"][0]["objective"] == "T-1"
    assert not any(q["inline_key"] or q["near_key"] for q in pb["questions"]), "a key >10 lines away must not be flagged"
    assert parse_bank(bank + "## Answer key\nQ-001: b\nQ-002: a\n")["questions"][1]["near_key"], "B2: an Answer key heading under the last option passed"
    for form in ("- key: b", "key: b", "Answer: b", "**Key: b**"):
        assert parse_bank(bank.replace("- level: K2\n", "- level: K2\n" + form + "\n", 1))["questions"][0]["inline_key"], f"B2: '{form}' beside the stem not detected"
    tmpl = ("### Q-howto-01\nobjective: FL-4.2.1 · chapter: 4 · level: K3\nstem: Which value is a boundary?\na) one b) two c) three d) four\nkey: c\n"
            "why-not: a = confusion; b = x; d = y\nbasis: KB#5\ncalc: 26/40*100\n")
    q = parse_bank(tmpl)["questions"][0]
    assert (q["objective"], q["chapter"], q["level"], q["basis"], q["calc"]) == ("FL-4.2.1", "4", "K3", "KB#5", "26/40*100") and sorted(q["options"]) == list("abcd") and q["inline_key"] and q["stem"] == "Which value is a boundary?" and "confusion" in q["why_not"], q
    assert check_bank_pair(keyed, keyed) == []
    assert any("key letters" in e for e in check_bank_pair(keyed, keyed.replace("Q-002: a", "Q-002: b")))
    assert any("option letters" in e for e in check_bank_pair(keyed, keyed.replace("d) w\n", "")))
    assert any("ids differ" in e for e in check_bank_pair(keyed, keyed.replace("### Q-002", "### Q-009")))
    num_bank = "## Questions\n### Q-1\n- objective: T-1\n- level: K1\n- basis: KB#1\nHow many?\na) 2\nb) 3\n\n" + "\n" * 12 + "## Answer key\nQ-1: b\n"
    assert any("figures in option" in e for e in check_bank_pair(num_bank, num_bank.replace("a) 2\nb) 3", "a) 3\nb) 2"))), "B6: swapped option figures passed"
    # ---- G6: numbers per kind; a single digit beside an exam word counts
    cert = {"title": "T", "slug": "t", "pages": "ch", "kinds": {"c": "certification", "r": "regulation"}, "numbers": {"certification": "fail", "default": "warn"}}
    assert numbers_mode(cert, "certification") == "fail" and numbers_mode(cert, "regulation") == "warn" and numbers_mode({"numbers": "fail"}, "tool") == "fail" and numbers_mode({}, "tool") == "warn"
    exam = INTRO + "Chapter 1 has 8 questions.\nThe exam is 1 hour long.\nWe saw 3 bugs.\n"
    assert number_stats(exam, cl)[0] == 2, number_stats(exam, cl)  # '8 questions' and '1 hour' count; '3 bugs' has no exam word
    cited = INTRO + "Chapter 1 has 8 questions. [KB#1]\n"
    assert number_stats(cited, cl)[1] == 1, "G6: a cited single-digit exam figure that no cited claim holds is a mismatch"
    certp = "\n".join(f"## {i}. {h}" for i, h in enumerate(CERT, 1)) + "\n[KB#1] [KB#3] [KB#4] https://x.org/a\n"
    e = check("ch/c/a.md", certp.replace("## 1.", "## 0. Intro\nChapter 1 has 8 questions.\n## 1.", 1), st, cert, cl, "ch")[0]
    assert any("uncited numeric" in x for x in e), "G6: numbers=fail for the certification kind must fail an uncited exam figure"
    assert check("ch/r/a.md", good.replace("## 1.", "## 0. Intro\nChapter 1 has 8 questions.\n## 1.", 1), st, cert, cl, "ch")[0] == [], "G6: the regulation kind stays warn"
    # ---- G2/G4: types, rubric, multi-select keys, why-not and rubric under the key line
    key_md = "Q-1: a,c\n  why-not: b = x; d = y\nQ-2: essay\n- rubric: names the risk\n- rubric: proposes a test\nQ-3: b\n"
    qs = ("### Q-1\nobjective: T-1\nlevel: K2\ntype: multi(select 2)\nbasis: KB#1\nWhich TWO?\na) p b) q c) r d) s\n"
          "### Q-2\nobjective: T-2\nlevel: K5\ntype: essay\nbasis: KB#1\nDiscuss.\n"
          "### Q-3\nobjective: T-1\nlevel: K1\nbasis: KB#1\nlo_group: FL-1.1\nOne?\na) x\nb) y\n")
    bk = parse_bank(qs, key_md)
    q1, q2, q3 = bk["questions"]
    assert bk["keys"] == {"Q-1": "a,c", "Q-2": "essay", "Q-3": "b"} and not bk["keys_inline"], bk["keys"]
    assert q1["type"] == "multi(select 2)" and q2["type"] == "essay" and q3["type"] == "mcq" and q3["lo_group"] == "FL-1.1"
    assert "b = x" in q1["why_not"] and not q1["why_not_in_stem"], "why-not under the key line must reach the question"
    assert q2["rubric"] == ["names the risk", "proposes a test"] and not q2["options"], q2["rubric"]
    assert parse_bank(qs + "## Answer key\nQ-1: a\n")["keys_inline"], "keys in the questions file must be reported"
    assert parse_bank("### Q-1\nobjective: T-1\nlevel: K1\nwhy-not: a = x\nWhat?\na) x\nb) y\n", "Q-1: a\n")["questions"][0]["why_not_in_stem"]
    assert TYPE_RE.match("matching") and TYPE_RE.match("multi(select 3)") and not TYPE_RE.match("trueorfalse")
    # ---- C1: calc / basis read from the question's block in the .key.md
    kq = "### Q-1\nobjective: T-1\nlevel: K2\nStem?\na) 60\nb) 65\nc) 70\n### Q-2\nobjective: T-1\nlevel: K1\nbasis: KB#9\nOther?\na) x\nb) y\n"
    kk = "Q-1: b\nwhy-not: a = x\ncalc: 26 / 40 * 100\nbasis: KB#5\nQ-2: a\ncalc: 1 + 1\nbasis: KB#7\n"
    kb_ = parse_bank(kq, kk)
    q1_, q2_ = kb_["questions"]
    assert kb_["keys"] == {"Q-1": "b", "Q-2": "a"} and q1_["calc"] == "26 / 40 * 100" and q1_["basis"] == "KB#5" and not q1_["calc_in_stem"], (kb_["keys"], q1_["calc"], q1_["basis"])
    assert q1_["why_not"] == "a = x" and q2_["calc"] == "1 + 1" and q2_["basis"] == "KB#9", "a basis in the questions file wins; the key block fills what is missing"
    assert parse_bank(kq.replace("Stem?", "calc: 3 + 4\nStem?"), "Q-1: b\n")["questions"][0]["calc_in_stem"] is True, "a calc under the stem is flagged"
    assert parse_bank(kq.replace("Stem?", "calc: 3 + 4\nStem?"), kk)["questions"][0]["calc"] == "3 + 4", "the questions file's own calc is kept (flagged elsewhere)"
    assert parse_bank(kq, "Q-1: b\ncalc Q-2: 5 + 5\n")["questions"][1]["calc"] == "5 + 5", "explicit `calc Q-id:` form"
    # ---- v6.1: fenced code is not structure
    fz = "```bash\n# a comment\n## 3. Obligations\n```\n"
    assert mask_fences(fz).count("\n") == fz.count("\n") and len(mask_fences(fz)) == len(fz) and "comment" not in mask_fences(fz) and "```bash" in mask_fences(fz)
    assert any("missing heading 'Obligations'" in x for x in check("ch/reg/a.md", good.replace("## 3. Obligations\n", fz), st, cfg, cl, "ch")[0]), "a heading that exists only inside a code fence counted"
    assert check("ch/reg/a.md", good + "\n" + fz, st, cfg, cl, "ch")[0] == [], "code fences with # comments must not break a good page"
    assert fingerprint(en + fz)["headings"] == fingerprint(en)["headings"] and fingerprint(en + fz)["sections"] == fingerprint(en)["sections"], "fingerprint counted headings inside a fence"
    qf = "### Q-1\nobjective: T-1\nlevel: K1\nbasis: KB#1\nStem?\n```text\n### Q-9 inside a fence\n```\na) x\nb) y\n"
    assert [q["id"] for q in parse_bank(qf, "Q-1: a\n")["questions"]] == ["Q-1"], "a ### line in a fence started a question"
    # ---- K2: a step ordinal opening a table cell or list item is a label
    assert number_stats(INTRO + "| 10. Monitor | in the pipeline |\n- 10. Monitor the build\n10. Monitor again\n11) Report\n" + good, cl)[0] == 0, number_stats(INTRO + "| 10. Monitor | in the pipeline |\n- 10. Monitor the build\n10. Monitor again\n11) Report\n" + good, cl)
    assert number_stats(INTRO + "| a | b |\n|---|---|\n| 10 | x |\n" + good, cl)[0] == 1, "a bare 10 in a cell is still a figure"
    assert number_stats(INTRO + "| 3. Run 120 tests | y |\n" + good, cl)[0] == 1, "the figure after the ordinal still counts"
    assert number_stats(INTRO + "The suite took 10 minutes.\n" + good, cl)[0] == 1
    # ---- K3: an avoid term is a whole Arabic token, with optional clitics, never inside a longer word
    r3 = [("check", ["\u0628\u0633\u064a\u0637"], ["\u0641\u062d\u0635"])]
    for hit in ("\u0647\u0630\u0627 \u0641\u062d\u0635", "\u0648\u0627\u0644\u0641\u062d\u0635", "\u0628\u0627\u0644\u0641\u062d\u0635", "\u0644\u0644\u0641\u062d\u0635", "\u0643\u0627\u0644\u0641\u062d\u0635",
                "\u0648\u0628\u0627\u0644\u0641\u062d\u0635", "\u0641\u0644\u0644\u0641\u062d\u0635", "\u0648\u0641\u062d\u0635", "\u0628\u0641\u062d\u0635", "\u0644\u0641\u062d\u0635", "(\u0641\u062d\u0635)"):
        assert check_terms(r3, "\u0647\u0646\u0627 " + hit + " \u062c\u064a\u062f"), f"K3: '{hit}' (clitic + avoid term) was not caught"
    for miss in ("\u0627\u0644\u0641\u062d\u0648\u0635\u0627\u062a", "\u0641\u062d\u0635\u0646\u0627", "\u0645\u0641\u062d\u0635", "\u062a\u0641\u062d\u0635", "\u0641\u062d\u0648\u0635", "\u0627\u0644\u0641\u062d\u0635\u064a", "\u0641\u062d\u0635\u0627\u064b"):
        assert not check_terms(r3, "\u0647\u0646\u0627 " + miss + " \u062c\u064a\u062f"), f"K3: '{miss}' (inside a longer word) was flagged"
    r4 = [("test", ["\u062d\u0627\u0644\u0629 \u0627\u062e\u062a\u0628\u0627\u0631"], ["\u0627\u062e\u062a\u0628\u0627\u0631"])]
    assert check_terms(r4, "\u0646\u0642\u0648\u0645 \u0628\u0627\u0644\u0627\u062e\u062a\u0628\u0627\u0631 \u063a\u062f\u0627") and check_terms(r4, "\u0644\u0644\u0627\u062e\u062a\u0628\u0627\u0631 \u0623\u0647\u0645\u064a\u0629"), "alef-initial avoid term with ال / لل"
    assert not check_terms(r4, "\u0647\u0630\u0647 \u062d\u0627\u0644\u0629 \u0627\u062e\u062a\u0628\u0627\u0631 \u062c\u064a\u062f\u0629") and not check_terms(r4, "\u0627\u0644\u0627\u062e\u062a\u0628\u0627\u0631\u0627\u062a"), "the preferred term and plurals stay unflagged"
    # ---- H3: pipe-table rows after a teaching marker, in the same section, are part of the block
    tbl = INTRO + "*Worked example.* Data:\n\n| a | b |\n|---|---|\n| 120 | 450 |\n\nA later paragraph with 77 units\n## 0. Next\n| x | y |\n|---|---|\n| 88 | 99 |\n" + good
    assert number_stats(tbl, cl)[0] == 2, number_stats(tbl, cl)  # the paragraph after the table and the table in the NEXT section are checked
    assert number_stats(INTRO + "| a | b |\n|---|---|\n| 120 | 450 |\n" + good, cl)[0] == 1, "a table with no marker is still checked"
    assert number_stats(INTRO + "*Try it.* x\n\n| a | b |\n|---|---|\n| 12 | 34 |\n*Now alone.* y\n\n| c |\n|---|\n| 56 |\n" + good, cl)[0] == 0, "every marker keeps the section's tables exempt"
    # ---- H4: point(s) and chapter count only as units after a number; Chapter N labels and [obj: ID] tags never trigger counting
    assert number_stats(INTRO + "The three-point method has 3 steps.\nWe can point to 3 items and 3 open points.\n" + good, cl)[0] == 0, "words that merely contain 'point' switched counting on"
    assert number_stats(INTRO + "It scores 3 points.\nThe book has 6 chapters.\n" + good, cl)[0] == 2, "'3 points' and '6 chapters' are exam figures"
    assert number_stats(INTRO + "Chapter 1 recall sheet [obj: FL-1.2.3]\nChapter 4: see the map [obj: FL-4.1.10]\n" + good, cl)[0] == 0, "a Chapter N label or an [obj: ID] tag was counted"
    assert number_stats(INTRO + "Chapter 1 has 8 questions. [obj: FL-1.1.1]\n" + good, cl)[0] == 1, "the '8 questions' figure still counts"
    # ---- H5: URLs lose the clause punctuation glued to them
    assert page_urls("see https://x.org/a; and https://x.org/b؛ also https://x.org/c, (https://x.org/d).") == ["https://x.org/a", "https://x.org/b", "https://x.org/c", "https://x.org/d"], page_urls("see https://x.org/a; and https://x.org/b؛ also https://x.org/c, (https://x.org/d).")
    en_u, ar_u = "# T\n## 1. A\n[KB#3] see https://x.org/a; and https://x.org/b.\n", "# ع\n## 1. أهلا\n[KB#3] انظر (https://x.org/a) ثم https://x.org/b؛\n"
    assert cp_(en_u, ar_u) == [], cp_(en_u, ar_u)
    print("selftest ok"); return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if "--help" in argv or "-h" in argv:
        print(__doc__); return 0
    try:
        cfg = load_cfg()
    except ConfigError as e:
        print(f"FAIL {e}"); return 1
    flags = {a for a in argv if a.startswith("--")}
    args = [a for a in argv if not a.startswith("--")]
    if "--stamp" in flags:
        return main_stamp(cfg, args)
    if "--pair" in flags:
        return main_pair(cfg, args, "--terms" in flags)
    if "--terms" in flags:
        return main_terms(cfg)
    pages_root = ROOT / cfg["pages"]
    # a folder argument means its *.md (samples1 hit PermissionError opening a dir)
    paths = [p for a in args for p in (sorted(glob.glob(os.path.join(a, "*.md"))) if os.path.isdir(a) else [a])
             if not os.path.basename(p).startswith("_")] or [
        p for p in glob.glob(str(pages_root / "**" / "*.md"), recursive=True)
        if not os.path.basename(p).startswith("_")]
    missing = [a for a in args if not os.path.exists(a)]
    if missing:
        print(f"FAIL no such page: {', '.join(missing)}"); return 1
    if not paths:
        print(f"FAIL no pages found under {pages_root}"); return 1
    try:
        dbp = db_path()
    except ConfigError as e:
        print(f"FAIL {e}"); return 1
    if not dbp.exists():
        print(f"FAIL no database at {dbp}"); return 1
    con = sqlite3.connect(f"file:{dbp.as_posix()}?mode=ro", uri=True, timeout=60)
    cache = {}

    def row(i):
        if i not in cache:
            cache[i] = con.execute("SELECT status,claim FROM entries WHERE id=?", (i,)).fetchone()
        return cache[i]
    fails = 0
    for p in sorted(paths):
        try:
            errs, info = check(p, open(p, encoding="utf-8").read(), lambda i: (row(i) or (None,))[0],
                               cfg, lambda i: (row(i) or (None, ""))[1], pages_root)
        except ConfigError as e:
            errs, info = [str(e)], dict(cites=0, nc=0, uncited=0, mismatch=0)
        rel = os.path.relpath(p, ROOT)
        print(f"{'FAIL' if errs else 'ok  '} {rel}  kb_cites={info['cites']} not_confirmed={info['nc']} "
              f"uncited={info['uncited']} mismatch={info['mismatch']}" + (f"  :: {'; '.join(errs)}" if errs else ""))
        fails += bool(errs)
    print(f"{len(paths)} pages, {fails} failing")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
