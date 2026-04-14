# Best ATRAC3+ Encoder Configs\n
## 2026-04-07 ? Best So Far (Post Scale-Fix + WL Energy)
Config:
- Encoder: atracdenc (build2)
- Env: ATRACDENC_WL_ENERGY=1
- ghadbg mask: 3 (equivalent 7 also good)
Metrics (Aligned SNR, ghadbg=3):
- sine_1k_5s: 30.6907 dB
- chirp_20_20k_5s: 6.9938 dB
- multitone_5s: 7.3109 dB
- transient_5s: 23.7665 dB
Avg aligned SNR: 17.1905 dB
Notes:
- Scale table now uses raw values (no normalization)
- Scaler clamps to max ScaleTable entry (no MAX_SCALE=1.0)
## 2026-04-07 ? Best So Far (WL Energy + Trim)
Config:
- Env: ATRACDENC_WL_ENERGY=1
- Env: ATRACDENC_WL_TRIM=1
- Env: ATRACDENC_WL_TRIM_TARGET_FRAC=0.95
- ghadbg mask: 3 (equivalent 7 also good)
Metrics (Aligned SNR, ghadbg=3):
- sine_1k_5s: 30.6907 dB
- chirp_20_20k_5s: 6.9938 dB
- multitone_5s: 7.3109 dB
- transient_5s: 23.7786 dB
Avg aligned SNR: 17.1935 dB
Notes:
- This is a tiny improvement over WL_ENERGY alone.
## 2026-04-07 ? Best So Far (WL Energy + Trim + Low-Band Boost)
Config:
- Env: ATRACDENC_WL_ENERGY=1
- Env: ATRACDENC_WL_TRIM=1
- Env: ATRACDENC_WL_TRIM_TARGET_FRAC=0.95
- Env: ATRACDENC_WL_BOOST_LOW=1
- Env: ATRACDENC_WL_BOOST_LOW_N=6
- Env: ATRACDENC_WL_BOOST_LOW_DELTA=1
- ghadbg mask: 3 (equivalent 7 also good)
Metrics (Aligned SNR, ghadbg=3):
- sine_1k_5s: 30.6908 dB
- chirp_20_20k_5s: 6.9938 dB
- multitone_5s: 7.3109 dB
- transient_5s: 23.7785 dB
Avg aligned SNR: 17.1935 dB
