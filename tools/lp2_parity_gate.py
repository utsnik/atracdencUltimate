#!/usr/bin/env python3
"""
LP2 parity gate: compare a candidate mode against frozen-v10 baseline and Sony.

This is a quick safety harness for tuning iterations:
- clips the input
- encodes candidate + frozen-v10 + Sony LP2
- decodes with at3tool
- computes full-band and HF-proxy SNR
- prints pass/fail against baseline guard rails
"""

from __future__ import annotations

import argparse
import math
import shutil
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed ({p.returncode}):\n{' '.join(cmd)}\n{p.stderr}")


def write_wav_slice(src: Path, dst: Path, seconds: float) -> None:
    with wave.open(str(src), "rb") as r:
        params = r.getparams()
        n = min(int(round(seconds * params.framerate)), params.nframes)
        frames = r.readframes(n)
    with wave.open(str(dst), "wb") as w:
        w.setparams(params)
        w.writeframes(frames)


def read_wav_mono16(path: Path) -> list[float]:
    with wave.open(str(path), "rb") as w:
        data = w.readframes(w.getnframes())
        ch = w.getnchannels()
        sw = w.getsampwidth()
    if sw != 2:
        raise RuntimeError(f"{path}: only 16-bit PCM WAV supported")
    vals = struct.unpack("<" + "h" * (len(data) // 2), data)
    return [float(v) for v in vals[::ch]]


def hp(x: list[float]) -> list[float]:
    out = [0.0] * len(x)
    prev = 0.0
    for i, v in enumerate(x):
        out[i] = v - prev
        prev = v
    return out


def snr_db(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n < 64:
        return -120.0
    a = a[:n]
    b = b[:n]
    sig = sum(x * x for x in a) / n
    noi = sum((a[i] - b[i]) ** 2 for i in range(n)) / n
    return 10.0 * math.log10((sig + 1e-20) / (noi + 1e-20))


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


def encode_with_wrapper(
    wrapper: Path,
    enc: Path,
    legacy_enc: Path,
    at3tool: Path,
    inp: Path,
    out: Path,
    mode: str,
) -> None:
    cmd = [
        sys.executable,
        str(wrapper),
        "--enc",
        str(enc),
        "--legacy-enc",
        str(legacy_enc),
        "--at3tool",
        str(at3tool),
        "-i",
        str(inp),
        "-o",
        str(out),
        "--mode",
        mode,
    ]
    run(cmd)


def decode_at3(at3tool: Path, inp: Path, out_wav: Path) -> None:
    run([str(at3tool), "-d", str(inp), str(out_wav)])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enc", required=True, type=Path, help="current encoder binary")
    ap.add_argument("--legacy-enc", required=True, type=Path, help="known-good legacy encoder binary")
    ap.add_argument("--at3tool", required=True, type=Path)
    ap.add_argument("-i", "--input", required=True, type=Path, help="input WAV")
    ap.add_argument("--mode", default="ml", help="candidate mode for tools/atracdenc_lp2.py")
    ap.add_argument("--seconds", type=float, default=30.0, help="clip length for gate")
    ap.add_argument("--full-guard-db", type=float, default=0.10, help="max full-band loss vs frozen-v10")
    ap.add_argument("--hf-guard-db", type=float, default=0.20, help="max HF loss vs frozen-v10")
    ap.add_argument("--keep-artifacts-dir", type=Path, default=None, help="optional folder to keep generated artifacts")
    args = ap.parse_args()

    wrapper = Path(__file__).with_name("atracdenc_lp2.py")

    with tempfile.TemporaryDirectory(prefix="lp2_gate_") as td:
        tmp = Path(td)
        clip = tmp / "clip.wav"
        write_wav_slice(args.input, clip, args.seconds)
        ref = read_wav_mono16(clip)

        candidate_at3 = tmp / "candidate.at3.wav"
        candidate_dec = tmp / "candidate.dec.wav"
        baseline_at3 = tmp / "baseline_v10.at3.wav"
        baseline_dec = tmp / "baseline_v10.dec.wav"
        sony_at3 = tmp / "sony.at3"
        sony_dec = tmp / "sony.dec.wav"

        encode_with_wrapper(wrapper, args.enc, args.legacy_enc, args.at3tool, clip, candidate_at3, args.mode)
        encode_with_wrapper(wrapper, args.enc, args.legacy_enc, args.at3tool, clip, baseline_at3, "quality-v10-frozen")
        run([str(args.at3tool), "-e", "-br", "132", str(clip), str(sony_at3)])

        decode_at3(args.at3tool, candidate_at3, candidate_dec)
        decode_at3(args.at3tool, baseline_at3, baseline_dec)
        decode_at3(args.at3tool, sony_at3, sony_dec)

        cand = read_wav_mono16(candidate_dec)
        base = read_wav_mono16(baseline_dec)
        sony = read_wav_mono16(sony_dec)

        lag_c = best_lag(ref, cand)
        lag_b = best_lag(ref, base)
        lag_s = best_lag(ref, sony)
        r_c, d_c = align(ref, cand, lag_c)
        r_b, d_b = align(ref, base, lag_b)
        r_s, d_s = align(ref, sony, lag_s)

        c_full = snr_db(r_c, d_c)
        c_hf = snr_db(hp(r_c), hp(d_c))
        b_full = snr_db(r_b, d_b)
        b_hf = snr_db(hp(r_b), hp(d_b))
        s_full = snr_db(r_s, d_s)
        s_hf = snr_db(hp(r_s), hp(d_s))

        d_full = c_full - b_full
        d_hf = c_hf - b_hf
        pass_gate = (d_full >= -args.full_guard_db) and (d_hf >= -args.hf_guard_db)

        print(
            "candidate_mode={m} lag={lag} "
            "lag_candidate={lc} lag_baseline={lb} lag_sony={ls} "
            "candidate_full={cf:.3f} candidate_hf={ch:.3f} "
            "baseline_full={bf:.3f} baseline_hf={bh:.3f} "
            "sony_full={sf:.3f} sony_hf={sh:.3f} "
            "delta_vs_baseline_full={df:.3f} delta_vs_baseline_hf={dh:.3f} "
            "gate_full={gf:.2f} gate_hf={gh:.2f} pass={p}".format(
                m=args.mode,
                lag=lag_c,
                lc=lag_c,
                lb=lag_b,
                ls=lag_s,
                cf=c_full,
                ch=c_hf,
                bf=b_full,
                bh=b_hf,
                sf=s_full,
                sh=s_hf,
                df=d_full,
                dh=d_hf,
                gf=args.full_guard_db,
                gh=args.hf_guard_db,
                p=int(pass_gate),
            )
        )

        if args.keep_artifacts_dir is not None:
            args.keep_artifacts_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidate_at3, args.keep_artifacts_dir / f"candidate_{args.mode}.at3.wav")
            shutil.copy2(candidate_dec, args.keep_artifacts_dir / f"candidate_{args.mode}.dec.wav")
            shutil.copy2(baseline_at3, args.keep_artifacts_dir / "baseline_v10.at3.wav")
            shutil.copy2(baseline_dec, args.keep_artifacts_dir / "baseline_v10.dec.wav")
            shutil.copy2(sony_at3, args.keep_artifacts_dir / "sony.at3")
            shutil.copy2(sony_dec, args.keep_artifacts_dir / "sony.dec.wav")
            print(f"artifacts_saved={args.keep_artifacts_dir}")

    raise SystemExit(0 if pass_gate else 2)


if __name__ == "__main__":
    main()
