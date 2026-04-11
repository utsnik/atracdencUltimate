#!/usr/bin/env python3
"""
Per-frame SNR comparison helper.

Compares two decoded WAV outputs against the same reference WAV, with automatic lag
alignment, then reports which frames each profile wins.
"""

from __future__ import annotations

import argparse
import math
import struct
import wave
from pathlib import Path


def read_wav_mono16(path: Path) -> list[float]:
    with wave.open(str(path), "rb") as w:
        data = w.readframes(w.getnframes())
        ch = w.getnchannels()
        if w.getsampwidth() != 2:
            raise RuntimeError(f"{path}: only 16-bit PCM supported")
    vals = struct.unpack("<" + "h" * (len(data) // 2), data)
    return [float(v) for v in vals[::ch]]


def snr_db(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n < 64:
        return -120.0
    a = a[:n]
    b = b[:n]
    sig = sum(x * x for x in a) / n
    noi = sum((a[i] - b[i]) ** 2 for i in range(n)) / n
    return 10.0 * math.log10((sig + 1e-20) / (noi + 1e-20))


def best_lag(ref: list[float], dec: list[float], max_lag: int = 300) -> int:
    best = (-1e9, 0)
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            r = ref[lag:]
            d = dec[: len(r)]
        else:
            d = dec[-lag:]
            r = ref[: len(d)]
        s = snr_db(r, d)
        if s > best[0]:
            best = (s, lag)
    return best[1]


def align(ref: list[float], dec: list[float], lag: int) -> tuple[list[float], list[float]]:
    if lag >= 0:
        r = ref[lag:]
        d = dec[: len(r)]
    else:
        d = dec[-lag:]
        r = ref[: len(d)]
    n = min(len(r), len(d))
    return r[:n], d[:n]


def per_frame_snr(ref: list[float], dec: list[float], frame: int = 1024) -> list[float]:
    out = []
    n = min(len(ref), len(dec))
    for i in range(0, n - frame + 1, frame):
        out.append(snr_db(ref[i : i + frame], dec[i : i + frame]))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, type=Path)
    ap.add_argument("--a", required=True, type=Path, help="decoded wav A")
    ap.add_argument("--b", required=True, type=Path, help="decoded wav B")
    ap.add_argument("--label-a", default="A")
    ap.add_argument("--label-b", default="B")
    args = ap.parse_args()

    ref = read_wav_mono16(args.ref)
    a = read_wav_mono16(args.a)
    b = read_wav_mono16(args.b)

    lag_a = best_lag(ref, a)
    lag_b = best_lag(ref, b)

    r_a, a_al = align(ref, a, lag_a)
    r_b, b_al = align(ref, b, lag_b)
    n = min(len(r_a), len(r_b), len(a_al), len(b_al))
    r = r_a[:n]
    a_al = a_al[:n]
    b_al = b_al[:n]

    snr_a = per_frame_snr(r, a_al)
    snr_b = per_frame_snr(r, b_al)
    m = min(len(snr_a), len(snr_b))
    snr_a = snr_a[:m]
    snr_b = snr_b[:m]

    wins_a = sum(1 for i in range(m) if snr_a[i] > snr_b[i] + 0.1)
    wins_b = sum(1 for i in range(m) if snr_b[i] > snr_a[i] + 0.1)
    ties = m - wins_a - wins_b
    avg_a = sum(snr_a) / max(1, m)
    avg_b = sum(snr_b) / max(1, m)

    print(f"lag_{args.label_a}={lag_a}")
    print(f"lag_{args.label_b}={lag_b}")
    print(f"frames={m}")
    print(f"avg_{args.label_a}={avg_a:.3f}")
    print(f"avg_{args.label_b}={avg_b:.3f}")
    print(f"wins_{args.label_a}={wins_a} wins_{args.label_b}={wins_b} ties={ties}")

    deltas = [(snr_b[i] - snr_a[i], i, snr_a[i], snr_b[i]) for i in range(m)]
    deltas.sort(reverse=True)
    print("top_frames_where_B_beats_A:")
    for d, i, sa, sb in deltas[:12]:
        print(f"frame={i} delta={d:.3f} {args.label_a}={sa:.3f} {args.label_b}={sb:.3f}")

    deltas.sort()
    print("top_frames_where_A_beats_B:")
    for d, i, sa, sb in deltas[:12]:
        print(f"frame={i} delta={d:.3f} {args.label_a}={sa:.3f} {args.label_b}={sb:.3f}")


if __name__ == "__main__":
    main()

