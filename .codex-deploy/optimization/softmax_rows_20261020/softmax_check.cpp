#include "ggml.h"
#include "ggml-cpu.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

struct Case {
    ggml_context * ctx;
    ggml_tensor * input;
    ggml_tensor * output;
    ggml_cgraph * graph;
    ggml_cplan plan;
    std::vector<uint8_t> work;
    std::vector<float> original;
    bool sinks;
    int cols,rows;
    Case(const int * shape,int mode,bool sink,bool broadcast,bool inplace,float scale,int threads,ggml_threadpool * pool) {
        const int c=shape[0],q=shape[1],h=shape[2],b=shape[3];
        cols=c;rows=q*h*b;sinks=sink;
        ggml_init_params ip={32u*1024u*1024u,nullptr,false};
        ctx=ggml_init(ip);
        input=ggml_new_tensor_4d(ctx,GGML_TYPE_F32,c,q,h,b);
        original.resize(c*rows);
        for(size_t i=0;i<original.size();++i)original[i]=float(int((i*37+17)%251)-125)/31.0f;
        std::memcpy(input->data,original.data(),original.size()*sizeof(float));
        ggml_tensor * mask=nullptr;
        if(mode) {
            const ggml_type mt=mode<=2?GGML_TYPE_F16:GGML_TYPE_F32;
            // Additional query rows test a mask whose head/batch strides differ.
            mask=ggml_new_tensor_4d(ctx,mt,c,q+3,broadcast?1:h,broadcast?1:b);
            for(int64_t i=0;i<ggml_nelements(mask);++i) {
                float value=float(-int((i*13)%23))/8.0f;
                if(i%c && i%11==0)value=-INFINITY; // every row retains a finite entry
                if(mt==GGML_TYPE_F16)((ggml_fp16_t *)mask->data)[i]=ggml_fp32_to_fp16(value);
                else ((float *)mask->data)[i]=value;
            }
        }
        const float bias=(mode==2||mode==4)?8.0f:0.0f;
        output=inplace?ggml_soft_max_ext_inplace(ctx,input,mask,scale,bias):ggml_soft_max_ext(ctx,input,mask,scale,bias);
        if(sink) {
            auto * sk=ggml_new_tensor_1d(ctx,GGML_TYPE_F32,h);
            for(int i=0;i<h;++i)((float *)sk->data)[i]=float(i%7-3)/4.0f;
            ggml_soft_max_add_sinks(output,sk);
        }
        graph=ggml_new_graph(ctx);ggml_build_forward_expand(graph,output);
        plan=ggml_graph_plan(graph,threads,pool);
        work.resize(plan.work_size);plan.work_data=work.data();
    }
    ~Case(){ggml_free(ctx);}
    void reset(){std::memcpy(input->data,original.data(),original.size()*sizeof(float));}
    void run(){if(ggml_graph_compute(graph,&plan)!=GGML_STATUS_SUCCESS)std::abort();}
    bool valid() {
        const float * p=ggml_get_data_f32(output);
        for(int r=0;r<rows;++r) {
            double sum=0;
            for(int i=0;i<cols;++i){float v=p[r*cols+i];if(!std::isfinite(v)||v<0||v>1.00001f)return false;sum+=v;}
            if(sinks ? !(sum>0&&sum<=1.00002) : std::fabs(sum-1.0)>2e-5)return false;
        }
        return true;
    }
};

int main(int argc,char **argv) {
    if(argc<2)return 2;
    ggml_cpu_init();
    if(!std::strcmp(argv[1],"--check")) {
        if(argc!=3)return 2;
        FILE * f=std::fopen(argv[2],"wb");if(!f)return 3;
        const int shapes[][4]={{1,1,1,1},{31,1,8,1},{128,1,40,2},{512,2,8,1},{257,3,4,2},{32,37,2,1},{32,38,3,1},{32,39,2,2}};
        size_t cases=0,values=0;
        for(int threads:{1,38}) {
            auto pp=ggml_threadpool_params_default(threads);
            auto * pool=ggml_threadpool_new(&pp);if(!pool)return 4;
            for(const auto & shape:shapes)for(int mode=0;mode<5;++mode)
            for(bool sink:{false,true})for(bool broadcast:{false,true})
            for(bool inplace:{false,true})for(float scale:{1.0f,0.125f}) {
                Case c(shape,mode,sink,broadcast,inplace,scale,threads,pool);
                const size_t bytes=ggml_nbytes(c.output);
                std::vector<uint8_t> first(bytes);
                for(int rep=0;rep<3;++rep) {
                    c.reset();c.run();
                    if(!c.valid())return 5;
                    if(rep==0)std::memcpy(first.data(),c.output->data,bytes);
                    else if(std::memcmp(first.data(),c.output->data,bytes))return 6;
                }
                if(std::fwrite(first.data(),1,bytes,f)!=bytes)return 7;
                ++cases;values+=bytes/sizeof(float);
            }
            ggml_threadpool_free(pool);
        }
        if(std::fclose(f))return 8;
        std::printf("{\"status\":\"PASS\",\"cases\":%zu,\"values\":%zu,\"repetitions\":3,\"threads\":[1,38],\"checks\":\"finite, range, row normalization, repeatable; cross-build comparison required\"}\n",cases,values);
        return 0;
    }
    if(std::strcmp(argv[1],"--bench"))return 2;
    const int shapes[][4]={{2048,1,32,1},{2048,4,32,1},{512,32,8,1},{512,128,8,1}};
    auto pp=ggml_threadpool_params_default(38);auto * pool=ggml_threadpool_new(&pp);
    if(!pool)return 4;
    std::printf("[");bool first=true;
    for(const auto & shape:shapes) {
        Case c(shape,1,false,true,false,0.125f,38,pool);
        for(int i=0;i<5;++i)c.run();
        const int repeats=20;
        const auto start=std::chrono::steady_clock::now();
        for(int i=0;i<repeats;++i)c.run();
        const double ns=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-start).count()/repeats;
        if(!c.valid())return 5;
        if(!first)std::printf(",");first=false;
        std::printf("{\"shape\":[%d,%d,%d,%d],\"threads\":38,\"repetitions\":%d,\"ns_per_graph\":%.9g}",shape[0],shape[1],shape[2],shape[3],repeats,ns);
    }
    std::printf("]\n");ggml_threadpool_free(pool);return 0;
}
