# Agent Handoff: ATRAC3 (LP2 / LP4) Parity Project

## Context
This project aims to achieve audio quality and bitstream parity with Sony's `at3tool.exe` for the ATRAC3 (MiniDisc LP2/LP4) format. We previously achieved parity for ATRAC3plus (PSP/Hi-MD).

## Key Technical Discoveries
The existing `atracdenc` ATRAC3 implementation was found to have three critical blockers:

1. **Bitrate Mapping Bug**: `main.cpp` used `bitrate * 1024` for lookup. For `132kbps`, this calculated `135,168`, which matched the `146,081` entry (424-byte frames). Official LP2 MUST be **132,300 bps** (384-byte frames).
2. **Signal Scaling Bug**: `atrac3denc.cpp` used a hardcoded `/ 4.0` scaling, losing 12 dB of dynamic range. Removing it entirely caused clipping. The optimal scaling was found to be **/ 1.25**.
3. **RIFF Header Incompatibility**: Sony tools require a **34-byte extradata** subchunk (total `fmt` size 52). `atracdenc` was outputting a minimal header that was rejected by official decoders.

## Current Status
- **Phase 1 (Baseline)**: Established. Sony baseline SNR is ~44 dB for LP2.
- **Phase 2 (Signal/Parameters)**: FIXED but unverified. `main.cpp` and `atrac3denc.cpp` have been updated with the refined parameters.
- **Phase 3 (RIFF Header)**: FIXED but unverified. `at3.cpp` has been updated to provide the 34-byte padded extradata.
- **Phase 4 (Spectral Suppression)**: PENDING. Porting the tonal suppression logic from ATRAC3plus.

## Next Steps for the Incoming Agent
1. **Verify fixes**: Run `.\build_win.bat` to rebuild the encoder.
2. **Test RIFF Header**: Run `atracdenc -e atrac3 --bitrate 132` and verify the output `.wav` header manually (ensure `fmt` size is 52 and `nBlockAlign` is 384).
3. **Run Quality Sweep**: Execute `python ghidra\reverse\quality\compare_at3_quality.py --at3tool ... --atracdenc ... --codec atrac3 --bitrate 132`.
4. **Implement Spectral Suppression**: Port MDCT bin-zeroing logic from the ATRAC3plus path to `atrac3_bitstream.cpp`.

## Reference Files
- [Implementation Plan](file:///c:/Users/Igland/Antigravity/Ghidra/atracdenc/implementation_plan.md)
- [Task Tracker](file:///c:/Users/Igland/Antigravity/Ghidra/atracdenc/task.md)
- Gold Standard Tool: `ghidra\reverse\windows\at3tool.exe`
