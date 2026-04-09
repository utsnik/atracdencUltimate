import os
import struct

def load_bits(filename, frame_idx=0):
    with open(filename, "rb") as f:
        data = f.read()
    idx = data.find(b'data')
    if idx == -1: return None
    
    # Each frame is 192 bytes.
    offset = idx + 8 + (frame_idx * 192)
    frame = data[offset : offset + 192]
    bits = ""
    for b in frame:
        bits += format(b, '08b')
    return bits

def compare():
    # Frame 1 is the first frame after silence in my current lead-in logic
    sony_bits = load_bits("audit_sony.at3", 1)
    mine_bits = load_bits("quality_verify_v2/encoded_atracdenc.at3", 1)
    
    if not sony_bits or not mine_bits:
        print("Missing files or frame")
        return
        
    print(f"Frame 1 (Real Signal) Comparison:")
    print(f"SONY Unit 0 Header: {sony_bits[:8]} {sony_bits[8:17]} {sony_bits[17:22]} {sony_bits[22:23]}")
    print(f"MINE Unit 0 Header: {mine_bits[:8]} {mine_bits[8:17]} {mine_bits[17:22]} {mine_bits[22:23]}")
    
    print(f"SONY Unit 1 Header: {sony_bits[768:768+8]} {sony_bits[768+8:768+17]} {sony_bits[768+17:768+22]} {sony_bits[768+22:768+23]}")
    print(f"MINE Unit 1 Header: {mine_bits[768:768+8]} {mine_bits[768+8:768+17]} {mine_bits[768+17:768+22]} {mine_bits[768+22:768+23]}")

if __name__ == "__main__":
    compare()
