import struct

def search_pattern(filename, pattern):
    with open(filename, 'rb') as f:
        data = f.read()
    
    idx = data.find(pattern)
    if idx != -1:
        print(f"Pattern found at offset 0x{idx:X}")
        return idx
    return -1

def solve():
    filename = r'c:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe'
    
    # ATRAC3 window is often 256 or 512 points.
    # Case 1: N=256 (for 512 MDCT), win[0] = sin(0.5 * pi / 512) = 0.0030679612
    # Float: 49 90 48 3B (LE)
    
    # Case 2: N=128 (for 256 MDCT), win[0] = sin(0.5 * pi / 256) = 0.0061358846
    # Float: 75 80 C8 3B (LE)
    
    # Case 3: Raised sine? ATRAC3 doesn't typically use it, but our current code did.
    
    # Let's search for 0.70710678 (sqrt(0.5)) - extremely common in MDCT
    # Float32: F3 04 35 3F
    # Float64: 6A 08 E1 12 F0 0B E6 3F
    
    patterns = [
        ("sqrt(0.5) float32", struct.pack('<f', 0.70710678)),
        ("sqrt(0.5) float64", struct.pack('<d', 0.7071067811865476)),
        ("sin(0.5*pi/256) float32", struct.pack('<f', 0.0061358846)),
        ("sin(0.5*pi/512) float32", struct.pack('<f', 0.0030679612)),
        ("Table address 0x452340", b'\x40\x23\x45\x00'),
    ]
    
    for name, p in patterns:
        print(f"Searching for {name}: {p.hex(' ').upper()}")
        search_pattern(filename, p)

if __name__ == "__main__":
    solve()
