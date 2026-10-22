#!/usr/bin/env python3
"""kb.py -- Arabic tashkeel knowledge base (SQLite, stdlib only). PYTHONUTF8=1 assumed.

One database for the five sectors: research, design, marketing, programs,
production. Every fact is an ENTRY tied to at least one SOURCE. An entry is
never "verified" by a model's say-so: it needs a lone TIER-1 primary source OR
two independent sources (different hosts), a retrieval date, and a named
verifier. Nothing that is not `verified` may be published.

    kb.py init
    kb.py add-source --sector research --name "arXiv cs.RO" --url URL --tier 2 [--kind rss|page] [--note ..]
    kb.py add-entry  --sector design --topic "colour" --claim ".." --sources 3,7 --by <author> [--summary ..] [--tags a,b]
    kb.py verify ENTRY_ID --by "<who>" [--second-source ID] [--allow-root REASON]   (verifier must be a different agent/run; deep links only)
    kb.py query  --sector marketing [--topic linkedin] [--tag x] [--status verified] [--limit 20] [--full]
    kb.py sources [--sector research] [--tier 1]
    kb.py stats
    kb.py stale [--days 90]
    kb.py export --sector programs      -> kb/digest-programs.md (a checkpoint file)
    kb.py triage --ids 1,2 | --all --by <who>   mark feed items as looked at
    kb.py detach ENTRY_ID --source SID --by "<who>" --reason ".."   withdraw one source's support, rescore, demote if what is left misses the bar
    kb.py demote ENTRY_ID --by "<who>" --reason ".." [--kind discredited|gate-change]   withdraw a verified entry -> status 'retracted'
    kb.py amend  ENTRY_ID --by "<who>" --reason ".." [--claim ..] [--summary ..]   correct in place (--claim resets to draft)

Output is deliberately terse (one line per row) so a director can read a query
without spending context. Use --full only when a worker needs the body.
"""
from __future__ import annotations
import argparse, re, sqlite3, sys, os, types, datetime as dt
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "kb", "tashkeel.db")
SECTORS = ("tashkeel",)
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
MIGRATIONS = ["ALTER TABLE entries ADD COLUMN author TEXT",
              "ALTER TABLE entries ADD COLUMN note TEXT"]
# `note` is the retraction/amendment record kept on the row itself: status
# 'retracted' says an entry WAS verified and was withdrawn (never-verified is
# 'draft'), and note says by whom and why. ponytail: one appended text column,
# not a history table -- add a table if anyone ever needs to query the history.


def today():
    return dt.date.today().isoformat()


def con():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB)
    c.executescript(SCHEMA)
    for m in MIGRATIONS:
        try: c.execute(m)
        except sqlite3.OperationalError: pass
    return c


def log(c, action, detail):
    c.execute("INSERT INTO log VALUES(?,?,?)", (dt.datetime.now().isoformat(timespec="seconds"), action, detail))


def sector(s):
    if s not in SECTORS:
        sys.exit(f"sector must be one of {SECTORS}")
    return s


def host(url):
    return url.split("/")[2].lower() if "://" in url else url.lower()


def is_root(url):
    """A bare homepage cites nothing: the fact must be on the page."""
    return re.match(r"https?://[^/]+/?(\?lang=\w+)?$", url) is not None


ROLES = {"author", "authors", "authored", "writer", "drafts", "draft",
         "verify", "verifier", "verification", "verified",
         "check", "checker", "review", "reviewer", "second"}


def agent_id(name):
    """Run identity behind an agent name: `reelsrc-0922-author` -> `reelsrc-0922`.

    Role words at either end, and a trailing single-character instance tag, are
    labels the same agent can put on itself; what is left is the run it belongs
    to. Compared instead of the raw string, so `x-author` and `x-verify` are
    one agent.
    ponytail: self-asserted names only -- an agent that picks two unrelated
    names still passes; a signed run id from the ops layer would close that.
    """
    t = [x for x in re.split(r"[^0-9a-z]+", (name or "").lower()) if x]
    while t and t[0] in ROLES:
        t.pop(0)
    while t and (t[-1] in ROLES or len(t[-1]) == 1):
        t.pop()
    return "-".join(t)


