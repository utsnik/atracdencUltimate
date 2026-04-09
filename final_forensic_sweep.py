import os
import subprocess
import itertools
import numpy as np
import shutil

# Paths
ATRACDENC = r"build\src\atracdenc.exe"
AT3TOOL = r"..\ghidra\reverse\windows\at3tool.exe"
SIGNS_FILE = "signs.txt"
MAPPING_FILE = "mapping.txt"
WORKDIR = "final_forensic_run"
ORIG_WAV = os.path.join(WORKDIR, "orig.wav")
AT3_FILE = os.path.join(WORKDIR, "encoded.at3")
DEC_WAV = os.path.join(WORKDIR, "decoded.wav")

def run_audit(mapping, signs):
    with open(MAPPING_FILE, "w") as f: f.write(" ".join(map(str, mapping)))
    with open(SIGNS_FILE, "w") as f: f.write(" ".join(map(str, signs)))
    
    try:
        subprocess.run([ATRACDENC, "-e", "atrac3", "-i", ORIG_WAV, "-o", AT3_FILE, "--bitrate", "132"], 
                       check=True, capture_output=True)
        subprocess.run([AT3TOOL, "-d", AT3_FILE, DEC_WAV], check=True, capture_output=True)
        
        os.makedirs("quality_verify_v2", exist_ok=True)
        shutil.copy(ORIG_WAV, os.path.join("quality_verify_v2", "orig.wav"))
        shutil.copy(DEC_WAV, os.path.join("quality_verify_v2", "dec_by_sony.wav"))
        
        result = subprocess.run(["python", "ForensicAudit.py"], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return str(e)

def parse_audit(output):
    lines = output.strip().split("\n")
    corrs = []
    pols = []
    for line in lines:
        if "|" in line and "Band" not in line and "-" not in line:
            parts = line.split("|")
            try:
                corrs.append(float(parts[1].strip()))
                pols.append(parts[3].strip())
            except: pass
    return corrs, pols

if __name__ == "__main__":
    os.makedirs(WORKDIR, exist_ok=True)
    SRC_ORIG = os.path.join("quality_verify_v2", "orig.wav")
    if os.path.exists(SRC_ORIG):
        shutil.copy(SRC_ORIG, ORIG_WAV)
    
    # 4 core mappings to test
    mappings = [(0, 2, 4, 6), (0, 2, 6, 4), (0, 4, 6, 2), (0, 6, 4, 2)]
    
    print("Final Forensic Audit Sweep (Fixed QMF)...")
    for m in mappings:
        # Run once with positive signs to detect required polarities
        out = run_audit(m, (1, 1, 1, 1))
        cs, ps = parse_audit(out)
        if cs:
            print(f"Mapping {m}: Corrs = {cs} Pols = {ps} Sum = {sum(cs):.4f}")
            if sum(cs) > 2.0:
                # Try correcting signs based on Audit Polarity
                new_signs = [1 if p == "+" else -1 for p in ps]
                if any(s == -1 for s in new_signs):
                    print(f"  Trying corrected signs: {new_signs}")
                    out_s = run_audit(m, new_signs)
                    cs_s, ps_s = parse_audit(out_s)
                    print(f"  Result: Corrs = {cs_s} Sum = {sum(cs_s):.4f}")
