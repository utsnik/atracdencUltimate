def dump(f):
    try:
        with open(f, 'rb') as b:
            data = b.read(128)
            print(f"Hex dump for {f}:")
            for i in range(0, len(data), 16):
                row = data[i:i+16]
                hex_row = ' '.join(f"{b:02x}" for b in row)
                ascii_row = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in row)
                print(f"{i:04x}: {hex_row:<48} {ascii_row}")
    except Exception as e:
        print(f"Error reading {f}: {e}")

if __name__ == "__main__":
    dump("sony_silence.at3")
    dump("enc_silence.at3.wav")
