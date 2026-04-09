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
WORKDIR = "forensic_sweep_run"
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
        
        # Run ForensicAudit on the files in WorkDir
        # Since ForensicAudit.py is hardcoded to quality_verify_v2, we need to adapt it
        import shutil
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
    for line in lines:
        if "|" in line and "Band" not in line and "-" not in line:
            parts = line.split("|")
            try:
                corrs.append(float(parts[1].strip()))
            except: pass
    return corrs

if __name__ == "__main__":
    os.makedirs(WORKDIR, exist_ok=True)
    # Use existing orig.wav
    shutil.copy(os.path.join("quality_verify_v2", "orig.wav"), ORIG_WAV)
    
    mappings = [(0, 2, 6, 4), (0, 2, 4, 6), (0, 4, 6, 2), (0, 6, 4, 2)]
    signs = (1, 1, 1, 1) # Fix signs for now, mapping is the main variable
    
    print("Forensic Mapping Sweep...")
    for m in mappings:
        out = run_audit(m, signs)
        cs = parse_audit(out)
        print(f"Mapping {m}: Corrs = {cs} Sum = {sum(cs):.4f}")
