import os

def load_unit(filename, offset, size):
    with open(filename, "rb") as f:
        f.seek(offset)
        return f.read(size)

def audit_v2():
    sony_file = "audit_sony.at3"
    mine_file = "quality_verify_v2/encoded_atracdenc.at3"
    
    # Check Unit 1 (Offset 176)
    s_data = load_unit(sony_file, 176, 16)
    m_data = load_unit(mine_file, 176, 16)
    
    print("      01234567 89012345 67890123")
    print(f"SONY Unit 1: {' '.join(format(b, '08b') for b in s_data[:4])}")
    print(f"MINE Unit 1: {' '.join(format(b, '08b') for b in m_data[:4])}")

if __name__ == "__main__":
    audit_v2()
