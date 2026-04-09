import wave
import numpy as np
import subprocess
import os

def generate_silence():
    at3tool = r"..\ghidra\reverse\windows\at3tool.exe"
    atracdenc = r"build\src\atracdenc.exe"
    if not os.path.exists(atracdenc):
        atracdenc = r"build2\src\atracdenc.exe"

    workdir = "silence_audit"
    os.makedirs(workdir, exist_ok=True)
    
    wav_file = os.path.join(workdir, "silence.wav")
    at3_file = os.path.join(workdir, "silence_atracdenc.at3")
    
    # 5 seconds of silence
    with wave.open(wav_file, 'w') as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(44100)
        f.writeframes(np.zeros(44100 * 5 * 2, dtype=np.int16).tobytes())
    
    print("Encoding silence with atracdenc...")
    subprocess.run([atracdenc, "-e", "atrac3", "-i", wav_file, "-o", at3_file, "--bitrate", "132"], check=True)
    
    # Audit
    # Sony Silence Frame (known from previous turns)
    # Unit 0: A2 00 00 ...
    # Unit 1: 00 00 00 ...
    
    with open(at3_file, "rb") as f:
        f.seek(80)
        u0 = f.read(8)
        f.seek(176)
        u1 = f.read(8)
        
    print(f"MINE SU0 Header: {u0.hex()}")
    print(f"MINE SU1 Header: {u1.hex()}")

if __name__ == "__main__":
    generate_silence()
