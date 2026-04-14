"""
deep_metrics_extractor_v4.py

Per-frame LP2 (132kbps ATRAC3) decoder-state dump from at3tool.exe.
Streaming mode: writes rows to disk immediately upon receipt to prevent data loss.
"""

import frida
import time
import csv
import json
import os
import sys

# ── Config ────────────────────────────────────────────────────────────────────
AT3TOOL = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\at3tool.exe"
SOURCES = [
    r"C:\Users\Igland\Antigravity\Ghidra\atracdenc\YOUtopia_source.wav",
    r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\quality\input\chirp_20_20k_5s.wav",
]
BITRATE = 132
OUTPUT_DIR = r"C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows"

RVAS = {
    "wrapper":     0x49f0,
    "atrac3_entry":0x4d20,
    "lp2_main":    0x3d1f0,
    "tonal_bits":  0x3ceb0,
    "gain_bits":   0x3d080,
    "extra_bits":  0x3cdc0,
    "e8c0":        0x3e8c0,
    "3f110":       0x3f110,
    "414f0":       0x414f0,
}

def build_script(rvas):
    js_consts = "\n".join([f"var RVA_{k.upper()} = {hex(v)};" for k, v in rvas.items()])
    return js_consts + r"""
var module_base = Process.mainModule.base;
var frame_counter = 0;
var lp2_call_in_frame = 0;

send({type: 'log', msg: 'JS Script loaded. Module Base: ' + module_base});

Interceptor.attach(module_base.add(RVA_ATRAC3_ENTRY), {
    onEnter: function() { 
        frame_counter++; 
        lp2_call_in_frame = 0;
        if (frame_counter % 1000 == 0) send({type: 'log', msg: 'Reached frame ' + frame_counter});
    }
});

var tonal_bits_per_call = [];
var gain_bits_per_call = [];
var extra_bits_per_call = [];
var tonal_candidates_per_call = [];
var e8c0_costs = [];

Interceptor.attach(module_base.add(RVA_TONAL_BITS), { onLeave: function(retval) { tonal_bits_per_call.push(retval.toInt32()); } });
Interceptor.attach(module_base.add(RVA_GAIN_BITS), { onLeave: function(retval) { gain_bits_per_call.push(retval.toInt32()); } });
Interceptor.attach(module_base.add(RVA_EXTRA_BITS), { onLeave: function(retval) { extra_bits_per_call.push(retval.toInt32()); } });
Interceptor.attach(module_base.add(RVA_3F110),    { onLeave: function(retval) { tonal_candidates_per_call.push(retval.toInt32()); } });

Interceptor.attach(module_base.add(RVA_E8C0), {
    onEnter: function(args) { this.cost_ptr = args[5]; },
    onLeave: function() { try { e8c0_costs.push(this.cost_ptr.readS32()); } catch(e) {} }
});

Interceptor.attach(module_base.add(RVA_LP2_MAIN), {
    onEnter: function(args) {
        this.ctx = args[2];
        this.channel = lp2_call_in_frame % 2;
        this.frame   = frame_counter;
        lp2_call_in_frame++;
        this.start_cost_idx = e8c0_costs.length;
        this.start_tonal_cand_idx = tonal_candidates_per_call.length;
    },

    onLeave: function(retval) {
        if (retval.toInt32() === -0x8000) return;
        var ctx = this.ctx;
        try {
            var num_out_bands = ctx.readS32();
            var matrix_idx    = ctx.add(4).readS32();
            var num_spectral_bands = ctx.add(0x1872 * 4).readS32();
            var transient_flag     = ctx.add(0x1860 * 4).readS32();
            var num_tonals         = ctx.add(0x110 * 4).readS32();
            var complexity_raw     = ctx.add(0x510 * 4).readS32();

            var t_bits = tonal_bits_per_call.shift() || 0;
            var g_bits = gain_bits_per_call.shift()  || 0;
            var x_bits = extra_bits_per_call.shift() || 0;
            
            var cand_list = tonal_candidates_per_call.splice(this.start_tonal_cand_idx);
            var t_cand = cand_list.length > 0 ? cand_list[0] : 0;

            var costs = e8c0_costs.splice(this.start_cost_idx);
            var residual_bits = costs.length > 0 ? costs[0] : 0;
            var actual_bits_used = costs.length > 0 ? costs[costs.length - 1] : 0;

            var weights = [];
            var gain_points = [];
            var tonals_per_band = [];
            for (var i = 0; i < 4; i++) {
                weights.push(ctx.add((0x143f + i) * 4).readS32());
                gain_points.push(ctx.add((0x141f + i) * 4).readS32());
                tonals_per_band.push(ctx.add((0x118 + i) * 4).readS32());
            }

            var record = {
                frame_idx:          this.frame,
                channel:            this.channel,
                num_bands:          num_out_bands,
                target_bits:        num_spectral_bands,
                sideinfo_bits:      t_bits + g_bits + x_bits,
                tonal_bits:         t_bits,
                gain_bits:          g_bits,
                residual_bits:      residual_bits,
                actual_bits_used:   actual_bits_used,
                complexity_score:   actual_bits_used - residual_bits,
                complexity_raw:     complexity_raw,
                num_tonals:         num_tonals,
                tonal_candidates:   t_cand,
                tonals_per_band:    tonals_per_band.join(";"),
                transient_triggered:transient_flag,
                matrix_index:       matrix_idx,
                energies:           "0;0;0;0;0;0;0;0",
                weight_idx:         weights.join(";"),
                gain_points:        gain_points.join(";")
            };
            send({type: 'row', data: record});
        } catch (e) {
            send({type: 'log', msg: 'Error in onLeave: ' + e});
        }
    }
});
"""

