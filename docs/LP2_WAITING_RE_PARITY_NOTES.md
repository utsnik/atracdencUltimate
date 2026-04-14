# LP2 Parity Notes (While RE Dumps Are Pending)

## Current Best Profile Snapshot

On current binary (`build2/src/atracdenc.exe`) at true LP2:

- `--bfuidxconst 32 --ml-hints` is best on `YOUtopia.wav` in our recent sweep.
- It still regresses transient-heavy synthetic material.

## Critical Finding

Decision logs show:

- `tonal_blocks: 0` for essentially all tested frames/channels (`YOUtopia`, `chirp`).

Latest external RE update suggests this may be intentional on Sony LP2 path:

- LP2 may bypass tonal promotion in many/most frames and rely on residual allocation.
- If confirmed by live hooks, parity work should focus first on allocator/transient/stereo
  rather than forcing tonal writes.

### Active Fix Scope

- Tonal-emission patch was prototyped in source, but should be gated behind fresh
  LP2 runtime evidence because RE now indicates zero-tonal behavior could be expected.
- Priority order updated:
  1. allocator complexity feedback parity,
  2. gain/transient parity,
  3. stereo matrix/weight side-info parity,
  4. tonal policy only if hooks show promoted tonals in target content.

## Tooling Added

- `tools/lp2_profile_sweep.py`:
  - runs profile matrix vs Sony at3tool baseline and prints aligned SNR deltas.
- `tools/decision_log_summary.py`:
  - summarizes `--decision-log` files into frame/channel stats.
- `tools/lp2_adaptive_encode.py`:
  - chooses LP2 profile by simple input features:
    - transient-heavy -> `default`
    - otherwise -> `--ml-hints` (policy v2; avoids forced BFU32 on long songs)
  - now also accepts `--re-metrics-csv` and can choose profile from extracted
    at3tool deep metrics when available.
- `tools/lp2_frame_snr_compare.py`:
  - compares per-frame SNR between two decoded outputs (with lag alignment).
- `tools/validate_re_dump.py`:
  - checks whether RE per-frame CSV dumps look dynamic or placeholder-like.
- `tools/atracdenc_lp2.py`:
  - convenience CLI mode wrapper:
    - `--mode lp2-adaptive`
    - `--mode default`
    - `--mode ml`
    - `--mode bfu32-ml`
    - `--mode ml-air` (preconditioned encode path for clearer sibilants/transients)
    - `--mode ml-nogain` (ML hints with disabled gain control)
    - `--mode ml-decision` (auto A/B choose `ml` vs `ml-nogain` on a short clip)
    - `--mode ml-decision-air` (adds preconditioned candidates to decision)
    - `--mode ml-decision-sharp` (HF-forward candidate set)
    - `--mode ml-decision-parity` (Sony-target distance mode)
    - `--mode quality-v10-frozen` (known-good legacy baseline + RIFF fix)
  - default mode is now `quality-v10-frozen` (stability-first).
  - non-frozen modes now run decode validation through `at3tool`.
  - on validation failure, wrapper auto-falls back to `quality-v10-frozen`
    unless explicitly disabled with `--no-fallback`.
- `tools/lp2_parity_gate.py`:
  - short-clip gate harness for tuning safety:
    - compares candidate mode vs `quality-v10-frozen` and Sony LP2.
    - computes full-band + HF proxy SNR.
    - fails fast when candidate regresses beyond configured guard rails.
- `tools/lp2_degradation_report.py`:
  - objective degradation audit across many already-decoded outputs.
  - reports:
    - aligned full-band SNR,
    - aligned HF proxy SNR,
    - deltas vs chosen baseline decode,
    - 2D distance to Sony metric point.
  - latest summary for YOUtopia 30 s window:
    - saved at `docs/LP2_DEGRADATION_AUDIT_2026-04-13.md`.
- `tools/lp2_perceptual_proxy.py`:
  - deeper proxy check for perceived regressions on a pair of decodes.
  - adds segmental robustness and vocal-band error estimates:
    - full-band SNR and HF proxy SNR,
    - segmental SNR (`p10`, median),
    - vocal error ratio in an approximate 300..3400 Hz band.
  - useful for catching "rolling/underwater" vocal regressions early.
