import subprocess
import os

cdb_path = r"C:\Program Files (x86)\Windows Kits\10\Debuggers\x86\cdb.exe"
if not os.path.exists(cdb_path):
    print("cdb.exe not found")
    exit(1)

at3tool_path = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
wav_path = r"C:\Users\Igland\Antigravity\Ghidra\atracdenc\YOUtopia_source.wav"
out_path = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\out.at3"

# Create a simple cdb script to just break at 004385ab, dump esp+510, and continue 10 times then quit
script_content = """
bp 004385ab ".printf \\"C=%x\\\\n\\\", dwo(esp+510); g"
g
"""
with open("script.cdb", "w") as f:
    f.write(script_content)

print("Running CDB...")
# Run cdb and capture output
try:
    result = subprocess.run(
        [cdb_path, "-cf", "script.cdb", "-G", "-o", at3tool_path, "-e", "-br", "132", wav_path, out_path],
        capture_output=True, text=True, timeout=5
    )
    print("CDB exited.")
    print("STDOUT:")
    # Print only lines containing our print format
    for line in result.stdout.splitlines():
        if "C=" in line:
            print(line)
except subprocess.TimeoutExpired as e:
    print("CDB timed out.")
    print("STDOUT so far:")
    for line in e.stdout.splitlines():
        if "C=" in line:
            print(line)

