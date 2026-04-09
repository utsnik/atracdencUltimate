import os
import subprocess

def test_window_offset(offset):
    print(f"\n--- Testing Window Start Offset: {offset} ---")
    
    # Update atrac3.h with the window offset
    with open("src/atrac/at3/atrac3.h", "r") as f:
        content = f.readlines()
    
    new_lines = []
    for line in content:
        if "float val = sin(M_PI / 512.0 * (i + 0.5));" in line:
            new_lines.append(f"                float val = sin(M_PI / 512.0 * (i + 0.5 + {offset}.0));\n")
        else:
            new_lines.append(line)
            
    with open("src/atrac/at3/atrac3.h", "w") as f:
        f.writelines(new_lines)
        
    # Build
    subprocess.run(["cmd", "/c", "build_win.bat"], check=True, capture_output=True)
    
    # Verify
    result = subprocess.run(["python", "verify_atracdenc_snr.py"], check=True, capture_output=True, text=True)
    print(result.stdout)
    
    # Save results
    with open("window_sweep_results.txt", "a") as f:
        f.write(f"Window Offset {offset}:\n{result.stdout}\n")

if __name__ == "__main__":
    if os.path.exists("window_sweep_results.txt"): os.remove("window_sweep_results.txt")
    
    # Restoring Sync branch as it's the standard
    # I'll just iterate a small range first
    for o in range(-4, 5):
        test_window_offset(o)
