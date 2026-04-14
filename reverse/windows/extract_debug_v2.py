import frida
import sys
import time

def on_message(message, data):
    if message['type'] == 'send':
        print(message['payload'])

at3tool = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
wav_file = r"C:\Users\Igland\Antigravity\Ghidra\atracdenc\YOUtopia_source.wav"
out_at3 = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\out.at3"

# -e encode -br 132
pid = frida.spawn([at3tool, "-e", "-br", "132", wav_file, out_at3])
session = frida.attach(pid)

script_code = """
var base = Process.mainModule.base;

// FUN_00436ea0 is Core Encode (RVA 0x36ea0)
// puVar10 is at param_3 + (int)local_228 * 0xb5c + 800
// puVar10[0xb58] is checked.

Interceptor.attach(base.add(0x36ea0), {
    onEnter: function (args) {
        // param_3 is args[2]
        var param_3 = args[2];
        this.param_3 = param_3;
        
        // Let's watch the loop in real-time by hooking just the entry to the loop
        // Or better, hook the allocator 0x37b40 directly with a counter.
    }
});

var allocatorCount = 0;
Interceptor.attach(base.add(0x37b40), {
    onEnter: function (args) {
        allocatorCount++;
        if (allocatorCount % 1000 == 0) {
           send("[*] Allocator RVA 0x37b40 triggered: " + allocatorCount);
        }
    }
});

var coreEncodeCount = 0;
Interceptor.attach(base.add(0x36ea0), {
    onEnter: function (args) {
        coreEncodeCount++;
        if (coreEncodeCount % 1000 == 0) {
           send("[*] Core Encode RVA 0x36ea0 triggered: " + coreEncodeCount);
        }
    }
});
"""

script = session.create_script(script_code)
script.on('message', on_message)
script.load()

frida.resume(pid)
print("[*] Monitoring Core Encode (0x36ea0) and Allocator (0x37b40)...")

while True:
    try:
        if not session.is_detached:
            time.sleep(1)
        else:
            break
    except KeyboardInterrupt:
        break
print("[*] Done.")
