#include "ggml.h"
#include "ggml-cpu.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <vector>

// Match the public type sizes; memcpy keeps deliberately non-vector-aligned
// buffers valid without violating C++ object lifetime or aliasing rules.
struct Q5 { uint16_t d,m; uint8_t qh[4],qs[16]; };
struct Q8 { uint16_t d,s; int8_t qs[32]; };
static_assert(sizeof(Q5)==24 && sizeof(Q8)==36,"quantized block layout");
static uint32_t next(uint32_t & s){s^=s<<13;s^=s>>17;s^=s<<5;return s;}
static void fill(uint8_t * x,uint8_t * y,int blocks,int pattern,uint32_t state) {
    for(int b=0;b<blocks;++b) {
        Q5 a={};Q8 c={};
        const float d=std::ldexp(1.0f,pattern==7?(b%15)-10:-5);
        a.d=ggml_fp32_to_fp16(d);a.m=ggml_fp32_to_fp16(-d*16);
        c.d=ggml_fp32_to_fp16(std::ldexp(1.0f,pattern==7?3-(b%9):-6));
        uint32_t bits=next(state);
        if(pattern==1)bits=0;
        if(pattern==2)bits=0xffffffffu;
        if(pattern==3)bits=0xaaaaaaaau;
        if(pattern==4)bits=0x55555555u;
        if(pattern==5)bits=uint32_t(1)<<(b%32);
        if(pattern==6)bits=~(uint32_t(1)<<(b%32));
        std::memcpy(a.qh,&bits,4);
        for(int j=0;j<16;++j)a.qs[j]=uint8_t(next(state));
        int sum=0;
        for(int j=0;j<32;++j){c.qs[j]=int8_t(int(next(state)%256)-128);sum+=c.qs[j];}
        c.s=ggml_fp32_to_fp16(ggml_fp16_to_fp32(c.d)*sum);
        if(pattern==1){a.d=a.m=0;std::memset(a.qs,0,16);}
        std::memcpy(x+b*sizeof(Q5),&a,sizeof(a));
        std::memcpy(y+b*sizeof(Q8),&c,sizeof(c));
    }
}
int main(int argc,char **argv) {
    if(argc<2)return 2;
    ggml_cpu_init();
    if(ggml_type_size(GGML_TYPE_Q5_1)!=sizeof(Q5)||ggml_type_size(GGML_TYPE_Q8_1)!=sizeof(Q8))return 3;
    auto fn=ggml_get_type_traits_cpu(GGML_TYPE_Q5_1)->vec_dot;
    if(!fn||ggml_get_type_traits_cpu(GGML_TYPE_Q5_1)->vec_dot_type!=GGML_TYPE_Q8_1)return 4;
    if(!std::strcmp(argv[1],"--check")) {
        if(argc!=3)return 2;
        FILE * out=std::fopen(argv[2],"wb");if(!out)return 5;
        std::vector<int> lengths;
        for(int nb=0;nb<=257;++nb)lengths.push_back(nb);
        for(int nb:{383,384,511,512,767,768,1024})lengths.push_back(nb);
        size_t cases=0;
        for(int nb:lengths)for(int offset:{0,2,6,14})for(int pattern=0;pattern<8;++pattern) {
            std::vector<uint8_t> ax(nb*sizeof(Q5)+64),ay(nb*sizeof(Q8)+64);
            auto * x=ax.data()+offset;auto * y=ay.data()+((offset+4)%16);
            fill(x,y,nb,pattern,0x314159u+uint32_t(nb*17+offset+pattern*101));
            float first=0;
            for(int repeat=0;repeat<3;++repeat){
                float value=0;fn(nb*32,&value,0,x,0,y,0,1);
                if(!std::isfinite(value))return 6;
                if(repeat==0)first=value;
                else if(std::memcmp(&value,&first,4))return 7;
            }
            if(std::fwrite(&first,4,1,out)!=1)return 8;
            ++cases;
        }
        if(std::fclose(out))return 9;
        std::printf("{\"status\":\"PASS\",\"cases\":%zu,\"repetitions\":3,\"failures\":0,\"scope\":\"finite and repeatable; cross-library bit comparison required\"}\n",cases);
        return 0;
    }
    if(std::strcmp(argv[1],"--bench"))return 2;
    std::printf("[");bool first=true;volatile float sink=0;
    for(int n:{256,1024,2560,6144,16384}) {
        std::vector<uint8_t> x(n/32*sizeof(Q5)),y(n/32*sizeof(Q8));
        fill(x.data(),y.data(),n/32,0,0x314159u);
        const int reps=std::max(1000,80000000/n);
        float value;
        for(int i=0;i<1000;++i)fn(n,&value,0,x.data(),0,y.data(),0,1);
        const auto begin=std::chrono::steady_clock::now();
        for(int i=0;i<reps;++i){fn(n,&value,0,x.data(),0,y.data(),0,1);sink=value;}
        const double ns=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-begin).count()/reps;
        if(!first)std::printf(",");first=false;
        std::printf("{\"n\":%d,\"repetitions\":%d,\"ns_per_call\":%.9g}",n,reps,ns);
    }
    std::printf("]\n");return std::isfinite(sink)?0:10;
}
