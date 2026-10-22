#!/usr/bin/env python3
"""check_governance.py -- deterministic gate for nj-governance-v3.

  python check_governance.py                       core-text assertions (v3 tree)
  python check_governance.py --brief <file.md>      validate one worker brief
  python check_governance.py --run <dir>            OWNED_PATHS overlap across
                                                     every brief in <dir>
  python check_governance.py --selftest             negative controls: every
                                                     gate must FAIL when its rule
                                                     is deleted from a copy

Exit 0 = all pass. Prints one line per failure, then a summary line.
"""
import argparse
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
SKILLS = Path(__file__).resolve().parents[2]          # .../nj-plugin-v3
sys.path.insert(0, str(SKILLS / "nj-agent-ops" / "scripts"))
import relay  # noqa: E402  (for _paths_overlap, BATCH_FIELDS)

CORE_FILE = SKILLS / "nj-delegate" / "SKILL.md"

# FOCUS, ENTRY_SMOKE, RESUME and the receipt's CHANGED line added 2026-09-29 (UI round 2:
# a derailed stage, a wiring fault a unit test missed, resumes with no log, receipts
# trusted without a file list). The template and this list change together.
REQUIRED_BRIEF_FIELDS = [
    "GOVERNANCE", "FOCUS", "TASK", "OBJECTIVE", "VERIFIED_FACTS", "SCOPE", "OWNED_PATHS",
    "PARALLEL", "VERIFIER", "TIER", "EFFORT", "BUDGET", "STALL_BOUND", "GATES",
    "ENTRY_SMOKE", "RESUME", "DELIVERABLES", "RECEIPT",
]
MAX_BRIEF_LINES = 25

# GATE tag token -> script path it must name, relative to SKILLS.
GATE_SCRIPTS = {
    "check_governance": "nj-delegate/scripts/check_governance.py",
    "relay.py": "nj-agent-ops/scripts/relay.py",
}


# ------------------------------------------------------------- core text ---

def _core_section(text):
    m = re.search(r"^## 0\..*?(?=^## 1\.)", text, re.S | re.M)
    return m.group(0) if m else ""


def gate_tags(core_text):
    """[GATE: x, y] -> list of raw tag bodies, one per clause."""
    return re.findall(r"\[GATE:\s*([^\]]+)\]", core_text)


def gate_script_violations(core_text):
    bad = []
    for tag in gate_tags(core_text):
        tokens = [t.strip() for t in tag.split(",")]
        script_tokens = [t.split()[0] for t in tokens if t.split()]
        named = [t for t in script_tokens if t in GATE_SCRIPTS or t.endswith(".py")]
        if not named:
            continue  # e.g. "receipt field" alone names no script -- not a gate claim
        for t in named:
            key = t if t in GATE_SCRIPTS else None
            rel = GATE_SCRIPTS.get(key)
            if rel is None:
                bad.append((tag, t, "unknown gate script"))
                continue
            if not (SKILLS / rel).exists():
                bad.append((tag, t, f"{rel} does not exist"))
    return bad


def run_core(project=None, memory=None):
    fails, n = [], 0

    def report(ok, label, detail=""):
        nonlocal n
        n += 1
        if not ok:
            fails.append(f"FAIL {label} {detail}")

    text = CORE_FILE.read_text(encoding="utf-8")
    core = _core_section(text)
    report(bool(core), "nj-delegate/SKILL.md: has a ## 0. ... ## 1. core section")
    report("nj-governance-v3" in core, "nj-delegate/SKILL.md: version named nj-governance-v3")

    bad = gate_script_violations(core)
    report(not bad, "every [GATE: x] names a script that exists", str(bad))

    # Restored 2026-09-22: v3 had dropped this check that v2 had, and the loss was
    # invisible until a column was added to the code and the gate stayed green.
    sys.path.insert(0, str(SKILLS / 'nj-agent-ops' / 'scripts'))
    from relay import BATCH_FIELDS  # docs and code must agree
    ops = (SKILLS / 'nj-agent-ops' / 'SKILL.md').read_text(encoding='utf-8')
    undocumented = [f for f in BATCH_FIELDS if f'`{f}`' not in ops]
    report(not undocumented, 'telemetry fields documented', str(undocumented))
    # Both directions. A doc naming a field the code lacks passed green once (2026-09-22):
    # the one-way check is why a half-applied patch looked complete.
    documented = set(re.findall(r'`([a-z][a-z0-9-]{2,})`', ops))
    known = set(BATCH_FIELDS) | {'estimate-min', 'estimate-tokens'}
    phantom = sorted(f for f in documented & known if f not in BATCH_FIELDS)
    report(not phantom, 'no telemetry field documented but absent from the code', str(phantom))

    for line in fails:
        print(line)
    print(f"governance check: {n - len(fails)}/{n} pass, {len(fails)} fail")
    return 1 if fails else 0


