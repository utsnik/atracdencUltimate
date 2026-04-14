# LP2 Score Workflow

Candidate mode: `quality-v10-gain-exp`; baseline mode: `quality-v10-native`.

| Sample | Candidate Full | Candidate HF | P10 | Median | Vocal Err | Side SNR | Side Ret (dB) | Dur Ratio | Hotspots | Worst Hotspot | Delta Full | Delta HF | Sony Dist | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| YOUtopia | 16.831 | 6.078 | 13.422 | 15.725 | 0.156518 | -3.073 | 0.118 | 1.000 | 8 | -7.885 | -0.433 | -0.539 | 1.249 | FAIL |
| Badlands | 21.121 | 8.921 | 17.440 | 21.332 | 0.088002 | -3.431 | 0.073 | 1.000 | 8 | -7.209 | -0.214 | -0.257 | 1.282 | FAIL |
| chirp_wait | 12.647 | 3.615 | 29.649 | 32.665 | 0.077857 | 0.000 | 0.000 | 1.012 | 8 | -0.009 | -0.024 | -0.017 | 1.712 | PASS |
| tmp_transient | 5.561 | 5.140 | 0.000 | 0.000 | n/a | 0.000 | 0.000 | 1.012 | 7 | -5.048 | -2.909 | -2.604 | 14.528 | FAIL |

## Stability Gate

FAIL

- YOUtopia: youtopia_full, youtopia_hf, youtopia_hotspot
- Badlands: badlands_hf, badlands_hotspot
- tmp_transient: transient_full, transient_hf, transient_hotspot

## Hotspots

### YOUtopia

Baseline full `17.264`, HF `6.617`; candidate full `16.831`, HF `6.078`; Sony full `16.486`, HF `7.278`.

| Frame | Delta vs Baseline | HF Energy (dB) | Baseline SNR | Candidate SNR |
|---|---:|---:|---:|---:|
| 407 | -7.885 | 74.57 | 13.735 | 5.850 |
| 369 | -7.324 | 68.52 | 14.282 | 6.958 |
| 366 | -5.010 | 68.95 | 14.020 | 9.010 |
| 368 | -3.392 | 69.37 | 12.740 | 9.348 |
| 1 | -2.782 | 67.17 | 15.789 | 13.008 |
| 610 | -2.568 | 65.80 | 13.418 | 10.849 |
| 594 | -2.329 | 69.77 | 18.849 | 16.520 |
| 581 | -1.935 | 71.86 | 18.089 | 16.154 |

### Badlands

Baseline full `21.334`, HF `9.178`; candidate full `21.121`, HF `8.921`; Sony full `20.381`, HF `9.969`.

| Frame | Delta vs Baseline | HF Energy (dB) | Baseline SNR | Candidate SNR |
|---|---:|---:|---:|---:|
| 31 | -7.209 | 54.85 | 22.036 | 14.828 |
| 221 | -3.637 | 53.16 | 21.728 | 18.091 |
| 32 | -3.453 | 62.48 | 23.732 | 20.279 |
| 52 | -2.603 | 51.16 | 13.033 | 10.430 |
| 309 | -2.185 | 62.55 | 25.040 | 22.856 |
| 267 | -1.620 | 62.74 | 25.059 | 23.439 |
| 637 | -1.478 | 56.76 | 23.177 | 21.699 |
| 479 | -1.449 | 63.24 | 25.719 | 24.270 |

### chirp_wait

Baseline full `12.671`, HF `3.632`; candidate full `12.647`, HF `3.615`; Sony full `13.969`, HF `4.702`.

| Frame | Delta vs Baseline | HF Energy (dB) | Baseline SNR | Candidate SNR |
|---|---:|---:|---:|---:|
| 201 | -0.009 | 88.80 | 31.484 | 31.475 |
| 202 | -0.002 | 88.98 | 30.079 | 30.077 |
| 180 | -0.001 | 83.87 | 29.209 | 29.208 |
| 0 | -0.000 | 33.76 | 31.974 | 31.974 |
| 200 | -0.000 | 88.60 | 33.886 | 33.886 |
| 214 | -0.000 | 90.68 | -0.000 | -0.000 |
| 179 | -0.000 | 83.61 | 30.916 | 30.916 |
| 203 | -0.000 | 89.18 | 6.264 | 6.264 |

### tmp_transient

Baseline full `8.470`, HF `7.744`; candidate full `5.561`, HF `5.140`; Sony full `17.230`, HF `13.795`.

| Frame | Delta vs Baseline | HF Energy (dB) | Baseline SNR | Candidate SNR |
|---|---:|---:|---:|---:|
| 180 | -5.048 | 66.74 | 9.812 | 4.764 |
| 81 | -5.019 | 66.74 | 9.643 | 4.624 |
| 146 | -3.287 | 66.74 | 12.035 | 8.747 |
| 47 | -3.266 | 66.74 | 10.963 | 7.697 |
| 116 | -2.450 | 66.74 | 10.941 | 8.491 |
| 21 | -1.836 | 66.74 | 11.645 | 9.808 |
| 181 | +12.946 | 23.73 | -32.067 | -19.122 |

