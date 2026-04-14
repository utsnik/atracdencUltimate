#!/usr/bin/env python3
"""
Decide among LP2 profiles using a short clip, then encode full input
with the chosen profile.
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


def encode_candidate(enc: Path, pre_script: Path, inp: Path, out_at3: Path, name: str) -> None:
    if name == "ml":
        run([str(enc), "-e", "atrac3", "-i", str(inp), "-o", str(out_at3), "--bitrate", "132", "--ml-hints"])
        return
    if name == "ml_nogain":
        run(
            [
                str(enc),
                "-e",
                "atrac3",
                "-i",
                str(inp),
                "-o",
                str(out_at3),
                "--bitrate",
                "132",
                "--ml-hints",
                "--nogaincontrol",
            ]
        )
        return
    if name == "ml_air":
        run(
            [
                sys.executable,
                str(pre_script),
                "--enc",
                str(enc),
                "-i",
                str(inp),
                "-o",
                str(out_at3),
            ]
        )
        return
    if name == "ml_air_nogain":
        run(
            [
                sys.executable,
                str(pre_script),
                "--enc",
                str(enc),
                "-i",
                str(inp),
                "-o",
                str(out_at3),
                "--nogaincontrol",
            ]
        )
        return
    if name == "bfu28_ml":
        run(
            [
                str(enc),
                "-e",
                "atrac3",
                "-i",
                str(inp),
                "-o",
                str(out_at3),
                "--bitrate",
                "132",
                "--ml-hints",
                "--bfuidxconst",
                "28",
            ]
        )
        return
    if name == "bfu28_base":
        run(
            [
                str(enc),
                "-e",
                "atrac3",
                "-i",
                str(inp),
                "-o",
                str(out_at3),
                "--bitrate",
                "132",
                "--bfuidxconst",
                "28",
            ]
        )
        return
    if name == "bfu27_ml":
        run(
            [
                str(enc),
                "-e",
                "atrac3",
                "-i",
                str(inp),
                "-o",
                str(out_at3),
                "--bitrate",
                "132",
                "--ml-hints",
                "--bfuidxconst",
                "27",
            ]
        )
        return
    if name == "bfu27_base":
        run(
            [
                str(enc),
                "-e",
                "atrac3",
                "-i",
                str(inp),
                "-o",
                str(out_at3),
                "--bitrate",
                "132",
                "--bfuidxconst",
                "27",
            ]
        )
        return
    if name == "bfu28_ml_nogain":
        run(
            [
                str(enc),
                "-e",
                "atrac3",
                "-i",
                str(inp),
                "-o",
                str(out_at3),
                "--bitrate",
                "132",
                "--ml-hints",
                "--nogaincontrol",
                "--bfuidxconst",
                "28",
            ]
        )
        return
    if name == "bfu28_base_nogain":
        run(
            [
                str(enc),
                "-e",
                "atrac3",
                "-i",
                str(inp),
                "-o",
                str(out_at3),
                "--bitrate",
                "132",
                "--nogaincontrol",
                "--bfuidxconst",
                "28",
            ]
        )
        return
    if name == "bfu27_ml_nogain":
        run(
            [
                str(enc),
                "-e",
                "atrac3",
                "-i",
                str(inp),
                "-o",
                str(out_at3),
                "--bitrate",
                "132",
                "--ml-hints",
                "--nogaincontrol",
                "--bfuidxconst",
                "27",
            ]
        )
        return
    if name == "bfu27_base_nogain":
        run(
            [
                str(enc),
                "-e",
                "atrac3",
                "-i",
                str(inp),
                "-o",
                str(out_at3),
                "--bitrate",
                "132",
                "--nogaincontrol",
                "--bfuidxconst",
                "27",
            ]
        )
        return
    raise RuntimeError(f"Unknown candidate: {name}")


def decode_at3(at3tool: Path, inp: Path, out_wav: Path) -> None:
    run([str(at3tool), "-d", str(inp), str(out_wav)])


def choose_profile(
    metrics: dict[str, tuple[float, float]],
    full_guard_db: float,
    hf_win_db: float,
    full_weight: float,
    hf_weight: float,
) -> tuple[str, str]:
    base_full, base_hf = metrics["ml"]

    viable: list[tuple[str, float]] = []
    for name, (full, hf) in metrics.items():
        if full < base_full - full_guard_db:
            continue
        d_full = full - base_full
        d_hf = hf - base_hf
        # Favor full-band improvements but still reward high-band clarity gains.
        score = d_full * full_weight + d_hf * hf_weight
        # If full-band is effectively tied, require a meaningful HF gain.
        if name != "ml" and abs(d_full) < 0.02 and d_hf < hf_win_db:
            score -= 1.0
        viable.append((name, score))

    if viable:
        viable.sort(key=lambda x: x[1], reverse=True)
        winner = viable[0][0]
        return winner, "best viable weighted score"

    # Fallback: choose best full-band SNR.
    winner = max(metrics.items(), key=lambda kv: kv[1][0])[0]
    return winner, "fallback best full-band"


def choose_profile_to_sony(
    metrics: dict[str, tuple[float, float]],
    sony_full: float,
    sony_hf: float,
    sony_full_weight: float,
    sony_hf_weight: float,
) -> tuple[str, str]:
    ranked: list[tuple[str, float]] = []
    for name, (full, hf) in metrics.items():
        d_full = full - sony_full
        d_hf = hf - sony_hf
        dist = ((d_full * sony_full_weight) ** 2 + (d_hf * sony_hf_weight) ** 2) ** 0.5
        ranked.append((name, dist))
    ranked.sort(key=lambda x: x[1])
    return ranked[0][0], "closest to sony metric target"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enc", required=True, type=Path)
    ap.add_argument("--at3tool", required=True, type=Path)
    ap.add_argument("-i", "--input", required=True, type=Path)
    ap.add_argument("-o", "--output", required=True, type=Path)
    ap.add_argument("--seconds", type=float, default=30.0, help="decision window length")
    ap.add_argument("--full-guard-db", type=float, default=0.10, help="max acceptable full-band SNR loss")
    ap.add_argument("--hf-win-db", type=float, default=0.05, help="minimum HF SNR gain to select no-gain")
    ap.add_argument("--full-weight", type=float, default=2.0, help="weight for full-band delta in decision score")
    ap.add_argument("--hf-weight", type=float, default=1.0, help="weight for HF delta in decision score")
    ap.add_argument("--include-air", action="store_true", help="include preconditioned candidates in decision")
    ap.add_argument("--include-hf-bfu", action="store_true", help="include BFU-28 candidates for HF-biased decisions")
    ap.add_argument("--target-sony", action="store_true", help="select candidate closest to Sony LP2 metrics on the clip")
    ap.add_argument("--sony-full-weight", type=float, default=1.0, help="weight for full-band distance in sony-target mode")
    ap.add_argument("--sony-hf-weight", type=float, default=1.0, help="weight for HF distance in sony-target mode")
    ap.add_argument("--print-only", action="store_true", help="evaluate and print decision without encoding output")
    args = ap.parse_args()

    pre_script = Path(__file__).with_name("lp2_precondition_encode.py")
    candidates = ["ml", "ml_nogain"]
    if args.include_air:
        candidates += ["ml_air", "ml_air_nogain"]
    if args.include_hf_bfu:
        candidates += [
            "bfu27_base",
            "bfu27_base_nogain",
            "bfu27_ml",
            "bfu27_ml_nogain",
            "bfu28_base",
            "bfu28_base_nogain",
            "bfu28_ml",
            "bfu28_ml_nogain",
        ]

    with tempfile.TemporaryDirectory(prefix="lp2_decision_") as td:
        tmp = Path(td)
        clip = tmp / "decision_clip.wav"
        write_wav_slice(args.input, clip, args.seconds)
        _, ref = read_wav_mono16(clip)

        decoded: dict[str, list[float]] = {}
        for name in candidates:
            at3 = tmp / f"{name}.at3.wav"
            dec = tmp / f"{name}.dec.wav"
            encode_candidate(args.enc, pre_script, clip, at3, name)
            decode_at3(args.at3tool, at3, dec)
            _, y = read_wav_mono16(dec)
            decoded[name] = y

        lag = best_lag(ref, decoded["ml"])
        metrics: dict[str, tuple[float, float]] = {}
        for name in candidates:
            r, d = align(ref, decoded[name], lag)
            full = snr_db(r, d)
            hf = snr_db(hp(r), hp(d))
            metrics[name] = (full, hf)
        sony_detail = ""
        if args.target_sony:
            sony_at3 = tmp / "sony_ref.at3"
            sony_dec = tmp / "sony_ref.dec.wav"
            run([str(args.at3tool), "-e", "-br", "132", str(clip), str(sony_at3)])
            decode_at3(args.at3tool, sony_at3, sony_dec)
            _, s = read_wav_mono16(sony_dec)
            lag_sony = best_lag(ref, s)
            rs, ss = align(ref, s, lag_sony)
            sony_full = snr_db(rs, ss)
            sony_hf = snr_db(hp(rs), hp(ss))
            profile, reason = choose_profile_to_sony(
                metrics=metrics,
                sony_full=sony_full,
                sony_hf=sony_hf,
                sony_full_weight=args.sony_full_weight,
                sony_hf_weight=args.sony_hf_weight,
            )
            sony_detail = (
                " sony_full={sf:.3f} sony_hf={sh:.3f} sony_full_w={sfw:.2f} sony_hf_w={shw:.2f}"
            ).format(
                sf=sony_full,
                sh=sony_hf,
                sfw=args.sony_full_weight,
                shw=args.sony_hf_weight,
            )
        else:
            profile, reason = choose_profile(
                metrics=metrics,
                full_guard_db=args.full_guard_db,
                hf_win_db=args.hf_win_db,
                full_weight=args.full_weight,
                hf_weight=args.hf_weight,
            )
        detail = " ".join([f"{n}_full={metrics[n][0]:.3f} {n}_hf={metrics[n][1]:.3f}" for n in candidates])
        print(
            (
                "decision={d} reason={r} lag={lag} {detail} full_guard={fg:.2f} hf_win={hw:.2f} full_weight={fw:.2f} hf_weight={hw2:.2f} include_air={ia} include_hf_bfu={ib} target_sony={ts}{sony_detail}"
            ).format(
                d=profile,
                r=reason,
                lag=lag,
                detail=detail,
                fg=args.full_guard_db,
                hw=args.hf_win_db,
                fw=args.full_weight,
                hw2=args.hf_weight,
                ia=int(args.include_air),
                ib=int(args.include_hf_bfu),
                ts=int(args.target_sony),
                sony_detail=sony_detail,
            )
        )

    if args.print_only:
        return

    with tempfile.TemporaryDirectory(prefix="lp2_decision_full_") as td:
        out_tmp = Path(td) / "chosen.at3.wav"
        encode_candidate(args.enc, pre_script, args.input, out_tmp, profile)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(out_tmp.read_bytes())


if __name__ == "__main__":
    main()
