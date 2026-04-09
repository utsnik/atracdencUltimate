import os
import subprocess

def test_mirroring(p):
    print(f"\n--- Testing Mirroring Pattern: {p} ---")
    
    with open("src/atrac3denc.cpp", "r") as f:
        lines = f.readlines()
        
    out_lines = []
    # Replace the mirroring logic in TAtrac3MDCT::Mdct
    patterns = {0: p[0], 1: p[1], 2: p[2], 3: p[3]}
    
    in_mdct = False
    for line in lines:
        if "void TAtrac3MDCT::Mdct" in line:
            in_mdct = True
        
        if in_mdct and "if (band % 2 != 0) {" in line:
            # Inject parity-specific mirroring
            mirror_logic = f"        bool do_mirror[4] = {{ {str(p[0]).lower()}, {str(p[1]).lower()}, {str(p[2]).lower()}, {str(p[3]).lower()} }};\n        if (do_mirror[band]) {{\n"
            out_lines.append(mirror_logic)
        elif in_mdct and "SwapArray(curSpec, 256);" in line:
             out_lines.append("            SwapArray(curSpec, 256);\n")
        elif in_mdct and "maxLevels[band] = max;" in line:
            in_mdct = False
            out_lines.append(line)
        else:
            out_lines.append(line)
            
    with open("src/atrac3denc.cpp", "w") as f:
        f.writelines(out_lines)
    
    # Build and Verify
    subprocess.run(["cmd", "/c", "build_win.bat"], check=True, capture_output=True)
    result = subprocess.run(["python", "verify_atracdenc_snr.py"], check=True, capture_output=True, text=True)
    
    print(result.stdout)
    with open("mirror_sweep_results.txt", "a") as f:
        f.write(f"Mirroring {p}:\n{result.stdout}\n")

if __name__ == "__main__":
    if os.path.exists("mirror_sweep_results.txt"): os.remove("mirror_sweep_results.txt")
    
    # Test all 16 combinations (False=Normal, True=Mirrored)
    from itertools import product
    combos = list(product([False, True], repeat=4))
    
    for p in combos:
        test_mirroring(p)
