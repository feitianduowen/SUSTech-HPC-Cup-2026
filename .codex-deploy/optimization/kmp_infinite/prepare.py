import json
from pathlib import Path

here=Path(__file__).resolve().parent
remote='/work/apac2602/qwen38-cpu/optimization/20261020-kmp-infinite'
gate=(here.parent/'factor_screen/evaluate.lsf').read_text(encoding='utf-8')
start=gate.index('case "${FACTOR:?}:${CASE_NAME:?}" in')
end=gate.index('\nesac',start)+len('\nesac')
gate=gate[:start]+'''case "${CASE_NAME:?}" in
  A) export KMP_BLOCKTIME=200 OMP_WAIT_POLICY=ACTIVE;;
  B) export KMP_BLOCKTIME=infinite OMP_WAIT_POLICY=ACTIVE;;
  *) exit 2;;
esac'''+gate[end:]
(here/'evaluate.lsf').write_bytes(gate.encode('utf-8'))
script='''#!/bin/bash
#BSUB -J qwen38_kmp_infinite
#BSUB -q ssc-cpu
#BSUB -m hg_6148
#BSUB -n 40
#BSUB -R "span[ptile=40]"
#BSUB -W 04:00
#BSUB -o /work/apac2602/qwen38-cpu/logs/%J.kmp_infinite.out
#BSUB -e /work/apac2602/qwen38-cpu/logs/%J.kmp_infinite.err
set -Eeuo pipefail
source /work/apac2602/qwen38-cpu/scripts/env.sh
ROOT=REMOTE_ROOT
OUT="$ROOT/results/$LSB_JOBID"
BUILD=/work/apac2602/qwen38-cpu/llama.cpp
[[ "${CASE_ORDER:?}" =~ ^(ABBA|BAAB)$ ]]
mkdir -p "$OUT"
phase=VERIFY
trap 'rc=$?; printf "FAILED phase=%s exit=%s time=%s\\n" "$phase" "$rc" "$(date -Is)" > "$OUT/job.status"; exit "$rc"' ERR
stage() { phase=$1; printf '%s time=%s\\n' "$phase" "$(date -Is)" | tee "$OUT/job.status"; }
unset KMP_BLOCKTIME OMP_WAIT_POLICY KMP_AFFINITY GOMP_CPU_AFFINITY KMP_HW_SUBSET PROF_DIR KMP_SETTINGS
export OMP_NUM_THREADS=38 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores
[[ "${LSB_DJOB_NUMPROC:?}" == 40 ]]
[[ $(getconf _NPROCESSORS_ONLN) == 40 ]]
lscpu | grep -q 'Intel(R) Xeon(R) Gold 6148'
cp /work/apac2602/qwen38-cpu/optimization/20261019-factor-screen/results/4338278/baseline-sha256.txt "$OUT/sha256.txt"
sha256sum -c "$OUT/sha256.txt" > "$OUT/hash-check.txt"
cp "$ROOT/$CASE_ORDER.json" "$OUT/plan.json"
cp "$ROOT/runtime_pair.lsf" "$ROOT/evaluate.lsf" "$ROOT/runtime_probe.c" "$OUT/"
{ date -Is; hostname; lscpu; module list; icc --version; icpc --version; } > "$OUT/environment.txt" 2>&1
stage VALIDATE_RUNTIME_SETTINGS
icc -gcc-name=/share/base/e5/gcc/11.2.0/bin/gcc -O2 -qopenmp "$OUT/runtime_probe.c" -o "$OUT/runtime-probe" > "$OUT/probe-compile.log" 2>&1
for value in 200 infinite; do
    KMP_BLOCKTIME="$value" OMP_WAIT_POLICY=ACTIVE KMP_SETTINGS=TRUE "$OUT/runtime-probe" > "$OUT/runtime-$value.log" 2>&1
done
python3 - "$OUT" <<'PY'
import json,re,sys
from pathlib import Path
d=Path(sys.argv[1]); result={}
for mode in ['200','infinite']:
    text=(d/('runtime-'+mode+'.log')).read_text()
    assert 'THREADS=38' in text
    values=re.findall(r'KMP_BLOCKTIME\\s*=\\s*([^\\n]+)',text)
    assert values
    effective=values[-1].strip()
    assert (mode=='200' and effective=='200') or (mode=='infinite' and effective in ['infinite','2147483647']),effective
    result[mode]={'effective_KMP_BLOCKTIME':effective,'threads':38,'OMP_WAIT_POLICY':'ACTIVE'}
(d/'runtime-validation.json').write_text(json.dumps(result,indent=2))
PY
na=0; nb=0
for ((i=0; i<4; i++)); do
    letter=${CASE_ORDER:$i:1}
    if [[ "$letter" == A ]]; then na=$((na+1)); rep=$na; else nb=$((nb+1)); rep=$nb; fi
    printf -v name '%02d_%s%d' "$((i+1))" "$letter" "$rep"
    stage "PPL_PP10_TG10_$name"
    # The harness resets wait settings for fixed PPL, then applies A/B only to speed.
    CASE_NAME="$letter" COMPILER_BUILD_ROOT="$BUILD" EXPERIMENT_OUTPUT_DIR="$OUT/$name" RUN_BENCH=1 bash "$OUT/evaluate.lsf" > "$OUT/$name.log" 2>&1
    sha256sum -c "$OUT/sha256.txt" >> "$OUT/hash-check.txt"
done
stage COMPLETE
'''.replace('REMOTE_ROOT',remote)
(here/'runtime_pair.lsf').write_bytes(script.encode('utf-8'))
for order in ['ABBA','BAAB']:
    prefix='confirm-kmp-infinite-'+order.lower()
    mapping={prefix+'-'+name+'_{job_id}':(prefix+'-A'+name[-1]+'_{job_id}' if name.startswith('B') else None) for name in ['A1','A2','B1','B2']}
    spec={'script':remote+'/runtime_pair.lsf','kind':'同节点完整对照',
          'purpose':'检验VTune首次PP fork-barrier等待线索：KMP_BLOCKTIME 200 vs infinite，顺序'+order,
          'config':'同一SHA核验Intel Classic2021.9 O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model原版；OpenMP/tinyBLAS ON、BLAS/GPU OFF；hg_6148单节点40slots/Gold6148，38线程close/cores，OMP_DYNAMIC FALSE。A=KMP_BLOCKTIME200，B=infinite，两者OMP_WAIT_POLICY ACTIVE，其余测速设置相同。先用Intel编译OpenMP小程序核对38线程及实际KMP_SETTINGS，infinite须被运行时识别，禁止静默回落。四轮'+order+'，每轮独立固定PPL t/tb38 c512 chunks2 b512ub256 f16KV ngl0 NUMA distribute no-warmup timeout590s，±5%；PPL使用固定默认等待环境，通过后才施加A/B到PP2048/TG128d2048各r10 t38 b2048ub512 f16KV ngl0 NUMA distribute。无VTune/OS采样。',
          'baseline':'同作业A1/A2的200ms配置，B1对应A1，B2对应A2；同节点顺序配对。跨作业只比较各自相对比值，并保留首次/顺序/节点/时段混杂',
          'case_prefix':prefix,'baseline_case':prefix+'-A1_{job_id}','measurement_baselines':mapping,'comparison_scope':'same-node',
          'environment':{'CASE_ORDER':order},'lsf_args':['-J','qwen38_kmp_infinite_'+order],
          'ppl_scope':'每轮独立新固定PPL，PPL默认等待设置；A/B仅测速生效。同一个原版二进制，无PPL共享',
          'note':'基于4340376首次PP中__kmp_fork_barrier等待记录提出运行时单变量干预；不先断言等待是唯一根因。保留全部四轮和低速样本，不选择最快轮次；正式采用运行时参数前按赛题要求申报。本轮无采样，开发自测不代表正式成绩；源码/模型/生产环境不替换。'}
    (here/(order+'.json')).write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared KMP_BLOCKTIME=200/infinite ABBA and BAAB with runtime validation')