# ------------------------------------------------------------- --brief -----

def _contract_block(text):
    """The contract block. A fenced block if the file has one (that is how the template
    displays it); otherwise the file itself, because a real brief IS the contract — it is
    not wrapped in anything. Prose after the block is documentation and is ignored: the
    contract ends at the first blank line followed by a markdown heading.

    _contract_block_v2 marker: see _fix_brief_gate.py for why the fence stopped being required.
    """
    m = re.search(r"```\n(.*?)\n```", text, re.S)
    if m:
        return m.group(1)
    body = re.split(r"\n\s*\n(?=#)", text, maxsplit=1)[0]
    return body if re.search(r"^[A-Z][A-Z_]*\s", body, re.M) else None


def _split_fields(block):
    """field name (all-caps/underscore, at column 0) -> list of its lines
    (field line + any indented continuation lines)."""
    fields = {}
    cur = None
    for line in block.splitlines():
        m = re.match(r"^([A-Z][A-Z_]*)\s", line) or re.match(r"^([A-Z][A-Z_]*)$", line)
        if m and (line[:1] != " "):
            cur = m.group(1)
            fields.setdefault(cur, []).append(line)
        elif cur is not None:
            fields[cur].append(line)
    return fields


def _has_citation(text):
    return bool(re.search(r":\d|https?://|`[^`]+`", text))


def _verifier_names_a_check(value):
    """True when VERIFIER names something runnable rather than a mood.

    Accepts: "none because <reason>", or any value carrying a command-shaped token —
    a backticked command, a path separator, or a file extension. Rejects bare words
    like "maybe" or "the usual", which is the whole point: a verifier you cannot run
    cannot judge a cheap tier's output, and §0.8 routes on exactly that judgement.
    """
    v = " ".join(value.split())
    low = v.lower()
    if low.startswith("none"):
        return "because" in low and len(low.split("because", 1)[1].strip()) >= 3
    return bool(re.search(r"`[^`]+`|[\\/]|\.\w{1,4}\b|--\w", v))


def _citation_exists(cite, base=None):
    """A [V] citation must point at something real: file:line, an existing path, a backticked
    command, or a URL. Whole-file citations are legal - demanding :line for a whole document
    only teaches people to invent a line number.

    Every path-shaped token in the line is tried, not just the first: a section reference like
    "S0.15" matches the filename pattern and would otherwise mask the real path behind it
    (found 2026-09-22 when this gate rejected a valid brief).
    """
    c = cite.strip()
    if re.search(r"https?://", c) or "`" in c:
        return True
    pat = re.compile(r"([A-Za-z]:[\\/][^\s,;]+|[\w./\\-]+\.\w{1,5})(?::(\d+))?")
    roots = [Path(".")]
    if base:
        roots.append(Path(base))
    roots.append(SKILLS)
    for m in pat.finditer(c):
        raw = m.group(1).replace("\\", "/")
        if any((r / raw).exists() for r in roots) or Path(raw).exists():
            return True
    # A line number is NOT proof: "no_such_file.ts:12" looked like evidence and was not.
    return False


def _strip_first_citation(text):
    """Mutator for the negative control: remove the evidence from the first [V] line."""
    out, done = [], False
    for line in text.splitlines():
        s = line.strip()
        if not done and s.startswith("[V]"):
            for sep in (" \u2014 ", " - ", ": "):
                if sep in line:
                    line = line.split(sep)[0]
                    done = True
                    break
        out.append(line)
    return "\n".join(out)


_BRIEF_DIR = None


