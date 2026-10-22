#!/usr/bin/env python3
"""audit_sample.py -- blind audits of the verified facts and the practice-bank questions (stdlib). PYTHONUTF8=1 assumed.

    audit_sample.py draw --by <auditor> [--entries | --banks] [--topic T[,T]] [--n auto|N] [--seed S]
    audit_sample.py check [--entries | --banks] [--topic T[,T]]        exit 1 unless every sampled row is `held`
    audit_sample.py --selftest

TWO audits, two files: `draw --entries` (stage 2b, before authoring) writes audit/entries.md; `draw --banks` (stage 3c, after the
banks exist) writes audit/banks.md. A plain `draw` does both (banks skipped while there are none); a plain `check` needs both
(the banks one only when banks with questions are in scope). build_report.py refuses unless both pass for the topics it builds.
--topic restricts the sample AND every later recount to those topics (a rehearsal of one item needs no database clone); the
topics are stored in the sample header, and a report building a topic the sample does not cover is refused.

Project = BOOK_ROOT env or cwd. The auditor is a run that wrote nothing to the book: `draw --entries` REFUSES if the auditor's
agent prefix (the part of the name before its first hyphen, leading role words dropped) equals the author or verifier
prefix of any sampled entry. Entries sample = max(30, 5 %) of the verified entries (--n N overrides); banks sample = max(10, 10 %)
of the bank questions in <practice>/*.md with their basis; drawn with a seed (default derived from the population: a re-draw is identical).
The auditor opens each row's raw locator, reads the quote in place, and writes exactly `held` or `missed: why` in the last column.
`check` recomputes everything from the DB (rows must equal the drawn ids, nothing sampled changed, the in-scope population within
10 % of the draw, floors met), prints n, misses, blanks and the 95 % upper bound on the miss rate (rule of three, 3/n, when misses = 0;
Wilson otherwise) -- the numbers the report's Method page prints. What it proves: a sampled fact's quote is real and supports the
claim. What it does not: the source is right.
"""
import hashlib, json, math, os, random, re, sqlite3, sys
from datetime import date, datetime
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_pages as cp
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = cp.ROOT
ROLES = {"author", "authors", "authored", "writer", "drafts", "draft", "verify", "verifier", "verification",
         "verified", "check", "checker", "review", "reviewer", "second", "audit", "auditor"}


def agent_id(name):
    """Same rule as kb.py (copied: kb.py lives in another skill). ponytail: self-asserted names only."""
    t = [x for x in re.split(r"[^0-9a-z]+", (name or "").lower()) if x]
    while t and t[0] in ROLES:
        t.pop(0)
    return t[0] if t else ""


def cell(s):
    return re.sub(r"\s+", " ", str(s if s is not None else "")).replace("|", "\\|").strip()


def upper95(n, misses):
    """95 % upper bound on the miss rate: 3/n at zero misses (rule of three), Wilson upper bound otherwise."""
    if n <= 0:
        return 1.0
    if misses == 0:
        return min(1.0, 3.0 / n)
    z, p = 1.96, misses / n
    return min(1.0, (p + z * z / (2 * n) + z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n))


FILES = {"entries": "entries.md", "banks": "banks.md"}  # two audits: stage 2b (facts, before authoring) and 3c (bank questions, after the banks exist)


def topic_list(s):
    return [t.strip() for t in (s or "").split(",") if t.strip() and t.strip() != "-"]


def _topic_sql(topics):
    return (f" AND topic IN ({','.join('?' * len(topics))})", list(topics)) if topics else ("", [])


def population(db, topics=None):
    c = sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True, timeout=60)
    have = {r[1] for r in c.execute("PRAGMA table_info(entries)")}
    sel = lambda n: n if n in have else "NULL"
    where, args = _topic_sql(topics)
    rows = c.execute(f"SELECT id,claim,{sel('quote')},{sel('locator')},{sel('author')},verified_by,{sel('derived')} FROM entries WHERE status='verified'{where} ORDER BY id", args).fetchall()
    c.close()
    return rows


def bank_population(cfg, root=None, topics=None):
    """(question key, basis, stem, keyed option) for every bank question; with topics, only banks whose slug is a topic."""
    out = []
    for f in cp.bank_files(cfg, root):
        if topics and f.stem not in topics:
            continue
        b = cp.load_bank(f)
        for q in b["questions"]:
            key = b["keys"].get(q["id"])
            out.append((f"{f.name}:{q['id']}", q["basis"], q["stem"], q["options"].get(key, "") if key else ""))
    return out


def is_verbatim(claim, quote):
    """A verbatim row: the claim IS (a span of) the quote -- the syllabus LO lines. Nothing was paraphrased, summed or counted."""
    c, q = " ".join((claim or "").split()).lower(), " ".join((quote or "").split()).lower()
    return bool(q) and (c == q or c in q)


def stratum(row):
    """G8: derived (census) | verbatim (a few) | nonverb (the bulk of the audit)."""
    if len(row) > 6 and row[6]:
        return "derived"
    return "verbatim" if is_verbatim(row[1], row[2]) else "nonverb"


def digest(db, bank_rows, ids, qids):
    """sha1 over the CURRENT content of the sampled rows: an entry edited, demoted or re-quoted after the draw changes it."""
    c = sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True, timeout=60)
    have = {r[1] for r in c.execute("PRAGMA table_info(entries)")}
    sel = lambda n: n if n in have else "NULL"
    parts = []
    for i in sorted(ids):
        r = c.execute(f"SELECT id,claim,{sel('quote')},{sel('locator')},status FROM entries WHERE id=?", (i,)).fetchone()
        parts.append("|".join(str(x) for x in (r or (i, "(gone)"))))
    c.close()
    byq = {q[0]: q for q in bank_rows}
    parts += ["|".join(byq.get(q, (q, "(gone)"))) for q in sorted(qids)]
    return hashlib.sha1("\n".join(parts).encode("utf-8")).hexdigest()


def verified_count(db, topics=None):
    c = sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True, timeout=60)
    where, args = _topic_sql(topics)
    n = c.execute(f"SELECT COUNT(*) FROM entries WHERE status='verified'{where}", args).fetchone()[0]
    c.close()
    return n


def floor_n(pop, pct, minimum):
    return min(pop, max(minimum, math.ceil(pct * pop)))


