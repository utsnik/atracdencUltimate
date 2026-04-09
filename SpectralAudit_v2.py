import os

def to_bits(byte_data):
    return "".join(f"{b:08b}" for b in byte_data)

def spectral_audit():
    sony_file = "tone_sony.at3"
    mine_file = "tone_mine.at3"
    
    with open(sony_file, "rb") as f:
        sony_data = f.read()
    with open(mine_file, "rb") as f:
        mine_data = f.read()

    # Offset 80 is start of data (Frame 0, SU0)
    # Frame size 384 (dual-frame block), so SU0 is at 80, SU1 is at 80+96, SU2 is at 80+192, SU3 is at 80+288
    # Let's inspect SU0 and SU2 (the master units of the two frames in the first block)
    
    offsets = [80, 80 + 192, 80 + 384, 80 + 384 + 192]
    
    for i, off in enumerate(offsets):
        s_su = sony_data[off:off+96]
        m_su = mine_data[off:off+96]
        
        print(f"--- Frame {i} (Offset {off}) ---")
        s_bits = to_bits(s_su)
        m_bits = to_bits(m_su)
        
        # Print first 64 bits to see header + allocation
        print(f"SONY: {s_bits[:8]} | {s_bits[8:16]} | {s_bits[16:24]} | {s_bits[24:32]} | {s_bits[32:48]} | {s_bits[48:64]}")
        print(f"MINE: {m_bits[:8]} | {m_bits[8:16]} | {m_bits[16:24]} | {m_bits[24:32]} | {m_bits[32:48]} | {m_bits[48:64]}")
        
        if s_bits[:64] != m_bits[:64]:
            print("!!! Divergence in first 64 bits !!!")
            for bit_i in range(64):
                if s_bits[bit_i] != m_bits[bit_i]:
                    print(f"First diff at bit {bit_i}: Sony={s_bits[bit_i]}, Mine={m_bits[bit_i]}")
                    break
        print()

if __name__ == "__main__":
    spectral_audit()
