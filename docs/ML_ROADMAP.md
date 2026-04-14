# ML/Neural Encoder Roadmap

## Overview

The encoder already has ML infrastructure (--ml-hints, TMlHints, ExtractMlFrameFeatures).
This document outlines the path to a learned per-frame bit allocator that can surpass Sony's
static hand-tuned tables on modern material.

## Why ML Can Beat Static Tuning

Sony's divisor table (x = 2.6/2.8/3.3/3.6/4.2/5.5 per BFU group) was hand-tuned once for
typical J-pop/rock circa 2001. A per-frame neural predictor adapts to signal content, placing
bits where they matter most for each specific frame.

## Proposed Architecture

### Phase A: Learned Bit Allocator (MLP, ~10k params, CPU inference)
- Input: energyPerBfu[32], smrPerBfu[32], BandEnergy[4], TransientScore, HfRatio
- Output: per-BFU divisor scale (replaces static x table)
- Training: encode corpus of 500+ tracks, compute PEAQ scores, train to maximise
- Integration: gate behind --ml-alloc flag, keep all safety gates (6-point cap, bit budget)

### Phase B: Temporal Context (shallow LSTM, ~50k params)
- 5-10 frame history for pre-echo prediction
- Dramatically improves on single-frame energy comparison in --temporal-masking
- Replaces heuristic attack slope threshold with learned detection

### Phase C: Neural Perceptual Metric
- Lightweight CDPAM/PEAQ proxy trained on this encoder's output distribution
- Provides correct training signal for Phases A and B (optimise for perception, not Sony parity)

## Expected Quality Gains

| Component | Estimated gain vs Sony |
|-----------|----------------------|
| Learned allocator (Phase A) | +0.3 to +0.8 dB full_snr |
| Temporal LSTM (Phase B) | +0.1 to +0.3 dB seg_p10 |
| Combined A+B | +0.5 to +1.5 dB on complex modern material |

## Implementation Steps

1. Build training dataset: encode corpus -> measure PEAQ -> record (features, allocations, score)
2. Train MLP offline in Python (PyTorch, export weights as constexpr C++ arrays)
3. Add --ml-alloc flag (same pattern as --smr-alloc, --temporal-masking)
4. Benchmark against Sony on diverse test corpus
5. If Phase A shows >0.2 dB gain, proceed to Phase B LSTM

## Constraints

- Bitstream format is fixed (must decode on real MDLP hardware) — ML influences decisions only
- No GPU at encode time — inference must be fast on CPU (<1ms per frame)
- All existing safety gates (6-point gain cap, BFU bounds, bit budget) must remain active
- Model weights ship as constexpr arrays in a header — zero runtime dependencies