def draw(db, cfg, by, n="auto", seed=None, root=None, today=None, topics=None, kind="entries"):
    """-> (markdown text, refusal reason|None). Writes nothing itself.
    kind "entries": max(30, 5 %) of the verified entries (of `topics`, when given), stage 2b.
    kind "banks": max(10, 10 %) of the bank questions (of banks whose slug is in `topics`), with their basis, stage 3c."""
    topics = topic_list(",".join(topics)) if isinstance(topics, (list, tuple)) else topic_list(topics)
    me = agent_id(by)
    if not me:
        return None, f"auditor name '{by}' has no identity (role words only)"
    pop = population(db, topics)
    bq = bank_population(cfg, root, topics)
    seed = seed or hashlib.sha1((",".join(str(r[0]) for r in pop) + "|" + str(len(bq)) + "|" + kind + "|" + ",".join(topics)).encode()).hexdigest()[:12]
    rng = random.Random(seed)
    ents, qs = [], []
    if kind == "entries":
        if not pop:
            return None, "no verified entries to sample" + (f" for topics {topics}" if topics else "")
        der = [r for r in pop if stratum(r) == "derived"]
        nonv = [r for r in pop if stratum(r) == "nonverb"]
        verb = [r for r in pop if stratum(r) == "verbatim"]
        k_nv = floor_n(len(nonv), 0.05, 30) if n == "auto" else min(int(n), len(nonv))
        k_v = min(len(verb), max(5, math.ceil(0.02 * len(verb))))
        ents = sorted(der + rng.sample(nonv, k_nv) + rng.sample(verb, k_v), key=lambda r: r[0])  # census of derived + 30 non-verbatim + a few verbatim
        clash = sorted({r[0] for r in ents if me in (agent_id(r[4]), agent_id(r[5]))})
        if clash:
            return None, (f"auditor '{by}' (prefix '{me}') is the author or verifier of sampled entries {clash[:8]}; "
                          "the audit must be a run that wrote nothing -- brief a different auditor")
    else:
        if not bq:
            return None, "no bank questions to sample" + (f" for topics {topics}" if topics else "") + " (write the banks first: this is the stage-3c audit)"
        qs = sorted(rng.sample(bq, floor_n(len(bq), 0.10, 10)))
    ids, qids = [r[0] for r in ents], [q[0] for q in qs]
    sha = digest(db, bq, ids, qids)
    when = today or datetime.now().isoformat(timespec="seconds")
    L = ["# Audit sample " + ("(facts, stage 2b)" if kind == "entries" else "(bank questions, stage 3c)"), "",
         f"<!-- audit: kind={kind} by={by} drawn={when} seed={seed} topics={','.join(topics) or '-'} entries={len(ents)}/{len(pop)} "
         f"strata=derived:{sum(stratum(r) == 'derived' for r in ents)},nonverb:{sum(stratum(r) == 'nonverb' for r in ents)},verbatim:{sum(stratum(r) == 'verbatim' for r in ents)} "
         f"questions={len(qs)}/{len(bq)} verified={len(pop)} ids={','.join(map(str, ids))} qids={','.join(qids)} sha={sha} -->", "",
         "Open each raw locator, read the quote in place, write exactly `held` or `missed: why` in the last column. Leave nothing blank. "
         "Do not add, delete or reorder rows: `check` compares them with the drawn ids.", ""]
    if ents:
        L += ["## Entries", "", "| id | claim | quote | raw locator | stratum | verdict |", "|---|---|---|---|---|---|"]
        L += [f"| {r[0]} | {cell(r[1])} | {cell(r[2]) or '(none stored)'} | {cell(r[3]) or '(none stored)'} | {stratum(r)} | |" for r in ents]
    if qs:
        L += ["## Bank questions", "", "| question | basis | stem | keyed option | verdict |", "|---|---|---|---|---|"]
        L += [f"| {cell(q[0])} | {cell(q[1])} | {cell(q[2])[:160]} | {cell(q[3])} | |" for q in qs]
    return "\n".join(L) + "\n", None


def write_draw(root, text, by, kind="entries"):
    """Write audit/<entries|banks>.md; the previous header and every new header are appended to audit/draws.log (append-only)."""
    root = Path(root)
    (root / "audit").mkdir(exist_ok=True)
    f, log = root / "audit" / FILES[kind], root / "audit" / "draws.log"
    with open(log, "a", encoding="utf-8", newline="\n") as lg:
        if f.exists():
            old = re.search(r"<!--\s*audit:.*?-->", f.read_text(encoding="utf-8"), re.S)
            lg.write("REPLACED " + (re.sub(r"\s+", " ", old.group(0)) if old else "(no header)") + "\n")
        new = re.search(r"<!--\s*audit:.*?-->", text, re.S)
        lg.write("DRAWN " + re.sub(r"\s+", " ", new.group(0)) + "\n")
    f.write_text(text, encoding="utf-8", newline="\n")
    return f


def parse_sample(text):
    """-> (meta, entry_rows, question_rows). A row is (first_cell, verdict_cell, n_cells)."""
    meta = {}
    m = re.search(r"<!--\s*audit:(.*?)-->", text, re.S)
    if m:
        meta = dict(kv.split("=", 1) for kv in m.group(1).split() if "=" in kv)
    ents, qs, cur = [], [], None
    for ln in text.split("\n"):
        h = re.match(r"^##\s+(.*)$", ln)
        if h:
            cur = ents if h.group(1).strip().lower().startswith("entries") else qs if "question" in h.group(1).lower() else None
            continue
        if cur is None or not ln.startswith("|") or re.match(r"^\|\s*:?-{2,}", ln):
            continue
        cells = re.split(r"(?<!\\)\|", ln.strip().strip("|"))
        if cells and cells[0].strip().lower() in ("id", "question"):
            continue
        cur.append((cells[0].strip(), cells[-1].strip(), len(cells), cells[-2].strip() if cur is ents and len(cells) >= 6 else None))
    return meta, ents, qs


def verdict_kind(v):
    if not v:
        return "blank"
    if v == "held":
        return "held"
    return "missed" if re.fullmatch(r"missed(:[^|]*)?", v) else "bad"


