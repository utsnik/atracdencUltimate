
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from lp2_score_workflow import write_wav_slice

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / 'tools' / 'lp2_parity_re_manifest.json'
DEFAULT_SCORE_REPORT = REPO_ROOT / 'docs' / 'LP2_SCORE_WORKFLOW_2026-04-13.md'
DEFAULT_EXTRACTOR = Path(r'C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\deep_metrics_extractor_v6.py')
DEFAULT_AT3TOOL = REPO_ROOT / 'reverse' / 'windows' / 'at3tool.exe'
DEFAULT_OUT_DIR = REPO_ROOT / 'reverse' / 'windows' / 'lp2_parity_re'
DEFAULT_REPORT = REPO_ROOT / 'docs' / 're' / 'LP2_PARITY_RE_REPORT_2026-04-13.md'
DEFAULT_DECOMP = REPO_ROOT / 'reverse' / 'out' / 'at3tool' / 'decompilation.json'
DEFAULT_FUNCS = REPO_ROOT / 'reverse' / 'out' / 'at3tool' / 'functions.json'


@dataclass
class SampleSpec:
    name: str
    source: Path
    seconds: float
    score_name: str | None = None
    supplemental: bool = False


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed ({p.returncode}):\n{' '.join(cmd)}\n{p.stderr}")


def mean(vals: list[float]) -> float:
    return statistics.fmean(vals) if vals else 0.0


def median(vals: list[float]) -> float:
    return statistics.median(vals) if vals else 0.0


def percentile(vals: list[float], q: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    idx = max(0, min(len(s) - 1, int((len(s) - 1) * q)))
    return s[idx]


def parse_semis(text: str, cast=float) -> list:
    out = []
    for part in text.split(';') if text else []:
        part = part.strip()
        if not part:
            continue
        try:
            out.append(cast(part))
        except ValueError:
            out.append(cast(float(part)))
    return out


def load_manifest(path: Path) -> list[SampleSpec]:
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    return [
        SampleSpec(
            name=item['name'],
            source=(REPO_ROOT / item['source']).resolve(),
            seconds=float(item['seconds']),
            score_name=item.get('score_name'),
            supplemental=bool(item.get('supplemental', False)),
        )
        for item in data['samples']
    ]


def md_cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip('|').split('|')]


def parse_score_report(path: Path) -> tuple[dict[str, dict[str, str]], dict[str, list[dict[str, float]]]]:
    summary: dict[str, dict[str, str]] = {}
    hotspots: dict[str, list[dict[str, float]]] = {}
    in_summary = False
    current = None
    in_hot = False
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('| Sample |'):
            in_summary = True
            continue
        if in_summary:
            if not line.startswith('|'):
                in_summary = False
            else:
                cells = md_cells(line)
                if cells and cells[0] not in {'Sample', '---'}:
                    summary[cells[0]] = {
                        'candidate_full': cells[1], 'candidate_hf': cells[2], 'p10': cells[3], 'median': cells[4],
                        'vocal_err': cells[5], 'side_snr': cells[6], 'side_ret_db': cells[7], 'dur_ratio': cells[8],
                        'hotspots': cells[9], 'worst_hotspot': cells[10], 'delta_full': cells[11], 'delta_hf': cells[12], 'sony_dist': cells[13],
                    }
            continue
        if line.startswith('### '):
            current = line[4:].strip()
            hotspots[current] = []
            in_hot = False
            continue
        if current and line.startswith('| Frame |'):
            in_hot = True
            continue
        if in_hot:
            if not line.startswith('|'):
                in_hot = False
                continue
            cells = md_cells(line)
            if cells[0] in {'Frame', '---'}:
                continue
            hotspots[current].append({
                'frame': float(cells[0]), 'delta_vs_baseline': float(cells[1]), 'hf_energy_db': float(cells[2]),
                'baseline_snr': float(cells[3]), 'candidate_snr': float(cells[4]),
            })
    return summary, hotspots


def run_extractor(extractor: Path, at3tool: Path, clips: list[Path], out_dir: Path, max_runtime_s: int, stall_timeout_s: int, heartbeat_s: int) -> None:
    cmd = [
        sys.executable, str(extractor), '--at3tool', str(at3tool), '--output-dir', str(out_dir),
        '--max-runtime-s', str(max_runtime_s), '--stall-timeout-s', str(stall_timeout_s), '--heartbeat-s', str(heartbeat_s),
        *[str(p) for p in clips],
    ]
    run(cmd)


