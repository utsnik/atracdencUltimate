# ATRAC3 (LP2 / LP4) Parity Task List

- `[x]` **Phase 1: Benchmarking Infrastructure**
    - `[x]` Update `compare_at3_quality.py` to support ATRAC3 (LP2/LP4)
    - `[x]` Generate baseline SNR report for ATRAC3 using `at3tool.exe`
- `[/]` **Phase 2: Signal Chain & Parameter Fix**
    - `[x]` Fix bitrate lookup (`* 1000` instead of `* 1024`) in `main.cpp`
    - `[x]` Adjust scaling to `/ 1.25` in `atrac3denc.cpp`
    - `[ ]` Verify SNR improvement for LP2
- `[/]` **Phase 3: RIFF Header Fix (Sony Parity)**
    - `[x]` Implement 34-byte extradata in `at3.cpp`
    - `[x]` Fix `bytes_per_frame` and padding for `at3tool` compatibility
    - `[ ]` Confirm that `at3tool -d` now works on `atracdenc` output
- `[ ]` **Phase 4: Tonal Spectral Suppression**
    - `[ ]` Implement MDCT bin zeroing for tonal components in `atrac3_bitstream.cpp`
    - `[ ]` Final quality sweep and verification
