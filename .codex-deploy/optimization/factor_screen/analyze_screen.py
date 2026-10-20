import json
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path

here=Path(__file__).resolve().parent
evidence=here.parent/'evidence'
r=json.loads((evidence/'job_registry.json').read_text(encoding='utf-8'))
jobs={j['job_id']:j for j in r['jobs']}
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
analysis={'updated_at_hkt':stamp,'source':'Completed LSF, original fixed PPL and all ten PP/TG samples, NaN PPL raw log','jobs':{}}
for jid in [str(x) for x in range(4338277,4338282)]:
    job=jobs[jid]
    cases={m['name'].split('_')[0].rsplit('-',1)[1]:m for m in job['measurements']}
    values={}
    for name,m in cases.items():
        p=m.get('ppl')
        values[name]={'ppl':p.get('ppl') if p else None,'ppl_status':p.get('status') if p else None}
        for phase in ['pp','tg']:
            obj=m.get(phase)
            if obj:
                x=obj[0]
                assert len(x['samples_ts'])==len(x['samples_ns'])==10
                values[name][phase]=x['avg_ts']
                values[name][phase+'_cv_percent']=100*x['stddev_ts']/x['avg_ts']
    item={'values':values}
    if jid=='4338281':
        assert job['state']=='EXIT' and values['candidate']['ppl'] is None
        item['ppl_observations']={cases['candidate']['name']:'数值无效（NaN；已运行）'}
        item['summary']='全局-fp-model fast=1数值失败：PPL进程74秒退出码0，但两个chunk均输出-nan，并报告Unexpected negative standard deviation of log(prob)，无有效Final estimate。固定PPL验证正确阻止测速。此结果不是±5%范围内通过，也不是未运行；candidate PP/TG/Score均未执行。两版Intel构建、量化测试、单变量缓存核验通过，但不代表模型数值有效。保留失败构建和日志，淘汰此全局fast=1配置，不盲目重提。baseline完整PPL/PP10/TG10保留。'
    else:
        assert job['state']=='DONE'
        a,b=values['baseline'],values['candidate']
        assert a['ppl_status']==b['ppl_status']=='PASS'
        pp=b['pp']/a['pp']-1; tg=b['tg']/a['tg']-1
        geo=math.sqrt((1+pp)*(1+tg))-1
        item['changes_percent']={'pp':100*pp,'tg':100*tg,'geomean':100*geo}
        item['summary']=(f'完整同节点baseline→candidate对照；两版独立固定PPL按5%通过（{a["ppl"]}/{b["ppl"]}），PP/TG各10次。'
                         f'候选相对本作业baseline：PP {pp:+.2%}，TG {tg:+.2%}，几何均值 {geo:+.2%}。'
                         '四组后运行候选PP均显著高于先运行baseline，且候选前的默认PPL也明显更快，存在强烈顺序/缓存/时段混杂；不能将PP大幅提升直接归因于变量。'
                         +('等待时长0的TG约下降36%，暂不继续；保留全部慢样本。' if jid=='4338277' else '下一轮复用已核验产物做candidate→baseline反序，并另设相同配置A/A对照。')+'开发自测非正式成绩。')
    analysis['jobs'][jid]=item
(evidence/'analysis_updates/factor_screen_20261019.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(here/'completed_analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v.get('changes_percent','NaN numeric failure') for k,v in analysis['jobs'].items()},ensure_ascii=False))
