# LP2 Parity RE Report

This runtime-first LP2 parity pass uses the Sony LP2 extractor as the primary truth source, then narrows remaining semantics with targeted Ghidra/decompilation follow-up.

## Corpus

- `YOUtopia`: `YOUtopia_source.wav`, clipped to `30.0` seconds.
- `Badlands`: `Badlands.wav`, clipped to `30.0` seconds.
- `chirp_20_20k_5s`: `chirp_20_20k_5s.wav`, clipped to `5.0` seconds.
- `chirp_wait`: `chirp_wait.wav`, clipped to `5.0` seconds (supplemental score-alignment control).
- `tmp_transient`: `tmp_transient.wav`, clipped to `5.0` seconds.

## Dynamic Field Validation

| Sample | Rows | Frames | Complexity UQ | Attack UQ | Matrix UQ | Weight UQ | GainPts UQ | Tonals UQ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| YOUtopia | 2592 | 1293 | 323 | 919 | 1 | 2290 | 115 | 1 |
| Badlands | 2592 | 1293 | 442 | 775 | 1 | 2168 | 174 | 1 |
| chirp_20_20k_5s | 438 | 217 | 167 | 31 | 2 | 46 | 10 | 17 |
| chirp_wait | 438 | 217 | 151 | 133 | 1 | 140 | 12 | 1 |
| tmp_transient | 438 | 217 | 13 | 7 | 1 | 23 | 3 | 1 |

Conclusion: the extracted LP2 fields vary meaningfully across the corpus, so this RE pass is now working with real dynamic data rather than placeholders. Supplemental note: chirp_20_20k_5s shows live matrix-mode and tonal variation, which confirms the extractor is seeing real LP2 JS/tonal path changes even when the music samples stay on a fixed matrix index.

## Score Alignment

| Sample | Current Full | Current HF | Worst Hotspot | Sony Dist | Hotspot Bucket |
|---|---:|---:|---:|---:|---|
| YOUtopia | 18.489 | 6.720 | -0.001 | 1.007 | stereo-driven, allocator-driven |
| Badlands | 21.465 | 9.071 | -8.029 | 1.299 | allocator-driven |
| chirp_wait | 12.647 | 3.615 | -32.449 | 1.712 | allocator-driven |
| tmp_transient | 8.470 | 7.744 | -8.294 | 10.646 | allocator-driven |

### YOUtopia

Hotspot bucket: **stereo-driven, allocator-driven**. Current `quality-v10-native` metrics are full `18.489` dB and HF `6.720` dB.

| Metric | Global | Hotspots |
|---|---:|---:|
| Complexity | 60.614 | 82.188 |
| Actual Bits Used | 1392.719 | 1389.750 |
| Residual Bits | 1332.104 | 1307.562 |
| Attack Ratio | 1.588 | 1.708 |
| Transient Rate | 0.097 | 0.125 |
| Matrix Change Rate | 0.000 | 0.000 |
| Weight Delta | 2.971 | 4.938 |
| Gain Delta | 1.110 | 1.438 |
| Gain Nonzero Bands | 3.994 | 4.000 |
| Num Tonals | 0.000 | 0.000 |

Driver notes:
- matrix/weight movement 0.00/4.94.
- complexity/actual bits 82.2/1389.8.

| Hot Frame | Delta vs Baseline | Candidate SNR | Sony Complexity | Sony Attack | Sony Matrix | Sony Weight Sum | Sony Gain Sum | Sony Tonals |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| 1290 | -0.001 | 21.099 | 29.5 | 1.884 | 3 | 200.5 | 18.0 | 0.0 |
| 1053 | +0.000 | 11.289 | 42.5 | 1.255 | 3 | 196.5 | 16.5 | 0.0 |
| 959 | +0.000 | 17.213 | -11.5 | 1.321 | 3 | 202.0 | 17.0 | 0.0 |
| 1075 | +0.000 | 14.751 | 127.5 | 1.733 | 3 | 199.5 | 18.5 | 0.0 |
| 1162 | +0.000 | 12.881 | 115.5 | 1.000 | 3 | 202.0 | 20.0 | 0.0 |
| 531 | +0.000 | 15.898 | 193.0 | 1.779 | 3 | 196.5 | 19.0 | 0.0 |
| 572 | +0.000 | 12.247 | 104.5 | 3.167 | 3 | 198.0 | 16.0 | 0.0 |
| 589 | +0.000 | 15.589 | 56.5 | 1.521 | 3 | 192.5 | 17.0 | 0.0 |