def brief_violations(text):
    v = []
    block = _contract_block(text)
    if block is None:
        return [("contract-block", None, "no ``` fenced block found")]
    lines = block.splitlines()
    if len(lines) > MAX_BRIEF_LINES:
        v.append(("contract-block", len(lines), f"exceeds {MAX_BRIEF_LINES} lines"))

    fields = _split_fields(block)
    for f in REQUIRED_BRIEF_FIELDS:
        if f not in fields:
            v.append((f, None, "missing required field"))

    if "VERIFIED_FACTS" in fields:
        for ln in fields["VERIFIED_FACTS"][1:] or fields["VERIFIED_FACTS"]:
            s = ln.strip()
            if not s:
                continue
            m = re.match(r"^\[(V|A|U)\]\s*(.*)$", s)
            if not m:
                v.append(("VERIFIED_FACTS", s, "not graded [V]/[A]/[U]"))
                continue
            grade, rest = m.group(1), m.group(2)
            if grade == "V" and not _citation_exists(rest, base=_BRIEF_DIR):
                v.append(("VERIFIED_FACTS[V]", s,
                          "citation points at nothing that exists "
                          "(need file:line, an existing path, a `command`, or a URL)"))
            if grade == "A" and "falsified by" not in rest.lower():
                v.append(("VERIFIED_FACTS[A]", s, "no 'falsified by'"))

    if "RECEIPT" in fields and "CHANGED" not in " ".join(fields["RECEIPT"]):
        v.append(("RECEIPT", None, "no CHANGED list (every path written, from git or a listing)"))

    if "VERIFIER" in fields:
        content = " ".join(fields["VERIFIER"]).split(None, 1)
        content = content[1].strip() if len(content) > 1 else ""
        if not content:
            v.append(("VERIFIER", content, "empty -- neither a named check nor "
                      "'none because <reason>'"))
        elif not _verifier_names_a_check(content):
            v.append(("VERIFIER", content, "names no runnable check -- give a command, "
                      "script or path, or write 'none because <reason>'"))

    return v


def run_brief(path):
    global _BRIEF_DIR
    _BRIEF_DIR = Path(path).resolve().parent
    text = Path(path).read_text(encoding="utf-8")
    violations = brief_violations(text)
    for field, value, why in violations:
        print(f"brief REJECTED: {field}={value} — {why}")
    print(f"brief check: {'FAIL' if violations else 'ok'} ({path})")
    return 1 if violations else 0


# --------------------------------------------------------------- --run -----

def _owned_paths_from_brief(text):
    block = _contract_block(text)
    if block is None:
        return []
    m = re.search(r"^OWNED_PATHS\s+(.*)$", block, re.M)
    if not m:
        return []
    line = m.group(1)
    line = re.split(r"\bNever:", line)[0]
    line = re.sub(r"(?i)you may write only:?", "", line)
    parts = re.split(r"[,·]", line)
    paths = [p.strip().rstrip(".") for p in parts if p.strip()]
    return paths


def _run_id_of(text):
    """The batch a brief belongs to: the first token of its TASK line.

    `TASK  v3-habits . governance-tooling . worker HAB of 1` -> "v3-habits".
    Returns None when the line is missing or unparseable; such a brief is compared against
    everything, because an unlabelled brief could belong to any batch.
    """
    m = re.search(r"^TASK\s+(\S+)", text, re.M)
    return m.group(1) if m else None


def run_run(directory):
    d = Path(directory)
    if not d.is_dir():
        print(f"run REJECTED: {directory} — not a directory")
        return 1
    if not list(d.glob("*.md")):
        print(f"run REJECTED: {directory} — no briefs found (a gate that passes on an "
              f"empty directory reports green for a typo)")
        return 1
    files = sorted(Path(directory).glob("*.md"))
    owned = {}   # file -> [paths]
    batch = {}   # file -> run-id (None = unlabelled, compared against everything)
    for f in files:
        txt = f.read_text(encoding="utf-8")
        owned[f] = _owned_paths_from_brief(txt)
        batch[f] = _run_id_of(txt)

    fails = []
    names = list(owned)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            # Only briefs of the SAME batch can collide. Two workers that ran one after the
            # other may reuse a path: the rule is one writer per path AT A TIME (2026-09-22).
            ba, bb = batch[names[i]], batch[names[j]]
            if ba is not None and bb is not None and ba != bb:
                continue
            for pa in owned[names[i]]:
                for pb in owned[names[j]]:
                    try:
                        if relay._paths_overlap(pa, pb):
                            fails.append(
                                f"FAIL OWNED_PATHS overlap: {names[i].name}:{pa} "
                                f"<-> {names[j].name}:{pb}")
                    except Exception:
                        continue
    for line in fails:
        print(line)
    print(f"run check: {len(files)} briefs, {len(fails)} overlap(s)")
    return 1 if fails else 0


