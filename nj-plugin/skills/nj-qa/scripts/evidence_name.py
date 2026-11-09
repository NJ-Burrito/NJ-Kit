"""Evidence file names (owner, 2026-11-09): <issue>-<service>-<YYYY-MM-DD>-<HH.MM>[-N].<ext>, Arabic only.

  python -X utf8 evidence_name.py --issue "زر الإرسال لا يستجيب" --service "طلب تسجيل منتج" [--when "2026-11-09 14:35"] [--ext png] [--code PROJ-5494] [--dir FOLDER]
  python -X utf8 evidence_name.py --check FILE...      exit 2 and a reason for every media file whose name breaks the pattern

Import: evidence_name(issue, service, when=None, ext="png", code=None, dir=None) and name_problem(filename).
Windows cannot hold ':' so the time is HH.MM (24 h). The whole name is at most 150 characters (the service shrinks first, the issue last).
The same issue + service in the same minute gets -2, -3 ... (checked against `dir` when given). Latin words are dropped; only a code like PROJ-5494 stays, after the issue.
"""
import argparse, datetime as dt, pathlib, re, sys, unicodedata

MAX_LEN = 150
MEDIA_EXT = {"png", "jpg", "jpeg", "gif", "webp", "mp4", "webm"}
AR = "".join(chr(c) for c in (0x621, 0x2d, 0x63a, 0x641, 0x2d, 0x64a, 0x660, 0x2d, 0x669))  # ranges: letters, then Arabic-Indic digits
_TOKEN = re.compile(rf"^[{AR}0-9]+$")
_LETTER = re.compile("[" + AR[:-3] + "]")
_TAIL = re.compile(r"^(?P<head>.+)-(?P<d>\d{4}-\d{2}-\d{2})-(?P<h>\d{2})\.(?P<m>\d{2})(?:-(?P<n>\d{1,3}))?$")
_CODE = re.compile(r"\b[A-Z][A-Z0-9]{1,9}-\d+\b")


def _words(text):
    text = unicodedata.normalize("NFC", text or "")
    text = re.sub("[" + chr(0x64b) + "-" + chr(0x65f) + chr(0x670) + chr(0x640) + "]", "", text)  # tashkeel and tatweel
    return re.sub(rf"[^{AR}0-9]+", " ", text).split()


def _when(when):
    if when is None:
        return dt.datetime.now()
    if isinstance(when, dt.datetime):
        return when
    return dt.datetime.fromisoformat(re.sub(r"(\d\d)\.(\d\d)$", r"\1:\2", str(when).replace("T", " ")))


def evidence_name(issue, service, when=None, ext="png", code=None, dir=None):
    m = _CODE.search(issue or "")
    code = code or (m.group(0) if m else None)
    iw, sw = _words(_CODE.sub(" ", issue or "")), _words(_CODE.sub(" ", service or ""))
    if not iw:
        raise ValueError("evidence_name: the issue needs Arabic words naming the defect")
    if not sw:
        raise ValueError("evidence_name: the service needs its Arabic portal name")
    if code and not re.fullmatch(_CODE.pattern, code):
        raise ValueError(f"evidence_name: code {code!r} is not like PROJ-5494")
    ext = ext.lstrip(".").lower()
    t = _when(when)
    tail = f"{t:%Y-%m-%d}-{t:%H.%M}"
    n = 1
    while True:
        suffix = f"-{n}" if n > 1 else ""
        budget = MAX_LEN - len(ext) - 1 - len(tail) - 1 - len(suffix)
        a, s = list(iw), list(sw)
        join = lambda: "-".join(a + ([code] if code else []) + s)
        while len(join()) > budget:
            if len(s) > 1: s.pop()
            elif len(a) > 1: a.pop()
            else: s[0] = s[0][:max(1, len(s[0]) - (len(join()) - budget))]
        name = f"{join()}-{tail}{suffix}.{ext}"
        if not dir or not (pathlib.Path(dir) / name).exists():
            return name
        n += 1


def name_problem(filename):
    """None when the name follows the rule (or is not a picture/video), else the reason in one sentence."""
    base = pathlib.PurePath(str(filename).replace("\\", "/")).name
    stem, _, ext = base.rpartition(".")
    if ext.lower() not in MEDIA_EXT:
        return None
    why = "expected <issue>-<service>-<YYYY-MM-DD>-<HH.MM>.<ext>, Arabic words only, e.g. زر-الإرسال-لا-يستجيب-طلب-تسجيل-2026-11-09-14.35.png"
    m = _TAIL.match(stem)
    if not m:
        return f"evidence name «{base}» does not end with date and time (-YYYY-MM-DD-HH.MM); {why}"
    try:
        dt.date.fromisoformat(m["d"])
        assert int(m["h"]) < 24 and int(m["m"]) < 60
    except (ValueError, AssertionError):
        return f"evidence name «{base}» has an impossible date or time ({m['d']} {m['h']}.{m['m']}, 24-hour clock)"
    toks, arabic, i = m["head"].split("-"), 0, 0
    while i < len(toks):
        tk = toks[i]
        if arabic and re.fullmatch(r"[A-Z][A-Z0-9]{1,9}", tk) and i + 1 < len(toks) and toks[i + 1].isdigit():
            i += 2  # a ticket code such as PROJ-5494, allowed after the issue
            continue
        if not _TOKEN.match(tk):
            return f"evidence name «{base}» has a non-Arabic or forbidden part «{tk}»; {why}"
        arabic += 1
        i += 1
    if arabic < 2 or not _LETTER.search(toks[0]):
        return f"evidence name «{base}» must carry an Arabic issue and then the service; {why}"
    if len(base) > MAX_LEN:
        return f"evidence name «{base}» is {len(base)} characters, over {MAX_LEN}"
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--issue"); ap.add_argument("--service"); ap.add_argument("--when"); ap.add_argument("--ext", default="png")
    ap.add_argument("--code"); ap.add_argument("--dir"); ap.add_argument("--check", nargs="+")
    a = ap.parse_args(argv)
    if a.check:
        bad = [p for f in a.check if (p := name_problem(f))]
        for p in bad: print("REFUSED:", p)
        return 2 if bad else 0
    if not (a.issue and a.service):
        ap.error("--issue and --service are required")
    print(evidence_name(a.issue, a.service, a.when, a.ext, a.code, a.dir))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
