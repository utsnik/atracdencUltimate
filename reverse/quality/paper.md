# ATRAC3+ Quality Experiments\n
## 2026-04-07 ? Psycho Alloc Sweep (target_frac=0.85, lambda=[0.001,0.2])
Result: No improvement vs prior best.
Best aligned SNR (ghadbg=2/6): sine=24.6716 dB, chirp=1.0076 dB, multitone=1.2777 dB, transient=16.8431 dB.
Notes: Same table as previous run; deltas unchanged.

## 2026-04-07 ? MDCT Gain Sweep (gain=0.7, ghadbg=1 focus)
Avg aligned SNR (ghadbg=1) = -9.77222716808319


## 2026-04-07 ? MDCT Gain Sweep (gain=1, ghadbg=1 focus)
Avg aligned SNR (ghadbg=1) = -9.77222716808319


## 2026-04-07 ? MDCT Gain Sweep (gain=1.3, ghadbg=1 focus)
Avg aligned SNR (ghadbg=1) = -9.77222716808319

## 2026-04-07 ? Scale Table Fix (raw scales + dynamic maxScale)
Change: at3p scale table no longer normalized; scaler now clamps to max ScaleTable value (no MAX_SCALE=1.0).
Result: Improvements observed. Best aligned SNR now at ghadbg=3/7: sine=30.6915 dB, chirp=3.6417 dB, multitone=7.2808 dB, transient=23.7535 dB. Avg aligned SNR=16.3419 dB.
Notes: prior best aligned SNR (ghadbg=2/6) avg ~10.95 dB; pass-input clipping errors disappeared.
## 2026-04-07 ? Psycho Alloc After Scale Fix (target_frac=0.85, lambda=[0.001,0.2])
Result: No improvement; some regressions vs baseline after scale fix.
Best aligned SNR in this run (ghadbg=3/7): sine=21.6037 dB, chirp=5.6461 dB, multitone=7.0137 dB, transient=23.6438 dB.
## 2026-04-07 ? Energy-Based Wordlen Heuristic (ATRACDENC_WL_ENERGY=1)
Result: Slight improvement vs scale-fix baseline.
Best aligned SNR (ghadbg=3/7): sine=30.6907 dB, chirp=6.9938 dB, multitone=7.3109 dB, transient=23.7665 dB. Avg aligned SNR=17.1905 dB.
## 2026-04-07 ? Psycho Alloc (target_frac=0.95, lambda=[0.0005,0.2])
Result: Regression. Avg aligned SNR (ghadbg=3/7) = 14.5346 dB.
## 2026-04-07 ? WL Energy Min/Max Sweep
- min=2 max=7: avg aligned SNR (ghadbg=3/7) = 17.1909 dB (no change)
- min=1 max=6: avg aligned SNR (ghadbg=3/7) = 17.1612 dB (slight regression)
## 2026-04-07 ? Bit-Budgeted WL Alloc (ATRACDENC_WL_BUDGET)
- target_frac=0.90, weight=none: avg aligned SNR (ghadbg=3/7) = 14.5250 dB (regression)
- target_frac=0.90, weight=energy: avg aligned SNR (ghadbg=3/7) = 14.5623 dB (regression)
## 2026-04-07 ? WL Energy + Trim Budget (target_frac=0.90)
Result: Tiny improvement.
Avg aligned SNR (ghadbg=3/7) = 17.1934 dB (vs 17.1905 baseline WL_ENERGY).
## 2026-04-07 ? WL Energy + Trim Budget Sweep
- target_frac=0.85: avg aligned SNR = 17.1934 dB
- target_frac=0.95: avg aligned SNR = 17.1935 dB (best so far)
## 2026-04-07 ? WL Energy + Trim + Low-Band Boost
Config: WL_ENERGY=1, WL_TRIM=1 (target_frac=0.95), WL_BOOST_LOW N=6 delta=1
Result: Tiny improvement.
Best aligned SNR (ghadbg=3): sine=30.6908 dB, chirp=6.9938 dB, multitone=7.3109 dB, transient=23.7785 dB. Avg aligned SNR=17.1935 dB.
2026-04-07 09:52:05 | WL_ENERGY+TRIM+LOWBOOST N=4 D=1 | 
2026-04-07 09:52:05 | WL_ENERGY+TRIM+LOWBOOST N=4 D=2 | 
2026-04-07 09:52:05 | WL_ENERGY+TRIM+LOWBOOST N=6 D=1 | 
2026-04-07 09:52:05 | WL_ENERGY+TRIM+LOWBOOST N=6 D=2 | 
2026-04-07 09:52:05 | WL_ENERGY+TRIM+LOWBOOST N=8 D=1 | 
2026-04-07 09:52:05 | WL_ENERGY+TRIM+LOWBOOST N=8 D=2 | 
