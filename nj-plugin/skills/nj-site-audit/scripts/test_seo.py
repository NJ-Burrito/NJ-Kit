#!/usr/bin/env python3
"""Proves every Group G check fails on a bad sample and passes on a good one.
Run: python test_seo.py   (stdlib unittest; scratch in the system temp folder)"""
import json, os, shutil, struct, sys, tempfile, unittest, zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_audit as S

BASE = "https://example.test/"
FAM = {"sib": "https://sib.test/"}
SCRATCH = os.path.join(tempfile.gettempdir(), "nj-seo-test")


def png(w, h):
    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + ch(b"IEND", b"")


def page(lang="en", title="Acme: free widget maker, open source", desc=None, canon=BASE, hl=True, ids="en",
         og_alt=True, h1=1, img='<img src="logo.png" alt="logo" width="40" height="40">', extra="", robots="", sib=True,
         person_same='["https://sib.test/"]', jsonld=None):
    desc = desc or ("Widgets keep breaking? Acme builds them for you in one click, free and open source, " + lang)
    alt = BASE if lang == "en" else BASE + "ar/"
    other = BASE + "ar/" if lang == "en" else BASE
    hrefl = (f'<link rel="alternate" hreflang="en" href="{BASE}"><link rel="alternate" hreflang="ar" href="{BASE}ar/">'
             f'<link rel="alternate" hreflang="x-default" href="{BASE}">') if hl else ""
    ld = jsonld if jsonld is not None else json.dumps({"@context": "https://schema.org", "@graph": [
        {"@type": "Person", "@id": BASE + "#person", "name": "N", "sameAs": json.loads(person_same)},
        {"@type": "FAQPage", "@id": f"{BASE}#faq-{ids}", "mainEntity": []}]})
    return f"""<!doctype html><html lang="{lang}" dir="{'rtl' if lang=='ar' else 'ltr'}"><head><meta charset="utf-8">
<title>{title}</title><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{desc}">{robots}
<link rel="canonical" href="{canon if canon != BASE else alt}">{hrefl}
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<meta property="og:image" content="{BASE}og.png"><meta property="og:url" content="{alt}"><meta property="og:type" content="website">
{'<meta property="og:image:alt" content="x"><meta name="twitter:image:alt" content="x">' if og_alt else ''}
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{ld}</script>{extra}</head><body>
{'<h1>Main</h1>' * h1}<h2>Part</h2>{img}{'<a href="https://sib.test/">sibling</a>' if sib else ''}<a href="{other}">other</a></body></html>"""


def site():
    sm = ('<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          f'<url><loc>{BASE}</loc></url><url><loc>{BASE}ar/</loc></url></urlset>')
    return {"index.html": page(), "ar/index.html": page("ar", title="أكمي: صانع أدوات مجاني ومفتوح المصدر", desc="هل تتعطل أدواتك؟ يصنعها لك أكمي بنقرة واحدة، مجانا ومفتوح المصدر، ويعمل بدون إنترنت أيضا", ids="ar"),
            "404.html": "<html><body>nope</body></html>", "sitemap.xml": sm,
            "robots.txt": f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n", "og.png": png(1200, 630),
            "logo.png": png(40, 40), "googleabcdef0123456789.html": "google-site-verification: googleabcdef0123456789.html"}


def audit(files, **kw):
    os.makedirs(SCRATCH, exist_ok=True)
    d = tempfile.mkdtemp(dir=SCRATCH)
    try:
        for p, c in files.items():
            fp = os.path.join(d, p)
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, "wb") as fh:
                fh.write(c if isinstance(c, bytes) else c.encode("utf-8"))
        kw.setdefault("family", FAM)
        return S.audit_target(d, BASE, **kw)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def codes(au):
    return {f["code"] for f in au.counted()}


