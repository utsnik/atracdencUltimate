# LP2 Stereo-Exp Findings (2026-04-13)

## Summary

`quality-v10-stereo-exp` now activates joint-stereo behavior and parity-informed M/S continuity, but it is not yet decode-valid on LP2 in at3tool.

## What Changed

- Added CLI option `--stereo-exp`.
- Added wrapper mode `quality-v10-stereo-exp`.
- Enabled joint-stereo override path in ATRAC3 container setup, encoder matrixing, and bitstream JS decisions.
- Extended decision-log output with:
  - `stereo_exp_mode`
  - `ms_preserve_side_prev`
  - `ms_hf_risk_prev`
  - `ms_hf_risk`

## Safety Check

- `quality-v10-stable` vs `quality-v10-native` fast gate remained PASS:
  - see `docs/LP2_FAST_STABILITY_GATE_STEREO_EXP_SAFE_2026-04-13.md`

## Stereo-Exp Runtime Evidence

On `scratch/YOUtopia_30s.wav` with decision log:

- `js_enabled: true` on all logged frames.
- `ms_preserve_side` and `ms_hf_risk` are non-zero and frame-varying.
- `ms_continuity_clamped: true` appears on a subset of frames.

## Current Blocker

Encode path is not yet fully LP2-conformant for this JS experiment:

- validation reports decoded duration ratio near zero.
- at3tool decode aborts with `error code : 0x1000105`.

Because of that, wrapper fallback replaces output with `quality-v10-frozen` unless `--no-fallback` is set.

## Next Step

Treat `quality-v10-stereo-exp` as RE-only until JS-at-132300 bitstream conformance is fixed. Focus on LP2 JS side-info packing and frame layout parity before perceptual tuning.
