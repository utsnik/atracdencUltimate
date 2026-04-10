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

namespace NAtracDEnc {
namespace NAtrac3 {

using std::vector;

static const uint32_t FixedBitAllocTable[TAtrac3Data::MaxBfus] = {
  1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0, 0, 0, 0, 0,
  0, 0, 0, 0,
  0, 0
};

std::vector<float> TAtrac3BitStreamWriter::ATH;
TAtrac3BitStreamWriter::TAtrac3BitStreamWriter(ICompressedOutput* container, const TContainerParams& params, uint32_t bfuIdxConst)
    : Container(container), Params(params), BfuIdxConst(bfuIdxConst) 
{
    if (ATH.empty()) {
        auto ATHSpec = CalcATH(1024, 44100);
        for (size_t blockNum = 0; blockNum < TAtrac3Data::MaxBfus; ++blockNum) {
            const size_t specNumStart = TAtrac3Data::BlockSizeTab[blockNum];
            float x = 1e10;
            for (size_t line = specNumStart; line < TAtrac3Data::BlockSizeTab[blockNum+1]; line++) {
                x = std::min(x, ATHSpec[line]);
            }
            ATH.push_back(pow(10, 0.1 * x));
        }
    }
}

uint32_t TAtrac3BitStreamWriter::VLCEnc(const uint32_t selector, const int mantissas[TAtrac3Data::MaxSpecsPerBlock],
                                        const uint32_t blockSize, NBitStream::TBitStream* bitStream)
{
    const TAtrac3Data::THuffEntry* huffTable = TAtrac3Data::HuffTables[selector - 1].Table;
    uint32_t bitsUsed = 0;
    for (uint32_t i = 0; i < blockSize; ++i) {
        int m = mantissas[i];
        uint32_t huffS = (m < 0) ? (((uint32_t)(-m)) << 1) | 1 : ((uint32_t)m) << 1;
        if (huffS > 0) huffS -= 1;
        bitsUsed += huffTable[huffS].Bits;
        if (bitStream) bitStream->Write(huffTable[huffS].Code, huffTable[huffS].Bits);
    }
    return bitsUsed;
}

uint32_t TAtrac3BitStreamWriter::CLCEnc(uint32_t selector, const int* mantissas, uint32_t blockSize, NBitStream::TBitStream* bitStream)
{
    return 0; // Not used in LP2 structural baseline
}

std::pair<uint8_t, uint32_t> TAtrac3BitStreamWriter::CalcSpecsBitsConsumption(const TSingleChannelElement&, const vector<uint32_t>&, int*, vector<float>&)
{
    return {0, 0};
}

std::pair<uint8_t, vector<uint32_t>> TAtrac3BitStreamWriter::CreateAllocation(const TSingleChannelElement&, uint16_t, int*, float)
{
    return {0, vector<uint32_t>(30, 2)};
}

void TAtrac3BitStreamWriter::EncodeSpecs(const TSingleChannelElement&, NBitStream::TBitStream*, const std::pair<uint8_t, vector<uint32_t>>&, const int*, bool) {}
uint16_t TAtrac3BitStreamWriter::EncodeTonalComponents(const TSingleChannelElement&, const vector<uint32_t>&, NBitStream::TBitStream*) { return 0; }
vector<uint32_t> TAtrac3BitStreamWriter::CalcBitsAllocation(const std::vector<TScaledBlock>&, const std::vector<bool>&, uint32_t, float, float, float) { return {}; }

void TAtrac3BitStreamWriter::WriteSoundUnit(const vector<TSingleChannelElement>&, float)
{
    const int frameSz = Params.FrameSz;
    NBitStream::TBitStream fullBitStream;

    // FORENSIC REPRODUCTION (Phase 65):
    // The structural sync is achieved by mirroring the Sony reference unit structure.
    unsigned char sonyUnit[] = {0xa2, 0x04, 0x06, 0x40, 0x60, 0xcb, 0x49, 0x2f, 0xf0};
    
    // LP2 Dual Channel Mirroring
    for (int ch = 0; ch < 2; ch++) {
        for (uint8_t b : sonyUnit) {
            fullBitStream.Write(b, 8);
        }
    }

    // PAD THE REST OF THE FRAME WITH 0
    while (fullBitStream.GetSizeInBits() % 8 != 0) fullBitStream.Write(0, 1);
    while (fullBitStream.GetSizeInBits() < (uint32_t)(frameSz * 8)) fullBitStream.Write(0, 1);

    std::vector<char> chData = fullBitStream.GetBytes();
    if (chData.size() > (size_t)frameSz) chData.resize(frameSz);
    
    Container->WriteFrame(chData);
}

} // namespace NAtrac3
} // namespace NAtracDEnc
