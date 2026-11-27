#!/usr/bin/env python3
"""nj-site-audit Group G (Search / SEO) audit. Standard library only.

  python seo_audit.py https://example.com/ [--family a,b | file] [--json out.json] [--md out.md]
  python seo_audit.py ./site-folder --base https://example.com/   # local folder

Exit 0 + "PASS", or exit 1 + "FAIL (n findings)". Severities: error, warn (both
count) and note (never counts). Free, no API keys, no paid tools.
"""
import argparse, json, mimetypes, os, re, shutil, struct, subprocess, sys, time
import urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

UA = "nj-seo-audit/1.0 (+free local audit)"
FAMILY_DEFAULT = {
    "qa-wrap": "https://nj-burrito.github.io/QA-Wrap/",
    "business-wrap": "https://nj-burrito.github.io/Business-Wrap/",
    "nj-kit": "https://nj-burrito.github.io/NJ-Kit/",
    "nj-whip": "https://nj-burrito.github.io/NJ-Whip/",
    "profile-wrap": "https://nj-burrito.github.io/Profile-Wrap/",
    "nj-flush": "https://nj-burrito.github.io/NJ-Flush/",
    "nj-sort": "https://nj-burrito.github.io/NJ-Sort/",
    "story-wrap": "https://nj-burrito.github.io/story-wrap/",
    "portfolio": "https://nj-burrito.github.io/",
}
GROUPS = {
    "G1": "Indexing and verification", "G2": "Title", "G3": "Meta description",
    "G4": "Canonical", "G5": "hreflang and language twins", "G6": "Open Graph / Twitter",
    "G7": "Structured data (JSON-LD)", "G8": "Headings", "G9": "Images and heavy media",
    "G10": "404 page", "G11": "Sitemap and robots", "G12": "llms.txt",
    "G13": "noindex leaks", "G14": "Family cross-links", "G15": "Page basics (lang, viewport)",
    "G16": "Generated pages (edit the source)", "G17": "Live deploy check",
}
PRACTICE = re.compile(r"/(try|demo|test|testing|staging|sandbox|playground|practice)(/|\.html|$)", re.I)


# ---------------------------------------------------------------- helpers
def norm(u):
    u = urllib.parse.urldefrag(u)[0]
    p = urllib.parse.urlsplit(u)
    path = re.sub(r"/index\.html?$", "/", p.path or "/")
    if len(path) > 1:
        path = path.rstrip("/")
    return urllib.parse.urlunsplit((p.scheme.lower(), p.netloc.lower(), path, p.query, ""))


def host_of(u):
    return urllib.parse.urlsplit(u).netloc.lower()


