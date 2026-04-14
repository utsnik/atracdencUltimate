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

#include "atrac3_bitstream.h"
#include "qmf/qmf.h"
#include <atrac/atrac_psy_common.h>
#include <bitstream/bitstream.h>
#include <util.h>
#include <env.h>
#include <algorithm>
#include <iostream>
#include <vector>
#include <cstdlib>
#include <cmath>

#include <cstring>

namespace NAtracDEnc {
namespace NAtrac3 {

using std::vector;
using std::memset;

static const uint32_t FixedBitAllocTable[TAtrac3Data::MaxBfus] = {
  4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
  2, 2, 2, 2, 2, 1, 1, 1,
  1, 1, 1, 1,
  0, 0
};

#define EAQ 1

#ifdef EAQ

static constexpr size_t LOSY_NAQ_START = 18;
static constexpr size_t BOOST_NAQ_END = 10;

#else

static constexpr size_t LOSY_NAQ_START = 31;
static constexpr size_t BOOST_NAQ_END = 0;

#endif

std::vector<float> TAtrac3BitStreamWriter::ATH;
TAtrac3BitStreamWriter::TAtrac3BitStreamWriter(ICompressedOutput* container, const TContainerParams& params, uint32_t bfuIdxConst,
                                               bool enableParityAnalysis,
                                               bool enableParitySearch,
                                               bool forceLegacyV10Quality,
                                               bool enableStabilityMode,
                                               bool enableStereoExp,
                                               bool enableStereoBalanceExp,
                                               bool enableGainExp,
                                               bool enableGainExp2,
                                               uint32_t startFrame,
                                               uint32_t maxFrames,
                                               std::ostream* decisionLog)
    : Container(container)
    , Params(params)
    , BfuIdxConst(bfuIdxConst)
    , EnableParityAnalysis(enableParityAnalysis)
, EnableParitySearch(enableParitySearch)
, ForceLegacyV10Quality(forceLegacyV10Quality)
, EnableStabilityMode(enableStabilityMode)
, EnableStereoExp(enableStereoExp)
, EnableStereoBalanceExp(enableStereoBalanceExp)
, EnableGainExp(enableGainExp)
, EnableGainExp2(enableGainExp2)
, UseJointStereo(params.Js || enableStereoExp)
, StartFrame(startFrame)
, MaxFrames(maxFrames)
, DecisionLog(decisionLog)
{
    NEnv::SetRoundFloat();
    if (ATH.size()) {
        return;
    }

    ATH.reserve(TAtrac3Data::MaxBfus);
    auto ATHSpec = CalcATH(1024, 44100);
    for (size_t bandNum = 0; bandNum < TAtrac3Data::NumQMF; ++bandNum) {
        for (size_t blockNum = TAtrac3Data::BlocksPerBand[bandNum]; blockNum < TAtrac3Data::BlocksPerBand[bandNum + 1]; ++blockNum) {
            const size_t specNumStart =  TAtrac3Data::SpecsStartLong[blockNum];
            float x = 999;
            for (size_t line = specNumStart; line < specNumStart + TAtrac3Data::SpecsPerBlock[blockNum]; line++) {
                x = fmin(x, ATHSpec[line]);
            }
            x = pow(10, 0.1 * x);
            ATH.push_back(x);
        }
    }
}

namespace {
struct TParityCandidateProfile {
    const char* Name;
    float SpreadBias;
    float ShiftBias;
    int NumBfuBias;
    float HfBias;
    float TonalBias;
    float TransientBias;
    float GainScale;
};

static float Clamp01(float x) {
    return std::max(0.0f, std::min(1.0f, x));
}

static float CalcParityErrorPenalty(float err) {
    if (err <= 0.0f) {
        return 1.0f;
    }
    return std::abs(std::log2(std::max(err, 1e-6f)));
}

static uint32_t BfuBandFromIndex(uint32_t idx) {
    for (uint32_t band = 1; band < TAtrac3Data::NumQMF; ++band) {
        if (idx < TAtrac3Data::BlocksPerBand[band]) {
            return band - 1;
        }
    }
    return TAtrac3Data::NumQMF - 1;
}

static bool InFrameWindow(uint64_t frameNum, uint32_t startFrame, uint32_t maxFrames) {
    if (frameNum < startFrame) {
        return false;
    }
    if (maxFrames == 0) {
        return true;
    }
    const uint64_t endFrameExclusive = static_cast<uint64_t>(startFrame) + static_cast<uint64_t>(maxFrames);
    return frameNum < endFrameExclusive;
}

static const char* ClassifyRisk(const TAtrac3BitStreamWriter::TParityFrameAnalysis* parity) {
    if (!parity || !parity->Valid) {
        return "off";
    }
    float score = 0.0f;
    score += parity->FrameRisk * 2.0f;
    score += parity->HfRisk * 3.0f;
    score += parity->MaxSibilanceRisk * 2.0f;
    score += std::max(0.0f, parity->AttackRisk - 4.0f) * 0.25f;
    score += std::max(0.0f, parity->TonalRisk - 0.8f) * 0.5f;
    score += std::max(0.0f, 0.8f - parity->Stability) * 1.5f;
    if (score >= 2.4f) {
        return "high";
    }
    if (score >= 1.3f) {
        return "medium";
    }
    return "low";
}

enum class EParityBucket : uint8_t {
    AllocatorDriven = 0,
    StereoDriven = 1,
    GainTransientDriven = 2,
};

static const char* ParityBucketName(EParityBucket bucket) {
    switch (bucket) {
        case EParityBucket::StereoDriven:
            return "stereo-driven";
        case EParityBucket::GainTransientDriven:
            return "gain/transient-driven";
        case EParityBucket::AllocatorDriven:
        default:
            return "allocator-driven";
    }
}

static EParityBucket ClassifyParityBucket(const TAtrac3BitStreamWriter::TParityFrameAnalysis* parity) {
    if (!parity || !parity->Valid) {
        return EParityBucket::AllocatorDriven;
    }
    const bool stereoDriven =
        (parity->StereoRisk > 0.10f && (parity->HfRisk > 0.015f || parity->MSEnergyRatio > 0.05f))
        || (parity->MSEnergyRatio > 0.085f && parity->MaxSibilanceRisk > 0.010f);
    if (stereoDriven) {
        return EParityBucket::StereoDriven;
    }
    const bool gainTransientDriven =
        (parity->AttackRisk > 4.6f && parity->Stability < 0.78f)
        || (parity->AttackRisk > 5.2f && parity->HfRisk < 0.020f);
    if (gainTransientDriven) {
        return EParityBucket::GainTransientDriven;
    }
    return EParityBucket::AllocatorDriven;
}

static const char* ParityBucketReason(const TAtrac3BitStreamWriter::TParityFrameAnalysis* parity, EParityBucket bucket) {
    if (!parity || !parity->Valid) {
        return "no-parity-window";
    }
    switch (bucket) {
        case EParityBucket::StereoDriven:
            return "stereo_risk_or_ms_ratio";
        case EParityBucket::GainTransientDriven:
            return "attack_with_low_stability";
        case EParityBucket::AllocatorDriven:
        default:
            return "complexity_or_residual_pressure";
    }
}

// Candidate profile search is staged behind a hard runtime gate until
// multi-frame stability issues are fully resolved.
static constexpr bool kEnableExperimentalParitySearch = false;
}

uint32_t TAtrac3BitStreamWriter::CLCEnc(const uint32_t selector, const int mantissas[TAtrac3Data::MaxSpecsPerBlock],
                                        const uint32_t blockSize, NBitStream::TBitStream* bitStream)
{
    const uint32_t numBits = TAtrac3Data::ClcLengthTab[selector];
    const uint32_t bitsUsed = (selector > 1) ? numBits * blockSize : numBits * blockSize / 2;
    if (!bitStream)
        return bitsUsed;
    if (selector > 1) {
        for (uint32_t i = 0; i < blockSize; ++i) {
            bitStream->Write(NBitStream::MakeSign(mantissas[i], numBits), numBits);
        }
    } else {
        for (uint32_t i = 0; i < blockSize / 2; ++i) {
            uint32_t code = TAtrac3Data::MantissaToCLcIdx(mantissas[i * 2]) << 2;
            code |= TAtrac3Data::MantissaToCLcIdx(mantissas[i * 2 + 1]);
            ASSERT(numBits == 4);
            bitStream->Write(code, numBits);
        }
    }
    return bitsUsed;
}

uint32_t TAtrac3BitStreamWriter::VLCEnc(const uint32_t selector, const int mantissas[TAtrac3Data::MaxSpecsPerBlock],
                                        const uint32_t blockSize, NBitStream::TBitStream* bitStream)
{
    ASSERT(selector > 0);
    const TAtrac3Data::THuffEntry* huffTable = TAtrac3Data::HuffTables[selector - 1].Table;
    const uint8_t tableSz = TAtrac3Data::HuffTables[selector - 1].Sz;
    uint32_t bitsUsed = 0;
    if (selector > 1) {
        for (uint32_t i = 0; i < blockSize; ++i) {
            int m = mantissas[i];
            uint32_t huffS = (m < 0) ? (((uint32_t)(-m)) << 1) | 1 : ((uint32_t)m) << 1;
            if (huffS)
                huffS -= 1;
            ASSERT(huffS < 256);
            ASSERT(huffS < tableSz);
            bitsUsed += huffTable[huffS].Bits;
            if (bitStream)
                bitStream->Write(huffTable[huffS].Code, huffTable[huffS].Bits);
        }
    } else {
        ASSERT(tableSz == 9); 
        for (uint32_t i = 0; i < blockSize / 2; ++i) {
            const int ma = mantissas[i * 2];
            const int mb = mantissas[i * 2 + 1];
            const uint32_t huffS = TAtrac3Data::MantissasToVlcIndex(ma, mb);
            bitsUsed += huffTable[huffS].Bits;
            if (bitStream)
                bitStream->Write(huffTable[huffS].Code, huffTable[huffS].Bits);
        }
    }
    return bitsUsed;
}

std::pair<uint8_t, uint32_t> TAtrac3BitStreamWriter::CalcSpecsBitsConsumption(const TSingleChannelElement& sce,
    const vector<uint32_t>& precisionPerEachBlocks, int* mantisas, vector<float>& energyErr)
{

    const vector<TScaledBlock>& scaledBlocks = sce.ScaledBlocks;
    const uint32_t numBlocks = precisionPerEachBlocks.size();
    uint32_t bitsUsed = numBlocks * 3;

    auto lambda = [this, numBlocks, mantisas, &precisionPerEachBlocks, &scaledBlocks, &energyErr](bool clcMode, bool calcMant) {
        uint32_t bits = 0;
        for (uint32_t i = 0; i < numBlocks; ++i) {
            if (precisionPerEachBlocks[i] == 0)
                continue;
            bits += 6; //sfi
            const uint32_t first = TAtrac3Data::BlockSizeTab[i];
            const uint32_t last = TAtrac3Data::BlockSizeTab[i+1];
            const uint32_t blockSize = last - first;
            const float mul = TAtrac3Data::MaxQuant[std::min(precisionPerEachBlocks[i], (uint32_t)7)];
            if (calcMant) {
                const float* values = scaledBlocks[i].Values.data();
                energyErr[i] = QuantMantisas(values, first, last, mul, i > LOSY_NAQ_START, mantisas);
            }
            bits += clcMode ? CLCEnc(precisionPerEachBlocks[i], mantisas + first, blockSize, nullptr) :
                VLCEnc(precisionPerEachBlocks[i], mantisas + first, blockSize, nullptr);
        }
        return bits;
    };
    const uint32_t clcBits = lambda(true, true);
    const uint32_t vlcBits = lambda(false, false);
    bool mode = clcBits <= vlcBits;
    return std::make_pair(mode, bitsUsed + (mode ? clcBits : vlcBits));
}

//true - should reencode
//false - not need to
static inline bool CheckBfus(uint16_t* numBfu, const vector<uint32_t>& precisionPerEachBlocks)
{
    ASSERT(*numBfu);
    uint16_t curLastBfu = *numBfu - 1;
    //assert(curLastBfu < precisionPerEachBlocks.size());
    ASSERT(*numBfu == precisionPerEachBlocks.size());
    if (precisionPerEachBlocks[curLastBfu] == 0) {
        *numBfu = curLastBfu;
        return true;
    }
    return false;
}

static const std::pair<uint8_t, vector<uint32_t>> DUMMY_ALLOC{1, vector<uint32_t>{0}};

bool ConsiderEnergyErr(const vector<float>& err, vector<uint32_t>& bits)
{
    if (err.size() < bits.size()) {
        return false;
    }

    bool adjusted = false;
    size_t lim = std::min((size_t)BOOST_NAQ_END, bits.size());
    for (size_t i = 0; i < lim; i++) {
        float e = err[i];
        if (((e > 0 && e < 0.7) || e > 1.2) & (bits[i] < 7)) {
            //std::cerr << "adjust: " << i << " e: " << e << " b: " << bits[i] << std::endl;
            bits[i]++;
            adjusted = true;
        }
    }

    return adjusted;
}

std::pair<uint8_t, vector<uint32_t>> TAtrac3BitStreamWriter::CreateAllocation(const TSingleChannelElement& sce,
    const uint16_t targetBits, int mt[TAtrac3Data::MaxSpecs], float laudness)
{
    const vector<TScaledBlock>& scaledBlocks = sce.ScaledBlocks;
    if (scaledBlocks.empty()) {
        return DUMMY_ALLOC;
    }
    if (ForceLegacyV10Quality) {
        return CreateAllocationLegacyV10(sce, targetBits, mt, laudness);
    }

    const bool parityPolicyActive = ParityActiveThisFrame && !ForceLegacyV10Quality;
    const TParityFrameAnalysis* parity = (parityPolicyActive && sce.ParityAnalysis.Valid)
        ? &sce.ParityAnalysis : nullptr;
    const float spread = AnalizeScaleFactorSpread(scaledBlocks);

    // Per-band bit-allocation boost pre-computed by CreateSubbandInfo.
    // Combines level boost (current frame's gain curve) and scale boost
    // (estimated next frame's first gain point).
    const int* gainBoostPerBand = sce.GainBoostPerBand;

    uint16_t tonalMinBfu = 1;
    for (const auto& tonal : sce.TonalBlocks) {
        tonalMinBfu = std::max<uint16_t>(tonalMinBfu, static_cast<uint16_t>(tonal.ValPtr->Bfu + 1));
    }

    uint16_t seedNumBfu = BfuIdxConst ? BfuIdxConst : 32;
    if (!BfuIdxConst && Params.Bitrate <= 132300) {
        // LP2 favors spending bits earlier in the spectrum; a smaller BFU
        // search space tends to improve effective precision for this mode.
        seedNumBfu = 24;
        if (spread > 0.80f) {
            seedNumBfu = 32;
        } else if (spread > 0.65f) {
            seedNumBfu = 28;
        }
    }
    if (!BfuIdxConst && !ForceLegacyV10Quality && sce.MlHints.Confidence >= 0.5f) {
        const int delta = (int)std::lround(std::max(-4.0f, std::min(4.0f, sce.MlHints.BfuBudgetBias * 2.0f)));
        const int adjusted = std::max(8, std::min(32, (int)seedNumBfu + delta));
        seedNumBfu = (uint16_t)adjusted;
    }
    if (!BfuIdxConst && parity) {
        const int parityDelta = (parity->FrameRisk > 0.26f ? 4 : 0)
                              + (parity->HfRisk > 0.08f ? 2 : 0)
                              + (parity->Stability < 0.70f ? 2 : 0);
        seedNumBfu = static_cast<uint16_t>(std::max(8, std::min(32, (int)seedNumBfu + parityDelta)));
    }
    seedNumBfu = std::max(seedNumBfu, tonalMinBfu);

    // Limit number of BFU if target bitrate is not enough
    // 3 bits to write each bfu without data
    // 5 bits we need for tonal header
    // 32 * 3 + 5 = 101
    uint16_t maxNumBfu = seedNumBfu;
    if (targetBits < 101) {
        uint16_t lim = (targetBits - 5) / 3;
        maxNumBfu = std::min(seedNumBfu, lim);
    }
    maxNumBfu = std::max(maxNumBfu, tonalMinBfu);
    if (DecisionLogActiveThisFrame) {
        *DecisionLog << "create_allocation: {spread: " << spread
                     << ", target_bits: " << targetBits
                     << ", num_bfu_seed: " << maxNumBfu;
        if (parity) {
            *DecisionLog << ", risk_class: " << ClassifyRisk(parity)
                         << ", max_sibilance_risk: " << parity->MaxSibilanceRisk
                         << ", max_hf_salience: " << parity->MaxHfSalience;
            *DecisionLog << ", frame_risk: " << parity->FrameRisk
                         << ", hf_risk: " << parity->HfRisk
                         << ", attack_risk: " << parity->AttackRisk
                         << ", tonal_risk: " << parity->TonalRisk
                         << ", stability: " << parity->Stability;
        }
        *DecisionLog << "}\n";
    }

    if (!parity) {
        uint16_t numBfu = maxNumBfu;
        vector<uint32_t> precisionPerEachBlocks(numBfu);
        vector<float> energyErr(numBfu);
        uint8_t mode = 1;
        bool cont = true;
        while (cont) {
            precisionPerEachBlocks.resize(numBfu);
            double maxShift = 20.0;
            double minShift = -8.0;
            for (int iter = 0; iter < 96; ++iter) {
                const double shift = (maxShift + minShift) / 2.0;
                vector<uint32_t> tmpAlloc = CalcBitsAllocation(scaledBlocks, numBfu, spread, (float)shift, laudness,
                                                               gainBoostPerBand, sce.MlHints);
                energyErr.assign(numBfu, 1.0f);
                std::pair<uint8_t, uint32_t> consumption;
                do {
                    consumption = CalcSpecsBitsConsumption(sce, tmpAlloc, mt, energyErr);
                } while (ConsiderEnergyErr(energyErr, tmpAlloc));

                consumption.second += EncodeTonalComponents(sce, tmpAlloc, nullptr);
                if (iter == 95) {
                    precisionPerEachBlocks = tmpAlloc;
                    mode = consumption.first;
                    cont = false;
                    break;
                }
                if (consumption.second < targetBits) {
                    if (maxShift - minShift < 0.1) {
                        precisionPerEachBlocks = tmpAlloc;
                        mode = consumption.first;
                        if (numBfu > 1) {
                            cont = !BfuIdxConst && CheckBfus(&numBfu, precisionPerEachBlocks);
                            if (numBfu < tonalMinBfu) {
                                numBfu = tonalMinBfu;
                                cont = false;
                            }
                        } else {
                            cont = false;
                        }
                        break;
                    }
                    maxShift = shift - 0.01;
                } else if (consumption.second > targetBits) {
                    minShift = shift + 0.01;
                } else {
                    precisionPerEachBlocks = tmpAlloc;
                    mode = consumption.first;
                    cont = !BfuIdxConst && CheckBfus(&numBfu, precisionPerEachBlocks);
                    if (numBfu < tonalMinBfu) {
                        numBfu = tonalMinBfu;
                        cont = false;
                    }
                    break;
                }
            }
        }
        if (DecisionLogActiveThisFrame) {
            *DecisionLog << "allocation_choice: {profile: legacy, num_bfu: " << precisionPerEachBlocks.size() << "}\n";
        }
        return { mode, precisionPerEachBlocks };
    }

    std::pair<uint8_t, vector<uint32_t>> safeParityAllocation = DUMMY_ALLOC;
    float safeHfBias = 0.0f;
    float safeTonalBias = 0.0f;
    float safeTransientBias = 0.0f;
    float safeGainScale = 1.0f;
    {
        uint16_t numBfu = maxNumBfu;
        vector<uint32_t> precisionPerEachBlocks(numBfu);
        vector<float> energyErr(numBfu);
        uint8_t mode = 1;
        safeHfBias = std::max(-0.25f, std::min(1.35f,
            parity->HfRisk * 10.0f +
            parity->MaxSibilanceRisk * 1.6f +
            std::max(0.0f, parity->MaxHfSalience - 0.08f) * 3.5f));
        safeTonalBias = std::max(-0.15f, std::min(0.95f,
            (parity->TonalRisk - 0.80f) * 0.90f +
            parity->MaxSibilanceRisk * 0.20f));
        safeTransientBias = std::max(-0.20f, std::min(1.00f,
            (parity->AttackRisk - 3.8f) * 0.24f +
            parity->MaxSibilanceRisk * 0.35f));
        safeGainScale = std::max(0.88f, std::min(1.22f,
            0.94f + safeTransientBias * 0.11f + parity->MaxSibilanceRisk * 0.08f));

        bool cont = true;
        while (cont) {
            precisionPerEachBlocks.resize(numBfu);
            double maxShift = 20.0;
            double minShift = -8.0;
            for (int iter = 0; iter < 96; ++iter) {
                const double shift = (maxShift + minShift) / 2.0;
                vector<uint32_t> tmpAlloc = CalcBitsAllocation(scaledBlocks, numBfu, spread, (float)shift, laudness,
                                                               gainBoostPerBand, sce.MlHints, parity,
                                                               safeHfBias, safeTonalBias, safeTransientBias, safeGainScale);
                energyErr.assign(numBfu, 1.0f);
                std::pair<uint8_t, uint32_t> consumption;
                do {
                    consumption = CalcSpecsBitsConsumption(sce, tmpAlloc, mt, energyErr);
                } while (ConsiderEnergyErr(energyErr, tmpAlloc));

                consumption.second += EncodeTonalComponents(sce, tmpAlloc, nullptr);
                if (iter == 95) {
                    precisionPerEachBlocks = tmpAlloc;
                    mode = consumption.first;
                    cont = false;
                    break;
                }
                if (consumption.second < targetBits) {
                    if (maxShift - minShift < 0.1) {
                        precisionPerEachBlocks = tmpAlloc;
                        mode = consumption.first;
                        if (numBfu > 1) {
                            cont = !BfuIdxConst && CheckBfus(&numBfu, precisionPerEachBlocks);
                            if (numBfu < tonalMinBfu) {
                                numBfu = tonalMinBfu;
                                cont = false;
                            }
                        } else {
                            cont = false;
                        }
                        break;
                    }
                    maxShift = shift - 0.01;
                } else if (consumption.second > targetBits) {
                    minShift = shift + 0.01;
                } else {
                    precisionPerEachBlocks = tmpAlloc;
                    mode = consumption.first;
                    cont = !BfuIdxConst && CheckBfus(&numBfu, precisionPerEachBlocks);
                    if (numBfu < tonalMinBfu) {
                        numBfu = tonalMinBfu;
                        cont = false;
                    }
                    break;
                }
            }
        }

        safeParityAllocation = { mode, precisionPerEachBlocks };
    }

    const bool runCandidateSearch = kEnableExperimentalParitySearch && parity && EnableParitySearch && (
        parity->FrameRisk > 0.24f ||
        parity->HfRisk > 0.09f ||
        parity->MaxSibilanceRisk > 0.18f ||
        parity->AttackRisk > 4.20f ||
        parity->TonalRisk > 0.80f ||
        parity->Stability < 0.72f);

    if (DecisionLogActiveThisFrame) {
        *DecisionLog << "allocation_choice: {profile: parity_safe, num_bfu: " << safeParityAllocation.second.size()
                     << ", hf_bias: " << safeHfBias
                     << ", tonal_bias: " << safeTonalBias
                     << ", transient_bias: " << safeTransientBias
                     << ", gain_scale: " << safeGainScale
                     << ", max_sibilance_risk: " << parity->MaxSibilanceRisk
                     << ", max_hf_salience: " << parity->MaxHfSalience
                     << ", candidate_search: " << (runCandidateSearch ? "true" : "false") << "}\n";
    }

    if (!runCandidateSearch) {
        return safeParityAllocation;
    }

    struct TResult {
        std::pair<uint8_t, vector<uint32_t>> Allocation = DUMMY_ALLOC;
        vector<float> EnergyErr;
        float Score = 1e30f;
        float FinalShift = 0.0f;
        uint16_t FinalNumBfu = 0;
        const char* Profile = "base";
    };

    std::vector<TParityCandidateProfile> profiles = {
        {"base", 0.0f, 0.0f, 0, 0.0f, 0.0f, 0.0f, 1.0f},
    };
    if (parity) {
        profiles.push_back({"stable", -0.03f, 0.15f, 0, -0.10f, 0.15f, 0.05f, 0.85f});
        if (parity->HfRisk > 0.08f || parity->FrameRisk > 0.20f) {
            profiles.push_back({"hf_guard", 0.04f, -0.35f, 2, 1.10f, 0.15f, 0.25f, 1.00f});
        }
        if (parity->AttackRisk > 3.0f) {
            profiles.push_back({"attack_focus", 0.03f, -0.25f, 1, 0.35f, 0.10f, 1.10f, 1.20f});
        }
        if (parity->TonalRisk > 0.60f) {
            profiles.push_back({"tonal_hold", 0.01f, -0.20f, 1, 0.15f, 1.10f, 0.25f, 1.00f});
        }
        if (parity->FrameRisk > 0.28f) {
            profiles.push_back({"wide_bfu", 0.05f, -0.30f, 4, 0.80f, 0.45f, 0.45f, 1.10f});
        }
    }

    auto scoreAllocation = [&](const TParityCandidateProfile& profile,
                               const vector<uint32_t>& alloc,
                               const vector<float>& energyErr,
                               uint32_t bitsUsed) {
        float score = 0.0f;
        float bandAlloc[TAtrac3Data::NumQMF] = {};
        float bandCount[TAtrac3Data::NumQMF] = {};
        for (size_t i = 0; i < alloc.size(); ++i) {
            const uint32_t band = BfuBandFromIndex((uint32_t)i);
            bandAlloc[band] += static_cast<float>(alloc[i]);
            bandCount[band] += 1.0f;
            float weight = 1.0f;
            if (parity) {
                const auto& pb = parity->Bands[band];
                weight += 1.50f * pb.HfSalience
                        + 1.20f * pb.SibilanceRisk
                        + 0.80f * pb.Tonality
                        + 0.70f * Clamp01(pb.TransientScore / 4.0f)
                        + 0.50f * (1.0f - pb.Stability)
                        + 0.35f * (1.0f - pb.StereoCoherence) * pb.StereoSideRatio;
                if (pb.Energy < pb.MaskingThreshold) {
                    weight *= 0.70f;
                }
            }
            score += CalcParityErrorPenalty(energyErr[i]) * weight;
        }

        if (parity) {
            const float hfAlloc = (bandAlloc[2] / std::max(1.0f, bandCount[2]) +
                                   bandAlloc[3] / std::max(1.0f, bandCount[3])) * 0.5f;
            const float attackAlloc = (bandAlloc[0] / std::max(1.0f, bandCount[0]) +
                                       bandAlloc[1] / std::max(1.0f, bandCount[1])) * 0.5f;
            score += std::max(0.0f, parity->HfRisk * 3.0f - hfAlloc * 0.22f);
            score += std::max(0.0f, parity->AttackRisk * 0.25f - attackAlloc * 0.18f);
            score += std::max(0.0f, parity->TonalRisk * 1.2f - static_cast<float>(sce.TonalBlocks.size()) * 0.04f);
            score += (1.0f - parity->Stability) * 0.8f * std::abs(profile.ShiftBias);
        }

        score += std::abs(static_cast<int32_t>(targetBits) - static_cast<int32_t>(bitsUsed)) * 0.0035f;
        return score;
    };

    auto evaluateProfile = [&](const TParityCandidateProfile& profile) {
        TResult best;
        uint16_t numBfu = static_cast<uint16_t>(std::max<int>(tonalMinBfu, std::min(32, (int)maxNumBfu + profile.NumBfuBias)));
        bool cont = true;
        while (cont) {
            vector<uint32_t> precisionPerEachBlocks(numBfu);
            vector<float> energyErr(numBfu);
            uint8_t mode = 1;
            float resolvedShift = 0.0f;
            double maxShift = 20.0;
            double minShift = -8.0;
            for (int iter = 0; iter < 96; ++iter) {
                const double rawShift = (maxShift + minShift) / 2.0;
                const double evalShift = rawShift + profile.ShiftBias;
                const float spreadEval = std::max(0.10f, std::min(0.95f, spread + profile.SpreadBias));
                vector<uint32_t> tmpAlloc = CalcBitsAllocation(scaledBlocks, numBfu, spreadEval, (float)evalShift,
                                                               laudness, gainBoostPerBand, sce.MlHints,
                                                               parity, profile.HfBias, profile.TonalBias,
                                                               profile.TransientBias, profile.GainScale);
                energyErr.assign(numBfu, 1.0f);
                std::pair<uint8_t, uint32_t> consumption;
                do {
                    consumption = CalcSpecsBitsConsumption(sce, tmpAlloc, mt, energyErr);
                } while (ConsiderEnergyErr(energyErr, tmpAlloc));

                consumption.second += EncodeTonalComponents(sce, tmpAlloc, nullptr);
                if (iter == 95) {
                    precisionPerEachBlocks = tmpAlloc;
                    mode = consumption.first;
                    resolvedShift = (float)evalShift;
                    cont = false;
                    break;
                }

                if (consumption.second < targetBits) {
                    if (maxShift - minShift < 0.1) {
                        precisionPerEachBlocks = tmpAlloc;
                        mode = consumption.first;
                        resolvedShift = (float)evalShift;
                        if (numBfu > 1) {
                            cont = !BfuIdxConst && CheckBfus(&numBfu, precisionPerEachBlocks);
                            if (numBfu < tonalMinBfu) {
                                numBfu = tonalMinBfu;
                                cont = false;
                            }
                        } else {
                            cont = false;
                        }
                        break;
                    }
                    maxShift = rawShift - 0.01;
                } else if (consumption.second > targetBits) {
                    minShift = rawShift + 0.01;
                } else {
                    precisionPerEachBlocks = tmpAlloc;
                    mode = consumption.first;
                    resolvedShift = (float)evalShift;
                    cont = !BfuIdxConst && CheckBfus(&numBfu, precisionPerEachBlocks);
                    if (numBfu < tonalMinBfu) {
                        numBfu = tonalMinBfu;
                        cont = false;
                    }
                    break;
                }
            }

            const uint32_t tonalBits = EncodeTonalComponents(sce, precisionPerEachBlocks, nullptr);
            energyErr.assign(precisionPerEachBlocks.size(), 1.0f);
            auto consumption = CalcSpecsBitsConsumption(sce, precisionPerEachBlocks, mt, energyErr);
            const uint32_t usedBits = consumption.second + tonalBits;
            const float score = scoreAllocation(profile, precisionPerEachBlocks, energyErr, usedBits);
            if (score < best.Score) {
                best.Score = score;
                best.Allocation = {mode, precisionPerEachBlocks};
                best.EnergyErr = energyErr;
                best.FinalShift = resolvedShift;
                best.FinalNumBfu = numBfu;
                best.Profile = profile.Name;
            }
        }
        return best;
    };

    TResult best;
    for (const auto& profile : profiles) {
        TResult candidate = evaluateProfile(profile);
        if (candidate.Score < best.Score) {
            best = std::move(candidate);
        }
    }

    if (best.Allocation.second.empty()) {
        return safeParityAllocation;
    }

    if (DecisionLogActiveThisFrame) {
        *DecisionLog << "allocation_choice: {profile: " << best.Profile
                     << ", score: " << best.Score
                     << ", shift: " << best.FinalShift
                     << ", num_bfu: " << best.FinalNumBfu << "}\n";
    }
    return best.Allocation;
}

std::pair<uint8_t, vector<uint32_t>> TAtrac3BitStreamWriter::CreateAllocationLegacyV10(const TSingleChannelElement& sce,
    const uint16_t targetBits, int mt[TAtrac3Data::MaxSpecs], float laudness)
{
    const vector<TScaledBlock>& scaledBlocks = sce.ScaledBlocks;
    const float spread = AnalizeScaleFactorSpread(scaledBlocks);
    const int* gainBoostPerBand = sce.GainBoostPerBand;
    const TParityFrameAnalysis* parity = (EnableStabilityMode && ParityActiveThisFrame && sce.ParityAnalysis.Valid)
        ? &sce.ParityAnalysis : nullptr;

    uint16_t numBfu = BfuIdxConst ? BfuIdxConst : 32;
    const bool hfFrameBoost = parity
        && parity->HfRisk > 0.010f
        && parity->MaxSibilanceRisk > 0.030f
        && parity->Stability < 0.90f;

    if (!BfuIdxConst && Params.Bitrate <= 132300) {
        numBfu = 24;
        if (spread > 0.80f) {
            numBfu = 32;
        } else if (spread > 0.65f) {
            numBfu = 28;
        }
        if (hfFrameBoost) {
            const int hfBfuBoost = (numBfu <= 24) ? 4 : 2;
            numBfu = static_cast<uint16_t>(std::min(32, static_cast<int>(numBfu) + hfBfuBoost));
        }
    }

    if (targetBits < 101) {
        const uint16_t lim = (targetBits - 5) / 3;
        numBfu = std::min(numBfu, lim);
    }

    if (DecisionLogActiveThisFrame) {
        *DecisionLog << "create_allocation: {spread: " << spread
                     << ", target_bits: " << targetBits
                     << ", num_bfu_seed: " << numBfu
                     << ", hf_frame_boost: " << (hfFrameBoost ? "true" : "false")
                     << ", profile: legacy_v10}\n";
    }

    vector<uint32_t> precisionPerEachBlocks(numBfu);
    vector<float> energyErr(numBfu);
    uint8_t mode = 1;
    bool cont = true;
    while (cont) {
        precisionPerEachBlocks.resize(numBfu);
        double maxShift = 20.0;
        double minShift = -8.0;
        for (;;) {
            const double shift = (maxShift + minShift) / 2.0;
            vector<uint32_t> tmpAlloc = CalcBitsAllocationLegacyV10(scaledBlocks, numBfu, spread, (float)shift,
                                                                    laudness, gainBoostPerBand, parity);
            energyErr.assign(numBfu, 1.0f);
            std::pair<uint8_t, uint32_t> consumption;
            do {
                consumption = CalcSpecsBitsConsumption(sce, tmpAlloc, mt, energyErr);
            } while (ConsiderEnergyErr(energyErr, tmpAlloc));

            consumption.second += EncodeTonalComponents(sce, tmpAlloc, nullptr);
            if (consumption.second < targetBits) {
                if (maxShift - minShift < 0.1) {
                    precisionPerEachBlocks = tmpAlloc;
                    mode = consumption.first;
                    if (numBfu > 1) {
                        cont = !BfuIdxConst && CheckBfus(&numBfu, precisionPerEachBlocks);
                    } else {
                        cont = false;
                    }
                    break;
                }
                maxShift = shift - 0.01;
            } else if (consumption.second > targetBits) {
                minShift = shift + 0.01;
            } else {
                precisionPerEachBlocks = tmpAlloc;
                mode = consumption.first;
                cont = !BfuIdxConst && CheckBfus(&numBfu, precisionPerEachBlocks);
                break;
            }
        }
    }
    if (DecisionLogActiveThisFrame) {
        *DecisionLog << "allocation_choice: {profile: legacy_v10, num_bfu: "
                     << precisionPerEachBlocks.size() << "}\n";
    }
    return { mode, precisionPerEachBlocks };
}

void TAtrac3BitStreamWriter::EncodeSpecs(const TSingleChannelElement& sce, NBitStream::TBitStream* bitStream,
    const std::pair<uint8_t, vector<uint32_t>>& allocation, const int mt[TAtrac3Data::MaxSpecs])
{

    const vector<TScaledBlock>& scaledBlocks = sce.ScaledBlocks;
    const vector<uint32_t>& precisionPerEachBlocks = allocation.second;
    EncodeTonalComponents(sce, precisionPerEachBlocks, bitStream);
    const uint32_t numBlocks = precisionPerEachBlocks.size(); //number of blocks to save
    const uint32_t codingMode = allocation.first;//0 - VLC, 1 - CLC

    ASSERT(numBlocks <= 32);
    bitStream->Write(numBlocks-1, 5);
    bitStream->Write(codingMode, 1);
    for (uint32_t i = 0; i < numBlocks; ++i) {
        uint32_t val = precisionPerEachBlocks[i]; //coding table used (VLC) or number of bits used (CLC)
        bitStream->Write(val, 3);
    }
    for (uint32_t i = 0; i < numBlocks; ++i) {
        if (precisionPerEachBlocks[i] == 0)
            continue;
        bitStream->Write(scaledBlocks[i].ScaleFactorIndex, 6);
    }
    for (uint32_t i = 0; i < numBlocks; ++i) {
        if (precisionPerEachBlocks[i] == 0)
            continue;

        const uint32_t first = TAtrac3Data::BlockSizeTab[i];
        const uint32_t last = TAtrac3Data::BlockSizeTab[i+1];
        const uint32_t blockSize = last - first;

        if (codingMode == 1) {
            CLCEnc(precisionPerEachBlocks[i], mt + first, blockSize, bitStream);
        } else {
            VLCEnc(precisionPerEachBlocks[i], mt + first, blockSize, bitStream);
        }
    }
}

uint8_t TAtrac3BitStreamWriter::GroupTonalComponents(const std::vector<TTonalBlock>& tonalComponents,
                                                     const vector<uint32_t>& allocTable,
                                                     TTonalComponentsSubGroup groups[64])
{
    for (const TTonalBlock& tc : tonalComponents) {
        if (tc.ScaledBlock.Values.empty() || tc.ScaledBlock.Values.size() >= 8) {
            continue;
        }
        if (tc.ValPtr->Bfu >= allocTable.size()) {
            continue;
        }
        auto quant = std::max((uint32_t)2, std::min(allocTable[tc.ValPtr->Bfu] + 1, (uint32_t)7));
        //std::cerr << " | " << tc.ValPtr->Pos << " | " << (int)tc.ValPtr->Bfu << " | " << quant << std::endl;
        groups[quant * 8 + tc.ScaledBlock.Values.size()].SubGroupPtr.push_back(&tc);
    }

    //std::cerr << "=====" << std::endl;
    uint8_t tcsgn = 0;
    //for each group
    for (uint8_t i = 0; i < 64; ++i) {
        size_t start_pos;
        size_t cur_pos = 0;
        //scan tonal components
        while (cur_pos < groups[i].SubGroupPtr.size()) {
            start_pos = cur_pos;
            if (tcsgn >= 31) {
                return tcsgn;
            }
            ++tcsgn;
            groups[i].SubGroupMap.push_back(static_cast<uint8_t>(cur_pos));
            uint8_t groupLimiter = 0;
            //allow not grather than 8 components in one subgroup limited by 64 specs
            do {
                ++cur_pos;
                if (cur_pos == groups[i].SubGroupPtr.size())
                    break;
                if (groups[i].SubGroupPtr[cur_pos]->ValPtr->Pos - (groups[i].SubGroupPtr[start_pos]->ValPtr->Pos & ~63) < 64) {
                    ++groupLimiter;
                } else {
                    groupLimiter = 0;
                    start_pos = cur_pos;
                }
            } while (groupLimiter < 7);
        }
    }
    return tcsgn;
}

uint16_t TAtrac3BitStreamWriter::EncodeTonalComponents(const TSingleChannelElement& sce,
                                                       const vector<uint32_t>& allocTable,
                                                       NBitStream::TBitStream* bitStream)
{
    const uint16_t bitsUsedOld = bitStream ? (uint16_t)bitStream->GetSizeInBits() : 0;
    const std::vector<TTonalBlock>& tonalComponents = sce.TonalBlocks;
    const TAtrac3Data::SubbandInfo& subbandInfo = sce.SubbandInfo;
    const uint8_t numQmfBand = subbandInfo.GetQmfNum();
    uint16_t bitsUsed = 0;

    //group tonal components with same quantizer and len
    TTonalComponentsSubGroup groups[64];
    const uint8_t tcsgn = GroupTonalComponents(tonalComponents, allocTable, groups);

    ASSERT(tcsgn < 32);

    bitsUsed += 5;
    if (bitStream)
        bitStream->Write(tcsgn, 5);

    if (tcsgn == 0) {
        for (int i = 0; i < 64; ++i)
            ASSERT(groups[i].SubGroupPtr.size() == 0);
        return bitsUsed;
    }
    //Coding mode:
    // 0 - All are VLC
    // 1 - All are CLC
    // 2 - Error
    // 3 - Own mode for each component

    //TODO: implement switch for best coding mode. Now VLC for all
    bitsUsed += 2;
    if (bitStream)
        bitStream->Write(0, 2);

    uint8_t tcgnCheck = 0;
    //for each group of equal quantiser and len 
    for (size_t i = 0; i < 64; ++i) {
        const TTonalComponentsSubGroup& curGroup = groups[i];
        if (curGroup.SubGroupPtr.size() == 0) {
            ASSERT(curGroup.SubGroupMap.size() == 0);
            continue;
        }
        ASSERT(curGroup.SubGroupMap.size());
        ASSERT(curGroup.SubGroupMap.size() < UINT8_MAX);
        for (size_t subgroup = 0; subgroup < curGroup.SubGroupMap.size(); ++subgroup) {
            const uint8_t subGroupStartPos = curGroup.SubGroupMap[subgroup];
            const uint8_t subGroupEndPos = (subgroup < curGroup.SubGroupMap.size() - 1) ?
                curGroup.SubGroupMap[subgroup+1] : (uint8_t)curGroup.SubGroupPtr.size();
            ASSERT(subGroupEndPos > subGroupStartPos);
            //number of coded values are same in group
            const uint8_t codedValues = (uint8_t)curGroup.SubGroupPtr[0]->ScaledBlock.Values.size();

            //Number of tonal component for each 64spec block. Used to set qmf band flags and simplify band encoding loop
            union {
                uint8_t c[16];
                uint32_t i[4] = {0};
            } bandFlags;
            ASSERT(numQmfBand <= 4);
            for (uint8_t j = subGroupStartPos; j < subGroupEndPos; ++j) {
                //assert num of coded values are same in group
                ASSERT(codedValues == curGroup.SubGroupPtr[j]->ScaledBlock.Values.size());
                uint8_t specBlock = (curGroup.SubGroupPtr[j]->ValPtr->Pos) >> 6;
                ASSERT((specBlock >> 2) < numQmfBand);
                bandFlags.c[specBlock]++;
            }

            ASSERT(numQmfBand == 4);

            tcgnCheck++;
            
            bitsUsed += numQmfBand;
            if (bitStream) {
                for (uint8_t j = 0; j < numQmfBand; ++j) {
                    bitStream->Write((bool)bandFlags.i[j], 1);
                }
            }
            //write number of coded values for components in current group
            ASSERT(codedValues > 0);
            bitsUsed += 3;
            if (bitStream)
                bitStream->Write(codedValues - 1, 3);
            //write quant index
            ASSERT((i >> 3) > 1);
            ASSERT((i >> 3) < 8);
            bitsUsed += 3;
            if (bitStream)
                bitStream->Write(i >> 3, 3);
            uint8_t lastPos = subGroupStartPos;
            uint8_t checkPos = 0;
            for (size_t j = 0; j < 16; ++j) {
                if (!(bandFlags.i[j >> 2])) {
                    continue;
                }

                const uint8_t codedComponents = bandFlags.c[j];
                ASSERT(codedComponents < 8);
                bitsUsed += 3;
                if (bitStream)
                    bitStream->Write(codedComponents, 3);
                uint16_t k = lastPos;
                for (; k < lastPos + codedComponents; ++k) {
                    ASSERT(curGroup.SubGroupPtr[k]->ValPtr->Pos >= j * 64);
                    uint16_t relPos = curGroup.SubGroupPtr[k]->ValPtr->Pos - j * 64;
                    ASSERT(curGroup.SubGroupPtr[k]->ScaledBlock.ScaleFactorIndex < 64);

                    bitsUsed += 6;
                    if (bitStream)
                        bitStream->Write(curGroup.SubGroupPtr[k]->ScaledBlock.ScaleFactorIndex, 6);

                    ASSERT(relPos < 64);
                    
                    bitsUsed += 6;
                    if (bitStream)
                        bitStream->Write(relPos, 6);

                    ASSERT(curGroup.SubGroupPtr[k]->ScaledBlock.Values.size() < 8);
                    int mantisas[256];
                    const float mul = TAtrac3Data::MaxQuant[std::min((uint32_t)(i>>3), (uint32_t)7)];
                    ASSERT(codedValues == curGroup.SubGroupPtr[k]->ScaledBlock.Values.size());
                    for (uint32_t z = 0; z < curGroup.SubGroupPtr[k]->ScaledBlock.Values.size(); ++z) {
                        mantisas[z] = lrint(curGroup.SubGroupPtr[k]->ScaledBlock.Values[z] * mul);
                    }
                    //VLCEnc

                    ASSERT(i);
                    bitsUsed += VLCEnc(i>>3, mantisas, curGroup.SubGroupPtr[k]->ScaledBlock.Values.size(), bitStream);

                }
                lastPos = k;
                checkPos = lastPos;
            }

            ASSERT(subGroupEndPos == checkPos);
        }
    }
    ASSERT(tcgnCheck == tcsgn);
    if (bitStream)
        ASSERT(bitStream->GetSizeInBits() - bitsUsedOld == bitsUsed);
    return bitsUsed;
}

vector<uint32_t> TAtrac3BitStreamWriter::CalcBitsAllocation(const std::vector<TScaledBlock>& scaledBlocks,
                                                            const uint32_t bfuNum,
                                                            const float spread,
                                                            const float shift,
                                                            const float loudness,
                                                            const int gainBoostPerBand[TAtrac3Data::NumQMF],
                                                            const TMlHints& hints,
                                                            const TParityFrameAnalysis* parity,
                                                            float hfBias,
                                                            float tonalBias,
                                                            float transientBias,
                                                            float gainScale)
{
    vector<uint32_t> bitsPerEachBlock(bfuNum);
    for (size_t i = 0; i < bitsPerEachBlock.size(); ++i) {
        float ath = ATH[i] * loudness;

        // Determine which QMF band this BFU belongs to for gain boost lookup.
        const uint32_t bfuBand = BfuBandFromIndex((uint32_t)i);

        if (scaledBlocks[i].MaxEnergy < ath) {
            bitsPerEachBlock[i] = 0;
        } else {
            const uint32_t fix = FixedBitAllocTable[i];
            float x = 6;
            if (i < 3) {
                x = 2.8;
            } else if (i < 10) {
                x = 2.6;
            } else if (i < 15) {
                x = 3.3;
            } else if (i <= 20) {
                x = 3.6;
            } else if (i <= 28) {
                x = 4.2;
            }
            int tmp = spread * ( (float)scaledBlocks[i].ScaleFactorIndex / x) + (1.0 - spread) * fix - shift
                      + (int)std::lround(gainBoostPerBand[bfuBand] * gainScale);
            if (Params.Bitrate <= 132300 && i >= 22 && scaledBlocks[i].MaxEnergy > ath * 2.5f) {
                tmp += 1;
            }
            if (hints.Confidence >= 0.5f) {
                const int h = (int)std::lround(std::max(-1.5f, std::min(1.5f, hints.HfNoiseBias * 1.5f)));
                if (i >= 20) {
                    tmp += h;
                }
            }
            if (parity && parity->Valid) {
                const auto& band = parity->Bands[bfuBand];
                const float audibility = Clamp01((scaledBlocks[i].MaxEnergy - band.MaskingThreshold)
                                                 / std::max(1e-6f, scaledBlocks[i].MaxEnergy));
                const float parityBoost = 1.35f * hfBias * band.HfSalience
                                        + 1.10f * tonalBias * band.Tonality
                                        + 1.00f * transientBias * Clamp01(band.TransientScore / 4.0f)
                                        + 0.90f * band.SibilanceRisk
                                        + 0.65f * (1.0f - band.Stability)
                                        + 0.45f * (1.0f - band.StereoCoherence) * band.StereoSideRatio;
                tmp += (int)std::lround(parityBoost * (0.5f + audibility));
                if (scaledBlocks[i].MaxEnergy < band.MaskingThreshold * 0.70f) {
                    tmp -= 1;
                }
            }
            if (tmp > 7) {
                bitsPerEachBlock[i] = 7;
            } else if (tmp < 0) {
                bitsPerEachBlock[i] = 0;
            } else if (tmp == 0) {
                bitsPerEachBlock[i] = 1;
            } else {
                bitsPerEachBlock[i] = tmp;
            }
        }
    }
    return bitsPerEachBlock;
}

vector<uint32_t> TAtrac3BitStreamWriter::CalcBitsAllocationLegacyV10(const std::vector<TScaledBlock>& scaledBlocks,
                                                                     const uint32_t bfuNum,
                                                                     const float spread,
                                                                     const float shift,
                                                                     const float loudness,
                                                                     const int gainBoostPerBand[TAtrac3Data::NumQMF],
                                                                     const TParityFrameAnalysis* parity)
{
    vector<uint32_t> bitsPerEachBlock(bfuNum);
    int transientProtectHits = 0;
    int hfSibilanceProtectHits = 0;
    int allocatorFeedbackHits = 0;
    const EParityBucket parityBucket = ClassifyParityBucket(parity);
    for (size_t i = 0; i < bitsPerEachBlock.size(); ++i) {
        const float ath = ATH[i] * loudness;
        const uint32_t bfuBand = BfuBandFromIndex((uint32_t)i);

        if (scaledBlocks[i].MaxEnergy < ath) {
            bitsPerEachBlock[i] = 0;
        } else {
            const uint32_t fix = FixedBitAllocTable[i];
            float x = 6.0f;
            if (i < 3) {
                x = 2.8f;
            } else if (i < 10) {
                x = 2.6f;
            } else if (i < 15) {
                x = 3.3f;
            } else if (i <= 20) {
                x = 3.6f;
            } else if (i <= 28) {
                x = 4.2f;
            }
            int tmp = spread * ((float)scaledBlocks[i].ScaleFactorIndex / x)
                    + (1.0f - spread) * fix
                    - shift
                    + gainBoostPerBand[bfuBand];
            if (Params.Bitrate <= 132300 && i >= 22 && scaledBlocks[i].MaxEnergy > ath * 2.5f) {
                tmp += 1;
            }
            if (parity && Params.Bitrate <= 132300) {
                const auto& pb = parity->Bands[bfuBand];
                // Stability-first micro-lane:
                // add a tiny bounded protection boost around true attack/HF-risk frames.
                // This intentionally avoids broad retuning of legacy-v10 allocation behavior.
                const bool transientProtect = (parityBucket == EParityBucket::GainTransientDriven)
                    && (bfuBand == 1)
                    && (parity->AttackRisk > 5.6f)
                    && (parity->Stability < 0.20f)
                    && (parity->HfRisk < 0.0018f)
                    && (parity->TonalRisk < 0.90f)
                    && (pb.TransientScore > 1.10f)
                    && (pb.Tonality < 0.62f)
                    && (scaledBlocks[i].ScaleFactorIndex >= 17);
                if (transientProtect) {
                    tmp += 1;
                    ++transientProtectHits;
                }
                const bool hfSibilanceProtect = (parityBucket == EParityBucket::StereoDriven)
                    && (bfuBand == 3)
                    && (parity->HfRisk > 0.050f)
                    && (parity->MaxSibilanceRisk > 0.20f)
                    && (parity->Stability > 0.90f)
                    && (pb.HfSalience > 0.080f)
                    && (pb.SibilanceRisk > 0.12f)
                    && (scaledBlocks[i].ScaleFactorIndex >= 17);
                if (hfSibilanceProtect) {
                    tmp += 1;
                    ++hfSibilanceProtectHits;
                }
                const bool allocatorFeedbackProtect = (parityBucket == EParityBucket::AllocatorDriven)
                    && (bfuBand >= 2)
                    && (parity->FrameRisk > 0.24f)
                    && (parity->HfRisk > 0.05f)
                    && (parity->MaxSibilanceRisk > 0.10f)
                    && (parity->Stability > 0.80f)
                    && (scaledBlocks[i].ScaleFactorIndex >= 18);
                if (allocatorFeedbackProtect) {
                    tmp += 1;
                    ++allocatorFeedbackHits;
                }
            }
            if (tmp > 7) {
                bitsPerEachBlock[i] = 7;
            } else if (tmp < 0) {
                bitsPerEachBlock[i] = 0;
            } else if (tmp == 0) {
                bitsPerEachBlock[i] = 1;
            } else {
                bitsPerEachBlock[i] = tmp;
            }
        }
    }
    if (DecisionLogActiveThisFrame && parity) {
        *DecisionLog << "allocation_micro_lane: {transient_hits: " << transientProtectHits
                     << ", hf_sibilance_hits: " << hfSibilanceProtectHits
                     << ", allocator_feedback_hits: " << allocatorFeedbackHits
                     << ", parity_bucket: " << ParityBucketName(parityBucket) << "}\n";
    }
    return bitsPerEachBlock;
}

void WriteJsParams(NBitStream::TBitStream* bs)
{
    bs->Write(0, 1);
    bs->Write(7, 3);
    for (int i = 0; i < 4; i++) {
        bs->Write(3, 2);
    }
}

//  0.5 - M only (mono)
//  0.0 - Uncorrelated
// -0.5 - S only
static float CalcMSRatio(float mEnergy, float sEnergy) {
    float total = sEnergy + mEnergy;
    if (total > 0)
        return mEnergy / total - 0.5;

    // No signal - nothing to shift
    return 0;
}

static const char* StableMsReasonName(uint32_t reason) {
    switch (reason) {
        case 1:
            return "coherence_jump";
        case 2:
            return "hf_spike";
        case 3:
            return "stability_hold";
        default:
            return "none";
    }
}

static int32_t CalcMSBytesShift(uint32_t frameSz,
                                const vector<TAtrac3BitStreamWriter::TSingleChannelElement>& elements,
                                const int32_t b[2],
                                bool enableParityAnalysis,
                                bool enableStabilityMode,
                                uint32_t parityBucket,
                                float lastRatio,
                                float lastPreserveSide,
                                float lastHfRisk,
                                float* rawRatioOut,
                                float* resolvedRatio,
                                float* preserveSideOut = nullptr,
                                float* holdOut = nullptr,
                                float* hfRiskOut = nullptr,
                                bool* continuityClampedOut = nullptr,
                                uint32_t* continuityReasonOut = nullptr)
{
    const int32_t totalUsedBits = 0 - b[0] - b[1];
    ASSERT(totalUsedBits > 0);

    const int32_t maxAllowedShift = (frameSz / 2 - Div8Ceil(totalUsedBits));

    const bool stereoDrivenBucket = (parityBucket == static_cast<uint32_t>(EParityBucket::StereoDriven));
    if (elements[1].ScaledBlocks.empty()) {
        if (rawRatioOut) {
            *rawRatioOut = 0.5f;
        }
        if (resolvedRatio) {
            *resolvedRatio = 0.5f;
        }
        if (hfRiskOut) {
            *hfRiskOut = 0.0f;
        }
        if (continuityClampedOut) {
            *continuityClampedOut = false;
        }
        if (continuityReasonOut) {
            *continuityReasonOut = 0;
        }
        return maxAllowedShift;
    } else {
        float ratio = CalcMSRatio(elements[0].Loudness, elements[1].Loudness);
        float rawRatio = ratio;
        bool continuityClamped = false;
        uint32_t continuityReason = 0;
        float parityMinStability = 1.0f;
        float parityHfRisk = 0.0f;
        float preserveSide = 0.0f;
        const bool allowStereoParityPolicy = (!enableStabilityMode) || stereoDrivenBucket;
        if (allowStereoParityPolicy && enableParityAnalysis && elements[0].ParityAnalysis.Valid && elements[1].ParityAnalysis.Valid) {
            const auto& p0 = elements[0].ParityAnalysis;
            const auto& p1 = elements[1].ParityAnalysis;
            for (uint32_t band = 0; band < TAtrac3Data::NumQMF; ++band) {
                const auto& pb0 = p0.Bands[band];
                const auto& pb1 = p1.Bands[band];
                const float coherence = 0.5f * (pb0.StereoCoherence + pb1.StereoCoherence);
                const float hf = 0.5f * (pb0.HfSalience + pb1.HfSalience);
                const float side = 0.5f * (pb0.StereoSideRatio + pb1.StereoSideRatio);
                const float tr = 0.5f * (pb0.TransientScore + pb1.TransientScore);
                preserveSide += (1.0f - coherence) * (0.55f + 0.60f * hf)
                              + side * (0.35f + 0.30f * Clamp01(tr / 4.0f));
            }
            preserveSide /= TAtrac3Data::NumQMF;

            // Keep more side energy when stereo is fragile in HF/transient bands.
            const float stereoFragility = std::max(p0.StereoRisk, p1.StereoRisk);
            const float hfRisk = std::max(p0.HfRisk, p1.HfRisk);
            parityHfRisk = hfRisk;
            const float protect = 0.25f + 0.18f * Clamp01(stereoFragility) + 0.20f * Clamp01(hfRisk * 5.0f);
            ratio -= preserveSide * protect;
            rawRatio = ratio;

            // Hysteresis: hold previous M/S ratio harder when stability is low.
            const float minStability = std::min(p0.Stability, p1.Stability);
            parityMinStability = minStability;
            const float instability = Clamp01(1.0f - minStability);
            const float hold = std::max(0.20f, std::min(0.92f, 0.20f + instability * 0.60f + Clamp01(hfRisk * 4.0f) * 0.12f));
            ratio = (1.0f - hold) * ratio + hold * lastRatio;
            if (preserveSideOut) {
                *preserveSideOut = preserveSide;
            }
            if (holdOut) {
                *holdOut = hold;
            }
        } else {
            if (preserveSideOut) {
                *preserveSideOut = 0.0f;
            }
            if (holdOut) {
                *holdOut = 0.0f;
            }
        }
        if (hfRiskOut) {
            *hfRiskOut = parityHfRisk;
        }
        if (enableStabilityMode) {
            const float preserveJump = std::abs(preserveSide - lastPreserveSide);
            const float hfRiskJump = std::max(0.0f, parityHfRisk - lastHfRisk);

            // Isolated HF events can otherwise swing M/S too far for one frame.
            if (parityMinStability < 0.92f && (preserveJump > 0.10f || hfRiskJump > 0.08f)) {
                const float spikeHold = std::max(0.50f, std::min(0.92f,
                    0.50f + preserveJump * 1.4f + hfRiskJump * 1.8f));
                ratio = (1.0f - spikeHold) * ratio + spikeHold * lastRatio;
                continuityReason = 2;
            }

            float maxDelta = 0.08f;
            if (parityHfRisk > 0.10f) {
                maxDelta = 0.05f;
                continuityReason = 2;
            }
            if (preserveJump > 0.12f || hfRiskJump > 0.10f) {
                maxDelta = std::min(maxDelta, 0.03f);
                continuityReason = 2;
            }
            if (parityMinStability < 0.78f) {
                maxDelta = std::min(maxDelta, 0.04f);
                continuityReason = 1;
            }
            if (parityMinStability < 0.65f) {
                maxDelta = std::min(maxDelta, 0.03f);
                continuityReason = 3;
            }
            const float sideBoostCap = (parityHfRisk > 0.10f || preserveJump > 0.12f) ? 0.025f : 0.04f;
            if (ratio < lastRatio - sideBoostCap) {
                ratio = lastRatio - sideBoostCap;
                continuityReason = 2;
            }
            const float minRatio = lastRatio - maxDelta;
            const float maxRatio = lastRatio + maxDelta;
            const float clampedRatio = std::max(minRatio, std::min(maxRatio, ratio));
            continuityClamped = std::abs(clampedRatio - ratio) > 1e-6f;
            ratio = clampedRatio;
        }
        ratio = std::max(-0.48f, std::min(0.48f, ratio));
        if (rawRatioOut) {
            *rawRatioOut = rawRatio;
        }
        if (resolvedRatio) {
            *resolvedRatio = ratio;
        }
        if (continuityClampedOut) {
            *continuityClampedOut = continuityClamped;
        }
        if (continuityReasonOut) {
            *continuityReasonOut = continuityClamped ? continuityReason : 0;
        }
        return std::max(std::min(ToInt(frameSz * ratio), maxAllowedShift), -maxAllowedShift);
    }
}

void TAtrac3BitStreamWriter::WriteSoundUnit(const vector<TSingleChannelElement>& singleChannelElements, float laudness)
{

    ASSERT(singleChannelElements.size() == 1 || singleChannelElements.size() == 2);

    const bool frameInWindow = InFrameWindow(FrameCounter, StartFrame, MaxFrames);
    ParityActiveThisFrame = EnableParityAnalysis && frameInWindow;
    DecisionLogActiveThisFrame = (DecisionLog != nullptr) && frameInWindow;

    const int halfFrameSz = Params.FrameSz >> 1;

    NBitStream::TBitStream bitStreams[2];

    int32_t bitsToAlloc[2] = {-6, -6}; // 6 bits used always to write num blocks and coding mode
                                       // See EncodeSpecs

    for (uint32_t channel = 0; channel < singleChannelElements.size(); channel++) {
        const TSingleChannelElement& sce = singleChannelElements[channel];
        const TAtrac3Data::SubbandInfo& subbandInfo = sce.SubbandInfo;

        NBitStream::TBitStream* bitStream = &bitStreams[channel];

        if (UseJointStereo && channel == 1) {
            WriteJsParams(bitStream);
            bitStream->Write(3, 2);
        } else {
            bitStream->Write(0x28, 6); //0x28 - id
        }

        const uint8_t numQmfBand = subbandInfo.GetQmfNum();
        ASSERT(numQmfBand > 0);
        bitStream->Write(numQmfBand - 1, 2);

        //write gain info
        for (uint32_t band = 0; band < numQmfBand; ++band) {
            const vector<TAtrac3Data::SubbandInfo::TGainPoint>& GainPoints = subbandInfo.GetGainPoints(band);
            ASSERT(GainPoints.size() < TAtrac3Data::SubbandInfo::MaxGainPointsNum);
            bitStream->Write(GainPoints.size(), 3);
            int s = 0;
            for (const TAtrac3Data::SubbandInfo::TGainPoint& point : GainPoints) {
                bitStream->Write(point.Level, 4);
                bitStream->Write(point.Location, 5);
                s++;
                ASSERT(s < 8);
            }
        }

        const int16_t bitsUsedByGainInfoAndHeader = (int16_t)bitStream->GetSizeInBits();
        bitsToAlloc[channel] -= bitsUsedByGainInfoAndHeader;
    }

    int mt[2][TAtrac3Data::MaxSpecs];
    std::pair<uint8_t, vector<uint32_t>> allocations[2];

    float resolvedMsRatio = LastMsRatio;
    float rawMsRatio = LastMsRatio;
    float prevMsPreserveSide = LastMsPreserveSide;
    float prevMsHfRisk = LastMsHfRisk;
    float msPreserveSide = 0.0f;
    float msHold = 0.0f;
    float msHfRisk = 0.0f;
    bool msContinuityClamped = false;
    uint32_t msContinuityReason = 0;
    EParityBucket frameParityBucket = EParityBucket::AllocatorDriven;
    const TAtrac3BitStreamWriter::TParityFrameAnalysis* frameParityRef = nullptr;
    if (ParityActiveThisFrame) {
        float bestScore = -1.0f;
        for (const auto& sce : singleChannelElements) {
            if (!sce.ParityAnalysis.Valid) {
                continue;
            }
            const float score = sce.ParityAnalysis.FrameRisk
                              + 0.9f * sce.ParityAnalysis.HfRisk
                              + 0.3f * std::max(0.0f, sce.ParityAnalysis.AttackRisk - 4.0f);
            if (score > bestScore) {
                bestScore = score;
                frameParityRef = &sce.ParityAnalysis;
            }
        }
        frameParityBucket = ClassifyParityBucket(frameParityRef);
        if (singleChannelElements.size() >= 2) {
            const auto b0 = ClassifyParityBucket(
                singleChannelElements[0].ParityAnalysis.Valid ? &singleChannelElements[0].ParityAnalysis : nullptr);
            const auto b1 = ClassifyParityBucket(
                singleChannelElements[1].ParityAnalysis.Valid ? &singleChannelElements[1].ParityAnalysis : nullptr);
            if (b0 == EParityBucket::StereoDriven || b1 == EParityBucket::StereoDriven) {
                frameParityBucket = EParityBucket::StereoDriven;
            } else if (b0 == EParityBucket::GainTransientDriven || b1 == EParityBucket::GainTransientDriven) {
                frameParityBucket = EParityBucket::GainTransientDriven;
            }
        }
    }
    // Keep legacy-v10 allocation, but allow parity-informed stereo continuity
    // when stability mode is explicitly enabled.
    const bool parityMsPolicyActive = ParityActiveThisFrame && (!ForceLegacyV10Quality || EnableStabilityMode);
    const int32_t msBytesShift = UseJointStereo
        ? CalcMSBytesShift(Params.FrameSz, singleChannelElements, bitsToAlloc,
                           parityMsPolicyActive, EnableStabilityMode, static_cast<uint32_t>(frameParityBucket),
                           LastMsRatio, LastMsPreserveSide, LastMsHfRisk,
                           &rawMsRatio, &resolvedMsRatio, &msPreserveSide, &msHold,
                           &msHfRisk,
                           &msContinuityClamped, &msContinuityReason)
        : 0; // positive - gain to m, negative to s. Must be zero if no joint stereo mode
    LastMsRatio = resolvedMsRatio;
    LastMsPreserveSide = msPreserveSide;
    LastMsHfRisk = msHfRisk;

    bitsToAlloc[0] += 8 * (halfFrameSz + msBytesShift);
    bitsToAlloc[1] += 8 * (halfFrameSz - msBytesShift);

    int32_t stereoBalanceBitsShift = 0;
    if (!UseJointStereo && EnableStereoBalanceExp && singleChannelElements.size() == 2) {
        float leftNeed = 0.0f;
        float rightNeed = 0.0f;
        if (ParityActiveThisFrame
            && singleChannelElements[0].ParityAnalysis.Valid
            && singleChannelElements[1].ParityAnalysis.Valid) {
            const auto& p0 = singleChannelElements[0].ParityAnalysis;
            const auto& p1 = singleChannelElements[1].ParityAnalysis;
            leftNeed = p0.StereoRisk + 2.0f * p0.HfRisk + 6.0f * p0.MaxSibilanceRisk
                     + std::max(0.0f, p0.AttackRisk - 4.0f) * 0.05f;
            rightNeed = p1.StereoRisk + 2.0f * p1.HfRisk + 6.0f * p1.MaxSibilanceRisk
                      + std::max(0.0f, p1.AttackRisk - 4.0f) * 0.05f;
            const float needDiff = rightNeed - leftNeed;
            const float minStability = std::min(p0.Stability, p1.Stability);
            const float needMagnitude = std::abs(needDiff);
            const float hfMarker = std::max(p0.HfRisk, p1.HfRisk)
                                 + std::max(p0.MaxSibilanceRisk, p1.MaxSibilanceRisk) * 6.0f;
            if (needMagnitude >= 0.18f && hfMarker >= 0.08f) {
                int32_t maxShiftBits = 16;
                if (minStability < 0.75f) {
                    maxShiftBits = 8;
                }
                stereoBalanceBitsShift = std::max(-maxShiftBits,
                    std::min(maxShiftBits, ToInt(needDiff * 32.0f)));
            }
        } else {
            const float l0 = singleChannelElements[0].Loudness;
            const float l1 = singleChannelElements[1].Loudness;
            const float total = std::max(1e-9f, l0 + l1);
            const float ratio = (l1 - l0) / total;
            if (std::abs(ratio) >= 0.12f) {
                stereoBalanceBitsShift = std::max(-4, std::min(4, ToInt(ratio * 16.0f)));
            }
        }
        bitsToAlloc[0] -= stereoBalanceBitsShift;
        bitsToAlloc[1] += stereoBalanceBitsShift;
    }

    for (uint32_t channel = 0; channel < singleChannelElements.size(); channel++) {
        const TSingleChannelElement& sce = singleChannelElements[channel];
        allocations[channel] = CreateAllocation(sce, bitsToAlloc[channel], mt[channel], laudness);
    }

    if (DecisionLogActiveThisFrame) {
        *DecisionLog << "---\n";
        *DecisionLog << "frame: " << FrameCounter << "\n";
        *DecisionLog << "ms_bytes_shift: " << msBytesShift << "\n";
        *DecisionLog << "quality_v10_mode: " << (ForceLegacyV10Quality ? "true" : "false") << "\n";
        *DecisionLog << "stability_mode: " << (EnableStabilityMode ? "true" : "false") << "\n";
        *DecisionLog << "stereo_exp_mode: " << (EnableStereoExp ? "true" : "false") << "\n";
        *DecisionLog << "stereo_balance_exp_mode: " << (EnableStereoBalanceExp ? "true" : "false") << "\n";
        const bool gainExpMode = EnableGainExp || EnableGainExp2;
        *DecisionLog << "gain_exp_mode: " << (gainExpMode ? "true" : "false") << "\n";
        *DecisionLog << "gain_exp2_mode: " << (EnableGainExp2 ? "true" : "false") << "\n";
        const char* baselineProfile = "standard";
        if (ForceLegacyV10Quality) {
            if (EnableGainExp2) {
                baselineProfile = "quality-v10-gain-exp2";
            } else if (EnableGainExp) {
                baselineProfile = "quality-v10-gain-exp";
            } else if (EnableStereoBalanceExp) {
                baselineProfile = "quality-v10-stereo-balance";
            } else if (EnableStereoExp) {
                baselineProfile = "quality-v10-stereo-exp";
            } else {
                baselineProfile = EnableStabilityMode ? "quality-v10-stable" : "quality-v10-native";
            }
        }
        *DecisionLog << "baseline_profile: " << baselineProfile << "\n";
        *DecisionLog << "bfu_idx_const: " << BfuIdxConst << "\n";
        *DecisionLog << "js_enabled: " << (UseJointStereo ? "true" : "false") << "\n";
        *DecisionLog << "ms_ratio_raw: " << rawMsRatio << "\n";
        *DecisionLog << "ms_ratio: " << resolvedMsRatio << "\n";
        *DecisionLog << "ms_ratio_final: " << resolvedMsRatio << "\n";
        *DecisionLog << "ms_preserve_side_prev: " << prevMsPreserveSide << "\n";
        *DecisionLog << "ms_preserve_side: " << msPreserveSide << "\n";
        *DecisionLog << "ms_hold: " << msHold << "\n";
        *DecisionLog << "ms_hf_risk_prev: " << prevMsHfRisk << "\n";
        *DecisionLog << "ms_hf_risk: " << msHfRisk << "\n";
        *DecisionLog << "ms_continuity_clamped: " << (msContinuityClamped ? "true" : "false") << "\n";
        *DecisionLog << "continuity_reason: " << StableMsReasonName(msContinuityReason) << "\n";
        *DecisionLog << "parity_bucket: " << ParityBucketName(frameParityBucket) << "\n";
        *DecisionLog << "parity_bucket_reason: " << ParityBucketReason(frameParityRef, frameParityBucket) << "\n";
        *DecisionLog << "stereo_balance_bits_shift: " << stereoBalanceBitsShift << "\n";
        *DecisionLog << "channels:\n";
        for (uint32_t channel = 0; channel < singleChannelElements.size(); ++channel) {
            const auto& sce = singleChannelElements[channel];
            *DecisionLog << "  - channel: " << channel << "\n";
            *DecisionLog << "    target_bits: " << bitsToAlloc[channel] << "\n";
            *DecisionLog << "    num_qmf_bands: " << sce.SubbandInfo.GetQmfNum() << "\n";
            *DecisionLog << "    tonal_blocks: " << sce.TonalBlocks.size() << "\n";
            *DecisionLog << "    allocation_mode: " << (int)allocations[channel].first << "\n";
            *DecisionLog << "    num_bfu: " << allocations[channel].second.size() << "\n";
            *DecisionLog << "    alloc_table: [";
            for (size_t i = 0; i < allocations[channel].second.size(); ++i) {
                if (i) {
                    *DecisionLog << ", ";
                }
                *DecisionLog << allocations[channel].second[i];
            }
            *DecisionLog << "]\n";
            *DecisionLog << "    gain_boost_per_band: ["
                         << sce.GainBoostPerBand[0] << ", "
                         << sce.GainBoostPerBand[1] << ", "
                         << sce.GainBoostPerBand[2] << ", "
                         << sce.GainBoostPerBand[3] << "]\n";
            *DecisionLog << "    gain_points_per_band: ["
                         << sce.SubbandInfo.GetGainPoints(0).size() << ", "
                         << sce.SubbandInfo.GetGainPoints(1).size() << ", "
                         << sce.SubbandInfo.GetGainPoints(2).size() << ", "
                         << sce.SubbandInfo.GetGainPoints(3).size() << "]\n";
            *DecisionLog << "    gain_continuity_clamped: ["
                         << (sce.GainContinuityClamped[0] ? "true" : "false") << ", "
                         << (sce.GainContinuityClamped[1] ? "true" : "false") << ", "
                         << (sce.GainContinuityClamped[2] ? "true" : "false") << ", "
                         << (sce.GainContinuityClamped[3] ? "true" : "false") << "]\n";
            *DecisionLog << "    gain_weak_transient_suppressed: ["
                         << (sce.GainWeakTransientSuppressed[0] ? "true" : "false") << ", "
                         << (sce.GainWeakTransientSuppressed[1] ? "true" : "false") << ", "
                         << (sce.GainWeakTransientSuppressed[2] ? "true" : "false") << ", "
                         << (sce.GainWeakTransientSuppressed[3] ? "true" : "false") << "]\n";
            *DecisionLog << "    hf_continuity_clamped: ["
                         << (sce.HfContinuityClamped[0] ? "true" : "false") << ", "
                         << (sce.HfContinuityClamped[1] ? "true" : "false") << ", "
                         << (sce.HfContinuityClamped[2] ? "true" : "false") << ", "
                         << (sce.HfContinuityClamped[3] ? "true" : "false") << "]\n";
            *DecisionLog << "    gain_target_prev: ["
                         << sce.GainTargetPrev[0] << ", "
                         << sce.GainTargetPrev[1] << ", "
                         << sce.GainTargetPrev[2] << ", "
                         << sce.GainTargetPrev[3] << "]\n";
            *DecisionLog << "    gain_target_cur: ["
                         << sce.GainTargetCur[0] << ", "
                         << sce.GainTargetCur[1] << ", "
                         << sce.GainTargetCur[2] << ", "
                         << sce.GainTargetCur[3] << "]\n";
            *DecisionLog << "    gain_first_level_prev: ["
                         << static_cast<int>(sce.GainFirstLevelPrev[0]) << ", "
                         << static_cast<int>(sce.GainFirstLevelPrev[1]) << ", "
                         << static_cast<int>(sce.GainFirstLevelPrev[2]) << ", "
                         << static_cast<int>(sce.GainFirstLevelPrev[3]) << "]\n";
            *DecisionLog << "    gain_first_level_cur: ["
                         << static_cast<int>(sce.GainFirstLevelCur[0]) << ", "
                         << static_cast<int>(sce.GainFirstLevelCur[1]) << ", "
                         << static_cast<int>(sce.GainFirstLevelCur[2]) << ", "
                         << static_cast<int>(sce.GainFirstLevelCur[3]) << "]\n";
            *DecisionLog << "    gain_point_counts: [";
            for (uint32_t band = 0; band < sce.SubbandInfo.GetQmfNum(); ++band) {
                if (band) {
                    *DecisionLog << ", ";
                }
                *DecisionLog << sce.SubbandInfo.GetGainPoints(band).size();
            }
            *DecisionLog << "]\n";
            *DecisionLog << "    ml_hints: {bfu_bias: " << sce.MlHints.BfuBudgetBias
                         << ", tonal_bias: " << sce.MlHints.TonalBias
                         << ", gain_bias: " << sce.MlHints.GainBias
                         << ", hf_bias: " << sce.MlHints.HfNoiseBias
                         << ", confidence: " << sce.MlHints.Confidence << "}\n";
            if (sce.ParityAnalysis.Valid) {
                *DecisionLog << "    parity: {frame_risk: " << sce.ParityAnalysis.FrameRisk
                             << ", stereo_risk: " << sce.ParityAnalysis.StereoRisk
                             << ", stability: " << sce.ParityAnalysis.Stability
                             << ", hf_risk: " << sce.ParityAnalysis.HfRisk
                             << ", max_sibilance_risk: " << sce.ParityAnalysis.MaxSibilanceRisk
                             << ", max_hf_salience: " << sce.ParityAnalysis.MaxHfSalience
                             << ", attack_risk: " << sce.ParityAnalysis.AttackRisk
                             << ", tonal_risk: " << sce.ParityAnalysis.TonalRisk
                             << ", ms_energy_ratio: " << sce.ParityAnalysis.MSEnergyRatio << "}\n";
            }
        }
    }

    for (uint32_t channel = 0; channel < singleChannelElements.size(); channel++) {
        const TSingleChannelElement& sce = singleChannelElements[channel];
        NBitStream::TBitStream* bitStream = &bitStreams[channel];

        EncodeSpecs(sce, bitStream, allocations[channel], mt[channel]);

        if (!Container)
            abort();

        std::vector<char> channelData = bitStream->GetBytes();

        if (UseJointStereo && channel == 1) {
            channelData.resize(halfFrameSz - msBytesShift);
            OutBuffer.insert(OutBuffer.end(), channelData.rbegin(), channelData.rend());
        } else {
            channelData.resize(halfFrameSz + msBytesShift);
            OutBuffer.insert(OutBuffer.end(), channelData.begin(), channelData.end());
        }
    }

    //No mone mode for atrac3, just make duplicate of first channel
    if (singleChannelElements.size() == 1 && !UseJointStereo) {
        int sz = OutBuffer.size();
        ASSERT(sz == halfFrameSz);
        OutBuffer.resize(sz << 1);
        std::copy_n(OutBuffer.begin(), sz, OutBuffer.begin() + sz);
    }

    Container->WriteFrame(OutBuffer);
    OutBuffer.clear();
    ++FrameCounter;
}

} // namespace NAtrac3
} // namespace NAtracDEnc
