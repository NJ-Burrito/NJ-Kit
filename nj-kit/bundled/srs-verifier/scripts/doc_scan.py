#!/usr/bin/env python
"""Mechanical pass of a document verification audit — the machine half of srs-verifier.

Domain-neutral. Everything specific to a project lives in a profile.json
(`profile.example.json`; schema in references/evidence-profiles.md). With no
profile, generic defaults apply and the run is worth much less.

    python doc_scan.py DOC [DOC2] --profile profile.json --out results/

DOC is .pdf, .txt or .md. PDFs are read with poppler `pdftotext -enc UTF-8`
only: pymupdf and pdfium drop Arabic words silently (measured 6/9 and 0/9
against poppler's 9/9 on one sentence). Two documents diff two revisions; the
first is the baseline.

Emits CANDIDATES, not findings. Every row is confirmed at the source — on the
rendered page, in the model, in the registry — or dropped. It also prints the
evidence ladder the profile declares and says which tiers are missing; the
missing ones become reservations in section 8 of the report.

Windows: run with PYTHONUTF8=1.
"""

from __future__ import annotations

import argparse
import csv
import glob as globmod
import json
import os
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fold_ar import CORRUPTION, fold, pdftotext  # noqa: E402  the house normaliser

if hasattr(sys.stdout, "reconfigure"):          # a cp1252 console cannot print
    sys.stdout.reconfigure(encoding="utf-8")    # one Arabic character
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# --------------------------------------------------------------------------- defaults

DEFAULTS = {
    "id_patterns": {
        "requirement": r"(?:FR|NFR|REQ)-\d{1,4}",
        "business_rule": r"BR-\d{1,4}",
        "user_story": r"US-\d{1,4}",
        "acceptance": r"AC-\d{1,4}",
        "error_code": r"ERROR[_-]\d+",
    },
    "sequential_ids": ["requirement", "business_rule", "user_story"],
    "cross_ref_patterns": [r"(?:FR|NFR|REQ|BR|US|AC)-\d{1,4}"],
    "optionality_markers": {
        "optional": ["optional", "not required", "اختياري", "غير اجباري", "غير إجباري"],
        "mandatory": ["mandatory", "required", "اجباري", "إجباري", "حقل إجباري"],
    },
    "promise_markers": [
        "notification", "notify", "sms", "email", "certificate", "output", "within",
        "deadline", "sla", "guarantee", "will receive",
        "إشعار", "رسالة نصية", "بريد إلكتروني", "مخرج", "شهادة", "خلال", "مهلة",
    ],
    "vague_terms": [
        "as needed", "as appropriate", "promptly", "regularly", "periodically",
        "sufficient", "adequate", "user-friendly", "etc.", "and so on", "if necessary",
        "حسب الحاجة", "بشكل مناسب", "دوريا", "عند الضرورة", "بشكل دوري", "الخ",
    ],
    "testable_verbs": [
        "shall", "must", "displays", "display", "rejects", "reject", "sends", "send",
        "returns", "return", "prevents", "prevent", "validates", "requires",
        "يجب", "يعرض", "يرفض", "يرسل", "يمنع", "ينقل", "يتحقق", "يوزع", "يلغي",
    ],
    "required_table_columns": [],
}

# Latin identifiers survive text extraction; Arabic frequently does not. The
# corruption signatures are fold_ar's, so the scanner and --check-extraction
# agree on what a broken extraction looks like. See references/extraction-traps.md.
MANGLE_SIGNATURES = list(CORRUPTION.items())

ARABIC_RANGE = re.compile(r"[؀-ۿ]")


# --------------------------------------------------------------------------- helpers

def load_config(path: str | None) -> dict:
    cfg = json.loads(json.dumps(DEFAULTS))
    if not path:
        return cfg
    with open(path, encoding="utf-8") as fh:
        user = json.load(fh)
    for key, value in user.items():
        if isinstance(value, dict) and isinstance(cfg.get(key), dict):
            cfg[key].update(value)
        else:
            cfg[key] = value
    return cfg


