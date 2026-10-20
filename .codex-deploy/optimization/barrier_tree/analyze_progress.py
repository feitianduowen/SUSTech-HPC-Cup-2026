import json
import math
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

here=Path(__file__).resolve().parent
evidence=here.parent/'evidence'
sys.path.insert(0,str(here.parent/'orchestrator'))
from ppl_policy5 import reassess

registry=json.loads((evidence/'job_registry.json').read_text(encoding='utf-8'))
jobs={j['job_id']:j for j in registry['jobs']}
raw=json.loads((here/'runtime_progress_evidence.json').read_text(encoding='utf-8'))
reference=json.loads((evidence/'ppl_policy_reference.json').read_text(encoding='utf-8'))
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
analysis={'updated_at_hkt':stamp,'source':'Fresh LSF/original JSON plus binary hash and actual speed environment snapshots','jobs':{}}
ids=['4340520','4340521','4340614','4340615']
for jid in ids:
    job=jobs[jid];values={}
    for path,text in raw[jid].items():
        if path=='hash-check.txt': assert all(s.endswith(': OK') for s in text.splitlines())
        if path.endswith('/speed_environment.txt'):
            env=dict(line.split('=',1) for line in text.splitlines() if '=' in line)
            label=Path(path).parent.name.split('_',1)[1]
            assert env['OMP_WAIT_POLICY']=='ACTIVE'
            assert env['OMP_PROC_BIND']=='close' and env['OMP_PLACES']=='cores'
            assert env['OMP_NUM_THREADS']=='38'
            if jid in ['4340520','4340521']:
                assert env['KMP_BLOCKTIME']==('200' if label.startswith('A') else 'infinite')
                assert 'KMP_PLAIN_BARRIER_PATTERN' not in env
            else:
                assert env['KMP_BLOCKTIME']=='200'
                assert env['KMP_PLAIN_BARRIER_PATTERN']==('hyper,hyper' if label.startswith('A') else 'tree,tree')
                assert env['KMP_FORKJOIN_BARRIER_PATTERN']=='hyper,hyper'
    for m in job['measurements']:
        label=m['name'].rsplit('-',1)[1].split('_')[0]
        value={'ppl':None,'pp':None,'tg':None}
        if m.get('ppl'):
            assert reassess(m['ppl'],reference)['verdict']=='PASS'
            value['ppl']=m['ppl']['ppl']
        for phase in ['pp','tg']:
            if m.get(phase):
                x=m[phase][0]
                assert len(x['samples_ts'])==len(x['samples_ns'])==10
                assert (x['n_threads'],x['n_batch'],x['n_ubatch'],x['type_k'],x['type_v'],x['n_gpu_layers'])==(38,2048,512,'f16','f16',0)
                assert (x['n_prompt'],x['n_gen'],x['n_depth'])==((2048,0,0) if phase=='pp' else (0,128,2048))
                value[phase]=x['avg_ts']
        value['complete']=all(value[k] is not None for k in ['ppl','pp','tg'])
        values[label]=value
    pairs=[]
    for n in [1,2]:
        a,b=values.get('A'+str(n),{}),values.get('B'+str(n),{})
        changes={}
        for phase in ['pp','tg']:
            if a.get(phase) and b.get(phase): changes[phase]=100*(b[phase]/a[phase]-1)
        complete=bool(a.get('complete') and b.get('complete'))
        if complete:changes['geomean']=100*(math.sqrt(b['pp']/a['pp']*b['tg']/a['tg'])-1)
        pairs.append({'pair':n,'complete':complete,'change_percent':changes})
    completed=sum(v['complete'] for v in values.values())
    stage=raw[jid].get('job.status','').strip()
    note=f'截至采集时间{registry["updated_at"]}，LSF {job["state"]}，阶段{stage}；完整PPL+PP10+TG10为{completed}/4轮。已完成PPL均按官方模型/数据/参数及5%通过，已写入的PP/TG均完整10次；当前已记录SHA及测速参数核验一致。'
    for p in pairs:
        if p['change_percent']:
            changes='、'.join(f'{k} {v:+.2f}%' for k,v in p['change_percent'].items())
            note+=f'B{p["pair"]}/A{p["pair"]}：{changes}（'+('整对完成' if p['complete'] else '整对尚未完成')+'）。'
    if job['state']=='RUN':note+='尚未完成四轮，不计算作业整体结论，不把单轮较快值当参数收益。保留首次慢速和全部低速样本。'
    else:
        assert completed==4
        note+='四轮全部完成；需结合两种顺序、首次状态和全部样本评估，开发自测非正式成绩。'
        if jid=='4340520':
            a1,a2,b1,b2=(values[k] for k in ['A1','A2','B1','B2'])
            note+=(f'同为200ms的A1→A2，PP {a1["pp"]:.6f}→{a2["pp"]:.6f}；回退200ms后仍接近infinite的{b1["pp"]:.6f}/{b2["pp"]:.6f}。'
                   f'因此首次大幅差异不能简单归因于infinite。第二对B2/A2约PP {pairs[1]["change_percent"]["pp"]:+.2f}%、TG {pairs[1]["change_percent"]["tg"]:+.2f}%，幅度较小，须等待反序完整结果确认，暂不采用。')
    analysis['jobs'][jid]={'summary':note,'values':values,'pairs':pairs,'completed_cases':completed,'state':job['state'],'stage':stage,'configuration_evidence':raw[jid]}
(evidence/'analysis_updates/runtime_progress_20261020.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(here/'runtime_progress_analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for directory,key in [('barrier_tree','jobs'),('kmp_infinite','jobs')]:
    p=here.parent/directory/'next_actions.json';next_actions=json.loads(p.read_text(encoding='utf-8'))
    next_actions['updated_at_hkt']=stamp
    for j in next_actions[key]: j['state']=jobs[j['job_id']]['state']
    for j in next_actions.get('other_active_jobs',[]): j['state']=jobs[j['job_id']]['state']
    completed_ids=[jid for jid in ids if jobs[jid]['state']=='DONE']
    running_ids=[jid for jid in ids if jobs[jid]['state']=='RUN']
    next_actions['phase']=f'{len(completed_ids)}/4 runtime comparison jobs completed'
    next_actions['latest_progress']=str(here/'runtime_progress_analysis.json')
    next_actions['next']='已完成：'+('、'.join(completed_ids) or '无')+'；继续收取运行中的'+('、'.join(running_ids) or '无')+'，不重复提交。4340520/4340521是等待时长，4340614/4340615是普通barrier算法。所有完整PPL与十次样本按原始记录保存，最终需四轮和两顺序均完成后比较同节点配对。当前部分配对方向相反或未完成，不宣称收益；保留慢样本，参数保持固定，正式采用运行时变更前按题目申报。'
    p.write_text(json.dumps(next_actions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({jid:{'state':v['state'],'completed_cases':v['completed_cases'],'pairs':v['pairs']} for jid,v in analysis['jobs'].items()},ensure_ascii=False))
