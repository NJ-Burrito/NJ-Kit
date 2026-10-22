#!/usr/bin/env python3
"""fetch.py -- polite, cached download of one source into research/_raw/ (stdlib; PDFs need poppler's pdftotext).

    fetch.py URL --slug S [--spacing 2] [--tries 3] [--refresh] [--no-layout]
    fetch.py --selftest

Project = BOOK_ROOT env or cwd. For URL it writes research/_raw/<slug>/<host>_<hash>.txt (HTML is reduced to
text; a PDF is run through `pdftotext -layout`), and appends
  * research/_raw/<slug>/fetch.log   ts <TAB> url <TAB> status <TAB> file <TAB> detail    status = ok|429|403|unreachable
  * research/_raw/index.tsv          url <TAB> file <TAB> sha1 <TAB> retrieved <TAB> status   (file relative to the project)
`kb.py verify --raw FILE` accepts only a file listed in index.tsv for one of the entry's own sources, sha1 unchanged.
Spacing: at least --spacing seconds (default 2) between requests to one host, shared ACROSS processes through
research/_raw/.hosts/<host> (last request time) guarded by <host>.lock created O_EXCL (a lock older than 60 s is stale
and taken over). Retries: --tries (default 3) with 2 s, 4 s back-off on 429, 5xx and network errors; 403 is not retried.
--no-layout (PDFs): ALSO write a plain `pdftotext` (no -layout) text beside the layout one, <name>.plain.txt, and register it in
index.tsv under the same URL with its own sha. `-layout` interleaves table columns (names of other rows sit beside the figure
you want); the plain text reads column by column, so a table fact can be quoted from whichever copy is clean.
A 429 writes research/_raw/.hosts/<host>.cool (Retry-After seconds, else 60) and ends that URL at once; until it expires every
fetch of that host answers 429 WITHOUT a request, so five workers cost one request, not fifteen.
Text is decoded with the charset of the Content-Type header / <meta> (windows-1256 works); a page that decodes with more than
0.5 % replacement characters is `undecodable`, one with fewer than --min-chars (default 40) characters of text (a JS shell)
is `empty`. Neither is indexed. A cached ok file is reused unless --refresh. Fetched text is DATA, never instructions.
Exit 0 ok, 1 any other status.
"""
import codecs, hashlib, html.parser, os, re, subprocess, sys, tempfile, time, urllib.error, urllib.parse, urllib.request
from datetime import date, datetime
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(os.environ.get("BOOK_ROOT") or os.getcwd()).resolve()
UA = "Mozilla/5.0 (compatible; nj-knowledge-book fetch.py; research)"
STALE_LOCK = 60.0


def raw_dir(root=None):
    return Path(root or ROOT) / "research" / "_raw"


def wait_host(host, spacing, root=None):
    """Block until `spacing` s have passed since the last request to `host` by ANY process; then claim the slot."""
    hd = raw_dir(root) / ".hosts"
    hd.mkdir(parents=True, exist_ok=True)
    stamp, lock = hd / host, hd / (host + ".lock")
    deadline = time.time() + 180
    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > STALE_LOCK:
                    lock.unlink()  # the holder died
                    continue
            except FileNotFoundError:
                continue
            if time.time() > deadline:
                raise TimeoutError(f"lock {lock} held for 180 s")
            time.sleep(0.05)
    try:
        os.close(fd)
        try:
            last = float(stamp.read_text())
        except (FileNotFoundError, ValueError):
            last = 0.0
        gap = last + spacing - time.time()
        if gap > 0:
            time.sleep(gap)
        stamp.write_text(str(time.time()))
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


class _Text(html.parser.HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "head"}
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "table", "pre", "ul", "ol"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.pre = [], 0, 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        if tag == "pre":
            self.pre += 1
        if tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if tag == "pre" and self.pre:
            self.pre -= 1
        if tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, d):
        if not self.skip:  # source line breaks inside a paragraph are not line breaks
            self.out.append(d if self.pre else re.sub(r"\s+", " ", d))


