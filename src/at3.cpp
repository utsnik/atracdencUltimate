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
#include <iostream>
#include <vector>
#include <cstdio>
#include <stdexcept>

namespace {

// HYBRID SYNC (Phase 113):
// Using the forensic bit-perfect Sony Sony template header.
static const unsigned char baselineHeader[80] = {
    0x52, 0x49, 0x46, 0x46, 0xec, 0x5d, 0x03, 0x00, 0x57, 0x41, 0x56, 0x45, 0x66, 0x6d, 0x74, 0x20,
    0x20, 0x00, 0x00, 0x00, 0x70, 0x02, 0x02, 0x00, 0x44, 0xac, 0x00, 0x00, 0x64, 0x58, 0x00, 0x00,
    0x80, 0x01, 0x00, 0x00, 0x0e, 0x00, 0x01, 0x00, 0x00, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00,
    0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x66, 0x61, 0x63, 0x74,
    0x0c, 0x00, 0x00, 0x00, 0xec, 0x5d, 0x03, 0x00, 0x64, 0x61, 0x74, 0x61, 0x28, 0x45, 0x01, 0x00
};

class TAt3 : public ICompressedOutput {
public:
    TAt3(const std::string &filename)
        : fp(fopen(filename.c_str(), "wb"))
    {
        if (!fp) throw std::runtime_error("Cannot open file to write");
        fwrite(baselineHeader, 1, 80, fp);
    }

    ~TAt3() override {
        if (fp) {
            fseek(fp, 0, SEEK_END);
            long data_pos = ftell(fp) - 80;
            
            // HYBRID SYNC PADDING:
            // The Sony decoder (at3tool.exe) rejects files with fractional frames.
            // We enforce a strict 384-byte multiple by padding the final block.
            while (data_pos % 384 != 0) {
                fputc(0, fp);
                data_pos++;
            }

            uint32_t final_data_size = (uint32_t)data_pos;
            uint32_t final_frames = final_data_size / 384;
            uint32_t total_samples = final_frames * 1024; 
            
            write32(4, 72 + final_data_size);
            write32(68, total_samples);
            write32(76, final_data_size);
            
            fclose(fp);
        }
    }

    void write32(long offset, uint32_t val) {
        fseek(fp, offset, SEEK_SET);
        unsigned char buf[4];
        buf[0] = val & 0xff;
        buf[1] = (val >> 8) & 0xff;
        buf[2] = (val >> 16) & 0xff;
        buf[3] = (val >> 24) & 0xff;
        fwrite(buf, 1, 4, fp);
    }

    void WriteFrame(std::vector<char> data) override {
        fseek(fp, 0, SEEK_END);
        fwrite(data.data(), 1, data.size(), fp);
    }

    std::string GetName() const override { return {}; }
    size_t GetChannelNum() const override { return 2; }

private:
    FILE *fp;
};

} //namespace

TCompressedOutputPtr
CreateAt3Output(const std::string& filename, size_t, uint32_t, uint32_t, bool)
{
    return std::unique_ptr<TAt3>(new TAt3(filename));
}
