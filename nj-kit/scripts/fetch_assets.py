#!/usr/bin/env python3
"""Fetch NJ-Kit assets v1, the heavy parts kept out of the git tree (stdlib only).

  python nj-kit/scripts/fetch_assets.py --list
  python nj-kit/scripts/fetch_assets.py graphify-package
  python nj-kit/scripts/fetch_assets.py --all [--root DIR]

Every download is checked against the sha256 in nj-kit/assets-manifest.json before
anything is written; a mismatch writes nothing and exits 1. Targets are relative to the
repo root unless --root is given. Existing files are overwritten.
"""
import argparse
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
MANIFEST = KIT / "assets-manifest.json"


def load() -> list:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["assets"]


def safe_join(base: Path, rel: str) -> Path:
    out = (base / rel).resolve()
    if base.resolve() != out and base.resolve() not in out.parents:
        raise ValueError(f"unsafe path in archive: {rel}")
    return out


def write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    tmp.write_bytes(data)
    tmp.replace(path)


def fetch(asset: dict, root: Path) -> bool:
    name = asset["name"]
    print(f"{name}: downloading {asset['url']}")
    try:
        with urllib.request.urlopen(asset["url"], timeout=120) as r:
            data = r.read()
    except Exception as e:  # network, 404 (release not uploaded yet), TLS
        print(f"  FAIL download: {e}")
        return False
    got = hashlib.sha256(data).hexdigest()
    if got != asset["sha256"]:
        print(f"  FAIL sha256: expected {asset['sha256']} got {got}; nothing written")
        return False
    target = root / asset["target"]
    kind = asset["kind"]
    if kind == "file":
        write(target, data)
        n = 1
    else:
        prefix = asset.get("extract_prefix", "")
        n = 0
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for m in z.namelist():
                if m.endswith("/") or not m.startswith(prefix):
                    continue
                write(safe_join(target, m[len(prefix):]), z.read(m))
                n += 1
    print(f"  ok sha256 verified; {n} file(s) -> {target}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help="asset names (see --list)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--root", type=Path, default=KIT.parent, help="base for each target (default: repo root)")
    a = ap.parse_args()
    assets = load()
    if a.list or not (a.names or a.all):
        for x in assets:
            print(f"{x['name']:<24} {x['kind']:<6} {x['version']:<11} {x['licence'].split(' (')[0]:<14} -> {x['target']}")
            print(f"  {x['what']}")
            print(f"  from {x['url']}")
        return 0
    by = {x["name"]: x for x in assets}
    unknown = [n for n in a.names if n not in by]
    if unknown:
        print("unknown asset(s):", ", ".join(unknown), "| known:", ", ".join(by))
        return 2
    chosen = assets if a.all else [by[n] for n in a.names]
    ok = [fetch(x, a.root) for x in chosen]
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
