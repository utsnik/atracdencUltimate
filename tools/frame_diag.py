#!/usr/bin/env python3
"""Per-frame SNR analysis to distinguish allocation gaps from codec-structural gaps."""

import argparse
import csv
import sys
import numpy as np

def load_wav(path):
    try:
        import soundfile as sf
        data, sr = sf.read(path, always_2d=True)
        data = data.astype(np.float64)
        return data, sr
    except ImportError:
        pass
    from scipy.io import wavfile
    sr, data = wavfile.read(path)
    if data.ndim == 1:
        data = data[:, np.newaxis]
    data = data.astype(np.float64)
    if np.issubdtype(np.dtype('int16'), np.integer):
        maxval = np.iinfo(np.int16).max
        if data.max() > 1.0 or data.min() < -1.0:
            data = data / 32768.0
    return data, sr


def to_mono_frames(data, frame_size=1024):
    """Average channels and split into frames."""
    mono = data.mean(axis=1)
    n_frames = len(mono) // frame_size
    frames = mono[:n_frames * frame_size].reshape(n_frames, frame_size)
    return frames


def to_mono(data):
    return data.mean(axis=1)


def band_energy(spectrum, lo, hi):
    """Sum of squared magnitudes in bin range [lo, hi] inclusive."""
    return np.sum(np.abs(spectrum[lo:hi+1]) ** 2)


def frame_snr(orig_frame, decoded_frame):
    """Compute SNR in 3 bands. Returns (snr_low, snr_mid, snr_hf)."""
    orig_fft = np.fft.rfft(orig_frame)      # 513 bins for 1024-pt FFT
    noise_fft = np.fft.rfft(decoded_frame - orig_frame)

    bands = [(0, 85), (86, 340), (341, 511)]
    snrs = []
    for lo, hi in bands:
        sig_e = band_energy(orig_fft, lo, hi)
        noi_e = band_energy(noise_fft, lo, hi)
        snr = 10.0 * np.log10(sig_e / max(noi_e, 1e-12))
        snrs.append(snr)
    return tuple(snrs)


def best_lag(orig, dec, max_lag):
    max_lag = max(0, int(max_lag))
    if len(orig) == 0 or len(dec) == 0:
        return 0
    max_lag = min(max_lag, len(dec) - 1)
    if max_lag <= 0:
        return 0

    try:
        from scipy.signal import correlate, correlation_lags
        corr = correlate(dec, orig, mode='full', method='auto')
        lags = correlation_lags(len(dec), len(orig), mode='full')
        mask = (lags >= 0) & (lags <= max_lag)
        if not np.any(mask):
            return 0
        masked_corr = corr[mask]
        masked_lags = lags[mask]
        return int(masked_lags[np.argmax(masked_corr)])
    except Exception:
        pass

    best = 0
    best_val = -np.inf
    for lag in range(max_lag + 1):
        n = min(len(orig), len(dec) - lag)
        if n <= 0:
            break
        val = float(np.dot(orig[:n], dec[lag:lag + n]))
        if val > best_val:
            best_val = val
            best = lag
    return best


