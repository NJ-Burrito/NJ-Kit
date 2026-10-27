# Changelog

## 2.0.1 — 2026-10-27

Security fixes from the 2026-10-27 audit of this repo and the site.

- `install.py` pins every third-party skill to a commit (`nj-kit/pinned-sources.json`, 13 repositories, 22 skills), fetches that exact commit and verifies it, pins the `skills` CLI (1.7.4) and `playwright` (1.64.1), shows the list and asks once before downloading (`--yes` accepts it). An unpinned source is refused.
- `context7` MCP is pinned to 4.4.4 (was `@latest`).
- `install.py` no longer writes the author's own CLAUDE.md. It writes a neutral template (`nj-kit/templates/CLAUDE.neutral.md`) and only when you have no `~/.claude/CLAUDE.md`. The old `bundled/CLAUDE.md` is removed.
- `export.py` no longer bundles auto-memory or the personal CLAUDE.md by default (`--with-memory`, `--with-personal` are private-migration opt-ins, gitignored), redacts secrets, query strings and the home path in hook commands and MCP args/urls, forces the pinned npm versions, and refuses to write a zip that holds a credential shape. Tests: `nj-kit/tests`, run in CI.
- graphify asset bumped to graphifyy 0.9.70 (fixes GHSA-pcc4-rvhr-2pr8); the skill pins that version and warns to index only trusted repositories.
- `nj_guard.py` inspects the PowerShell tool as well as Bash and blocks `~/.config/<project>/*.env` style paths for helpers. It stays a best-effort, fail-open guard.
- Site (EN and AR): meta Content-Security-Policy with computed script hashes, referrer policy, and a line saying what the installer changes (hooks, status line, env, MCP, neutral CLAUDE.md). The build computes the hashes and fails if a script is not covered.
- CI and Pages actions pinned by commit SHA; `ci.yml` has `permissions: contents: read`.

## 2.0.0 — 2026-10-22

- Trimmed: no client material, no duplicate plugin copies, no archives. `nj-kit/assets-manifest.json` plus `nj-kit/scripts/fetch_assets.py` fetch the heavy parts (graphify package, researcher `sources.db`, tashkeel evidence runs) on demand, sha256-checked. `install.py` restores the plugin from the repo's own `nj-plugin/`.

- First public release: the `nj-kit` plugin (23 skills) and the `nj-kit` installer with its bundled skills.
- All credentials, private hosts and machine paths replaced by environment variables and placeholders.
