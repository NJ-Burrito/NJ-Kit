---
name: nj-automation-suite
description: 'Create an automation-tests folder (a portable, self-contained Playwright suite) like the PROJ one: layout, lib/paths.ts portability (env vars, auto-discovery, no absolute paths), HTML report + per-service Jira HTML, AI-RUN-NOTES.md, AGENT.md, PDFs (Thmanyah TrueType only), launchers, Docker image-only share, sweep-chrome, sign-in lock. Triggers: create an automation suite, scaffold test folder, make it portable, docker for the tests, report pdf. Arabic: أنشئ مجلد اختبارات آلية، اجعله قابلاً للنقل، تقرير HTML وPDF، Docker للاختبارات.'
---

# nj-automation-suite: scaffold a suite like `Improvement Delivery/Automation Tests`

Reference implementation = the reference suite. COPY its files (do not re-type them); this skill says which, what each must guarantee, and the gate that proves it. Project facts: your project profile. Layout and file list: `references/layout.md`. Reports/PDF detail: `references/outputs-pdf.md`. Docker detail: `references/docker.md`.

## Steps (each leaves a file)
1. **Skeleton** -> `package.json` (scripts: test list typecheck stage menu selftest discover generate report strip-credentials jira:sync jira:test jira:add jira:track ui sweep-chrome), `tsconfig.json`, `playwright.config.ts` (`retries: 0`, workers from `<PREFIX>_WORKERS`, headed real Chrome), `.gitignore`, `.gitattributes`, `.dockerignore`. Pin exact versions (`@playwright/test`, `tsx`, `typescript`, `@types/node`). Gate: `npm i && npx tsc --noEmit` = 0.
2. **Portability** -> `lib/paths.ts` first (below). Gate: `selftest/paths.selftest.ts` scans sources for drive letters, `/Users/`, user or machine names, `Program Files`.
3. **Core lib** -> `lib/` (env, browser, signin, lock, stage, journey, jira, jiraenv, jiranotes, evidence, el, arabic, backoffice, payment, ...). Copy from the reference; replace only the project's URLs/accounts in `lib/env.ts`.
4. **Services** -> `services/<directorate>/<card>/` per service: spec (DATA block), `discovery.json`, `desks.json`, `README-service.md`, `AGENT.md`, `jira-checks.ts`, `jira.config.json`. Folder = the PORTAL card's own title.
5. **Reporter** -> `reporter/index.ts` (terminal + `reports/index.html` + `history.json` + per-service Jira HTML + `AI-RUN-NOTES.md`). Gate: selftest renders a fixture history.
6. **PDF tools** -> `tools/run-report/{build.ts,gates.ts,crop.py}`, `tools/build-guide.ts`. Gate: `gates.ts` passes on a fixture run.
7. **Launchers** -> `شغّل اختباراً.cmd` (Windows, relative path, calls `tools/run-ui.ts`) + `run.sh` (Linux/macOS, `cd "$(dirname "$0")"`, `npm ci` if no node_modules). Gate: both open the Arabic page with no absolute path.
8. **Docker** -> `Dockerfile`, `docker-compose.yml` (image only), `docker-compose.build.yml`, `docker/{entrypoint.sh,chrome-nosandbox.sh,README-docker.md,share/run.{sh,ps1,cmd}}`. Gate: `docker compose run --rm tests --list` lists every test.
9. **Hygiene tools** -> `tools/sweep-chrome.ts` and `lib/lock.ts` (below), `tools/strip-credentials.ts`.
10. **Docs** -> `README.md`, `docs/pipeline.md`, `docs/<guide>.pdf` (the setup/run guide, Arabic). Gate: README states each env var in a table.

## Portability rules (permanent)
- Never write a drive letter, `/Users/...`, a user or machine name or `Program Files` in the suite. Everything resolves through `lib/paths.ts`: `SUITE_ROOT` (from its own location), `resolve()`, `fontsDir()`, `chromeExe()`, `popplerTool()`, `testDataFile()`, `tmpRoot()`, `fileUrl()`, `openUrl()`, `pythonBin()`, `killTree()`.
- Env override first, auto-discovery second, bundled default last: `<P>_CHROME` (then standard Chrome locations per OS, then `google-chrome`/`chromium` on PATH, then Playwright Chromium), `<P>_FONTS_DIR` (default `assets/fonts/<face>`), `<P>_POPPLER_BIN` (PATH, else a WinGet Poppler), `<P>_TEST_DATA`, `<P>_TMP`, `<P>_PYTHON` (`python` on Windows, `python3` elsewhere).
- Generators emit `__dirname`-relative code. `.gitattributes`: `*.sh eol=lf`, `*.cmd eol=crlf` (a CRLF `.sh` breaks in the container).
- Lock namespace is per checkout (hash of the lower-cased suite path) so two copies do not block each other.

