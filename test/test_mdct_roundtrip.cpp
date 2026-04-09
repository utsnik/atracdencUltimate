#include <iostream>
#include <vector>
#include <cmath>
#include <iomanip>
#include "../src/lib/mdct/mdct.h"
#include "../src/atrac/at3/atrac3.h"

using namespace std;
using namespace NAtracDEnc;

int main() {
    // Initializing Sony Window (Simplified for check)
    float window[256];
    for (int i = 0; i < 256; i++) {
        window[i] = sin((M_PI / 256.0) * (i + 0.5)); // use sine window for scaling test
    }

    NMDCT::TMDCT<256> mdct(1.0 / sqrt(128.0));
    NMDCT::TMIDCT<256> midct(sqrt(128.0));

    float input[256];
    for (int i = 0; i < 256; i++) input[i] = sin(0.123 * i);

    // Apply window
    float windowed[256];
    for (int i = 0; i < 256; i++) windowed[i] = input[i] * window[i];

    // Forward MDCT
    const vector<float>& spec = mdct(windowed);
    cout << "Spectrum size: " << spec.size() << " (Expected 128)" << endl;

    // Inverse MDCT
    const vector<float>& output = midct(spec.data());
    cout << "Output size: " << output.size() << " (Expected 256)" << endl;

    // Apply window again (Princen-Bradley)
    float final_out[256];
    for (int i = 0; i < 256; i++) final_out[i] = output[i] * window[i];

    // Check center samples (where overlap-add would sum to 1.0)
    // Note: This is a single block, so we check scaling.
    float error = 0;
    for (int i = 0; i < 256; i++) {
        float expected = input[i] * window[i] * window[i];
        error += abs(final_out[i] - expected);
    }

    cout << "Total scaling error: " << error << endl;
    if (error < 1e-4) cout << "SCALING OK" << endl;
    else cout << "SCALING FAILED" << endl;

    return 0;
}
