# LP2 Parity-First Heuristic Overhaul

## Summary
Build a new accuracy-first LP2 encoding path that keeps ATRAC3/LP2 bitstream compliance for MiniDisc hardware, but replaces the current shallow heuristics with a slower, more perceptually informed decision engine. The immediate goal is Sony parity first, then headroom to surpass it with better heuristics and more compute, without ML and without changing decoder expectations.

## Status (2026-04-12)
- Failure: the `v11` to `v16` parity branch improved tooling and container correctness, but regressed audible quality versus `v10`.
- The new parity heuristics produce more artifacts, more hollow texture, and weaker high-frequency quality on `YOUtopia` than `youtopia_song.current_best_parity_v10.at3.wav`.
- `v16` fixed RIFF/header correctness only. It is a packaging fix, not a sound-quality win.
- Useful outcomes from this branch:
  - RIFF container finalization is now correct.
  - `tools/fix_at3_riff_header.py` can repair older broken `.at3.wav` headers.
  - Decision logging, frame-window controls, and parity metrics are still useful as research tooling.
- Not accepted as encoder direction:
  - the current `--parity` tuning
  - the current parity-safe allocation biases
  - the current parity-driven M/S and transient weighting as a quality path

## Recommendation
- Treat `v10` as the current quality baseline.
- Keep the container/header fix from `v16`.
- Roll back audio decision behavior toward the `v10` character before attempting new quality tuning.
- Keep newer parity logic only as instrumentation and offline analysis until it can beat `v10` on both listening and scorecard metrics.
- A dedicated `--quality-v10` mode now exists to force legacy `v10`-style audio decisions while preserving fixed RIFF output.

## Replacement Direction
1. Restore a `v10`-style encode path as the default quality branch.
2. Preserve only non-audio-risk improvements from the failed parity branch:
- correct RIFF/data sizing
- repair tooling
- frame-window logging
- parity analysis logs for inspection only
3. Freeze experimental parity heuristics behind explicit flags and do not tune by ear on top of them yet.
4. Resume parity work from a narrower scope:
- first close the gap on sibilants/cymbals without changing the overall tonal balance
- then revisit stereo preservation
- then revisit risky-frame search only after it is provably stable

## Key Changes
1. Add a parity-focused analysis pipeline
- Produce per-frame, per-band masking, tonality/noisiness, transient, HF salience, stereo coherence, and stability features.
- Use spectral spreading, temporal look-behind/look-ahead, HF risk tagging, and artifact-risk estimation.
- Keep the current fast path intact and add a `parity` path for tuning work.

2. Replace shallow stereo decisions
- Use stereo coherence, side energy ratio, HF prominence, and transient mismatch to preserve fragile stereo content.
- Add hysteresis so stereo policy does not flap frame-to-frame.
- Keep bitstream syntax and decoder behavior fully compliant.

3. Turn LP2 allocation into a search problem
- Build a small legal candidate set per risky frame.
- Explore BFU budget, HF protection, gain aggressiveness, stereo bias, and tonal preservation.
- Score candidates with perceptual penalties instead of fixed heuristics only.

4. Rework gain/transient control
- Improve attack/sustain/decay discrimination.
- Separate true attacks from noisy HF and near-silent material.
- Favor continuity over gain-point oscillation.

5. Improve tonal handling after parity closes
- Move from one-frame peak picking toward harmonic grouping and cross-frame continuity.
- Treat tonal refinement as a later milestone after stereo/gain/allocation parity work.

6. Extend tooling and visibility
- Add a slow parity mode in the encoder CLI and LP2 wrapper.
- Emit structured decision logs for frame risk, chosen profiles, and allocation outcomes.
- Keep Sony baseline comparisons central to tuning.

## Test Plan
- Corpus: `YOUtopia_source.wav`, chirps/sweeps, sibilant-heavy vocals, cymbals/applause/reverb tails, clicks/castanet-like attacks, tones, and noise bursts.
- Metrics: full-band SNR, HF proxy SNR, stereo preservation, transient-window error, gain/stereo stability, bitstream compliance, and successful decode on the LP2 reference path.
- Acceptance: strict LP2 compatibility, beat the current best parity candidate on `YOUtopia`, reduce Sony HF gap before chasing broad SNR gains, and avoid regressions like stereo collapse or hollow/“whooley” tone.

## Implementation Order
1. Build the parity analysis outputs and risk classifier.
2. Replace shallow stereo allocation with coherence-aware policy.
3. Introduce local candidate search for risky frames.
4. Fold gain/transient behavior into the search.
5. Revisit tonal continuity after parity improves on the main corpus.
6. Retune weights against Sony metrics and listening tests.

## Assumptions
- Scope is LP2 first; LP4 is out of scope for this phase.
- Speed is secondary to quality; multi-pass and local search are acceptable.
- No ML or neural components are included in this phase.
- Bitstream syntax, frame size, decoder interpretation, and hardware compatibility must stay unchanged.
- The parity path should coexist with the current implementation until it clearly outperforms it.
