#!/usr/bin/env python3
"""
Quick LP2 quality diagnostics focused on sibilance/transients.

Computes:
- aligned full-band SNR
- high-band proxy SNR (first-difference)
- top "sibilance-like" frames where candidate underperforms baseline
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


def high_proxy(x: list[float]) -> list[float]:
    out = [0.0] * len(x)
    prev = 0.0
    for i, v in enumerate(x):
        out[i] = v - prev
        prev = v
    return out


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


def frame_metric(ref: list[float], dec: list[float], frame: int = 1024) -> list[tuple[int, float, float]]:
    hp_ref = high_proxy(ref)
    hp_dec = high_proxy(dec)
    out: list[tuple[int, float, float]] = []
    n = min(len(ref), len(dec))
    for i in range(0, n - frame + 1, frame):
        rs = ref[i : i + frame]
        ds = dec[i : i + frame]
        hs = hp_ref[i : i + frame]
        hd = hp_dec[i : i + frame]
        hi_energy = sum(v * v for v in hs) / frame
        out.append((i // frame, snr_db(rs, ds), 10.0 * math.log10(hi_energy + 1e-20)))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, type=Path)
    ap.add_argument("--base", required=True, type=Path, help="baseline decode (e.g. ml)")
    ap.add_argument("--cand", required=True, type=Path, help="candidate decode")
    ap.add_argument("--label-base", default="base")
    ap.add_argument("--label-cand", default="cand")
    ap.add_argument("--lag", type=int, default=None, help="fixed lag for both decodes (skip lag search)")
    ap.add_argument("--max-lag", type=int, default=300, help="max lag for search when --lag is not set")
    ap.add_argument("--seconds", type=float, default=0.0, help="analyze only first N seconds (0=full)")
    args = ap.parse_args()

    ref = read_wav_mono16(args.ref)
    base = read_wav_mono16(args.base)
    cand = read_wav_mono16(args.cand)

    if args.seconds > 0.0:
        n = int(44100 * args.seconds)
        ref = ref[:n]
        base = base[:n]
        cand = cand[:n]

    if args.lag is not None:
        lag_b = args.lag
        lag_c = args.lag
    else:
        lag_b = best_lag(ref, base, max_lag=args.max_lag)
        lag_c = best_lag(ref, cand, max_lag=args.max_lag)
    rb, bb = align(ref, base, lag_b)
    rc, cc = align(ref, cand, lag_c)
    n = min(len(rb), len(rc), len(bb), len(cc))
    r = rb[:n]
    b = bb[:n]
    c = cc[:n]

    full_b = snr_db(r, b)
    full_c = snr_db(r, c)
    hf_b = snr_db(high_proxy(r), high_proxy(b))
    hf_c = snr_db(high_proxy(r), high_proxy(c))

    fb = frame_metric(r, b)
    fc = frame_metric(r, c)
    m = min(len(fb), len(fc))
    deltas = []
    for i in range(m):
        _, snr_b, hi_db = fb[i]
        _, snr_c, _ = fc[i]
        deltas.append((snr_c - snr_b, i, hi_db, snr_b, snr_c))

    # Focus on high-energy high-band frames (sibilance-like)
    deltas.sort(key=lambda x: (x[0], -x[2]))
    print(f"lag_{args.label_base}={lag_b}")
    print(f"lag_{args.label_cand}={lag_c}")
    print(f"full_snr_{args.label_base}={full_b:.3f}")
    print(f"full_snr_{args.label_cand}={full_c:.3f}")
    print(f"hf_snr_{args.label_base}={hf_b:.3f}")
    print(f"hf_snr_{args.label_cand}={hf_c:.3f}")
    print("top_hf_frames_where_candidate_underperforms:")
    shown = 0
    for d, idx, hi_db, sb, sc in deltas:
        if hi_db < 18.0:
            continue
        print(
            f"frame={idx} delta={d:.3f} hf_energy_db={hi_db:.2f} "
            f"{args.label_base}={sb:.3f} {args.label_cand}={sc:.3f}"
        )
        shown += 1
        if shown >= 12:
            break


if __name__ == "__main__":
    main()
