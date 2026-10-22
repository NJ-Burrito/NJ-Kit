# Contributing

1. One skill per folder, with a `SKILL.md` (frontmatter `name` + `description`).
2. Every skill ends in a gate: a script or check that prints PASS/FAIL. No "should work".
3. No secrets, no personal data, no absolute paths: read them from environment variables or `~/.claude/secrets/`, and resolve repo paths from the script's own location.
4. Deletions go to the recycle bin (`safe-delete`), never `rm -rf`.
5. Arabic and English are both first-class: fix both sides of a bilingual pair together.
6. Open a pull request; CI must be green.
