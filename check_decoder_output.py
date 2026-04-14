import subprocess
import os
import struct

atracdenc = r"build\src\atracdenc.exe"
at3tool = r"..\at3tool.exe" # Adjusted path based on previous turns
orig_wav = r"quality_verify_v2\orig.wav"
encoded_at3 = "diagnostic.at3"
decoded_wav = "diagnostic_decoded.wav"

def run():
    if not os.path.exists(orig_wav):
        print(f"Error: {orig_wav} not found")
        return

    # 1. Encode
    print("Encoding...")
    cmd_e = [atracdenc, "-e", "atrac3", "-i", orig_wav, "-o", encoded_at3, "--bitrate", "132", "--notonal", "--nogaincontrol"]
    res_e = subprocess.run(cmd_e, capture_output=True, text=True)
    if res_e.returncode != 0:
        print(f"Encoder failed: {res_e.stderr}")
        return

    print(f"Encoded file size: {os.path.getsize(encoded_at3)} bytes")

    # 2. Decode
    print("Decoding with Sony at3tool.exe...")
    if not os.path.exists(at3tool):
        # Try local path
        if os.path.exists("at3tool.exe"):
            tool_path = "at3tool.exe"
        else:
            print("Error: at3tool.exe not found")
            return
    else:
        tool_path = at3tool

    cmd_d = [tool_path, "-d", encoded_at3, decoded_wav]
    res_d = subprocess.run(cmd_d, capture_output=True, text=True)
    print(f"Decoder stdout: {res_d.stdout}")
    print(f"Decoder stderr: {res_d.stderr}")

    if not os.path.exists(decoded_wav):
        print("Error: Decoded WAV was not created")
        return

    size = os.path.getsize(decoded_wav)
    print(f"Decoded WAV size: {size} bytes")

    if size > 44:
        with open(decoded_wav, 'rb') as f:
            f.seek(44) # Skip header
            data = f.read(100)
            print(f"First 100 bytes of audio: {data.hex()}")
            samples = struct.unpack(f'<{len(data)//2}h', data)
            print(f"First few samples: {samples[:10]}")
    else:
        print("Decoded WAV is empty (header only)")

if __name__ == "__main__":
    run()