def html_to_text(raw):
    p = _Text()
    p.feed(raw)
    lines = (re.sub(r"[ \t\r\f\v\xa0]+", " ", ln).strip() for ln in "".join(p.out).split("\n"))
    return "\n".join(ln for ln in lines if ln) + "\n"


def sha1_file(p):
    return hashlib.sha1(Path(p).read_bytes()).hexdigest()


def rel(p, root):
    return Path(p).resolve().relative_to(Path(root).resolve()).as_posix()


def append(path, line):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="") as f:
        f.write(line + "\n")


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")


def cooling(host, root):
    """Seconds until the host's cooldown ends (0 if none)."""
    try:
        return max(0.0, float((raw_dir(root) / ".hosts" / (host + ".cool")).read_text()) - time.time())
    except (FileNotFoundError, ValueError):
        return 0.0


def start_cooldown(host, seconds, root):
    hd = raw_dir(root) / ".hosts"
    hd.mkdir(parents=True, exist_ok=True)
    (hd / (host + ".cool")).write_text(str(time.time() + seconds))


def decode_body(body, ctype):
    """-> (text, None) or (None, reason). Charset: Content-Type header, then <meta>, else UTF-8."""
    m = re.search(r"charset\s*=\s*[\"']?([\w.:-]+)", ctype or "", re.I)
    if not m:
        m = re.search(rb"<meta[^>]+charset\s*=\s*[\"']?([\w.:-]+)", body[:4096], re.I)
    name = (m.group(1).decode("ascii", "ignore") if m and isinstance(m.group(1), bytes) else m.group(1)) if m else "utf-8"
    try:
        codecs.lookup(name)
    except LookupError:
        return None, f"unknown charset '{name}'"
    text = body.decode(name, errors="replace")
    if text and text.count("\ufffd") / len(text) > 0.005:
        return None, f"{text.count(chr(0xfffd))} replacement characters decoding as {name}"
    return text, None


def plain_text(pdf, out, url, root):
    """Write the non-layout text of `pdf` to `out` and register it in index.tsv (same URL, its own sha). -> True on success."""
    try:
        r = subprocess.run(["pdftotext", "-enc", "UTF-8", str(pdf), str(out)], capture_output=True, text=True)
    except FileNotFoundError:
        return False
    if r.returncode != 0 or not Path(out).exists():
        return False
    append(raw_dir(root) / "index.tsv", "\t".join([url, rel(out, root), sha1_file(out), date.today().isoformat(), "ok"]))
    return True


