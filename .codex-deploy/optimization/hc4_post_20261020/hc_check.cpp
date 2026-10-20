#include "ggml.h"
#include "ggml-cpu.h"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

static float & at(ggml_tensor * t, int a, int b=0, int c=0) {
    return *(float *) ((char *) t->data + a*t->nb[0] + b*t->nb[1] + c*t->nb[2]);
}

struct Case {
    ggml_context * ctx;
    ggml_tensor * x, * residual, * post, * comb, * output;
    ggml_cgraph * graph;
    ggml_cplan plan;
    std::vector<uint8_t> work;
    int embd, hc, tokens;

    Case(int e,int h,int t,int layout,int mixing,int threads,ggml_threadpool * pool):embd(e),hc(h),tokens(t) {
        ggml_init_params ip={128u*1024u*1024u,nullptr,false};
        ctx=ggml_init(ip);if(!ctx)std::abort();
        if(layout==0) {
            x=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,e,t);
            residual=ggml_new_tensor_3d(ctx,GGML_TYPE_F32,e,h,t);
            post=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,h,t);
            comb=mixing?ggml_new_tensor_3d(ctx,GGML_TYPE_F32,h,h,t):nullptr;
        } else if(layout==1) {
            auto * xb=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,e+7,t);
            x=ggml_view_2d(ctx,xb,e,t,xb->nb[1],sizeof(float));
            auto * rb=ggml_new_tensor_3d(ctx,GGML_TYPE_F32,e+5,h+1,t);
            residual=ggml_view_3d(ctx,rb,e,h,t,rb->nb[1],rb->nb[2],sizeof(float));
            auto * pb=ggml_new_tensor_2d(ctx,GGML_TYPE_F32,h+3,t);
            post=ggml_view_2d(ctx,pb,h,t,pb->nb[1],sizeof(float));
            if(mixing) {
                auto * cb=ggml_new_tensor_3d(ctx,GGML_TYPE_F32,h+3,h+1,t);
                comb=ggml_view_3d(ctx,cb,h,h,t,cb->nb[1],cb->nb[2],sizeof(float));
            } else comb=nullptr;
        } else {
            x=ggml_transpose(ctx,ggml_new_tensor_2d(ctx,GGML_TYPE_F32,t,e));
            residual=ggml_permute(ctx,ggml_new_tensor_3d(ctx,GGML_TYPE_F32,h,e,t),1,0,2,3);
            post=ggml_transpose(ctx,ggml_new_tensor_2d(ctx,GGML_TYPE_F32,t,h));
            comb=mixing?ggml_permute(ctx,ggml_new_tensor_3d(ctx,GGML_TYPE_F32,h,h,t),1,0,2,3):nullptr;
        }
        for(int k=0;k<t;++k) {
            for(int i=0;i<e;++i)at(x,i,k)=float((i*37+k*11)%251-125)/31.0f;
            for(int j=0;j<h;++j) {
                at(post,j,k)=float((j*13+k*7)%23-11)/9.0f;
                for(int i=0;i<e;++i) {
                    const float scale=(i%3==0)?0.001f:(i%3==1)?1.0f:1000.0f;
                    at(residual,i,j,k)=scale*float((i*17+j*19+k*5)%127-63)/17.0f;
                }
                if(comb)for(int s=0;s<h;++s)at(comb,j,s,k)=mixing==1?float(j==s):float((j*7+s*11+k*13)%29-14)/19.0f;
            }
        }
        output=ggml_dsv4_hc_post(ctx,x,residual,post,comb);
        graph=ggml_new_graph(ctx);ggml_build_forward_expand(graph,output);
        plan=ggml_graph_plan(graph,threads,pool);work.resize(plan.work_size);plan.work_data=work.data();
    }
    ~Case(){ggml_free(ctx);}
    void run(){if(ggml_graph_compute(graph,&plan)!=GGML_STATUS_SUCCESS)std::abort();}
    bool valid() {
        for(int k=0;k<tokens;++k)for(int j=0;j<hc;++j)for(int i=0;i<embd;++i) {
            double expected=double(at(x,i,k))*at(post,j,k);
            double magnitude=std::fabs(expected);
            if(comb)for(int s=0;s<hc;++s) {
                const double term=double(at(residual,i,s,k))*at(comb,j,s,k);
                expected+=term;magnitude+=std::fabs(term);
            } else {expected+=at(residual,i,j,k);magnitude+=std::fabs(at(residual,i,j,k));}
            const float actual=at(output,i,j,k);
            if(!std::isfinite(actual)||std::fabs(double(actual)-expected)>2e-6*magnitude+1e-7) {
                std::fprintf(stderr,"oracle failure e=%d h=%d t=%d at=%d,%d,%d actual=%g expected=%.17g\n",embd,hc,tokens,i,j,k,actual,expected);
                return false;
            }
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
        const int shapes[][2]={{1,1},{7,3},{16,1},{31,39},{32,3},{33,1},{257,3},{2560,1},{2560,39}};
        size_t cases=0,values=0;
        for(int threads:{1,3,38}) {
            auto pp=ggml_threadpool_params_default(threads);
            auto * pool=ggml_threadpool_new(&pp);if(!pool)return 4;
            for(const auto & shape:shapes)for(int hc:{1,2,4,8})
            for(int layout:{0,1,2})for(int mixing:{0,1,2}) {
                Case c(shape[0],hc,shape[1],layout,mixing,threads,pool);
                const size_t bytes=ggml_nbytes(c.output);
                std::vector<uint8_t> first(bytes);
                for(int rep=0;rep<3;++rep) {
                    c.run();
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
        std::printf("{\"status\":\"PASS\",\"cases\":%zu,\"values\":%zu,\"repetitions\":3,\"threads\":[1,3,38],\"checks\":\"finite, double oracle, repeatable; cross-build bit comparison required\"}\n",cases,values);
        return 0;
    }
    if(std::strcmp(argv[1],"--bench"))return 2;
    const int shapes[][3]={{2560,4,1},{2560,4,32},{2560,4,512},{10240,4,1}};
    auto pp=ggml_threadpool_params_default(38);auto * pool=ggml_threadpool_new(&pp);if(!pool)return 4;
    std::printf("[");bool first=true;
    for(const auto & shape:shapes) {
        Case c(shape[0],shape[1],shape[2],0,2,38,pool);
        for(int i=0;i<5;++i)c.run();
        const int repeats=40;
        const auto start=std::chrono::steady_clock::now();
        for(int i=0;i<repeats;++i)c.run();
        const double ns=std::chrono::duration<double,std::nano>(std::chrono::steady_clock::now()-start).count()/repeats;
        if(!c.valid())return 5;
        if(!first)std::printf(",");first=false;
        std::printf("{\"shape\":[%d,%d,%d],\"threads\":38,\"repetitions\":%d,\"ns_per_graph\":%.9g}",shape[0],shape[1],shape[2],repeats,ns);
    }
    std::printf("]\n");ggml_threadpool_free(pool);return 0;
}