### Badlands

Hotspot bucket: **allocator-driven**. Current `quality-v10-native` metrics are full `21.465` dB and HF `9.071` dB.

| Metric | Global | Hotspots |
|---|---:|---:|
| Complexity | 16.179 | -74.812 |
| Actual Bits Used | 1395.722 | 1396.812 |
| Residual Bits | 1379.544 | 1471.625 |
| Attack Ratio | 1.457 | 1.254 |
| Transient Rate | 0.052 | 0.000 |
| Matrix Change Rate | 0.000 | 0.000 |
| Weight Delta | 4.083 | 1.750 |
| Gain Delta | 1.203 | 1.250 |
| Gain Nonzero Bands | 3.994 | 4.000 |
| Num Tonals | 0.000 | 0.000 |

Driver notes:
- no strong gain or stereo signature; remaining gap clusters in LP2 allocation pressure.

| Hot Frame | Delta vs Baseline | Candidate SNR | Sony Complexity | Sony Attack | Sony Matrix | Sony Weight Sum | Sony Gain Sum | Sony Tonals |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| 52 | -8.029 | 13.033 | -74.0 | 1.351 | 3 | 171.0 | 23.0 | 0.0 |
| 308 | -4.679 | 19.630 | -78.0 | 1.189 | 3 | 169.5 | 22.5 | 0.0 |
| 696 | -4.628 | 18.491 | -117.0 | 1.273 | 3 | 186.5 | 20.5 | 0.0 |
| 691 | -4.220 | 17.920 | -37.5 | 1.630 | 3 | 196.0 | 18.5 | 0.0 |
| 20 | -4.069 | 25.979 | -102.5 | 1.000 | 3 | 177.0 | 22.0 | 0.0 |
| 53 | -4.017 | 22.638 | -108.5 | 1.000 | 3 | 168.5 | 21.5 | 0.0 |
| 538 | -3.978 | 19.994 | -65.5 | 1.196 | 3 | 177.0 | 21.5 | 0.0 |
| 731 | -3.975 | 18.667 | -15.5 | 1.393 | 3 | 196.5 | 23.0 | 0.0 |

### chirp_wait

Hotspot bucket: **allocator-driven**. Current `quality-v10-native` metrics are full `12.647` dB and HF `3.615` dB.

| Metric | Global | Hotspots |
|---|---:|---:|
| Complexity | 211.510 | 239.000 |
| Actual Bits Used | 584.160 | 880.000 |
| Residual Bits | 372.650 | 641.000 |
| Attack Ratio | 1.423 | 1.000 |
| Transient Rate | 0.253 | 0.000 |
| Matrix Change Rate | 0.000 | 0.000 |
| Weight Delta | 6.551 | 0.250 |
| Gain Delta | 1.651 | 0.000 |
| Gain Nonzero Bands | 2.161 | 0.000 |
| Num Tonals | 0.000 | 0.000 |

Driver notes:
- complexity/actual bits 239.0/880.0.

