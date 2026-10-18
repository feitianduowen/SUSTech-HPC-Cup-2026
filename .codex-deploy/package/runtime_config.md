# Runtime configuration

Source: llama.cpp v0.6.0, d81235049384534c167caea52b85a694f6103d14. Model computation source is unmodified.

Final compilers: Intel Classic 2021.9.0.20230302 (icc/icpc), from oneAPI 2023.1. Modules: cmake/3.28.1, gcc/11.2.0, icc/2023.1.0. GCC provides standard headers and libstdc++; the project C/C++ translation units are compiled by Intel.

C flags: -gcc-name=/share/base/e5/gcc/11.2.0/bin/gcc -fp-model precise -no-ftz -xCORE-AVX512 -qsimd-honor-fp-model -diag-disable=10441.

C++ flags: -gxx-name=/share/base/e5/gcc/11.2.0/bin/g++ -fp-model precise -no-ftz -xCORE-AVX512 -qsimd-honor-fp-model -diag-disable=10441.

Release uses -O3 -DNDEBUG. GGML_NATIVE=ON, GGML_OPENMP=ON, GGML_BLAS=OFF. Accelerator backends are disabled. Both executable and shared-library linker flags are -Wl,--no-as-needed,/lib64/libm.so.6,--as-needed. System libm is linked first for scalar math consistency with the reference environment. OpenMP is Intel libiomp5, using -qopenmp.

All jobs request one 40-slot node from hg_6148 in ssc-cpu. The queue does not accept the LSF exclusive flag; all 40 slots on the selected 40-slot node are allocated to the job. Inference uses 38 threads. No additional PP/TG runtime tuning is applied.

Common environment: OMP_NUM_THREADS=38, OMP_DYNAMIC=FALSE, OMP_PROC_BIND=close, OMP_PLACES=cores, OPENBLAS_NUM_THREADS=38, MKL_NUM_THREADS=38, BLIS_NUM_THREADS=38.

PPL: -t 38 -tb 38 -ngl 0 -c 512 -b 512 -ub 256 -ctk f16 -ctv f16 --numa distribute --chunks 2 --no-warmup.

PP: -t 38 -ngl 0 -b 2048 -ub 512 -ctk f16 -ctv f16 --numa distribute -p 2048 -n 0 -r 10 -o json.

TG: -t 38 -ngl 0 -b 2048 -ub 512 -ctk f16 -ctv f16 --numa distribute -p 0 -n 128 -d 2048 -r 10 -o json.

Successful deployment validation: job 4335636 on r13n16. PPL=2.7767, relative difference +0.2563547082611084%, PASS. Server health, completion generation, and chat completion PASS. The temporary validation server exits after the checks. The service launcher is scripts/server.lsf.

The HTTP server is for interactive use, not competition scoring. It uses 38 compute threads, 2048 context, f16 KV, CPU only, and loopback binding. Full PP/TG performance benchmarks have not been run for this deployment.
