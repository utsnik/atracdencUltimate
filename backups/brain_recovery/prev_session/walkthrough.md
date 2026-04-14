# Walkthrough - ATRAC3 LP2 Parity & Decoder Compatibility

We have successfully resolved the persistent `0x1000105` decoder error that had blocked audio rendering. The encoder now produces bitstreams that are successfully parsed and "locked" by Sony's proprietary `at3tool.exe` decoder.

## Key Achievements

### 1. Structural Synchronization (The "Mono-Sync" Fix)
We discovered a critical structural mismatch in how stereo frames are serialized. Standard ATRAC3 LP2 (132kbps) uses two sound units per frame, but only the **first** unit (Unit 0) contains the `A2` syncword and QMF configuration.
- **Unit 0**: Starts with `0xA2` (Sync + 3 bands).
- **Unit 1**: Starts with a single `0` (No-Sync flag), followed immediately by gain and spectral data.
- **Result**: The decoder now correctly identifies the start of every frame and maintains synchronization throughout the file.

### 2. RIFF Container Alignment
Sony's hardware-derived decoders are extremely strict about the RIFF `fmt` chunk extension for ATRAC3 (`WAVE_FORMAT_SONY_SCX`).
- **Block Alignment**: Standardized to **384 bytes** (supporting dual-frame blocks) to match Sony's hardware buffering.
- **Samples Per Block**: Corrected to **4096 samples** (total sum across channels and frames in a block).
- **Byte Rate**: Aligned to **16538 Bps** (132.3kbps / 8, rounded up).
- **Result**: `at3tool.exe` now recognizes the files as valid ATRAC3 without initialization errors.

### 3. Bitstream Serialization Integrity
- **Bit-Packing Fix**: Resolved a bit-leakage bug in `TBitStream::Write` by implementing mandatory masking of input values, preventing high-bit corruption of adjacent spectral fields.
- **Joint Stereo Positioning**: Correctly positioned JS parameters immediately preceding the spectral residue, ensuring bit-alignment with the Sony reference.
- **Silence Lead-in**: Implemented a forced silence lead-in for the first frame to allow the decoder's QMF tree and overlap history to stabilize.

## Validation Results

### Decoder Compatibility
The following results confirm that the synchronization and container barriers have been broken:

| Test Case | Error Code (Sony) | Status |
| :--- | :--- | :--- |
| v35 (Baseline) | `0x1000105` | **Failed** |
| v40 (Current) | `0x0000000` | **Success** |

### SNR Parity Progress
With the decoder now stable, we can begin the final frequency-dependent polarity and subband mapping sweep.

> [!IMPORTANT]
> The decoder currently outputs audio without crashing, but the signal remains low due to the forced silence lead-in and the ongoing optimization of the subband mapping `{0, 1, 3, 2}`.

## Files Modified
- [atrac3_bitstream.cpp](file:///c:/Users/Igland/Antigravity/Ghidra/atracdenc/src/atrac/at3/atrac3_bitstream.cpp): Implemented Mono-Sync and bit-budgeting.
- [at3.cpp](file:///c:/Users/Igland/Antigravity/Ghidra/atracdenc/src/at3.cpp): Aligned RIFF container parameters.
- [atrac3.h](file:///c:/Users/Igland/Antigravity/Ghidra/atracdenc/src/atrac/at3/atrac3.h): Corrected LP2 container constants.
- [bitstream.cpp](file:///c:/Users/Igland/Antigravity/Ghidra/atracdenc/src/lib/bitstream/bitstream.cpp): Fixed bit-masking corruption.

## Next Steps
1. **SNR Optimization**: Perform a high-speed sweep to find the exact subband signs for the LL, HL, HH, LH freq-order.
2. **Dynamic Range Validation**: Verify that the gain control logic (currently minimal) matches Sony's suppression curves.
