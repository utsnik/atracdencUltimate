import numpy as np
import wave
import sys

def get_audio(f):
    with wave.open(f, 'r') as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)

def analyze():
    orig = get_audio("YOUtopia.wav")
    dec = get_audio("sweep_dec.wav")
    
    print(f"Orig: Len={len(orig)}, RMS={np.sqrt(np.mean(orig**2)):.2f}")
    print(f"Dec:  Len={len(dec)}, RMS={np.sqrt(np.mean(dec**2)):.2f}")
    
    # Calculate global gain ratio
    ratio = np.sqrt(np.mean(orig**2)) / np.sqrt(np.mean(dec**2))
    print(f"Required Gain Adjustment: {ratio:.4f} ({20*np.log10(ratio):.2f} dB)")
    
    # Try multiple lags and polarity with gain adjustment
    best_snr = -100
    best_lag = 0
    best_pol = 1
    
    # Only check a segment to avoid length issues
    L = min(len(orig), len(dec)) - 5000
    for pol in [1, -1]:
        for lag in range(1400, 1500):
            o = orig[0:L]
            d = dec[lag:lag+L] * pol * ratio
            noise = o - d
            snr = 10 * np.log10(np.mean(o**2) / np.mean(noise**2))
            if snr > best_snr:
                best_snr = snr
                best_lag = lag
                best_pol = pol
                
    print(f"Best (with gain fix): SNR={best_snr:.2f} dB, Lag={best_lag}, Polarity={best_pol}")
    
    # Correlation
    o = orig[0:L]
    d = dec[best_lag:best_lag+L] * best_pol
    corr = np.corrcoef(o, d)[0, 1]
    print(f"Correlation (raw): {corr:.4f}")

if __name__ == "__main__":
    analyze()
