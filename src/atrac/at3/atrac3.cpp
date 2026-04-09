#include "atrac3.h"
#include <algorithm>

namespace NAtracDEnc {
namespace NAtrac3 {

// Static constexpr members are initialized inline in atrac3.h (C++17)

// Definition is inline in the header for C++17 compatibility.
float TAtrac3Data::EncodeWindow[512] = {0};
float TAtrac3Data::DecodeWindow[512] = {0};
float TAtrac3Data::ScaleTable[64] = {0};
float TAtrac3Data::GainLevel[16];
float TAtrac3Data::GainInterpolation[31];

static const TAtrac3Data Atrac3Data;

const TContainerParams* TAtrac3Data::GetContainerParamsForBitrate(uint32_t bitrate) {
    if (bitrate < 1000) bitrate *= 1000;
    if (bitrate == 0) bitrate = 132300;
    
    // Explicitly handle standard Sony bitrates
    if (bitrate >= 130000 && bitrate <= 135168) return &ContainerParams[3];
    if (bitrate >= 60000 && bitrate <= 68000)   return &ContainerParams[0];

    int bestIdx = 0;
    uint32_t bestDiff = 0xFFFFFFFF;
    for (int i = 0; i < 8; ++i) {
        uint32_t b1 = ContainerParams[i].Bitrate;
        uint32_t diff = (b1 > bitrate) ? (b1 - bitrate) : (bitrate - b1);
        if (diff < bestDiff) {
            bestDiff = diff;
            bestIdx = i;
        }
    }
    return &ContainerParams[bestIdx];
}

} // namespace NAtrac3
} // namespace NAtracDEnc
