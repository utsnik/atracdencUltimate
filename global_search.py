import numpy as np
import wave
import os

def get_audio(f):
    if not os.path.exists(f): return None
    with wave.open(f, 'r') as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)

def global_lag_search():
    orig = get_audio("YOUtopia.wav")
    dec = get_audio("sweep_dec.wav")
    if orig is None or dec is None: return
    
    ratio = np.sqrt(np.mean(orig**2)) / np.sqrt(np.mean(dec**2))
    
    best_corr = 0
    best_lag = 0
    best_pol = 1
    
    print("Searching for lag (0 to 10000)...")
    # Take a chunk of 20000 samples for speed
    L = 20000
    o_chunk = orig[10000:10000+L]
    
    for lag in range(0, 10000, 10):
        if len(dec) < lag + L: break
        d_chunk = dec[lag:lag+L]
        
        corr = np.corrcoef(o_chunk, d_chunk)[0, 1]
        if abs(corr) > abs(best_corr):
            best_corr = corr
            best_lag = lag
            best_pol = 1 if corr > 0 else -1
            
    print(f"Global Best: Correlation={best_corr:.4f}, Lag={best_lag}, Polarity={best_pol}")
    
    if abs(best_corr) < 0.1:
        print("No significant correlation found in first 10000 samples.")
        print("Trying Channel Swap search...")
        # Check if Dec Left matches Orig Right?
        # Dec is stereo interleaved: L, R, L, R
        dec_l = dec[0::2]
        dec_r = dec[1::2]
        orig_l = orig[0::2]
        orig_r = orig[1::2]
        
        # Check Dec Left vs Orig Left
        corr_ll = np.corrcoef(orig_l[5000:15000], dec_l[5000:15000])[0, 1]
        # Check Dec Left vs Orig Right
        corr_lr = np.corrcoef(orig_r[5000:15000], dec_l[5000:15000])[0, 1]
        
        print(f"L-L Corr: {corr_ll:.4f}")
        print(f"L-R Corr: {corr_lr:.4f}")

if __name__ == "__main__":
    global_lag_search()
