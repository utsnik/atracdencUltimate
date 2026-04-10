# ATRAC3 LP2 Forensic Restoration Guide (Restoration Milestone v1.0)

**Project Identifier**: AtracDEnc LP2 Parity Restoration
**Status**: Playable (Structural Sync Achieved)
**Target Bitrate**: 132kbps (Joint Stereo)
**Decoder Baseline**: Sony `at3tool.exe` (v3.0.0.0)

## 1. The Breakthrough: The "Borough" of Sync Errors

After an exhaustive forensic analysis of the official Sony reference bitstreams (`baseline_lp2.at3.wav`), we identified three "Magic" constraints that were causing the Sony decoder to return `0x1000105` (Sync Error) or fail silently.

### A. Tight-Packing (The 192-Byte Myth)
Standard documentation often implies that dual-channel LP2 frames (384 bytes) contain two units padded to 192 bytes each. **THIS IS INCORRECT.**
- **Finding**: Sony LP2 bitstreams use **Tight Packing**. The second Sound Unit (Unit ID `0x28`) follows the first channel's spectral data *immediately*, without 192-byte alignment.
- **Verification**: Byte-level dumping of the reference showed the second `0xA2` (Unit ID 0x28 + Bands 2) appearing at arbitrary byte offsets (often around Byte 10-18) rather than Byte 192.

### B. The Dual ID Mirror
The decoder expects both stereo segments to be introduced by the `0x28` Sound Unit ID. 
- **Legacy Error**: Attempting to use the mid-stream identifier (`0x03`) associated with Joint Stereo in some ATRAC specifications fails in the LP2 132kbps context.

### C. The `.at3.wav` Extension Constraint
The Sony decoder executable is environmental-sensitive.
- **Finding**: Files named `test.wav` or `output.at3` frequently trigger the `Usage` help text even if the binary content is 100% correct.
- **Requirement**: The output filename **MUST** end in strictly `.at3.wav` for the decoder to enter ATRAC3 processing mode.

---

## 2. Structural Requirements (Header Parity)

The RIFF container must be a bit-perfect fingerprint. The following hex indices are critical:

| Offset | Field | Value (Hex) | Requirement |
| :--- | :--- | :--- | :--- |
| `0x14` | Codec ID | `70 02` | **0x0270** (ATRAC3) |
| `0x20` | BlockAlign | `80 01` | **384** (LP2 Standard) |
| `0x3C` | Sample Count | `XX XX XX XX` | **(Frames * 1024) - 2048** (The Forensic Offset) |

**The Forensic Offset**: Sony decoders interpret the `fact` chunk sample count as "Playable Samples." There is an approximate 2048 sample preamble (reduction) required to satisfy the block-to-sample mapping check.

---

## 3. Reproducibility Checklist

To recreate the working state from source:

1.  **Clone Branch**: `lp2-restoration-release`
2.  **Verify `src/at3.cpp`**: Ensure the `baselineHeader[80]` template is being used for the `fmt` and `fact` chunks.
3.  **Verify `src/atrac/at3/atrac3_bitstream.cpp`**: 
    - `WriteSoundUnit` must loop twice writing ID `0x28` to the **SAME** `fullBitStream`.
    - No `while` padding between units.
4.  **Execute**:
    ```powershell
    .\atracdenc.exe -e atrac3 -i input.wav -o output.at3.wav --bitrate 132
    ```
5.  **Validate**:
    ```powershell
    at3tool.exe -d output.at3.wav decoded.wav
    ```

---

## 4. Known Status (Fidelity)
As of v1.0, the signal chain prioritizes **Structural Compliance**. The decoder accepts the frames and produces audible audio. Fidelity tuning (matching the specific MDCT scaling behavior of the Sony ASIC) is the objective of v2.0.

**DOCUMENTATION RESTORED.** No more Borough.
