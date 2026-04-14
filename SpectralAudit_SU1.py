import os

def to_bits(byte_data):
    return "".join(f"{b:08b}" for b in byte_data)

def spectral_audit_su1():
    sony_file = "tone_sony.at3"
    mine_file = "tone_mine.at3"
    
    with open(sony_file, "rb") as f:
        sony_data = f.read()
    with open(mine_file, "rb") as f:
        mine_data = f.read()

    # Offset 80 is start of data (SU0)
    # SU1 starts at +96
    offsets = [80 + 96, 80 + 192 + 96, 80 + 384 + 96]
    
    for i, off in enumerate(offsets):
        s_su = sony_data[off:off+96]
        m_su = mine_data[off:off+96]
        
        print(f"=== Frame {i} SU1 (Offset {off}) ===")
        s_bits = to_bits(s_su)
        m_bits = to_bits(m_su)
        
        print(f"SONY: {s_bits[:32]}")
        print(f"MINE: {m_bits[:32]}")
        print()

if __name__ == "__main__":
    spectral_audit_su1()
