"""Real token use from a session's transcripts, per service and per model. Read-only, stdlib.

usage: python -X utf8 tokens.py SESSION_DIR [--since HH:MM] [--run RUN_DIR] [--until HH:MM] [--service KEY] [--json [--out FILE]]
--json: the machine output the hub reads (docs/ARCHITECTURE.md 3.7): per service, per role, per model {fresh, cache_read}, the
        service's state against the budget (ok < 2.5M, warn >= 2.5M, stop >= 3.0M fresh), and the director's own use. --out writes it
        to FILE atomically as well as printing it.
--service: one service only, one row per crew role, so services never mix.
--budget N: with --service, exit 3 and print STOP when the service's fresh tokens pass N thousand, WARN past half.
--run: RUN_DIR/<KEY>/raw/*.json folds each sub-task's key into its service.
SESSION_DIR = ~/.claude/projects/<project>/<session id>; its <session id>.jsonl beside it is the director.
Counts input + output + cache creation. Cache reads are shown apart: they are far cheaper and would drown the rest.
"""
import collections, json, os, pathlib, re, sys

KEY = re.compile(r"PROJ-\d{4}")


def family(model):
    for f in ("opus", "sonnet", "haiku", "fable"):
        if f in (model or ""):
            return f.capitalize()
    return "other"


def role_of(text):
    "The crew role from an agent's first message."
    m = re.search(r"nj-qa-(leader|harvester|tester|scavenger)", text)
    if m:
        return m[1].capitalize()
    n = re.search(r"[Yy]our name[:\s]+([\w-]+)", text)
    name = (n[1] if n else "").lower()
    for prefix, role in (("t-", "Tester"), ("tester", "Tester"), ("scav", "Scavenger"), ("harv", "Harvester")):
        if name.startswith(prefix):
            return role
    return "Leader" if "leader" in text[:400].lower() else "Other"


def first_text(rec):
    c = (rec.get("message") or {}).get("content")
    if isinstance(c, str):
        return c
    return " ".join(x.get("text", "") for x in c or [] if isinstance(x, dict))


last_role = "Other"


def read(path, since=None, until=None):
    """-> (service found in the first message, {model family: [fresh, cache read]})"""
    service, seen, out = None, set(), collections.defaultdict(lambda: [0, 0])
    global last_role
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if service is None and r.get("type") == "user":
                m = KEY.search(first_text(r))
                service = m[0] if m else ""
                last_role = role_of(first_text(r))
            m = r.get("message") or {}
            u = m.get("usage") if isinstance(m, dict) else None
            if not u or m.get("id") in seen:
                continue
            if since and r.get("timestamp", "")[11:16] < since:
                continue
            if until and r.get("timestamp", "")[11:16] >= until:
                continue
            seen.add(m.get("id"))
            t = out[family(m.get("model"))]
            t[0] += u.get("input_tokens", 0) + u.get("output_tokens", 0) + u.get("cache_creation_input_tokens", 0)
            t[1] += u.get("cache_read_input_tokens", 0)
    return service or "", out


def table(rows):
    """rows = {stage: {model: [fresh, read]}} -> markdown, models always in the same order."""
    models = ["Opus", "Sonnet", "Haiku"]
    k = lambda n: f"{n / 1000:,.0f}k"
    lines = ["| Stage | " + " | ".join(models) + " | Total | Cache reads |", "|---|" + "---:|" * (len(models) + 2)]
    tot = collections.defaultdict(lambda: [0, 0])
    for stage in sorted(rows):
        r = rows[stage]
        for m, v in r.items():
            tot[m][0] += v[0]
            tot[m][1] += v[1]
        lines.append(f"| {stage} | " + " | ".join(k(r[m][0]) if m in r else "0k" for m in models) + f" | {k(sum(v[0] for v in r.values()))} | {k(sum(v[1] for v in r.values()))} |")
    lines.append("| **Total** | " + " | ".join(k(tot[m][0]) if m in tot else "0k" for m in models) + f" | {k(sum(v[0] for v in tot.values()))} | {k(sum(v[1] for v in tot.values()))} |")
    return "\n".join(lines)