## Hygiene
- **Sign-in lock:** cross-process folder lock, sign-ins one at a time and >= 5 s apart while reCAPTCHA is on (`<P>_CAPTCHA=off|on`); owner token + heartbeat; stale after 5 min. Worker briefs add an outer lock `mkdir reports/.signin-lock` (retry 10 s, remove only if older than 4 min, rmdir right after the sign-in lands). Hold it only for the sign-in itself.
- **Chrome closes itself** with its node process (normal end, error, Ctrl+C, killed worker, watchdog on hard kill). `npm run sweep-chrome` lists orphans (a suite profile with no live CDP client); `-- --kill` closes only those. Never touch the user's own Chrome. Run it at the end of every session.
- Specs hold literal staging logins by design: the folder never leaves the team; `npm run strip-credentials` writes a blanked copy for sharing. Jira credentials never enter the suite except the git-ignored `jira.local.json`.

## Reports and PDFs (summary)
- `reports/index.html`: directorate > service > request > stage, latest result kept per request, Arabic RTL, sticky TOC. Per-service Jira HTML `reports/jira/<service>.html` opens by itself after a run (`NO_OPEN` env stops it). `reports/AI-RUN-NOTES.md` is rewritten after every run (TL;DR verdict, failures with suggested class and the re-run command); `AGENT.md` per service via `tools/gen-agent-md.ts`.
- PDFs: HTML -> headless real Chrome print, **Thmanyah TrueType cuts only** (Serif Text body, Serif Display headings), base64 `@font-face`; gates: every item in the PDF text, `pdffonts` shows only Thmanyah TrueType (no Type 3), Arabic extracts with poppler `pdftotext -enc UTF-8`. **Fonts are never shipped in a shared image, archive or share** (licence: no handing the files to others): exclude `assets/fonts/**` in `.dockerignore` and the 7z; containers mount them: `-v <fonts>:/fonts -e <P>_FONTS_DIR=/fonts`.
- HTML preview: after building a page, screenshot it headless (`reports/<pass>/index.png`) so the Lead looks at the picture, not the source.

## Docker (summary)
Image-only compose (`image:` + `platform: linux/amd64`, `shm_size: 2gb`, `./reports:/suite/reports`, env names passed bare); real Google Chrome under Xvfb, `tini` as PID 1, `TZ`, Arabic fonts; no credentials in the image; wrappers `run.sh/run.ps1/run.cmd` load the `.tar` once (SHA-256 check) then run. Share = tar + sha256 + compose + README + wrapper, zipped as 7z without fonts. Details in `references/docker.md`.

## Standard suite parts (2026-10-12)
Five capabilities every suite carries (reference: the reference suite):
1. **Masked page text** beside every screenshot (`lib/evidence.ts` `snap()` writes `<name>.txt`).
2. **Build and run id** (`lib/build.ts`) on evidence, `run-meta.json` and `filed-requests.csv` (`build`, `run_id`).
3. **Findings scanner** (`lib/findings/`, `tools/findings/scan-cli.ts`, `selftest/findings.selftest.ts`): rules in `rules.ts`; add a rule by appending, never by dropping hits silently. Gate: selftest 9 of 12 caught, 0 false positives.
4. **Pre-filing review page** (`tools/review/`): nothing files without an approved key.
5. **Per-build recheck** (`tools/recheck/`): unchanged / fixed / broken / new / unreachable; env-down is never fixed.

Gate for a new suite: all five run offline on a fixture and the selftests pass. Machine paths stay out of suite code: `NJ_RANK_PREVIEW` and `NJ_RANK_SCRIPT` env vars locate the nj-rank combined page. Method source: the reference suite's `reports/factcheck-2026-10-12/method/{reverse-engineering.md,adopt-plan.md}`.

## Oracles and self-healing (2026-10-18)
A suite ships the heal log (observe-only, no apply mode): `lib/heal-log.ts`, `reporter/heal.ts` in playwright.config reporters, `tools/heal-report.ts`, `selftest/heal-check.ts`; `HEAL_MODE=observe|off`; noHeal for login, Send, fee, signature, negative and assertion steps. The oracle rules R1-R8, heal rules H1-H7, guards G1-G9, verdicts and the window 2026-10-18 -> 2026-11-15 are in `nj-qa-pipeline` section 5 (canonical). Never change an expected value to match what the system does.

## ADHD output
Every page, PDF, terminal line and note the suite writes: verdict + count chips first, red first, one idea per card, icon + word per state, collapsed detail, «الخطوة التالية» per item, sticky TOC (HTML), section tabs + page numbers (PDF), times HH:MM:SS. Standard: `nj-qa-pipeline/references/adhd-standard.md`.

## Run once
The suite's own selftest (`npm run selftest`, offline) is the gate; staging runs are single, no retry loops, "not verified" said plainly.

## Screenshots: viewport only (owner, 2026-10-18, global)
Evidence screenshots are NORMAL viewport screenshots, never `fullPage:true`. Scroll the target into view and assert its bounding box lies inside the viewport before capturing — use the suite helper `shotOf(page, target, path)` (`tests/PROJ/_shared/shot.ts` in project-tests, `lib/shot.ts` in Automation Tests). Canonical: `~/.claude/CLAUDE.md` § Standing facts.