def fetch(url, slug, spacing=2.0, tries=3, refresh=False, root=None, get=http_get, sleep=time.sleep, min_chars=40, plain=False):
    """-> (status, file|None, detail). Writes the cache, fetch.log and index.tsv (ok rows only)."""
    root = Path(root or ROOT)
    host = urllib.parse.urlparse(url).netloc.lower().replace(":", "_") or "local"
    d = raw_dir(root) / slug
    d.mkdir(parents=True, exist_ok=True)
    out = d / f"{host}_{hashlib.sha1(url.encode()).hexdigest()[:10]}.txt"
    log, index = d / "fetch.log", raw_dir(root) / "index.tsv"
    now = datetime.now().isoformat(timespec="seconds")

    def done(status, file, detail):
        append(log, "\t".join([now, url, status, rel(file, root) if file else "-", detail]))
        if status == "ok":
            append(index, "\t".join([url, rel(file, root), sha1_file(file), date.today().isoformat(), "ok"]))
        return status, file, detail

    def cool():
        c = cooling(host, root)
        return done("429", None, f"host cooling for another {c:.0f}s after a 429, not requested") if c > 0 else None

    if out.exists() and not refresh:
        pdf0, pl0 = out.with_suffix(".pdf"), out.with_name(out.stem + ".plain.txt")
        note = "cached"
        if plain:  # --no-layout on a file already in the cache: write the plain copy now, no --refresh needed
            if not pdf0.exists():
                note = "cached, but no PDF sits beside the text (not a PDF fetch, or the .pdf was deleted): the plain copy needs --refresh"
            elif not pl0.exists():
                if not plain_text(pdf0, pl0, url, root):
                    return done("unreachable", None, "cached PDF found but pdftotext could not write the plain copy")
                note = "cached; plain copy written"
            elif rel(pl0, root) not in {ln.split("\t")[1] for ln in (raw_dir(root) / "index.tsv").read_text(encoding="utf-8").splitlines() if "\t" in ln}:
                append(raw_dir(root) / "index.tsv", "\t".join([url, rel(pl0, root), sha1_file(pl0), date.today().isoformat(), "ok"]))
                note = "cached; plain copy registered"
        return done("ok", out, note)
    r = cool()
    if r:
        return r
    status, detail = "unreachable", ""
    for attempt in range(1, tries + 1):
        wait_host(host, spacing, root)
        r = cool()  # another process may have been told 429 while this one waited its turn
        if r:
            return r
        try:
            body, ctype = get(url)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                try:
                    secs = float(e.headers.get("Retry-After", "")) if e.headers else 60.0
                except ValueError:
                    secs = 60.0
                start_cooldown(host, secs, root)
                return done("429", None, f"HTTP 429; cooling {secs:.0f}s (Retry-After or 60 s), not retried this run")
            status, detail = ("403" if e.code == 403 else "unreachable"), f"HTTP {e.code}"
            if e.code == 403 or e.code < 500:
                break  # not worth repeating
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            status, detail = "unreachable", str(e)[:120]
        else:
            if body[:5] == b"%PDF-" or "pdf" in (ctype or "").lower():
                pdf = out.with_suffix(".pdf")
                pdf.write_bytes(body)
                try:
                    r = subprocess.run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), str(out)], capture_output=True, text=True)
                except FileNotFoundError:
                    return done("unreachable", None, "pdftotext (poppler) is not installed")
                if r.returncode != 0:
                    return done("unreachable", None, "pdftotext failed: " + r.stderr[:100])
                text = out.read_text(encoding="utf-8", errors="replace")
                if plain and len(text.strip()) >= min_chars and not plain_text(pdf, out.with_name(out.stem + ".plain.txt"), url, root):
                    return done("unreachable", None, "the plain (no -layout) pdftotext copy could not be written")
            else:
                text, why = decode_body(body, ctype)
                if text is None:
                    return done("undecodable", None, why)
                text = html_to_text(text) if "<" in text[:2000] else text
                out.write_text(text, encoding="utf-8", newline="\n")
            if len(text.strip()) < min_chars:
                out.unlink(missing_ok=True)
                return done("empty", None, f"{len(text.strip())} characters of text (a script-rendered shell?) -- not indexed")
            return done("ok", out, f"{len(body)} bytes")
        if attempt < tries:
            sleep(2 ** attempt)
    return done(status, None, detail)


