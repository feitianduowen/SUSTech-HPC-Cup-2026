import json
from pathlib import Path

local = Path(__file__).resolve().parent
remote = '/work/apac2602/qwen38-cpu/optimization/20261019-q8-avx2-v2'
lsf = '''#!/bin/bash
#BSUB -J qwen38_q8_avx2_paired
#BSUB -q ssc-cpu
#BSUB -m hg_6148
#BSUB -n 40
#BSUB -R "span[ptile=40]"
#BSUB -W 03:00
#BSUB -o /work/apac2602/qwen38-cpu/logs/%J.q8_avx2_paired.out
#BSUB -e /work/apac2602/qwen38-cpu/logs/%J.q8_avx2_paired.err
set -Eeuo pipefail
source /work/apac2602/qwen38-cpu/scripts/env.sh
ROOT=/work/apac2602/qwen38-cpu/optimization/20261019-q8-avx2-v2
VARIANT=${Q8_VARIANT:?set variant}
PARENT=${Q8_BUILD_JOB:?set successful build}
[[ "$VARIANT" == schedule4 && "$PARENT" == 4336892 || "$VARIANT" == schedule4_prefetch16 && "$PARENT" == 4336891 ]]
OUT="$ROOT/results/$LSB_JOBID"
mkdir -p "$OUT/01_baseline" "$OUT/02_candidate"
phase=VERIFY
trap 'rc=$?; echo "FAILED phase=$phase exit=$rc" > "$OUT/job.status"; exit "$rc"' ERR
stage() { phase=$1; echo "$phase time=$(date -Is)" > "$OUT/job.status"; }
[[ "${LSB_DJOB_NUMPROC:?}" == 40 ]]
[[ $(getconf _NPROCESSORS_ONLN) == 40 ]]
lscpu | grep -q 'Intel(R) Xeon(R) Gold 6148'
grep -q BUILD_PPL_PASS "$ROOT/results/$PARENT/job.status"
sha256sum -c "$ROOT/results/$PARENT/sha256.txt" > "$OUT/build-input-verification.txt"
BASE=/work/apac2602/qwen38-cpu/llama.cpp
SRC="$ROOT/sources/$VARIANT"
cp /work/apac2602/qwen38-cpu/llama_bench_results_4335636/perplexity_result.json "$OUT/01_baseline/perplexity_result.json"
cp "$ROOT/results/$PARENT/01_$VARIANT/perplexity_result.json" "$OUT/02_candidate/perplexity_result.json"
python3 "$ROOT/scripts/verify_pair.py" "$OUT" "$VARIANT" "$PARENT"
unset KMP_AFFINITY GOMP_CPU_AFFINITY KMP_BLOCKTIME OMP_WAIT_POLICY
export OMP_NUM_THREADS=38 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores
export OPENBLAS_NUM_THREADS=38 MKL_NUM_THREADS=38 BLIS_NUM_THREADS=38
MODEL=/work/ssc-zhaojh/llama_model/unsloth/Qwen3.8-Flash-Next-GGUF/UD-Q4_K_XL/Qwen3.8-Flash-Next-UD-Q4_K_XL-00001-of-00004.gguf
COMMON=(-m "$MODEL" -t 38 -ngl 0 -b 2048 -ub 512 -ctk f16 -ctv f16 --numa distribute -r 10)
{ date -Is; hostname; lscpu; icc --version; module list; for key in OMP_NUM_THREADS OMP_DYNAMIC OMP_PROC_BIND OMP_PLACES OPENBLAS_NUM_THREADS MKL_NUM_THREADS BLIS_NUM_THREADS; do printf '%s=%s\\n' "$key" "${!key}"; done; } > "$OUT/environment.txt" 2>&1
stage PP_BASELINE
"$BASE/build/bin/llama-bench" "${COMMON[@]}" -p 2048 -n 0 -o json > "$OUT/01_baseline/pp.json" 2> "$OUT/01_baseline/pp.log"
stage PP_CANDIDATE
"$SRC/build/bin/llama-bench" "${COMMON[@]}" -p 2048 -n 0 -o json > "$OUT/02_candidate/pp.json" 2> "$OUT/02_candidate/pp.log"
stage TG_CANDIDATE
"$SRC/build/bin/llama-bench" "${COMMON[@]}" -p 0 -n 128 -d 2048 -o json > "$OUT/02_candidate/tg.json" 2> "$OUT/02_candidate/tg.log"
stage TG_BASELINE
"$BASE/build/bin/llama-bench" "${COMMON[@]}" -p 0 -n 128 -d 2048 -o json > "$OUT/01_baseline/tg.json" 2> "$OUT/01_baseline/tg.log"
stage PAIRED_COMPLETE
'''
(local/'paired.lsf').write_bytes(lsf.encode())
for variant,parent in [('schedule4','4336892'),('schedule4_prefetch16','4336891')]:
    spec={'script':remote+'/paired.lsf','kind':'同节点完整对照','purpose':'Q8_0 '+variant+' 与生产Intel原版同节点完整PP2048/TG128@D2048对照','config':'Intel Classic 2021.9 O3 precise/no-ftz CORE-AVX512；hg_6148 40slots/38推理线程；PP p2048 n0、TG p0 n128 d2048，b2048 ub512 KVf16 ngl0 NUMA distribute，各10次；OpenMP close/cores；顺序baselinePP→candidatePP→candidateTG→baselineTG；无VTune/OS采样','baseline':'本作业01_baseline：生产Intel原版，同节点顺序对照；官方PP46.929024/TG3.295524仅用于开发自测归一化','environment':{'Q8_VARIANT':variant,'Q8_BUILD_JOB':parent},'case_prefix':'q8-paired-'+variant,'baseline_case':'q8-paired-'+variant+'-baseline_{job_id}','note':'每版本PPL为已验证的相同二进制固定配置结果复用，不在此作业重跑：baseline来自4335636，candidate来自'+parent+'；运行前验证二进制SHA256和PASS。两候选在不同节点时只比较各自相对同节点baseline的比例；顺序及缓存影响保留；完整10次样本保留，Score仅为开发自测，非正式成绩。'}
    spec['ppl_scope']='按相同二进制复用已有固定PPL：baseline 4335636，candidate '+parent+'；此测速作业未重跑PPL，各版本有独立PPL证据'
    (local/(variant+'_paired_submission.json')).write_bytes(json.dumps(spec,ensure_ascii=False,indent=2).encode())
print(local/'paired.lsf')