def _one(root, kind, topics, cfg, db):
    """-> (ok, n, misses, blanks, msg) for one sample file; recount restricted to the topics stored in its header."""
    f = Path(root) / "audit" / FILES[kind]
    flag = f"--{kind}"
    if not f.is_file():
        return False, 0, 0, 0, f"{kind}: no {f.name} -- run `audit_sample.py draw {flag}` and have a blind auditor fill it"
    meta, ents, qs = parse_sample(f.read_text(encoding="utf-8"))
    for k in ("ids", "sha", "verified", "drawn"):
        if k not in meta:
            return False, 0, 0, 0, f"{kind}: header lacks '{k}': not written by `audit_sample.py draw`"
    errs = []
    if meta.get("kind", kind) != kind:
        errs.append(f"file holds a '{meta.get('kind')}' sample")
    scope = topic_list(meta.get("topics", "-"))
    if scope and topics and not set(topics) <= set(scope):
        errs.append(f"the sample covers topics {scope} but the report builds {sorted(set(topics) - set(scope))} too")
    drawn_ids = [int(x) for x in meta["ids"].split(",") if x]
    drawn_q = [x for x in meta.get("qids", "").split(",") if x]
    if [r[0] for r in ents] != [str(i) for i in drawn_ids]:
        errs.append(f"entry rows {len(ents)} differ from the {len(drawn_ids)} drawn ids (rows added, deleted or reordered)")
    if [r[0] for r in qs] != drawn_q:
        errs.append(f"question rows {len(qs)} differ from the {len(drawn_q)} drawn")
    rows = ents + qs
    n = len(rows)
    kinds = [verdict_kind(r[1]) if r[2] == (6 if i < len(ents) else 5) else "bad" for i, r in enumerate(rows)]
    blanks, misses = kinds.count("blank"), kinds.count("missed") + kinds.count("bad")
    if db.exists():
        if kind == "entries":
            now, at = verified_count(db, scope), int(meta["verified"])
            if now > math.ceil(at * 1.10) or now < at * 0.90:
                errs.append(f"verified entries{' of ' + ','.join(scope) if scope else ''} went from {at} at the draw to {now}: draw a fresh sample")
            pop_now = population(db, scope)
            by_s = {k: [r for r in pop_now if stratum(r) == k] for k in ("derived", "nonverb", "verbatim")}
            miss_der = [r[0] for r in by_s["derived"] if r[0] not in drawn_ids]
            if miss_der:
                errs.append(f"derived entries {miss_der[:6]} are not in the sample: every derived entry is audited (census); draw a fresh sample")
            got = {k: sum(1 for r in ents if r[3] == k) for k in by_s}
            need_nv = floor_n(len(by_s["nonverb"]), 0.05, 30)
            if got["nonverb"] < need_nv:
                errs.append(f"{got['nonverb']} non-verbatim entries sampled, floor for {len(by_s['nonverb'])} is {need_nv}")
            if got["verbatim"] < min(len(by_s["verbatim"]), 5):
                errs.append(f"{got['verbatim']} verbatim entries sampled, floor is {min(len(by_s['verbatim']), 5)}")
        bq = bank_population(cfg, root, scope)
        if digest(db, bq, drawn_ids, drawn_q) != meta["sha"]:
            errs.append("a sampled entry or question changed since the draw (sha differs): draw a fresh sample")
        if kind == "banks" and len(drawn_q) < floor_n(len(bq), 0.10, 10):
            errs.append(f"{len(drawn_q)} questions sampled, floor for {len(bq)} is {floor_n(len(bq), 0.10, 10)}")
    else:
        errs.append(f"no database at {db}")
    ok = n > 0 and not errs and blanks == 0 and misses == 0
    disc = None
    tol = (cfg.get("audit_tolerance") or {}).get(kind)
    if tol is not None and not ok:  # an owner's DISCLOSED tolerance: book.json audit_tolerance.<kind> = {"max_misses": N, "decided_by": "who / date"}
        mm = tol.get("max_misses") if isinstance(tol, dict) else None
        by = (tol.get("decided_by") or "").strip() if isinstance(tol, dict) and isinstance(tol.get("decided_by"), str) else ""
        if not isinstance(mm, int) or isinstance(mm, bool) or mm < 0 or not by:
            errs.append(f"book.json audit_tolerance.{kind} needs an integer max_misses >= 0 and a decided_by (who / date)")
        elif misses > mm:
            errs.append(f"{misses} misses exceed the disclosed tolerance max_misses={mm} (decided_by {by})")
        elif n > 0 and not errs and blanks == 0 and misses > 0:
            ok = True
            disc = dict(kind=kind, n=n, misses=misses, upper=upper95(n, misses), ids=[rows[i][0] for i, k_ in enumerate(kinds) if k_ in ("missed", "bad")],
                        decided_by=by, max_misses=mm)
    strat = ""
    if kind == "entries":
        parts_ = []
        for k in ("derived", "nonverb", "verbatim"):
            ks = [kinds[i] for i, r in enumerate(ents) if r[3] == k]
            m_ = sum(1 for x in ks if x not in ("held", "blank"))
            parts_.append(f"{k}: n={len(ks)} misses={m_}" + ("" if k == "derived" else f" upper95={upper95(len(ks), m_):.3f}") + (" (census)" if k == "derived" else ""))
        strat = " [" + "; ".join(parts_) + "]"
    msg = f"{kind}: n={n} held={kinds.count('held')} misses={misses} blank={blanks}{strat}" + (f" -- {'; '.join(errs)}" if errs else "")
    if disc:
        msg = (f"{kind}: DISCLOSED n={n} misses={misses} upper95={disc['upper']:.3f} missed [{', '.join(disc['ids'])}] "
               f"accepted by {disc['decided_by']} (tolerance max_misses={disc['max_misses']}){strat}")
    return ok, n, misses, blanks, msg, disc


def summarize(root=None, kind=None, topics=None):
    """-> dict(ok, n, misses, blanks, upper, msg). Both audits must hold (entries always; banks when the in-scope banks have
    questions) unless `kind` names one. A sample is valid only if it is the one drawn: rows equal the drawn ids, nothing sampled
    changed, the in-scope population grew < 10 %, the floors hold for the CURRENT population, every verdict is exactly `held`."""
    root = Path(root or ROOT)
    topics = topic_list(",".join(topics)) if isinstance(topics, (list, tuple)) else topic_list(topics)
    try:
        cfg = cp.load_cfg(root)
    except cp.ConfigError:
        cfg = {}
    try:
        db = cp.db_path(root)
    except cp.ConfigError as e:
        return dict(ok=False, n=0, misses=0, blanks=0, upper=1.0, msg=str(e))
    parts = []
    for k in ([kind] if kind else ["entries", "banks"]):
        if k == "banks" and not kind and not bank_population(cfg, root, topics or None):
            continue  # no bank questions in scope: nothing for the 3c audit to sample
        parts.append(_one(root, k, topics, cfg, db))
    n, misses, blanks = (sum(p[i] for p in parts) for i in (1, 2, 3))
    ok = bool(parts) and all(p[0] for p in parts)
    disclosures = [p[5] for p in parts if len(p) > 5 and p[5]]
    return dict(ok=ok, n=n, misses=misses, blanks=blanks, upper=upper95(n, misses), disclosed=bool(ok and disclosures), disclosures=disclosures,
                msg=" | ".join(p[4] for p in parts) + f" | total n={n} misses={misses} upper95={upper95(n, misses):.3f}")


def verified_since(db, when, scope):
    """Ids verified after `when` (an ISO datetime): from the kb log (exact), plus any entry whose verified_on is a later day."""
    c = sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True, timeout=60)
    ids = set()
    try:
        for ts, detail in c.execute("SELECT ts,detail FROM log WHERE action='verify' AND ts>?", (when,)):
            m = re.match(r"\s*(\d+)\b", detail or "")
            if m:
                ids.add(int(m.group(1)))
    except sqlite3.OperationalError:
        pass  # no log table: verified_on below is all there is
    have = {r[1] for r in c.execute("PRAGMA table_info(entries)")}
    if "verified_on" in have:
        ids |= {r[0] for r in c.execute("SELECT id FROM entries WHERE status='verified' AND verified_on>?", (when[:10],))}
    c.close()
    return ids


