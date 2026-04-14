import argparse
import json
from pathlib import Path
import wave

import numpy as np


BLOCK_SIZE_TAB = [
    0, 16, 32, 48, 64, 80, 96, 112,
    128, 160, 192, 224, 256, 288, 320, 352,
    384, 448, 512, 576, 640, 704, 768, 896,
    1024, 1152, 1280, 1408, 1536, 1664, 1792, 1920,
    2048
]


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


def qu_bin_ranges():
    ranges = []
    for i in range(len(BLOCK_SIZE_TAB) - 1):
        s = BLOCK_SIZE_TAB[i]
        e = BLOCK_SIZE_TAB[i + 1]
        # Map 2048-point spectrum to 1024 bins
        bs = max(0, s // 2)
        be = max(bs + 1, e // 2)
        ranges.append((bs, be))
    return ranges


def load_jsonl(path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--mask", type=int, default=2)
    ap.add_argument("--dump", required=True, help="atracdenc_frames.jsonl")
    ap.add_argument("--out", required=True, help="output .npz")
    ap.add_argument("--n-fft", type=int, default=2048)
    ap.add_argument("--hop", type=int, default=512)
    args = ap.parse_args()

    workdir = Path(args.workdir)
    in_dir = workdir / "input"
    out_dir = workdir / "out"
    mask_dir = out_dir / f"mask_{args.mask}"

    dump_items = load_jsonl(args.dump)
    if not dump_items:
        raise RuntimeError("Dump file is empty")

    # Group dump frames by input clip in order of encoding run
    # We rely on sequential order: runs are per input wav in run_quality.ps1
    wavs = sorted(in_dir.glob("*.wav"))
    if not wavs:
        raise RuntimeError("No input wavs found")

    # Build per-clip frame slices by equally splitting by decoded frame count
    # Use decoded files to derive frame count (STFT frames)
    ranges = qu_bin_ranges()
    X_list = []
    Y_list = []
    Q_list = []
    meta = []

    cursor = 0
    for wav in wavs:
        name = wav.stem
        at3tool_wav = out_dir / f"{name}.at3tool.dec.wav"
        atrac_wav = mask_dir / f"{name}.atracdenc.dec.wav"
        if not at3tool_wav.exists() or not atrac_wav.exists():
            continue

        ref, sr = read_wav_mono(wav)
        tool, sr2 = read_wav_mono(at3tool_wav)
        atrac, sr3 = read_wav_mono(atrac_wav)
        if sr != sr2 or sr != sr3:
            raise ValueError("Sample rate mismatch")

        lag_tool = best_alignment(ref, tool)
        lag_atrac = best_alignment(ref, atrac)
        ref_t, tool_t = align_to(ref, tool, lag_tool)
        ref_a, atrac_t = align_to(ref, atrac, lag_atrac)
        min_len = min(len(ref_t), len(ref_a), len(tool_t), len(atrac_t))
        tool_t = tool_t[:min_len]
        atrac_t = atrac_t[:min_len]

        m_tool = stft_mag(tool_t, n_fft=args.n_fft, hop=args.hop)
        m_atrac = stft_mag(atrac_t, n_fft=args.n_fft, hop=args.hop)
        frames = min(m_tool.shape[0], m_atrac.shape[0])
        if frames == 0:
            continue

        # Slice dump frames for this clip
        # Use same number of frames as STFT
        clip_frames = dump_items[cursor: cursor + frames]
        cursor += frames
        if len(clip_frames) != frames:
            break

        for fidx in range(frames):
            d = clip_frames[fidx]
            energies = d["max_energy"][0]
            sf_idx = d["sf_idx"]
            num_qu = d["num_qu"]
            for qu in range(num_qu):
                bs, be = ranges[qu]
                tool_mag = np.mean(m_tool[fidx, bs:be])
                atrac_mag = np.mean(m_atrac[fidx, bs:be])
                target = np.log10(tool_mag + 1e-8) - np.log10(atrac_mag + 1e-8)
                feat = [
                    np.log10(float(energies[qu]) + 1e-8),
                    float(sf_idx[qu][0]),
                ]
                X_list.append(feat)
                Y_list.append(target)
                Q_list.append(qu)

        meta.append({
            "input": str(wav),
            "frames": int(frames),
            "lag_tool": int(lag_tool),
            "lag_atrac": int(lag_atrac),
        })

    if not X_list:
        raise RuntimeError("No samples built; check dump alignment")

    X = np.asarray(X_list, dtype=np.float32)
    Y = np.asarray(Y_list, dtype=np.float32)
    Q = np.asarray(Q_list, dtype=np.int32)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_path, X=X, Y=Y, Q=Q, n_fft=args.n_fft, hop=args.hop)

    meta_path = out_path.with_suffix(".json")
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump({"items": meta}, f, indent=2)

    print(f"Wrote dataset: {out_path}")
    print(f"Wrote meta: {meta_path}")


if __name__ == "__main__":
    main()
