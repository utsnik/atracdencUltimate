import sys

def scan(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    pos = data.find(b'\xA2')
    if pos == -1: return None
    payload = data[pos:pos+64]
    bits = ''.join(f'{b:08b}' for b in payload)
    
    print(f"File: {filename} (Offset {pos})")
    print(f"Sync: {bits[0:8]}")
    print(f"B0 Cnt: {bits[8:11]}")
    print(f"B1 Cnt: {bits[11:14]}")
    print(f"B1 P0: Lvl={bits[14:18]}, Loc={bits[18:23]}")
    print(f"B2 Cnt: {bits[23:26]}")
    print(f"B2 P0: Lvl={bits[26:30]}, Loc={bits[30:35]}")
    print(f"Tonal Flag: {bits[35]}")
    print(f"Block Count (5b): {bits[36:41]}")
    print(f"Coding Mode: {bits[41]}")
    print("Precisions (next 32 bits):")
    for i in range(16):
        print(f"B{i}: {bits[42+i*3:45+i*3]} ", end="")
    print("\n")

if __name__ == "__main__":
    scan(sys.argv[1])
