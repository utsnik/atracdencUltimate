# LP2 Gate Results (2026-04-12)

## Setup
- Input: `YOUtopia_source.wav` (10 s clip)
- Current encoder: `build_work/src/atracdenc.exe`
- Frozen baseline: `build2/src/atracdenc.exe` via `quality-v10-frozen`
- Sony reference: `at3tool -e -br 132`
- Tool: `tools/lp2_parity_gate.py`

## Snapshot

| Candidate mode | Candidate full | Candidate HF | Frozen-v10 full | Frozen-v10 HF | Sony full | Sony HF | Delta full vs frozen-v10 | Delta HF vs frozen-v10 | Pass |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `default` | 7.987 | 3.949 | 15.369 | 5.173 | 13.480 | 6.365 | -7.382 | -1.224 | 0 |
| `ml` | 8.052 | 3.668 | 15.369 | 5.173 | 13.480 | 6.365 | -7.317 | -1.505 | 0 |
| `quality-v10` | 7.987 | 3.949 | 15.369 | 5.173 | 13.480 | 6.365 | -7.382 | -1.224 | 0 |

## Interpretation
- Current in-source candidate modes are still far below `quality-v10-frozen` on this clip.
- Keep `quality-v10-frozen` as the listening baseline while parity tuning continues.

## Full-Track Sanity (YOUtopia)
- `youtopia_song.stable_baseline_v10f_2026-04-12.at3.wav` decodes successfully in `at3tool`
  (`10451` frames).
- Quick aligned metrics vs source:
  - full-band SNR: `17.868 dB`
  - HF proxy SNR: `4.497 dB`
  - lag: `-69`
