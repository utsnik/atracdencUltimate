#!/usr/bin/env python3
"""
Convenience CLI for LP2 workflows.

Examples:
  python tools/atracdenc_lp2.py --enc build_work/src/atracdenc.exe --legacy-enc build2/src/atracdenc.exe -i YOUtopia_source.wav -o out.at3.wav
  python tools/atracdenc_lp2.py --enc build2/src/atracdenc.exe -i YOUtopia.wav -o out.at3.wav --mode lp2-adaptive
  python tools/atracdenc_lp2.py --enc build2/src/atracdenc.exe -i YOUtopia.wav -o out.at3.wav --mode default
  python tools/atracdenc_lp2.py --enc build2/src/atracdenc.exe -i YOUtopia.wav -o out.at3.wav --mode bfu32-ml
  python tools/atracdenc_lp2.py --enc build2/src/atracdenc.exe -i YOUtopia_source.wav -o out.at3.wav --mode ml-air
  python tools/atracdenc_lp2.py --enc build2/src/atracdenc.exe --at3tool reverse/windows/at3tool.exe -i YOUtopia_source.wav -o out.at3.wav --mode ml-decision
  python tools/atracdenc_lp2.py --enc build2/src/atracdenc.exe --at3tool reverse/windows/at3tool.exe -i YOUtopia_source.wav -o out.at3.wav --mode ml-decision-air
  python tools/atracdenc_lp2.py --enc build2/src/atracdenc.exe --at3tool reverse/windows/at3tool.exe -i YOUtopia_source.wav -o out.at3.wav --mode ml-decision-sharp
  python tools/atracdenc_lp2.py --enc build2/src/atracdenc.exe --at3tool reverse/windows/at3tool.exe -i YOUtopia_source.wav -o out.at3.wav --mode ml-decision-parity
  python tools/atracdenc_lp2.py --enc build2/src/atracdenc.exe -i YOUtopia_source.wav -o out.at3.wav --mode parity
  python tools/atracdenc_lp2.py --enc build2/src/atracdenc.exe -i YOUtopia_source.wav -o out.at3.wav --mode quality-v10
  python tools/atracdenc_lp2.py --enc build_work/src/atracdenc.exe -i YOUtopia_source.wav -o out.at3.wav --mode quality-v10-native
  python tools/atracdenc_lp2.py --enc build_work/src/atracdenc.exe -i YOUtopia_source.wav -o out.at3.wav --mode quality-v10-stable
  python tools/atracdenc_lp2.py --enc build_work/src/atracdenc.exe -i YOUtopia_source.wav -o out.at3.wav --mode quality-v10-stereo-balance
  python tools/atracdenc_lp2.py --enc build_work/src/atracdenc.exe -i YOUtopia_source.wav -o out.at3.wav --mode quality-v10-stereo-exp
  python tools/atracdenc_lp2.py --enc build_work/src/atracdenc.exe -i YOUtopia_source.wav -o out.at3.wav --mode quality-v10-gain-exp
  python tools/atracdenc_lp2.py --enc build_work/src/atracdenc.exe -i YOUtopia_source.wav -o out.at3.wav --mode quality-v10-gain-exp2
  python tools/atracdenc_lp2.py --enc build_work/src/atracdenc.exe --legacy-enc build2/src/atracdenc.exe -i YOUtopia_source.wav -o out.at3.wav --mode quality-v10-frozen

Notes:
  - Default mode is now `quality-v10-frozen` (stability-first baseline).
  - Canonical native baseline mode is `quality-v10-native`.
  - Stability tuning mode is `quality-v10-stable`.
  - Non-JS stereo balancing experiment mode is `quality-v10-stereo-balance`.
  - Joint-stereo experiment mode is `quality-v10-stereo-exp`.
  - Narrow gain experiment mode is `quality-v10-gain-exp`.
  - High-band gain experiment mode is `quality-v10-gain-exp2`.
  - Non-frozen modes are validated by decoding with at3tool; on failure,
    the wrapper falls back to `quality-v10-frozen` unless `--no-fallback`.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import wave
from pathlib import Path


def run(cmd: list[str]) -> int:
    p = subprocess.run(cmd)
    return p.returncode


def read_wav_duration_seconds(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        fr = w.getframerate()
        n = w.getnframes()
    if fr <= 0:
        return 0.0
    return float(n) / float(fr)


def validate_with_at3tool(input_wav: Path, output_at3: Path, at3tool: Path, min_ratio: float) -> tuple[bool, str]:
    if not output_at3.exists():
        return False, "encoded output file missing"
    if output_at3.stat().st_size < 4096:
        return False, f"encoded output too small ({output_at3.stat().st_size} bytes)"
    try:
        in_sec = read_wav_duration_seconds(input_wav)
    except Exception:
        return True, "input duration unavailable; decode validation skipped"

    with tempfile.TemporaryDirectory(prefix="lp2_validate_") as td:
        dec = Path(td) / "decoded.wav"
        rc = run([str(at3tool), "-d", str(output_at3), str(dec)])
        if rc != 0:
            return False, f"at3tool decode failed (exit {rc})"
        try:
            out_sec = read_wav_duration_seconds(dec)
        except Exception:
            return False, "decoded wav unreadable"

    if in_sec <= 0.0:
        return True, "input duration unavailable; decode validation skipped"
    ratio = out_sec / in_sec
    if ratio < min_ratio:
        return False, "decoded duration too short ({:.3f}s vs {:.3f}s, ratio {:.3f} < {:.3f})".format(
            out_sec, in_sec, ratio, min_ratio
        )
    return True, "decode ok ({:.3f}s vs {:.3f}s, ratio {:.3f})".format(out_sec, in_sec, ratio)


def run_quality_v10_frozen(args: argparse.Namespace) -> int:
    cmd = [str(args.legacy_enc), "-e", "atrac3", "-i", str(args.input), "-o", str(args.output), "--bitrate", "132"]
    rc = run(cmd)
    if rc != 0:
        return rc
    fix_script = Path(__file__).with_name("fix_at3_riff_header.py")
    return run([sys.executable, str(fix_script), str(args.output), "--min-size", "1000"])


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument("--enc", required=True, type=Path, help="path to atracdenc.exe")
    ap.add_argument(
        "--legacy-enc",
        type=Path,
        default=repo_root / "build2" / "src" / "atracdenc.exe",
        help="path to known-good legacy encoder binary (used by --mode quality-v10-frozen)",
    )
    ap.add_argument(
        "--at3tool",
        type=Path,
        default=repo_root / "reverse" / "windows" / "at3tool.exe",
        help="path to at3tool.exe (used by --mode ml-decision)",
    )
    ap.add_argument("-i", "--input", required=True, type=Path, help="input wav")
    ap.add_argument("-o", "--output", required=True, type=Path, help="output at3/at3.wav")
    ap.add_argument("--start-frame", type=int, default=0, help="start frame for parity/log analysis window")
    ap.add_argument("--max-frames", type=int, default=0, help="max frames in parity/log analysis window (0=all)")
    ap.add_argument("--decision-log", type=Path, default=None, help="optional decision log path")
    ap.add_argument("--parity-search", action="store_true", help="enable experimental local candidate search in parity mode")
    ap.add_argument("--no-validate", action="store_true", help="skip decode validation with at3tool")
    ap.add_argument(
        "--min-duration-ratio",
        type=float,
        default=0.95,
        help="minimum decoded/input duration ratio for validation",
    )
    ap.add_argument(
        "--no-fallback",
        action="store_true",
        help="do not auto-fallback to quality-v10-frozen when validation fails",
    )
    ap.add_argument(
        "--mode",
        default="quality-v10-frozen",
        choices=[
            "lp2-adaptive",
            "default",
            "ml",
            "bfu32-ml",
            "ml-air",
            "ml-nogain",
            "ml-decision",
            "ml-decision-air",
            "ml-decision-sharp",
            "ml-decision-parity",
            "parity",
            "quality-v10",
            "quality-v10-native",
            "quality-v10-stable",
            "quality-v10-stereo-balance",
            "quality-v10-stereo-exp",
            "quality-v10-gain-exp",
            "quality-v10-gain-exp2",
            "quality-v10-frozen",
        ],
        help="encoding mode",
    )
    args = ap.parse_args()

    if args.mode == "lp2-adaptive":
        script = Path(__file__).with_name("lp2_adaptive_encode.py")
        rc = run(
            [
                sys.executable,
                str(script),
                "--enc",
                str(args.enc),
                "-i",
                str(args.input),
                "-o",
                str(args.output),
            ]
        )
        raise SystemExit(rc)

    if args.mode == "ml-air":
        script = Path(__file__).with_name("lp2_precondition_encode.py")
        rc = run(
            [
                sys.executable,
                str(script),
                "--enc",
                str(args.enc),
                "-i",
                str(args.input),
                "-o",
                str(args.output),
            ]
        )
        raise SystemExit(rc)

    if args.mode in {"ml-decision", "ml-decision-air", "ml-decision-sharp", "ml-decision-parity"}:
        script = Path(__file__).with_name("lp2_decision_encode.py")
        cmd = [
            sys.executable,
            str(script),
            "--enc",
            str(args.enc),
            "--at3tool",
            str(args.at3tool),
            "-i",
            str(args.input),
            "-o",
            str(args.output),
        ]
        if args.mode in {"ml-decision-air", "ml-decision-sharp", "ml-decision-parity"}:
            cmd.append("--include-air")
        if args.mode in {"ml-decision-sharp", "ml-decision-parity"}:
            cmd.extend(
                [
                    "--include-hf-bfu",
                ]
            )
        if args.mode == "ml-decision-sharp":
            cmd.extend(
                [
                    "--full-guard-db",
                    "1.00",
                    "--full-weight",
                    "1.60",
                    "--hf-weight",
                    "1.80",
                ]
            )
        if args.mode == "ml-decision-parity":
            cmd.extend(["--target-sony", "--sony-full-weight", "1.00", "--sony-hf-weight", "1.40"])
        rc = run(cmd)
        raise SystemExit(rc)

    if args.mode == "quality-v10-frozen":
        rc = run_quality_v10_frozen(args)
        raise SystemExit(rc)

    mode_flags = {
        "default": [],
        "ml": ["--ml-hints"],
        "bfu32-ml": ["--bfuidxconst", "32", "--ml-hints"],
        "ml-nogain": ["--ml-hints", "--nogaincontrol"],
        "parity": ["--parity"],
        "quality-v10": ["--parity", "--quality-v10"],
        "quality-v10-native": ["--quality-v10", "--bfuidxconst", "28", "--nogaincontrol"],
        "quality-v10-stable": ["--quality-v10", "--quality-v10-stable", "--parity", "--bfuidxconst", "28", "--nogaincontrol"],
        "quality-v10-stereo-balance": ["--quality-v10", "--quality-v10-stable", "--parity", "--stereo-balance-exp", "--bfuidxconst", "28", "--nogaincontrol"],
        "quality-v10-stereo-exp": ["--quality-v10", "--quality-v10-stable", "--parity", "--stereo-exp", "--bfuidxconst", "28", "--nogaincontrol"],
        "quality-v10-gain-exp": ["--quality-v10", "--quality-v10-stable", "--gain-exp", "--parity", "--bfuidxconst", "28"],
        "quality-v10-gain-exp2": ["--quality-v10", "--quality-v10-stable", "--gain-exp2", "--parity", "--bfuidxconst", "28"],
    }[args.mode]

    cmd = [str(args.enc), "-e", "atrac3", "-i", str(args.input), "-o", str(args.output), "--bitrate", "132"] + mode_flags
    if args.start_frame > 0:
        cmd += ["--start-frame", str(args.start_frame)]
    if args.max_frames > 0:
        cmd += ["--max-frames", str(args.max_frames)]
    if args.decision_log is not None:
        cmd += ["--decision-log", str(args.decision_log)]
    if args.parity_search:
        cmd += ["--parity-search"]
    rc = run(cmd)
    if rc != 0:
        raise SystemExit(rc)

    if args.no_validate:
        raise SystemExit(0)

    ok, msg = validate_with_at3tool(args.input, args.output, args.at3tool, args.min_duration_ratio)
    print(f"validation: {msg}")
    if ok:
        raise SystemExit(0)

    if args.no_fallback:
        raise SystemExit(2)

    print("validation failed; falling back to quality-v10-frozen baseline")
    rc = run_quality_v10_frozen(args)
    if rc != 0:
        raise SystemExit(rc)
    ok2, msg2 = validate_with_at3tool(args.input, args.output, args.at3tool, args.min_duration_ratio)
    print(f"fallback validation: {msg2}")
    raise SystemExit(0 if ok2 else 3)


if __name__ == "__main__":
    main()
