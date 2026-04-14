# LP2 Deep Metrics Status (2026-04-11)

## Confirmed
- LP2 path is `0x4d20 -> FUN_0043c5d0 -> FUN_0043d1f0`.
- Prior targets (`0x36d40`, `0x37b40`, `0x38e60`) are not the active LP2 path.
- Working sub-hooks:
  - `0x3ceb0` tonal sideinfo
  - `0x3d080` gain sideinfo
  - `0x3ce80` extra sideinfo

## Late Update (External RE Sync)
- Updated report in `docs/re/reverse_engineering_report_external_2026-04-11.md`
  indicates LP2 branch separation by bitrate:
  - LP4 aligns with `0x36d40` family.
  - LP2 aligns with `0x3d1f0` / `0x3f270` family.
- Important parity implication:
  - zero/near-zero tonal promotion at LP2 can be legitimate behavior,
    so allocator/transient/stereo paths should remain top priority.

## Current Gaps
- `complexity_score`, `residual_bits`, `actual_bits_used` are zero due to cross-hook index mismatch.
- `transient_triggered` is reading a session-level flag, not per-frame/per-band trigger state.
- Per-band arrays (`num_tonals_per_band`, `gain_points_per_band`, `weight_idx`) are not yet read from LP2 context write-back.
- Segment energies (`S0..S7`) and true attack ratio are not yet captured from the `FUN_0043ec60` path.

## Concrete Next Fixes
1. Replace cross-hook frame index sharing with a monotonic per-thread counter keyed at `FUN_0043d1f0` entry.
2. In `FUN_0043d1f0` onLeave, read context arrays:
   - `ctx + ((0x141f + i) * 4)` for per-band bit-allocation-like values
   - `ctx + ((0x143f + i) * 4)` for per-band power/weight values
3. Add hook on `0x3ec60` and dump 8 floats from its segment-energy argument.
4. Move `transient_triggered` source to per-frame/per-band path (not `param_3[0x1860]` session flag).
5. Re-run extraction on:
   - `YOUtopia_source.wav`
   - `C:\Users\Igland\Antigravity\Ghidra\atracdenc_solo_20260411\reverse\quality\input\chirp_20_20k_5s.wav`

## Validation Rule Before Using Dump For Parity
- Within each sample, these fields must vary across frames:
  - `complexity_score`
  - `num_tonals_total` (or per-band tonal counts)
  - `attack_ratio` or `transient_triggered`
  - `matrix_index` or `weights`

## 2026-04-12 Runtime Guard + v6 Extractor Update
- New guarded extractor added:
  - `C:\Users\Igland\Antigravity\Ghidra\ghidra\reverse\windows\deep_metrics_extractor_v6.py`
- Improvements:
  - per-call correlation for LP2 side hooks (`tonal/gain/extra/e8c0`) is now stable,
  - heartbeat logging (`rows`, `max_frame`, `elapsed`, `idle`),
  - max-runtime guard,
  - stall-timeout guard (auto-terminate when frame index stops advancing),
  - optional stale process cleanup (`--kill-stale-at3tool`).
- Current practical run behavior:
  - extraction reaches full frame coverage fast,
  - process can remain alive after useful work; guard now cuts it safely.

### Latest Dynamic Dump Snapshot
- `deep_metrics_YOUtopia_source.csv` rows: `20908` (full stereo frame coverage).
- `deep_metrics_chirp_20_20k_5s.csv` rows: `438`.
- Non-zero/dynamic fields now confirmed:
  - `residual_bits`,
  - `actual_bits_used`,
  - `complexity_score`,
  - `attack_ratio`,
  - `transient_triggered`.
- LP2 tonal behavior remains consistent with current hypothesis:
  - `tonal_promoted_count` remains `0` on YOUtopia/chirp in current hooks.

### Caveat
- Frida prints a recurring Windows ACL warning during forced termination:
  - `Frida-CRITICAL ... Error setting ACLs ...`
- It has not corrupted CSV outputs in current runs, but we should keep a checksum/row-count check after each extraction.