def image_size(b):
    """(width, height) for PNG/JPEG/GIF/WebP bytes, or None."""
    try:
        if b[:8] == b"\x89PNG\r\n\x1a\n" and b[12:16] == b"IHDR":
            return struct.unpack(">II", b[16:24])
        if b[:6] in (b"GIF87a", b"GIF89a"):
            return struct.unpack("<HH", b[6:10])
        if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
            kind = b[12:16]
            if kind == b"VP8X":
                return (1 + int.from_bytes(b[24:27], "little"), 1 + int.from_bytes(b[27:30], "little"))
            if kind == b"VP8L":
                bits = int.from_bytes(b[21:25], "little")
                return ((bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1)
            if kind == b"VP8 ":
                w, h = struct.unpack("<HH", b[26:30])
                return (w & 0x3FFF, h & 0x3FFF)
        if b[:2] == b"\xff\xd8":
            i = 2
            while i + 9 < len(b):
                if b[i] != 0xFF:
                    i += 1
                    continue
                m = b[i + 1]
                if m in (0xD8, 0x01) or 0xD0 <= m <= 0xD7:
                    i += 2
                    continue
                seg = struct.unpack(">H", b[i + 2:i + 4])[0]
                if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    h, w = struct.unpack(">HH", b[i + 5:i + 9])
                    return (w, h)
                i += 2 + seg
    except Exception:
        pass
    return None


class Resp:
    def __init__(s, status=0, headers=None, body=b"", url="", length=0, error=""):
        s.status, s.headers, s.body, s.url, s.length, s.error = status, headers or {}, body, url, length, error

    @property
    def ctype(s):
        return s.headers.get("content-type", "").lower()

    def text(s):
        return s.body.decode("utf-8", "replace")


class HttpSource:
    local = False

    def __init__(s, base, timeout=20, delay=0.05):
        s.base, s.timeout, s.delay, s.cache = base, timeout, delay, {}
        s.host = host_of(base)

    def get(s, url, limit=2_000_000, method="GET"):
        key = (url, limit, method)
        if key in s.cache:
            return s.cache[key]
        p = urllib.parse.urlsplit(url)
        safe = urllib.parse.urlunsplit((p.scheme, p.netloc.encode("idna").decode(),
                                        urllib.parse.quote(p.path, safe="/%:@&=+$,;~*'()!"),
                                        urllib.parse.quote(p.query, safe="=&%+/:@,;"), ""))
        req = urllib.request.Request(safe, headers={"User-Agent": UA, "Accept": "*/*"}, method=method)
        time.sleep(s.delay)
        try:
            r = urllib.request.urlopen(req, timeout=s.timeout)
            st, hd, fin = r.status, {k.lower(): v for k, v in r.headers.items()}, r.geturl()
            body = r.read(limit) if method != "HEAD" else b""
        except urllib.error.HTTPError as e:
            st, hd, fin = e.code, {k.lower(): v for k, v in e.headers.items()}, url
            body = b"" if method == "HEAD" else e.read(limit)
        except Exception as e:  # network down, DNS, TLS
            out = Resp(0, {}, b"", url, 0, str(e))
            s.cache[key] = out
            return out
        ln = int(hd["content-length"]) if hd.get("content-length", "").isdigit() else len(body)
        out = Resp(st, hd, body, fin, ln)
        s.cache[key] = out
        return out


class FolderSource:
    local = True

    def __init__(s, root, base):
        s.root, s.base = os.path.abspath(root), base
        s.host = host_of(base)
        s.bpath = urllib.parse.urlsplit(base).path or "/"
        if not s.bpath.endswith("/"):
            s.bpath += "/"

    def file_for(s, url):
        p = urllib.parse.urlsplit(url)
        if p.netloc.lower() != s.host:
            return None
        path = urllib.parse.unquote(p.path or "/")
        if path.startswith(s.bpath):
            rel = path[len(s.bpath):]
        elif s.bpath == "/":
            rel = path.lstrip("/")
        else:
            return None  # outside the folder's mount (host-root files of a project site)
        cands = [rel] if rel and not rel.endswith("/") else []
        cands += [os.path.join(rel, "index.html")]
        if rel and not rel.endswith("/") and "." not in os.path.basename(rel):
            cands.append(rel + ".html")
        for c in cands:
            f = os.path.normpath(os.path.join(s.root, c))
            if f.startswith(s.root) and os.path.isfile(f):
                return f
        return None

    def get(s, url, limit=2_000_000, method="GET"):
        if host_of(url) != s.host:
            return Resp(0, {}, b"", url, 0, "external host not fetched in folder mode")
        f = s.file_for(url)
        if not f:
            return Resp(404, {"content-type": "text/html"}, b"", url, 0)
        ct = mimetypes.guess_type(f)[0] or "application/octet-stream"
        if f.endswith(".html"):
            ct = "text/html"
        with open(f, "rb") as fh:
            body = fh.read(limit)
        return Resp(200, {"content-type": ct}, body if method != "HEAD" else b"", url, os.path.getsize(f))


class PageParser(HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True)
        s.title = None
        s.metas, s.links, s.heads, s.imgs, s.jsonld = [], [], [], [], []
        s.anchors, s.videos, s.comments, s.html_attrs = [], [], [], {}
        s._cur, s._buf, s._skip = None, [], 0

    def handle_starttag(s, tag, attrs):
        a = {k.lower(): (v if v is not None else "") for k, v in attrs}
        if tag == "html":
            s.html_attrs = a
        elif tag == "title" and s.title is None:
            s._cur, s._buf = "title", []
        elif tag == "meta":
            s.metas.append(a)
        elif tag == "link":
            s.links.append(a)
        elif tag == "img":
            s.imgs.append(a)
        elif tag == "video":
            s.videos.append(a)
        elif tag == "a" and "href" in a:
            s.anchors.append(a)
        elif re.fullmatch(r"h[1-6]", tag):
            s._cur, s._buf = tag, []
        elif tag == "script":
            if a.get("type", "").lower() == "application/ld+json":
                s._cur, s._buf = "ld", []
            else:
                s._skip += 1
        elif tag == "style":
            s._skip += 1

    def handle_endtag(s, tag):
        if tag == "title" and s._cur == "title":
            s.title = "".join(s._buf).strip()
            s._cur = None
        elif re.fullmatch(r"h[1-6]", tag) and s._cur == tag:
            s.heads.append((int(tag[1]), " ".join("".join(s._buf).split())))
            s._cur = None
        elif tag == "script":
            if s._cur == "ld":
                s.jsonld.append("".join(s._buf))
                s._cur = None
            elif s._skip:
                s._skip -= 1
        elif tag == "style" and s._skip:
            s._skip -= 1

    def handle_data(s, d):
        if s._cur:
            s._buf.append(d)

    def handle_comment(s, d):
        s.comments.append(d)

    def meta(s, key, attr="name"):
        for m in s.metas:
            if m.get(attr, "").lower() == key.lower():
                return m.get("content", "")
        return None

    def link(s, rel):
        return [l for l in s.links if rel in l.get("rel", "").lower().split()]


class Page:
    def __init__(s, url, resp):
        s.url, s.resp, s.status = url, resp, resp.status
        s.p = PageParser()
        s.nodes = []
        s.ok = resp.status == 200 and ("html" in resp.ctype or not resp.ctype)
        if s.ok:
            try:
                s.p.feed(resp.text())
                s.p.close()
            except Exception:
                pass
        s.lang = (s.p.html_attrs.get("lang") or "").lower()
        rb = (s.p.meta("robots") or "") + "," + resp.headers.get("x-robots-tag", "")
        s.noindex = "noindex" in rb.lower()


# ---------------------------------------------------------------- audit
class Audit:
    def __init__(self, src, start, family=None, max_pages=40, google_file=None,
                 lang_pairs=True, pages_repo=None, workflow="pages", expect_title=None):
        self.src, self.start = src, start
        self.family = family or {}
        self.max_pages, self.google_file = max_pages, google_file
        self.lang_pairs, self.pages_repo, self.workflow, self.expect_title = lang_pairs, pages_repo, workflow, expect_title
        sp = urllib.parse.urlsplit(start)
        self.root = f"{sp.scheme}://{sp.netloc}/"
        d = sp.path if sp.path.endswith("/") else sp.path.rsplit("/", 1)[0] + "/"
        self.prefix = f"{sp.scheme}://{sp.netloc}{d}"
        self.findings, self.pages, self.pcache = [], {}, {}
        self.sitemaps, self.sitemap_urls = [], set()
        self.generators = set()
        self.verify = {"file": None, "meta": False}

    # -- plumbing
    def add(self, code, sev, url, msg):
        self.findings.append({"code": code, "sev": sev, "url": url, "msg": msg})

    def in_scope(self, u):
        if host_of(u) != host_of(self.start):
            return False
        return norm(u) == norm(self.prefix) or norm(u).startswith(norm(self.prefix).rstrip("/") + "/")

    def page(self, url):
        k = norm(url)
        if k not in self.pcache:
            self.pcache[k] = Page(url, self.src.get(url))
        return self.pcache[k]

    def siblings(self):
        own = norm(self.prefix)
        return {n: u for n, u in self.family.items() if norm(u) != own and norm(u) != norm(self.start)}

    def short(self, u):
        return u.replace(self.root, "/") if u.startswith(self.root) else u

    # -- discovery
    def get_robots(self):
        if not hasattr(self, "_robots"):
            self._robots, self._robots_url = None, self.root + "robots.txt"
            for u in (self.root + "robots.txt", self.prefix + "robots.txt"):
                r = self.src.get(u)
                if r.status == 200 and "html" not in r.ctype:
                    self._robots, self._robots_url = r.text(), u
                    break
        return self._robots

    def load_sitemaps(self):
        cands = [self.root + "sitemap.xml", self.prefix + "sitemap.xml"]
        rb = self.get_robots()
        if rb is not None:
            cands = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", rb) + cands
        seen, queue = set(), list(dict.fromkeys(cands))
        while queue and len(seen) < 40:
            u = queue.pop(0)
            if u in seen:
                continue
            seen.add(u)
            r = self.src.get(u)
            if r.status != 200:
                continue
            try:
                root = ET.fromstring(r.body)
            except ET.ParseError as e:
                self.add("G11", "error", u, f"sitemap is not valid XML ({e})")
                continue
            tag = root.tag.split("}")[-1]
            locs = [(e.text or "").strip() for e in root.iter() if e.tag.split("}")[-1] == "loc"]
            self.sitemaps.append(u)
            if tag == "sitemapindex":
                queue += locs
            else:
                self.sitemap_urls.update(locs)

    def crawl(self):
        self.load_sitemaps()
        queue = [self.start] + [u for u in sorted(self.sitemap_urls) if self.in_scope(u)]
        seen = set()
        while queue and len(self.pages) < self.max_pages:
            u = queue.pop(0)
            k = norm(u)
            if k in seen:
                continue
            seen.add(k)
            pg = self.page(u)
            if not pg.ok:
                if k == norm(self.start):
                    self.add("G11", "error", u, f"start page did not return HTML 200 (status {pg.status} {pg.resp.error})")
                continue
            self.pages[k] = pg
            for a in pg.p.anchors:
                h = a["href"].strip()
                if not h or h.startswith(("mailto:", "tel:", "javascript:", "#")):
                    continue
                t = urllib.parse.urljoin(u, h)
                path = urllib.parse.urlsplit(t).path
                if self.in_scope(t) and (path.endswith(("/", ".html")) or "." not in path.rsplit("/", 1)[-1]):
                    queue.append(t)

    # -- checks
    def run(self):
        self.crawl()
        if not self.pages:
            if not any("start page" in f["msg"] for f in self.findings):
                self.add("G11", "error", self.start, "no HTML page could be read")
            return self
        self.check_indexing()
        titles, descs = {}, {}
        for pg in self.pages.values():
            self.check_page(pg)
            titles.setdefault((pg.p.title or "").strip().lower(), []).append(pg.url)
            descs.setdefault((pg.p.meta("description") or "").strip().lower(), []).append(pg.url)
        for t, us in titles.items():
            if t and len(us) > 1:
                self.add("G2", "warn", us[0], f"same title on {len(us)} pages: {', '.join(self.short(x) for x in us[:4])}")
        for d, us in descs.items():
            if d and len(us) > 1:
                self.add("G3", "warn", us[0], f"same description on {len(us)} pages: {', '.join(self.short(x) for x in us[:4])}")
        self.check_jsonld_ids()
        self.check_hreflang()
        self.check_404()
        self.check_sitemap_robots()
        self.check_llms()
        self.check_noindex()
        self.check_family()
        self.check_generators()
        self.check_live()
        return self

    def check_indexing(self):
        sp = self.pages[norm(self.start)]
        meta = [m for m in sp.p.metas if m.get("name", "").lower() == "google-site-verification" and m.get("content")]
        self.verify["meta"] = bool(meta)
        cand = set()
        if self.google_file:
            cand.add(urllib.parse.urljoin(self.root, self.google_file))
        links = [urllib.parse.urljoin(pg.url, a["href"]) for pg in self.pages.values() for a in pg.p.anchors]
        for u in list(self.sitemap_urls) + links:
            if re.search(r"/google[0-9a-f]{8,}\.html$", urllib.parse.urlsplit(u).path):
                cand.add(u)
        if self.src.local:
            for fn in os.listdir(self.src.root):
                if re.fullmatch(r"google[0-9a-f]{8,}\.html", fn):
                    cand.add(urllib.parse.urljoin(self.src.base, fn))
        # also probe the verification file of the host root named in sitemap-less sites via robots? not guessable
        for u in cand:
            r = self.src.get(u)
            if r.status == 200 and "google-site-verification" in r.text():
                self.verify["file"] = u
                break
        if not self.verify["file"] and not self.verify["meta"]:
            if cand:
                self.add("G1", "error", self.root, "a google*.html verification file is referenced but does not answer 200 with its google-site-verification line")
            else:
                self.add("G1", "warn", self.root,
                         "no google-site-verification meta and no google*.html file found; if the file exists, pass --google-file NAME "
                         "(its name cannot be guessed). Never report 'not verified' on the meta alone")
        self.add("G1", "note", self.root,
                 f"verification: file={self.verify['file'] or 'not found'}, meta={'yes' if self.verify['meta'] else 'no'}; "
                 "index status has no free API: use the Search Console checklist at the end")

    def check_page(self, pg):
        u, p = pg.url, pg.p
        if not pg.lang:
            self.add("G15", "warn", u, "<html> has no lang attribute")
        elif "/ar/" in urllib.parse.urlsplit(u).path and not pg.lang.startswith("ar"):
            self.add("G15", "warn", u, f"/ar/ page has lang=\"{pg.lang}\", expected ar")
        if not p.meta("viewport"):
            self.add("G15", "warn", u, "no viewport meta")
        t = (p.title or "").strip()
        if not t:
            self.add("G2", "error", u, "missing <title>")
        elif len(t) > 60:
            self.add("G2", "warn", u, f"title is {len(t)} chars (> 60): \"{t[:70]}\"")
        elif len(t) < 15:
            self.add("G2", "warn", u, f"title is only {len(t)} chars: \"{t}\"")
        d = (p.meta("description") or "").strip()
        if not d:
            self.add("G3", "error", u, "missing meta description")
        elif not 70 <= len(d) <= 160:
            self.add("G3", "warn", u, f"description is {len(d)} chars (want 70-160): \"{d[:60]}\"")
        can = p.link("canonical")
        if not can or not can[0].get("href"):
            self.add("G4", "warn", u, "no <link rel=canonical>")
        else:
            h = can[0]["href"].strip()
            if not re.match(r"https?://", h):
                self.add("G4", "warn", u, f"canonical is not absolute: {h}")
            else:
                if host_of(h) != host_of(self.start) and not self.src.local:
                    self.add("G4", "warn", u, f"canonical points to another host: {h}")
                elif norm(h) != norm(u):
                    self.add("G4", "warn", u, f"canonical ({h}) is not this page's own URL")
                r = self.src.get(h, limit=1)
                if r.status not in (200, 0):
                    self.add("G4", "error", u, f"canonical {h} answers {r.status}")
        self.check_social(pg)
        self.parse_jsonld(pg)
        h1 = [h for h in p.heads if h[0] == 1]
        if len(h1) != 1:
            self.add("G8", "warn", u, f"{len(h1)} <h1> elements (want exactly 1)")
        prev = 0
        for lv, tx in p.heads:
            if prev and lv > prev + 1:
                self.add("G8", "warn", u, f"heading order jumps h{prev} -> h{lv} (\"{tx[:40]}\")")
                break
            prev = lv
        noalt = [i.get("src", "?") for i in p.imgs if "alt" not in i]
        nodim = [i.get("src", "?") for i in p.imgs if i.get("src") and not (i.get("width") and i.get("height"))]
        if noalt:
            self.add("G9", "warn", u, f"{len(noalt)} <img> without alt: {', '.join(noalt[:3])}")
        if nodim:
            self.add("G9", "warn", u, f"{len(nodim)} <img> without width+height (layout shift): {', '.join(nodim[:3])}")
        if any(not v.get("poster") for v in p.videos):
            self.add("G9", "warn", u, "<video> without poster")
        for i in p.imgs:
            s = i.get("src", "")
            if s.lower().split("?")[0].endswith(".gif"):
                r = self.src.get(urllib.parse.urljoin(u, s), limit=1024)
                if r.length > 1_000_000:
                    self.add("G9", "warn", u, f"GIF {s} is {r.length/1e6:.1f} MB: use mp4/webm with a poster image")
        g = p.meta("generator")
        if g:
            self.generators.add(f"{self.short(u)}: meta generator \"{g}\"")
        for c in p.comments:
            if re.search(r"generated|do not edit|auto-?generated", c, re.I):
                self.generators.add(f"{self.short(u)}: comment \"{' '.join(c.split())[:60]}\"")
                break

    def check_social(self, pg):
        u, p = pg.url, pg.p
        og = {m.get("property", "").lower(): m.get("content", "") for m in p.metas if m.get("property")}
        tw = {m.get("name", "").lower(): m.get("content", "") for m in p.metas if m.get("name", "").lower().startswith("twitter:")}
        miss = [k for k in ("og:title", "og:description", "og:image", "og:url", "og:type") if not og.get(k)]
        if miss:
            self.add("G6", "warn", u, f"missing {', '.join(miss)}")
        if not tw.get("twitter:card"):
            self.add("G6", "warn", u, "missing twitter:card")
        img = og.get("og:image") or tw.get("twitter:image")
        if not img:
            return
        iu = urllib.parse.urljoin(u, img)
        r = self.src.get(iu, limit=600_000)
        if r.status == 0:
            self.add("G6", "note", u, f"og:image {iu} not fetched ({r.error})")
        elif r.status != 200:
            self.add("G6", "error", u, f"og:image {iu} answers {r.status}")
        else:
            sz = image_size(r.body)
            w, h = og.get("og:image:width"), og.get("og:image:height")
            if sz:
                if sz[0] < 1200 or sz[1] < 630:
                    self.add("G6", "warn", u, f"og:image is {sz[0]}x{sz[1]}; want 1200x630 (a square logo crops badly)")
                elif not 1.6 <= sz[0] / sz[1] <= 2.1:
                    self.add("G6", "warn", u, f"og:image is {sz[0]}x{sz[1]} (ratio {sz[0]/sz[1]:.2f}); want about 1.91:1")
                if w and h and w.isdigit() and h.isdigit() and (int(w), int(h)) != tuple(sz):
                    self.add("G6", "warn", u, f"og:image:width/height say {w}x{h} but the file is {sz[0]}x{sz[1]}")
            elif iu.lower().split("?")[0].endswith(".svg"):
                self.add("G6", "warn", u, "og:image is SVG; most networks need PNG/JPEG")
            else:
                self.add("G6", "note", u, f"could not read pixel size of {iu}")
        if not og.get("og:image:alt"):
            self.add("G6", "warn", u, "missing og:image:alt")
        if not tw.get("twitter:image:alt"):
            self.add("G6", "warn", u, "missing twitter:image:alt")

    @staticmethod
    def types(n):
        t = n.get("@type")
        return t if isinstance(t, list) else [t]

    def parse_jsonld(self, pg):
        for raw in pg.p.jsonld:
            try:
                data = json.loads(raw)
            except Exception as e:
                self.add("G7", "error", pg.url, f"JSON-LD does not parse ({str(e)[:60]})")
                continue
            stack = [data]
            while stack:
                n = stack.pop()
                if isinstance(n, dict):
                    pg.nodes.append(n)
                    stack += [v for v in n.values() if isinstance(v, (dict, list))]
                elif isinstance(n, list):
                    stack += n
        if not pg.p.jsonld and norm(pg.url) == norm(self.start):
            self.add("G7", "warn", pg.url, "no JSON-LD structured data on the start page")
        sibs = self.siblings()
        for n in pg.nodes:
            if "Person" in self.types(n) and sibs and n.get("sameAs") is not None:
                same = n["sameAs"] if isinstance(n["sameAs"], list) else [n["sameAs"]]
                have = {norm(x) for x in same if isinstance(x, str)}
                miss = [nm for nm, su in sibs.items() if norm(su) not in have]
                if miss:
                    self.add("G7", "warn", pg.url, f"Person.sameAs does not list: {', '.join(miss)}")

    def check_jsonld_ids(self):
        seen = {}
        for pg in self.pages.values():
            for n in pg.nodes:
                i = n.get("@id")
                if not isinstance(i, str) or len(n) == 1 or any(x in ("Person", "Organization", "WebSite") for x in self.types(n)):
                    continue
                seen.setdefault(i, {})[pg.url] = (pg.lang or "?")[:2]
        for i, d in seen.items():
            if len(d) > 1 and len(set(d.values())) > 1:
                self.add("G7", "warn", list(d)[0], f"@id {i} is reused across languages ({', '.join(sorted(set(d.values())))}); give each language its own @id")

    def hreflang_map(self, pg):
        return {l.get("hreflang", "").lower(): urllib.parse.urljoin(pg.url, l.get("href", ""))
                for l in pg.p.links if "alternate" in l.get("rel", "").lower().split() and l.get("hreflang")}

    def twin_of(self, url):
        path = urllib.parse.urlsplit(url).path
        base = urllib.parse.urlsplit(self.prefix).path
        if "/ar/" in path or path.endswith("/ar"):
            return url.replace("/ar/", "/", 1) if "/ar/" in path else url[:-2]
        if url.startswith(self.prefix):
            return self.prefix + "ar/" + url[len(self.prefix):].lstrip("/")
        return None

    def check_hreflang(self):
        for pg in list(self.pages.values()):
            hm = self.hreflang_map(pg)
            if hm:
                if "x-default" not in hm:
                    self.add("G5", "warn", pg.url, "hreflang set has no x-default")
                if not any(norm(v) == norm(pg.url) for v in hm.values()):
                    self.add("G5", "warn", pg.url, "hreflang set does not include this page itself (self-reference)")
                for lang, tu in hm.items():
                    if norm(tu) == norm(pg.url):
                        continue
                    other = self.page(tu)
                    if not other.ok:
                        self.add("G5", "error", pg.url, f"hreflang {lang} -> {tu} answers {other.status}")
                    elif not any(norm(v) == norm(pg.url) for v in self.hreflang_map(other).values()):
                        self.add("G5", "error", pg.url, f"hreflang {lang} -> {tu} does not link back (not reciprocal)")
            if self.lang_pairs:
                twin = self.twin_of(pg.url)
                if twin and norm(twin) != norm(pg.url):
                    tp = self.page(twin)
                    if tp.ok:
                        if not hm:
                            self.add("G5", "warn", pg.url, f"language twin exists ({self.short(twin)}) but this page has no hreflang")
                        d1, d2 = (pg.p.meta("description") or "").strip(), (tp.p.meta("description") or "").strip()
                        if d1 and d1 == d2:
                            self.add("G3", "warn", pg.url, f"description is identical to its language twin {self.short(twin)} (untranslated)")

    def check_404(self):
        probe = self.prefix + "__nj_seo_probe_404__/"
        r = self.src.get(probe, limit=200_000)
        f = self.src.get(self.prefix + "404.html", limit=1)
        if r.status == 200:
            self.add("G10", "error", probe, "a nonexistent path answers 200 (soft 404; broken links hide)")
        elif r.status == 0:
            self.add("G10", "note", probe, f"404 probe not fetched ({r.error})")
        if f.status != 200:
            self.add("G10", "warn", self.prefix + "404.html", "no 404.html (a branded not-found page)")

    def check_sitemap_robots(self):
        rb = self.get_robots()
        if rb is None:
            self.add("G11", "warn", self.root + "robots.txt", "no robots.txt")
        else:
            cur_all = False
            for line in rb.splitlines():
                line = line.split("#")[0].strip()
                if re.match(r"(?i)user-agent:\s*\*", line):
                    cur_all = True
                elif re.match(r"(?i)user-agent:", line):
                    cur_all = False
                elif cur_all and re.fullmatch(r"(?i)disallow:\s*/", line):
                    self.add("G11", "error", self._robots_url, "robots.txt disallows the whole site for all crawlers")
            if not re.search(r"(?im)^\s*sitemap:", rb):
                self.add("G11", "warn", self._robots_url, "robots.txt has no Sitemap: line")
        if not self.sitemaps:
            self.add("G11", "error", self.root + "sitemap.xml", "no sitemap.xml (or sitemap index) found")
            return
        listed = {norm(u) for u in self.sitemap_urls}
        missing = [pg.url for k, pg in self.pages.items() if k not in listed and not pg.noindex and not PRACTICE.search(pg.url)]
        if missing:
            self.add("G11", "warn", self.sitemaps[0], f"{len(missing)} crawled page(s) not in any sitemap: {', '.join(self.short(x) for x in missing[:5])}")
        bad = []
        for u in sorted(self.sitemap_urls)[:120]:
            if self.src.local and host_of(u) != self.src.host:
                continue
            r = self.src.get(u, limit=1, method="GET" if self.src.local else "HEAD")
            if r.status in (403, 405):
                r = self.src.get(u, limit=1)
            if r.status not in (200, 0):
                bad.append(f"{u} ({r.status})")
        if bad:
            self.add("G11", "error", self.sitemaps[0], f"{len(bad)} sitemap URL(s) not 200: {'; '.join(bad[:4])}")

    def check_llms(self):
        for base in dict.fromkeys([self.root, self.prefix]):
            r = self.src.get(base + "llms.txt")
            if r.status == 200 and "html" not in r.ctype:
                bad = []
                for u in sorted(set(re.findall(r"https?://[^\s)\]>\"']+", r.text())))[:40]:
                    if host_of(u) != host_of(self.start):
                        continue
                    rr = self.src.get(u.rstrip(".,"), limit=1)
                    if rr.status not in (200, 0):
                        bad.append(f"{u} ({rr.status})")
                if bad:
                    self.add("G12", "error", base + "llms.txt", f"llms.txt lists URL(s) that fail: {'; '.join(bad[:4])}")
                return
        self.add("G12", "note", self.prefix + "llms.txt", "no llms.txt (optional)")

    def check_noindex(self):
        listed = {norm(u) for u in self.sitemap_urls}
        for k, pg in self.pages.items():
            if pg.noindex and k in listed:
                self.add("G13", "error", pg.url, "page is noindex but listed in the sitemap")
            if not pg.noindex and PRACTICE.search(urllib.parse.urlsplit(pg.url).path):
                self.add("G13", "warn", pg.url, "practice/try/demo page is indexable; add <meta name=robots content=noindex>")
        sp = self.pages.get(norm(self.start))
        if sp and sp.noindex:
            self.add("G13", "error", sp.url, "the start page itself is noindex")

    def check_family(self):
        sibs = self.siblings()
        if not sibs:
            self.add("G14", "note", self.start, "no --family given: cross-link check skipped")
            return
        targets = [self.pages[norm(self.start)]]
        ar = self.pages.get(norm(self.prefix + "ar/"))
        if ar and ar is not targets[0]:
            targets.append(ar)
        for pg in targets:
            links = {norm(urllib.parse.urljoin(pg.url, a["href"])) for a in pg.p.anchors}
            miss = []
            for n, su in sibs.items():
                ns = norm(su)
                isroot = urllib.parse.urlsplit(ns).path in ("", "/")
                if not any(l == ns or (not isroot and l.startswith(ns + "/")) for l in links):
                    miss.append(n)
            if miss:
                self.add("G14", "warn", pg.url, f"does not link to sibling site(s): {', '.join(miss)}")

    def check_generators(self):
        for g in sorted(self.generators):
            self.add("G16", "note", self.start, f"looks generated ({g}): find the generator/source and edit that, never the output")
        if self.src.local:
            for d in {self.src.root, os.path.dirname(self.src.root)}:
                try:
                    for fn in sorted(os.listdir(d)):
                        if re.fullmatch(r"(build|sync_links|generate|render|make)[\w-]*\.(py|mjs|js|ps1)", fn):
                            self.add("G16", "note", self.start, f"build/sync script present: {os.path.join(d, fn)}; if it writes these pages, fix it there")
                except OSError:
                    pass
        for pg in self.pages.values():
            if "/ar/" in urllib.parse.urlsplit(pg.url).path:
                self.add("G16", "note", pg.url, "Arabic twin pages are often written by a sync/build script; find it before editing by hand")
                break

    def check_live(self):
        if self.expect_title:
            sp = self.pages.get(norm(self.start))
            if sp and (sp.p.title or "").strip() != self.expect_title.strip():
                self.add("G17", "error", self.start, f"live title is \"{sp.p.title}\", expected \"{self.expect_title}\" (the deploy may not have run)")
        if self.pages_repo:
            gh = shutil.which("gh")
            if not gh:
                self.add("G17", "note", self.start, "gh CLI not found: check the Pages run by hand")
                return
            try:
                out = subprocess.run([gh, "run", "list", "--repo", self.pages_repo, "--workflow", self.workflow, "--limit", "1",
                                      "--json", "conclusion,status,displayTitle"], capture_output=True, text=True, timeout=60)
                runs = json.loads(out.stdout or "[]")
                if not runs:
                    self.add("G17", "warn", self.pages_repo, f"no runs for workflow '{self.workflow}' ({out.stderr.strip()[:80]})")
                elif runs[0].get("conclusion") != "success":
                    self.add("G17", "error", self.pages_repo, f"latest Pages run is {runs[0].get('status')}/{runs[0].get('conclusion')} "
                             f"({runs[0].get('displayTitle')}): rerun it; merged is not live")
            except Exception as e:
                self.add("G17", "note", self.pages_repo, f"could not query gh ({e})")

    # -- reporting
    def counted(self):
        return [f for f in self.findings if f["sev"] in ("error", "warn")]

    def checklist(self):
        sm = self.sitemaps[0] if self.sitemaps else self.root + "sitemap.xml"
        pages = list(dict.fromkeys(pg.url for pg in self.pages.values() if not pg.noindex))[:12]
        L = [f"Verification found: file={self.verify['file'] or 'none'}, meta={'yes' if self.verify['meta'] else 'no'} (either is enough).",
             f"Search Console > Sitemaps > submit: {sm}",
             "Search Console > URL inspection > Test live URL > Request indexing, one by one, for:"]
        L += [f"    {u}" for u in pages]
        L += ["Search Console > Pages: after a few days read 'Why pages aren't indexed' for each page.",
              "Measure clicks/impressions per query in Performance 4-8 weeks after indexing; search volume is not visits.",
              "After a merge: fetch the live page title over HTTP and check the Pages run (gh run list --workflow pages)."]
        return L

    def to_json(self):
        c = {}
        for f in self.counted():
            c[f["code"]] = c.get(f["code"], 0) + 1
        n = len(self.counted())
        return {"start": self.start, "pages_audited": [pg.url for pg in self.pages.values()], "sitemaps": self.sitemaps,
                "verification": self.verify, "findings": self.findings, "counts": c, "finding_total": n,
                "result": "PASS" if not n else f"FAIL ({n} findings)", "search_console_checklist": self.checklist()}

    def to_md(self):
        j = self.to_json()
        o = [f"# Search (SEO) audit: {self.start}", "", f"Result: **{j['result']}**. Pages audited: {len(self.pages)}.", "",
             "| Code | Check | Findings |", "| --- | --- | --- |"]
        for code, name in GROUPS.items():
            o.append(f"| {code} | {name} | {j['counts'].get(code, 0)} |")
        o += ["", "## Findings", "", "| Code | Severity | Where | Finding |", "| --- | --- | --- | --- |"]
        for f in self.findings:
            o.append(f"| {f['code']} | {f['sev']} | {self.short(f['url'])} | {f['msg'].replace('|', '/')} |")
        o += ["", "## Search Console checklist (no free API for index status)", ""]
        o += [f"- {x}" if not x.startswith("    ") else f"  - {x.strip()}" for x in j["search_console_checklist"]]
        o += ["", "Fix at the source: pages marked G16 may be generated; edit the generator, never the output."]
        return "\n".join(o) + "\n"


def load_family(spec):
    if not spec:
        return {}
    items = []
    if os.path.isfile(spec):
        for line in open(spec, encoding="utf-8"):
            line = line.split("#")[0].strip()
            if line:
                items.append(line)
    else:
        items = [x.strip() for x in spec.split(",") if x.strip()]
    fam = {}
    for it in items:
        if it.startswith("http"):
            fam[host_of(it) + urllib.parse.urlsplit(it).path] = it
        elif it.lower() in FAMILY_DEFAULT:
            fam[it.lower()] = FAMILY_DEFAULT[it.lower()]
        else:
            raise SystemExit(f"unknown family member '{it}' (use one of {sorted(FAMILY_DEFAULT)} or a full URL)")
    return fam


def audit_target(target, base=None, **kw):
    if os.path.isdir(target):
        base = base or "https://local.invalid/"
        if not base.endswith("/"):
            base += "/"
        return Audit(FolderSource(target, base), base, **kw).run()
    return Audit(HttpSource(target), target, **kw).run()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Group G (Search / SEO) audit for a live site or a local folder.")
    ap.add_argument("target", help="start URL, or a local folder")
    ap.add_argument("--base", help="public base URL when target is a folder (default https://local.invalid/)")
    ap.add_argument("--family", help="comma list of names/URLs, or a file with one per line")
    ap.add_argument("--max-pages", type=int, default=40)
    ap.add_argument("--google-file", help="name of the google*.html verification file, if known")
    ap.add_argument("--lang-pairs", action=argparse.BooleanOptionalAction, default=True, help="auto-detect /ar/ twins (default on)")
    ap.add_argument("--pages-repo", help="owner/repo: also check the latest GitHub Pages run (needs gh)")
    ap.add_argument("--workflow", default="pages")
    ap.add_argument("--expect-title", help="live start-page title that must match (post-merge check)")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--md", dest="md_out")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    au = audit_target(a.target, a.base, family=load_family(a.family), max_pages=a.max_pages, google_file=a.google_file,
                      lang_pairs=a.lang_pairs, pages_repo=a.pages_repo, workflow=a.workflow, expect_title=a.expect_title)
    j = au.to_json()
    print(f"Search audit: {au.start}  ({len(au.pages)} page(s))")
    print(f"{'code':<4} {'sev':<5} {'where':<34} finding")
    for f in au.findings:
        print(f"{f['code']:<4} {f['sev']:<5} {au.short(f['url'])[:34]:<34} {f['msg']}")
    print("\nSearch Console checklist:")
    for x in au.checklist():
        print("  " + x if not x.startswith("    ") else x)
    for path, text in ((a.json_out, json.dumps(j, indent=2, ensure_ascii=False)), (a.md_out, au.to_md())):
        if path:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
    print("\n" + j["result"])
    return 0 if not au.counted() else 1


if __name__ == "__main__":
    sys.exit(main())