def read_text(path: str) -> str:
    """Extract text with page markers. PDFs go through poppler, never pymupdf."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        raw = pdftotext(path, None)
        pages = raw.split("\f")
        if pages and not pages[-1].strip():
            pages.pop()
        return "\n".join(f"\n[[page {i + 1}]]\n{t}" for i, t in enumerate(pages))
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def normalise_ar(text: str) -> str:
    """The house normaliser (fold_ar.fold) plus whitespace collapse.

    Folding is for matching only. Quote the original in every report row.
    """
    return re.sub(r"\s+", " ", fold(text)).strip()


def page_of(text: str, index: int) -> str:
    marks = [m for m in re.finditer(r"\[\[page (\d+)\]\]", text) if m.start() <= index]
    return marks[-1].group(1) if marks else "?"


def boundary_re(term: str) -> re.Pattern:
    """Match a term only as a whole word.

    Arabic letters are word characters, so \\b behaves correctly for them: without this,
    'الخ' matches inside 'الخدمة' and floods the output with false positives.
    """
    pattern = re.escape(term)
    if term[:1].isalnum() or ARABIC_RANGE.match(term[:1] or " "):
        pattern = r"\b" + pattern
    if term[-1:].isalnum() or ARABIC_RANGE.match(term[-1:] or " "):
        pattern = pattern + r"\b"
    return re.compile(pattern, re.IGNORECASE)


def lines_with(text: str, term: str) -> list[tuple[int, str]]:
    rx = boundary_re(term)
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        if rx.search(line):
            out.append((n, line.strip()))
    return out


# --------------------------------------------------------------------------- checks

def check_extraction(text: str) -> list[dict]:
    rows = []
    for sig, why in MANGLE_SIGNATURES:
        if sig in text:
            rows.append(_row("EXTRACTION", "HIGH",
                             f"Extraction distortion detected ({why}); Arabic searches "
                             f"return false zeros. Confirm counts on rendered pages.",
                             sig, ""))
            break
    # 'V03' reversed to '03V' is the signature; a plain 'V03' is fine.
    if ARABIC_RANGE.search(text) and re.search(r"(?<![\w/.-])\d{2}V\b", text):
        rows.append(_row("EXTRACTION", "MED",
                         "Latin/digit runs appear reordered around Arabic text; anchor "
                         "comparisons on identifier cores, not on full strings.", "", ""))
    return rows


def check_identifiers(text: str, cfg: dict) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    found: dict[str, list[str]] = {}
    for kind, pattern in cfg["id_patterns"].items():
        hits = re.findall(pattern, text)
        found[kind] = hits
        if not hits:
            continue
        counts = Counter(hits)
        uniq = sorted(set(hits))

        if kind in cfg.get("sequential_ids", []):
            nums = sorted({int(re.search(r"(\d+)$", h).group(1)) for h in uniq})
            span = nums[-1] - nums[0] + 1
            gaps = [n for n in range(nums[0], nums[-1] + 1) if n not in nums]
            if gaps:
                shown = ", ".join(map(str, gaps[:15]))
                more = f" (+{len(gaps) - 15} more)" if len(gaps) > 15 else ""
                # Mostly-holes means this is not one contiguous series: a consolidated
                # document quoting several documents' identifiers, not a numbering break.
                sparse = len(gaps) > span / 2
                rows.append(_row("ID-GAP", "LOW" if sparse else "MED",
                                 f"{kind}: {len(gaps)} number(s) missing from the range "
                                 f"{nums[0]}-{nums[-1]}: {shown}{more}. "
                                 + ("Sparse, so probably identifiers quoted from several "
                                    "documents rather than one broken sequence; confirm the "
                                    "series boundary."
                                    if sparse else
                                    "Traceability break or a deleted item."),
                                 shown + more, ""))

        dupes = [i for i, n in counts.items() if n > 1 and i in definitions(text, pattern)
                 and definitions(text, pattern).count(i) > 1]
        for ident in sorted(set(dupes)):
            rows.append(_row("ID-DUPLICATE", "HIGH",
                             f"{ident} is defined more than once. Two items share one "
                             f"identifier, so every reference to it is ambiguous.",
                             ident, str(page_of(text, text.find(ident)))))
    return rows, found


def definitions(text: str, pattern: str) -> list[str]:
    """Identifiers at either end of a line: the definition sites.

    Anywhere else the identifier is a reference to something defined elsewhere.
    The prefix class swallows the bidi and joiner marks a PDF extraction puts
    around a cell's text, and the end-of-line form is needed because a
    right-to-left table extracts its identifier at the end of the line as often
    as at the start. Without both, XREF-DANGLING fires on every id in the
    document, which is a false alarm loud enough to hide the real ones.
    """
    cls = r"[\s|>*#.\-​-‏‪-‮⁦-⁩﻿]*"
    head = re.compile(r"^" + cls + r"(" + pattern + r")", re.MULTILINE)
    tail = re.compile(r"(" + pattern + r")" + cls + r"$", re.MULTILINE)
    # Dedupe by position: a cell holding only 'FR-01' matches both patterns, and
    # counting it twice would invent an ID-DUPLICATE finding.
    at: dict[int, str] = {}
    for rx in (head, tail):
        for m in rx.finditer(text):
            at[m.start(1)] = m.group(1)
    return [at[k] for k in sorted(at)]


def check_cross_refs(text: str, found: dict, cfg: dict) -> list[dict]:
    rows = []
    for pattern in cfg.get("cross_ref_patterns", []):
        defined = set(definitions(text, pattern))
        for ref in sorted(set(re.findall(pattern, text))):
            if ref not in defined:
                rows.append(_row("XREF-DANGLING", "HIGH",
                                 f"{ref} is referenced but never defined here: no line or "
                                 f"table row starts with it. Either the definition is "
                                 f"missing, or the reference points at another document.",
                                 ref, str(page_of(text, text.find(ref)))))
    return rows


def check_lists(text: str) -> list[dict]:
    """Repeated and near-duplicate entries inside one enumerated list."""
    rows = []
    for line in text.splitlines():
        if line.count("،") + line.count(",") < 2:
            continue
        parts = [p.strip() for p in re.split(r"[،,]", line) if p.strip()]
        if len(parts) < 3:
            continue
        norm = [normalise_ar(p).replace(" ", "") for p in parts]
        seen: dict[str, str] = {}
        for original, key in zip(parts, norm):
            if not key:
                continue
            if key in seen:
                rows.append(_row("LIST-DUP", "MED",
                                 f"List repeats '{original}'"
                                 + (f" (also written '{seen[key]}')"
                                    if seen[key] != original else "") + ".",
                                 line.strip()[:120], ""))
            seen[key] = original

        # Same value under two spellings: 'كيلوغرام' beside 'كيلو جرام'. Normalisation
        # cannot fold these because the letters genuinely differ, so compare by similarity.
        keys = list(seen)
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                a, b = keys[i], keys[j]
                if min(len(a), len(b)) < 4:
                    continue
                if SequenceMatcher(None, a, b).ratio() >= 0.8:
                    rows.append(_row("LIST-NEAR-DUP", "MED",
                                     f"List holds two near-identical entries, "
                                     f"'{seen[a]}' and '{seen[b]}'. Usually one value "
                                     f"spelled two ways, which makes the option ambiguous.",
                                     line.strip()[:120], ""))
    return rows


def check_unsourced_numbers(text: str) -> list[dict]:
    """Numbers added in parentheses beside a value name; they rarely exist in registries."""
    rows = []
    for m in re.finditer(r"[)(]\s*[-−]?\d+(?:[.,]\d+)?\s*(?:°|درجة|مئوية|C\b|%|[A-Za-z]{0,12})\s*[)(]", text):
        frag = text[max(0, m.start() - 60): m.end() + 20].replace("\n", " ")
        rows.append(_row("NUM-UNSOURCED", "LOW",
                         "Parenthesised number attached to a value name. Confirm it exists "
                         "in the registry rather than only in this document.",
                         frag.strip()[:140], str(page_of(text, m.start()))))
    return rows


def check_optionality(text: str, cfg: dict) -> list[dict]:
    """Inventory of items called optional, for manual testing against the enforcement tier."""
    rows = []
    markers = cfg["optionality_markers"]["optional"]
    ntext = normalise_ar(text)
    for marker in markers:
        nm = normalise_ar(marker)
        hits = len(boundary_re(nm).findall(ntext)) if nm else 0
        if hits:
            rows.append(_row("OPTIONAL-INVENTORY", "HIGH",
                             f"{hits} occurrence(s) of '{marker}'. Every one must be tested "
                             f"against the enforced-behaviour tier (validation/error "
                             f"catalogue, regulation). This is the highest-yield check.",
                             marker, ""))
    return rows


def check_promises(text: str, cfg: dict) -> list[dict]:
    rows = []
    ntext = normalise_ar(text)
    for marker in cfg["promise_markers"]:
        nm = normalise_ar(marker)
        hits = len(boundary_re(nm).findall(ntext)) if nm else 0
        if hits:
            rows.append(_row("PROMISE", "MED",
                             f"{hits} occurrence(s) of '{marker}'. Each promise needs a named "
                             f"mechanism in the executing artefact; report the count and the "
                             f"location of the mechanisms found.",
                             marker, ""))
    return rows


def check_vague(text: str, cfg: dict) -> list[dict]:
    rows = []
    for term in cfg["vague_terms"]:
        for n, line in lines_with(text, term):
            rows.append(_row("VAGUE", "MED",
                             f"Untestable wording '{term}': no test can pass or fail it. "
                             f"Replace with a value or delete.",
                             line[:140], str(page_of(text, text.find(line)))))
    return rows


def check_testability(text: str, cfg: dict) -> list[dict]:
    """Requirement-shaped lines carrying no testable verb."""
    rows = []
    verbs = [normalise_ar(v) for v in cfg["testable_verbs"]]
    id_re = re.compile("|".join(cfg["id_patterns"].values()))
    for line in text.splitlines():
        stripped = line.strip()
        if len(stripped) < 20 or not id_re.search(stripped):
            continue
        norm = normalise_ar(stripped)
        if not any(v and v in norm for v in verbs):
            rows.append(_row("UNTESTABLE", "LOW",
                             "Requirement-shaped line with no testable verb; may state a "
                             "capability rather than a checkable behaviour.",
                             stripped[:140], str(page_of(text, text.find(stripped)))))
    return rows


def check_columns(text: str, cfg: dict) -> list[dict]:
    rows = []
    ntext = normalise_ar(text).lower()
    for col in cfg.get("required_table_columns", []):
        norm = normalise_ar(col).lower()
        if norm in ntext:
            continue
        # A two-word header wrapped onto two lines extracts with other cells
        # between its halves, so the full string is absent while the column is
        # there. Measured on the first real run: both TEMPLATE candidates were
        # this. Check the parts before calling a column missing.
        parts = [w for w in norm.split() if len(w) > 2]
        if parts and all(w in ntext for w in parts):
            rows.append(_row("TEMPLATE", "MED",
                             f"Template column '{col}' not found as one string, but every "
                             f"word of it is present. Usually a header wrapped onto two "
                             f"lines. Confirm on the rendered page before reporting it.",
                             col, ""))
            continue
        rows.append(_row("TEMPLATE", "HIGH",
                         f"Template column '{col}' not found. Missing columns are where "
                         f"value lists and limits live, so this is usually the cause of "
                         f"other gaps, not a cosmetic deviation.", col, ""))
    return rows


def compare_revisions(a: str, b: str, cfg: dict) -> list[dict]:
    rows = []
    for kind, pattern in cfg["id_patterns"].items():
        set_a, set_b = set(re.findall(pattern, a)), set(re.findall(pattern, b))
        removed, added = sorted(set_a - set_b), sorted(set_b - set_a)
        if removed:
            rows.append(_row("DIFF-REMOVED", "HIGH",
                             f"{kind}: {len(removed)} identifier(s) gone. Search the new "
                             f"document for their content before calling them deleted; rules "
                             f"migrate into other columns.", ", ".join(removed[:20]), ""))
        if added:
            rows.append(_row("DIFF-ADDED", "MED",
                             f"{kind}: {len(added)} new identifier(s).",
                             ", ".join(added[:20]), ""))
        if removed and added and len(removed) > 3 and len(added) > 3:
            rows.append(_row("DIFF-RENUMBER", "HIGH",
                             f"{kind}: wholesale renumbering. Without a mapping table this "
                             f"breaks traceability to every prior review, test case and "
                             f"ticket.", "", ""))
    va = set(re.findall(r"\bV\d{2}\b|\b\d{2}V\b", a))
    vb = set(re.findall(r"\bV\d{2}\b|\b\d{2}V\b", b))
    if va and va == vb and normalise_ar(a) != normalise_ar(b):
        rows.append(_row("DIFF-VERSION", "HIGH",
                         "Content changed while the cover version stayed the same. Nothing "
                         "tells a reader the document is different.", ", ".join(sorted(va)), ""))
    return rows


def report_ladder(cfg: dict, profile_path: str | None) -> list[str]:
    """Print the evidence ladder the profile declares and check each source exists.

    Returns the tiers that are missing. Each missing tier disables checks and
    becomes a reservation in section 8 of the report. Nothing here reads a
    credential: a profile names where credentials live, and the name is all
    that is ever printed.
    """
    ladder = cfg.get("evidence_ladder") or {}
    if not ladder:
        return []
    here = (os.path.dirname(os.path.abspath(profile_path))
            if profile_path else os.getcwd())
    root = cfg.get("root")
    base = here if not root else (root if os.path.isabs(root)
                                  else os.path.normpath(os.path.join(here, root)))
    missing: list[str] = []
    print("Evidence ladder (profile: %s)" % os.path.basename(profile_path or "-"))
    for tier in sorted(ladder):
        item = ladder[tier]
        if isinstance(item, str):
            print(f"  {tier:30} {item}   [not path-checked]")
            continue
        path = item.get("path") or item.get("glob") or ""
        settles = item.get("settles", "")
        if not path:
            print(f"  {tier:30} {item.get('note', 'declared, no path')}")
            continue
        full = path if os.path.isabs(path) else os.path.join(base, path)
        hits = globmod.glob(full)
        if hits:
            print(f"  {tier:30} FOUND {len(hits):>4}  {path}   {settles}")
        else:
            missing.append(f"{tier} ({path})")
            print(f"  {tier:30} MISSING     {path}   {settles}")
    live = cfg.get("live_ui") or {}
    if live.get("base_url"):
        creds = live.get("credentials_at")
        print(f"  {'live_ui':30} {live['base_url']}"
              + (f"   credentials in {creds} (never printed)" if creds else ""))
    if missing:
        print("\nMissing tiers - every check they would settle is a reservation, "
              "not a silent gap:\n  " + "\n  ".join(missing))
    print()
    return missing


def _row(check: str, sev: str, note: str, evidence: str, page: str) -> dict:
    return {"check": check, "severity": sev, "note": note,
            "evidence": evidence, "page": page}


# --------------------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docs", nargs="+", help=".pdf, .txt or .md; two documents diffs revisions")
    ap.add_argument("--profile", "--config", dest="config",
                    help="profile.json for this domain (see profile.example.json)")
    ap.add_argument("--out", default="doc_scan_out", help="output directory")
    args = ap.parse_args()

    cfg = load_config(args.config)
    os.makedirs(args.out, exist_ok=True)

    print("CANDIDATES, not findings. Confirm each one at the source or drop it.\n")
    if not args.config:
        print("No profile given: running on generic defaults. A domain profile makes this "
              "materially better. See references/evidence-profiles.md.\n")

    missing_tiers = report_ladder(cfg, args.config)
    if missing_tiers:
        with open(os.path.join(args.out, "ladder-gaps.txt"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(missing_tiers) + "\n")

    texts = [read_text(p) for p in args.docs]
    all_rows: list[dict] = []

    for path, text in zip(args.docs, texts):
        rows: list[dict] = []
        rows += check_extraction(text)
        id_rows, found = check_identifiers(text, cfg)
        rows += id_rows
        rows += check_cross_refs(text, found, cfg)
        rows += check_lists(text)
        rows += check_unsourced_numbers(text)
        rows += check_optionality(text, cfg)
        rows += check_promises(text, cfg)
        rows += check_vague(text, cfg)
        rows += check_testability(text, cfg)
        rows += check_columns(text, cfg)
        for r in rows:
            r["document"] = os.path.basename(path)
        all_rows += rows

        counts = {k: len(set(v)) for k, v in found.items() if v}
        print(f"{os.path.basename(path)}: {len(rows)} candidates; identifiers {counts}")

    if len(texts) >= 2:
        diff = compare_revisions(texts[0], texts[1], cfg)
        for r in diff:
            r["document"] = f"{os.path.basename(args.docs[0])} -> {os.path.basename(args.docs[1])}"
        all_rows += diff
        print(f"revision diff: {len(diff)} candidates")

    order = {"HIGH": 0, "MED": 1, "LOW": 2}
    all_rows.sort(key=lambda r: (order.get(r["severity"], 3), r["check"]))

    out = os.path.join(args.out, "candidates.csv")
    with open(out, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=["document", "check", "severity", "note",
                                           "evidence", "page"])
        w.writeheader()
        w.writerows(all_rows)

    by_check = defaultdict(int)
    for r in all_rows:
        by_check[r["check"]] += 1
    print(f"\n{len(all_rows)} candidates -> {out}")
    for check, n in sorted(by_check.items(), key=lambda kv: -kv[1]):
        print(f"  {check:22} {n}")
    print("\nChecks this tool cannot run: enforcement of optional fields, enum completeness, "
          "mechanism counts, internal contradiction, omissions. Those are the judgement pass; "
          "see references/check-catalogue.md and references/checks-by-doctype.md.")


if __name__ == "__main__":
    main()
