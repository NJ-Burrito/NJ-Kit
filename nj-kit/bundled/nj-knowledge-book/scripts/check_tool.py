#!/usr/bin/env python3
"""check_tool.py -- does a TOOL page teach by doing, and does its code parse? (stdlib; node and bash for the parsers). PYTHONUTF8=1 assumed.

    check_tool.py [page.md ...]        pages of kind `tool` (default: every such page under <pages>)
    check_tool.py --selftest

Project = BOOK_ROOT env or cwd; book.json: pages, practice, kinds (a folder of kind "tool"). A tool page carries:
  * `## Do it yourself`  with EXACTLY 3 tasks, each a `### Task N: <title>` heading holding
        Done when:        followed by a fenced command (the thing the learner runs), and
        Expected:         the exact output or exit code (text on the line, or a fenced block).
  * `## Check yourself`  naming exactly 3 bank questions `Q-<slug>-NN` that exist in <practice>/<slug>.md, each with
        `objective: TASK-1` / `TASK-2` / `TASK-3` (one per task, so the questions test the tasks).
  * every fenced code block parses: json (json.loads), py/python (ast), js/mjs/cjs (node --check), ts (types stripped, then node --check),
    bash/sh (bash -n), yaml/yml (PyYAML when installed). An info string containing `nocheck` skips a block and is counted.
Prints one line per page; exit 0 ok, 1 any failure, 3 when only a parser was missing (a SKIP line says which: never a pass).
What it does not do: run the commands. Running them against a real target is stage 5 and is recorded on the page.
"""
import ast, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_pages as cp
import check_teach as ct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = cp.ROOT
FENCE = re.compile(r"^```[ \t]*([^\n`]*)\n(.*?)^```[ \t]*$", re.S | re.M)
LANGS = {"json": "json", "py": "py", "python": "py", "js": "js", "javascript": "js", "mjs": "js", "cjs": "js", "ts": "ts", "typescript": "ts",
         "bash": "sh", "sh": "sh", "shell": "sh", "zsh": "sh", "yaml": "yaml", "yml": "yaml"}


def _msg(stderr, default="does not parse"):
    """The informative line of a node/bash error (not the trailing 'Node.js v24' banner)."""
    lines = [l.strip() for l in stderr.strip().splitlines() if l.strip() and not l.strip().startswith(("Node.js v", "at ", "^", "file:///"))]
    err = [l for l in lines if "Error" in l or "error" in l or "unexpected" in l.lower()]
    return (err or lines or [default])[0][:120]


def parse_block(lang, code):
    """-> None if it parses, a message if it does not, or ("SKIP", why) when no parser is available."""
    try:
        if lang == "json":
            json.loads(code)
        elif lang == "py":
            ast.parse(code)
        elif lang in ("js", "ts"):
            node = shutil.which("node")
            if not node:
                return ("SKIP", "node is not installed")
            with tempfile.TemporaryDirectory() as td:
                src = Path(td) / "b.mjs"
                if lang == "ts":
                    strip = ("const m=require('node:module');const fs=require('fs');"
                             "fs.writeFileSync(process.argv[2],m.stripTypeScriptTypes(fs.readFileSync(process.argv[1],'utf8')))")
                    (Path(td) / "in.ts").write_text(code, encoding="utf-8")
                    r = subprocess.run([node, "--no-warnings", "-e", strip, str(Path(td) / "in.ts"), str(src)], capture_output=True, text=True)
                    if r.returncode != 0:
                        if "ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX" in r.stderr:
                            return None  # valid TypeScript that is not erasable (parameter property, enum): it parsed, strip-only mode just cannot emit it
                        if "stripTypeScriptTypes" in r.stderr and "not a function" in r.stderr:
                            return ("SKIP", "this node cannot strip TypeScript types")
                        return _msg(r.stderr, "TypeScript does not parse")
                else:
                    src.write_text(code, encoding="utf-8")
                r = subprocess.run([node, "--check", str(src)], capture_output=True, text=True)
                if r.returncode != 0:
                    return _msg(r.stderr)
        elif lang == "sh":
            bash = shutil.which("bash")
            if not bash:
                return ("SKIP", "bash is not installed")
            r = subprocess.run([bash, "-n"], input=code, capture_output=True, text=True)
            if r.returncode != 0:
                return _msg(r.stderr)
        elif lang == "yaml":
            try:
                import yaml
            except ImportError:
                return ("SKIP", "PyYAML is not installed (uv pip install pyyaml)")
            list(yaml.safe_load_all(code))
    except (ValueError, SyntaxError) as e:
        return f"{type(e).__name__}: {str(e).splitlines()[0][:100]}"
    except Exception as e:  # yaml.YAMLError and friends
        return f"{type(e).__name__}: {str(e).splitlines()[0][:100] if str(e) else ''}"
    return None


