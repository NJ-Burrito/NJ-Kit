"""Shared loader: pulls the ```json Matrix block out of NARRATION.md.
No third-party deps. Used by narration_brief.py, narration_check.py, guide_lint.py.
"""
import json
import re
from pathlib import Path

NARRATION_MD = Path(__file__).resolve().parent.parent / "NARRATION.md"

_BLOCK_RE = re.compile(r"```json\n(.*?)\n```", re.S)


def load_matrix(path=None):
    path = Path(path) if path else NARRATION_MD
    text = path.read_text(encoding="utf-8")
    blocks = _BLOCK_RE.findall(text)
    if not blocks:
        raise ValueError(f"no ```json block found in {path}")
    # the Matrix block is the last fenced json block in the file
    matrix = json.loads(blocks[-1])
    return matrix, text


def find_row(matrix, genre, language, destination=None):
    rows = [r for r in matrix["rows"] if r["genre"] == genre and r["language"] == language]
    if destination:
        rows = [r for r in rows if r["destination"] == destination] or rows
    return rows[0] if rows else None


def arabic_word_count(text):
    """Counting rule: split on whitespace; each whitespace-delimited token is
    one word, INCLUDING attached clitics (و-, ال-, -ه, -ها) — Arabic writes
    these joined, so this undercounts spoken syllables relative to English
    words. Stated limit: this is an orthographic-word count, not a syllable
    count; wpm bands for Arabic are pre-scaled (x0.667) to compensate, per
    NARRATION.md source_pairing notes. Diacritics (tashkil) are stripped
    first so they never inflate a token count.
    """
    tashkil = re.compile(r"[ً-ْٰ]")
    stripped = tashkil.sub("", text)
    return len([w for w in stripped.split() if w.strip()])


def word_count(text, language):
    if language == "ar":
        return arabic_word_count(text)
    return len([w for w in text.split() if w.strip()])
