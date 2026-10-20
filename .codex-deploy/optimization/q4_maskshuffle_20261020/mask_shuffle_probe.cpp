#include <immintrin.h>
#include <cstdint>
#include <cstring>
#include <cstdio>
int main() {
#if !defined(__AVX512F__) || !defined(__AVX512VL__)
    return 2;
#else
    uint64_t state=1238919837;
    for(int rep=0;rep<4096;++rep) {
        uint32_t a[8],b[8],x[8],y[8];
        for(int i=0;i<8;++i){state^=state<<13;state^=state>>7;state^=state<<17;a[i]=uint32_t(state);b[i]=uint32_t(state>>32);}
        __m256i av=_mm256_loadu_si256((__m256i *)a),bv=_mm256_loadu_si256((__m256i *)b);
        __m256i old0=_mm256_blend_epi32(av,_mm256_shuffle_epi32(bv,177),170);
        __m256i old1=_mm256_blend_epi32(_mm256_shuffle_epi32(av,177),bv,170);
        __m256i new0=_mm256_mask_shuffle_epi32(av,(__mmask8)0xAA,bv,177);
        __m256i new1=_mm256_mask_shuffle_epi32(bv,(__mmask8)0x55,av,177);
        _mm256_storeu_si256((__m256i *)x,old0);_mm256_storeu_si256((__m256i *)y,new0);
        if(std::memcmp(x,y,sizeof(x)))return 3;
        for(int i=0;i<8;++i)if(y[i]!=(i%2?b[i-1]:a[i]))return 4;
        _mm256_storeu_si256((__m256i *)x,old1);_mm256_storeu_si256((__m256i *)y,new1);
        if(std::memcmp(x,y,sizeof(x)))return 5;
        for(int i=0;i<8;++i)if(y[i]!=(i%2?b[i]:a[i+1]))return 6;
    }
    std::puts("{\"status\":\"PASS\",\"cases\":4096,\"lane_bit_mismatches\":0}");return 0;
#endif
}
