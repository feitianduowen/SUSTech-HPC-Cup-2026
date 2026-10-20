import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

here=Path(__file__).resolve().parent
evidence=here.parent/'evidence'
progress=json.loads((here/'runtime_progress_analysis.json').read_text(encoding='utf-8'))
registry=json.loads((evidence/'job_registry.json').read_text(encoding='utf-8'))
jobs={j['job_id']:j for j in registry['jobs']}
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
out={'updated_at_hkt':stamp,'source':'All four completed jobs, fixed PPL, full ten samples, effective runtime settings and SHA checks','jobs':{}}
for jid,p in progress['jobs'].items():
    assert p['state']=='DONE' and p['completed_cases']==4
    assert all(pair['complete'] for pair in p['pairs'])
    second=p['pairs'][1]['change_percent']
    a2,b2=p['values']['A2'],p['values']['B2']
    if jid in ['4340520','4340521']:
        text=(f'等待时长200/infinite四轮完成：第二对PP {second["pp"]:+.2f}%，TG {second["tg"]:+.2f}%，几何均值 {second["geomean"]:+.2f}%。'
              '两个顺序的第二对PP约+1%，但首对方向反转且反序TG baseline含明显慢样本，未证明一致、稳定的综合收益；infinite首次PP仍约31.63，未消除先慢现象。保留所有样本，暂不采用infinite，不把首次大幅差异归因于参数。')
    else:
        text=(f'普通barrier hyper/tree四轮完成：第二对PP {second["pp"]:+.2f}%，TG {second["tg"]:+.2f}%，几何均值 {second["geomean"]:+.2f}%。'
              '两个顺序的第二对PP分别约-0.51%/+0.83%，方向不一致；TG约+0.54%/+0.44%，幅度小，尚不足以证明稳定的端到端收益。tree首次PP约30.63，仍有先慢现象。保留所有样本，暂不采用tree。')
    text+='四轮独立PPL均2.7767，按±5%通过；每轮PP/TG各完整10次，共80条。无采样，按题目固定参数执行，二进制SHA和实际环境核验通过。两种顺序仍分属不同节点/时段，不能把“第二对”挑作唯一成绩；全部轮次与配对均已记录，开发自测非正式成绩。'
    cv={}
    for m in jobs[jid]['measurements']:
        name=m['name'].rsplit('-',1)[1].split('_')[0]
        cv[name]={phase:100*m[phase][0]['stddev_ts']/m[phase][0]['avg_ts'] for phase in ['pp','tg']}
    out['jobs'][jid]={'summary':text,'all_pairs':p['pairs'],'all_values':p['values'],'cv_percent':cv,'samples_retained':80,'verdict':'未证明稳定综合收益，暂不采用'}
(evidence/'analysis_updates/runtime_verdict_20261020.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(here/'completed_runtime_verdict.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
next_text='四个作业均已完成，不重提。infinite未消除首次慢速，第二对PP约+1%而TG受低速样本干扰；tree第二对PP方向不一致、TG差异约0.5%，两项均未证明稳定综合收益，暂不采用。保留全部16轮PPL、320测速样本及全部对照。后续以源码热点优化为主，候选需固定流程和配对重复评估；停止仅基于首次/后续速度差推进运行时猜测。'
for directory in ['barrier_tree','kmp_infinite']:
    path=here.parent/directory/'next_actions.json'
    n=json.loads(path.read_text(encoding='utf-8'))
    n.update(updated_at_hkt=stamp,phase='all four complete; runtime changes not adopted',next=next_text,completed_verdict=str(here/'completed_runtime_verdict.json'))
    path.write_text(json.dumps(n,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({jid:p['pairs'][1]['change_percent'] for jid,p in progress['jobs'].items()}))
