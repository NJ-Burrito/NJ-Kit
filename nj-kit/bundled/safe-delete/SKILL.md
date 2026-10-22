---
name: safe-delete
description: 'Delete files and folders to the operating system''s recycle bin instead of destroying them, so anything removed can be restored. Use for every deletion: rm, Remove-Item, del, fs.rm, shutil.rmtree, cleanups, delete the stale artifacts, remove that folder.'
---

# Nothing is deleted permanently

**Every deletion goes to the recycle bin.** Not `rm`, not `rm -rf`, not
`Remove-Item`, not `shutil.rmtree`, not `fs.rmSync` — those destroy, and a
destroyed file that turns out to have been wanted is not a mistake that can be
apologised away.

```bash
python ~/.claude/skills/safe-delete/scripts/trash.py <path> [path...]
```

It moves each path to the OS recycle bin and prints what it moved. On Windows it
uses the Shell API, so the items appear in the Recycle Bin with **Restore**
available exactly as if a person had deleted them from Explorer.

## When this applies

Always. Including — especially — the cases that feel safe:

- build output, caches, intermediates, "regenerable" files
- stale copies after a move or a rename
- folders you created yourself earlier in the same session
- anything described as "temporary", "orphan" or "unused"

"It can be regenerated" is not a reason to destroy it. Regenerating costs
minutes; the judgement that it *was* regenerable can be wrong, and then the cost
is unbounded. 4.1 GB of video intermediates were destroyed on that reasoning
before this rule existed.

## The exceptions, and they are narrow

- **Overwriting a file you are rewriting** — writing to a path is not deleting.
- **Scratch files in the session's own temp directory**, created and discarded
  within one task and never seen by the user.
- **The user explicitly says to destroy it permanently**, in those terms.

Anything else: recycle bin.

## If the recycle bin is not available

Network drives, some containers and most CI machines have none. Then **move the
path aside instead of deleting it** — a sibling `.trash/` directory with a
timestamp — and say so, so the user knows where it went and that it still
exists:

```bash
python ~/.claude/skills/safe-delete/scripts/trash.py --fallback-dir .trash <path>
```

## A name with `%` in it, or "nothing moved"

The shell's recycle-bin API decodes percent-escapes, so a folder literally named
`QA%20Engineer` is read as `QA Engineer` — a *different* folder — and the call
refuses ("nothing moved" / "the specified path is invalid"). Never retry with
another API that might succeed on the decoded name. Rename the item to a plain
name first (`Rename-Item -LiteralPath`), check the renamed path holds what you
expect, then recycle that.

If the rename itself says access denied / in use while no file is locked, a
process holds a directory handle (a watcher, not an open file). Find it before
guessing: enumerate this user's handles and match the path (2026-10-16 it was
PDFgear's `FileWatcher.exe`, which watches the folder of every PDF opened in
PDFgear). Stop that process, then rename and recycle.

## Say what you removed

A deletion is reported like any other change: what was removed, how much of it,
and where it can be recovered from. "Cleaned up" is not a report.
