import difflib
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
remote = '/work/apac2602/qwen38-cpu/optimization/20261020-hc4-post-v2'
variant = 'hc4-post-v2'
original = (here/'ops.original.cpp').read_text(encoding='utf-8')
start = original.index('static void ggml_compute_forward_dsv4_hc_post_f32(')
pos = original.index('    for (int64_t ir = ir0; ir < ir1; ++ir) {', start)
fast = (here/'fastpath.inc').read_text(encoding='utf-8') + '\n'
candidate = original[:pos] + fast + original[pos:]
candidate = candidate.replace('#include <cmath>', '#include <cmath>\n\n#if defined(__AVX2__) && defined(__FMA__)\n#include <immintrin.h>\n#endif', 1)
relative = 'ggml/src/ggml-cpu/ops.cpp'
dest = here/'variants'/variant/relative
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_bytes(candidate.encode())
(here/(variant+'.patch')).write_text(''.join(difflib.unified_diff(original.splitlines(True),candidate.splitlines(True),fromfile='a/'+relative,tofile='b/'+relative)),encoding='utf-8',newline='\n')
manifest = {'variants': {variant: {'file': relative,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'original_sha256':hashlib.sha256((here/'ops.original.cpp').read_bytes()).hexdigest()}}}
(here/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8',newline='\n')
old = here.parent/'softmax_rows_20261020'
(here/'copy_verify.py').write_text((old/'copy_verify.py').read_text(encoding='utf-8').replace('20261020-softmax-rows','20261020-hc4-post-v2'),encoding='utf-8',newline='\n')
(here/'ppl_gate.lsf').write_text((old/'ppl_gate.lsf').read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
pipeline=(old/'build_and_pair.lsf').read_text(encoding='utf-8').replace('20261020-softmax-rows','20261020-hc4-post-v2').replace('softmax_rows','hc4_post').replace('softmax-rows','hc4-post-v2').replace('SOFTMAX','HC4_POST').replace('softmax_check.cpp','hc_check.cpp').replace('softmax-bench.log','hc-bench.log')
pipeline=pipeline.replace('#BSUB -W 04:00','#BSUB -W 06:00')
pipeline=pipeline.replace('unset KMP_AFFINITY GOMP_CPU_AFFINITY KMP_BLOCKTIME OMP_WAIT_POLICY KMP_HW_SUBSET PROF_DIR INTEL_PROF_DUMP_INTERVAL INTEL_PROF_DUMP_CUMULATIVE','unset KMP_AFFINITY GOMP_CPU_AFFINITY KMP_BLOCKTIME OMP_WAIT_POLICY KMP_HW_SUBSET KMP_FORKJOIN_BARRIER KMP_FORKJOIN_BARRIER_PATTERN KMP_PLAIN_BARRIER KMP_PLAIN_BARRIER_PATTERN KMP_REDUCTION_BARRIER KMP_REDUCTION_BARRIER_PATTERN KMP_HOT_TEAMS_MAX_LEVEL KMP_HOT_TEAMS_MODE PROF_DIR INTEL_PROF_DUMP_INTERVAL INTEL_PROF_DUMP_CUMULATIVE')
pipeline=pipeline.replace("-diag-disable=10441'","-diag-disable=10441 -qopt-report=3 -qopt-report-phase=vec'")
pipeline=pipeline[:pipeline.index('# The op may be bypassed')]+'''ORDER=${PAIR_ORDER:?set PAIR_ORDER}
case "$ORDER" in
    ABBA) names=(A1 B1 B2 A2) ;;
    BAAB) names=(B1 A1 A2 B2) ;;
    *) exit 2 ;;
esac
ordinal=0
for name in "${names[@]}"; do
    ordinal=$((ordinal+1))
    stage "PPL_PP10_TG10_$name"
    CASE_ROOT="$SRC"
    [[ "$name" != A* ]] || CASE_ROOT="$BASE"
    dir=$(printf "%02d_%s" "$ordinal" "$name")
    sha256sum "$CASE_ROOT/build/bin/llama-bench" "$CASE_ROOT/build/bin/llama-perplexity" "$CASE_ROOT/build/bin/"lib*.so* > "$OUT/$name-sha256.txt"
    COMPILER_BUILD_ROOT="$CASE_ROOT" RUN_BENCH=1 EXPERIMENT_OUTPUT_DIR="$OUT/$dir" bash "$OUT/ppl_gate.lsf" > "$OUT/$name-bench.log" 2>&1
done
stage COMPLETE
'''
(here/'build_and_pair.lsf').write_text(pipeline,encoding='utf-8',newline='\n')
for order in ['ABBA','BAAB']:
    prefix='confirm-hc4-post-v2-'+order.lower()
    mappings={prefix+'-'+n+'_{job_id}': (prefix+'-'+('A1' if n=='B1' else 'A2')+'_{job_id}' if n[0]=='B' else None) for n in ['A1','B1','B2','A2']}
    spec={
        'script':remote+'/build_and_pair.lsf','kind':'同节点完整对照',
        'purpose':'HC-post四路连续通道专用展开：固定hc=4并提升post/comb加载，保留每输出乘加顺序和线程分块；其余形状走原版。仅修改ops.cpp，不叠加HC-pre、NUMA或量化候选。',
        'environment':{'SOURCE_VARIANT':variant,'PAIR_ORDER':order},
        'lsf_args':['-J','qwen38_hc4v2_'+order.lower()],
        'config':'Intel Classic2021.9 icc/icpc O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model；OpenMP ON，BLAS OFF；hg_6148 Gold6148双路40核40slots，推理38线程close/cores。独立源码副本全SHA校验，四工具构建、量化测试、ldd；实际GGML图1/3/38线程、hc1/2/4/8、连续/填充/转置、comb缺省/单位/稠密、短行尾段和真实2560通道，3重复及跨库逐bit一致门槛；10轮AB/BA算子微基准。整模顺序'+order+'，A=原版，B=候选；每case固定PPL t/tb38 c512 chunks2 b512 ub256 f16KV ngl0 NUMA distribute no-warmup 590s ±5%；每case PP2048、TG128d2048各r10 b2048 ub512。',
        'baseline':'本作业同节点Intel原版A1/A2；B1对应A1，B2对应A2；算子对照原版实际库',
        'case_prefix':prefix,'comparison_scope':'same-node','measurement_baselines':mappings,
        'ppl_scope':'每case独立固定PPL，无共享PPL',
        'note':'实际库逐bit差分不过即停止，保留失败及所有慢样本。两个节点分别ABBA/BAAB以检查顺序影响，跨节点不直接相除；算子收益不是整模成绩，完整结果前不替换部署。'}
    (here/('submission_'+order.lower()+'.json')).write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(json.dumps(manifest))
