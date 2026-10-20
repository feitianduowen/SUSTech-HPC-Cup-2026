import json
from pathlib import Path

here=Path(__file__).resolve().parent
remote='/work/apac2602/qwen38-cpu/optimization/20261019-other-source'
template=(here.parent/'orchestrator/build_variant.lsf').read_text(encoding='utf-8')
configure=template[template.index('cmake -S "$SRC"'):template.index('echo BUILD_READY')]
script='''#!/bin/bash
#BSUB -J qwen38_other_source
#BSUB -q ssc-cpu
#BSUB -m hg_6148
#BSUB -n 40
#BSUB -R "span[ptile=40]"
#BSUB -W 04:00
#BSUB -o /work/apac2602/qwen38-cpu/logs/%J.other_source.out
#BSUB -e /work/apac2602/qwen38-cpu/logs/%J.other_source.err
set -Eeuo pipefail
source /work/apac2602/qwen38-cpu/scripts/env.sh
ROOT=/work/apac2602/qwen38-cpu/optimization/20261019-other-source
VARIANT=${SOURCE_VARIANT:?set SOURCE_VARIANT}
[[ "$VARIANT" == gemm-balanced || "$VARIANT" == row-quant ]]
OUT="$ROOT/results/$LSB_JOBID"
SRC="$ROOT/sources/$VARIANT-$LSB_JOBID"
BUILD="$SRC/build"
mkdir -p "$OUT"
phase=INIT
trap 'rc=$?; echo "FAILED phase=$phase exit=$rc time=$(date -Is)" > "$OUT/job.status"; exit "$rc"' ERR
stage() { phase=$1; echo "$phase time=$(date -Is)" > "$OUT/job.status"; }
[[ "$LSB_DJOB_NUMPROC" == 40 ]]
[[ $(getconf _NPROCESSORS_ONLN) == 40 ]]
lscpu | grep -q 'Intel(R) Xeon(R) Gold 6148'
unset KMP_AFFINITY GOMP_CPU_AFFINITY KMP_BLOCKTIME OMP_WAIT_POLICY KMP_HW_SUBSET PROF_DIR INTEL_PROF_DUMP_INTERVAL INTEL_PROF_DUMP_CUMULATIVE
export OMP_NUM_THREADS=38 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores
export OPENBLAS_NUM_THREADS=38 MKL_NUM_THREADS=38 BLIS_NUM_THREADS=38
{ date -Is; hostname; lscpu; module list; icc --version; icpc --version; } > "$OUT/environment.txt" 2>&1
cp "$ROOT/build_and_pair.lsf" "$OUT/pipeline.lsf"
cp "$ROOT/ppl_gate.lsf" "$OUT/ppl_gate.lsf"
cp "$ROOT/$VARIANT.patch" "$OUT/source.patch"
stage COPY_VERIFY_SOURCE
python3 "$ROOT/copy_verify.py" > "$OUT/source-verification.json"
flags='-fp-model precise -no-ftz -xCORE-AVX512 -qsimd-honor-fp-model -diag-disable=10441'
omp=ON
blas=OFF
extra=()
stage BUILD_AND_QUANT_TEST
'''+configure+'''
stage BUILD_MATMUL_CHECK
BASE=/work/apac2602/qwen38-cpu/llama.cpp
for name in baseline candidate; do
    BIN="$BUILD/bin"
    [[ "$name" != baseline ]] || BIN="$BASE/build/bin"
    icpc -gxx-name=/share/base/e5/gcc/11.2.0/bin/g++ -std=c++17 -O3 $flags -I"$SRC/ggml/include" "$ROOT/matmul_check.cpp" -L"$BIN" -Wl,-rpath,"$BIN",--no-as-needed -lggml-cpu -lggml -lggml-base -Wl,--no-as-needed,/lib64/libm.so.6,--as-needed -qopenmp -o "$OUT/check-$name" > "$OUT/check-$name-build.log" 2>&1
    ldd "$OUT/check-$name" > "$OUT/check-$name-ldd.txt"
    ! grep -q 'not found' "$OUT/check-$name-ldd.txt"
    stage "MATMUL_CHECK_$name"
    timeout --signal=TERM --kill-after=10s 900 "$OUT/check-$name" "$OUT/$name.bin" > "$OUT/$name-check.json" 2> "$OUT/$name-check.log"
done
python3 "$ROOT/compare.py" "$OUT" > "$OUT/differential.log"
# Candidate first in both jobs. A reverse-order confirmation is needed if
# apparent gains survive these initial full-workload screening measurements.
for name in candidate baseline; do
    stage "PPL_PP10_TG10_$name"
    CASE_ROOT="$SRC"
    ordinal=02
    if [[ "$name" == baseline ]]; then CASE_ROOT="$BASE"; ordinal=01; fi
    sha256sum "$CASE_ROOT/build/bin/llama-bench" "$CASE_ROOT/build/bin/llama-perplexity" "$CASE_ROOT/build/bin/"lib*.so* > "$OUT/$name-sha256.txt"
    COMPILER_BUILD_ROOT="$CASE_ROOT" RUN_BENCH=1 EXPERIMENT_OUTPUT_DIR="$OUT/${ordinal}_$name" bash "$OUT/ppl_gate.lsf" > "$OUT/$name-bench.log" 2>&1
done
stage COMPLETE
'''
(here/'build_and_pair.lsf').write_bytes(script.encode())
(here/'ppl_gate.lsf').write_bytes((here.parent/'pgo_hot_serial/ppl_gate.lsf').read_bytes())
for variant,purpose in [('gemm-balanced','tinyBLAS AVX量化矩阵三种tile循环改为商余数均衡连续分配，减少ceil划分导致的尾部线程空闲；tile内部算术及原有同步点不变'),('row-quant','ggml mul_mat中F32输入且token行数>=线程数时按整行循环分配量化，避免每行被所有线程切成短块；小token和F16/BF16保持原分块，原同步点不变')]:
    spec={'script':remote+'/build_and_pair.lsf','kind':'源码修改、算子差分及同节点完整对照','purpose':purpose,
      'environment':{'SOURCE_VARIANT':variant},'lsf_args':['-J','qwen38_'+variant],
      'config':'Intel Classic2021.9 O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model；hg_6148单节点40slots，OpenMP ON/BLAS OFF；每作业从官方d812350 SHA校验3687文件，独立sources/<variant>-<job>副本，仅1个文件修改；四工具构建/ldd、量化单测；实际库矩阵差分8权重类型×9形状×1/38线程=144配置，每配置重复3次且逐bit对照原版；通过后candidate先、baseline后各独立固定PPL t/tb38 c512 chunks2 b512ub256 f16KV ngl0 NUMA distribute no-warmup timeout590s ±5%，各PP2048/TG128d2048 r10 b2048ub512 f16KV ngl0 NUMA distribute，38线程close/cores，无性能采样',
      'baseline':'本作业01_baseline生产Intel官方原版，同节点顺序后执行；算子差分同节点baseline先、candidate后',
      'case_prefix':'other-'+variant,'baseline_case':'other-'+variant+'-baseline_{job_id}',
      'ppl_scope':'candidate及baseline各自本作业新固定PPL，无共享PPL；通过PPL后才运行该版本完整测速',
      'note':'保留所有旧源码和构建；两个独立修改分别提交，不混入Q8内核修改或PGO。候选先执行存在缓存/顺序限制，跨作业节点不同不可直接比较绝对吞吐；有收益时再做反序。矩阵差分只验证覆盖形状，完整PPL另测；任一阶段失败即停止后续，未完成指标留空，完整十次慢样本保留，分数仅开发自测。'}
    (here/(variant+'.json')).write_bytes(json.dumps(spec,ensure_ascii=False,indent=2).encode())
print(here/'build_and_pair.lsf')
