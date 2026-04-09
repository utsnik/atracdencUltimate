import os

with open(r'C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe', 'rb') as f:
    data = f.read()

# Pattern for 0x452340 (little-endian: 40 23 45 00)
pattern = b'\x40\x23\x45\x00'
pos = 0
found = False

while True:
    pos = data.find(pattern, pos)
    if pos == -1:
        break
    print(f'Found reference at file offset: {hex(pos)}')
    found = True
    pos += 1

if not found:
    print("Pattern not found.")