def tasks_of(text):
    for lv, h, sub in ct.subtrees(text):
        if lv == 2 and re.search(r"do it yourself", h, re.I):
            return [(h2, b2) for lv2, h2, b2 in ct.subtrees(sub_with_heading(sub)) if lv2 in (3, 4) and re.match(r"(task\s*\d+|\d+[.)])", h2, re.I)]
    return None


def sub_with_heading(body):
    return body  # subtrees() reads headings inside the body text itself


def section(text, pattern):
    for lv, h, sub in ct.subtrees(text):
        if lv == 2 and re.search(pattern, h, re.I):
            return sub
    return None


def check_page(cfg, path, text, bank_of):
    """-> (errors, info dict, skips [(lang, why)]). bank_of(slug) -> parsed bank or None."""
    slug = Path(path).stem
    errs, skips = [], []
    tasks = tasks_of(text)
    if tasks is None:
        errs.append("no `## Do it yourself` section")
    else:
        if len(tasks) != 3:
            errs.append(f"Do it yourself has {len(tasks)} task(s), exactly 3 are required (### Task N: <title>)")
        for h, body in tasks:
            clean = re.sub(r"<!--.*?-->", "", body, flags=re.S)
            dm = re.search(r"(?mi)^\s*(?:[-*]\s*)?\**done when\**\s*:?", clean)
            if not dm:
                errs.append(f"'{h[:30]}': no `Done when:` line")
            elif not any(f.group(2).strip() for f in FENCE.finditer(clean[dm.end():])):
                errs.append(f"'{h[:30]}': `Done when:` holds no fenced command")
            em = re.search(r"(?mi)^\s*(?:[-*]\s*)?\**expected\**\s*:?\**[ \t]*(\S[^\n]*)?$", clean)
            if not em:
                errs.append(f"'{h[:30]}': no `Expected:` line (the exact output or exit code)")
            elif not (em.group(1) or "").strip() and not any(f.group(2).strip() for f in FENCE.finditer(clean[em.end():])):
                errs.append(f"'{h[:30]}': `Expected:` is empty")
    chk = section(text, r"check yourself")
    bank = bank_of(slug)
    if chk is None:
        errs.append("no `## Check yourself` section")
    else:
        ids = sorted(set(re.findall(rf"Q-{re.escape(slug)}-\d+", chk)))
        if len(ids) != 3:
            errs.append(f"Check yourself names {len(ids)} question id(s) Q-{slug}-NN, exactly 3 are required")
        if bank is None:
            errs.append(f"no bank file for {slug} (Check yourself points at it)")
        else:
            byid = {q["id"]: q for q in bank["questions"]}
            seen = set()
            for i in ids:
                q = byid.get(i)
                if q is None:
                    errs.append(f"{i} is not in the bank")
                    continue
                m = re.search(r"TASK-(\d)", q["objective"])
                if not m:
                    errs.append(f"{i}: objective must be TASK-1, TASK-2 or TASK-3 (got '{q['objective']}')")
                else:
                    seen.add(m.group(1))
            if len(ids) == 3 and seen != {"1", "2", "3"} and all(i in byid for i in ids):
                errs.append(f"the 3 questions must test TASK-1, TASK-2 and TASK-3 once each (got {sorted(seen)})")
    n = parsed = nocheck = 0
    for m in FENCE.finditer(text):
        info = m.group(1).strip().lower()
        lang = LANGS.get(info.split()[0].strip("{}.") if info else "")
        if not lang:
            continue
        n += 1
        if "nocheck" in info:
            nocheck += 1
            continue
        line = text.count("\n", 0, m.start()) + 1
        r = parse_block(lang, m.group(2))
        if r is None:
            parsed += 1
        elif isinstance(r, tuple):
            skips.append((lang, r[1]))
        else:
            errs.append(f"{lang} block at line {line} does not parse: {r}")
    return errs, dict(tasks=len(tasks or []), checks=len(re.findall(rf"Q-{re.escape(slug)}-\d+", chk or "")), blocks=n, parsed=parsed, nocheck=nocheck), skips