| Hot Frame | Delta vs Baseline | Candidate SNR | Sony Complexity | Sony Attack | Sony Matrix | Sony Weight Sum | Sony Gain Sum | Sony Tonals |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| 207 | -32.449 | 0.000 | 169.0 | 1.000 | 3 | 0.0 | 0.0 | 0.0 |
| 206 | -32.249 | 0.000 | 115.0 | 1.000 | 3 | 0.0 | 0.0 | 0.0 |
| 210 | -28.036 | 0.000 | 224.0 | 1.000 | 3 | 0.0 | 0.0 | 0.0 |
| 208 | -27.049 | 0.000 | 305.0 | 1.000 | 3 | 0.0 | 0.0 | 0.0 |
| 203 | -26.481 | 6.264 | -139.0 | 1.000 | 3 | 0.0 | 0.0 | 0.0 |
| 209 | -25.371 | 0.000 | 369.0 | 1.000 | 3 | 0.0 | 0.0 | 0.0 |
| 205 | -4.205 | 0.000 | 40.0 | 1.000 | 3 | 0.0 | 0.0 | 0.0 |
| 213 | -3.330 | -0.000 | 829.0 | 1.000 | 3 | 0.0 | 0.0 | 0.0 |

### tmp_transient

Hotspot bucket: **allocator-driven**. Current `quality-v10-native` metrics are full `8.470` dB and HF `7.744` dB.

| Metric | Global | Hotspots |
|---|---:|---:|
| Complexity | -24.346 | 0.000 |
| Actual Bits Used | 72.092 | 0.000 |
| Residual Bits | 96.438 | 0.000 |
| Attack Ratio | 1.175 | 1.000 |
| Transient Rate | 0.023 | 0.000 |
| Matrix Change Rate | 0.000 | 0.000 |
| Weight Delta | 16.565 | 23.000 |
| Gain Delta | 0.512 | 0.429 |
| Gain Nonzero Bands | 2.627 | 2.143 |
| Num Tonals | 0.000 | 0.000 |

Driver notes:
- complexity/actual bits 0.0/0.0.

| Hot Frame | Delta vs Baseline | Candidate SNR | Sony Complexity | Sony Attack | Sony Matrix | Sony Weight Sum | Sony Gain Sum | Sony Tonals |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| 181 | -8.294 | -32.067 | 0.0 | 1.000 | 3 | 27.0 | 3.0 | 0.0 |
| 47 | -3.721 | 10.963 | 0.0 | 1.000 | 3 | 0.0 | 0.0 | 0.0 |
| 116 | -3.257 | 10.941 | 0.0 | 1.000 | 3 | 60.0 | 3.0 | 0.0 |
| 81 | -3.043 | 9.643 | 0.0 | 1.000 | 3 | 48.0 | 3.0 | 0.0 |
| 180 | -3.003 | 9.812 | 0.0 | 1.000 | 3 | 50.0 | 3.0 | 0.0 |
| 21 | -2.964 | 11.645 | 0.0 | 1.000 | 3 | 0.0 | 0.0 | 0.0 |
| 146 | -2.634 | 12.035 | 0.0 | 1.000 | 3 | 60.0 | 3.0 | 0.0 |

## Parity Questions

1. Is Sony protecting HF by allocator feedback or by stereo weighting on the bad frames? `chirp_wait` hotspots skew allocator-heavy with hotspot complexity `239.0` vs global `211.5` `YOUtopia` hotspots move with matrix/weight changes `0.00` / `4.94` `Badlands` shows the same stereo-weight motion with hotspot weight delta `1.75`.
2. Are transient-heavy regressions driven by gain-point emission or by missing bit reallocation around attacks? `tmp_transient` hotspot attack ratio is `1.00` vs global `1.18` with gain nonzero bands `2.14` `chirp_wait` still shows hot-frame transients without matching allocator recovery (actual bits `880.0` vs global `584.2`).
3. Are the worst vocal/HF regressions correlated with JS matrix/weight changes? `YOUtopia` hotspots move with matrix/weight changes (0.00 / 4.94) `Badlands` hotspots also show stereo movement and elevated gain deltas (1.25).

## Targeted Ghidra Follow-Up

- `FUN_0043f270` (`int __cdecl FUN_0043f270(int param_1, int param_2, int param_3, uint param_4, int param_5, int param_6, int param_7, int param_8, int param_9)`): best allocator-feedback target. In `FUN_0043d1f0` its return is stored in `local_a848` and subtracted from the remaining LP2 budget before the later quantizer loop.