- `tools/lp2_decision_encode.py`:
  - quick decision runner:
    - encodes first `N` seconds with candidate profiles,
    - decodes candidates with `at3tool`,
    - compares aligned full-band SNR + HF proxy SNR,
    - then encodes the full file with the selected profile.
  - supports:
    - `ml`, `ml_nogain` by default,
    - optional `--include-air` to also consider `ml_air` and `ml_air_nogain`.
- `tools/lp2_precondition_encode.py`:
  - WAV preconditioning front-end before LP2 encode:
    - gentle low-mid trim,
    - HF pre-emphasis,
    - onset-aware high-band boost,
    - normalization guard.
  - defaults tuned to a safer preset from 30 s YOUtopia sweep:
    - `preemph=0.02`, `low_cut_mix=0.00`, `transient_mix=0.02`
    - observed effect on 30 s slice vs plain `ml`:
      - full-band SNR delta: about `-0.18 dB`
      - HF proxy delta: about `+0.03 dB`
- `tools/lp2_scorecard.py`:
  - generates a Markdown scorecard from a fixed profile set and Sony baseline.
  - latest output: `docs/LP2_SCORECARD_CURRENT.md`.

## New Interim Result (No RE Runtime Hooks Yet)

- Adaptive wrapper improved synthetic average delta in recent sweep:
  - from about `-8.14 dB` (`default`) to about `-4.43 dB` (adaptive policy).
- `YOUtopia` remains closer to Sony under the fidelity profile than plain default.
- Adaptive selector upgraded to use frame-aware statistics
  (`burst_ratio`, `mean_frame_crest`) instead of only global track metrics.
- Current scorecard (`docs/LP2_SCORECARD_CURRENT.md`) shows:
  - `default` avg delta: `-8.861 dB`
  - `ml` avg delta: `-8.085 dB`
  - `bfu32_ml` avg delta: `-5.933 dB`
  - `adaptive_policy` avg delta: `-3.847 dB`

## New Finding (Gain Control Is A Large Lever)

- On full `YOUtopia_source.wav` (30 s decision window, fixed lag `-69`):
  - `ml`: full `17.968 dB`, HF `4.925 dB`
  - `ml-nogain`: full `18.349 dB`, HF `5.027 dB`
  - improvement: `+0.381 dB` full, `+0.102 dB` HF proxy.
- However, synthetic transient-heavy sample (`tmp_transient.wav`) regresses with
  full no-gain, so the likely best path is adaptive gain policy (not always-off).

## New Finding (Decision Policy v2)

- Added `--mode ml-decision-air` to `tools/atracdenc_lp2.py`:
  - runs short A/B/C/D (`ml`, `ml_nogain`, `ml_air`, `ml_air_nogain`),
  - selects a profile with a full-band guard + weighted scoring.
- Added `--mode ml-decision-sharp` to `tools/atracdenc_lp2.py`:
  - adds HF-biased BFU candidates (`bfu27_*`, `bfu28_*`),
  - uses relaxed full-band guard and stronger HF score weighting.
- Current sweep summary:
  - `tmp_sine.wav` -> `ml`
  - `tmp_multitone.wav` -> `ml`
  - `tmp_transient.wav` -> `ml`
  - `chirp_wait.wav` -> `ml`
  - `YOUtopia.wav` -> `ml`
  - `YOUtopia_source.wav` -> `ml_nogain`
- This is the current best conservative behavior: keep gain control for transients,
  disable it for the demanding full-song YOUtopia case.

## New Finding (HF-Forward Tradeoff Mode)

- For YOUtopia 30 s decision window:
  - `ml`: full `17.968`, HF `4.925`
  - `ml_nogain` (fidelity profile): full `18.349`, HF `5.027`
  - `bfu27_ml_nogain` (sharp profile v9): full `17.825`, HF `6.101`
- Interpretation:
  - `ml_nogain` is safer and highest full-band metric.
  - `bfu27_ml_nogain` gives much stronger HF recovery (closer to Sony treble)
    with a smaller full-band penalty than `bfu28`.
- Full-track YOUtopia trend (approx):
  - `ml_nogain`: full `18.382`, HF `4.352`
  - `sharp_v9` (`bfu27_ml_nogain`): full `18.089`, HF `5.468`
  - Sony decode baseline: full `16.596`, HF `6.565`
