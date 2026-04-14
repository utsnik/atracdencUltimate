# ATRAC3 LP2 Parity Project: Technical Forensic Log

This document provides an exhaustive technical record of the development path taken to achieve bit-exact parity for ATRAC3 LP2 (132kbps).

---

## Phase 1: Signal Chain Synchronization (Waveform Alignment)
**Goal**: Match the exact time-alignment and phase of the Sony `at3tool.exe` output.

### 1.1 QMF Tree Architecture
- **Discovery**: Traditional QMF (Quadrature Mirror Filter) banks introduce a cascaded delay. Forensic analysis of the Sony pulse response showed specialized handling.
- **Implementation**: Modified `atrac3_qmf.h` to optimize history buffer management. Standardized on the MDCT-to-QMF timing alignment found in early hardware decoders.

### 1.2 MDCT Window & Symmetry
- **Discovery**: Earlier `atracdenc` versions used an asymmetric window with a -4.0 sample offset. 
- **Implementation**: Standardized on a 512-point symmetric sine window in `atrac3.h`. Verified that the Sony decoder does not use the asymmetric offset for LP2.

### 1.3 Overlap-Add History Management
- **Issue**: MDCT transformation requires 512 samples (256 old + 256 new).
- **Fix**: Implemented `PcmBuffer.Shift(false)` in `atrac3denc.cpp` to maintain the 256-sample history across frame boundaries.

---

## Phase 2: RIFF Container Forensics (Initialization Parity)
**Goal**: Satisfy the strict header validation of Sony's hardware-derived decoders.

### 2.1 The 384-Byte Block Alignment
- **Discovery**: While an LP2 frame is 192 bytes, Sony decoders require `BlockAlign = 384`.
- **Rationale**: Setting `BlockAlign` to 192 caused error `0x1000105`. Standardizing to 384 resolved the initialization crash.

### 2.2 WAVE_FORMAT_SONY_SCX (0x0270)
- **Extradata Detail**: Matched to Sony v3.0 tool (52 bytes total `fmt` chunk).
    - Hardcoded `extradata_size = 34` with 20 bytes of zero-padding at the end.

---

## Phase 3: Bitstream Structural Integrity (Serialization)
**Goal**: Correct the serialized bitstream order to prevent decoder desync.

### 3.1 The "Mono-Sync" Protocol
- **Discovery**: Sony LP2 uses a "Unit 0 + Extension" stream.
    - **Unit 0**: Writes `0xA2` syncword.
    - **Unit 1**: Writes a single `0` (1 bit) flag.
- **Implementation**: Forced 96-byte padding for Unit 0 to ensure Unit 1 starts at a deterministic offset.

### 3.2 Fixed Bit-Budgeting
- **Bug Fix**: Resolved double-subtraction of frame headers in the Joint Stereo calculation.
- **Serialization**: Enforced strict sound-unit boundaries in `atrac3_bitstream.cpp`.

---

## Phase 4: Build System Alignment (MSVC)
**Goal**: Overcome MSVC-specific compilation barriers for rapid iteration.

### 4.1 ODR Fixes
- **Issue**: Multiple definition errors in VS2022 linker for `static constexpr` members.
- **Resolution**: Utilized C++17 inline initialization.

### 4.2 Automated Benchmarking
- **Implementation**: Created `build_atracdenc.ps1` and `verify_atracdenc_snr.py` for headless terminal validation.

---

## Phase 5: GHA & Tonal Parameter Mapping
**Goal**: Align the GHA (Generalized Harmonic Analysis) component of ATRAC3 with reference tools.

### 5.1 Gain Control Calibration
- **Discovery**: Sony tools use a specific gain control field in Unit 0.
- **Implementation**: Calibrated the gain control threshold to prevent overflow into the spectral residue field.

---

## Phase 6: QMF Delay Calibration (The 11-Sample Lag)
**Goal**: Identify the exact history buffer offset in the Sony analyzer.

