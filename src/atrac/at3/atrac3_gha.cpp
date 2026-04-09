#include "atrac3_gha.h"
#include <cmath>
#include <algorithm>
#include <cstring>

namespace NAtracDEnc {
namespace NAtrac3 {

TAtrac3GhaProcessor::TAtrac3GhaProcessor()
    : LibGhaCtx(gha_create_ctx(SAMPLES_PER_SUBBAND))
{
    gha_set_max_magnitude(LibGhaCtx, 32768.0f);
    gha_set_upsample(LibGhaCtx, 1);
}

TAtrac3GhaProcessor::~TAtrac3GhaProcessor()
{
    gha_free_ctx(LibGhaCtx);
}

void TAtrac3GhaProcessor::ExtractTones(float* bandTimeData, 
                                      int bandIndex, 
                                      const std::vector<uint32_t>& allocator,
                                      std::vector<TTonalBlock>& outTonalBlocks,
                                      std::vector<bool>& outBfuIsTonal)
{
    float buf[SAMPLES_PER_SUBBAND];
    memcpy(buf, bandTimeData, sizeof(float) * SAMPLES_PER_SUBBAND);

    // ATRAC3 LP2 typically uses between 4 and 8 tonal components total.
    // We'll extract a maximum of 1 strongest tone per subband for safety/parity testing.
    const int maxTonesPerBand = 1;
    struct gha_info infos[maxTonesPerBand];
    
    // Perform GHA extraction
    gha_extract_many_simple(buf, infos, maxTonesPerBand, LibGhaCtx);

    for (int i = 0; i < maxTonesPerBand; ++i) {
        if (infos[i].magnitude < 1.0f) continue; // Skip near-zero tones

        // Convert GHA frequency to 1024-range spectrum index
        // f is [0, PI]. Subband is 256 samples.
        // Bin in subband = (f / PI) * 255.
        // Global bin = subband_offset + (f / PI) * 255.
        float freq_norm = infos[i].frequency / M_PI;
        uint32_t localPos = static_cast<uint32_t>(std::round(freq_norm * 255.0f));
        uint32_t globalPos = bandIndex * 256 + localPos;

        // Match ATRAC3 BFU structure (32 BFUs total, variable sizes)
        uint8_t bfu = 0;
        const uint32_t* bpb = TAtrac3Data::BlocksPerBand;
        const uint32_t* bst = TAtrac3Data::SpecsStartLong;
        
        // Find BFU within this band
        for (uint32_t b = bpb[bandIndex]; b < bpb[bandIndex + 1]; ++b) {
            uint32_t bfuStart = bst[b] - (bandIndex * 256);
            uint32_t bfuEnd = bst[b+1] - (bandIndex * 256);
            if (localPos >= bfuStart && localPos < bfuEnd) {
                bfu = static_cast<uint8_t>(b);
                break;
            }
        }
        
        // Default to last BFU in band if not found
        if (bfu == 0 && localPos >= 128) bfu = bpb[bandIndex + 1] - 1; 

        // Magnitude to TScaleTable index
        // amp = 2^((idx-15)/3)  => idx = 3 * log2(amp) + 15
        float amp = infos[i].magnitude / 32768.0f; // Scale back if needed, but GHA works on raw PCM
        // Actually GHA works on whatever we give it. 
        // If we want it to match existing Scaler, we should treat it consistently.
        float idx_float = 3.0f * std::log2(std::max(amp, 1e-10f)) + 15.0f;
        int idx = static_cast<int>(std::round(idx_float));
        idx = std::max(0, std::min(63, idx));

        // Create TonalVal and TonalBlock
        TAtrac3Data::TTonalVal tv = { (uint16_t)globalPos, (double)infos[i].magnitude, bfu };
        
        // Tonal component usually spans ~3 bins but we encode it as a point with a scale factor.
        // For LP2 parity, we need to match how at3tool subtracts these.
        TScaledBlock sb(static_cast<uint8_t>(idx));
        sb.Values.push_back(1.0f); // Represent peak as 1.0 at quantized scale

        outTonalBlocks.emplace_back(tv, sb);
        outBfuIsTonal[bfu] = true;

        // Optimization: Subtract the tone from the time-domain signal to find residue
        // gha_extract_many_simple already does this to the 'buf' passed in.
    }
    
    // Final residue is copied back to bandTimeData so MDCT only processes the residue
    memcpy(bandTimeData, buf, sizeof(float) * SAMPLES_PER_SUBBAND); 
}

} // namespace NAtrac3
} // namespace NAtracDEnc
