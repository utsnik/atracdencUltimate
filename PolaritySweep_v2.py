import subprocess
import os
import re
import numpy as np

atracdenc = r"build\src\atracdenc.exe"
at3tool = r"..\ghidra\reverse\windows\at3tool.exe"
orig_wav = r"quality_verify_v2\orig.wav"
dec_wav = r"quality_verify_v2\dec_by_sony.wav"
at3_file = r"quality_verify_v2\encoded_atracdenc.at3"

def run_test(signs):
    # Save signs
    with open("signs.txt", "w") as f:
        f.write(" ".join(map(str, signs)))
    with open("mapping.txt", "w") as f:
        f.write("0 1 3 2")
        
    try:
        # Encode
        subprocess.run([atracdenc, "-e", "atrac3", "-i", orig_wav, "-o", at3_file, "--bitrate", "132", "--notonal", "--nogaincontrol"], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        # Decode
        res = subprocess.run([at3tool, "-d", at3_file, dec_wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode != 0:
            return -100.0, 0
            
        # Calculate SNR
        from scipy.io import wavfile
        sr_orig, data_orig = wavfile.read(orig_wav)
        sr_dec, data_dec = wavfile.read(dec_wav)
        
        # Sony output is often slightly different length
        ln = min(len(data_orig), len(data_dec))
        s1 = data_orig[:ln, 0].astype(np.float32)
        s2 = data_dec[:ln, 0].astype(np.float32)
        
        # Test 132 sample lag
        lag = 132
        if ln > lag:
            s1_cut = s1[lag:]
            s2_cut = s2[:len(s1_cut)]
            noise = s1_cut - s2_cut
            p_sig = np.sum(s1_cut**2)
            p_noise = np.sum(noise**2)
            if p_noise < 1e-10: return 100.0, lag
            snr = 10 * np.log10(p_sig / p_noise)
            return snr, lag
        return -100.0, 0
    except Exception as e:
        return -100.0, 0

def sweep():
    best_snr = -100.0
    best_signs = None
    
    print("Starting Polarity Sweep (Sony Mapping {0, 1, 3, 2})...")
    for i in range(16):
        signs = [1 if (i & (1 << j)) else -1 for j in range(4)]
        snr, lag = run_test(signs)
        print(f"Signs {signs}: SNR = {snr:.4f} dB")
        if snr > best_snr:
            best_snr = snr
            best_signs = signs
            
    print(f"\nWINNER: Best SNR = {best_snr:.4f} dB with Signs {best_signs}")

if __name__ == "__main__":
    sweep()
