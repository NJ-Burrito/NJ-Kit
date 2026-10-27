# Standing instructions (NJ-Kit neutral template)

This file was written by the NJ-Kit installer because you had no `~/.claude/CLAUDE.md`.
It is a neutral starting point. Edit it freely; the installer never overwrites an existing file.

## Work by nj-method

If the `nj-method` skill is installed, read it and follow it for every request:

1. Analyse: name the deliverable, its language, its audience, and what "done" means.
2. Look up an installed skill before improvising.
3. Plan in short ordered steps; each expensive step leaves a file the next step reads.
4. Execute and verify as you go. A build that "should work" has not been tested.
5. Review against the request, item by item. Say what was not done, and why.

Proportionality is part of the method: a one-line question gets a one-line answer.

## Defaults

- Match the deliverable's language, not the conversation's. Arabic and English are both first-class; for a bilingual pair, fix both sides together.
- Deletions go to the recycle bin (the `safe-delete` skill), never `rm -rf`.
- On Windows set `PYTHONUTF8=1` so Arabic text does not crash scripts.
- Python packages through `uv`, not `pip`.
- Never put credentials in a repository. Do not push, publish, post or send anything outward without being asked.
- Report once at the end: what was done, what was not, and where the files are.
