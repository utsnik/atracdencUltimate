import sys

def compare_bits(f1, f2):
    with open(f1, 'rb') as b1, open(f2, 'rb') as b2:
        d1 = b1.read(1024)
        d2 = b2.read(1024)
        
    print(f"Comparing first 1024 bytes of {f1} vs {f2}")
    
    # Find first difference
    for i in range(min(len(d1), len(d2))):
        if d1[i] != d2[i]:
            print(f"First difference at byte {i}: {d1[i]:02x} vs {d2[i]:02x}")
            # Show context
            print(f"Ref: {d1[i:i+16].hex(' ')}")
            print(f"Enc: {d2[i:i+16].hex(' ')}")
            break
    else:
        print("First 1024 bytes are identical.")

if __name__ == "__main__":
    # Assuming at3tool.exe output is available as reference.at3
    # and atracdenc output is sweep_tmp.at3.wav
    compare_bits("reference.at3", "sweep_tmp.at3.wav")
