import os
import subprocess
import numpy as np
import wave

def get_audio_data(filename):
    if not os.path.exists(filename): return None
    with wave.open(filename, 'r') as f:
        data = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float64)
    return data

def calculate_snr(original, decoded):
    length = min(len(original), len(decoded))
    original = original[:length]
    decoded = decoded[:length]
    
    # Gain compensation
    rms_orig = np.sqrt(np.mean(original**2))
    rms_dec = np.sqrt(np.mean(decoded**2))
    if rms_dec > 0:
        decoded = decoded * (rms_orig / rms_dec)
        
    noise = original - decoded
    signal_power = np.mean(original**2)
    noise_power = np.mean(noise**2)
    if noise_power == 0: return float('inf')
    return 10 * np.log10(signal_power / noise_power)

def run_sweep():
    ffmpeg = r"C:\Users\Igland\Documents\NRK Downloader\ffmpeg.exe"
    atracdenc = r"C:\Users\Igland\Antigravity\Ghidra\atracdenc\build\src\atracdenc.exe"
    orig_wav = "YOUtopia.wav"
    at3_file = "sweep_tmp.at3.wav"
    dec_wav = "sweep_dec.wav"
    
    if not os.path.exists(orig_wav):
        print(f"Error: {orig_wav} not found.")
        return

    orig_data = get_audio_data(orig_wav)
    
    results = []
    
    print("Starting Combined Order & Polarity Sweep (32 combinations)...")
    # Order 0: {0,1,2,3}, Order 1: {0,1,3,2}
    for order in [0, 1]:
        for mask in range(16):
            env = os.environ.copy()
            env["ATRAC3_POLARITY_MASK"] = str(mask)
            env["ATRAC3_ORDER_SWAP"] = str(order)
            
            # Encode
            subprocess.run([atracdenc, "-e", "atrac3", "-i", orig_wav, "-o", at3_file, "--bitrate", "132"], 
                           env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Decode
            subprocess.run([ffmpeg, "-y", "-i", at3_file, dec_wav], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            dec_data = get_audio_data(dec_wav)
            if dec_data is None:
                results.append((order, mask, -100))
                continue
                
            # Find best lag
            best_snr = -100
            for lag in range(12290, 12310, 2): # Localized search for speed around 12300
                snr = calculate_snr(orig_data[:len(dec_data)-lag], dec_data[lag:])
                if snr > best_snr: best_snr = snr
                
            print(f"Order {order}, Mask {mask:04b}: Max SNR = {best_snr:.2f} dB")
            results.append((order, mask, best_snr))
        
    best_order, best_mask, best_val = max(results, key=lambda x: x[2])
    print(f"\nSweep Complete. Best Result: Order {best_order}, Mask {best_mask:04b} ({best_mask}) with SNR: {best_val:.2f} dB")

if __name__ == "__main__":
    run_sweep()
