import json
from pathlib import Path

root=Path(__file__).resolve().parent
remote='/work/apac2602/qwen38-cpu/optimization/20261019-q8-avx2-v2'
text=(root/'paired.lsf').read_text(encoding='utf-8')
begin=text.index('stage PP_BASELINE\n')
finish=text.index('stage PAIRED_COMPLETE\n',begin)
blocks={}
for phase in ['PP_BASELINE','PP_CANDIDATE','TG_CANDIDATE','TG_BASELINE']:
    start=text.index('stage '+phase+'\n',begin)
    stop=text.index('\nstage ',start+1)+1
    blocks[phase]=text[start:stop]
text=text[:begin]+''.join(blocks[p] for p in ['PP_CANDIDATE','PP_BASELINE','TG_BASELINE','TG_CANDIDATE'])+text[finish:]
text=text.replace('qwen38_q8_avx2_paired','qwen38_q8_avx2_reverse').replace('.q8_avx2_paired.','.q8_avx2_reverse.')
text=text.replace('"$ROOT/scripts/verify_pair.py"','"$ROOT/scripts/verify_reverse.py"')
(root/'reverse.lsf').write_bytes(text.encode())
verify=(root/'verify_pair.py').read_text().replace("['baselinePP','candidatePP','candidateTG','baselineTG']","['candidatePP','baselinePP','baselineTG','candidateTG']")
(root/'verify_reverse.py').write_bytes(verify.encode())
for variant in ['schedule4','schedule4_prefetch16']:
    spec=json.loads((root/(variant+'_paired_submission.json')).read_text(encoding='utf-8'))
    spec['script']=remote+'/reverse.lsf'
    spec['purpose']='反向顺序复核Q8 '+variant+'：候选先PP，原版后PP；原版先TG，候选后TG，确认完整模型差异是否依赖顺序'
    spec['config']=spec['config'].replace('baselinePP→candidatePP→candidateTG→baselineTG','candidatePP→baselinePP→baselineTG→candidateTG')
    spec['case_prefix']='q8-paired-reverse-'+variant
    spec['baseline_case']=spec['case_prefix']+'-baseline_{job_id}'
    spec['note']+=' 首轮原版PP约27~28而候选约51~54，异常大差异伴随原版PP高CV；TG没有稳定收益。本次反序确认，不将首轮差异直接归因于源码。反序与首轮跨节点，仍不能完全消除节点/缓存影响。'
    spec['retry_of']='4337011' if variant=='schedule4' else '4337012'
    (root/(variant+'_reverse_submission.json')).write_bytes(json.dumps(spec,ensure_ascii=False,indent=2).encode())
print(root/'reverse.lsf')
