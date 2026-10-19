#define _GNU_SOURCE
#include "q8-candidate-kernels.c"
#include <dlfcn.h>
#include <math.h>
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

typedef void (*dot_fn)(int, float *, size_t, const void *, size_t, const void *, size_t, int);
static volatile double checksum;

static uint32_t random_u32(uint32_t * state) {
    uint32_t v = *state;
    v ^= v << 13;
    v ^= v >> 17;
    v ^= v << 5;
    return *state = v;
}

static uint32_t bits(float value) {
    uint32_t result;
    memcpy(&result, &value, sizeof(result));
    return result;
}

static void fill(block_q8_0 * data, size_t count, int pattern, uint32_t * state) {
    const uint16_t scales[] = {0, 0x8000, 1, 0x03ff, 0x0400, 0x1400, 0x3c00, 0xbc00, 0x7bff, 0xfbff};
    for (size_t i = 0; i < count; ++i) {
        data[i].d = scales[random_u32(state) % (sizeof(scales)/sizeof(scales[0]))];
        for (int k = 0; k < 32; ++k) {
            int value = (int) (random_u32(state) % (pattern == 1 ? 255 : 256)) - (pattern == 1 ? 127 : 128);
            if (pattern == 0) value = 0;
            if (pattern == 3) value = ((i+k)&1) ? 127 : -128;
            if (pattern == 4 && k % 7) value = 0;
            if (pattern == 5) value = k < 16 ? 127 : -127;
            data[i].qs[k] = (int8_t) value;
        }
    }
}

static float evaluate(dot_fn fn, int nb, const block_q8_0 * x, const block_q8_0 * y) {
    float result = NAN;
    fn(nb*32, &result, 0, x, 0, y, 0, 1);
    return result;
}

static int compare(dot_fn baseline, dot_fn candidate, int nb, const block_q8_0 * x, const block_q8_0 * y) {
    uint32_t expected = bits(evaluate(baseline,nb,x,y));
    uint32_t reference = bits(evaluate(q8_reference,nb,x,y));
    uint32_t actual = bits(evaluate(candidate,nb,x,y));
    if (expected != reference || expected != actual) {
        #pragma omp critical(q8_diagnostic)
        {
            static int printed = 0;
            if (printed++ < 8) fprintf(stderr,"nb=%d baseline=%08x reference=%08x candidate=%08x\n",nb,expected,reference,actual);
        }
        return 1;
    }
    return 0;
}

static void * load_library(const char * path, dot_fn * fn) {
    void * lib = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!lib) { fprintf(stderr,"dlopen %s: %s\n",path,dlerror()); exit(2); }
    void (*init)(void);
    void * symbol = dlsym(lib,"ggml_cpu_init");
    if (!symbol || sizeof(symbol)!=sizeof(init)) exit(2);
    memcpy(&init,&symbol,sizeof(init));
    init();
    symbol = dlsym(lib,"ggml_vec_dot_q8_0_q8_0");
    if (!symbol || sizeof(symbol)!=sizeof(*fn)) exit(2);
    memcpy(fn,&symbol,sizeof(*fn));
    return lib;
}

