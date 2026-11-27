# Failure modes seen in the origin run, and the fix

| Symptom | Cause | Fix |
|---|---|---|
| `git worktree add` or the harness's automatic worktree refuses, or one path looks like two repos | Drive-letter case differs between spellings of the same path (`c:` and `C:`) | Make worktrees yourself with one exact spelling and give that spelling to every crew |
| A build or render run from bash through `cmd /c` hangs or prints nothing; a stray background build leaves no output | A Windows `cmd` launched from a POSIX shell wrapper does not return or hides its output | Run builds and renders from PowerShell; redirect output to a log file; wait for the process by script |
| First render produced no files | It ran while the build was still finishing | Wait for the build to exit and check its exit code before rendering |
| Crews' status files and receipts show up in the repo's `git status` | The agent tooling wrote its bookkeeping into the working directory | Add the folder to `.git/info/exclude` before launch; move it out when merging |
| The product ran its real action and overwrote the installed copy | A crew passed a bare argument without the render switch; the entry point treated it as "install and run" | Fix the entry point: unknown arguments do nothing. Render switch first in every brief |
| Intermittent test failures after merging several crews | Tests share static state (singletons, static settings) and run in parallel | Reset the static state in each test, or run those tests serially. The crews are not the cause |
| One variant crashes on render | A malformed vector path string (a bad segment) | The crew fixes its own file; the first render of any new path is a test |
| Two crews both need a change in the shared host file | One file per crew is the rule | Each reports the change; the lead applies it once after merging |
| A crew says "done" but the sheet shows clipping | It looked at one frame, not the sheet | The brief says to judge every frame; the lead checks every sheet once anyway |
| Sound cannot be judged from frames | Frames carry no audio | Say "not verified" in the report; check by ear or with an audio tool |
