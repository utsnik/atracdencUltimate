import os
import subprocess
import itertools
import numpy as np
import wave
import time

# Paths
ATRACDENC = r"build\src\atracdenc.exe"
AT3TOOL = r"..\ghidra\reverse\windows\at3tool.exe"
WORKDIR = "universal_sweep_run"
ORIG_WAV = os.path.join(WORKDIR, "orig.wav")
AT3_FILE = os.path.join(WORKDIR, "encoded.at3")
DEC_WAV = os.path.join(WORKDIR, "decoded.wav")
SIGNS_FILE = "signs.txt"
MAPPING_FILE = "mapping.txt"
RESULTS_FILE = "universal_sweep_results.txt"

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
    if noise_power <= 0: return 100.0
    return 10 * np.log10(signal_power / noise_power)

def run_test(mapping, signs):
    # Write files
    with open(MAPPING_FILE, "w") as f:
        f.write(" ".join(map(str, mapping)))
    with open(SIGNS_FILE, "w") as f:
        f.write(" ".join(map(str, signs)))
    
    # Run silently
    try:
        # Encode
        subprocess.run([ATRACDENC, "-e", "atrac3", "-i", ORIG_WAV, "-o", AT3_FILE, "--bitrate", "132"], 
                       check=True, capture_output=True)
        # Decode
        subprocess.run([AT3TOOL, "-d", AT3_FILE, DEC_WAV], check=True, capture_output=True)
        
        # Calculate
        dec_data = get_audio_data(DEC_WAV)
        orig_data = get_audio_data(ORIG_WAV)
        lag = 132
        snr = calculate_snr(orig_data[:len(dec_data)-lag], dec_data[lag:])
        return snr
    except Exception:
        return -100.0

def create_test_signal(filename, duration=0.5):
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    from scipy.signal import chirp
    # Frequency sweep to exercise all subbands
    data_mono = (0.9 * 32767 * chirp(t, f0=100, f1=20000, t1=duration, method='logarithmic')).astype(np.int16)
    data = np.stack((data_mono, data_mono), axis=-1).flatten()
    with wave.open(filename, 'w') as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(data.tobytes())

if __name__ == "__main__":
    os.makedirs(WORKDIR, exist_ok=True)
    if not os.path.exists(ORIG_WAV):
        create_test_signal(ORIG_WAV)
    
    mappings = list(itertools.permutations([0, 2, 4, 6]))
    signs_patterns = list(itertools.product([1, -1], repeat=4))
    
    total = len(mappings) * len(signs_patterns)
    count = 0
    best_snr = -100
    best_config = None
    
    print(f"Starting silent sweep of {total} combinations...")
    start_time = time.time()
    
    with open(RESULTS_FILE, "w") as f_res:
        f_res.write("Universal Sweep Results\n")
        f_res.write("-" * 40 + "\n")
        
        for m in mappings:
            for s in signs_patterns:
                snr = run_test(m, s)
                count += 1
                if snr > best_snr:
                    best_snr = snr
                    best_config = (m, s)
                    print(f"New Best: Mapping={m} Signs={s} SNR={snr:.4f} dB ({count}/{total})")
                
                # Silent logging
                f_res.write(f"M={m} S={s} SNR={snr:.4f}\n")
                
                if count % 50 == 0:
                    elapsed = time.time() - start_time
                    print(f"Progress: {count}/{total} (Elapsed: {elapsed:.1f}s)")
        
    print("-" * 40)
    print(f"Sweep Complete. Best Result:")
    print(f"Mapping: {best_config[0]}")
    print(f"Signs:   {best_config[1]}")
    print(f"SNR:     {best_snr:.4f} dB")
    with open("best_config.txt", "w") as f_best:
        f_best.write(f"Mapping: {best_config[0]}\nSigns: {best_config[1]}\nSNR: {best_snr:.4f}\n")
