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
#include "atrac3.h"
#include <compressed_io.h>
#include <atrac/atrac_scale.h>
#include <vector>
#include <utility>
#include <string>

namespace NBitStream {
    class TBitStream;
}

namespace NAtracDEnc {
namespace NAtrac3 {

struct TTonalBlock {
    TTonalBlock(const TAtrac3Data::TTonalVal* valPtr, const TScaledBlock& scaledBlock)
        : ValPtr(valPtr)
        , ScaledBlock(scaledBlock)
    {}
    const TAtrac3Data::TTonalVal* ValPtr = nullptr;
    TScaledBlock ScaledBlock;
};

class TAtrac3BitStreamWriter {
public:
    struct TParityBandAnalysis {
        float Energy = 0.0f;
        float MaskingThreshold = 0.0f;
        float Tonality = 0.0f;
        float Noisiness = 0.0f;
        float TransientScore = 0.0f;
        float DecayScore = 0.0f;
        float HfSalience = 0.0f;
        float SibilanceRisk = 0.0f;
        float StereoCoherence = 1.0f;
        float StereoSideRatio = 0.0f;
        float Stability = 1.0f;
    };
    struct TParityFrameAnalysis {
        TParityBandAnalysis Bands[TAtrac3Data::NumQMF];
        float FrameRisk = 0.0f;
        float StereoRisk = 0.0f;
        float Stability = 1.0f;
        float HfRisk = 0.0f;
        float MaxSibilanceRisk = 0.0f;
        float MaxHfSalience = 0.0f;
        float AttackRisk = 0.0f;
        float TonalRisk = 0.0f;
        float MSEnergyRatio = 0.0f;
        bool Valid = false;
    };
    struct TMlHints {
        float BfuBudgetBias = 0.0f;
        float TonalBias = 0.0f;
        float GainBias = 0.0f;
        float HfNoiseBias = 0.0f;
        float Confidence = 0.0f;
    };
    struct TSingleChannelElement {
        TAtrac3Data::SubbandInfo SubbandInfo;
        // Storage backing pointers used by TonalBlocks.
        std::vector<TAtrac3Data::TTonalVal> TonalVals;
        std::vector<TTonalBlock> TonalBlocks;
        std::vector<TScaledBlock> ScaledBlocks;
        float Loudness;
        // Per-band bit-allocation boost to compensate for gain-demodulation noise
        // amplification.  Combines the level boost (from the current frame's gain
        // curve) and the scale boost (estimated from the next frame's first gain
        // point).  Set by CreateSubbandInfo; read by CreateAllocation.
        int GainBoostPerBand[TAtrac3Data::NumQMF] = {};
        bool GainContinuityClamped[TAtrac3Data::NumQMF] = {};
        bool GainWeakTransientSuppressed[TAtrac3Data::NumQMF] = {};
        bool HfContinuityClamped[TAtrac3Data::NumQMF] = {};
        float GainTargetPrev[TAtrac3Data::NumQMF] = {};
        float GainTargetCur[TAtrac3Data::NumQMF] = {};
        uint8_t GainFirstLevelPrev[TAtrac3Data::NumQMF] = {};
        uint8_t GainFirstLevelCur[TAtrac3Data::NumQMF] = {};
        TMlHints MlHints;
        TParityFrameAnalysis ParityAnalysis;
    };
private:
    static std::vector<float> ATH;

    struct TTonalComponentsSubGroup {
        std::vector<uint8_t> SubGroupMap;
        std::vector<const TTonalBlock*> SubGroupPtr;
    };
    ICompressedOutput* Container;
    const TContainerParams Params;
    const uint32_t BfuIdxConst;
    const bool EnableParityAnalysis;
    const bool EnableParitySearch;
    const bool ForceLegacyV10Quality;
    const bool EnableStabilityMode;
    const bool EnableStereoExp;
    const bool EnableStereoBalanceExp;
    const bool EnableGainExp;
    const bool EnableGainExp2;
    const bool UseJointStereo;
    const uint32_t StartFrame;
    const uint32_t MaxFrames;
    std::ostream* DecisionLog;
    uint64_t FrameCounter = 0;
    float LastMsRatio = 0.0f;
    float LastMsPreserveSide = 0.0f;
    float LastMsHfRisk = 0.0f;
    bool ParityActiveThisFrame = false;
    bool DecisionLogActiveThisFrame = false;
    std::vector<char> OutBuffer;

