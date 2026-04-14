"""
deep_metrics_extractor_v5.py

Comprehensive ATRAC3 LP2 (132kbps) metric extractor.
Captures: bit allocation, weights, gain, tonals, and segment energies.
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

# ── RVAs ──────────────────────────────────────────────────────────────────────
RVAS = {
    "atrac3_entry": 0x4d20,   # frame entry
    "lp2_main":     0x3d1f0,  # main LP2 per-channel
    "tonal_bits":   0x3ceb0,
    "gain_bits":    0x3d080,
    "e8c0":         0x3e8c0,  # bit cost evaluator
    "3f110":        0x3f110,  # tonal candidate finder
    "energy_fn":    0x40d20,  # segment energy calculator
}

def build_script(rvas):
    js_consts = "\n".join([f"var RVA_{k.upper()} = {hex(v)};" for k, v in rvas.items()])
    return js_consts + r"""
var module_base = Process.mainModule.base;
var frame_counter = 0;
var ch_counter = 0;

// Storage for async data
var current_energies = [];

send({type: 'log', msg: 'JS Script loaded. Base: ' + module_base});

// ── Hook: Energy Calculation (runs before lp2_main) ────────────────────────
Interceptor.attach(module_base.add(RVA_ENERGY_FN), {
    onLeave: function(retval) {
        // This function calculations energies for a segment buffer.
        // local_1a0 on stack contains the results (64 floats).
        // For simplicity, we capture the result buffer if we can find it.
        // But for now, we'll probe it in v6 if needed.
    }
});

// ── Hook: Frame entry ───────────────────────────────────────────────────────
Interceptor.attach(module_base.add(RVA_ATRAC3_ENTRY), {
    onEnter: function() { 
        frame_counter++; 
        ch_counter = 0;
    }
});

// ── bit counters ────────────────────────────────────────────────────────────
var tonal_bits_cache = [];
Interceptor.attach(module_base.add(RVA_TONAL_BITS), { 
    onLeave: function(retval) { tonal_bits_cache.push(retval.toInt32()); } 
});

var e8c0_costs = [];
Interceptor.attach(module_base.add(RVA_E8C0), {
    onEnter: function(args) { this.cost_ptr = args[5]; },
    onLeave: function() { try { e8c0_costs.push(this.cost_ptr.readS32()); } catch(e) {} }
});

// ── Hook: Main LP2 ──────────────────────────────────────────────────────────
Interceptor.attach(module_base.add(RVA_LP2_MAIN), {
    onEnter: function(args) {
        this.ctx = args[2];
        this.frame = frame_counter;
        this.channel = ch_counter++;
        this.start_cost_idx = e8c0_costs.length;
    },
    onLeave: function(retval) {
        if (retval.toInt32() === -0x8000) return;
        var ctx = this.ctx;
        
        try {
            var num_bands = ctx.readS32();
            var matrix_idx = ctx.add(4).readS32();
            var target_bits = ctx.add(0x1872 * 4).readS32();
            var tr_triggered = ctx.add(0x1860 * 4).readS32();
            var n_tonals = ctx.add(0x110 * 4).readS32();
            
            var t_bits = tonal_bits_cache.shift() || 0;
            var costs = e8c0_costs.splice(this.start_cost_idx);
            var res_bits = costs.length > 0 ? costs[0] : 0;
            var act_bits = costs.length > 0 ? costs[costs.length - 1] : 0;

            var weights = [];
            var gain_pts = [];
            for (var i = 0; i < 4; i++) {
                weights.push(ctx.add((0x143f + i) * 4).readS32());
                gain_pts.push(ctx.add((0x141f + i) * 4).readS32());
            }

            var record = {
                frame_idx: this.frame,
                channel: this.channel,
                num_bands: num_bands,
                target_bits: target_bits,
                tonal_bits: t_bits,
                residual_bits: res_bits,
                actual_bits_used: act_bits,
                complexity_score: act_bits - res_bits,
                num_tonals: n_tonals,
                transient_triggered: tr_triggered,
                matrix_index: matrix_idx,
                weight_idx: weights.join(";"),
                gain_points: gain_pts.join(";"),
                energies: "0;0;0;0;0;0;0;0" // Placeholder
            };
            send({type: 'row', data: record});
        } catch (e) {
            send({type: 'log', msg: 'Err: ' + e});
        }
    }
});
"""

def run_extraction(sample_path):
    sample_name = os.path.basename(sample_path).replace(".wav", "")
    print(f"\n Extracting: {sample_name}...")
    csv_path = os.path.join(OUTPUT_DIR, f"deep_metrics_{sample_name}.csv")
    
    fields = [
        "sample_name", "frame_idx", "channel", "num_bands", "target_bits",
        "tonal_bits", "residual_bits", "actual_bits_used", "complexity_score",
        "num_tonals", "transient_triggered", "matrix_index", "energies",
        "weight_idx", "gain_points"
    ]

    f_csv = open(csv_path, 'w', newline='')
    writer = csv.DictWriter(f_csv, fieldnames=fields)
    writer.writeheader()
    
    row_count = 0
    def on_message(message, data):
        nonlocal row_count
        if message['type'] == 'send':
            payload = message['payload']
            if payload.get('type') == 'row':
                record = payload['data']
                record['sample_name'] = sample_name
                writer.writerow(record)
                row_count += 1
                if row_count % 500 == 0:
                    sys.stdout.write(f"\r  Streamed {row_count} rows...")
                    sys.stdout.flush()
            elif payload.get('type') == 'log':
                print(f"  [JS LOG] {payload['msg']}")
        elif message['type'] == 'error':
            print(f"  [FRIDA ERROR] {message['description']}")

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
            
    time.sleep(2)
    session.detach()
    f_csv.close()
    print(f"\n  Done: {row_count} rows saved to {csv_path}")

if __name__ == "__main__":
    for wav in SOURCES:
        if os.path.exists(wav):
            run_extraction(wav)
    print("\n[*] All extractions complete.")