```c
0xd;
  }
  else {
    local_a844 = (int *)0x1;
    if ((int)uVar15 < 0xa0) {
      if (0x5f < (int)uVar15) {
        *param_3 = 0x1e;
        param_3[1] = 3;
      }
    }
    else {
      *param_3 = 0x20;
      param_3[1] = 4;
    }
    cVar5 = FUN_0043ce60((int)param_3);
    iVar14 = *param_3;
    iVar7 = FUN_0043ce80((int)param_3);
    local_a85c = (((iVar11 + iVar14 * -3) - CONCAT31(extraout_var,cVar5)) - iVar7) + -0xd;
    local_a848 = (float)FUN_0043f270(local_a85c,(int)local_a834,(0x4b0 < iVar11) + 1,uVar15,
                                     param_3[1],0x100,param_2,(int)local_4800,(int)param_3);
    if (local_a848 == -NAN) {
      return -0x8000;
    }
    local_a85c = local_a85c - (int)local_a848;
  }
  iVar11 = *param_3;
  iVar14 = param_3[1];
  local_a838 = iVar14;
  iVar7 = FUN_0043cda0(iVar11);
  local_a840 = (float)((int)(iVar7 + (iVar7 >> 0x
```

- `FUN_0043ec60` (`undefined __cdecl FUN_0043ec60(undefined4 param_1, undefined4 * param_2, undefined4 * param_3, undefined4 * param_4)`): segment-energy hook point. `FUN_0043d1f0` calls it before LP2 allocation, so runtime `attack_ratio` is useful but still a derived proxy until the output arrays are fully mapped.

```c
undefined1 local_4800 [18428];
  undefined4 uStack_4;
  
  uStack_4 = 0x43d1fa;
  local_a830 = param_3[0x187d];
  piVar13 = local_a000;
  for (iVar11 = 0x400; iVar11 != 0; iVar11 = iVar11 + -1) {
    *piVar13 = 0;
    piVar13 = piVar13 + 1;
  }
  iVar11 = param_3[0x1872];
  local_a828 = param_3 + 0x145f;
  uVar15 = 0;
  local_a820 = 7;
  local_a844 = (int *)0x0;
  local_a848 = 0.0;
  local_a82c = 0.0;
  local_a83c = iVar11;
  FUN_0043ec60((int)(iVar11 + (iVar11 >> 0x1f & 7U)) >> 3,local_a81c,local_a518,&local_a820);
  FUN_0043eb30(param_2,(int)local_4800,0x100);
  FUN_0043eb30(param_1,(int)local_9000,0x100);
  uVar12 = 0;
  iVar14 = 0;
  iVar7 = 0;
  do {
    if (*(int *)((int)local_8ffc + iVar14) < *(int *)((int)local_8ffc + iVar7)) {
      iVar14 = iVar7;
      uVar15 = uVar12;
    }
    iVar7 = iVar7 + 0x48;
    uVar12 = uVar12 + 1;
  } while (iVar7 <
```

- `FUN_0043d080` (`int __cdecl FUN_0043d080(int * param_1)`): next gain-sideinfo target. The runtime `gain_points_per_band` values already correlate with hotspot frames, but Ghidra still needs to confirm whether they are absolute levels or differential packed indices.
- `FUN_0043ceb0` (`int __cdecl FUN_0043ceb0(int param_1)`): tonal state exists, but the current LP2 corpus does not show tonal counts dominating the bad frames, so tonal work stays below stereo/gain/allocator parity.

- Context write-back that still needs semantic confirmation:

