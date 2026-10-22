# Security

**Report a vulnerability** privately through GitHub: *Security → Report a vulnerability* on this repo. Please do not open a public issue.

What this repo promises:

- No credentials are stored here. Skills read keys and URLs from environment variables or from `~/.claude/secrets/`, which is never committed.
- CI fails on anything that looks like a key, a private key or a machine-specific path.
- `nj-kit/bundled/claude-v4/hooks/nj_guard.py` stops sub-agents from reading secret paths.
- Before installing any third-party skill, run `nj-security-review`.
