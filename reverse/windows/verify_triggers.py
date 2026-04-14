import frida
import sys
import time

at3tool = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
wav_file = r"C:\Users\Igland\Antigravity\Ghidra\atracdenc\YOUtopia_source.wav"
out_at3 = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\out.at3"

pid = frida.spawn([at3tool, "-e", "-br", "132", wav_file, out_at3])
session = frida.attach(pid)

script_code = """
var base = Process.mainModule.base;

// Let's hook the known entry point at 0x49f0 and some others to see what triggers.
var targets = [0x49f0, 0x4d20, 0x36ea0, 0x37b40, 0x38e60, 0x36ce0, 0x36d40];

targets.forEach(function(rva) {
    Interceptor.attach(base.add(rva), {
        onEnter: function(args) {
            send({rva: "0x" + rva.toString(16), count: 1});
        }
    });
});
"""

counts = {}

def on_message(message, data):
    if message['type'] == 'send':
        rva = message['payload']['rva']
        counts[rva] = counts.get(rva, 0) + 1

script = session.create_script(script_code)
script.on('message', on_message)
script.load()

frida.resume(pid)
print("[*] Monitoring RVA triggers...")

while True:
    try:
        if session.is_detached:
            break
        time.sleep(1)
    except:
        break

print("[*] Summary of triggers:")
for rva, count in counts.items():
    print(f"RVA {rva}: {count} times")
