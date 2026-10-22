#!/usr/bin/env python3
"""bg-music — build a background-music library from free, commercially usable sources.

Searches Openverse (no API key, indexes Jamendo, Freesound, ccMixter, WikiCommons),
keeps only licences that permit commercial use, downloads, optionally normalises
to a bed loudness, and writes library.json + ATTRIBUTION.md.

    python fetch_music.py --out %NJ_LIBRARY%/music --per-mood 6   # then: library.py sync
    python fetch_music.py --out LIB --mood deep --per-mood 10 --normalize
    python fetch_music.py --out LIB --search "oud instrumental" --mood arabic
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import ssl
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:  # certifi is required on this machine — no CA bundle otherwise
    SSL_CTX = ssl.create_default_context()

API = "https://api.openverse.org/v1/audio/"
UA = {"User-Agent": "nj-bg-music/1.0 (personal media library)"}

# Mood -> search terms. The four categories come from the short-form convention
# (informational / challenge / motivational / deep); the rest are house additions.
MOODS = {
    "informational": ["clean minimal electronic loop", "light corporate background", "soft synth pad groove"],
    "challenge":     ["driving percussion loop", "energetic electronic beat", "tension build drums"],
    "motivational":  ["uplifting instrumental", "cinematic inspiring strings", "hopeful piano build"],
    "deep":          ["ambient atmospheric pad", "slow emotional piano", "dark ambient drone"],
    "arabic":        ["oud instrumental", "middle eastern percussion", "arabic ambient"],
    "corporate":     ["corporate presentation background", "neutral tech ambience"],
    "cinematic":     ["cinematic orchestral", "film score ambient"],
}
# Licences that allow commercial use. NC/ND are refused: a client video is commercial
# use, and ND forbids the edit every video makes.
OK_LICENCES = {"cc0", "pdm", "by", "by-sa"}
ATTRIB_REQUIRED = {"by", "by-sa"}


def die(msg: str, code: int = 1):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(code)


def slug(s: str, n: int = 60) -> str:
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE).strip()
    return re.sub(r"[-\s]+", "-", s)[:n] or "track"


def api_get(params: dict) -> dict:
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, context=SSL_CTX, timeout=45) as r:
        return json.load(r)


def search(query: str, page_size: int, min_seconds: int) -> list[dict]:
    try:
        data = api_get({"q": query, "license_type": "commercial",
                        "page_size": min(page_size * 4, 40), "mature": "false"})
    except Exception as e:
        print(f"  ! search failed for {query!r}: {e}")
        return []
    out = []
    for r in data.get("results", []):
        lic = (r.get("license") or "").lower()
        dur_ms = r.get("duration") or 0
        if lic not in OK_LICENCES:
            continue
        if dur_ms and dur_ms / 1000 < min_seconds:
            continue
        if not r.get("url"):
            continue
        out.append(r)
    return out[:page_size]


def download(url: str, dst: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, context=SSL_CTX, timeout=120) as r, open(dst, "wb") as f:
            shutil.copyfileobj(r, f)
        return dst.stat().st_size > 10_000
    except Exception as e:
        print(f"  ! download failed: {e}")
        dst.unlink(missing_ok=True)
        return False


def normalise(src: Path, lufs: float) -> bool:
    """Bed loudness, so every track in the library sits at the same level."""
    if not shutil.which("ffmpeg"):
        return False
    dst = src.with_name(src.stem + "-bed.wav")
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(src),
                        "-af", f"loudnorm=I={lufs}:TP=-2:LRA=11", "-ar", "48000",
                        "-c:a", "pcm_s16le", str(dst)],
                       capture_output=True, text=True)
    return p.returncode == 0


def main():
    p = argparse.ArgumentParser(description="Fetch a free, commercially usable music library.")
    p.add_argument("--out", required=True, help="library directory")
    p.add_argument("--mood", action="append", choices=sorted(MOODS), help="repeatable; default all")
    p.add_argument("--search", help="extra free-text query, filed under --mood")
    p.add_argument("--per-mood", type=int, default=6)
    p.add_argument("--min-seconds", type=int, default=30, help="skip one-shots and stingers")
    p.add_argument("--normalize", action="store_true", help="also write a -23 LUFS bed copy")
    p.add_argument("--bed-lufs", type=float, default=-23.0)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    lib_path = out / "library.json"
    library = json.loads(lib_path.read_text(encoding="utf-8")) if lib_path.exists() else {"tracks": []}
    seen = {t["source_url"] for t in library["tracks"]}

    moods = a.mood or sorted(MOODS)
    added = 0
    for mood in moods:
        queries = ([a.search] if a.search else []) + MOODS[mood]
        mood_dir = out / mood
        got = 0
        print(f"[{mood}]")
        for q in queries:
            if got >= a.per_mood:
                break
            for r in search(q, a.per_mood - got, a.min_seconds):
                if r["url"] in seen:
                    continue
                lic = r["license"].lower()
                name = f"{slug(r.get('creator') or 'unknown', 24)}--{slug(r.get('title') or 'track')}"
                ext = ".mp3" if ".mp3" in r["url"] else Path(urllib.parse.urlparse(r["url"]).path).suffix or ".mp3"
                dst = mood_dir / (name + ext)
                print(f"  {lic.upper():5} {(r.get('title') or '')[:48]:48} {(r.get('duration') or 0)//1000:>4}s")
                if a.dry_run:
                    got += 1
                    continue
                mood_dir.mkdir(parents=True, exist_ok=True)
                if not download(r["url"], dst):
                    continue
                if a.normalize:
                    normalise(dst, a.bed_lufs)
                library["tracks"].append({
                    "mood": mood, "query": q, "file": str(dst.relative_to(out)).replace("\\", "/"),
                    "title": r.get("title"), "creator": r.get("creator"),
                    "licence": lic, "licence_version": r.get("license_version"),
                    "licence_url": r.get("license_url"),
                    "attribution_required": lic in ATTRIB_REQUIRED,
                    "provider": r.get("provider"), "source_url": r["url"],
                    "landing_page": r.get("foreign_landing_url"),
                    "duration_s": round((r.get("duration") or 0) / 1000),
                    "retrieved": date.today().isoformat(),
                })
                seen.add(r["url"])
                got += 1
                added += 1
                if got >= a.per_mood:
                    break

    if a.dry_run:
        return

    library["updated"] = date.today().isoformat()
    lib_path.write_text(json.dumps(library, ensure_ascii=False, indent=2), encoding="utf-8")

    # ATTRIBUTION.md is not paperwork: CC-BY without the credit line is an
    # unlicensed use, which is the same legal position as taking the track.
    lines = ["# Attribution", "",
             "Every track below is free to use commercially. Tracks marked **credit required**",
             "must carry the line shown wherever the video is published (description, caption,",
             "or end card). CC0 / Public Domain tracks need nothing.", "",
             f"Generated {library['updated']} by `bg-music`. Source: Openverse.", ""]
    for mood in sorted({t["mood"] for t in library["tracks"]}):
        lines.append(f"## {mood}")
        lines.append("")
        for t in [x for x in library["tracks"] if x["mood"] == mood]:
            if t["attribution_required"]:
                lines.append(f"- **credit required** — \"{t['title']}\" by {t['creator']}, "
                             f"CC {t['licence'].upper()} {t.get('licence_version') or ''} "
                             f"— {t.get('landing_page') or t['source_url']}  \n  `{t['file']}`")
            else:
                lines.append(f"- free, no credit — \"{t['title']}\" by {t['creator']} "
                             f"({t['licence'].upper()})  \n  `{t['file']}`")
        lines.append("")
    (out / "ATTRIBUTION.md").write_text("\n".join(lines), encoding="utf-8")

    n = len(library["tracks"])
    need = sum(1 for t in library["tracks"] if t["attribution_required"])
    print(f"\n{added} new, {n} total in {out}  ({need} need a credit line)")
    if added == 0:
        die("nothing downloaded", code=2)


if __name__ == "__main__":
    main()
