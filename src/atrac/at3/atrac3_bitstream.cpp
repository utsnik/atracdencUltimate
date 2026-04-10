/*
 * This file is part of AtracDEnc.
 *
 * AtracDEnc is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * AtracDEnc is distributed in the hope that it will be details.
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
#include <cmath>
#include <cstdio>

namespace NAtracDEnc {
namespace NAtrac3 {

using std::vector;

static const uint32_t FixedBitAllocTable[TAtrac3Data::MaxBfus] = {
  4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
  2, 2, 2, 2, 2, 1, 1, 1,
  1, 1, 1, 1,
  0, 0
};

std::vector<float> TAtrac3BitStreamWriter::ATH;
TAtrac3BitStreamWriter::TAtrac3BitStreamWriter(ICompressedOutput* container, const TContainerParams& params, uint32_t bfuIdxConst)
    : Container(container), Params(params), BfuIdxConst(bfuIdxConst)
{
    if (ATH.empty()) {
        ATH.reserve(32);
        auto ATHSpec = CalcATH(1024, 44100);
        for (size_t blockNum = 0; blockNum < 32; ++blockNum) {
            float x = 999;
            uint32_t start = (blockNum < 33) ? TAtrac3Data::BlockSizeTab[blockNum] : 1024;
            uint32_t end = (blockNum+1 < 33) ? TAtrac3Data::BlockSizeTab[blockNum+1] : 1024;
            for (size_t line = start; line < end && line < ATHSpec.size(); line++) {
                x = std::min(x, ATHSpec[line]);
            }
            ATH.push_back(pow(10, 0.1 * x) / 100);
        }
    }
}

uint32_t TAtrac3BitStreamWriter::CLCEnc(const uint32_t s, const int ms[TAtrac3Data::MaxSpecsPerBlock],
                                        const uint32_t bs, NBitStream::TBitStream* bitStream)
{
    const uint32_t sel = s & 7;
    const uint32_t numBits = TAtrac3Data::ClcLengthTab[sel];
    const uint32_t bitsUsed = (sel > 1) ? numBits * bs : numBits * bs / 2;
    if (!bitStream) return bitsUsed;
    if (sel > 1) {
        for (uint32_t i = 0; i < bs; ++i) bitStream->Write(NBitStream::MakeSign(ms[i], numBits), numBits);
    } else {
        for (uint32_t i = 0; i < bs / 2; ++i) {
            int m0 = std::clamp(ms[i*2], -2, 1);
            int m1 = std::clamp(ms[i*2+1], -2, 1);
            uint32_t code = TAtrac3Data::MantissaToCLcIdx(m0) << 2 | TAtrac3Data::MantissaToCLcIdx(m1);
            bitStream->Write(code, 4);
        }
    }
    return bitsUsed;
}

uint32_t TAtrac3BitStreamWriter::VLCEnc(const uint32_t selector, const int ms[TAtrac3Data::MaxSpecsPerBlock],
                                        const uint32_t bs, NBitStream::TBitStream* bitStream)
{
    if (selector == 0) return 0;
    const uint32_t s = std::min(selector, 7u);
    const TAtrac3Data::THuffEntry* huffTable = TAtrac3Data::HuffTables[s - 1].Table;
    uint32_t bitsUsed = 0;
    if (s > 1) {
        int maxM = (1 << (s - 1));
        for (uint32_t i = 0; i < bs; ++i) {
            int m = std::clamp(ms[i], -maxM, maxM - 1);
            uint32_t huffS = (m < 0) ? (((uint32_t)(-m)) << 1) | 1 : ((uint32_t)m) << 1;
            if (huffS > 0) huffS -= 1;
            bitsUsed += huffTable[huffS].Bits;
            if (bitStream) bitStream->Write(huffTable[huffS].Code, huffTable[huffS].Bits);
        }
    } else {
        for (uint32_t i = 0; i < bs / 2; ++i) {
            int m0 = std::clamp(ms[i*2], -1, 1);
            int m1 = std::clamp(ms[i*2+1], -1, 1);
            const uint32_t huffS = TAtrac3Data::MantissasToVlcIndex(m0, m1);
            bitsUsed += huffTable[huffS].Bits;
            if (bitStream) bitStream->Write(huffTable[huffS].Code, huffTable[huffS].Bits);
        }
    }
    return bitsUsed;
}

std::pair<uint8_t, uint32_t> TAtrac3BitStreamWriter::CalcSpecsBitsConsumption(const TSingleChannelElement& sce,
    const vector<uint32_t>& p, int* mt, vector<float>& energyErr)
{
    uint32_t bitsUsed = 12 + p.size() * 3;
    for (uint32_t i = 0; i < p.size(); i++) {
        if (p[i] == 0 || i >= sce.ScaledBlocks.size()) continue;
        bitsUsed += 6; 
        const float mul = TAtrac3Data::MaxQuant[std::min(p[i], 7u)];
        uint32_t first = TAtrac3Data::BlockSizeTab[i];
        uint32_t last = TAtrac3Data::BlockSizeTab[i+1];
        if (sce.ScaledBlocks[i].Values.empty()) continue;
        energyErr[i] = QuantMantisas(sce.ScaledBlocks[i].Values.data(), first, last, mul, i > 18, mt);
        bitsUsed += VLCEnc(p[i], mt + first, last - first, nullptr);
    }
    return {0, bitsUsed};
}

std::pair<uint8_t, vector<uint32_t>> TAtrac3BitStreamWriter::CreateAllocation(const TSingleChannelElement& sce, uint16_t budget, int mt[TAtrac3Data::MaxSpecs], float loud)
{
    uint32_t n = 30;
    vector<uint32_t> best(n, 0);
    vector<float> err(n, 0.0f);
    float mi = -10, ma = 40;
    for(int iter=0; iter<40; ++iter) {
        float sh = (mi + ma) / 2.0f;
        vector<uint32_t> cur = CalcBitsAllocation(sce.ScaledBlocks, n, 0.5f, sh, loud);
        if (CalcSpecsBitsConsumption(sce, cur, mt, err).second < budget) { ma = sh; best = cur; } else { mi = sh; }
    }
    return {0, best};
}

vector<uint32_t> TAtrac3BitStreamWriter::CalcBitsAllocation(const vector<TScaledBlock>& s, uint32_t n, float spread, float sh, float loud)
{
    vector<uint32_t> bits(n, 0);
    for (size_t i=0; i<n; ++i) {
        if (i < s.size()) {
            float ath = ATH[i] * loud;
            if (s[i].MaxEnergy >= ath) {
                int tmp = spread * ((float)s[i].ScaleFactorIndex / 3.0f) + (1.0f - spread) * FixedBitAllocTable[i] - sh;
                bits[i] = std::clamp(tmp, 0, 7);
            }
        }
    }
    return bits;
}

void TAtrac3BitStreamWriter::EncodeSpecs(const TSingleChannelElement& sce, NBitStream::TBitStream* bs, const std::pair<uint8_t, vector<uint32_t>>& alloc, const int mt[TAtrac3Data::MaxSpecs])
{
    const vector<uint32_t>& p = alloc.second;
    bs->Write(0, 1); 
    bs->Write(p.size() - 1, 5); 
    bs->Write(0, 1); 
    for (uint32_t v : p) bs->Write(v, 3);
    for (uint32_t i=0; i<p.size(); ++i) {
        if (p[i]) {
            uint8_t sf = (i < sce.ScaledBlocks.size()) ? sce.ScaledBlocks[i].ScaleFactorIndex : 32;
            bs->Write(sf, 6);
        }
    }
    for (uint32_t i=0; i<p.size(); ++i) {
        if (p[i]) {
            uint32_t first = TAtrac3Data::BlockSizeTab[i];
            uint32_t last = TAtrac3Data::BlockSizeTab[i+1];
            VLCEnc(p[i], mt + first, last - first, bs);
        }
    }
}

void TAtrac3BitStreamWriter::WriteSoundUnit(const vector<TSingleChannelElement>& sces, float loud)
{
    if (sces.empty()) return;
    static int mt[TAtrac3Data::MaxSpecs]; 
    std::vector<char> fullFrame;
    fullFrame.reserve(384);

    for (uint32_t ch = 0; ch < 2; ch++) {
        const TSingleChannelElement& sce = (ch < sces.size()) ? sces[ch] : sces[0];
        NBitStream::TBitStream unit;
        
        // HARD SYNC (Phase 125): Unit-level signature
        unit.Write(0x4a02, 16); 
        for(int b=0; b<3; ++b) unit.Write(0, 3); 
        
        // Each unit is exactly 192 bytes = 1536 bits
        int32_t budget = 1536 - unit.GetSizeInBits();
        memset(mt, 0, sizeof(mt));
        auto allocation = CreateAllocation(sce, (uint16_t)(budget - 8), mt, loud);
        EncodeSpecs(sce, &unit, allocation, mt);
        
        // Pad to exactly 192 bytes
        while (unit.GetSizeInBits() < 1536) unit.Write(0, 1);
        
        const std::vector<char>& bytes = unit.GetBytes();
        for(int i=0; i<192; ++i) {
            fullFrame.push_back( (i < (int)bytes.size()) ? bytes[i] : 0 );
        }
    }
    
    Container->WriteFrame(fullFrame);
}

} // namespace NAtrac3
} // namespace NAtracDEnc
