import numpy as np
import scipy.io.wavfile as wav
import sys

def find_lag(orig_file, ref_file):
    rate1, data1 = wav.read(orig_file)
    rate2, data2 = wav.read(ref_file)
    
    # Use mono for speed
    s1 = data1[:, 0].astype(float)
    s2 = data2[:, 0].astype(float)
    
    # Cross-correlation on a chunk
    chunk_len = 8192
    offset = rate1 * 1 # 1 second in
    s1_chunk = s1[offset:offset+chunk_len]
    
    correlations = []
    lags = range(0, 5000)
    for lag in lags:
        s2_chunk = s2[offset+lag:offset+lag+chunk_len]
        if len(s2_chunk) < chunk_len: break
        c = np.corrcoef(s1_chunk, s2_chunk)[0, 1]
        correlations.append(c)
    
    best_lag = lags[np.argmax(correlations)]
    best_corr = np.max(correlations)
    print(f"Best Lag: {best_lag}")
    print(f"Max Correlation: {best_corr}")

if __name__ == "__main__":
    find_lag(sys.argv[1], sys.argv[2])
