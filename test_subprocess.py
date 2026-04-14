import subprocess
import os

tool = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
print(f"Testing tool existence: {os.path.exists(tool)}")

try:
    res = subprocess.run([tool, "-?"], capture_output=True, text=True)
    print(f"Success! Return code: {res.returncode}")
    print(f"Stdout: {res.stdout}")
except Exception as e:
    print(f"Failed with exception: {e}")
