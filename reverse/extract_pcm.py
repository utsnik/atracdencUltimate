import os

files = {
    'sine_1k_5s.wav': r'C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\quality\input\sine_1k_5s.wav',
    'chirp_20_20k_5s.wav': r'C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\quality\input\chirp_20_20k_5s.wav',
    'multitone_5s.wav': r'C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\quality\input\multitone_5s.wav',
    'transient_5s.wav': r'C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\quality\input\transient_5s.wav',
    'YOUtopia.wav': r'C:\Users\Igland\Antigravity\Ghidra\atracdenc\YOUtopia.wav'
}

out_dir = r'C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse'

for name, path in files.items():
    if os.path.exists(path):
        with open(path, 'rb') as f:
            f.seek(44) # Skip WAV header
            data = f.read(4096 * 20) # Read 20 frames (81920 bytes)
            out_path = os.path.join(out_dir, name.replace('.wav', '.raw'))
            with open(out_path, 'wb') as out_f:
                out_f.write(data)
        print(f"Extracted {name}")
    else:
        print(f"FAILED: {path} not found")
