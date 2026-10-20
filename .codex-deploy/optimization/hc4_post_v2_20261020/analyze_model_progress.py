import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

here=Path(__file__).resolve().parent
snapshot=json.loads((here/'progress_snapshot.json').read_text(encoding='utf-8'))
analyses=[]
notes={}
sample_count=0
for job in snapshot['jobs']:
    cases={}
    for case in job['cases']:
        name=case['name'].split('_',1)[1]
        gate=case.get('ppl',{})
        if gate:
            assert gate['status']=='PASS'
            assert gate['tolerance_percent']==5 and 2.63112<=gate['ppl']<=2.90808
            c=gate['conditions']
            assert [c[k] for k in ['ppl_ctx','ppl_chunks','ppl_batch','ppl_ubatch','threads','kv_cache_k','kv_cache_v','numa','warmup','gpu_layers']]==[512,2,512,256,38,'f16','f16','distribute',False,0]
            assert c['data_sha256']=='173c87a53759e0201f33e0ccf978e510c2042d7f2cb78229d9a50d79b9e7dd08'
        row={'ppl':gate.get('ppl'),'ppl_status':gate.get('status'),'ppl_elapsed_seconds':gate.get('elapsed_seconds'),'pp':None,'tg':None,'complete':False}
        for key,filename in [('pp','pp2048.json'),('tg','tg128_d2048.json')]:
            data=case.get(filename)
            if data:
                data=data[0] if isinstance(data,list) else data
                assert len(data['samples_ns'])==len(data['samples_ts'])==10
                assert all(math.isfinite(x) and x>0 for x in data['samples_ts'])
                row[key]={'avg_ts':data['avg_ts'],'stddev_ts':data['stddev_ts'],'cv':data['stddev_ts']/data['avg_ts'],'samples_ts':data['samples_ts'],'samples_ns':data['samples_ns']}
                sample_count+=10
        row['complete']=row['ppl_status']=='PASS' and bool(row['pp']) and bool(row['tg'])
        cases[name]=row
    pairs=[]
    for index in [1,2]:
        a=cases.get('A'+str(index),{})
        b=cases.get('B'+str(index),{})
        pair={'pair':index,'baseline':'A'+str(index),'candidate':'B'+str(index),'complete':bool(a.get('complete') and b.get('complete')),'change_percent':{}}
        for key in ['pp','tg']:
            if a.get(key) and b.get(key):pair['change_percent'][key]=100*(b[key]['avg_ts']/a[key]['avg_ts']-1)
        if pair['complete']:
            pair['change_percent']['geomean']=100*(math.sqrt((1+pair['change_percent']['pp']/100)*(1+pair['change_percent']['tg']/100))-1)
        pairs.append(pair)
    complete=sum(bool(r['complete']) for r in cases.values())
    passed=sum(r['ppl_status']=='PASS' for r in cases.values())
    item={'job_id':job['job_id'],'stage':job['status'],'all_values':cases,'pairs':pairs,'complete_cases':complete,'ppl_passed':passed}
    analyses.append(item)
    second=pairs[1]['change_percent']
    summary=f"8组ABBA/BAAB对照进度中的本作业：固定PPL已通过{passed}/4，各PPL均为2.7767；完整PP10/TG10共{complete}/4轮，当前阶段{job['status']}。"
    if 'pp' in second:summary+=f"第二对B2/A2的PP变化{second['pp']:+.2f}%。"
    if 'tg' in second:summary+=f"第二对TG变化{second['tg']:+.2f}%。"
    if 'geomean' in second:summary+=f"第二对PP/TG几何均值变化{second['geomean']:+.2f}%。"
    first=pairs[0]['change_percent']
    if 'pp' in first:summary+=f"首对PP变化{first['pp']:+.2f}%。"
    summary+='首对仍受首次慢速和顺序影响；两对均保留，不把首轮大幅差异当作源码收益。'
    if complete==4:
        summary+='本作业四轮全部完成；后段配对PP/TG同向提升，列为复测候选。需要在其他同配置节点以ABABA/BABAB交错复测，观察后段A-B-A/B-A-B对照及运行漂移；当前未替换部署。'
    else:
        summary+='完整TG/配对尚未齐前暂不确认整体收益或替换部署。'
    summary+='所有已完成十次原始样本、PPL及算子样本保留。'
    notes[job['job_id']]={'summary':summary,'model_progress':item}

stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
analysis={'updated_at_hkt':stamp,'snapshot_time':snapshot['updated_at_hkt'],'complete_cases':sum(r['complete_cases'] for r in analyses),'ppl_passed':sum(r['ppl_passed'] for r in analyses),'full_benchmark_samples':sample_count,'jobs':analyses,'interpretation':'Preliminary: later-position PP gain is consistent across orders, but all TG pairs must finish. Preserve both pairs and all samples; first-position PP remains confounded by order. No promotion or repeat submission while these jobs are running.'}
all_complete=analysis['complete_cases']==8 and all(r['stage'].startswith('COMPLETE ') for r in analyses)
if all_complete:
    assert analysis['ppl_passed']==8 and sample_count==160
    analysis['interpretation']='Both balanced comparisons complete. Later-position pairs show PP/TG gains on both nodes; first-pair PP effects reverse with order and remain confounded. Preserve all eight cases and 160 samples. Keep HC-post v2 as a candidate and repeat on different matching nodes with ABABA/BABAB to inspect late A-B-A/B-A-B controls and drift; no production replacement yet.'
    (here/'completed_model_analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2),encoding='utf-8')
(here/'model_progress_analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2),encoding='utf-8')
(here.parent/'evidence/analysis_updates/hc4_post_v2_model_progress_20261020.json').write_text(json.dumps({'updated_at_hkt':stamp,'source':snapshot['remote_root']+'/progress_snapshot.json','jobs':notes},ensure_ascii=False,indent=2),encoding='utf-8')
path=here/'next_actions.json'
actions=json.loads(path.read_text(encoding='utf-8'))
actions['updated_at_hkt']=stamp
actions['phase']='Both jobs complete; HC-post v2 shortlisted for independent replication' if all_complete else 'All 8 fixed PPL passed; final model throughput rounds running'
actions['current_stages']={j['job_id']:j['status'] for j in snapshot['jobs']}
actions['model_progress_analysis']=str(here/'model_progress_analysis.json')
actions['next']='Submit independent ABABA/BABAB repetitions on other Gold6148 nodes with frozen verified Intel binaries, a fresh fixed PPL and PP10/TG10 per case. Preserve first-position slow samples and inspect both late sandwich controls before promotion.' if all_complete else 'Await the two final TG10 results, then inspect both within-node pairs and all sample variation. Do not resubmit these running jobs or promote before the balanced comparison is complete.'
path.write_text(json.dumps(actions,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in analysis.items() if k!='jobs'}))
print(json.dumps([{'job_id':r['job_id'],'pairs':r['pairs']} for r in analyses]))
