# LP2 YOUtopia Long Sweep (2026-04-11)

## Inputs
- Source: `youtopia_source.wav` (full song)
- Encoder under test: `build2/src/atracdenc.exe`
- Sony baseline tool: `ghidra/reverse/windows/at3tool.exe`

## Profile Sweep (Aligned SNR vs Sony)

| Profile | Ours SNR | Sony SNR | Delta |
|---|---:|---:|---:|
| `default` | 17.868 | 16.596 | +1.272 |
| `ml` | 18.095 | 16.596 | +1.499 |
| `bfu24` | 17.869 | 16.596 | +1.274 |
| `bfu28` | 16.394 | 16.596 | -0.202 |
| `bfu32` | 14.845 | 16.596 | -1.751 |
| `bfu32_ml` | 15.817 | 16.596 | -0.779 |
| `nogain` | 18.277 | 16.596 | +1.681 |
| `notonal` | 17.868 | 16.596 | +1.272 |

Notes:
- `notonal` matching `default` on this sample supports the latest RE hypothesis
  that LP2 may often run effectively without promoted tonals.
- `bfu32` underperforms badly on the full track; lower BFU policies are better.
- Adaptive policy updated after this sweep:
  - `tools/lp2_adaptive_encode.py` now defaults to `ml` for stable/non-transient
    content instead of forcing `bfu32_ml`.

## Decision Log Snapshot (Full Song, `--bfuidxconst 32 --ml-hints`)

From `youtopia_song.decision_test.log`:
- `rows=20846`
- `avg_target_bits=1491.20`
- `avg_num_bfu=32.00`
- `avg_tonal_blocks=0.00`
- `avg_ml_confidence=0.750`
- `avg_ml_hf_bias=-0.923`
- `avg_ml_gain_bias=1.000`

## Immediate Direction
1. Prioritize allocator/transient/stereo parity over tonal forcing.
2. Use real LP2 deep dumps (with non-constant complexity/attack/matrix fields)
   to tune per-frame policy.
3. Re-test full-song sweep once updated deep metrics are available.