### 6.1 Recursive Delay Sweep
- **Discovery**: Forensic analysis via `SonyRecursiveDelaySweep.py` revealed a consistent **11-sample lag** in the Sony reference analyzer.
- **Implementation**: Hardcoded the 11-sample delay in the QMF analysis chain to ensure mdct-to-pcm parity.

---

## Phase 7: Subband Mapping Optimization ({0, 1, 3, 2})
**Goal**: Solve the subband frequency mapping mismatch.

### 7.1 Forensic Audit Sweep
- **Discovery**: Brute-force analysis of the Sony QMF bank revealed a non-linear subband order.
- **Implementation**: Reordered the analyzer outputs to follow the `{0, 1, 3, 2}` pattern (mapping Sony bands 2 and 3 to their correct frequency indices).

---

## Phase 8: Spectral Polarity & Mirroring
**Goal**: Correct the subband sign inversions required by the QMF mirror properties.

### 8.1 Polarity Sweep
- **Implementation**: Iterated through $2^4$ sign combinations.
- **Winning Configuration**: Confirmed that Band 1 and Band 3 require mirroring/sign-reversal to maintain phase lock with the side-band cross-talk cancellation.

---

## Phase 9: Active Signal Activation & Phase-Lock
**Goal**: Break the -100 dB SNR barrier for non-zero test signals.

### 9.1 Phase-Lock Reversal
- **Issue**: SNR remained at -100 dB despite correct containers.
- **Discovery**: Discovered a phase inversion in subbands 1 and 2 (Sony 1 and 3). 
- **Fix**: Re-calibrated the `PCM De-interleaving` in `atrac3denc.cpp` to ensure stereo buffers are phase-aligned before analysis.

---

## Phase 10: Final Parity & Tonal Stabilization (Current)
**Goal**: Achieve the 57 dB bit-exact target.

### 10.1 Tonal Residue Porting
- **Status**: Porting the high-fidelity MDCT bin-zeroing logic from ATRAC3plus.
- **Target**: Eliminate quantization noise in the 1kHz sine-wave test to match the Sony reference SNR of **56.96 dB**.

---

---

## Phase 11: Bit-Allocation Parity & Weighting Extraction (2026-04-11)
**Goal**: Match the iterative bit-allocation heuristic of `at3tool.exe`.

### 11.1 Weighting Factor Extraction
- **Discovery**: Analyzed `FUN_0043d1f0` in Ghidra. Found that Sony uses specific weighting factors (1/x) for each BFU index, differing from the previously used hardcoded values.
- **Constants**:
  - `i < 8`: 1/3.0
  - `i < 12`: 1/3.3
  - `i < 16`: 1/3.4
  - `i < 18`: 1/3.5
  - `i < 26`: 1/3.6
  - `i < 28`: 1/3.8
  - `i < 30`: 0.0 (Weighting disabled)
  - `else`: 1/4.2
- **Implementation**: Updated `CalcBitsAllocation` in `atrac3_bitstream.cpp`.

### 11.2 Frequency-Dependent Shift Scaling
- **Discovery**: The "shift" (waterfilling baseline) is scaled per frequency band in `at3tool`.
- **Factors**:
  - `i < 1`: 0.2x
  - `i < 2`: 0.3x
  - `i < 8`: 0.4x
  - `i < 18`: 0.6x
  - `else`: 1.0x
- **Implementation**: Integrated per-band `shiftScale` logic.

### 11.3 Results & The FFmpeg Polarity Regression
- **Metric**: Sony SNR reached **20.20 dB** (Up from prior low).
- **Issue**: FFmpeg SNR dropped to **-2.61 dB**. This indicates a fundamental polarity inversion in the subband MDCTs relative to the FFmpeg implementation of ATRAC3.

---

## Current Metrics (Updated)
- **Sony Baseline**: 56.96 dB
- **atracdenc Current**: **20.20 dB** (with Corrected Weighting)
- **FFmpeg Baseline**: ~50 dB
- **atracdenc Current (FFmpeg)**: **-2.61 dB** (Phase Inverted)
- **Status**: Phase 12 (Polarity Sweep) In-Progress.
