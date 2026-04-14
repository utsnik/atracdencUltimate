import os
import struct

def patch_at3(filename):
    if not os.path.exists(filename): return
    size = os.path.getsize(filename)
    data_size = size - 72
    # Standard LP2 padding sync
    padding = (384 - (data_size % 384)) % 384
    if padding > 0:
        with open(filename, 'ab') as f:
            f.write(b'\x00' * padding)
        size += padding
        data_size += padding
    
    samples = (data_size // 384) * 1024
    
    with open(filename, 'r+b') as f:
        # RIFF Size
        f.seek(4)
        f.write(struct.pack('<I', size - 8))
        # Samples (fact)
        f.seek(60)
        f.write(struct.pack('<I', samples))
        # Data Size
        f.seek(68)
        f.write(struct.pack('<I', data_size))
    print(f"SUCCESS: {filename} patched. Size: {size}, Data: {data_size}, Samples: {samples}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        patch_at3(sys.argv[1])
