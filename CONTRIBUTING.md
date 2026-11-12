# Contributing

1. One skill per folder, with a `SKILL.md` (frontmatter `name` + `description`).
2. Every skill ends in a gate: a script or check that prints PASS/FAIL. No "should work".
3. No secrets, no personal data, no absolute paths: read them from environment variables or `~/.claude/secrets/`, and resolve repo paths from the script's own location.
4. Deletions go to the recycle bin (`nj-safe-delete`), never `rm -rf`.
5. Arabic and English are both first-class: fix both sides of a bilingual pair together.
6. Before you open a pull request run `python scripts/publish-check.py` (no secrets, no project data, no machine paths, no font files) and `python scripts/skill-table.py` (README skill table).
7. Open a pull request; CI must be green.
