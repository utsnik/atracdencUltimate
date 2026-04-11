#!/usr/bin/env python3
"""
Convenience CLI for LP2 workflows.

Examples:
  python tools/atracdenc_lp2.py --enc build2/src/atracdenc.exe -i YOUtopia.wav -o out.at3.wav --mode lp2-adaptive
  python tools/atracdenc_lp2.py --enc build2/src/atracdenc.exe -i YOUtopia.wav -o out.at3.wav --mode default
  python tools/atracdenc_lp2.py --enc build2/src/atracdenc.exe -i YOUtopia.wav -o out.at3.wav --mode bfu32-ml
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> int:
    p = subprocess.run(cmd)
    return p.returncode


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enc", required=True, type=Path, help="path to atracdenc.exe")
    ap.add_argument("-i", "--input", required=True, type=Path, help="input wav")
    ap.add_argument("-o", "--output", required=True, type=Path, help="output at3/at3.wav")
    ap.add_argument(
        "--mode",
        default="lp2-adaptive",
        choices=["lp2-adaptive", "default", "ml", "bfu32-ml"],
        help="encoding mode",
    )
    args = ap.parse_args()

    if args.mode == "lp2-adaptive":
        script = Path(__file__).with_name("lp2_adaptive_encode.py")
        rc = run(
            [
                sys.executable,
                str(script),
                "--enc",
                str(args.enc),
                "-i",
                str(args.input),
                "-o",
                str(args.output),
            ]
        )
        raise SystemExit(rc)

    mode_flags = {
        "default": [],
        "ml": ["--ml-hints"],
        "bfu32-ml": ["--bfuidxconst", "32", "--ml-hints"],
    }[args.mode]

    cmd = [str(args.enc), "-e", "atrac3", "-i", str(args.input), "-o", str(args.output), "--bitrate", "132"] + mode_flags
    rc = run(cmd)
    raise SystemExit(rc)


if __name__ == "__main__":
    main()

