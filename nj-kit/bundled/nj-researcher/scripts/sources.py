#!/usr/bin/env python3
"""sources.py -- nj-researcher source registry (SQLite, stdlib only). PYTHONUTF8=1.

Why a script and not context: the registry holds 300+ sources. Loading that list
into a model costs ~25-30k tokens EVERY time. A `query` returns 5-10 one-line
rows, ~200-500 tokens. The model asks a question and gets the few rows it needs.
Same pattern as ENSERA's scripts/kb.py ("the knowledge base is a script, not
context").

    sources.py init
    sources.py seed [--file data/seed.tsv] [--reset]
    sources.py stats
    sources.py query --topic "clinical trial" [--domain medicine] [--tier 1]
                     [--lang ar] [--region mena] [--limit 8] [--full]
    sources.py add --name N --url U --domain D --tier 1..4 --lang en|ar|mixed
                   --for "what it is authoritative for" --why "why this tier"
                   [--region global|mena|jordan|eu|us] [--state verified|unverified]
    sources.py check --url U [--name N] [--domain D]
                   -> rubric verdict for ONE candidate, with reasons
    sources.py candidate --url U --name N --domain D --tier T --verdict accept|reject|unsure
                   --reasons "..." [--for ...]        (record a fetch verdict)
    sources.py candidates [--status pending|accept|reject|unsure]
    sources.py promote ID --by WHO        (candidate -> registry)
    sources.py export --topic T [--domain D] [--out PATH]   -> checkpoint file
    sources.py cost --topic T             (measure the token cost of a lookup)

Honesty: `state` is `verified` (URL confirmed to exist) or `unverified` (recorded
from knowledge, not confirmed this session). `query` prints `?` in front of every
unverified row. The registry never asserts what it has not checked.
"""
from __future__ import annotations
import argparse, sqlite3, sys, os, datetime as dt, re

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB = os.environ.get("NJ_SOURCES_DB", os.path.join(ROOT, "data", "sources.db"))
SEED = os.path.join(ROOT, "data", "seed.tsv")

TIERS = {
    1: "primary / official record: the body that MAKES the fact (law, standard, registry, statistics office, the paper itself)",
    2: "peer-reviewed or institutional secondary: reports the primary faithfully, has editorial or scientific review",
    3: "reputable specialist press / vendor documentation: named authors, corrections policy, but interested or unreviewed",
    4: "aggregator / community / encyclopaedic: a map to primaries, never the citation itself",
}
DOMAINS = ("ai", "software", "security", "medicine", "law", "finance", "science",
           "data", "standards", "government", "reference", "journalism", "mena", "meta")
STATES = ("verified", "unverified")

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  url TEXT NOT NULL UNIQUE,
  domain TEXT NOT NULL,
  tier INTEGER NOT NULL CHECK(tier BETWEEN 1 AND 4),
  lang TEXT NOT NULL DEFAULT 'en',
  region TEXT NOT NULL DEFAULT 'global',
  state TEXT NOT NULL DEFAULT 'unverified',
  authoritative_for TEXT NOT NULL,
  why TEXT NOT NULL,
  chain TEXT,
  added TEXT NOT NULL,
  last_checked TEXT);
