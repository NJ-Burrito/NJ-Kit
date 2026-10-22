---
name: nj-laya
description: >
  Decide whether a local, token-free classifier (Laya) applies before reaching for it — for
  routing a free-text choice, triaging a Playwright/test failure, or picking a UI locator.
  Use when: a classifier or router is being considered for local/CPU/zero-token use, Laya or
  Jev come up by name, a Playwright test is failing and needs triage, an agent needs to pick
  an element/locator from a page, or someone asks "can this run without tokens" or "محلي بدون
  توكنز". Routes deterministic-first (regex/lookup/stored field) and permits Laya only inside
  a narrow, evidence-tested envelope (English, ≤10 options, suggest-only, never an action).
  Covers the PROJ Playwright harvest→script→run→triage loop as a worked example.
---

# nj-laya — deterministic first, Laya only inside ADOPT-NARROW

Devil-pass verdict, 2026-09-24: `artifacts/ops/laya-devil-2026-09-24.md`. Read it before
adopting Laya anywhere; do not re-argue it, encode it.

## Decision table

| situation | do this | not Laya because |
|---|---|---|
| answer is a stored field / DB column / foreign key | read the field | it's already known, not a classification |
| answer matches a regex / fixed error shape (timeouts, strict-mode, `expect` diffs) | regex classifier (`scripts/pw_triage.py`) | Playwright error text is structured |
| picking a locator while **authoring** a script | Claude writes it from the snapshot already in context | 0 tokens saved — Claude already has the snapshot |
| picking a locator or acting **at run time** (self-healing that clicks/submits/pays) | never — hard reject | a wrong pick can pass silently on a live system (rule 1) |
| routing which skill/tool to use | Claude's own routing (skill listing already in context) | a hook can only add context, never remove the listing |
| free-text choice, ≤10 English options, no stored field or regex answers it, wrong answer only costs a re-run | `scripts/laya_ask.mjs`, suggest-only | the one envelope the evidence supports (EN McNemar p=0.0117) |
| Arabic input | route away from Laya entirely | AR result not significant (McNemar p=0.453); no multilingual checkpoint hosted at `receptron/laya-onnx` (verified 2026-09-24, HF tree listing: only `tokenizer/`, no `multilingual/`) |
| triaging 45 motion-reference descriptions into an 8-bucket style shortlist (>10 options, out of envelope) | Haiku, gated behind a 15-label Laya accuracy check first | outside ADOPT-NARROW (rule 5, >10 options); measured 2026-09-25 anyway as a second data point — see below |

## The 14 rules (imperative, evidence in `laya-devil-2026-09-24.md`)

1. Never let a Laya answer trigger an action on a live system (click, submit, pay, send).
2. Never use Laya as a gate or verifier; write its answer to a file as a suggestion.
3. Use Laya only when the input is free text and no stored field/regex/lookup answers it.
4. English input only. No multilingual checkpoint exists at `receptron/laya-onnx` (verified
   2026-09-24: HF tree has `tokenizer/`, no `multilingual/` folder). A third-party mirror
   (`mizchi/laya-multilingual-onnx`) exists but is unverified and out of scope — do not wire it
   without a fresh probe.
5. Keep options at 10 or fewer per call; never pass a whole page snapshot.
6. Read only `choice` and `confidence`; never use `noul` or `act_probability` (upstream bugs,
   see research/laya-jev-2026-09-23.md §2).
7. Before any adoption claim, measure against a deterministic baseline with stop-words fixed
   and a synonym table.
8. Score only on text the scoring worker did not write — verbatim from SRS/spec sources.
9. Report non-quoted-item accuracy and paired McNemar, not headline accuracy.
10. Do not call Laya from a per-event Claude hook until a warm-cache `Laya.load()` is measured
    under 1 s (cold load measured 35.7 s, includes a download — not yet retested warm).
11. Do not use Laya for skill or tool routing.
12. Do not use Laya to pick PROJ locators at authoring time.
13. For Playwright failures: run `scripts/pw_triage.py` first, hand Laya only the
    `unclassified` residue, and only after 30+ real failures exist.
14. Pin the checkpoint (`revision`) and name it (English/multilingual) in every result.

## PROJ worked example (harvest → script → run → triage)

- **Harvest**: Playwright `codegen` or an aria snapshot (`browser_snapshot` / accessibility
  tree) — role + accessible name per element. Read-only, no Laya.
- **Author**: Claude writes the Playwright script from the snapshot (`getByRole`, fills,
  waits, data). Locator picking happens here, by Claude, not Laya (rule 12).
- **Run**: `npx playwright test`. Deterministic, zero tokens.
- **Triage a failure**: `python scripts/pw_triage.py --report <path>` classifies into
  `locator-changed | timeout-env | auth-session | assertion | unclassified` by regex over
  Playwright's JSON reporter output or `error-context.md` files. Only the `unclassified`
  bucket is a Laya candidate (rule 13), and only once ≥30 real failures exist — PROJ had zero
  as of the 2026-09-24 probe (`artifacts/ops/laya-PROJ-probe-2026-09-24.md`).
- **Self-healing that acts**: rejected outright (rule 1) — PROJ specs file real requests
  against a live government portal behind reCAPTCHA, and 719 swallowed `.catch(() => {})`
  mean a wrong click can pass silently.

## Scripts

- `scripts/laya_ask.mjs` — English-only, ≤10 options, pinned `revision`, suggest-only JSON to
  stdout/file. Never call it inside a per-event hook (rule 10) or on an action path (rule 1).
- `scripts/pw_triage.py` — stdlib regex classifier over a Playwright JSON report or
  `test-results/**/error-context.md`. Self-test: `python scripts/pw_triage.py --self-test`.

## Evidence outside the envelope: style-triage measurement, 2026-09-25

`kacs-v4` (ENSERA, `artifacts/research/kac-sentinel/v4/refs/`) measured Laya on an
8-bucket style classification with 45 refs, 15 hand-labelled — an **out-of-envelope**
call (>10 options, rule 5) run anyway as a gate before committing to Laya for a real
triage. **Laya accuracy = 0.40 on the 15 labelled rows (`triage.json`), below the 0.70
gate** — most wrong answers collapsed onto `kinetic-typography` regardless of the true
bucket, confidence uncorrelated with correctness (0.99 on a wrong answer, 0.54 on a
right one). Haiku triaged the same 45 rows at 1.0 against the same 15 labels
(`triage-haiku.json`) but that number is unguarded: Haiku scored its own labelled set,
so it may be label-leaked (no held-out split was possible with only 15 gold rows) — do
not cite 1.0 as a clean accuracy figure. Confirms rule 5 from the other side: this is
exactly the >10-option shape the envelope excludes, and it failed exactly as the
envelope predicts. Not a new adopted use — the entry exists so nobody re-runs this
experiment expecting a different result.

## Not yet supported

- Playwright failure triage (candidate 2/row 2): blocked on data — 0 real failures measured.
- Locator-drift hint, suggest-only (row 3b): same data gap.
- Any multilingual Arabic path: no verified hosted checkpoint; third-party mirror unverified.
- >10-option classification (style/bucket triage): measured 0.40 accuracy 2026-09-25, fails the envelope — use Haiku instead, unguarded by a clean held-out score.
