import os
import subprocess
import numpy as np
import wave

def create_pulse_wav(filename):
    with wave.open(filename, 'w') as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(44100)
        # 10240 samples to ensure at least a few frames
        data = np.zeros(20480, dtype=np.int16)
        data[4096:4100] = 10000 
        f.writeframes(data.tobytes())

def forensic_audit():
    at3tool = r"..\ghidra\reverse\windows\at3tool.exe"
    atracdenc = r"build\src\atracdenc.exe"
    
    pulse_wav = "audit_pulse.wav"
    at3_sony = "audit_sony.at3"
    at3_mine = "audit_mine.at3"
    
    create_pulse_wav(pulse_wav)
    
    print("Encoding with Sony...")
    # Add absolute path just in case
    # Try different command line if standard -e fails
    res = subprocess.run([at3tool, "-e", "-br", "132", pulse_wav, at3_sony], capture_output=True)
    if res.returncode != 0:
        print(f"Sony Encoder Failed: {res.stderr.decode(errors='replace')}")
    
    print("Encoding with atracdenc...")
    subprocess.run([atracdenc, "-e", "atrac3", "-i", pulse_wav, "-o", at3_mine, "--bitrate", "132"], capture_output=True)
    
    def dump_first_frame(filename, tag):
        if not os.path.exists(filename):
            print(f"{tag}: File not found")
            return
        with open(filename, "rb") as f:
            data = f.read()
            # Find 'data' chunk
            idx = data.find(b'data')
            if idx != -1:
                frame_start = idx + 8
                # In ATRAC3 WAV, there might be some padding or extra info
                # But usually the first frame is right after 'data' + size
                frame = data[frame_start:frame_start+192]
                print(f"{tag} (First Frame - Hex):")
                print(frame.hex(" "))
                print(f"{tag} (First 4 bytes - Bin):")
                for b in frame[:4]:
                    print(format(b, '08b'), end=" ")
                print()
            else:
                # If no 'data' chunk, maybe it's raw?
                print(f"{tag}: 'data' chunk not found, dumping first 32 bytes")
                print(data[:32].hex(" "))

    dump_first_frame(at3_sony, "SONY")
    dump_first_frame(at3_mine, "MINE")

if __name__ == "__main__":
    forensic_audit()
