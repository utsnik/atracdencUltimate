import frida
import sys
import json
import csv
import threading
import time

# Metrics counter
processed_frames = 0
hook_count = 0

# Output files
out_csv = open("per_frame_metrics.csv", "w", newline='')
csv_writer = csv.writer(out_csv)
csv_writer.writerow([
    "frame_idx", "complexity", "target_bits", "sideinfo_bits", 
    "tonal_bits", "residual_bits", "diff_gain_indices"
])

out_jsonl = open("metrics.jsonl", "w")

def on_message(message, data):
    global processed_frames, hook_count
    if message['type'] == 'send':
        payload = message['payload']
        if isinstance(payload, str) and payload.startswith("HOOK_"):
            hook_count += 1
            # print(f"[VERBOSE] {payload}")
        elif isinstance(payload, dict):
            # Write to JSONL
            out_jsonl.write(json.dumps(payload) + "\n")
            out_jsonl.flush()
            
            # Write to CSV
            diff_str = "|".join([f"{g['loc']}-{g['lvl']}" for g in payload.get('diff_gains', [])])
            csv_writer.writerow([
                payload.get('frame_idx', 0),
                payload.get('complexity', 0),
                payload.get('target_bits', 0),
                payload.get('sideinfo_bits', 0),
                payload.get('tonal_bits', 0),
                payload.get('residual_bits', 0),
                diff_str
            ])
            out_csv.flush()
            processed_frames += 1
            if processed_frames % 1000 == 0:
                print(f"[*] Processed {processed_frames} frames...")
        else:
            print("[FRIDA]", payload)
    elif message['type'] == 'error':
        print("[!] FRIDA ERROR:", message['description'])

# at3tool.exe path
at3tool = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
wav_file = r"C:\Users\Igland\Antigravity\Ghidra\atracdenc\YOUtopia_source.wav"
out_at3 = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\out.at3"

print("[*] Spawning at3tool.exe...")
pid = frida.spawn([at3tool, "-e", "-br", "132", wav_file, out_at3])
session = frida.attach(pid)

script_code = """
var base = Process.mainModule.base;
var current_frame = 0;
var frame_data = {
    frame_idx: 0,
    complexity: 0,
    target_bits: 0,
    sideinfo_bits: 0,
    tonal_bits: 0,
    residual_bits: 0,
    diff_gains: []
};

// Hook Bit Allocator Entry (FUN_00437b40)
Interceptor.attach(base.add(0x37b40), function (args) {
    send("HOOK_ALLOC_START");
    var param1 = args[0];
    try {
        // target_bits is at bit_alloc_struct + 0xb58*4
        frame_data.target_bits = param1.add(0xb58 * 4).readU32();
    } catch (e) {}
});

// Hook Tonal Processing (FUN_00438e60)
Interceptor.attach(base.add(0x38e60), {
    onLeave: function (retval) {
        frame_data.tonal_bits = retval.toInt32();
    }
});

// Hook Allocator End (0x385ab is the ADD ESP, 0x520 cleanup)
Interceptor.attach(base.add(0x385ab), function (args) {
    try {
        var esp = this.context.esp;
        // complexity is at [esp + 0x510]
        frame_data.complexity = esp.add(0x510).readU32();
        frame_data.residual_bits = esp.add(0x51c).readU32();
        frame_data.frame_idx = current_frame;
        
        send(frame_data);
        
        // Reset for next frame
        current_frame++;
        frame_data = {
            frame_idx: current_frame,
            complexity: 0,
            target_bits: 0,
            sideinfo_bits: 0,
            tonal_bits: 0,
            residual_bits: 0,
            diff_gains: []
        };
    } catch (e) {
        send("HOOK_ERR " + e.message);
    }
});

// Hook Bitstream Write (FUN_00437670)
Interceptor.attach(base.add(0x37670), function (args) {
    try {
        var val = args[0].toInt32();
        var num_bits = args[1].toInt32();
        if (num_bits === 9) {
            var location = val & 0x1F;
            var level = (val >> 5) & 0xF;
            frame_data.diff_gains.push({loc: location, lvl: level});
        }
    } catch (e) {}
});
"""

script = session.create_script(script_code)
script.on('message', on_message)
script.load()

print(f"[*] Harvesting Dynamic Metrics from at3tool.exe...")
frida.resume(pid)

# Wait for process to exit
event = threading.Event()
session.on('detached', lambda reason: event.set())
event.wait()

# Give Frida some time to drain messages
for _ in range(10):
    if processed_frames >= 10452: break
    time.sleep(0.5)

out_csv.close()
out_jsonl.close()
print(f"[*] Done. Extracted {processed_frames} frames. Hook hits: {hook_count}")
