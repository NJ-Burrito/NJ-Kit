#!/usr/bin/env python3
"""book_status.py -- where is the book? Derived, never recorded; writes nothing. (stdlib) PYTHONUTF8=1 assumed.

    book_status.py                      one line per page slug: research / entries / page / teach / twin
    book_status.py plan [--items N] [--slots 20]     recommended topology for N items, with the arithmetic
    book_status.py --selftest

Project = BOOK_ROOT env or cwd (book.json + kb/kb.json). A stage is `done` only when its gate would pass right now:
the check functions of check_pages.py / check_teach.py / audit_sample.py are run in-process, so a file that merely
exists never counts. Stages per slug (slug = page file stem; entries are those whose topic equals the slug):
  research  done = research/<slug>.md exists AND the slug has entries      (todo otherwise)
  entries   done = at least one entry and none of them draft/retracted     (shows <verified>v/<draft>d)
  page      done = check_pages gate passes for the page                    (FAIL(first reason) otherwise; todo = no page)
  teach     done = check_teach gate passes; n/a for kinds that do not teach
  probe     (only when the page has a bank) ok | GUESSABLE | none, from audit/probe/<slug>.ans written by probe_bank.py's blind prober
  tool      (kind tool only) done = check_tool gate passes (Do it yourself, Check yourself, fenced code parses) and its bank passes check_teach
  twin      done = pair fingerprint passes; n/a with no twin configured; todo = twin page missing
The last line is the audit (audit/entries.md and audit/banks.md all `held`, current, big enough). Exit 0 when every stage that applies is done.

plan: items <= 5 -> solo; <= 12 -> one lead, no helpers; else leads = ceil(items/6), helpers only for leads with
>= 4 items (one helper per item), and waves = ceil((leads+helpers)/slots) when that exceeds the slots.
"""
import math, os, sqlite3, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_pages as cp
import check_teach as ct
import check_tool as ctool
import probe_bank as pb
import audit_sample as au
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = cp.ROOT


def ffd(footprints, cap):
    """First-fit-decreasing packing of lead+helper footprints into waves of `cap` slots -> number of waves."""
    bins = []
    for f in sorted(footprints, reverse=True):
        for i, used in enumerate(bins):
            if used + f <= cap:
                bins[i] += f
                break
        else:
            bins.append(f)
    return len(bins)


def plan(items, slots=20, reserved=0):
    """-> (dict, [lines]); raises ValueError for slots that cannot run anything. Monotone in items.
    items <= 5: solo. Otherwise leads = ceil(items/6) (groups of at most 6). Two options are printed: ONE WAVE with
    MAX_HELPERS = min(free // leads - 1, largest group) per lead (the number a brief carries), and FULL helpers (one per
    item), packed first-fit-decreasing by footprint (lead + its helpers) into the free slots."""
    free = slots - reserved
    if slots <= 0 or free < 2:
        raise ValueError(f"slots={slots}, reserved={reserved}: {free} free slot(s); need >= 2 (a lead and one helper) -- raise --slots or lower --reserved")
    L = [f"items = {items}, slots = {slots}, reserved = {reserved}, free = {free}"]
    if items <= 5:
        L.append(f"{items} <= 5 -> solo: no lead tree, the Lead (or one worker) does every item; helpers = 0")
        return dict(mode="solo", leads=0, max_helpers=0, one_wave_workers=1, one_wave_waves=1, full_workers=1, full_waves=1, sizes=[], free=free), L
    leads = math.ceil(items / 6)
    base, extra = divmod(items, leads)
    sizes = [base + 1] * extra + [base] * (leads - extra)
    L.append(f"{items} > 5 -> leads = ceil({items} / 6) = {leads}; group sizes {sizes} (at most 6 items per lead)")
    per = free // leads
    if per >= 1:
        mh = min(per - 1, max(sizes))
        ow_workers, ow_waves = leads * (1 + mh), 1
        L.append(f"one wave : MAX_HELPERS = min({free} // {leads} - 1, {max(sizes)}) = {mh} -> workers = {leads} x (1 + {mh}) = {ow_workers}, 1 wave")
    else:
        mh, ow_waves = 0, math.ceil(leads / free)
        ow_workers = leads
        L.append(f"one wave : impossible ({leads} leads > {free} free slots); with MAX_HELPERS = 0 the {leads} leads run in ceil({leads} / {free}) = {ow_waves} waves")
    foot = [sz + 1 for sz in sizes]
    if max(foot) > free:
        fw, fwaves = None, None
        L.append(f"full helpers (one per item): infeasible -- a lead with its {max(sizes)} helpers is a footprint of {max(foot)} > {free} free slots; use MAX_HELPERS <= {free - 1}")
    else:
        fwaves, fw = ffd(foot, free), leads + items
        L.append(f"full helpers (one per item): footprints {sorted(foot, reverse=True)} packed first-fit-decreasing into {free} slots -> waves = {fwaves}, workers = {leads} + {items} = {fw}")
    L.append(f"V and B spawn no helpers: B = ceil({leads} / {free}) = {math.ceil(leads / free)} wave(s)")
    return dict(mode="leads", leads=leads, max_helpers=mh, one_wave_workers=ow_workers, one_wave_waves=ow_waves,
                full_workers=fw, full_waves=fwaves, sizes=sizes, free=free), L