BUDGET_K, STOP_K = 2500, 3000


def pair(v):
    return {"fresh": v[0], "cache_read": v[1]}


def collect(d, since=None, parent=None, until=None):
    """-> the Tokens object of the contract. Services are told apart by the ticket key in the sub-agent's first message."""
    parent = parent or {}
    director = {}
    own_file = d.parent / f"{d.name}.jsonl"
    if own_file.exists():
        _, own = read(own_file, since, until)
        director = {m.lower(): pair(v) for m, v in own.items()}
    services = {}
    for f in sorted((d / "subagents").glob("*.jsonl")):
        service, use = read(f, since, until)
        service = parent.get(service, service)
        if not service:
            continue
        role = last_role.lower()
        roles = services.setdefault(service, {})
        cell = roles.setdefault(role, {})
        for m, v in use.items():
            c = cell.setdefault(m.lower(), [0, 0])
            c[0] += v[0]
            c[1] += v[1]
    out = {}
    for key in sorted(services):
        roles = {r: {m: pair(v) for m, v in sorted(cell.items())} for r, cell in sorted(services[key].items())}
        total = [sum(p["fresh"] for c in roles.values() for p in c.values()), sum(p["cache_read"] for c in roles.values() for p in c.values())]
        fresh_k = total[0] / 1000
        out[key] = {"state": "stop" if fresh_k >= STOP_K else "warn" if fresh_k >= BUDGET_K else "ok", "roles": roles, "total": pair(total)}
    import datetime
    return {"v": 1, "at": os.environ.get("NJQA_NOW") or datetime.datetime.now().replace(microsecond=0).isoformat(),
            "budget_k": BUDGET_K, "stop_k": STOP_K, "services": out, "director": dict(sorted(director.items()))}


def main():
    d = pathlib.Path(sys.argv[1])
    since = sys.argv[sys.argv.index("--since") + 1] if "--since" in sys.argv else None
    until = sys.argv[sys.argv.index("--until") + 1] if "--until" in sys.argv else None
    parent = {}
    if "--run" in sys.argv:
        for raw in pathlib.Path(sys.argv[sys.argv.index("--run") + 1]).glob("*/raw/*.json"):
            parent[raw.stem] = raw.parent.parent.name
    only = sys.argv[sys.argv.index("--service") + 1] if "--service" in sys.argv else None
    if "--json" in sys.argv:
        text = json.dumps(collect(d, since, parent, until), ensure_ascii=False, indent=1)
        if "--out" in sys.argv:
            out = pathlib.Path(sys.argv[sys.argv.index("--out") + 1])
            tmp = out.with_name(out.name + f".{os.getpid()}.tmp")
            tmp.write_text(text + "\n", encoding="utf-8")
            os.replace(tmp, out)
        print(text)
        return
    rows = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
    _, own = read(d.parent / f"{d.name}.jsonl", since) if (d.parent / f"{d.name}.jsonl").exists() else ("", {})
    for m, v in ({} if only else own).items():
        rows["Director"][m][0] += v[0]
        rows["Director"][m][1] += v[1]
    for f in sorted((d / "subagents").glob("*.jsonl")):
        service, use = read(f, since)
        service = parent.get(service, service)
        if only and service != only:
            continue
        row = last_role if only else (service or "other")
        for m, v in use.items():
            rows[row][m][0] += v[0]
            rows[row][m][1] += v[1]
    print(table(rows))
    if only and "--budget" in sys.argv:
        cap = int(sys.argv[sys.argv.index("--budget") + 1]) * 1000
        spent = sum(v[0] for r in rows.values() for v in r.values())
        if spent >= cap:
            print(f"STOP: {spent // 1000}k of {cap // 1000}k spent. Finish what's in flight, start nothing new, report.")
            sys.exit(3)
        if spent >= cap / 2:
            print(f"WARN: {spent // 1000}k of {cap // 1000}k spent.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main()
