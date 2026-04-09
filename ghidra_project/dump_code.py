import sys
import struct

def dump_code(filepath, offset, size):
    with open(filepath, 'rb') as f:
        f.seek(offset)
        data = f.read(size)
        print(f"--- Dumping {size} bytes from offset {hex(offset)} ---")
        hex_str = " ".join(f"{b:02X}" for b in data)
        print(hex_str)

if __name__ == "__main__":
    dump_code(r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe", 0x17800, 512)
