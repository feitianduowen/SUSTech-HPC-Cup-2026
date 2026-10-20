import json
from pathlib import Path

r=Path(__file__).resolve().parent
s=(r/'resume_checks.lsf').read_text(encoding='utf-8')
s=s.replace('qwen38_q5_mask_resume','qwen38_q5_mask_reverse').replace('%J.q5_mask_resume.','%J.q5_mask_reverse.')
s=s.replace('cp "$ROOT/resume_checks.lsf" "$OUT/pipeline.lsf"','cp "$ROOT/reverse_checks.lsf" "$OUT/pipeline.lsf"')
s=s.replace('# Bracket the candidate with identical original builds; retain order limitations.','# Reverse B/A/B confirmation; each case independently runs fixed PPL and PP10/TG10.')
s=s.replace('for name in baseline candidate baseline_after; do','for name in candidate baseline candidate_after; do')
s=s.replace('ordinal=02\n    if [[ "$name" == baseline ]]; then CASE_ROOT="$BASE"; ordinal=01; fi\n    if [[ "$name" == baseline_after ]]; then CASE_ROOT="$BASE"; ordinal=03; fi','ordinal=01\n    if [[ "$name" == baseline ]]; then CASE_ROOT="$BASE"; ordinal=02; fi\n    if [[ "$name" == candidate_after ]]; then ordinal=03; fi')
assert 'baseline_after' not in s
(r/'reverse_checks.lsf').write_bytes(s.encode())
d=json.loads((r/'resume_submission.json').read_text(encoding='utf-8'))
d['script']=d['script'].replace('resume_checks.lsf','reverse_checks.lsf')
d['purpose']='Q5掩码解包反序B/A/B完整确认：4338567微基准五长度提升5.59%-12.66%、逐bit验证通过，但A/B/A原版PP漂移31.11→53.35 t/s，整模型收益未确认。复用同一Intel候选，候选→原版→候选独立PPL和PP10/TG10。'
d['kind']='Q5_1源码优化反序完整确认'
d['lsf_args']=['-J','qwen38_q5_mask_reverse']
d['config']=d['config'].replace('baseline→candidate→baseline_after','candidate→baseline→candidate_after')
d['baseline']='本作业02_baseline原版Intel（同节点中间执行），与01_candidate及03_candidate_after比较；跨作业4338567仅用于顺序趋势参考'
d['case_prefix']='confirm-q5-mask-reverse'
d['baseline_case']='confirm-q5-mask-reverse-baseline_{job_id}'
d['note']='原版与候选均复用已SHA核验的固定产物。核函数收益不代表模型收益；本轮B/A/B仍须保留时段、缓存、NUMA驻留影响，不能只挑选有利baseline或剔除慢样本。首次4338563验证工具失败及4338567完整结果全部保留。'
(r/'reverse_submission.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
