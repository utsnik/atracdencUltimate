import frida
import sys

at3tool = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
wav_file = r"C:\Users\Igland\Antigravity\Ghidra\atracdenc\YOUtopia_source.wav"
out_at3 = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\out.at3"

pid = frida.spawn([at3tool, "-e", "-br", "132", wav_file, out_at3])
session = frida.attach(pid)

script_code = """
var base = Process.mainModule.base;
var size = Process.mainModule.size;

// Identify ALL functions called under 0x49f0
var calls = new Set();
var total_frames = 0;

Interceptor.attach(base.add(0x49f0), {
    onEnter: function (args) {
        total_frames++;
        if (total_frames === 1) {
            console.log("[*] Stalking frame 1 execution...");
            Stalker.follow(Process.getCurrentThreadId(), {
                events: {
                    call: true
                },
                onReceive: function (events) {
                    var decoded = Stalker.parse(events);
                    for (var i = 0; i < decoded.length; i++) {
                        var e = decoded[i];
                        var target = e[2];
                        if (target.compare(base) >= 0 && target.compare(base.add(size)) < 0) {
                            calls.add(target.sub(base).toString(16));
                        }
                    }
                }
            });
        }
        if (total_frames === 2) {
            Stalker.unfollow(Process.getCurrentThreadId());
            console.log("[*] Final Call Set for LP2 132kbps:");
            var arr = Array.from(calls);
            arr.sort();
            console.log(arr.join("\\n"));
        }
    }
});
"""

script = session.create_script(script_code)
script.on('message', lambda msg, data: print(msg))
script.load()

frida.resume(pid)
print("[*] Monitoring...")

import time
time.sleep(10)
session.detach()
