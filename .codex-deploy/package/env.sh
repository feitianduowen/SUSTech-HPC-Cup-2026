#!/bin/bash
export QWEN_DEPLOY=/work/apac2602/qwen38-cpu
export LLAMA_CPP_DIR="$QWEN_DEPLOY/llama.cpp"
export MODEL=/work/ssc-zhaojh/llama_model/unsloth/Qwen3.8-Flash-Next-GGUF/UD-Q4_K_XL/Qwen3.8-Flash-Next-UD-Q4_K_XL-00001-of-00004.gguf
export PPL_DATA=/work/ssc-zhaojh/llama_model/unsloth/Qwen3.8-Flash-Next-GGUF/wikitext-2-raw/wiki.test.raw
export PPL_BASELINE_JSON=/work/ssc-zhaojh/llama_model/unsloth/Qwen3.8-Flash-Next-GGUF/perplexity_result.json
module use /share/intel/oneapi-2023.1/modulefiles
module load cmake/3.28.1 gcc/11.2.0 icc/2023.1.0
export CC=icc
export CXX=icpc
export PATH="$LLAMA_CPP_DIR/build/bin:$PATH"
export OMP_NUM_THREADS=38
export OMP_DYNAMIC=FALSE
export OMP_PROC_BIND=close
export OMP_PLACES=cores
export OPENBLAS_NUM_THREADS=38
export MKL_NUM_THREADS=38
export BLIS_NUM_THREADS=38
