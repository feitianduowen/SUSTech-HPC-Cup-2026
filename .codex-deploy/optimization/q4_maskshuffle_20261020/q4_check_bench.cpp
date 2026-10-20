#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <dlfcn.h>
#include <fstream>
#include <string>
#include <vector>

struct Q4 { uint16_t d[8], dmin[8]; uint8_t scales[96], qs[1024]; };
struct Q8 { float d; int8_t qs[256]; int16_t bsums[16]; };
static_assert(sizeof(Q4) == 1152 && sizeof(Q8) == 292, "Q4_Kx8/Q8_K layouts");
using Fn = void (*)(int, float *, size_t, const void *, const void *, int, int);
using Clock = std::chrono::steady_clock;
static volatile float sink;
static uint64_t state = 0x3ff2aa771239ull;
static uint64_t next() { state ^= state << 13; state ^= state >> 7; state ^= state << 17; return state; }
static void fail(const char * message) { std::fprintf(stderr, "%s\n", message); std::exit(1); }
static Fn load(const char * path) {
    void * handle = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!handle) { std::fprintf(stderr, "%s\n", dlerror()); std::exit(2); }
    auto fn = reinterpret_cast<Fn>(dlsym(handle, "ggml_gemv_q4_K_8x8_q8_K"));
    Dl_info info = {};
    if (!fn || !dladdr(reinterpret_cast<void *>(fn), &info) || !info.dli_fname || std::string(info.dli_fname) != path) fail("Actual-library function identity mismatch");
    return fn;
}
static void fill(Q4 * q4, size_t count4, Q8 * q8, size_t count8, int pattern) {
    const uint16_t halves[] = {0,0x8000,1,0x8001,0x03ff,0x0400,0x3c00,0xbc00,0x7bff,0xfbff,0x3555};
    for (size_t b=0; b<count4; ++b) {
        for (int i=0;i<8;++i) { q4[b].d[i]=halves[next()%11]; q4[b].dmin[i]=halves[next()%11]; }
        for (auto & v : q4[b].scales) v=uint8_t(next());
        for (size_t i=0;i<1024;++i) {
            uint8_t v=uint8_t(next());
            if (pattern==1) v=0;
            if (pattern==2) v=255;
            if (pattern==3) v=0x88;
            if (pattern==4) v=i%2?0xf0:0x0f;
            q4[b].qs[i]=v;
        }
    }
    for (size_t b=0;b<count8;++b) {
        q8[b].d=(pattern==1?0.0f:(pattern==5?-0.00003125f:0.00390625f));
        for (int i=0;i<256;++i) {
            int8_t v=int8_t(next());
            if (pattern==1) v=0;
            if (pattern==2) v=-128;
            if (pattern==3) v=127;
            if (pattern==4) v=i%2?-128:127;
            q8[b].qs[i]=v;
        }
        for (int i=0;i<16;++i) {
            int sum=0; for(int j=0;j<16;++j)sum+=q8[b].qs[16*i+j];
            q8[b].bsums[i]=pattern==6?int16_t(next()):int16_t(sum);
        }
    }
}
static void check(Fn base, Fn candidate, int n, int nc, const Q4 * x, const Q8 * y, uint64_t & cases, uint64_t & values) {
    std::vector<float> a(nc+16), b(nc+16), first(nc);
    for (int rep=0;rep<3;++rep) {
        std::fill(a.begin(),a.end(),12345.0f);std::fill(b.begin(),b.end(),12345.0f);
        base(n,a.data()+8,nc*sizeof(float),x,y,1,nc);
        candidate(n,b.data()+8,nc*sizeof(float),x,y,1,nc);
        for(int i=0;i<nc;++i) if(!std::isfinite(a[i+8])||!std::isfinite(b[i+8])) fail("Nonfinite result");
        if(std::memcmp(a.data(),b.data(),a.size()*sizeof(float))) fail("Bit mismatch baseline/candidate");
        for(int i=0;i<8;++i) if(a[i]!=12345.0f||a[nc+8+i]!=12345.0f) fail("Output guard overwritten");
        if(rep==0)std::memcpy(first.data(),a.data()+8,nc*sizeof(float));
        else if(std::memcmp(first.data(),a.data()+8,nc*sizeof(float)))fail("Not repeatable");
    }
    ++cases;values+=nc;
}
static double measure(Fn fn, int n, int nc, const Q4 * x, const Q8 * y, size_t sets, uint64_t calls) {
    std::vector<float> out(nc);
    size_t blocks=size_t(n/256)*(nc/8);
    const auto begin=Clock::now();
    for(uint64_t i=0;i<calls;++i) fn(n,out.data(),nc*sizeof(float),x+(i%sets)*blocks,y,1,nc);
    const auto end=Clock::now();sink=out.back();
    return std::chrono::duration<double,std::nano>(end-begin).count()/calls;
}
int main(int argc,char **argv) {
    if(argc!=4)return 2;
    const Fn baseline=load(argv[1]),candidate=load(argv[2]);
    if(baseline==candidate)fail("Aliased original and candidate function pointers");
    const std::string outdir=argv[3];
    uint64_t cases=0,values=0;
    for(int n : {256,512,768,1280,2560,6144,16384,32768}) for(int nc : {8,16,24,64,152,256}) for(int offset : {0,4,16}) for(int pattern=0;pattern<8;++pattern) {
        const size_t nb=n/256,count=nb*(nc/8);
        std::vector<uint8_t> xb(count*sizeof(Q4)+32),yb(nb*sizeof(Q8)+32);
        Q4 * x=reinterpret_cast<Q4 *>(xb.data()+offset);Q8 * y=reinterpret_cast<Q8 *>(yb.data()+offset);
        fill(x,count,y,nb,pattern);check(baseline,candidate,n,nc,x,y,cases,values);
    }
    Q4 x;Q8 y;fill(&x,1,&y,1,0);
    for(uint32_t bits=0;bits<65536;++bits) {
        if((bits&0x7c00)==0x7c00)continue;
        for(int field=0;field<2;++field) {
            for(int i=0;i<8;++i){x.d[i]=field==0?uint16_t(bits):uint16_t(0x3c00);x.dmin[i]=field==1?uint16_t(bits):uint16_t(0x3555);}
            check(baseline,candidate,256,8,&x,&y,cases,values);
        }
    }
    {
        std::ofstream f(outdir+"/q4-correctness.json");
        f<<"{\"status\":\"PASS\",\"cases\":"<<cases<<",\"values\":"<<values<<",\"bit_mismatches\":0,\"repetitions\":3,\"finite_half_patterns\":63488,\"scope\":\"actual original/candidate libraries; nr1; eight n values, six nc values, three byte offsets, eight raw patterns; all finite FP16 patterns in both d and dmin; guards and repeatability\"}\n";
    }
    std::ofstream f(outdir+"/q4-raw-samples.json");f<<"[";bool firstcase=true;
    for(int n : {2560,6144})for(int nc : {8,64})for(int streaming : {0,1}) {
        const size_t nb=n/256,blocks=nb*(nc/8),bytes=blocks*sizeof(Q4);
        const size_t sets=streaming?std::max<size_t>(2,(256u*1024u*1024u+bytes-1)/bytes):1;
        std::vector<Q4> weights(blocks*sets);std::vector<Q8> input(nb);
        fill(weights.data(),weights.size(),input.data(),nb,0);
        // Both functions see the same first-touched data and perform one full
        // traversal before timed rounds. Stream size is logical Q4 weight bytes.
        measure(baseline,n,nc,weights.data(),input.data(),sets,sets);
        measure(candidate,n,nc,weights.data(),input.data(),sets,sets);
        const double ns=measure(baseline,n,nc,weights.data(),input.data(),sets,std::max<size_t>(10,sets));
        uint64_t calls=std::max<uint64_t>(10,uint64_t(60000000.0/ns));
        if(streaming)calls=std::max<uint64_t>(sets,calls);
        std::vector<double> a,b;
        for(int round=0;round<10;++round) {
            double av,bv;
            if(round%2==0){av=measure(baseline,n,nc,weights.data(),input.data(),sets,calls);bv=measure(candidate,n,nc,weights.data(),input.data(),sets,calls);}
            else{bv=measure(candidate,n,nc,weights.data(),input.data(),sets,calls);av=measure(baseline,n,nc,weights.data(),input.data(),sets,calls);}
            a.push_back(av);b.push_back(bv);
        }
        if(!firstcase)f<<",";firstcase=false;
        f<<"{\"n\":"<<n<<",\"nc\":"<<nc<<",\"mode\":\""<<(streaming?"stream256MiB":"resident")<<"\",\"weight_bytes\":"<<bytes*sets<<",\"sets\":"<<sets<<",\"calls_per_round\":"<<calls<<",\"baseline\":[";
        for(size_t i=0;i<a.size();++i){if(i)f<<",";f<<a[i];}f<<"],\"candidate\":[";
        for(size_t i=0;i<b.size();++i){if(i)f<<",";f<<b[i];}f<<"]}";f.flush();
    }
    f<<"]\n";std::puts("Actual-library Q4 correctness and eight microbenchmark configurations complete");return 0;
}
