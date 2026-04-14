# LP2 Scorecard

## Per Sample

| Sample | Profile | Ours SNR | Sony SNR | Delta |
|---|---:|---:|---:|---:|
| tmp_sine.wav | default | 34.828 | 56.796 | -21.968 |
| tmp_sine.wav | ml | 34.829 | 56.796 | -21.968 |
| tmp_sine.wav | bfu32_ml | 34.810 | 56.796 | -21.986 |
| chirp_wait.wav | default | 17.220 | 13.969 | 3.250 |
| chirp_wait.wav | ml | 18.424 | 13.969 | 4.454 |
| chirp_wait.wav | bfu32_ml | 31.201 | 13.969 | 17.232 |
| tmp_multitone.wav | default | 30.933 | 40.823 | -9.890 |
| tmp_multitone.wav | ml | 30.950 | 40.823 | -9.873 |
| tmp_multitone.wav | bfu32_ml | 31.827 | 40.823 | -8.997 |
| tmp_transient.wav | default | 13.261 | 17.230 | -3.969 |
| tmp_transient.wav | ml | 12.259 | 17.230 | -4.971 |
| tmp_transient.wav | bfu32_ml | 2.831 | 17.230 | -14.399 |
| YOUtopia.wav | default | 20.195 | 31.925 | -11.729 |
| YOUtopia.wav | ml | 23.859 | 31.925 | -8.066 |
| YOUtopia.wav | bfu32_ml | 30.409 | 31.925 | -1.515 |

## Averages

| Mode | Avg Delta vs Sony |
|---|---:|
| default | -8.861 |
| ml | -8.085 |
| bfu32_ml | -5.933 |
| adaptive_policy | -7.884 |

## Notes

- `adaptive_policy` currently selects `default` for transient samples and `ml` otherwise.
- This is an interim policy pending true dynamic RE frame dumps.
