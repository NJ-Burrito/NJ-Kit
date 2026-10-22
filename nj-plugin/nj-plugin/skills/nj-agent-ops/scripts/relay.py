#!/usr/bin/env python3
"""relay.py -- nj-agent-ops result relay + measurement ledger
(2026-09-14; v3 write-time validation + verify/claim 2026-09-22).

Subcommands:
  init <project> <run-id>      create .agent-ops/{results,briefs}/<run-id>
  digest <project> <run-id>    print one line per agent result, then totals
  ledger <project> <run-id> --agent A --stage S --status ok|partial|failed
                                --runtime R [--tier T] [--task-class C] [--role R]
                                [--cached-in N] [--uncached-in N] [--output N]
                                [--reasoning N] [--model-calls N] [--tool-calls N]
                                [--workers N] [--retries N] [--duration-min N]
                                [--verify-status S] [--final-status S]
                                [--defects N] [--escalations N]
                                [--cost X] [--basis actual|estimated]
                                [--rework y|n] [--note "cause of any overrun"]
                                REFUSES and writes nothing on: bad tier, empty/bad
                                exec-status, a non-integer numeric field, --cost
                                without --basis, or rework not in {y,n} when
                                status != ok (core §0.14).
  claim <project> <run-id> --agent A --paths p1 p2 ...
                                append-only ownership registry at
                                .agent-ops/claims/<run-id>.json. Refuses (exit 1,
                                writes nothing) on overlap with an existing claim
                                by a different agent (core §0.6).
  verify <project> [--run-id X]
                                audits ledger.md + batches.md, prints one line per
                                invalid row, prints the §0.15 KPI block, exit 1 if
                                any row invalid or any KPI breaches its target.
  batch <project> <task-id> [--task-class C] [--lead-runtime R] [--worker-count N]
                                [--peak-concurrent N] [--lead-wakeups N] ...
                                one calibration row per task in batches.md
                                (nj-governance-v3; see BATCH_FIELDS). A field
                                not passed is written NOT_VISIBLE.
  sweep <project> [--tag T] [--run-id R]
                                what this session still owns; exit 1 if anything
                                survives (browsers, agents, runs, open claims)
  route <project> --class C [--failed "gate line" --cause CLASS [--ran-on opus]]
                                start model + effort per task-class learned from
                                ledger.md (floor sonnet); with --failed, ESCALATE
                                opus once or STOP. --selftest runs the assert check.
  stale <project>               list result files older than 7 days

PYTHONUTF8=1 assumed; stdout is reconfigured to utf-8 defensively.
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path, PureWindowsPath

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REQUIRED_FIELDS = ["agent", "stage", "status", "files", "gates", "artefacts",
                   "leftovers", "detail_path"]
VALID_STATUS = {"ok", "partial", "failed"}
VALID_TIERS = ["DETERMINISTIC", "FREE-LOCAL", "ECONOMY", "STANDARD", "FRONTIER"]
STALE_DAYS = 7
NOT_MEASURED = "NOT_MEASURED"
NOT_VISIBLE = "NOT_VISIBLE"
BLANKS = {NOT_MEASURED, NOT_VISIBLE}

# H3 (core Sec0.12): enum a failed/partial result's failure_class must be one of.
FAILURE_CLASSES = {
    "CAPABILITY_LIMIT", "CONTEXT_DEFECT", "IMPLEMENTATION_DEFECT", "TOOL_FAILURE",
    "ENVIRONMENT_FAILURE", "TEST_FAILURE", "AMBIGUOUS_REQUIREMENT",
    "AUTHORIZATION_BLOCKER", "LEAD_DEFECT",
}

# H4 (core Sec0.13): per-tier overrun threshold basis. These are derived from
# tool-call estimates at spec time, NOT counter-measured from real runs --
# do not later quote them as measured figures.
CLASS_BUDGETS = {"FRONTIER": 150000, "STANDARD": 65000, "ECONOMY": 12000}
OVERRUN_MULTIPLIER = 1.5

# ledger.md numeric columns (int-or-absent only; NOT_MEASURED/NOT_VISIBLE are
# illegal here -- core §0.14: "estimates never occupy a numeric field").
LEDGER_NUMERIC = ["cached-in", "uncached-in", "output", "reasoning",
                   "model-calls", "tool-calls", "workers", "retries",
                   "duration-min", "defects", "escalations", "estimate-min"]

LEDGER_COLUMNS = [
    "date", "run-id", "agent", "runtime", "tier", "effort", "task-class", "role", "stage",
    "cached-in", "uncached-in", "output", "reasoning", "model-calls",
    "tool-calls", "workers", "retries", "duration-min",
    "exec-status", "verify-status", "final-status",
    "defects", "escalations", "cost", "basis", "rework", "note",
    "estimate-min",
]


def _migrate_ledger(path):
    """A ledger whose header lacks `effort` (added after `tier`): insert a blank
    cell after tier in every 26/27-cell row, rewrite the header. In place, no row
    lost. Returns the number of rows changed."""
    lines = path.read_text(encoding="utf-8").split("\n")
    hi = next((i for i, l in enumerate(lines) if l.strip().startswith("| date |")), None)
    if hi is None or "effort" in _split_row(lines[hi]):
        return 0
    at = _split_row(lines[hi]).index("tier") + 1
    lines[hi] = "| " + " | ".join(LEDGER_COLUMNS) + " |"
    if hi + 1 < len(lines) and lines[hi + 1].startswith("|---"):
        lines[hi + 1] = "|" + "---|" * len(LEDGER_COLUMNS)
    n = 0
    for i in range(hi + 2, len(lines)):
        if lines[i].strip().startswith("|") and len(_split_row(lines[i])) in (len(LEDGER_COLUMNS) - 1, len(LEDGER_COLUMNS) - 2):
            c = _split_row(lines[i])
            lines[i] = "| " + " | ".join(c[:at] + [""] + c[at:]) + " |"
            n += 1
    path.write_text("\n".join(lines), encoding="utf-8")
    return n


def agent_ops_root(project: str) -> Path:
    return Path(project) / ".agent-ops"


def cmd_init(args):
    root = agent_ops_root(args.project)
    for sub in ("results", "briefs"):
        (root / sub / args.run_id if sub == "results" else root / sub).mkdir(
            parents=True, exist_ok=True
        )
    (root / "results" / args.run_id).mkdir(parents=True, exist_ok=True)
    print(f"init ok: {root / 'results' / args.run_id}, {root / 'briefs'}")


def _validate(doc, path):
    missing = [f for f in REQUIRED_FIELDS if f not in doc]
    if missing:
        return f"invalid ({path.name}): missing {missing}"
    if doc["status"] not in VALID_STATUS:
        return f"invalid ({path.name}): bad status {doc['status']!r}"
    not_list = [f for f in ("files", "gates", "artefacts", "leftovers")
                if not isinstance(doc[f], list)]
    if not_list:
        return f"invalid ({path.name}): must be arrays: {not_list}"
    return None


def cmd_digest(args):
    result_dir = agent_ops_root(args.project) / "results" / args.run_id
    if not result_dir.is_dir():
        print(f"no such run: {result_dir}")
        return 1
    files = sorted(result_dir.glob("*.json"))
    if not files:
        print(f"0 agents, run {args.run_id} empty")
        return 1
    any_bad = False
    counts = {"ok": 0, "partial": 0, "failed": 0, "invalid": 0}
    for f in files:
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"{f.stem} | INVALID JSON: {e}")
            counts["invalid"] += 1
            any_bad = True
            continue
        err = _validate(doc, f)
        if err:
            print(f"{f.stem} | {err}")
            counts["invalid"] += 1
            any_bad = True
            continue
        status = doc["status"]
        counts[status] += 1
        if status == "failed":
            any_bad = True
        u = doc.get("usage") or {}
        usage = ""
        if u:
            basis = u.get("basis", "estimated")
            bits = [f"{k}={u[k]}" for k in
                    ("uncached_in", "cached_in", "output", "reasoning",
                     "model_calls", "tool_calls", "retries") if u.get(k) is not None]
            if bits:
                usage = f" | {basis}: " + " ".join(bits)
        print(
            f"{doc['agent']} | {doc['stage']} | {status} | "
            f"files={len(doc['files'])} gates={len(doc['gates'])} "
            f"leftovers={len(doc['leftovers'])}{usage} | detail={doc['detail_path']}"
        )
    total = len(files)
    print(
        f"TOTAL {total} agents: ok={counts['ok']} partial={counts['partial']} "
        f"failed={counts['failed']} invalid={counts['invalid']}"
    )
    return 1 if any_bad else 0


def _cell(v):
    """Empty cell = not measured. Never invent a number."""
    return "" if v is None else str(v)


def _is_int_str(s):
    if s is None:
        return False
    s = str(s)
    if s.startswith("-"):
        s = s[1:]
    return s.isdigit()


def ledger_violations(row):
    """row: dict field(kebab-case) -> raw string value or None. Returns list of
    (field, value, why). Empty list == valid. Never guesses; only the rules in
    core §0.14 / brief item 1 of CODE.md."""
    v = []

    tier = row.get("tier")
    if tier not in (None, "") and tier not in VALID_TIERS:
        v.append(("tier", tier, f"not one of {VALID_TIERS}"))

    status = row.get("exec-status")
    if status in (None, ""):
        v.append(("exec-status", status, "empty"))
    elif status not in VALID_STATUS:
        v.append(("exec-status", status, f"not one of {sorted(VALID_STATUS)}"))

    for field in LEDGER_NUMERIC:
        val = row.get(field)
        if val in (None, ""):
            continue  # omitted is legal -- "not measured"
        if val in BLANKS:
            v.append((field, val, "NOT_MEASURED/NOT_VISIBLE are legal only in "
                                   "non-numeric fields"))
        elif not _is_int_str(val):
            v.append((field, val, "not an integer"))

    cost = row.get("cost")
    basis = row.get("basis")
    if cost not in (None, "") and basis in (None, ""):
        v.append(("cost", cost, "--cost requires --basis actual|estimated"))

    rework = row.get("rework")
    if status not in (None, "", "ok"):
        if rework not in ("y", "n"):
            v.append(("rework", rework, "must be y|n when exec-status != ok"))
    elif rework not in (None, "", "y", "n"):
        v.append(("rework", rework, "must be y|n"))

    return v


def cmd_ledger(args):
    ledger_path = agent_ops_root(args.project) / "ledger.md"
    row_dict = {
        "date": time.strftime("%Y-%m-%d"),
        "run-id": args.run_id,
        "agent": args.agent,
        "runtime": args.runtime if args.runtime is not None else args.model,
        "tier": args.tier,
        "effort": args.effort,
        "task-class": args.task_class,
        "role": args.role,
        "stage": args.stage,
        "cached-in": args.cached_in,
        "uncached-in": args.uncached_in,
        "output": args.output,
        "reasoning": args.reasoning,
        "model-calls": args.model_calls,
        "tool-calls": args.tool_calls,
        "workers": args.workers,
        "retries": args.retries,
        "duration-min": args.duration_min,
        "exec-status": args.status,
        "verify-status": args.verify_status,
        "final-status": args.final_status,
        "defects": args.defects,
        "escalations": args.escalations,
        "cost": args.cost,
        "basis": args.basis,
        "rework": args.rework,
        "note": args.note,
        "estimate-min": args.estimate_min,
    }
    if row_dict["runtime"] is None:
        print("ledger REJECTED: runtime=None — --runtime (or legacy --model) is required")
        return 1

    if args.role == "worker" and not args.verify_status:
        print("ledger WARN: worker row without --verify-status; `relay.py route` "
              "learns only from rows that carry it", file=sys.stderr)
    if args.effort not in (None, "low", "medium", "high"):
        print(f"ledger REJECTED: effort={args.effort} — not low|medium|high")
        return 1

    violations = ledger_violations(row_dict)
    if violations:
        for field, value, why in violations:
            print(f"ledger REJECTED: {field}={value} — {why}")
        return 1

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    header = ("| " + " | ".join(LEDGER_COLUMNS) + " |\n"
              + "|" + "---|" * len(LEDGER_COLUMNS) + "\n")
    if not ledger_path.exists():
        ledger_path.write_text(header, encoding="utf-8")
    else:
        _migrate_ledger(ledger_path)
    row = "| " + " | ".join(_cell(row_dict[c]) for c in LEDGER_COLUMNS) + " |\n"
    with ledger_path.open("a", encoding="utf-8") as fh:
        fh.write(row)
    print(f"ledger ok: {ledger_path}")
    return 0


ESTIMATE_MIN_N = 5
ESTIMATE_METRICS = {"duration-min": "duration-min", "uncached-in": "uncached-in"}


def _percentile(sorted_vals, p):
    """Linear-interpolation percentile over an already-sorted list of numbers."""
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    k = (p / 100) * (len(sorted_vals) - 1)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return float(sorted_vals[f])
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def cmd_estimate(args):
    """Reference-class forecast from validated ledger history -- never from
    imagining the task at hand (core failure this fixes: a 1-unit pilot
    guessed at 20 min took 90). Refuses rather than invent a number when the
    class is thin; reports skew instead of smoothing it away."""
    metric = ESTIMATE_METRICS[args.metric]
    ledger_path = agent_ops_root(args.project) / "ledger.md"
    rows = _parse_table(ledger_path, LEDGER_COLUMNS)

    vals, dates = [], []
    class_counts = {}
    for _lineno, row in rows:
        if "__column_count__" in row:
            continue
        row_norm = {k: (None if v in ("", None) else v) for k, v in row.items()}
        if ledger_violations(row_norm):
            continue  # a row the ledger would reject never informs a forecast
        tc = row_norm.get("task-class")
        if tc:
            class_counts[tc] = class_counts.get(tc, 0) + 1
        if tc != args.task_class:
            continue
        val = row_norm.get(metric)
        if val is None or val in BLANKS or not _is_int_str(val):
            continue
        vals.append(int(val))
        if row_norm.get("date"):
            dates.append(row_norm["date"])

    n = len(vals)
    if n < ESTIMATE_MIN_N:
        others = sorted(
            ((k, v) for k, v in class_counts.items() if k != args.task_class),
            key=lambda kv: -kv[1],
        )
        nearest = ", ".join(f"{k}(n={v})" for k, v in others[:3]) or "none"
        print(f"estimate NO BASIS: task-class={args.task_class} n={n} "
              f"(need {ESTIMATE_MIN_N}) — nearest classes: {nearest}")
        return 1

    sv = sorted(vals)
    median, p80 = _percentile(sv, 50), _percentile(sv, 80)
    p25, p75 = _percentile(sv, 25), _percentile(sv, 75)
    lo, hi = sv[0], sv[-1]
    span = f"{min(dates)}..{max(dates)}" if dates else NOT_VISIBLE
    print(f"estimate task-class={args.task_class} metric={metric} n={n} "
          f"median={median:.1f} p80={p80:.1f} min={lo} max={hi} "
          f"IQR={p75 - p25:.1f} date-span={span}")
    if median > 0 and hi / median >= 3:
        print(f"WARNING: long tail (max {hi} vs median {median:.1f}) — "
              f"p80 is the number to plan with, not the median.")
    return 0


GOVERNANCE_VERSION = "nj-governance-v3"
# Calibration telemetry, one row per task (core §0.14/§0.15). Order is the
# file's column order; anything not passed is NOT_VISIBLE, never guessed.
BATCH_FIELDS = [
    "task-class", "governance-version", "lead-runtime", "lead-tier",
    "lead-effort", "worker-count", "peak-concurrent", "lead-wakeups",
    "wake-reasons", "invalid-status-wakeups", "model-polls",
    "lead-passes-while-active", "parallelism-considered", "parallelism-used",
    "parallelism-reason", "serial-deps", "w2w-delegations", "nested-spawns",
    "model-passes", "verification-result", "review-findings", "escalations",
    "lead-defects", "false-challenges", "estimate-min", "estimate-tokens", "wake-ratio", "cascade-attempts", "cascade-escalations",
    "duration-min", "note",
]
# NOTE (EST, 2026-09-22): spec item 2 also asks for --estimate-min /
# --estimate-tokens on `batch`. Not added: BATCH_FIELDS entries are gated by
# check_governance.py's telemetry-docs-drift check against
# nj-agent-ops/SKILL.md, which is outside this worker's OWNED_PATHS (no .md
# outside tests/) -- adding the column here would fail an existing green
# gate (test_check_governance_core_green) that this run must keep passing.
# Calibration below scores off ledger's estimate-min vs duration-min instead,
# which needs no new BATCH_FIELDS entry. Lead: add the two fields to
# BATCH_FIELDS + document them in nj-agent-ops/SKILL.md in one change if the
# batch-level estimate is wanted too.


def _wake_ratio(values):
    wakeups = values.get("lead-wakeups")
    workers = values.get("worker-count")
    if not _is_int_str(wakeups) or not _is_int_str(workers) or int(workers) == 0:
        return NOT_VISIBLE
    return f"{int(wakeups) / int(workers):.2f}"


def cmd_batch(args):
    path = agent_ops_root(args.project) / "batches.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = ["date", "task-id"] + BATCH_FIELDS
    if not path.exists():
        path.write_text("| " + " | ".join(cols) + " |\n"
                        + "|" + "---|" * len(cols) + "\n", encoding="utf-8")
    raw = {f: getattr(args, f.replace("-", "_")) for f in BATCH_FIELDS
           if f not in ("wake-ratio",)}
    raw["wake-ratio"] = args.wake_ratio if args.wake_ratio is not None else _wake_ratio(raw)
    values = [time.strftime("%Y-%m-%d"), args.run_id]
    for f in BATCH_FIELDS:
        v = raw.get(f)
        values.append(NOT_VISIBLE if v is None else str(v).replace("|", "/"))
    with path.open("a", encoding="utf-8") as fh:
        fh.write("| " + " | ".join(values) + " |\n")
    for f in ("w2w-delegations", "nested-spawns", "model-polls"):
        v = getattr(args, f.replace("-", "_"))
        if v not in (None, "0"):
            print(f"batch WARN: {f}={v} (expected 0)")
    print(f"batch ok: {path}")



def _owned_processes(tags):
    """Processes whose command line carries one of this session's tags.

    Windows only; returns [] anywhere else rather than guessing. Never lists a process it
    cannot attribute — killing another session's browser is worse than leaving your own.
    """
    import subprocess
    if not sys.platform.startswith("win"):
        return []
    pat = "|".join(re.escape(x) for x in tags if x)
    if not pat:
        return []
    ps = ("Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match '" + pat +
          "' -and $_.Name -notmatch '^(powershell|pwsh|conhost|bash|sh|git)\\.exe$' } | "
          "ForEach-Object { '{0}|{1}' -f $_.Name, $_.ProcessId }")
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                             capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return []
    mine = {str(os.getpid()), str(os.getppid())}
    rows = []
    for line in out.splitlines():
        if "|" not in line:
            continue
        name, pid = line.strip().split("|", 1)
        if pid.strip() in mine:
            continue          # the sweep is not its own leftover
        rows.append(line.strip())
    return rows


def cmd_sweep(args):
    """What this session still owns. Exit 1 if anything survives.

    The owner, 2026-09-22: never leave leftovers - browsers, agents, tasks, subagents, runs.
    A session that finishes owing nothing is the only acceptable end state, and a rule
    nobody can check is how the leftovers happened in the first place.
    """
    root = agent_ops_root(args.project)
    left = []

    tags = [t for t in (args.tag or []) if t]
    for row in _owned_processes(tags):
        name, pid = row.split("|", 1)
        left.append(f"process {name} pid={pid} (matches a tag of this session)")

    # A dispatched run with no receipt: either the worker never reported, or nobody collected it.
    results = root / "results"
    if results.is_dir():
        for rundir in sorted(p for p in results.iterdir() if p.is_dir()):
            if args.run_id and rundir.name != args.run_id:
                continue
            if not list(rundir.glob("*.json")):
                left.append(f"run {rundir.name} has a results dir but no receipt")

    # A claim never released: the path is still marked as owned by a finished worker.
    claims = root / "claims"
    if claims.is_dir():
        for c in sorted(claims.glob("*.json")):
            if args.run_id and c.stem != args.run_id:
                continue
            if args.released and c.stem in args.released:
                continue
            left.append(f"claim {c.name} still open (release it when the batch ends)")

    for line in left:
        print(f"sweep LEFTOVER: {line}")
    print(f"sweep: {len(left)} leftover(s)"
          + ("" if left else " - nothing of this session is still running"))
    return 1 if left else 0


def cmd_stale(args):
    root = agent_ops_root(args.project) / "results"
    if not root.is_dir():
        print("0 stale (no results dir)")
        return 0
    cutoff = time.time() - STALE_DAYS * 86400
    stale = [p for p in root.rglob("*.json") if p.stat().st_mtime < cutoff]
    for p in stale:
        print(str(p))
    print(f"{len(stale)} stale (> {STALE_DAYS}d)")
    return 0


# ---------------------------------------------------------------- claim ----

def _norm_path(p):
    """Resolved-absolute, separators normalised, case-folded (Windows §0.6)."""
    pw = PureWindowsPath(str(Path(p).resolve()))
    return str(pw).replace("/", "\\").lower()


def _paths_overlap(a, b):
    pa, pb = _norm_path(a).split("\\"), _norm_path(b).split("\\")
    short, long_ = (pa, pb) if len(pa) <= len(pb) else (pb, pa)
    return long_[:len(short)] == short


def cmd_claim(args):
    claims_dir = agent_ops_root(args.project) / "claims"
    claims_dir.mkdir(parents=True, exist_ok=True)
    claims_path = claims_dir / f"{args.run_id}.json"
    existing = []
    if claims_path.exists():
        existing = json.loads(claims_path.read_text(encoding="utf-8") or "[]")

    for rec in existing:
        if rec["agent"] == args.agent:
            continue
        for new_p in args.paths:
            for old_p in rec["paths"]:
                if _paths_overlap(new_p, old_p):
                    print(f"claim REJECTED: {args.agent}:{new_p} overlaps "
                          f"{rec['agent']}:{old_p}")
                    return 1

    existing.append({
        "agent": args.agent,
        "paths": args.paths,
        "date": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    claims_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False),
                            encoding="utf-8")
    print(f"claim ok: {claims_path}")
    return 0


# --------------------------------------------------------------- verify ----

def _split_row(line):
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def _parse_table(path, columns):
    """Returns list of (row_number_1_based, dict). Skips header/separator/
    comment lines. A row whose cell count does not match `columns` gets a
    single dict {"__column_count__": n} so verify can flag it."""
    if not path.exists():
        return []
    rows = []
    in_comment = False
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        s = line.strip()
        if not s:
            continue
        if s.startswith("<!--"):
            in_comment = not s.endswith("-->")
            continue
        if in_comment:
            if s.endswith("-->"):
                in_comment = False
            continue
        if not s.startswith("|"):
            continue
        cells = _split_row(s)
        if cells and cells[0].startswith("---"):
            continue
        if cells and cells[0] == columns[0]:  # header row
            continue
        if len(cells) != len(columns):
            rows.append((i, {"__column_count__": len(cells)}))
            continue
        rows.append((i, dict(zip(columns, cells))))
    return rows


def cmd_verify(args):
    ledger_path = agent_ops_root(args.project) / "ledger.md"
    batches_path = agent_ops_root(args.project) / "batches.md"
    bad = 0

    ledger_rows = _parse_table(ledger_path, LEDGER_COLUMNS)
    valid_ledger_rows = []
    for lineno, row in ledger_rows:
        if args.run_id and row.get("run-id") not in (None, args.run_id):
            continue
        if "__column_count__" in row:
            print(f"verify FAIL ledger.md:{lineno} column-count — "
                  f"expected {len(LEDGER_COLUMNS)} got {row['__column_count__']} "
                  f"(pre-2026-09-16 legacy row)")
            bad += 1
            continue
        row_norm = {k: (None if v in ("", None) else v) for k, v in row.items()}
        violations = ledger_violations(row_norm)
        for field, value, why in violations:
            print(f"verify FAIL ledger.md:{lineno} {field}={value} — {why}")
            bad += 1
        if not violations:
            valid_ledger_rows.append(row_norm)

    # ---- H4 (core §0.13): budgets are ceilings, an overrun must carry a
    # cause. No tier or no uncached-in -> skipped, never failed (absence is
    # not a breach). Tiers outside CLASS_BUDGETS (DETERMINISTIC, FREE-LOCAL)
    # have no defined budget here -- also skipped, not failed. ----
    for row_norm in valid_ledger_rows:
        tier = row_norm.get("tier")
        uncached = row_norm.get("uncached-in")
        if tier is None or uncached is None or tier not in CLASS_BUDGETS:
            continue
        if not _is_int_str(uncached):
            continue
        threshold = CLASS_BUDGETS[tier] * OVERRUN_MULTIPLIER
        if int(uncached) > threshold and not (row_norm.get("note") or "").strip():
            print(f"verify FAIL ledger.md run={row_norm.get('run-id')} "
                  f"agent={row_norm.get('agent')} uncached-in={uncached} — "
                  f"exceeds {threshold:.0f} ({tier} budget x{OVERRUN_MULTIPLIER}) with no note")
            bad += 1

    batch_columns = ["date", "task-id"] + BATCH_FIELDS
    batch_rows = _parse_table(batches_path, batch_columns)
    for lineno, row in batch_rows:
        if args.run_id and row.get("task-id") not in (None, args.run_id):
            continue
        if "__column_count__" in row:
            # older batches.md predates the v3 columns -- structural, not a
            # value defect; report but do not fail the KPI computation on it.
            print(f"verify NOTE batches.md:{lineno} column-count — "
                  f"expected {len(batch_columns)} got {row['__column_count__']} "
                  f"(pre-v3 schema row)")
            continue
        # ---- H1 (core §0.5): no model-mediated polling. NOT_VISIBLE (not
        # recorded) is legal; a recorded count above zero is the breach. ----
        model_polls = row.get("model-polls")
        if _is_int_str(model_polls) and int(model_polls) > 0:
            print(f"verify FAIL batches.md:{lineno} run={row.get('task-id')} "
                  f"model-polls={model_polls} — model-mediated polling detected")
            bad += 1

    # ---- H2 (core §0.7) + H3 (core §0.12): one receipt per worker, and a
    # failed/partial result must name its cause. Scoped to runs that have
    # ledger rows AND an existing results/<run-id>/ dir -- a run with no
    # results dir at all was never receipted through this path, so its
    # absence is not a breach (absence is never a breach). ----
    run_ids = sorted({r.get("run-id") for r in valid_ledger_rows if r.get("run-id")})
    for run_id in run_ids:
        rdir = agent_ops_root(args.project) / "results" / run_id
        if not rdir.is_dir():
            continue
        agent_files = {}
        for f in sorted(rdir.glob("*.json")):
            try:
                doc = json.loads(f.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"verify FAIL results/{run_id}/{f.name} — invalid JSON: {e}")
                bad += 1
                continue
            a = doc.get("agent")
            if not a:
                continue
            agent_files.setdefault(a, []).append(f.name)
            status = doc.get("status")
            if status in ("failed", "partial"):
                fc = doc.get("failure_class")
                if fc not in FAILURE_CLASSES:
                    print(f"verify FAIL results/{run_id}/{f.name} agent={a} "
                          f"status={status} — failure_class missing or not in "
                          f"{sorted(FAILURE_CLASSES)}")
                    bad += 1
        for a, names in agent_files.items():
            if len(names) > 1:
                print(f"verify FAIL results/{run_id} agent={a} — "
                      f"{len(names)} result files (one receipt per worker): {names}")
                bad += 1
        ledger_agents = {r.get("agent") for r in valid_ledger_rows
                          if r.get("run-id") == run_id and r.get("agent")}
        for a in sorted(ledger_agents - set(agent_files)):
            print(f"verify FAIL results/{run_id} agent={a} — "
                  f"ledger row present, no result file")
            bad += 1

    # ---- KPI block (core §0.15) ----
    print("--- KPI (core §0.15) ---")
    kpi_bad = False
    valid_batch_rows = [r for _, r in batch_rows if "__column_count__" not in r]

    ratios = [float(r["wake-ratio"]) for r in valid_batch_rows
              if r.get("wake-ratio") not in (None, "", NOT_VISIBLE)]
    if ratios:
        avg_ratio = sum(ratios) / len(ratios)
        breach = avg_ratio > 1.5
        print(f"lead-wakeups/worker-count: {avg_ratio:.2f} (target <=1.5)"
              f"{' BREACH' if breach else ''}")
        kpi_bad = kpi_bad or breach
    else:
        print("lead-wakeups/worker-count: NOT_VISIBLE (no batch rows with both fields)")

    defects = [int(r["lead-defects"]) for r in valid_batch_rows
               if _is_int_str(r.get("lead-defects"))]
    if defects:
        total_defects, n_tasks = sum(defects), len(defects)
        rate = total_defects / n_tasks * 10
        breach = rate >= 2
        print(f"lead-defects per 10 tasks: {rate:.2f} (target 0)"
              f"{' BREACH' if breach else ''}")
        kpi_bad = kpi_bad or breach
    else:
        print("lead-defects per 10 tasks: NOT_VISIBLE (no batch rows with lead-defects)")

    print(f"ledger rows failing verify: {bad} (target 0)"
          f"{' BREACH' if bad else ''}")
    kpi_bad = kpi_bad or bool(bad)

    delegations = [int(r[f]) for f in ("w2w-delegations", "nested-spawns")
                   for r in valid_batch_rows if _is_int_str(r.get(f))]
    if delegations:
        total_delegations = sum(delegations)
        breach = total_delegations > 0
        print(f"worker->worker delegations + nested spawns: {total_delegations} "
              f"(target 0){' BREACH' if breach else ''}")
        kpi_bad = kpi_bad or breach
    else:
        print("worker->worker delegations + nested spawns: NOT_VISIBLE")

    cascades = [(int(r["cascade-attempts"]), int(r["cascade-escalations"]))
                for r in valid_batch_rows
                if _is_int_str(r.get("cascade-attempts"))
                and _is_int_str(r.get("cascade-escalations"))
                and int(r["cascade-attempts"]) > 0]
    if cascades:
        total_attempts = sum(a for a, _ in cascades)
        total_esc = sum(e for _, e in cascades)
        rate = total_esc / total_attempts
        breach = not (0.10 <= rate <= 0.40)
        print(f"cascade escalation rate: {rate:.2f} (target 0.10-0.40)"
              f"{' BREACH' if breach else ''}")
        kpi_bad = kpi_bad or breach
    else:
        print("cascade escalation rate: NOT_VISIBLE (no cascade attempts recorded)")

    # ---- calibration: score every row carrying both estimate-min and the
    # actual duration-min it predicted (core §0.15 extension). ----
    scored = []
    for r in valid_ledger_rows:
        est, act = r.get("estimate-min"), r.get("duration-min")
        if _is_int_str(est) and _is_int_str(act):
            scored.append((int(est), int(act)))
    n_scored = len(scored)
    if n_scored == 0:
        print(f"estimate calibration: {NOT_VISIBLE} (n=0 scored, basis: none yet)")
    else:
        ape = [abs(a - e) / a * 100 for e, a in scored if a != 0]
        mape = sum(ape) / len(ape) if ape else 0.0
        hit_rate = sum(1 for e, a in scored if a <= e) / n_scored * 100
        errors = sorted(a - e for e, a in scored)
        median_err = _percentile(errors, 50)
        bias = ("under-estimating" if median_err > 0
                 else "over-estimating" if median_err < 0 else "on target")
        print(f"estimate calibration: n scored={n_scored} MAPE={mape:.2f}% "
              f"p80 hit={hit_rate:.2f}% bias={bias} "
              f"(median signed error {median_err:+.1f} min)")
        breach = mape > 30 or hit_rate < 80
        print(f"estimate calibration: MAPE {mape:.2f}% (target <=30), "
              f"p80 hit {hit_rate:.2f}% (target >=80) basis=n={n_scored}"
              f"{' BREACH' if breach else ''}")
        kpi_bad = kpi_bad or breach

    return 1 if (bad or kpi_bad) else 0


ROUTE_MIN_N = 5
ROUTE_ESCALATE_CAUSES = {"CAPABILITY_LIMIT", "IMPLEMENTATION_DEFECT", "TEST_FAILURE"}
ROUTE_CAUSES = FAILURE_CLASSES | {"ENVIRONMENT_FAILURE"}


def route_decide(rows, task_class, failed=None, cause=None, ran_on=None):
    """Pure routing rule (owner 2026-10-02). rows: ledger dicts. Floor is sonnet,
    never haiku. Returns the line to print."""
    if failed is not None:
        if cause not in ROUTE_CAUSES:
            return f"STOP cause {cause} is not a §0.12 class", 1
        if ran_on == "opus":
            return f"STOP cause {cause}: opus already used; one escalation per stage -- report the failing line", 0
        if cause in ROUTE_ESCALATE_CAUSES:
            return (f"ESCALATE opus cause {cause} gate \"{failed}\" -- once; record "
                    f"escalations=1 on the row; then stop and report"), 0
        return f"STOP cause {cause}: a higher model does not fix it -- report the failing line", 0
    ev = [r for r in rows if r.get("task-class") == task_class
          and "sonnet" in (r.get("runtime") or "").lower()
          and r.get("verify-status") not in (None, "")]
    n = len(ev)
    ok = sum(1 for r in ev if r["verify-status"] == "ok"
             and r.get("retries") in (None, "", "0") and r.get("escalations") in (None, "", "0"))
    if n < ROUTE_MIN_N:
        return f"START sonnet EFFORT high -- learning ({n}/{ROUTE_MIN_N}) class={task_class}", 0
    rate = 100 * ok / n
    if rate < 60:
        return f"START opus EFFORT high -- n={n} sonnet runs, first-pass {rate:.0f}% < 60% class={task_class}", 0
    # effort is lowered only on rows whose effort cell is recorded; blank rows never lower it
    for eff in ("low", "medium"):
        g = [r for r in ev if r.get("effort") == eff]
        if len(g) >= ROUTE_MIN_N and all(
                r["verify-status"] == "ok" and r.get("retries") in (None, "", "0")
                and r.get("escalations") in (None, "", "0") for r in g):
            return f"START sonnet EFFORT {eff} -- n={len(g)} sonnet runs at {eff}, first-pass 100% class={task_class}", 0
    return f"START sonnet EFFORT high -- no lower effort has {ROUTE_MIN_N} recorded clean runs, n={n} class={task_class}", 0


def _route_selftest():
    import tempfile
    def row(tc, vs, rt="claude-sonnet-5-5", retries="", esc=""):
        return {"task-class": tc, "runtime": rt, "verify-status": vs, "retries": retries, "escalations": esc}
    d = lambda rows, **k: route_decide(rows, "x", **k)[0]
    assert "learning (2/5)" in d([row("x", "ok")] * 2)
    assert "START opus" in d([row("x", "ok")] * 2 + [row("x", "failed")] * 3)
    assert "EFFORT high" in d([row("x", "ok")] * 5)  # blank effort never lowers
    assert "EFFORT high" in d([row("x", "ok")] * 4 + [row("x", "failed")])
    assert d([], failed="g", cause="TEST_FAILURE", ran_on="sonnet").startswith("ESCALATE opus")
    assert d([], failed="g", cause="CAPABILITY_LIMIT", ran_on="sonnet").startswith("ESCALATE opus")
    assert d([], failed="g", cause="TEST_FAILURE", ran_on="opus").startswith("STOP")
    assert d([], failed="g", cause="ENVIRONMENT_FAILURE", ran_on="sonnet").startswith("STOP")
    assert d([row("x", "ok", rt="claude-haiku")] * 9).startswith("START sonnet EFFORT high -- learning (0/5)")
    # effort grouping; blank effort never lowers
    e = lambda eff, vs="ok": dict(row("x", vs), effort=eff)
    assert "EFFORT medium" in d([e("medium")] * 5)
    assert "EFFORT low" in d([e("low")] * 5)
    assert "EFFORT high" in d([e("medium")] * 4 + [e("")])
    assert "EFFORT high" in d([e("", "ok")] * 5 + [e("medium", "failed")])
    assert "EFFORT high" in d([e("")] * 9)
    # header migration keeps every row
    with tempfile.TemporaryDirectory() as t:
        led = Path(t) / "ledger.md"
        old = [c for c in LEDGER_COLUMNS if c != "effort"]
        led.write_text("| " + " | ".join(old) + " |\n|" + "---|" * len(old) + "\n"
                       + ("| " + " | ".join("v" for _ in old) + " |\n") * 3
                       + ("| " + " | ".join("v" for _ in old[:-1]) + " |\n"), encoding="utf-8")
        assert _migrate_ledger(led) == 4 and _migrate_ledger(led) == 0
        assert len(_parse_table(led, LEDGER_COLUMNS)) == 4
        assert all("__column_count__" not in r for _n, r in _parse_table(led, LEDGER_COLUMNS)[:3])
    # end to end through the ledger parser
    with tempfile.TemporaryDirectory() as t:
        led = Path(t) / ".agent-ops" / "ledger.md"
        led.parent.mkdir()
        hdr = "| " + " | ".join(LEDGER_COLUMNS) + " |\n|" + "---|" * len(LEDGER_COLUMNS) + "\n"
        line = {c: "" for c in LEDGER_COLUMNS}
        line.update({"runtime": "claude-sonnet-5-5", "task-class": "x", "verify-status": "ok", "exec-status": "ok"})
        led.write_text(hdr + ("| " + " | ".join(line[c] for c in LEDGER_COLUMNS) + " |\n") * 5, encoding="utf-8")
        class A: project = t; task_class = "x"; failed = None; cause = None; ran_on = None; selftest = False
        assert cmd_route(A) == 0
    print("route selftest: ok")


def cmd_route(args):
    """Learning router: start model + effort per task-class from ledger.md;
    with --failed, the one-step escalation decision after a failed verifier."""
    if args.selftest:
        return _route_selftest()
    if not args.project or not args.task_class:
        print("route: <project> --class C required")
        return 1
    if args.failed is not None and not args.cause:
        print("route: --failed needs --cause <§0.12 class>")
        return 1
    led = agent_ops_root(args.project) / "ledger.md"
    # a ledger created before estimate-min existed has 26 columns: read both shapes
    old = [c for c in LEDGER_COLUMNS if c != "effort"]
    rows = [r for cols in (LEDGER_COLUMNS, LEDGER_COLUMNS[:-1], old, old[:-1])
            for _n, r in _parse_table(led, cols) if "__column_count__" not in r]
    line, rc = route_decide(rows, args.task_class, args.failed, args.cause, args.ran_on or "sonnet")
    print(line)
    return rc


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("project")
    p_init.add_argument("run_id")
    p_init.set_defaults(func=cmd_init)

    p_digest = sub.add_parser("digest")
    p_digest.add_argument("project")
    p_digest.add_argument("run_id")
    p_digest.set_defaults(func=cmd_digest)

    p_ledger = sub.add_parser("ledger")
    p_ledger.add_argument("project")
    p_ledger.add_argument("run_id")
    p_ledger.add_argument("--agent", required=True)
    p_ledger.add_argument("--stage", required=True)
    p_ledger.add_argument("--status", required=True,
                          help="execution status (validated: ok|partial|failed)")
    p_ledger.add_argument("--runtime", default=None,
                          help="provider/model runtime id actually used")
    p_ledger.add_argument("--model", default=None, help="legacy alias of --runtime")
    p_ledger.add_argument("--tier", default=None,
                          help="DETERMINISTIC|FREE-LOCAL|ECONOMY|STANDARD|FRONTIER")
    p_ledger.add_argument("--effort", default=None, help="low|medium|high actually used")
    p_ledger.add_argument("--task-class", dest="task_class", default=None)
    p_ledger.add_argument("--role", default=None,
                          help="director | worker | interpreter | verifier")
    for _tok in ("cached-in", "uncached-in", "output", "reasoning",
                 "model-calls", "tool-calls", "workers", "retries",
                 "duration-min", "defects", "escalations", "estimate-min"):
        p_ledger.add_argument("--" + _tok, dest=_tok.replace("-", "_"),
                              default=None,
                              help="integer, or omit -- never NOT_MEASURED here")
    p_ledger.add_argument("--verify-status", dest="verify_status", default=None)
    p_ledger.add_argument("--final-status", dest="final_status", default=None)
    p_ledger.add_argument("--cost", default=None,
                          help="requires --basis; estimated and actual never mixed")
    p_ledger.add_argument("--basis", default=None, choices=["actual", "estimated"])
    p_ledger.add_argument("--note", default=None,
                          help="one line: cause of an overrun, or why reworked")
    p_ledger.add_argument("--rework", default=None, help="y|n")
    p_ledger.set_defaults(func=cmd_ledger)

    p_claim = sub.add_parser("claim")
    p_claim.add_argument("project")
    p_claim.add_argument("run_id")
    p_claim.add_argument("--agent", required=True)
    p_claim.add_argument("--paths", required=True, nargs="+")
    p_claim.set_defaults(func=cmd_claim)

    p_verify = sub.add_parser("verify")
    p_verify.add_argument("project")
    p_verify.add_argument("--run-id", dest="run_id", default=None)
    p_verify.set_defaults(func=cmd_verify)

    p_batch = sub.add_parser("batch")
    p_batch.add_argument("project")
    p_batch.add_argument("run_id", help="the TASK_ID")
    for _f in BATCH_FIELDS:
        p_batch.add_argument("--" + _f, dest=_f.replace("-", "_"),
                             default=GOVERNANCE_VERSION
                             if _f == "governance-version" else None)
    p_batch.set_defaults(func=cmd_batch)

    p_estimate = sub.add_parser("estimate")
    p_estimate.add_argument("project")
    p_estimate.add_argument("--task-class", dest="task_class", required=True)
    p_estimate.add_argument("--metric", default="duration-min",
                            choices=list(ESTIMATE_METRICS))
    p_estimate.set_defaults(func=cmd_estimate)


    p_sweep = sub.add_parser("sweep")


    p_sweep.add_argument("project")


    p_sweep.add_argument("--run-id", dest="run_id", default=None)


    p_sweep.add_argument("--tag", action="append", default=[],


                         help="a session tag to match in process command lines")


    p_sweep.add_argument("--released", action="append", default=[],


                         help="run-ids whose claims are deliberately kept")


    p_sweep.set_defaults(func=cmd_sweep)

    p_route = sub.add_parser("route")
    p_route.add_argument("project", nargs="?")
    p_route.add_argument("--class", dest="task_class")
    p_route.add_argument("--failed", default=None, help="the failed gate line")
    p_route.add_argument("--cause", default=None, help="§0.12 failure class")
    p_route.add_argument("--ran-on", dest="ran_on", default=None, choices=["sonnet", "opus"])
    p_route.add_argument("--selftest", action="store_true")
    p_route.set_defaults(func=cmd_route)

    p_stale = sub.add_parser("stale")
    p_stale.add_argument("project")
    p_stale.set_defaults(func=cmd_stale)

    args = ap.parse_args()
    rc = args.func(args)
    sys.exit(rc or 0)


if __name__ == "__main__":
    main()
