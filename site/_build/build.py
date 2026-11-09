"""Build site/index.html (English) and site/ar/index.html (Arabic) from page.html.tpl.

The template is bilingual: any element carrying data-l="en" or data-l="ar" belongs to that
language only. The build keeps one language per page, so each URL is a clean single-language
document with its own <html lang>, title, description, canonical and hreflang links.

    python site/_build/build.py          # writes both pages and llms.txt, exits non-zero on a check failure
    python site/_build/build.py --check  # same, then fails if the committed site differs from the build (CI)
"""
from __future__ import annotations

import base64
import hashlib
import html as htmllib
import importlib.util
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
TPL = SITE / "_build" / "page.html.tpl"
BASE = "https://nj-burrito.github.io/NJ-Kit/"
ROOT = SITE.parent
SKILLS = SITE / "_build" / "skills.json"
# nj-kit/bundled folders that are not kit-only skills: the v4 agent files, and a copy of a plugin skill
NOT_KIT_SKILLS = {"claude-v4", "pdf-typography"}
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


INLINE_SCRIPT = re.compile(r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>", re.S)


def inline_script_hashes(html: str) -> list[str]:
    """CSP hashes of every inline script the browser would run (JSON-LD data blocks are not executed)."""
    out = []
    for m in INLINE_SCRIPT.finditer(html):
        attrs = m.group("attrs")
        if "src=" in attrs or "application/ld+json" in attrs:
            continue
        digest = hashlib.sha256(m.group("body").encode("utf-8")).digest()
        out.append("'sha256-" + base64.b64encode(digest).decode() + "'")
    return out


def csp_meta(html: str) -> str:
    """Meta CSP with the computed script hashes (frame-ancestors cannot be set from a meta tag).
    style-src keeps 'unsafe-inline' because hashes would disable it for the style="" attributes."""
    hashes = " ".join(inline_script_hashes(html))
    policy = ("default-src 'self'; script-src 'self' " + hashes + "; style-src 'self' 'unsafe-inline'; "
              "img-src 'self' data:; font-src 'self'; connect-src 'none'; object-src 'none'; "
              "base-uri 'self'; form-action 'none'")
    return f'<meta http-equiv="Content-Security-Policy" content="{policy}">'


def load_skills() -> dict:
    """Skill counts, groups and per-skill text, checked against the real skills so the page cannot go stale.

    Plugin skills come from .claude-plugin/marketplace.json and their English line from each SKILL.md
    (the same function scripts/skill-table.py uses for the README). skills.json only assigns groups and
    holds the Arabic text, plus a shorter English line where the SKILL.md sentence is too long for the page.
    """
    spec = importlib.util.spec_from_file_location("skill_table", ROOT / "scripts" / "skill-table.py")
    st = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(st)
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))["plugins"][0]
    plugin = {Path(s).name: ROOT / market["source"] / s / "SKILL.md" for s in market["skills"]}
    data = json.loads(SKILLS.read_text(encoding="utf-8"))
    grouped = [s for g in data["groups"] for s in g["skills"]]
    errs = []
    if sorted(grouped) != sorted(plugin):
        errs.append(f"groups differ from marketplace.json: missing {sorted(set(plugin) - set(grouped))}, "
                    f"unknown {sorted(set(grouped) - set(plugin))}, duplicated {sorted({s for s in grouped if grouped.count(s) > 1})}")
    kit_dirs = {p.name for p in (ROOT / "nj-kit" / "bundled").iterdir() if p.is_dir()} - NOT_KIT_SKILLS
    if kit_dirs != set(data["bundled"]["skills"]):
        errs.append(f"bundled differs from nj-kit/bundled: {sorted(kit_dirs ^ set(data['bundled']['skills']))}")
    errs += [f"no Arabic text for {s}" for s in plugin if not data["text"].get(s, {}).get("ar")]
    errs += [f"new skill not in the plugin: {s}" for s in data["new"]["skills"] if s not in plugin]
    if data["new"]["current"] != market["version"]:
        errs.append(f'"current" is {data["new"]["current"]}, marketplace.json says {market["version"]}')
    if errs:
        raise SystemExit("skills.json: " + "; ".join(errs))
    for s, md in plugin.items():
        data["text"][s].setdefault("en", st.description(md).replace("`", ""))
    data["counts"] = {"ALL": len(plugin) + len(data["bundled"]["skills"]), "PLUGIN": len(plugin),
                      "KIT": len(data["bundled"]["skills"])}
    return data


