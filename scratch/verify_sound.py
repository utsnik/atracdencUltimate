
import sys
import struct
import math
import numpy as np

def manual_rms_check(filename):
    print(f"--- ANALYZING {filename} ---")
    with open(filename, 'rb') as f:
        data = f.read()

    # Find the first Frame 1 Sync (A2) after Frame 0 (384 bytes)
    # Header 72 + Frame 0 384 = 456 (0x1c8)
    offset = 456
    if data[offset] != 0xA2:
        print(f"ERROR: Sync word A2 not found at 0x1c8. Found: {hex(data[offset])}")
        return

    print("Sync word A2 found at 0x1c8.")
    # Extract 384 bytes of Frame 1
    frame_data = data[offset:offset+384]
    
    # Check for non-zero entropy in the spectral area (after bit 64)
    spectral_payload = frame_data[8:384]
    nonzero_count = sum(1 for b in spectral_payload if b != 0)
    
    print(f"Non-zero bytes in spectral payload (376 bytes): {nonzero_count}")
    
    if nonzero_count == 0:
        print("RESULT: FAILURE - Spectral payload is COMPLETELY SILENT (All Zeros).")
    elif nonzero_count < 20: 
        print(f"RESULT: WARNING - Extremely low entropy ({nonzero_count} bytes). Might be nearly silent.")
    else:
        print(f"RESULT: SUCCESS - Bitstream contains {nonzero_count} bytes of active spectral data.")
        print("The music IS encoded in the file.")

    # Check for Infinity/NaN signatures (often 0xFF or 0x7F patterns if float-to-int failed)
    if b'\xff\xff\xff\xff' in frame_data:
        print("WARNING: Possible saturation/infinity detected in bitstream.")

    print(f"First 16 bytes of frame data: {frame_data[:16].hex()}")

if __name__ == "__main__":
    manual_rms_check("YOUtopia_v13_GOLD.at3")