# ------------------------------------------------------------ selftest -----

EXAMPLE_BRIEF = HERE.parent / "templates" / "worker-brief.example.md"


def tally():
    """Count the gates and habits in the core, and check each gate names a real script.

    Exists because the count was written by hand once and both the author (9/7) and the
    reviewer (8/8) got it wrong. A governance that demands graded evidence cannot publish an
    ungraded number about itself.
    """
    sec = _core_section(CORE_FILE.read_text(encoding="utf-8"))
    raw = re.findall(r"\[GATE:\s*([^\]]+)\]", sec)
    placeholders = [g for g in raw if g.strip().startswith("<")]
    gates = [g.strip() for g in raw if not g.strip().startswith("<")]
    # Count only habits attached to a clause. The preamble sentence that explains the
    # convention carries a [HABIT] too, and counting it produced 8+9=17 for 16 clauses
    # — a wrong number published under a "measured" label (audit, 2026-09-22).
    _clause_habits = [m for m in re.finditer(r"\[HABIT[^\]]*\]", sec)
                      if re.search(r"^###? 0\.\d+", sec[:m.start()].splitlines()[-1] or "")]
    habits = _clause_habits
    print(f"gates:  {len(gates)}  (+{len(placeholders)} prose placeholder)")
    for g in gates:
        print(f"    {g}")
    print(f"habits: {len(habits)}")
    clauses = len(re.findall(r"^###? 0\.\d+", sec, re.M))
    if len(gates) + len(habits) != clauses:
        print(f"FAIL tagged {len(gates)}+{len(habits)} != {clauses} clauses "
              f"— every clause carries exactly one tag")
    missing = gate_script_violations(sec)
    for m in missing:
        print(f"FAIL gate names a missing script: {m}")
    print(f"tally: {len(gates)} gates, {len(habits)} habits, {len(missing)} naming a missing script")
    return 1 if (missing or len(gates) + len(habits) != clauses) else 0


