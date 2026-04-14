#!/usr/bin/env python3
"""
Generate a compact LP2 scorecard (Markdown) from a profile sweep.
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
    ("bfu32_ml", ["--bfuidxconst", "32", "--ml-hints"]),
]


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed:\n{' '.join(cmd)}\n{p.stderr}")


def read_wav_mono16(path: Path) -> list[float]:
    with wave.open(str(path), "rb") as w:
        data = w.readframes(w.getnframes())
        ch = w.getnchannels()
    vals = struct.unpack("<" + "h" * (len(data) // 2), data)
    return [float(v) for v in vals[::ch]]


def snr_db(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    a = a[:n]
    b = b[:n]
    sig = sum(x * x for x in a) / max(1, n)
    noi = sum((a[i] - b[i]) ** 2 for i in range(n)) / max(1, n)
    return 10.0 * math.log10((sig + 1e-20) / (noi + 1e-20))


def best_aligned_snr(ref: list[float], dec: list[float], max_lag: int = 300) -> tuple[float, int]:
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
    return best


def bench_one(inp: Path, enc: Path, at3tool: Path, tmp: Path) -> list[tuple[str, float, float, float]]:
    sony_at3 = tmp / f"{inp.stem}.sony.at3"
    sony_dec = tmp / f"{inp.stem}.sony.dec.wav"
    run([str(at3tool), "-e", "-br", "132", str(inp), str(sony_at3)])
    run([str(at3tool), "-d", str(sony_at3), str(sony_dec)])
    ref = read_wav_mono16(inp)
    s = read_wav_mono16(sony_dec)
    sony_snr, _ = best_aligned_snr(ref, s)

    out = []
    for name, args in PROFILES:
        ours_at3 = tmp / f"{inp.stem}.{name}.at3.wav"
        ours_dec = tmp / f"{inp.stem}.{name}.dec.wav"
        run([str(enc), "-e", "atrac3", "-i", str(inp), "-o", str(ours_at3), "--bitrate", "132"] + args)
        run([str(at3tool), "-d", str(ours_at3), str(ours_dec)])
        o = read_wav_mono16(ours_dec)
        ours_snr, _ = best_aligned_snr(ref, o)
        out.append((name, ours_snr, sony_snr, ours_snr - sony_snr))
    return out


def choose_adaptive_best(sample: str, rows: list[tuple[str, float, float, float]]) -> str:
    # Interim policy v2:
    # - keep default on explicitly transient-heavy cases
    # - use ml elsewhere (avoid forcing BFU32 on music/full tracks)
    if "transient" in sample.lower():
        return "default"
    return "ml"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enc", required=True, type=Path)
    ap.add_argument("--at3tool", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path, help="output markdown path")
    ap.add_argument("wav", nargs="+", type=Path)
    args = ap.parse_args()

    all_rows: dict[str, list[tuple[str, float, float, float]]] = {}
    with tempfile.TemporaryDirectory(prefix="lp2_score_") as td:
        tmp = Path(td)
        for w in args.wav:
            all_rows[w.name] = bench_one(w, args.enc, args.at3tool, tmp)

    # Aggregate
    prof_to_deltas: dict[str, list[float]] = {k: [] for k, _ in PROFILES}
    adaptive_deltas: list[float] = []
    for sample, rows in all_rows.items():
        for name, _, _, d in rows:
            prof_to_deltas[name].append(d)
        chosen = choose_adaptive_best(sample, rows)
        chosen_delta = next(d for name, _, _, d in rows if name == chosen)
        adaptive_deltas.append(chosen_delta)

    lines: list[str] = []
    lines.append("# LP2 Scorecard")
    lines.append("")
    lines.append("## Per Sample")
    lines.append("")
    lines.append("| Sample | Profile | Ours SNR | Sony SNR | Delta |")
    lines.append("|---|---:|---:|---:|---:|")
    for sample, rows in all_rows.items():
        for name, ours, sony, d in rows:
            lines.append(f"| {sample} | {name} | {ours:.3f} | {sony:.3f} | {d:.3f} |")
    lines.append("")
    lines.append("## Averages")
    lines.append("")
    lines.append("| Mode | Avg Delta vs Sony |")
    lines.append("|---|---:|")
    for name, _ in PROFILES:
        vals = prof_to_deltas[name]
        lines.append(f"| {name} | {sum(vals)/len(vals):.3f} |")
    lines.append(f"| adaptive_policy | {sum(adaptive_deltas)/len(adaptive_deltas):.3f} |")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- `adaptive_policy` currently selects `default` for transient samples and `ml` otherwise.")
    lines.append("- This is an interim policy pending true dynamic RE frame dumps.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