def main():
    parser = argparse.ArgumentParser(description='Per-frame SNR analysis for ATRAC3 decodes.')
    parser.add_argument('--orig', required=True, help='Original WAV')
    parser.add_argument('--sony', required=True, help='Sony decoded WAV')
    parser.add_argument('--ours', required=True, help='Our decoded WAV')
    parser.add_argument('--out', required=True, help='Output CSV path')
    parser.add_argument('--lag', type=int, default=None, help='Fixed lag (samples) applied to both decoded streams (default: auto)')
    parser.add_argument('--lag-sony', type=int, default=None, help='Fixed lag (samples) for Sony stream only (overrides --lag for Sony)')
    parser.add_argument('--lag-ours', type=int, default=None, help='Fixed lag (samples) for our stream only (overrides --lag for ours)')
    parser.add_argument('--max-lag', type=int, default=200, help='Maximum lag (samples) to search in auto mode (default: 200)')
    parser.add_argument('--worst', type=int, default=20, help='Number of worst frames to print (default: 20)')
    args = parser.parse_args()

    orig_data, orig_sr = load_wav(args.orig)
    sony_data, sony_sr = load_wav(args.sony)
    ours_data, ours_sr = load_wav(args.ours)

    FRAME = 1024

    orig_mono = to_mono(orig_data)
    sony_mono = to_mono(sony_data)
    ours_mono = to_mono(ours_data)

    if args.lag_sony is not None:
        lag_sony = int(args.lag_sony)
    elif args.lag is not None:
        lag_sony = int(args.lag)
    else:
        lag_sony = best_lag(orig_mono, sony_mono, args.max_lag)

    if args.lag_ours is not None:
        lag_ours = int(args.lag_ours)
    elif args.lag is not None:
        lag_ours = int(args.lag)
    else:
        lag_ours = best_lag(orig_mono, ours_mono, args.max_lag)

    rows = []
    max_orig_frames = len(orig_mono) // FRAME
    for f in range(max_orig_frames):
        orig_start = f * FRAME
        ours_start = orig_start + lag_ours
        sony_start = orig_start + lag_sony

        if orig_start < 0 or ours_start < 0 or sony_start < 0:
            continue
        if orig_start + FRAME > len(orig_mono):
            continue
        if ours_start + FRAME > len(ours_mono):
            continue
        if sony_start + FRAME > len(sony_mono):
            continue

        orig_frame = orig_mono[orig_start:orig_start + FRAME]
        ours_frame = ours_mono[ours_start:ours_start + FRAME]
        sony_frame = sony_mono[sony_start:sony_start + FRAME]

        s_low, s_mid, s_hf = frame_snr(orig_frame, sony_frame)
        o_low, o_mid, o_hf = frame_snr(orig_frame, ours_frame)
        d_low = o_low - s_low
        d_mid = o_mid - s_mid
        d_hf = o_hf - s_hf
        rows.append({
            'frame': f,
            'sony_snr_low': s_low,
            'sony_snr_mid': s_mid,
            'sony_snr_hf': s_hf,
            'ours_snr_low': o_low,
            'ours_snr_mid': o_mid,
            'ours_snr_hf': o_hf,
            'delta_low': d_low,
            'delta_mid': d_mid,
            'delta_hf': d_hf,
        })

    fieldnames = ['frame', 'sony_snr_low', 'sony_snr_mid', 'sony_snr_hf',
                  'ours_snr_low', 'ours_snr_mid', 'ours_snr_hf',
                  'delta_low', 'delta_mid', 'delta_hf']

    with open(args.out, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    n = len(rows)
    print(f"Lag ours vs orig: {lag_ours} samples")
    print(f"Lag sony vs orig: {lag_sony} samples")
    print(f"Wrote {n} frames to {args.out}")
    print()

    # Mean deltas
    d_lows = np.array([r['delta_low'] for r in rows])
    d_mids = np.array([r['delta_mid'] for r in rows])
    d_hfs  = np.array([r['delta_hf']  for r in rows])

    print("=== Mean delta per band (ours - sony, positive = we beat Sony) ===")
    print(f"  low  (0–3.6kHz):    {d_lows.mean():.3f} dB")
    print(f"  mid  (3.6–14.6kHz): {d_mids.mean():.3f} dB")
    print(f"  hf   (14.6–22kHz):  {d_hfs.mean():.3f} dB")
    print()

    N = args.worst

    # Worst N frames by delta_mid
    worst_mid_idx = np.argsort(d_mids)[:N]
    print(f"=== Worst {N} frames by delta_mid (largest underperformance in mid band) ===")
    print(f"{'frame':>7}  {'delta_low':>10}  {'delta_mid':>10}  {'delta_hf':>10}")
    for idx in worst_mid_idx:
        r = rows[idx]
        print(f"{r['frame']:>7}  {r['delta_low']:>10.3f}  {r['delta_mid']:>10.3f}  {r['delta_hf']:>10.3f}")
    print()

    # Worst N frames by delta_hf
    worst_hf_idx = np.argsort(d_hfs)[:N]
    print(f"=== Worst {N} frames by delta_hf (largest underperformance in hf band) ===")
    print(f"{'frame':>7}  {'delta_low':>10}  {'delta_mid':>10}  {'delta_hf':>10}")
    for idx in worst_hf_idx:
        r = rows[idx]
        print(f"{r['frame']:>7}  {r['delta_low']:>10.3f}  {r['delta_mid']:>10.3f}  {r['delta_hf']:>10.3f}")
    print()

    # Histogram of delta_full
    delta_full = (d_lows + d_mids + d_hfs) / 3.0
    buckets = [
        ('<-3',    delta_full < -3),
        ('-3..-2', (delta_full >= -3) & (delta_full < -2)),
        ('-2..-1', (delta_full >= -2) & (delta_full < -1)),
        ('-1..0',  (delta_full >= -1) & (delta_full < 0)),
        ('0..1',   (delta_full >= 0)  & (delta_full < 1)),
        ('>1',     delta_full >= 1),
    ]
    print("=== Histogram: frames by delta_full (mean of 3 bands) ===")
    for label, mask in buckets:
        count = int(mask.sum())
        bar = '#' * min(count, 60)
        print(f"  {label:>8}  {count:>6}  {bar}")
    print()


if __name__ == '__main__':
    main()
