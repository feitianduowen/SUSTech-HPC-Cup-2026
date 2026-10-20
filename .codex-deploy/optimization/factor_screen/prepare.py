import json
from pathlib import Path

here = Path(__file__).resolve().parent
remote = '/work/apac2602/qwen38-cpu/optimization/20261019-factor-screen'
old = here.parent/'compiler_pgo'
gate = (old/'ppl_gate.lsf').read_text(encoding='utf-8')
hook = '''# Runtime factors apply to development speed measurements only.
case "${FACTOR:?}:${CASE_NAME:?}" in
  wait:baseline) export KMP_BLOCKTIME=200 OMP_WAIT_POLICY=ACTIVE;;
  wait:candidate) export KMP_BLOCKTIME=0 OMP_WAIT_POLICY=ACTIVE;;
  affinity:candidate) export OMP_PROC_BIND=spread;;
esac
env | sort | grep -E '^(OMP_|KMP_|MKL_|OPENBLAS_|BLIS_)' > "$RESULT_DIR/speed_environment.txt"
'''
assert gate.count('COMMON_ARGS=(') == 1
gate = gate.replace('COMMON_ARGS=(', hook+'COMMON_ARGS=(')
gate = gate.replace('export OMP_NUM_THREADS="${THREADS}"', 'unset KMP_BLOCKTIME OMP_WAIT_POLICY KMP_AFFINITY GOMP_CPU_AFFINITY KMP_HW_SUBSET\nexport OMP_NUM_THREADS="${THREADS}"')
gate = gate.replace('"${LLAMA_BENCH}" "${COMMON_ARGS[@]}" -p 2048', 'printf \'%q \' "${LLAMA_BENCH}" "${COMMON_ARGS[@]}" -p 2048 -n 0 -o json > "${RESULT_DIR}/pp.command"\n"${LLAMA_BENCH}" "${COMMON_ARGS[@]}" -p 2048')
gate = gate.replace('"${LLAMA_BENCH}" "${COMMON_ARGS[@]}" -p 0', 'printf \'%q \' "${LLAMA_BENCH}" "${COMMON_ARGS[@]}" -p 0 -n 128 -d 2048 -o json > "${RESULT_DIR}/tg.command"\n"${LLAMA_BENCH}" "${COMMON_ARGS[@]}" -p 0')
(here/'evaluate.lsf').write_bytes(gate.encode('utf-8'))

original = (old/'pipeline_driver_long_train.lsf').read_text(encoding='utf-8')
build = original[original.index('    local command=(cmake'):original.index('\n}\ngate()')]
build = '\n'.join(line for line in build.splitlines() if 'CMAKE_PROJECT_INCLUDE' not in line and 'check_driver_scope' not in line)
build = build.replace('$flags $pgo', '$flags').replace('$effective_link', '$link')
build = build.replace('-DGGML_NATIVE=ON', '"-DGGML_LLAMAFILE=$tiny" -DGGML_NATIVE=ON')
driver = '''#!/bin/bash
#BSUB -J qwen38_factor
#BSUB -q ssc-cpu
#BSUB -m hg_6148
#BSUB -n 40
#BSUB -R "span[ptile=40]"
#BSUB -W 04:00
#BSUB -o /work/apac2602/qwen38-cpu/logs/%J.factor.out
#BSUB -e /work/apac2602/qwen38-cpu/logs/%J.factor.err
set -Eeuo pipefail
source /work/apac2602/qwen38-cpu/scripts/env.sh
ROOT=REMOTE_ROOT
VERIFY=/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo
SRC=/work/apac2602/qwen38-cpu/optimization/20261018-v1/sources/native
OUT="$ROOT/results/$LSB_JOBID"
BUILDS="$ROOT/builds/$LSB_JOBID"
[[ "${FACTOR:?}" =~ ^(wait|affinity|tinyblas|optlevel|fpmodel)$ ]]
mkdir -p "$OUT" "$BUILDS"
phase=INIT
trap 'rc=$?; printf "FAILED phase=%s exit=%s time=%s\\n" "$phase" "$rc" "$(date -Is)" > "$OUT/job.status"; exit "$rc"' ERR
stage() { phase=$1; printf '%s time=%s\\n' "$phase" "$(date -Is)" | tee "$OUT/job.status"; }
unset KMP_BLOCKTIME OMP_WAIT_POLICY KMP_AFFINITY GOMP_CPU_AFFINITY KMP_HW_SUBSET PROF_DIR
export OMP_NUM_THREADS=38 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores
export GIT_OPTIONAL_LOCKS=0
[[ "${LSB_DJOB_NUMPROC:?}" == 40 ]]
[[ $(getconf _NPROCESSORS_ONLN) == 40 ]]
lscpu | grep -q 'Intel(R) Xeon(R) Gold 6148'
python3 "$VERIFY/verify_source.py" "$SRC" "$VERIFY/source_identity.json" > "$OUT/source-verification.json"
{ date -Is; hostname; lscpu; module list; icc --version; icpc --version; } > "$OUT/environment.txt" 2>&1
cp "$ROOT/$FACTOR.json" "$OUT/plan.json"
cp "$ROOT/factor_job.lsf" "$ROOT/evaluate.lsf" "$OUT/"
link='-Wl,--no-as-needed,/lib64/libm.so.6,--as-needed'
build_one() {
    local name=$1 mode=plain LEVEL=3 tiny=ON
    local flags='-fp-model precise -no-ftz -xCORE-AVX512 -qsimd-honor-fp-model -diag-disable=10441'
    if [[ "$name" == candidate ]]; then
        case "$FACTOR" in
            tinyblas) tiny=OFF;;
            optlevel) LEVEL=2;;
            fpmodel) flags=${flags/precise/fast=1};;
        esac
    fi
    local dest="$BUILDS/$name/build" logs="$OUT/$name-build"
    local targets=(llama-cli llama-server llama-bench llama-perplexity test-quantize-fns)
    mkdir -p "$logs"
BUILD_BODY
}
case "$FACTOR" in
  wait|affinity)
    for name in baseline candidate; do
      ln -s /work/apac2602/qwen38-cpu/llama.cpp "$BUILDS/$name"
    done;;
  *)
    stage BUILD_BASELINE; build_one baseline
    stage BUILD_CANDIDATE; build_one candidate
    python3 "$ROOT/verify_factor.py" "$FACTOR" "$BUILDS" > "$OUT/variable-verification.json";;
esac
for name in baseline candidate; do
    sha256sum "$BUILDS/$name/build/bin/llama-bench" "$BUILDS/$name/build/bin/llama-perplexity" "$BUILDS/$name/build/bin/"*.so* > "$OUT/$name-sha256.txt"
done
for name in baseline candidate; do
    stage "PPL_PP10_TG10_$name"
    ordinal=01; [[ "$name" != candidate ]] || ordinal=02
    sha256sum -c "$OUT/$name-sha256.txt" > "$OUT/$name-sha-check.txt"
    CASE_NAME="$name" COMPILER_BUILD_ROOT="$BUILDS/$name" EXPERIMENT_OUTPUT_DIR="$OUT/${ordinal}_$name" RUN_BENCH=1 bash "$OUT/evaluate.lsf" > "$OUT/$name-bench.log" 2>&1
    sha256sum -c "$OUT/$name-sha256.txt" >> "$OUT/$name-sha-check.txt"
done
stage COMPLETE
'''.replace('REMOTE_ROOT', remote).replace('BUILD_BODY', build)
(here/'factor_job.lsf').write_bytes(driver.encode('utf-8'))