- So we now have two practical listening targets:
  - fidelity-biased (`ml-decision-air`),
  - sharpness-biased (`ml-decision-sharp`).

## Sony Distance Snapshot (2026-04-12)

Using aligned decode-vs-source SNR metrics on `YOUtopia_source.wav`:

- Sony LP2 decode baseline:
  - full-band: `16.596`
  - HF proxy: `6.565`
- `current_best_v7` (`ml_nogain`, fidelity):
  - full-band: `18.382` (`+1.786` vs Sony)
  - HF proxy: `4.352` (`-2.212` vs Sony)
- `current_best_sharp_v8` (`bfu28_ml_nogain`):
  - full-band: `17.523` (`+0.928` vs Sony)
  - HF proxy: `5.694` (`-0.871` vs Sony)
- `current_best_sharp_v9` (`bfu27_ml_nogain`):
  - full-band: `18.089` (`+1.493` vs Sony)
  - HF proxy: `5.468` (`-1.096` vs Sony)
- `current_best_parity_v10` (`bfu28_base_nogain`):
  - full-band: `17.303` (`+0.707` vs Sony)
  - HF proxy: `5.770` (`-0.794` vs Sony)

Practical read:

- `v8` is currently our closest-to-Sony treble balance of the sharp variants.
- `v7` has the strongest full-band metric but is farther from Sony in HF.
- `v10` is currently the closest combined parity point (full+HF) we have measured.

## New Finding (`--notonal` Is Inert On Current LP2 Path)

- In current build/profile, `--notonal` produces bit-identical output vs `ml`
  (same SHA-256 and exact byte equality on `YOUtopia_source.wav`).
- Synthetic checks (`sine`, `multitone`, `transient`, `chirp`) also show `0.000 dB`
  SNR delta between `ml` and `ml_notonal`.
- This supports the current RE hypothesis that tonal packing is effectively not
  active on our practical LP2 path right now; we should prioritize gain/allocator
  parity first.

## Metric Hardening Update

- The canonical score workflow now suppresses the vocal-band error proxy on
  control material that does not contain enough vocal-band energy.
- This matters because transient-only samples can otherwise explode the proxy
  into meaningless values and hide real stability regressions.
- Current practical use:
  - `YOUtopia` and other vocal-heavy music still report the vocal proxy.
- `tmp_transient` now shows `n/a` instead of a garbage-scale value.
- That makes the metric set better suited for the next anti-wobble tuning pass.

## Stability Lane Update (2026-04-13)

- Added a new tuning mode:
  - `quality-v10-stable`
- Its current wrapper policy is intentionally conservative:
  - starts from `quality-v10-native`
  - keeps `--nogaincontrol`
  - enables stability-only analysis/logging and future continuity hooks
- Added stability gating to `tools/lp2_score_workflow.py`:
  - per-sample pass/fail
  - duration guard
  - YOUtopia regression guard
  - hotspot-aware reporting
  - small improvement epsilon for measurement noise on synthetic control files
- Current full-corpus result:
  - `docs/LP2_SCORE_WORKFLOW_STABLE_2026-04-13.md`
  - gate status: `PASS`
- Important practical read:
  - this phase successfully formalized the anti-regression lane
  - it does not yet improve transient/chirp quality beyond native v10
  - the new mode is currently baseline-preserving by design, which is the right
    place to be before further risky tuning

## New Decision Log Fields

- `stability_mode`
- `ms_ratio_raw`
- `ms_ratio_final`
- `ms_continuity_clamped`
- `continuity_reason`
- `gain_continuity_clamped`
- `gain_weak_transient_suppressed`
- `hf_continuity_clamped`
- `gain_target_prev`
- `gain_target_cur`
- `gain_first_level_prev`
- `gain_first_level_cur`

## Narrow Gain Experiment Update (2026-04-13)

- Added a separate experimental mode:
  - `quality-v10-gain-exp`
- Goal:
  - keep `quality-v10-stable` clean,
  - test narrow gain-control changes in a lane that is allowed to fail.
- Current implementation:
  - inherits the `quality-v10` baseline path,
  - turns on the stability plumbing,
  - tightens marginal gain triggering,
  - clamps first gain-point jumps more aggressively,
  - skips explicit point-0 boundary edits during the experiment.

### New Tooling

