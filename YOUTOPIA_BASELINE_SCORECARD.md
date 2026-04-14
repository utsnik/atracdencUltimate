# YOUtopia LP2 Scorecard

Date: 2026-04-11

## Encodes

- Sony reference:
  - Command: `at3tool.exe -e -br 132 YOUtopia.wav youtopia_at3tool_132.at3`
  - Output: `youtopia_at3tool_132.at3`
- atracdenc candidate:
  - Command: `build2\src\atracdenc.exe -e atrac3 -i YOUtopia.wav -o youtopia_atracdenc_132.at3.wav --bitrate 132`
  - Output: `youtopia_atracdenc_132.at3.wav`

## Decode Paths Used For Scoring

- `youtopia_at3tool_132.at3` decoded by:
  - `at3tool.exe` -> `youtopia_at3tool_132_dec_by_at3tool.wav`
  - FFmpeg -> `youtopia_at3tool_132_dec.wav`
- `youtopia_atracdenc_132.at3.wav` decoded by:
  - `at3tool.exe` -> `youtopia_atracdenc_132_dec_by_at3tool.wav`
  - FFmpeg -> `youtopia_atracdenc_132_dec.wav`

## Metrics (vs original `YOUtopia.wav`)

### Sony (native decoder path)

- File: `youtopia_at3tool_132_dec_by_at3tool.wav`
- Lag: `0`
- SNR: `16.463 dB`
- Segmental SNR: `17.667 dB`
- HF noise ratio: `-6.527 dB`

### atracdenc (FFmpeg decoder path)

- File: `youtopia_atracdenc_132_dec.wav`
- Lag: `-1458`
- SNR: `-2.274 dB`
- Segmental SNR: `-2.399 dB`
- HF noise ratio: `2.312 dB`

### atracdenc (native at3tool decoder path)

- File: `youtopia_atracdenc_132_dec_by_at3tool.wav`
- Lag: `-69`
- SNR: `17.794 dB`
- Segmental SNR: `19.656 dB`
- HF noise ratio: `-4.402 dB`

### Sony (FFmpeg decoder path, for decoder cross-check)

- File: `youtopia_at3tool_132_dec.wav`
- Lag: `-797`
- SNR: `-2.290 dB`
- Segmental SNR: `-2.419 dB`
- HF noise ratio: `2.866 dB`

## Notes

- Native decoder compatibility improved: `at3tool.exe` now decodes our current LP2 output.
- On this demanding track, atracdenc now exceeds Sony on SNR/segmental SNR in native decode path.
- This scorecard remains a demanding-track baseline and trend tracker while we close the remaining quality gap.
