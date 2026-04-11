#!/usr/bin/env python3
"""
Summarize atracdenc --decision-log output into compact frame stats.

Expected format: YAML-like blocks emitted by TAtrac3BitStreamWriter.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


RE_FRAME = re.compile(r"^frame:\s+(\d+)")
RE_CH = re.compile(r"^\s+- channel:\s+(\d+)")
RE_TGT = re.compile(r"^\s+target_bits:\s+(-?\d+)")
RE_BFU = re.compile(r"^\s+num_bfu:\s+(\d+)")
RE_TONAL = re.compile(r"^\s+tonal_blocks:\s+(\d+)")
RE_ML = re.compile(
    r"^\s+ml_hints:\s+\{bfu_bias:\s+([-\d.]+), tonal_bias:\s+([-\d.]+), gain_bias:\s+([-\d.]+), hf_bias:\s+([-\d.]+), confidence:\s+([-\d.]+)\}"
)


def parse(path: Path) -> list[dict]:
    rows: list[dict] = []
    frame = None
    ch = None
    cur: dict = {}

    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = RE_FRAME.match(line)
        if m:
            frame = int(m.group(1))
            continue
        m = RE_CH.match(line)
        if m:
            if cur:
                rows.append(cur)
            ch = int(m.group(1))
            cur = {"frame": frame, "channel": ch}
            continue
        m = RE_TGT.match(line)
        if m and cur:
            cur["target_bits"] = int(m.group(1))
            continue
        m = RE_BFU.match(line)
        if m and cur:
            cur["num_bfu"] = int(m.group(1))
            continue
        m = RE_TONAL.match(line)
        if m and cur:
            cur["tonal_blocks"] = int(m.group(1))
            continue
        m = RE_ML.match(line)
        if m and cur:
            cur["ml_bfu_bias"] = float(m.group(1))
            cur["ml_tonal_bias"] = float(m.group(2))
            cur["ml_gain_bias"] = float(m.group(3))
            cur["ml_hf_bias"] = float(m.group(4))
            cur["ml_confidence"] = float(m.group(5))
            continue

    if cur:
        rows.append(cur)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path, help="decision log path")
    args = ap.parse_args()

    rows = parse(args.log)
    if not rows:
        print("No rows parsed.")
        return

    n = len(rows)
    avg_target = sum(r.get("target_bits", 0) for r in rows) / n
    avg_bfu = sum(r.get("num_bfu", 0) for r in rows) / n
    avg_tonal = sum(r.get("tonal_blocks", 0) for r in rows) / n
    avg_conf = sum(r.get("ml_confidence", 0.0) for r in rows) / n
    avg_hf = sum(r.get("ml_hf_bias", 0.0) for r in rows) / n
    avg_gain = sum(r.get("ml_gain_bias", 0.0) for r in rows) / n

    print(f"rows={n}")
    print(f"avg_target_bits={avg_target:.2f}")
    print(f"avg_num_bfu={avg_bfu:.2f}")
    print(f"avg_tonal_blocks={avg_tonal:.2f}")
    print(f"avg_ml_confidence={avg_conf:.3f}")
    print(f"avg_ml_hf_bias={avg_hf:.3f}")
    print(f"avg_ml_gain_bias={avg_gain:.3f}")

    top = sorted(rows, key=lambda r: r.get("target_bits", -10**9))[:10]
    print("worst_target_frames=" + ",".join(f"{r.get('frame')}:{r.get('channel')}" for r in top))


if __name__ == "__main__":
    main()