def support(srcs):
    """The publication bar, in one place: (passes, confidence) for a set of
    (id, url, tier) rows. A LONE source carries an entry only at tier 1
    (official / standards body / primary); otherwise it takes two sources on
    different hosts. Shared by `verify` and `detach` so withdrawing support is
    scored by exactly the rule that granted it.

    Changed 2026-09-22 (owner): a lone tier-2 source used to pass. It no
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
    c = con(); c.commit(); print(f"ok  {DB}")


def cmd_add_source(a):
    c = con()
    c.execute("INSERT INTO sources(sector,name,url,kind,tier,note,added) VALUES(?,?,?,?,?,?,?)",
              (sector(a.sector), a.name, a.url, a.kind, a.tier, a.note, today()))
    sid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    log(c, "add-source", a.url); c.commit()
    print(f"source {sid}  tier{a.tier}  {a.name}")


def cmd_add_entry(a):
    c = con()
    ids = [int(x) for x in a.sources.split(",") if x.strip()]
    marks = ",".join("?" * len(ids))
    known = {r[0] for r in c.execute(f"SELECT id FROM sources WHERE id IN ({marks})", ids)}
    missing = set(ids) - known
    if missing:
        sys.exit(f"unknown source ids {sorted(missing)} -- add the source first; a claim without a source is not stored")
    c.execute("INSERT INTO entries(sector,topic,claim,summary,tags,source_ids,retrieved,updated,author) VALUES(?,?,?,?,?,?,?,?,?)",
              (sector(a.sector), a.topic, a.claim, a.summary, a.tags, ",".join(map(str, ids)), a.retrieved or today(), today(), a.by))
    eid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    log(c, "add-entry", a.claim[:80]); c.commit()
    print(f"entry {eid}  draft  {a.topic}")


def cmd_verify(a):
    """Gate: a lone tier-1 source, or two independent sources on different hosts."""
    c = con()
    row = c.execute("SELECT source_ids,author FROM entries WHERE id=?", (a.id,)).fetchone()
    if not row:
        sys.exit("no such entry")
    # ponytail: rows written before the `author` migration have author NULL and
    # cannot be checked; add-entry has required --by ever since, so this is history only.
    if row[1] and agent_id(row[1]) == agent_id(a.by):
        sys.exit(f"GATE FAIL: entry {a.id}: author '{row[1]}' and verifier '{a.by}' are the same agent (run '{agent_id(a.by) or '(role words only)'}'); a different agent must verify.")
    ids = [int(x) for x in row[0].split(",")]
    if a.second_source and a.second_source not in ids:
        ids.append(a.second_source)
    marks = ",".join("?" * len(ids))
    srcs = c.execute(f"SELECT id,url,tier FROM sources WHERE id IN ({marks})", ids).fetchall()
    roots = [u for _, u, _ in srcs if is_root(u)]
    if roots and not a.allow_root:
        sys.exit("GATE FAIL: source is a bare homepage, not the page that states the fact: " + ", ".join(roots) + "  (add the deep link as a source, or --allow-root with a reason)")
    ok, conf = support(srcs)
    if not ok:
        sys.exit("GATE FAIL: needs a tier-1 source on its own, or two sources on different hosts. Not verified.")
    c.execute("UPDATE entries SET status='verified',verified_by=?,verified_on=?,second_source=?,source_ids=?,confidence=?,updated=? WHERE id=?",
              (a.by, today(), a.second_source, ",".join(map(str, ids)), conf, today(), a.id))
    log(c, "verify", f"{a.id} by {a.by}"); c.commit()
    print(f"entry {a.id}  verified  confidence {conf}")


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


def cmd_demote(a):
    """Withdraw a verified entry. Records WHO, WHY and WHICH KIND on the row: a
    retraction is a fact, not an absence -- status 'retracted' is
    distinguishable from 'draft' (never verified), and verified_by/verified_on
    are kept as the record of the verification being withdrawn."""
    c = con()
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
    c = con()
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


def cmd_amend(a):
    """Correct a claim or a summary in place, recording what changed.

    Amending the CLAIM resets the entry to draft -- the verification was of the
    old words, so keeping 'verified' would be self-verification by the back
    door. Amending a verified entry at all is refused for its own author, the
    same identity gate cmd_verify uses.
    """
    c = con()
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
    reset = a.claim is not None and st == "verified"
    if reset:
        sets += ["status='draft'", "verified_by=NULL", "verified_on=NULL", "second_source=NULL", "confidence=0.5"]
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
    q = "SELECT id,sector,topic,status,confidence,retrieved,claim,summary,source_ids,tags,note,author,verified_by FROM entries WHERE 1=1"
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


def cmd_stale(a):
    c = con()
    cut = (dt.date.today() - dt.timedelta(days=a.days)).isoformat()
    rows = c.execute("SELECT id,sector,topic,retrieved FROM entries WHERE status='verified' AND retrieved<?", (cut,)).fetchall()
    for r in rows:
        print(f"#{r[0]} {r[1]}/{r[2]} retrieved {r[3]}")
    print(f"{len(rows)} entries older than {a.days} days")


def cmd_triage(a):
    """Mark feed items as looked at. --ids 1,2,3 or --all (after a worker has read the queue file)."""
    c = con()
    if a.all:
        n = c.execute("UPDATE updates SET triaged=1 WHERE triaged=0").rowcount
    else:
        ids = [int(x) for x in a.ids.split(",") if x.strip()]
        n = c.execute(f"UPDATE updates SET triaged=1 WHERE id IN ({','.join('?'*len(ids))})", ids).rowcount
    log(c, "triage", f"{n} items by {a.by}"); c.commit(); print(f"triaged {n}")


def cmd_fix_sources(a):
    """Repair a citation only: source_ids. Forces back to draft (unverified)."""
    c = con()
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
    c.execute("UPDATE entries SET source_ids=?,status='draft',verified_by=NULL,verified_on=NULL,second_source=NULL,confidence=0.5,updated=? WHERE id=?",
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
    import tempfile
    global DB
    real_db = DB
    tmp = tempfile.mktemp(suffix=".db")
    DB = tmp
    try:
        c = con()
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
            cmd_verify(types.SimpleNamespace(id=eid, by=by, second_source=None, allow_root=None))

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

        assert agent_id("x-0922-author") == agent_id("verify-x-0922") == "x-0922"
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

        print("selftest: OK (draft reset, log old/new, identical refused, unknown rejected, "
              "self-verify refused by run identity, second agent accepted, demote records reason "
              "+ status 'retracted' != 'draft', amend keeps summary-only verified, claim amend resets, "
              "amend respects the author gate, detach rescores and demotes when support falls away, "
              "detach refuses the author / the only source / an unattached source, "
              "independence flag is derived and three-valued, "
              "a lone tier-2 source is REFUSED while a lone tier-1 and two independent tier-2s pass, "
              "demote records kind gate-change vs discredited)")
    finally:
        DB = real_db
        try: os.remove(tmp)
        except OSError: pass


def cmd_export(a):
    c = con(); s = sector(a.sector)
    out = os.path.join(ROOT, "kb", f"digest-{s}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# Arabic tashkeel KB digest -- {s} -- {today()}\n\nOnly `verified` entries. Draft, recheck and stale entries are not publishable.\nAn entry flagged SELF-VERIFIED or UNKNOWN INDEPENDENCE is not independent corroboration -- do not cite it as a second source.\n\n")
        for r in c.execute("SELECT id,topic,claim,summary,source_ids,retrieved,confidence,author,verified_by FROM entries WHERE sector=? AND status='verified' ORDER BY topic,id", (s,)):
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
    x = sp.add_parser("add-source")
    x.add_argument("--sector", required=True); x.add_argument("--name", required=True); x.add_argument("--url", required=True)
    x.add_argument("--tier", type=int, required=True); x.add_argument("--kind", default="page", choices=["page", "rss"]); x.add_argument("--note")
    x.set_defaults(f=cmd_add_source)
    x = sp.add_parser("add-entry")
    x.add_argument("--sector", required=True); x.add_argument("--topic", required=True); x.add_argument("--claim", required=True)
    x.add_argument("--sources", required=True); x.add_argument("--summary"); x.add_argument("--tags"); x.add_argument("--retrieved"); x.add_argument("--by", required=True)
    x.set_defaults(f=cmd_add_entry)
    x = sp.add_parser("verify"); x.add_argument("id", type=int); x.add_argument("--by", required=True); x.add_argument("--second-source", type=int); x.add_argument("--allow-root", metavar="REASON")
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
    a = ap.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
