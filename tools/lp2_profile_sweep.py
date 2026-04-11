#!/usr/bin/env python3
"""
LP2 profile sweep helper for atracdenc + at3tool.

Runs a small profile matrix on a set of WAV files and reports aligned SNR deltas
versus Sony at3tool encode/decode at 132 kbps.
"""

from __future__ import annotations

import argparse
import math
import struct
import subprocess
import tempfile
import wave
from pathlib import Path


PROFILES = [
    ("default", []),
    ("ml", ["--ml-hints"]),
    ("bfu24", ["--bfuidxconst", "24"]),
    ("bfu28", ["--bfuidxconst", "28"]),
    ("bfu32", ["--bfuidxconst", "32"]),
    ("bfu32_ml", ["--bfuidxconst", "32", "--ml-hints"]),
    ("nogain", ["--nogaincontrol"]),
    ("notonal", ["--notonal"]),
]


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed:\n{' '.join(cmd)}\n{p.stderr}")


def read_wav_mono16(path: Path) -> list[float]:
    with wave.open(str(path), "rb") as w:
        data = w.readframes(w.getnframes())
        ch = w.getnchannels()
        if w.getsampwidth() != 2:
            raise RuntimeError(f"{path}: only 16-bit PCM supported")
    vals = struct.unpack("<" + "h" * (len(data) // 2), data)
    return [float(v) for v in vals[::ch]]


def snr_db(ref: list[float], test: list[float]) -> float:
    n = min(len(ref), len(test))
    ref = ref[:n]
    test = test[:n]
    sig = sum(x * x for x in ref) / max(1, n)
    noi = sum((ref[i] - test[i]) ** 2 for i in range(n)) / max(1, n)
    return 10.0 * math.log10((sig + 1e-20) / (noi + 1e-20))


def best_aligned_snr(ref: list[float], test: list[float], max_lag: int = 300) -> tuple[float, int]:
    best = (-1e9, 0)
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            a = ref[lag:]
            b = test[: len(a)]
        else:
            b = test[-lag:]
            a = ref[: len(b)]
        if len(a) < 1000:
            continue
        s = snr_db(a, b)
        if s > best[0]:
            best = (s, lag)
    return best


def bench_file(inp: Path, enc: Path, at3tool: Path, tmp: Path) -> list[tuple[str, float, float, float, int, int]]:
    sony_at3 = tmp / f"{inp.stem}.sony.at3"
    sony_dec = tmp / f"{inp.stem}.sony.dec.wav"
    run([str(at3tool), "-e", "-br", "132", str(inp), str(sony_at3)])
    run([str(at3tool), "-d", str(sony_at3), str(sony_dec)])
    ref = read_wav_mono16(inp)
    sony = read_wav_mono16(sony_dec)
    sony_snr, sony_lag = best_aligned_snr(ref, sony)

    rows = []
    for name, args in PROFILES:
        ours_at3 = tmp / f"{inp.stem}.{name}.at3.wav"
        ours_dec = tmp / f"{inp.stem}.{name}.dec.wav"
        run([str(enc), "-e", "atrac3", "-i", str(inp), "-o", str(ours_at3), "--bitrate", "132"] + args)
        run([str(at3tool), "-d", str(ours_at3), str(ours_dec)])
        ours = read_wav_mono16(ours_dec)
        ours_snr, ours_lag = best_aligned_snr(ref, ours)
        rows.append((name, ours_snr, sony_snr, ours_snr - sony_snr, ours_lag, sony_lag))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enc", required=True, type=Path, help="Path to atracdenc.exe")
    ap.add_argument("--at3tool", required=True, type=Path, help="Path to at3tool.exe")
    ap.add_argument("wav", nargs="+", type=Path, help="Input WAV files")
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="lp2_sweep_") as t:
        tmp = Path(t)
        for wav_path in args.wav:
            print(f"\nCASE {wav_path.name}")
            rows = bench_file(wav_path, args.enc, args.at3tool, tmp)
            for name, ours, sony, delta, olag, slag in rows:
                print(
                    f"{name:10s} ours={ours:7.3f} sony={sony:7.3f} "
                    f"delta={delta:7.3f} lag={olag}/{slag}"
                )


if __name__ == "__main__":
    main()

