import argparse
import json
from pathlib import Path
import wave

import numpy as np


def read_wav_mono(path):
    with wave.open(str(path), "rb") as wf:
        n = wf.getnframes()
        ch = wf.getnchannels()
        sr = wf.getframerate()
        sampwidth = wf.getsampwidth()
        data = wf.readframes(n)
    if sampwidth != 2:
        raise ValueError(f"Expected 16-bit PCM, got {sampwidth * 8}-bit")
    pcm = np.frombuffer(data, dtype=np.int16)
    if ch > 1:
        pcm = pcm.reshape(-1, ch).mean(axis=1)
    return pcm.astype(np.float32) / 32768.0, sr


def snr_db(ref, test):
    min_len = min(len(ref), len(test))
    ref = ref[:min_len]
    test = test[:min_len]
    noise = ref - test
    num = np.mean(ref ** 2)
    den = np.mean(noise ** 2) + 1e-12
    return 10 * np.log10(num / den)


def best_alignment(ref, test, max_shift=4096):
    n = min(len(ref), len(test), 65536)
    if n < 1024:
        return 0
    a = ref[:n]
    b = test[:n]

    size = 1
    while size < 2 * n:
        size *= 2
    fa = np.fft.rfft(a, size)
    fb = np.fft.rfft(b, size)
    corr = np.fft.irfft(fa * np.conj(fb), size)

    corr_lin = np.concatenate((corr[:n], corr[-(n - 1):]))
    lags = np.concatenate((np.arange(0, n), np.arange(-(n - 1), 0)))
    mask = (lags >= -max_shift) & (lags <= max_shift)
    lags = lags[mask]
    corr_lin = corr_lin[mask]
    return int(lags[int(np.argmax(corr_lin))])


def align_to(ref, test, lag):
    if lag >= 0:
        r = ref[lag:]
        t = test[:len(r)]
    else:
        r = ref[:len(ref) + lag]
        t = test[-lag: -lag + len(r)]
    return r, t


def stft_mag(x, n_fft=2048, hop=512):
    if len(x) < n_fft:
        return np.zeros((0, n_fft // 2 + 1), dtype=np.float32)
    frames = 1 + (len(x) - n_fft) // hop
    window = np.hanning(n_fft).astype(np.float32)
    mags = np.empty((frames, n_fft // 2 + 1), dtype=np.float32)
    for i in range(frames):
        start = i * hop
        seg = x[start:start + n_fft] * window
        spec = np.fft.rfft(seg)
        mags[i, :] = np.abs(spec)
    return mags


def build_dataset(input_wav, at3tool_wav, atracdenc_wav, n_fft=2048, hop=512):
    ref, sr = read_wav_mono(input_wav)
    ttool, sr2 = read_wav_mono(at3tool_wav)
    atrac, sr3 = read_wav_mono(atracdenc_wav)
    if sr != sr2 or sr != sr3:
        raise ValueError("Sample rate mismatch between inputs")

    lag_tool = best_alignment(ref, ttool)
    lag_atrac = best_alignment(ref, atrac)
    ref1, ttool1 = align_to(ref, ttool, lag_tool)
    ref2, atrac1 = align_to(ref, atrac, lag_atrac)
    min_len = min(len(ref1), len(ref2), len(ttool1), len(atrac1))
    ref1 = ref1[:min_len]
    ttool1 = ttool1[:min_len]
    atrac1 = atrac1[:min_len]

    # Feature: log magnitude of input
    X = stft_mag(ref1, n_fft=n_fft, hop=hop)
    # Target: log magnitude difference (at3tool - atracdenc)
    Ttool = stft_mag(ttool1, n_fft=n_fft, hop=hop)
    Tatrac = stft_mag(atrac1, n_fft=n_fft, hop=hop)
    frames = min(X.shape[0], Ttool.shape[0], Tatrac.shape[0])
    X = X[:frames]
    Ttool = Ttool[:frames]
    Tatrac = Tatrac[:frames]

    eps = 1e-8
    feat = np.log10(X + eps)
    target = np.log10(Ttool + eps) - np.log10(Tatrac + eps)

    metrics = {
        "lag_tool": int(lag_tool),
        "lag_atrac": int(lag_atrac),
        "snr_at3tool": float(snr_db(ref1, ttool1)),
        "snr_atrac": float(snr_db(ref1, atrac1)),
    }
    return feat.astype(np.float32), target.astype(np.float32), metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--mask", type=int, default=2)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-fft", type=int, default=2048)
    ap.add_argument("--hop", type=int, default=512)
    args = ap.parse_args()

    workdir = Path(args.workdir)
    in_dir = workdir / "input"
    out_dir = workdir / "out"
    mask_dir = out_dir / f"mask_{args.mask}"

    if not in_dir.exists():
        raise FileNotFoundError(f"Missing input dir: {in_dir}")
    if not out_dir.exists():
        raise FileNotFoundError(f"Missing output dir: {out_dir}")
    if not mask_dir.exists():
        raise FileNotFoundError(f"Missing mask dir: {mask_dir}")

    feats = []
    targets = []
    meta = []

    for wav in sorted(in_dir.glob("*.wav")):
        name = wav.stem
        at3tool_wav = out_dir / f"{name}.at3tool.dec.wav"
        atracdenc_wav = mask_dir / f"{name}.atracdenc.dec.wav"
        if not at3tool_wav.exists() or not atracdenc_wav.exists():
            continue
        feat, target, metrics = build_dataset(
            wav, at3tool_wav, atracdenc_wav, n_fft=args.n_fft, hop=args.hop
        )
        feats.append(feat)
        targets.append(target)
        meta.append({
            "input": str(wav),
            "at3tool_dec": str(at3tool_wav),
            "atracdenc_dec": str(atracdenc_wav),
            "frames": int(feat.shape[0]),
            **metrics,
        })

    if not feats:
        raise RuntimeError("No matching files found to build dataset")

    X = np.concatenate(feats, axis=0)
    Y = np.concatenate(targets, axis=0)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_path, X=X, Y=Y, n_fft=args.n_fft, hop=args.hop)

    meta_path = out_path.with_suffix(".json")
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump({"items": meta}, f, indent=2)

    print(f"Wrote dataset: {out_path}")
    print(f"Wrote meta: {meta_path}")


if __name__ == "__main__":
    main()
