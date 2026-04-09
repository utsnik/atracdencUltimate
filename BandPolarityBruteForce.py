import os
import subprocess

def test_polarity(p):
    print(f"\n--- Testing Polarity: {p} ---")
    
    with open("src/atrac3denc.cpp", "r") as f:
        content = f.read()
    
    # Simple replacement of the polarity multipliers
    # { p[0], p[1], p[2], p[3] }
    new_code = content.replace(
        "curSpec[i] = sp[i] * 1.41421356f;",
        f"curSpec[i] = sp[i] * ({p[0]}.0f);"
    )
    # We'll use band-specific multipliers in a more robust way
    # I'll just rewrite the loop logic in the test script
    
    # Update for this specific test
    with open("src/atrac3denc.cpp", "r") as f:
        lines = f.readlines()
        
    out_lines = []
    in_loop = False
    band_logic = f"            float mults[4] = {{ {p[0]}.0f, {p[1]}.0f, {p[2]}.0f, {p[3]}.0f }};\n            curSpec[i] = sp[i] * mults[band];\n"
    
    for line in lines:
        if "curSpec[i] = sp[i] * 1.41421356f;" in line:
            out_lines.append(band_logic)
        else:
            out_lines.append(line)
            
    with open("src/atrac3denc.cpp", "w") as f:
        f.writelines(out_lines)
    
    # Build and Verify
    subprocess.run(["cmd", "/c", "build_win.bat"], check=True, capture_output=True)
    result = subprocess.run(["python", "verify_atracdenc_snr.py"], check=True, capture_output=True, text=True)
    
    print(result.stdout)
    with open("polarity_sweep_results.txt", "a") as f:
        f.write(f"Polarity {p}:\n{result.stdout}\n")

if __name__ == "__main__":
    if os.path.exists("polarity_sweep_results.txt"): os.remove("polarity_sweep_results.txt")
    
    combos = [
        (1, 1, 1, 1),
        (1, 1, 1, -1),
        (1, 1, -1, 1),
        (1, 1, -1, -1),
        (1, -1, 1, 1),
        (1, -1, 1, -1),
        (1, -1, -1, 1),
        (1, -1, -1, -1),
        (-1, 1, 1, 1),
        (-1, 1, 1, -1),
        (-1, 1, -1, 1),
        (-1, 1, -1, -1),
        (-1, -1, 1, 1),
        (-1, -1, 1, -1),
        (-1, -1, -1, 1),
        (-1, -1, -1, -1),
    ]
    
    for p in combos:
        test_polarity(p)
