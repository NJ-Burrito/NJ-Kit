#!/usr/bin/env python
"""narration_check.py — given a script (one beat per line, blank-line
separated blocks; a beat may carry `direction:`, `kb:#id`, `seconds:N`) plus
a brief, FAILS before a word is voiced. It reports; it never rewrites.
stdlib only.

Script format, one beat per block:
    direction: warm, confident, lean in on the last three words
    kb:12
    Ensera trains the people who will build the region's AI.

Usage:
    PYTHONUTF8=1 python narration_check.py <script.md> <brief.md> [pair_script.md pair_brief.md]
    PYTHONUTF8=1 python narration_check.py --selftest
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _matrix import load_matrix, find_row, word_count  # noqa: E402
from narration_brief import parse_brief, words_budget_field  # noqa: E402

DIGIT_RE = re.compile(r"\d")
NUMBER_WORD_RE = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|million|billion|percent)\b",
    re.I,
)
KB_RE = re.compile(r"kb:#?\d+", re.I)


def parse_script(text):
    """Returns a list of beats: {direction, kb, seconds, text}."""
    beats = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [l for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        beat = {"direction": None, "kb": None, "seconds": None, "text_lines": []}
        for line in lines:
            low = line.strip().lower()
            if low.startswith("direction:"):
                beat["direction"] = line.split(":", 1)[1].strip()
            elif low.startswith("kb:"):
                beat["kb"] = line.split(":", 1)[1].strip()
            elif low.startswith("seconds:"):
                beat["seconds"] = float(line.split(":", 1)[1].strip())
            else:
                beat["text_lines"].append(line.strip())
        beat["text"] = " ".join(beat["text_lines"])
        beats.append(beat)
    return beats


def check_script(script_text, slots, matrix, require_kb=False, require_arc=True):
    """Returns list of FAIL strings (empty = pass) and list of WARN strings."""
    fails, warns = [], []
    genre = slots["genre"]
    language = slots["language"]
    row = find_row(matrix, genre, language, slots.get("destination"))
    if row is None:
        return [f"no matrix row for {genre}/{language}"], []

    beats = parse_script(script_text)
    if not beats:
        return ["script has no beats"], []

    length_s = slots.get("length_s")
    field = words_budget_field(length_s) if length_s else None
    total_words = sum(word_count(b["text"], language) for b in beats)

    if field and field in row:
        budget = row[field]
        low, high = budget * 0.9, budget * 1.1
        if not (low <= total_words <= high):
            fails.append(
                f"word budget: {total_words} words vs {budget} budget for {length_s}s "
                f"(allowed {low:.0f}-{high:.0f}) — this is the '12s speech for a 20s film' fault"
            )
    else:
        warns.append(f"no exact words_budget field for length_s={length_s}; word-budget check skipped")

    max_words_sentence = row.get("max_words_per_sentence")
    for i, b in enumerate(beats):
        sentences = [s for s in re.split(r"[.!?؟]", b["text"]) if s.strip()]
        for s in sentences:
            n = word_count(s, language)
            if max_words_sentence and n > max_words_sentence:
                fails.append(f"beat {i}: sentence of {n} words exceeds ceiling {max_words_sentence}")
        if not b["direction"]:
            fails.append(f"beat {i}: no direction: line")
        has_number = DIGIT_RE.search(b["text"]) or NUMBER_WORD_RE.search(b["text"])
        if require_kb and has_number and not b["kb"] and not KB_RE.search(b["text"]):
            fails.append(f"beat {i}: contains a number/claim with no kb:#id")
        # numeral policy: language 'ar' must spell digits out
        if language == "ar" and DIGIT_RE.search(b["text"]):
            fails.append(f"beat {i}: Arabic beat has a raw digit — numeral_policy requires spelled-out words")
        wpm = (row["wpm_min"] + row["wpm_max"]) / 2
        expected_s = word_count(b["text"], language) / (wpm / 60)
        if b["seconds"] is not None:
            drift = abs(b["seconds"] - expected_s) / max(expected_s, 0.01)
            if drift > 0.45:  # voice.py's own redraw threshold, measured
                fails.append(f"beat {i}: seconds={b['seconds']} vs expected~{expected_s:.1f}s (drift {drift:.0%})")

    required_parts = row.get("required_parts", [])
    if required_parts and len(beats) < len(required_parts):
        warns.append(f"fewer beats ({len(beats)}) than required_parts ({len(required_parts)}) — check structure by hand")

    if require_arc and not any("arc" in (b["direction"] or "").lower() or i in (0, len(beats) - 1) for i, b in enumerate(beats)):
        pass  # arc is a house-default guidance check, not enforced as hard fail here

    return fails, warns


def check_pair(script_a, slots_a, script_b, slots_b, matrix, tolerance=0.20):
    fails = []
    beats_a = parse_script(script_a)
    beats_b = parse_script(script_b)
    if len(beats_a) != len(beats_b):
        fails.append(f"pair beat-count mismatch: {len(beats_a)} vs {len(beats_b)}")
        return fails
    row_a = find_row(matrix, slots_a["genre"], slots_a["language"], slots_a.get("destination"))
    row_b = find_row(matrix, slots_b["genre"], slots_b["language"], slots_b.get("destination"))
    for i, (ba, bb) in enumerate(zip(beats_a, beats_b)):
        wa = word_count(ba["text"], slots_a["language"])
        wb = word_count(bb["text"], slots_b["language"])
        wpm_a = (row_a["wpm_min"] + row_a["wpm_max"]) / 2
        wpm_b = (row_b["wpm_min"] + row_b["wpm_max"]) / 2
        dur_a = wa / (wpm_a / 60)
        dur_b = wb / (wpm_b / 60)
        drift = abs(dur_a - dur_b) / max(dur_a, dur_b, 0.01)
        if drift > tolerance:
            fails.append(f"beat {i}: pair duration drift {drift:.0%} exceeds tolerance {tolerance:.0%}")
    return fails


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if len(argv) not in (3, 5):
        print("usage: narration_check.py <script.md> <brief.md> [pair_script.md pair_brief.md]")
        return 1
    matrix, _ = load_matrix()
    script_text = Path(argv[1]).read_text(encoding="utf-8")
    slots = parse_brief(argv[2])
    fails, warns = check_script(script_text, slots, matrix, require_kb=slots.get("kb_ids", "").lower() != "none")
    for w in warns:
        print("WARN: " + w)
    for f in fails:
        print("FAIL: " + f)
    if len(argv) == 5:
        script_b = Path(argv[3]).read_text(encoding="utf-8")
        slots_b = parse_brief(argv[4])
        pair_fails = check_pair(script_text, slots, script_b, slots_b, matrix)
        for f in pair_fails:
            print("FAIL (pair): " + f)
        fails += pair_fails
    print("RESULT: %s (%d fail, %d warn)" % ("FAIL" if fails else "PASS", len(fails), len(warns)))
    return 1 if fails else 0


def selftest():
    matrix, _ = load_matrix()
    base_slots = {"genre": "commercial", "language": "en", "destination": "social_video", "length_s": "15"}
    controls = []

    # 1. 12s of speech for a 20s film fails (the founding fault)
    row = find_row(matrix, "commercial", "en", "social_video")
    wpm = (row["wpm_min"] + row["wpm_max"]) / 2
    words_for_12s = round(wpm / 60 * 12)
    text = " ".join(["word"] * words_for_12s)
    script = f"direction: calm\nkb:1\n{text}"
    slots20 = dict(base_slots, length_s="30")  # nearest budget field available (words_budget_30s)
    fails, warns = check_script(script, slots20, matrix)
    controls.append(("12s speech for a 30s-budget beat fails word budget",
                      any("word budget" in f for f in fails)))

    # 2. missing direction: line fails
    script = "kb:1\nEnsera builds the future of AI training in Jordan and beyond today now."
    fails, warns = check_script(script, base_slots, matrix)
    controls.append(("missing direction: line fails", any("no direction" in f for f in fails)))

    # 3. sentence over max_words_per_sentence fails
    long_sentence = " ".join(["word"] * 30)
    script = f"direction: calm\nkb:1\n{long_sentence}."
    fails, warns = check_script(script, base_slots, matrix)
    controls.append(("30-word sentence exceeds ceiling", any("exceeds ceiling" in f for f in fails)))

    # 4. Arabic beat with a raw digit fails numeral policy
    ar_slots = {"genre": "commercial", "language": "ar", "destination": "social_video", "length_s": "15"}
    script = "direction: دافئ\nإنسيرا تدرب 80 طالباً هذا العام."
    fails, warns = check_script(script, ar_slots, matrix)
    controls.append(("Arabic raw digit fails numeral policy", any("raw digit" in f for f in fails)))

    # 5. Arabic word count handles clitics/diacritics without crashing
    from _matrix import arabic_word_count
    n1 = arabic_word_count("وَالطُّلَّابُ يَتَعَلَّمُونَ")
    n2 = arabic_word_count("والطلاب يتعلمون")
    controls.append(("Arabic word count strips diacritics consistently", n1 == n2 and n1 == 2))

    # 6. digit/number with no kb id fails when sourcing required
    script = "direction: calm\nEnsera trained five hundred students this year."
    fails, warns = check_script(script, base_slots, matrix, require_kb=True)
    controls.append(("number with no kb:#id fails when sourcing required",
                      any("kb:#id" in f for f in fails)))

    # 7. clean, well-formed English script passes with no fails
    words_needed = row.get("words_budget_15s", 38)
    # short sentences (<=12 words each, the row's ceiling), no digits/number-words
    sentence = "This works well for the whole region now."  # 8 words
    n_sentences = max(1, round(words_needed / 8))
    clean_text = " ".join([sentence] * n_sentences)
    script = f"direction: confident, warm\nkb:1\n{clean_text}"
    fails, warns = check_script(script, base_slots, matrix, require_kb=True)
    controls.append(("clean well-formed script has zero FAILs", len(fails) == 0))

    # 8. bilingual pair beat-count mismatch fails
    fails_pair = check_pair("direction: a\nkb:1\nOne.", base_slots,
                             "direction: b\nkb:1\nOne.\n\ndirection: c\nkb:1\nTwo.",
                             ar_slots, matrix)
    controls.append(("pair beat-count mismatch fails", any("beat-count mismatch" in f for f in fails_pair)))

    # 9. bilingual pair duration drift beyond tolerance fails
    long_en = " ".join(["word"] * 40)
    fails_pair2 = check_pair(f"direction: a\nkb:1\n{long_en}.", base_slots,
                              "direction: b\nkb:1\nكلمة واحدة قصيرة فقط.", ar_slots, matrix)
    controls.append(("pair duration drift beyond tolerance fails", len(fails_pair2) > 0))

    print("SELFTEST negative controls:")
    ok = True
    for name, passed in controls:
        print(f"  [{'OK' if passed else 'FAIL'}] {name}")
        ok = ok and passed
    print("SELFTEST %s: %d controls" % ("PASS" if ok else "FAIL", len(controls)))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
