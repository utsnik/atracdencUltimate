def find_data_offset(f):
    with open(f, 'rb') as b:
        data = b.read(2048)
        offset = data.find(b'data')
        if offset != -1:
            size_bytes = data[offset+4:offset+8]
            size = int.from_bytes(size_bytes, 'little')
            print(f"File {f}: data chunk found at offset {offset}, size {size}")
            return offset + 8
    return -1

def compare_frames():
    ref_off = find_data_offset("reference.at3")
    enc_off = find_data_offset("sweep_tmp.at3.wav")
    
    if ref_off == -1 or enc_off == -1: return
    
    with open("reference.at3", 'rb') as r, open("sweep_tmp.at3.wav", 'rb') as e:
        r.seek(ref_off)
        e.seek(enc_off)
        
        # Read first 10 frames (3840 bytes)
        r_data = r.read(3840)
        e_data = e.read(3840)
        
    print(f"Comparing data frames...")
    # ATRAC3 frames often start with a common bit-pattern.
    # Check for byte-reversal or bit-swapping
    for i in range(100):
        if r_data[i] != e_data[i]:
            print(f"Frame mismatch at byte {i}: {r_data[i]:02x} vs {e_data[i]:02x}")
            print(f"Ref: {r_data[i:i+32].hex(' ')}")
            print(f"Enc: {e_data[i:i+32].hex(' ')}")
            
            # Check for bit-reversal
            rev_e = bin(e_data[i])[2:].zfill(8)[::-1]
            rev_e_byte = int(rev_e, 2)
            if rev_e_byte == r_data[i]:
                print(f"CRITICAL: Byte {i} is BIT-REVERSED!")
            
            # Check for byte-reversal within the frame
            # (First 8 bytes vs Last 8 bytes?)
            break
    else:
        print("Frames are identical in first 100 bytes.")

if __name__ == "__main__":
    compare_frames()