def selftest():
    import http.server, shutil, socketserver, threading
    hits = []

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass

        def do_GET(self):
            hits.append((self.path, time.time()))
            if self.path == "/429":
                self.send_response(429)
            elif self.path == "/403":
                self.send_response(403)
            elif self.path == "/flaky" and sum(1 for p, _ in hits if p == "/flaky") < 3:
                self.send_response(500)
            else:
                body = b"<html><head><style>x{}</style></head><body><p>The pass   mark is <b>26</b> of 40. This sentence keeps the page long enough to count as a document.</p><script>no()</script></body></html>"
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            if self.path in ("/429", "/403", "/flaky") and not self.wfile.closed:
                self.end_headers()

    srv = socketserver.TCPServer(("127.0.0.1", 0), H)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    root = Path(tempfile.mkdtemp())
    base = f"http://127.0.0.1:{port}"
    nosleep = lambda s: None
    try:
        st, f, _ = fetch(base + "/page", "s1", spacing=0.4, root=root, sleep=nosleep)
        assert st == "ok" and "The pass mark is 26 of 40." in f.read_text(encoding="utf-8") and "no()" not in f.read_text(encoding="utf-8")
        idx = (raw_dir(root) / "index.tsv").read_text(encoding="utf-8").strip().split("\n")
        cols = idx[-1].split("\t")
        assert len(cols) == 5 and cols[0] == base + "/page" and cols[1].startswith("research/_raw/s1/") and cols[2] == sha1_file(f) and cols[4] == "ok", cols
        n = len(hits)
        st, _, d = fetch(base + "/page", "s1", spacing=0.4, root=root, sleep=nosleep)
        assert st == "ok" and d == "cached" and len(hits) == n, "a cached file was fetched again"
        assert fetch(base + "/403", "s1", spacing=0.1, root=root, sleep=nosleep)[0] == "403"
        n = len(hits)
        assert fetch(base + "/429", "s1", spacing=0.1, root=root, sleep=nosleep)[0] == "429" and len(hits) - n == 1, "a 429 ends the URL at once"
        n = len(hits)
        st429 = fetch(base + "/429b", "s1", spacing=0.1, root=root, sleep=nosleep)
        assert st429[0] == "429" and "cooling" in st429[2] and len(hits) == n, "F9/B1: the cooldown must be seen by the next fetch with NO request"
        for cf in (raw_dir(root) / ".hosts").glob("*.cool"):
            cf.unlink()  # the rest of this test talks to the same host
        n = len(hits)
        assert fetch(base + "/flaky", "s1", spacing=0.1, tries=3, root=root, sleep=nosleep)[0] == "ok", "backoff retries did not recover"
        assert fetch("http://127.0.0.1:9/none", "s1", spacing=0.1, tries=2, root=root, sleep=nosleep)[0] == "unreachable"
        log = (raw_dir(root) / "s1" / "fetch.log").read_text(encoding="utf-8")
        assert all(s in log for s in ("\tok\t", "\t403\t", "\t429\t", "\tunreachable\t")), log
        assert "403" not in (raw_dir(root) / "index.tsv").read_text(encoding="utf-8"), "a failed fetch was indexed"
        # F9/B1: five workers, five URLs, one host answering 429 -> at most 3 requests, then everyone sees the cooldown
        calls = []
        def g429(u):
            calls.append(u)
            raise urllib.error.HTTPError(u, 429, "Too Many", {"Retry-After": "30"}, None)
        root2 = Path(tempfile.mkdtemp())
        res = []
        ths = [threading.Thread(target=lambda i=i: res.append(fetch(f"http://h429.example/p{i}", "s", spacing=0.05, root=root2, get=g429, sleep=nosleep))) for i in range(5)]
        [t.start() for t in ths]; [t.join() for t in ths]
        assert len(calls) <= 3 and all(r[0] == "429" for r in res), f"B1: {len(calls)} requests for a host that said 429"
        assert 25 < cooling("h429.example", root2) <= 30, "Retry-After seconds must set the cooldown"
        # F9/B2: a script-rendered shell is `empty`, not ok, and not indexed
        shell = lambda u: (b"<html><body><div id=app></div><script>render()</script></body></html>", "text/html")
        r = fetch("http://shell.example/app", "s", spacing=0.05, root=root2, get=shell, sleep=nosleep)
        assert r[0] == "empty" and r[1] is None, f"B2: {r}"
        assert "shell.example" not in ((raw_dir(root2) / "index.tsv").read_text(encoding="utf-8") if (raw_dir(root2) / "index.tsv").exists() else "")
        # F9/B3: windows-1256 pages are decoded with the declared charset; an undeclared non-UTF-8 page is `undecodable`
        ar = ("مرحبا بكم في صفحة الاختبار الخاصة بنا اليوم " * 3).encode("cp1256")
        r = fetch("http://ar.example/p", "s", spacing=0.05, root=root2, get=lambda u: (ar, "text/html; charset=windows-1256"), sleep=nosleep)
        assert r[0] == "ok" and "مرحبا بكم" in r[1].read_text(encoding="utf-8"), f"B3: {r}"
        r = fetch("http://ar2.example/p", "s", spacing=0.05, root=root2, get=lambda u: (b"<meta charset=windows-1256>" + ar, "text/html"), sleep=nosleep)
        assert r[0] == "ok", f"B3: <meta> charset ignored: {r}"
        r = fetch("http://ar3.example/p", "s", spacing=0.05, root=root2, get=lambda u: (ar, "text/html"), sleep=nosleep)
        assert r[0] == "undecodable" and r[1] is None, f"B3: mojibake was indexed: {r}"
        r = fetch("http://bad.example/p", "s", spacing=0.05, root=root2, get=lambda u: (b"hello world " * 10, "text/plain; charset=nope-9"), sleep=nosleep)
        assert r[0] == "undecodable", r
        shutil.rmtree(root2, ignore_errors=True)
        # S8: --no-layout writes a second, plain text beside the -layout one and indexes it under the same URL with its own sha
        if shutil.which("pdftotext"):
            def make_pdf(rows):
                ops = "".join(f"BT /F1 11 Tf {x} {y} Td ({t}) Tj ET\n" for x, y, t in rows).encode("latin-1")
                objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
                        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
                        b"<< /Length %d >>\nstream\n" % len(ops) + ops + b"endstream", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
                out_, offs = b"%PDF-1.4\n", []
                for i, o in enumerate(objs, 1):
                    offs.append(len(out_)); out_ += b"%d 0 obj\n" % i + o + b"\nendobj\n"
                x = len(out_)
                out_ += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offs)
                return out_ + b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)
            tbl = make_pdf([(50, 700, "CTFL questions 40 and the first column"), (330, 700, "OTHER certification 99 second column"),
                            (50, 680, "CTFL pass mark 26 of the first column"), (330, 680, "OTHER mark 77 second column")])
            root3 = Path(tempfile.mkdtemp())
            r = fetch("http://pdf.example/t.pdf", "s", spacing=0.05, root=root3, get=lambda u: (tbl, "application/pdf"), sleep=nosleep, plain=True)
            assert r[0] == "ok", r
            pl = r[1].with_name(r[1].stem + ".plain.txt")
            assert pl.exists() and pl.read_text(encoding="utf-8") != r[1].read_text(encoding="utf-8"), "S8: the plain copy must exist and differ from the -layout copy"
            rows = [x.split("\t") for x in (raw_dir(root3) / "index.tsv").read_text(encoding="utf-8").strip().split("\n")]
            assert len(rows) == 2 and rows[0][0] == rows[1][0] == "http://pdf.example/t.pdf" and rows[0][1] != rows[1][1], rows
            assert {rw[1]: rw[2] for rw in rows} == {rel(r[1], root3): sha1_file(r[1]), rel(pl, root3): sha1_file(pl)}, "S8: each index row carries its own file's sha1"
            r2 = fetch("http://pdf2.example/t.pdf", "s", spacing=0.05, root=root3, get=lambda u: (tbl, "application/pdf"), sleep=nosleep)
            assert not r2[1].with_name(r2[1].stem + ".plain.txt").exists(), "without --no-layout there is no plain copy"
            # H2: --no-layout on a PDF already in the cache writes the plain copy with NO request and NO --refresh, registers it once
            def nohit(u):
                raise AssertionError("a cached file must not be requested")
            r3 = fetch("http://pdf2.example/t.pdf", "s", spacing=0.05, root=root3, get=nohit, sleep=nosleep, plain=True)
            pl3 = r3[1].with_name(r3[1].stem + ".plain.txt")
            assert r3[0] == "ok" and "plain copy written" in r3[2] and pl3.exists(), r3
            fetch("http://pdf2.example/t.pdf", "s", spacing=0.05, root=root3, get=nohit, sleep=nosleep, plain=True)
            idx3 = [x.split("\t") for x in (raw_dir(root3) / "index.tsv").read_text(encoding="utf-8").splitlines()]
            assert sum(1 for x in idx3 if x[1] == rel(pl3, root3)) == 1 and [x for x in idx3 if x[1] == rel(pl3, root3)][0][2] == sha1_file(pl3), "H2: the plain copy is registered once, with its own sha"
            pl3.unlink()  # a plain file on disk but missing from the index is registered too
            pl3.write_text(r3[1].read_text(encoding="utf-8").replace("  ", " "), encoding="utf-8")
            r5 = fetch("http://pdf2.example/t.pdf", "s", spacing=0.05, root=root3, get=nohit, sleep=nosleep, plain=True)
            assert r5[0] == "ok" and sum(1 for x in (raw_dir(root3) / "index.tsv").read_text(encoding="utf-8").splitlines() if x.split("\t")[1] == rel(pl3, root3)) == 1
            html_get = lambda u: (b"<html><body><p>" + b"A cached html page with enough text to count as a document. " * 2 + b"</p></body></html>", "text/html")
            h1 = fetch("http://html.example/p", "s", spacing=0.05, root=root3, get=html_get, sleep=nosleep)
            h2 = fetch("http://html.example/p", "s", spacing=0.05, root=root3, get=nohit, sleep=nosleep, plain=True)
            assert h1[0] == "ok" and h2[0] == "ok" and "no PDF sits beside" in h2[2] and "--refresh" in h2[2], f"H2: say why there is no plain copy: {h2}"
            shutil.rmtree(root3, ignore_errors=True)
        # spacing is shared through the stamp file; a stale lock is taken over
        t0 = time.time(); wait_host("h.example", 0.5, root); wait_host("h.example", 0.5, root)
        assert time.time() - t0 >= 0.49, "two claims on one host were not spaced"
        lock = raw_dir(root) / ".hosts" / "h.example.lock"
        lock.write_text("x"); old = time.time() - 120; os.utime(lock, (old, old))
        t0 = time.time(); wait_host("h.example", 0.0, root)
        assert time.time() - t0 < 5 and not lock.exists(), "a stale lock blocked or survived"
        # two real processes share the spacing
        import subprocess as sp
        code = ("import sys,time;sys.path.insert(0,sys.argv[1]);import fetch;from pathlib import Path;"
                "fetch.wait_host('p.example',1.0,Path(sys.argv[2]));print(time.time())")
        ps = [sp.Popen([sys.executable, "-c", code, os.path.dirname(os.path.abspath(__file__)), str(root)], stdout=sp.PIPE, text=True) for _ in range(2)]
        ts = sorted(float(p.communicate()[0]) for p in ps)
        assert ts[1] - ts[0] >= 0.9, f"two processes hit one host {ts[1] - ts[0]:.2f}s apart"
        # html_to_text keeps phrases whole
        assert html_to_text("<p>a <b>b</b>\n  c</p><p>d</p>") == "a b c\nd\n"
    finally:
        srv.shutdown()
        import shutil
        shutil.rmtree(root, ignore_errors=True)
    print("selftest ok"); return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url"); ap.add_argument("--slug", required=True)
    ap.add_argument("--spacing", type=float, default=2.0); ap.add_argument("--tries", type=int, default=3)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--no-layout", action="store_true", help="PDFs: also write a plain (no -layout) text copy and index it")
    a = ap.parse_args(argv)
    st, f, d = fetch(a.url, a.slug, a.spacing, a.tries, a.refresh, plain=a.no_layout)
    print(f"{st:11} {a.url}  {rel(f, ROOT) if f else '-'}  {d}")
    return 0 if st == "ok" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
