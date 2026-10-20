import json
import tarfile
from pathlib import Path

base = Path('D:/compete/.codex-deploy/optimization')
old = base / 'q5_balanced_20261020'
out = base / 'q5_combined_balanced_20261020'
out.mkdir(exist_ok=False)
root = '/work/apac2602/qwen38-cpu/optimization/20261020-q5-combined-balanced'
combined = '/work/apac2602/qwen38-cpu/optimization/20261020-q5-combined'
text = (old / 'balanced.lsf').read_text(encoding='utf-8')
text = text.replace('qwen38_q5_balanced', 'qwen38_q5_combined_balanced').replace('%J.q5_balanced', '%J.q5_combined_balanced')
text = text.replace('/optimization/20261020-q5-balanced', '/optimization/20261020-q5-combined-balanced')
text = text.replace('/optimization/20261019-q5-mask', '/optimization/20261020-q5-combined')
text = text.replace('sources/q5-mask-4338563', 'sources/q5-mask-unroll4-4340624')
text = text.replace('$Q5/results/4338563/sha256.txt', '$Q5/results/4340624/candidate-sha256.txt')
text = text.replace('$Q5/results/4339768/baseline-sha256.txt', '$Q5/results/4340624/baseline-sha256.txt')
start = text.index('# Explicit development-only preparation.')
end = text.index('\nbaseline_index=0', start)
text = text[:start] + '''# Separate development preparation: original fixed PPL + PP10 + TG10.
# Retain all raw samples; exclude this predeclared directory from comparative gains.
stage PREPARATION_FIXED_PPL_PP10_TG10
PREP="$OUT/diagnostics/preparation"
mkdir -p "$PREP"
COMPILER_BUILD_ROOT="$BASE" RUN_BENCH=1 EXPERIMENT_OUTPUT_DIR="$PREP" bash "$OUT/ppl_gate.lsf" > "$OUT/preparation.log" 2>&1
check_hashes
python3 "$OUT/analyze.py" "$OUT" --preparation-only > "$OUT/preparation-check.log"
''' + text[end:]
(out / 'balanced.lsf').write_text(text, encoding='utf-8', newline='\n')
(out / 'ppl_gate.lsf').write_bytes((old / 'ppl_gate.lsf').read_bytes())
verify = (old / 'verify_existing.py').read_text(encoding='utf-8')
verify = verify.replace('20261019-q5-mask', '20261020-q5-combined').replace('sources/q5-mask-4338563', 'sources/q5-mask-unroll4-4340624')
verify = verify.replace("['variants']['q5-mask']", "['variants']['q5-mask-unroll4']").replace("'4338563'", "'4340624'")
(out / 'verify_existing.py').write_text(verify, encoding='utf-8', newline='\n')
analysis = (old / 'analyze.py').read_text(encoding='utf-8')
analysis = analysis.replace("'tg':workload(prep/'tg128_d2048.json','tg')", "'pp':workload(prep/'pp2048.json','pp'),'tg':workload(prep/'tg128_d2048.json','tg')")
analysis = analysis.replace("x['stddev_ts']/x['avg_ts']", "statistics.stdev(x['samples_ts'])/statistics.mean(x['samples_ts'])")
analysis = analysis.replace('Preparation fixed PPL and TG10', 'Preparation fixed PPL, PP10 and TG10')
analysis = analysis.replace('original TG10 preparation', 'original fixed PPL/PP10/TG10 preparation')
analysis = analysis.replace('Development Q5 balanced', 'Development Q5 combined balanced').replace('Completed Q5 ', 'Completed Q5 combined ')
(out / 'analyze.py').write_text(analysis, encoding='utf-8', newline='\n')
for order in ['ABBA', 'BAAB']:
    plan = json.loads((old / (order + '-plan.json')).read_text(encoding='utf-8'))
    plan.update(B='Q5 mask+unroll4 Intel build from4340624',
                preparation='Separate original fixed PPL then PP2048 r10 then TG128d2048 r10; all preparation samples retained, excluded from gains. Four later cases each run fresh fixed PPL, PP10 and TG10.')
    (out / (order + '-plan.json')).write_text(json.dumps(plan, indent=2), encoding='utf-8')
    spec = json.loads((old / (order + '.json')).read_text(encoding='utf-8'))
    spec.update(script=root+'/balanced.lsf', kind='Q5组合源码候选完整准备段后换序复测',
                purpose='复测4340624 Q5 mask+unroll4组合版，顺序'+order+'（A原版/B组合）。此前A/B/A末轮对照PP+2.34%、TG-0.04%，首轮原版PP明显偏慢，尚未证明模型收益。本次原版完整PPL/PP10/TG10准备段单列保留，然后四段独立PPL/PP10/TG10。',
                config='Intel Classic2021.9 O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model；OpenMP ON/BLAS OFF；hg_6148 40slots，推理38线程close/cores。复用4340624独立源码/构建，不重新编译；3687源码SHA与原版/组合四工具及所有lib*.so* SHA核验。原版完整固定PPL→PP10→TG10准备段独立保存、排除比较；其后'+order+'四段各固定PPL t/tb38 c512 chunks2 b512ub256 f16KV ngl0 NUMA distribute no-warmup590s ±5%，PP2048/TG128d2048各r10 b2048ub512。无VTune、无系统设置更改。',
                lsf_args=['-J','qwen38_q5_combo_'+order],
                case_prefix='confirm-q5-combined-balanced-'+order.lower(),
                baseline_case='confirm-q5-combined-balanced-'+order.lower()+'-baseline1_{job_id}',
                note='开发复测。增加明确单列的原版PP10准备以检查首次PP偏慢，所有准备和比较样本保留。四比较段仍各r10且各自PPL；两节点ABBA/BAAB位置互补，不假定准备段能消除漂移，最终联合审查两个方向及每段变异，未确立模型收益前不替换部署。')
    (out / (order+'.json')).write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding='utf-8')
with tarfile.open(out / 'inputs.tar.gz', 'w:gz') as archive:
    for path in out.iterdir():
        if path.suffix in ['.py', '.lsf', '.json']:
            archive.add(path, arcname=path.name)
print(out)
