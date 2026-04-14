#!/usr/bin/env python3
"""
Precondition + encode helper for LP2.

Goal: improve perceived sharpness (sibilants/transients) before ATRAC3 LP2 encode,
while keeping fully compliant ATRAC3 output.
"""

from __future__ import annotations

import argparse
import math
import struct
import subprocess
import tempfile
import wave
from pathlib import Path


def read_wav_i16(path: Path) -> tuple[int, int, list[list[float]]]:
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        sw = w.getsampwidth()
        if sw != 2:
            raise RuntimeError("Only 16-bit PCM WAV input is supported")
        data = w.readframes(w.getnframes())
    vals = struct.unpack("<" + "h" * (len(data) // 2), data)
    chans = [[] for _ in range(ch)]
    for i in range(0, len(vals), ch):
        for c in range(ch):
            chans[c].append(vals[i + c] / 32768.0)
    return sr, ch, chans


def write_wav_i16(path: Path, sr: int, chans: list[list[float]]) -> None:
    n = min(len(c) for c in chans)
    interleaved: list[int] = []
    for i in range(n):
        for c in chans:
            v = max(-1.0, min(1.0, c[i]))
            interleaved.append(int(round(v * 32767.0)))
    raw = struct.pack("<" + "h" * len(interleaved), *interleaved)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(len(chans))
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(raw)


def onepole_lp(x: list[float], fc: float, sr: int) -> list[float]:
    a = math.exp(-2.0 * math.pi * fc / max(1.0, float(sr)))
    y = [0.0] * len(x)
    s = 0.0
    for i, v in enumerate(x):
        s = (1.0 - a) * v + a * s
        y[i] = s
    return y


def process_channel(
    x: list[float],
    sr: int,
    preemph: float,
    low_cut_mix: float,
    transient_mix: float,
) -> list[float]:
    # Remove low-mid wool with a gentle low-shelf style subtraction.
    low = onepole_lp(x, fc=240.0, sr=sr)
    y = [x[i] - low_cut_mix * low[i] for i in range(len(x))]

    # Add high-frequency pre-emphasis (helps preserve sibilants after LP2 quantization).
    z = [0.0] * len(y)
    prev = 0.0
    for i, v in enumerate(y):
        z[i] = v + preemph * (v - prev)
        prev = v

    # Attack-aware HF boost: only add extra high-band energy on detected onsets.
    hi_lp = onepole_lp(z, fc=3600.0, sr=sr)
    out = [0.0] * len(z)
    env_fast = 0.0
    env_slow = 0.0
    a_fast = math.exp(-1.0 / max(1.0, 0.002 * sr))
    a_slow = math.exp(-1.0 / max(1.0, 0.040 * sr))
    for i, v in enumerate(z):
        av = abs(v)
        env_fast = a_fast * env_fast + (1.0 - a_fast) * av
        env_slow = a_slow * env_slow + (1.0 - a_slow) * av
        onset = max(0.0, env_fast - env_slow)
        boost = min(1.0, onset * 8.0)
        hi = v - hi_lp[i]
        out[i] = v + transient_mix * boost * hi
    return out


def normalize(chans: list[list[float]], peak_target: float = 0.98) -> list[list[float]]:
    peak = 1e-9
    for c in chans:
        if c:
            peak = max(peak, max(abs(v) for v in c))
    scale = min(1.0, peak_target / peak)
    return [[v * scale for v in c] for c in chans]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enc", required=True, type=Path, help="path to atracdenc.exe")
    ap.add_argument("-i", "--input", required=True, type=Path, help="input WAV")
    ap.add_argument("-o", "--output", required=True, type=Path, help="output .at3/.at3.wav")
    ap.add_argument("--preemph", type=float, default=0.02, help="HF pre-emphasis amount")
    ap.add_argument("--low-cut-mix", type=float, default=0.00, help="low-mid trim amount")
    ap.add_argument("--transient-mix", type=float, default=0.02, help="onset HF boost amount")
    ap.add_argument("--no-ml", action="store_true", help="disable --ml-hints")
    ap.add_argument("--nogaincontrol", action="store_true", help="pass --nogaincontrol to encoder")
    args = ap.parse_args()

    sr, _, chans = read_wav_i16(args.input)
    proc = [
        process_channel(c, sr, args.preemph, args.low_cut_mix, args.transient_mix)
        for c in chans
    ]
    proc = normalize(proc)

    with tempfile.TemporaryDirectory(prefix="lp2_pre_") as td:
        tmp_wav = Path(td) / f"{args.input.stem}.pre.wav"
        write_wav_i16(tmp_wav, sr, proc)
        cmd = [
            str(args.enc),
            "-e",
            "atrac3",
            "-i",
            str(tmp_wav),
            "-o",
            str(args.output),
            "--bitrate",
            "132",
        ]
        if not args.no_ml:
            cmd.append("--ml-hints")
        if args.nogaincontrol:
            cmd.append("--nogaincontrol")
        p = subprocess.run(cmd)
        raise SystemExit(p.returncode)


if __name__ == "__main__":
    main()
