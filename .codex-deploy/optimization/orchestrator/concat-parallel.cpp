#include "ggml.h"
#include "ggml-cpu.h"
#include "ggml-cpu-impl.h"
#include <cstdio>
#include <cstring>
#include <cstdint>
#include <dlfcn.h>
#include <omp.h>
#include <initializer_list>

typedef void (*concat_fn)(const ggml_compute_params *, ggml_tensor *);
static uint32_t random_state = 123456789;
static uint32_t random_bits() {
    random_state ^= random_state << 13;
    random_state ^= random_state >> 17;
    random_state ^= random_state << 5;
    return random_state;
}

static ggml_tensor * tensor(ggml_context * ctx, ggml_type type, const int64_t * dims, int padded) {
    if(padded==2) {
        ggml_tensor * storage=ggml_new_tensor_4d(ctx,type,dims[1],dims[0],dims[2],dims[3]);
        return ggml_transpose(ctx,storage);
    }
    ggml_tensor * storage = ggml_new_tensor_4d(ctx,type,dims[0]+(padded ? 7 : 0),dims[1],dims[2],dims[3]);
    return ggml_view_4d(ctx,storage,dims[0],dims[1],dims[2],dims[3],storage->nb[1],storage->nb[2],storage->nb[3],0);
}

static void fill(ggml_tensor * t) {
    for (int64_t i3=0;i3<t->ne[3];++i3) for(int64_t i2=0;i2<t->ne[2];++i2) for(int64_t i1=0;i1<t->ne[1];++i1) for(int64_t i0=0;i0<t->ne[0];++i0) {
        uint32_t value=random_bits();
        std::memcpy((char *)t->data+i0*t->nb[0]+i1*t->nb[1]+i2*t->nb[2]+i3*t->nb[3],&value,4);
    }
}

int main(int argc,char ** argv) {
    if(argc!=3) return 2;
    void * libs[2]={dlopen(argv[1],RTLD_NOW|RTLD_LOCAL),dlopen(argv[2],RTLD_NOW|RTLD_LOCAL)};
    concat_fn funcs[2];
    for(int i=0;i<2;++i) {
        if(!libs[i]) { std::fprintf(stderr,"dlopen: %s\n",dlerror()); return 2; }
        void * sym=dlsym(libs[i],"ggml_compute_forward_concat");
        if(!sym || sizeof(sym)!=sizeof(funcs[i])) { std::fprintf(stderr,"missing concat symbol\n");return 2; }
        std::memcpy(&funcs[i],&sym,sizeof(sym));
    }
    ggml_cpu_init();
    int cases=0;
    const int threads[]={1,3,38};
    for(int dtype=0;dtype<2;++dtype) for(int dim=0;dim<4;++dim) for(int padded=0;padded<3;++padded) for(int shape=0;shape<3;++shape) for(int nth:threads) {
        ggml_init_params ip={64*1024*1024,nullptr,false};
        ggml_context * ctx=ggml_init(ip);
        if(!ctx) return 2;
        int64_t dims0[]={5,7,2,2};
        if(shape==1) { dims0[0]=9;dims0[1]=127;dims0[2]=1;dims0[3]=1; }
        if(shape==2) { dims0[0]=128;dims0[1]=38;dims0[2]=1;dims0[3]=1; }
        int64_t dims1[4];std::memcpy(dims1,dims0,sizeof(dims0));dims1[dim]+=3;
        ggml_type type=dtype ? GGML_TYPE_I32 : GGML_TYPE_F32;
        ggml_tensor * a=tensor(ctx,type,dims0,padded);
        ggml_tensor * b=tensor(ctx,type,dims1,padded);
        fill(a);fill(b);
        ggml_tensor * outputs[2]={ggml_concat(ctx,a,b,dim),ggml_concat(ctx,a,b,dim)};
        for(int which=0;which<2;++which) {
            if(padded) {
                ggml_tensor * op=outputs[which];
                outputs[which]=tensor(ctx,type,op->ne,1);
                outputs[which]->op=op->op;
                std::memcpy(outputs[which]->op_params,op->op_params,sizeof(op->op_params));
                outputs[which]->src[0]=a;
                outputs[which]->src[1]=b;
            }
            std::memset(outputs[which]->data,0xcd,ggml_nbytes(outputs[which]));
            #pragma omp parallel for num_threads(nth)
            for(int ith=0;ith<nth;++ith) {
                ggml_compute_params params={};params.ith=ith;params.nth=nth;
                funcs[which](&params,outputs[which]);
            }
        }
        if(std::memcmp(outputs[0]->data,outputs[1]->data,ggml_nbytes(outputs[0]))) {
            std::fprintf(stderr,"FAIL type=%d dim=%d padded=%d shape=%d threads=%d\n",dtype,dim,padded,shape,nth);return 1;
        }
        ++cases;
        ggml_free(ctx);
    }
    std::printf("PASS %d actual-library concat differential cases, F32/I32 raw bits, all axes, padded rows, 1/3/38 tasks\n",cases);

    for (int tail : {1, 512}) for (int prefix : {3, 9}) {
        ggml_init_params ip={256*1024*1024,nullptr,false};
        ggml_context * ctx=ggml_init(ip);
        if (!ctx) return 2;
        ggml_tensor * a=ggml_new_tensor_4d(ctx,GGML_TYPE_F32,prefix,10240,1,1);
        ggml_tensor * b=ggml_new_tensor_4d(ctx,GGML_TYPE_F32,tail,10240,1,1);
        fill(a); fill(b);
        ggml_tensor * outputs[]={ggml_concat(ctx,a,b,0),ggml_concat(ctx,a,b,0)};
        for(int which=0;which<2;++which) {
            std::memset(outputs[which]->data,0xcd,ggml_nbytes(outputs[which]));
        }
        for(int round=-1;round<5;++round) for(int order=0;order<2;++order) {
            const int which=(order+(round<0?0:round))%2;
            const double start=omp_get_wtime();
            for(int rep=0;rep<10;++rep) {
                #pragma omp parallel num_threads(38)
                {
                    ggml_compute_params params={};
                    params.ith=omp_get_thread_num(); params.nth=omp_get_num_threads();
                    funcs[which](&params,outputs[which]);
                }
            }
            const double seconds=(omp_get_wtime()-start)/10;
            if(round>=0) std::printf("timing,%d,%d,10240,38,%d,%s,%.9f\n",prefix,tail,round,which?"candidate":"reference",seconds);
        }
        if(std::memcmp(outputs[0]->data,outputs[1]->data,ggml_nbytes(outputs[0]))) {
            std::fprintf(stderr,"real-shape concurrent mismatch\n");return 1;
        }
        ggml_free(ctx);
    }
    for(void * lib:libs) dlclose(lib);
    return 0;
}
