from pathlib import Path

root = Path(__file__).parent
source = (root/'concat-diff.cpp').read_text()
source = source.replace('#include <dlfcn.h>', '#include <dlfcn.h>\n#include <omp.h>')
source = source.replace('            for(int ith=0;ith<nth;++ith) {', '            #pragma omp parallel for num_threads(nth)\n            for(int ith=0;ith<nth;++ith) {')
timing = r'''
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
'''
source = source.replace('#include <omp.h>', '#include <omp.h>\n#include <initializer_list>')
source = source.replace('    for(void * lib:libs) dlclose(lib);',timing+'    for(void * lib:libs) dlclose(lib);')
(root/'concat-parallel.cpp').write_bytes(source.encode())
lsf = (root/'concat_test.lsf').read_text()
lsf = lsf.replace('qwen38_concat_test','qwen38_concat_parallel').replace('concat_test_', 'concat_parallel_')
lsf = lsf.replace(' -std=c++17 -O2 ', ' -std=c++17 -O2 -qopenmp ')
lsf = lsf.replace('concat-diff.cpp', 'concat-parallel.cpp')
(root/'concat_parallel.lsf').write_bytes(lsf.encode())
