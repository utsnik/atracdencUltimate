# LP2 Score Workflow

Candidate mode: `quality-v10-stable`; baseline mode: `quality-v10-native`.

| Sample | Candidate Full | Candidate HF | P10 | Median | Vocal Err | Side SNR | Side Ret (dB) | Dur Ratio | Hotspots | Worst Hotspot | Delta Full | Delta HF | Sony Dist | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| YOUtopia | 16.665 | 6.659 | 13.192 | 15.237 | 0.156711 | -3.080 | 0.129 | 1.000 | 8 | -2.658 | -0.599 | +0.042 | 0.645 | FAIL |
| Badlands | 20.807 | 8.938 | 17.050 | 21.062 | 0.090153 | -3.435 | 0.083 | 1.000 | 8 | -2.741 | -0.528 | -0.240 | 1.115 | FAIL |
| chirp_wait | 12.647 | 3.615 | 29.649 | 32.665 | 0.077857 | 0.000 | 0.000 | 1.012 | 8 | -0.000 | -0.024 | -0.017 | 1.712 | PASS |
| tmp_transient | 8.467 | 7.720 | 0.000 | 0.000 | n/a | 0.000 | 0.000 | 1.012 | 7 | -0.122 | -0.003 | -0.024 | 10.663 | FAIL |

## Stability Gate

FAIL

- YOUtopia: youtopia_full, youtopia_hotspot
- Badlands: badlands_full, badlands_hf, badlands_hotspot
- tmp_transient: transient_hotspot

## Hotspots

### YOUtopia

Baseline full `17.264`, HF `6.617`; candidate full `16.665`, HF `6.659`; Sony full `16.486`, HF `7.278`.

| Frame | Delta vs Baseline | HF Energy (dB) | Baseline SNR | Candidate SNR |
|---|---:|---:|---:|---:|
| 390 | -2.658 | 68.23 | 15.849 | 13.191 |
| 441 | -2.477 | 69.08 | 19.915 | 17.438 |
| 535 | -2.297 | 68.03 | 22.592 | 20.295 |
| 524 | -2.282 | 72.43 | 18.665 | 16.383 |
| 375 | -2.275 | 68.11 | 15.265 | 12.990 |
| 636 | -2.189 | 67.93 | 21.976 | 19.787 |
| 591 | -2.101 | 68.69 | 21.370 | 19.270 |
| 243 | -2.026 | 65.47 | 16.536 | 14.511 |

### Badlands

Baseline full `21.334`, HF `9.178`; candidate full `20.807`, HF `8.938`; Sony full `20.381`, HF `9.969`.

| Frame | Delta vs Baseline | HF Energy (dB) | Baseline SNR | Candidate SNR |
|---|---:|---:|---:|---:|
| 504 | -2.741 | 53.52 | 18.475 | 15.734 |
| 288 | -2.560 | 62.26 | 25.922 | 23.362 |
| 2 | -2.455 | 58.93 | 19.573 | 17.118 |
| 473 | -2.303 | 48.32 | 27.517 | 25.214 |
| 213 | -2.109 | 53.70 | 21.834 | 19.725 |
| 512 | -2.107 | 55.23 | 24.958 | 22.850 |
| 221 | -2.067 | 53.16 | 21.728 | 19.662 |
| 542 | -2.045 | 63.48 | 24.349 | 22.304 |

### chirp_wait

Baseline full `12.671`, HF `3.632`; candidate full `12.647`, HF `3.615`; Sony full `13.969`, HF `4.702`.

| Frame | Delta vs Baseline | HF Energy (dB) | Baseline SNR | Candidate SNR |
|---|---:|---:|---:|---:|
| 213 | -0.000 | 90.59 | -0.000 | -0.000 |
| 212 | +0.000 | 90.50 | 0.000 | 0.000 |
| 211 | +0.000 | 90.40 | 0.000 | 0.000 |
| 210 | +0.000 | 90.27 | 0.000 | 0.000 |
| 209 | +0.000 | 90.15 | 0.000 | 0.000 |
| 208 | +0.000 | 90.00 | 0.000 | 0.000 |
| 207 | +0.000 | 89.85 | 0.000 | 0.000 |
| 206 | +0.000 | 89.70 | 0.000 | 0.000 |

### tmp_transient

Baseline full `8.470`, HF `7.744`; candidate full `8.467`, HF `7.720`; Sony full `17.230`, HF `13.795`.

| Frame | Delta vs Baseline | HF Energy (dB) | Baseline SNR | Candidate SNR |
|---|---:|---:|---:|---:|
| 81 | -0.122 | 66.74 | 9.643 | 9.521 |
| 21 | -0.015 | 66.74 | 11.645 | 11.630 |
| 146 | +0.000 | 66.74 | 12.035 | 12.035 |
| 116 | +0.007 | 66.74 | 10.941 | 10.948 |
| 47 | +0.016 | 66.74 | 10.963 | 10.979 |
| 180 | +0.022 | 66.74 | 9.812 | 9.834 |
| 181 | +0.025 | 23.73 | -32.067 | -32.043 |

