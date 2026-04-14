# ATRAC3 LP2 Implementation Notes

This document describes the current ATRAC3 LP2 implementation in this branch, how to reproduce it, and which knobs affect quality.

## Scope

- Codec mode: ATRAC3 LP2 at true `132300` bps.
- Container for MD/VLC compatibility: ATRAC3-in-WAV (`.at3.wav`) with ATRAC3 `fmt` extension (`fmt` size `0x20`).
- Input constraints: `44.1 kHz`, PCM WAV.

## Active Encode Path

- CLI entry: `src/main.cpp`
- ATRAC3 encoder: `src/atrac3denc.cpp`
- Bit allocation and sound-unit packing: `src/atrac/at3/atrac3_bitstream.cpp`
- ATRAC3 WAV container writer: `src/at3.cpp`

## LP2 Bitrate Mapping

CLI `--bitrate 132` is mapped to exact LP2 `132300` bps in `src/main.cpp` via `Atrac3CliBitrateToBps()`.

This avoids rounding to nearby profiles (for example `146081`), which can break MD LP2 expectations.

## Container/Compatibility Behavior

The build should use `src/at3.cpp` as the `CreateAt3Output()` provider for WAV output.

- `fmt` chunk includes ATRAC3 extension bytes.
- Header reports ATRAC3 (`0x0270`), stereo, `44.1 kHz`, and LP2 frame layout.

## Quality-Relevant Settings

- `--nogaincontrol`
  - Disables subband gain-control signaling.
  - Usually reduces quality on transient content.
- `--bfuidxconst <1..32>`
  - Forces a fixed BFU range.
  - Lower values can improve effective precision at LP2 by concentrating bits.
- `--notonal`
  - Disables tonal component path (exposed in CLI for tuning/testing).

## LP2 Quality Heuristic

In `src/atrac/at3/atrac3_bitstream.cpp`, `CreateAllocation()` now applies:

- Default BFU search range `24` for LP2 and below (`Params.Bitrate <= 132300`) when `--bfuidxconst` is not set.
- Previous behavior (`32`) is still available with `--bfuidxconst 32`.

Rationale:
- LP2 has limited frame budget; reducing BFU search range helps preserve precision in the most audible ranges.

## Repro Commands

Build:

```powershell
powershell -ExecutionPolicy Bypass -File build_atracdenc2.ps1
```

Encode LP2:

```powershell
build2\src\atracdenc.exe -e atrac3 -i YOUtopia.wav -o YOUtopia_atracdenc_lp2.at3.wav --bitrate 132
```

Quick decode check (FFmpeg):

```powershell
& "C:\Users\Igland\Documents\NRK Downloader\ffmpeg.exe" -v error -i YOUtopia_atracdenc_lp2.at3.wav -f null -
```

## Known Gaps

- Objective quality measurement pipeline needs a single standardized scorer/runbook for this branch.
- Sony encoder parity is not yet reached; additional work is expected in transient/tonal decisioning and quantizer tuning.
