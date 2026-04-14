# LP2 Gain-Mode Activity Check (2026-04-13)

## Goal
Confirm whether our current gain experiment lanes actually emit gain points, and whether they change LP2 output vs `quality-v10-native`.

## What Was Run
- `quality-v10-native` on `scratch/YOUtopia_30s.wav` with decision log.
- `quality-v10-gain-exp` on `scratch/YOUtopia_30s.wav` with decision log.
- `quality-v10-gain-exp2` on `scratch/YOUtopia_30s.wav` with decision log.
- `quality-v10` (legacy v10 with gain enabled) on `scratch/YOUtopia_30s.wav` and `tmp_transient.wav` with decision logs.
- Byte-level compare (`fc /b`) between native and gain-exp outputs, and between native and gain-exp2 outputs.

## Findings
1. `quality-v10-gain-exp` and `quality-v10-gain-exp2` are currently **bitstream-identical** to `quality-v10-native` on `YOUtopia_30s`.
   - `fc /b scratch\\YOUtopia_30s.native_t2.at3.wav scratch\\YOUtopia_30s.gain_exp_t2.at3.wav` => `SAME`
   - `fc /b scratch\\YOUtopia_30s.native_t2.at3.wav scratch\\YOUtopia_30s.gain_exp2_t2.at3.wav` => `SAME`

2. Decision logs confirm both gain-exp lanes emit **zero gain points** on this sample.
   - `gain_points_per_band` totals were `[0, 0, 0, 0]` across all logged channel-frames.

3. `quality-v10` (gain-enabled legacy path) emits many gain points and is unstable on key samples.
   - On `YOUtopia_30s`, gain point totals were `[242, 1897, 1526, 0]`.
   - On `tmp_transient`, hotspot frames showed recurring `gain_points_per_band: [1, 1, 1, 0]` with aggressive first gain levels (`0`/`1`/`2`) and severe metric collapse in prior gate run.

4. Fast stability gate after instrumentation change remained PASS for `quality-v10-stable` (no regressions introduced by logging fields).

## Conclusion
- Current gain experiment lanes are effectively **no-op safety lanes** on the tested LP2 corpus.
- The legacy gain-enabled path (`quality-v10`) is still too unstable for parity baseline use.

## Recommendation
- Keep `quality-v10-native` / `quality-v10-stable` as protected baseline.
- For next parity work, prioritize allocator/stereo decisions and treat gain as an opt-in narrow lane only after adding explicit guardrails around first-level extremes and per-band activation.
