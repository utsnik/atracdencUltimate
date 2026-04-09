import sys
import numpy as np
import scipy.io.wavfile as wav

def audit_dsp(orig_file, ref_file):
    # Load original and reference (both 44100Hz 16-bit)
    rate1, data1 = wav.read(orig_file)
    rate2, data2 = wav.read(ref_file)
    
    # Take a 1024 sample window at a point of high energy (e.g. 1.0s)
    offset1 = 44100 # 1.0s
    offset2 = 44100 - 138 # Adjust for the known 138 sample lag
    
    len_samples = 4096
    s1 = data1[offset1:offset1+len_samples, 0].astype(float)
    s2 = data2[offset2:offset2+len_samples, 0].astype(float)
    
    # Calculate Correlation
    corr = np.corrcoef(s1, s2)[0, 1]
    print(f"Global Correlation (at lag 0 relative to offset): {corr:.6f}")
    
    # FFT to check band energy distribution
    f1 = np.fft.fft(s1)
    f2 = np.fft.fft(s2)
    
    # Split into 4 ATRAC3 subbands (0-5.5kHz, 5.5-11k, 11-16.5k, 16.5-22k)
    # 4096 bins -> 1024 bins per band
    for b in range(4):
        start = b * 512
        end = (b + 1) * 512
        band_corr = np.corrcoef(np.abs(f1[start:end]), np.abs(f2[start:end]))[0, 1]
        phase_diff = np.mean(np.angle(f1[start:end] / f2[start:end]))
        print(f"Band {b} Magnitude Correlation: {band_corr:.6f}")
        print(f"Band {b} Mean Phase Diff: {phase_diff:.6f} rad ({np.degrees(phase_diff):.2f} deg)")

if __name__ == "__main__":
    # Usage: python audit_dsp.py quality_verify_v2/orig.wav quality_verify_v2/baseline_sony_decoded.wav
    audit_dsp(sys.argv[1], sys.argv[2])