class T(unittest.TestCase):
    def bad(self, code, mutate, **kw):
        f = site()
        mutate(f)
        au = audit(f, **kw)
        self.assertIn(code, codes(au), f"{code} should fail: {[x['msg'] for x in au.counted()]}")

    def test_good_sample_passes(self):
        au = audit(site())
        self.assertEqual(au.counted(), [], [f["msg"] for f in au.counted()])
        self.assertEqual(au.to_json()["result"], "PASS")

    def test_g1_verification(self):
        def m(f): del f["googleabcdef0123456789.html"]
        self.bad("G1", m)
        f = site()  # meta form alone is also accepted
        del f["googleabcdef0123456789.html"]
        f["index.html"] = f["index.html"].replace("<title>", '<meta name="google-site-verification" content="abc"><title>', 1)
        self.assertEqual(audit(f).counted(), [])

    def test_g2_title(self):
        self.bad("G2", lambda f: f.update({"index.html": page(title="A" * 72)}))
        self.bad("G2", lambda f: f.update({"index.html": page(title="")}))

    def test_g3_description(self):
        self.bad("G3", lambda f: f.update({"index.html": page(desc="too short")}))
        d = page().split('name="description" content="')[1].split('"')[0]
        self.bad("G3", lambda f: f.update({"ar/index.html": page("ar", title="أكمي: صانع أدوات مجاني ومفتوح المصدر", desc=d, ids="ar")}))

    def test_g4_canonical(self):
        self.bad("G4", lambda f: f.update({"index.html": f["index.html"].replace('rel="canonical"', 'rel="nothing"')}))
        self.bad("G4", lambda f: f.update({"index.html": page(canon=BASE + "elsewhere/")}))

    def test_g5_hreflang(self):
        self.bad("G5", lambda f: f.update({"ar/index.html": page("ar", title="أكمي: صانع أدوات مجاني ومفتوح المصدر", hl=False, ids="ar")}))
        self.bad("G5", lambda f: f.update({"index.html": f["index.html"].replace(f'<link rel="alternate" hreflang="x-default" href="{BASE}">', "")}))
        self.bad("G5", lambda f: f.update({"index.html": page(hl=False), "ar/index.html": page("ar", title="أكمي: صانع أدوات مجاني ومفتوح المصدر", hl=False, ids="ar")}))

    def test_g6_social(self):
        self.bad("G6", lambda f: f.update({"og.png": png(512, 512)}))
        self.bad("G6", lambda f: f.update({"index.html": page(og_alt=False)}))
        self.bad("G6", lambda f: f.pop("og.png"))

    def test_g7_jsonld(self):
        self.bad("G7", lambda f: f.update({"index.html": page(jsonld="{not json")}))
        self.bad("G7", lambda f: f.update({"index.html": page(person_same="[]")}))
        self.bad("G7", lambda f: f.update({"ar/index.html": page("ar", ids="en", title="أكمي: صانع أدوات مجاني ومفتوح المصدر", desc="هل تتعطل أدواتك؟ يصنعها لك أكمي بنقرة واحدة، مجانا ومفتوح المصدر، ويعمل بدون إنترنت أيضا")}))

    def test_g8_headings(self):
        self.bad("G8", lambda f: f.update({"index.html": page(h1=2)}))
        self.bad("G8", lambda f: f.update({"index.html": f["index.html"].replace("<h2>Part</h2>", "<h3>Part</h3>")}))

    def test_g9_images(self):
        self.bad("G9", lambda f: f.update({"index.html": page(img='<img src="logo.png" width="4" height="4">')}))
        self.bad("G9", lambda f: f.update({"index.html": page(img='<img src="logo.png" alt="x">')}))
        gif = b"GIF89a" + struct.pack("<HH", 10, 10) + b"\0" * 1_200_000
        self.bad("G9", lambda f: f.update({"index.html": page(img='<img src="a.gif" alt="x" width="1" height="1">'), "a.gif": gif}))

    def test_g10_404(self):
        self.bad("G10", lambda f: f.pop("404.html"))

    def test_g11_sitemap_robots(self):
        self.bad("G11", lambda f: f.pop("sitemap.xml"))
        self.bad("G11", lambda f: f.update({"sitemap.xml": f["sitemap.xml"].replace("</urlset>", f"<url><loc>{BASE}gone.html</loc></url></urlset>")}))
        self.bad("G11", lambda f: f.update({"sitemap.xml": f["sitemap.xml"].replace(f"<url><loc>{BASE}ar/</loc></url>", "")}))
        self.bad("G11", lambda f: f.update({"robots.txt": "User-agent: *\nDisallow: /\n"}))

    def test_g12_llms(self):
        self.bad("G12", lambda f: f.update({"llms.txt": f"# Acme\n- [x]({BASE}missing.html)\n"}))
        f = site()
        f["llms.txt"] = f"# Acme\n- [x]({BASE}ar/)\n"
        self.assertEqual(audit(f).counted(), [])

    def test_g13_noindex(self):
        tryp = page(title="Acme try it out page, practice")
        def m(f):
            f["try/index.html"] = tryp
            f["index.html"] = f["index.html"].replace("</body>", '<a href="try/">try</a></body>')
        self.bad("G13", m)
        f = site()
        f["try/index.html"] = page(title="Acme try it out page, practice", robots='<meta name="robots" content="noindex">', canon=BASE + "try/")
        f["index.html"] = f["index.html"].replace("</body>", '<a href="try/">try</a></body>')
        self.assertNotIn("G13", codes(audit(f)))
        self.bad("G13", lambda f: f.update({"index.html": page(robots='<meta name="robots" content="noindex">')}))

    def test_g14_family(self):
        self.bad("G14", lambda f: f.update({"index.html": page(sib=False)}))

    def test_g15_basics(self):
        self.bad("G15", lambda f: f.update({"index.html": f["index.html"].replace('<html lang="en"', "<html")}))
        self.bad("G15", lambda f: f.update({"index.html": f["index.html"].replace('<meta name="viewport" content="width=device-width,initial-scale=1">', "")}))

    def test_g16_generated_is_a_note(self):
        f = site()
        f["index.html"] = f["index.html"].replace("<head>", "<head><!-- generated by build.py: do not edit -->")
        au = audit(f)
        self.assertTrue(any(x["code"] == "G16" and x["sev"] == "note" for x in au.findings))
        self.assertEqual(au.counted(), [])

    def test_g17_live_title(self):
        au = audit(site(), expect_title="Some other title")
        self.assertIn("G17", codes(au))

    def test_image_sizes(self):
        self.assertEqual(S.image_size(png(1200, 630)), (1200, 630))
        self.assertEqual(S.image_size(b"GIF89a" + struct.pack("<HH", 7, 9)), (7, 9))
        vp8x = b"RIFF\0\0\0\0WEBPVP8X" + b"\0" * 8 + (1199).to_bytes(3, "little") + (629).to_bytes(3, "little")
        self.assertEqual(S.image_size(vp8x), (1200, 630))
        jpg = b"\xff\xd8\xff\xe0" + struct.pack(">H", 4) + b"\0\0" + b"\xff\xc0" + struct.pack(">HBHH", 11, 8, 630, 1200) + b"\0" * 6
        self.assertEqual(S.image_size(jpg), (1200, 630))
        self.assertIsNone(S.image_size(b"not an image"))

    def test_cli_exit_codes(self):
        d = tempfile.mkdtemp(dir=SCRATCH if os.path.isdir(SCRATCH) else None)
        try:
            for p, c in site().items():
                fp = os.path.join(d, p)
                os.makedirs(os.path.dirname(fp), exist_ok=True)
                with open(fp, "wb") as fh:
                    fh.write(c if isinstance(c, bytes) else c.encode())
            self.assertEqual(S.main([d, "--base", BASE, "--family", "https://sib.test/"]), 0)
            os.remove(os.path.join(d, "404.html"))
            self.assertEqual(S.main([d, "--base", BASE, "--family", "https://sib.test/"]), 1)
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    os.makedirs(SCRATCH, exist_ok=True)
    unittest.main(verbosity=1)
