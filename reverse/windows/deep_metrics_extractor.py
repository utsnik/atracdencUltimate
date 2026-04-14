import frida
import sys
import time
import csv
import json
import hashlib

# Configuration
AT3TOOL_PATH = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
IMAGE_BASE = 0x400000
RVAS = {
    "frame_entry": 0x36d40,
    "allocator": 0x37b40,
    "tonal_packer": 0x38e60
}

def get_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest().upper()

BINARY_HASH = get_hash(AT3TOOL_PATH)

def extract_metrics(wav_filename):
    out_prefix = wav_filename.split("\\")[-1].replace(".wav", "")
    csv_path = f"deep_metrics_{out_prefix}.csv"
    jsonl_path = f"deep_metrics_{out_prefix}.jsonl"
    at3_path = f"{out_prefix}.at3"
    
    csv_file = open(csv_path, "w", newline="")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow([
        "frame_idx", "channel", "complexity_score", "target_bits", 
        "sideinfo_bits", "tonal_bits", "residual_bits", "actual_bits_used",
        "tonal_candidates", "tonal_promoted", "tonality_ratio_raw", "tonality_ratio_pass"
    ])
    
    jsonl_file = open(jsonl_path, "w")
    
    print(f"[*] Processing {wav_filename} -> {csv_path}")
    
    pid = frida.spawn([AT3TOOL_PATH, "-e", "-br", "132", wav_filename, at3_path])
    session = frida.attach(pid)
    
    script_code = """
    var base = Process.mainModule.base;
    var frame_idx = 0;
    
    // Per-frame state
    var current_frame = {
        idx: 0,
        channels: [{}, {}]
    };

    // FUN_00436d40: Frame Logic entry
    Interceptor.attach(base.add(0x36d40), {
        onEnter: function (args) {
            current_frame.idx = frame_idx;
        }
    });

    // FUN_00437b40: Allocator
    Interceptor.attach(base.add(0x37b40), {
        onEnter: function (args) {
            // Read complexity from stack (ESP is at args[0] in Interceptor context roughly)
            // But better use the 'this.context'
            var esp = this.context.esp;
            var complexity = this.context.esp.add(0x510).readU32();
            var target_bits = this.context.esp.add(0x50c).readU32();
            
            var channel_idx = (frame_idx % 2); // Heuristic for now
            var ch = current_frame.channels[channel_idx];
            ch.complexity = complexity;
            ch.target_bits = target_bits;
            
            // send({type: 'log', data: "Alloc triggering for frame " + frame_idx});
        }
    });

    // FUN_00438e60: Tonal Packer
    Interceptor.attach(base.add(0x38e60), {
        onEnter: function (args) {
            // Placeholder for tonal candidate tracking
        },
        onLeave: function (retval) {
            var channel_idx = (frame_idx % 2);
            var ch = current_frame.channels[channel_idx];
            ch.actual_bits_used = retval.toInt32();
            
            if (channel_idx == 1) {
                send({type: 'frame', data: current_frame});
                frame_idx++;
            }
        }
    });
    """
    
    def on_message(message, data):
        if message['type'] == 'send':
            payload = message['payload']
            if payload['type'] == 'frame':
                frame = payload['data']
                for i, ch in enumerate(frame['channels']):
                    csv_writer.writerow([
                        frame['idx'], i, ch.get('complexity', 0), ch.get('target_bits', 0),
                        0, 0, 0, ch.get('actual_bits_used', 0),
                        0, 0, 0, 0
                    ])
                jsonl_file.write(json.dumps(frame) + "\\n")
                if frame['idx'] % 1000 == 0:
                    print(f"[*] Harvested {frame['idx']} frames...")

    script = session.create_script(script_code)
    script.on('message', on_message)
    script.load()
    
    frida.resume(pid)
    
    # Wait for process to exit
    while True:
        try:
            if session.is_detached:
                break
            time.sleep(1)
        except:
            break
            
    csv_file.close()
    jsonl_file.close()
    print(f"[*] Completed {out_prefix}.")

# Execution
YOUtopia = r"C:\Users\Igland\Antigravity\Ghidra\atracdenc\YOUtopia_source.wav"
Chirp = r"C:\Users\Igland\Antigravity\Ghidra\atracdenc_solo_20260411\chirp_20_20k_5s.wav"

extract_metrics(YOUtopia)
extract_metrics(Chirp)

print("[*] All deep metrics harvested.")
