import os
import subprocess

def test_byte(first_byte):
    at3tool = r"..\ghidra\reverse\windows\at3tool.exe"
    input_at3 = "quality_verify_v2/test_no.at3"
    test_at3 = "brute_test.at3"
    output_wav = "brute_out.wav"
    
    if os.path.exists(output_wav): os.remove(output_wav)
    
    with open(input_at3, "rb") as f:
        data = bytearray(f.read())
    
    idx = data.find(b'data')
    if idx == -1: return False
    
    # Modify ONLY the first byte of the first frame
    data[idx + 8] = first_byte
    
    with open(test_at3, "wb") as f:
        f.write(data)
    
    # at3tool returns non-zero on error
    res = subprocess.run([at3tool, "-d", test_at3, output_wav], capture_output=True)
    
    if res.returncode == 0 and os.path.exists(output_wav):
        # Even if it returns 0, check if it's too small (meaning it failed early)
        if os.path.getsize(output_wav) > 1000:
            return True
    return False

def brute_force():
    results = []
    print("Surgical Brute-force for 0x1000105 error...")
    for b in range(256):
        if test_byte(b):
            print(f"CRITICAL SUCCESS: Byte {hex(b)} leads to valid decode.")
            results.append(b)
    
    if not results:
        print("Still failing. The alignment error is likely deeper (not just the first byte).")

if __name__ == "__main__":
    brute_force()
