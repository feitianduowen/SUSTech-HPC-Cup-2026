import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

here=Path(__file__).resolve().parent
evidence=here.parent/'evidence'
registry=json.loads((evidence/'job_registry.json').read_text(encoding='utf-8'))
jobs={j['job_id']:j for j in registry['jobs']}
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
raw_path=here.parent/'factor_screen/completed_evidence.json'
raw=json.loads(raw_path.read_text(encoding='utf-8'))
analysis_path=evidence/'analysis_updates/factor_screen_20261019.json'
analysis=json.loads(analysis_path.read_text(encoding='utf-8'))
for jid, files in raw.items():
    analysis['jobs'][jid]['evidence_files']=[str(raw_path)]
    analysis['jobs'][jid]['configuration_evidence']=files
    if jid in ['4338279','4338280','4338281']:
        verification=json.loads(next(v for k,v in files.items() if k.endswith('/variable-verification.json')))
        assert verification['single_factor_verified'] is True
    if jid=='4338281':
        log=next(v for k,v in files.items() if k.endswith('/02_candidate/perplexity.log'))
        assert '[1]-nan,[2]-nan' in log
        assert 'Final estimate:' not in log
    for k,v in files.items():
        if k.endswith('-sha-check.txt'): assert all(line.endswith(': OK') for line in v.splitlines())
analysis['updated_at_hkt']=stamp
analysis_path.write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
new_ids=['4338446','4338447','4338448','4338449']
next_actions={'updated_at_hkt':stamp,'phase':'reverse comparisons and AA running',
              'jobs':[{'job_id':jid,'state':jobs[jid]['state'],'host':jobs[jid].get('exec_host'),'factor':jobs[jid]['submission']['environment']['FACTOR']} for jid in new_ids],
              'completed_parent_jobs':{jid:jobs[jid]['state'] for jid in raw},
              'next':'完成后检查每版固定PPL及PP/TG完整10次。将反序与正序各自同节点比值比较，并结合A/A量化顺序效应；A/A若复现明显PP差异则暂不能归因于任何参数。fast=1已因NaN淘汰，无效PPL绝不放行。等待时长0因TG下降约36%暂停。保留所有慢样本，Intel编译器及固定参数不变。',
              'do_not_duplicate':['4338429'], 'excel':'D:/compete/Qwen38_CPU_实验日志.xlsx'}
(here/'next_actions.json').write_text(json.dumps(next_actions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
prior=here.parent/'factor_screen/next_actions.json'
data=json.loads(prior.read_text(encoding='utf-8'))
data['phase']='screen completed; follow reverse/AA results'
data['updated_at_hkt']=stamp
for job in data['jobs']: job['state']=jobs[job['job_id']]['state']
data['latest_followup']=str(here/'next_actions.json')
data['next']=next_actions['next']
prior.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'new_jobs':next_actions['jobs'],'parent_evidence_verified':True},ensure_ascii=False))
