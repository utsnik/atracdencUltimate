#!/usr/bin/env python3
"""
Generate and compare LP2 decision logs between two modes.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


TOP_FIELDS = {
    "frame",
    "ms_bytes_shift",
    "quality_v10_mode",
    "stability_mode",
    "gain_exp_mode",
    "baseline_profile",
    "bfu_idx_const",
    "js_enabled",
    "ms_ratio_raw",
    "ms_ratio",
    "ms_ratio_final",
    "ms_preserve_side",
    "ms_hold",
    "ms_continuity_clamped",
    "continuity_reason",
    "parity_bucket",
    "parity_bucket_reason",
}

CHANNEL_FIELDS = {
    "target_bits",
    "num_qmf_bands",
    "tonal_blocks",
    "allocation_mode",
    "num_bfu",
    "alloc_table",
    "gain_boost_per_band",
    "gain_continuity_clamped",
    "gain_weak_transient_suppressed",
    "hf_continuity_clamped",
    "gain_target_prev",
    "gain_target_cur",
    "gain_first_level_prev",
    "gain_first_level_cur",
    "gain_point_counts",
}


def parse_value(text: str):
    text = text.strip()
    if text in {"true", "false"}:
        return text == "true"
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [parse_value(part.strip()) for part in inner.split(",")]
    try:
        if any(ch in text for ch in (".", "e", "E")):
            return float(text)
        return int(text)
    except ValueError:
        return text


def parse_decision_log(path: Path) -> list[dict]:
    frames: list[dict] = []
    cur: dict | None = None
    cur_channel: dict | None = None
    in_channels = False

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line == "---":
            if cur is not None:
                frames.append(cur)
            cur = {"channels": []}
            cur_channel = None
            in_channels = False
            continue
        if cur is None or not line:
            continue
        if line == "channels:":
            in_channels = True
            cur_channel = None
            continue
        if in_channels and line.startswith("  - channel: "):
            cur_channel = {"channel": parse_value(line.split(": ", 1)[1])}
            cur["channels"].append(cur_channel)
            continue
        if in_channels and cur_channel is not None and line.startswith("    ") and ": " in line:
            key, value = line.strip().split(": ", 1)
            if key in CHANNEL_FIELDS:
                cur_channel[key] = parse_value(value)
            continue
        if not line.startswith("  ") and ": " in line:
            key, value = line.split(": ", 1)
            if key in TOP_FIELDS:
                cur[key] = parse_value(value)

    if cur is not None:
        frames.append(cur)
    return frames


def run_wrapper(wrapper: Path, enc: Path, legacy_enc: Path, at3tool: Path, input_wav: Path,
                mode: str, output_at3: Path, log_path: Path, start_frame: int, max_frames: int) -> None:
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
        str(input_wav),
        "-o",
        str(output_at3),
        "--mode",
        mode,
        "--start-frame",
        str(start_frame),
        "--max-frames",
        str(max_frames),
        "--decision-log",
        str(log_path),
        "--no-validate",
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"wrapper failed for mode {mode}:\n{p.stderr}")


def compare_frames(native_frames: list[dict], candidate_frames: list[dict]) -> tuple[list[str], list[str]]:
    summary: list[str] = []
    examples: list[str] = []
    common = min(len(native_frames), len(candidate_frames))
    top_changes = 0
    channel_changes = 0

    for idx in range(common):
        nf = native_frames[idx]
        cf = candidate_frames[idx]
        frame_no = nf.get("frame", idx)
        frame_top_changes: list[str] = []
        for key in sorted(TOP_FIELDS - {"frame"}):
            if nf.get(key) != cf.get(key):
                top_changes += 1
                frame_top_changes.append(f"{key}: {nf.get(key)} -> {cf.get(key)}")
        frame_channel_changes: list[str] = []
        for ch_idx, (nch, cch) in enumerate(zip(nf.get("channels", []), cf.get("channels", []))):
            for key in sorted(CHANNEL_FIELDS):
                if nch.get(key) != cch.get(key):
                    channel_changes += 1
                    frame_channel_changes.append(f"ch{ch_idx}.{key}: {nch.get(key)} -> {cch.get(key)}")
        if frame_top_changes or frame_channel_changes:
            if len(examples) < 20:
                parts = frame_top_changes[:4] + frame_channel_changes[:6]
                examples.append(f"- frame {frame_no}: " + "; ".join(parts))

    summary.append(f"- compared frames: {common}")
    summary.append(f"- top-level field changes: {top_changes}")
    summary.append(f"- channel field changes: {channel_changes}")
    return summary, examples


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    wrapper = Path(__file__).with_name("atracdenc_lp2.py")

    ap = argparse.ArgumentParser()
    ap.add_argument("--enc", required=True, type=Path)
    ap.add_argument("--legacy-enc", type=Path, default=repo_root / "build2" / "src" / "atracdenc.exe")
    ap.add_argument("--at3tool", type=Path, default=repo_root / "reverse" / "windows" / "at3tool.exe")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--native-mode", default="quality-v10-native")
    ap.add_argument("--candidate-mode", default="quality-v10-gain-exp")
    ap.add_argument("--start-frame", type=int, default=0)
    ap.add_argument("--max-frames", type=int, default=8)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="lp2_decision_log_diff_") as td:
        tmp = Path(td)
        native_log = tmp / "native.log"
        candidate_log = tmp / "candidate.log"
        run_wrapper(wrapper, args.enc, args.legacy_enc, args.at3tool, args.input,
                    args.native_mode, tmp / "native.at3.wav", native_log,
                    args.start_frame, args.max_frames)
        run_wrapper(wrapper, args.enc, args.legacy_enc, args.at3tool, args.input,
                    args.candidate_mode, tmp / "candidate.at3.wav", candidate_log,
                    args.start_frame, args.max_frames)

        native_frames = parse_decision_log(native_log)
        candidate_frames = parse_decision_log(candidate_log)

    summary, examples = compare_frames(native_frames, candidate_frames)
    lines = [
        "# LP2 Decision Log Diff",
        "",
        f"- input: `{args.input.name}`",
        f"- native mode: `{args.native_mode}`",
        f"- candidate mode: `{args.candidate_mode}`",
        f"- frame window: start `{args.start_frame}`, max `{args.max_frames}`",
        "",
        "## Summary",
        "",
        *summary,
        "",
        "## Sample Differences",
        "",
    ]
    if examples:
        lines.extend(examples)
    else:
        lines.append("- no decision-log differences detected in the requested frame window")
    text = "\n".join(lines) + "\n"

    if args.out_md is not None:
        args.out_md.write_text(text, encoding="utf-8")
        print(f"wrote={args.out_md}")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
