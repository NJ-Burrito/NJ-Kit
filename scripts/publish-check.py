#!/usr/bin/env python3
"""publish-check: refuse to publish anything private.

Scans every file git would commit (tracked + untracked, .gitignore respected) for
credentials, private project data, personal machine paths, font files and large or
binary artefacts. Prints `file:line  PATTERN-NAME` for each hit, never the matched
value, then PASS (exit 0) or FAIL (exit 1).

    python scripts/publish-check.py            # scan the repo
    python scripts/publish-check.py --selftest # prove every pattern still fires

Extend PRIVATE_TERMS below with the names of your own clients and projects before a
release. Run it before every push; CI runs it on every pull request.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SELF = Path(__file__).resolve()

# Words that must never reach the public repo: client, project and people names.
# Stored split so this file does not match itself when read by other scanners.
PRIVATE_TERMS = [
    "jf" + "da", "mo" + "ap2", "taq" + "neen", "en" + "sera", "san" + "ad",
    "althu" + "nibat", "almash" + "ayekh", "ala" + "a", "dom" + "i",
    "flow" + "able-jfda", "staging-back" + "office",
    "raw" + "an", "abushe" + "hab", "rag" + "had", "oth" + "man", "abdel" + "halim", "alta" + "wil",
]
ARABIC_TERMS = [
    "المؤسسة العامة " + "للغذاء والدواء", "الغذاء " + "والدواء", "وزارة " + "الزراعة",
    "تقن" + "ين", "إنسي" + "را", "انسي" + "را", "الدو" + "مي", "الاّء", "الآء",
]
ALLOWED_EMAILS = {"naderalzghoulbusiness@gmail.com", "noreply@anthropic.com"}
ALLOWED_EMAILS |= {"git@github.com"}
ALLOWED_EMAIL_DOMAINS = ("example.com", "example.org", "example.net", ".example", ".test", ".invalid",
                         "users.noreply.github.com", "anthropic.com", "greensock.com")

PATTERNS: list[tuple[str, re.Pattern]] = [
    ("project-term", re.compile(r"(?<![A-Za-z])(?:" + "|".join(PRIVATE_TERMS) + r")(?![A-Za-z])", re.I)),
    ("project-term-ar", re.compile("|".join(map(re.escape, ARABIC_TERMS)))),
    ("project-acronym-moa", re.compile(r"(?<![A-Za-z])MOA(?![A-Za-z])")),
    ("jira-key-private", re.compile(r"\b(?:JF" + r"DA|MO" + r"AP\d*|MOA)-\d+", re.I)),
    ("private-host", re.compile(r"\.jf" + r"da\.jo|jira\.taq" + r"neensoft|@taq" + r"neensoft", re.I)),
    ("private-ip", re.compile(r"\b(?:192\.168|10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b")),
    ("machine-path", re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+|/c/Users/|/home/[a-z][a-z0-9_-]+/|/Users/[A-Za-z][A-Za-z0-9_-]+/", re.I)),
    ("machine-user", re.compile(r"(?<![A-Za-z])ACER(?![A-Za-z])")),
    # 9+ ASCII digits. Placeholders (123456789..., one repeated digit, INT32 max as a z-index) and
    # URL path segments are not data.
    ("long-digits", re.compile(r"(?<![\w.#/-])\+?(?!123456789|0123456789|2147483|(\d)\1{8})[0-9]{9,}(?![\w.])")),
    ("phone", re.compile(r"(?<![0-9])(?:\+?962|07[789])[0-9]{7,8}(?![0-9])")),
    ("secret-assignment", re.compile(
        r"\b(?:password|passwd|pwd|pin|token|secret|api[_-]?key|client[_-]?secret)\b[\"']?\s*[:=]\s*[\"']"
        r"(?!<|\$\{|\$|%|\{\{|your|xxx|\*\*\*|changeme|example|placeholder|redacted|no-check)[^\"'\s]{4,}[\"']", re.I)),
    ("aws-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}|github[_]pat_[A-Za-z0-9_]{20,}")),
    ("openrouter-or-openai-key", re.compile(r"\bsk-(?:or-|ant-|proj-)?[A-Za-z0-9-]{20,}")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY")),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
]

FORBIDDEN_NAMES = re.compile(r"(?:^|/)(?:credentials\.json|[^/]*\.local\.json|\.env(?:\.[^/]*)?|secrets/.*)$", re.I)
FONT_EXT = {".ttf", ".otf", ".woff", ".woff2", ".eot", ".ttc"}
BINARY_EXT = {".zip", ".7z", ".rar", ".tar", ".gz", ".mp4", ".webm", ".mov", ".mp3", ".wav", ".m4a",
              ".ogg", ".flac", ".pdf", ".docx", ".xlsx", ".pptx", ".exe", ".dll", ".sqlite"}
MAX_BYTES = 2 * 1024 * 1024
# Reviewed by a person: the project's own banner artwork, not a recording or a screenshot of a system.
REVIEWED_LARGE = {"docs/assets/banner.gif", "site/assets/banner.gif"}


def files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=ROOT,
                         capture_output=True, check=True).stdout.decode("utf-8")
    return sorted(p for p in out.split("\0") if p and (ROOT / p).is_file())


def email_ok(addr: str) -> bool:
    a = addr.lower()
    return a in ALLOWED_EMAILS or a.endswith(ALLOWED_EMAIL_DOMAINS) or a.split("@")[1].count(".") == 0


def scan_text(text: str) -> list[tuple[int, str]]:
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        for name, rx in PATTERNS:
            for m in rx.finditer(line):
                if name == "email" and email_ok(m.group(0)):
                    continue
                if name == "email" and re.match(r"[\w.-]+@\d", m.group(0)):  # pkg@1.2.3
                    continue
                hits.append((n, name))
                break
    return hits


def scan() -> int:
    hits: list[str] = []
    for rel in files():
        p = ROOT / rel
        if p.resolve() == SELF:
            continue
        ext = p.suffix.lower()
        if FORBIDDEN_NAMES.search(rel):
            hits.append(f"{rel}  forbidden-file")
        if ext in FONT_EXT:
            hits.append(f"{rel}  font-file")
            continue
        if ext in BINARY_EXT:
            hits.append(f"{rel}  binary-artefact")
            continue
        if p.stat().st_size > MAX_BYTES and rel not in REVIEWED_LARGE:
            hits.append(f"{rel}  large-file")
            continue
        data = p.read_bytes()
        if b"\0" in data[:8192]:
            continue  # images and other binaries: names and size checked above
        for n, name in scan_text(data.decode("utf-8", errors="replace")):
            hits.append(f"{rel}:{n}  {name}")
    for h in hits:
        print(h)
    print(f"publish-check: {len(hits)} hit(s)")
    print("PASS" if not hits else "FAIL")
    return 1 if hits else 0


def selftest() -> int:
    bad = {
        "project-term": "see the " + "JF" + "DA portal",
        "project-term-ar": "المؤسسة العامة " + "للغذاء والدواء",
        "jira-key-private": "MO" + "AP2-77",
        "private-host": "https://staging" + ".jf" + "da.jo/",
        "private-ip": "http://192." + "168.1.20/",
        "machine-path": "C:" + "\\Users\\bob\\Desktop",
        "long-digits": "id 2000" + "123456",
        "secret-assignment": "password" + " = 'hunter22'",
        "aws-key": "AKIA" + "ABCDEFGHIJKLMNOP",
        "github-token": "ghp_" + "a" * 30,
        "openrouter-or-openai-key": "sk-or-" + "v1-" + "a" * 30,
        "jwt": "eyJ" + "a" * 12 + ".eyJ" + "b" * 12 + "." + "c" * 12,
        "email": "someone" + "@company.co",
    }
    good = ["PROJ-123 on https://jira.example.com", "password = '${JIRA_PASSWORD}'",
            "token: os.environ['TOKEN']", "naderalzghoulbusiness@gmail.com", "react@18.3.1",
            "version 2.3.0", "%USERPROFILE%\\.claude\\skills", "a SANDBOX run", "id 1234567890",
            "z-index:2147483647", '"X-Atlassian-Token": "no-check"', "jack@greensock.com"]
    fails = 0
    for name, s in bad.items():
        got = {n for _, n in scan_text(s)}
        if not got:
            print(f"selftest: {name} did not fire"); fails += 1
    for s in good:
        got = scan_text(s)
        if got:
            print(f"selftest: false positive {got[0][1]} on a clean line"); fails += 1
    print("PASS" if not fails else "FAIL")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else scan())
