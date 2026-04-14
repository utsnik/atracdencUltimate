#!/usr/bin/env python3
"""
Canonical LP2 music-parity gate runner.

Runs:
- fast corpus gate (YOUtopia, Badlands, chirp_wait, tmp_transient)
- long YOUtopia242 gate

Enforces hard anti-regression rules and tracks consecutive music-target passes.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}\n{p.stderr}")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_row(rows: list[dict], name: str) -> dict:
    for row in rows:
        if str(row.get("name", "")) == name:
            return row
    return {}


def to_float(row: dict, key: str, default: float = 0.0) -> float:
    try:
        v = row.get(key, default)
        if v is None:
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    score = Path(__file__).with_name("lp2_score_workflow.py")
    fast_manifest = Path(__file__).with_name("lp2_fast_stability_manifest.json")
    long_manifest = Path(__file__).with_name("lp2_youtopia242_manifest.json")

    ap = argparse.ArgumentParser(description="Run LP2 music-parity-first gate")
    ap.add_argument("--enc", required=True, type=Path)
    ap.add_argument("--legacy-enc", type=Path, default=repo_root / "build2" / "src" / "atracdenc.exe")
    ap.add_argument("--at3tool", type=Path, default=repo_root / "reverse" / "windows" / "at3tool.exe")
    ap.add_argument("--mode", default="quality-v10-stable")
    ap.add_argument("--baseline-mode", default="quality-v10-native")
    ap.add_argument("--out-md", type=Path, default=repo_root / "docs" / "LP2_MUSIC_PARITY_GATE.md")
    ap.add_argument("--state-json", type=Path, default=repo_root / "docs" / "re" / "lp2_music_parity_state.json")
    ap.add_argument("--enforce-music-targets", action="store_true")
    ap.add_argument("--gate-duration-ratio-min", type=float, default=0.95)
    ap.add_argument("--gate-youtopia-full-min", type=float, default=-0.10)
    ap.add_argument("--gate-youtopia-hf-min", type=float, default=-0.10)
    ap.add_argument("--gate-youtopia242-worst-hotspot-min", type=float, default=-0.25)
    ap.add_argument("--music-target-youtopia-sony-dist-max", type=float, default=0.90)
    ap.add_argument("--music-target-badlands-sony-dist-max", type=float, default=1.00)
    args = ap.parse_args()

    work_dir = args.out_md.parent
    work_dir.mkdir(parents=True, exist_ok=True)
    fast_md = work_dir / "LP2_FAST_MUSIC_GATE.md"
    fast_json = work_dir / "LP2_FAST_MUSIC_GATE.json"
    long_md = work_dir / "LP2_LONG_YOUTOPIA242_GATE.md"
    long_json = work_dir / "LP2_LONG_YOUTOPIA242_GATE.json"

    common = [
        sys.executable,
        str(score),
        "--enc",
        str(args.enc),
        "--legacy-enc",
        str(args.legacy_enc),
        "--at3tool",
        str(args.at3tool),
        "--mode",
        args.mode,
        "--baseline-mode",
        args.baseline_mode,
        "--stability-gate",
        "--gate-duration-ratio-min",
        f"{args.gate_duration_ratio_min}",
        "--gate-youtopia-full-min",
        f"{args.gate_youtopia_full_min}",
        "--gate-youtopia-hf-min",
        f"{args.gate_youtopia_hf_min}",
        "--gate-youtopia-worst-hotspot-min",
        f"{args.gate_youtopia242_worst_hotspot_min}",
    ]

    run(
        common
        + [
            "--manifest",
            str(fast_manifest),
            "--out-md",
            str(fast_md),
            "--out-json",
            str(fast_json),
            "--hotspot-limit",
            "25",
        ]
    )
    run(
        common
        + [
            "--manifest",
            str(long_manifest),
            "--out-md",
            str(long_md),
            "--out-json",
            str(long_json),
            "--hotspot-limit",
            "25",
        ]
    )

    fast = load_json(fast_json)
    long = load_json(long_json)
    fast_rows = fast.get("rows", [])
    long_rows = long.get("rows", [])
    you = find_row(fast_rows, "YOUtopia")
    bad = find_row(fast_rows, "Badlands")
    you242 = find_row(long_rows, "YOUtopia242")

    hard_failures: list[str] = []
    if fast.get("stability_gate", {}).get("status") != "PASS":
        hard_failures.append("fast_corpus_gate")
    if long.get("stability_gate", {}).get("status") != "PASS":
        hard_failures.append("long_youtopia242_gate")

    if to_float(you242, "candidate_hotspot_worst_delta", -999.0) < args.gate_youtopia242_worst_hotspot_min:
        hard_failures.append("youtopia242_worst_hotspot")
    if to_float(you, "delta_full_vs_baseline", -999.0) < args.gate_youtopia_full_min:
        hard_failures.append("youtopia_full_delta")
    if to_float(you, "delta_hf_vs_baseline", -999.0) < args.gate_youtopia_hf_min:
        hard_failures.append("youtopia_hf_delta")

    for row in fast_rows + long_rows:
        if to_float(row, "candidate_duration_ratio", 0.0) < args.gate_duration_ratio_min:
            hard_failures.append(f"{row.get('name', 'unknown')}_duration_ratio")

    hard_pass = len(hard_failures) == 0
    you_sony = to_float(you, "sony_distance", 999.0)
    bad_sony = to_float(bad, "sony_distance", 999.0)
    music_target_pass = hard_pass and you_sony <= args.music_target_youtopia_sony_dist_max and bad_sony <= args.music_target_badlands_sony_dist_max

    state = {"consecutive_music_target_passes": 0}
    if args.state_json.exists():
        try:
            state = json.loads(args.state_json.read_text(encoding="utf-8"))
        except Exception:
            state = {"consecutive_music_target_passes": 0}
    if music_target_pass:
        state["consecutive_music_target_passes"] = int(state.get("consecutive_music_target_passes", 0)) + 1
    else:
        state["consecutive_music_target_passes"] = 0
    args.state_json.parent.mkdir(parents=True, exist_ok=True)
    args.state_json.write_text(json.dumps(state, indent=2), encoding="utf-8")

    lines = [
        "# LP2 Music Parity Gate",
        "",
        f"Candidate mode: `{args.mode}`; baseline mode: `{args.baseline_mode}`.",
        "",
        "## Safety Gate",
        "",
        f"- Fast corpus gate: `{fast.get('stability_gate', {}).get('status', 'UNKNOWN')}`",
        f"- Long YOUtopia242 gate: `{long.get('stability_gate', {}).get('status', 'UNKNOWN')}`",
        f"- YOUtopia242 worst hotspot: `{to_float(you242, 'candidate_hotspot_worst_delta', 0.0):+.3f}` dB",
        f"- YOUtopia full/HF delta vs native: `{to_float(you, 'delta_full_vs_baseline', 0.0):+.3f}` / `{to_float(you, 'delta_hf_vs_baseline', 0.0):+.3f}` dB",
        f"- Safety status: `{'PASS' if hard_pass else 'FAIL'}`",
    ]
    if hard_failures:
        lines += ["", "Hard-fail reasons:"]
        for item in sorted(set(hard_failures)):
            lines.append(f"- `{item}`")

    lines += [
        "",
        "## Music Targets",
        "",
        f"- YOUtopia Sony distance: `{you_sony:.3f}` (target `<= {args.music_target_youtopia_sony_dist_max:.2f}`)",
        f"- Badlands Sony distance: `{bad_sony:.3f}` (target `<= {args.music_target_badlands_sony_dist_max:.2f}`)",
        f"- Music target status: `{'PASS' if music_target_pass else 'PENDING'}`",
        f"- Consecutive music-target passes: `{state['consecutive_music_target_passes']}`",
        "",
        "## Reports",
        "",
        f"- Fast markdown: `{fast_md}`",
        f"- Fast json: `{fast_json}`",
        f"- Long markdown: `{long_md}`",
        f"- Long json: `{long_json}`",
    ]
    text = "\n".join(lines) + "\n"
    args.out_md.write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote={args.out_md}")

    if not hard_pass:
        raise SystemExit(2)
    if args.enforce_music_targets and not music_target_pass:
        raise SystemExit(3)


if __name__ == "__main__":
    main()

