#include "ggml.h"
#include "ggml-cpu.h"
#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

int main(int argc, char ** argv) {
    if (argc != 3) return 2;
    const int threads = std::atoi(argv[1]);
    const int repetitions = std::atoi(argv[2]);
    if ((threads != 1 && threads != 38) || repetitions < 1) return 2;
    ggml_cpu_init();
    ggml_init_params parameters = {64u*1024u*1024u, nullptr, false};
    ggml_context * context = ggml_init(parameters);
    if (!context) return 3;
    ggml_tensor * a = ggml_new_tensor_2d(context, GGML_TYPE_F32, 256, 256);
    ggml_tensor * b = ggml_new_tensor_2d(context, GGML_TYPE_F32, 256, 64);
    ggml_set_f32(a,1.0f);
    ggml_set_f32(b,2.0f);
    ggml_tensor * output = ggml_mul_mat(context,a,b);
    ggml_tensor * bias = ggml_new_tensor_2d(context,GGML_TYPE_F32,256,64);
    ggml_set_f32(bias,1.0f);
    for (int i=0; i<16; ++i) output = ggml_add(context,output,bias);
    ggml_cgraph * graph = ggml_new_graph(context);
    ggml_build_forward_expand(graph,output);
    ggml_threadpool_params pool_parameters = ggml_threadpool_params_default(threads);
    ggml_threadpool * pool = ggml_threadpool_new(&pool_parameters);
    if (!pool) return 3;
    ggml_cplan plan = ggml_graph_plan(graph,threads,pool);
    std::vector<uint8_t> work(plan.work_size);
    plan.work_data = work.data();
    std::fprintf(stderr,"READY threads=%d repetitions=%d work_bytes=%zu\n",threads,repetitions,plan.work_size);
    std::fflush(stderr);
    const auto begin=std::chrono::steady_clock::now();
    for (int i=0; i<repetitions; ++i) {
        if (ggml_graph_compute(graph,&plan)!=GGML_STATUS_SUCCESS) return 4;
    }
    const double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
    const float * data=ggml_get_data_f32(output);
    size_t mismatches=0;
    for (int i=0; i<256*64; ++i) mismatches += data[i]!=528.0f;
    std::printf("{\"threads\":%d,\"repetitions\":%d,\"seconds\":%.9g,\"mismatches\":%zu,\"status\":\"%s\"}\n",threads,repetitions,seconds,mismatches,mismatches ? "FAIL" : "PASS");
    ggml_threadpool_free(pool);
    ggml_free(context);
    return mismatches ? 5 : 0;
}
