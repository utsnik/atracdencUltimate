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

#include "at3.h"
#include <util.h>
#include <vector>
#include <cstring>
#include <iostream>
#include <memory>
#include <fstream>

// THE DATA TAG (Phase 228 - UNIVERSAL PLAYABILITY)
// 80-byte header: Sony Base(72) + Data Tag(8)

namespace {

class TAt3WavOutput : public ICompressedOutput {
public:
    TAt3WavOutput(const std::string& outFile, int numChannels, uint32_t numFrames, uint32_t frameSz, bool jointStereo)
        : OutputFile(outFile), Channels(numChannels), Frames(numFrames), FrameSize(frameSz), JointStereo(jointStereo)
    {
        File.open(OutputFile, std::ios::binary);
        if (!File.is_open()) return;

        // DEFINITIVE SONY AT3 HEADER (80 BYTES TOTAL, DATA TAG AT 0x48)
        uint32_t dataSize = (uint32_t)(384 * Frames);
        uint32_t riffSize = dataSize + 72;
        uint32_t factSamples = (uint32_t)(1024 * Frames);

        uint8_t h[80] = {
            0x52, 0x49, 0x46, 0x46, 0x00, 0x00, 0x00, 0x00, // 0x00: RIFF tag + size
            0x57, 0x41, 0x56, 0x45, 0x66, 0x6D, 0x74, 0x20, // 0x08: WAVEfmt 
            0x20, 0x00, 0x00, 0x00, 0x70, 0x02, (uint8_t)numChannels, 0x00, // 0x10: fmt sz=32
            0x44, 0xAC, 0x00, 0x00, 0x9A, 0x40, 0x00, 0x00, // 0x18: 44100, 16538 bps
            0x80, 0x01, 0x00, 0x00, 0x0E, 0x00, 0x01, 0x00, // 0x20: align 384, ext sz=14
            0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // 0x28: Samples/block 1024
            0x01, 0x00, 0x00, 0x00, 0x66, 0x61, 0x63, 0x74, // 0x30: fact tag
            0x0C, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // 0x38: fact sz=12, samples
            0x00, 0x04, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, // 0x40: padding/fact samples data
            0x64, 0x61, 0x74, 0x61, 0x00, 0x00, 0x00, 0x00  // 0x48: data tag + size
        };

        memcpy(h + 4, &riffSize, 4);
        memcpy(h + 60, &factSamples, 4);
        memcpy(h + 76, &dataSize, 4);

        File.write((const char*)h, 80);
    }

    virtual ~TAt3WavOutput() {
        if (File.is_open()) File.close();
    }

    virtual void WriteFrame(std::vector<char> data) override {
        if (File.is_open()) {
            File.write(data.data(), data.size());
        }
    }

    virtual std::string GetName() const override { return "ATRAC3-RIFF"; }
    virtual size_t GetChannelNum() const override { return (size_t)Channels; }

private:
    std::string OutputFile;
    std::ofstream File;
    int Channels;
    uint32_t Frames;
    uint32_t FrameSize;
    bool JointStereo;
};

} // namespace

TCompressedOutputPtr CreateAt3Output(const std::string& filename, size_t numChannel,
        uint32_t numFrames, uint32_t framesize, bool jointStereo)
{
    return std::make_unique<TAt3WavOutput>(filename, (int)numChannel, numFrames, framesize, jointStereo);
}
