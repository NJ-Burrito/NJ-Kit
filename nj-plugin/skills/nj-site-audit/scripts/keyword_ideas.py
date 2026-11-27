#!/usr/bin/env python3
"""Free keyword ideas from search-box autocomplete. Standard library only.

  python keyword_ideas.py --seed "desktop icons" --lang en --country us --depth 1
  python keyword_ideas.py --seed "ram cleaner" --seed "windows memory cleaner" --md out.md --json out.json

HONEST LIMIT: these are autocomplete suggestions, NOT search volumes. The score is a relative
signal (how often a phrase recurs across expansions and sources, how high it ranks, how clear its
intent is). Search volume is not visits; measure in Search Console 4-8 weeks after indexing.
Sources: Google suggest, with Bing and DuckDuckGo as fallbacks. Polite: one request at a time with a delay.
"""
import argparse, collections, json, os, random, re, sys, time
import urllib.parse, urllib.request

UA = "Mozilla/5.0 (compatible; nj-keyword-ideas/1.0)"
QW = {"en": ["what", "how", "why", "can", "does", "is", "best", "free", "vs", "for", "to", "without", "alternative", "template", "online"],
      "ar": ["كيف", "ما", "لماذا", "هل", "افضل", "مجانا", "تحميل", "طريقة", "برنامج", "بدون"]}
ALPHA = {"en": "abcdefghijklmnopqrstuvwxyz", "ar": "ابتثجحخدذرزسشصضطظعغفقكلمنهوي"}
INTENT = [("question", r"^(what|how|why|can|does|is|are|when|where|which|كيف|ما|لماذا|هل|متى|اين)\b|\?"),
          ("comparison", r"\b(vs|versus|alternative|alternatives|compare|مقابل|بديل)\b"),
          ("transactional", r"\b(free|download|buy|price|template|tool|software|online|مجانا|تحميل|برنامج|نموذج|قالب)\b"),
          ("best-of", r"\b(best|top|افضل)\b")]
STOP = set("a an the of to in on for and or is are with without my your how what why can does do i it vs".split())


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def suggest(q, lang, country):
    """Return (source, [phrases]) trying Google, then Bing, then DuckDuckGo."""
    enc = urllib.parse.quote(q)
    tries = [("google", f"https://suggestqueries.google.com/complete/search?client=firefox&hl={lang}&gl={country}&q={enc}", lambda d: d[1]),
             ("bing", f"https://api.bing.com/osjson.aspx?query={enc}&mkt={lang}-{country.upper()}", lambda d: d[1]),
             ("duckduckgo", f"https://duckduckgo.com/ac/?q={enc}&type=list&kl={country}-{lang}", lambda d: d[1])]
    for name, url, pick in tries:
        try:
            out = [s for s in pick(fetch(url)) if isinstance(s, str)]
            if out:
                return name, out
        except Exception:
            continue
    return None, []


def expansions(seed, lang, depth_level):
    qw, al = QW.get(lang, QW["en"]), ALPHA.get(lang, ALPHA["en"])
    qs = [seed]
    qs += [f"{w} {seed}" for w in qw] + [f"{seed} {w}" for w in qw]
    if depth_level == 1:
        qs += [f"{seed} {c}" for c in al]
    return qs


