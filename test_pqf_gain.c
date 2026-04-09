#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "src/atrac/atrac3plus_pqf/atrac3plus_pqf.h"

int main() {
    at3plus_pqf_a_ctx_t ctx = at3plus_pqf_create_a_ctx();
    float in[2048];
    float out[2048];

    // Simple 1kHz sine at 44.1kHz
    for (int i = 0; i < 2048; i++) {
        in[i] = sinf(2.0 * M_PI * 1000.0 * i / 44100.0);
    }

    at3plus_pqf_do_analyse(ctx, in, out);

    float max_out = 0;
    for (int i = 0; i < 2048; i++) {
        if (fabs(out[i]) > max_out) max_out = fabs(out[i]);
    }

    printf("Input Max: 1.0, Output Max: %f\n", max_out);

    at3plus_pqf_free_a_ctx(ctx);
    return 0;
}
