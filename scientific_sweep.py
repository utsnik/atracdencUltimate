import os
import subprocess
import itertools
import numpy as np
import wave

# Paths
ATRACDENC = r"build\src\atracdenc.exe"
AT3TOOL = r"..\ghidra\reverse\windows\at3tool.exe"
SIGNS_FILE = "signs.txt"
MAPPING_FILE = "mapping.txt"
DELAYS_FILE = "delays.txt"
WORKDIR = "scientific_sweep_run"
ORIG_WAV = os.path.join(WORKDIR, "orig.wav")
AT3_FILE = os.path.join(WORKDIR, "encoded.at3")
DEC_WAV = os.path.join(WORKDIR, "decoded.wav")

def get_audio_data(filename):
    with wave.open(filename, 'r') as f:
        data = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float64)
    return data

def calculate_snr(original, decoded, lag=132):
    length = min(len(original), len(decoded))
    original = original[:length-lag]
    decoded = decoded[lag:length]
    noise = original - decoded
    signal_power = np.mean(original**2)
    noise_power = np.mean(noise**2)
    if noise_power <= 0: return 100.0
    return 10 * np.log10(signal_power / noise_power)

def run_test(mapping, signs, delays):
    with open(MAPPING_FILE, "w") as f: f.write(" ".join(map(str, mapping)))
    with open(SIGNS_FILE, "w") as f: f.write(" ".join(map(str, signs)))
    with open(DELAYS_FILE, "w") as f: f.write(" ".join(map(str, delays)))
    
    try:
        subprocess.run([ATRACDENC, "-e", "atrac3", "-i", ORIG_WAV, "-o", AT3_FILE, "--bitrate", "132"], 
                       check=True, capture_output=True)
        subprocess.run([AT3TOOL, "-d", AT3_FILE, DEC_WAV], check=True, capture_output=True)
        
        dec_data = get_audio_data(DEC_WAV)
        orig_data = get_audio_data(ORIG_WAV)
        
        # Test a small range of lags around 132
        best_snr = -100
        for lag in range(128, 140):
            snr = calculate_snr(orig_data, dec_data, lag)
            if snr > best_snr: best_snr = snr
        return best_snr
    except Exception:
        return -100.0

if __name__ == "__main__":
    os.makedirs(WORKDIR, exist_ok=True)
    
    # Use existing signal from verify folder if possible
    SRC_ORIG = os.path.join("quality_verify_v2", "orig.wav")
    if os.path.exists(SRC_ORIG):
        import shutil
        shutil.copy(SRC_ORIG, ORIG_WAV)
    
    if not os.path.exists(ORIG_WAV):
        print("Generating test signal...")
        # (Chirp generation logic here if needed)
    
    # Signs for 4 bands
    signs_patterns = list(itertools.product([1, -1], repeat=4))
    
    # Strategic Mapping (from 8dB success)
    mapping = (0, 2, 6, 4) 
    
    # Strategic Delays
    # Scientific Hypothesis: HH is at Lag 17, others at 16.
    # We try: 
    # (0,0,0,0) - Baseline
    # (1,1,1,0) - Delaying LL, LH, HL by 1 to align with HH
    # (0,0,0,1) - Delaying HH by 1 (making it Lag 18?)
    delay_configs = [
        (0,0,0,0),
        (1,1,1,0),
        (2,2,2,1),
        (1,1,1,1)
    ]
    
    print("Starting Scientific Sweep (Silent)...")
    results = []
    for d in delay_configs:
        print(f"Testing Delay Configuration: {d}")
        for s in signs_patterns:
            snr = run_test(mapping, s, d)
            results.append((d, s, snr))
            if snr > 10:
                print(f"!!! BREAKTHROUGH: Delay={d} Signs={s} SNR={snr:.4f} !!!")
            
    best_d, best_s, best_snr = max(results, key=lambda x: x[2])
    print("-" * 40)
    print(f"Best Scientific Config:\nDelay: {best_d}\nSigns: {best_s}\nSNR: {best_snr:.4f} dB")
