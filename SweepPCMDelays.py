import os
import subprocess

def test_shift(shift):
    print(f"\n--- Testing PCM Shift: {shift} ---")
    
    # Update atrac3denc.cpp with the shift
    with open("src/atrac3denc.cpp", "r") as f:
        content = f.read()
    
    # Find the loading logic and inject the shift
    # We'll just modify the h_pos offset or the loading offset
    new_content = content.replace(
        "src[i] = (*history)[idx] * 32768.0f;",
        f"size_t s_idx = ch_offset + ((*h_pos + i + {shift}) % 1024);\n                src[i] = (*history)[s_idx] * 32768.0f;"
    )
    
    with open("src/atrac3denc.cpp", "w") as f:
        f.write(new_content)
        
    # Build
    subprocess.run(["cmd", "/c", "build_win.bat"], check=True, capture_output=True)
    
    # Verify
    result = subprocess.run(["python", "verify_atracdenc_snr.py"], check=True, capture_output=True, text=True)
    print(result.stdout)
    
    # Save results
    with open("sweep_results.txt", "a") as f:
        f.write(f"Shift {shift}:\n{result.stdout}\n")
    
    # Restore (optional, we overwrite anyway)

if __name__ == "__main__":
    if os.path.exists("sweep_results.txt"): os.remove("sweep_results.txt")
    for s in [0, 1, 2, 3]:
        test_shift(s)
