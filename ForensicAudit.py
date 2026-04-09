import os
import subprocess
import numpy as np
import wave

def create_pulse_wav(filename):
    with wave.open(filename, 'w') as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(44100)
        # 1024 samples of silence, then a pulse
        data = np.zeros(2048, dtype=np.int16)
        data[1024] = 10000 
        data[1025] = 10000
        f.writeframes(data.tobytes())

def forensic_audit():
    at3tool = r"..\ghidra\reverse\windows\at3tool.exe"
    atracdenc = r"build\src\atracdenc.exe"
    
    pulse_wav = "audit_pulse.wav"
    at3_sony = "audit_sony.at3"
    at3_mine = "audit_mine.at3"
    
    create_pulse_wav(pulse_wav)
    
    print("Encoding with Sony...")
    subprocess.run([at3tool, "-e", "-br", "132", pulse_wav, at3_sony], check=False, capture_output=True)
    
    print("Encoding with atracdenc...")
    subprocess.run([atracdenc, "-e", "atrac3", "-i", pulse_wav, "-o", at3_mine, "--bitrate", "132"], check=False, capture_output=True)
    
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
                frame = data[frame_start:frame_start+192]
                print(f"{tag} (First Frame - Hex):")
                print(frame.hex(" "))
                # Print bit representation of first few bytes
                print(f"{tag} (First 4 bytes - Bin):")
                for b in frame[:4]:
                    print(format(b, '08b'), end=" ")
                print()
            else:
                print(f"{tag}: 'data' chunk not found")

    dump_first_frame(at3_sony, "SONY")
    dump_first_frame(at3_mine, "MINE")

if __name__ == "__main__":
    forensic_audit()
