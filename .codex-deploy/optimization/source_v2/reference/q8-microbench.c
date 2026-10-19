/* Single-thread diagnostics; not a substitute for the fixed model benchmark. */
#define _POSIX_C_SOURCE 200809L
#include "q8-kernels.c"
#include <dlfcn.h>
#include <errno.h>
#include <float.h>
#include <inttypes.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef void (*dot_fn)(int, float *, size_t, const void *, size_t, const void *, size_t, int);

static dot_fn functions[] = { q8_baseline, q8_u2, q8_u4, q8_a2, q8_a4 };
static const char * names[] = { "baseline", "u2", "u4", "a2", "a4" };
static volatile double checksum;
static uint32_t rng_state = 0x91e10da5;

static uint32_t random_u32(void) {
    uint32_t value = rng_state;
    value ^= value << 13;
    value ^= value >> 17;
    value ^= value << 5;
    rng_state = value;
    return value;
}

static double seconds_now(void) {
    struct timespec time_value;
    if (clock_gettime(CLOCK_MONOTONIC, &time_value)) {
        perror("clock_gettime");
        exit(2);
    }
    return time_value.tv_sec + time_value.tv_nsec * 1e-9;
}

static uint32_t float_bits(float value) {
    uint32_t result;
    memcpy(&result, &value, sizeof(result));
    return result;
}

static block_q8_0 * allocate_blocks(size_t count) {
    void * result = NULL;
    if (count > SIZE_MAX / sizeof(block_q8_0) || posix_memalign(&result, 64, (count ? count : 1) * sizeof(block_q8_0))) {
        fprintf(stderr, "allocation failed\n");
        exit(2);
    }
    return result;
}

