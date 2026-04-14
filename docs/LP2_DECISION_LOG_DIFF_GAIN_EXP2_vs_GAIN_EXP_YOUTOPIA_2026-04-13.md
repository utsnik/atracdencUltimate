# LP2 Decision Log Diff

- input: `YOUtopia_source.wav`
- native mode: `quality-v10-gain-exp`
- candidate mode: `quality-v10-gain-exp2`
- frame window: start `320`, max `160`

## Summary

- compared frames: 160
- top-level field changes: 160
- channel field changes: 170

## Sample Differences

- frame 320: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2
- frame 321: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2
- frame 322: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2; ch1.gain_first_level_cur: [4, 4, 4, 4] -> [3, 3, 4, 4]
- frame 323: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2; ch1.gain_first_level_cur: [4, 4, 4, 4] -> [4, 3, 4, 4]; ch1.gain_first_level_prev: [4, 4, 4, 4] -> [3, 3, 4, 4]
- frame 324: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2; ch0.gain_first_level_cur: [4, 3, 3, 3] -> [4, 3, 3, 4]; ch1.gain_first_level_prev: [4, 4, 4, 4] -> [4, 3, 4, 4]
- frame 325: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2; ch0.gain_first_level_prev: [4, 3, 3, 3] -> [4, 3, 3, 4]
- frame 326: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2
- frame 327: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2
- frame 328: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2
- frame 329: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2
- frame 330: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2; ch0.gain_first_level_cur: [4, 4, 4, 4] -> [4, 4, 4, 3]
- frame 331: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2; ch0.gain_first_level_prev: [4, 4, 4, 4] -> [4, 4, 4, 3]
- frame 332: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2; ch0.gain_first_level_cur: [4, 4, 4, 4] -> [4, 4, 4, 3]; ch1.gain_first_level_cur: [4, 4, 4, 4] -> [4, 4, 3, 4]
- frame 333: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2; ch0.gain_first_level_prev: [4, 4, 4, 4] -> [4, 4, 4, 3]; ch1.gain_first_level_cur: [4, 4, 4, 3] -> [4, 3, 4, 3]; ch1.gain_first_level_prev: [4, 4, 4, 4] -> [4, 4, 3, 4]
- frame 334: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2; ch1.gain_first_level_prev: [4, 4, 4, 3] -> [4, 3, 4, 3]
- frame 335: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2
- frame 336: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2; ch1.gain_first_level_cur: [4, 4, 4, 4] -> [4, 4, 4, 3]
- frame 337: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2; ch0.gain_first_level_cur: [4, 4, 4, 4] -> [4, 4, 4, 3]; ch1.gain_first_level_prev: [4, 4, 4, 4] -> [4, 4, 4, 3]
- frame 338: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2; ch0.gain_first_level_prev: [4, 4, 4, 4] -> [4, 4, 4, 3]
- frame 339: baseline_profile: quality-v10-gain-exp -> quality-v10-gain-exp2; ch0.gain_first_level_cur: [4, 4, 4, 4] -> [4, 3, 4, 4]
