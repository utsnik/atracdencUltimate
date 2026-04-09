# ATRAC Quality Sweep Report (atrac3)

Bitrate: 132 kbps

## Baseline (at3tool)

- sine_1k_5s.wav: SNR=56.95640563964844 dB, SpectralL1=0.0003716604834935609, AlignedSNR=56.95640563964844 (lag=0)
- chirp_20_20k_5s.wav: SNR=24.14443588256836 dB, SpectralL1=0.0015781773990833723, AlignedSNR=24.14443588256836 (lag=0)
- multitone_5s.wav: SNR=39.34388732910156 dB, SpectralL1=0.0012567982093402703, AlignedSNR=39.34388732910156 (lag=0)
- transient_5s.wav: SNR=45.740867614746094 dB, SpectralL1=0.002460296977163687, AlignedSNR=45.740867614746094 (lag=0)

## Atracdenc Sweep (atrac3)

| Input | SNR | Aligned SNR | Spectral L1 | Delta SNR (vs at3tool) | Delta Aligned SNR |
|---|---:|---:|---:|---:|---:|
| sine_1k_5s.wav | None | None | None | None | None |
| chirp_20_20k_5s.wav | None | None | None | None | None |
| multitone_5s.wav | None | None | None | None | None |
| transient_5s.wav | -1.7149450778961182 | 3.2381792068481445 | 0.024128485131186234 | -47.45581269264221 | -42.50268840789795 |

