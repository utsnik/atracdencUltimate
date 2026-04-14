#!/usr/bin/env python3
"""
Quick 4-sample LP2 stability gate.

This is a convenience wrapper around lp2_score_workflow.py using a shorter
manifest so we can iterate on narrow experimental modes more quickly.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    score = Path(__file__).with_name("lp2_score_workflow.py")
    manifest = Path(__file__).with_name("lp2_fast_stability_manifest.json")

    ap = argparse.ArgumentParser()
    ap.add_argument("--enc", required=True, type=Path)
    ap.add_argument("--legacy-enc", type=Path, default=repo_root / "build2" / "src" / "atracdenc.exe")
    ap.add_argument("--at3tool", type=Path, default=repo_root / "reverse" / "windows" / "at3tool.exe")
    ap.add_argument("--mode", default="quality-v10-gain-exp")
    ap.add_argument("--baseline-mode", default="quality-v10-native")
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    cmd = [
        sys.executable,
        str(score),
        "--enc",
        str(args.enc),
        "--legacy-enc",
        str(args.legacy_enc),
        "--at3tool",
        str(args.at3tool),
        "--mode",
        args.mode,
        "--baseline-mode",
        args.baseline_mode,
        "--manifest",
        str(manifest),
        "--stability-gate",
    ]
    if args.out_md is not None:
        cmd.extend(["--out-md", str(args.out_md)])

    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