static int correctness(dot_fn baseline, dot_fn candidate) {
    const int sizes[] = {0,1,2,3,4,5,7,8,9,15,16,17,31,32,33,63,64,65,79,80,81,127,128,129,191,192,193,255,256,257,511,512,513,1024,4096};
    const int offsets[] = {0,2,14,30};
    unsigned long cases = 0, mismatches = 0;
    uint32_t state = 0x91e10da5;
    size_t bytes = 4096*sizeof(block_q8_0)+64;
    char * xb = malloc(bytes);
    char * yb = malloc(bytes);
    if (!xb || !yb) exit(2);
    for (size_t offset = 0; offset < 4; ++offset) {
        block_q8_0 * x = (block_q8_0 *) (xb+offsets[offset]);
        block_q8_0 * y = (block_q8_0 *) (yb+offsets[3-offset]);
        for (int pattern = 0; pattern < 6; ++pattern) {
            for (int repeat = 0; repeat < 8; ++repeat) {
                fill(x,4096,pattern,&state);
                fill(y,4096,pattern,&state);
                for (size_t i = 0; i < sizeof(sizes)/sizeof(sizes[0]); ++i) {
                    mismatches += compare(baseline,candidate,sizes[i],x,y);
                    ++cases;
                }
            }
        }
    }
    block_q8_0 x2[2], y2[2];
    for (int a = -128; a <= 127; ++a) {
        for (int b = -128; b <= 127; ++b) {
            for (int i = 0; i < 2; ++i) {
                x2[i].d = i ? 0xbc00 : 0x3c00;
                y2[i].d = 0x3c00;
                memset(x2[i].qs,i ? ~a : a,32);
                memset(y2[i].qs,i ? ~b : b,32);
            }
            mismatches += compare(baseline,candidate,2,x2,y2);
            ++cases;
            x2[1].d = 0;
            mismatches += compare(baseline,candidate,2,x2,y2);
            ++cases;
            x2[0].d = 0;
            x2[1].d = 0x3c00;
            mismatches += compare(baseline,candidate,2,x2,y2);
            ++cases;
        }
    }
    size_t page = (size_t) sysconf(_SC_PAGESIZE);
    char * xmap = mmap(NULL,page*2,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    char * ymap = mmap(NULL,page*2,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);
    if (xmap==MAP_FAILED || ymap==MAP_FAILED || mprotect(xmap+page,page,PROT_NONE) || mprotect(ymap+page,page,PROT_NONE)) exit(2);
    for (int nb = 0; nb <= 65; ++nb) {
        block_q8_0 * x = (block_q8_0 *) (xmap+page-nb*sizeof(block_q8_0));
        block_q8_0 * y = (block_q8_0 *) (ymap+page-nb*sizeof(block_q8_0));
        fill(x,nb,2,&state);
        fill(y,nb,2,&state);
        mismatches += compare(baseline,candidate,nb,x,y);
        ++cases;
    }
    munmap(xmap,page*2);
    munmap(ymap,page*2);
    int observed_threads = 0;
    #pragma omp parallel num_threads(38)
    {
        #pragma omp single
        observed_threads = omp_get_num_threads();
    }
    unsigned long concurrent_mismatches = 0;
    #pragma omp parallel for num_threads(38) reduction(+:concurrent_mismatches)
    for (int i = 0; i < 760; ++i) {
        block_q8_0 x[257], y[257];
        uint32_t local_state = 0x67812345u+i;
        int nb = 1+(i*37)%257;
        fill(x,nb,i%6,&local_state);
        fill(y,nb,(i+1)%6,&local_state);
        concurrent_mismatches += compare(baseline,candidate,nb,x,y);
    }
    cases += 760;
    mismatches += concurrent_mismatches;
    printf("{\"cases\":%lu,\"bit_mismatches\":%lu,\"guard_page_cases\":66,\"int8_pairs\":65536,\"concurrent_cases\":760,\"threads\":%d,\"status\":\"%s\"}\n",cases,mismatches,observed_threads,!mismatches && observed_threads==38 ? "PASS" : "FAIL");
    free(xb);
    free(yb);
    return mismatches || observed_threads!=38;
}

static double now(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC,&t)) exit(2);
    return t.tv_sec+t.tv_nsec*1e-9;
}

static double measure(dot_fn fn, int nb, const block_q8_0 * x, const block_q8_0 * y, size_t rows, size_t calls) {
    double sum = 0, begin = now();
    for (size_t i = 0; i < calls; ++i) sum += evaluate(fn,nb,x+(i%rows)*nb,y);
    double elapsed = now()-begin;
    checksum += sum;
    return elapsed;
}

static void benchmark(dot_fn baseline, dot_fn candidate) {
    const int shapes[] = {80,192};
    dot_fn functions[] = {baseline,candidate};
    const char * names[] = {"baseline","avx512-ordered"};
    puts("shape_blocks,mode,round,order,kernel,seconds,calls,ns_per_dot,weight_GB_s");
    for (size_t shape = 0; shape < 2; ++shape) {
        int nb = shapes[shape];
        size_t row_bytes = nb*sizeof(block_q8_0);
        size_t rows = (256u*1024*1024)/row_bytes;
        block_q8_0 * x = malloc(rows*row_bytes);
        block_q8_0 * y = malloc(row_bytes);
        if (!x || !y) exit(2);
        uint32_t state = 0x12345678;
        fill(x,rows*nb,1,&state);
        fill(y,nb,1,&state);
        for (int mode = 0; mode < 2; ++mode) {
            size_t active_rows = mode ? rows : 1;
            size_t calls = mode ? rows : 20000000u/nb;
            for (int k = 0; k < 2; ++k) checksum += measure(functions[k],nb,x,y,active_rows,calls);
            for (int round = 0; round < 10; ++round) {
                for (int order = 0; order < 2; ++order) {
                    int k = (round+order)%2;
                    double elapsed = measure(functions[k],nb,x,y,active_rows,calls);
                    printf("%d,%s,%d,%d,%s,%.9g,%zu,%.9g,%.9g\n",nb,mode ? "stream" : "resident",round,order,names[k],elapsed,calls,elapsed*1e9/calls,(double) row_bytes*calls/elapsed/1e9);
                }
            }
        }
        free(x);
        free(y);
    }
    fprintf(stderr,"checksum=%.17g\n",checksum);
}

int main(int argc, char ** argv) {
    if (argc!=4 || (strcmp(argv[3],"--check") && strcmp(argv[3],"--bench"))) {
        fprintf(stderr,"usage: %s BASELINE_LIB CANDIDATE_LIB_OR_- --check|--bench\n",argv[0]);
        return 2;
    }
    dot_fn baseline, candidate = q8_candidate;
    void * base_lib = load_library(argv[1],&baseline);
    void * candidate_lib = strcmp(argv[2],"-") ? load_library(argv[2],&candidate) : NULL;
    fprintf(stderr,"candidate=%s\n",candidate_lib ? argv[2] : "exact-source-excerpt");
    int result = 0;
    if (!strcmp(argv[3],"--check")) result = correctness(baseline,candidate);
    else benchmark(baseline,candidate);
    if (candidate_lib) dlclose(candidate_lib);
    dlclose(base_lib);
    return result;
}
