import sys

def scan_v13(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    
    # Find first sync (Frame 0 start at 0x50)
    pos = 0x50
    frame = data[pos:pos+384]
    bits = ''.join(f'{b:08b}' for b in frame)
    
    print(f"Sync: {bits[0:8]}")
    print(f"B0-B2 Cnt: {bits[8:11]} {bits[11:14]} {bits[14:17]}")
    
    # Tonal
    print(f"Tonal Flag: {bits[27]}") # Approx
    
    # Block Count
    print(f"Block Count (5b): {bits[28:33]}")
    print(f"Coding Mode: {bits[33]}")
    
    # Precisions
    offset = 34
    num_blocks = int(bits[28:33], 2) + 1
    print(f"Num Blocks: {num_blocks}")
    precisions = []
    for i in range(num_blocks):
        prec = int(bits[offset:offset+3], 2)
        precisions.append(prec)
        offset += 3
    print(f"Precisions: {precisions}")
    
    # Scale Factors
    print(f"SF Start Offset: {offset}")
    sfs = []
    for i in range(num_blocks):
        if precisions[i] > 0:
            sf = int(bits[offset:offset+6], 2)
            sfs.append(sf)
            offset += 6
    print(f"Scale Factors: {sfs}")
    
    # Spectral Checks
    print(f"Spectral Start Offset: {offset}")
    spectral_bits = bits[offset:offset+32]
    print(f"First 32 Spectral Bits: {spectral_bits}")

if __name__ == "__main__":
    scan_v13(sys.argv[1])
