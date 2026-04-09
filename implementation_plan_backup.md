# ATRAC3 (LP2 / LP4) Parity – Complete Implementation Plan

Goal: Finalize the ATRAC3 (LP2/LP4) encoder to reach audio quality parity with Sony's `at3tool.exe`. This involves fixing fundamental codec bugs, correcting the RIFF header to pass Sony decoder validation, running automated SNR benchmarking, and implementing tonal spectral suppression.

---

## Sony Baseline SNR Targets

### LP2 @ 132 kbps (MiniDisc LP2, 384-byte frames, stereo)

Measured directly from `at3tool.exe -e -br 132`. These are our parity targets.

| Test Signal | at3tool SNR | at3tool AlignedSNR | SpectralL1 |
|---|---:|---:|---:|
| sine_1k_5s.wav | **56.96 dB** | 56.96 dB (lag=0) | 0.000372 |
| chirp_20_20k_5s.wav | **24.14 dB** | 24.14 dB (lag=0) | 0.001578 |
| multitone_5s.wav | **39.34 dB** | 39.34 dB (lag=0) | 0.001257 |
| transient_5s.wav | **45.74 dB** | 45.74 dB (lag=0) | 0.002460 |

### LP4 @ 66 kbps (MiniDisc LP4, 192-byte frames, joint stereo)

⏳ **Pending** — must run `at3tool -e -br 66` baseline sweep once header fix is applied.

| Test Signal | at3tool SNR | at3tool AlignedSNR | SpectralL1 |
|---|---:|---:|---:|
| sine_1k_5s.wav | TBD | TBD | TBD |
| chirp_20_20k_5s.wav | TBD | TBD | TBD |
| multitone_5s.wav | TBD | TBD | TBD |
| transient_5s.wav | TBD | TBD | TBD |

> [!IMPORTANT]
> **Current atracdenc status**: All `atracdenc_metrics` are `None` — `at3tool -d` rejects our output with exit code 1 ("Not Supported Parameter"). Fixing the RIFF header is the **entire prerequisite** before any SNR numbers can be measured.

---

## Key Findings & Root Cause Analysis

### Bug 1 — Bitrate Mapping (`main.cpp`) ✅ FIXED & REBUILT
`main.cpp` incorrectly used `bitrate * 1024`, selecting the 424-byte frame container instead of the 384-byte LP2 container.
- Fix applied: `bitrate * 1000` → `132300 bps` → 384-byte frames.
- New binary confirmed at `Bitrate: 132300` and `.oma` file size ~83,400 bytes (5s stereo). ✅

### Bug 2 — Signal Scaling (`atrac3denc.cpp`) ✅ FIXED, UNVERIFIED
`atrac3denc.cpp` ~line 313: `src[i] = data[...] / 1.25`. Fix applied. Cannot verify until `at3tool -d` accepts the files.
- `/ 1.0` caused clipping at 1.19 peak MDCT coefficient.
- `/ 1.25` maximizes SNR while preventing quantizer overflow.

### Bug 3 — RIFF Header (`at3.cpp`) ❌ REQUIRES REWORK

Hex dump comparison of Sony baseline vs our output:

**Sony `baseline_lp2.at3.wav` (at3tool -e -br 132):**
```
00000000  52 49 46 46 C8 45 01 00  57 41 56 45 66 6D 74 20  RIFF...WAVEfmt
00000010  20 00 00 00 70 02 02 00  44 AC 00 00 9A 40 00 00   ...p...D....@..
00000020  80 01 00 00 0E 00 01 00  00 10 00 00 00 00 00 00  ................
00000030  01 00 00 00 66 61 63 74  0C 00 00 00 54 5D 03 00  ....fact....T]..
00000040  00 04 00 00 00 04 00 00  64 61 74 61 ...          ........data....
```

**Our `test_direct.wav` (atracdenc WAV output):**
```
00000000  52 49 46 46 D0 42 01 00  57 41 56 45 66 6D 74 20  RIFFDB..WAVEfmt
00000010  34 00 00 00 70 02 02 00  44 AC 00 00 99 40 00 00  4...p...D....@..
00000020  80 01 00 00 22 00 01 00  00 04 00 00 00 00 00 00  ...."...........
00000030  01 00 00 00 00 00 00 00  ...                      ................
00000040  00 00 00 00 00 00 00 00  64 61 74 61 ...          ........data....
```

**Differences requiring fixes:**

| Field | Sony | Ours | Fix |
|---|---|---|---|
| `fmt` subchunk size | `0x20` (32) = 18+**14** extradata | `0x34` (52) = 18+**34** | Shrink to **14-byte extradata**, remove 20-byte padding |
| `samples_per_block` (4-byte) | `0x00001000` = 4096 (=1024×2ch×2) | `0x00000400` = 1024 | Fix to `numSamples * numChannels * 2` |
| `fact` chunk | ✅ Present (total=220500 samples, 0x400, 0x400) | ❌ Missing | **Must add `fact` chunk** |
| 20-byte padding | Not present | Present (all zeros) | Remove |