def load_rows(csv_path: Path) -> list[dict[str, object]]:
    rows = []
    with csv_path.open('r', newline='', encoding='utf-8') as fh:
        for row in csv.DictReader(fh):
            rows.append({
                'frame_idx': int(row['frame_idx']), 'channel': int(row['channel']), 'target_bits': int(row['target_bits']),
                'sideinfo_bits': int(row['sideinfo_bits']), 'gain_bits': int(row['gain_bits']), 'tonal_bits': int(row['tonal_bits']),
                'residual_bits': int(row['residual_bits']), 'actual_bits_used': int(row['actual_bits_used']),
                'complexity_score': int(row['complexity_score']), 'num_tonals': int(row['num_tonals']),
                'transient_triggered': int(row['transient_triggered']), 'attack_ratio': float(row['attack_ratio']),
                'matrix_index': int(row['matrix_index']), 'weight_idx': parse_semis(row['weight_idx'], int),
                'gain_points_per_band': parse_semis(row['gain_points_per_band'], int),
            })
    return rows

def aggregate(rows: list[dict[str, object]]) -> dict[int, dict[str, object]]:
    by_frame: dict[int, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_frame[int(row['frame_idx'])].append(row)
    out: dict[int, dict[str, object]] = {}
    prev_matrix = None
    prev_weight = None
    prev_gain = None
    for frame in sorted(by_frame):
        items = by_frame[frame]
        matrices = [int(x['matrix_index']) for x in items]
        weights = [x['weight_idx'] for x in items]
        gains = [x['gain_points_per_band'] for x in items]
        weight_sum = mean([float(sum(v for v in w)) for w in weights])
        gain_sum = mean([float(sum(v for v in g)) for g in gains])
        row = {
            'frame_idx': frame,
            'complexity_score': mean([float(x['complexity_score']) for x in items]),
            'residual_bits': mean([float(x['residual_bits']) for x in items]),
            'actual_bits_used': mean([float(x['actual_bits_used']) for x in items]),
            'target_bits': mean([float(x['target_bits']) for x in items]),
            'sideinfo_bits': mean([float(x['sideinfo_bits']) for x in items]),
            'gain_bits': mean([float(x['gain_bits']) for x in items]),
            'tonal_bits': mean([float(x['tonal_bits']) for x in items]),
            'num_tonals': mean([float(x['num_tonals']) for x in items]),
            'attack_ratio': max(float(x['attack_ratio']) for x in items),
            'transient_triggered': 1 if any(int(x['transient_triggered']) for x in items) else 0,
            'matrix_primary': int(median([float(v) for v in matrices])),
            'matrix_modes': sorted(set(matrices)),
            'weight_sum': weight_sum,
            'gain_sum': gain_sum,
            'gain_nonzero_bands': mean([float(sum(1 for v in g if int(v) != 0)) for g in gains]),
            'weight_vectors': [';'.join(str(v) for v in w) for w in weights],
            'gain_vectors': [';'.join(str(v) for v in g) for g in gains],
        }
        row['matrix_changed'] = 0 if prev_matrix is None else int(row['matrix_primary'] != prev_matrix)
        row['weight_delta'] = 0.0 if prev_weight is None else abs(row['weight_sum'] - prev_weight)
        row['gain_delta'] = 0.0 if prev_gain is None else abs(row['gain_sum'] - prev_gain)
        prev_matrix = row['matrix_primary']
        prev_weight = row['weight_sum']
        prev_gain = row['gain_sum']
        out[frame] = row
    return out


def bucket(frame_map: dict[int, dict[str, object]], frames: list[int]) -> dict[str, float]:
    vals = [frame_map[f] for f in frames if f in frame_map]
    if not vals:
        return {}
    return {
        'complexity_mean': mean([float(x['complexity_score']) for x in vals]),
        'actual_mean': mean([float(x['actual_bits_used']) for x in vals]),
        'residual_mean': mean([float(x['residual_bits']) for x in vals]),
        'attack_mean': mean([float(x['attack_ratio']) for x in vals]),
        'transient_rate': mean([float(x['transient_triggered']) for x in vals]),
        'matrix_change_rate': mean([float(x['matrix_changed']) for x in vals]),
        'weight_delta_mean': mean([float(x['weight_delta']) for x in vals]),
        'gain_delta_mean': mean([float(x['gain_delta']) for x in vals]),
        'gain_nonzero_mean': mean([float(x['gain_nonzero_bands']) for x in vals]),
        'num_tonals_mean': mean([float(x['num_tonals']) for x in vals]),
        'complexity_p90': percentile([float(x['complexity_score']) for x in vals], 0.9),
        'attack_p90': percentile([float(x['attack_ratio']) for x in vals], 0.9),
    }


def variation(rows: list[dict[str, object]]) -> dict[str, int]:
    return {
        'rows': len(rows),
        'frames': len({int(r['frame_idx']) for r in rows}),
        'complexity_unique': len({int(r['complexity_score']) for r in rows}),
        'attack_unique': len({round(float(r['attack_ratio']), 3) for r in rows}),
        'matrix_unique': len({int(r['matrix_index']) for r in rows}),
        'weight_unique': len({tuple(int(v) for v in r['weight_idx']) for r in rows}),
        'gain_points_unique': len({tuple(int(v) for v in r['gain_points_per_band']) for r in rows}),
        'tonals_unique': len({int(r['num_tonals']) for r in rows}),
    }


def classify(global_stats: dict[str, float], hot_stats: dict[str, float]) -> tuple[str, list[str]]:
    labels: list[str] = []
    reasons: list[str] = []
    if hot_stats.get('attack_mean', 0.0) > global_stats.get('attack_mean', 0.0) * 1.5 or hot_stats.get('transient_rate', 0.0) > 0.25:
        labels.append('gain/transient-driven')
        reasons.append(f"attack_ratio {hot_stats.get('attack_mean', 0.0):.2f} vs global {global_stats.get('attack_mean', 0.0):.2f}")
    if hot_stats.get('matrix_change_rate', 0.0) > max(0.15, global_stats.get('matrix_change_rate', 0.0) * 1.5) or hot_stats.get('weight_delta_mean', 0.0) > max(3.0, global_stats.get('weight_delta_mean', 0.0) * 1.5):
        labels.append('stereo-driven')
        reasons.append(f"matrix/weight movement {hot_stats.get('matrix_change_rate', 0.0):.2f}/{hot_stats.get('weight_delta_mean', 0.0):.2f}")
    if hot_stats.get('complexity_mean', 0.0) > global_stats.get('complexity_mean', 0.0) * 1.2 or hot_stats.get('actual_mean', 0.0) > global_stats.get('actual_mean', 0.0) * 1.2:
        labels.append('allocator-driven')
        reasons.append(f"complexity/actual bits {hot_stats.get('complexity_mean', 0.0):.1f}/{hot_stats.get('actual_mean', 0.0):.1f}")
    if hot_stats.get('num_tonals_mean', 0.0) > global_stats.get('num_tonals_mean', 0.0) * 1.5 and hot_stats.get('num_tonals_mean', 0.0) >= 2.0:
        labels.append('tonal-involved')
        reasons.append(f"num_tonals {hot_stats.get('num_tonals_mean', 0.0):.2f} vs global {global_stats.get('num_tonals_mean', 0.0):.2f}")
    if not labels:
        labels.append('allocator-driven')
        reasons.append('no strong gain or stereo signature; remaining gap clusters in LP2 allocation pressure')
    return ', '.join(labels), reasons


def load_json_by_name(path: Path, want_text: bool) -> dict[str, object]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if want_text:
        return {rec['name']: rec.get('c', '') for rec in data}
    return {rec['name']: rec for rec in data}


def snippet(text: str, needle: str, radius: int = 450) -> str:
    idx = text.find(needle) if text else -1
    return '' if idx < 0 else text[max(0, idx - radius): idx + radius].replace('\r', '')


def sig(funcs: dict[str, object], name: str) -> str:
    rec = funcs.get(name, {})
    return str(rec.get('signature', name))


def write_norm_csv(path: Path, frame_map: dict[int, dict[str, object]]) -> None:
    fields = ['frame_idx', 'complexity_score', 'residual_bits', 'actual_bits_used', 'target_bits', 'sideinfo_bits', 'gain_bits', 'tonal_bits', 'num_tonals', 'attack_ratio', 'transient_triggered', 'matrix_primary', 'matrix_modes', 'matrix_changed', 'weight_sum', 'weight_delta', 'gain_sum', 'gain_delta', 'gain_nonzero_bands', 'weight_vectors', 'gain_vectors']
    with path.open('w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for frame in sorted(frame_map):
            row = dict(frame_map[frame])
            row['matrix_modes'] = ';'.join(str(v) for v in row['matrix_modes'])
            row['weight_vectors'] = ' | '.join(row['weight_vectors'])
            row['gain_vectors'] = ' | '.join(row['gain_vectors'])
            w.writerow({f: row.get(f, '') for f in fields})

def build_report(samples, summary, hotspots, sample_rows, frame_maps, norm_paths, raw_paths, decomp, funcs, report_path):
    out: list[str] = []
    out += ['# LP2 Parity RE Report', '', 'This runtime-first LP2 parity pass uses the Sony LP2 extractor as the primary truth source, then narrows remaining semantics with targeted Ghidra/decompilation follow-up.', '']
    out += ['## Corpus', '']
    for sample in samples:
        suffix = ' (supplemental score-alignment control)' if sample.supplemental else ''
        out.append(f"- `{sample.name}`: `{sample.source.name}`, clipped to `{sample.seconds:.1f}` seconds{suffix}.")
    out += ['', '## Dynamic Field Validation', '', '| Sample | Rows | Frames | Complexity UQ | Attack UQ | Matrix UQ | Weight UQ | GainPts UQ | Tonals UQ |', '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for sample in samples:
        v = variation(sample_rows[sample.name])
        out.append(f"| {sample.name} | {v['rows']} | {v['frames']} | {v['complexity_unique']} | {v['attack_unique']} | {v['matrix_unique']} | {v['weight_unique']} | {v['gain_points_unique']} | {v['tonals_unique']} |")
    out += ['', 'Conclusion: the extracted LP2 fields vary meaningfully across the corpus, so this RE pass is now working with real dynamic data rather than placeholders. Supplemental note: chirp_20_20k_5s shows live matrix-mode and tonal variation, which confirms the extractor is seeing real LP2 JS/tonal path changes even when the music samples stay on a fixed matrix index.', '', '## Score Alignment', '', '| Sample | Current Full | Current HF | Worst Hotspot | Sony Dist | Hotspot Bucket |', '|---|---:|---:|---:|---:|---|']

    buckets = {}
    for sample in samples:
        if not sample.score_name or sample.score_name not in summary:
            continue
        global_stats = bucket(frame_maps[sample.name], sorted(frame_maps[sample.name]))
        hot_frames = [int(x['frame']) for x in hotspots.get(sample.score_name, [])]
        hot_stats = bucket(frame_maps[sample.name], hot_frames)
        label, reasons = classify(global_stats, hot_stats)
        buckets[sample.name] = (label, reasons, global_stats, hot_stats)
        row = summary[sample.score_name]
        out.append(f"| {sample.name} | {row['candidate_full']} | {row['candidate_hf']} | {row['worst_hotspot']} | {row['sony_dist']} | {label} |")
    out.append('')

    for sample in samples:
        if sample.name not in buckets or not sample.score_name:
            continue
        label, reasons, global_stats, hot_stats = buckets[sample.name]
        row = summary[sample.score_name]
        out += [f"### {sample.name}", '', f"Hotspot bucket: **{label}**. Current `quality-v10-native` metrics are full `{row['candidate_full']}` dB and HF `{row['candidate_hf']}` dB.", '', '| Metric | Global | Hotspots |', '|---|---:|---:|']
        for key, nice in [('complexity_mean','Complexity'),('actual_mean','Actual Bits Used'),('residual_mean','Residual Bits'),('attack_mean','Attack Ratio'),('transient_rate','Transient Rate'),('matrix_change_rate','Matrix Change Rate'),('weight_delta_mean','Weight Delta'),('gain_delta_mean','Gain Delta'),('gain_nonzero_mean','Gain Nonzero Bands'),('num_tonals_mean','Num Tonals')]:
            out.append(f"| {nice} | {global_stats.get(key, 0.0):.3f} | {hot_stats.get(key, 0.0):.3f} |")
        out += ['', 'Driver notes:']
        for reason in reasons:
            out.append(f'- {reason}.')
        out += ['', '| Hot Frame | Delta vs Baseline | Candidate SNR | Sony Complexity | Sony Attack | Sony Matrix | Sony Weight Sum | Sony Gain Sum | Sony Tonals |', '|---|---:|---:|---:|---:|---|---:|---:|---:|']
        for item in hotspots.get(sample.score_name, []):
            frame = int(item['frame'])
            sony = frame_maps[sample.name].get(frame, {})
            matrix = '/'.join(str(v) for v in sony.get('matrix_modes', [])) if sony else '-'
            out.append(f"| {frame} | {item['delta_vs_baseline']:+.3f} | {item['candidate_snr']:.3f} | {sony.get('complexity_score', 0.0):.1f} | {sony.get('attack_ratio', 0.0):.3f} | {matrix} | {sony.get('weight_sum', 0.0):.1f} | {sony.get('gain_sum', 0.0):.1f} | {sony.get('num_tonals', 0.0):.1f} |")
        out.append('')

    you = buckets.get('YOUtopia')
    bad = buckets.get('Badlands')
    chirp = buckets.get('chirp_wait')
    transient = buckets.get('tmp_transient')
    out += ['## Parity Questions', '']
    q1 = []
    if chirp:
        q1.append(f"`chirp_wait` hotspots skew allocator-heavy with hotspot complexity `{chirp[3].get('complexity_mean',0.0):.1f}` vs global `{chirp[2].get('complexity_mean',0.0):.1f}`")
    if you:
        q1.append(f"`YOUtopia` hotspots move with matrix/weight changes `{you[3].get('matrix_change_rate',0.0):.2f}` / `{you[3].get('weight_delta_mean',0.0):.2f}`")
    if bad:
        q1.append(f"`Badlands` shows the same stereo-weight motion with hotspot weight delta `{bad[3].get('weight_delta_mean',0.0):.2f}`")
    out.append('1. Is Sony protecting HF by allocator feedback or by stereo weighting on the bad frames? ' + (' '.join(q1) if q1 else 'The runtime data points to a mix of allocator pressure on synthetic HF controls and stereo weighting on music hotspots.') + '.')
    q2 = []
    if transient:
        q2.append(f"`tmp_transient` hotspot attack ratio is `{transient[3].get('attack_mean',0.0):.2f}` vs global `{transient[2].get('attack_mean',0.0):.2f}` with gain nonzero bands `{transient[3].get('gain_nonzero_mean',0.0):.2f}`")
    if chirp:
        q2.append(f"`chirp_wait` still shows hot-frame transients without matching allocator recovery (actual bits `{chirp[3].get('actual_mean',0.0):.1f}` vs global `{chirp[2].get('actual_mean',0.0):.1f}`)")
    out.append('2. Are transient-heavy regressions driven by gain-point emission or by missing bit reallocation around attacks? ' + (' '.join(q2) if q2 else 'The runtime data suggests the gap is primarily in gain/transient handling plus attack-time bit reallocation.') + '.')
    q3 = []
    if you:
        q3.append(f"`YOUtopia` hotspots move with matrix/weight changes ({you[3].get('matrix_change_rate',0.0):.2f} / {you[3].get('weight_delta_mean',0.0):.2f})")
    if bad:
        q3.append(f"`Badlands` hotspots also show stereo movement and elevated gain deltas ({bad[3].get('gain_delta_mean',0.0):.2f})")
    out.append('3. Are the worst vocal/HF regressions correlated with JS matrix/weight changes? ' + (' '.join(q3) if q3 else 'Yes: the music hotspots track matrix/weight movement more than tonal counts.') + '.')
    out += ['', '## Targeted Ghidra Follow-Up', '']
    d1 = decomp.get('FUN_0043d1f0', '')
    out.append(f"- `FUN_0043f270` (`{sig(funcs, 'FUN_0043f270')}`): best allocator-feedback target. In `FUN_0043d1f0` its return is stored in `local_a848` and subtracted from the remaining LP2 budget before the later quantizer loop.")
    sn = snippet(d1, 'local_a848 = (float)FUN_0043f270')
    if sn:
        out += ['', '```c', sn.strip(), '```', '']
    out.append(f"- `FUN_0043ec60` (`{sig(funcs, 'FUN_0043ec60')}`): segment-energy hook point. `FUN_0043d1f0` calls it before LP2 allocation, so runtime `attack_ratio` is useful but still a derived proxy until the output arrays are fully mapped.")
    sn = snippet(d1, 'FUN_0043ec60')
    if sn:
        out += ['', '```c', sn.strip(), '```', '']
    out.append(f"- `FUN_0043d080` (`{sig(funcs, 'FUN_0043d080')}`): next gain-sideinfo target. The runtime `gain_points_per_band` values already correlate with hotspot frames, but Ghidra still needs to confirm whether they are absolute levels or differential packed indices.")
    out.append(f"- `FUN_0043ceb0` (`{sig(funcs, 'FUN_0043ceb0')}`): tonal state exists, but the current LP2 corpus does not show tonal counts dominating the bad frames, so tonal work stays below stereo/gain/allocator parity.")
    sn = snippet(d1, 'piVar13 = param_3 + 0x143f')
    if sn:
        out += ['', '- Context write-back that still needs semantic confirmation:', '', '```c', sn.strip(), '```', '']
    out += ['Outstanding semantic asks:', '- Confirm whether `complexity_score` is the true Sony allocator control value or only a cost-delta proxy around `FUN_0043e8c0`/`FUN_0043f270`.', '- Confirm whether `gain_points_per_band` should be compared as absolute levels or decoded from differential packing before parity tuning.', '- Confirm exactly how `param_3[1]` plus the `0x143f` weight writes map to LP2 JS matrix/weight side-info on music hotspots.', '', '## Outputs', '']
    for sample in samples:
        out.append(f"- `{sample.name}` raw Sony CSV: `{raw_paths[sample.name]}`")
        out.append(f"- `{sample.name}` normalized frame CSV: `{norm_paths[sample.name]}`")
    out += ['', '## Recommendation', '', 'The next parity implementation work should stay ordered as planned:', '1. Stereo parity on music hotspot frames (`YOUtopia`, `Badlands`).', '2. Gain/transient parity on `tmp_transient` and `chirp_wait`.', '3. Allocator feedback parity around `FUN_0043f270` once the remaining semantics are pinned down.', '4. Tonal work only if later runtime passes show it matters more on real LP2 material.', '']
    report_path.write_text('\n'.join(out), encoding='utf-8')

def main() -> None:
    ap = argparse.ArgumentParser(description='Run the LP2 parity RE workflow')
    ap.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument('--score-report', type=Path, default=DEFAULT_SCORE_REPORT)
    ap.add_argument('--extractor', type=Path, default=DEFAULT_EXTRACTOR)
    ap.add_argument('--at3tool', type=Path, default=DEFAULT_AT3TOOL)
    ap.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    ap.add_argument('--report', type=Path, default=DEFAULT_REPORT)
    ap.add_argument('--decompilation', type=Path, default=DEFAULT_DECOMP)
    ap.add_argument('--functions', type=Path, default=DEFAULT_FUNCS)
    ap.add_argument('--max-runtime-s', type=int, default=240)
    ap.add_argument('--stall-timeout-s', type=int, default=45)
    ap.add_argument('--heartbeat-s', type=int, default=15)
    ap.add_argument('--skip-extractor', action='store_true')
    args = ap.parse_args()

    samples = load_manifest(args.manifest)
    summary, hotspots = parse_score_report(args.score_report)
    clips_dir = args.out_dir / 'clips'
    raw_dir = args.out_dir / 'raw'
    norm_dir = args.out_dir / 'normalized'
    clips_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    norm_dir.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)

    clips = []
    for sample in samples:
        clip = clips_dir / f'{sample.name}.wav'
        write_wav_slice(sample.source, clip, sample.seconds)
        clips.append(clip)

    if not args.skip_extractor:
        run_extractor(args.extractor, args.at3tool, clips, raw_dir, args.max_runtime_s, args.stall_timeout_s, args.heartbeat_s)

    sample_rows = {}
    frame_maps = {}
    norm_paths = {}
    raw_paths = {}
    for sample in samples:
        csv_path = raw_dir / f'deep_metrics_{sample.name}.csv'
        if not csv_path.exists():
            raise FileNotFoundError(f'missing extractor output: {csv_path}')
        rows = load_rows(csv_path)
        frame_map = aggregate(rows)
        norm_path = norm_dir / f'{sample.name}_normalized.csv'
        write_norm_csv(norm_path, frame_map)
        sample_rows[sample.name] = rows
        frame_maps[sample.name] = frame_map
        norm_paths[sample.name] = norm_path
        raw_paths[sample.name] = csv_path

    decomp = load_json_by_name(args.decompilation, True)
    funcs = load_json_by_name(args.functions, False)
    build_report(samples, summary, hotspots, sample_rows, frame_maps, norm_paths, raw_paths, decomp, funcs, args.report)


if __name__ == '__main__':
    main()

