import struct
import os

def find_window_tables():
    file_path = r'C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe'
    if not os.path.exists(file_path):
        print("Binary not found")
        return
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # 1. Search for 512-point float arrays with symmetry or PR condition
    #    MDCT window of size N=512: w[i]**2 + w[i + N/2]**2 = 1.0 for i in 0..N/2
    N = 512
    step = 4
    for i in range(0, len(data) - N * 4, step):
        try:
            # Check PR condition for several points
            fits = True
            for k in [0, 64, 128]:
                w_k = struct.unpack('<f', data[i + k*4 : i + (k+1)*4])[0]
                w_mid_k = struct.unpack('<f', data[i + (k+256)*4 : i + (k+257)*4])[0]
                if abs(w_k**2 + w_mid_k**2 - 1.0) > 0.001:
                    fits = False
                    break
            if fits:
                print(f"Found potential 512-float window at {hex(i)}")
                # Print first 4 values
                vals = [struct.unpack('<f', data[i+j*4:i+(j+1)*4])[0] for j in range(4)]
                print(f"Values: {vals}")
        except:
            continue

    # 2. Search for 256-point float arrays
    N2 = 256
    for i in range(0, len(data) - N2 * 4, step):
        try:
            # Check if it grows from 0 to 1
            w0 = struct.unpack('<f', data[i:i+4])[0]
            w255 = struct.unpack('<f', data[i+255*4:i+256*4])[0]
            if 0 <= w0 < 0.01 and 0.99 < w255 <= 1.01:
                # Check for smooth monotonicity
                w128 = struct.unpack('<f', data[i+128*4:i+129*4])[0]
                if 0.6 < w128 < 0.8: # sin(pi/4) approx 0.707
                    print(f"Found potential 256-float window half at {hex(i)}")
                    vals = [struct.unpack('<f', data[i+j*4:i+(j+1)*4])[0] for j in range(4)]
                    print(f"Values: {vals}")
        except:
            continue

if __name__ == "__main__":
    find_window_tables()
