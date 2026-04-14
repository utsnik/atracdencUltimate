import numpy as np
import wave
import os

def get_audio(f):
    if not os.path.exists(f): return None
    with wave.open(f, 'r') as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)

def calculate_best_possible_snr(orig, dec):
    # Cross-correlation to find lag and polarity
    # Use a middle chunk of 20000 samples for robustness
    L = 40000
    if len(orig) < L + 20000 or len(dec) < L + 20000:
        L = min(len(orig), len(dec)) // 2
        
    start = 10000
    o_chunk = orig[start:start+L]
    
    best_snr = -100
    best_lag = 0
    best_pol = 1
    best_gain = 1.0
    
    # Global lag search
    for lag in range(0, 15000, 2):
        if len(dec) < lag + L: break
        d_chunk = dec[lag:lag+L]
        
        # Optimal gain and polarity using linear regression
        # d * g = o  => g = sum(o*d) / sum(d*d)
        num = np.sum(o_chunk * d_chunk)
        den = np.sum(d_chunk * d_chunk)
        if den == 0: continue
        gain = num / den
        
        # Calculate SNR with this gain
        pred = d_chunk * gain
        noise_pwr = np.mean((o_chunk - pred)**2)
        sig_pwr = np.mean(o_chunk**2)
        if noise_pwr == 0: snr = 100
        else: snr = 10 * np.log10(sig_pwr / noise_pwr)
        
        if snr > best_snr:
            best_snr = snr
            best_lag = lag
            best_gain = gain
            best_pol = 1 if gain > 0 else -1

    return best_snr, best_lag, best_gain

def audit():
    orig = get_audio("YOUtopia.wav")
    dec = get_audio("sweep_dec.wav")
    if orig is None or dec is None: return
    
    snr, lag, gain = calculate_best_possible_snr(orig, dec)
    print(f"Max Attainable SNR: {snr:.2f} dB")
    print(f"Optimal Lag: {lag}")
    print(f"Optimal Gain: {gain:.4f}")
    
    # Check if this is a "real" signal
    if snr < 1.0:
        print("ALERT: Signal is uncorrelated or garbage.")
    else:
        print("SUCCESS: Signal is valid, just needs scaling and phasing.")

if __name__ == "__main__":
    audit()
