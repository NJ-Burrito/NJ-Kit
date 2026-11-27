#!/usr/bin/env python3
"""Run Lighthouse locally (free). Never pay a SEO tool for Lighthouse.

  python lighthouse_local.py URL [URL ...] [--urls-file f.txt] [--out DIR] [--json summary.json]

Needs node/npx and a Chromium: PLAYWRIGHT_BROWSERS_PATH (default: Playwright's own cache folder for this OS)
is searched and CHROME_PATH is set for lighthouse. Standard library only.
Exit 0 ok, 1 a run failed, 2 node/npx or Chromium missing.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, tempfile

CATS = ("performance", "accessibility", "best-practices", "seo")



def _default_pw_cache():
    """Playwright's default browser cache when PLAYWRIGHT_BROWSERS_PATH is not set."""
    import sys
    home = os.path.expanduser("~")
    if sys.platform.startswith("win"):
        return os.path.join(os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local")), "ms-playwright")
    if sys.platform == "darwin":
        return os.path.join(home, "Library", "Caches", "ms-playwright")
    return os.path.join(home, ".cache", "ms-playwright")

def find_chromium():
    if os.environ.get("CHROME_PATH") and os.path.isfile(os.environ["CHROME_PATH"]):
        return os.environ["CHROME_PATH"]
    root = os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or _default_pw_cache()
    pats = ["chromium-*/chrome-win*/chrome.exe", "chromium_headless_shell-*/chrome-headless-shell-win*/chrome-headless-shell.exe",
            "chromium-*/chrome-linux*/chrome", "chromium-*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium"]
    for p in pats:
        hits = sorted(glob.glob(os.path.join(root, p)))
        if hits:
            return hits[-1]
    return None


def summarise(data):
    cats = {k: round((v.get("score") or 0) * 100) for k, v in data.get("categories", {}).items()}
    audits = data.get("audits", {})
    weight = {}
    for c in data.get("categories", {}).values():
        for ref in c.get("auditRefs", []):
            weight[ref["id"]] = ref.get("weight", 0)
    failed = [(a.get("score"), weight.get(i, 0), i, a.get("title"), a.get("displayValue", ""))
              for i, a in audits.items()
              if a.get("score") is not None and a["score"] < 0.9 and a.get("scoreDisplayMode") in ("numeric", "binary") and weight.get(i, 0) > 0]
    failed.sort(key=lambda t: (t[0], -t[1]))
    m = {k: audits.get(k, {}).get("displayValue", "") for k in
         ("first-contentful-paint", "largest-contentful-paint", "total-blocking-time", "cumulative-layout-shift", "speed-index")}
    return {"scores": cats, "metrics": m,
            "top_failed": [{"id": i, "title": t, "score": s, "value": v} for s, w, i, t, v in failed[:8]]}


def run_one(npx, chrome, url, outdir):
    os.makedirs(outdir, exist_ok=True)
    name = re.sub(r"[^A-Za-z0-9]+", "_", url).strip("_")[:80] + ".json"
    path = os.path.join(outdir, name)
    env = dict(os.environ, CHROME_PATH=chrome, PYTHONUTF8="1")
    cmd = [npx, "--yes", "lighthouse", url, "--output", "json", "--output-path", path, "--quiet",
           "--only-categories=" + ",".join(CATS), "--chrome-flags=--headless=new --no-sandbox"]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
    if r.returncode != 0 or not os.path.isfile(path):
        return {"url": url, "error": (r.stderr or r.stdout).strip()[-400:] or f"exit {r.returncode}"}
    with open(path, encoding="utf-8") as fh:
        res = summarise(json.load(fh))
    res.update(url=url, report=path)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--urls-file")
    ap.add_argument("--out", default=os.path.join(os.environ.get("TMPDIR") or tempfile.gettempdir(), "lighthouse"))
    ap.add_argument("--json", dest="json_out")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    urls = list(a.urls)
    if a.urls_file:
        urls += [l.strip() for l in open(a.urls_file, encoding="utf-8") if l.strip() and not l.startswith("#")]
    if not urls:
        ap.error("give at least one URL")
    npx = shutil.which("npx")
    if not (shutil.which("node") and npx):
        print("MISSING: node/npx not found on PATH. Install Node.js (https://nodejs.org) and retry. Nothing was run.")
        return 2
    chrome = find_chromium()
    if not chrome:
        print("MISSING: no Chromium under PLAYWRIGHT_BROWSERS_PATH "
              f"({os.environ.get('PLAYWRIGHT_BROWSERS_PATH') or _default_pw_cache()}). "
              "Run `npx playwright install chromium` with that variable set, or set CHROME_PATH. Nothing was run.")
        return 2
    print(f"chromium: {chrome}")
    results, bad = [], 0
    for u in urls:
        print(f"running lighthouse on {u} ...", flush=True)
        try:
            res = run_one(npx, chrome, u, a.out)
        except Exception as e:
            res = {"url": u, "error": str(e)}
        results.append(res)
        bad += "error" in res
    print(f"\n{'url':<50} perf  a11y  best  seo")
    for r in results:
        if "error" in r:
            print(f"{r['url'][:50]:<50} ERROR {r['error'][:100]}")
            continue
        s = r["scores"]
        print(f"{r['url'][:50]:<50} {s.get('performance','-'):>4}  {s.get('accessibility','-'):>4}  {s.get('best-practices','-'):>4}  {s.get('seo','-'):>3}")
        print("    " + ", ".join(f"{k}={v}" for k, v in r["metrics"].items() if v))
        for f in r["top_failed"]:
            print(f"    fail: {f['title']} ({f['id']}) {f['value']}".rstrip())
    if a.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(a.json_out)), exist_ok=True)
        with open(a.json_out, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2, ensure_ascii=False)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
