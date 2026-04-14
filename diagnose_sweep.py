import numpy as np
import wave
import os

def get_audio(f):
    if not os.path.exists(f): return None
    with wave.open(f, 'r') as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)

def calculate_snr(original, decoded):
    length = min(len(original), len(decoded))
    original = original[:length]
    decoded = decoded[:length]
    noise = original - decoded
    return 10 * np.log10(np.mean(original**2) / np.mean(noise**2))

def diagnose():
    orig = get_audio("YOUtopia.wav")
    dec = get_audio("sweep_dec.wav")
    if orig is None or dec is None: return
    
    lag = 12300
    L = 40000
    start = 10000
    o_chunk = orig[start:start+L]
    d_chunk = dec[lag+start:lag+start+L]
    
    # Calculate correlation
    corr = np.corrcoef(o_chunk, d_chunk)[0, 1]
    print(f"Correlation at 12300: {corr:.4f}")
    
    # Calculate gain
    gain = np.sum(o_chunk * d_chunk) / np.sum(d_chunk * d_chunk)
    print(f"Optimal Gain: {gain:.4f}")
    
    # Calculate SNR raw
    snr_raw = calculate_snr(o_chunk, d_chunk)
    print(f"Raw SNR: {snr_raw:.2f} dB")
    
    # Calculate SNR gain-compensated
    snr_comp = calculate_snr(o_chunk, d_chunk * gain)
    print(f"Compensated SNR: {snr_comp:.2f} dB")

if __name__ == "__main__":
    diagnose()
