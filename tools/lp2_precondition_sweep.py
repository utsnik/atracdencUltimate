#!/usr/bin/env python3
"""
Sweep precondition parameters on a short excerpt to find a safer LP2 "air" preset.
"""

from __future__ import annotations

import argparse
import math
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed:\n{' '.join(cmd)}\n{p.stderr}")


def read_wav_mono16(path: Path) -> tuple[int, list[float]]:
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        data = w.readframes(w.getnframes())
        ch = w.getnchannels()
        if w.getsampwidth() != 2:
            raise RuntimeError(f"{path}: only 16-bit PCM supported")
    vals = struct.unpack("<" + "h" * (len(data) // 2), data)
    return sr, [float(v) for v in vals[::ch]]


def write_wav_slice(src: Path, dst: Path, seconds: float) -> None:
    with wave.open(str(src), "rb") as r:
        params = r.getparams()
        n = min(int(round(seconds * params.framerate)), params.nframes)
        frames = r.readframes(n)
    with wave.open(str(dst), "wb") as w:
        w.setparams(params)
        w.writeframes(frames)


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


def best_lag(ref: list[float], dec: list[float], max_lag: int = 120) -> int:
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


def encode_ml(enc: Path, inp: Path, out_at3: Path) -> None:
    run([str(enc), "-e", "atrac3", "-i", str(inp), "-o", str(out_at3), "--bitrate", "132", "--ml-hints"])


def decode_at3(at3tool: Path, inp: Path, out_wav: Path) -> None:
    run([str(at3tool), "-d", str(inp), str(out_wav)])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enc", required=True, type=Path)
    ap.add_argument("--at3tool", required=True, type=Path)
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--seconds", type=float, default=30.0)
    args = ap.parse_args()

    pre_script = Path(__file__).with_name("lp2_precondition_encode.py")
    presets = [
        (0.02, 0.00, 0.02),
        (0.03, 0.00, 0.04),
        (0.04, 0.01, 0.04),
        (0.06, 0.01, 0.06),
        (0.08, 0.02, 0.10),
    ]

    with tempfile.TemporaryDirectory(prefix="lp2_pre_sweep_") as td:
        tmp = Path(td)
        clip = tmp / "clip.wav"
        write_wav_slice(args.input, clip, args.seconds)
        _, ref = read_wav_mono16(clip)

        base_at3 = tmp / "base_ml.at3.wav"
        base_dec = tmp / "base_ml.dec.wav"
        encode_ml(args.enc, clip, base_at3)
        decode_at3(args.at3tool, base_at3, base_dec)
        _, b = read_wav_mono16(base_dec)
        lag = best_lag(ref, b)
        ar, ab = align(ref, b, lag)
        base_full = snr_db(ar, ab)
        base_hf = snr_db(hp(ar), hp(ab))

        print(f"clip_seconds={args.seconds:.1f} lag={lag} base_full={base_full:.3f} base_hf={base_hf:.3f}")
        print("preset,full_snr,hf_snr,delta_full,delta_hf,score")

        best = (-1e9, None)
        for pre, low, tr in presets:
            out_at3 = tmp / f"p_{pre:.2f}_{low:.2f}_{tr:.2f}.at3.wav"
            out_dec = tmp / f"p_{pre:.2f}_{low:.2f}_{tr:.2f}.dec.wav"
            run(
                [
                    sys.executable,
                    str(pre_script),
                    "--enc",
                    str(args.enc),
                    "-i",
                    str(clip),
                    "-o",
                    str(out_at3),
                    "--preemph",
                    f"{pre:.4f}",
                    "--low-cut-mix",
                    f"{low:.4f}",
                    "--transient-mix",
                    f"{tr:.4f}",
                ]
            )
            decode_at3(args.at3tool, out_at3, out_dec)
            _, c = read_wav_mono16(out_dec)
            rr, cc = align(ref, c, lag)
            full = snr_db(rr, cc)
            hf = snr_db(hp(rr), hp(cc))
            d_full = full - base_full
            d_hf = hf - base_hf
            # Favor HF gains but heavily penalize full-band loss.
            score = d_hf - max(0.0, -d_full * 1.8)
            print(f"{pre:.2f}/{low:.2f}/{tr:.2f},{full:.3f},{hf:.3f},{d_full:.3f},{d_hf:.3f},{score:.3f}")
            if score > best[0]:
                best = (score, (pre, low, tr, full, hf, d_full, d_hf))

        bp = best[1]
        assert bp is not None
        print(
            "best="
            f"pre={bp[0]:.2f} low={bp[1]:.2f} tr={bp[2]:.2f} "
            f"full={bp[3]:.3f} hf={bp[4]:.3f} d_full={bp[5]:.3f} d_hf={bp[6]:.3f}"
        )


if __name__ == "__main__":
    main()
