import frida
import time
import json

AT3TOOL = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
WAV     = r"C:\Users\Igland\Antigravity\Ghidra\atracdenc\YOUtopia_source.wav"
OUT     = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\lp2_trace.at3"

pid = frida.spawn([AT3TOOL, "-e", "-br", "132", WAV, OUT])
session = frida.attach(pid)

script_code = r"""
var base = Process.mainModule.base;
var size = Process.mainModule.size;
var rvas = {};
var frame = 0;
var stalking = false;

Interceptor.attach(base.add(0x4d20), {
    onEnter: function() {
        frame++;
        if (frame === 1 && !stalking) {
            stalking = true;
            Stalker.follow(Process.getCurrentThreadId(), {
                events: { call: true },
                onReceive: function(events) {
                    var decoded = Stalker.parse(events, {stringify: false});
                    for (var i = 0; i < decoded.length; i++) {
                        var target = decoded[i][2];
                        if (target !== null &&
                            target.compare(base) >= 0 &&
                            target.compare(base.add(size)) < 0) {
                            var rva = target.sub(base).toUInt32();
                            if (rvas[rva] === undefined) rvas[rva] = 0;
                            rvas[rva]++;
                        }
                    }
                }
            });
        }
        if (frame === 3 && stalking) {
            stalking = false;
            Stalker.unfollow(Process.getCurrentThreadId());
            setTimeout(function() {
                Stalker.flush();
                Stalker.garbageCollect();
                send({type: 'rvas', data: rvas});
            }, 500);
        }
    }
});
"""

results = {}

def on_msg(msg, data):
    if msg['type'] == 'send':
        p = msg['payload']
        if p.get('type') == 'rvas':
            results.update(p['data'])
            print(f"[*] Received {len(p['data'])} unique RVAs from LP2 frame trace")
    elif msg['type'] == 'error':
        print(f"[FRIDA ERROR] {msg}")

script = session.create_script(script_code)
script.on('message', on_msg)
script.load()
frida.resume(pid)

print("[*] Tracing LP2 call tree (frames 1-3)...")
while True:
    try:
        if session.is_detached:
            break
        time.sleep(0.5)
    except KeyboardInterrupt:
        break

# Save and print sorted RVAs
sorted_rvas = sorted(results.items(), key=lambda x: x[0])
with open("lp2_rvas.json", "w") as f:
    json.dump({f"0x{int(k):x}": v for k, v in sorted_rvas}, f, indent=2)

print("\n[*] Unique RVAs called during LP2 (sorted):")
for rva, count in sorted_rvas:
    print(f"  0x{int(rva):05x}  (called {count}x)")

print(f"\n[*] Total unique RVAs: {len(sorted_rvas)}")
print("[*] Saved to lp2_rvas.json")
