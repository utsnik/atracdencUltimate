import struct
import os

pe_path = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
with open(pe_path, "rb") as f:
    # Read DOS header
    dos_header = f.read(64)
    e_lfanew = struct.unpack_from("<I", dos_header, 0x3C)[0]
    
    # Read PE header
    f.seek(e_lfanew)
    pe_sig = f.read(4)
    if pe_sig != b"PE\0\0":
        print("Not a PE file")
        exit(1)
        
    # File Header is 20 bytes
    # Optional Header starts after that
    f.seek(e_lfanew + 4 + 20)
    opt_header_magic = struct.unpack("<H", f.read(2))[0]
    
    # PE32 (0x10b) or PE32+ (0x20b)
    if opt_header_magic == 0x10b:
        # PE32
        # DllCharacteristics is at offset 70 in Optional Header
        f.seek(e_lfanew + 4 + 20 + 70)
        dll_char = struct.unpack("<H", f.read(2))[0]
    else:
        # PE32+
        # DllCharacteristics is at offset 70 in Optional Header
        f.seek(e_lfanew + 4 + 20 + 70)
        dll_char = struct.unpack("<H", f.read(2))[0]
        
    is_aslr = (dll_char & 0x0040) != 0 # IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE
    print(f"ASLR Enabled: {is_aslr}")
    print(f"DllCharacteristics: {hex(dll_char)}")

