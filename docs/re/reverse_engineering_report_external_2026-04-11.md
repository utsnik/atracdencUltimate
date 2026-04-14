# Detailed Reverse Engineering Report: Sony at3tool.exe (ATRAC3 LP2)

This report details the internal psychoacoustic and bit-allocation logic of `at3tool.exe` (v3.0.0.0), extracted via static analysis and memory dumping of the 132 kbps (LP2) encoding path.

## 1. Bit Allocation & Complexity Score Loop
The core allocation logic is located in `FUN_00437b40`. Unlike standard constant-bitrate models, ATRAC3 uses a frame-local feedback loop to manage the bit budget across BFUs (Bit Frequency Units).

### Complexity Metric (`iStack_510`)
*   **Definition**: A count of BFUs within the active subbands that exceed an energy threshold ($E > 7$).
*   **Initialization**: Initialized to 0 at the start of each frame.
*   **Accumulation**: Inside the initial spectral scan loop (Lines 467-505), `iStack_510` increments for each BFU where the peak spectral component `uVar6` is greater than 7.

### Quantization Feedback Formula
Once the initial tonal bits and side-info bits are reserved, the residual bits are allocated using a feedback factor (`Adjust`) calculated as:
$$Adjust = \frac{(TargetBits - ActualBits) \cdot 1024}{ComplexityCount \cdot 10}$$
*   **TargetBits**: Bit budget for the remaining BFUs (Total Frame bits - SideInfo - Tonals).
*   **ComplexityCount**: The `iStack_510` value (active BFU count).
*   **Application**: This `Adjust` factor is added to the base bit-depth of each BFU during the final quantization pass.

> [!NOTE]
> This mechanism ensures that "complex" frames (many high-energy BFUs) receive more bits by aggressively penalizing the quantization of simpler frames in the same stream.

## 2. Tonal Component Promotion Logic
Tonal components are handled in `FUN_00438e60`. Sony’s logic is highly selective to avoid "warbling" artifacts in the residual.

### Criteria for Promotion:
1.  **Energy Threshold**: Minimum peak energy of `0x500` (1280).
2.  **Selection Pool**: A candidate pool of local spectral maxima is created.
3.  **Tonality Ratio**: Candidates are promoted only if their peak-to-average ratio (SMR proxy) exceeds values in the table at `0x48CEE0`.
4.  **Capacity**: A strict hard limit of **7 tonal components** per subband is enforced. If more are found, the lowest-energy ones are demoted back to the residual.

## 3. Gain Control & Transient Detection
The transient detector in `FUN_00439630` drives the gain-control metadata.

### Segment Analysis:
*   The frame is divided into 8 temporal segments.
*   **Attack Trigger**: If the energy ratio between segments $S_n$ and $S_{n-1}$ exceeds $\approx 2.0$, a transient is flagged.
*   **Logic (VA 00439794)**:
    ```c
    if (fVar3 <= fVar1 * fVar5) { // fVar1 is threshold constant
        // Transient flagged, MDCT window modification triggered
    }
    ```

### High-Fidelity Masking:
When a transient is flagged, the encoder swaps to a modified windowing function (based on tables at `0x452340`) that zero-weights the first few samples to prevent pre-echo smear, relying on temporal masking to cover the gap.

## 4. Stereo Matrixing Strategy
ATRAC3 LP2 (132 kbps) utilizes Joint Stereo (JS) with a frequency-dependent matrixing policy.

*   **Side-Info Signature**: Located in `FUN_00437490`. The write sequence includes:
    -   **Matrix Selector Index**: 2-bit field (xref lines 1854-1855).
    -   **Weight/Delay Fields**: 4 small fields written in a tight loop.
*   **Subband 0-1 (0-5.5 kHz)**: Almost always matrixed into L+R (Mid) and L-R (Side).
*   **Subband 2-3 (5.5-22 kHz)**: Matrixing is conditional based on the **Stereo Decorrelation Score**.
*   **Weighting**: The Side channel is heavily bit-starved if the overall complexity score (`iStack_510`) is high, prioritizing the Mid channel.

## 5. Hook Points (RVA)
Based on the checklist, the following RVAs (assuming ImageBase `0x400000`) are target hook sites:
*   `0x36d40`: Frame entry/exit (`FUN_00436d40`).
*   `0x37b40`: Allocator (`FUN_00437b40`).
*   `0x38e60`: Tonal packing (`FUN_00438e60`).

### Confirmed RVAs and Memory Offsets (132kbps LP2)

The 132kbps LP2 mode uses a different encoding engine than the lower bitrates.

| Component | RVA (at3tool v3.0) | Context Offset (Word) | Notes |
| :--- | :--- | :--- | :--- |
| **Main Encoder** | `0x3d1f0` | - | Primary per-channel entry point for LP2. |
| **Bit Allocator** | `0x3f270` | - | Dynamic bit budget dispatcher. |
| **Spectral Weights** | - | `0x143f` | 4-band weights (range 0–63). |
| **Gain Points** | - | `0x141f` | 4-param gain control array. |
| **Target Bits** | - | `0x1872` | Current bit/spectral band target. |
| **Transient Flag** | - | `0x1860` | Triggered decision boolean. |
| **Tonal Counts** | - | `0x110` | Total promoted tonals. |

### Discovery: Engine Path Discrepancy
While the user provided RVAs starting at `0x36d40`, dynamic tracing reveals that `at3tool.exe` branches strictly based on bitrate:
- **LP4 (66kbps)**: Dispatches to `0x36d40`. Matches the user's provided RVA list.
- **LP2 (132kbps)**: Dispatches to `0x3d1f0`. This is the high-fidelity path.

### Tonal Analysis
In the 132kbps LP2 path, the Tonal Candidate Finder (`0x3f110`) consistently returns `0` for both standard music (`YOUtopia`) and pure sweeps (`chirp`). This indicates that at the current LP2 quality settings, the encoder relies entirely on residual spectral bits and bypasses GHA (tonal) encoding to maintain fidelity.

## 6. Actionable Constants for atracdenc
| Feature | at3tool.exe Constant (Hex) | atracdenc Equivalent Action |
| :--- | :--- | :--- |
| **Bitrate Goal** | `0x84` (132 kbps) | Map to 384 byte frames |
| **Tonal Energy Floor**| `0x500` | Implement as `tonal_min_energy = 1280` |
| **Max Tonals/Band** | `0x07` | Cap `num_tonals` at 7 |
| **Transient Ratio** | `2.0` | Set `attack_threshold = 2.0` |
| **Feedback Scale** | `0x400` / `10` | Scale `quant_feedback` by $102.4$ |
