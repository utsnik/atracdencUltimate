import os

def load_bits(filename):
    with open(filename, "rb") as f:
        data = f.read()
    idx = data.find(b'data')
    if idx == -1: return None
    frame = data[idx+8:idx+8+192]
    bits = ""
    for b in frame:
        bits += format(b, '08b')
    return bits

def compare():
    sony_bits = load_bits("audit_sony.at3")
    mine_bits = load_bits("quality_verify_v2/test_no.at3")
    
    if not sony_bits or not mine_bits:
        print("Missing files")
        return
        
    print(f"SONY Header : {sony_bits[:8]} {sony_bits[8:17]} {sony_bits[17:22]} {sony_bits[22:23]}")
    # Sony Silence likely has numBlocks=0 or something similar?
    
    print(f"MINE Header : {mine_bits[:8]} {mine_bits[8:17]} {mine_bits[17:22]} {mine_bits[22:23]}")

if __name__ == "__main__":
    compare()
