# Lead checklist: merge, check every variant, close

## Before launch
- [ ] Pieces are one file each; the split is committed; every crew's worktree starts from that commit.
- [ ] The renderer runs for every variant and writes frames and a sheet (not blank).
- [ ] An unknown command-line argument does nothing; the real action needs an explicit flag.
- [ ] Contract file written; quality bar filled; the reference piece renders.
- [ ] `python scripts/brief_gate.py <briefs>` prints PASS.
- [ ] The installed copy of the product is on no crew's path.

## At each merge
- [ ] `git diff --stat <base>..crew/<piece>` touches only the piece's own file.
- [ ] Merge; build; no new warnings you cannot explain.
- [ ] Crew bookkeeping inside the repo (status files, receipts, queue folders) is not staged; move it out.

## After all merges: one check, every variant
- [ ] Render every variant of every piece; open every sheet once.
- [ ] Per sheet: nothing crosses or clips; colour tells the true story (no leftover warning colour after the fix);
      every main object has depth; every marker is readable at sheet size; the last frame is settled.
- [ ] Compare the variants of one piece side by side: clearly different in intensity.
- [ ] Fix each fault yourself, one fix per fault, then re-render only that variant. Do not reopen the whole review.
- [ ] Run the project's tests. Tests that share static or global state must not run in parallel with each other.
- [ ] Confirm the fixed beats are unchanged (diff the contract's times against the code, by script if you can).

## Close
- [ ] Worktrees removed, merged `crew/*` branches deleted, no crew process still running.
- [ ] Renders and logs live outside the repo; `git status` shows only intended files.
- [ ] Report: one line per piece; sheet paths; what was not seen live and the one action that checks it.
