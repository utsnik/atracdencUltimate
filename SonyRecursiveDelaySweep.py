import os
import subprocess

def test_delay(d, branch="High"):
    print(f"\n--- Testing Recursive Delay: {d} samples on {branch} branch ---")
    
    # Update atrac3_qmf.h
    qmf_h = f"""/*
 * This file is part of AtracDEnc.
 */

#pragma once
#include <vector>
#include "../qmf/qmf.h"

namespace NAtracDEnc {{

class Atrac3AnalysisFilterBank {{
    const static int nInSamples = 1024;
    TQmf<nInSamples> Qmf1;
    TQmf<nInSamples / 2> Qmf2;
    TQmf<nInSamples / 2> Qmf3;
    std::vector<float> Buf1;
    std::vector<float> Buf2;
    std::vector<float> DelayBuffer;
public:
    Atrac3AnalysisFilterBank() noexcept {{
        Buf1.resize(nInSamples / 2);
        Buf2.resize(nInSamples / 2);
        DelayBuffer.assign({d}, 0.0f);
    }}
    void Analysis(const float* pcm, float* subs[4]) noexcept {{
        Qmf1.Analysis(pcm, Buf1.data(), Buf2.data());
        
        {"// Delay Low Branch" if branch == "Low" else "// Delay High Branch"}
        if ({d} > 0) {{
            std::vector<float> delayed(512);
            float* target = {"Buf1.data()" if branch == "Low" else "Buf2.data()"};
            for (int i = 0; i < 512; ++i) {{
                delayed[i] = DelayBuffer[0];
                DelayBuffer.erase(DelayBuffer.begin());
                DelayBuffer.push_back(target[i]);
            }}
            memcpy(target, delayed.data(), 512 * sizeof(float));
        }}

        Qmf2.Analysis(Buf1.data(), subs[0], subs[1]);
        Qmf3.Analysis(Buf2.data(), subs[2], subs[3]);
    }}
}};

}} //namespace NAtracDEnc
"""
    with open("src/atrac/at3/atrac3_qmf.h", "w") as f:
        f.write(qmf_h)
    
    # Build and Verify
    subprocess.run(["cmd", "/c", "build_win.bat"], check=True, capture_output=True)
    result = subprocess.run(["python", "verify_atracdenc_snr.py"], check=True, capture_output=True, text=True)
    
    print(result.stdout)
    with open("delay_sweep_results.txt", "a") as f:
        f.write(f"Delay {d} ({branch}):\n{result.stdout}\n")

if __name__ == "__main__":
    if os.path.exists("delay_sweep_results.txt"): os.remove("delay_sweep_results.txt")
    
    # Sweep High branch (based on forensic lag report)
    for d in range(0, 33):
        test_delay(d, "High")
    
    # Sweep Low branch (just in case)
    for d in range(1, 33):
        test_delay(d, "Low")
