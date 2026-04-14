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
var total_frames = 0;

Interceptor.attach(base.add(0x4d20), {
    onEnter: function (args) {
        total_frames++;
        if (total_frames === 1) {
            console.log("[*] Mapping 0x4d20 call tree for LP2 132kbps...");
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
                            var rva = target.sub(base).toString(16);
                            send({rva: "0x" + rva});
                        }
                    }
                }
            });
        }
        if (total_frames === 2) {
            Stalker.unfollow(Process.getCurrentThreadId());
            send({type: 'done'});
        }
    }
});
"""

visited_rvas = set()

def on_message(message, data):
    if message['type'] == 'send':
        payload = message['payload']
        if 'rva' in payload:
            visited_rvas.add(payload['rva'])
        if payload.get('type') == 'done':
            print("[*] Unique RVAs called from 0x4d20:")
            for rva in sorted(list(visited_rvas)):
                print(rva)

script = session.create_script(script_code)
script.on('message', on_message)
script.load()

frida.resume(pid)

import time
time.sleep(10)
session.detach()
