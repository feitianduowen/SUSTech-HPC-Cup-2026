#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif
#include "ggml.h"
#include "ggml-cpu.h"
#include <omp.h>
#include <dlfcn.h>
#include <sched.h>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

struct Q5 { uint16_t d,m; uint8_t qh[4],qs[16]; };
struct Q8 { uint16_t d,s; int8_t qs[32]; };
static_assert(sizeof(Q5)==24&&sizeof(Q8)==36,"quantized layouts");
using Clock=std::chrono::steady_clock;
static uint64_t mix(uint64_t x){x^=x>>30;x*=UINT64_C(0xbf58476d1ce4e5b9);x^=x>>27;x*=UINT64_C(0x94d049bb133111eb);return x^(x>>31);}

int main(int argc,char **argv) {
    if(argc!=2)return 2;
    ggml_cpu_init();omp_set_dynamic(0);
    auto fn=ggml_get_type_traits_cpu(GGML_TYPE_Q5_1)->vec_dot;
    Dl_info info={};
    if(!fn||!dladdr((void *)fn,&info)||!info.dli_fname||!std::strstr(info.dli_fname,argv[1]))return 3;
    if(ggml_type_size(GGML_TYPE_Q5_1)!=sizeof(Q5)||ggml_type_size(GGML_TYPE_Q8_1)!=sizeof(Q8))return 4;
    std::printf("{\"library\":\"%s\",\"cases\":[",info.dli_fname);bool first_case=true;
    for(int n:{2560,6144})for(int threads:{1,19,38})for(int mode=0;mode<2;++mode) {
        const size_t row_bytes=size_t(n/32)*sizeof(Q5),y_bytes=size_t(n/32)*sizeof(Q8);
        const size_t rows=mode?std::max(size_t(4),size_t(512u*1024u*1024u)/(threads*row_bytes)):4;
        const size_t bytes=rows*threads*row_bytes;
        const uint16_t d5=ggml_fp32_to_fp16(1.0f/32),m5=ggml_fp32_to_fp16(-0.5f),d8=ggml_fp32_to_fp16(1.0f/64);
        void * raw=nullptr,*raw_y=nullptr;
        if(posix_memalign(&raw,64,bytes)||posix_memalign(&raw_y,64,y_bytes*threads))return 5;
        auto * weights=(uint8_t *)raw;auto * inputs=(uint8_t *)raw_y;
        std::vector<uint64_t> hashes(threads);std::vector<int> cpus(threads),valid(threads,1);
        std::vector<float> sinks(threads);
        // Allocation is untouched until each worker writes its own region.
        #pragma omp parallel num_threads(threads)
        {
            const int tid=omp_get_thread_num();cpus[tid]=sched_getcpu();
            if(omp_get_num_threads()!=threads)valid[tid]=0;
            Q8 * y=(Q8 *)(inputs+tid*y_bytes);
            for(int b=0;b<n/32;++b) {
                y[b].d=d8;int sum=0;
                for(int j=0;j<32;++j){y[b].qs[j]=int8_t((j*37+b*7+tid*11)%255-127);sum+=y[b].qs[j];}
                y[b].s=ggml_fp32_to_fp16(float(sum)/64);
            }
            Q5 * x=(Q5 *)(weights+tid*rows*row_bytes);
            for(size_t i=0;i<rows*size_t(n/32);++i) {
                const uint64_t z=mix(i+uint64_t(tid)*rows*(n/32)+17);
                Q5 v;v.d=d5;v.m=m5;
                uint32_t high=uint32_t(z);std::memcpy(v.qh,&high,4);
                uint64_t lo=mix(z),hi=mix(z+1);std::memcpy(v.qs,&lo,8);std::memcpy(v.qs+8,&hi,8);
                std::memcpy(x+i,&v,sizeof(v));
            }
            uint64_t hash=UINT64_C(1469598103934665603);
            for(size_t row=0;row<rows;++row) {
                float value=0;fn(n,&value,0,(uint8_t *)x+row*row_bytes,0,y,0,1);
                if(!std::isfinite(value))valid[tid]=0;
                uint32_t bits;std::memcpy(&bits,&value,4);hash=(hash^bits)*UINT64_C(1099511628211);
            }
            hashes[tid]=hash;
        }
        for(int x:valid)if(!x)return 6;
        auto run=[&](int reps) {
            const auto start=Clock::now();
            #pragma omp parallel num_threads(threads)
            {
                const int tid=omp_get_thread_num();
                const uint8_t * x=weights+tid*rows*row_bytes;const uint8_t * y=inputs+tid*y_bytes;
                float value=0;
                for(int rep=0;rep<reps;++rep)for(size_t row=0;row<rows;++row)fn(n,&value,0,x+row*row_bytes,0,y,0,1);
                sinks[tid]=value;
            }
            return std::chrono::duration<double,std::nano>(Clock::now()-start).count();
        };
        const int calibration_reps=mode?1:1000;
        const double calibration_ns=run(calibration_reps);
        const int reps=std::max(1,std::min(2000000,int(std::ceil(200000000.0*calibration_reps/std::max(1.0,calibration_ns)))));
        const double ns=run(reps),dots=double(reps)*rows*threads;
        for(float x:sinks)if(!std::isfinite(x))return 7;
        if(!first_case)std::printf(",");first_case=false;
        std::printf("{\"n\":%d,\"threads\":%d,\"mode\":\"%s\",\"rows_per_thread\":%zu,\"weight_bytes\":%zu,\"repetitions\":%d,\"elapsed_ns\":%.12g,\"ns_per_dot\":%.12g,\"effective_weight_GBps\":%.12g,\"cpu_ids\":[",n,threads,mode?"stream512MiB":"resident4rows",rows,bytes,reps,ns,ns/dots,dots*row_bytes/ns);
        for(int t=0;t<threads;++t){if(t)std::printf(",");std::printf("%d",cpus[t]);}
        std::printf("],\"checked_output_hashes\":[");
        for(int t=0;t<threads;++t){if(t)std::printf(",");std::printf("\"%016llx\"",(unsigned long long)hashes[t]);}
        std::printf("]}");std::fflush(stdout);
        std::free(raw);std::free(raw_y);
    }
    std::printf("]}\n");return 0;
}
