import numpy as np
import wave
import subprocess
import os

def create_sine_wave(filename, frequency=1000, duration=5, sample_rate=44100, amplitude=1.0):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Use -1dBFS to avoid any potential header-level clipping issues, though amplitude 1.0 is 0dBFS
    # Let's try exactly 1.0 (0dBFS) first since we are testing SNR limits.
    # Stereo data
    data_mono = (amplitude * 32767 * np.sin(2 * np.pi * frequency * t)).astype(np.int16)
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
    # Align signals if necessary (shouldn't be for at3tool if it's sample accurate)
    length = min(len(original), len(decoded))
    original = original[:length]
    decoded = decoded[:length]
    
    # Calculate noise
    noise = original - decoded
    
    signal_power = np.mean(original**2)
    noise_power = np.mean(noise**2)
    
    if noise_power == 0:
        return float('inf')
    
    snr = 10 * np.log10(signal_power / noise_power)
    return snr

def verify_sony():
    at3tool = r"ghidra\reverse\windows\at3tool.exe"
    workdir = "atracdenc/verify_sony"
    os.makedirs(workdir, exist_ok=True)
    
    orig_wav = os.path.join(workdir, "orig.wav")
    at3_file = os.path.join(workdir, "encoded.at3")
    dec_wav = os.path.join(workdir, "dec_sony.wav")
    
    print("Generating 1kHz sine wave...")
    create_sine_wave(orig_wav, amplitude=0.99) # 0.99 to be safe from peak clipping
    
    print("Encoding with at3tool LP2 (132kbps)...")
    subprocess.run([at3tool, "-e", "-br", "132", orig_wav, at3_file], check=True)
    
    print("Decoding with at3tool...")
    subprocess.run([at3tool, "-d", at3_file, dec_wav], check=True)
    
    orig_data = get_audio_data(orig_wav)
    dec_data = get_audio_data(dec_wav)
    
    # Align (at3tool often adds a delay)
    print("Checking alignment...")
    best_snr = -100
    for lag in range(0, 10000):
        if len(orig_data) <= lag: break
        snr = calculate_snr(orig_data, dec_data[lag:])
        if snr > best_snr:
            best_snr = snr
            best_lag = lag
    
    print(f"Sony Baseline SNR: {best_snr:.4f} dB (at lag {best_lag})")

if __name__ == "__main__":
    verify_sony()
