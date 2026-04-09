import os
import subprocess
import itertools
import numpy as np
import wave
import time

# Paths
ATRACDENC = r"build\src\atracdenc.exe"
AT3TOOL = r"..\ghidra\reverse\windows\at3tool.exe"
SIGNS_FILE = "signs.txt"
MAPPING_FILE = "mapping.txt"
DELAYS_FILE = "delays.txt"
MIRROR_FILE = "mirroring.txt"
WORKDIR = "mirror_sweep_run"
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

def run_test(mapping, signs, mirroring, delays=(0,0,0,0)):
    with open(MAPPING_FILE, "w") as f: f.write(" ".join(map(str, mapping)))
    with open(SIGNS_FILE, "w") as f: f.write(" ".join(map(str, signs)))
    with open(MIRROR_FILE, "w") as f: f.write(" ".join(map(str, mirroring)))
    with open(DELAYS_FILE, "w") as f: f.write(" ".join(map(str, delays)))
    
    try:
        subprocess.run([ATRACDENC, "-e", "atrac3", "-i", ORIG_WAV, "-o", AT3_FILE, "--bitrate", "132"], 
                       check=True, capture_output=True)
        subprocess.run([AT3TOOL, "-d", AT3_FILE, DEC_WAV], check=True, capture_output=True)
        
        dec_data = get_audio_data(DEC_WAV)
        orig_data = get_audio_data(ORIG_WAV)
        
        best_snr = -100
        for lag in range(128, 140):
            snr = calculate_snr(orig_data, dec_data, lag)
            if snr > best_snr: best_snr = snr
        return best_snr
    except Exception:
        return -100.0

if __name__ == "__main__":
    os.makedirs(WORKDIR, exist_ok=True)
    SRC_ORIG = os.path.join("quality_verify_v2", "orig.wav")
    if os.path.exists(SRC_ORIG):
        import shutil
        shutil.copy(SRC_ORIG, ORIG_WAV)
    
    signs_patterns = list(itertools.product([1, -1], repeat=4))
    mirror_patterns = list(itertools.product([0, 1], repeat=4))
    mappings = [(0, 2, 4, 6), (0, 2, 6, 4), (0, 4, 6, 2)]
    
    total = len(mappings) * len(signs_patterns) * len(mirror_patterns)
    print(f"Starting Mirror & Sign Sweep ({total} combos)...")
    count = 0
    best_snr = -100
    best_cfg = None
    
    with open("mirror_sweep_results_v33.txt", "w") as f_log:
        for m in mappings:
            for mir in mirror_patterns:
                for s in signs_patterns:
                    snr = run_test(m, s, mir)
                    count += 1
                    if snr > best_snr:
                        best_snr = snr
                        best_cfg = (m, s, mir)
                        print(f"NEW BEST: Mapping={m} Signs={s} Mirror={mir} SNR={snr:.4f} dB")
                    
                    if count % 100 == 0:
                        print(f"Progress: {count}/{total}")
    
    print("-" * 40)
    print(f"Sweep Complete. GLOBAL BEST:")
    print(f"Mapping: {best_cfg[0]}")
    print(f"Signs:   {best_cfg[1]}")
    print(f"Mirror:  {best_cfg[2]}")
    print(f"SNR:     {best_snr:.4f} dB")