- `tools/lp2_fast_stability_manifest.json`
  - short 4-sample gate corpus for quick iteration.
- `tools/lp2_fast_stability_gate.py`
  - convenience runner for the fast gate.
- `tools/lp2_decision_log_diff.py`
  - auto-generates and compares decision logs between two modes.

### First Experimental Result

- Fast gate report:
  - `docs/LP2_FAST_STABILITY_GATE_GAIN_EXP_2026-04-13.md`
- Decision-log diff report:
  - `docs/LP2_DECISION_LOG_DIFF_GAIN_EXP_2026-04-13.md`

Outcome:

- `quality-v10-gain-exp` is wired correctly and measurably changes decisions.
- It is not acceptable yet:
  - `YOUtopia`: regresses full-band, HF, and worst-hotspot metrics.
  - `Badlands`: regresses HF and hotspot behavior.
  - `tmp_transient`: regresses strongly.
  - `chirp_wait`: effectively neutral.

Current recommendation remains:

- keep `quality-v10-native` as the listening/reference baseline,
- keep `quality-v10-stable` as the anti-regression harness,
- treat `quality-v10-gain-exp` as a failed first experiment, not a candidate upgrade.

### Follow-up Tightening Result (pass3)

- Added a stricter gain-exp allow gate:
  - very high attack threshold,
  - very low sustain requirement,
  - narrow attack width,
  - stronger HPF overlap gate.
- Validation report:
  - `docs/LP2_FAST_STABILITY_GATE_GAIN_EXP_2026-04-13_pass3.md`
- Current status:
  - fast stability gate: `PASS`.
  - on the fast corpus this mode is now effectively baseline-preserving
    (no practical metric delta vs `quality-v10-native`).

Practical interpretation:

- this is a successful safety quarantine for the experimental lane,
- but it is not yet an audible quality improvement path.

## Gain-Exp2 Follow-up (2026-04-13)

- Added a second isolated experiment lane:
  - CLI flag: `--gain-exp2`
  - wrapper mode: `quality-v10-gain-exp2`
- Intended behavior:
  - keep legacy-v10 baseline path intact,
  - allow only a high-band-only gain experiment with very strict safety limits.

### Results

- First run failed fast gate:
  - `docs/LP2_FAST_STABILITY_GATE_GAIN_EXP2_2026-04-13.md`
- A wider pass still failed hard:
  - `docs/LP2_FAST_STABILITY_GATE_GAIN_EXP2_2026-04-13_pass2.md`
- After strict re-tightening, fast gate passed:
  - `docs/LP2_FAST_STABILITY_GATE_GAIN_EXP2_2026-04-13_pass3.md`

### Current interpretation

- `quality-v10-gain-exp2` is now safety-quarantined and stable.
- On the fast corpus it is effectively baseline-preserving (no practical gain over
  `quality-v10-native`).
- We should treat it as a controlled test lane, not as a shipping quality uplift.

## RE Dump Status

- `reverse/per_frame_metrics.csv` and `reverse/metrics.jsonl` currently appear
  generated from hardcoded values in `reverse/ghidra_scripts/ExtractDetailedMetrics.java`,
  not live frame-varying hook captures.
- We should treat current dump values as scaffolding only until dynamic runtime
  extraction is wired.
- external analysis snapshot copied to:
  `docs/re/reverse_engineering_report_external_2026-04-11.md`.

## What We Need From RE Dumps

From at3tool frame traces:

- tonal component counts per frame,
- tonal bits contribution,
- complexity score behavior around tonal/transient branches,
- gain-point counts per band,
- JS matrix/weight side-info.

These will let us map missing tonal/transient behavior and tune toward Sony parity.

## Runtime-First LP2 Parity RE (2026-04-13)

Generated artifacts:

- report: `docs/re/LP2_PARITY_RE_REPORT_2026-04-13.md`
- raw Sony LP2 CSV/JSONL: `reverse/windows/lp2_parity_re/raw/`
- normalized frame tables: `reverse/windows/lp2_parity_re/normalized/`

Key findings:

- Dynamic LP2 fields now vary meaningfully across the corpus, so the Frida LP2 extractor is usable for parity work.
- `YOUtopia` hotspots look mixed stereo-plus-allocator driven:
  - matrix index stays fixed, but weight movement rises on bad frames,
  - complexity also rises on those same frames.
