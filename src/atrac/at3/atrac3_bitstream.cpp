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
#include <atrac/atrac_psy_common.h>
#include <bitstream/bitstream.h>
#include <util.h>
#include <env.h>
#include <algorithm>
#include <iostream>
#include <vector>
#include <cstdlib>

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
TAtrac3BitStreamWriter::TAtrac3BitStreamWriter(ICompressedOutput* container, const TContainerParams& params, uint32_t bfuIdxConst)
    : Container(container)
    , Params(params)
    , BfuIdxConst(bfuIdxConst)
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
           ATH.push_back(x / 100); //reduce efficiency of ATH, but prevents aliasing problem, TODO: fix it?
        }
    }
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
    bool changed = false;
    while (*numBfu > 0 && precisionPerEachBlocks[*numBfu - 1] == 0) {
        (*numBfu)--;
        changed = true;
    }
    return changed;
}

static const std::pair<uint8_t, vector<uint32_t>> DUMMY_ALLOC{1, vector<uint32_t>{0}};

void WriteJsParams(NBitStream::TBitStream* bs)
{
    bs->Write(0, 1);
    bs->Write(7, 3);
    for (int i = 0; i < 4; i++) {
        bs->Write(3, 2);
    }
}

bool ConsiderEnergyErr(const vector<float>& err, vector<uint32_t>& bits)
{
    if (err.size() < bits.size())
        abort();

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

    float spread = AnalizeScaleFactorSpread(scaledBlocks);

    uint16_t numBfu = BfuIdxConst ? BfuIdxConst : 32;

    // Limit number of BFU if target bitrate is not enough
    // 3 bits to write each bfu without data
    // 5 bits we need for tonal header
    // 32 * 3 + 5 = 101
    if (targetBits < 101) {
        uint16_t lim = (targetBits - 5) / 3;
        numBfu = std::min(numBfu, lim);
    }

    vector<uint32_t> precisionPerEachBlocks(numBfu);
    vector<float> energyErr(numBfu);
    uint8_t mode;
    bool cont = true;
    while (cont) {
        precisionPerEachBlocks.resize(numBfu);
        double maxShift = 20;
        double minShift = -8;
        for (;;) {
            double shift = (maxShift + minShift) / 2;
            vector<uint32_t> tmpAlloc = CalcBitsAllocation(scaledBlocks, sce.BfuIsTonal, numBfu, spread, shift, laudness);
            energyErr.clear();
            energyErr.resize(numBfu);
            std::pair<uint8_t, uint32_t> consumption;

            do {
                consumption = CalcSpecsBitsConsumption(sce, tmpAlloc, mt, energyErr);
            } while (ConsiderEnergyErr(energyErr, tmpAlloc));

            auto bitsUsedByTonal = EncodeTonalComponents(sce, tmpAlloc, nullptr);
            //std::cerr << consumption.second << " |tonal: " << bitsUsedByTonal << " target: " << targetBits << " shift " << shift << " max | min " << maxShift << " " << minShift << " numBfu: " << numBfu << std::endl;
            consumption.second += bitsUsedByTonal;

            if (consumption.second < targetBits) {
                if (maxShift - minShift < 0.1) {
                    precisionPerEachBlocks = tmpAlloc;
                    mode = consumption.first;
                    if (numBfu >= 1) {
                        cont = !BfuIdxConst && CheckBfus(&numBfu, precisionPerEachBlocks);
                        if (cont) {
                            precisionPerEachBlocks.resize(numBfu);
                            tmpAlloc.resize(numBfu);
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
                if (cont) {
                    precisionPerEachBlocks.resize(numBfu);
                    tmpAlloc.resize(numBfu);
                }
                break;
            }
        }
    }
    
    // Silence Detection: If all BFUs have 0 precision, force numBfu to 0 for Sony parity
    // Also prune if energy is virtually zero (to overcome dither/noise)
    bool virtuallySilent = true;
    for (size_t i = 0; i < precisionPerEachBlocks.size(); i++) {
        const float threshold = (ATH[i] * laudness) + 1e-4f; // More aggressive floor
        if (precisionPerEachBlocks[i] > 0 || sce.ScaledBlocks[i].MaxEnergy > threshold) {
            virtuallySilent = false;
            break;
        }
    }
    static int frameCounter = 0;
    if (frameCounter < 2) { // 1 frame lead-in
        virtuallySilent = true;
    }
    frameCounter++;

    if (virtuallySilent) {
        precisionPerEachBlocks.clear();
        mode = 0; // Force VLC mode for silence
    }
    
    //std::cerr << "==" << std::endl;
    return { mode, precisionPerEachBlocks };
}

void TAtrac3BitStreamWriter::EncodeSpecs(const TSingleChannelElement& sce, NBitStream::TBitStream* bitStream,
    const std::pair<uint8_t, vector<uint32_t>>& allocation, const int mt[TAtrac3Data::MaxSpecs], bool isSideChannel)
{

    const vector<TScaledBlock>& scaledBlocks = sce.ScaledBlocks;
    const vector<uint32_t>& precisionPerEachBlocks = allocation.second;
    const uint32_t numBlocks = precisionPerEachBlocks.size(); //number of blocks to save
    const uint32_t codingMode = allocation.first;
    const bool virtuallySilent = (numBlocks == 0);

    if (virtuallySilent) {
        return; // The unit header was already written in WriteSoundUnit
    }

    EncodeTonalComponents(sce, precisionPerEachBlocks, bitStream);
    

    // Sony compatible block count: at least 1 block must be declared
    uint32_t codedBlocks = (numBlocks > 0) ? numBlocks : 1;
    bitStream->Write(codedBlocks - 1, 5);
    bitStream->Write(codingMode, 1);
    for (uint32_t i = 0; i < codedBlocks; ++i) {
        uint32_t val = (i < numBlocks) ? precisionPerEachBlocks[i] : 0;
        bitStream->Write(val, 3);
    }

    if (bitStream && isSideChannel) {
        WriteJsParams(bitStream);
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
        ASSERT(tc.ScaledBlock.Values.size() < 8);
        ASSERT(tc.ScaledBlock.Values.size() > 0);
        
        // Safety check: Skip tones in BFUs that were dropped during allocation
        // OR in BFUs that have 0 bits allocated (silent bands).
        if (tc.Val.Bfu >= allocTable.size() || allocTable[tc.Val.Bfu] == 0) {
            continue; 
        }

        auto quant = std::max((uint32_t)2, std::min(allocTable[tc.Val.Bfu] + 1, (uint32_t)7));
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
            ++tcsgn;
            groups[i].SubGroupMap.push_back(static_cast<uint8_t>(cur_pos));
            uint8_t groupLimiter = 0;
            //allow not grather than 8 components in one subgroup limited by 64 specs
            do {
                ++cur_pos;
                if (cur_pos == groups[i].SubGroupPtr.size())
                    break;
                if (groups[i].SubGroupPtr[cur_pos]->Val.Pos - (groups[i].SubGroupPtr[start_pos]->Val.Pos & ~63) < 64) {
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

    bitsUsed += 1;
    if (bitStream)
        bitStream->Write(tcsgn > 0, 1);

    if (tcsgn == 0) {
        for (int i = 0; i < 64; ++i)
            ASSERT(groups[i].SubGroupPtr.size() == 0);
        return bitsUsed;
    }

    bitsUsed += 5;
    if (bitStream)
        bitStream->Write(tcsgn, 5);

    //Coding mode:
    // 0 - All are VLC
    // 1 - CLC/Separate? Spec varies, but 1-bit '0' is standard VLC mode.
    bitsUsed += 1;
    if (bitStream)
        bitStream->Write(0, 1);

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
                uint8_t specBlock = (curGroup.SubGroupPtr[j]->Val.Pos) >> 6;
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
                    ASSERT(curGroup.SubGroupPtr[k]->Val.Pos >= j * 64);
                    uint16_t relPos = curGroup.SubGroupPtr[k]->Val.Pos - j * 64;
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
                                                            const std::vector<bool>& bfuIsTonal,
                                                            const uint32_t bfuNum,
                                                            const float spread,
                                                            const float shift,
                                                            const float loudness)
{
    vector<uint32_t> bitsPerEachBlock(bfuNum);
    for (size_t i = 0; i < bitsPerEachBlock.size(); ++i) {
        // Sony Parity: For silence/low-loudness, do not allocate any bits to spectral residue
        if (loudness < 1e-6f || scaledBlocks[i].MaxEnergy <= (ATH[i] * loudness) + 1e-9f) {
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
            int tmp = spread * ( (float)scaledBlocks[i].ScaleFactorIndex / x) + (1.0 - spread) * fix - shift;
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

static int32_t CalcMSBytesShift(uint32_t frameSz,
                                const vector<TAtrac3BitStreamWriter::TSingleChannelElement>& elements,
                                const int32_t b[2])
{
    const int32_t totalUsedBits = 0 - b[0] - b[1];
    ASSERT(totalUsedBits > 0);

    const int32_t maxAllowedShift = (frameSz / 2 - Div8Ceil(totalUsedBits));

    if (elements[1].ScaledBlocks.empty()) {
        return maxAllowedShift;
    } else {
        float ratio = CalcMSRatio(elements[0].Loudness, elements[1].Loudness);
        //std::cerr << ratio << std::endl;
        return std::max(std::min(ToInt(frameSz * ratio), maxAllowedShift), -maxAllowedShift);
    }
}

void TAtrac3BitStreamWriter::WriteSoundUnit(const vector<TSingleChannelElement>& singleChannelElements, float laudness)
{

    ASSERT(singleChannelElements.size() == 1 || singleChannelElements.size() == 2);

    const int halfFrameSz = Params.FrameSz >> 1;

    NBitStream::TBitStream bitStreams[2];

    int32_t bitsToAlloc[2] = {0, 0}; // Dynamic initialization
                                       // See EncodeSpecs

    for (uint32_t channel = 0; channel < singleChannelElements.size(); channel++) {
        const TSingleChannelElement& sce = singleChannelElements[channel];
        const TAtrac3Data::SubbandInfo& subbandInfo = sce.SubbandInfo;
        NBitStream::TBitStream* bitStream = &bitStreams[channel];
        uint8_t currentUnitQmfBands = 3;
        if (channel == 0) {
            // Sony Unit 0 starts with A2 (Sync 0x28 + 3 bands)
            bitStream->Write(0x28, 6);
            bitStream->Write(2, 2); 
            currentUnitQmfBands = 3;
        } else {
            // Sony Unit 1 (Side) starts with a single 0-bit (No Syncword)
            bitStream->Write(0, 1);
            currentUnitQmfBands = 3;
        }

        //write gain info
        for (uint32_t band = 0; band < currentUnitQmfBands; ++band) {
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

        int32_t usedBits = bitStream->GetSizeInBits();
        bitsToAlloc[channel] = (halfFrameSz * 8) - usedBits;

        // Account for Joint Stereo parameters if needed
        if (channel == 1 && Params.Js) {
            bitsToAlloc[channel] -= 12; // JS flag + 3 selector + 4*2 components
        }
    }

    int mt[2][TAtrac3Data::MaxSpecs];
    std::pair<uint8_t, vector<uint32_t>> allocations[2];

    // Sony Compatible: Force 0 shift for 132kbps (ensures 96/96 byte split)
    const int32_t msBytesShift = 0; 

    bitsToAlloc[0] += msBytesShift * 8;
    bitsToAlloc[1] -= msBytesShift * 8;

    for (uint32_t channel = 0; channel < singleChannelElements.size(); channel++) {
        const TSingleChannelElement& sce = singleChannelElements[channel];
        allocations[channel] = CreateAllocation(sce, bitsToAlloc[channel], mt[channel], laudness);
    }

    for (uint32_t channel = 0; channel < singleChannelElements.size(); channel++) {
        const TSingleChannelElement& sce = singleChannelElements[channel];
        NBitStream::TBitStream* bitStream = &bitStreams[channel];

        EncodeSpecs(sce, bitStream, allocations[channel], mt[channel], (Params.Js && channel == 1));

        if (!Container)
            abort();

        std::vector<char> channelData = bitStream->GetBytes();

        if (Params.Js && channel == 1) {
            channelData.resize(halfFrameSz - msBytesShift);
            OutBuffer.insert(OutBuffer.end(), channelData.begin(), channelData.end());
        } else {
            channelData.resize(halfFrameSz + msBytesShift);
            OutBuffer.insert(OutBuffer.end(), channelData.begin(), channelData.end());
        }
    }

    //No mone mode for atrac3, just make duplicate of first channel
    if (singleChannelElements.size() == 1 && !Params.Js) {
        int sz = OutBuffer.size();
        ASSERT(sz == halfFrameSz);
        OutBuffer.resize(sz << 1);
        std::copy_n(OutBuffer.begin(), sz, OutBuffer.begin() + sz);
    }

    Container->WriteFrame(OutBuffer);
    OutBuffer.clear();
}

} // namespace NAtrac3
} // namespace NAtracDEnc
