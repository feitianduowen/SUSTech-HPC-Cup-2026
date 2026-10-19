import json
from pathlib import Path

local = Path(__file__).resolve().parent
root = '/work/apac2602/qwen38-cpu/optimization/20261019-q8-avx2-v2'
old = (local.parent/'orchestrator/build_variant.lsf').read_text(encoding='utf-8')
body = old[old.index('cmake -S "$SRC"'):old.index('echo BUILD_READY')]
header = '''#!/bin/bash
#BSUB -J qwen38_q8_avx2_library
#BSUB -q ssc-cpu
#BSUB -m hg_6148
#BSUB -n 40
#BSUB -R "span[ptile=40]"
#BSUB -W 01:30
#BSUB -o /work/apac2602/qwen38-cpu/logs/%J.q8_avx2_library.out
#BSUB -e /work/apac2602/qwen38-cpu/logs/%J.q8_avx2_library.err
set -Eeuo pipefail
source /work/apac2602/qwen38-cpu/scripts/env.sh
ROOT=/work/apac2602/qwen38-cpu/optimization/20261019-q8-avx2-v2
VARIANT=${Q8_VARIANT:?set variant}
[[ "$VARIANT" == schedule4 || "$VARIANT" == schedule4_prefetch16 ]]
SRC="$ROOT/sources/$VARIANT"
BUILD="$SRC/build"
OUT="$ROOT/results/$LSB_JOBID"
PARENT=4336888
mkdir -p "$OUT"
phase=COPY_SOURCE
trap 'rc=$?; echo "FAILED phase=$phase exit=$rc" > "$OUT/job.status"; exit "$rc"' ERR
stage() { phase=$1; echo "$phase time=$(date -Is)" > "$OUT/job.status"; }
[[ "${LSB_DJOB_NUMPROC:?}" == 40 ]]
[[ $(getconf _NPROCESSORS_ONLN) == 40 ]]
lscpu | grep -q 'Intel(R) Xeon(R) Gold 6148'
grep -q UNIT_PASS "$ROOT/results/$PARENT/job.status"
sha256sum -c "$ROOT/results/$PARENT/sha256.txt" > "$OUT/unit-input-verification.txt"
stage COPY_SOURCE
python3 -u "$ROOT/scripts/copy_verify.py" > "$OUT/source-verification.json"
unset KMP_AFFINITY GOMP_CPU_AFFINITY KMP_BLOCKTIME OMP_WAIT_POLICY
flags='-fp-model precise -no-ftz -xCORE-AVX512 -qsimd-honor-fp-model -diag-disable=10441'
omp=ON
blas=OFF
extra=()
{ date -Is; hostname; lscpu; icc --version; icpc --version; module list; } > "$OUT/environment.txt" 2>&1
stage BUILDING
'''
tail = '''stage LIBRARY_DIFFERENTIAL
mkdir -p "$OUT/$VARIANT"
cp "$ROOT/results/$PARENT/test-q8" "$OUT/test-q8"
BASE=/work/apac2602/qwen38-cpu/llama.cpp/build/bin/libggml-cpu.so
CANDIDATE="$BUILD/bin/libggml-cpu.so"
"$OUT/test-q8" "$BASE" "$CANDIDATE" --check "$VARIANT" > "$OUT/$VARIANT/correctness.json" 2> "$OUT/$VARIANT/correctness.log"
cp "$OUT/$VARIANT/correctness.json" "$OUT/library-correctness.json"
objdump -d "$CANDIDATE" > "$OUT/library-assembly.txt"
awk '/<ggml_vec_dot_q8_0_q8_0>:/ {inside=1; print; next} inside && /^[[:xdigit:]]+ <[^>]+>:/ {exit} inside {print}' "$OUT/library-assembly.txt" > "$OUT/avx2-assembly.txt"
stage LIBRARY_MICROBENCH
numactl --physcpubind=0 --membind=0 "$OUT/test-q8" "$BASE" "$CANDIDATE" --bench "$VARIANT" > "$OUT/$VARIANT/kernel-times.csv" 2> "$OUT/$VARIANT/kernel-times.log"
python3 "$ROOT/scripts/analyze.py" "$OUT" > "$OUT/kernel-summary.log"
stage PPL_CANDIDATE
COMPILER_BUILD_ROOT="$SRC" RUN_BENCH=0 EXPERIMENT_OUTPUT_DIR="$OUT/01_$VARIANT" bash "$ROOT/ppl_gate.lsf" > "$OUT/ppl-gate.log" 2>&1
sha256sum "$BUILD/bin/llama-bench" "$BUILD/bin/llama-perplexity" "$CANDIDATE" >> "$OUT/sha256.txt"
stage BUILD_PPL_PASS
'''
(local/'build.lsf').write_bytes((header+body+tail).encode())
(local/'ppl_gate.lsf').write_bytes((local.parent/'source_v2/ppl_gate.lsf').read_bytes())
for variant in ['schedule4','schedule4_prefetch16']:
    spec={'script':root+'/build.lsf','kind':'Q8源码修改/完整库差分/PPL','purpose':'独立源码构建 '+variant+'，验证真实动态库的逐位一致性、微基准与固定PPL','config':'Intel Classic icc/icpc2021.9；Release O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model，OpenMP ON BLAS OFF；Gold6148单节点40slots，38线程固定PPL c512 chunks2 b512 ub256 f16 ngl0 NUMA distribute timeout590；4可执行文件与quantize单测；实际动态库204154例差分；CPU0/membind0单核nb80/192各10轮AB/BA resident/256MiB stream；本作业不跑完整PP/TG','baseline':'同节点同进程原版Intel libggml-cpu.so；PPL官方2.7696；无完整模型性能baseline','environment':{'Q8_VARIANT':variant},'case_prefix':'q8-avx2','note':'源码在sources/'+variant+'，为独立普通文件；同节点成对微基准，两个候选构建在不同作业/节点时不能用绝对速度直接互比；不覆盖原源码，不计算Score。摘取版control已出现性能偏移，只以实际库比较为依据。'}
    (local/(variant+'_submission.json')).write_bytes(json.dumps(spec,ensure_ascii=False,indent=2).encode())
print(local/'build.lsf')
