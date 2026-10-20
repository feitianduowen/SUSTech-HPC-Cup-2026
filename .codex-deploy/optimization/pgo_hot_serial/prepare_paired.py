import json
from pathlib import Path

here=Path(__file__).resolve().parent
old='/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo'
remote='/work/apac2602/qwen38-cpu/optimization/20261019-pgo-hot-serial'
script=(here.parent/'compiler_pgo/paired_bench.lsf').read_text(encoding='utf-8')
script=script.replace(old,remote).replace('qwen38_compiler_paired','qwen38_hot_pgo_paired').replace('%J.compiler_paired','%J.hot_pgo_paired')
script=script.replace('    printf -v ordinal \'%02d\' "$i"','    ordinal=01\n    [[ "$name" != pgo ]] || ordinal=02')
# Record host and runtime choices in this job's evidence directory.
anchor='python3 "$ROOT/verify_manifest.py"'
script=script.replace(anchor, '{ date -Is; hostname; lscpu; module list; icc --version; icpc --version; env | sort | grep -E "^(OMP_|MKL_|OPENBLAS_|BLIS_)"; } > "$OUT/environment.txt" 2>&1\n'+anchor)
(here/'paired_bench.lsf').write_bytes(script.encode('utf-8'))
(here/'verify_manifest.py').write_bytes((here.parent/'compiler_pgo/verify_manifest.py').read_bytes())
for order in ['control-first','pgo-first']:
    spec={
      'script':remote+'/paired_bench.lsf','kind':'同节点完整对照',
      'purpose':'热点源文件单线程训练PGO首次完整模型配对测速，'+order+'；产物来自4337670，固定PPL先通过后测速',
      'config':'Intel Classic2021.9 O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model；官方源码d812350；hg_6148 40slots/38推理线程，OpenMP close/cores、BLAS OFF；原版control及PGO同节点顺序各重新跑固定PPL t/tb38 c512 chunks2 b512ub256 f16KV ngl0 NUMA distribute no-warmup timeout590s，含边界±5%；随后每版本PP2048及TG128d2048各r10，b2048ub512 f16KV ngl0 NUMA distribute；无VTune/OS采样；顺序='+order,
      'baseline':'本作业01_control：4337670中SHA核验只读复用4337216的Intel O3 plain control；同节点顺序对照',
      'baseline_case':'hot-pgo-control_{job_id}','case_prefix':'hot-pgo',
      'environment':{'PGO_PARENT_JOB':'4337670','PGO_ORDER':order},
      'lsf_args':['-J','qwen38_hot_pgo_'+order],
      'ppl_scope':'每个二进制在本作业分别重新跑固定PPL，无共享PPL；先校验4337670 manifest全部产物SHA',
      'note':'训练PP64/TG8d64 t1 OMP1且完整正常退出，新计数独立合并；训练未用WikiText且不计分。gen/use范围校验恰好quants.c、sgemm.cpp和thin main三源。反馈日志保留未训练函数静态profile提醒，覆盖有限；性能收益以完整测速为准。正反顺序分属不同节点，只比较各自同节点比例并保留顺序/缓存局限；全部10次样本保留。只算开发自测分数，不是正式成绩。'
    }
    (here/('paired_'+order+'.json')).write_bytes(json.dumps(spec,ensure_ascii=False,indent=2).encode('utf-8'))
print(here/'paired_bench.lsf')
