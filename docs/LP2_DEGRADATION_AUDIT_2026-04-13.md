# LP2 Degradation Audit

Window: `30.0` s, Sony lag `0`, baseline lag `-69`

Sony metrics: full `16.019`, HF `6.856`; baseline metrics: full `16.880`, HF `6.307`.

| File | Lag | Full SNR | HF SNR | Delta Full vs Baseline | Delta HF vs Baseline | Sony Distance |
|---|---:|---:|---:|---:|---:|---:|
| youtopia_song.quality_v10_frozen_v1.dec.wav | -69 | 17.667 | 5.166 | +0.786 | -1.141 | 2.360 |
| youtopia_song.stable_baseline_v10f_2026-04-12.dec.wav | -69 | 17.667 | 5.166 | +0.786 | -1.141 | 2.360 |
| youtopia_song.current_best_parity_v10.dec.wav | -69 | 16.880 | 6.307 | +0.000 | +0.000 | 1.021 |
| youtopia_song.quality_v10_v1.dec.wav | -69 | 9.199 | 4.172 | -7.681 | -2.135 | 7.330 |
| youtopia_song.default_current.dec.wav | -69 | 9.199 | 4.172 | -7.681 | -2.135 | 7.330 |
| youtopia_song.parity_v11.dec.wav | -69 | 8.784 | 4.154 | -8.097 | -2.153 | 7.724 |
| youtopia_song.parity_v11b.dec.wav | -69 | 8.784 | 4.154 | -8.097 | -2.153 | 7.724 |
| youtopia_song.parity_v11_safe.dec.wav | -69 | 8.784 | 4.154 | -8.097 | -2.153 | 7.724 |
| youtopia_song.parity_v12_hf_guard.dec.wav | -69 | 8.770 | 4.155 | -8.110 | -2.152 | 7.736 |
| youtopia_song.parity_v13_hf_tuned.dec.wav | -69 | 8.770 | 4.155 | -8.110 | -2.152 | 7.736 |
| youtopia_song.parity_v14_riskclass.dec.wav | -69 | 8.770 | 4.155 | -8.110 | -2.152 | 7.736 |
| youtopia_song.parity_v15_hf_tuned.dec.wav | -69 | 8.770 | 4.155 | -8.110 | -2.152 | 7.736 |
| youtopia_song.parity_v16_container_fix.dec.wav | -69 | 8.770 | 4.155 | -8.110 | -2.152 | 7.736 |

## Takeaways
- Yes, degradation is measurable: `v11`..`v16` show a large objective drop vs `v10` on this window.
- The drop is not subtle: about `-8.1 dB` full-band and about `-2.15 dB` HF proxy.
- `quality_v10_frozen` is closer to the current shipping-safe target but trades some HF sharpness for stronger full-band SNR.

