# ATRAC3 LP2 ML Assist Plan (Bitstream-Compatible)

This plan keeps ATRAC3 syntax fully standard for MiniDisc players and uses ML only for encoder decisions.

## Goal

- Improve LP2 quality toward/above Sony `at3tool` without changing container/bitstream format.
- Start with low-risk control knobs already present in the encoder.

## What ML Controls (v1)

Per frame (and optionally per QMF band), predict:

- `bfu_budget_hint` (effective complexity target)
- `tonal_strength_bias` (promote/demote tonal coding aggressiveness)
- `gain_curve_bias` (when to allow stronger gain compensation)
- `hf_noise_shaping_bias` (push bits toward hiss-prone regions)

These become bounded hints, not hard overrides.

## Non-Goals (v1)

- No neural bitstream format.
- No decoder changes.
- No runtime dependency on heavy frameworks.

## Training Signal

Use Sony as teacher from existing reverse assets:

- Teacher outputs: decoded reference quality + extracted frame behavior proxies from snapshots/logs.
- Student target: pick encoder hints that reduce quality gap while staying decodable by `at3tool`.

## Features (cheap + robust)

Frame-level:

- band energies / log-energies
- spectral flatness per band
- transient score (existing detector features)
- tonal candidate count + stability
- inter-channel correlation / JS suitability

Band-level:

- local SNR proxy
- HF ratio and masking proxy
- previous-frame deltas (temporal context)

## Model Choice

Start simple and deterministic:

- Ridge/linear model or tiny tree ensemble exported as constants.
- Optional tiny MLP later only if measurable gain justifies complexity.

## Integration Points

- Main orchestration: `C:\Users\Igland\Antigravity\Ghidra\atracdenc\src\atrac3denc.cpp`
- Bitstream/element budgeting: `C:\Users\Igland\Antigravity\Ghidra\atracdenc\src\atrac\at3\atrac3_bitstream.cpp`
- Scaling/noise behavior: `C:\Users\Igland\Antigravity\Ghidra\atracdenc\src\atrac\atrac_scale.cpp`

Implementation shape:

- `ExtractFrameFeatures(...)`
- `PredictMlHints(...)`
- `ClampHintsToSafeRange(...)`
- apply hints before final scale/tonal/gain decisions.

## Safety Guardrails

- If model output is invalid/out-of-range -> ignore and use current heuristics.
- Confidence gate: fallback to deterministic path on low confidence.
- Hard limits on BFU/gain/tonal biases.
- Must remain decodable by `at3tool` on all regression corpus files.

## Evaluation Loop

Regression corpus:

- YOUtopia + synthetic set (`sine/chirp/multitone/transient`) + extra noise/sine/chirp stress tests.

Gates:

- decode success with `at3tool` = 100%
- no regression on YOUtopia aligned SNR
- average synthetic aligned SNR delta vs Sony must improve from current baseline
- listening spot-check queue for chirp/hiss/transient artifacts

## v1 Milestones

1. Feature dump + dataset builder from current encode path.
2. Train first lightweight model and export static coefficients.
3. Wire inference with safe clamping and fallback.
4. Run full parity harness and compare against deterministic baseline.
