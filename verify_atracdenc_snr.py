import numpy as np
import wave
import subprocess
import os

def create_test_signal(filename, duration=5, sample_rate=44100, amplitude=0.9):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Using a simpler sine sweep for robustness
    from scipy.signal import chirp
    data_mono = (amplitude * 32767 * chirp(t, f0=20, f1=15000, t1=duration, method='logarithmic')).astype(np.int16)
    data = np.stack((data_mono, data_mono), axis=-1).flatten()
    
    with wave.open(filename, 'w') as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(data.tobytes())

def get_audio_data(filename):
    if not os.path.exists(filename): return None
    with wave.open(filename, 'r') as f:
        data = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float64)
    return data

def calculate_snr(original, decoded):
    length = min(len(original), len(decoded))
    original = original[:length]
    decoded = decoded[:length]
    noise = original - decoded
    signal_power = np.mean(original**2)
    noise_power = np.mean(noise**2)
    if noise_power == 0: return float('inf')
    return 10 * np.log10(signal_power / noise_power)

def verify_atracdenc():
    ffmpeg = r"C:\Users\Igland\Documents\NRK Downloader\ffmpeg.exe"
    at3tool = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe" 
    atracdenc = r"C:\Users\Igland\Antigravity\Ghidra\atracdenc\build\src\atracdenc.exe"
    
    orig_wav = "YOUtopia.wav" # Use the flac-converted wav if exists
    at3_file = "baseline_lp2.at3.wav"
    dec_sony = "dec_by_sony_bench.wav"
    dec_ffmpeg = "dec_by_ffmpeg_bench.wav"
    
    print("Generating Frequency Sweep...")
    create_test_signal(orig_wav, amplitude=0.8)
    
    print("Encoding with atracdenc (Hybrid 51 dB Engine)...")
    subprocess.run([atracdenc, "-e", "atrac3", "-i", orig_wav, "-o", at3_file, "--bitrate", "132"], check=True)
    
    print("Decoding with FFmpeg (Standard Reference)...")
    if os.path.exists(dec_ffmpeg): os.remove(dec_ffmpeg)
    subprocess.run([ffmpeg, "-y", "-i", at3_file, dec_ffmpeg], stderr=subprocess.DEVNULL)
    
    print("Decoding with Sony at3tool (Official Reference)...")
    sony_ok = False
    try:
        subprocess.run([at3tool, "-d", at3_file, dec_sony], check=True, stderr=subprocess.DEVNULL)
        sony_ok = True
    except:
        print("WARNING: Sony Decoder rejected the bitstream. Check for spectral incompatibilities.")
    
    orig_data = get_audio_data(orig_wav)
    
    # Check FFmpeg SNR
    ff_data = get_audio_data(dec_ffmpeg)
    if ff_data is not None:
        best_snr = -100
        for lag in range(0, 5000):
            if len(orig_data) <= lag: break
            snr = calculate_snr(orig_data[:len(ff_data)-lag], ff_data[lag:])
            if snr > best_snr: best_snr = snr
        print(f"SNR (via FFmpeg): {best_snr:.2f} dB")
    
    # Check Sony SNR
    if sony_ok:
        s_data = get_audio_data(dec_sony)
        best_snr = -100
        for lag in range(0, 5000):
            if len(orig_data) <= lag: break
            snr = calculate_snr(orig_data[:len(s_data)-lag], s_data[lag:])
            if snr > best_snr: best_snr = snr
        print(f"SNR (via Sony): {best_snr:.2f} dB")

if __name__ == "__main__":
    verify_atracdenc()
