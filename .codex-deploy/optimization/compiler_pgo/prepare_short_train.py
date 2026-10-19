import json
from pathlib import Path

here=Path(__file__).resolve().parent
remote='/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo'
text=(here/'pipeline.lsf').read_text(encoding='utf-8')
text=text.replace('cp "$ROOT/pipeline.lsf" "$OUT/pipeline.lsf"','cp "$ROOT/pipeline_short_train.lsf" "$OUT/pipeline.lsf"')
text=text.replace('exit "$rc"\' ERR','echo FAILED > "$OUT/training.watch"; exit "$rc"\' ERR')
text=text.replace('export PROF_DIR="$PROFILE"','''export PROF_DIR="$PROFILE"
# Preserve counts even if the diagnostic training run cannot reach normal exit.
export INTEL_PROF_DUMP_INTERVAL=60 INTEL_PROF_DUMP_CUMULATIVE=1
echo RUNNING > "$OUT/training.watch"
python3 /work/apac2602/qwen38-cpu/optimization/20261018-v1/scripts/monitor_runtime.py "$OUT/training-os.jsonl" "$OUT/training.watch" > "$OUT/training-monitor.log" 2>&1 &
monitor_pid=$!''')
text=text.replace('--no-warmup -o json)', '--no-warmup -v -o json)')
text=text.replace('    "${command[@]}" > "$OUT/training-$phase_name.json"', '    INTEL_PROF_DYN_PREFIX="$phase_name" "${command[@]}" > "$OUT/training-$phase_name.json"')
text=text.replace('training pp 900 -p 1024 -n 0','training pp 1200 -p 64 -n 0')
text=text.replace('training tg 600 -p 0 -n 32 -d 512','''training tg 900 -p 0 -n 8 -d 64
echo READY > "$OUT/training.watch"
wait "$monitor_pid"
python3 "$ROOT/check_training.py" "$OUT"''')
text=text.replace('python3 "$ROOT/write_manifest.py"','python3 "$ROOT/write_manifest_short.py"')
(here/'pipeline_short_train.lsf').write_bytes(text.encode())
manifest=(here/'write_manifest.py').read_text(encoding='utf-8').replace('Synthetic PP1024 and TG32@D512','Synthetic PP64 and TG8@D64; verbose plus 15s OS observation and 60s cumulative PGO counter dumps')
(here/'write_manifest_short.py').write_bytes(manifest.encode())
for level,parent in [(3,'4336626'),(2,'4336627')]:
    spec=json.loads((here/('retry_O'+str(level)+'.json')).read_text(encoding='utf-8'))
    spec.update(script=remote+'/pipeline_short_train.lsf',kind='Intel PGO短训练/构建/PPL',
        purpose='Intel O'+str(level)+' PGO训练超时后修复：缩小不计分训练、增加进度/OS日志与周期计数，成功后自动反馈编译及固定PPL',
        retry_of=parent,lsf_args=['-J','qwen38_O'+str(level)+'_pgo_short'],
        note='前次'+parent+'的无PGO control固定PPL=2.7767 PASS；gen构建成功，但PP1024训练900s超时且无dyn，尚未生成PGO构建。此次全新独立构建和计数目录，训练改PP64及TG8@D64（各r1、38线程；PP1200s/TG900s训练限时）；开启-v、15s OS观察及60s累计计数。训练必须正常完成且JSON参数匹配才合并；超时计数仅诊断，不自动冒充完整训练。正式PPL与未来完整PP/TG所有固定参数保持原样。先提交O3验证公共训练流程，O2待确认后再提交。开发自测，未计算成绩。')
    spec['config']=spec['config'].replace('训练仅合成PP1024/TG32@D512、r1、不计分','训练仅合成PP64/TG8@D64、r1、不计分；-v、15s OS记录；INTEL_PROF_DUMP_INTERVAL=60、INTEL_PROF_DUMP_CUMULATIVE=1；训练PP1200s/TG900s限时')
    (here/('short_O'+str(level)+'.json')).write_bytes(json.dumps(spec,ensure_ascii=False,indent=2).encode())
print('Prepared short-training pipeline and O3/O2 specs; submit O3 first.')
