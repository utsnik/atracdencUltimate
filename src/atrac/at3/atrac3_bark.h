/*
 * This file is part of AtracDEnc.
 *
 * AtracDEnc is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * AtracDEnc is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with AtracDEnc; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
 */

#pragma once
#ifndef AT3_BARK_H_
#define AT3_BARK_H_

/*
 * Bark-scale BFU mapping for ATRAC3 LP2 psychoacoustic masking.
 *
 * The Bark scale is a perceptual frequency scale that approximates the
 * critical band resolution of the human auditory system.  Each critical band
 * is approximately 1 Bark wide; bands at the same Bark distance interact
 * strongly via simultaneous masking.
 *
 * These tables map each of the 32 ATRAC3 BFUs to its center frequency and
 * corresponding Bark value, enabling SMR (Signal-to-Mask Ratio) computation
 * for perceptual bit allocation.
 *
 * Derivation:
 *   freq_resolution = 44100 / (2 * 1024) = 21.533 Hz/coeff
 *   center_hz[i]    = midpoint_coeff[i] * freq_resolution
 *   bark[i]         = 13*atan(0.00076*f) + 3.5*atan((f/7500)^2)   (Zwicker formula)
 */

#include <cstdint>

namespace NAtrac3 {

// Center frequency (Hz) for each of the 32 ATRAC3 BFUs.
static constexpr float kBfuCenterHz[32] = {
     86.133f,   258.398f,   430.664f,   602.930f,
    775.195f,   947.461f,  1119.727f,  1291.992f,
   1550.391f,  1894.922f,  2239.453f,  2583.984f,
   2928.516f,  3273.047f,  3617.578f,  3962.109f,
   4478.906f,  5167.969f,  5857.031f,  6546.094f,
   7235.156f,  7924.219f,  8613.281f,  9302.344f,
   9991.406f, 10680.469f, 11714.062f, 13092.188f,
  14470.312f, 15848.438f, 17915.625f, 20671.875f,
};

// Bark value for each of the 32 ATRAC3 BFUs.
// Range: ~0.85 Bark (BFU 0, ~86 Hz) to ~24.6 Bark (BFU 31, ~20.7 kHz).
static constexpr float kBfuBark[32] = {
     0.8502f,  2.5251f,  4.1236f,  5.6084f,
     6.9586f,  8.1688f,  9.2439f, 10.1954f,
    11.4214f, 12.7532f, 13.8258f, 14.7110f,
    15.4603f, 16.1100f, 16.6854f, 17.2047f,
    17.9048f, 18.7309f, 19.4643f, 20.1202f,
    20.7049f, 21.2223f, 21.6769f, 22.0740f,
    22.4200f, 22.7212f, 23.1024f, 23.5062f,
    23.8207f, 24.0702f, 24.3579f, 24.6337f,
};

} // namespace NAtrac3

#endif // AT3_BARK_H_