def run_extraction(sample_path):
    sample_name = os.path.basename(sample_path).replace(".wav", "")
    print(f"\n Extracting: {sample_name}...")
    
    csv_path = os.path.join(OUTPUT_DIR, f"deep_metrics_{sample_name}.csv")
    jsonl_path = os.path.join(OUTPUT_DIR, f"deep_metrics_{sample_name}.jsonl")
    
    fields = [
        "sample_name", "frame_idx", "channel", "num_bands", "target_bits",
        "sideinfo_bits", "tonal_bits", "gain_bits", "residual_bits",
        "actual_bits_used", "complexity_score", "complexity_raw", "num_tonals",
        "tonal_candidates", "tonals_per_band", "transient_triggered",
        "matrix_index", "energies", "weight_idx", "gain_points"
    ]

    f_csv = open(csv_path, 'w', newline='')
    writer = csv.DictWriter(f_csv, fieldnames=fields)
    writer.writeheader()
    
    f_jsonl = open(jsonl_path, 'w')
    
    row_count = 0

    def on_message(message, data):
        nonlocal row_count
        if message['type'] == 'send':
            payload = message['payload']
            if payload.get('type') == 'row':
                record = payload['data']
                record['sample_name'] = sample_name
                writer.writerow(record)
                f_jsonl.write(json.dumps(record) + "\n")
                row_count += 1
                if row_count % 500 == 0:
                    sys.stdout.write(f"\r  Streamed {row_count} rows...")
                    sys.stdout.flush()
            elif payload.get('type') == 'log':
                print(f"  [JS LOG] {payload['msg']}")
        elif message['type'] == 'error':
            print(f"  [FRIDA ERROR] {message['description']}")

    # Start at3tool
    pid = frida.spawn([AT3TOOL, "-e", "-br", str(BITRATE), sample_path, "temp.at3"])
    session = frida.attach(pid)
    script = session.create_script(build_script(RVAS))
    script.on('message', on_message)
    script.load()
    frida.resume(pid)
    
    while True:
        try:
            os.kill(pid, 0)
            time.sleep(1)
        except OSError:
            break
            
    # Final wait to catch trailing messages before closing files
    time.sleep(3)
    
    session.detach()
    f_csv.close()
    f_jsonl.close()
    print(f"\n  Done: {row_count} rows saved to {csv_path}")

if __name__ == "__main__":
    for wav in SOURCES:
        if os.path.exists(wav):
            run_extraction(wav)
    print("\n[*] All extractions complete.")
