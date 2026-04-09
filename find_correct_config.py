import os
import subprocess
import itertools
import time

def update_atrac3denc(signs):
    with open("src/atrac3denc.cpp", "r") as f:
        lines = f.readlines()
        
    out = []
    sign_array = ", ".join([f"{s}.0f" for s in signs])

    # We want to replace the band_sign logic with raw custom signs
    found = False
    for line in lines:
        if "static float custom_signs[4] =" in line:
            out.append(f"        static float custom_signs[4] = {{ {sign_array} }};\n")
            found = True
            continue
        if "float band_sign =" in line and found:
            out.append(f"        float band_sign = custom_signs[band];\n")
            found = False
            continue
            
        out.append(line)
        
    with open("src/atrac3denc.cpp", "w") as f:
        f.writelines(out)
    time.sleep(2)

def run_test():
    try:
        # Robust build
        for _ in range(3):
            build_res = subprocess.run(["cmd", "/c", "build_win.bat"], capture_output=True, text=True)
            if build_res.returncode == 0:
                break
            time.sleep(3)
        else:
            return "BUILD ERROR"
            
        res = subprocess.run(["python", "verify_atracdenc_snr.py"], capture_output=True, text=True)
        # Search for SNR specifically from THIS run
        snr = "SNR: NOT FOUND"
        for line in res.stdout.split('\n'):
            if "SNR:" in line:
                snr = line.strip()
        return snr
    except Exception as e:
        return f"ERROR: {str(e)}"

if __name__ == "__main__":
    signs = list(itertools.product([1, -1], repeat=4))
    
    results_file = "raw_sign_results.txt"
    if os.path.exists(results_file): os.remove(results_file)
    
    for s in signs:
        print(f"Testing Raw Signs {s}...", end=" ", flush=True)
        update_atrac3denc(s)
        snr_line = run_test()
        print(snr_line)
        with open(results_file, "a") as f:
            f.write(f"Signs {s} => {snr_line}\n")
        
        if "SNR:" in snr_line:
            try:
                val = float(snr_line.split(":")[1].split("dB")[0].strip())
                if val > 15:
                    print("!!! HIGH PARITY DETECTED !!!")
                    # exit(0) - Continue to find the BEST
            except:
                pass
