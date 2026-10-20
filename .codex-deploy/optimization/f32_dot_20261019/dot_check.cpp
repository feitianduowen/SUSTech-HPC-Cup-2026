#include "ggml.h"
#include "ggml-cpu.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cfloat>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

int main(int argc,char **argv) {
    if(argc!=2)return 2;
    ggml_cpu_init();
    auto fn=ggml_get_type_traits_cpu(GGML_TYPE_F32)->vec_dot;
    if(!fn)return 3;
    if(!std::strcmp(argv[1],"--check")) {
        std::vector<int> lengths;
        for(int n=0;n<=257;++n)lengths.push_back(n);
        for(int n:{383,384,511,512,767,768,1024,1536,2560,4096,6144,8192,16384})lengths.push_back(n);
        size_t cases=0,failures=0;
        long double max_normalized=0,max_ratio=0;
        for(int n:lengths)for(int offset:{0,1,3,7})for(int pattern=0;pattern<8;++pattern) {
            std::vector<float> ax(n+16),ay(n+16);
            float * x=ax.data()+offset,*y=ay.data()+((offset+3)%8);
            uint32_t state=0x54321u+uint32_t(n*17+offset+pattern*101);
            for(int i=0;i<n;++i) {
                state^=state<<13;state^=state>>17;state^=state<<5;
                x[i]=float(int(state%2001)-1000)/1000.0f;
                state^=state<<13;state^=state>>17;state^=state<<5;
                y[i]=float(int(state%2001)-1000)/1000.0f;
                if(pattern==1){x[i]=0;y[i]=1;}
                if(pattern==2){x[i]=1;y[i]=1;}
                if(pattern==3){x[i]=(i&1)?-1.0f:1.0f;y[i]=1.0f;}
                if(pattern==4){x[i]=std::ldexp(x[i],(i%17)-8);y[i]=std::ldexp(y[i],8-(i%17));}
                if(pattern==5){y[i]=x[i];}
                if(pattern==6){x[i]*=1e-15f;y[i]*=1e-15f;}
                if(pattern==7){x[i]=i==n-1?0.001f:((i&1)?-100.0f:100.0f);y[i]=1.0f;}
            }
            long double ref=0,magnitude=0;
            for(int i=0;i<n;++i){long double product=(long double)x[i]*(long double)y[i];ref+=product;magnitude+=std::fabs(product);}
            float value=0;fn(n,&value,0,x,0,y,0,1);
            const long double bound=4.0L*FLT_EPSILON*(n/64+80)*magnitude+1e-30L;
            const long double error=std::fabs((long double)value-ref);
            if(!std::isfinite(value)||error>bound){++failures;if(failures<5)std::fprintf(stderr,"n=%d offset=%d pattern=%d error=%Lg bound=%Lg\n",n,offset,pattern,error,bound);}
            max_ratio=std::max(max_ratio,error/bound);
            max_normalized=std::max(max_normalized,error/(magnitude+1e-30L));
            ++cases;
        }
        std::printf("{\"status\":\"%s\",\"cases\":%zu,\"failures\":%zu,\"max_normalized_absolute_error\":%.12Lg,\"max_error_bound_ratio\":%.12Lg,\"reference\":\"long double\",\"bound\":\"4*FLT_EPSILON*(n/64+80)*sum(abs(x*y))+1e-30\"}\n",failures?"FAIL":"PASS",cases,failures,max_normalized,max_ratio);
        return failures?4:0;
    }
    if(std::strcmp(argv[1],"--bench"))return 2;
    std::printf("[");bool first=true;volatile float sink=0;
    for(int n:{256,1024,2560,4096,16384}) {
        std::vector<float>x(n),y(n);
        for(int i=0;i<n;++i){x[i]=float((i*17)%127-63)/64.0f;y[i]=float((i*31)%113-56)/64.0f;}
        const int reps=std::max(500,20000000/n);
        float value;
        for(int i=0;i<100;++i)fn(n,&value,0,x.data(),0,y.data(),0,1);
        const auto begin=std::chrono::steady_clock::now();
        for(int i=0;i<reps;++i){fn(n,&value,0,x.data(),0,y.data(),0,1);sink=value;}
        const double ns=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-begin).count()/reps;
        if(!first)std::printf(",");first=false;
        std::printf("{\"n\":%d,\"repetitions\":%d,\"ns_per_call\":%.9g}",n,reps,ns);
    }
    std::printf("]\n");return std::isfinite(sink)?0:5;
}
