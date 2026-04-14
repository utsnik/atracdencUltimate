import sys

def scan_unit(data, name, is_side=False):
    bits = ''.join(f'{b:08b}' for b in data)
    print(f"--- Unit: {name} ---")
    if not is_side:
        print(f"Sync: {bits[0:8]}")
        offset = 8
    else:
        print(f"Side Flag: {bits[0:1]}")
        offset = 1
        
    print(f"B0 Cnt: {bits[offset:offset+3]}")
    print(f"B1 Cnt: {bits[offset+3:offset+6]}")
    # ... Simplified for quick look
    print(f"Tonal Flag (approx): {bits[offset+27]}")
    print(f"Block Count (5b): {bits[offset+28:offset+33]}")
    print(f"Coding Mode: {bits[offset+33]}")
    print(f"Raw Bits 32-64: {bits[32:64]}")

def scan(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    pos = data.find(b'\xA2')
    if pos == -1: return
    
    # Unit 0 (Assume 192 bytes)
    scan_unit(data[pos:pos+192], "Unit 0")
    
    # Unit 1 
    scan_unit(data[pos+192:pos+384], "Unit 1", is_side=True)

if __name__ == "__main__":
    scan(sys.argv[1])
