import os
import subprocess
import itertools
import numpy as np
import wave

# Paths
ATRACDENC = r"build\src\atracdenc.exe"
AT3TOOL = r"..\ghidra\reverse\windows\at3tool.exe"
WORKDIR = "quality_sweep"
ORIG_WAV = os.path.join(WORKDIR, "orig.wav")
AT3_FILE = os.path.join(WORKDIR, "encoded.at3")
DEC_WAV = os.path.join(WORKDIR, "decoded.wav")
SIGNS_FILE = "signs.txt"

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
    if noise_power == 0: return float('inf')
    return 10 * np.log10(signal_power / noise_power)

def run_test(signs):
    # Write signs.txt
    with open(SIGNS_FILE, "w") as f:
        f.write(" ".join(map(str, signs)))
    
    # Encode
    try:
        subprocess.run([ATRACDENC, "-e", "atrac3", "-i", ORIG_WAV, "-o", AT3_FILE, "--bitrate", "132"], 
                       check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error encoding: {e.stderr}")
        return -100

    # Decode with Sony
    try:
        subprocess.run([AT3TOOL, "-d", AT3_FILE, DEC_WAV], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Error decoding: {e.stderr}")
        return -100

    # Calculate SNR
    dec_data = get_audio_data(DEC_WAV)
    orig_data = get_audio_data(ORIG_WAV)
    
    # Align (from 132 sample lag)
    lag = 132
    snr = calculate_snr(orig_data[:len(dec_data)-lag], dec_data[lag:])
    return snr

def create_test_signal(filename, duration=1.0, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    from scipy.signal import chirp
    data_mono = (0.9 * 32767 * chirp(t, f0=100, f1=18000, t1=duration, method='logarithmic')).astype(np.int16)
    data = np.stack((data_mono, data_mono), axis=-1).flatten()
    with wave.open(filename, 'w') as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(data.tobytes())

if __name__ == "__main__":
    os.makedirs(WORKDIR, exist_ok=True)
    if not os.path.exists(ORIG_WAV):
        print("Generating test signal...")
        create_test_signal(ORIG_WAV)
    
    results = []
    permutations = list(itertools.product([1, -1], repeat=4))
    
    print(f"{'Signs':<20} | {'SNR (dB)':<10}")
    print("-" * 35)
    
    for p in permutations:
        snr = run_test(p)
        results.append((p, snr))
        print(f"{str(p):<20} | {snr:>10.4f}")
        
    best_p, best_snr = max(results, key=lambda x: x[1])
    print("-" * 35)
    print(f"Best Signs: {best_p} with SNR: {best_snr:.4f} dB")
    
    with open("sign_sweep_results_v33.txt", "w") as f:
        f.write(f"Best Signs: {best_p} with SNR: {best_snr:.4f} dB\n")
        f.write("Full Results:\n")
        for p, snr in results:
            f.write(f"{p}: {snr:.4f} dB\n")
