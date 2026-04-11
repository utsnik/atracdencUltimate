# LP2 Parity Notes (While RE Dumps Are Pending)

## Current Best Profile Snapshot

On current binary (`build2/src/atracdenc.exe`) at true LP2:

- `--bfuidxconst 32 --ml-hints` is best on `YOUtopia.wav` in our recent sweep.
- It still regresses transient-heavy synthetic material.

## Critical Finding

Decision logs show:

- `tonal_blocks: 0` for essentially all tested frames/channels (`YOUtopia`, `chirp`).

That means tonal coding appears inactive in practice, which likely explains a large part of parity gap vs Sony.

## Tooling Added

- `tools/lp2_profile_sweep.py`:
  - runs profile matrix vs Sony at3tool baseline and prints aligned SNR deltas.
- `tools/decision_log_summary.py`:
  - summarizes `--decision-log` files into frame/channel stats.
- `tools/lp2_adaptive_encode.py`:
  - chooses LP2 profile by simple input features:
    - transient-heavy -> `default`
    - otherwise -> `--bfuidxconst 32 --ml-hints`
- `tools/lp2_frame_snr_compare.py`:
  - compares per-frame SNR between two decoded outputs (with lag alignment).
- `tools/validate_re_dump.py`:
  - checks whether RE per-frame CSV dumps look dynamic or placeholder-like.
- `tools/atracdenc_lp2.py`:
  - convenience CLI mode wrapper:
    - `--mode lp2-adaptive`
    - `--mode default`
    - `--mode ml`
    - `--mode bfu32-ml`

## New Interim Result (No RE Runtime Hooks Yet)

- Adaptive wrapper improved synthetic average delta in recent sweep:
  - from about `-8.14 dB` (`default`) to about `-4.43 dB` (adaptive policy).
- `YOUtopia` remains closer to Sony under the fidelity profile than plain default.
- Adaptive selector upgraded to use frame-aware statistics
  (`burst_ratio`, `mean_frame_crest`) instead of only global track metrics.

## RE Dump Status

- `reverse/per_frame_metrics.csv` and `reverse/metrics.jsonl` currently appear
  generated from hardcoded values in `reverse/ghidra_scripts/ExtractDetailedMetrics.java`,
  not live frame-varying hook captures.
- We should treat current dump values as scaffolding only until dynamic runtime
  extraction is wired.

## What We Need From RE Dumps

From at3tool frame traces:

- tonal component counts per frame,
- tonal bits contribution,
- complexity score behavior around tonal/transient branches,
- gain-point counts per band,
- JS matrix/weight side-info.

These will let us map missing tonal/transient behavior and tune toward Sony parity.
