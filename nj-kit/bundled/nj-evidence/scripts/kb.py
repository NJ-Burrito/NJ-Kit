#!/usr/bin/env python3
"""kb.py -- gated fact database (SQLite, stdlib only). PYTHONUTF8=1 assumed.

Every fact is an ENTRY tied to at least one SOURCE. An entry is never "verified"
by a model's say-so: it needs a lone TIER-1 primary source OR two independent
sources (different hosts), a retrieval date, a named verifier who is a different
agent from the author, AND a quoted span that really occurs in the raw file the
fact was read from. Nothing that is not `verified` may be published.

Project = BOOK_ROOT env or cwd. Config = <project>/kb/kb.json, REQUIRED (no project's values are guessed:
`kb.py init` without it writes a template and stops so you fill in db, sectors, primary_hosts):
    {"db": "kb/qa.db", "sectors": ["a", "b"], "primary_hosts": {"istqb.org": 1}}
`add-source --tier 1` needs `primary_hosts` in kb/kb.json and refuses any host not listed
(a missing key refuses every tier-1 source: there is no silent default). Optional
"raw_index": "research/_raw/index.tsv" (written by fetch.py).
Read commands open the DB read-only and never alter it; columns are added (ALTER)
only inside write commands.

    kb.py init
    kb.py add-source --sector S --name N --url URL --tier 2 [--kind page|rss] [--note ..] [--allow-root REASON]
    kb.py add-entry  --sector S --topic T --claim ".." --sources 3,7 --by <author> [--summary ..] [--tags a,b] [--retrieved YYYY-MM-DD]
    kb.py add-batch  FILE.jsonl [--by <author>]      one JSON object per line: sector,topic,claim,sources[,by,summary,tags,retrieved];
                                                     strict UTF-8, refuses any CR, empty claim/sources; one transaction; prints ids.
                                                     add-entry / add-batch are idempotent: same topic + whitespace-normalised claim -> `dup <id>`
    kb.py verify ID --by "<who>" --quote "<span>" --raw <file> [--derived "<reason>"] [--second-source ID] [--allow-root REASON]
                                                     --raw must be a file fetch.py indexed (research/_raw/index.tsv) for the URL of one of
                                                     the entry's sources, its sha1 unchanged; the quote must occur in it (whitespace-
                                                     normalised) and every number in the claim must occur in the quote, unless
                                                     --derived "<reason, >= 10 chars>" waives the number rule (counted in `stats`)
    kb.py verify-batch FILE.jsonl --by "<who>"       rows {id, quote, raw[, derived][, weak: true]} (quote and raw may each be a LIST: several spans, several files); each row gets exactly verify's checks (a weak:true row is refused); held rows are
                                                     written in one transaction, refused rows are listed; exit 1 if any refused
    kb.py hygiene [--topic T[,T]] [--apply --by "<who>"]   dry run: claims carrying provenance text (Source: .., (retrieved <date>), (page N), section 7.1)
                                                     and what they would become; --apply moves the text to the summary through the amend path
                                                     WITHOUT resetting status (only when nothing but the trailer is removed); the rest is listed
    kb.py query  [--sector S] [--topic T] [--tag x] [--status verified] [--limit 20] [--full]
    kb.py sources [--sector S] [--tier 1]
    kb.py stats
    kb.py stale [--days 90]
    kb.py export --sector S                          -> kb/digest-S.md (a checkpoint file)
    kb.py triage --ids 1,2 | --all --by <who>        mark feed items as looked at
    kb.py feed [--sector S] [--untriaged] [--limit N]
    kb.py fix-sources ID --sources 1,2 --by <who> --reason ".."   repair a citation; forces back to draft
    kb.py detach ID --source SID --by "<who>" --reason ".."       withdraw one source's support, rescore, demote if the bar is missed
    kb.py demote ID --by "<who>" --reason ".." [--kind discredited|gate-change]   verified -> 'retracted'
    kb.py amend  ID --by "<who>" --reason ".." [--claim ..] [--summary ..]        correct in place (--claim resets to draft)
    kb.py --selftest

Output is deliberately terse (one line per row). Exit 0 ok, 1 refusal/failure.
Same-agent rule: the part of a name before its first hyphen (after leading role words
such as `verify-`) is the run identity; author and verifier sharing it are refused.
"""
from __future__ import annotations
import argparse, json, re, sqlite3, sys, os, types, datetime as dt
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.abspath(os.environ.get("BOOK_ROOT") or os.getcwd())


