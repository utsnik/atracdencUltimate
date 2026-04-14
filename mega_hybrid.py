import os

def patch(b, off, v):
    b[off:off+4] = v.to_bytes(4, 'little')
    return b

try:
    with open('baseline_lp2.at3.wav', 'rb') as f:
        ref = f.read()
    
    with open('YOUtopia_PHASE49_SAMPLES.wav', 'rb') as f:
        my_all = f.read()
        my_dat = my_all[80:]
    
    sz = len(my_dat)
    num_frames = sz // 384
    fact_samples = (num_frames * 1024) - 1708
    
    h = bytearray(ref[:80])
    h = patch(h, 4, sz + 72)
    h = patch(h, 60, fact_samples)
    h = patch(h, 76, sz)
    
    with open('MEGA_HYBRID.wav', 'wb') as f:
        f.write(h)
        f.write(my_dat)
    
    print(f"MEGA_HYBRID created. Data: {sz} bytes, {num_frames} frames.")
except Exception as e:
    print(f"Error: {e}")
