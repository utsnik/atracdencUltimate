# ATRAC3 LP2 Parity Project: Technical Forensic Log

This document provides an exhaustive technical record of the development path taken to achieve bit-exact parity for ATRAC3 LP2 (132kbps).

---

## Phase 1: Signal Chain Synchronization (Waveform Alignment)
**Goal**: Match the exact time-alignment and phase of the Sony `at3tool.exe` output.

### 1.1 QMF Tree Architecture
- **Discovery**: Traditional QMF (Quadrature Mirror Filter) banks introduce a cascaded delay (typically 15-31 samples). Forensic analysis of the Sony pulse response showed **zero delay**.
- **Implementation**: Modified `atrac3_qmf.h` to remove the 15-sample history buffer. The analysis bank now feeds the MDCT directly from the current window, aligning the waveform perfectly with the Sony reference.

### 1.2 MDCT Window & Symmetry
- **Discovery**: Earlier `atracdenc` versions used an asymmetric window with a -4.0 sample offset. 
- **Implementation**: Standardized on a 512-point symmetric sine window in `atrac3.h`. Verified that the Sony decoder does not use the asymmetric offset, which was a source of spectral leakage in previous versions.

### 1.3 Overlap-Add History Management
- **Issue**: MDCT transformation requires 512 samples (256 old + 256 new).
- **Fix**: Implemented `PcmBuffer.Shift(false)` in `atrac3denc.cpp` to maintain the 256-sample history across frame boundaries. This ensures the overlap-add process is continuous, preventing transient "clicks" at frame edges.

---

## Phase 2: RIFF Container Forensics (Initialization Parity)
**Goal**: Satisfy the strict header validation of Sony's hardware-derived decoders.

### 2.1 The 384-Byte Block Alignment
- **Discovery**: While an LP2 frame is 192 bytes (768 bits * 2 units / 8), Sony decoders require `BlockAlign = 384`.
- **Rationale**: The decoder expects a "dual-frame" block. Setting `BlockAlign` to 192 caused the Sony tool to return `0x1000105`. Standardizing to 384 resolved the initialization crash.

### 2.2 WAVE_FORMAT_SONY_SCX (0x0270)
- **Extradata Detail**: The 14-byte extradata block was forensic-matched to the Sony v3.0 tool:
    - Bytes 0-1: `0x0001` (Unknown / Format version)
    - Bytes 2-5: `0x00000800` (2048 Samples per block per channel)
    - Bytes 6-13: `0x00000001 00000001` (Joint Stereo / Band configuration)

---

## Phase 3: Bitstream Structural Integrity (Serialization)
**Goal**: Correct the serialized bitstream order to prevent decoder desync.

### 3.1 The "Mono-Sync" Protocol
- **Discovery**: Sony LP2 is NOT a "True Stereo" stream (two identical A2 units). It is a "Unit 0 + Extension" stream.
- **Implementation**:
    - **Unit 0**: Writes `0x28` (6 bits) for Sync, then `0x02` (2 bits) for 3 QMF bands. Total = `0xA2`.
    - **Unit 1**: Writes a single `0` (1 bit) flag. This matches the "Mono" header style for the side channel, saving 7 bits per frame for spectral residue.

### 3.2 Fixed Bit-Budgeting
- **Double-Accounting Fix**: Resolved a critical bug in `atrac3_bitstream.cpp` where `halfFrameSz` (96 bytes) was being subtracted twice from the budget during the Joint Stereo calculation.
- **Strict 96-Byte Padding**: Implemented an explicit `bitStream->Flush(OutBuffer, 96)` for every sound unit. This guarantees that Unit 1 starts exactly at byte offset 96, even if Unit 0 ends early.

---

## Phase 4: Target Build Resolution
**Goal**: Overcome MSVC-specific compilation barriers.

### 4.1 MSVC C++17 ODR Fix
- **Issue**: `static constexpr` members define-initialized in the header were being redefined in `atrac3.cpp`, causing "multiple definition" errors in the VS2022 linker.
- **Resolution**: Removed redundant definitions. In C++17, these members are implicitly `inline` and only require the header-level initialization.

### 4.2 Verbose Pipeline
- **Implementation**: Updated `build_atracdenc.ps1` to capture all compiler stderr to `build_output.txt`. This revealed hidden undeclared identifiers (`FrameSz` vs `frameSize`) that were causing silent binary stagnation.

---

## Phase 5: Spectral Convergence (Current State)
**Goal**: Resolve the remaining signal desync to achieve 57 dB SNR.

### 5.1 Mirroring & Polarity Mapping
- **Discovery**: Sony QMF banks alternate the spectral polarity of subbands.
- **Forensic Table**:
    - Band 0 (LL): Normal
    - Band 1 (HL): **Mirrored/SwapArray**
    - Band 2 (HH): Normal
    - Band 3 (LH): **Mirrored/SwapArray**
- **Winning Sweep**: Ongoing iteration via `PolaritySweep_v2.py` to identify the final sign configuration for the $\{0, 1, 3, 2\}$ mapping.

---

## Current Metrics
- **Structural Success**: Silence frames are bit-identical to reference.
- **Decoder Stability**: 0% crash rate in `at3tool.exe`.
- **Remaining Task**: Final spectral residue calibration for non-zero signals.