# ---------------------------------------------------------------- selftest
def selftest():
    cfg = {"title": "T", "slug": "t", "pages": "pg", "kinds": {"tool": "tool"}}
    task = lambda n, cmd="echo hi", exp="Expected: `hi`": f"### Task {n}: step {n}\nDo the thing.\nDone when:\n```bash\n{cmd}\n```\n{exp}\n"
    page = ("# PW\n## 1. What it is\nx\n## 9. Do it yourself\n" + task(1) + task(2) + task(3) +
            "## 10. Check yourself\n- Q-pw-01 one\n- Q-pw-02 two\n- Q-pw-03 three\n## 11. Sources\nx\n")
    mkq = lambda objs: cp.parse_bank("".join(f"### Q-pw-0{i}\nobjective: {o}\nlevel: K2\nbasis: KB#1\nStem?\na) x\nb) y\n" for i, o in enumerate(objs, 1)), "Q-pw-01: a\nQ-pw-02: a\nQ-pw-03: a\n")
    bank = mkq(["TASK-1", "TASK-2", "TASK-3"])
    chk = lambda p=page, b=bank: check_page(cfg, "pg/pw.md", p, lambda s: b)
    e, info, sk = chk()
    assert e == [] and info["tasks"] == 3 and info["checks"] == 3 and info["parsed"] == 3 and not sk, (e, info, sk)
    assert any("exactly 3" in x and "2 task" in x for x in chk(page.replace(task(3), ""))[0]), "two tasks passed"
    assert any("no `Done when:`" in x for x in chk(page.replace("Done when:\n", ""))[0]), "a task without Done when passed"
    assert any("no fenced command" in x for x in chk(page.replace("```bash\necho hi\n```\n", "", 1))[0]), "Done when without a command passed"
    assert any("no `Expected:`" in x for x in chk(page.replace("Expected: `hi`\n", "", 1))[0]), "a task without Expected passed"
    assert any("`Expected:` is empty" in x for x in chk(page.replace("Expected: `hi`\n", "Expected:\n", 1))[0])
    assert chk(page.replace("Expected: `hi`\n", "Expected:\n```\nhi\n```\n", 1))[0] == [], "Expected as a fenced block is fine"
    assert any("no `## Do it yourself`" in x for x in chk(page.replace("Do it yourself", "Exercises"))[0])
    assert any("no `## Check yourself`" in x for x in chk(page.replace("Check yourself", "Quiz"))[0])
    assert any("exactly 3 are required" in x and "2 question" in x for x in chk(page.replace("- Q-pw-03 three\n", ""))[0]), "two check questions passed"
    assert any("Q-pw-03 is not in the bank" in x for x in chk(b=mkq(["TASK-1", "TASK-2"]))[0]), "an id missing from the bank passed"
    assert any("objective must be TASK" in x for x in chk(b=mkq(["TASK-1", "TASK-2", "FL-1.1"]))[0]), "a non-TASK objective passed"
    assert any("once each" in x for x in chk(b=mkq(["TASK-1", "TASK-1", "TASK-2"]))[0]), "two questions on one task passed"
    assert any("no bank file" in x for x in check_page(cfg, "pg/pw.md", page, lambda s: None)[0])
    # fenced code must parse
    blk = lambda lang, code: page.replace("## 11. Sources", f"```{lang}\n{code}\n```\n## 11. Sources")
    assert chk(blk("json", '{"a": [1, 2]}'))[0] == [] and any("json block" in x for x in chk(blk("json", '{"a": [1, 2,]}'))[0]), "json"
    assert chk(blk("python", "x = [1]\nprint(x)"))[0] == [] and any("py block" in x for x in chk(blk("python", "def f(:\n  pass"))[0]), "python"
    assert chk(blk("bash", "for f in *; do echo $f; done"))[0] == [] and any("sh block" in x for x in chk(blk("bash", "if then fi ("))[0]), "bash"
    if shutil.which("node"):
        assert chk(blk("js", "import x from 'y';\nconst a = async () => { await x(); };"))[0] == [] and any("js block" in x for x in chk(blk("js", "const = ;"))[0]), "js"
        e_ts = chk(blk("ts", "const x: number = 1;\nexport const f = (a: string): string => a;"))
        assert (e_ts[0] == [] or e_ts[2]) and (any("ts block" in x for x in chk(blk("ts", "const x: = ;"))[0]) or chk(blk("ts", "const x: = ;"))[2]), "ts"
    if shutil.which("node"):
        e_pp = chk(blk("ts", "class A { constructor(private page: string) {} }"))
        assert e_pp[0] == [], "valid TypeScript that strip-only mode cannot emit (parameter property) is a parse success, not a failure"
    # v6.1: a `# comment` inside the Done-when fence must not cut the task short (Expected: comes after the fence)
    cm = page.replace("```bash\necho hi\n```\nExpected: `hi`\n", "```bash\n# list the tests\necho hi\n```\nExpected: `hi`\n", 1)
    assert cm != page and chk(cm)[0] == [], chk(cm)[0]
    assert any("no `Expected:`" in x for x in chk(cm.replace("Expected: `hi`\n", "", 1))[0]), "and a task missing Expected still fails"
    e_y, _, sk_y = chk(blk("yaml", "a: [1, 2\nb: {"))
    try:
        import yaml  # noqa: F401
        assert any("yaml block" in x for x in e_y), "yaml"
    except ImportError:
        assert sk_y and sk_y[0][0] == "yaml", "a missing YAML parser must be a SKIP, never a pass"
    assert chk(blk("json nocheck", "{broken"))[1]["nocheck"] == 1 and chk(blk("json nocheck", "{broken"))[0] == [], "nocheck skips a block and is counted"
    assert chk(blk("text", "not code {"))[0] == [] and chk(blk("", "also {"))[0] == [], "unlabelled and text blocks are not parsed"
    print("selftest ok"); return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    try:
        cfg = cp.load_cfg()
    except cp.ConfigError as e:
        print(f"FAIL {e}"); return 1
    pages_root = ROOT / cfg["pages"]
    allp = sorted(p for p in pages_root.rglob("*.md") if not p.name.startswith("_")) if pages_root.is_dir() else []
    if not allp:
        print(f"FAIL no pages found under {pages_root} (check 'pages' in book.json)"); return 1
    args = [a for a in argv if not a.startswith("--")]
    missing = [a for a in args if not os.path.exists(a)]
    if missing:
        print(f"FAIL no such page: {missing}"); return 1
    paths = [Path(a) for a in args] or allp
    bank_of = lambda slug: cp.load_bank(ROOT / (cfg.get("practice") or "practice") / f"{slug}.md") if (ROOT / (cfg.get("practice") or "practice") / f"{slug}.md").exists() else None
    fails = n = skipped = 0
    for p in paths:
        try:
            kind = cp.profile_for(cfg, cp.folder_of(p, pages_root))[0]
        except cp.ConfigError as e:
            print(f"FAIL {p}  :: {e}"); fails += 1; continue
        if kind != "tool":
            continue
        n += 1
        errs, info, sk = check_page(cfg, p, p.read_text(encoding="utf-8"), bank_of)
        skipped += bool(sk)
        print(f"{'FAIL' if errs else 'ok  '} {os.path.relpath(p, ROOT)}  tasks={info['tasks']} checks={info['checks']} blocks={info['blocks']} parsed={info['parsed']} nocheck={info['nocheck']}"
              + (f" skipped={len(sk)}" if sk else "") + (f"  :: {'; '.join(errs)}" if errs else ""))
        for lang, why in sorted(set(sk)):
            print(f"SKIP {os.path.relpath(p, ROOT)}  {lang} blocks not parsed: {why}")
        fails += bool(errs)
    print(f"{n} tool page(s), {fails} failing" + (f", {skipped} with unparsed blocks (SKIP)" if skipped else ""))
    if fails:
        return 1
    return 3 if skipped else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
