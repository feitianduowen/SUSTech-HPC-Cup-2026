import json
from pathlib import Path

here=Path(__file__).resolve().parent
prior=here.parent/'order_diagnostic'
remote='/work/apac2602/qwen38-cpu/optimization/20261020-order-crossover'
observer=(prior/'observed_run.py').read_text(encoding='utf-8')
helper='''def thread_samples(proc):
    result=[]
    for task in sorted((proc/'task').glob('[0-9]*')):
        try:
            stat=read(task/'stat')
            if not stat: continue
            fields=stat.rsplit(')',1)[1].split()
            sched=read(task/'schedstat')
            result.append({'tid':int(task.name),'start_ticks':int(fields[19]),'state':fields[0],
                           'cpu_seconds':(int(fields[11])+int(fields[12]))/os.sysconf('SC_CLK_TCK'),
                           'last_cpu':int(fields[36]),'wchan':read(task/'wchan'),
                           'schedstat_raw':sched,
                           'status':'\\n'.join(x for x in (read(task/'status') or '').splitlines() if x.split(':')[0] in ['Cpus_allowed_list','Mems_allowed_list','voluntary_ctxt_switches','nonvoluntary_ctxt_switches'])})
        except (OSError,ValueError,IndexError): continue
    return result

'''
observer=observer.replace('def sample(pid):',helper+'def sample(pid):')
observer=observer.replace("    row['sampling_seconds']=time.monotonic()-start",'''    row['threads']=thread_samples(proc)
    row['host_sched_schedstats']=read('/proc/sys/kernel/sched_schedstats')
    row['host_cpu_stat']=read('/proc/stat')
    row['host_loadavg']=read('/proc/loadavg')
    row['host_pressure']={kind:read('/proc/pressure/'+kind) for kind in ['cpu','memory','io']}
    row['host_cpu_frequency_khz']={str(p.parent.parent.name):read(p) for p in Path('/sys/devices/system/cpu').glob('cpu[0-9]*/cpufreq/scaling_cur_freq')}
    row['sampling_seconds']=time.monotonic()-start''')
