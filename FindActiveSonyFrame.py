import os

def find_active_frame(filename):
    with open(filename, "rb") as f:
        data = f.read()
    idx = data.find(b'data')
    if idx == -1: return
    
    payload = data[idx+8:]
    frame_sz = 192
    
    for f in range(len(payload) // frame_sz):
        frame = payload[f*frame_sz : (f+1)*frame_sz]
        unit0 = frame[:96]
        unit1 = frame[96:]
        
        # Count non-zero bytes
        nz0 = sum(1 for b in unit0 if b != 0)
        nz1 = sum(1 for b in unit1 if b != 0)
        
        if nz0 > 4 and nz1 > 4:
            print(f"First Active Frame: {f}")
            u0_bits = ''.join(format(b, '08b') for b in unit0[:4])
            u1_bits = ''.join(format(b, '08b') for b in unit1[:4])
            print(f"Unit 0 Start: {u0_bits}")
            print(f"Unit 1 Start: {u1_bits}")
            return f

if __name__ == "__main__":
    find_active_frame("audit_sony.at3")
