import json
from pathlib import Path

here=Path(__file__).resolve().parent
remote='/work/apac2602/qwen38-cpu/optimization/20261020-vtune-wait-pair'
(here/'ppl_gate.lsf').write_bytes((here.parent/'order_diagnostic/ppl_gate.lsf').read_bytes())
(here/'observed_run.py').write_bytes((here.parent/'order_crossover/observed_run.py').read_bytes())
(here/'probe.py').write_bytes((here.parent.parent/'profiling/profile_probe.py').read_bytes())
driver='''#!/bin/bash
#BSUB -J qwen38_wait_profile
#BSUB -q ssc-cpu
#BSUB -m hg_6148
#BSUB -n 40
#BSUB -R "span[ptile=40]"
#BSUB -W 04:00
#BSUB -o /work/apac2602/qwen38-cpu/logs/%J.wait_profile.out
#BSUB -e /work/apac2602/qwen38-cpu/logs/%J.wait_profile.err
set -Eeuo pipefail
source /work/apac2602/qwen38-cpu/scripts/env.sh
ROOT=REMOTE_ROOT
OUT="$ROOT/results/$LSB_JOBID"
BUILD=/work/apac2602/qwen38-cpu/llama.cpp
VTUNE=/share/intel/oneapi-2023.1/vtune/2023.1.0/bin64/vtune
[[ "${PROFILE_MODE:?}" =~ ^(threading|hotspots)$ ]]
mkdir -p "$OUT"
phase=VERIFY
trap 'rc=$?; printf "FAILED phase=%s exit=%s time=%s\\n" "$phase" "$rc" "$(date -Is)" > "$OUT/job.status"; exit "$rc"' ERR
stage() { phase=$1; printf '%s time=%s\\n' "$phase" "$(date -Is)" | tee "$OUT/job.status"; }
unset KMP_BLOCKTIME OMP_WAIT_POLICY KMP_AFFINITY GOMP_CPU_AFFINITY KMP_HW_SUBSET PROF_DIR
export OMP_NUM_THREADS=38 OMP_DYNAMIC=FALSE OMP_PROC_BIND=close OMP_PLACES=cores
export MKL_NUM_THREADS=38 OPENBLAS_NUM_THREADS=38 BLIS_NUM_THREADS=38 LC_ALL=C
[[ "${LSB_DJOB_NUMPROC:?}" == 40 ]]
[[ $(getconf _NPROCESSORS_ONLN) == 40 ]]
lscpu | grep -q 'Intel(R) Xeon(R) Gold 6148'
cp /work/apac2602/qwen38-cpu/optimization/20261019-factor-screen/results/4338278/baseline-sha256.txt "$OUT/sha256.txt"
sha256sum -c "$OUT/sha256.txt" > "$OUT/hash-check.txt"
cp "$ROOT/$PROFILE_MODE.json" "$OUT/plan.json"
cp "$ROOT/profile_pair.lsf" "$ROOT/ppl_gate.lsf" "$ROOT/target_exec.py" "$ROOT/roi_monitor.py" "$ROOT/observed_run.py" "$ROOT/probe.py" "$OUT/"
{ date -Is; hostname; lscpu; module list; icc --version; icpc --version; "$VTUNE" -version; cat /proc/sys/kernel/perf_event_paranoid; } > "$OUT/environment.txt" 2>&1
args=(-collect threading -knob sampling-and-waits=sw -knob sampling-interval=10 -knob enable-stack-collection=true -knob stack-size=2048)
[[ "$PROFILE_MODE" != hotspots ]] || args=(-collect hotspots -knob sampling-mode=hw -knob sampling-interval=10 -knob enable-stack-collection=true -knob stack-size=2048)
stage PROBE
timeout --kill-after=15s 200s "$VTUNE" "${args[@]}" -data-limit=128 -r "$OUT/probe" -- python3 "$OUT/probe.py" > "$OUT/probe.log" 2>&1
"$VTUNE" -report summary -r "$OUT/probe" > "$OUT/probe-summary.txt" 2> "$OUT/probe-report.log"
"$VTUNE" -report hotspots -r "$OUT/probe" '-group-by=?' > "$OUT/report-groupings.txt" 2>&1 || true
"$VTUNE" -report hotspots -r "$OUT/probe" '-column=?' > "$OUT/report-columns.txt" 2>&1 || true
stage FIXED_PPL
COMPILER_BUILD_ROOT="$BUILD" EXPERIMENT_OUTPUT_DIR="$OUT/ppl" RUN_BENCH=0 bash "$OUT/ppl_gate.lsf" > "$OUT/ppl.log" 2>&1
MODEL=/work/ssc-zhaojh/llama_model/unsloth/Qwen3.8-Flash-Next-GGUF/UD-Q4_K_XL/Qwen3.8-Flash-Next-UD-Q4_K_XL-00001-of-00004.gguf
common=(-m "$MODEL" -t 38 -ngl 0 -b 2048 -ub 512 -ctk f16 -ctv f16 --numa distribute -r 10 --progress -o json)
profile_pp() {
    local name=$1
    local case_dir="$OUT/$name"
    mkdir -p "$case_dir"
    timeout --signal=TERM --kill-after=30s 3600s "$VTUNE" "${args[@]}" -data-limit=2048 -start-paused -r "$case_dir/vtune" -- python3 "$OUT/target_exec.py" "$case_dir" pp "$BUILD/build/bin/llama-bench" "${common[@]}" -p 2048 -n 0 > "$case_dir/vtune.log" 2>&1 &
    local collector=$!
    python3 "$OUT/roi_monitor.py" "$case_dir" "$VTUNE" 60 > "$case_dir/monitor.log" 2>&1 &
    local monitor=$!
    local rc=0 monitor_rc=0
    wait "$collector" || rc=$?
    printf '%s\\n' "$rc" > "$case_dir/collector.exit"
    wait "$monitor" || monitor_rc=$?
    [[ "$rc" == 0 && "$monitor_rc" == 0 ]]
    [[ $(cat "$case_dir/target.exit") == 0 ]]
    "$VTUNE" -report summary -r "$case_dir/vtune" -report-output "$case_dir/summary.txt" > "$case_dir/report.log" 2>&1
    for kind in function thread process,function; do
        if "$VTUNE" -report hotspots -r "$case_dir/vtune" -group-by "$kind" -format csv -csv-delimiter comma -limit 120 -report-output "$case_dir/hotspots-$kind.csv" >> "$case_dir/report.log" 2>&1; then
            printf 'hotspots-%s=0\\n' "$kind" >> "$case_dir/report-status.txt"
        else
            printf 'hotspots-%s=%s\\n' "$kind" "$?" >> "$case_dir/report-status.txt"
        fi
    done
    for report in callstacks top-down; do
        if "$VTUNE" -report "$report" -r "$case_dir/vtune" -format csv -csv-delimiter comma -limit 120 -report-output "$case_dir/$report.csv" >> "$case_dir/report.log" 2>&1; then
            printf '%s=0\\n' "$report" >> "$case_dir/report-status.txt"
        else
            printf '%s=%s\\n' "$report" "$?" >> "$case_dir/report-status.txt"
        fi
    done
    sha256sum -c "$OUT/sha256.txt" >> "$OUT/hash-check.txt"
}
stage PROFILE_FIRST_PP
profile_pp 01_first_pp
stage UNPROFILED_TG
mkdir -p "$OUT/02_intervening_tg"
timeout --signal=TERM --kill-after=15s 3600s python3 "$OUT/target_exec.py" "$OUT/02_intervening_tg" tg "$BUILD/build/bin/llama-bench" "${common[@]}" -p 0 -n 128 -d 2048 > "$OUT/tg-exec.log" 2>&1
stage PROFILE_LATER_PP
profile_pp 03_later_pp
stage COMPLETE
'''.replace('REMOTE_ROOT',remote)
report_start=driver.index('    "$VTUNE" -report summary -r "$case_dir/vtune"')
report_end=driver.index('    sha256sum -c "$OUT/sha256.txt"',report_start)
reports=driver[report_start:report_end]
driver=driver[:report_start]+driver[report_end:]
driver=driver.replace('stage COMPLETE\n','stage EXPORT_REPORTS\nfor name in 01_first_pp 03_later_pp; do\n    case_dir="$OUT/$name"\n'+reports+'done\nstage COMPLETE\n')
(here/'profile_pair.lsf').write_bytes(driver.encode('utf-8'))
for mode in ['threading','hotspots']:
    prefix='profile-waits-'+mode
    spec={'script':remote+'/profile_pair.lsf','kind':'VTune首次/后续PP等待诊断（不计分）',
          'purpose':'同节点首次PP→无采样TG→后续PP；'+('VTune软件线程/等待分析，定位大量自愿上下文切换的调用栈' if mode=='threading' else 'VTune硬件热点栈采样，对照首次与后续PP的CPU热点'),
          'config':'同一SHA核验Intel Classic2021.9 O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model原版；OpenMP/tinyBLAS ON、BLAS/GPU OFF；hg_6148单节点40slots/Gold6148，38推理线程close/cores、默认等待。先2.5秒工具探测（不触碰模型），独立固定PPL t/tb38 c512 chunks2 b512ub256 f16KV ngl0 NUMA distribute no-warmup timeout590s，±5%。PP p2048n0、TG p0n128d2048，各r10 t38 b2048ub512 KVf16 ngl0 NUMA distribute --progress。VTune '+mode+'，10ms栈采样2048bytes、每case数据上限2048MB；PP start-paused，正式prompt run1/10后resume，60秒后pause，目标继续完成全部10次。每30秒独立只读记录目标PID与各线程/NUMA；每case3600s保护。',
          'baseline':'同作业01_first_pp首次PP采样窗口；03_later_pp为TG后PP。仅同节点诊断，不是源码优化；TG无同作业内性能baseline',
          'baseline_case':prefix+'-first_pp_{job_id}','case_prefix':prefix,'comparison_scope':'same-node',
          'environment':{'PROFILE_MODE':mode},'lsf_args':['-J','qwen38_wait_'+mode],
          'ppl_scope':'本作业一次新固定PPL，三个诊断workload共享门槛；两个PP采样，无性能Score',
          'note':'不预设first一定慢或later一定快，必须用实际完整JSON与ROI时间确认。采样窗口按墙钟60秒，可能覆盖不同token数量；不能直接把样本计数当速度。软件插桩/暂停状态仍可能影响运行时，硬件模式为独立跨节点诊断参照。包装Python进程在采样树内，分析必须用target.pid和process分组区分llama-bench，避免把Python等待管道算进模型等待。收集summary/hotspots/callstacks/top-down及原始结果；可选report失败记录返回码，不伪造报告。完整10样本及所有旧慢样本保留，不修改生产构建或系统设置，开发诊断非正式成绩。'}
    (here/(mode+'.json')).write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared software threading and hardware hotspots paired diagnostics')