def selftest():
    results = {}

    # Positive control: a real, unfenced brief file must PASS. Without it, a gate that
    # rejects everything is indistinguishable from a gate that works (Lead fix, 2026-09-22).
    if EXAMPLE_BRIEF.is_file():
        ex = EXAMPLE_BRIEF.read_text(encoding="utf-8")
        results["positive control: the example brief passes"] = not brief_violations(ex)
        results["negative control: a [V] with no citation is caught"] = any(
            v[0].startswith("VERIFIED_FACTS") for v in brief_violations(_strip_first_citation(ex)))
        bare = re.sub(r"(?m)^VERIFIER .*$", "VERIFIER     maybe", ex, count=1)
        results["negative control: a bare VERIFIER is caught"] = any(
            v[0] == "VERIFIER" for v in brief_violations(bare))
        results["negative control: a [V] citing a missing file is caught"] = any(
            v[0].startswith("VERIFIED_FACTS")
            for v in brief_violations(ex.replace("worker-brief.md", "no_such_file_xyz.md", 1)))
    else:
        results["positive control: the example brief passes"] = False

    core = CORE_FILE.read_text(encoding="utf-8")
    csec = _core_section(core)
    results["clean core passes (version + gate scripts)"] = (
        "nj-governance-v3" in csec and not gate_script_violations(csec))
    stripped_version = csec.replace("nj-governance-v3", "nj-governance-vX")
    results["deleted version string is caught"] = "nj-governance-v3" not in stripped_version
    broken_gate = csec.replace("[GATE: relay.py]", "[GATE: no_such_script.py]")
    results["GATE naming a missing script is caught"] = bool(gate_script_violations(broken_gate))

    good_brief = f"""```
GOVERNANCE   v3 · rules: r.md (read once, first)
FOCUS        your only deliverable is the test file
TASK         t1 · class · worker A of 1
OBJECTIVE    do the thing
VERIFIED_FACTS
  [V] the gate under test exists — nj-delegate/scripts/check_governance.py
  [A] inference one — falsified by: a failing test
SCOPE        in. NOT in scope: out.
OWNED_PATHS  you may write ONLY: nj-plugin-v3\\tests\\. Never: elsewhere.
PARALLEL     with: none — serial because sole writer
VERIFIER     tests/test_v3.py
TIER         STANDARD because implementation to spec
EFFORT       high
BUDGET       uncached in <= 100k
STALL_BOUND  15 min
GATES        tests/test_v3.py green
ENTRY_SMOKE  none — no signature, message shape or entry path changes
RESUME       detail file: tests/progress.md
DELIVERABLES tests/test_v3.py
RECEIPT      STATUS / FINDING / EVIDENCE / FILES-SYMBOLS / RISK / NEXT ACTION
             + CHANGED: from git status
```"""
    results["clean brief passes"] = not brief_violations(good_brief)

    no_objective = good_brief.replace("OBJECTIVE    do the thing\n", "")
    results["missing required field is caught"] = any(
        f == "OBJECTIVE" for f, _, _ in brief_violations(no_objective))

    for field in ("FOCUS", "ENTRY_SMOKE", "RESUME"):
        dropped = re.sub(rf"(?m)^{field} .*\n", "", good_brief, count=1)
        results[f"missing {field} is caught"] = any(
            f == field for f, _, _ in brief_violations(dropped))

    no_changed = good_brief.replace("             + CHANGED: from git status\n", "")
    results["RECEIPT with no CHANGED list is caught"] = any(
        f == "RECEIPT" for f, _, _ in brief_violations(no_changed))

    bad_grade = good_brief.replace("[V] the gate", "[X] the gate")
    results["ungraded VERIFIED_FACTS line is caught"] = any(
        "VERIFIED_FACTS" == f for f, _, _ in brief_violations(bad_grade))

    no_citation = good_brief.replace("— nj-delegate/scripts/check_governance.py", "")
    results["[V] with no citation is caught"] = any(
        "VERIFIED_FACTS[V]" == f for f, _, _ in brief_violations(no_citation))

    no_falsified = good_brief.replace(" — falsified by: a failing test", "")
    results["[A] with no 'falsified by' is caught"] = any(
        "VERIFIED_FACTS[A]" == f for f, _, _ in brief_violations(no_falsified))

    bad_verifier = good_brief.replace("VERIFIER     tests/test_v3.py",
                                       "VERIFIER     none")
    results["bare 'none' VERIFIER (no 'because') is caught"] = any(
        f == "VERIFIER" for f, _, _ in brief_violations(bad_verifier))

    too_long = good_brief.replace(
        "GATES        tests/test_v3.py green\n",
        "GATES        tests/test_v3.py green\n" + "EXTRA        line\n" * 20)
    results["over-25-line block is caught"] = any(
        f == "contract-block" for f, _, _ in brief_violations(too_long))

    a_paths = ["nj-plugin-v3\\tests\\"]
    b_paths_ok = ["nj-plugin-v3\\nj-delegate\\scripts\\"]
    b_paths_overlap = ["nj-plugin-v3\\tests\\fixtures\\"]
    results["--run: disjoint OWNED_PATHS pass"] = not relay._paths_overlap(
        a_paths[0], b_paths_ok[0])
    results["--run: overlapping OWNED_PATHS (prefix) is caught"] = relay._paths_overlap(
        a_paths[0], b_paths_overlap[0])

    for k, v in results.items():
        print(("ok   " if v else "FAIL ") + k)
    return 0 if all(results.values()) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project")
    ap.add_argument("--memory")
    ap.add_argument("--brief")
    ap.add_argument("--run")
    ap.add_argument("--selftest", action="store_true")

    ap.add_argument("--tally", action="store_true",

                    help="count gates and habits in the core, and check each gate names a real script")
    a = ap.parse_args()
    if a.tally:
        sys.exit(tally())
    if a.selftest:
        sys.exit(selftest())
    if a.brief:
        sys.exit(run_brief(a.brief))
    if a.run:
        sys.exit(run_run(a.run))
    sys.exit(run_core(a.project, a.memory))


if __name__ == "__main__":
    main()
