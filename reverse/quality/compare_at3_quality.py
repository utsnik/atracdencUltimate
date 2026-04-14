import argparse
import json
import os
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np


def write_wav(path, data, sr=44100):
    data = np.clip(data, -1.0, 1.0)
    pcm = (data * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        # Duplicate mono to stereo
        stereo = np.column_stack((pcm, pcm)).flatten()
        wf.writeframes(stereo.tobytes())


def gen_test_wavs(out_dir, sr=44100):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tests = []

    t = np.linspace(0, 5.0, int(sr * 5.0), endpoint=False)
    sine_1k = 0.6 * np.sin(2 * np.pi * 1000 * t)
    p = out_dir / "sine_1k_5s.wav"
    write_wav(p, sine_1k, sr)
    tests.append(p)

    # Chirp 20Hz -> 20kHz
    t = np.linspace(0, 5.0, int(sr * 5.0), endpoint=False)
    f0, f1 = 20.0, 20000.0
    k = (f1 - f0) / t[-1]
    chirp = 0.6 * np.sin(2 * np.pi * (f0 * t + 0.5 * k * t * t))
    p = out_dir / "chirp_20_20k_5s.wav"
    write_wav(p, chirp, sr)
    tests.append(p)

    # Multitone
    freqs = [60, 250, 1000, 4000, 12000]
    t = np.linspace(0, 5.0, int(sr * 5.0), endpoint=False)
    multi = np.zeros_like(t)
    for f in freqs:
        multi += (0.5 / len(freqs)) * np.sin(2 * np.pi * f * t)
    p = out_dir / "multitone_5s.wav"
    write_wav(p, multi, sr)
    tests.append(p)

    # Transient: silence + impulse + sine tail
    t = np.linspace(0, 5.0, int(sr * 5.0), endpoint=False)
    transient = np.zeros_like(t)
    transient[int(0.5 * sr)] = 0.95
    transient += 0.4 * np.sin(2 * np.pi * 440 * t) * (t > 0.6)
    p = out_dir / "transient_5s.wav"
    write_wav(p, transient, sr)
    tests.append(p)

    return tests


def read_wav(path):
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


def spectral_l1(ref, test, n_fft=2048, hop=512):
    min_len = min(len(ref), len(test))
    ref = ref[:min_len]
    test = test[:min_len]
    # Pad to frame
    pad = (n_fft - (min_len % hop)) % hop
    ref = np.pad(ref, (0, pad))
    test = np.pad(test, (0, pad))

    def stft_mag(x):
        frames = 1 + (len(x) - n_fft) // hop
        mags = []
        window = np.hanning(n_fft)
        for i in range(frames):
            start = i * hop
            seg = x[start:start+n_fft] * window
            spec = np.fft.rfft(seg)
            mags.append(np.abs(spec))
        return np.stack(mags, axis=0)

    m_ref = stft_mag(ref)
    m_test = stft_mag(test)
    return float(np.mean(np.abs(m_ref - m_test)))


def run_cmd(cmd, cwd=None):
    res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return res.returncode, res.stdout


def best_alignment_snr(ref, test, max_shift=4096):
    n = min(len(ref), len(test), 65536)
    if n < 1024:
        return 0, snr_db(ref, test)
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
    best = int(lags[int(np.argmax(corr_lin))])

    best_snr = None
    best_lag = best
    for lag in range(best - 16, best + 17):
        if lag > max_shift or lag < -max_shift:
            continue
        if lag >= 0:
            r = ref[lag:]
            t = test[:len(r)]
        else:
            r = ref[:len(ref) + lag]
            t = test[-lag: -lag + len(r)]
        if len(r) < 1024:
            continue
        s = snr_db(r, t)
        if best_snr is None or s > best_snr:
            best_snr = s
            best_lag = lag
    if best_snr is None:
        best_snr = snr_db(ref, test)
        best_lag = 0
    return best_lag, float(best_snr)


def oma_to_at3tool_riff(oma_path, out_path, total_samples):
    # Convert OMA (EA3) ATRAC3/ATRAC3plus to RIFF/WAVE (at3tool-compatible)
    with open(oma_path, "rb") as f:
        data = f.read()

    if len(data) < 96 or data[0:3] != b"EA3":
        raise ValueError("Not a valid OMA/EA3 file")

    header = data[:96]
    params = int.from_bytes(header[32:36], byteorder="big", signed=False)
    codec_id = (params >> 24) & 0xFF
    
    # ATRAC3 = 0x00, ATRAC3plus = 0x01
    is_atrac3p = (codec_id == 0x01)
    
    samplerate_idx = (params >> 13) & 0x7
    samplerate_table = [32000, 44100, 48000, 88200, 96000, 0, 0, 0]
    samplerate = samplerate_table[samplerate_idx]
    if samplerate == 0:
        raise ValueError("Unsupported samplerate in OMA")

    ch_id = (params >> 10) & 0x7
    channels = ch_id  # 1..8
    frame_size = ((params & 0x3FF) * 8) + 8

    payload = data[96:]
    num_frames = len(payload) // frame_size
    payload = payload[: num_frames * frame_size]

    # Build RIFF/WAVE header (at3tool style)
    fmt_size = 52
    fact_size = 12
    data_size = len(payload)
    riff_size = 4 + (8 + fmt_size) + (8 + fact_size) + (8 + data_size)

    # WAVEFORMATEX
    w_format_tag = 0xFFFE  # WAVE_FORMAT_EXTENSIBLE
    n_channels = channels
    n_samples_per_sec = samplerate
    n_block_align = frame_size
    if is_atrac3p:
        n_avg_bytes_per_sec = int(frame_size * samplerate / 2048)
    else:
        n_avg_bytes_per_sec = int(frame_size * samplerate / 1024)
    w_bits_per_sample = 0
    cb_size = 34

    # WAVEFORMATEXTENSIBLE extra
    w_valid_bits_per_sample = 2048 if is_atrac3p else 1024
    channel_mask = 0x1 if channels == 1 else 0x3
    
    if is_atrac3p:
        subformat = bytes.fromhex("bfaa23e958cb7144a119fffa01e4ce62")  # ATRAC3plus GUID
    else:
        subformat = bytes.fromhex("34451fe27ad2214da23e063d75812b40")  # ATRAC3 GUID
        
    extra_rest_val = frame_size * 32 - 220 if is_atrac3p else 0
    extra_rest = (1).to_bytes(2, "little") + extra_rest_val.to_bytes(4, "little") + (0).to_bytes(6, "little")
    extra = (
        w_valid_bits_per_sample.to_bytes(2, "little")
        + channel_mask.to_bytes(4, "little")
        + subformat
        + extra_rest
    )

    # FACT chunk
    fact = (
        int(total_samples).to_bytes(4, "little")
        + (0x00080000).to_bytes(4, "little")
        + (0x000008B8).to_bytes(4, "little")
    )

    with open(out_path, "wb") as f:
        f.write(b"RIFF")
        f.write(riff_size.to_bytes(4, "little"))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(fmt_size.to_bytes(4, "little"))
        f.write(w_format_tag.to_bytes(2, "little"))
        f.write(n_channels.to_bytes(2, "little"))
        f.write(n_samples_per_sec.to_bytes(4, "little"))
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--at3tool", required=True)
    ap.add_argument("--atracdenc", required=False)
    ap.add_argument("--codec", choices=["atrac3", "atrac3plus"], default="atrac3plus")
    ap.add_argument("--bitrate", type=int, default=128)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--ghadbg-sweep", action="store_true")
    ap.add_argument("--report", required=False)
    args = ap.parse_args()

    workdir = Path(args.workdir)
    in_dir = workdir / "input"
    out_dir = workdir / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    tests = gen_test_wavs(in_dir)

    results = []
    baseline = {}

    for wav in tests:
        item = {"input": str(wav)}

        # at3tool encode/decode baseline
        at3_enc = out_dir / (wav.stem + ".at3tool.at3")
        at3_dec = out_dir / (wav.stem + ".at3tool.dec.wav")
        cmd = [args.at3tool, "-e", "-br", str(args.bitrate), str(wav), str(at3_enc)]
        code, out = run_cmd(cmd)
        item["at3tool_encode"] = {"code": code, "log": out[-2000:]}
        if code == 0 and at3_enc.exists():
            cmd = [args.at3tool, "-d", str(at3_enc), str(at3_dec)]
            code2, out2 = run_cmd(cmd)
            item["at3tool_decode"] = {"code": code2, "log": out2[-2000:]}
            if code2 == 0 and at3_dec.exists():
                ref, sr = read_wav(wav)
                test, sr2 = read_wav(at3_dec)
                item["at3tool_metrics"] = {
                    "snr_db": float(snr_db(ref, test)),
                    "spectral_l1": float(spectral_l1(ref, test)),
                    "sr": sr,
                    "sr_dec": sr2,
                }
                lag, snr_aligned = best_alignment_snr(ref, test)
                item["at3tool_metrics_aligned"] = {
                    "snr_db": float(snr_aligned),
                    "lag": int(lag),
                }
                baseline[Path(wav).name] = {
                    "ref": ref,
                    "sr": sr,
                }

        results.append(item)

    sweep_results = []
    if args.atracdenc:
        masks = list(range(0, 8)) if args.ghadbg_sweep else [None]
        for mask in masks:
            run = {"ghadbg": mask, "items": []}
            subdir = out_dir / ("mask_" + str(mask) if mask is not None else "default")
            subdir.mkdir(parents=True, exist_ok=True)
            for wav in tests:
                item = {"input": str(wav)}
                atrac_enc = subdir / (wav.stem + f".atracdenc.{'wav' if args.codec == 'atrac3' else 'oma'}")
                atrac_dec = subdir / (wav.stem + ".atracdenc.dec.wav")
                atrac_riff = subdir / (wav.stem + ".atracdenc.at3tool.wav")
                cmd = [args.atracdenc, "-e", args.codec, "--bitrate", str(args.bitrate), "-i", str(wav), "-o", str(atrac_enc)]
                if mask is not None:
                    cmd += ["--advanced", f"ghadbg={mask}"]
                code3, out3 = run_cmd(cmd)
                item["atracdenc_encode"] = {"code": code3, "log": out3[-2000:]}
                if code3 == 0 and atrac_enc.exists():
                    ref = baseline.get(Path(wav).name, {}).get("ref")
                    if ref is None:
                        ref, _ = read_wav(wav)
                    try:
                        if args.codec == 'atrac3':
                            atrac_riff_path = str(atrac_enc)
                        else:
                            oma_to_at3tool_riff(str(atrac_enc), str(atrac_riff), total_samples=len(ref))
                            atrac_riff_path = str(atrac_riff)
                        
                        cmd = [args.at3tool, "-d", atrac_riff_path, str(atrac_dec)]
                        code4, out4 = run_cmd(cmd)
                        item["atracdenc_decode_with_at3tool"] = {"code": code4, "log": out4[-2000:]}
                        if code4 == 0 and atrac_dec.exists():
                            test, sr2 = read_wav(atrac_dec)
                            item["atracdenc_metrics"] = {
                                "snr_db": float(snr_db(ref, test)),
                                "spectral_l1": float(spectral_l1(ref, test)),
                                "sr_dec": sr2,
                            }
                            lag, snr_aligned = best_alignment_snr(ref, test)
                            item["atracdenc_metrics_aligned"] = {
                                "snr_db": float(snr_aligned),
                                "lag": int(lag),
                            }
                    except Exception as e:
                        item["atracdenc_decode_with_at3tool"] = {"code": -1, "log": str(e)}
                run["items"].append(item)
            sweep_results.append(run)

    out_json = out_dir / "quality_report.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"baseline": results, "sweep": sweep_results}, f, indent=2)

    if args.report:
        report_path = Path(args.report)
        with report_path.open("w", encoding="utf-8") as f:
            f.write(f"# ATRAC Quality Sweep Report ({args.codec})\n\n")
            f.write(f"Bitrate: {args.bitrate} kbps\n\n")
            f.write("## Baseline (at3tool)\n\n")
            for item in results:
                name = Path(item['input']).name
                m = item.get("at3tool_metrics", {})
                ma = item.get("at3tool_metrics_aligned", {})
                f.write(f"- {name}: SNR={m.get('snr_db')} dB, SpectralL1={m.get('spectral_l1')}, AlignedSNR={ma.get('snr_db')} (lag={ma.get('lag')})\n")
            f.write(f"\n## Atracdenc Sweep ({args.codec})\n\n")
            for run in sweep_results:
                if run['ghadbg'] is not None:
                    f.write(f"### ghadbg={run['ghadbg']}\n\n")
                f.write("| Input | SNR | Aligned SNR | Spectral L1 | Delta SNR (vs at3tool) | Delta Aligned SNR |\n")
                f.write("|---|---:|---:|---:|---:|---:|\n")
                for item in run["items"]:
                    name = Path(item["input"]).name
                    m = item.get("atracdenc_metrics", {})
                    ma = item.get("atracdenc_metrics_aligned", {})
                    base = next((b for b in results if Path(b["input"]).name == name), None)
                    bsnr = base.get("at3tool_metrics", {}).get("snr_db") if base else None
                    basnra = base.get("at3tool_metrics_aligned", {}).get("snr_db") if base else None
                    dsnr = (m.get("snr_db") - bsnr) if (m.get("snr_db") is not None and bsnr is not None) else None
                    dsnra = (ma.get("snr_db") - basnra) if (ma.get("snr_db") is not None and basnra is not None) else None
                    f.write(f"| {name} | {m.get('snr_db')} | {ma.get('snr_db')} | {m.get('spectral_l1')} | {dsnr} | {dsnra} |\n")
                f.write("\n")

    print(f"Wrote {out_json}")


if __name__ == "__main__":
    main()



if __name__ == "__main__":
    main()
