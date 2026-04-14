# LP2 Parity Branch Postmortem (2026-04-12)

## Verdict
- Failure as an audio-quality branch.
- `v11` to `v16` added valuable tooling and fixed container correctness, but they did not beat `v10` subjectively.
- `youtopia_song.current_best_parity_v10.at3.wav` remains the best-sounding current result.

## What Went Wrong
- The parity branch became over-reactive to transient and HF risk.
- That pushed too many bits and decision penalties toward "danger" frames without enough evidence that the tradeoff was perceptually correct.
- At LP2's fixed 132 kbps budget, those extra protections starved the rest of the spectrum and made the output sound hollow, splashy, and artifact-prone.
- Tonal handling is still too weak to support aggressive HF/transient protection safely.
- Candidate-search work is not stable enough yet to rescue the heuristic mistakes.

## What Was Still Worth Keeping
- Correct RIFF/data size finalization in the ATRAC3 RIFF container writer.
- `tools/fix_at3_riff_header.py` for repairing older broken `.at3.wav` outputs.
- Decision logging and frame-window controls.
- Stereo/parity metrics as offline diagnostics.

## What We Should Do Instead
1. Re-center on `v10` as the audio baseline.
2. Keep container and tooling fixes, but stop treating the current parity heuristics as progress.
3. Split future work into two tracks:
- shipping track: `v10` sound character plus container correctness
- research track: parity metrics and offline experiments behind explicit flags
4. Only merge research ideas into the shipping path if they beat `v10` on both:
- listening tests on `YOUtopia` and killer samples
- objective metrics on the fixed LP2 corpus

## Recommended Next Implementation Step
- Implemented: `--quality-v10` now forces legacy `v10`-style allocation/stereo policy while keeping the fixed RIFF writer.
- Use `--parity --quality-v10` when you want the v10-quality character plus parity tooling hooks.
- Added practical baseline mode in wrapper: `tools/atracdenc_lp2.py --mode quality-v10-frozen` uses the known-good legacy encoder binary and then repairs RIFF header sizes.
- Compare every new heuristic change against this baseline one variable at a time.

## Stabilization Update (2026-04-12, later pass)
- Wrapper default is now stability-first:
  - `tools/atracdenc_lp2.py` default mode is `quality-v10-frozen`.
- Added automatic decode validation for non-frozen modes:
  - wrapper now decodes the encoded file with `at3tool` and checks decoded duration.
  - if validation fails, wrapper auto-falls back to `quality-v10-frozen` (can be disabled with `--no-fallback`).
- Added a parity gate harness:
  - `tools/lp2_parity_gate.py` compares candidate mode vs frozen-v10 baseline vs Sony on a short clip.
  - gate fails if candidate regresses too much vs frozen-v10.

## Important Clarification
- Current in-source `--quality-v10` behavior is still not matching the frozen-v10 legacy binary output on YOUtopia checks.
- So for listening-quality baseline, treat `quality-v10-frozen` as canonical until native parity is proven.