- `chirp_wait` still looks predominantly allocator-driven.
- `tmp_transient` still points at gain/transient parity work, but the current attack proxy is still partly derived and should be treated carefully until `FUN_0043ec60` semantics are pinned down.
- Current runtime corpus does not show tonal counts dominating the hard LP2 failures, so tonal work should stay below stereo/gain/allocator parity.

Targeted Ghidra follow-up remains:

- `FUN_0043f270` for allocator feedback semantics,
- `FUN_0043ec60` for segment-energy / attack semantics,
- `FUN_0043d080` for gain side-info / gain-point meaning,
- `param_3[1]` plus `0x143f` write-back mapping for LP2 JS weight behavior.

## Stereo-Exp Lane (2026-04-13)

Goal:

- verify whether LP2 parity gap is partly caused by disabled joint-stereo path at 132300.

Implementation:

- added `--stereo-exp` CLI switch.
- added wrapper mode `quality-v10-stereo-exp`.
- wired joint-stereo override through:
  - container creation,
  - encoder matrixing path,
  - bitstream writer JS path.

Verification:

- safety path (`quality-v10-stable` vs `quality-v10-native`) remains PASS on fast gate:
  - `docs/LP2_FAST_STABILITY_GATE_STEREO_EXP_SAFE_2026-04-13.md`
- stereo-exp decision logs confirm JS path is active:
  - `js_enabled: true`
  - non-zero `ms_preserve_side`, `ms_hf_risk`
  - continuity clamps trigger on some frames.

Current blocker:

- `quality-v10-stereo-exp` currently fails decode validation on LP2 with at3tool:
  - decoded duration ratio collapses to ~0
  - at3tool reports `error code : 0x1000105`
- wrapper therefore falls back to `quality-v10-frozen` unless `--no-fallback`.

Conclusion:

- this lane is useful for RE and logging, but not yet valid for listening/parity scoring.
- next focused task is bitstream conformance for JS-at-132300 (LP2) before quality tuning.

## Gain-Mode Activity Check (2026-04-13)

Artifacts:

- report: `docs/LP2_GAIN_MODE_ACTIVITY_2026-04-13.md`
- stable gate re-check: `docs/LP2_FAST_STABILITY_GATE_stable_post_gainpoints_2026-04-13.md`

Key findings:

- Added `gain_points_per_band` to decision logs so we can directly verify whether gain curves are emitted per channel/frame.
- `quality-v10-gain-exp` and `quality-v10-gain-exp2` are currently no-op on `YOUtopia_30s`:
  - both emit zero gain points,
  - both are byte-identical to `quality-v10-native` (`fc /b` reports `SAME`).
- `quality-v10` (legacy gain-enabled path) emits substantial gain activity and remains unstable on killer samples:
  - `YOUtopia_30s` gain-point totals: `[242, 1897, 1526, 0]`.
  - prior fast gate run confirms severe hotspot regressions on `tmp_transient` and HF regressions on `YOUtopia`.

Conclusion:

- keep native/stable no-gain baseline protected.
- treat gain work as a narrow lane requiring stronger guardrails before reintroducing it for parity closing.

## Stability Transient Micro-Lane (2026-04-13, lane3)

Goal:

- improve `tmp_transient` without changing `YOUtopia` behavior.

Implementation:

- Added a bounded, stability-mode-only micro boost inside legacy-v10 allocation path.
- Trigger is intentionally narrow (LP2 only):
  - very low frame stability,
  - high attack risk,
  - low HF-risk,
  - low-band BFUs only.
- This lane runs only when parity window is active in `quality-v10-stable`.

Result:

- gate report: `docs/LP2_FAST_STABILITY_GATE_stable_transient_lane3_2026-04-13.md`
- `YOUtopia`: unchanged vs baseline (byte-identical on 30s probe)
- `tmp_transient`: small objective uplift:
  - full `+0.005 dB`
  - HF `+0.002 dB`
  - Sony-distance `10.646 -> 10.641`
  - worst hotspot still near baseline (`-0.015 dB`)

Status:

- Accepted as a safe micro-step, but gain is small.
- Next high-value step remains HF/sibilance allocation rescue on real music hotspots.

## 2026-04-13 Stability Lane4-6 Follow-up

