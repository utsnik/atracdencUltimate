import subprocess
import os
import sys
import re

def run_test(swap_23, parts):
    # Modify atrac3_qmf.h
    qmf_path = r'src/atrac/at3/atrac3_qmf.h'
    with open(qmf_path, 'r') as f:
        lines = f.readlines()
    if swap_23:
        lines[39] = '        Qmf3.Analysis(Buf2.data(), subs[3], subs[2]);\n'
    else:
        lines[39] = '        Qmf3.Analysis(Buf2.data(), subs[2], subs[3]);\n'
    with open(qmf_path, 'w') as f:
        f.writelines(lines)

    # Modify atrac3denc.cpp
    cpp_path = r'src/atrac3denc.cpp'
    with open(cpp_path, 'r') as f:
        content = f.read()
    
    parts_str = " || ".join(parts) if parts else "false"
    inv_code = f"if ({parts_str})"
    
    # Use a more specific regex to avoid double replacement
    content = re.sub(r'if \(band == 1 \|\| band == 2\)|if \(band == 0 \|\| band == 1 \|\| band == 2 \|\| band == 3\)|if \(false\)|if \(band == 1 \|\| band == 3\)', inv_code, content)
    
    with open(cpp_path, 'w') as f:
        f.write(content)

    # Build
    proc = subprocess.run(['build_win.bat'], capture_output=True, text=True)
    if proc.returncode != 0:
        return -100
    
    # Verify
    result = subprocess.run(['python', 'verify_atracdenc_snr.py'], capture_output=True, text=True)
    snr = -100
    for line in result.stdout.split('\n'):
        if 'SNR:' in line:
            try:
                snr = float(line.split('SNR:')[1].split('dB')[0].strip())
            except:
                pass
    return snr

# All 16 permutations of inversion (for bands 0,1,2,3) + 2 permutations of swap 2/3 = 32 tests
# But we can skip band 0 inversion as it's almost certainly not inverted.
test_configs = []
for swap in [False, True]:
    for i1 in [False, True]:
        for i2 in [False, True]:
            for i3 in [False, True]:
                parts = []
                if i1: parts.append("band == 1")
                if i2: parts.append("band == 2")
                if i3: parts.append("band == 3")
                test_configs.append((swap, parts))

print(f"Starting brute force on {len(test_configs)} configurations...")
sys.stdout.flush()

best_snr = -100
best_config = None

for i, (swap, parts) in enumerate(test_configs):
    print(f"[{i+1}/{len(test_configs)}] Swap23={swap}, Inv={parts} ... ", end="")
    sys.stdout.flush()
    snr = run_test(swap, parts)
    print(f"SNR: {snr} dB")
    sys.stdout.flush()
    if snr > best_snr:
        best_snr = snr
        best_config = (swap, parts)

print(f"\nWINNER: SNR {best_snr} dB with Swap23={best_config[0]}, Inv={best_config[1]}")
