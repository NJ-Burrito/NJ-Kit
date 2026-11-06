# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Memory and VRAM preflight before loading a local TTS model (nj-narration).

    python voice_preflight.py --need-vram-gb 3.6 --need-ram-gb 6        # exit 0 = fits, 1 = too little, 2 = NOT_MEASURED

The numbers you pass are the ENGINE'S need on YOUR machine, measured once (peak of a first run) and written in the
project's engine record; this script never guesses them. Free VRAM comes from `nvidia-smi` (all GPUs; the largest
free value counts), free RAM from the OS. A value it cannot read is reported NOT_MEASURED and the exit code is 2:
never load on a guess. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys


def parse_nvidia_smi(text: str) -> list[float]:
    """`nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits` -> free MiB per GPU."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            try:
                out.append(float(line))
            except ValueError:
                return []
    return out


def free_vram_gb() -> float | None:
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    vals = parse_nvidia_smi(r.stdout) if r.returncode == 0 else []
    return round(max(vals) / 1024, 2) if vals else None


def free_ram_gb() -> float | None:
    try:
        if sys.platform == "win32":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [(n, ctypes.c_ulonglong) for n in
                            ("tot", "avail", "pagetot", "pageavail", "vtot", "vavail", "ext")]
            m = MS()
            m.l = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            # commit headroom (page file included) matters on Windows: a model can fail on commit, not on RAM
            return round(min(m.avail, m.pageavail) / 2 ** 30, 2)
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return round(int(line.split()[1]) / 2 ** 20, 2)
    except Exception:
        return None
    return None


def check(free_vram, free_ram, need_vram, need_ram) -> tuple[int, list[str]]:
    msgs, code = [], 0
    for name, free, need in (("VRAM", free_vram, need_vram), ("RAM/commit", free_ram, need_ram)):
        if need is None:
            continue
        if free is None:
            msgs.append(f"{name}: NOT_MEASURED (will not load on a guess)")
            code = max(code, 2)
        elif free < need:
            msgs.append(f"{name}: {free} GB free, engine needs {need} GB: close other GPU/RAM users first, do not load")
            code = max(code, 1) if code != 2 else 2
    return code, msgs


def main(argv):
    ap = argparse.ArgumentParser(description="refuse to load a local model when memory is short")
    ap.add_argument("--need-vram-gb", type=float)
    ap.add_argument("--need-ram-gb", type=float)
    a = ap.parse_args(argv)
    fv = free_vram_gb() if a.need_vram_gb is not None else None
    fr = free_ram_gb() if a.need_ram_gb is not None else None
    code, msgs = check(fv, fr, a.need_vram_gb, a.need_ram_gb)
    print(json.dumps({"free_vram_gb": fv, "free_ram_gb": fr, "need_vram_gb": a.need_vram_gb, "need_ram_gb": a.need_ram_gb,
                      "pass": code == 0, "problems": msgs}))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