factors = {
 'wait': ('OpenMP等待时长', 'KMP_BLOCKTIME=200 → 0；两者OMP_WAIT_POLICY=ACTIVE，其余相同'),
 'affinity': ('OpenMP线程绑定', 'OMP_PROC_BIND=close → spread；OMP_PLACES=cores；KMP_BLOCKTIME/OMP_WAIT_POLICY均unset'),
 'tinyblas': ('tinyBLAS执行路径', 'GGML_LLAMAFILE=ON → OFF；OpenMP ON、BLAS OFF'),
 'optlevel': ('Intel优化级别', 'Intel icc/icpc Release -O3 → -O2；其余precise浮点选项相同'),
 'fpmodel': ('Intel浮点优化模式', '-fp-model precise → fast=1；两者O3，保留-no-ftz和-qsimd-honor-fp-model'),
}
for key,(title,change) in factors.items():
    prefix='confirm-factor-'+key
    spec={
      'script': remote+'/factor_job.lsf', 'kind':'同节点完整对照',
      'purpose':title+'单变量筛选：'+change,
      'config':'Intel Classic2021.9 icc/icpc、官方源码d812350；hg_6148单节点40slots/Gold6148/38推理线程；baseline先、candidate后；'+change+'。默认O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model，OpenMP ON、tinyBLAS ON、BLAS/GPU OFF、无PGO。每版独立固定PPL t/tb38 c512 chunks2 b512 ub256 f16KV ngl0 NUMA distribute no-warmup timeout590s，±5% [2.63112,2.90808]；通过后PP2048和TG128d2048各r10 b2048 ub512，其余固定。',
      'baseline':'本作业'+prefix+'-baseline_{job_id}，同节点第一组；无跨节点性能baseline替代',
      'case_prefix':prefix, 'baseline_case':prefix+'-baseline_{job_id}',
      'environment':{'FACTOR':key}, 'lsf_args':['-J','qwen38_factor_'+key],
      'ppl_scope':'每版分别重跑固定PPL，无共享；运行时变量仅测速阶段生效，PPL固定默认环境',
      'note':'开发单变量筛选，非正式成绩。固定baseline→candidate顺序仍有缓存/顺序局限，有收益须反序复测。全部10次样本保留；无VTune/OS采样。运行时变量正式采用前须按赛题要求申报。编译因素两版独立新构建/量化测试/链接核验；运行时因素复用同一生产Intel二进制并前后SHA校验。',
    }
    (here/(key+'.json')).write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared five factor specifications and harnesses')
