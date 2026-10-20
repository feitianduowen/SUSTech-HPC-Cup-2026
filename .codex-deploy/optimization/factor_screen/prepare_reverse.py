import json
from pathlib import Path

here=Path(__file__).resolve().parent
out=here.parent/'factor_reverse'
out.mkdir(exist_ok=True)
remote='/work/apac2602/qwen38-cpu/optimization/20261019-factor-reverse'
parent='/work/apac2602/qwen38-cpu/optimization/20261019-factor-screen'
(out/'evaluate.lsf').write_bytes((here/'evaluate.lsf').read_bytes())
script='''#!/bin/bash
#BSUB -J qwen38_factor_reverse
#BSUB -q ssc-cpu
#BSUB -m hg_6148
#BSUB -n 40
#BSUB -R "span[ptile=40]"
#BSUB -W 04:00
#BSUB -o /work/apac2602/qwen38-cpu/logs/%J.factor_reverse.out
#BSUB -e /work/apac2602/qwen38-cpu/logs/%J.factor_reverse.err
set -Eeuo pipefail
source /work/apac2602/qwen38-cpu/scripts/env.sh
ROOT=REMOTE_ROOT
PARENT_ROOT=PARENT_ROOT_PLACEHOLDER
[[ "${FACTOR:?}" =~ ^(affinity|tinyblas|optlevel|aa)$ ]]
[[ "${PARENT_JOB:?}" =~ ^[0-9]+$ ]]
OUT="$ROOT/results/$LSB_JOBID"
PARENT_OUT="$PARENT_ROOT/results/$PARENT_JOB"
BUILDS="$PARENT_ROOT/builds/$PARENT_JOB"
mkdir -p "$OUT"
phase=VERIFY
trap 'rc=$?; printf "FAILED phase=%s exit=%s time=%s\\n" "$phase" "$rc" "$(date -Is)" > "$OUT/job.status"; exit "$rc"' ERR
stage() { phase=$1; printf '%s time=%s\\n' "$phase" "$(date -Is)" | tee "$OUT/job.status"; }
unset KMP_BLOCKTIME OMP_WAIT_POLICY KMP_AFFINITY GOMP_CPU_AFFINITY KMP_HW_SUBSET PROF_DIR
export OMP_NUM_THREADS=38 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores
[[ "${LSB_DJOB_NUMPROC:?}" == 40 ]]
[[ $(getconf _NPROCESSORS_ONLN) == 40 ]]
lscpu | grep -q 'Intel(R) Xeon(R) Gold 6148'
{ date -Is; hostname; lscpu; module list; icc --version; icpc --version; } > "$OUT/environment.txt" 2>&1
cp "$ROOT/$FACTOR.json" "$OUT/plan.json"
cp "$ROOT/reverse.lsf" "$ROOT/evaluate.lsf" "$OUT/"
grep -q '^COMPLETE ' "$PARENT_OUT/job.status"
for name in baseline candidate; do
    cp "$PARENT_OUT/$name-sha256.txt" "$OUT/$name-parent-sha256.txt"
    sha256sum -c "$OUT/$name-parent-sha256.txt" > "$OUT/$name-sha-check.txt"
done
if [[ "$FACTOR" == tinyblas || "$FACTOR" == optlevel ]]; then
    cp "$PARENT_OUT/variable-verification.json" "$OUT/variable-verification.json"
fi
cases=(candidate baseline)
[[ "$FACTOR" != aa ]] || cases=(baseline candidate)
for name in "${cases[@]}"; do
    stage "PPL_PP10_TG10_$name"
    ordinal=01; [[ "$name" != candidate ]] || ordinal=02
    actual_name="$name"
    [[ "$FACTOR" != aa ]] || actual_name=baseline
    sha256sum -c "$OUT/$actual_name-parent-sha256.txt" >> "$OUT/$actual_name-sha-check.txt"
    CASE_NAME="$actual_name" COMPILER_BUILD_ROOT="$BUILDS/$actual_name" EXPERIMENT_OUTPUT_DIR="$OUT/${ordinal}_$name" RUN_BENCH=1 bash "$OUT/evaluate.lsf" > "$OUT/$name-bench.log" 2>&1
    sha256sum -c "$OUT/$actual_name-parent-sha256.txt" >> "$OUT/$actual_name-sha-check.txt"
done
stage COMPLETE
'''.replace('REMOTE_ROOT',remote).replace('PARENT_ROOT_PLACEHOLDER',parent)
(out/'reverse.lsf').write_bytes(script.encode('utf-8'))
for factor,jid in [('affinity','4338278'),('tinyblas','4338279'),('optlevel','4338280'),('aa','4338278')]:
    spec=json.loads((here/((factor if factor!='aa' else 'affinity')+'.json')).read_text(encoding='utf-8'))
    prefix='confirm-reverse-'+factor
    if factor=='aa':
        spec['purpose']='相同Intel原版配置A/A重复对照：量化先后顺序/缓存/节点时段混杂，两次均close/cores'
        spec['config']=spec['config'].replace('baseline先、candidate后','同一baseline二进制及配置连续运行两遍').replace('OMP_PROC_BIND=close → spread；OMP_PLACES=cores；KMP_BLOCKTIME/OMP_WAIT_POLICY均unset','两次OMP_PROC_BIND=close、OMP_PLACES=cores；KMP_BLOCKTIME/OMP_WAIT_POLICY均unset')
    else:
        spec['purpose']='反序复测：'+spec['purpose']
        spec['config']=spec['config'].replace('baseline先、candidate后','candidate先、baseline后')
    spec.update(script=remote+'/reverse.lsf',case_prefix=prefix,baseline_case=prefix+'-baseline_{job_id}',
                baseline='本作业'+prefix+'-baseline_{job_id}同节点对照；A/A中为第一次相同配置运行' if factor=='aa' else '本作业'+prefix+'-baseline_{job_id}同节点后运行baseline；原正序作业'+jid+'只用于比较各自同节点比例',
                environment={'FACTOR':factor,'PARENT_JOB':jid},lsf_args=['-J','qwen38_reverse_'+factor],parent_job=jid,
                note='只读复用父作业产物，父作业全部SHA256校验通过才运行，前后重复核验。每case独立重新固定PPL，无共享。无VTune/OS采样，不清缓存、不修改OS。保留全部10次样本，开发自测非正式成绩；反序与旧正序跨节点/时段，不能消除全部混杂。运行时参数正式采用前按题目申报。'+('A/A两组同一binary/close/cores/默认等待策略，candidate仅是第二次运行的记录标签，无配置变化。' if factor=='aa' else '本作业不重新编译。'))
    (out/(factor+'.json')).write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared three reverse comparisons and one A/A control')
