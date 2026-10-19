import json
import math
from pathlib import Path

root=Path(__file__).resolve().parent
registry=json.loads((root.parent/'evidence/job_registry.json').read_text(encoding='utf-8'))
results=[]
for jid in ['4337011','4337012']:
    job=next(j for j in registry['jobs'] if j['job_id']==jid)
    assert job['state']=='DONE'
    cases={}
    for measurement in job['measurements']:
        case='baseline' if '-baseline_' in measurement['name'] else 'candidate'
        assert measurement['ppl']['status']=='PASS'
        data={'ppl':measurement['ppl'],'path':measurement['path']}
        for phase in ['pp','tg']:
            value=measurement[phase][0]
            assert (value['n_threads'],value['n_batch'],value['n_ubatch'],value['n_gpu_layers'],value['type_k'],value['type_v'])==(38,2048,512,0,'f16','f16')
            assert len(value['samples_ts'])==len(value['samples_ns'])==10
            data[phase]={'avg_ts':value['avg_ts'],'cv':value['stddev_ts']/value['avg_ts'],'samples_ts':value['samples_ts'],'samples_ns':value['samples_ns']}
        data['development_score']=100*math.sqrt(data['pp']['avg_ts']/46.929024*data['tg']['avg_ts']/3.295524)
        cases[case]=data
    relative={phase:cases['candidate'][phase]['avg_ts']/cases['baseline'][phase]['avg_ts']-1 for phase in ['pp','tg']}
    results.append({'job_id':jid,'variant':'schedule4' if jid=='4337011' else 'schedule4_prefetch16','host':job['exec_host'],'cases':cases,'relative_to_same_job_baseline':relative,'interpretation':'PP baseline is unusually slow and unstable while candidate executes later; PP speed difference is not yet attributable to code. TG does not establish an improvement. Keep all samples, including the late TG slowdown in 4337011. Reverse order confirmation required.'})
summary={'status':'FORWARD_COMPLETE_REVERSE_REQUIRED','order':['baselinePP','candidatePP','candidateTG','baselineTG'],'score_scope':'Development score only, not official performance. Each binary reused its independent fixed PPL pass with SHA256 verification; no PPL rerun in speed jobs.','results':results,'decision':'Preserve candidates but do not replace production. Submit reverse order comparisons before drawing a kernel speedup conclusion.'}
(root/'forward-analysis.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
destination=Path('D:/compete/q8-avx2-v2/evidence/forward-analysis.json')
destination.write_text(json.dumps(summary,indent=2),encoding='utf-8')
for result in results:
    print(result['job_id'],result['relative_to_same_job_baseline'])