### Bug 4 — OMA Frame Size Mismatch ✅ RESOLVED
Was 91,680 bytes (424-byte frames). Now 83,400 bytes (384-byte frames) after Bug 1 rebuild.

### Bug 5 — `TonalBlocks` Never Populated ⚠️ PHASE 4
`sce.TonalBlocks` is never filled in the ATRAC3 encode path. The tonal block bitstream section always writes `tcsgn=0`, wasting bits that could go to spectral quantization.

### Bug 6 — Bit Allocation Heuristics ⚠️ PHASE 5
`CalcBitsAllocation()` in `atrac3_bitstream.cpp` uses hand-tuned `x` divisors per frequency band. If post-fix SNR gap is > 5 dB, these need tuning against Sony's psych model.

---

## Proposed Changes

### Phase 2 — RIFF Header Fix [IMMEDIATE BLOCKER for SNR measurement]

#### [MODIFY] [at3.cpp](file:///c:/Users/Igland/Antigravity/Ghidra/atracdenc/src/at3.cpp)
1. Remove `uint8_t padding[20]` from `At3WaveHeader` struct.
2. Set `extradata_size` to **14** (`0x0E`).
3. Fix `samples_per_block` to `1024 * numChannels * 2` (= 4096 for stereo).
4. Add `fact` chunk fields to struct: `char fact_id[4]`, `uint32_t fact_size` (=12), `uint32_t total_samples` (= numFrames × 1024), `uint32_t fact_unknown_a` (=0x400), `uint32_t fact_unknown_b` (=0x400).
5. Serialize `fact` chunk between `fmt` and `data` in the constructor.
6. Update `subchunk1_size` = `offsetof(fact_id) - offsetof(audio_format)` = 32.

---

### Phase 3 — Quality Benchmarking

#### [EXECUTE] LP2 Sweep (after header fix + rebuild)
```powershell
python ghidra\reverse\quality\compare_at3_quality.py `
  --at3tool ghidra\reverse\windows\at3tool.exe `
  --atracdenc atracdenc\build\src\atracdenc.exe `
  --codec atrac3 --bitrate 132 `
  --workdir atracdenc\quality_run_lp2_v2 `
  --report atracdenc\quality_run_lp2_v2\report.md
```

#### [EXECUTE] LP4 Sweep (64 kbps, joint stereo)
```powershell
python ghidra\reverse\quality\compare_at3_quality.py `
  --at3tool ghidra\reverse\windows\at3tool.exe `
  --atracdenc atracdenc\build\src\atracdenc.exe `
  --codec atrac3 --bitrate 64 `
  --workdir atracdenc\quality_run_lp4_v1 `
  --report atracdenc\quality_run_lp4_v1\report.md
```

**Success criteria**: `at3tool -d` exit code **0**, SNR values non-None.

---

### Phase 4 — Tonal Spectral Suppression (Maximum Quality)

#### [MODIFY] [atrac3denc.cpp](file:///c:/Users/Igland/Antigravity/Ghidra/atracdenc/src/atrac3denc.cpp)
After `Mdct()`, scan the MDCT spectrum for tonal peaks (bins significantly above neighbors). Zero those bins before `ScaleFrame()` to prevent tonal energy being double-quantized as noise. Mirrors the suppress-then-encode pattern from `at3p.cpp` lines ~162–180.

#### [MODIFY] [atrac3_bitstream.cpp](file:///c:/Users/Igland/Antigravity/Ghidra/atracdenc/src/atrac/at3/atrac3_bitstream.cpp)
Port tonal component extraction and encoding so `sce.TonalBlocks` gets populated, fully utilizing the tonal section of the bitstream.

---

### Phase 5 — LP4-Specific Tuning

LP4 = 64 kbps, joint stereo (`Js=true`), 192-byte frames.
- Verify M/S matrixing path works correctly.
- Validate SNR vs `at3tool` LP4 baseline.
- May need separate `CalcBitsAllocation` constant tuning at LP4's tighter bit budget.

---

## Verification Scorecard

| Check | Target | Status |
|---|---|---|
| atracdenc reported bitrate (LP2) | 132300 bps | ✅ Confirmed |
| OMA frame size (5s stereo LP2) | ~83,400 bytes | ✅ Confirmed |
| `at3tool -d` exit code on our WAV output | 0 | ❌ Failing (header issue) |
| LP2 sine SNR | ~56.96 dB | ⏳ Blocked on header |
| LP2 multitone SNR | ~39.34 dB | ⏳ Blocked on header |
| LP2 transient SNR | ~45.74 dB | ⏳ Blocked on header |
| LP2 chirp SNR | ~24.14 dB | ⏳ Blocked on header |
| LP4 decode + SNR | TBD | ⏳ Not started |
