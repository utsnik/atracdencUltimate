#!/usr/bin/env python3
"""
LP2 degradation audit for already-decoded WAV outputs.

Computes aligned objective metrics vs source:
- full-band SNR
- HF proxy SNR (first difference)
- delta vs chosen baseline decode
- distance to Sony decode in the (full, HF) plane
"""

from __future__ import annotations

import argparse
import math
import struct
import wave
from pathlib import Path


def read_wav_mono16(path: Path, max_frames: int = 0) -> tuple[int, list[float]]:
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        sw = w.getsampwidth()
        frames = w.getnframes() if max_frames <= 0 else min(w.getnframes(), max_frames)
        data = w.readframes(frames)
    if sw != 2:
        raise RuntimeError(f"{path}: only 16-bit PCM WAV supported")
    vals = struct.unpack("<" + "h" * (len(data) // 2), data)
    return sr, [float(v) for v in vals[::ch]]


def snr_db(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n < 64:
        return -120.0
    a = a[:n]
    b = b[:n]
    sig = sum(x * x for x in a) / n
    noi = sum((a[i] - b[i]) ** 2 for i in range(n)) / n
    return 10.0 * math.log10((sig + 1e-20) / (noi + 1e-20))


def hp(x: list[float]) -> list[float]:
    out = [0.0] * len(x)
    prev = 0.0
    for i, v in enumerate(x):
        out[i] = v - prev
        prev = v
    return out


def align(ref: list[float], dec: list[float], lag: int) -> tuple[list[float], list[float]]:
    if lag >= 0:
        r = ref[lag:]
        d = dec[: len(r)]
    else:
        d = dec[-lag:]
        r = ref[: len(d)]
    n = min(len(r), len(d))
    return r[:n], d[:n]


def best_lag(ref: list[float], dec: list[float], max_lag: int) -> int:
    best = (-1e9, 0)
    for lag in range(-max_lag, max_lag + 1):
        r, d = align(ref, dec, lag)
        s = snr_db(r, d)
        if s > best[0]:
            best = (s, lag)
    return best[1]


def metric_pair(ref: list[float], dec: list[float], lag: int) -> tuple[float, float]:
    r, d = align(ref, dec, lag)
    full = snr_db(r, d)
    hf = snr_db(hp(r), hp(d))
    return full, hf


def markdown_table(rows: list[dict[str, object]]) -> str:
    lines: list[str] = []
    lines.append("| File | Lag | Full SNR | HF SNR | Delta Full vs Baseline | Delta HF vs Baseline | Sony Distance |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        lines.append(
            "| {f} | {lag} | {full:.3f} | {hf:.3f} | {df:+.3f} | {dh:+.3f} | {sd:.3f} |".format(
                f=r["file"],
                lag=r["lag"],
                full=r["full"],
                hf=r["hf"],
                df=r["delta_full_vs_baseline"],
                dh=r["delta_hf_vs_baseline"],
                sd=r["sony_distance"],
            )
        )
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, type=Path, help="reference source WAV")
    ap.add_argument("--sony", required=True, type=Path, help="Sony-decoded WAV for distance target")
    ap.add_argument("--baseline", required=True, type=Path, help="baseline decode WAV")
    ap.add_argument("--seconds", type=float, default=30.0, help="analyze first N seconds (0=full)")
    ap.add_argument("--max-lag", type=int, default=120)
    ap.add_argument("--out-md", type=Path, default=None)
    ap.add_argument("decodes", nargs="+", type=Path, help="candidate decode WAV files")
    args = ap.parse_args()

    max_frames = 0
    if args.seconds > 0:
        max_frames = int(round(44100.0 * args.seconds))

    sr_ref, ref = read_wav_mono16(args.ref, max_frames=max_frames)
    sr_s, sony = read_wav_mono16(args.sony, max_frames=max_frames)
    sr_b, base = read_wav_mono16(args.baseline, max_frames=max_frames)
    if sr_ref != sr_s or sr_ref != sr_b:
        raise RuntimeError("sample-rate mismatch among ref/sony/baseline")

    lag_s = best_lag(ref, sony, args.max_lag)
    lag_b = best_lag(ref, base, args.max_lag)
    sony_full, sony_hf = metric_pair(ref, sony, lag_s)
    base_full, base_hf = metric_pair(ref, base, lag_b)

    rows: list[dict[str, object]] = []
    for p in args.decodes:
        if not p.exists():
            continue
        sr_d, dec = read_wav_mono16(p, max_frames=max_frames)
        if sr_d != sr_ref:
            raise RuntimeError(f"{p}: sample-rate mismatch")
        lag = best_lag(ref, dec, args.max_lag)
        full, hf = metric_pair(ref, dec, lag)
        rows.append(
            {
                "file": p.name,
                "lag": lag,
                "full": full,
                "hf": hf,
                "delta_full_vs_baseline": full - base_full,
                "delta_hf_vs_baseline": hf - base_hf,
                "sony_distance": ((full - sony_full) ** 2 + (hf - sony_hf) ** 2) ** 0.5,
            }
        )

    rows.sort(key=lambda r: (r["delta_full_vs_baseline"], r["delta_hf_vs_baseline"]), reverse=True)

    print(
        "audit_window_s={w:.1f} sony_lag={ls} baseline_lag={lb} sony_full={sf:.3f} sony_hf={sh:.3f} baseline_full={bf:.3f} baseline_hf={bh:.3f}".format(
            w=args.seconds,
            ls=lag_s,
            lb=lag_b,
            sf=sony_full,
            sh=sony_hf,
            bf=base_full,
            bh=base_hf,
        )
    )
    print(markdown_table(rows))

    if args.out_md is not None:
        lines: list[str] = []
        lines.append("# LP2 Degradation Audit")
        lines.append("")
        lines.append(
            "Window: `{:.1f}` s, Sony lag `{}`, baseline lag `{}`".format(
                args.seconds, lag_s, lag_b
            )
        )
        lines.append("")
        lines.append(
            "Sony metrics: full `{:.3f}`, HF `{:.3f}`; baseline metrics: full `{:.3f}`, HF `{:.3f}`.".format(
                sony_full, sony_hf, base_full, base_hf
            )
        )
        lines.append("")
        lines.append(markdown_table(rows))
        lines.append("")
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"wrote={args.out_md}")


if __name__ == "__main__":
    main()
