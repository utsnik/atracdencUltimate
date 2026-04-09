import numpy as np
import wave
import subprocess
import os

def create_test_signal(filename, duration=5, sample_rate=44100, amplitude=0.9):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Use a frequency sweep to cover all ATRAC3 subbands
    from scipy.signal import chirp
    data_mono = (amplitude * 32767 * chirp(t, f0=100, f1=20000, t1=duration, method='logarithmic')).astype(np.int16)
    data = np.stack((data_mono, data_mono), axis=-1).flatten()
    
    with wave.open(filename, 'w') as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(data.tobytes())

def get_audio_data(filename):
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
    
    if noise_power == 0:
        return float('inf')
    
    snr = 10 * np.log10(signal_power / noise_power)
    return snr

def verify_atracdenc():
    at3tool = r"..\ghidra\reverse\windows\at3tool.exe" # Relative to atracdenc root
    atracdenc = r"build2\src\atracdenc.exe"
    
    workdir = "quality_verify_v2"
    os.makedirs(workdir, exist_ok=True)
    
    orig_wav = os.path.join(workdir, "orig.wav")
    at3_file = os.path.join(workdir, "encoded_atracdenc.at3")
    dec_wav = os.path.join(workdir, "dec_by_sony.wav")
    
    print("Generating frequency sweep (log chirp)...")
    create_test_signal(orig_wav, amplitude=0.99)
    
    print("Encoding with atracdenc LP2...")
    # atracdenc usage: -e atrac3 -i <input> -o <output> --bitrate 132
    subprocess.run([atracdenc, "-e", "atrac3", "-i", orig_wav, "-o", at3_file, "--bitrate", "132"], check=True)
    
    print("Decoding with Sony at3tool.exe for verification...")
    subprocess.run([at3tool, "-d", at3_file, dec_wav], check=True)
    
    orig_data = get_audio_data(orig_wav)
    dec_data = get_audio_data(dec_wav)
    
    # Align
    print("Checking alignment and SNR...")
    best_snr = -100
    best_lag = 0
    # Scan a range of lags. ATRAC3 delay is usually around 1000-2000 samples.
    for lag in range(0, 5000):
        if len(orig_data) <= lag: break
        snr = calculate_snr(orig_data[:len(dec_data)-lag], dec_data[lag:])
        if snr > best_snr:
            best_snr = snr
            best_lag = lag
            
    print("-" * 40)
    print(f"atracdenc (with Sony Decode) SNR: {best_snr:.4f} dB")
    print(f"Best delay (lag): {best_lag} samples")
    print("-" * 40)
    
    if best_snr < 0:
        print("WARNING: SNR is negative. Signal mismatch or major clipping.")
    elif best_snr > 50:
        print("EXCELLENT: High SNR achieved! Approaching Sony parity.")
    else:
        print("Note: SNR is positive but below target 57 dB.")

if __name__ == "__main__":
    verify_atracdenc()
