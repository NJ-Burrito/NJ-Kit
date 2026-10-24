"""Build site/index.html (English) and site/ar/index.html (Arabic) from page.html.tpl.

The template is bilingual: any element carrying data-l="en" or data-l="ar" belongs to that
language only. The build keeps one language per page, so each URL is a clean single-language
document with its own <html lang>, title, description, canonical and hreflang links.

    python site/_build/build.py          # writes both pages, exits non-zero on a check failure
"""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
TPL = SITE / "_build" / "page.html.tpl"
BASE = "https://nj-burrito.github.io/NJ-Kit/"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class Keep(HTMLParser):
    """Re-emit the template verbatim, dropping every element whose data-l is another language."""

    def __init__(self, lang: str):
        super().__init__(convert_charrefs=False)
        self.lang, self.out, self.skip, self.depth = lang, [], None, 0

    def _other(self, attrs) -> bool:
        v = dict(attrs).get("data-l")
        return v is not None and v != self.lang

    def handle_starttag(self, tag, attrs):
        if self.skip:
            if tag == self.skip:
                self.depth += 1
            return
        if self._other(attrs):
            if tag not in VOID:
                self.skip, self.depth = tag, 1
            return
        self.out.append(self.get_starttag_text())

    def handle_startendtag(self, tag, attrs):
        if self.skip or self._other(attrs):
            return
        self.out.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if self.skip:
            if tag == self.skip:
                self.depth -= 1
                if self.depth == 0:
                    self.skip = None
            return
        self.out.append(f"</{tag}>")

    def _raw(self, s):
        if not self.skip:
            self.out.append(s)

    def handle_data(self, d): self._raw(d)
    def handle_entityref(self, n): self._raw(f"&{n};")
    def handle_charref(self, n): self._raw(f"&#{n};")
    def handle_comment(self, d): self._raw(f"<!--{d}-->")
    def handle_decl(self, d): self._raw(f"<!{d}>")
    def handle_pi(self, d): self._raw(f"<?{d}>")


def build(lang: str) -> str:
    src = TPL.read_text(encoding="utf-8")
    p = Keep(lang)
    p.feed(src)
    p.close()
    html = "".join(p.out)
    html = re.sub(r' data-l="(en|ar)"', "", html)
    # brand names and code tokens stay untranslated by browser translators
    html = re.sub(r"<(code|bdi)(?![^>]*translate=)", lambda m: "<" + m.group(1) + ' translate="no"', html)
    sub = {
        "{LANG}": lang,
        "{DIR}": "rtl" if lang == "ar" else "ltr",
        "{R}": "../" if lang == "ar" else "",
        "{SELF}": BASE + ("ar/" if lang == "ar" else ""),
    }
    for k, v in sub.items():
        html = html.replace(k, v)
    return html


def check(lang: str, html: str) -> list[str]:
    bad = []
    if re.search(r"\{(LANG|DIR|R|SELF)\}", html):
        bad.append("placeholder left")
    if "data-l=" in html:
        bad.append("data-l left")
    if html.count("<h1") != 1:
        bad.append(f"h1 count {html.count('<h1')}")
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            json.loads(m.group(1))
        except ValueError as e:
            bad.append(f"JSON-LD: {e}")
    if "—" in html:
        bad.append("em dash present")
    if f'<html lang="{lang}"' not in html:
        bad.append("html lang")
    return bad


def main() -> int:
    fails = 0
    for lang, out in (("en", SITE / "index.html"), ("ar", SITE / "ar" / "index.html")):
        html = build(lang)
        problems = check(lang, html)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8", newline="\n")
        status = "PASS" if not problems else "FAIL " + "; ".join(problems)
        print(f"{lang}: {out.relative_to(SITE)} {len(html.encode('utf-8'))} bytes {status}")
        fails += bool(problems)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
