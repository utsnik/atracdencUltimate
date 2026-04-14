import sys

def read_at3_payload(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    # Find first syncword 0xA2
    pos = data.find(b'\xA2')
    if pos == -1:
        # Try A3
        pos = data.find(b'\xA3')
    if pos == -1:
        return None
    print(f"Found sync in {filename} at offset {pos} (hex {hex(pos)})")
    return data[pos:pos+192]

def to_bits(data):
    return ''.join(f'{b:08b}' for b in data)

def main():
    if len(sys.argv) < 3:
        print("Usage: python bitstream_forensics.py <ref> <mine>")
        return
        
    ref_file = sys.argv[1]
    mine_file = sys.argv[2]
    
    ref = read_at3_payload(ref_file)
    mine = read_at3_payload(mine_file)

    if not ref or not mine:
        print("Could not find payload in one of the files")
        return

    ref_bits = to_bits(ref)
    mine_bits = to_bits(mine)

    print(f"REF:  {ref_bits[:128]}")
    print(f"MINE: {mine_bits[:128]}")

    for i in range(min(len(ref_bits), len(mine_bits))):
        if ref_bits[i] != mine_bits[i]:
            print(f"First difference at bit {i}: REF={ref_bits[i]}, MINE={mine_bits[i]}")
            # Context
            start = max(0, i - 16)
            end = min(len(ref_bits), i + 32)
            print(f"Context: {ref_bits[start:i]}[{ref_bits[i]}] vs {mine_bits[start:i]}[{mine_bits[i]}]")
            break

if __name__ == "__main__":
    main()
