# LP2 Score Workflow

Candidate mode: `quality-v10`; baseline mode: `quality-v10-native`.

| Sample | Candidate Full | Candidate HF | P10 | Median | Vocal Err | Side SNR | Side Ret (dB) | Dur Ratio | Hotspots | Worst Hotspot | Delta Full | Delta HF | Sony Dist | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| YOUtopia | 17.604 | 4.954 | 14.566 | 16.868 | 0.109488 | -3.023 | 0.016 | 1.000 | 8 | -5.174 | +0.340 | -1.662 | 2.579 | FAIL |
| Badlands | 22.864 | 8.991 | 19.368 | 23.063 | 0.068376 | -3.419 | 0.040 | 1.000 | 8 | -3.434 | +1.529 | -0.187 | 2.668 | FAIL |
| chirp_wait | 17.224 | 8.085 | 30.262 | 32.665 | 0.044875 | 0.000 | 0.000 | 1.012 | 8 | -6.441 | +4.553 | +4.453 | 4.694 | FAIL |
| tmp_transient | -5.207 | -5.314 | -0.400 | 0.000 | n/a | 0.000 | 0.000 | 1.012 | 7 | -16.923 | -13.677 | -13.058 | 29.471 | FAIL |

## Stability Gate

FAIL

- YOUtopia: youtopia_hf, youtopia_hotspot
- Badlands: badlands_hf, badlands_hotspot
- chirp_wait: chirp_hotspot
- tmp_transient: transient_full, transient_hf, transient_hotspot

## Hotspots

### YOUtopia

Baseline full `17.264`, HF `6.617`; candidate full `17.604`, HF `4.954`; Sony full `16.486`, HF `7.278`.

| Frame | Delta vs Baseline | HF Energy (dB) | Baseline SNR | Candidate SNR |
|---|---:|---:|---:|---:|
| 407 | -5.174 | 74.57 | 13.735 | 8.561 |
| 611 | -3.797 | 73.81 | 20.512 | 16.716 |
| 572 | -3.371 | 75.11 | 12.247 | 8.875 |
| 573 | -3.224 | 74.73 | 12.807 | 9.582 |
| 571 | -3.050 | 74.45 | 12.527 | 9.477 |
| 528 | -2.897 | 74.24 | 13.267 | 10.369 |
| 530 | -2.791 | 74.40 | 12.375 | 9.584 |
| 529 | -2.678 | 74.32 | 12.001 | 9.323 |

### Badlands

Baseline full `21.334`, HF `9.178`; candidate full `22.864`, HF `8.991`; Sony full `20.381`, HF `9.969`.

| Frame | Delta vs Baseline | HF Energy (dB) | Baseline SNR | Candidate SNR |
|---|---:|---:|---:|---:|
| 221 | -3.434 | 53.16 | 21.728 | 18.294 |
| 31 | -2.426 | 54.85 | 22.036 | 19.610 |
| 32 | -1.000 | 62.48 | 23.732 | 22.732 |
| 390 | -0.926 | 44.84 | 27.055 | 26.129 |
| 222 | -0.900 | 54.13 | 19.158 | 18.257 |
| 273 | -0.548 | 55.57 | 23.325 | 22.777 |
| 367 | -0.527 | 54.97 | 24.290 | 23.763 |
| 156 | -0.522 | 55.50 | 24.202 | 23.680 |

### chirp_wait

Baseline full `12.671`, HF `3.632`; candidate full `17.224`, HF `8.085`; Sony full `13.969`, HF `4.702`.

| Frame | Delta vs Baseline | HF Energy (dB) | Baseline SNR | Candidate SNR |
|---|---:|---:|---:|---:|
| 174 | -6.441 | 82.31 | 32.157 | 25.716 |
| 175 | -1.566 | 82.56 | 33.350 | 31.784 |
| 179 | -0.009 | 83.61 | 30.916 | 30.907 |
| 201 | -0.009 | 88.80 | 31.484 | 31.475 |
| 180 | -0.002 | 83.87 | 29.209 | 29.207 |
| 212 | -0.001 | 90.50 | 0.000 | -0.001 |
| 173 | -0.001 | 82.04 | 31.994 | 31.993 |
| 200 | -0.000 | 88.60 | 33.886 | 33.886 |

### tmp_transient

Baseline full `8.470`, HF `7.744`; candidate full `-5.207`, HF `-5.314`; Sony full `17.230`, HF `13.795`.

| Frame | Delta vs Baseline | HF Energy (dB) | Baseline SNR | Candidate SNR |
|---|---:|---:|---:|---:|
| 146 | -16.923 | 66.74 | 12.035 | -4.888 |
| 47 | -14.420 | 66.74 | 10.963 | -3.457 |
| 116 | -14.218 | 66.74 | 10.941 | -3.276 |
| 21 | -12.377 | 66.74 | 11.645 | -0.733 |
| 180 | -10.212 | 66.74 | 9.812 | -0.400 |
| 81 | -5.943 | 66.74 | 9.643 | 3.700 |
| 181 | +26.028 | 23.73 | -32.067 | -6.039 |

