import os
import subprocess

def test_bit_shift(shift_bits):
    at3tool = r"..\ghidra\reverse\windows\at3tool.exe"
    input_at3 = "quality_verify_v2/test_no.at3"
    test_at3 = "shift_test.at3"
    output_wav = "shift_out.wav"
    
    if os.path.exists(output_wav): os.remove(output_wav)
    
    with open(input_at3, "rb") as f:
        data = bytearray(f.read())
    
    idx = data.find(b'data')
    if idx == -1: return False
    
    # Extract first frame (192 bytes)
    frame_start = idx + 8
    frame = data[frame_start:frame_start+192]
    
    # Convert frame to bitstream
    bits = ""
    for b in frame:
        bits += format(b, '08b')
    
    # Shift bitstream (add leading zeros or skip leading bits)
    if shift_bits > 0:
        new_bits = ('0' * shift_bits) + bits[:-shift_bits]
    elif shift_bits < 0:
        new_bits = bits[-shift_bits:] + ('0' * -shift_bits)
    else:
        new_bits = bits
        
    # Convert bits back to bytes
    new_frame = bytearray()
    for i in range(0, len(new_bits), 8):
        new_frame.append(int(new_bits[i:i+8], 2))
    
    # Replace frame in data
    data[frame_start:frame_start+192] = new_frame
    
    with open(test_at3, "wb") as f:
        f.write(data)
    
    res = subprocess.run([at3tool, "-d", test_at3, output_wav], capture_output=True)
    return res.returncode == 0 and os.path.exists(output_wav) and os.path.getsize(output_wav) > 1000

def bit_sweep():
    print("Sweeping bit shifts for ATRAC3 LP2...")
    for shift in range(-8, 9):
        if test_bit_shift(shift):
            print(f"BINGO! Shift of {shift} bits worked!")
            return
    print("Bit sweep failed. The error is likely not a simple bit-shift.")

if __name__ == "__main__":
    bit_sweep()