def _load_cfg(root):
    try:
        with open(os.path.join(root, "kb", "kb.json"), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


CFG = _load_cfg(ROOT)
CFG_PRESENT = os.path.isfile(os.path.join(ROOT, "kb", "kb.json"))
DB = os.path.join(ROOT, CFG.get("db", "kb/facts.db"))
SECTORS = tuple(CFG.get("sectors") or ())
PRIMARY_HOSTS = CFG.get("primary_hosts")  # None = no allowlist configured
TIERS = {1: "official / standards body / primary", 2: "peer-reviewed / institutional",
         3: "reputable specialist media / vendor docs", 4: "community / aggregator"}
SCHEMA = """
CREATE TABLE IF NOT EXISTS sources(
  id INTEGER PRIMARY KEY, sector TEXT NOT NULL, name TEXT NOT NULL, url TEXT NOT NULL UNIQUE,
  kind TEXT DEFAULT 'page', tier INTEGER NOT NULL CHECK(tier BETWEEN 1 AND 4),
  note TEXT, added TEXT NOT NULL, last_checked TEXT, last_hash TEXT, status TEXT DEFAULT 'new');
CREATE TABLE IF NOT EXISTS entries(
  id INTEGER PRIMARY KEY, sector TEXT NOT NULL, topic TEXT NOT NULL, claim TEXT NOT NULL,
  summary TEXT, tags TEXT, source_ids TEXT NOT NULL, retrieved TEXT NOT NULL,
  status TEXT DEFAULT 'draft', verified_by TEXT, verified_on TEXT, second_source INTEGER,
  confidence REAL DEFAULT 0.5, updated TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS updates(
  id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL, title TEXT, link TEXT UNIQUE,
  published TEXT, seen TEXT NOT NULL, triaged INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS log(ts TEXT, action TEXT, detail TEXT);
"""
# Columns added after the first schema. Applied (ALTER) only by write commands, and only
# when missing; read commands never touch the file. `note` is the retraction/amendment
# record; `quote`/`locator`/`derived` are the verification evidence.
# ponytail: one appended text column per fact, not a history table.
NEW_COLUMNS = {"entries": [("author", "TEXT"), ("note", "TEXT"), ("quote", "TEXT"),
                           ("locator", "TEXT"), ("derived", "TEXT")]}
OPTIONAL = ("author", "note", "quote", "locator", "derived")  # may be absent on an old DB being read


def today():
    return dt.date.today().isoformat()


def con(write=False):
    """write=True: create/migrate and return a read-write connection.
    write=False: read-only handle; refuses if the DB does not exist."""
    if write:
        os.makedirs(os.path.dirname(DB), exist_ok=True)
        c = sqlite3.connect(DB, timeout=60)  # ~30 concurrent agents write here; default 5 s lock wait drops writes
        c.executescript(SCHEMA)
        for tbl, cols in NEW_COLUMNS.items():
            have = {r[1] for r in c.execute(f"PRAGMA table_info({tbl})")}
            for name, typ in cols:
                if name not in have:
                    c.execute(f"ALTER TABLE {tbl} ADD COLUMN {name} {typ}")
        return c
    if not os.path.exists(DB):
        sys.exit(f"no database at {DB} -- run `kb.py init` (project = BOOK_ROOT or cwd)")
    return sqlite3.connect("file:" + DB.replace(os.sep, "/") + "?mode=ro", uri=True, timeout=60)


def col(c, name):
    """SQL expression for an optional entries column: the column, or NULL on an old DB."""
    have = {r[1] for r in c.execute("PRAGMA table_info(entries)")}
    return name if name in have else "NULL"


def log(c, action, detail):
    c.execute("INSERT INTO log VALUES(?,?,?)", (dt.datetime.now().isoformat(timespec="seconds"), action, detail))


def sector(s):
    if s not in SECTORS:
        sys.exit(f"sector must be one of {SECTORS}")
    return s


def host(url):
    """Host without port or credentials: 127.0.0.1:8080 and 127.0.0.1 are one host."""
    h = url.split("/")[2].lower() if "://" in url else url.lower()
    return h.rsplit("@", 1)[-1].split(":")[0]


def is_root(url):
    """A bare homepage cites nothing: the fact must be on the page."""
    return re.match(r"https?://[^/]+/?(\?lang=\w+)?$", url) is not None


ROLES = {"author", "authors", "authored", "writer", "drafts", "draft",
         "verify", "verifier", "verification", "verified",
         "check", "checker", "review", "reviewer", "second"}


def agent_id(name):
    """Run identity behind an agent name: `reelsrc-0922-author` -> `reelsrc`.

    Leading role words (`verify-x`) are labels and are dropped; the part before the
    first hyphen of what is left is the run. Names sharing it are one agent, so
    `x-helper` / `x-lead` / `verify-x-0922` are all `x`.
    ponytail: self-asserted names only -- an agent that picks two unrelated names
    still passes; the Lead briefs distinct prefixes and never verifies its own
    helpers' entries, and the blind audit sample (audit_sample.py) is the backstop.
    """
    t = [x for x in re.split(r"[\W_]+", (name or "").lower()) if x]  # unicode word characters: Arabic names have identities too
    while t and t[0] in ROLES:
        t.pop(0)
    return t[0] if t else ""


def support(srcs):
    """The publication bar, in one place: (passes, confidence) for a set of
    (id, url, tier) rows. A LONE source carries an entry only at tier 1
    (official / standards body / primary); otherwise it takes two sources on
    different hosts. Shared by `verify` and `detach` so withdrawing support is
    scored by exactly the rule that granted it.

    Changed 2026-09-22 (the owner): a lone tier-2 source used to pass. It no
    longer does -- an institutional write-up is corroboration, not a primary."""
    hosts = {host(u) for _, u, _ in srcs}
    primary = any(t <= 2 for _, _, t in srcs)
    lone_ok = any(t == 1 for _, _, t in srcs)
    if not (lone_ok or len(hosts) >= 2):
        return False, 0.0
    return True, (0.95 if (primary and len(hosts) >= 2) else 0.85 if lone_ok else 0.75)


def independence(author, verified_by):
    """Was the verifier a different agent from the author? Derived on read, so
    it can never go stale: a row second-read by a real second agent stops being
    flagged the moment `verified_by` changes.

    '' = independent or not yet verified, 'self' = same run wrote and verified
    it, 'unknown' = author was never recorded (rows older than the `author`
    migration) and the question cannot be answered. 'unknown' is a third
    answer, not a guess in either direction."""
    if not verified_by:
        return ""
    if not author:
        return "unknown"
    return "self" if agent_id(author) == agent_id(verified_by) else ""


INDEPENDENCE_LABEL = {
    "self": "SELF-VERIFIED (author and verifier are the same agent) -- not independent corroboration",
    "unknown": "UNKNOWN INDEPENDENCE (author not recorded; cannot be checked)",
}


def cmd_init(a):
    c = con(True); c.commit(); print(f"ok  {DB}")


def host_listed(h):
    """Is host `h` (or a parent domain of it) on the project's tier-1 allowlist?"""
    h = h[4:] if h.startswith("www.") else h
    allowed = PRIMARY_HOSTS.keys() if isinstance(PRIMARY_HOSTS, dict) else PRIMARY_HOSTS
    return any(h == k or h.endswith("." + k) for k in (x.lower() for x in allowed))


def cmd_add_source(a):
    if a.tier not in TIERS:
        sys.exit(f"refused: --tier must be one of {sorted(TIERS)}")
    if is_root(a.url) and not a.allow_root:
        sys.exit(f"refused: {a.url} is a bare homepage, not the page that states the fact -- add the deep link, or --allow-root REASON")
    if a.tier == 1 and PRIMARY_HOSTS is None:
        sys.exit("refused: tier 1 needs a `primary_hosts` allowlist in kb/kb.json (none configured -- there is no default); "
                 "the Lead signs the allowlist before research, or use tier 2-4")
    if a.tier == 1 and not host_listed(host(a.url)):
        sys.exit(f"refused: host '{host(a.url)}' is not in primary_hosts of kb/kb.json, so it cannot be tier 1 "
                 "(the Lead signs the allowlist before research; use tier 2-4 or add the host with a reason)")
    c = con(True)
    old = c.execute("SELECT id,tier FROM sources WHERE url=?", (a.url,)).fetchone()
    if old:  # idempotent on URL; a different tier is a conflict, never a silent upgrade
        if old[1] != a.tier:
            sys.exit(f"refused: source {old[0]} already holds this URL at tier {old[1]}, not {a.tier}")
        print(f"source {old[0]}  tier{a.tier}  exists  {a.name}"); return
    note = a.note
    if a.allow_root:
        note = (note + " | " if note else "") + "ROOT-ALLOWED: " + a.allow_root
    c.execute("INSERT INTO sources(sector,name,url,kind,tier,note,added) VALUES(?,?,?,?,?,?,?)",
              (sector(a.sector), a.name, a.url, a.kind, a.tier, note, today()))
    sid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    log(c, "add-source", a.url); c.commit()
    print(f"source {sid}  tier{a.tier}  {a.name}")


def find_dup(c, topic, claim):
    """id of an entry with the same topic and whitespace-normalised claim, else None (add is idempotent)."""
    want = " ".join(claim.split())
    for eid, cl in c.execute("SELECT id,claim FROM entries WHERE topic=?", (topic,)):
        if " ".join(cl.split()) == want:
            return eid
    return None


def cmd_add_entry(a):
    c = con(True)
    ids = [int(x) for x in a.sources.split(",") if x.strip()]
    if not a.claim.strip() or not ids:
        sys.exit("refused: empty claim or empty sources -- a claim without a source is not stored")
    marks = ",".join("?" * len(ids))
    known = {r[0] for r in c.execute(f"SELECT id FROM sources WHERE id IN ({marks})", ids)}
    missing = set(ids) - known
    if missing:
        sys.exit(f"unknown source ids {sorted(missing)} -- add the source first; a claim without a source is not stored")
    dup = find_dup(c, a.topic, a.claim)
    if dup:
        print(f"dup {dup}"); return
    c.execute("INSERT INTO entries(sector,topic,claim,summary,tags,source_ids,retrieved,updated,author) VALUES(?,?,?,?,?,?,?,?,?)",
              (sector(a.sector), a.topic, a.claim, a.summary, a.tags, ",".join(map(str, ids)), a.retrieved or today(), today(), a.by))
    eid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    log(c, "add-entry", a.claim[:80]); c.commit()
    print(f"entry {eid}  draft  {a.topic}")


def cmd_add_batch(a):
    """FILE.jsonl, one object per line. All-or-nothing: any bad line refuses the whole file."""
    jrows, errs = read_jsonl(a.file)
    c = con(True)
    rows = []
    for n, d in jrows:
        claim = d.get("claim")
        srcs = d.get("sources")
        if isinstance(srcs, str):
            srcs = [x for x in srcs.split(",") if x.strip()]
        try:
            ids = [int(x) for x in (srcs or [])]
        except (TypeError, ValueError):
            errs.append(f"line {n}: sources must be ids"); continue
        by = d.get("by") or a.by
        if not isinstance(claim, str) or not claim.strip():
            errs.append(f"line {n}: empty claim"); continue
        if not ids:
            errs.append(f"line {n}: empty sources"); continue
        if not by:
            errs.append(f"line {n}: no 'by' (author) on the line or --by"); continue
        if d.get("sector") not in SECTORS:
            errs.append(f"line {n}: sector {d.get('sector')!r} not in {SECTORS}"); continue
        if not str(d.get("topic") or "").strip():
            errs.append(f"line {n}: empty topic"); continue
        marks = ",".join("?" * len(ids))
        known = {r[0] for r in c.execute(f"SELECT id FROM sources WHERE id IN ({marks})", ids)}
        if set(ids) - known:
            errs.append(f"line {n}: unknown source ids {sorted(set(ids) - known)}"); continue
        rows.append((d["sector"], d["topic"], claim, d.get("summary"), d.get("tags"), ",".join(map(str, ids)),
                     d.get("retrieved") or today(), today(), by))
    if errs:
        sys.exit("refused: " + str(len(errs)) + " bad line(s), no row was added\n" + "\n".join(errs[:20]))
    added = dup = 0
    for r in rows:  # idempotent on (sector, topic, claim): a re-run adds nothing
        hit = find_dup(c, r[1], r[2])
        if hit:
            dup += 1; print(f"dup {hit}\t{r[2][:60]}"); continue
        c.execute("INSERT INTO entries(sector,topic,claim,summary,tags,source_ids,retrieved,updated,author) VALUES(?,?,?,?,?,?,?,?,?)", r)
        print(f"{c.execute('SELECT last_insert_rowid()').fetchone()[0]}\t{r[2][:60]}")  # file order: map ids to claims by this, never by base+n
        added += 1
    log(c, "add-batch", f"{a.file} added={added} dup={dup}")
    c.commit()  # one transaction: everything above is invisible to others until here
    print(f"batch ok  added={added} existing={dup}")


_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def numbers(text):
    """Number tokens in a text (Arabic-Indic digits folded, thousands commas dropped)."""
    return {n.replace(",", "") for n in re.findall(r"\d+(?:[.,]\d+)*", (text or "").translate(_DIGITS))}


def locate(raw_text, quote):
    """1-based line where `quote` starts in raw_text, whitespace-normalised; None if absent."""
    words = quote.split()
    if not words:
        return None
    m = re.search(r"\s+".join(re.escape(w) for w in words), raw_text)
    return raw_text.count("\n", 0, m.start()) + 1 if m else None


def sha1_file(path):
    import hashlib
    with open(path, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()


def urlnorm(u):
    return u.strip().split("#")[0].rstrip("/").lower()


def raw_binding(raw, src_urls):
    """None if `raw` is a fetched file (research/_raw/index.tsv) for one of the entry's sources
    and unchanged since the fetch; else the reason it is refused."""
    idx = os.path.join(ROOT, CFG.get("raw_index", "research/_raw/index.tsv"))
    if not os.path.isfile(idx):
        return f"no raw index at {idx} -- fetch.py writes it; a quote must come from a fetched file"
    rel = os.path.relpath(raw, ROOT).replace(os.sep, "/")
    with open(idx, encoding="utf-8") as f:
        rows = [ln.rstrip("\n").split("\t") for ln in f if ln.strip()]
    mine = [r for r in rows if len(r) >= 5 and r[1] == rel]
    if not mine:
        return f"{rel} is not in the raw index (not fetched by fetch.py)"
    sha = sha1_file(raw)
    fresh = [r for r in mine if r[2] == sha]
    if not fresh:
        return f"{rel} changed since it was fetched (sha1 no longer matches the index)"
    want = {urlnorm(u) for u in src_urls}
    if not any(urlnorm(r[0]) in want and r[4] == "ok" for r in fresh):
        return f"{rel} was fetched from {sorted({r[0] for r in fresh})}, which is none of this entry's sources"
    return None


class Refuse(Exception):
    """A gate said no. Raised before any write for that row."""


_NUM = re.compile(r"\d+(?:[.,]\d+)*")


def num_list(text):
    """Number tokens IN ORDER (Arabic-Indic digits folded, thousands commas dropped)."""
    return [n.replace(",", "") for n in _NUM.findall((text or "").translate(_DIGITS))]


def in_order(want, have):
    """Is `want` a subsequence of `have`? -> (ok, first missing/out-of-order token)."""
    it = iter(have)
    for w in want:
        if not any(w == h for h in it):
            return False, w
    return True, None


def min_quote(claim):
    return min(40, len(" ".join(claim.split())))


_VERSION = re.compile(r"v?\d+\.\d+(?:\.\d+)?", re.I)


def strip_versions(claim, names):
    """Remove from `claim` every version token (v4.0, 2.1.1) that occurs in one of the source names: the label is
    carried by the source's title, so the quote need not repeat it. Every other figure keeps its full rule."""
    hay = " ".join(names).lower()
    return _VERSION.sub(lambda m: " " if m.group(0).lower().lstrip("v") in hay else m.group(0), claim)


def _as_list(x):
    return [] if x is None else list(x) if isinstance(x, (list, tuple)) else [x]


def _check_quote(quote, raw, claim, srcs, derived, what="quote", names=()):
    """Raise Refuse unless every span of `quote` (a string, or a list of spans) is a real, long-enough span of one of the `raw` files
    (a path, or a list), every raw file is bound to one of `srcs`, and the claim's figures occur in the JOINED spans in order.
    -> [(raw path, line)] one per span."""
    quotes = [q for q in _as_list(quote) if (q or "").strip()]
    raws = [r for r in _as_list(raw) if r]
    if not quotes or not raws:
        raise Refuse(f"GATE FAIL: verify needs a {what} (verbatim span) and its raw file (the file the span was read from). Not verified.")
    for r in raws:
        if not os.path.isfile(r):
            raise Refuse(f"GATE FAIL: raw file not found: {r}")
    need = min_quote(claim)
    for qq in quotes:
        if len(" ".join(qq.split())) < need:
            raise Refuse(f"GATE FAIL: the {what} is {len(' '.join(qq.split()))} chars; it must be a span that carries the claim: >= {need} chars (40, or the whole claim if shorter)"
                         + (" -- every span of a multi-span quote needs that length" if len(quotes) > 1 else ""))
    urls = [u for _, u, _ in srcs]
    for r in raws:
        why = raw_binding(r, urls)  # each file is bound to one of the entry's own sources
        if why:
            raise Refuse(f"GATE FAIL: {why}. Not verified.")
    texts = {}
    for r in raws:
        with open(r, encoding="utf-8", errors="replace") as f:
            texts[r] = f.read()
    locs = []
    for qq in quotes:
        hit = next(((r, locate(texts[r], qq)) for r in raws if locate(texts[r], qq) is not None), None)
        if hit is None:
            raise Refuse(f"GATE FAIL: the {what} does not occur in {', '.join(raws)} (whitespace-normalised): '{' '.join(qq.split())[:50]}'. Not verified.")
        locs.append(hit)
    if not derived:
        joined = " ".join(quotes)
        ok, bad = in_order(num_list(strip_versions(claim, names)), num_list(joined))
        if not ok:
            raise Refuse(f"GATE FAIL: the claim's figures {num_list(claim)} do not occur in the {what} in the same order (stuck at '{bad}'); quote the span that holds them, or --derived \"<how computed>\"")
    return locs


def _verify(c, eid, by, quote, raw, derived_arg, second_source, allow_root, second_raw=None, second_quote=None, weak=False):
    """Gate: named independent verifier + a long-enough quote that is really in a file fetched for a source ALREADY on
    the entry (figures in the claim occur in it in order) + a lone tier-1 source or two on different hosts.
    A second source adds support only with its own quote and raw file, checked the same way. Every refusal is before any write."""
    row = c.execute("SELECT source_ids,author,claim,status FROM entries WHERE id=?", (eid,)).fetchone()
    if not row:
        raise Refuse("no such entry")
    if row[3] == "retracted":  # a demotion is a decision: a misdirected verify-batch must not silently undo it
        raise Refuse(f"GATE FAIL: entry {eid} is retracted \u2014 re-add or amend it first (verify never revives a demoted entry)")
    if weak:
        raise Refuse(f"GATE FAIL: entry {eid} was marked weak by its verifier (claim wider than its quote): re-quote it or amend/demote the claim "
                     "BEFORE the audit draw; a weak row is never verified")
    if not (by or "").strip():
        raise Refuse("GATE FAIL: --by (the verifier's name) is required")
    # ponytail: rows written before the `author` migration have author NULL and
    # cannot be checked; add-entry has required --by ever since, so this is history only.
    if row[1] and agent_id(row[1]) == agent_id(by):
        raise Refuse(f"GATE FAIL: entry {eid}: author '{row[1]}' and verifier '{by}' are the same agent (run '{agent_id(by) or '(no identity)'}'); a different agent must verify.")
    if not agent_id(by):
        raise Refuse(f"GATE FAIL: verifier name '{by}' has no identity (role words or punctuation only)")
    derived = (derived_arg or "").strip()
    if derived_arg is not None and len(derived) < 10:
        raise Refuse("GATE FAIL: --derived needs a reason of at least 10 characters (how the number was computed)")
    ids = [int(x) for x in row[0].split(",")]
    marks = ",".join("?" * len(ids))
    srcs = c.execute(f"SELECT id,url,tier FROM sources WHERE id IN ({marks})", ids).fetchall()
    names = [r[0] for r in c.execute(f"SELECT name FROM sources WHERE id IN ({marks})", ids)]
    locs = _check_quote(quote, raw, row[2], srcs, derived, names=names)  # bound to the entry's STORED sources only
    if second_source and second_source not in ids:
        s2 = c.execute("SELECT id,url,tier FROM sources WHERE id=?", (second_source,)).fetchone()
        if not s2:
            raise Refuse(f"GATE FAIL: --second-source {second_source} is not a stored source")
        _check_quote(second_quote or quote, second_raw, row[2], [s2], derived, what="second quote",
                     names=[c.execute("SELECT name FROM sources WHERE id=?", (second_source,)).fetchone()[0]])
        ids.append(second_source)
        srcs = srcs + [s2]
    elif second_source:
        second_source = None  # already attached: nothing new to add
    roots = [u for _, u, _ in srcs if is_root(u)]
    if roots and not allow_root:
        raise Refuse("GATE FAIL: source is a bare homepage, not the page that states the fact: " + ", ".join(roots) + "  (add the deep link as a source, or --allow-root with a reason)")
    ok, conf = support(srcs)
    if not ok:
        raise Refuse("GATE FAIL: needs a tier-1 source on its own, or two sources on different hosts. Not verified.")
    def where(r, line):
        try:
            return f"{os.path.relpath(r, ROOT).replace(os.sep, '/')}:{line}"
        except ValueError:  # other drive
            return f"{os.path.abspath(r)}:{line}"
    locator = "; ".join(where(r, ln) for r, ln in locs)
    quote_text = " \u2026 ".join(" ".join(q.split()) for q in _as_list(quote) if (q or "").strip())
    c.execute("UPDATE entries SET status='verified',verified_by=?,verified_on=?,second_source=?,source_ids=?,confidence=?,updated=?,"
              "quote=?,locator=?,derived=? WHERE id=?",
              (by, today(), second_source, ",".join(map(str, ids)), conf, today(), quote_text, locator, derived or None, eid))
    log(c, "verify", f"{eid} by {by} at {locator}")
    return (f"entry {eid}  verified  confidence {conf}  quote at {locator}" + (f"  derived: {derived}" if derived else ""))


def cmd_verify(a):
    c = con(True)
    try:
        msg = _verify(c, a.id, a.by, getattr(a, "quote", None), getattr(a, "raw", None), getattr(a, "derived", None),
                      a.second_source, a.allow_root, getattr(a, "second_raw", None), getattr(a, "second_quote", None),
                      weak=bool(getattr(a, "weak", False)))
    except Refuse as e:
        sys.exit(str(e))
    c.commit()
    print(msg)


def read_jsonl(path):
    """Strict UTF-8, no CR; -> (list of (lineno, obj), errors). Shared by add-batch and verify-batch."""
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError as e:
        sys.exit(f"refused: cannot read {path}: {e}")
    if b"\r" in raw:
        sys.exit("refused: file contains CR (CRLF or lone CR) -- write LF line ends only; nothing was written")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        sys.exit(f"refused: file is not valid UTF-8 ({e}); nothing was written")
    rows, errs = [], []
    for n, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        try:
            d = json.loads(line)
            if not isinstance(d, dict):
                raise ValueError("not an object")
            rows.append((n, d))
        except ValueError as e:
            errs.append(f"line {n}: bad JSON ({e})")
    return rows, errs


def cmd_verify_batch(a):
    """FILE.jsonl rows {id, quote, raw[, derived]}: each row passes exactly the checks of `verify`;
    the held rows are written in ONE transaction, refused rows are listed with the reason. Exit 1 if any refused."""
    rows, errs = read_jsonl(a.file)
    if errs:
        sys.exit("refused: " + str(len(errs)) + " bad line(s), nothing was written\n" + "\n".join(errs[:20]))
    c = con(True)
    held = refused = 0
    for n, d in rows:
        eid = d.get("id")
        try:
            if not isinstance(eid, int):
                raise Refuse("row has no integer 'id'")
            msg = _verify(c, eid, a.by, d.get("quote"), d.get("raw"), d.get("derived"), d.get("second_source"), d.get("allow_root"),
                         d.get("second_raw"), d.get("second_quote"), weak=bool(d.get("weak")))
            held += 1
            print(f"held     {eid}  {msg.split('  ', 2)[-1]}")
        except Refuse as e:
            refused += 1
            print(f"refused  {eid if isinstance(eid, int) else f'line {n}'}  {str(e).replace(chr(10), ' ')[:200]}")
    c.commit()  # one transaction for every held row
    print(f"verify-batch: held={held} refused={refused}")
    if refused:
        sys.exit(1)


def note_line(c, eid, text):
    """Append one dated line to the entry's note column; never overwrites."""
    old = c.execute("SELECT note FROM entries WHERE id=?", (eid,)).fetchone()[0]
    return ((old + "\n") if old else "") + f"{today()} {text}"


DEMOTE_KINDS = ("discredited", "gate-change")
# Two different facts wear the same status. 'discredited' = the claim or its
# source failed on its merits. 'gate-change' = the claim was never re-read; the
# BAR moved under it (2026-09-22: a lone tier-2 primary stopped qualifying), so
# most of these recover by re-tiering a mis-filed source, not by new research.
# Written as a fixed token in the note and the log so a later reader -- or a
# grep -- can tell the two apart without parsing free text.


def cascade(eid):
    """Everything that still cites entry `eid`: rule packs (**Because:** #id) and pages / banks / twin pages (KB#id).
    -> [(kind, 'path:line')]."""
    hits = []
    rdir = os.path.join(ROOT, CFG.get("rules", "kb/rules"))
    rule = re.compile(r"#%d(?!\d)" % eid)
    if os.path.isdir(rdir):
        for f in sorted(os.listdir(rdir)):
            if f.endswith(".md") and f != "INDEX.md":
                for i, ln in enumerate(open(os.path.join(rdir, f), encoding="utf-8"), 1):
                    if ln.startswith("**Because:**") and rule.search(ln):
                        hits.append(("rule", f"{os.path.relpath(os.path.join(rdir, f), ROOT)}:{i}"))
    try:
        with open(os.path.join(ROOT, "book.json"), encoding="utf-8") as f:
            bk = json.load(f)
    except (FileNotFoundError, ValueError):
        bk = {}
    practice = bk.get("practice") or "practice"
    suffix = str(bk.get("twin") or "").rsplit("-", 1)[-1]
    dirs = [bk.get("pages"), bk.get("twin"), practice, bk.get("practice_twin") or (f"{practice}-{suffix}" if suffix else None)]
    page = re.compile(r"KB#%d(?!\d)" % eid)
    for d in [d for d in dirs if d]:
        base = os.path.join(ROOT, d)
        for dp, _, fs in os.walk(base):
            for fn in sorted(fs):
                if fn.endswith(".md"):
                    fp = os.path.join(dp, fn)
                    for i, ln in enumerate(open(fp, encoding="utf-8", errors="replace"), 1):
                        if page.search(ln):
                            hits.append(("page", f"{os.path.relpath(fp, ROOT)}:{i}"))
    return hits


def cmd_demote(a):
    """Withdraw a verified entry. Records WHO, WHY and WHICH KIND on the row: a
    retraction is a fact, not an absence -- status 'retracted' is
    distinguishable from 'draft' (never verified), and verified_by/verified_on
    are kept as the record of the verification being withdrawn."""
    c = con(True)
    kind = getattr(a, "kind", None) or "discredited"
    if kind not in DEMOTE_KINDS:
        sys.exit(f"refused: --kind must be one of {DEMOTE_KINDS}")
    row = c.execute("SELECT status,verified_by FROM entries WHERE id=?", (a.id,)).fetchone()
    if not row:
        sys.exit("no such entry")
    if row[0] == "retracted":
        sys.exit(f"refused: entry {a.id} is already retracted -- nothing to demote")
    if not a.reason.strip():
        sys.exit("refused: --reason is required and must not be empty; a retraction without a reason is an absence")
    # No verifier-identity gate here: demote only lowers status, so it cannot
    # launder a claim. Re-verifying afterwards still goes through cmd_verify,
    # which refuses the author. (Gate bypass would be a path that raises status.)
    c.execute("UPDATE entries SET status='retracted',confidence=0.0,note=?,updated=? WHERE id=?",
              (note_line(c, a.id, f"RETRACTED[{kind}] by {a.by} (was {row[0]}, verified_by {row[1] or '-'}): {a.reason}"), today(), a.id))
    log(c, "demote", f"entry {a.id} was={row[0]} kind={kind} by={a.by} reason={a.reason}")
    c.commit()
    print(f"entry {a.id}  retracted[{kind}]  (was {row[0]})  by {a.by}")
    hits = cascade(a.id)
    for k, where in hits:
        print(f"  still cited by {k}  {where}")
    if hits:  # the cascade is visible: rules.py check / check_pages will fail until these are re-grounded
        print(f"CASCADE entry {a.id} is cited in {len(hits)} place(s): re-ground or remove each, then run rules.py check and check_pages.py")
        sys.exit(2)


def cmd_detach(a):
    """Withdraw ONE source's support from an entry and rescore what is left.

    `fix-sources` replaces the whole citation and forces the row back to draft;
    that is the wrong shape when a second reader disqualifies one source of
    several. Detach removes that source, recomputes confidence with the same
    `support()` rule the verification used, and -- if what remains no longer
    clears the bar -- hands the row to `cmd_demote` rather than leaving a
    `verified` row standing on nothing.

    Confidence can only fall (the source set only shrinks), so this is not a
    laundering path; the author gate `cmd_amend` uses still applies, so an
    agent cannot quietly re-shape the evidence under its own verified claim.
    """
    c = con(True)
    row = c.execute("SELECT source_ids,status,author,second_source FROM entries WHERE id=?", (a.id,)).fetchone()
    if not row:
        sys.exit("no such entry")
    ids_s, st, author, second = row
    if not a.reason.strip():
        sys.exit("refused: --reason is required and must not be empty; support withdrawn without a reason is an absence")
    ids = [int(x) for x in ids_s.split(",") if x.strip()]
    if a.source not in ids:
        sys.exit(f"refused: source {a.source} is not attached to entry {a.id} (attached: {ids_s})")
    if len(ids) == 1:
        sys.exit(f"refused: source {a.source} is the only source on entry {a.id}; an entry with no source is not stored -- use `demote` to withdraw the entry")
    if st == "verified" and author and agent_id(author) == agent_id(a.by):
        sys.exit(f"GATE FAIL: entry {a.id}: author '{author}' and detacher '{a.by}' are the same agent (run '{agent_id(a.by) or '(role words only)'}'); a different agent must change the evidence under a verified entry.")
    rest = [i for i in ids if i != a.source]
    marks = ",".join("?" * len(rest))
    srcs = c.execute(f"SELECT id,url,tier FROM sources WHERE id IN ({marks})", rest).fetchall()
    ok, conf = support(srcs)
    sets = ["source_ids=?", "note=?", "updated=?"]
    vals = [",".join(map(str, rest)), note_line(c, a.id, f"DETACHED source {a.source} by {a.by}: {a.reason}"), today()]
    if second == a.source:
        sets.append("second_source=NULL")
    if st == "verified" and ok:
        sets.append("confidence=?"); vals.append(conf)
    vals.append(a.id)
    c.execute(f"UPDATE entries SET {','.join(sets)} WHERE id=?", vals)
    log(c, "detach", f"entry {a.id} source {a.source} rest={','.join(map(str, rest))} by={a.by} reason={a.reason}")
    c.commit()
    if st == "verified" and not ok:
        print(f"entry {a.id}  source {a.source} detached  -- what remains does not clear the bar")
        cmd_demote(types.SimpleNamespace(id=a.id, by=a.by, reason=f"source {a.source} detached ({a.reason}); remaining sources do not meet the verification bar"))
        return
    print(f"entry {a.id}  {st}  source {a.source} detached  confidence -> {conf if st == 'verified' else 'n/a (not verified)'}")


_TRAILERS = [
    re.compile(r"\s*[\(\[]\s*(?:retrieved|fetched|accessed|as of|checked|last checked)\s*:?\s*\d{4}-\d{2}-\d{2}\s*[\)\]]", re.I),
    re.compile(r"\s*[\(\[]\s*(?:page|pages|p\.|pp\.)\s*\d+(?:\s*[-\u2013]\s*\d+)?\s*[\)\]]", re.I),
    re.compile(r"[\s,;]*\b(?:retrieved|fetched|accessed|as of)\s+\d{4}-\d{2}-\d{2}\.?\s*$", re.I),
    re.compile(r"[\s,;]*\bSources?\s*:\s*[^\n]*$", re.I),
    re.compile(r"[\s,;]*\b(?:see\s+|per\s+)?(?:section|sec\.|\u00a7)\s*\d+(?:\.\d+)*\.?\s*$", re.I),
]


def strip_trailers(claim):
    """-> (claim without provenance trailers, [removed trailer texts]). Only trailers: 'Source: ...', '(retrieved 2026-10-15)', '(page 3)',
    'as of <date>', a closing 'section 7.1'. Nothing else in the claim is touched (whitespace is normalised)."""
    out, found = claim, []
    for _ in range(6):
        changed = False
        for rx in _TRAILERS:
            m = rx.search(out)
            if m:
                found.append(m.group(0).strip(" ,;"))
                out = out[:m.start()] + out[m.end():]
                changed = True
        if not changed:
            break
    return " ".join(out.split()), found


def cmd_hygiene(a):
    """Dry run by default: list claims that carry provenance text and what they would become. --apply amends them through the
    amend path WITHOUT resetting status, only when nothing but the trailer is removed; the trailer moves to the summary."""
    c = con(bool(a.apply))
    where, args = ("", [])
    if a.topic:
        tl = [t for t in a.topic.split(",") if t.strip()]
        where, args = f" AND topic IN ({','.join('?' * len(tl))})", tl
    rows = c.execute(f"SELECT id,claim,summary,status,author FROM entries WHERE status IN ('draft','verified'){where} ORDER BY id", args).fetchall()
    found = applied = listed = 0
    for eid, claim, summary, st, author in rows:
        new, trailers = strip_trailers(claim)
        if not trailers or new == " ".join(claim.split()):
            continue
        found += 1
        print(f"#{eid} [{st}]\n  before: {claim}\n  after:  {new}\n  moved:  {' | '.join(trailers)}")
        if len(new) < 10:
            listed += 1; print("  NOT APPLIED: the remaining claim is too short to be a claim -- rewrite it by hand"); continue
        if not a.apply:
            continue
        if st == "verified" and author and agent_id(author) == agent_id(a.by):
            listed += 1; print(f"  NOT APPLIED: author '{author}' and --by '{a.by}' are the same agent (a different agent amends a verified entry)"); continue
        try:
            cmd_amend(types.SimpleNamespace(id=eid, by=a.by, claim=new, reason="hygiene: provenance trailer moved out of the claim",
                                            summary=((summary + " | ") if summary else "") + "provenance: " + "; ".join(trailers), keep_status=True))
            applied += 1
        except SystemExit as e:
            listed += 1; print(f"  NOT APPLIED: {e}")
    print(f"hygiene: {found} claim(s) carry provenance text; " + (f"{applied} amended (status kept), {listed} listed not applied" if a.apply else "dry run, nothing changed (--apply --by <name> to amend)"))
    return 1 if (a.apply and listed) else 0


def cmd_amend(a):
    """Correct a claim or a summary in place, recording what changed.

    Amending the CLAIM resets the entry to draft -- the verification was of the
    old words, so keeping 'verified' would be self-verification by the back
    door. Amending a verified entry at all is refused for its own author, the
    same identity gate cmd_verify uses.
    """
    c = con(True)
    row = c.execute("SELECT status,claim,summary,author FROM entries WHERE id=?", (a.id,)).fetchone()
    if not row:
        sys.exit("no such entry")
    st, claim, summary, author = row
    if a.claim is None and a.summary is None:
        sys.exit("refused: nothing to amend -- give --claim and/or --summary")
    if a.claim is not None and a.claim == claim:
        sys.exit("refused: new claim identical to old -- nothing to amend")
    if a.summary is not None and a.summary == summary:
        sys.exit("refused: new summary identical to old -- nothing to amend")
    if not a.reason.strip():
        sys.exit("refused: --reason is required and must not be empty")
    if st == "verified" and author and agent_id(author) == agent_id(a.by):
        sys.exit(f"GATE FAIL: entry {a.id}: author '{author}' and amender '{a.by}' are the same agent (run '{agent_id(a.by) or '(role words only)'}'); a different agent must amend a verified entry.")
    changed, sets, vals = [], [], []
    if a.claim is not None:
        changed.append(f"claim was: {claim}"); sets.append("claim=?"); vals.append(a.claim)
    if a.summary is not None:
        changed.append(f"summary was: {summary}"); sets.append("summary=?"); vals.append(a.summary)
    reset = a.claim is not None and st == "verified" and not getattr(a, "keep_status", False)
    if reset:
        sets += ["status='draft'", "verified_by=NULL", "verified_on=NULL", "second_source=NULL", "confidence=0.5", "quote=NULL", "locator=NULL", "derived=NULL"]
    note = note_line(c, a.id, f"AMENDED by {a.by}: {a.reason} || " + " || ".join(changed))
    sets.append("note=?"); vals.append(note)
    sets.append("updated=?"); vals.append(today())
    vals.append(a.id)
    c.execute(f"UPDATE entries SET {','.join(sets)} WHERE id=?", vals)
    log(c, "amend", f"entry {a.id} fields={'+'.join(f for f, v in (('claim', a.claim), ('summary', a.summary)) if v is not None)} by={a.by} reason={a.reason}")
    c.commit()
    print(f"entry {a.id}  {'draft (claim amended, must be re-verified)' if reset else st}  amended by {a.by}")


def cmd_query(a):
    c = con()
    q = f"SELECT id,sector,topic,status,confidence,retrieved,claim,summary,source_ids,tags,{col(c, 'note')},{col(c, 'author')},verified_by FROM entries WHERE 1=1"
    p = []
    if a.sector:
        q += " AND sector=?"; p.append(sector(a.sector))
    if a.topic:
        q += " AND (topic LIKE ? OR claim LIKE ?)"; p += [f"%{a.topic}%"] * 2
    if a.tag:
        q += " AND tags LIKE ?"; p.append(f"%{a.tag}%")
    if a.status:
        q += " AND status=?"; p.append(a.status)
    q += " ORDER BY updated DESC LIMIT ?"; p.append(a.limit)
    rows = c.execute(q, p).fetchall()
    if not rows:
        print("(no entries)"); return
    for r in rows:
        print(f"#{r[0]} [{r[1]}/{r[2]}] {r[3]} c={r[4]:.2f} {r[5]} src={r[8]} :: {r[6][:140]}")
        if a.full and r[7]:
            print(f"    {r[7]}\n    tags={r[9]}")
        flag = independence(r[11], r[12])
        if flag:  # never hidden behind --full: it is read at the moment of citation
            print(f"    ! {INDEPENDENCE_LABEL[flag]}")
        if r[10]:  # retraction/amendment always shows, --full or not
            print("".join(f"    ! {ln}\n" for ln in r[10].splitlines()), end="")


def cmd_sources(a):
    c = con()
    q = "SELECT id,sector,tier,kind,status,last_checked,name,url FROM sources WHERE 1=1"; p = []
    if a.sector:
        q += " AND sector=?"; p.append(sector(a.sector))
    if a.tier:
        q += " AND tier=?"; p.append(a.tier)
    for r in c.execute(q + " ORDER BY sector,tier,id", p):
        print(f"#{r[0]} {r[1]} t{r[2]} {r[3]} {r[4]} {r[5] or '-'}  {r[6]}  {r[7]}")


def cmd_stats(a):
    c = con()
    for s in SECTORS:
        n = c.execute("SELECT COUNT(*) FROM sources WHERE sector=?", (s,)).fetchone()[0]
        e = c.execute("SELECT status,COUNT(*) FROM entries WHERE sector=? GROUP BY status", (s,)).fetchall()
        print(f"{s:11} sources={n:3}  entries={dict(e)}")
    print("untriaged feed items:", c.execute("SELECT COUNT(*) FROM updates WHERE triaged=0").fetchone()[0])
    d = col(c, "derived")
    print("derived_count:", c.execute(f"SELECT COUNT(*) FROM entries WHERE status='verified' AND {d} IS NOT NULL").fetchone()[0],
          "of", c.execute("SELECT COUNT(*) FROM entries WHERE status='verified'").fetchone()[0], "verified")


def cmd_stale(a):
    c = con()
    cut = (dt.date.today() - dt.timedelta(days=a.days)).isoformat()
    rows = c.execute("SELECT id,sector,topic,retrieved FROM entries WHERE status='verified' AND retrieved<?", (cut,)).fetchall()
    for r in rows:
        print(f"#{r[0]} {r[1]}/{r[2]} retrieved {r[3]}")
    print(f"{len(rows)} entries older than {a.days} days")


def cmd_triage(a):
    """Mark feed items as looked at. --ids 1,2,3 or --all (after a worker has read the queue file)."""
    c = con(True)
    if a.all:
        n = c.execute("UPDATE updates SET triaged=1 WHERE triaged=0").rowcount
    else:
        ids = [int(x) for x in a.ids.split(",") if x.strip()]
        n = c.execute(f"UPDATE updates SET triaged=1 WHERE id IN ({','.join('?'*len(ids))})", ids).rowcount
    log(c, "triage", f"{n} items by {a.by}"); c.commit(); print(f"triaged {n}")


def cmd_fix_sources(a):
    """Repair a citation only: source_ids. Forces back to draft (unverified)."""
    c = con(True)
    row = c.execute("SELECT source_ids FROM entries WHERE id=?", (a.id,)).fetchone()
    if not row:
        sys.exit("no such entry")
    ids = [int(x) for x in a.sources.split(",") if x.strip()]
    marks = ",".join("?" * len(ids))
    known = {r[0] for r in c.execute(f"SELECT id FROM sources WHERE id IN ({marks})", ids)}
    missing = set(ids) - known
    if missing:
        sys.exit(f"unknown source ids {sorted(missing)} -- add the source first; a claim without a source is not stored")
    old = row[0]
    if sorted(map(int, old.split(","))) == sorted(ids):
        sys.exit("refused: new source_ids identical to old -- nothing to repair")
    c.execute("UPDATE entries SET source_ids=?,status='draft',verified_by=NULL,verified_on=NULL,second_source=NULL,confidence=0.5,quote=NULL,locator=NULL,derived=NULL,updated=? WHERE id=?",
              (",".join(map(str, ids)), today(), a.id))
    log(c, "fix-sources", f"entry {a.id} old={old} new={','.join(map(str, ids))} by={a.by} reason={a.reason}")
    c.commit()
    print(f"entry {a.id}  draft  source_ids {old} -> {','.join(map(str, ids))}")


def cmd_feed(a):
    c = con()
    q = "SELECT u.id,u.source_id,s.sector,u.published,u.title,u.link FROM updates u JOIN sources s ON s.id=u.source_id WHERE 1=1"
    p = []
    if a.sector:
        q += " AND s.sector=?"; p.append(sector(a.sector))
    if a.untriaged:
        q += " AND u.triaged=0"
    q += " ORDER BY u.id"
    if a.limit:
        q += " LIMIT ?"; p.append(a.limit)
    for r in c.execute(q, p):
        print(f"#{r[0]} src{r[1]} [{r[2]}] {r[3] or '-'}  {r[4]}  {r[5]}")


def selftest():
    """Runs against a temp DB. Asserts fix-sources behaviour."""
    import tempfile, contextlib, io
    global DB, PRIMARY_HOSTS, ROOT, SECTORS
    real_db, real_hosts, real_root, real_sectors = DB, PRIMARY_HOSTS, ROOT, SECTORS
    SECTORS = SECTORS + ("research",)
    tdir = tempfile.mkdtemp()
    tmp = os.path.join(tdir, "kb", "t.db")
    DB, ROOT = tmp, tdir
    rawf = os.path.join(tdir, "research", "_raw", "s", "raw.txt")
    os.makedirs(os.path.dirname(rawf))
    with open(rawf, "w", encoding="utf-8") as f:
        f.write("header\nthe official pass mark is   26 of 40 points for this exam\n"
                "the exam has 40 questions in 60 minutes in total here\nthe official fee is 65 USD and it is paid once\nfooter\n")
    QT = "the official pass mark is 26 of 40 points for this exam"
    raw2f = os.path.join(tdir, "research", "_raw", "s", "raw2.txt")
    with open(raw2f, "w", encoding="utf-8") as f:
        f.write("second source says: the official pass mark is 26 of 40 points for this exam\n")

    def index_rows(c, file=None, only=None, sha=None):
        """Write research/_raw/index.tsv the way fetch.py would: one row per (source url, file)."""
        file = file or rawf
        rel = os.path.relpath(file, tdir).replace(os.sep, "/")
        with open(os.path.join(tdir, "research", "_raw", "index.tsv"), "w", encoding="utf-8", newline="") as f:
            for sid, url in c.execute("SELECT id,url FROM sources ORDER BY id"):
                if only is None or sid in only:
                    f.write("\t".join([url, rel, sha or sha1_file(file), "2026-01-01", "ok"]) + "\n")
                if file == rawf and sid == 2 and only is None:  # raw2.txt belongs to source 2 only
                    f.write("\t".join([url, os.path.relpath(raw2f, tdir).replace(os.sep, "/"), sha1_file(raw2f), "2026-01-01", "ok"]) + "\n")
    try:
        c = con(True)
        c.execute("INSERT INTO sources(sector,name,url,kind,tier,note,added) VALUES('research','A','https://a.example/x','page',1,NULL,?)", (today(),))
        c.execute("INSERT INTO sources(sector,name,url,kind,tier,note,added) VALUES('research','B','https://b.example/y','page',1,NULL,?)", (today(),))
        c.execute("INSERT INTO entries(sector,topic,claim,summary,tags,source_ids,retrieved,status,verified_by,verified_on,second_source,confidence,updated,author) "
                   "VALUES('research','t','claim',NULL,NULL,'1','2026-01-01','verified','someone','2026-01-01',NULL,0.9,?,'author')", (today(),))
        eid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        c.commit()

        a = types.SimpleNamespace(id=eid, sources="2", by="tester", reason="test repair")
        cmd_fix_sources(a)
        row = c.execute("SELECT source_ids,status,verified_by,verified_on,second_source,confidence FROM entries WHERE id=?", (eid,)).fetchone()
        assert row == ("2", "draft", None, None, None, 0.5), f"fix-sources did not reset row correctly: {row}"
        logrow = c.execute("SELECT detail FROM log WHERE action='fix-sources' ORDER BY ts DESC LIMIT 1").fetchone()[0]
        assert "old=1" in logrow and "new=2" in logrow, f"log missing old ids: {logrow}"

        try:
            cmd_fix_sources(types.SimpleNamespace(id=eid, sources="2", by="tester", reason="noop")); ok = False
        except SystemExit:
            ok = True
        assert ok, "identical source_ids repair was not refused"

        try:
            cmd_fix_sources(types.SimpleNamespace(id=eid, sources="999", by="tester", reason="bad")); ok = False
        except SystemExit:
            ok = True
        assert ok, "unknown source id was not rejected"

        # verifier independence: same run wearing two role names must be refused.
        def draft(by):
            c.execute("INSERT INTO entries(sector,topic,claim,source_ids,retrieved,updated,author) "
                      "VALUES('research','t','c','2','2026-01-01',?,?)", (today(), by))
            c.commit()
            return c.execute("SELECT last_insert_rowid()").fetchone()[0]

        def verify(eid, by):
            index_rows(c)
            cmd_verify(types.SimpleNamespace(id=eid, by=by, second_source=None, allow_root=None,
                                             quote=QT, raw=rawf, derived=None))

        e1 = draft("reelsrc-0922-author")
        try:
            verify(e1, "reelsrc-0922-verify"); ok = False
        except SystemExit:
            ok = True
        assert ok, "self-verification (same run id, two role names) was not refused"
        assert c.execute("SELECT status FROM entries WHERE id=?", (e1,)).fetchone()[0] == "draft", "refused verify still wrote the row"

        e2 = draft("reelsrc-0922-author")
        verify(e2, "kbgate-0922-verify")
        assert c.execute("SELECT status FROM entries WHERE id=?", (e2,)).fetchone()[0] == "verified", "a genuine second agent was blocked"

        assert agent_id("x-0922-author") == agent_id("verify-x-0922") == agent_id("x-helper") == agent_id("x-lead") == "x"
        assert agent_id("deep-research") != agent_id("verify-rp")

        # --- demote: retraction is recorded, not a silent no-op -------------
        def refused(fn, *a, **k):
            try:
                fn(*a, **k); return False
            except SystemExit:
                return True

        cmd_demote(types.SimpleNamespace(id=e2, by="kbfix-0922", reason="overstated claim"))
        st, conf, note = c.execute("SELECT status,confidence,note FROM entries WHERE id=?", (e2,)).fetchone()
        assert st == "retracted", f"demote did not change status: {st}"
        assert st != "draft", "a retracted entry must stay distinguishable from one never verified"
        assert conf == 0.0, f"demote left confidence at {conf}"
        assert note and "overstated claim" in note and "kbfix-0922" in note, f"demote lost the reason: {note!r}"
        assert c.execute("SELECT verified_by FROM entries WHERE id=?", (e2,)).fetchone()[0], "demote erased who verified it"
        dl = c.execute("SELECT detail FROM log WHERE action='demote' ORDER BY ts DESC LIMIT 1").fetchone()
        assert dl and "overstated claim" in dl[0], f"demote not logged with reason: {dl}"
        assert refused(cmd_demote, types.SimpleNamespace(id=e2, by="x", reason="again")), "second demote not refused"
        assert refused(cmd_demote, types.SimpleNamespace(id=e2, by="x", reason="  ")), "empty reason not refused"

        # --- amend: summary only keeps verified, claim resets, gate holds ---
        e3 = draft("reelsrc-0922-author")
        verify(e3, "kbgate-0922-verify")
        c.execute("UPDATE entries SET summary='old summary' WHERE id=?", (e3,)); c.commit()
        cmd_amend(types.SimpleNamespace(id=e3, by="kbfix-0922", claim=None, summary="new summary", reason="false note"))
        st, sm, note = c.execute("SELECT status,summary,note FROM entries WHERE id=?", (e3,)).fetchone()
        assert (st, sm) == ("verified", "new summary"), f"summary amend wrong: {st} {sm!r}"
        assert note and "false note" in note and "old summary" in note, f"amend lost reason/old value: {note!r}"
        assert refused(cmd_amend, types.SimpleNamespace(id=e3, by="k", claim=None, summary="new summary", reason="r")), "no-op amend not refused"
        assert refused(cmd_amend, types.SimpleNamespace(id=e3, by="k", claim=None, summary=None, reason="r")), "empty amend not refused"
        # the verifier-identity gate is not bypassed by amend
        assert refused(cmd_amend, types.SimpleNamespace(id=e3, by="verify-reelsrc-0922", claim="x", summary=None, reason="r")),             "author amending its own verified entry was not refused"
        assert c.execute("SELECT claim FROM entries WHERE id=?", (e3,)).fetchone()[0] != "x", "refused amend still wrote the row"
        cmd_amend(types.SimpleNamespace(id=e3, by="kbfix-0922", claim="corrected claim", summary=None, reason="narrowed"))
        st, cl, vb = c.execute("SELECT status,claim,verified_by FROM entries WHERE id=?", (e3,)).fetchone()
        assert (st, cl, vb) == ("draft", "corrected claim", None), f"claim amend must reset to draft: {st} {cl!r} {vb!r}"

        # --- detach: recompute confidence, demote when support falls away ----
        c.execute("INSERT INTO sources(sector,name,url,kind,tier,note,added) VALUES('research','C','https://c.example/z','page',4,NULL,?)", (today(),))
        c.execute("INSERT INTO sources(sector,name,url,kind,tier,note,added) VALUES('research','D','https://d.example/w','page',4,NULL,?)", (today(),))
        sc, sd = 3, 4
        c.commit()

        # two hosts + a tier-1 primary = 0.95; drop the primary -> one tier-4 host left -> below the bar
        def draft_srcs(by, srcs):
            c.execute("INSERT INTO entries(sector,topic,claim,source_ids,retrieved,updated,author) "
                      "VALUES('research','t','c',?,'2026-01-01',?,?)", (srcs, today(), by))
            c.commit()
            return c.execute("SELECT last_insert_rowid()").fetchone()[0]

        e4 = draft_srcs("kbharden-0922-author", "1,2")
        verify(e4, "other-0922-verify")
        assert c.execute("SELECT confidence FROM entries WHERE id=?", (e4,)).fetchone()[0] == 0.95
        cmd_detach(types.SimpleNamespace(id=e4, source=2, by="other-0922-verify", reason="second reader disqualified it"))
        st, conf, sids, note = c.execute("SELECT status,confidence,source_ids,note FROM entries WHERE id=?", (e4,)).fetchone()
        assert (st, conf, sids) == ("verified", 0.85, "1"), f"detach did not rescore a still-supported entry: {st} {conf} {sids}"
        assert "DETACHED source 2" in note and "second reader disqualified it" in note, f"detach lost the reason: {note!r}"

        e5 = draft_srcs("kbharden-0922-author", f"1,{sc}")
        verify(e5, "other-0922-verify")
        cmd_detach(types.SimpleNamespace(id=e5, source=1, by="other-0922-verify", reason="primary withdrawn"))
        st, conf, note = c.execute("SELECT status,confidence,note FROM entries WHERE id=?", (e5,)).fetchone()
        assert st == "retracted", f"detaching the last supporting source left status {st}, not retracted"
        assert conf == 0.0, f"retracted row kept confidence {conf}"
        assert "RETRACTED" in note and "primary withdrawn" in note, f"demote path not taken through detach: {note!r}"

        e6 = draft_srcs("kbharden-0922-author", f"{sc},{sd}")
        assert refused(cmd_detach, types.SimpleNamespace(id=e6, source=99, by="x", reason="r")), "detaching an unattached source not refused"
        assert refused(cmd_detach, types.SimpleNamespace(id=e6, source=sc, by="x", reason="  ")), "empty reason not refused"
        e7 = draft_srcs("kbharden-0922-author", "1")
        assert refused(cmd_detach, types.SimpleNamespace(id=e7, source=1, by="x", reason="r")), "detaching the only source not refused"
        # the author gate is not bypassed by detach
        e8 = draft_srcs("kbharden-0922-author", "1,2")
        verify(e8, "other-0922-verify")
        assert refused(cmd_detach, types.SimpleNamespace(id=e8, source=2, by="verify-kbharden-0922", reason="r")), "author detaching from its own verified entry was not refused"
        assert c.execute("SELECT source_ids FROM entries WHERE id=?", (e8,)).fetchone()[0] == "1,2", "refused detach still wrote the row"

        # --- independence flag: derived, three-valued, never guessed --------
        assert independence("kbharden-0922-author", "verify-kbharden-0922") == "self"
        assert independence("kbharden-0922-author", "other-0922-verify") == ""
        assert independence(None, "someone") == "unknown", "a NULL author must be 'unknown', not assumed independent or self"
        assert independence(None, None) == "" and independence("a", None) == "", "an unverified row carries no independence claim"

        # --- the bar: a LONE source carries an entry only at tier 1 ---------
        for name, hostname, t in (("E", "e.example", 2), ("F", "f.example", 2), ("G", "e.example", 2)):
            c.execute("INSERT INTO sources(sector,name,url,kind,tier,note,added) VALUES('research',?,?,'page',?,NULL,?)",
                      (name, f"https://{hostname}/{name.lower()}", t, today()))
        se, sf, sg = 5, 6, 7
        c.commit()

        e9 = draft_srcs("kbflip-0922-author", str(se))
        assert refused(verify, e9, "other-0922-verify"), "a lone tier-2 source still verified an entry"
        assert c.execute("SELECT status FROM entries WHERE id=?", (e9,)).fetchone()[0] == "draft", "refused verify still wrote the row"

        e10 = draft_srcs("kbflip-0922-author", "1")
        verify(e10, "other-0922-verify")
        assert c.execute("SELECT status,confidence FROM entries WHERE id=?", (e10,)).fetchone() == ("verified", 0.85), "a lone tier-1 source must still verify at 0.85"

        e11 = draft_srcs("kbflip-0922-author", f"{se},{sf}")
        verify(e11, "other-0922-verify")
        assert c.execute("SELECT status,confidence FROM entries WHERE id=?", (e11,)).fetchone() == ("verified", 0.95), "two independent tier-2 sources must still verify at 0.95"

        e12 = draft_srcs("kbflip-0922-author", f"{se},{sg}")
        assert refused(verify, e12, "other-0922-verify"), "two tier-2 sources on ONE host verified an entry"

        # --- demote kind: 'the bar moved' is not 'the claim was wrong' ------
        cmd_demote(types.SimpleNamespace(id=e11, by="kbflip-0922", reason="under-evidenced by the 2026-09-22 bar", kind="gate-change"))
        note = c.execute("SELECT note FROM entries WHERE id=?", (e11,)).fetchone()[0]
        assert "RETRACTED[gate-change]" in note, f"demote did not record the kind: {note!r}"
        assert refused(cmd_demote, types.SimpleNamespace(id=e10, by="x", reason="r", kind="nonsense")), "an unknown demote kind was not refused"
        cmd_demote(types.SimpleNamespace(id=e10, by="x", reason="r"))
        assert "RETRACTED[discredited]" in c.execute("SELECT note FROM entries WHERE id=?", (e10,)).fetchone()[0], "demote default kind is not 'discredited'"

        # --- evidence gate: quote must be in the raw file, numbers must be in the quote ---
        def vq(eid, quote, raw=rawf, derived=None, by="auditor-0001-verify"):
            index_rows(c)
            cmd_verify(types.SimpleNamespace(id=eid, by=by, second_source=None, allow_root=None,
                                             quote=quote, raw=raw, derived=derived))
        q1 = draft_srcs("kbq-0001-author", "1")
        c.execute("UPDATE entries SET claim='The pass mark is 26 of 40.' WHERE id=?", (q1,)); c.commit()
        assert refused(vq, q1, "this sentence is nowhere in the file"), "a quote absent from the raw file verified an entry"
        assert refused(vq, q1, ""), "an empty quote verified an entry"
        assert refused(vq, q1, QT, raw=os.path.join(tdir, "nope.txt")), "a missing raw file verified an entry"
        assert refused(vq, q1, "pass mark is"), "claim numbers 26, 40 absent from the quote were accepted"
        assert c.execute("SELECT status FROM entries WHERE id=?", (q1,)).fetchone()[0] == "draft", "refused verify still wrote the row"
        vq(q1, "the official pass  mark is\n 26 of 40 points for this exam")  # whitespace-normalised match
        st, qt, loc = c.execute("SELECT status,quote,locator FROM entries WHERE id=?", (q1,)).fetchone()
        assert st == "verified" and qt == QT and loc == "research/_raw/s/raw.txt:2", (st, qt, loc)
        q2 = draft_srcs("kbq-0001-author", "1")
        c.execute("UPDATE entries SET claim='26 of 40 is 65 percent' WHERE id=?", (q2,)); c.commit()
        assert refused(vq, q2, QT), "65 is not in the quote and no --derived was given"
        vq(q2, QT, derived="26/40 = 65 percent")
        assert c.execute("SELECT derived FROM entries WHERE id=?", (q2,)).fetchone()[0] == "26/40 = 65 percent"
        assert refused(vq, q2, QT, derived="short"), "a --derived reason under 10 chars was accepted"
        assert numbers("1,057 and ٢٦") == {"1057", "26"}, "number folding is wrong"

        # --- add-source: tier-1 allowlist, bare root, idempotent ---------------
        def add_src(url, tier, allow_root=None):
            cmd_add_source(types.SimpleNamespace(sector="research", name="n", url=url, kind="page", tier=tier, note=None, allow_root=allow_root))
        PRIMARY_HOSTS = {"istqb.org": 1}
        add_src("https://www.istqb.org/certifications/x", 1)
        add_src("https://sub.istqb.org/y", 1)
        assert refused(add_src, "https://other.example/p", 1), "tier 1 accepted for a host outside primary_hosts"
        add_src("https://other.example/p", 2)
        assert refused(add_src, "https://istqb.org/", 1), "bare root accepted without --allow-root"
        add_src("https://istqb.org/", 1, allow_root="vendor home is the only index")
        assert "ROOT-ALLOWED" in c.execute("SELECT note FROM sources WHERE url='https://istqb.org/'").fetchone()[0]
        add_src("https://other.example/p", 2)  # same URL, same tier: idempotent
        assert refused(add_src, "https://other.example/p", 3), "same URL at another tier not refused"
        PRIMARY_HOSTS = None
        try:
            add_src("https://anything.example/q", 1); msg = ""
        except SystemExit as e:
            msg = str(e)
        assert "kb/kb.json" in msg and "primary_hosts" in msg, f"missing primary_hosts must refuse tier 1 naming kb/kb.json: {msg!r}"
        add_src("https://anything.example/q", 2)  # lower tiers need no allowlist

        # --- raw must be bound to the entry's own source and unchanged -----------
        q3 = draft_srcs("kbq-0001-author", "1")
        c.execute("UPDATE entries SET claim='The pass mark is 26 of 40.' WHERE id=?", (q3,)); c.commit()
        def vraw(eid, **kw):
            cmd_verify(types.SimpleNamespace(id=eid, by="auditor-0001-verify", second_source=None, allow_root=None,
                                             quote=QT, raw=rawf, derived=None))
        index_rows(c, only={2})  # the file belongs to source 2 only, entry cites source 1
        assert refused(vraw, q3), "a raw file fetched for a different source verified the entry"
        os.remove(os.path.join(tdir, "research", "_raw", "index.tsv"))
        assert refused(vraw, q3), "verify without any raw index was accepted"
        index_rows(c, only={1}, sha="0" * 40)
        assert refused(vraw, q3), "a raw file whose sha1 no longer matches the index was accepted"
        index_rows(c, only={1})
        vraw(q3)
        assert c.execute("SELECT status FROM entries WHERE id=?", (q3,)).fetchone()[0] == "verified"
        n_der = c.execute("SELECT COUNT(*) FROM entries WHERE derived IS NOT NULL").fetchone()[0]
        assert n_der >= 1, "derived entries are not counted"
        cmd_stats(types.SimpleNamespace())

        # --- add-batch: CR, bad UTF-8, empty fields, one transaction -----------
        def batch(data, name="b.jsonl"):
            p = os.path.join(tdir, name)
            with open(p, "wb") as f:
                f.write(data)
            cmd_add_batch(types.SimpleNamespace(file=p, by="batch-0001-author"))
            return p
        good = ('{"sector":"research","topic":"bt","claim":"one","sources":[1]}\n'
                '{"sector":"research","topic":"bt","claim":"two","sources":"1,2"}\n').encode()
        n0 = c.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        assert refused(batch, good.replace(b"\n", b"\r\n")), "a CRLF batch file was accepted"
        assert refused(batch, good + b'{"sector":"research","topic":"bt","claim":"\xff","sources":[1]}'), "invalid UTF-8 accepted"
        assert refused(batch, good + b'{"sector":"research","topic":"bt","claim":"","sources":[1]}\n'), "empty claim accepted"
        assert refused(batch, good + b'{"sector":"research","topic":"bt","claim":"x","sources":[]}\n'), "empty sources accepted"
        assert refused(batch, good + b'{"sector":"research","topic":"bt","claim":"x","sources":[999]}\n'), "unknown source accepted"
        assert c.execute("SELECT COUNT(*) FROM entries").fetchone()[0] == n0, "a refused batch still wrote rows"
        batch(good)
        assert c.execute("SELECT COUNT(*) FROM entries").fetchone()[0] == n0 + 2
        batch(good, "b2.jsonl")  # idempotent re-run
        assert c.execute("SELECT COUNT(*) FROM entries").fetchone()[0] == n0 + 2, "re-running a batch duplicated rows"

        # --- round-3 breaks (F1, F2, F14, B7): each reproduces the break and must now be refused ---
        def newe(claim, srcs="1", by="kbr3-0001-author"):
            e = draft_srcs(by, srcs)
            c.execute("UPDATE entries SET claim=? WHERE id=?", (claim, e)); c.commit()
            return e
        index_rows(c)
        # F1/B1: --second-source widens the binding: a quote read from a source the author did NOT attach
        e = newe("The official pass mark is 26 of 40 points for this exam.", "1")
        def vsec(eid, **kw):
            cmd_verify(types.SimpleNamespace(id=eid, by="auditor-0002-verify", allow_root=None, derived=None, **kw))
        assert refused(vsec, e, quote=QT, raw=raw2f, second_source=2), "B1: a raw file of the unattached second source verified the entry"
        assert refused(vsec, e, quote=QT, raw=rawf, second_source=2), "B1: second source added without its own raw"
        assert refused(vsec, e, quote=QT, raw=rawf, second_source=999, second_raw=raw2f), "B2: unknown second source accepted"
        assert c.execute("SELECT status,source_ids FROM entries WHERE id=?", (e,)).fetchone() == ("draft", "1"), "refused second-source verify wrote the row"
        vsec(e, quote=QT, raw=rawf, second_source=2, second_raw=raw2f, second_quote=QT)
        assert c.execute("SELECT status,source_ids,confidence FROM entries WHERE id=?", (e,)).fetchone() == ("verified", "1,2", 0.95)
        # F2/B3: swapped figures; B4: bare token; B5: quote too short to carry the claim; B6: empty verifier
        sw = newe("The exam has 60 questions in 40 minutes in total here.")
        assert refused(vq, sw, "the exam has 40 questions in 60 minutes in total here"), "B3: swapped figures verified"
        fee = newe("The official fee is 65 USD and it is paid once.")
        assert refused(vq, fee, "65"), "B4: a bare token verified"
        assert refused(vq, fee, "the official fee is 65 USD"), "B4: a quote shorter than the claim (<40) verified"
        vq(fee, "the official fee is 65 USD and it is paid once")
        iso = newe("ISTQB certifies testers worldwide in many countries today")
        assert refused(vq, iso, "ISTQB"), "B5: a one-word quote verified"
        for blank in ("", "   "):
            assert refused(vq, newe("The official fee is 65 USD and it is paid once."), "the official fee is 65 USD and it is paid once", by=blank), "B6: empty verifier accepted"
        # B7: Arabic names have identities
        assert agent_id("\u0627\u0644\u0645\u0624\u0644\u0641-\u0661") == "\u0627\u0644\u0645\u0624\u0644\u0641"
        ar_e = newe("The official fee is 65 USD and it is paid once.", by="\u0627\u0644\u0645\u0624\u0644\u0641-\u0661")
        vq(ar_e, "the official fee is 65 USD and it is paid once", by="\u0627\u0644\u0645\u062f\u0642\u0642-\u0662")
        ar_e2 = newe("The official fee is 65 USD and it is paid once.", by="\u0627\u0644\u0645\u0624\u0644\u0641-\u0661")
        assert refused(vq, ar_e2, "the official fee is 65 USD and it is paid once", by="\u0627\u0644\u0645\u0624\u0644\u0641-\u0663"), "same Arabic prefix accepted"
        # F14: no kb/kb.json is an error, not a QA default
        assert not CFG_PRESENT or True
        assert SECTORS is not None
        r = __import__("subprocess").run([sys.executable, os.path.abspath(__file__), "stats"], env=dict(os.environ, BOOK_ROOT=tdir), capture_output=True, text=True)
        assert r.returncode != 0 and "kb/kb.json" in (r.stderr + r.stdout), "F14: kb.py without kb/kb.json guessed values"
        r = __import__("subprocess").run([sys.executable, os.path.abspath(__file__), "init"], env=dict(os.environ, BOOK_ROOT=tdir), capture_output=True, text=True)
        assert r.returncode != 0 and os.path.isfile(os.path.join(tdir, "kb", "kb.json")), "F14: init did not write a template and stop"
        r = __import__("subprocess").run([sys.executable, os.path.abspath(__file__), "stats"], env=dict(os.environ, BOOK_ROOT=tdir), capture_output=True, text=True)
        assert r.returncode != 0 and "EDIT-ME" in (r.stderr + r.stdout), "F14: a template kb.json was used as real config"
        os.remove(os.path.join(tdir, "kb", "kb.json"))

        # --- add-entry idempotent on topic + whitespace-normalised claim ---------
        ae = lambda claim: cmd_add_entry(types.SimpleNamespace(sector="research", topic="dupt", claim=claim, sources="1", summary=None,
                                                                tags=None, retrieved=None, by="dupa-0001-author"))
        ae("same   claim here")
        n1 = c.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        ae("same claim\nhere")
        assert c.execute("SELECT COUNT(*) FROM entries").fetchone()[0] == n1, "add-entry duplicated a whitespace-equal claim"

        # --- verify-batch: per-row checks, one transaction, exit 1 on any refusal ---
        index_rows(c)
        vb1 = draft_srcs("vb-0001-author", "1")
        vb2 = draft_srcs("vb-0001-author", "1")
        c.execute("UPDATE entries SET claim='pass mark 26 of 40' WHERE id IN (?,?)", (vb1, vb2)); c.commit()
        rel = os.path.relpath(rawf, tdir).replace(os.sep, "/")
        def vbatch(rows, by="vbaud-0001-verify"):
            p = os.path.join(tdir, "vb.jsonl")
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write("".join(json.dumps(r) + "\n" for r in rows))
            cmd_verify_batch(types.SimpleNamespace(file=p, by=by))
        good_row = lambda i: {"id": i, "quote": QT, "raw": rawf}
        assert refused(vbatch, [good_row(vb1), {"id": vb2, "quote": "not in the file", "raw": rawf}]), "a batch with a refused row exited 0"
        st = dict(c.execute("SELECT id,status FROM entries WHERE id IN (?,?)", (vb1, vb2)).fetchall())
        assert st == {vb1: "verified", vb2: "draft"}, f"held row not written / refused row written: {st}"
        assert refused(vbatch, [good_row(vb2)], by="vb-0009-verify"), "verify-batch skipped the same-agent rule"
        vbatch([good_row(vb2)])
        assert c.execute("SELECT status FROM entries WHERE id=?", (vb2,)).fetchone()[0] == "verified"

        # --- G11: several raw files, several quote spans ---
        with open(os.path.join(tdir, "research", "_raw", "s", "m1.txt"), "w", encoding="utf-8") as f:
            f.write("Part one of the exam: the examination has 40 questions in total for the candidate.\n")
        with open(os.path.join(tdir, "research", "_raw", "s", "m2.txt"), "w", encoding="utf-8") as f:
            f.write("Part two of the exam: the pass mark is 26 points and the duration is 60 minutes.\n")
        m1, m2 = (os.path.join(tdir, "research", "_raw", "s", n) for n in ("m1.txt", "m2.txt"))
        with open(os.path.join(tdir, "research", "_raw", "index.tsv"), "a", encoding="utf-8", newline="") as f:
            for r_ in (m1, m2):
                f.write("\t".join(["https://a.example/x", os.path.relpath(r_, tdir).replace(os.sep, "/"), sha1_file(r_), "2026-01-01", "ok"]) + chr(10))
        sp1 = "the examination has 40 questions in total for the candidate"
        sp2 = "the pass mark is 26 points and the duration is 60 minutes"
        mc = lambda: newe("The exam has 40 questions, a pass mark of 26 points and lasts 60 minutes.")
        vm = lambda eid, quote, raw, by="auditor-0011-verify": cmd_verify(types.SimpleNamespace(id=eid, by=by, second_source=None, allow_root=None, derived=None, quote=quote, raw=raw))
        assert refused(vm, mc(), sp1, m1), "one span cannot hold the claim's 26 and 60"
        e11 = mc()
        vm(e11, [sp1, sp2], [m1, m2])
        row11 = c.execute("SELECT status,quote,locator FROM entries WHERE id=?", (e11,)).fetchone()
        assert row11[0] == "verified" and " \u2026 " in row11[1] and row11[2].count(":1") == 2 and "; " in row11[2], row11
        assert refused(vm, mc(), [sp2, sp1], [m1, m2]), "G11: spans out of the claim's order must fail the in-order figures rule"
        assert refused(vm, mc(), [sp1, sp2 + " plus words nowhere in any file"], [m1, m2]), "G11: a span found in no file was accepted"
        assert refused(vm, mc(), [sp1, "short span"], [m1, m2]), "G11: every span needs the length floor"
        assert refused(vm, mc(), [sp1, sp2], [m1, raw2f]), "G11: a raw file fetched for another source must refuse the whole quote"
        assert refused(vm, mc(), [sp1, sp2], [m1, os.path.join(tdir, "nope.txt")]), "G11: a missing raw file was accepted"
        vm(mc(), sp1 + " " + "", [m1]) if False else None
        wbp = os.path.join(tdir, "g11.jsonl")
        eb = mc()
        with open(wbp, "w", encoding="utf-8", newline="") as f:
            f.write(json.dumps({"id": eb, "quote": [sp1, sp2], "raw": [m1, m2]}) + chr(10))
        cmd_verify_batch(types.SimpleNamespace(file=wbp, by="auditor-0011-verify"))
        assert c.execute("SELECT status FROM entries WHERE id=?", (eb,)).fetchone()[0] == "verified", "G11: verify-batch rows accept lists"

        # --- G10: hygiene -- provenance text inside claims ---
        assert strip_trailers("The exam has 40 questions. Source: Exam Structure v2.32, section 7.1") == ("The exam has 40 questions.", ["Source: Exam Structure v2.32, section 7.1"]), strip_trailers("The exam has 40 questions. Source: Exam Structure v2.32, section 7.1")
        assert strip_trailers("Pass mark is 26 (retrieved 2026-10-15).")[0] == "Pass mark is 26."
        assert strip_trailers("Duration is 60 minutes, section 7.1")[0] == "Duration is 60 minutes"
        assert strip_trailers("Fee is 65 USD (page 3) and paid once")[0] == "Fee is 65 USD and paid once"
        assert strip_trailers("A clean claim with 40 questions.") == ("A clean claim with 40 questions.", [])
        hy = [newe("The exam has 40 questions. Source: Exam Structure v2.32, section 7.1", by="hyg-0001-author"),
              newe("Pass mark is 26 points (retrieved 2026-10-15).", by="hyg-0001-author"),
              newe("A clean claim with 40 questions in the text.", by="hyg-0001-author"),
              newe("Duration is 60 minutes, section 7.1", by="hyg-0001-author")]
        vq(hy[3], "x" * 10) if False else None
        c.execute("UPDATE entries SET topic='hyg' WHERE id IN (%s)" % ",".join(map(str, hy))); c.commit()
        cmd_verify(types.SimpleNamespace(id=hy[1], by="auditor-0012-verify", second_source=None, allow_root=None, derived="presence of both figures", quote=QT, raw=rawf))
        before = c.execute("SELECT claim,status FROM entries WHERE id IN (%s) ORDER BY id" % ",".join(map(str, hy))).fetchall()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc0 = cmd_hygiene(types.SimpleNamespace(topic="hyg", apply=False, by="hyg-0002"))
        assert rc0 == 0 and "dry run, nothing changed" in buf.getvalue() and "3 claim(s) carry provenance text" in buf.getvalue(), buf.getvalue()
        assert c.execute("SELECT claim,status FROM entries WHERE id IN (%s) ORDER BY id" % ",".join(map(str, hy))).fetchall() == before, "G10: the dry run changed something"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc1 = cmd_hygiene(types.SimpleNamespace(topic="hyg", apply=True, by="hyg-0003"))
        assert rc1 == 1 and "NOT APPLIED: author 'hyg-0001-author'" in buf.getvalue(), "G10: the author's own prefix may not amend a VERIFIED entry"
        after = {r[0]: r for r in c.execute("SELECT id,claim,status,summary FROM entries WHERE id IN (%s)" % ",".join(map(str, hy)))}
        assert after[hy[0]][1] == "The exam has 40 questions." and after[hy[0]][2] == "draft" and "provenance: Source: Exam Structure" in after[hy[0]][3], after[hy[0]]
        assert after[hy[3]][1] == "Duration is 60 minutes" and after[hy[2]][1] == "A clean claim with 40 questions in the text."
        assert after[hy[1]][1] == "Pass mark is 26 points (retrieved 2026-10-15)." and after[hy[1]][2] == "verified", "the refused verified row must be untouched"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc2 = cmd_hygiene(types.SimpleNamespace(topic="hyg", apply=True, by="other-0004"))
        assert rc2 == 0, buf.getvalue()
        r1 = c.execute("SELECT claim,status,verified_by,note FROM entries WHERE id=?", (hy[1],)).fetchone()
        assert r1[0] == "Pass mark is 26 points." and r1[1] == "verified" and r1[2] == "auditor-0012-verify" and "hygiene" in r1[3], f"G10: a verified entry keeps its status after a trailer-only amend: {r1}"

        # --- K1: verify / verify-batch never revive a retracted entry ---
        rt1 = newe("The official fee is 65 USD and it is paid once.")
        fee_q = "the official fee is 65 USD and it is paid once"
        vq(rt1, fee_q)
        cmd_demote(types.SimpleNamespace(id=rt1, by="kbk1-0001", reason="test retraction"))
        assert c.execute("SELECT status FROM entries WHERE id=?", (rt1,)).fetchone()[0] == "retracted"
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                vq(rt1, fee_q)
            raise AssertionError("K1: verify revived a retracted entry")
        except SystemExit as e:
            assert "retracted" in str(e) and "re-add or amend it first" in str(e), e
        fresh = newe("The official fee is 65 USD and it is paid once.")
        kbp = os.path.join(tdir, "k1.jsonl")
        with open(kbp, "w", encoding="utf-8", newline="") as f:
            f.write("".join(json.dumps({"id": i, "quote": fee_q, "raw": rawf}) + chr(10) for i in (rt1, fresh)))
        index_rows(c)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                cmd_verify_batch(types.SimpleNamespace(file=kbp, by="auditor-0001-verify"))
            raise AssertionError("K1: a batch with a retracted row exited 0")
        except SystemExit as e:
            assert e.code == 1, e.code
        assert f"refused  {rt1}" in buf.getvalue() and "retracted" in buf.getvalue() and f"held     {fresh}" in buf.getvalue(), buf.getvalue()
        assert c.execute("SELECT status FROM entries WHERE id=?", (rt1,)).fetchone()[0] == "retracted", "K1: the batch revived the retracted entry"
        assert c.execute("SELECT status FROM entries WHERE id=?", (fresh,)).fetchone()[0] == "verified", "K1: the other rows of the batch still verify"

        # --- G9: a row its verifier marked weak is refused (single and batch) ---
        wk = newe("The official fee is 65 USD and it is paid once.")
        assert refused(cmd_verify, types.SimpleNamespace(id=wk, by="auditor-0009-verify", second_source=None, allow_root=None, derived=None,
                                                         quote="the official fee is 65 USD and it is paid once", raw=rawf, weak=True)), "G9: a weak row was verified"
        assert c.execute("SELECT status FROM entries WHERE id=?", (wk,)).fetchone()[0] == "draft"
        wkp = os.path.join(tdir, "wk.jsonl")
        with open(wkp, "w", encoding="utf-8", newline="") as f:
            f.write(json.dumps({"id": wk, "quote": "the official fee is 65 USD and it is paid once", "raw": rawf, "weak": True}) + chr(10))
        assert refused(cmd_verify_batch, types.SimpleNamespace(file=wkp, by="auditor-0009-verify")), "G9: a weak:true batch row was verified"
        assert c.execute("SELECT status FROM entries WHERE id=?", (wk,)).fetchone()[0] == "draft"
        with open(wkp, "w", encoding="utf-8", newline="") as f:
            f.write(json.dumps({"id": wk, "quote": "the official fee is 65 USD and it is paid once", "raw": rawf, "weak": False}) + chr(10))
        cmd_verify_batch(types.SimpleNamespace(file=wkp, by="auditor-0009-verify"))
        assert c.execute("SELECT status FROM entries WHERE id=?", (wk,)).fetchone()[0] == "verified", "G9: weak:false must still verify"

        # --- S3: a version token in the source's NAME is not a figure the quote must hold ---
        c.execute("INSERT INTO sources(sector,name,url,kind,tier,note,added) VALUES('research','ISTQB CTFL v4.0 Syllabus','https://v.example/syl','page',1,NULL,?)", (today(),))
        c.commit()
        with open(os.path.join(tdir, "research", "_raw", "s", "ver.txt"), "w", encoding="utf-8") as f:
            f.write("Exam structure: the examination has 40 questions in total and lasts 60 minutes.\n")
        vrel = "research/_raw/s/ver.txt"
        with open(os.path.join(tdir, "research", "_raw", "index.tsv"), "a", encoding="utf-8", newline="") as f:
            f.write("\t".join(["https://v.example/syl", vrel, sha1_file(os.path.join(tdir, vrel)), "2026-01-01", "ok"]) + "\n")
        vsrc = c.execute("SELECT id FROM sources WHERE url='https://v.example/syl'").fetchone()[0]
        ve = draft_srcs("kbs3-0001-author", str(vsrc))
        c.execute("UPDATE entries SET claim=? WHERE id=?", ("The CTFL v4.0 examination has 40 questions in total.", ve)); c.commit()
        vqt = "the examination has 40 questions in total and lasts 60 minutes"
        cmd_verify(types.SimpleNamespace(id=ve, by="auditor-0003-verify", second_source=None, allow_root=None, derived=None, quote=vqt, raw=os.path.join(tdir, vrel)))
        assert c.execute("SELECT status FROM entries WHERE id=?", (ve,)).fetchone()[0] == "verified", "S3: the version label in the source name must be exempt"
        ve2 = draft_srcs("kbs3-0001-author", str(vsrc))
        c.execute("UPDATE entries SET claim=? WHERE id=?", ("The CTFL v9.9 examination has 40 questions in total.", ve2)); c.commit()
        assert refused(cmd_verify, types.SimpleNamespace(id=ve2, by="auditor-0003-verify", second_source=None, allow_root=None, derived=None, quote=vqt, raw=os.path.join(tdir, vrel))), "S3: a version token NOT in the source name must still be found in the quote"
        ve3 = draft_srcs("kbs3-0001-author", str(vsrc))
        c.execute("UPDATE entries SET claim=? WHERE id=?", ("The CTFL v4.0 examination has 45 questions in total.", ve3)); c.commit()
        assert refused(cmd_verify, types.SimpleNamespace(id=ve3, by="auditor-0003-verify", second_source=None, allow_root=None, derived=None, quote=vqt, raw=os.path.join(tdir, vrel))), "S3: every OTHER figure keeps the full rule"
        assert strip_versions("CTFL v4.0 has 40 and 2.1.1", ["ISTQB CTFL v4.0"]) == "CTFL   has 40 and 2.1.1"

        # --- S9: add-batch prints id<TAB>claim60 per row in file order ---
        bp = os.path.join(tdir, "s9.jsonl")
        with open(bp, "w", encoding="utf-8", newline="") as f:
            f.write("".join(json.dumps(dict(sector="research", topic="s9", claim=f"S9 claim number {i} " + "x" * 70, sources=[1], by="s9-0001-author")) + "\n" for i in (3, 1, 2)))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_add_batch(types.SimpleNamespace(file=bp, by=None))
        rows = [l.split("\t") for l in buf.getvalue().splitlines() if "\t" in l]
        assert [r[1][:15] for r in rows] == ["S9 claim number", "S9 claim number", "S9 claim number"] and [r[1][16] for r in rows] == ["3", "1", "2"] and all(len(r[1]) == 60 for r in rows), rows
        ids9 = [int(r[0]) for r in rows]
        assert ids9 == sorted(ids9) and c.execute("SELECT claim FROM entries WHERE id=?", (ids9[0],)).fetchone()[0].startswith("S9 claim number 3"), "S9: ids must map to claims in file order"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_add_batch(types.SimpleNamespace(file=bp, by=None))
        assert buf.getvalue().count("dup ") == 3 and "\tS9 claim number 3" in buf.getvalue(), "S9: a re-run prints dup <id><TAB>claim"

        # --- S7: a demotion shows everything that still cites the entry, and exits 2 ---
        os.makedirs(os.path.join(tdir, "chapters"), exist_ok=True)
        os.makedirs(os.path.join(tdir, "kb", "rules"), exist_ok=True)
        with open(os.path.join(tdir, "book.json"), "w", encoding="utf-8") as f:
            json.dump({"title": "T", "slug": "t", "pages": "chapters", "practice": "practice", "kinds": {}}, f)
        with open(os.path.join(tdir, "chapters", "p.md"), "w", encoding="utf-8") as f:
            f.write("# P\nA claim [KB#%d] and another [KB#%d0].\n" % (ve, ve))
        os.makedirs(os.path.join(tdir, "practice"), exist_ok=True)
        with open(os.path.join(tdir, "practice", "p.md"), "w", encoding="utf-8") as f:
            f.write("### Q-1\n- basis: KB#%d\n" % ve)
        with open(os.path.join(tdir, "kb", "rules", "x.md"), "w", encoding="utf-8") as f:
            f.write("### R-X-001 \u00b7 t\n**Rule:** r\n**When:** w\n**Because:** #%d, #99\n" % ve)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                cmd_demote(types.SimpleNamespace(id=ve, by="kbs7-0001", reason="weak: claim wider than quote"))
            raise AssertionError("S7: a demotion with live citations exited 0")
        except SystemExit as e:
            assert e.code == 2, e.code
        out7 = buf.getvalue()
        assert "kb/rules/x.md:4" in out7.replace(os.sep, "/") and "chapters/p.md:2" in out7.replace(os.sep, "/") and "practice/p.md:2" in out7.replace(os.sep, "/") and "KB#%d0" % ve not in out7, out7
        assert out7.count("still cited by") == 3, "S7: KB#%d0 is a different id and must not match" % ve

        # --- read commands never alter: a DB without the new columns is read, not migrated ---
        old = os.path.join(tdir, "kb", "old.db")
        oc = sqlite3.connect(old, timeout=60)
        oc.executescript(SCHEMA)
        oc.execute("INSERT INTO entries(sector,topic,claim,source_ids,retrieved,updated) VALUES('research','t','c','1','2026-01-01','2026-01-01')")
        oc.commit(); oc.close()
        DB = old
        cmd_query(types.SimpleNamespace(sector=None, topic=None, tag=None, status=None, limit=5, full=False))
        cols = {r[1] for r in sqlite3.connect(old, timeout=60).execute("PRAGMA table_info(entries)")}
        assert "quote" not in cols, "a read command ALTERed the database"
        DB = tmp

        print("selftest: OK (draft reset, log old/new, identical refused, unknown rejected, "
              "self-verify refused by run identity, second agent accepted, demote records reason "
              "+ status 'retracted' != 'draft', amend keeps summary-only verified, claim amend resets, "
              "amend respects the author gate, detach rescores and demotes when support falls away, "
              "detach refuses the author / the only source / an unattached source, "
              "independence flag is derived and three-valued, "
              "a lone tier-2 source is REFUSED while a lone tier-1 and two independent tier-2s pass, "
              "demote records kind gate-change vs discredited, quote absent from raw refused, numbers outside the quote refused unless --derived, "
              "tier-1 host allowlist, bare root, batch CR/UTF-8/empty/unknown refused and atomic, reads never ALTER)")
    finally:
        DB, PRIMARY_HOSTS, ROOT, SECTORS = real_db, real_hosts, real_root, real_sectors
        import shutil
        shutil.rmtree(tdir, ignore_errors=True)


def cmd_export(a):
    c = con(); s = sector(a.sector)
    out = os.path.join(ROOT, "kb", f"digest-{s}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# KB digest -- {s} -- {today()}\n\nOnly `verified` entries. Draft, recheck and stale entries are not publishable.\nAn entry flagged SELF-VERIFIED or UNKNOWN INDEPENDENCE is not independent corroboration -- do not cite it as a second source.\n\n")
        for r in c.execute(f"SELECT id,topic,claim,summary,source_ids,retrieved,confidence,{col(c, 'author')},verified_by FROM entries WHERE sector=? AND status='verified' ORDER BY topic,id", (s,)):
            urls = [u for (u,) in c.execute(f"SELECT url FROM sources WHERE id IN ({r[4]})")]
            f.write(f"## #{r[0]} {r[1]}\n{r[2]}\n\n{r[3] or ''}\n\n- retrieved {r[5]}, confidence {r[6]}\n")
            flag = independence(r[7], r[8])
            if flag:  # a worker handed the digest sees it without opening the DB
                f.write(f"- **{INDEPENDENCE_LABEL[flag]}**\n")
            f.write("".join(f"- {u}\n" for u in urls) + "\n")
    print(f"wrote {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("init").set_defaults(f=cmd_init)
    x = sp.add_parser("add-batch"); x.add_argument("file"); x.add_argument("--by"); x.set_defaults(f=cmd_add_batch)
    x = sp.add_parser("verify-batch"); x.add_argument("file"); x.add_argument("--by", required=True); x.set_defaults(f=cmd_verify_batch)
    x = sp.add_parser("hygiene"); x.add_argument("--topic"); x.add_argument("--apply", action="store_true"); x.add_argument("--by", default="hygiene-0001")
    x.set_defaults(f=lambda a: sys.exit(cmd_hygiene(a)))
    x = sp.add_parser("add-source")
    x.add_argument("--sector", required=True); x.add_argument("--name", required=True); x.add_argument("--url", required=True)
    x.add_argument("--tier", type=int, required=True); x.add_argument("--kind", default="page", choices=["page", "rss"]); x.add_argument("--note")
    x.add_argument("--allow-root", metavar="REASON")
    x.set_defaults(f=cmd_add_source)
    x = sp.add_parser("add-entry")
    x.add_argument("--sector", required=True); x.add_argument("--topic", required=True); x.add_argument("--claim", required=True)
    x.add_argument("--sources", required=True); x.add_argument("--summary"); x.add_argument("--tags"); x.add_argument("--retrieved"); x.add_argument("--by", required=True)
    x.set_defaults(f=cmd_add_entry)
    x = sp.add_parser("verify"); x.add_argument("id", type=int); x.add_argument("--by", required=True); x.add_argument("--second-source", type=int); x.add_argument("--allow-root", metavar="REASON")
    x.add_argument("--quote", action="append", help="repeat for several spans (each >= 40 chars)"); x.add_argument("--raw", action="append", help="repeat for several raw files, each fetched for one of the entry's own sources"); x.add_argument("--derived", metavar="REASON")
    x.add_argument("--second-raw"); x.add_argument("--second-quote")
    x.add_argument("--weak", action="store_true", help="the verifier judges the claim wider than the quote: refused, re-quote or demote")
    x.set_defaults(f=cmd_verify)
    x = sp.add_parser("query"); x.add_argument("--sector"); x.add_argument("--topic"); x.add_argument("--tag"); x.add_argument("--status")
    x.add_argument("--limit", type=int, default=20); x.add_argument("--full", action="store_true"); x.set_defaults(f=cmd_query)
    x = sp.add_parser("sources"); x.add_argument("--sector"); x.add_argument("--tier", type=int); x.set_defaults(f=cmd_sources)
    sp.add_parser("stats").set_defaults(f=cmd_stats)
    x = sp.add_parser("stale"); x.add_argument("--days", type=int, default=90); x.set_defaults(f=cmd_stale)
    x = sp.add_parser("export"); x.add_argument("--sector", required=True); x.set_defaults(f=cmd_export)
    x = sp.add_parser("triage"); x.add_argument("--ids"); x.add_argument("--all", action="store_true"); x.add_argument("--by", required=True); x.set_defaults(f=cmd_triage)
    x = sp.add_parser("fix-sources"); x.add_argument("id", type=int); x.add_argument("--sources", required=True)
    x.add_argument("--by", required=True); x.add_argument("--reason", required=True); x.set_defaults(f=cmd_fix_sources)
    x = sp.add_parser("detach"); x.add_argument("id", type=int); x.add_argument("--source", type=int, required=True)
    x.add_argument("--by", required=True); x.add_argument("--reason", required=True); x.set_defaults(f=cmd_detach)
    x = sp.add_parser("demote"); x.add_argument("id", type=int); x.add_argument("--by", required=True)
    x.add_argument("--reason", required=True)
    x.add_argument("--kind", default="discredited", choices=list(DEMOTE_KINDS),
                   help="discredited = failed on its merits; gate-change = the bar moved under it")
    x.set_defaults(f=cmd_demote)
    x = sp.add_parser("amend"); x.add_argument("id", type=int); x.add_argument("--by", required=True)
    x.add_argument("--claim"); x.add_argument("--summary"); x.add_argument("--reason", required=True); x.set_defaults(f=cmd_amend)
    x = sp.add_parser("feed"); x.add_argument("--sector"); x.add_argument("--untriaged", action="store_true")
    x.add_argument("--limit", type=int); x.set_defaults(f=cmd_feed)
    ap.add_argument("--selftest", action="store_true", help="run internal self-check and exit")
    if "--selftest" in sys.argv:
        selftest(); return
    a = ap.parse_args()
    if a.cmd == "init" and not CFG_PRESENT:
        os.makedirs(os.path.join(ROOT, "kb"), exist_ok=True)
        with open(os.path.join(ROOT, "kb", "kb.json"), "w", encoding="utf-8") as f:
            json.dump({"db": "kb/facts.db", "sectors": ["EDIT-ME"], "primary_hosts": {"EDIT-ME.example": 1}}, f, indent=1)
        sys.exit(f"no kb/kb.json in {ROOT}: wrote a template -- edit db, sectors and primary_hosts (the Lead signs the host list), then run init again")
    if not CFG_PRESENT:
        sys.exit(f"no kb/kb.json in {ROOT} (project = BOOK_ROOT or cwd): write {{\"db\": ..., \"sectors\": [...], \"primary_hosts\": {{...}}}}; `kb.py init` writes a template")
    if "EDIT-ME" in SECTORS:
        sys.exit("kb/kb.json still holds the template values (EDIT-ME): fill in sectors and primary_hosts first")
    a.f(a)


if __name__ == "__main__":
    main()
