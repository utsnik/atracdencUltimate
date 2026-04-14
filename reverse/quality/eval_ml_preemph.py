import argparse
import json
import subprocess
import wave
from pathlib import Path

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


def write_wav(path, data, sr):
    data = np.clip(data, -1.0, 1.0)
    pcm = (data * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def snr_db(ref, test):
    min_len = min(len(ref), len(test))
    ref = ref[:min_len]
    test = test[:min_len]
    noise = ref - test
    num = np.mean(ref ** 2)
    den = np.mean(noise ** 2) + 1e-12
    return 10 * np.log10(num / den)


def spectral_l1(ref, test, n_fft=2048, hop=512):
    min_len = min(len(ref), len(test))
    ref = ref[:min_len]
    test = test[:min_len]
    pad = (n_fft - (min_len % hop)) % hop
    ref = np.pad(ref, (0, pad))
    test = np.pad(test, (0, pad))

    def stft_mag(x):
        frames = 1 + (len(x) - n_fft) // hop
        mags = []
        window = np.hanning(n_fft)
        for i in range(frames):
            start = i * hop
            seg = x[start:start + n_fft] * window
            spec = np.fft.rfft(seg)
            mags.append(np.abs(spec))
        return np.stack(mags, axis=0)

    m_ref = stft_mag(ref)
    m_test = stft_mag(test)
    return float(np.mean(np.abs(m_ref - m_test)))


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


def stft(x, n_fft=2048, hop=512):
    if len(x) < n_fft:
        return np.zeros((0, n_fft // 2 + 1), dtype=np.complex64), n_fft, hop
    frames = 1 + (len(x) - n_fft) // hop
    window = np.hanning(n_fft).astype(np.float32)
    out = np.empty((frames, n_fft // 2 + 1), dtype=np.complex64)
    for i in range(frames):
        start = i * hop
        seg = x[start:start + n_fft] * window
        out[i, :] = np.fft.rfft(seg)
    return out, n_fft, hop


def istft(spec, n_fft=2048, hop=512):
    if spec.shape[0] == 0:
        return np.zeros(0, dtype=np.float32)
    window = np.hanning(n_fft).astype(np.float32)
    out_len = (spec.shape[0] - 1) * hop + n_fft
    out = np.zeros(out_len, dtype=np.float32)
    win_sum = np.zeros(out_len, dtype=np.float32)
    for i in range(spec.shape[0]):
        start = i * hop
        seg = np.fft.irfft(spec[i]).astype(np.float32)
        out[start:start + n_fft] += seg * window
        win_sum[start:start + n_fft] += window ** 2
    win_sum = np.maximum(win_sum, 1e-6)
    out /= win_sum
    return out


def apply_preemph(x, model):
    W = model["W"]
    clip = float(model["clip"])
    spec, n_fft, hop = stft(x)
    if spec.shape[0] == 0:
        return x
    mag = np.abs(spec)
    phase = np.angle(spec)
    feat = np.log10(mag + 1e-8)
    ones = np.ones((feat.shape[0], 1), dtype=np.float32)
    feat_b = np.concatenate([feat, ones], axis=1)
    delta = feat_b @ W
    delta = np.clip(delta, -clip, clip)
    gain = 10 ** delta
    new_mag = mag * gain
    new_spec = new_mag * (np.cos(phase) + 1j * np.sin(phase))
    return istft(new_spec, n_fft=n_fft, hop=hop)


def run_cmd(cmd, cwd=None):
    res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return res.returncode, res.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--at3tool", required=True)
    ap.add_argument("--atracdenc", required=True)
    ap.add_argument("--bitrate", type=int, default=128)
    ap.add_argument("--mask", type=int, default=2)
    ap.add_argument("--model", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    workdir = Path(args.workdir)
    in_dir = workdir / "input"
    out_dir = workdir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    pre_dir = out_dir / "ml_preemph"
    pre_dir.mkdir(parents=True, exist_ok=True)

    model = np.load(args.model)

    results = []
    for wav in sorted(in_dir.glob("*.wav")):
        ref, sr = read_wav_mono(wav)

        pre_wav = pre_dir / f"{wav.stem}.mlpre.wav"
        pre = apply_preemph(ref, model)
        write_wav(pre_wav, pre, sr)

        # at3tool baseline
        at3_enc = pre_dir / f"{wav.stem}.at3tool.at3"
        at3_dec = pre_dir / f"{wav.stem}.at3tool.dec.wav"
        code, out = run_cmd([args.at3tool, "-e", "-br", str(args.bitrate), str(wav), str(at3_enc)])
        if code != 0 or not at3_enc.exists():
            results.append({"input": str(wav), "error": "at3tool encode failed", "log": out[-2000:]})
            continue
        code, out = run_cmd([args.at3tool, "-d", str(at3_enc), str(at3_dec)])
        if code != 0 or not at3_dec.exists():
            results.append({"input": str(wav), "error": "at3tool decode failed", "log": out[-2000:]})
            continue
        at3_dec_pcm, _ = read_wav_mono(at3_dec)
        lag_tool = best_alignment(ref, at3_dec_pcm)
        ref_t, at3_t = align_to(ref, at3_dec_pcm, lag_tool)
        base = {
            "snr_db": float(snr_db(ref_t, at3_t)),
            "spectral_l1": float(spectral_l1(ref_t, at3_t)),
            "lag": int(lag_tool),
        }

        # atracdenc baseline (no preemph)
        atrac_enc = pre_dir / f"{wav.stem}.atracdenc.oma"
        atrac_dec = pre_dir / f"{wav.stem}.atracdenc.dec.wav"
        code, out = run_cmd([
            args.atracdenc, "-e", "atrac3plus", "--bitrate", str(args.bitrate),
            "--advanced", f"ghadbg={args.mask}", "-i", str(wav), "-o", str(atrac_enc)
        ])
        if code != 0 or not atrac_enc.exists():
            results.append({"input": str(wav), "error": "atracdenc encode failed", "log": out[-2000:]})
            continue

        # decode atracdenc with at3tool (reuse OMA->RIFF helper from earlier pipeline)
        riff = pre_dir / f"{wav.stem}.atracdenc.at3tool.wav"
        oma = atrac_enc.read_bytes()
        if not oma.startswith(b"EA3"):
            results.append({"input": str(wav), "error": "atracdenc output not EA3"})
            continue
        header = oma[:96]
        params = int.from_bytes(header[32:36], byteorder="big", signed=False)
        frame_size = ((params & 0x3FF) * 8) + 8
        payload = oma[96:]
        num_frames = len(payload) // frame_size
        payload = payload[: num_frames * frame_size]

        # Write RIFF/WAVE for at3tool decode
        samplerate_idx = (params >> 13) & 0x7
        samplerate_table = [32000, 44100, 48000, 88200, 96000, 0, 0, 0]
        samplerate = samplerate_table[samplerate_idx]
        ch_id = (params >> 10) & 0x7
        channels = ch_id
        data_size = len(payload)
        fmt_size = 52
        fact_size = 12
        riff_size = 4 + (8 + fmt_size) + (8 + fact_size) + (8 + data_size)
        w_format_tag = 0xFFFE
        n_block_align = frame_size
        n_avg_bytes_per_sec = int(frame_size * samplerate / 2048)
        w_bits_per_sample = 0
        cb_size = 34
        w_valid_bits_per_sample = 2048
        channel_mask = 0x1 if channels == 1 else 0x3
        subformat = bytes.fromhex("bfaa23e958cb7144a119fffa01e4ce62")
        extra_rest_val = frame_size * 32 - 220
        extra_rest = (1).to_bytes(2, "little") + extra_rest_val.to_bytes(4, "little") + (0).to_bytes(6, "little")
        extra = (
            w_valid_bits_per_sample.to_bytes(2, "little")
            + channel_mask.to_bytes(4, "little")
            + subformat
            + extra_rest
        )
        fact = (
            int(len(ref)).to_bytes(4, "little")
            + (0x00080000).to_bytes(4, "little")
            + (0x000008B8).to_bytes(4, "little")
        )
        with open(riff, "wb") as f:
            f.write(b"RIFF")
            f.write(riff_size.to_bytes(4, "little"))
            f.write(b"WAVE")
            f.write(b"fmt ")
            f.write(fmt_size.to_bytes(4, "little"))
            f.write(w_format_tag.to_bytes(2, "little"))
            f.write(channels.to_bytes(2, "little"))
            f.write(samplerate.to_bytes(4, "little"))
            f.write(n_avg_bytes_per_sec.to_bytes(4, "little"))
            f.write(n_block_align.to_bytes(2, "little"))
            f.write(w_bits_per_sample.to_bytes(2, "little"))
            f.write(cb_size.to_bytes(2, "little"))
            f.write(extra)
            f.write(b"fact")
            f.write(fact_size.to_bytes(4, "little"))
            f.write(fact)
            f.write(b"data")
            f.write(data_size.to_bytes(4, "little"))
            f.write(payload)

        code, out = run_cmd([args.at3tool, "-d", str(riff), str(atrac_dec)])
        if code != 0 or not atrac_dec.exists():
            results.append({"input": str(wav), "error": "atracdenc decode failed", "log": out[-2000:]})
            continue
        atrac_dec_pcm, _ = read_wav_mono(atrac_dec)
        lag_atrac = best_alignment(ref, atrac_dec_pcm)
        ref_a, atrac_a = align_to(ref, atrac_dec_pcm, lag_atrac)
        atrac_metrics = {
            "snr_db": float(snr_db(ref_a, atrac_a)),
            "spectral_l1": float(spectral_l1(ref_a, atrac_a)),
            "lag": int(lag_atrac),
        }

        # ML preemph encode
        ml_enc = pre_dir / f"{wav.stem}.ml.oma"
        ml_dec = pre_dir / f"{wav.stem}.ml.dec.wav"
        code, out = run_cmd([
            args.atracdenc, "-e", "atrac3plus", "--bitrate", str(args.bitrate),
            "--advanced", f"ghadbg={args.mask}", "-i", str(pre_wav), "-o", str(ml_enc)
        ])
        if code != 0 or not ml_enc.exists():
            results.append({"input": str(wav), "error": "ml encode failed", "log": out[-2000:]})
            continue
        oma = ml_enc.read_bytes()
        header = oma[:96]
        params = int.from_bytes(header[32:36], byteorder="big", signed=False)
        frame_size = ((params & 0x3FF) * 8) + 8
        payload = oma[96:]
        num_frames = len(payload) // frame_size
        payload = payload[: num_frames * frame_size]

        riff_ml = pre_dir / f"{wav.stem}.ml.at3tool.wav"
        with open(riff_ml, "wb") as f:
            f.write(b"RIFF")
            f.write(riff_size.to_bytes(4, "little"))
            f.write(b"WAVE")
            f.write(b"fmt ")
            f.write(fmt_size.to_bytes(4, "little"))
            f.write(w_format_tag.to_bytes(2, "little"))
            f.write(channels.to_bytes(2, "little"))
            f.write(samplerate.to_bytes(4, "little"))
            f.write(n_avg_bytes_per_sec.to_bytes(4, "little"))
            f.write(n_block_align.to_bytes(2, "little"))
            f.write(w_bits_per_sample.to_bytes(2, "little"))
            f.write(cb_size.to_bytes(2, "little"))
            f.write(extra)
            f.write(b"fact")
            f.write(fact_size.to_bytes(4, "little"))
            f.write(fact)
            f.write(b"data")
            f.write(data_size.to_bytes(4, "little"))
            f.write(payload)

        code, out = run_cmd([args.at3tool, "-d", str(riff_ml), str(ml_dec)])
        if code != 0 or not ml_dec.exists():
            results.append({"input": str(wav), "error": "ml decode failed", "log": out[-2000:]})
            continue
        ml_dec_pcm, _ = read_wav_mono(ml_dec)
        lag_ml = best_alignment(ref, ml_dec_pcm)
        ref_m, ml_m = align_to(ref, ml_dec_pcm, lag_ml)
        ml_metrics = {
            "snr_db": float(snr_db(ref_m, ml_m)),
            "spectral_l1": float(spectral_l1(ref_m, ml_m)),
            "lag": int(lag_ml),
        }

        results.append({
            "input": str(wav),
            "baseline_at3tool": base,
            "baseline_atrac": atrac_metrics,
            "ml_preemph": ml_metrics,
        })

    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("w", encoding="utf-8") as f:
        f.write("# ML Pre-emphasis Evaluation\n\n")
        f.write(f"Bitrate: {args.bitrate} kbps, mask={args.mask}\n\n")
        for item in results:
            f.write(f"## {Path(item['input']).name}\n\n")
            if "error" in item:
                f.write(f"Error: {item['error']}\n\n")
                continue
            b = item["baseline_at3tool"]
            a = item["baseline_atrac"]
            m = item["ml_preemph"]
            f.write(f"- at3tool SNR: {b['snr_db']} dB, SpectralL1: {b['spectral_l1']}\n")
            f.write(f"- atracdenc SNR: {a['snr_db']} dB, SpectralL1: {a['spectral_l1']}\n")
            f.write(f"- ml-pre SNR: {m['snr_db']} dB, SpectralL1: {m['spectral_l1']}\n\n")

    json_path = report.with_suffix(".json")
    with json_path.open("w", encoding="utf-8") as f:
        json.dump({"items": results}, f, indent=2)

    print(f"Wrote report: {report}")
    print(f"Wrote json: {json_path}")


if __name__ == "__main__":
    main()
