import frida
import sys
import time

# Dictionary to track which RVAs receive 132 as an argument
matches = []

def on_message(message, data):
    if message['type'] == 'send':
        payload = message['payload']
        if "MATCH" in payload:
            print(f"[!] {payload}")
            matches.append(payload)

# at3tool.exe path
at3tool = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
wav_file = r"C:\Users\Igland\Antigravity\Ghidra\atracdenc\YOUtopia_source.wav"
out_at3 = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\out_trace.at3"

pid = frida.spawn([at3tool, "-e", "-br", "132", wav_file, out_at3])
session = frida.attach(pid)

# We sweep the likely code area [0x1000 to 0x40000] 
# and hook every potential function entry (usually 16-byte aligned or sub esp push)
script_code = """
var base = Process.mainModule.base;
var size = Process.mainModule.size;

// We'll hook common "function start" addresses found in the data section
// or just a range. A range is safer.
var codeStart = 0x1000;
var codeEnd = 0x50000; 

for (var offset = codeStart; offset < codeEnd; offset += 4) {
    try {
        var addr = base.add(offset);
        // We only hook if it looks like a function: 
        // 55 (push ebp) or 83 ec (sub esp) or 81 ec
        var bytes = addr.readByteArray(3);
        var u8 = new Uint8Array(bytes);
        if (u8[0] == 0x55 || (u8[0] == 0x83 && u8[1] == 0xec) || (u8[0] == 0x81 && u8[1] == 0xec) || (u8[0] == 0x53 && u8[1] == 0x56)) {
            Interceptor.attach(addr, function (args) {
                // Check if any of the first 4 arguments is 132
                for (var i = 0; i < 4; i++) {
                    if (this.context.eax == 132 || this.context.ecx == 132 || args[i].toInt32() == 132) {
                        send("MATCH RVA 0x" + this.context.pc.sub(base).toString(16) + " arg[" + i + "]=132");
                    }
                }
            });
        }
    } catch (e) {}
}
"""

script = session.create_script(script_code)
script.on('message', on_message)
script.load()

frida.resume(pid)

print("[*] Monitoring for '132' bitrate handling...")
time.sleep(10)
session.detach()
