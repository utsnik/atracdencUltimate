# at3tool LP2 RE Hunt Checklist

This checklist is optimized for your current map:

- `FUN_00436d40` frame entry
- `FUN_00437b40` bit allocation
- `FUN_00438e60` tonal packing

## 1) Joint Stereo (JS) Matrix + Weight Branch Signatures

Goal: isolate where JS side-info is chosen/written (matrix coeff + weight delay fields).

1. Start at `FUN_00436d40`.
2. Find the stereo-mode gate:
   - branch that is only taken when channel mode is stereo pair / JS-capable mode.
   - usually a short chain of `if (channels == 2)` + mode flag checks.
3. Locate the side-info write block that emits:
   - one matrix selector index,
   - then a tight loop writing 4 small weight/delay fields.
4. Branch signature to capture:
   - condition comparing L/R or M/S energies before matrix index is selected,
   - clamp/min-max around a small integer range (matrix index and weight index ranges are small).
5. Dump for each frame:
   - `frame_idx`, `is_js`, `matrix_index`, `weight_idx[4]`,
   - any pre-branch energy terms used by the selector.

## 2) Gain-Point Transient Trigger Signatures

Goal: isolate the "insert gain points vs no points" decisions that protect transients.

1. Trace from `FUN_00436d40` into pre-MDCT / control-analysis region.
2. Find per-band loop (expect 4 subbands in ATRAC3 LP2 path).
3. Inside each band loop, identify:
   - attack detector branch (energy rise / delta / slope),
   - gain-point count clamp (0..7-ish behavior in write path),
   - point location and level quantization branches.
4. Branch signature to capture:
   - threshold compare(s) that flip `num_points` from 0 to >0,
   - look-ahead dependent branch (next-window/buffer influence),
   - suppression branch that prunes extra points.
5. Dump for each frame + band:
   - `attack_metric`, `threshold`, `num_gain_points`,
   - `gain_level[]`, `gain_loc[]`,
   - pre/post-prune point counts.

## 3) Allocator/Complexity Correlation (Your `iStack_510` Track)

Goal: confirm what `iStack_510` controls and how it feeds quantizer pressure.

1. In `FUN_00437b40`, log:
   - target budget,
   - side-info bits,
   - tonal bits,
   - residual budget (`uStack_51c` style),
   - actual used bits after allocation pass.
2. Capture update site of `iStack_510`:
   - before update, after update, and where it is consumed.
3. Verify whether it influences:
   - global shift/scaling term,
   - BFU count/limit,
   - high-band penalties/bonuses.

## 4) Minimal Frida Hook Plan

Hook points (by RVA once rebased):

- `FUN_00436d40` entry/exit: frame index + mode + channel context
- `FUN_00437b40` entry/exit: budget + complexity + bits-used stats
- `FUN_00438e60` entry/exit: tonal count + tonal bits

Log format (CSV/JSONL) per frame:

- `frame,mode,channels,target_bits,sideinfo_bits,tonal_bits,residual_bits,bits_used,complexity`
- `gain_points_b0..b3,matrix_idx,weight0..weight3`

## 5) Killer-Sample Probe Sequence

Run exactly this order to de-risk interpretation:

1. `sine_1k_5s.wav` (sanity/stability)
2. `chirp_20_20k_5s.wav` (HF allocation + JS stress)
3. `multitone_5s.wav` (tonal packing pressure)
4. `transient_5s.wav` (gain/transient logic)
5. `YOUtopia.wav` (real-world mixed stress)

For each sample, compare:

- per-frame `complexity` trend
- `num_gain_points` bursts
- JS matrix/weight changes near audible artifact regions

## 6) What to Send Back For Fast Encoder Parity Work

Please export a compact dump with these columns:

- `frame_idx`
- `target_bits`, `tonal_bits`, `residual_bits`, `bits_used`
- `complexity_score` (`iStack_510` path)
- `matrix_index`, `weight_idx[4]`
- `gain_points_per_band[4]`
- optional: `gain_level/loc` packed values

With that, we can directly map at3tool decisions into our `--decision-log` parity loop.
