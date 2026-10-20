#include "ggml.h"
#include "ggml-cpu.h"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <vector>

static void fill(ggml_tensor * t, int salt) {
    const int64_t count=ggml_nelements(t);
    std::vector<float> v(count);
    for (int64_t i=0;i<count;++i) v[i]=float(int((i*37+salt*17)%251)-125)/127.0f;
    const size_t n=ggml_quantize_chunk(t->type,v.data(),t->data,0,count/t->ne[0],t->ne[0],nullptr);
    if (n!=ggml_nbytes(t)) std::abort();
}
int main(int argc,char **argv) {
    if(argc!=2)return 2;
    FILE * f=std::fopen(argv[1],"wb");
    if(!f)return 3;
    ggml_cpu_init();
    const ggml_type types[]={GGML_TYPE_F32,GGML_TYPE_F16,GGML_TYPE_BF16,GGML_TYPE_Q8_0,GGML_TYPE_Q4_0,GGML_TYPE_Q4_1,GGML_TYPE_Q5_1,GGML_TYPE_Q4_K};
    const int shapes[][4]={{4,1,256,1},{7,3,256,1},{152,4,256,1},{64,7,512,1},{152,37,256,1},{152,38,256,1},{152,39,256,1},{64,64,512,2},{156,128,256,1}};
    size_t cases=0,values=0;
    for (int threads : {1,38}) {
        auto pp=ggml_threadpool_params_default(threads);
        auto * pool=ggml_threadpool_new(&pp);
        if(!pool)return 4;
        for (ggml_type type : types) for (const auto & shape : shapes) {
            const int m=shape[0],n=shape[1],k=shape[2],batch=shape[3];
            ggml_init_params ip={32u*1024u*1024u,nullptr,false};
            auto * ctx=ggml_init(ip);
            auto * a=ggml_new_tensor_3d(ctx,type,k,m,batch);
            auto * b=ggml_new_tensor_3d(ctx,GGML_TYPE_F32,k,n,batch);
            fill(a,1);fill(b,2);
            auto * y=ggml_mul_mat(ctx,a,b);
            auto * g=ggml_new_graph(ctx);ggml_build_forward_expand(g,y);
            auto plan=ggml_graph_plan(g,threads,pool);
            std::vector<uint8_t> work(plan.work_size);plan.work_data=work.data();
            const size_t count=ggml_nelements(y),bytes=count*sizeof(float);
            std::vector<uint8_t> first(bytes);
            for (int rep=0;rep<3;++rep) {
                std::memset(y->data,0xff,bytes);
                if(ggml_graph_compute(g,&plan)!=GGML_STATUS_SUCCESS)return 5;
                const float * p=ggml_get_data_f32(y);
                for(size_t j=0;j<count;++j)if(!std::isfinite(p[j]))return 6;
                if(rep==0)std::memcpy(first.data(),p,bytes);
                else if(std::memcmp(first.data(),p,bytes))return 7;
            }
            if(std::fwrite(y->data,1,bytes,f)!=bytes)return 8;
            values+=count;++cases;
            ggml_free(ctx);
        }
        ggml_threadpool_free(pool);
    }
    std::fclose(f);
    std::printf("{\"status\":\"PASS\",\"cases\":%zu,\"values\":%zu,\"repetitions\":3,\"threads\":[1,38]}\n",cases,values);
    return 0;
}
