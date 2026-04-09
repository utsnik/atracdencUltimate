from scipy.io import wavfile
import numpy as np
import os

def analyze():
    dec_wav = r"quality_verify_v2\dec_by_sony.wav"
    if not os.path.exists(dec_wav):
        print("File not found")
        return
        
    sr, data = wavfile.read(dec_wav)
    rms = np.sqrt(np.mean(data.astype(np.float32)**2))
    mx = np.max(np.abs(data))
    print(f"File: {dec_wav}")
    print(f"  Duration: {len(data)/sr:.2f}s")
    print(f"  RMS:      {rms:.6f}")
    print(f"  Max:      {mx}")
    
    # Check first 1000 samples
    print(f"  First 10 samples: {data[:10, 0]}")

if __name__ == "__main__":
    analyze()
