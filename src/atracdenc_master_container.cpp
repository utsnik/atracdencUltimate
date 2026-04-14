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

#include "at3.h"
#include <vector>
#include <cstring>
#include <memory>
#include <fstream>

namespace {

class TAt3WavOutput : public ICompressedOutput {
public:
    TAt3WavOutput(const std::string& outFile, int numChannels, uint32_t numFrames, uint32_t frameSz, bool jointStereo)
        : OutputFile(outFile)
        , Channels(numChannels)
        , FrameSize(frameSz)
        , JointStereo(jointStereo)
    {
        File.open(OutputFile, std::ios::binary);
        if (!File.is_open()) {
            return;
        }

        const uint32_t expectedDataSize = frameSz * numFrames;
        const uint32_t expectedRiffSize = expectedDataSize + 52;
        const uint32_t avgBytesPerSec = (frameSz * 44100) / 1024;

        // 60-byte ATRAC3 RIFF header compatible with at3tool and MiniDisc players.
        uint8_t h[60] = {
            0x52, 0x49, 0x46, 0x46, 0x00, 0x00, 0x00, 0x00, // RIFF + size
            0x57, 0x41, 0x56, 0x45, 0x66, 0x6D, 0x74, 0x20, // WAVE + fmt
            0x20, 0x00, 0x00, 0x00, 0x70, 0x02, 0x02, 0x00, // fmt size + codec + channels
            0x44, 0xAC, 0x00, 0x00, 0x99, 0x40, 0x00, 0x00, // sample rate + avg bytes/sec
            0x80, 0x01, 0x00, 0x00, 0x0E, 0x00, 0x01, 0x00, // block align + bits + cbSize + ext
            0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // ATRAC3 extra
            0x01, 0x00, 0x00, 0x00, 0x64, 0x61, 0x74, 0x61, // ATRAC3 extra + data
            0x00, 0x00, 0x00, 0x00  // data size
        };

        h[22] = static_cast<uint8_t>(numChannels);
        std::memcpy(h + 28, &avgBytesPerSec, sizeof(avgBytesPerSec));
        std::memcpy(h + 32, &frameSz, sizeof(uint16_t));
        std::memcpy(h + 4, &expectedRiffSize, sizeof(expectedRiffSize));
        std::memcpy(h + 56, &expectedDataSize, sizeof(expectedDataSize));

        File.write(reinterpret_cast<const char*>(h), sizeof(h));
    }

    ~TAt3WavOutput() override {
        if (File.is_open()) {
            FinalizeHeader();
            File.close();
        }
    }

    void WriteFrame(std::vector<char> data) override {
        if (!File.is_open()) {
            return;
        }
        File.write(data.data(), data.size());
        DataBytesWritten += static_cast<uint32_t>(data.size());
    }

    std::string GetName() const override { return "AT3 (RIFF)"; }
    size_t GetChannelNum() const override { return static_cast<size_t>(Channels); }

private:
    void FinalizeHeader() {
        const uint32_t riffSize = DataBytesWritten + 52;
        File.seekp(4, std::ios::beg);
        File.write(reinterpret_cast<const char*>(&riffSize), sizeof(riffSize));
        File.seekp(56, std::ios::beg);
        File.write(reinterpret_cast<const char*>(&DataBytesWritten), sizeof(DataBytesWritten));
        File.flush();
    }

    std::string OutputFile;
    std::ofstream File;
    int Channels = 2;
    uint32_t FrameSize = 384;
    bool JointStereo = false;
    uint32_t DataBytesWritten = 0;
};

} // namespace

TCompressedOutputPtr CreateAt3Output(const std::string& filename, size_t numChannel,
        uint32_t numFrames, uint32_t framesize, bool jointStereo)
{
    return std::make_unique<TAt3WavOutput>(filename, static_cast<int>(numChannel), numFrames, framesize, jointStereo);
}
