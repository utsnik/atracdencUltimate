
import struct
import os

def patch_header(filename, num_frames, frame_size):
    # Total samples for real YOUtopia (approx 242.6s)
    total_samples = num_frames * 1024
    data_size = num_frames * frame_size
    file_size = 80 + data_size
    
    # WAV Header (80 bytes)
    header = bytearray(80)
    
    # RIFF (0-11)
    header[0:4] = b'RIFF'
    header[4:8] = struct.pack('<I', file_size - 8)
    header[8:12] = b'WAVE'
    
    # fmt  (12-43) - 32 bytes
    header[12:16] = b'fmt '
    header[16:20] = struct.pack('<I', 32)
    header[20:22] = struct.pack('<H', 0x0270) # audio_format
    header[22:24] = struct.pack('<H', 2)      # num_channels
    header[24:28] = struct.pack('<I', 44100)  # sample_rate
    header[28:32] = struct.pack('<I', 16538)  # byte_rate
    header[32:34] = struct.pack('<H', 384)    # block_align
    header[34:36] = struct.pack('<H', 0)      # bits_per_sample
    header[36:38] = struct.pack('<H', 14)     # extradata_size
    
    # Extradata (38-51)
    header[38:40] = struct.pack('<H', 1)      # unknown0
    header[40:44] = struct.pack('<I', 1024)   # samples_per_block (One frame per block)
    header[44:46] = struct.pack('<H', 1)      # coding_mode (1 = Joint Stereo)
    header[46:48] = struct.pack('<H', 1)      # coding_mode2
    header[48:50] = struct.pack('<H', 1)      # unknown1
    header[50:52] = struct.pack('<H', 0)      # unknown2
    
    # fact (52-63) - 12 bytes
    header[52:56] = b'fact'
    header[56:60] = struct.pack('<I', 4)
    header[60:64] = struct.pack('<I', total_samples)
    
    # data (64-71)
    header[64:68] = b'data'
    header[68:72] = struct.pack('<I', data_size)
    
    print(f"Patching {filename} Header...")
    with open(filename, 'r+b') as f:
        f.seek(0)
        f.write(header)
    print("Done.")

if __name__ == "__main__":
    # YOUtopia_AUDIBLE_FINAL_V2.wav matches these frame counts (4,013,640 / 384 = 10,452.18?) 
    # Wait, the file size was 4013640. 
    # Header was 80. Data is 4013560. 
    # 4013560 / 384 = 10451.9? 
    # I'll use exactly 10452 frames.
    patch_header("YOUtopia_AUDIBLE_FINAL_V2.wav", 10452, 384)