CREATE TABLE IF NOT EXISTS candidates(
  id INTEGER PRIMARY KEY, name TEXT, url TEXT UNIQUE, domain TEXT, tier INTEGER,
  verdict TEXT, reasons TEXT, authoritative_for TEXT, found TEXT NOT NULL,
  promoted INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS log(ts TEXT, action TEXT, detail TEXT);
CREATE INDEX IF NOT EXISTS ix_dom ON sources(domain);
CREATE INDEX IF NOT EXISTS ix_tier ON sources(tier);
"""


def today():
    return dt.date.today().isoformat()


def con():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB)
    c.executescript(SCHEMA)
    return c


def log(c, action, detail):
    c.execute("INSERT INTO log VALUES(?,?,?)",
              (dt.datetime.now().isoformat(timespec="seconds"), action, detail))


def host(url):
    return url.split("/")[2].lower() if "://" in url else url.lower()


def tokens(s):
    """Rough token estimate: ~4 chars/token for latin, ~2.5 for Arabic."""
    ar = sum(1 for ch in s if "؀" <= ch <= "ۿ")
    return int((len(s) - ar) / 4 + ar / 2.5)


# --------------------------------------------------------------- commands
def cmd_init(a):
    c = con(); c.commit(); print(f"ok  {DB}")


def cmd_seed(a):
    path = a.file or SEED
    if not os.path.exists(path):
        sys.exit(f"no seed file at {path}")
    c = con()
    if a.reset:
        c.execute("DELETE FROM sources")
    n = skipped = bad = 0
    with open(path, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split("\t") if "\t" in line else line.split(" | ")
            if len(parts) != 9:
                bad += 1
                print(f"  line {ln}: expected 9 columns, got {len(parts)} -- skipped", file=sys.stderr)
                continue
            name, url, domain, tier, lang, region, state, afor, why = [p.strip() for p in parts]
            try:
                c.execute("INSERT INTO sources(name,url,domain,tier,lang,region,state,"
                          "authoritative_for,why,added) VALUES(?,?,?,?,?,?,?,?,?,?)",
                          (name, url, domain, int(tier), lang, region, state, afor, why, today()))
                n += 1
            except sqlite3.IntegrityError:
                skipped += 1
    log(c, "seed", f"{n} added, {skipped} dupes, {bad} malformed"); c.commit()
    print(f"seeded {n}  (duplicates skipped {skipped}, malformed {bad})")


def cmd_stats(a):
    c = con()
    total = c.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    print(f"sources total: {total}")
    print("by domain: " + "  ".join(
        f"{d}={n}" for d, n in c.execute(
            "SELECT domain,COUNT(*) FROM sources GROUP BY domain ORDER BY COUNT(*) DESC")))
    print("by tier:   " + "  ".join(
        f"t{t}={n}" for t, n in c.execute("SELECT tier,COUNT(*) FROM sources GROUP BY tier ORDER BY tier")))
    print("by state:  " + "  ".join(
        f"{s}={n}" for s, n in c.execute("SELECT state,COUNT(*) FROM sources GROUP BY state")))
    print("by lang:   " + "  ".join(
        f"{l}={n}" for l, n in c.execute("SELECT lang,COUNT(*) FROM sources GROUP BY lang ORDER BY COUNT(*) DESC")))
    print("by region: " + "  ".join(
        f"{r}={n}" for r, n in c.execute("SELECT region,COUNT(*) FROM sources GROUP BY region ORDER BY COUNT(*) DESC")))
    print("distinct hosts: %d  (independence ceiling for any one claim)" %
          len({host(u) for (u,) in c.execute("SELECT url FROM sources")}))
    pend = c.execute("SELECT COUNT(*) FROM candidates WHERE promoted=0").fetchone()[0]
    print(f"candidates awaiting promotion: {pend}")


def _rows(c, a):
    q = ("SELECT id,name,url,domain,tier,lang,region,state,authoritative_for,why "
         "FROM sources WHERE 1=1")
    p = []
    if a.topic:
        # every word of the topic must appear somewhere in the row. The de-spaced
        # copy makes "clinical trial" find "ClinicalTrials.gov".
        blob = "(name||' '||authoritative_for||' '||url||' '||domain||' '||why)"
        for w in a.topic.split():
            q += f" AND ({blob} LIKE ? OR REPLACE({blob},' ','') LIKE ?)"
            p += [f"%{w}%", f"%{w}%"]
    if getattr(a, "domain", None):
        q += " AND domain=?"; p.append(a.domain)
    if getattr(a, "tier", None):
        q += " AND tier<=?"; p.append(a.tier)
    if getattr(a, "lang", None):
        q += " AND (lang=? OR lang='mixed')"; p.append(a.lang)
    if getattr(a, "region", None):
        q += " AND (region=? OR region='global')"; p.append(a.region)
    q += " ORDER BY tier, state DESC, id LIMIT ?"
    p.append(getattr(a, "limit", 8))
    return c.execute(q, p).fetchall()


def cmd_query(a):
    c = con()
    rows = _rows(c, a)
    if not rows:
        print("(no sources match -- say so, do not invent one; try `fetch` for new candidates)")
        return
    out = []
    for r in rows:
        mark = "" if r[7] == "verified" else "?"
        out.append(f"#{r[0]} t{r[4]} {mark}{r[1]} [{r[3]}/{r[5]}/{r[6]}] {r[2]}\n    FOR: {r[8]}")
        if a.full:
            out.append(f"    WHY t{r[4]}: {r[9]}")
    txt = "\n".join(out)
    print(txt)
    hosts = {host(r[2]) for r in rows}
    print(f"-- {len(rows)} rows, {len(hosts)} distinct hosts, ~{tokens(txt)} tokens. "
          f"'?' = URL unverified, confirm before citing.")


def cmd_add(a):
    c = con()
    if a.tier not in TIERS:
        sys.exit("tier must be 1-4")
    if a.state not in STATES:
        sys.exit(f"state must be one of {STATES}")
    try:
        c.execute("INSERT INTO sources(name,url,domain,tier,lang,region,state,"
                  "authoritative_for,why,chain,added) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                  (a.name, a.url, a.domain, a.tier, a.lang, a.region, a.state,
                   getattr(a, "for_"), a.why, a.chain, today()))
    except sqlite3.IntegrityError:
        sys.exit(f"already registered: {a.url}")
    sid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    log(c, "add", a.url); c.commit()
    print(f"source {sid}  t{a.tier}  {a.name}  [{a.state}]")


# ------------------------------------------------------------------ check
# Deterministic signals only. This is NOT a truth oracle: it scores the
# structural markers the rubric names, prints every reason, and says out loud
# what a human or a fetch still has to confirm.
TLD_PRIMARY = (".gov", ".gov.jo", ".gov.uk", ".europa.eu", ".int", ".mil", ".un.org")
EDU = (".edu", ".ac.uk", ".edu.jo", ".ac.", ".uni-")
KNOWN_T1 = ("who.int", "nih.gov", "cdc.gov", "fda.gov", "ema.europa.eu", "eur-lex.europa.eu",
            "iso.org", "ietf.org", "rfc-editor.org", "w3.org", "nist.gov", "ieee.org",
            "imf.org", "worldbank.org", "oecd.org", "un.org", "wto.org", "wipo.int",
            "bis.org", "ecb.europa.eu", "federalreserve.gov", "bls.gov", "census.gov",
            "eurostat.ec.europa.eu", "dos.gov.jo", "cbj.gov.jo", "moh.gov.jo",
            "clinicaltrials.gov", "cve.org", "nvd.nist.gov", "first.org", "cisa.gov")
KNOWN_T2 = ("nature.com", "science.org", "thelancet.com", "nejm.org", "bmj.com", "cell.com",
            "pnas.org", "jamanetwork.com", "cochranelibrary.com", "pubmed.ncbi.nlm.nih.gov",
            "arxiv.org", "acm.org", "springer.com", "sciencedirect.com", "wiley.com",
            "jstor.org", "plos.org", "elifesciences.org", "nber.org", "brookings.edu")
KNOWN_T3 = ("reuters.com", "apnews.com", "ft.com", "economist.com", "bbc.com", "nytimes.com",
            "wsj.com", "theguardian.com", "aljazeera.net", "arabnews.com", "bloomberg.com",
            "arstechnica.com", "theverge.com", "ieee.org", "developer.mozilla.org")
KNOWN_T4 = ("wikipedia.org", "reddit.com", "medium.com", "substack.com", "quora.com",
            "stackoverflow.com", "news.ycombinator.com", "x.com", "twitter.com",
            "linkedin.com", "youtube.com", "blogspot.com", "wordpress.com")
AGGREGATOR_PATH = ("/blog", "/news", "/press-release", "/opinion", "/sponsored")


def assess(url, name="", domain=""):
    """Returns (tier_or_None, verdict, reasons[], open_questions[])."""
    h = host(url)
    reasons, opens = [], []
    tier = None
    if not url.startswith(("http://", "https://")):
        return None, "reject", ["not an http(s) URL"], []
    if url.startswith("http://"):
        reasons.append("plain http, no TLS -- weak custody signal, verify the canonical https origin")
    hit = lambda tbl: next((k for k in tbl if h == k or h.endswith("." + k)), None)
    k1, k2, k3, k4 = hit(KNOWN_T1), hit(KNOWN_T2), hit(KNOWN_T3), hit(KNOWN_T4)
    if k1:
        tier, = (1,); reasons.append(f"host matches a known primary/official register ({k1})")
    elif any(h.endswith(t) or t in h for t in TLD_PRIMARY):
        tier = 1; reasons.append("government / IGO domain: publishes the record itself")
    elif k2:
        tier = 2; reasons.append(f"host matches a known peer-reviewed or institutional publisher ({k2})")
    elif any(e in h for e in EDU):
        tier = 2; reasons.append("academic domain: institutional review, but a personal page on one is not peer review")
        opens.append("is this an institutional page or an individual's homepage? tier 2 only for the former")
    elif k3:
        tier = 3; reasons.append(f"host matches reputable press / vendor docs ({k3})")
    elif k4:
        tier = 4; reasons.append(f"host is an aggregator, encyclopaedia or user-generated platform ({k4}) -- "
                                 "use it to FIND the primary, never as the citation")
    else:
        reasons.append("host is not in the known table -- tier cannot be assigned from structure alone")
        opens.append("who publishes it, who funds it, is there a named author and a corrections policy?")
    if re.match(r"https?://[^/]+/?$", url):
        reasons.append("bare homepage: a homepage states no fact; the deep link to the page is required")
        opens.append("replace with the deep link that carries the claim")
    low = (url + " " + name).lower()
    if any(p in low for p in AGGREGATOR_PATH):
        reasons.append("path looks like blog/news/PR: even on a tier-1 host, a press release is the "
                       "organisation's own account, not an independent one")
    if any(w in low for w in ("press-release", "prnewswire", "businesswire", "sponsored")):
        tier = max(tier or 3, 3); reasons.append("wire/PR distribution: the subject wrote it; treat as a self-claim")
    verdict = ("accept" if tier and tier <= 2 else
               "accept-with-care" if tier == 3 else
               "reject-as-citation" if tier == 4 else "unsure")
    if tier is None:
        opens.append("run `fetch` (WebSearch/WebFetch) or ask the owner before citing")
    opens.append("independence: does it share an author, funder or wire feed with your other source?")
    opens.append("recency: is this inside the decay window for its field (see RUBRIC.md §5)?")
    return tier, verdict, reasons, opens


def cmd_check(a):
    c = con()
    known = c.execute("SELECT id,tier,state,authoritative_for FROM sources WHERE url=?", (a.url,)).fetchone()
    h = host(a.url)
    same = c.execute("SELECT id,name,tier FROM sources WHERE url LIKE ?", (f"%{h}%",)).fetchall()
    tier, verdict, reasons, opens = assess(a.url, a.name or "", a.domain or "")
    print(f"URL     {a.url}")
    print(f"HOST    {h}")
    if known:
        print(f"KNOWN   already registered as #{known[0]} tier {known[1]} [{known[2]}] -- FOR: {known[3]}")
    elif same:
        print("KNOWN   same host already registered: " + ", ".join(f"#{i} t{t} {n}" for i, n, t in same[:3]))
    print(f"TIER    {tier if tier else '?'}  {TIERS.get(tier, 'not assignable from structure')}")
    print(f"VERDICT {verdict}")
    for r in reasons:
        print(f"  + {r}")
    print("MUST STILL BE CONFIRMED (the script cannot):")
    for o in opens:
        print(f"  ? {o}")
    print("NOTE    a tier is authority FOR A DOMAIN, not in general. "
          "Prestige is not authority for this specific claim (RUBRIC.md §6).")


def cmd_candidate(a):
    c = con()
    try:
        c.execute("INSERT INTO candidates(name,url,domain,tier,verdict,reasons,"
                  "authoritative_for,found) VALUES(?,?,?,?,?,?,?,?)",
                  (a.name, a.url, a.domain, a.tier, a.verdict, a.reasons,
                   getattr(a, "for_", None), today()))
    except sqlite3.IntegrityError:
        sys.exit(f"candidate already recorded: {a.url}")
    cid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
    log(c, "candidate", f"{a.url} {a.verdict}"); c.commit()
    print(f"candidate {cid}  {a.verdict}  t{a.tier}  {a.name}")


def cmd_candidates(a):
    c = con()
    q = "SELECT id,name,url,domain,tier,verdict,reasons FROM candidates WHERE promoted=0"
    p = []
    if a.status:
        q += " AND verdict=?"; p.append(a.status)
    rows = c.execute(q + " ORDER BY tier,id", p).fetchall()
    for r in rows:
        print(f"#{r[0]} t{r[4]} {r[5]} {r[1]} [{r[3]}] {r[2]}\n    {r[6]}")
    print(f"-- {len(rows)} candidates")


def cmd_promote(a):
    c = con()
    r = c.execute("SELECT name,url,domain,tier,verdict,reasons,authoritative_for "
                  "FROM candidates WHERE id=?", (a.id,)).fetchone()
    if not r:
        sys.exit("no such candidate")
    if r[4] not in ("accept", "accept-with-care"):
        sys.exit(f"GATE FAIL: verdict is '{r[4]}' -- only accept / accept-with-care may be promoted.")
    try:
        c.execute("INSERT INTO sources(name,url,domain,tier,lang,region,state,"
                  "authoritative_for,why,added) VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (r[0], r[1], r[2], r[3], a.lang, a.region, "verified",
                   r[6] or "(not stated)", f"{r[5]} -- promoted by {a.by} on {today()}", today()))
    except sqlite3.IntegrityError:
        sys.exit("already in the registry")
    c.execute("UPDATE candidates SET promoted=1 WHERE id=?", (a.id,))
    log(c, "promote", f"{r[1]} by {a.by}"); c.commit()
    print(f"promoted {r[1]} -> registry (tier {r[3]}, verified)")


def cmd_export(a):
    c = con()
    rows = _rows(c, a)
    out = a.out or os.path.join(os.getcwd(), f"research-{re.sub(r'[^a-zA-Z0-9]+', '-', a.topic or a.domain or 'all')[:40]}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# Research checkpoint -- {a.topic or a.domain} -- {today()}\n\n")
        f.write("Sources selected from the nj-researcher registry. `?` = URL not confirmed "
                "this session; confirm before citing. Tier meaning: RUBRIC.md.\n\n")
        for r in rows:
            mark = "" if r[7] == "verified" else "? "
            f.write(f"## {mark}{r[1]} (tier {r[4]})\n- {r[2]}\n- domain: {r[3]} | lang: {r[5]} | region: {r[6]}\n"
                    f"- authoritative for: {r[8]}\n- why this tier: {r[9]}\n\n")
        hosts = sorted({host(r[2]) for r in rows})
        f.write(f"## Independence\n{len(rows)} sources across {len(hosts)} hosts: {', '.join(hosts)}\n\n"
                "Two rows on the same host, or two that republish one wire/press release, are ONE source.\n\n"
                "## Open questions\n- (fill: what could not be verified)\n")
    print(f"wrote {out}  ({len(rows)} sources)")


def cmd_cost(a):
    c = con()
    rows = _rows(c, a)
    body = "\n".join(f"#{r[0]} t{r[4]} {r[1]} [{r[3]}] {r[2]} FOR: {r[8]}" for r in rows)
    whole = "\n".join(f"{r[1]} {r[2]} {r[8]} {r[9]}" for r in
                      c.execute("SELECT id,name,url,domain,tier,lang,region,state,authoritative_for,why FROM sources"))
    print(f"lookup '{a.topic}': {len(rows)} rows, ~{tokens(body)} tokens")
    print(f"whole registry in context: ~{tokens(whole)} tokens")
    if tokens(body):
        print(f"saving: {tokens(whole) // max(tokens(body), 1)}x")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("init").set_defaults(f=cmd_init)
    x = sp.add_parser("seed"); x.add_argument("--file"); x.add_argument("--reset", action="store_true")
    x.set_defaults(f=cmd_seed)
    sp.add_parser("stats").set_defaults(f=cmd_stats)
    for nm, fn in (("query", cmd_query), ("export", cmd_export)):
        x = sp.add_parser(nm)
        x.add_argument("--topic"); x.add_argument("--domain"); x.add_argument("--tier", type=int)
        x.add_argument("--lang"); x.add_argument("--region")
        x.add_argument("--limit", type=int, default=8)
        x.add_argument("--full", action="store_true")
        if nm == "export":
            x.add_argument("--out")
        x.set_defaults(f=fn)
    x = sp.add_parser("cost"); x.add_argument("--topic", required=True); x.add_argument("--domain")
    x.add_argument("--tier", type=int); x.add_argument("--lang"); x.add_argument("--region")
    x.add_argument("--limit", type=int, default=8); x.set_defaults(f=cmd_cost)
    x = sp.add_parser("add")
    x.add_argument("--name", required=True); x.add_argument("--url", required=True)
    x.add_argument("--domain", required=True); x.add_argument("--tier", type=int, required=True)
    x.add_argument("--lang", default="en"); x.add_argument("--region", default="global")
    x.add_argument("--state", default="unverified"); x.add_argument("--chain")
    x.add_argument("--for", dest="for_", required=True); x.add_argument("--why", required=True)
    x.set_defaults(f=cmd_add)
    x = sp.add_parser("check"); x.add_argument("--url", required=True)
    x.add_argument("--name"); x.add_argument("--domain"); x.set_defaults(f=cmd_check)
    x = sp.add_parser("candidate")
    x.add_argument("--name", required=True); x.add_argument("--url", required=True)
    x.add_argument("--domain", required=True); x.add_argument("--tier", type=int, required=True)
    x.add_argument("--verdict", required=True, choices=["accept", "accept-with-care", "reject-as-citation", "unsure"])
    x.add_argument("--reasons", required=True); x.add_argument("--for", dest="for_")
    x.set_defaults(f=cmd_candidate)
    x = sp.add_parser("candidates"); x.add_argument("--status"); x.set_defaults(f=cmd_candidates)
    x = sp.add_parser("promote"); x.add_argument("id", type=int); x.add_argument("--by", required=True)
    x.add_argument("--lang", default="en"); x.add_argument("--region", default="global")
    x.set_defaults(f=cmd_promote)
    a = ap.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