    uint32_t CLCEnc(const uint32_t selector, const int mantissas[TAtrac3Data::MaxSpecsPerBlock],
                    const uint32_t blockSize, NBitStream::TBitStream* bitStream);

    uint32_t VLCEnc(const uint32_t selector, const int mantissas[TAtrac3Data::MaxSpecsPerBlock],
                    const uint32_t blockSize, NBitStream::TBitStream* bitStream);

    std::vector<uint32_t> CalcBitsAllocation(const std::vector<TScaledBlock>& scaledBlocks,
                                             uint32_t bfuNum, float spread, float shift, float loudness,
                                             const int gainBoostPerBand[TAtrac3Data::NumQMF],
                                             const TMlHints& hints,
                                             const TParityFrameAnalysis* parity = nullptr,
                                             float hfBias = 0.0f,
                                             float tonalBias = 0.0f,
                                             float transientBias = 0.0f,
                                             float gainScale = 1.0f);
    std::vector<uint32_t> CalcBitsAllocationLegacyV10(const std::vector<TScaledBlock>& scaledBlocks,
                                                      uint32_t bfuNum, float spread, float shift, float loudness,
                                                      const int gainBoostPerBand[TAtrac3Data::NumQMF],
                                                      const TParityFrameAnalysis* parity = nullptr);

    std::pair<uint8_t, std::vector<uint32_t>> CreateAllocation(const TSingleChannelElement& sce,
                                                               uint16_t targetBits, int mt[TAtrac3Data::MaxSpecs], float laudness);
    std::pair<uint8_t, std::vector<uint32_t>> CreateAllocationLegacyV10(const TSingleChannelElement& sce,
                                                                        uint16_t targetBits, int mt[TAtrac3Data::MaxSpecs], float laudness);

    std::pair<uint8_t, uint32_t> CalcSpecsBitsConsumption(const TSingleChannelElement& sce,
                                                          const std::vector<uint32_t>& precisionPerEachBlocks,
                                                          int* mantisas, std::vector<float>& energyErr);

    void EncodeSpecs(const TSingleChannelElement& sce, NBitStream::TBitStream* bitStream,
                     const std::pair<uint8_t, std::vector<uint32_t>>&, const int mt[TAtrac3Data::MaxSpecs]);

    uint8_t GroupTonalComponents(const std::vector<TTonalBlock>& tonalComponents,
                                 const std::vector<uint32_t>& allocTable,
                                 TTonalComponentsSubGroup groups[64]);

    uint16_t EncodeTonalComponents(const TSingleChannelElement& sce,
                                   const std::vector<uint32_t>& allocTable,
                                   NBitStream::TBitStream* bitStream);
public:
    TAtrac3BitStreamWriter(ICompressedOutput* container, const TContainerParams& params, uint32_t bfuIdxConst,
                           bool enableParityAnalysis = false,
                           bool enableParitySearch = false,
                           bool forceLegacyV10Quality = false,
                           bool enableStabilityMode = false,
                           bool enableStereoExp = false,
                           bool enableStereoBalanceExp = false,
                           bool enableGainExp = false,
                           bool enableGainExp2 = false,
                           uint32_t startFrame = 0,
                           uint32_t maxFrames = 0,
                           std::ostream* decisionLog = nullptr);

    void WriteSoundUnit(const std::vector<TSingleChannelElement>& singleChannelElements, float laudness);
};

} // namespace NAtrac3
} // namespace NAtracDEnc
