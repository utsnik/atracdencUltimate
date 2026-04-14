# ATRAC3 LP2 Parity Project — Phase 9 & 10

Based on the recovered roadmap, we are currently at the critical transition between **Phase 9 (Active Signal Activation)** and **Phase 10 (Final Parity & Tonal stabilization)**.

## User Review Required

> [!IMPORTANT]
> **Subband Phase Lock**: We have identified that the -100 dB SNR "Silence" failure is a phase-lock issue. The current calibration reversed subbands 1 and 3, but forensic audit of the Sony `{0, 1, 3, 2}` mapping indicates the reversal must target **subbands 1 and 2** (Sony indices 1 and 3) to align with the QMF mirror-polarity.

## Proposed Changes

### Phase 9: Active Signal Activation (Restoration)

#### [MODIFY] [atrac3denc.cpp](file:///c:/Users/Igland/Antigravity/Ghidra/atracdenc/src/atrac3denc.cpp)
- **PCM De-interleaving**: Finalize the `GetLambda` fix to ensure stereo samples are correctly mapped to independent channel buffers before the QMF analysis.
- **LoudFactor Propagation**: Ensure the `Loudness` and `LoudFactor` metrics are correctly calculated and propagated to the bitstream, preventing the encoder from defaulting to a minimal bit-allocation state.

#### [MODIFY] [atrac3_qmf.h](file:///c:/Users/Igland/Antigravity/Ghidra/atracdenc/src/atrac/at3/atrac3_qmf.h)
- **Subband Mapping Optimization**: Implement the `{0, 1, 3, 2}` analyzer mapping discovered via the `brute_force_snr.py` sweep to match the reference encoder's band order.

### Phase 10: Final Parity & Tonal Stabilization

#### [NEW] [TonalSuppression.cpp](file:///c:/Users/Igland/Antigravity/Ghidra/atracdenc/src/atrac/at3/TonalSuppression.cpp) (or port to bitstream)
- **MDCT Bin Zeroing**: Port the tonal component extraction logic from the ATRAC3plus project to zero out peak bins in the residual spectrum. This will free up bits for the quantizer and bring the SNR from ~45 dB to the **57 dB parity target**.

## Open Questions

1. **Phase 10 Definition**: Is "Phase 10" specifically the **Tonal Psychoacoustic Stabilization** (as seen in the earlier bot-related logs) or does it refer to a specific **SNR target (57 dB)** achievement?
2. **Subband 0 Polarity**: Are we certain subband 0 is never inverted? The `silent_sweep.py` results so far suggest it's a fixed normal polarity.

## Verification Plan

### Automated Tests
- `python brute_force_snr.py`: This script should now return a "WINNER" with SNR > 50 dB.
- `python silent_sweep.py`: Verify that the [!!!] PARITY ACHIEVED [!!!] flag is triggered.

### Manual Verification
- **Bit-Level Audit**: Use `SpectralAudit_SU1.py` to confirm that Unit 1 is no longer zeroed out and matches the Sony baseline for the first 32 bits.
