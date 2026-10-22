#!/usr/bin/env python3
"""Pinterest API v5 pin search — stdlib only (urllib, no requests).

Reads PINTEREST_TOKEN from <project root>/credentials/pinterest.env, where "project
root" is the current working directory this script is run from (this file lives in
the portable nj-motion-deck skill, not inside any one project, so it cannot locate
credentials/ relative to its own path — run it from the project root). Exits 3 with a
clear message if no token is present (see PINTEREST-SETUP.md); never creates an
account or app. Read-only: GET /v5/search/pins.

Usage: PYTHONUTF8=1 python pinterest_search.py "editorial infographic motion design"
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

ENV_PATH = os.path.join(os.getcwd(), "credentials", "pinterest.env")
API_BASE = "https://api.pinterest.com/v5"


def load_token(env_path: str) -> str | None:
    if not os.path.isfile(env_path):
        return None
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("PINTEREST_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'") or None
    return None


def search_pins(token: str, query: str, page_size: int = 25) -> dict:
    params = urllib.parse.urlencode({"query": query, "page_size": page_size})
    url = f"{API_BASE}/search/pins?{params}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def main() -> int:
    token = load_token(ENV_PATH)
    if not token:
        print(
            f"no Pinterest token found at {ENV_PATH} (expected PINTEREST_TOKEN=...). "
            "See PINTEREST-SETUP.md — the owner registers the app and drops the token there.",
            file=sys.stderr,
        )
        return 3

    if len(sys.argv) < 2:
        print("usage: pinterest_search.py <query>", file=sys.stderr)
        return 2

    query = " ".join(sys.argv[1:])
    try:
        data = search_pins(token, query)
    except urllib.error.HTTPError as e:
        print(f"Pinterest API error {e.code}: {e.read().decode(errors='replace')}", file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"network error reaching Pinterest API: {e.reason}", file=sys.stderr)
        return 1

    for item in data.get("items", []):
        pin_id = item.get("id", "")
        title = item.get("title", "")
        desc = item.get("description", "")
        link = item.get("link", "")
        media = item.get("media", {}) or {}
        images = media.get("images", {}) or {}
        image_url = next(iter(images.values()), {}).get("url", "") if images else ""
        print(f"{pin_id}\t{title}\t{desc}\t{link}\t{image_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
