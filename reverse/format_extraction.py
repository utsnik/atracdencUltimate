import csv
import json
import os

raw_output_path = r'C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\extraction_raw.log'
csv_path = r'C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\per_frame_metrics.csv'
jsonl_path = r'C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\metrics.jsonl'

metadata = {
    "at3tool_version": "3.0.0.0",
    "at3tool_sha256": "705B40CFC26DD1227D7D937C9102FBB9C4375C9CC9EF10F589CE0BA11EADCA1B",
    "image_base": "0x400000",
    "hook_rvas": {
        "frame_entry": "0x36d40",
        "allocator": "0x37b40",
        "tonal_packer": "0x38e60",
        "transient_analysis": "0x39630",
        "js_matrix": "0x37490"
    }
}

csv_header = [
    "sample", "frame_idx", "target_bits", "sideinfo_bits", "tonal_bits", "residual_bits", 
    "used_bits", "complexity", "num_tonals_total", "num_tonals_per_band", "gain_points_per_band",
    "matrix_index", "weights", "energies", "attack_ratio", "trigger"
]

rows = []
with open(raw_output_path, 'r') as f:
    for line in f:
        if line.startswith('INFO  ExtractDetailedMetrics.java> FRAME_VERBOSE,'):
            # Extract the CSV part
            parts = line.split('FRAME_VERBOSE,')[1].strip().split(',')
            # parts: sample, idx, target, side, tonal, res, used, comp, tCount, matrix, t_per_band, g_per_band, weights, energies, attack, trigger
            # In our updated script, we had some hardcoded arrays joined by |
            rows.append(parts)

# Write CSV
with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["# METADATA: " + json.dumps(metadata)])
    writer.writerow(csv_header)
    writer.writerows(rows)

# Write JSONL
with open(jsonl_path, 'w') as f:
    for r in rows:
        obj = {
            "metadata": metadata,
            "sample": r[0],
            "frame_idx": int(r[1]),
            "bits": {
                "target": int(r[2]),
                "sideinfo": int(r[3]),
                "tonal": int(r[4]),
                "residual": int(r[5]),
                "used": int(r[6])
            },
            "complexity": int(r[7]),
            "tonals": {
                "total": int(r[8]),
                "per_band": r[9].split('|')
            },
            "gain": {
                "points_per_band": r[10].split('|'),
                "energies": r[13].split('|'),
                "attack_ratio": float(r[14]),
                "trigger": int(r[15])
            },
            "stereo": {
                "matrix_index": int(r[11]),
                "weights": r[12].split('|')
            }
        }
        f.write(json.dumps(obj) + '\n')

print(f"Generated {csv_path} and {jsonl_path}")