- Goal: remove long-file `YOUtopia242` hotspot regression at frame `3420` while preserving the tiny `tmp_transient` win in `quality-v10-stable`.
- Verified with canonical gates:
  - `docs/LP2_FAST_STABILITY_GATE_stable_transient_lane4_2026-04-13.md`
  - `docs/LP2_FAST_STABILITY_GATE_stable_transient_lane5_2026-04-13.md`
  - `docs/LP2_FAST_STABILITY_GATE_stable_transient_lane6_2026-04-13.md`
  - `docs/LP2_SCORE_WORKFLOW_YOUTOPIA242_stable_vs_native_lane4_2026-04-13.md`
  - `docs/LP2_SCORE_WORKFLOW_YOUTOPIA242_stable_vs_native_lane5_2026-04-13.md`
  - `docs/LP2_SCORE_WORKFLOW_YOUTOPIA242_stable_vs_native_lane6_2026-04-13.md`
- Result: no regression from new micro-lane edits, but the existing stable-vs-native long-file hotspot remains unchanged (`frame 3420: -0.601 dB`).

### What we confirmed

- The `-0.601 dB` hotspot is not caused by the recent HF micro-boost experiments; it is already present in the baseline stable lane.
- Frame-window decision-log diffs around `3419..3422` show the divergence is dominated by gain continuity state carry-over (clamp state and first-level history), not by broad BFU or JS policy changes.
- Fast gate improvements are still tiny and localized (`tmp_transient` +0.005 full / +0.002 HF), while `YOUtopia` short-window gate stays effectively neutral.

### Current interpretation

- The remaining long-file hotspot is a continuity-state issue (gain controller memory effect) rather than a frame-local allocation rule bug.
- Next highest-value action is to add a narrow anti-wobble guard in gain continuity that is conditional on sustained context (not a per-frame clamp), then re-run long-file validation.

## 2026-04-14 Stability Lane9 Fix (Long-File Hotspot Cleared)

- Root cause for the lingering `YOUtopia242` frame `3420` hotspot was the stability micro-lane transient protection firing on non-target tonal/vocal content around frame `3421`.
- Fixes applied:
  - Scoped gain continuity behavior in `CreateSubbandInfo` to HF bands (`band >= 2`) when `quality-v10-stable` is active.
  - Tightened transient micro-boost gating in `CalcBitsAllocationLegacyV10` to a strict narrow lane (`bfuBand == 1`, stronger attack/tonal/HF guards).
- Results after rebuild and rerun:
  - Long-file `YOUtopia242`: hotspot improved from `-0.601 dB` to `+0.000 dB` (cleared).
  - Decision diff around frames `3418..3427`: channel field deltas dropped to `0` (only expected mode/profile fields differ).
  - Fast stability gate remains PASS across corpus.
- Tradeoff:
  - Previous tiny `tmp_transient` uplift (`+0.005 dB`) is now neutralized (`+0.000 dB`) in exchange for eliminating long-file vocal instability risk.

## 2026-04-14 Stability Lane12/Lane13 Follow-up (Anti-Regression Kept)

- Ran an HF protection experiment in `quality-v10-stable` targeting high-band sibilance-risk frames.
- Outcome:
  - Fast gate stayed PASS, but long-file `YOUtopia242` regressed with new hotspots (worst `-0.615 dB`), so this lane was rejected.
  - Reverted to the safer narrow gating profile; long-file parity returned to neutral (`worst hotspot +0.000`).
- Added observability in legacy-v10 allocation logs:
  - `allocation_micro_lane: {transient_hits, hf_sibilance_hits}`
  - This gives frame-level visibility into whether micro-lane conditions actually fire during shift search.
- Current status:
  - `quality-v10-stable` remains protected and regression-free versus `quality-v10-native` on both fast gate and `YOUtopia242` long run.
  - No accepted quality uplift yet from the new HF micro-lane; we need better targeted trigger evidence before further tuning.

## 2026-04-14 Music-Parity-First Plan Implementation (Phase A)

Implemented foundations for the LP2 music-parity lane with strict anti-regression gating and hotspot-correlation tooling.

### What landed

