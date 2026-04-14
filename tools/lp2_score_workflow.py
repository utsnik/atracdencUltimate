#!/usr/bin/env python3
"""
Canonical LP2 score workflow.

For each sample in a corpus manifest:
- creates a fixed-duration source clip
- encodes candidate mode via the LP2 wrapper
- decodes candidate, Sony reference, and baseline
- reports objective metrics and hotspot frames
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
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


def read_wav(path: Path, max_frames: int = 0) -> tuple[int, int, list[list[float]]]:
    with wave.open(str(path), "rb") as w:
        sr = w.getframerate()
        ch = w.getnchannels()
        sw = w.getsampwidth()
        n = w.getnframes() if max_frames <= 0 else min(w.getnframes(), max_frames)
        data = w.readframes(n)
    if sw != 2:
        raise RuntimeError(f"{path}: only 16-bit PCM WAV supported")
    vals = struct.unpack("<" + "h" * (len(data) // 2), data)
    out = [[0.0] * (len(vals) // ch) for _ in range(ch)]
    idx = 0
    for i in range(len(out[0])):
        for c in range(ch):
            out[c][i] = float(vals[idx])
            idx += 1
    return sr, ch, out


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        if w.getframerate() <= 0:
            return 0.0
        return float(w.getnframes()) / float(w.getframerate())


def find_ffmpeg() -> str | None:
    env = os.environ.get("LP2_FFMPEG", "")
    if env and Path(env).exists():
        return env
    candidates = [
        "ffmpeg",
        r"C:\Users\Igland\Documents\NRK Downloader\ffmpeg.exe",
    ]
    for cand in candidates:
        try:
            p = subprocess.run([cand, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        except OSError:
            continue
        if p.returncode == 0:
            return cand
    return None


def write_wav_slice(src: Path, dst: Path, seconds: float) -> None:
    try:
        with wave.open(str(src), "rb") as r:
            params = r.getparams()
            needs_ffmpeg = params.framerate != 44100 or params.sampwidth != 2
            if not needs_ffmpeg:
                n = min(int(round(seconds * params.framerate)), params.nframes)
                frames = r.readframes(n)
                with wave.open(str(dst), "wb") as w:
                    w.setparams(params)
                    w.writeframes(frames)
                return
    except wave.Error:
        pass

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError(f"ffmpeg is required to normalize {src}")
    run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(src),
            "-t",
            f"{seconds:.3f}",
            "-ar",
            "44100",
            "-acodec",
            "pcm_s16le",
            str(dst),
        ]
    )


def mid_side(channels: list[list[float]]) -> tuple[list[float], list[float]]:
    if len(channels) == 1:
        x = channels[0]
        return x[:], [0.0] * len(x)
    n = min(len(channels[0]), len(channels[1]))
    mid = [(channels[0][i] + channels[1][i]) * 0.5 for i in range(n)]
    side = [(channels[0][i] - channels[1][i]) * 0.5 for i in range(n)]
    return mid, side


def snr_db(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n < 64:
        return -120.0
    a = a[:n]
    b = b[:n]
    sig = sum(x * x for x in a) / n
    noi = sum((a[i] - b[i]) ** 2 for i in range(n)) / n
    return 10.0 * math.log10((sig + 1e-20) / (noi + 1e-20))


def hp_diff(x: list[float]) -> list[float]:
    out = [0.0] * len(x)
    prev = 0.0
    for i, v in enumerate(x):
        out[i] = v - prev
        prev = v
    return out


def align(ref: list[float], dec: list[float], lag: int) -> tuple[list[float], list[float]]:
    if lag >= 0:
        r = ref[lag:]
        d = dec[: len(r)]
    else:
        d = dec[-lag:]
        r = ref[: len(d)]
    n = min(len(r), len(d))
    return r[:n], d[:n]


def best_lag(ref: list[float], dec: list[float], max_lag: int = 120) -> int:
    best = (-1e9, 0)
    for lag in range(-max_lag, max_lag + 1):
        r, d = align(ref, dec, lag)
        s = snr_db(r, d)
        if s > best[0]:
            best = (s, lag)
    return best[1]


def frame_snr(ref: list[float], dec: list[float], frame: int = 1024) -> list[float]:
    n = min(len(ref), len(dec))
    out: list[float] = []
    for i in range(0, n - frame + 1, frame):
        out.append(snr_db(ref[i : i + frame], dec[i : i + frame]))
    return out


def high_energy_db(x: list[float], frame: int = 1024) -> list[float]:
    hp = hp_diff(x)
    n = len(hp)
    out: list[float] = []
    for i in range(0, n - frame + 1, frame):
        seg = hp[i : i + frame]
        e = sum(v * v for v in seg) / frame
        out.append(10.0 * math.log10(e + 1e-20))
    return out


def percentile(vals: list[float], p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    idx = int((len(s) - 1) * p)
    return s[max(0, min(len(s) - 1, idx))]


def lowpass_1pole(x: list[float], sr: int, fc: float) -> list[float]:
    if not x:
        return []
    dt = 1.0 / float(sr)
    rc = 1.0 / (2.0 * math.pi * fc)
    a = dt / (rc + dt)
    y = [0.0] * len(x)
    yp = x[0]
    for i, v in enumerate(x):
        yp = yp + a * (v - yp)
        y[i] = yp
    return y


def highpass_1pole(x: list[float], sr: int, fc: float) -> list[float]:
    lp = lowpass_1pole(x, sr, fc)
    return [x[i] - lp[i] for i in range(min(len(x), len(lp)))]


def vocal_band(x: list[float], sr: int) -> list[float]:
    lp = lowpass_1pole(x, sr, 3400.0)
    return highpass_1pole(lp, sr, 300.0)


def rms_envelope(x: list[float], frame: int = 256, hop: int = 128) -> list[float]:
    out: list[float] = []
    for i in range(0, max(0, len(x) - frame + 1), hop):
        seg = x[i : i + frame]
        e = sum(v * v for v in seg) / frame
        out.append(math.sqrt(max(0.0, e)))
    return out


def vocal_error_ratio(ref: list[float], dec: list[float], sr: int) -> float:
    vr = vocal_band(ref, sr)
    vd = vocal_band(dec, sr)
    n = min(len(vr), len(vd))
    if n < 512:
        return 0.0
    err = [vr[i] - vd[i] for i in range(n)]
    sig_env = rms_envelope(vr)
    err_env = rms_envelope(err)
    m = min(len(sig_env), len(err_env))
    if m < 8:
        return 0.0
    vocal_rms = statistics.fmean(sig_env)
    # This proxy is only useful when there is real vocal-band content.
    # Otherwise it can explode on transient-only control material.
    if vocal_rms < 20.0:
        return 0.0
    norm = [err_env[i] / (sig_env[i] + 1e-9) for i in range(m)]
    return statistics.fmean(norm)


def stereo_metrics(ref_channels: list[list[float]], dec_channels: list[list[float]]) -> tuple[float, float]:
    ref_mid, ref_side = mid_side(ref_channels)
    dec_mid, dec_side = mid_side(dec_channels)
    n = min(len(ref_mid), len(dec_mid), len(ref_side), len(dec_side))
    ref_side = ref_side[:n]
    dec_side = dec_side[:n]
    side_snr = snr_db(ref_side, dec_side)
    ref_side_energy = sum(v * v for v in ref_side) / max(1, n)
    dec_side_energy = sum(v * v for v in dec_side) / max(1, n)
    side_retention_db = 10.0 * math.log10((dec_side_energy + 1e-20) / (ref_side_energy + 1e-20))
    return side_snr, side_retention_db


def compute_hotspots(
    ref_mid: list[float],
    base_mid: list[float],
    cand_mid: list[float],
    lag_b: int,
    lag_c: int,
    hf_energy_threshold_db: float = 18.0,
    limit: int = 8,
) -> list[dict[str, float]]:
    rb, bb = align(ref_mid, base_mid, lag_b)
    rc, cc = align(ref_mid, cand_mid, lag_c)
    n = min(len(rb), len(rc), len(bb), len(cc))
    r = rb[:n]
    b = bb[:n]
    c = cc[:n]
    snr_b = frame_snr(r, b)
    snr_c = frame_snr(r, c)
    hi = high_energy_db(r)
    m = min(len(snr_b), len(snr_c), len(hi))
    rows = []
    for i in range(m):
        if hi[i] < hf_energy_threshold_db:
            continue
        rows.append(
            {
                "frame": i,
                "delta": snr_c[i] - snr_b[i],
                "hf_energy_db": hi[i],
                "baseline_snr": snr_b[i],
                "candidate_snr": snr_c[i],
            }
        )
    rows.sort(key=lambda x: (x["delta"], -x["hf_energy_db"]))
    return rows[: max(1, limit)]


def score_mid(ref_mid: list[float], dec_mid: list[float], lag: int, sr: int) -> dict[str, float | None]:
    r, d = align(ref_mid, dec_mid, lag)
    seg = frame_snr(r, d)
    vocal_ratio = vocal_error_ratio(r, d, sr)
    return {
        "full": snr_db(r, d),
        "hf": snr_db(hp_diff(r), hp_diff(d)),
        "seg_p10": percentile(seg, 0.10),
        "seg_median": percentile(seg, 0.50),
        "vocal_err_ratio": vocal_ratio if vocal_ratio > 0.0 else None,
    }


def encode_with_wrapper(wrapper: Path, enc: Path, legacy_enc: Path, at3tool: Path, source: Path, output: Path, mode: str) -> None:
    run(
        [
            sys.executable,
            str(wrapper),
            "--enc",
            str(enc),
            "--legacy-enc",
            str(legacy_enc),
            "--at3tool",
            str(at3tool),
            "-i",
            str(source),
            "-o",
            str(output),
            "--mode",
            mode,
        ]
    )


def decode_at3(at3tool: Path, source: Path, output: Path) -> None:
    run([str(at3tool), "-d", str(source), str(output)])


def render_table(rows: list[dict[str, object]]) -> list[str]:
    def fmt_ratio(v: object) -> str:
        if v is None:
            return "n/a"
        return f"{float(v):.6f}"

    def fmt_gate(v: object) -> str:
        if v is None:
            return "n/a"
        return str(v)

    lines = [
        "| Sample | Candidate Full | Candidate HF | P10 | Median | Vocal Err | Side SNR | Side Ret (dB) | Dur Ratio | Hotspots | Worst Hotspot | Delta Full | Delta HF | Sony Dist | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {name} | {full:.3f} | {hf:.3f} | {p10:.3f} | {median:.3f} | {vocal} | {side_snr:.3f} | {side_ret:.3f} | {dur:.3f} | {hotspots} | {worst:+.3f} | {df:+.3f} | {dh:+.3f} | {sony:.3f} | {gate} |".format(
                name=row["name"],
                full=row["candidate_full"],
                hf=row["candidate_hf"],
                p10=row["candidate_seg_p10"],
                median=row["candidate_seg_median"],
                vocal=fmt_ratio(row["candidate_vocal_err_ratio"]),
                side_snr=row["candidate_side_snr"],
                side_ret=row["candidate_side_retention_db"],
                dur=row["candidate_duration_ratio"],
                hotspots=row["candidate_hotspot_count"],
                worst=row["candidate_hotspot_worst_delta"],
                df=row["delta_full_vs_baseline"],
                dh=row["delta_hf_vs_baseline"],
                sony=row["sony_distance"],
                gate=fmt_gate(row.get("gate_status")),
            )
        )
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enc", required=True, type=Path)
    ap.add_argument("--legacy-enc", required=True, type=Path)
    ap.add_argument("--at3tool", required=True, type=Path)
    ap.add_argument("--mode", default="quality-v10-native")
    ap.add_argument("--baseline-mode", default="quality-v10-frozen")
    ap.add_argument("--manifest", type=Path, default=Path(__file__).with_name("lp2_corpus_manifest.json"))
    ap.add_argument("--out-md", type=Path, default=None)
    ap.add_argument("--out-json", type=Path, default=None)
    ap.add_argument("--hotspot-limit", type=int, default=8)
    ap.add_argument("--hotspot-hf-threshold-db", type=float, default=18.0)
    ap.add_argument("--stability-gate", action="store_true")
    ap.add_argument("--gate-duration-ratio-min", type=float, default=0.95)
    ap.add_argument("--gate-youtopia-full-min", type=float, default=-0.10)
    ap.add_argument("--gate-youtopia-hf-min", type=float, default=-0.10)
    ap.add_argument("--gate-youtopia-worst-hotspot-min", type=float, default=-0.25)
    ap.add_argument("--gate-badlands-full-min", type=float, default=-0.50)
    ap.add_argument("--gate-improvement-epsilon", type=float, default=0.05)
    args = ap.parse_args()

    wrapper = Path(__file__).with_name("atracdenc_lp2.py")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    samples = manifest.get("samples", [])
    if not samples:
        raise RuntimeError("manifest has no samples")

    report_rows: list[dict[str, object]] = []
    report_hotspots: dict[str, list[dict[str, float]]] = {}
    hotspot_sections: list[str] = []
    gate_failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="lp2_score_workflow_") as td:
        tmp = Path(td)
        for sample in samples:
            name = sample["name"]
            source = Path(sample["source"])
            seconds = float(sample.get("seconds", 0.0))
            baseline_decode_override = sample.get("baseline_decode")

            clip = tmp / f"{name}.src.wav"
            if seconds > 0:
                write_wav_slice(source, clip, seconds)
            else:
                clip.write_bytes(source.read_bytes())

            cand_at3 = tmp / f"{name}.candidate.at3.wav"
            cand_dec = tmp / f"{name}.candidate.dec.wav"
            base_at3 = tmp / f"{name}.baseline.at3.wav"
            base_dec = tmp / f"{name}.baseline.dec.wav"
            sony_at3 = tmp / f"{name}.sony.at3"
            sony_dec = tmp / f"{name}.sony.dec.wav"

            encode_with_wrapper(wrapper, args.enc, args.legacy_enc, args.at3tool, clip, cand_at3, args.mode)
            decode_at3(args.at3tool, cand_at3, cand_dec)

            if baseline_decode_override:
                base_dec = Path(baseline_decode_override)
            else:
                encode_with_wrapper(wrapper, args.enc, args.legacy_enc, args.at3tool, clip, base_at3, args.baseline_mode)
                decode_at3(args.at3tool, base_at3, base_dec)

            run([str(args.at3tool), "-e", "-br", "132", str(clip), str(sony_at3)])
            decode_at3(args.at3tool, sony_at3, sony_dec)

            sr_ref, _, ref_ch = read_wav(clip)
            sr_c, _, cand_ch = read_wav(cand_dec)
            sr_b, _, base_ch = read_wav(base_dec, max_frames=int(round(seconds * sr_ref)) if seconds > 0 else 0)
            sr_s, _, sony_ch = read_wav(sony_dec)
            if not (sr_ref == sr_c == sr_b == sr_s):
                raise RuntimeError(f"{name}: sample rate mismatch")

            ref_mid, _ = mid_side(ref_ch)
            cand_mid, _ = mid_side(cand_ch)
            base_mid, _ = mid_side(base_ch)
            sony_mid, _ = mid_side(sony_ch)

            lag_c = best_lag(ref_mid, cand_mid)
            lag_b = best_lag(ref_mid, base_mid)
            lag_s = best_lag(ref_mid, sony_mid)

            cand_score = score_mid(ref_mid, cand_mid, lag_c, sr_ref)
            base_score = score_mid(ref_mid, base_mid, lag_b, sr_ref)
            sony_score = score_mid(ref_mid, sony_mid, lag_s, sr_ref)

            cand_side_snr, cand_side_ret = stereo_metrics(ref_ch, cand_ch)
            base_side_snr, base_side_ret = stereo_metrics(ref_ch, base_ch)
            sony_side_snr, sony_side_ret = stereo_metrics(ref_ch, sony_ch)
            candidate_duration_ratio = wav_duration(cand_dec) / max(1e-9, wav_duration(clip))
            hotspots = compute_hotspots(
                ref_mid,
                base_mid,
                cand_mid,
                lag_b,
                lag_c,
                hf_energy_threshold_db=args.hotspot_hf_threshold_db,
                limit=args.hotspot_limit,
            )
            hotspot_count = len(hotspots)
            hotspot_worst_delta = min((h["delta"] for h in hotspots), default=0.0)
            report_hotspots[name] = hotspots

            report_rows.append(
                {
                    "name": name,
                    "candidate_full": cand_score["full"],
                    "candidate_hf": cand_score["hf"],
                    "candidate_seg_p10": cand_score["seg_p10"],
                    "candidate_seg_median": cand_score["seg_median"],
                    "candidate_vocal_err_ratio": cand_score["vocal_err_ratio"],
                    "candidate_side_snr": cand_side_snr,
                    "candidate_side_retention_db": cand_side_ret,
                    "candidate_duration_ratio": candidate_duration_ratio,
                    "candidate_hotspot_count": hotspot_count,
                    "candidate_hotspot_worst_delta": hotspot_worst_delta,
                    "delta_full_vs_baseline": cand_score["full"] - base_score["full"],
                    "delta_hf_vs_baseline": cand_score["hf"] - base_score["hf"],
                    "delta_seg_p10_vs_baseline": cand_score["seg_p10"] - base_score["seg_p10"],
                    "delta_vocal_vs_baseline": None
                    if cand_score["vocal_err_ratio"] is None or base_score["vocal_err_ratio"] is None
                    else cand_score["vocal_err_ratio"] - base_score["vocal_err_ratio"],
                    "delta_side_snr_vs_baseline": cand_side_snr - base_side_snr,
                    "delta_side_retention_vs_baseline": cand_side_ret - base_side_ret,
                    "sony_distance": ((cand_score["full"] - sony_score["full"]) ** 2 + (cand_score["hf"] - sony_score["hf"]) ** 2) ** 0.5,
                    "sony_side_distance": ((cand_side_snr - sony_side_snr) ** 2 + (cand_side_ret - sony_side_ret) ** 2) ** 0.5,
                    "gate_status": None,
                }
            )

            hotspot_sections.append(f"### {name}")
            hotspot_sections.append("")
            hotspot_sections.append(
                "Baseline full `{:.3f}`, HF `{:.3f}`; candidate full `{:.3f}`, HF `{:.3f}`; Sony full `{:.3f}`, HF `{:.3f}`.".format(
                    base_score["full"], base_score["hf"], cand_score["full"], cand_score["hf"], sony_score["full"], sony_score["hf"]
                )
            )
            hotspot_sections.append("")
            if hotspots:
                hotspot_sections.append("| Frame | Delta vs Baseline | HF Energy (dB) | Baseline SNR | Candidate SNR |")
                hotspot_sections.append("|---|---:|---:|---:|---:|")
                for h in hotspots:
                    hotspot_sections.append(
                        "| {frame} | {delta:+.3f} | {hf_energy_db:.2f} | {baseline_snr:.3f} | {candidate_snr:.3f} |".format(**h)
                    )
            else:
                hotspot_sections.append("No hotspot frames over the HF-energy threshold.")
            hotspot_sections.append("")

    if args.stability_gate:
        for row in report_rows:
            name = str(row["name"])
            checks: list[bool] = []
            reasons: list[str] = []
            duration_ok = float(row["candidate_duration_ratio"]) >= args.gate_duration_ratio_min
            checks.append(duration_ok)
            if not duration_ok:
                reasons.append("duration")
            if name == "YOUtopia":
                full_ok = float(row["delta_full_vs_baseline"]) >= args.gate_youtopia_full_min
                hf_ok = float(row["delta_hf_vs_baseline"]) >= args.gate_youtopia_hf_min
                hotspot_ok = float(row["candidate_hotspot_worst_delta"]) >= args.gate_youtopia_worst_hotspot_min
                checks.extend([full_ok, hf_ok, hotspot_ok])
                if not full_ok:
                    reasons.append("youtopia_full")
                if not hf_ok:
                    reasons.append("youtopia_hf")
                if not hotspot_ok:
                    reasons.append("youtopia_hotspot")
            elif name == "chirp_wait":
                full_ok = float(row["delta_full_vs_baseline"]) >= -args.gate_improvement_epsilon
                hf_ok = float(row["delta_hf_vs_baseline"]) >= -args.gate_improvement_epsilon
                hotspot_ok = float(row["candidate_hotspot_worst_delta"]) >= -args.gate_improvement_epsilon
                checks.extend([full_ok, hf_ok, hotspot_ok])
                if not full_ok:
                    reasons.append("chirp_full")
                if not hf_ok:
                    reasons.append("chirp_hf")
                if not hotspot_ok:
                    reasons.append("chirp_hotspot")
            elif name == "tmp_transient":
                full_ok = float(row["delta_full_vs_baseline"]) >= -args.gate_improvement_epsilon
                hf_ok = float(row["delta_hf_vs_baseline"]) >= -args.gate_improvement_epsilon
                hotspot_ok = float(row["candidate_hotspot_worst_delta"]) >= -args.gate_improvement_epsilon
                checks.extend([full_ok, hf_ok, hotspot_ok])
                if not full_ok:
                    reasons.append("transient_full")
                if not hf_ok:
                    reasons.append("transient_hf")
                if not hotspot_ok:
                    reasons.append("transient_hotspot")
            elif name == "Badlands":
                full_ok = float(row["delta_full_vs_baseline"]) >= args.gate_badlands_full_min
                hf_ok = float(row["delta_hf_vs_baseline"]) >= -args.gate_improvement_epsilon
                hotspot_ok = float(row["candidate_hotspot_worst_delta"]) >= -args.gate_improvement_epsilon
                checks.extend([full_ok, hf_ok, hotspot_ok])
                if not full_ok:
                    reasons.append("badlands_full")
                if not hf_ok:
                    reasons.append("badlands_hf")
                if not hotspot_ok:
                    reasons.append("badlands_hotspot")
            gate_ok = all(checks)
            row["gate_status"] = "PASS" if gate_ok else "FAIL"
            if not gate_ok:
                gate_failures.append(f"{name}: {', '.join(reasons)}")

    lines: list[str] = []
    lines.append("# LP2 Score Workflow")
    lines.append("")
    lines.append(f"Candidate mode: `{args.mode}`; baseline mode: `{args.baseline_mode}`.")
    lines.append("")
    lines.extend(render_table(report_rows))
    if args.stability_gate:
        lines.append("")
        lines.append("## Stability Gate")
        lines.append("")
        if gate_failures:
            lines.append("FAIL")
            lines.append("")
            for item in gate_failures:
                lines.append(f"- {item}")
        else:
            lines.append("PASS")
    lines.append("")
    lines.append("## Hotspots")
    lines.append("")
    lines.extend(hotspot_sections)
    lines.append("")

    text = "\n".join(lines)
    print(text)
    if args.out_md is not None:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(text, encoding="utf-8")
        print(f"wrote={args.out_md}")
    if args.out_json is not None:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "mode": args.mode,
            "baseline_mode": args.baseline_mode,
            "manifest": str(args.manifest),
            "hotspot_limit": int(args.hotspot_limit),
            "hotspot_hf_threshold_db": float(args.hotspot_hf_threshold_db),
            "rows": report_rows,
            "hotspots": report_hotspots,
            "stability_gate": {
                "enabled": bool(args.stability_gate),
                "failures": gate_failures,
                "status": "FAIL" if gate_failures else "PASS",
            },
        }
        args.out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"wrote={args.out_json}")
    if args.stability_gate and gate_failures:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