def slug_rows(db, slug):
    c = sqlite3.connect(f"file:{Path(db).as_posix()}?mode=ro", uri=True, timeout=60)
    r = dict(c.execute("SELECT status,COUNT(*) FROM entries WHERE topic=? GROUP BY status", (slug,)).fetchall())
    c.close()
    return r


def stage_state(cfg, root, page, status_of, claim_of, entries):
    """-> dict stage -> 'done' | 'todo' | 'n/a' | 'FAIL(reason)'."""
    slug = page.stem
    s = {}
    v, d = entries.get("verified", 0), entries.get("draft", 0)  # retracted / discredited / gate-change entries are history
    text = page.read_text(encoding="utf-8")
    pages_root = root / cfg["pages"]
    try:
        kind0, _, min_cites0, _ = cp.profile_for(cfg, cp.folder_of(page, pages_root))
    except cp.ConfigError as e:
        return dict(s, page=f"FAIL({e})", teach="n/a", twin="n/a")
    if min_cites0 == 0 and not (v + d):  # a page that cites nothing (practice kind) has no research or entries stage
        s["research"] = s["entries"] = "n/a"
    else:
        s["research"] = "done" if (root / "research" / f"{slug}.md").is_file() and (v + d) else "todo"
        s["entries"] = "done" if v and not d else "todo"
    try:
        errs, _ = cp.check(page, text, status_of, cfg, claim_of, pages_root)
        kind = cp.profile_for(cfg, cp.folder_of(page, pages_root))[0]
    except cp.ConfigError as e:
        return dict(s, page=f"FAIL({e})", teach="n/a", twin="n/a")
    s["page"] = "done" if not errs else f"FAIL({errs[0]})"
    if kind in ct.teach_kinds(cfg):
        bf = root / (cfg.get("practice") or "practice") / f"{slug}.md"
        te, _ = ct.check_page(cfg, page, text, cp.load_bank(bf) if bf.exists() else None, lambda i: status_of(i) == "verified")
        s["teach"] = "done" if not te else f"FAIL({te[0]})"
    else:
        s["teach"] = "n/a"
    if kind == "tool":  # a tool page is gated by check_tool.py (Do it yourself, Check yourself, code parses); its bank by check_teach
        bf = root / (cfg.get("practice") or "practice") / f"{slug}.md"
        te, _ = ct.check_page(cfg, page, text, cp.load_bank(bf) if bf.exists() else None, lambda i: status_of(i) == "verified", teaching=False) if bf.exists() else ([], None)
        tl, _, sk = ctool.check_page(cfg, page, text, lambda sl: cp.load_bank(bf) if bf.exists() else None)
        bad = tl + te
        s["tool"] = "done" if not bad and not sk else f"FAIL({bad[0]})" if bad else "SKIP(" + sk[0][1][:30] + ")"
    if (root / (cfg.get("practice") or "practice") / f"{slug}.md").exists():  # blind stem-less probe of the bank (probe_bank.py)
        s["probe"] = pb.status(root, slug, cfg)
    if cfg.get("twin"):
        tw = root / cfg["twin"] / page.relative_to(pages_root)
        if not tw.is_file():
            s["twin"] = "todo"
        else:
            pe = cp.check_pair(text, tw.read_text(encoding="utf-8"))
            s["twin"] = "done" if not pe else f"FAIL({pe[0]})"
    else:
        s["twin"] = "n/a"
    return s


def short(x, n=44):
    return x if len(x) <= n else x[: n - 1] + "…"


