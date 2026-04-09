/*
 * This file is part of AtracDEnc.
 */

#pragma once
#include <vector>
#include "../qmf/qmf.h"

namespace NAtracDEnc {

class Atrac3AnalysisFilterBank {
    const static int nInSamples = 1024;
    TQmf<nInSamples> Qmf1;
    TQmf<nInSamples / 2> Qmf2;
    TQmf<nInSamples / 2> Qmf3;
    std::vector<float> Buf1;
    std::vector<float> Buf2;
    std::vector<std::vector<float>> SubbandDelays;
public:
    int DelayConfig[4] = {0, 0, 0, 0};

    Atrac3AnalysisFilterBank() noexcept {
        Buf1.resize(nInSamples / 2);
        Buf2.resize(nInSamples / 2);
        SubbandDelays.resize(4);
        for (int i = 0; i < 4; ++i) SubbandDelays[i].assign(8, 0.0f); // Max 8 samples delay
    }
    void Analysis(const float* pcm, float* subs[4]) noexcept {
        // Stage 1: Split into L (Buf1) and H (Buf2)
        Qmf1.Analysis(pcm, Buf1.data(), Buf2.data());
        
        // Stage 2: Synchronized split. 
        float* raw_subs[4];
        float tmp[4][256];
        for (int i=0; i<4; ++i) raw_subs[i] = tmp[i];

        Qmf2.Analysis(Buf1.data(), raw_subs[0], raw_subs[1]);
        Qmf3.Analysis(Buf2.data(), raw_subs[2], raw_subs[3]);

        // Apply individual delays
        for (int band = 0; band < 4; ++band) {
            int d = DelayConfig[band];
            if (d <= 0) {
                memcpy(subs[band], raw_subs[band], 256 * sizeof(float));
            } else {
                for (int i = 0; i < 256; ++i) {
                    subs[band][i] = SubbandDelays[band][d - 1];
                    for (int k = d - 1; k > 0; --k) SubbandDelays[band][k] = SubbandDelays[band][k-1];
                    SubbandDelays[band][0] = raw_subs[band][i];
                }
            }
        }
    }
};

} //namespace NAtracDEnc
