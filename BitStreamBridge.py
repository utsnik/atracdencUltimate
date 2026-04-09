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
        
    print(f"SONY START: {sony_bits[:64]}")
    print(f"MINE START: {mine_bits[:64]}")
    
    # Find first difference
    for i in range(min(len(sony_bits), len(mine_bits))):
        if sony_bits[i] != mine_bits[i]:
            print(f"First Difference at bit {i}: SONY={sony_bits[i]}, MINE={mine_bits[i]}")
            # Snippet
            start = max(0, i - 10)
            end = i + 20
            print(f"SONY Context: ... {sony_bits[start:i]}[{sony_bits[i]}]{sony_bits[i+1:end]} ...")
            print(f"MINE Context: ... {mine_bits[start:i]}[{mine_bits[i]}]{mine_bits[i+1:end]} ...")
            break

if __name__ == "__main__":
    compare()