def status(cfg, root):
    pages_root = root / cfg["pages"]
    pages = sorted(p for p in pages_root.rglob("*.md") if not p.name.startswith("_"))
    db = cp.db_path(root)
    if not db.exists():
        print(f"FAIL no database at {db}"); return 1
    c = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True, timeout=60)
    cache = {}

    def row(i):
        if i not in cache:
            cache[i] = c.execute("SELECT status,claim FROM entries WHERE id=?", (i,)).fetchone()
        return cache[i]
    bad = 0
    for p in pages:
        ent = slug_rows(db, p.stem)
        st = stage_state(cfg, root, p, lambda i: (row(i) or (None,))[0], lambda i: (row(i) or (None, ""))[1], ent)
        bad += any(v not in ("done", "n/a", "ok") for v in st.values())
        print(f"{p.stem:24} {p.relative_to(pages_root).parts[0] if len(p.relative_to(pages_root).parts) > 1 else '.':14} "
              f"entries={ent.get('verified', 0)}v/{ent.get('draft', 0)}d  " +
              "  ".join(f"{k}={short(v)}" for k, v in st.items()))
    a = au.summarize(root)
    print(f"audit: {'done' if a['ok'] else 'todo'}  {a['msg']}")
    bad += not a["ok"]
    print(f"{len(pages)} pages, {bad} item(s) not done")
    return 1 if bad else 0


