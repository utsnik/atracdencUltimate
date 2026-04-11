#!/usr/bin/env python3
"""
Adaptive LP2 wrapper for atracdenc (no codec changes, flag-policy only).

This version uses frame-aware statistics (1024-sample windows) to choose a
track profile:
- `default`     : transient-bursty material
- `ml`          : mixed/uncertain material
- `bfu32_ml`    : stable, non-bursty material
"""

from __future__ import annotations

import argparse
import struct
import subprocess
import wave
from pathlib import Path


def read_mono_i16(path: Path) -> list[int]:
    with wave.open(str(path), "rb") as w:
        data = w.readframes(w.getnframes())
        ch = w.getnchannels()
        if w.getsampwidth() != 2:
            raise RuntimeError("Only 16-bit PCM WAV is supported")
    vals = struct.unpack("<" + "h" * (len(data) // 2), data)
    return list(vals[::ch])


def measure_global_features(samples: list[int]) -> tuple[float, float, float]:
    a = [abs(v) / 32768.0 for v in samples]
    mean_abs = sum(a) / max(1, len(a))
    peak = max(a) if a else 0.0
    crest = peak / (mean_abs + 1e-9)

    zc = 0
    prev = samples[0] if samples else 0
    for v in samples[1:]:
        if (prev < 0 <= v) or (prev >= 0 > v):
            zc += 1
        prev = v
    zcr = zc / max(1, len(samples))

    hop = 1024
    es = []
    for i in range(0, max(0, len(samples) - hop), hop):
        seg = samples[i : i + hop]
        es.append(sum(x * x for x in seg) / hop)
    if not es:
        return crest, zcr, 0.0
    m = sum(es) / len(es)
    var = sum((e - m) * (e - m) for e in es) / len(es)
    ecv = (var**0.5) / (m + 1e-9)
    return crest, zcr, ecv


def measure_frame_features(samples: list[int], frame: int = 1024) -> tuple[float, float]:
    """
    Returns:
    - burst_ratio: fraction of frames with strong local attack-like behavior
    - mean_crest: average frame crest factor
    """
    if len(samples) < frame:
        return 0.0, 0.0

    burst = 0
    csum = 0.0
    n = 0
    prev_e = None
    for i in range(0, len(samples) - frame + 1, frame):
        seg = samples[i : i + frame]
        abs_seg = [abs(v) / 32768.0 for v in seg]
        mean_abs = sum(abs_seg) / frame
        peak = max(abs_seg)
        crest = peak / (mean_abs + 1e-9)
        e = sum(v * v for v in seg) / frame
        if prev_e is not None and prev_e > 1e-6:
            ratio = e / prev_e
            if crest > 8.0 and ratio > 2.0:
                burst += 1
        prev_e = e
        csum += crest
        n += 1
    return burst / max(1, n), csum / max(1, n)


def choose_profile(
    crest: float, zcr: float, ecv: float, burst_ratio: float, mean_frame_crest: float
) -> tuple[str, list[str]]:
    # Transient burst profile: bursty frame behavior dominates.
    if burst_ratio > 0.02 or (crest > 20.0 and ecv > 1.0):
        return "default", []
    # Uncertain middle ground: keep ML hints but avoid aggressive BFU forcing.
    if burst_ratio > 0.005 or mean_frame_crest > 4.5 or ecv > 0.10:
        return "ml", ["--ml-hints"]
    # High-fidelity profile for stable non-bursty material.
    return "bfu32_ml", ["--bfuidxconst", "32", "--ml-hints"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enc", required=True, type=Path, help="path to atracdenc.exe")
    ap.add_argument("-i", "--input", required=True, type=Path, help="input WAV")
    ap.add_argument("-o", "--output", required=True, type=Path, help="output .at3.wav/.at3")
    ap.add_argument("--print-only", action="store_true", help="print selected profile and exit")
    args = ap.parse_args()

    samples = read_mono_i16(args.input)
    crest, zcr, ecv = measure_global_features(samples)
    burst_ratio, mean_frame_crest = measure_frame_features(samples)
    profile_name, extra = choose_profile(crest, zcr, ecv, burst_ratio, mean_frame_crest)

    print(
        "profile={p} crest={c:.3f} zcr={z:.4f} ecv={e:.3f} burst_ratio={b:.4f} frame_crest={fc:.3f}".format(
            p=profile_name, c=crest, z=zcr, e=ecv, b=burst_ratio, fc=mean_frame_crest
        )
    )
    if args.print_only:
        return

    cmd = [str(args.enc), "-e", "atrac3", "-i", str(args.input), "-o", str(args.output), "--bitrate", "132"] + extra
    p = subprocess.run(cmd)
    if p.returncode != 0:
        raise SystemExit(p.returncode)


if __name__ == "__main__":
    main()
