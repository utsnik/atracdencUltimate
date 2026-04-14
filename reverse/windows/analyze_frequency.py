import frida
import sys
import time

# Dictionary to store call counts
counts = {}

def on_message(message, data):
    if message['type'] == 'send':
        addr = message['payload']
        counts[addr] = counts.get(addr, 0) + 1

# at3tool.exe path
at3tool = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
wav_file = r"C:\Users\Igland\Antigravity\Ghidra\atracdenc\YOUtopia_source.wav"
out_at3 = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\out_trace.at3"

print("[*] Spawning at3tool.exe for call frequency analysis...")
pid = frida.spawn([at3tool, "-e", "-br", "132", wav_file, out_at3])
session = frida.attach(pid)

# We want to trace ONLY functions in the main module
# We'll use a script that enumerates all 'sub_' or 'FUN_' style logic
# Actually, we can just hook every 16-byte aligned address in the code section?
# Better: Use the PE Export/Ghidra info to find logic starts.
# For now, let's just log EVERY internal function call detected by Interceptor.
script_code = """
var mainModule = Process.mainModule;
var base = mainModule.base;
var size = mainModule.size;

// Enumerating all functions is hard without debug symbols, 
// so we'll use a common pattern: hook the addresses we previously found
// and also any other prominent ones.
// But for "Discovery", we can use Module.enumerateSymbols() or similar.
var symbols = mainModule.enumerateSymbols();
// at3tool usually doesn't have symbols, so we'll use a scan approach or just 
// hook the specific functions we suspect and 100 others around them.

// ACTUALLY: Let's hook a range of addresses in the code section.
// This is a "Spray and Pray" approach for discovery.
var codeStart = base.add(0x1000); // Typical PE code start
var codeEnd = base.add(0x40000); // Scan first 256KB of code

for (var addr = codeStart; addr.compare(codeEnd) < 0; addr = addr.add(0x10)) {
    try {
        Interceptor.attach(addr, {
            onEnter: function (args) {
                send(this.returnAddress.sub(base).toString());
            }
        });
    } catch (e) {}
}
"""

# Wait, the above is too slow. 
# Let's use a smarter discovery: Hook common function offsets we found in Ghidra 
# and see which ones are called precisely 10452 times.

suspects = [0x37b40, 0x38e60, 0x39630, 0x37490, 0x36d40, 0x3ebd0, 0x38630, 0x385c0, 0x38690]

script_code = """
var base = Process.mainModule.base;
var suspects = [0x37b40, 0x38e60, 0x39630, 0x37490, 0x36d40, 0x3ebd0, 0x38630, 0x385c0, 0x38690, 0x37b30, 0x37c00, 0x37400];

suspects.forEach(function(offset) {
    try {
        Interceptor.attach(base.add(offset), function (args) {
            send(offset.toString(16));
        });
    } catch (e) {}
});
"""

script = session.create_script(script_code)
script.on('message', on_message)
script.load()

frida.resume(pid)

print("[*] Monitoring call counts for 5 seconds...")
time.sleep(5)

# Report
print("\\n[+] Call Frequency Analysis (Top Suspects):")
sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
for addr, count in sorted_counts:
    print(f"RVA 0x{addr}: {count} calls")

session.detach()