def selftest():
    import json, shutil, tempfile
    for items, mode in ((4, "solo"), (10, "leads"), (37, "leads")):
        t, lines = plan(items, 20)
        assert t["mode"] == mode and lines[0].startswith(f"items = {items}"), (items, t)
    t, lines = plan(37, 20)
    assert (t["leads"], t["max_helpers"], t["one_wave_workers"], t["full_waves"], t["full_workers"]) == (7, 1, 14, 3, 44) and sum(t["sizes"]) == 37, t
    assert "leads = ceil(37 / 6) = 7" in " ".join(lines) and "waves = 3, workers = 7 + 37 = 44" in " ".join(lines) and "MAX_HELPERS = min(20 // 7 - 1, 6) = 1" in " ".join(lines), lines
    # round-3 breaks (orc): packing, tiny slots, bad slots, monotone, reserved
    t = plan(37, 10)[0]
    assert (t["max_helpers"], t["one_wave_waves"], t["full_waves"]) == (0, 1, 7), f"B1: footprints of 6-7 never fit twice in 10 slots: {t}"
    t, lines = plan(37, 5)
    assert t["full_waves"] is None and t["one_wave_waves"] == 2 and "infeasible" in " ".join(lines), f"B2: {t}"
    for bad in (0, -3, 1):
        try:
            plan(37, bad); raise AssertionError(f"B3: slots={bad} accepted")
        except ValueError:
            pass
    try:
        plan(37, 20, reserved=19); raise AssertionError("reserved leaving 1 slot accepted")
    except ValueError:
        pass
    assert plan(37, 20, reserved=10)[0]["free"] == 10 and plan(37, 20, reserved=10)[0]["full_waves"] == 7
    assert plan(12, 20)[0]["leads"] == 2 and plan(13, 20)[0]["leads"] == 3 and plan(6, 20)[0]["leads"] == 1 and plan(5, 20)[0]["mode"] == "solo"
    ws = [plan(n, 40)[0]["full_workers"] for n in range(1, 60)]
    assert ws == sorted(ws), f"B4: workers not monotone in items: {ws}"
    ms = [plan(n, 40)[0]["leads"] for n in range(1, 60)]
    assert ms == sorted(ms), "leads not monotone in items"
    assert ffd([7, 7, 6, 6, 6, 6, 6], 20) == 3 and ffd([7, 7, 6, 6, 6, 6, 6], 10) == 7
    # status is derived from gates, not from files
    d = Path(tempfile.mkdtemp())
    try:
        (d / "kb").mkdir(); (d / "ch" / "a").mkdir(parents=True); (d / "research").mkdir()
        cfg = {"title": "T", "slug": "t", "pages": "ch", "kinds": {"a": "regulation"}}
        (d / "book.json").write_text(json.dumps(cfg))
        db = d / "kb" / "qa.db"
        c = sqlite3.connect(db, timeout=60)
        c.execute("CREATE TABLE entries(id INTEGER PRIMARY KEY, topic TEXT, claim TEXT, status TEXT)")
        c.executemany("INSERT INTO entries VALUES(?,?,?,?)", [(1, "x", "c", "verified"), (2, "x", "c", "verified"), (3, "x", "c", "verified"), (4, "x", "c", "draft")])
        c.commit(); c.close()
        page = d / "ch" / "a" / "x.md"
        page.write_text("# X\n[KB#1] [KB#2] [KB#3] https://a.org/x\n", encoding="utf-8")  # a page FILE exists but the gate fails
        (d / "research" / "x.md").write_text("notes")
        st = lambda i: {1: "verified", 2: "verified", 3: "verified", 4: "draft"}.get(i)
        s = stage_state(cfg, d, page, st, lambda i: "c", {"verified": 3, "draft": 1})
        assert s["page"].startswith("FAIL(missing heading") and s["research"] == "done" and s["entries"] == "todo" and s["twin"] == "n/a" and s["teach"] == "n/a", s
        page.write_text("\n".join(f"## {i}. {h}" for i, h in enumerate(cp.REGULATION, 1)) + "\n[KB#1] [KB#2] [KB#3] https://a.org/x\n", encoding="utf-8")
        s = stage_state(cfg, d, page, st, lambda i: "c", {"verified": 3})
        assert s["page"] == "done" and s["entries"] == "done", s
        s = stage_state(dict(cfg, twin="ch-ar"), d, page, st, lambda i: "c", {"verified": 3})
        assert s["twin"] == "todo", s
        # F8 / B5: retracted rows are history; a practice page with no entries is n/a
        s = stage_state(cfg, d, page, st, lambda i: "c", {"verified": 3, "retracted": 1})
        assert s["entries"] == "done" and s["research"] == "done", f"B5: retracted entries counted as open: {s}"
        s = stage_state(cfg, d, page, st, lambda i: "c", {"verified": 3, "draft": 1})
        assert s["entries"] == "todo", "a real draft must still count"
        (d / "ch" / "p").mkdir()
        pr = d / "ch" / "p" / "glossary.md"
        pr.write_text("# G\n## Sources\nhttps://a.org/x\n", encoding="utf-8")
        s = stage_state(dict(cfg, kinds={"a": "regulation", "p": "practice"}), d, pr, st, lambda i: "c", {})
        assert s["research"] == "n/a" and s["entries"] == "n/a" and s["page"] == "done", f"B5: practice page read as todo: {s}"
        # K4: probe=ok | GUESSABLE | none per bank from audit/probe/<slug>.ans
        (d / "practice").mkdir(exist_ok=True)
        (d / "practice" / "x.md").write_text("".join(f"### Q-{i}\nobjective: t-1\nlevel: K1\nbasis: KB#1\nS{i}?\na) p\nb) q\nc) r\nd) s\n" for i in range(1, 11)), encoding="utf-8")
        (d / "practice" / "x.key.md").write_text("".join(f"Q-{i}: {'abcd'[i % 4]}\n" for i in range(1, 11)), encoding="utf-8")
        sp = stage_state(cfg, d, page, st, lambda i: "c", {"verified": 3})
        assert sp["probe"] == "none", sp
        (d / "audit" / "probe").mkdir(parents=True)
        (d / "audit" / "probe" / "x.ans").write_text("".join(f"Q-{i}: {'abcd'[i % 4]}\n" for i in range(1, 11)), encoding="utf-8")
        assert stage_state(cfg, d, page, st, lambda i: "c", {"verified": 3})["probe"] == "GUESSABLE", "all ten keyed from the options alone"
        (d / "audit" / "probe" / "x.ans").write_text("".join(f"Q-{i}: {'abcd'[(i + 1) % 4]}\n" for i in range(1, 11)), encoding="utf-8")
        assert stage_state(cfg, d, page, st, lambda i: "c", {"verified": 3})["probe"] == "ok"
        (d / "audit" / "probe" / "x.ans").unlink(); (d / "audit" / "probe").rmdir(); (d / "audit").rmdir()
        shutil.rmtree(d / "practice")
        before = sorted(p.name for p in d.rglob("*"))
        os.environ["BOOK_ROOT"] = str(d)
        assert sorted(p.name for p in d.rglob("*")) == before, "status wrote something"
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("selftest ok"); return 0


def main(argv):
    if "--selftest" in argv:
        return selftest()
    if argv and argv[0] == "plan":
        num = lambda flag, d: int(argv[argv.index(flag) + 1]) if flag in argv else d
        slots, reserved = num("--slots", 20), num("--reserved", 0)
        if "--items" in argv:
            items = num("--items", 0)
        else:
            try:
                cfg = cp.load_cfg()
            except cp.ConfigError as e:
                print(f"FAIL {e}"); return 1
            items = len([p for p in (ROOT / cfg["pages"]).rglob("*.md") if not p.name.startswith("_")])
        try:
            t, lines = plan(items, slots, reserved)
        except ValueError as e:
            print(f"FAIL {e}"); return 1
        print("\n".join(lines))
        print(f"-> {t['mode']}: leads={t['leads']} MAX_HELPERS(one wave)={t['max_helpers']} one_wave_workers={t['one_wave_workers']} "
              f"full_waves={t['full_waves'] if t['full_waves'] else 'infeasible'}")
        return 0
    try:
        cfg = cp.load_cfg()
    except cp.ConfigError as e:
        print(f"FAIL {e}"); return 1
    return status(cfg, ROOT)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
