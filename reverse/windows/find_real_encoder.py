import frida
import sys
import time

# Collect function call counts
counts = {}

def on_message(message, data):
    pass # Counts are handled in-script for speed

at3tool = r"C:\\Users\\Igland\\Antigravity\\Ghidra\\ghidra\\reverse\\windows\\at3tool.exe"
wav_file = r"C:\\Users\\Igland\\Antigravity\\Ghidra\\atracdenc\\YOUtopia_source.wav"
out_at3 = r"C:\\Users\\Igland\\Antigravity\\Ghidra\\ghidra\\reverse\\windows\\out.at3"

pid = frida.spawn([at3tool, "-e", "-br", "132", wav_file, out_at3])
session = frida.attach(pid)

script_code = """
var base = Process.mainModule.base;
var size = Process.mainModule.size;
var functions = [];

// Enumerate all functions in the .text section
var sections = Process.mainModule.enumerateSections();
var text = sections.filter(s => s.name === '.text')[0];

console.log("[*] Scanning .text section: " + text.base + " - " + text.base.add(text.size));

// We'll hook functions at the start of basic blocks or common function entry patterns
// since we don't have a full symbol table in Frida for a stripped binary.
// Alternatively, we use our Ghidra-identified RVAs as a starting point.

var candidates = [
    0x49f0,  // Wrapper (Known working)
    0x4d20,  // Atrac3 Entry
    0x36ea0, // Core Encode (Not triggering?)
    0x37b40, // Allocator (Not triggering?)
    0x36ce0, // Lib Entry
    0x36d40  // Frame Logic
];

// Let's broaden the search to the entire 0x30000 - 0x40000 range in the Sony lib
// Actually, let's just trace from 0x49f0 downwards.

var wrapper = base.add(0x49f0);
var counts = {};

Interceptor.attach(wrapper, {
    onEnter: function (args) {
        var threadId = Process.getCurrentThreadId();
        if (counts["total"] === undefined) counts["total"] = 0;
        counts["total"]++;
        
        // Use Stalker to follow the execution of exactly ONE frame
        if (counts["total"] === 1) {
            console.log("[*] Stalking first frame from 0x49f0...");
            Stalker.follow(threadId, {
                events: {
                    call: true
                },
                onReceive: function (events) {
                    var decoded = Stalker.parse(events);
                    for (var i = 0; i < decoded.length; i++) {
                        var e = decoded[i];
                        var target = e[2];
                        if (target.compare(base) >= 0 && target.compare(base.add(size)) < 0) {
                            var rva = target.sub(base);
                            if (counts[rva] === undefined) counts[rva] = 0;
                            counts[rva]++;
                        }
                    }
                }
            });
        }
        if (counts["total"] === 2) {
            Stalker.unfollow(threadId);
            console.log("[*] Stalking finished. Results:");
            for (var rva in counts) {
                if (rva !== "total" && counts[rva] > 0) {
                    console.log("RVA: " + rva + " Count: " + counts[rva]);
                }
            }
        }
    }
});
"""

script = session.create_script(script_code)
script.on('message', on_message)
script.load()

frida.resume(pid)

time.sleep(5)
session.detach()
print("[*] Scan complete.")
