## [Unreleased]

### Added
- `--smr-alloc`: Psychoacoustic bit allocation using Bark-scale simultaneous masking (ISO spreading function). Computes per-BFU SMR and modulates the bit allocation divisor by ±10%. Applies a −4% mid-band bias on BFUs 8–25 (~1.5–11 kHz) to prioritise perceptual core precision.
- `--temporal-masking`: Pre-echo protection via temporal energy history. Detects rapid energy increases in the current frame (current/previous energy ratio >4×) and reduces the allocation divisor by up to 15% for at-risk BFUs to prevent pre-echo artifacts.
- `atrac3_bark.h`: Constexpr Bark-scale BFU mapping table (center Hz + Bark values for all 32 BFUs).
- `atrac3_masking.h`: ISO Psychoacoustic Model 1 spreading function (32×32 pre-computed matrix) + CalcMaskingThreshold / CalcSmr inline functions.
