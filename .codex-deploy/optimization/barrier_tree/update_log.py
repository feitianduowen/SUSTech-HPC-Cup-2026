import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

here=Path(__file__).resolve().parent
evidence=here.parent/'evidence'
r=json.loads((evidence/'job_registry.json').read_text(encoding='utf-8'))
jobs={j['job_id']:j for j in r['jobs']}
checks=json.loads((here/'runtime_check_evidence.json').read_text(encoding='utf-8'))
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
new_ids=['4340614','4340615']
new=[]
analysis={'updated_at_hkt':stamp,'source':'Intel runtime effective settings and fresh LSF/original JSON snapshot','jobs':{}}
for jid in new_ids:
    j=jobs[jid]
    v=json.loads(checks[jid]['runtime-validation.json'])
    assert v['hyper']['plain_pattern']=='hyper,hyper' and v['tree']['plain_pattern']=='tree,tree'
    for mode in v.values():
        assert mode['forkjoin_pattern']=='hyper,hyper' and mode['KMP_BLOCKTIME']==200 and mode['threads']==38
    new.append({'job_id':jid,'state':j['state'],'host':j.get('exec_host'),'order':j['submission']['environment']['CASE_ORDER']})
    analysis['jobs'][jid]={'summary':'Intel实际运行时验证通过：普通barrier分别hyper/tree，forkjoin均hyper、blocktime均200ms、ACTIVE/38线程。四轮固定PPL和PP/TG执行中，当前尚无完整收益结论。','runtime_evidence':checks[jid]}
for jid in ['4340520','4340521']:
    j=jobs[jid];partial=[]
    for m in j['measurements']:
        val={'name':m['name'],'ppl':(m.get('ppl') or {}).get('ppl'),'ppl_status':(m.get('ppl') or {}).get('status')}
        for phase in ['pp','tg']:
            if m.get(phase):
                x=m[phase][0]
                assert len(x['samples_ts'])==len(x['samples_ns'])==10
                val[phase]=x['avg_ts']
        partial.append(val)
    analysis['jobs'][jid]={'summary':'200/infinite等待时长实验仍运行，已完成的子项按原始JSON保留，未完成项不补造。首次200与infinite PP分别约32.48/31.63t/s属于不同节点，不可直接认定收益或失败；需要完成全部ABBA/BAAB同节点配对。新增hyper/tree普通barrier实验独立进行，不混用两组变量。','partial_values':partial}
(evidence/'analysis_updates/barrier_tree_20261020.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
next_actions={'updated_at_hkt':stamp,'phase':'plain-barrier algorithm experiment running alongside wait-time experiment','jobs':new,
              'other_active_jobs':[{'job_id':jid,'state':jobs[jid]['state'],'host':jobs[jid].get('exec_host')} for jid in ['4340520','4340521']],
              'next':'监控四个作业，不重复提交。infinite组独立比较等待时长；本组仅比较普通barrier hyper/tree，forkjoin固定hyper、blocktime200/ACTIVE固定。每个作业四轮各新固定PPL再PP10/TG10，完整后B1对A1、B2对A2，保留全部慢样本与首次状态/顺序/节点时段限制。运行时模式已用Intel程序核验生效；正式采用前按题目申报，开发自测不是正式成绩。',
              'excel':'D:/compete/Qwen38_CPU_实验日志.xlsx'}
(here/'next_actions.json').write_text(json.dumps(next_actions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
prior=here.parent/'kmp_infinite/next_actions.json'
p=json.loads(prior.read_text(encoding='utf-8'))
p['updated_at_hkt']=stamp;p['parallel_followup']=str(here/'next_actions.json')
p['next']=next_actions['next']
prior.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'new_jobs':new,'runtime_algorithms_verified':True,'existing_wait_jobs_preserved':True},ensure_ascii=False))
