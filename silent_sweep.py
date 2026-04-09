import os
import subprocess
import itertools
import time
import sys

def run_test(signs):
    # Write signs to file for the encoder to read at runtime
    with open("signs.txt", "w") as f:
        f.write(" ".join([f"{s:.1f}" for s in signs]))
    
    try:
        # Run verification but hide ALL output
        devnull = open(os.devnull, 'w')
        res = subprocess.run(["python", "verify_atracdenc_snr.py"], 
                             capture_output=True, text=True)
        
        # Extract SNR from the captured output
        snr = "NotFound"
        for line in res.stdout.split('\n'):
            if "SNR:" in line:
                snr = line.strip().split(":")[-1].strip()
            if "Best delay (lag):" in line:
                lag = line.strip().split(":")[-1].strip()
        
        return snr, lag
    except Exception as e:
        return f"Error: {str(e)}", "N/A"

if __name__ == "__main__":
    # 16 combinations of raw subband signs
    signs_pool = list(itertools.product([1, -1], repeat=4))
    
    results_file = "final_parity_results.txt"
    if os.path.exists(results_file): os.remove(results_file)
    
    print(f"{'Signs':<20} | {'SNR':<12} | {'Lag':<6}")
    print("-" * 45)
    
    for s in signs_pool:
        snr, lag = run_test(s)
        out_line = f"{str(s):<20} | {snr:<12} | {lag:<6}"
        print(out_line)
        
        with open(results_file, "a") as f:
            f.write(out_line + "\n")
        
        # Early exit if we hit the parity target
        if "dB" in snr:
            try:
                val = float(snr.replace("dB", "").strip())
                if val > 50:
                    print("\n[!!!] PARITY ACHIEVED [!!!]")
                    print(f"Final Configuration: Signs {s}")
                    break
            except:
                pass