def intent_of(p):
    for name, rx in INTENT:
        if re.search(rx, p, re.I):
            return name
    return "informational"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", action="append", required=True)
    ap.add_argument("--lang", default="en")
    ap.add_argument("--country", default="us")
    ap.add_argument("--depth", type=int, default=1, help="0 seed only; 1 qualifiers + a-z; 2 also expands the top candidates")
    ap.add_argument("--max-requests", type=int, default=150)
    ap.add_argument("--delay", type=float, default=0.5)
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--md", dest="md_out")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    hits = collections.defaultdict(lambda: {"count": 0, "rank": 0.0, "sources": set()})
    reqs, failures, used = 0, 0, set()

    def ask(q):
        nonlocal reqs, failures
        if reqs >= a.max_requests:
            return
        reqs += 1
        src, out = suggest(q, a.lang, a.country)
        time.sleep(a.delay + random.random() * 0.3)
        if not src:
            failures += 1
            return
        used.add(src)
        for i, s in enumerate(out):
            s = " ".join(s.lower().split())
            h = hits[s]
            h["count"] += 1
            h["rank"] += 1.0 / (i + 1)
            h["sources"].add(src)

    seeds = [s.lower() for s in a.seed]
    for sd in seeds:
        qs = [sd] if a.depth == 0 else expansions(sd, a.lang, 1 if a.depth >= 1 else 0)
        for q in qs:
            ask(q)
    if a.depth >= 2 and hits:
        top = sorted(hits, key=lambda p: -(hits[p]["count"] + hits[p]["rank"]))[:12]
        for p in top:
            if p not in seeds:
                for q in expansions(p, a.lang, 0)[:8]:
                    ask(q)

    if not hits:
        print(f"NO RESULTS: {reqs} request(s), {failures} failed. Autocomplete endpoints may be blocked from this network.")
        return 1

    cand = []
    for p, h in hits.items():
        if p in seeds:
            continue
        bonus = {"question": 1.0, "comparison": 1.0, "transactional": 1.5, "best-of": 1.0, "informational": 0.0}[intent_of(p)]
        cand.append({"phrase": p, "score": round(h["count"] + h["rank"] + bonus + 0.5 * (len(h["sources"]) - 1), 2),
                     "seen": h["count"], "intent": intent_of(p), "sources": sorted(h["sources"])})
    cand.sort(key=lambda c: (-c["score"], c["phrase"]))

    seedtok = {t for s in seeds for t in re.findall(r"\w+", s)}
    freq = collections.Counter(t for c in cand for t in set(re.findall(r"\w+", c["phrase"])) if t not in seedtok and t not in STOP and len(t) > 2)
    clusters = collections.defaultdict(list)
    for c in cand:
        toks = [t for t in re.findall(r"\w+", c["phrase"]) if t in freq]
        head = max(toks, key=lambda t: (freq[t], -len(t))) if toks else "(seed variants)"
        c["cluster"] = head
        clusters[head].append(c)
    order = sorted(clusters, key=lambda k: -sum(x["score"] for x in clusters[k]))

    out = {"seeds": seeds, "lang": a.lang, "country": a.country, "requests": reqs, "failed_requests": failures,
           "sources_used": sorted(used), "note": "Autocomplete suggestions only. Scores are relative signals, NOT search volumes.",
           "candidates": cand[:a.top * 3], "clusters": {k: [c["phrase"] for c in clusters[k][:10]] for k in order[:15]}}
    md = [f"# Keyword ideas: {', '.join(seeds)} ({a.lang}-{a.country})", "",
          f"> Autocomplete suggestions from {', '.join(sorted(used))}; {reqs} requests, {failures} failed. "
          "Scores are relative signals (recurrence, rank, intent). **They are not search volumes**, and search volume is not visits. "
          "Pick one primary phrase per page; prefer specific low-competition phrases; measure in Search Console 4-8 weeks after indexing.", "",
          "| # | Phrase | Score | Intent | Seen |", "| --- | --- | --- | --- | --- |"]
    for i, c in enumerate(cand[:a.top], 1):
        md.append(f"| {i} | {c['phrase']} | {c['score']} | {c['intent']} | {c['seen']} |")
    md += ["", "## Clusters (by head term)", ""]
    for k in order[:15]:
        md.append(f"- **{k}**: " + "; ".join(c["phrase"] for c in clusters[k][:8]))
    text = "\n".join(md) + "\n"
    print(text)
    for path, body in ((a.md_out, text), (a.json_out, json.dumps(out, indent=2, ensure_ascii=False))):
        if path:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
