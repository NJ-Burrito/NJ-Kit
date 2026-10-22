#!/usr/bin/env python
"""narration_brief.py — reads a filled NARRATION-BRIEF.md, prints missing
REQUIRED slots (exit 1) or the tailored rule sheet for that exact request:
the matrix row, the words budget for the stated length, the structure to
follow, the five highest-risk mistakes for that genre/language combo, and
which checks narration_check.py will run. stdlib only.

Usage:
    PYTHONUTF8=1 python narration_brief.py <brief.md>
    PYTHONUTF8=1 python narration_brief.py --selftest
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _matrix import load_matrix, find_row  # noqa: E402

REQUIRED = ["genre", "language", "destination", "length_s", "audience", "listener_action"]
OPTIONAL_FALLBACKS = {
    "kb_ids": "none — no sourced facts in this script",
    "lexicon_terms": "templates/LEXICON.md defaults only",
    "tone_words": "the matrix row's `register` field",
    "bans": "none stated",
}

# Five highest-risk mistakes per genre, drawn from the guide + devil pass.
RISKS = {
    "commercial": [
        "words over budget for the stated length (the 15s-against-20s fault)",
        "no single stressed CTA verb — buried or duplicated",
        "flat list reading (no pitch-reset cue in the text)",
        "unfalsifiable adjective with no proof/source",
        "no direction: line on the hook beat",
    ],
    "educational": [
        "sentence length not varied beat-to-beat (monotone cadence)",
        "no recap naming the ONE thing to know",
        "wpm too fast for comprehension of complex material (f04 direction only, no bound)",
        "signpost words with no pitch lift",
        "missing kb:#id on a factual claim",
    ],
    "walkthrough": [
        "narration outruns the on-screen action (say-then-do violated)",
        "more than one action per sentence",
        "UI label not quoted verbatim as it reads on screen",
        "no confirmation line at the end of a step",
        "flat delivery reading as bored, not competent",
    ],
    "podcast": [
        "chapter boundary with no real pause (500-800ms house default)",
        "ad-read disclosure omitted",
        "sentence length not varied (least conversational-sounding failure)",
        "more than one CTA (should be one ask in the outro)",
        "outro too loud/energetic instead of intimate",
    ],
    "event_promo": [
        "no date/place/link in the CTA",
        "words over budget for a short social cut",
        "hook window (3s) missed",
        "urgency tone read as generic commercial energy",
        "no direction: line on the CTA beat",
    ],
    "recruitment": [
        "role/programme described inaccurately (no source discipline)",
        "more than one apply-CTA (must be exactly once, at the end)",
        "aspirational claim with no proof",
        "wrong register (too casual for accuracy-bearing content)",
        "no direction: line carrying trust/aspiration",
    ],
    "investor_partnership": [
        "a traction figure with no kb:#id",
        "more than one checkable ask",
        "sentence length exceeds educational ceiling",
        "arc missing its lift-on-traction beat",
        "register drifts from precise-conversational into pure pitch-deck jargon",
    ],
}


def parse_brief(path):
    slots = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip().lower().replace(" ", "_")
        val = val.strip()
        if val:
            slots[key] = val
    return slots


def words_budget_field(length_s):
    return f"words_budget_{length_s}s"


def build_sheet(slots, matrix):
    genre = slots["genre"]
    language = slots["language"]
    destination = slots.get("destination")
    row = find_row(matrix, genre, language, destination)
    if row is None:
        return None, f"no matrix row for genre={genre} language={language}"
    length_s = slots["length_s"]
    field = words_budget_field(length_s)
    budget = row.get(field, f"no exact-length budget field '{field}' — nearest rows: "
                             + ", ".join(k for k in row if k.startswith("words_budget_")))
    lines = []
    lines.append(f"RULE SHEET — {genre} / {language} / {row['destination']}")
    lines.append(f"matrix row: wpm {row['wpm_min']}-{row['wpm_max']} [{row['wpm_source']}]")
    lines.append(f"words budget for {length_s}s: {budget}")
    lines.append(f"structure (required_parts): {', '.join(row['required_parts'])}")
    lines.append(f"register: {row['register']}")
    lines.append(f"cta_rule: {row['cta_rule']}")
    lines.append(f"silence_ratio_max: {row['silence_ratio_max']} [{row['silence_ratio_max_source']}]")
    lines.append(f"loudness_target_lufs: {row['loudness_target_lufs']} [{row['loudness_target_source']}]")
    lines.append("top-5 risks for this combination:")
    for r in RISKS.get(genre, ["(no risk list for this genre yet)"]):
        lines.append(f"  - {r}")
    lines.append("checks narration_check.py will run: word budget, sentence-length ceiling, "
                  "direction: line present, digit/numeral policy, lexicon form, kb:#id sourcing, "
                  "required structural parts, emotional arc declared, and (if a pair) beat-count "
                  "and duration-drift match.")
    for k, fallback in OPTIONAL_FALLBACKS.items():
        if k not in slots:
            lines.append(f"NOTE: '{k}' not given in brief — falls back to: {fallback}")
    return "\n".join(lines), None


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if len(argv) != 2:
        print("usage: narration_brief.py <brief.md> | --selftest")
        return 1
    brief_path = argv[1]
    slots = parse_brief(brief_path)
    missing = [s for s in REQUIRED if s not in slots]
    if missing:
        print("MISSING REQUIRED SLOTS: " + ", ".join(missing))
        return 1
    matrix, _ = load_matrix()
    sheet, err = build_sheet(slots, matrix)
    if err:
        print("ERROR: " + err)
        return 1
    print(sheet)
    return 0


def selftest():
    import tempfile, os
    matrix, _ = load_matrix()
    ok = True

    # 1. missing required slots -> exit 1
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("genre: commercial\nlanguage: en\n")
        path = f.name
    slots = parse_brief(path)
    missing = [s for s in REQUIRED if s not in slots]
    assert missing, "expected missing slots"
    os.unlink(path)

    # 2. complete brief -> a rule sheet builds for every genre in the matrix
    genres = sorted({r["genre"] for r in matrix["rows"]})
    for g in genres:
        row = find_row(matrix, g, "en")
        assert row is not None, f"no en row for {g}"
        slots = {
            "genre": g, "language": "en", "destination": row["destination"],
            "length_s": "30" if "words_budget_30s" in row else "60",
            "audience": "test", "listener_action": "test",
        }
        sheet, err = build_sheet(slots, matrix)
        assert err is None and sheet, f"sheet build failed for {g}: {err}"

    # 3. unknown genre -> error, not a crash
    sheet, err = build_sheet({"genre": "not_a_genre", "language": "en", "length_s": "30"}, matrix)
    assert sheet is None and err

    # 4. Arabic row exists for every genre too
    for g in genres:
        assert find_row(matrix, g, "ar") is not None, f"no ar row for {g}"

    print("SELFTEST PASS: %d genres, missing-slot detection ok, unknown-genre error ok" % len(genres))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