def topup(db, cfg, by, root, text, seed=None, now=None):
    """Extend an existing audit/entries.md instead of re-drawing it (stage 2b after the KB grew).
    Appends (a) a CENSUS of every verified entry verified after the draw and not yet sampled, (b) every derived entry not yet sampled,
    (c) enough extra non-verbatim / verbatim entries to restore the stratum floors for the CURRENT verified count. Existing rows and
    verdicts are untouched; the header's ids / entries / strata / verified / sha are re-based. Refuses when a sampled entry changed since
    the draw (re-signing it would hide the change) or when the auditor wrote or verified an appended row.
    -> (new text, [(id, stratum, why)], refusal|None)."""
    meta, ents, _ = parse_sample(text)
    for k in ("ids", "sha", "verified", "drawn"):
        if k not in meta:
            return text, [], f"sample header lacks '{k}': not written by `audit_sample.py draw`"
    if meta.get("kind", "entries") != "entries":
        return text, [], "only the entries audit is topped up"
    me = agent_id(by)
    if not me:
        return text, [], f"auditor name '{by}' has no identity (role words only)"
    scope = topic_list(meta.get("topics", "-"))
    old_ids = [int(x) for x in meta["ids"].split(",") if x]
    if [r[0] for r in ents] != [str(i) for i in old_ids]:
        return text, [], "the file's rows differ from its drawn ids (rows added, deleted or reordered): draw a fresh sample"
    if digest(db, [], old_ids, []) != meta["sha"]:
        return text, [], "a sampled entry changed since the draw (sha differs): a top-up must not re-sign it; draw a fresh sample"
    pop = population(db, scope)
    byid = {r[0]: r for r in pop}
    sampled = set(old_ids)
    add = {}
    for i in sorted(verified_since(db, meta["drawn"], scope)):
        if i in byid and i not in sampled:
            add[i] = "verified after the draw (census)"
    for r in pop:
        if stratum(r) == "derived" and r[0] not in sampled and r[0] not in add:
            add[r[0]] = "derived (census)"
    counts = {k: sum(1 for r in ents if r[3] == k) for k in ("derived", "nonverb", "verbatim")}
    for i in add:
        counts[stratum(byid[i])] += 1
    pools = {k: [r for r in pop if stratum(r) == k] for k in ("derived", "nonverb", "verbatim")}
    need = {"nonverb": floor_n(len(pools["nonverb"]), 0.05, 30), "verbatim": min(len(pools["verbatim"]), 5)}
    rng = random.Random(seed or hashlib.sha1((meta["sha"] + str(len(pop))).encode()).hexdigest()[:12])
    for k in ("nonverb", "verbatim"):
        short = need[k] - counts[k]
        free = [r for r in pools[k] if r[0] not in sampled and r[0] not in add]
        if short > 0 and free:
            for r in sorted(rng.sample(free, min(short, len(free))), key=lambda r: r[0]):
                add[r[0]] = f"extra {k} to restore the floor for {len(pools[k])}"
    if not add:
        return text, [], None
    clash = sorted(i for i in add if me in (agent_id(byid[i][4]), agent_id(byid[i][5])))
    if clash:
        return text, [], (f"auditor '{by}' (prefix '{me}') is the author or verifier of appended entries {clash[:8]}; brief a different auditor")
    rows = [byid[i] for i in sorted(add)]
    lines = text.split("\n")
    last = max(i for i, ln in enumerate(lines) if ln.startswith("|") and not re.match(r"^\|\s*:?-{2,}", ln) and i < (next((j for j, l2 in enumerate(lines) if l2.startswith("## Bank")), len(lines))))
    new_rows = [f"| {r[0]} | {cell(r[1])} | {cell(r[2]) or '(none stored)'} | {cell(r[3]) or '(none stored)'} | {stratum(r)} | |" for r in rows]
    lines[last + 1:last + 1] = new_rows
    all_ids = old_ids + [r[0] for r in rows]
    strata = {k: counts[k] + sum(1 for r in rows if stratum(r) == k and add[r[0]].startswith("extra")) for k in counts}
    meta2 = dict(meta)
    meta2.update(entries=f"{len(all_ids)}/{len(pop)}", verified=str(len(pop)), ids=",".join(map(str, all_ids)),
                 strata=f"derived:{strata['derived']},nonverb:{strata['nonverb']},verbatim:{strata['verbatim']}",
                 sha=digest(db, [], all_ids, []), topups=str(int(meta.get("topups", "0")) + 1), topup_by=by, topup_at=now or datetime.now().isoformat(timespec="seconds"))
    header = "<!-- audit: " + " ".join(f"{k}={v}" for k, v in meta2.items()) + " -->"
    out = "\n".join(lines)
    out = re.sub(r"<!--\s*audit:.*?-->", lambda m: header, out, count=1, flags=re.S)
    return out, [(r[0], stratum(r), add[r[0]]) for r in rows], None