static void fill_blocks(block_q8_0 * blocks, size_t count, int pattern) {
    for (size_t i = 0; i < count; ++i) {
        float scale = ldexpf(1.0f + (random_u32() & 1023) / 1024.0f, (int) (random_u32() % 18) - 12);
        if (pattern == 0) {
            scale = 0.0f;
        } else if (pattern == 5 && (random_u32() & 1)) {
            scale = -scale;
        }
        blocks[i].d = _cvtss_sh(scale, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
        for (int j = 0; j < QK8_0; ++j) {
            int value = (int) (random_u32() % 255) - 127;
            if (pattern == 0) {
                value = 0;
            } else if (pattern == 2) {
                value = ((i + (size_t) j) & 1) ? 127 : -127;
            } else if (pattern == 3) {
                value = (j % 13 == 0) ? value : 0;
            } else if (pattern == 4) {
                value = (j < 16) ? 127 : -127;
            }
            blocks[i].qs[j] = (int8_t) value;
        }
        if (pattern != 0) {
            blocks[i].qs[random_u32() % QK8_0] = 127;
        }
    }
}

static float evaluate(dot_fn function, int nb, const block_q8_0 * x, const block_q8_0 * y) {
    float result = NAN;
    function(nb * QK8_0, &result, 0, x, 0, y, 0, 1);
    return result;
}

static double reference_double(int nb, const block_q8_0 * x, const block_q8_0 * y) {
    double result = 0;
    for (int i = 0; i < nb; ++i) {
        int sum = 0;
        for (int j = 0; j < QK8_0; ++j) {
            sum += x[i].qs[j] * y[i].qs[j];
        }
        result += sum * ((double) _cvtsh_ss(x[i].d) * _cvtsh_ss(y[i].d));
    }
    return result;
}

static int check_correctness(dot_fn production) {
    const int sizes[] = { 0, 1, 2, 3, 4, 5, 7, 8, 9, 15, 16, 17, 31, 32, 33, 63, 64, 65, 127, 128, 129, 255, 256, 257, 511, 512, 513, 1024, 4096 };
    const size_t n_functions = sizeof(functions) / sizeof(functions[0]);
    size_t changed[5] = { 0 }, non_finite[5] = { 0 };
    double absolute_max[5] = { 0 }, relative_max[5] = { 0 }, error_sq[5] = { 0 }, reference_error[5] = { 0 };
    size_t checks = 0, production_mismatches = 0;
    block_q8_0 * x = allocate_blocks(4096);
    block_q8_0 * y = allocate_blocks(4096);
    for (int pattern = 0; pattern < 6; ++pattern) {
        for (int repetition = 0; repetition < 8; ++repetition) {
            fill_blocks(x, 4096, pattern);
            fill_blocks(y, 4096, pattern);
            if (pattern == 4) {
                for (int i = 1; i < 4096; i += 2) {
                    for (int j = 0; j < QK8_0; ++j) {
                        y[i].qs[j] = (int8_t) -y[i].qs[j];
                    }
                }
            }
            for (size_t index = 0; index < sizeof(sizes) / sizeof(sizes[0]); ++index) {
                int nb = sizes[index];
                float baseline = evaluate(q8_baseline, nb, x, y);
                double reference = reference_double(nb, x, y);
                if (production && float_bits(evaluate(production, nb, x, y)) != float_bits(baseline)) {
                    ++production_mismatches;
                }
                for (size_t k = 0; k < n_functions; ++k) {
                    float actual = evaluate(functions[k], nb, x, y);
                    double error = fabs((double) actual - baseline);
                    double relative = error / fmax(fabs((double) baseline), 1e-20);
                    changed[k] += float_bits(actual) != float_bits(baseline);
                    non_finite[k] += !isfinite(actual);
                    absolute_max[k] = fmax(absolute_max[k], error);
                    relative_max[k] = fmax(relative_max[k], relative);
                    error_sq[k] += error * error;
                    reference_error[k] = fmax(reference_error[k], fabs((double) actual - reference));
                }
                ++checks;
            }
        }
    }
    puts("correctness,name,cases,bit_mismatches,non_finite,max_abs_vs_baseline,max_rel_vs_baseline,rms_vs_baseline,max_abs_vs_double");
    for (size_t k = 0; k < n_functions; ++k) {
        printf("correctness,%s,%zu,%zu,%zu,%.12g,%.12g,%.12g,%.12g\n", names[k], checks, changed[k], non_finite[k], absolute_max[k], relative_max[k], sqrt(error_sq[k] / checks), reference_error[k]);
    }
    fprintf(stderr, "production_comparison=%s mismatches=%zu cases=%zu\n", production ? "enabled" : "not_requested", production_mismatches, checks);
    free(y);
    free(x);
    return production_mismatches || changed[1] || changed[2] || non_finite[0] || non_finite[1] || non_finite[2] || non_finite[3] || non_finite[4];
}

static double time_kernel(dot_fn function, int nb, const block_q8_0 * x, const block_q8_0 * y, size_t rows, size_t iterations) {
    double start = seconds_now();
    double sum = 0;
    for (size_t iteration = 0; iteration < iterations; ++iteration) {
        size_t row = iteration % rows;
        sum += evaluate(function, nb, x + row * (size_t) nb, y);
    }
    double elapsed = seconds_now() - start;
    checksum += sum;
    return elapsed;
}

static size_t parse_size(const char * value, size_t upper_limit) {
    char * end;
    errno = 0;
    unsigned long long parsed = strtoull(value, &end, 10);
    if (errno || *end || !*value || value[0] == '-' || parsed == 0 || parsed > upper_limit) {
        fprintf(stderr, "invalid positive size: %s\n", value);
        exit(2);
    }
    return (size_t) parsed;
}

int main(int argc, char ** argv) {
    if (argc > 4) {
        fprintf(stderr, "usage: %s [production_lib_or_- [nb=128 [stream_mib=256]]]\n", argv[0]);
        return 2;
    }
    dot_fn production = NULL;
    void * library = NULL;
    if (argc > 1 && strcmp(argv[1], "-") != 0) {
        library = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
        if (!library) {
            fprintf(stderr, "dlopen: %s\n", dlerror());
            return 2;
        }
        void (*initialize_cpu)(void) = NULL;
        void * init_symbol = dlsym(library, "ggml_cpu_init");
        if (!init_symbol || sizeof(init_symbol) != sizeof(initialize_cpu)) {
            fprintf(stderr, "production ggml_cpu_init symbol unavailable\n");
            dlclose(library);
            return 2;
        }
        memcpy(&initialize_cpu, &init_symbol, sizeof(initialize_cpu));
        initialize_cpu();
        void * symbol = dlsym(library, "ggml_vec_dot_q8_0_q8_0");
        if (!symbol || sizeof(symbol) != sizeof(production)) {
            fprintf(stderr, "production Q8 symbol unavailable\n");
            dlclose(library);
            return 2;
        }
        memcpy(&production, &symbol, sizeof(production));
    }
    int nb = argc > 2 ? (int) parse_size(argv[2], 65536) : 128;
    size_t stream_mib = argc > 3 ? parse_size(argv[3], 2048) : 256;
    if (check_correctness(production)) {
        fprintf(stderr, "correctness failed; timings skipped\n");
        return 1;
    }
    size_t row_bytes = (size_t) nb * sizeof(block_q8_0);
    size_t rows = stream_mib * 1024 * 1024 / row_bytes;
    if (!rows) {
        rows = 1;
    }
    block_q8_0 * x = allocate_blocks(rows * (size_t) nb);
    block_q8_0 * y = allocate_blocks(nb);
    fill_blocks(x, rows * (size_t) nb, 1);
    fill_blocks(y, nb, 1);
    size_t iterations_resident = 10000000 / nb;
    if (iterations_resident < 100) {
        iterations_resident = 100;
    }
    const size_t n_functions = sizeof(functions) / sizeof(functions[0]);
    printf("config,nb,%d,rows,%zu,stream_bytes,%zu,resident_iterations,%zu\n", nb, rows, rows * row_bytes, iterations_resident);
    puts("timing,mode,round,name,seconds,calls,ns_per_dot,weight_GB_s");
    for (int mode = 0; mode < 2; ++mode) {
        size_t active_rows = mode ? rows : 1;
        size_t iterations = mode ? rows : iterations_resident;
        for (size_t k = 0; k < n_functions; ++k) {
            checksum += evaluate(functions[k], nb, x, y);
        }
        for (int round = 0; round < 5; ++round) {
            for (size_t order = 0; order < n_functions; ++order) {
                size_t k = (order + (size_t) round) % n_functions;
                double elapsed = time_kernel(functions[k], nb, x, y, active_rows, iterations);
                printf("timing,%s,%d,%s,%.9g,%zu,%.9g,%.9g\n", mode ? "stream" : "resident", round, names[k], elapsed, iterations, elapsed * 1e9 / iterations, (double) row_bytes * iterations / elapsed / 1e9);
            }
        }
    }
    fprintf(stderr, "checksum=%.17g\n", checksum);
    free(y);
    free(x);
    if (library) {
        dlclose(library);
    }
    return 0;
}
