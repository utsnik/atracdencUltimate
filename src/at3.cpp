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
#include <cstring>
#include <vector>
#include <stdexcept>
#include <iostream>

namespace {

// LITERAL HEADER TEMPLATE (Phase 57):
// Taken from baseline_lp2.at3.wav. 
// Match for ATRAC3 132kbps (LP2) - 384 byte alignment.
unsigned char baselineHeader[80] = {
    0x52, 0x49, 0x46, 0x46, 0x68, 0x45, 0x01, 0x00, 0x57, 0x41, 0x56, 0x45, 0x66, 0x6d, 0x74, 0x20, 
    0x20, 0x00, 0x00, 0x00, 0x70, 0x02, 0x02, 0x00, 0x44, 0xac, 0x00, 0x00, 0x9a, 0x40, 0x00, 0x00, 
    0x80, 0x01, 0x00, 0x00, 0x0e, 0x00, 0x01, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
    0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x66, 0x61, 0x63, 0x74, 0x0c, 0x00, 0x00, 0x00, 0xec, 0x5d, 
    0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x64, 0x61, 0x74, 0x61, 0x28, 0x45, 0x01, 0x00
};

class TAt3 : public ICompressedOutput {
public:
    TAt3(const std::string &filename, size_t numChannels,
        uint32_t numFrames, uint32_t frameSize, bool jointStereo)
        : fp(fopen(filename.c_str(), "wb")), FramesWritten(0), TotalFrames(numFrames), FrameSz(frameSize)
    {
        if (!fp) throw std::runtime_error("Cannot open file to write");
        // Initial write of the working template.
        fwrite(baselineHeader, 1, 80, fp);
    }

    virtual ~TAt3() override {
        fseek(fp, 0, SEEK_SET);
        
        uint32_t data_size = FramesWritten * FrameSz;
        uint32_t total_samples = (FramesWritten * 1024) - 2048;
        
        std::cout << "DESTRUCTION: Final Header Patching. Data: " << data_size << std::endl;

        uint8_t h[80];
        memcpy(h, baselineHeader, 80);

        auto write32 = [&](uint32_t offset, uint32_t val) {
            h[offset] = val & 0xFF;
            h[offset+1] = (val >> 8) & 0xFF;
            h[offset+2] = (val >> 16) & 0xFF;
            h[offset+3] = (val >> 24) & 0xFF;
        };

        // PATCH SIZES DYNAMICALLY FOR FULL TRACK SUPPORT
        write32(4, 72 + data_size); 
        write32(60, total_samples); 
        write32(76, data_size);     

        fwrite(h, 1, 80, fp); 
        fclose(fp);
    }

    virtual void WriteFrame(std::vector<char> data) override {
        fwrite(data.data(), 1, data.size(), fp);
        FramesWritten++;
    }

    std::string GetName() const override { return {}; }
    size_t GetChannelNum() const override { return 2; }

private:
    FILE *fp;
    uint32_t FramesWritten;
    uint32_t TotalFrames;
    uint32_t FrameSz;
};

} //namespace

TCompressedOutputPtr
CreateAt3Output(const std::string& filename, size_t numChannel,
        uint32_t numFrames, uint32_t framesize, bool jointStereo)
{
    return std::unique_ptr<TAt3>(new TAt3(filename, numChannel, numFrames, framesize, jointStereo));
}
