#include "ggml-cpu-impl.h"
#include "ggml-quants.h"
#include "ggml-cpu.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <omp.h>

extern "C" bool sgemm_reference(const ggml_compute_params *, int64_t, int64_t, int64_t, const void *, int64_t, const void *, int64_t, void *, int64_t, int, int, int);
extern "C" bool sgemm_candidate(const ggml_compute_params *, int64_t, int64_t, int64_t, const void *, int64_t, const void *, int64_t, void *, int64_t, int, int, int);
typedef bool (*gemm_fn)(const ggml_compute_params *, int64_t, int64_t, int64_t, const void *, int64_t, const void *, int64_t, void *, int64_t, int, int, int);

static bool compute(gemm_fn fn, int m, int n, int k, int nth, int lda, int ldb, int ldc, const block_q8_0 * a, const block_q8_0 * b, float * c) {
    for (int ith = 0; ith < nth; ++ith) {
        ggml_compute_params p = {};
        p.ith = ith;
        p.nth = nth;
        if (!fn(&p, m, n, k, a, lda, b, ldb, c, ldc, GGML_TYPE_Q8_0, GGML_TYPE_Q8_0, GGML_TYPE_F32)) {
            return false;
        }
    }
    return true;
}

int main(void) {
    ggml_cpu_init();
    int cases = 0;
    const int dims[] = {4, 5, 7, 8, 15, 16, 31, 64};
    const int blocks[] = {1, 3, 16, 128};
    const int threads[] = {1, 3, 38};
    for (int m : dims) for (int n : dims) for (int k : blocks) for (int nth : threads) {
        const int lda = k + 1, ldb = k + 2, ldc = m + 3;
        std::vector<block_q8_0> a((size_t)m*lda), b((size_t)n*ldb);
        std::vector<float> row((size_t)k*QK8_0);
        for (int r = 0; r < m; ++r) {
            for (size_t i = 0; i < row.size(); ++i) row[i] = std::sin((float)(i + 13*r)*0.07f)*(r%3+1);
            quantize_row_q8_0_ref(row.data(), a.data() + (size_t)r*lda, row.size());
        }
        for (int r = 0; r < n; ++r) {
            for (size_t i = 0; i < row.size(); ++i) row[i] = std::cos((float)(i + 17*r)*0.11f)*(r%5+1);
            quantize_row_q8_0_ref(row.data(), b.data() + (size_t)r*ldb, row.size());
        }
        std::vector<float> reference((size_t)n*ldc + 16, -987654.0f), candidate = reference;
        const bool ok0 = compute(sgemm_reference,m,n,k,nth,lda,ldb,ldc,a.data(),b.data(),reference.data());
        const bool ok1 = compute(sgemm_candidate,m,n,k,nth,lda,ldb,ldc,a.data(),b.data(),candidate.data());
        if (ok0 != ok1 || !ok0 || std::memcmp(reference.data(),candidate.data(),reference.size()*sizeof(float))) {
            std::fprintf(stderr,"mismatch m=%d n=%d k_blocks=%d nth=%d accepted=%d/%d\n",m,n,k,nth,ok0,ok1);
            return 1;
        }
        ++cases;
    }
    std::printf("PASS: %d Q8 tinyBLAS cases, padded strides and guard outputs, bitwise equal\n",cases);
    if(std::getenv("PP_KERNEL_TIMING")) {
        const int sizes[][3]={{10240,512,80},{2560,512,192}};
        const gemm_fn funcs[]={sgemm_reference,sgemm_candidate};
        const char * names[]={"reference","candidate"};
        for(const auto & dims:sizes) {
            const int m=dims[0],n=dims[1],k=dims[2];
            std::vector<block_q8_0> a((size_t)m*k),b((size_t)n*k);
            std::vector<float> input((size_t)k*QK8_0), output((size_t)m*n);
            for(size_t i=0;i<input.size();++i) input[i]=std::sin(i*.07f);
            for(int r=0;r<m;++r) quantize_row_q8_0_ref(input.data(),a.data()+(size_t)r*k,input.size());
            for(int r=0;r<n;++r) quantize_row_q8_0_ref(input.data(),b.data()+(size_t)r*k,input.size());
            for(int round=-1;round<5;++round) for(int order=0;order<2;++order) {
                const int which=(order+(round<0?0:round))%2;
                const double start=omp_get_wtime();
                for(int rep=0;rep<3;++rep) {
                    #pragma omp parallel num_threads(38)
                    {
                        ggml_compute_params p={};p.ith=omp_get_thread_num();p.nth=omp_get_num_threads();
                        funcs[which](&p,m,n,k,a.data(),k,b.data(),k,output.data(),m,GGML_TYPE_Q8_0,GGML_TYPE_Q8_0,GGML_TYPE_F32);
                    }
                }
                const double elapsed=(omp_get_wtime()-start)/3;
                if(round>=0) std::printf("timing,%d,%d,%d,%d,%s,%.9f,%.9g\n",m,n,k,round,names[which],elapsed,output[0]);
            }
        }
    }
    return 0;
}
