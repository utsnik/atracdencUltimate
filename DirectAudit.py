import os

def load_bits(filename, offset, size):
    with open(filename, "rb") as f:
        f.seek(offset)
        data = f.read(size)
    bits = ""
    for b in data:
        bits += format(b, '08b')
    return bits

def audit():
    sony_file = "audit_sony.at3"
    mine_file = "quality_verify_v2/test_no.at3"
    
    if not os.path.exists(sony_file):
        print(f"Error: {sony_file} missing")
        return
        
    s_bits = load_bits(sony_file, 80, 48) # Compare first 48 bytes (Header + Gain + Pre-roll)
    m_bits = load_bits(mine_file, 80, 48)
    
    print("      01234567 89012345 67890123")
    print(f"SONY: {s_bits[:8]} {s_bits[8:17]} {s_bits[17:23]} {s_bits[23:31]}")
    print(f"MINE: {m_bits[:8]} {m_bits[8:17]} {m_bits[17:23]} {m_bits[23:31]}")
    
    for i in range(len(s_bits)):
        if s_bits[i] != m_bits[i]:
            print(f"DIVERGENCE at bit {i}: SONY={s_bits[i]}, MINE={m_bits[i]}")
            break

if __name__ == "__main__":
    audit()