```c
dd41:
  if (iVar11 == 0) {
    local_a798[0] = 0.0;
    *param_3 = 1;
    param_3[1] = 1;
    param_3[4] = 0;
    param_3[0x44] = 0;
    iVar11 = FUN_0043ce00(param_3);
    return iVar11;
  }
  iVar14 = (&iStack_a79c)[iVar11];
  piVar13 = &iStack_a79c + iVar11;
  for (iVar7 = iVar11; (iVar14 == 0 && (1 < iVar7)); iVar7 = iVar7 + -1) {
    iVar14 = piVar13[-1];
    piVar13 = piVar13 + -1;
  }
  iVar14 = 0;
  if (0 < iVar7) {
    piVar13 = param_3 + 0x143f;
    do {
      pfVar16 = local_a798 + iVar14;
      iVar14 = iVar14 + 1;
      piVar13[-0x20] = (int)*pfVar16;
      *piVar13 = aiStack_a284[iVar14];
      piVar13 = piVar13 + 1;
    } while (iVar14 < iVar7);
  }
  param_3[1] = local_a838;
  iVar14 = 0;
  local_a85c = local_a83c - (local_a85c + ((iVar11 - iVar7) * 3 - iVar8));
  *param_3 = iVar7;
  param_3[2] = 1;
  param_3[3] = 0;
  if (0 < iVar7) {
```

Outstanding semantic asks:
- Confirm whether `complexity_score` is the true Sony allocator control value or only a cost-delta proxy around `FUN_0043e8c0`/`FUN_0043f270`.
- Confirm whether `gain_points_per_band` should be compared as absolute levels or decoded from differential packing before parity tuning.
- Confirm exactly how `param_3[1]` plus the `0x143f` weight writes map to LP2 JS matrix/weight side-info on music hotspots.

## Outputs

- `YOUtopia` raw Sony CSV: `C:\Users\Igland\Antigravity\Ghidra\atracdenc_solo_20260411\reverse\windows\lp2_parity_re\raw\deep_metrics_YOUtopia.csv`
- `YOUtopia` normalized frame CSV: `C:\Users\Igland\Antigravity\Ghidra\atracdenc_solo_20260411\reverse\windows\lp2_parity_re\normalized\YOUtopia_normalized.csv`
- `Badlands` raw Sony CSV: `C:\Users\Igland\Antigravity\Ghidra\atracdenc_solo_20260411\reverse\windows\lp2_parity_re\raw\deep_metrics_Badlands.csv`
- `Badlands` normalized frame CSV: `C:\Users\Igland\Antigravity\Ghidra\atracdenc_solo_20260411\reverse\windows\lp2_parity_re\normalized\Badlands_normalized.csv`
- `chirp_20_20k_5s` raw Sony CSV: `C:\Users\Igland\Antigravity\Ghidra\atracdenc_solo_20260411\reverse\windows\lp2_parity_re\raw\deep_metrics_chirp_20_20k_5s.csv`
- `chirp_20_20k_5s` normalized frame CSV: `C:\Users\Igland\Antigravity\Ghidra\atracdenc_solo_20260411\reverse\windows\lp2_parity_re\normalized\chirp_20_20k_5s_normalized.csv`
- `chirp_wait` raw Sony CSV: `C:\Users\Igland\Antigravity\Ghidra\atracdenc_solo_20260411\reverse\windows\lp2_parity_re\raw\deep_metrics_chirp_wait.csv`
- `chirp_wait` normalized frame CSV: `C:\Users\Igland\Antigravity\Ghidra\atracdenc_solo_20260411\reverse\windows\lp2_parity_re\normalized\chirp_wait_normalized.csv`
- `tmp_transient` raw Sony CSV: `C:\Users\Igland\Antigravity\Ghidra\atracdenc_solo_20260411\reverse\windows\lp2_parity_re\raw\deep_metrics_tmp_transient.csv`
- `tmp_transient` normalized frame CSV: `C:\Users\Igland\Antigravity\Ghidra\atracdenc_solo_20260411\reverse\windows\lp2_parity_re\normalized\tmp_transient_normalized.csv`

## Recommendation

The next parity implementation work should stay ordered as planned:
1. Stereo parity on music hotspot frames (`YOUtopia`, `Badlands`).
2. Gain/transient parity on `tmp_transient` and `chirp_wait`.
3. Allocator feedback parity around `FUN_0043f270` once the remaining semantics are pinned down.
4. Tonal work only if later runtime passes show it matters more on real LP2 material.
