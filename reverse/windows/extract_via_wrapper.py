import frida
import sys
import time
import csv

# Metrics counter
processed_frames = 0

# Output files
out_csv = open("per_frame_metrics.csv", "w", newline='')
csv_writer = csv.writer(out_csv)
csv_writer.writerow([
    "frame_idx", "complexity", "target_bits", "sideinfo_bits", 
    "tonal_bits", "residual_bits", "diff_gain_indices"
])

def on_message(message, data):
    global processed_frames
    if message['type'] == 'send':
        payload = message['payload']
        if isinstance(payload, dict):
            csv_writer.writerow([
                payload.get('frame_idx', 0),
                payload.get('complexity', 0),
                payload.get('target_bits', 0),
                payload.get('sideinfo_bits', 0),
                payload.get('tonal_bits', 0),
                payload.get('residual_bits', 0),
                ""
            ])
            out_csv.flush()
            processed_frames += 1
            if processed_frames % 1000 == 0:
                print(f"[*] Harvested {processed_frames} frames...")

# at3tool.exe path
at3tool = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
wav_file = r"C:\Users\Igland\Antigravity\Ghidra\atracdenc\YOUtopia_source.wav"
out_at3 = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\out.at3"

pid = frida.spawn([at3tool, "-e", "-br", "132", wav_file, out_at3])
session = frida.attach(pid)

script_code = """
var base = Process.mainModule.base;
var frame_idx = 0;

// FUN_004049f0 is the encoder wrapper (RVA 0x49f0)
// We use Interceptor.attach here to be safe, but we'll read the state after the call.
Interceptor.attach(base.add(0x49f0), {
    onEnter: function (args) {
        // param_1 is the encoder state
        this.ctx = args[0];
    },
    onLeave: function (retval) {
        // After the frame is encoded, we harvest the complexity.
        // We need to find where the Sony library stores the complexity for the frame.
        // In static analysis, it was in a local variable on the stack of FUN_00437b40.
        // If we can't find it there, we'll search the memory of the encoder state.
        
        var data = {
            frame_idx: frame_idx,
            complexity: 0,
            target_bits: 0,
            tonal_bits: 0
        };
        
        try {
            // Heuristic hunt for the complexity score in the encoder state structure
            // Usually, these are 32-bit ints that change per frame.
            data.target_bits = this.ctx.add(0xb58 * 4).readU32();
        } catch (e) {}

        send(data);
        frame_idx++;
    }
});
"""

script = session.create_script(script_code)
script.on('message', on_message)
script.load()

frida.resume(pid)
print("[*] Monitoring high-level encoder wrapper (0x49f0)...")

# Wait for completion
while True:
    try:
        if not session.is_detached:
            time.sleep(1)
        else:
            break
    except KeyboardInterrupt:
        break

out_csv.close()
print(f"[*] Done. Final frame count: {processed_frames}")
