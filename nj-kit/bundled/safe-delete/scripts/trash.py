#!/usr/bin/env python
"""Move paths to the operating system's recycle bin instead of destroying them.

    python trash.py build/ stale.log
    python trash.py --fallback-dir .trash build/     (where there is no bin)

Prints what moved and where. Exit status is 1 if anything could not be moved,
so a script that calls this stops rather than continuing as though it had.

The Windows path uses the Shell's own file operation, which is what puts an item
in the Recycle Bin with **Restore** available — moving a folder into
`$Recycle.Bin` by hand does not, and produces something Explorer cannot restore.
"""
import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Windows consoles default to cp1252, which cannot encode the tick this script
# prints on success. Without this the deletion happens and then the *report*
# raises, which reads exactly like a failed delete. Report in the same encoding
# the paths themselves may be in.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def to_recycle_bin_windows(paths: list) -> tuple:
    """Ask the Windows shell to delete these, with the undo record it keeps.

    `SHFileOperation` via `Microsoft.VisualBasic.FileIO.FileSystem` is the
    documented way to get "send to recycle bin" semantics; the flags say do it
    without a confirmation dialog and without the progress UI, which a headless
    caller has nowhere to show.
    """
    # The paths are embedded in the script as a literal array rather than
    # passed as arguments: `powershell -Command "..." -- a b` does not populate
    # $args the way it looks like it should, and the call silently deletes
    # nothing while reporting an exit code.
    literal = ", ".join("'" + str(Path(p).resolve()).replace("'", "''") + "'" for p in paths)
    script = (
        "Add-Type -AssemblyName Microsoft.VisualBasic; "
        f"$targets = @({literal}); "
        "foreach ($p in $targets) { "
        "  try { "
        "    if (Test-Path -LiteralPath $p -PathType Container) { "
        "      [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory($p, 'OnlyErrorDialogs', 'SendToRecycleBin') "
        "    } else { "
        "      [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile($p, 'OnlyErrorDialogs', 'SendToRecycleBin') "
        "    } "
        "    Write-Output \"OK $p\" "
        "  } catch { Write-Output \"ERR $p :: $($_.Exception.Message)\" } "
        "}"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
    )
    moved, failed = [], []
    for line in (result.stdout or "").splitlines():
        if line.startswith("OK "):
            moved.append(line[3:])
        elif line.startswith("ERR "):
            failed.append(line[4:])
    if result.returncode != 0 and not moved and not failed:
        failed = [f"{p} :: powershell exited {result.returncode}" for p in paths]
    return moved, failed


def to_fallback_dir(paths: list, where: Path) -> tuple:
    """No recycle bin: move the path aside, timestamped, and say where."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = where / stamp
    target.mkdir(parents=True, exist_ok=True)
    moved, failed = [], []
    for p in paths:
        try:
            shutil.move(p, str(target / Path(p).name))
            moved.append(f"{p} -> {target / Path(p).name}")
        except Exception as err:  # noqa: BLE001 - reported, not swallowed
            failed.append(f"{p} :: {err}")
    return moved, failed


def size_of(path: str) -> str:
    total = 0
    p = Path(path)
    if p.is_file():
        total = p.stat().st_size
    else:
        for root, _dirs, files in os.walk(path):
            for f in files:
                try:
                    total += (Path(root) / f).stat().st_size
                except OSError:
                    pass
    for unit in ("B", "KB", "MB", "GB"):
        if total < 1024 or unit == "GB":
            return f"{total:.0f}{unit}" if unit == "B" else f"{total:.1f}{unit}"
        total /= 1024
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--fallback-dir", help="where to move things when there is no recycle bin")
    args = ap.parse_args()

    # A path that arrived with a carriage return on it is still that path.
    #
    # Feeding this a list built on Windows — `python … $(cat list.txt)`, where
    # the list was written by a script that opened the file in text mode — hands
    # every entry but the last a trailing `\r`. `Path("a.json\r").exists()` is
    # False, so ninety-four files that were plainly there were reported "already
    # gone" and left on disk, while the one line without a newline was deleted.
    # Silent, and exactly backwards from the failure this tool exists to avoid.
    paths = [p.strip().strip("\r\n") for p in args.paths]
    paths = [p for p in paths if p]

    present = [p for p in paths if Path(p).exists()]
    absent = [p for p in paths if not Path(p).exists()]
    for p in absent:
        print(f"  · {p} — already gone")
    if not present:
        return 0

    sizes = {p: size_of(p) for p in present}

    if args.fallback_dir:
        moved, failed = to_fallback_dir(present, Path(args.fallback_dir))
        where = f"moved aside into {args.fallback_dir}"
    elif sys.platform == "win32":
        moved, failed = to_recycle_bin_windows(present)
        where = "in the Recycle Bin — restorable from Explorer"
    else:
        try:
            import send2trash  # type: ignore
        except ImportError:
            return int(bool(print("no recycle bin available: pip install send2trash, or pass --fallback-dir")))
        moved, failed = [], []
        for p in present:
            try:
                send2trash.send2trash(p)
                moved.append(p)
            except Exception as err:  # noqa: BLE001
                failed.append(f"{p} :: {err}")
        where = "in the trash"

    for p in moved:
        key = p.split(" -> ")[0]
        print(f"  ✓ {p}  ({sizes.get(key, '')})")
    for f in failed:
        print(f"  ✗ {f}")
    print(f"\n{len(moved)} item(s) {where}." if moved else "\nnothing moved.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