- Added canonical music gate runner: `tools/lp2_music_parity_gate.py`.
  - Runs required per-change checks:
    - fast corpus (`YOUtopia`, `Badlands`, `chirp_wait`, `tmp_transient`)
    - long `YOUtopia242`
  - Enforces hard reject rules:
    - `YOUtopia242` worst hotspot must stay `>= -0.25 dB`
    - `YOUtopia` full/HF deltas vs native must stay `>= -0.10 dB`
    - decoded duration ratio must stay valid
  - Tracks consecutive music-target passes in `docs/re/lp2_music_parity_state.json`.

- Extended `tools/lp2_score_workflow.py`:
  - configurable hotspot settings: `--hotspot-limit`, `--hotspot-hf-threshold-db`
  - machine-readable output: `--out-json`

- Added hotspot join tool: `tools/lp2_hotspot_join.py`.
  - Produces standardized joined reports (`csv` + `jsonl`) from score hotspots + Sony extractor CSV.
  - Emits per-hotspot bucket labels and ranked action recommendations:
    - `stereo-driven`
    - `gain/transient-driven`
    - `allocator-driven`
  - Supports top-K ranking per sample (default 25).

- Added bucket visibility in decision logs (`src/atrac/at3/atrac3_bitstream.cpp`):
  - top-level: `parity_bucket`, `parity_bucket_reason`
  - allocation micro-lane summary now logs hit counts and bucket context.

- Added bucket-aware narrow behavior in stability lane:
  - stereo parity policy in `CalcMSBytesShift` is gated by frame bucket
  - allocator micro nudges in legacy-v10 path are bucket-gated
  - transient micro-lane is restricted to gain/transient bucket

- Added conservative gain/transient context gating in `CreateSubbandInfo` (`src/atrac3denc.cpp`)
  based on prior-frame parity context to reduce one-frame misfires outside transient lanes.

### Validation snapshot

- Canonical music gate run:
  - report: `docs/LP2_MUSIC_PARITY_GATE_2026-04-14.md`
  - safety gate: PASS
  - long `YOUtopia242` worst hotspot: `-0.057 dB` (within hard gate)
  - music Sony-distance targets remain pending (`YOUtopia 1.022`, `Badlands 1.239`).

- Standardized hotspot join outputs:
  - `docs/LP2_HOTSPOT_JOIN_FAST_2026-04-14.csv`
  - `docs/LP2_HOTSPOT_JOIN_FAST_2026-04-14.jsonl`

### Status

- Phase A complete: baseline lock + gating + hotspot-correlation + bucket observability are in place.
- Next phase is tuning work driven by the joined top-25 hotspot action list, with no-regression gating on every accepted change.

## 2026-04-14 Music-Parity-First Validation Re-Run (Phase A Sanity Check)

- Re-ran canonical gate end-to-end with the current `quality-v10-stable` lane:
  - command output report: `docs/LP2_MUSIC_PARITY_GATE_2026-04-14_rerun.md`
  - safety gate: PASS
  - long `YOUtopia242` worst hotspot: `-0.057 dB` (inside hard gate)
  - `YOUtopia` full/HF delta vs native: `+0.001 / +0.001 dB`
  - music Sony-distance targets are still pending (`YOUtopia 1.022`, `Badlands 1.239`)
- Re-ran hotspot join from the fast gate JSON:
  - `docs/LP2_HOTSPOT_JOIN_FAST_2026-04-14_rerun.csv`
  - `docs/LP2_HOTSPOT_JOIN_FAST_2026-04-14_rerun.jsonl`
  - rows: `82`
- Verified decision-log bucket observability on a short probe run:
  - `scratch/bucket_probe.log` now contains:
    - `parity_bucket`
    - `parity_bucket_reason`
    - `allocation_micro_lane` with `transient_hits`, `hf_sibilance_hits`, `allocator_feedback_hits`
    - continuity fields (`ms_continuity_clamped`, `gain_continuity_clamped`)

### Status after re-run

- The plan infrastructure is stable and reproducible.
- Top-25 hotspot bucket mix from rerun join:
  - `YOUtopia`: `stereo-driven 16`, `gain/transient-driven 9`
  - `Badlands`: `stereo-driven 17`, `gain/transient-driven 8`
  - `chirp_wait`: `allocator-driven 21`, `stereo-driven 4`
  - `tmp_transient`: `stereo-driven 6`, `allocator-driven 1`
- Next accepted changes should be tuning-only and justified by the hotspot join top-25 action table.
