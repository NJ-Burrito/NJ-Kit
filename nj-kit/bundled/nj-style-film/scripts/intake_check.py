"""Stage 0 gate: is PROJECT.md filled enough to start?

    python intake_check.py <project>/PROJECT.md

Exit 0  every REQUIRED slot has a value; prints what falls back.
Exit 1  lists the REQUIRED slots still empty. Ask for exactly those, once.
Exit 2  the file is missing or unreadable.

Reads `key: value` lines only. A value is empty when it is blank, or still a
placeholder (`<...>`, `TODO`). Paths are checked for existence, because "the
file I meant" not being there is the most expensive failure to find late.
"""
import os
import re
import sys

# The film cannot start without these.
REQUIRED = {
    "narration_audio": "2. Source      the exact narration file, as a path",
    "platform":        "3. Format      where it will be posted",
    "aspect":          "3. Format      e.g. 1080x1920",
}
# One of these must be filled: a style has to come from somewhere.
STYLE_ANY = ("reference_stills", "reference_video", "what_i_like")

# Empty is fine; the fallback named in the form is used and must be recorded.
FALLBACK = {
    "cutouts_dir":   "props are DRAWN, one element each, swappable later",
    "narration_srt": "transcribe the audio once",
    "captures_dir":  "reuse the nearest existing captures, scaled",
    "fonts_dir":     "fonts and palette from the project's own tokens",
    "budget":        "normal",
    "approve":       "ask",
}
PATH_KEYS = ("narration_audio", "narration_srt", "cutouts_dir", "captures_dir", "fonts_dir", "logo")


def read(path):
    values = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"^([a-z_]+):\s*(.*)$", line.rstrip("\n"))
            if m and not m.group(1).startswith("fallback"):
                values[m.group(1)] = m.group(2).strip()
    return values


def empty(v):
    return not v or v.upper().startswith("TODO") or (v.startswith("<") and v.endswith(">"))


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    try:
        v = read(path)
    except OSError as err:
        print(f"cannot read {path}: {err}")
        return 2

    base = os.path.dirname(os.path.abspath(path))
    missing = [label for key, label in REQUIRED.items() if empty(v.get(key, ""))]
    if all(empty(v.get(k, "")) for k in STYLE_ANY):
        missing.append("4. Style       at least one of reference_stills / reference_video / what_i_like")

    bad_paths = []
    for key in PATH_KEYS:
        val = v.get(key, "")
        if empty(val):
            continue
        for part in [p.strip() for p in val.split(",") if p.strip()]:
            full = part if os.path.isabs(part) else os.path.join(base, part)
            if not os.path.exists(full):
                bad_paths.append(f"{key}: {part}")

    budget = v.get("budget", "") or "normal"
    if budget not in ("cheap", "normal", "best"):
        missing.append(f"8. Run shape   budget must be cheap, normal or best (got: {budget})")

    if missing or bad_paths:
        print("NOT READY. Ask for exactly these, in one message, then stop:\n")
        for m in missing:
            print(f"  - {m}")
        for b in bad_paths:
            print(f"  - path does not exist -> {b}")
        return 1

    print(f"READY. budget={budget}  approve={v.get('approve') or 'ask'}\n")
    used = [f"{k} -> {why}" for k, why in FALLBACK.items() if empty(v.get(k, ""))]
    if used:
        print("Fallbacks in force. Write each under '## Fallbacks used':")
        for u in used:
            print(f"  - {u}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
