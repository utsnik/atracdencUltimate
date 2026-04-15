#!/usr/bin/env python3
"""
Perceptual-proxy metrics for LP2 decode comparisons.

These are still proxies (not a formal MOS model), but they catch
"underwater/rolling" regressions better than global SNR alone.
"""

from __future__ import annotations

import argparse
import math
import statistics
import struct
import wave
from pathlib import Path


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


def mid_channel(channels: list[list[float]]) -> list[float]:
    if len(channels) == 1:
        return channels[0]
    n = min(len(ch) for ch in channels)
    return [(channels[0][i] + channels[1][i]) * 0.5 for i in range(n)]


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


def best_lag(ref: list[float], dec: list[float], max_lag: int) -> int:
    best = (-1e9, 0)
    for lag in range(-max_lag, max_lag + 1):
        r, d = align(ref, dec, lag)
        s = snr_db(r, d)
        if s > best[0]:
            best = (s, lag)
    return best[1]


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
    # Approximate 300..3400 Hz voice band.
    lp = lowpass_1pole(x, sr, 3400.0)
    return highpass_1pole(lp, sr, 300.0)


def frame_snr(ref: list[float], dec: list[float], frame: int = 1024) -> list[float]:
    n = min(len(ref), len(dec))
    out: list[float] = []
    for i in range(0, n - frame + 1, frame):
        out.append(snr_db(ref[i : i + frame], dec[i : i + frame]))
    return out


def rms_envelope(x: list[float], frame: int = 256, hop: int = 128) -> list[float]:
    out: list[float] = []
    for i in range(0, max(0, len(x) - frame + 1), hop):
        seg = x[i : i + frame]
        e = sum(v * v for v in seg) / frame
        out.append(math.sqrt(max(0.0, e)))
    return out


def percentile(vals: list[float], p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    idx = int((len(s) - 1) * p)
    return s[max(0, min(len(s) - 1, idx))]


def vocal_error_features(ref: list[float], dec: list[float], sr: int) -> tuple[float, float]:
    vr = vocal_band(ref, sr)
    vd = vocal_band(dec, sr)
    n = min(len(vr), len(vd))
    if n < 512:
        return 0.0, 0.0
    err = [vr[i] - vd[i] for i in range(n)]
    sig_env = rms_envelope(vr)
    err_env = rms_envelope(err)
    m = min(len(sig_env), len(err_env))
    if m < 8:
        return 0.0, 0.0
    norm = [err_env[i] / (sig_env[i] + 1e-9) for i in range(m)]
    dif = [norm[i] - norm[i - 1] for i in range(1, m)]
    if not dif:
        return statistics.fmean(norm), 0.0
    # mean error ratio: higher is clearly worse.
    mean_ratio = statistics.fmean(norm)
    # modulation index: relative fluctuation of error ratio (heuristic).
    mod_idx = statistics.pstdev(dif) / (mean_ratio + 1e-9)
    return mean_ratio, mod_idx


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True, type=Path)
    ap.add_argument("--base", required=True, type=Path)
    ap.add_argument("--cand", required=True, type=Path)
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--max-lag", type=int, default=120)
    ap.add_argument("--lag", type=int, default=None)
    ap.add_argument("--lag-base", type=int, default=None)
    ap.add_argument("--lag-cand", type=int, default=None)
    ap.add_argument("--label-base", default="base")
    ap.add_argument("--label-cand", default="cand")
    args = ap.parse_args()

    max_frames = 0 if args.seconds <= 0 else int(round(args.seconds * 44100.0))
    sr_r, _, ref_ch = read_wav(args.ref, max_frames=max_frames)
    sr_b, _, base_ch = read_wav(args.base, max_frames=max_frames)
    sr_c, _, cand_ch = read_wav(args.cand, max_frames=max_frames)
    if not (sr_r == sr_b == sr_c):
        raise RuntimeError("sample-rate mismatch")

    ref = mid_channel(ref_ch)
    base = mid_channel(base_ch)
    cand = mid_channel(cand_ch)

    if args.lag_base is not None:
        lag_b = args.lag_base
    elif args.lag is not None:
        lag_b = args.lag
    else:
        lag_b = best_lag(ref, base, args.max_lag)

    if args.lag_cand is not None:
        lag_c = args.lag_cand
    elif args.lag is not None:
        lag_c = args.lag
    else:
        lag_c = best_lag(ref, cand, args.max_lag)

    rb, bb = align(ref, base, lag_b)
    rc, cc = align(ref, cand, lag_c)
    n = min(len(rb), len(rc), len(bb), len(cc))
    r = rb[:n]
    b = bb[:n]
    c = cc[:n]

    full_b = snr_db(r, b)
    full_c = snr_db(r, c)
    hf_b = snr_db(hp_diff(r), hp_diff(b))
    hf_c = snr_db(hp_diff(r), hp_diff(c))

    seg_b = frame_snr(r, b)
    seg_c = frame_snr(r, c)
    p10_b = percentile(seg_b, 0.10)
    p10_c = percentile(seg_c, 0.10)
    med_b = percentile(seg_b, 0.50)
    med_c = percentile(seg_c, 0.50)

    ver_b, mod_b = vocal_error_features(r, b, sr_r)
    ver_c, mod_c = vocal_error_features(r, c, sr_r)

    print(f"lag_{args.label_base}={lag_b}")
    print(f"lag_{args.label_cand}={lag_c}")
    print(f"full_snr_{args.label_base}={full_b:.3f}")
    print(f"full_snr_{args.label_cand}={full_c:.3f}")
    print(f"hf_snr_{args.label_base}={hf_b:.3f}")
    print(f"hf_snr_{args.label_cand}={hf_c:.3f}")
    print(f"seg_snr_p10_{args.label_base}={p10_b:.3f}")
    print(f"seg_snr_p10_{args.label_cand}={p10_c:.3f}")
    print(f"seg_snr_median_{args.label_base}={med_b:.3f}")
    print(f"seg_snr_median_{args.label_cand}={med_c:.3f}")
    print(f"vocal_err_ratio_{args.label_base}={ver_b:.6f}")
    print(f"vocal_err_ratio_{args.label_cand}={ver_c:.6f}")
    print(f"vocal_mod_idx_{args.label_base}={mod_b:.6f}")
    print(f"vocal_mod_idx_{args.label_cand}={mod_c:.6f}")
    print(f"delta_full={full_c - full_b:+.3f}")
    print(f"delta_hf={hf_c - hf_b:+.3f}")
    print(f"delta_seg_p10={p10_c - p10_b:+.3f}")
    print(f"delta_seg_median={med_c - med_b:+.3f}")
    print(f"delta_vocal_err_ratio={ver_c - ver_b:+.6f}")
    # Modulation index is heuristic and not yet threshold-calibrated.
    print(f"delta_vocal_mod_idx={mod_c - mod_b:+.6f}")


if __name__ == "__main__":
    main()
