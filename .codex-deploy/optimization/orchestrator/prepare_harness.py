from pathlib import Path

root = Path(__file__).parent
s = Path('D:/compete/.codex-deploy/package/benchmark.lsf').read_text(encoding='utf-8')
s = s.replace('#BSUB -J llama_bench_ppl_38t', '#BSUB -J qwen38_candidate_bench')
needle = 'source /work/apac2602/qwen38-cpu/scripts/env.sh'
s = s.replace(needle, needle + '''
EXPERIMENT_ROOT=/work/apac2602/qwen38-cpu/optimization/20261018-v1
EXPERIMENT_VARIANT=${EXPERIMENT_VARIANT:?set EXPERIMENT_VARIANT}
LLAMA_CPP_DIR=${EXPERIMENT_ROOT}/sources/${EXPERIMENT_VARIANT}
if [[ "$EXPERIMENT_VARIANT" == baseline ]]; then
    LLAMA_CPP_DIR=/work/apac2602/qwen38-cpu/llama.cpp
fi
if [[ "$EXPERIMENT_VARIANT" == mkl || "$EXPERIMENT_VARIANT" == ipo ]]; then
    LLAMA_CPP_DIR=${EXPERIMENT_ROOT}/variants/${EXPERIMENT_VARIANT}
fi
''')
s = s.replace('RESULT_DIR="${LS_SUBCWD:-$PWD}/llama_bench_results_${LSB_JOBID:-manual}"', 'RESULT_DIR="${EXPERIMENT_OUTPUT_DIR:-${EXPERIMENT_ROOT}/results/${EXPERIMENT_VARIANT}_${LSB_JOBID}}"')
(root/'benchmark_variant.lsf').write_bytes(s.encode('utf-8'))

runtime = Path('D:/compete/.codex-deploy/package/benchmark.lsf').read_text(encoding='utf-8')
runtime = runtime.replace('#BSUB -J llama_bench_ppl_38t', '#BSUB -J qwen38_runtime_bench')
runtime = runtime.replace('RESULT_DIR="${LS_SUBCWD:-$PWD}/llama_bench_results_${LSB_JOBID:-manual}"', 'RESULT_DIR="/work/apac2602/qwen38-cpu/optimization/20261018-v1/results/runtime_${EXPERIMENT_POLICY:?}_${LSB_JOBID}"')
runtime = runtime.replace('# 4. ORIGINAL SPEED BENCHMARKS (NOT INCLUDED in the 10-minute PPL limit)', '# 4. DEVELOPMENT RUNTIME EXPERIMENTS; FIXED SPEED WORKLOAD')
runtime = runtime.replace('COMMON_ARGS=(', '''
unset KMP_BLOCKTIME OMP_WAIT_POLICY
prefix=()
case "${EXPERIMENT_POLICY}" in
    bt0-passive) export KMP_BLOCKTIME=0 OMP_WAIT_POLICY=PASSIVE;;
    bt1-active) export KMP_BLOCKTIME=1 OMP_WAIT_POLICY=ACTIVE;;
    bt20-active) export KMP_BLOCKTIME=20 OMP_WAIT_POLICY=ACTIVE;;
    bt200-active) export KMP_BLOCKTIME=200 OMP_WAIT_POLICY=ACTIVE;;
    spread) export OMP_PROC_BIND=spread;;
    interleave) prefix=(numactl --interleave=all);;
    *) error "Unknown development policy";;
esac
env | sort > "${RESULT_DIR}/speed_environment.txt"
declare -p prefix > "${RESULT_DIR}/speed_prefix.txt"
COMMON_ARGS=(''')
runtime = runtime.replace('"${LLAMA_BENCH}" "${COMMON_ARGS[@]}"', '"${prefix[@]}" "${LLAMA_BENCH}" "${COMMON_ARGS[@]}"')
(root/'benchmark_runtime.lsf').write_bytes(runtime.encode('utf-8'))

diag = s.replace('#BSUB -J qwen38_candidate_bench', '#BSUB -J qwen38_node_diagnostic')
diag = diag.replace('echo "===== Running PP2048 ====="', '''
export GGML_NODE_STATS_PREFIX="${RESULT_DIR}/pp_nodes"
export GGML_NODE_STATS_SKIP=0 GGML_NODE_STATS_GRAPHS=4
export GGML_TINYBLAS_DIAG="${RESULT_DIR}/pp_shapes.csv"
echo "===== Running PP2048 (diagnostic build, not a score) ====="''')
diag = diag.replace('echo "===== Running TG128 @ depth 2048 ====="', '''
export GGML_NODE_STATS_PREFIX="${RESULT_DIR}/tg_nodes"
export GGML_NODE_STATS_SKIP=5 GGML_NODE_STATS_GRAPHS=4
export GGML_TINYBLAS_DIAG="${RESULT_DIR}/tg_shapes.csv"
echo "===== Running TG128 @ depth 2048 (diagnostic build, not a score) ====="''')
diag = diag.replace('    score = 100.0 * math.sqrt((pp_avg/base_pp) * (tg_avg/base_tg))', '    score = float("nan") # Diagnostic overhead prevents score interpretation.')
(root/'benchmark_diagnostic.lsf').write_bytes(diag.encode('utf-8'))
