#pragma once
#include "atrac3.h"
#include "atrac3_bitstream.h"
#include <libgha/include/libgha.h>
#include <vector>
#include <memory>

namespace NAtracDEnc {
namespace NAtrac3 {

class TAtrac3GhaProcessor {
public:
    TAtrac3GhaProcessor();
    ~TAtrac3GhaProcessor();

    struct TTonalResult {
        std::vector<TTonalBlock> TonalBlocks;
        std::vector<bool> BfuIsTonal;
    };

    /**
     * @brief Extracts tonal components from a subband signal.
     * @param bandTimeData Time domain subband data (256 samples).
     * @param bandIndex Subband index (0-3).
     * @param allocator Bits allocation table (required for tonal grouping logic).
     * @param outTonalBlocks Vector to append extracted tonal blocks to.
     * @param outBfuIsTonal reference to array of 32 BFU flags.
     */
    void ExtractTones(float* bandTimeData, 
                     int bandIndex, 
                     const std::vector<uint32_t>& allocator,
                     std::vector<TTonalBlock>& outTonalBlocks,
                     std::vector<bool>& outBfuIsTonal);

private:
    gha_ctx_t LibGhaCtx;
    static constexpr int SAMPLES_PER_SUBBAND = 256;
};

} // namespace NAtrac3
} // namespace NAtracDEnc
