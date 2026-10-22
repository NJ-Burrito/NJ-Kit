# Docker for a suite (Windows / Linux / macOS)

## Image
- Base `mcr.microsoft.com/playwright:v<same as @playwright/test>-noble`; install real Google Chrome (`npx playwright install --with-deps chrome`), `xvfb xauth`, Arabic fonts (noto, kacst-one, amiri), `tini` (PID 1: xvfb-run hangs as PID 1), `poppler-utils` (pdftotext). `TZ` set, `LANG=C.UTF-8`, `PYTHONUTF8=1`.
- Chrome as root needs `--no-sandbox`: wrapper `docker/chrome-nosandbox.sh`, picked up through `<P>_CHROME`.
- `COPY package.json package-lock.json` then `npm ci`, then `COPY . .` (cache layer).
- `.dockerignore`: node_modules, reports, test-results, `.git`, `*.local.json`, `**/profile`, `**/evidence`, `**/probes`, `**/jira-*-<run>` working folders, and **`assets/fonts/**` (licence)**.
- No credentials in the image; secrets reach it only as env at run time.

## Compose (image only, no build)
```
services:
  tests:
    image: <suite>:<tag>
    platform: linux/amd64        # Google ships no Linux-arm64 Chrome; Apple Silicon emulates
    shm_size: 2gb
    volumes: [ "./reports:/suite/reports" ]
    environment: [ <P>_ENV, <P>_WORKERS, <P>_FONTS_DIR, JIRA_BASE_URL, JIRA_USER, JIRA_PASS, ... ]   # bare names = passed only when set
```
Build overlay: `docker-compose.build.yml` (maintainers): `docker compose -f docker-compose.yml -f docker-compose.build.yml build`, then `docker save -o <suite>-<tag>.tar <suite>:<tag>` and a `.sha256`.

## Wrappers (`docker/share/`)
`run.sh` (bash/zsh), `run.ps1` (PowerShell), `run.cmd` (cmd): load the tar once if the image is missing (verify SHA-256 when `.sha256` sits beside it), create `./reports`, then `docker compose run --rm tests "$@"`. Entry rule: arguments starting with `-`, ending `.spec.ts` or starting `services/` go to `npx playwright test`; anything else runs as a command. **LF for `.sh`, CRLF for `.cmd`** (`.gitattributes`). If the exec bit is lost: `sh run.sh`. PowerShell blocked: `powershell -ExecutionPolicy Bypass -File .\run.ps1`.

## PDFs in the container
Fonts come from a mounted folder: `-v <fonts>:/fonts -e <P>_FONTS_DIR=/fonts`; wrapper form `<P>_FONTS_HOST=<fonts> ./run.sh npx tsx tools/run-report/build.ts ...`.

## Share + 7z
Share folder = tar, sha256, compose, README-docker.md, the wrapper(s). 7z it WITHOUT fonts, `jira.local.json`, Jira attachments, working folders or specs with real logins unless the recipient is the team. Rebuild image + share + 7z after any change to lib/tools/services.

## Known limits (state them in the README)
reCAPTCHA may still refuse another IP (the portal, not the image); the payment host is office-network only (VPN or a URL override); staging only; every filing run submits a real request.

## Gate
`docker compose run --rm tests --list` lists every test; one non-filing test runs headed-in-Xvfb and writes `./reports/index.html`.
