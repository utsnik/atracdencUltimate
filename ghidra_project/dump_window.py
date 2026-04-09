import struct

def dump_floats(filename, offset, count):
    with open(filename, 'rb') as f:
        f.seek(offset)
        raw = f.read(count * 4)
    
    return struct.unpack(f'<{count}f', raw)

def solve():
    filename = r'c:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe'
    offset = 0x52340
    
    print(f"--- Dumping 512 floats from 0x{offset:X} ---")
    coeffs = dump_floats(filename, offset, 512)
    
    # Format as C++ array
    print("const float SonyEncodeWindow[512] = {")
    for i in range(0, 512, 8):
        row = coeffs[i:i+8]
        print("    " + ", ".join(f"{c:.10f}f" for c in row) + ",")
    print("};")

if __name__ == "__main__":
    solve()
