#!/usr/bin/env python3
"""
Join LP2 score-workflow hotspots with Sony deep extractor metrics.

Outputs:
- CSV table with top-K ranked hotspot actions per sample
- JSONL rows for downstream analysis
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path


def parse_semis(text: str, cast=int) -> list:
    if not text:
        return []
    out = []
    for part in text.split(";"):
        p = part.strip()
        if not p:
            continue
        try:
            out.append(cast(p))
        except ValueError:
            out.append(cast(float(p)))
    return out


def mean(vals: list[float]) -> float:
    return statistics.fmean(vals) if vals else 0.0


def quantile(vals: list[float], q: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    idx = max(0, min(len(s) - 1, int((len(s) - 1) * q)))
    return s[idx]


def aggregate_sony(csv_path: Path) -> tuple[dict[int, dict[str, float | int]], dict[str, float]]:
    by_frame: dict[int, list[dict[str, float | int]]] = {}
    with csv_path.open("r", newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            frame = int(row.get("frame_idx", "0"))
            weight_idx = parse_semis(row.get("weight_idx", ""), int)
            gain_points = parse_semis(row.get("gain_points_per_band", ""), int)
            item = {
                "complexity_score": float(row.get("complexity_score", "0")),
                "residual_bits": float(row.get("residual_bits", "0")),
                "actual_bits_used": float(row.get("actual_bits_used", "0")),
                "attack_ratio": float(row.get("attack_ratio", "0")),
                "transient_triggered": int(row.get("transient_triggered", "0")),
                "matrix_index": int(row.get("matrix_index", "0")),
                "num_tonals": float(row.get("num_tonals", "0")),
                "weight_sum": float(sum(weight_idx)),
                "gain_sum": float(sum(gain_points)),
            }
            by_frame.setdefault(frame, []).append(item)

    out: dict[int, dict[str, float | int]] = {}
    prev_matrix = None
    prev_weight = None
    prev_gain = None
    for frame in sorted(by_frame):
        items = by_frame[frame]
        matrix_values = [int(x["matrix_index"]) for x in items]
        matrix_primary = int(round(mean([float(v) for v in matrix_values])))
        weight_sum = mean([float(x["weight_sum"]) for x in items])
        gain_sum = mean([float(x["gain_sum"]) for x in items])
        row = {
            "complexity_score": mean([float(x["complexity_score"]) for x in items]),
            "residual_bits": mean([float(x["residual_bits"]) for x in items]),
            "actual_bits_used": mean([float(x["actual_bits_used"]) for x in items]),
            "attack_ratio": max(float(x["attack_ratio"]) for x in items),
            "transient_triggered": 1 if any(int(x["transient_triggered"]) for x in items) else 0,
            "matrix_index": matrix_primary,
            "matrix_modes": len(set(matrix_values)),
            "weight_sum": weight_sum,
            "gain_sum": gain_sum,
            "num_tonals": mean([float(x["num_tonals"]) for x in items]),
            "matrix_changed": 0 if prev_matrix is None else int(matrix_primary != prev_matrix),
            "weight_delta": 0.0 if prev_weight is None else abs(weight_sum - prev_weight),
            "gain_delta": 0.0 if prev_gain is None else abs(gain_sum - prev_gain),
        }
        out[frame] = row
        prev_matrix = matrix_primary
        prev_weight = weight_sum
        prev_gain = gain_sum

    all_complexity = [float(v["complexity_score"]) for v in out.values()]
    all_actual = [float(v["actual_bits_used"]) for v in out.values()]
    all_residual = [float(v["residual_bits"]) for v in out.values()]
    stats = {
        "complexity_q75": quantile(all_complexity, 0.75),
        "actual_q75": quantile(all_actual, 0.75),
        "residual_q75": quantile(all_residual, 0.75),
    }
    return out, stats


def classify_bucket(sony: dict[str, float | int], stats: dict[str, float]) -> tuple[str, str, str]:
    stereo_driven = (
        int(sony.get("matrix_changed", 0)) == 1
        or float(sony.get("weight_delta", 0.0)) > 2.0
        or int(sony.get("matrix_modes", 1)) > 1
    )
    if stereo_driven:
        return (
            "stereo-driven",
            "matrix/weight movement around hotspot frame",
            "tighten HF side-retention hysteresis and matrix hold continuity",
        )

    gt_driven = (
        int(sony.get("transient_triggered", 0)) == 1
        or float(sony.get("attack_ratio", 0.0)) > 4.0
        or float(sony.get("gain_sum", 0.0)) > 0.5
    )
    if gt_driven:
        return (
            "gain/transient-driven",
            "elevated attack/gain signature around hotspot frame",
            "adjust attack protection and weak one-frame gain-trigger suppression",
        )

    alloc_driven = (
        float(sony.get("complexity_score", 0.0)) >= stats.get("complexity_q75", 0.0)
        or float(sony.get("actual_bits_used", 0.0)) >= stats.get("actual_q75", 0.0)
        or float(sony.get("residual_bits", 0.0)) >= stats.get("residual_q75", 0.0)
    )
    if alloc_driven:
        return (
            "allocator-driven",
            "high complexity/bit-pressure relative to sample baseline",
            "apply bounded BFU/shift feedback nudges with strict continuity caps",
        )

    return (
        "allocator-driven",
        "default fallback after stereo/transient tests",
        "prioritize conservative allocator-side micro-adjustments",
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description="Join score hotspots with Sony LP2 metrics")
    ap.add_argument("--score-json", required=True, type=Path, help="JSON output from lp2_score_workflow.py")
    ap.add_argument("--sony-raw-dir", type=Path, default=repo_root / "reverse" / "windows" / "lp2_parity_re" / "raw")
    ap.add_argument("--top-k", type=int, default=25)
    ap.add_argument("--out-csv", required=True, type=Path)
    ap.add_argument("--out-jsonl", required=True, type=Path)
    args = ap.parse_args()

    score = json.loads(args.score_json.read_text(encoding="utf-8"))
    hotspots: dict[str, list[dict[str, float]]] = score.get("hotspots", {})
    rows: list[dict] = []

    for sample, frames in hotspots.items():
        sony_csv = args.sony_raw_dir / f"deep_metrics_{sample}.csv"
        if not sony_csv.exists():
            continue
        sony_map, stats = aggregate_sony(sony_csv)
        ranked = sorted(frames, key=lambda x: (float(x.get("delta", 0.0)), -float(x.get("hf_energy_db", 0.0))))[: max(1, args.top_k)]
        for i, h in enumerate(ranked, start=1):
            frame = int(h.get("frame", 0))
            sony = sony_map.get(frame, {})
            bucket, reason, action = classify_bucket(sony, stats)
            rows.append(
                {
                    "sample": sample,
                    "rank": i,
                    "frame": frame,
                    "delta_vs_baseline": float(h.get("delta", 0.0)),
                    "hf_energy_db": float(h.get("hf_energy_db", 0.0)),
                    "baseline_snr": float(h.get("baseline_snr", 0.0)),
                    "candidate_snr": float(h.get("candidate_snr", 0.0)),
                    "sony_complexity_score": float(sony.get("complexity_score", 0.0)),
                    "sony_residual_bits": float(sony.get("residual_bits", 0.0)),
                    "sony_actual_bits_used": float(sony.get("actual_bits_used", 0.0)),
                    "sony_attack_ratio": float(sony.get("attack_ratio", 0.0)),
                    "sony_transient_triggered": int(sony.get("transient_triggered", 0)),
                    "sony_matrix_index": int(sony.get("matrix_index", 0)),
                    "sony_matrix_changed": int(sony.get("matrix_changed", 0)),
                    "sony_weight_sum": float(sony.get("weight_sum", 0.0)),
                    "sony_weight_delta": float(sony.get("weight_delta", 0.0)),
                    "sony_gain_sum": float(sony.get("gain_sum", 0.0)),
                    "sony_gain_delta": float(sony.get("gain_delta", 0.0)),
                    "sony_num_tonals": float(sony.get("num_tonals", 0.0)),
                    "bucket": bucket,
                    "bucket_reason": reason,
                    "recommended_action": action,
                }
            )

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    args.out_jsonl.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "sample",
        "rank",
        "frame",
        "delta_vs_baseline",
        "hf_energy_db",
        "baseline_snr",
        "candidate_snr",
        "sony_complexity_score",
        "sony_residual_bits",
        "sony_actual_bits_used",
        "sony_attack_ratio",
        "sony_transient_triggered",
        "sony_matrix_index",
        "sony_matrix_changed",
        "sony_weight_sum",
        "sony_weight_delta",
        "sony_gain_sum",
        "sony_gain_delta",
        "sony_num_tonals",
        "bucket",
        "bucket_reason",
        "recommended_action",
    ]
    with args.out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(row)

    with args.out_jsonl.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=True) + "\n")

    print(f"wrote={args.out_csv}")
    print(f"wrote={args.out_jsonl}")
    print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()

