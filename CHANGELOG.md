# Changelog

## 2.0.0 — 2026-10-22

- Trimmed: no client material, no duplicate plugin copies, no archives. `nj-kit/assets-manifest.json` plus `nj-kit/scripts/fetch_assets.py` fetch the heavy optional parts (graphify package, researcher `sources.db`, tashkeel evidence runs) on demand, sha256-checked. `install.py` restores the plugin from the repo's own `nj-plugin/`.

- First public release: the `nj-kit` plugin (23 skills) and the `nj-kit` installer with its bundled skills.
- All credentials, private hosts and machine paths replaced by environment variables and placeholders.
