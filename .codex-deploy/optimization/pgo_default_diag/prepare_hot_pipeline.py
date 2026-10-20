import json
from pathlib import Path

here = Path(__file__).resolve().parent
dest = here.parent/'pgo_hot_serial'
dest.mkdir(exist_ok=True)
base = here.parent/'compiler_pgo'
old = '/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo'
remote = '/work/apac2602/qwen38-cpu/optimization/20261019-pgo-hot-serial'
script = (base/'pipeline_ggml_pgo_v4.lsf').read_text(encoding='utf-8')
script = script.replace('qwen38_compiler_pgo','qwen38_pgo_hot_serial').replace('%J.compiler_pgo','%J.pgo_hot_serial')
script = script.replace('#BSUB -W 04:00','#BSUB -W 02:00')
script = script.replace('ROOT='+old,'ROOT='+remote)
script = script.replace('"$ROOT/verify_source.py"', '"'+old+'/verify_source.py"').replace('"$ROOT/source_identity.json"','"'+old+'/source_identity.json"')
script = script.replace('pipeline_ggml_pgo_v4.lsf','pipeline.lsf').replace('ggml_pgo_targets_v2.cmake','hot_sources.cmake')
script = script.replace('    case "$mode" in\n        gen) pgo="-prof-gen=threadsafe -prof-dir $PROFILE";;\n        use) pgo="-prof-use=nomerge -prof-dir $PROFILE";;\n    esac\n','')
script = script.replace('"-DQWEN_PGO_PHASE=$mode"','"-DQWEN_PGO_PHASE=$mode" "-DQWEN_PROFILE_DIR=$PROFILE"')
script = script.replace('check_pgo_scope_v2.py','check_hot_scope.py')
script = script.replace('CONTROL_OUT="$ROOT/results/$CONTROL_PARENT"','CONTROL_OUT="'+old+'/results/$CONTROL_PARENT"')
script = script.replace('CONTROL_BUILD="$ROOT/builds/$CONTROL_PARENT/control"','CONTROL_BUILD="'+old+'/builds/$CONTROL_PARENT/control"')
script = script.replace('export INTEL_PROF_DUMP_INTERVAL=60 INTEL_PROF_DUMP_CUMULATIVE=1','unset INTEL_PROF_DUMP_INTERVAL INTEL_PROF_DUMP_CUMULATIVE\nexport OMP_NUM_THREADS=1')
script = script.replace('common=(-m "$MODEL" -t 38','common=(-m "$MODEL" -t 1')
script = script.replace('training pp 3600','training pp 900').replace('training tg 3600','training tg 900')
script = script.replace('stage MERGE','export OMP_NUM_THREADS=38\nstage MERGE')
script = script.replace('write_manifest_ggml.py','write_manifest.py')
(dest/'pipeline.lsf').write_bytes(script.encode('utf-8'))
checker = (base/'check_training.py').read_text(encoding='utf-8').replace("==(38,2048", "==(1,2048")
(dest/'check_training.py').write_bytes(checker.encode('utf-8'))
manifest = (base/'write_manifest_ggml.py').read_text(encoding='utf-8').replace(old,remote)
manifest = manifest.replace('GGML backend only; llama/common/tools keep plain Intel optimization in gen and use stages','Only x86/quants.c, llamafile/sgemm.cpp and thin llama-bench main.cpp; all other sources plain')
manifest = manifest.replace('Synthetic PP64 and TG8@D64; verbose plus 15s OS observation and 60s cumulative PGO counter dumps; 38 threads; profile branch counters only; unscored; no WikiText training','Synthetic PP64 and TG8@D64; default counters, single inference/OpenMP thread to avoid races; 900s each, normal exits only; no periodic dump, new profiles only; unscored, no WikiText training; PPL and official performance remain 38 threads')
(dest/'write_manifest.py').write_bytes(manifest.encode('utf-8'))
(dest/'ppl_gate.lsf').write_bytes((base/'ppl_gate.lsf').read_bytes())
spec = {
 'script':remote+'/pipeline.lsf','kind':'热点源码PGO单线程训练与PPL验证',
 'purpose':'修复线程安全PGO运行时checkpoint严重开销：仅两热点源文件和thin main默认插桩，以单线程收集无竞争的新训练计数，再反馈编译并跑38线程固定PPL',
 'config':'Intel Classic2021.9 O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model；hg_6148 40slots；官方原始源码SHA校验，只读，不覆盖旧源码/构建；gen仅quants.c/sgemm.cpp/main.cpp -prof-gen=default，use对应-prof-use=nomerge；独立build/profile。训练PP64r1、TG8d64r1，t1/OMP1，b2048ub512 f16KV ngl0 NUMA distribute；分别900s，无周期dump，正常退出并验证完整JSON后才合并。use跑量化单测和四工具链接检查；固定PPL t/tb38,c512,chunks2,b512ub256,f16KV,ngl0,NUMA distribute,no-warmup,590s，±5%含边界。此作业不跑完整PP/TG测速。',
 'baseline':'4337216已验证Intel O3 plain control，SHA256核验后只读复用；PPL2.7767，未重跑control PPL；无完整模型性能baseline',
 'environment':{'PGO_OPT_LEVEL':'3'},'retry_of':'4337448',
 'note':'4337634 VTune显示77.3%CPU在threadsafe checkpoint；4337642 default模式诊断后才提交此方案。38线程default诊断计数可能竞争，绝不复用。此作业新计数只由1线程真实模型训练产生；训练计数与单线程分布不完全代表38线程负载，后续需完整配对测速证明收益。失败/超时则禁止合并。生产模型、官方源、旧构建全部保留。',
 'ppl_scope':'control复用SHA校验的4337216固定PPL；候选use必须独立重新跑固定PPL，容差±5%'
}
(dest/'pipeline.json').write_bytes(json.dumps(spec,ensure_ascii=False,indent=2).encode('utf-8'))
print(dest)
