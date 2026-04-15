## [Unreleased]

### Added
- `--smr-alloc`: Psychoacoustic bit allocation using Bark-scale simultaneous masking (ISO spreading function). Computes per-BFU SMR and modulates the bit allocation divisor by ±10%. Applies a −4% mid-band bias on BFUs 8–25 (~1.5–11 kHz) to prioritise perceptual core precision.
- `--temporal-masking`: Pre-echo protection via temporal energy history. Detects rapid energy increases in the current frame (current/previous energy ratio >2.5x) and reduces the allocation divisor by up to 20% for at-risk BFUs to prevent pre-echo artifacts.
- `atrac3_bark.h`: Constexpr Bark-scale BFU mapping table (center Hz + Bark values for all 32 BFUs).
- `atrac3_masking.h`: ISO Psychoacoustic Model 1 spreading function (32×32 pre-computed matrix) + CalcMaskingThreshold / CalcSmr inline functions.

### Planned
- ML/Neural learned bit allocator (--ml-alloc): per-frame MLP replacing static divisor table, with optional LSTM temporal context. See docs/ML_ROADMAP.md.

### Benchmark Results

**9-track multi-genre benchmark (vs Sony at3tool reference, recommended flags):**

| Track | Genre | delta_full | delta_hf | delta_seg_p10 | delta_seg_med |
|-------|-------|-----------|---------|--------------|--------------|
| Lorde - California | Indie pop | +0.042 | +0.933 | +0.080 | +0.085 |
| Daft Punk - HBFS | Electronic | +0.013 | +0.646 | +0.029 | +0.030 |
| Kendrick - King Kunta | Hip-hop | +0.471 | +0.420 | -0.217 | +0.503 |
| The Weeknd - Gasoline | Synth pop | -0.012 | +0.136 | -0.205 | -0.065 |
| Rise Against - Savior | Punk/rock | -0.124 | +0.091 | -0.145 | -0.098 |
| Fleetwood Mac - Midnight | Classic rock | -0.045 | +0.867 | -0.270 | +0.405 |
| Gundelach - My Frail Body | Ambient | -0.509 | +0.688 | +0.220 | +0.342 |
| Bob Dylan - Big Girl Now | Acoustic folk | -0.987 | +0.728 | -1.257 | -0.973 |
| Miles Davis - All Blues | Jazz | -1.471 | -0.268 | -0.461 | -1.557 |

6 of 9 tracks at or better than Sony on HF. 3 tracks beat Sony on full SNR. Dylan and Miles Davis have structural gaps in the base encoder on wide-dynamic acoustic content — targeted for ML/neural allocator work.

Gain control alone caused severe degradation on YOUtopia (delta_full=−0.372, delta_seg_p10=−0.237). Combined with --smr-alloc and --temporal-masking the psychoacoustic model absorbs the quantization noise, reducing the cost to within statistical noise on most metrics.

**Recommended default encoding flags:** --quality-v10 --quality-v10-stable --smr-alloc --temporal-masking (gain control ON, no --nogaincontrol, no --bfuidxconst)

Removing --bfuidxconst 28 improves HF quality on every track (+0.24 to +0.92 dB delta_hf) with no regressions. The flag artificially caps BFU count, starving high-frequency bands.