def skills_ui(d: dict) -> str:
    """Group tabs (both languages) and one panel per plugin group; the bundled panel stays in the template."""
    groups = d["groups"] + [dict(d["bundled"], id="b", n=d["counts"]["KIT"])]

    def tab(g, lang, first):
        sel = ("true", "") if first else ("false", ' tabindex="-1"')
        return (f'<button class="tab" role="tab" id="tab-{g["id"]}" aria-controls="p-{g["id"]}" aria-selected="{sel[0]}"{sel[1]}>'
                f'<svg class="ic" aria-hidden="true"><use href="#{g["icon"]}"/></svg>{g[lang]}'
                f'<span class="n">{g.get("n", len(g["skills"]))}</span></button>')

    out = []
    for lang, label in (("en", "Skill groups"), ("ar", "مجموعات المهارات")):
        tabs = "\n".join("          " + tab(g, lang, i == 0) for i, g in enumerate(groups))
        out.append(f'<div class="tabs" role="tablist" aria-label="{label}" data-l="{lang}">\n'
                   f'          <span class="pill" aria-hidden="true"></span>\n{tabs}\n        </div>')
    for i, g in enumerate(d["groups"]):
        rows = "\n".join(
            f'            <li><code>{s}</code><span data-l="en">{htmllib.escape(d["text"][s]["en"], quote=False)}</span>'
            f'<span data-l="ar">{d["text"][s]["ar"]}</span></li>' for s in g["skills"])
        out.append(f'<div class="panel" role="tabpanel" id="p-{g["id"]}" aria-labelledby="tab-{g["id"]}"{"" if i == 0 else " hidden"}>\n'
                   f'          <ul class="skills">\n{rows}\n          </ul>\n        </div>')
    return "\n        ".join(out)


def skills_new(d: dict) -> str:
    v, cur = d["new"]["version"], d["new"]["current"]
    names = "".join(f"<li>{s}</li>" for s in d["new"]["skills"])
    rel = f"https://github.com/NJ-Burrito/NJ-Kit/releases/tag/v{cur}"
    return "\n      ".join([
        f'<p class="note" data-l="en">Current release: <a href="{rel}">v{cur}</a>. New skills in {v}:</p>',
        f'<p class="note" data-l="ar">الإصدار الحالي: <a href="{rel}"><bdi dir="ltr">v{cur}</bdi></a>. مهارات جديدة في {v}:</p>',
        f'<ul class="chipset" aria-label="New in {v}">{names}</ul>'])


def groups_line(d: dict) -> str:
    parts = [f'{g["en"]} ({len(g["skills"])})' for g in d["groups"]]
    return ", ".join(parts + [f'{d["bundled"]["en"]} ({d["counts"]["KIT"]})'])


def llms() -> str:
    d = load_skills()
    txt = (SITE / "_build" / "llms.txt.tpl").read_text(encoding="utf-8").replace("{GROUPS}", groups_line(d))
    for k, v in d["counts"].items():
        txt = txt.replace("{N_" + k + "}", str(v))
    return txt


def build(lang: str) -> str:
    d = load_skills()
    src = TPL.read_text(encoding="utf-8").replace("{SKILLS_UI}", skills_ui(d)).replace("{SKILLS_NEW}", skills_new(d))
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
        **{"{N_" + k + "}": str(v) for k, v in d["counts"].items()},
    }
    for k, v in sub.items():
        html = html.replace(k, v)
    html = html.replace("{CSP}", csp_meta(html.replace("{CSP}", "")))   # last: hashes cover the final script text
    return html


def check(lang: str, html: str) -> list[str]:
    bad = []
    if re.search(r"\{(LANG|DIR|R|SELF|N_[A-Z]+|SKILLS_[A-Z]+)\}", html):
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
    if 'http-equiv="Content-Security-Policy"' not in html:
        bad.append("CSP meta missing")
    if 'name="referrer"' not in html:
        bad.append("referrer meta missing")
    if re.search(r"<[a-z][^>]*\son[a-z]+=", html, re.I):
        bad.append("inline event handler (blocked by the CSP)")
    for h in inline_script_hashes(html):
        if h not in html:
            bad.append("script hash not in CSP")
    if re.search(r"<(?:script|link|img|iframe)[^>]+(?:src|href)=[\"']https?://(?![^\"']*(?:nj-burrito\.github\.io|github\.com|linkedin\.com))", html, re.I):
        bad.append("external subresource")
    counts = load_skills()["counts"].values()
    for m in re.finditer(r"(\d+)\s*(?:Claude Code\s+)?(?:plugin\s+)?(?:skills|مهارة)", html):
        if int(m.group(1)) not in counts and m.group(1) != "22":   # 22 = third-party sources the installer lists
            bad.append(f"stale skill count {m.group(0)!r}")
    if "—" in html:
        bad.append("em dash present")
    if f'<html lang="{lang}"' not in html:
        bad.append("html lang")
    return bad


def main() -> int:
    fails = 0
    (SITE / "llms.txt").write_text(llms(), encoding="utf-8", newline="\n")
    print("llms.txt written")
    for lang, out in (("en", SITE / "index.html"), ("ar", SITE / "ar" / "index.html")):
        html = build(lang)
        problems = check(lang, html)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8", newline="\n")
        status = "PASS" if not problems else "FAIL " + "; ".join(problems)
        print(f"{lang}: {out.relative_to(SITE)} {len(html.encode('utf-8'))} bytes {status}")
        fails += bool(problems)
    if "--check" in sys.argv:   # CI: the committed site must equal a fresh build
        stale = subprocess.run(["git", "diff", "--quiet", "--", "site"], cwd=ROOT).returncode
        print("site stale: run python site/_build/build.py and commit" if stale else "site is current")
        fails += bool(stale)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
