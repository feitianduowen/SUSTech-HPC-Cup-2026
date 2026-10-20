import json
from pathlib import Path

here=Path(__file__).resolve().parent
remote='/work/apac2602/qwen38-cpu/optimization/20261019-order-diagnostic'
(here/'ppl_gate.lsf').write_bytes((here.parent/'compiler_pgo/ppl_gate.lsf').read_bytes())
header='''#!/bin/bash
#BSUB -J qwen38_order
#BSUB -q ssc-cpu
#BSUB -m hg_6148
#BSUB -n 40
#BSUB -R "span[ptile=40]"
#BSUB -W 04:00
#BSUB -o /work/apac2602/qwen38-cpu/logs/%J.order.out
#BSUB -e /work/apac2602/qwen38-cpu/logs/%J.order.err
set -Eeuo pipefail
source /work/apac2602/qwen38-cpu/scripts/env.sh
ROOT=REMOTE_ROOT
OUT="$ROOT/results/$LSB_JOBID"
BUILD=/work/apac2602/qwen38-cpu/llama.cpp
PARENT=/work/apac2602/qwen38-cpu/optimization/20261019-factor-screen/results/4338278
[[ "${ORDER_MODE:?}" =~ ^(pp-chain|tg-between|aaa)$ ]]
mkdir -p "$OUT"
phase=VERIFY
trap 'rc=$?; printf "FAILED phase=%s exit=%s time=%s\\n" "$phase" "$rc" "$(date -Is)" > "$OUT/job.status"; exit "$rc"' ERR
stage() { phase=$1; printf '%s time=%s\\n' "$phase" "$(date -Is)" | tee "$OUT/job.status"; }
unset KMP_BLOCKTIME OMP_WAIT_POLICY KMP_AFFINITY GOMP_CPU_AFFINITY KMP_HW_SUBSET PROF_DIR
export OMP_NUM_THREADS=38 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores
export MKL_NUM_THREADS=38 OPENBLAS_NUM_THREADS=38 BLIS_NUM_THREADS=38
[[ "${LSB_DJOB_NUMPROC:?}" == 40 ]]
[[ $(getconf _NPROCESSORS_ONLN) == 40 ]]
lscpu | grep -q 'Intel(R) Xeon(R) Gold 6148'
cp "$PARENT/baseline-sha256.txt" "$OUT/sha256.txt"
sha256sum -c "$OUT/sha256.txt" > "$OUT/hash-check.txt"
cp "$ROOT/$ORDER_MODE.json" "$OUT/plan.json"
cp "$ROOT/order_job.lsf" "$ROOT/ppl_gate.lsf" "$ROOT/observed_run.py" "$OUT/"
{ date -Is; hostname; lscpu; module list; icc --version; icpc --version; cat /proc/sys/kernel/numa_balancing; env | sort | grep -E '^(OMP_|KMP_|MKL_|OPENBLAS_|BLIS_)'; } > "$OUT/environment.txt" 2>&1
if [[ "$ORDER_MODE" == aaa ]]; then
    for name in 01_baseline 02_repeat2 03_repeat3; do
        stage "FIXED_PPL_PP10_TG10_$name"
        COMPILER_BUILD_ROOT="$BUILD" EXPERIMENT_OUTPUT_DIR="$OUT/$name" RUN_BENCH=1 bash "$OUT/ppl_gate.lsf" > "$OUT/$name.log" 2>&1
        sha256sum -c "$OUT/sha256.txt" >> "$OUT/hash-check.txt"
    done
else
    stage FIXED_PPL
    COMPILER_BUILD_ROOT="$BUILD" EXPERIMENT_OUTPUT_DIR="$OUT/ppl" RUN_BENCH=0 bash "$OUT/ppl_gate.lsf" > "$OUT/ppl.log" 2>&1
    MODEL=/work/ssc-zhaojh/llama_model/unsloth/Qwen3.8-Flash-Next-GGUF/UD-Q4_K_XL/Qwen3.8-Flash-Next-UD-Q4_K_XL-00001-of-00004.gguf
    common=(-m "$MODEL" -t 38 -ngl 0 -b 2048 -ub 512 -ctk f16 -ctv f16 --numa distribute -r 10 -v -o json)
    tasks=(01_baseline:pp 02_repeat2:pp 03_repeat3:pp 01_baseline:tg 02_repeat2:tg)
    [[ "$ORDER_MODE" != tg-between ]] || tasks=(01_baseline:pp 01_baseline:tg 02_repeat2:pp 02_repeat2:tg 03_repeat3:pp)
    for task in "${tasks[@]}"; do
        name=${task%:*}; workload=${task#*:}
        stage "DIAGNOSTIC_${name}_$workload"
        mkdir -p "$OUT/$name"
        args=(-p 2048 -n 0)
        [[ "$workload" != tg ]] || args=(-p 0 -n 128 -d 2048)
        python3 "$OUT/observed_run.py" --output "$OUT/$name/$workload" --timeout 3600 --interval 30 "$BUILD/build/bin/llama-bench" "${common[@]}" "${args[@]}" > "$OUT/$name/$workload.observer.log" 2>&1
        python3 - "$OUT/$name/$workload.json" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))[0]
assert len(x['samples_ts'])==len(x['samples_ns'])==10
assert all(v>0 for v in x['samples_ns'])
PY
        sha256sum -c "$OUT/sha256.txt" >> "$OUT/hash-check.txt"
    done
fi
stage COMPLETE
'''.replace('REMOTE_ROOT',remote)
(here/'order_job.lsf').write_bytes(header.encode('utf-8'))
for mode in ['pp-chain','tg-between','aaa']:
    diagnostic=mode!='aaa'
    order={'pp-chain':'固定PPL一次→PP1→PP2→PP3→TG1→TG2','tg-between':'固定PPL一次→PP1→TG1→PP2→TG2→PP3','aaa':'三轮连续相同配置；每轮固定PPL→PP10→TG10'}[mode]
    prefix=('diagnostic-order-' if diagnostic else 'confirm-order-')+mode
    spec={
      'script':remote+'/order_job.lsf','kind':'顺序效应诊断（不计分）' if diagnostic else '同节点完整对照',
      'purpose':('定位TG穿插、模型加载/缺页/NUMA分布与PP逐轮加速的关联：' if diagnostic else '无采样重复完整固定评测，检查第二、第三轮是否趋稳：')+order,
      'config':'只读复用SHA核验Intel Classic2021.9 O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model官方原版；OpenMP ON、tinyBLAS ON、BLAS/GPU OFF。hg_6148单节点40slots/Gold6148，推理38线程close/cores，默认等待策略。PPL t/tb38 c512 chunks2 b512 ub256 KVf16 ngl0 NUMA distribute no-warmup timeout590s，±5%[2.63112,2.90808]。PP p2048n0、TG p0n128d2048，各r10/t38/b2048/ub512/f16KV/ngl0/NUMA distribute；执行顺序='+order+'。'+('测速-v，每30秒只读采样该子进程缺页、I/O、RSS、GGUF/其他NUMA页分布，及主机内存/NUMA迁移计数；每命令超时3600s；不计算Score。' if diagnostic else '无VTune/OS采样；三轮全部原始样本保留。'),
      'baseline':'同作业01_baseline的首次PP/首次TG；比较各自同节点后续相同workload，非优化收益',
      'baseline_case':prefix+'-baseline_{job_id}','case_prefix':prefix,'comparison_scope':'same-node',
      'environment':{'ORDER_MODE':mode},'lsf_args':['-J','qwen38_order_'+mode],
      'os_monitoring':diagnostic,
      'ppl_scope':'所有测速阶段共享本作业开始时的一次独立固定PPL，非每case重跑；采样只覆盖测速' if diagnostic else '三轮各自独立重跑固定PPL，无共享',
      'note':'A/A 4338449无配置变化第二次PP约+76.6%，因此先验证测量顺序效应。'+('两种顺序分属不同节点/时段，采样有开销，均为诊断不能计分；分目录PP与TG可能不相邻，真实顺序见plan、command和时间戳。主机计数可能含其他系统活动，相关性不能单独证明因果。' if diagnostic else '同一二进制同一配置重复三次，不挑选最快轮次、不删除第一轮；开发自测非正式成绩。')+'不清缓存、不改OS NUMA设置，不修改生产构建或模型。',
    }
    (here/(mode+'.json')).write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared PP-chain, TG-between and unsampled AAA')