(here/'observed_run.py').write_bytes(observer.encode('utf-8'))
(here/'ppl_gate.lsf').write_bytes((prior/'ppl_gate.lsf').read_bytes())
driver=(prior/'order_job.lsf').read_text(encoding='utf-8').split('if [[ "$ORDER_MODE" == aaa ]]; then')[0]
driver=driver.replace('qwen38_order','qwen38_crossover').replace('%J.order.','%J.crossover.')
driver=driver.replace('/optimization/20261019-order-diagnostic', '/optimization/20261020-order-crossover')
driver=driver.replace('ORDER_MODE','CROSSOVER').replace('^(pp-chain|tg-between|aaa)$','^(ABBA|BAAB)$').replace('order_job.lsf','crossover.lsf')
driver+='''stage FIXED_PPL
COMPILER_BUILD_ROOT="$BUILD" EXPERIMENT_OUTPUT_DIR="$OUT/ppl" RUN_BENCH=0 bash "$OUT/ppl_gate.lsf" > "$OUT/ppl.log" 2>&1
MODEL=/work/ssc-zhaojh/llama_model/unsloth/Qwen3.8-Flash-Next-GGUF/UD-Q4_K_XL/Qwen3.8-Flash-Next-UD-Q4_K_XL-00001-of-00004.gguf
common=(-m "$MODEL" -t 38 -ngl 0 -b 2048 -ub 512 -ctk f16 -ctv f16 --numa distribute -r 10 -v -o json)
ordinal=0
for ((block=1; block<=4; block++)); do
    letter=${CROSSOVER:$((block-1)):1}
    roles=(anchor probe tg)
    [[ "$letter" != B ]] || roles=(anchor tg probe)
    for role in "${roles[@]}"; do
        ordinal=$((ordinal+1))
        printf -v name '%02d_b%d_%s_%s' "$ordinal" "$block" "$letter" "$role"
        workload=pp; args=(-p 2048 -n 0)
        [[ "$role" != tg ]] || { workload=tg; args=(-p 0 -n 128 -d 2048); }
        stage "DIAGNOSTIC_$name"
        mkdir -p "$OUT/$name"
        python3 - "$OUT/$name/result.json" "$block" "$letter" "$role" "$workload" <<'PY'
import json,sys,time
p,b,l,r,w=sys.argv[1:]
json.dump({'block':int(b),'order':l,'role':r,'workload':w,'started_unix':time.time(),'baseline_role':'same-block anchor PP' if r=='probe' else None,'diagnostic_unscored':True},open(p,'w'),indent=2)
PY
        python3 "$OUT/observed_run.py" --output "$OUT/$name/$workload" --timeout 3600 --interval 30 "$BUILD/build/bin/llama-bench" "${common[@]}" "${args[@]}" > "$OUT/$name/$workload.observer.log" 2>&1
        python3 - "$OUT/$name/$workload.json" "$workload" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]))[0]
assert len(x['samples_ts'])==len(x['samples_ns'])==10
assert all(v>0 for v in x['samples_ns'])
assert (x['n_threads'],x['n_batch'],x['n_ubatch'],x['n_gpu_layers'],x['type_k'],x['type_v'])==(38,2048,512,0,'f16','f16')
assert (x['n_prompt'],x['n_gen'],x['n_depth'])==((2048,0,0) if sys.argv[2]=='pp' else (0,128,2048))
PY
        sha256sum -c "$OUT/sha256.txt" >> "$OUT/hash-check.txt"
    done
done
stage COMPLETE
'''
(here/'crossover.lsf').write_bytes(driver.encode('utf-8'))
template=json.loads((prior/'pp-chain.json').read_text(encoding='utf-8'))
for order in ['ABBA','BAAB']:
    prefix='diagnostic-crossover-'+order.lower()
    mapping={}
    for block,letter in enumerate(order,1):
        anchor=prefix+'-b%d_%s_anchor_{job_id}'%(block,letter)
        for role in ['anchor','probe','tg']:
            mapping[prefix+'-b%d_%s_%s_{job_id}'%(block,letter,role)]=anchor if role=='probe' else None
    spec=dict(template)
    spec.update(script=remote+'/crossover.lsf',kind='同节点平衡顺序诊断（不计分）',
                purpose='同节点四段'+order+'平衡顺序诊断：A=PP→PP→TG，B=PP→TG→PP；逐段比较probe/anchor PP并观察逐线程等待与内存分布',
                config='SHA核验只读Intel Classic2021.9 O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model原版，OpenMP/tinyBLAS ON，BLAS/GPU OFF；hg_6148单节点40slots/Gold6148，38推理线程close/cores、默认等待。开头一次固定PPL t/tb38 c512 chunks2 b512ub256 KVf16 ngl0 NUMA distribute no-warmup timeout590s，±5%。四段'+order+'，每段2次PP2048与1次TG128d2048，各r10 t38 b2048ub512 KVf16 ngl0 NUMA distribute -v；总8次PP10+4次TG10，无额外PPL插入。每30秒只读记录缺页/I/O/RSS/GGUF和其他NUMA分布，加各TID stat/status/schedstat/wchan、亲和性、host CPU/load/pressure/frequency（不可用时null），每测速命令3600秒保护；不计Score。',
                baseline='每段probe PP相对同段anchor PP；TG是顺序干预，无独立baseline。每个作业内同节点；ABBA与BAAB跨节点，只比较各自段内比值',
                baseline_case=prefix+'-no-global-baseline_{job_id}',case_prefix=prefix,
                measurement_baselines=mapping,
                environment={'CROSSOVER':order},lsf_args=['-J','qwen38_crossover_'+order],
                note='上一轮A/A复现相同代码第二次PP加速，跨节点PP-chain/TG-between不足以归因。现在同节点ABBA/BAAB平衡时间位置，仍存在跨段状态延续，无缓存重置；不能自动视为无残留效应的因果实验。记录每个线程而不只主线程；schedstat可能未启用，wchan可能受权限限制，保留原始值，不修改系统设置。带采样开销，仅诊断，所有慢样本保留；原始测量配置不改。',
                ppl_scope='本作业开始时独立固定PPL一次，12个诊断测速进程共享此门槛；无每段重新PPL，不计分')
    (here/(order+'.json')).write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Prepared ABBA and BAAB; 12 measured commands per job, no scores')
