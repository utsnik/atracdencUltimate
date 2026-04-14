#!/usr/bin/env python3
"""
Adaptive LP2 wrapper for atracdenc (no codec changes, flag-policy only).

This version uses frame-aware statistics (1024-sample windows) to choose a
track profile:
- `default`     : transient-bursty material
- `ml`          : mixed/uncertain and stable material
"""

from __future__ import annotations

import argparse
import csv
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
    # Mixed material: keep ML hints but avoid aggressive BFU forcing.
    if burst_ratio > 0.005 or mean_frame_crest > 4.5 or ecv > 0.10:
        return "ml", ["--ml-hints"]
    # Stable material: still keep ML-only policy by default.
    # Full-song sweeps showed bfu32 can regress on real music despite doing well
    # on short synthetic excerpts.
    return "ml", ["--ml-hints"]


def choose_profile_from_re_metrics(path: Path) -> tuple[str, list[str], str]:
    """
    Try deriving a profile decision from LP2 reverse metrics CSV.

    The script is robust to partial dumps: if expected fields are missing
    or constant zero, it falls back to generic behavior.
    """
    rows = []
    with path.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    if not rows:
        return "ml", ["--ml-hints"], "re-metrics-empty-fallback"

    def read_float(key: str) -> list[float]:
        out = []
        for row in rows:
            v = row.get(key, "")
            if v is None or v == "":
                continue
            try:
                out.append(float(v))
            except ValueError:
                continue
        return out

    gain = read_float("gain_bits")
    side = read_float("sideinfo_bits")
    tonal = read_float("tonal_bits")
    complexity = read_float("complexity_score")
    residual = read_float("residual_bits")
    actual = read_float("actual_bits_used")
    attack = read_float("attack_ratio")
    triggered = read_float("transient_triggered")
    promoted = read_float("tonal_promoted_count")
    matrix_idx = read_float("matrix_index")

    gain_points = []
    for i in range(4):
        gain_points.extend(read_float(f"gain_points_per_band[{i}]"))
    # Newer extractors may store gain points as one semicolon-packed field.
    if not gain_points:
        for row in rows:
            packed = row.get("gain_points_per_band", "")
            if not packed:
                continue
            for tok in packed.split(";"):
                try:
                    gain_points.append(float(tok))
                except ValueError:
                    continue

    if not gain or not side:
        return "ml", ["--ml-hints"], "re-metrics-missing-fields-fallback"

    def mean(vals: list[float]) -> float:
        return sum(vals) / max(1, len(vals))

    def cv(vals: list[float]) -> float:
        m = mean(vals)
        if m <= 1e-9:
            return 0.0
        v = sum((x - m) * (x - m) for x in vals) / max(1, len(vals))
        return (v**0.5) / m

    gain_cv = cv(gain)
    side_cv = cv(side)
    tonal_peak = max(tonal) if tonal else 0.0
    side_mean = mean(side)
    c_mean = mean(complexity) if complexity else 0.0
    attack_mean = mean(attack) if attack else 0.0
    trigger_rate = mean(triggered) if triggered else 0.0
    promoted_mean = mean(promoted) if promoted else 0.0
    gain_points_mean = mean(gain_points) if gain_points else 0.0
    matrix_cv = cv(matrix_idx) if matrix_idx else 0.0
    budget_fill = mean(actual) / max(1e-9, mean(actual) + mean(residual)) if (actual and residual) else 0.0

    if (
        gain_cv > 0.20
        or side_cv > 0.20
        or attack_mean > 1.80
        or trigger_rate > 0.12
    ):
        return "default", [], "re-metrics-transient-heavy"
    if promoted_mean >= 0.5 and matrix_cv > 0.05 and budget_fill > 0.80:
        return "bfu32_ml", ["--bfuidxconst", "32", "--ml-hints"], "re-metrics-tonal-stereo-rich"
    return "ml", ["--ml-hints"], "re-metrics-mixed"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enc", required=True, type=Path, help="path to atracdenc.exe")
    ap.add_argument("-i", "--input", required=True, type=Path, help="input WAV")
    ap.add_argument("-o", "--output", required=True, type=Path, help="output .at3.wav/.at3")
    ap.add_argument(
        "--re-metrics-csv",
        type=Path,
        default=None,
        help="optional deep LP2 metrics CSV from at3tool instrumentation",
    )
    ap.add_argument("--print-only", action="store_true", help="print selected profile and exit")
    args = ap.parse_args()

    decision_source = "signal-features"
    if args.re_metrics_csv is not None and args.re_metrics_csv.exists():
        profile_name, extra, decision_source = choose_profile_from_re_metrics(args.re_metrics_csv)
        crest = zcr = ecv = burst_ratio = mean_frame_crest = 0.0
    else:
        try:
            samples = read_mono_i16(args.input)
            crest, zcr, ecv = measure_global_features(samples)
            burst_ratio, mean_frame_crest = measure_frame_features(samples)
            profile_name, extra = choose_profile(crest, zcr, ecv, burst_ratio, mean_frame_crest)
        except Exception:
            # Non-WAV or unsupported PCM format: use conservative stable policy.
            profile_name, extra = "ml", ["--ml-hints"]
            decision_source = "input-format-fallback"
            crest = zcr = ecv = burst_ratio = mean_frame_crest = 0.0

    print(
        "source={s} profile={p} crest={c:.3f} zcr={z:.4f} ecv={e:.3f} burst_ratio={b:.4f} frame_crest={fc:.3f}".format(
            s=decision_source,
            p=profile_name,
            c=crest,
            z=zcr,
            e=ecv,
            b=burst_ratio,
            fc=mean_frame_crest,
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
