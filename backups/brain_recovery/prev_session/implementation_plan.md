# Phase 9: Active Signal Activation & Parity Verification

This phase focuses on breaking the -100 dB SNR barrier and achieving the final 57 dB bit-exact parity for ATRAC3 LP2. We have successfully decontaminated the build system; now we must restore the active signal chain.

## User Review Required

> [!IMPORTANT]
> The -100 dB SNR failure is confirmed to be a subband phase mismatch. My previous calibration flipped subbands 1 and 3 based on loop indices, but under the {0, 1, 3, 2} Sony subband mapping, the flips must target subbands 1 and 2 (Sony 1 and 3). I am correcting this calibration to restore decoder phase-lock.

## Proposed Changes

### Encoder Signal Chain

#### [MODIFY] [atrac3denc.cpp](file:///c:/Users/Igland/Antigravity/Ghidra/atracdenc/src/atrac3denc.cpp)
- **PCM De-interleaving**: Update the `GetLambda` function to copy interleaved input samples into per-channel buffers before `AnalysisFilterBank` processing.
- **Loudness Logic**: Fix usage of `Loudness` and `LoudFactor` members to ensure bit allocation is not defaulting to a static value.

#### [MODIFY] [atrac3_bitstream.cpp](file:///c:/Users/Igland/Antigravity/Ghidra/atracdenc/src/atrac/at3/atrac3_bitstream.cpp)
- **Silence Threshold**: Relax the `Energy` check threshold from `1e-4f` to `1e-9f` to prevent pruning of test signals.
- **Sync Word Verification**: Confirm `0xA2` sync word is correctly emitted for both LP2 streams.

### Automated Testing

#### [MODIFY] [PolaritySweep_v2.py](file:///c:/Users/Igland/Antigravity/Ghidra/atracdenc/PolaritySweep_v2.py)
- Ensure the script correctly parses the updated `atracdenc.exe` output.

## Verification Plan

### Automated Tests
- **Full Build**: Run `build_atracdenc.ps1` to ensure no regressions.
- **Polarity Sweep**: Run `python PolaritySweep_v2.py`.
- **Target**: We expect SNR to break above 0 dB and reach ~57 dB with the correct polarity mapping (expected winner: `{0, 1, 3, 2}` with odd subband reversal).

### Manual Verification
- Validate the generated `.at3` file in Sony's SonicStage or `at3tool.exe` (if possible) to ensure standard compatibility.
