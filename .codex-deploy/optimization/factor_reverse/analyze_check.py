import json
import math
from pathlib import Path
from datetime import datetime, timezone, timedelta

here=Path(__file__).resolve().parent
evidence=here.parent/'evidence'
r=json.loads((evidence/'job_registry.json').read_text(encoding='utf-8'))
jobs={j['job_id']:j for j in r['jobs']}
audit=json.loads((here/'check_evidence.json').read_text(encoding='utf-8'))
assert audit['aa_speed_environment_identical']
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
analysis={'updated_at_hkt':stamp,'source':'LSF, fixed PPL JSON, complete benchmark JSON, SHA checks and actual runtime environments','jobs':{}}
for jid in ['4338446','4338447','4338448','4338449']:
    j=jobs[jid]
    cases={m['name'].split('_')[0].rsplit('-',1)[1]:m for m in j['measurements']}
    values={}
    for name,m in cases.items():
        p=m.get('ppl') or {}
        if p:
            assert p['status']=='PASS' and 2.63112<=p['ppl']<=2.90808
        v={'ppl':p.get('ppl'),'ppl_seconds':p.get('elapsed_seconds')}
        for phase in ['pp','tg']:
            x=m.get(phase)
            if x:
                x=x[0]
                assert len(x['samples_ts'])==len(x['samples_ns'])==10
                assert (x['n_threads'],x['n_batch'],x['n_ubatch'],x['n_gpu_layers'],x['type_k'],x['type_v'])==(38,2048,512,0,'f16','f16')
                assert (x['n_prompt'],x['n_gen'],x['n_depth'])==((2048,0,0) if phase=='pp' else (0,128,2048))
                v[phase]=x['avg_ts']
        values[name]=v
    a,b=values['baseline'],values['candidate']
    change={}
    for phase in ['pp','tg']:
        if phase in a and phase in b: change[phase]=100*(b[phase]/a[phase]-1)
    if len(change)==2: change['geomean']=100*(math.sqrt(b['pp']/a['pp']*b['tg']/a['tg'])-1)
    complete=j['state']=='DONE' and len(change)==3
    if jid=='4338449':
        summary=(f'A/A同一Intel二进制、同一配置重复两次，全部SHA校验通过，两次测速环境文件完全相同；各自PPL2.7767 PASS和PP/TG各10次。第二次相对第一次PP {change["pp"]:+.2f}%（{a["pp"]:.6f}→{b["pp"]:.6f}），TG {change["tg"]:+.2f}%。'
                 '无代码或参数优化仍出现巨大PP加速，证实该测试流程存在强顺序/运行状态混杂。尚未区分页缓存、NUMA页迁移或其他系统因素；不能把此前候选PP增益直接认定为优化收益。全部慢样本保留。')
    else:
        summary=('反序candidate→baseline同节点对照已完成。' if complete else '反序candidate→baseline对照仍运行，baseline TG尚未完成，禁止计算完整相对分数。')
        summary+=f'两版本固定PPL通过±5%；已完成PP各10次，候选相对baseline PP {change["pp"]:+.2f}%。'
        if 'tg' in change: summary+=f'TG {change["tg"]:+.2f}%。'
        summary+='PP相对方向与正序反转；A/A同配置第二次运行也出现大幅PP加速。结合强顺序/运行状态混杂，目前没有证据证明该变量提供稳定PP收益，不提升生产版本。开发自测非正式成绩。'
    analysis['jobs'][jid]={'summary':summary,'state':j['state'],'values':values,'change_percent':change,'complete':complete,'configuration_evidence':audit[jid]}
(evidence/'analysis_updates/factor_reverse_20261019.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(here/'check_analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=here/'next_actions.json'
next_actions=json.loads(p.read_text(encoding='utf-8'))
next_actions['updated_at_hkt']=stamp
for job in next_actions['jobs']: job['state']=jobs[job['job_id']]['state']
next_actions['phase']='three completed; affinity baseline TG pending' if jobs['4338446']['state']=='RUN' else 'reverse and AA completed'
next_actions['next']='优先收取4338446剩余TG结果。A/A已证实相同配置第二次PP约+76.6%，此前单次前后对照不足以确认收益。后续先独立诊断顺序/页缓存/NUMA/运行状态影响，必要时做平衡重复；正式固定评测参数不改、不删慢样本。当前不提升任何候选为生产版本；不重复提交已有作业。'
p.write_text(json.dumps(next_actions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({jid:{'state':a['state'],'change_percent':a['change_percent']} for jid,a in analysis['jobs'].items()},ensure_ascii=False))
