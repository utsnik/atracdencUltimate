import frida
import sys
import json
import time

AT3TOOL = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
WAV = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\quality\input\chirp_20_20k_5s.wav"

def on_message(message, data):
    if message['type'] == 'send':
        print(f"[*] {message['payload']}")
    else:
        print(message)

# We trace a broad range to see if the user's RVAs (36d40, 37b40, 38e60) are hit.
# lp2_main is 3d1f0.
SCRIPT = """
var base = Process.mainModule.base;
var hits = {};

// Hook candidate RVAs to see if they are hit
var targets = [0x36d40, 0x37b40, 0x38e60, 0x3d1f0, 0x3d080, 0x3ceb0, 0x414f0];
targets.forEach(function(rva) {
    Interceptor.attach(base.add(rva), {
        onEnter: function(args) {
            hits[rva] = (hits[rva] || 0) + 1;
            send("Hit RVA: " + rva.toString(16) + " count: " + hits[rva]);
        }
    });
});
"""

if __name__ == "__main__":
    pid = frida.spawn([AT3TOOL, "-e", "-br", "132", WAV, "debug.at3"])
    session = frida.attach(pid)
    script = session.create_script(SCRIPT)
    script.on('message', on_message)
    script.load()
    frida.resume(pid)

    time.sleep(5) # Let it run for a bit
    session.detach()
    print("[*] Trace complete.")
