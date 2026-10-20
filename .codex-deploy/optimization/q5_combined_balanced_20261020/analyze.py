import json
import statistics
import sys
from pathlib import Path

r=Path(sys.argv[1])
plan=json.loads((r/'plan.json').read_text())
def ppl(p):
    x=json.loads(p.read_text());c=x['conditions']
    assert x['status']=='PASS' and 2.63112<=x['ppl']<=2.90808
    assert (c['ppl_ctx'],c['ppl_chunks'],c['ppl_batch'],c['ppl_ubatch'],c['threads'],c['kv_cache_k'],c['kv_cache_v'],c['numa'],c['warmup'],c['gpu_layers'])==(512,2,512,256,38,'f16','f16','distribute',False,0)
    return {'ppl':x['ppl'],'elapsed_seconds':x['elapsed_seconds']}
def workload(p,key):
    x=json.loads(p.read_text())[0]
    assert (x['n_threads'],x['n_batch'],x['n_ubatch'],x['n_gpu_layers'],x['type_k'],x['type_v'])==(38,2048,512,0,'f16','f16')
    assert (x['n_prompt'],x['n_gen'],x['n_depth'])==((2048,0,0) if key=='pp' else (0,128,2048))
    assert len(x['samples_ts'])==len(x['samples_ns'])==10 and min(x['samples_ns'])>0
    return {'avg_ts':x['avg_ts'],'cv':statistics.stdev(x['samples_ts'])/statistics.mean(x['samples_ts']),'samples_ts':x['samples_ts']}
prep=r/'diagnostics/preparation'
preparation={'purpose':'Separate development preparation; retained but excluded from comparative statistics; not an official score.','ppl':ppl(prep/'perplexity_result.json'),'pp':workload(prep/'pp2048.json','pp'),'tg':workload(prep/'tg128_d2048.json','tg'),'path':str(prep)}
s={'order':plan['order'],'preparation':preparation,'interpretation':'Development Q5 combined balanced confirmation. Preparation fixed PPL, PP10 and TG10 completed, separately retained and excluded from gains. Four independent fixed PPL/PP10/TG10 cases pending; do not promote.'}
if '--preparation-only' not in sys.argv:
    cases=[]
    for item in plan['cases']:
        p=r/item['directory']
        case=dict(item,ppl=ppl(p/'perplexity_result.json'),pp=workload(p/'pp2048.json','pp'),tg=workload(p/'tg128_d2048.json','tg'))
        cases.append(case)
    groups={letter:{key:[c[key]['avg_ts'] for c in cases if c['letter']==letter] for key in ['pp','tg']} for letter in ['A','B']}
    means={letter:{key:statistics.mean(values) for key,values in g.items()} for letter,g in groups.items()}
    changes={key:means['B'][key]/means['A'][key]-1 for key in ['pp','tg']}
    s.update(cases=cases,pass_means=means,candidate_change=changes,decision='requires_joint_ABBA_BAAB_review_not_promoted')
    s['interpretation']='Completed Q5 combined '+plan['order']+' development confirmation after explicitly separate original fixed PPL/PP10/TG10 preparation. Four cases each independently passed fixed PPL and all10 PP/TG samples. Candidate pass-mean PP change={:+.3%}, TG change={:+.3%}. Both original passes and both candidate passes retained. Compare the other node/order and examine all within-pass variation before any conclusion; preparation is excluded, no formal score claimed.'.format(changes['pp'],changes['tg'])
(r/'summary.json').write_text(json.dumps(s,indent=2));print(json.dumps(s))