def write_topup(root, new_text, by, added):
    """Atomic rewrite of audit/entries.md; one TOPUP line (header + added ids) appended to audit/draws.log."""
    import tempfile as _tf
    root = Path(root)
    f, log = root / "audit" / FILES["entries"], root / "audit" / "draws.log"
    new = re.search(r"<!--\s*audit:.*?-->", new_text, re.S)
    with open(log, "a", encoding="utf-8", newline="\n") as lg:
        lg.write("TOPUP " + re.sub(r"\s+", " ", new.group(0)) + " added=" + ",".join(str(a[0]) for a in added) + "\n")
    fd, tmp = _tf.mkstemp(dir=str(f.parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(new_text)
    os.replace(tmp, f)
    return f


def format_line(s):
    """The line `check` prints. DISCLOSED (not ok) when an owner-accepted tolerance absorbed the misses."""
    if s["ok"] and s.get("disclosed"):
        return "DISCLOSED audit " + s["msg"]
    return ("ok   " if s["ok"] else "FAIL ") + "audit " + s["msg"]


def report_topics(cfg, pages_root):
    """The topics a report builds: book.json "topics", else the slug (file stem) of every page it contains."""
    return list(cfg.get("topics") or sorted({p.stem for p in Path(pages_root).rglob("*.md") if not p.name.startswith("_")}))


def summarize_text(root, text, kind="entries"):
    (Path(root) / "audit").mkdir(exist_ok=True)
    (Path(root) / "audit" / FILES[kind]).write_text(text, encoding="utf-8")
    return summarize(root, kind)


def selftest():
    import shutil, tempfile
    d = Path(tempfile.mkdtemp())
    try:
        (d / "kb").mkdir()
        (d / "kb" / "kb.json").write_text(json.dumps({"db": "kb/t.db"}))
        (d / "book.json").write_text(json.dumps({"title": "T", "slug": "t", "pages": "ch", "kinds": {}, "practice": "practice"}))
        db = d / "kb" / "t.db"
        c = sqlite3.connect(db, timeout=60)
        c.execute("CREATE TABLE entries(id INTEGER PRIMARY KEY, topic TEXT, claim TEXT, status TEXT, quote TEXT, locator TEXT, author TEXT, verified_by TEXT)")
        for i in range(1, 101):
            c.execute("INSERT INTO entries VALUES(?,?,?,?,?,?,?,?)", (i, "ta" if i <= 60 else "tb", f"claim {i} | pipe", "verified", f"quote {i}", f"research/_raw/s/f.txt:{i}", "wa-helper", "wv-lead"))
        c.execute("INSERT INTO entries VALUES(101,'ta','draft one','draft',NULL,NULL,'wa-helper',NULL)")
        c.commit(); c.close()
        (d / "practice").mkdir()
        qs = "".join(f"### Q-{i:02d}\n- objective: t-1\n- level: K1\n- basis: KB#{i}\nStem {i}?\na) x\nb) y\n" for i in range(1, 41))
        (d / "practice" / "ta.md").write_text("## Questions\n" + qs, encoding="utf-8")
        (d / "practice" / "ta.key.md").write_text("".join(f"Q-{i:02d}: a\n" for i in range(1, 41)), encoding="utf-8")
        cfg = {"practice": "practice"}
        text, why = draw(db, cfg, "aud-1", root=d)
        assert why is None
        meta, ents, qrows = parse_sample(text)
        assert meta["kind"] == "entries" and meta["entries"] == "30/100" and meta["questions"] == "0/40" and len(ents) == 30 and not qrows, meta  # max(30, 5 %)
        assert all(r[1] == "" for r in ents), "fresh sample must have blank verdicts"
        assert "\\|" in text and "(none stored)" not in text
        assert draw(db, cfg, "aud-1", root=d)[0].split("drawn=")[0] == text.split("drawn=")[0], "the draw is not reproducible"
        for who in ("wa-writer", "verify-wv", "wv-lead"):
            assert draw(db, cfg, who, root=d)[1], f"auditor '{who}' sharing a prefix with an author/verifier was not refused"
        assert draw(db, cfg, "audit", root=d)[1], "role-words-only auditor accepted"
        assert len(parse_sample(draw(db, cfg, "aud-1", n="50", root=d)[0])[1]) == 50
        f = write_draw(d, text, "aud-1")
        assert f.name == "entries.md"
        assert summarize(d, "entries")["blanks"] == 30 and not summarize(d, "entries")["ok"], "blank verdicts must fail"
        held = re.sub(r"\| \|\n", "| held |\n", text)
        f.write_text(held, encoding="utf-8")
        s = summarize(d, "entries")
        assert s["ok"] and s["n"] == 30 and s["misses"] == 0 and abs(s["upper"] - 3 / 30) < 1e-9, s
        # F3 / B12-B16 (round 3)
        rows = held.split("\n")
        first = next(i for i, l in enumerate(rows) if l.startswith("| ") and l.split("|")[1].strip().isdigit())
        f.write_text("\n".join(rows[:first] + rows[first + 3:]), encoding="utf-8")
        assert not summarize(d, "entries")["ok"] and "differ from the" in summarize(d, "entries")["msg"], "B12: deleted rows passed"
        f.write_text(held.replace("| held |\n", "| missed: why \\| held |\n", 1), encoding="utf-8")
        s = summarize(d, "entries")
        assert not s["ok"] and s["misses"] >= 1, f"B13: 'missed: why | held' counted as held: {s}"
        f.write_text(held.replace("| held |\n", "| missed: quote says 25 |\n", 1), encoding="utf-8")
        s = summarize(d, "entries")
        assert not s["ok"] and s["misses"] == 1 and s["upper"] > 1 / 30, s
        f.write_text(held.replace("| held |\n", "| Held |\n", 1), encoding="utf-8")
        assert not summarize(d, "entries")["ok"], "a verdict that is not exactly `held` passed"
        f.write_text(held + "".join("| 9999 | x | y | z | held |\n" for _ in range(1000)), encoding="utf-8")
        assert not summarize(d, "entries")["ok"], "B14: appended rows passed"
        f.write_text(held, encoding="utf-8")
        c = sqlite3.connect(db, timeout=60)
        c.executemany("INSERT INTO entries VALUES(?,?,?,?,?,?,?,?)", [(200 + i, "ta", f"late {i}", "verified", "q", "l", "wa-helper", "wv-lead") for i in range(14)])
        c.commit(); c.close()
        s = summarize(d, "entries")
        assert not s["ok"] and "fresh sample" in s["msg"], f"B15: a sample older than 14 later verifications passed: {s}"
        c = sqlite3.connect(db, timeout=60); c.execute("DELETE FROM entries WHERE id>=200"); c.commit(); c.close()
        assert summarize(d, "entries")["ok"], "restoring the population should restore ok"
        first_id = int(meta["ids"].split(",")[0])
        c = sqlite3.connect(db, timeout=60); c.execute("UPDATE entries SET claim='changed' WHERE id=?", (first_id,)); c.commit(); c.close()
        assert not summarize(d, "entries")["ok"] and "changed since the draw" in summarize(d, "entries")["msg"], "an edited sampled entry passed"
        c = sqlite3.connect(db, timeout=60); c.execute("UPDATE entries SET claim=? WHERE id=?", (f"claim {first_id} | pipe", first_id)); c.commit(); c.close()
        small = re.sub(r"entries=\d+/\d+", "entries=1/1", held)
        small = re.sub(r" ids=[\d,]+", " ids=" + str(first_id), small)
        small = re.sub(r" verified=\d+", " verified=1", small)
        assert not summarize_text(d, small)["ok"], "mnt B2: a header edited to entries=1/1 passed"
        f.write_text(held, encoding="utf-8")
        write_draw(d, draw(db, cfg, "aud-1", seed="7", root=d)[0], "aud-1")
        log = (d / "audit" / "draws.log").read_text(encoding="utf-8")
        assert log.count("DRAWN") == 2 and "REPLACED" in log and "seed=7" in log, log
        # ---- S1: --topic restricts the sample AND the recount, and is stored in the header
        t_text, why = draw(db, cfg, "aud-1", root=d, topics="ta")
        assert why is None
        tm, tents, _ = parse_sample(t_text)
        assert tm["topics"] == "ta" and tm["entries"] == "30/60" and all(int(r[0]) <= 60 for r in tents), tm
        assert draw(db, cfg, "aud-1", root=d, topics="tb")[0].count("| 6") + draw(db, cfg, "aud-1", root=d, topics="tb")[0].count("| 7") > 0
        tf = write_draw(d, t_text, "aud-1")
        tf.write_text(re.sub(r"\| \|\n", "| held |\n", t_text), encoding="utf-8")
        assert summarize(d, "entries", topics="ta")["ok"], summarize(d, "entries", topics="ta")
        c = sqlite3.connect(db, timeout=60)
        c.executemany("INSERT INTO entries VALUES(?,?,?,?,?,?,?,?)", [(300 + i, "tb", f"other {i}", "verified", "q", "l", "wa-helper", "wv-lead") for i in range(40)])
        c.commit(); c.close()
        assert summarize(d, "entries", topics="ta")["ok"], "S1: verified entries added to ANOTHER topic must not invalidate a topic-restricted sample"
        assert not summarize(d, "entries", topics="ta,tb")["ok"] and "covers topics" in summarize(d, "entries", topics="ta,tb")["msg"], "S1: a report building tb must not accept a ta-only audit"
        c = sqlite3.connect(db, timeout=60)
        c.executemany("INSERT INTO entries VALUES(?,?,?,?,?,?,?,?)", [(400 + i, "ta", f"more {i}", "verified", "q", "l", "wa-helper", "wv-lead") for i in range(10)])
        c.commit(); c.close()
        assert not summarize(d, "entries", topics="ta")["ok"], "S1: 10 new verified entries in the sampled topic (> 10 %) must invalidate it"
        c = sqlite3.connect(db, timeout=60); c.execute("DELETE FROM entries WHERE id>=300"); c.commit(); c.close()
        # ---- T5: --topup extends entries.md with a census of what was verified since the draw + the extra rows the CURRENT floor needs
        d3 = Path(tempfile.mkdtemp())
        (d3 / "kb").mkdir()
        (d3 / "kb" / "kb.json").write_text(json.dumps({"db": "kb/u.db"}))
        (d3 / "book.json").write_text(json.dumps({"title": "T", "slug": "t", "pages": "ch", "kinds": {}, "practice": "practice"}))
        db3 = d3 / "kb" / "u.db"
        c3 = sqlite3.connect(db3, timeout=60)
        c3.execute("CREATE TABLE entries(id INTEGER PRIMARY KEY, topic TEXT, claim TEXT, status TEXT, quote TEXT, locator TEXT, author TEXT, verified_by TEXT, derived TEXT, verified_on TEXT)")
        c3.execute("CREATE TABLE log(ts TEXT, action TEXT, detail TEXT)")
        add_e = lambda i, who="wa-h", day="2020-01-01": c3.execute("INSERT INTO entries VALUES(?,?,?,?,?,?,?,?,?,?)", (i, "t", f"paraphrase {i}", "verified", f"original wording {i}", "f:1", who, "wv-l", None, day))
        for i in range(1, 601):
            add_e(i)
        c3.commit()
        t3, why3 = draw(db3, {}, "aud-5", root=d3)
        assert why3 is None and parse_sample(t3)[0]["entries"] == "30/600", parse_sample(t3)[0]
        f3 = write_draw(d3, t3, "aud-5")
        held3 = re.sub(r"\| \|\n", "| held |\n", t3)
        f3.write_text(held3, encoding="utf-8")
        assert summarize(d3, "entries")["ok"]
        drawn3 = parse_sample(held3)[0]["drawn"]
        # 41 entries joined the KB without a post-draw log row (older verified_on): population 641 -> floor 33 > 30 sampled
        for i in range(601, 642):
            add_e(i)
        c3.commit()
        s3 = summarize(d3, "entries")
        assert not s3["ok"] and "floor for 641 is 33" in s3["msg"], s3["msg"]
        assert topup(db3, {}, "wa-helper", d3, held3)[2] is not None and "appended" in topup(db3, {}, "wa-helper", d3, held3)[2], "T5: an auditor who authored an appended row must be refused"
        new3, added3, why = topup(db3, {}, "aud-5", d3, held3)
        assert why is None and len(added3) == 3 and all(w.startswith("extra nonverb") for _, _, w in added3), (why, added3)
        old_rows = [l for l in held3.split("\n") if l.startswith("| ") and "held" in l]
        assert all(l in new3.split("\n") for l in old_rows), "T5: existing rows and verdicts must be untouched"
        m3 = parse_sample(new3)[0]
        assert m3["entries"] == "33/641" and m3["verified"] == "641" and m3["topups"] == "1" and m3["strata"] == "derived:0,nonverb:33,verbatim:0" and m3["drawn"] == drawn3, m3
        write_topup(d3, new3, "aud-5", added3)
        s3 = summarize(d3, "entries")
        assert not s3["ok"] and "blank=3" in s3["msg"] and "floor" not in s3["msg"], s3["msg"]
        f3.write_text(re.sub(r"\| \|\n", "| held |\n", f3.read_text(encoding="utf-8")), encoding="utf-8")
        s3 = summarize(d3, "entries")
        assert s3["ok"] and s3["n"] == 33, s3
        assert "TOPUP" in (d3 / "audit" / "draws.log").read_text(encoding="utf-8") and not list((d3 / "audit").glob("*.tmp"))
        assert topup(db3, {}, "aud-5", d3, f3.read_text(encoding="utf-8"))[1] == [] and topup(db3, {}, "aud-5", d3, f3.read_text(encoding="utf-8"))[2] is None, "T5: nothing to add is a clean no-op"
        # 17 entries verified AFTER the draw (logged) + one derived: the census takes every one of them
        for i in range(642, 659):
            add_e(i, day="2999-01-01")
            c3.execute("INSERT INTO log VALUES(?,?,?)", ("2999-01-01T00:00:00", "verify", f"{i} by wv-l at x:1"))
        c3.execute("INSERT INTO entries VALUES(700,'t','derived count','verified','adjacent line','f:2','wa-h','wv-l','counted over the LO entries','2999-01-01')")
        c3.execute("INSERT INTO log VALUES('2999-01-01T00:00:01','verify','700 by wv-l at x:2')")
        c3.commit()
        before3 = f3.read_text(encoding="utf-8")
        assert not summarize(d3, "entries")["ok"], "the newest entries are unsampled: check must fail"
        new4, added4, why4 = topup(db3, {}, "aud-5", d3, before3)
        assert why4 is None and {i for i, _, _ in added4} >= set(range(642, 659)) | {700} and sum(1 for _, _, w in added4 if "census" in w) == 18, added4
        assert [s_ for i, s_, _ in added4 if i == 700] == ["derived"]
        write_topup(d3, new4, "aud-5", added4)
        f3.write_text(re.sub(r"\| \|\n", "| held |\n", f3.read_text(encoding="utf-8")), encoding="utf-8")
        s4 = summarize(d3, "entries")
        assert s4["ok"] and s4["n"] >= 33 + 18 and parse_sample(f3.read_text(encoding="utf-8"))[0]["topups"] == "2", s4
        # the command line: `draw --entries --topup --by X`
        import subprocess as _sp
        cli3 = lambda *a: _sp.run([sys.executable, os.path.abspath(__file__), "draw", *a], env=dict(os.environ, BOOK_ROOT=str(d3), PYTHONUTF8="1"), capture_output=True, text=True, encoding="utf-8")
        r_ = cli3("--entries", "--topup", "--by", "aud-5")
        assert r_.returncode == 0 and "nothing to add" in r_.stdout, r_.stdout + r_.stderr
        add_e(800, day="2999-01-02")
        c3.execute("INSERT INTO log VALUES('2999-01-02T00:00:00','verify','800 by wv-l at x:3')"); c3.commit()
        r_ = cli3("--entries", "--topup", "--by", "wa-helper")
        assert r_.returncode == 1 and "FAIL" in r_.stdout and " 800" not in f3.read_text(encoding="utf-8"), "the CLI must refuse an auditor who wrote an appended row and change nothing"
        r_ = cli3("--entries", "--topup", "--by", "aud-5")
        assert r_.returncode == 0 and "appended 1 row(s)" in r_.stdout and "| 800 |" in f3.read_text(encoding="utf-8") and "TOPUP" in (d3 / "audit" / "draws.log").read_text(encoding="utf-8"), r_.stdout + r_.stderr
        assert cli3("--banks", "--topup", "--by", "aud-5").returncode == 1, "--topup is for the entries audit only"
        f3.write_text(re.sub(r"\| \|\n", "| held |\n", f3.read_text(encoding="utf-8")), encoding="utf-8")
        assert summarize(d3, "entries")["ok"]
        # a sampled entry edited after the draw: a top-up must refuse instead of re-signing it
        c3.execute("UPDATE entries SET claim='edited after the draw' WHERE id=?", (old_ids3 := int(parse_sample(f3.read_text(encoding='utf-8'))[0]["ids"].split(",")[0]),)); c3.commit()
        assert "changed since the draw" in (topup(db3, {}, "aud-5", d3, f3.read_text(encoding="utf-8"))[2] or ""), "T5: a changed sampled entry must block the top-up"
        c3.close()
        import shutil as _sh3
        _sh3.rmtree(d3, ignore_errors=True)

        # ---- S2: two audits; the banks one needs banks and is a separate file
        assert draw(db, cfg, "aud-1", root=d, kind="banks", topics="tb")[1] and "no bank questions" in draw(db, cfg, "aud-1", root=d, kind="banks", topics="tb")[1]
        b_text, why = draw(db, cfg, "aud-1", root=d, kind="banks", topics="ta")
        assert why is None
        bm, bents, bqs = parse_sample(b_text)
        assert bm["kind"] == "banks" and bm["questions"] == "10/40" and not bents and len(bqs) == 10 and "KB#" in b_text, bm  # max(10, 10 %) with their basis
        full = summarize(d, topics="ta")
        assert not full["ok"] and "banks: no banks.md" in full["msg"], f"S2: the report must refuse with only the entries audit when the topic has bank questions: {full}"
        bf = write_draw(d, b_text, "aud-1", "banks")
        assert bf.name == "banks.md" and not summarize(d, topics="ta")["ok"], "blank bank verdicts must fail the combined check"
        bf.write_text(re.sub(r"\| \|\n", "| held |\n", b_text), encoding="utf-8")
        both = summarize(d, topics="ta")
        assert both["ok"] and both["n"] == 40 and "entries:" in both["msg"] and "banks:" in both["msg"], both
        # ---- T1: a DISCLOSED miss (owner decision): book.json audit_tolerance.banks = {"max_misses": N, "decided_by": "..."}
        bj = d / "book.json"
        base_cfg = json.loads(bj.read_text(encoding="utf-8"))
        held_b = re.sub(r"\| \|\n", "| held |\n", b_text)
        one = held_b.replace("| held |\n", "| missed: stem is ambiguous |\n", 1)
        two = one.replace("| held |\n", "| missed: second |\n", 1)
        tol = lambda n_, by="owner 2026-10-16": bj.write_text(json.dumps(dict(base_cfg, audit_tolerance={"banks": {"max_misses": n_, "decided_by": by}})), encoding="utf-8")
        bf.write_text(one, encoding="utf-8")
        assert not summarize(d, topics="ta")["ok"] and not summarize(d, topics="ta").get("disclosed"), "no tolerance key: one miss must fail as before"
        tol(1)
        s1 = summarize(d, topics="ta")
        assert s1["ok"] and s1["disclosed"] and s1["misses"] == 1 and len(s1["disclosures"]) == 1, s1
        d1 = s1["disclosures"][0]
        assert d1["kind"] == "banks" and d1["n"] == 10 and d1["decided_by"] == "owner 2026-10-16" and d1["max_misses"] == 1 and len(d1["ids"]) == 1 and 0 < d1["upper"] < 1, d1
        line = format_line(s1)
        assert line.startswith("DISCLOSED audit") and not line.startswith("ok") and "n=10" in line and "misses=1" in line and "upper95=" in line and "owner 2026-10-16" in line, line
        bf.write_text(two, encoding="utf-8")
        s2 = summarize(d, topics="ta")
        assert not s2["ok"] and not s2["disclosed"] and "exceed the disclosed tolerance max_misses=1" in s2["msg"] and format_line(s2).startswith("FAIL"), s2
        tol(2)
        assert summarize(d, topics="ta")["ok"] and summarize(d, topics="ta")["disclosed"], "tolerance 2 absorbs two misses"
        bf.write_text(held_b, encoding="utf-8")
        assert summarize(d, topics="ta")["ok"] and not summarize(d, topics="ta")["disclosed"] and format_line(summarize(d, topics="ta")).startswith("ok"), "no miss: plain ok, not DISCLOSED"
        bf.write_text(one.replace("| held |\n", "| |\n", 1), encoding="utf-8")
        tol(1)
        assert not summarize(d, topics="ta")["ok"], "a blank verdict is never tolerated"
        bf.write_text(one, encoding="utf-8")
        for bad_key in ({"max_misses": 1}, {"max_misses": 1, "decided_by": "  "}, {"max_misses": -1, "decided_by": "x"}, {"max_misses": True, "decided_by": "x"}, "yes"):
            bj.write_text(json.dumps(dict(base_cfg, audit_tolerance={"banks": bad_key})), encoding="utf-8")
            assert not summarize(d, topics="ta")["ok"], f"an incomplete tolerance {bad_key!r} must not absorb a miss"
        tol(1)
        ef = d / "audit" / "entries.md"
        keep_e = ef.read_text(encoding="utf-8")
        ef.write_text(keep_e.replace("| held |\n", "| missed: x |\n", 1), encoding="utf-8")
        assert not summarize(d, topics="ta")["ok"], "the banks tolerance must not excuse a miss in the entries audit"
        ef.write_text(keep_e, encoding="utf-8")
        bj.write_text(json.dumps(base_cfg), encoding="utf-8")
        bf.write_text(re.sub(r"\| \|\n", "| held |\n", b_text).replace("KB#1 ", "KB#1 ", 1), encoding="utf-8")
        c = sqlite3.connect(db, timeout=60); c.close()
        (d / "practice" / "ta.md").write_text((d / "practice" / "ta.md").read_text(encoding="utf-8").replace("Stem ", "Changed stem "), encoding="utf-8")
        assert not summarize(d, topics="ta")["ok"], "S2: a bank question edited after the draw must invalidate the banks audit"
        (d / "practice" / "ta.md").write_text((d / "practice" / "ta.md").read_text(encoding="utf-8").replace("Changed stem ", "Stem "), encoding="utf-8")
        # a topic without banks needs only the entries audit
        ftb = d / "audit" / "entries.md"
        tb_text, _ = draw(db, cfg, "aud-1", root=d, topics="tb")
        ftb.write_text(re.sub(r"\| \|\n", "| held |\n", tb_text), encoding="utf-8")
        assert summarize(d, topics="tb")["ok"], "a topic with no bank questions must not demand a banks audit"
        assert 0.0 < upper95(100, 0) < upper95(100, 1) < upper95(100, 5) < 1
        assert summarize(Path(tempfile.mkdtemp()))["ok"] is False
        # ---- G8: strata -- every derived entry (census) + >= 30 non-verbatim + a few verbatim LO lines, per-stratum results
        d2 = Path(tempfile.mkdtemp())
        (d2 / "kb").mkdir()
        (d2 / "kb" / "kb.json").write_text(json.dumps({"db": "kb/s.db"}))
        (d2 / "book.json").write_text(json.dumps({"title": "T", "slug": "t", "pages": "ch", "kinds": {}, "practice": "practice"}))
        c2 = sqlite3.connect(d2 / "kb" / "s.db", timeout=60)
        c2.execute("CREATE TABLE entries(id INTEGER PRIMARY KEY, topic TEXT, claim TEXT, status TEXT, quote TEXT, locator TEXT, author TEXT, verified_by TEXT, derived TEXT)")
        for i in range(1, 94):
            if i <= 3:
                row = (i, "t", f"count {i} of LOs", "verified", "adjacent line", "f:1", "a-h", "v-l", "counted over the LO entries")
            elif i <= 43:
                row = (i, "t", f"FL-1.{i} (K2) Explain thing {i}", "verified", f"FL-1.{i} (K2) Explain thing {i}", "f:2", "a-h", "v-l", None)
            else:
                row = (i, "t", f"paraphrase {i}", "verified", f"original wording {i}", "f:3", "a-h", "v-l", None)
            c2.execute("INSERT INTO entries VALUES(?,?,?,?,?,?,?,?,?)", row)
        c2.commit(); c2.close()
        db2 = d2 / "kb" / "s.db"
        t2, why2 = draw(db2, {}, "aud-9", root=d2)
        assert why2 is None
        m2, e2, _ = parse_sample(t2)
        assert m2["strata"] == "derived:3,nonverb:30,verbatim:5" and m2["entries"] == "38/93", m2
        assert {r[0] for r in e2} >= {"1", "2", "3"} and [r[3] for r in e2].count("derived") == 3, "G8: every derived entry is sampled (census)"
        assert all(r[2] == 6 for r in e2) and "| stratum | verdict |" in t2
        f2 = write_draw(d2, t2, "aud-9")
        f2.write_text(re.sub(r"\| \|\n", "| held |\n", t2), encoding="utf-8")
        s2 = summarize(d2, "entries")
        assert s2["ok"] and "derived: n=3 misses=0 (census)" in s2["msg"] and "nonverb: n=30" in s2["msg"] and "verbatim: n=5" in s2["msg"] and "upper95=" in s2["msg"], s2
        f2.write_text(re.sub(r"\| \|\n", "| held |\n", t2).replace("| held |\n", "| missed: count is 4 |\n", 1), encoding="utf-8")
        s2 = summarize(d2, "entries")
        assert not s2["ok"] and s2["misses"] == 1, s2
        f2.write_text(re.sub(r"\| \|\n", "| held |\n", t2), encoding="utf-8")
        late = next(i for i in range(44, 94) if str(i) not in {r[0] for r in e2})
        c2 = sqlite3.connect(db2, timeout=60); c2.execute("UPDATE entries SET derived='late' WHERE id=?", (late,)); c2.commit(); c2.close()
        s2 = summarize(d2, "entries")
        assert not s2["ok"] and "census" in s2["msg"] and str(late) in s2["msg"], f"G8: a derived entry outside the sample passed: {s2}"
        import shutil as _sh
        _sh.rmtree(d2, ignore_errors=True)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("selftest ok"); return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    for name in ("draw", "check"):
        x = sp.add_parser(name)
        x.add_argument("--topic", help="comma list: restrict the sample (draw) or the recount (check) to these topics")
        x.add_argument("--entries", action="store_true", help="the stage-2b audit of verified facts")
        x.add_argument("--banks", action="store_true", help="the stage-3c audit of bank questions")
        if name == "draw":
            x.add_argument("--by", required=True); x.add_argument("--n", default="auto"); x.add_argument("--seed")
            x.add_argument("--topup", action="store_true", help="with --entries: extend the existing entries.md with a census of what was verified since the draw "
                           "and the extra entries the current floor needs (existing verdicts untouched)")
    a = ap.parse_args(argv)
    kinds = [k for k in ("entries", "banks") if getattr(a, k)] or ["entries", "banks"]
    if a.cmd == "draw":
        try:
            cfg = cp.load_cfg()
            db = cp.db_path()
        except cp.ConfigError as e:
            print(f"FAIL {e}"); return 1
        if not db.exists():
            print(f"FAIL no database at {db}"); return 1
        if a.topup:
            f = ROOT / "audit" / FILES["entries"]
            if not f.is_file() or a.banks:
                print("FAIL --topup extends an existing audit/entries.md (run `draw --entries` first); it does not apply to --banks"); return 1
            new, added, why = topup(db, cfg, a.by, ROOT, f.read_text(encoding="utf-8"), a.seed)
            if why:
                print(f"FAIL {why}"); return 1
            if not added:
                print("topup: nothing to add -- every entry verified since the draw is already sampled and the floors hold"); return 0
            write_topup(ROOT, new, a.by, added)
            by_why = {}
            for _, st_, w_ in added:
                by_why[w_.split(" for ")[0]] = by_why.get(w_.split(" for ")[0], 0) + 1
            print(f"topup: appended {len(added)} row(s) to {f} ({'; '.join(f'{n} {w}' for w, n in by_why.items())}); blank verdicts for the auditor, existing verdicts untouched")
            return 0
        rc = 0
        for k in kinds:
            text, why = draw(db, cfg, a.by, a.n, a.seed, topics=a.topic, kind=k)
            if why:
                if k == "banks" and not (a.banks):  # a plain `draw` skips the banks audit when there are no banks yet
                    print(f"skip banks audit: {why}"); continue
                print(f"FAIL {why}"); rc = 1; continue
            out = write_draw(ROOT, text, a.by, k)
            meta = parse_sample(text)[0]
            print(f"wrote {out}  topics={meta['topics']} entries={meta['entries']} questions={meta['questions']}  (header logged in audit/draws.log)")
        return rc
    kind = kinds[0] if len(kinds) == 1 else None
    s = summarize(kind=kind, topics=a.topic)
    print(format_line(s))
    return 0 if s["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
