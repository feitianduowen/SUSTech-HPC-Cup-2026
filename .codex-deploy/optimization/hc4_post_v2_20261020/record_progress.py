import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

here=Path(__file__).resolve().parent
snapshot=json.loads((here/'progress_snapshot.json').read_text(encoding='utf-8'))
notes={}
for job in snapshot['jobs']:
    check=job.get('library_correctness')
    text='当前阶段：'+job['status']+'。'
    if check:
        text+='实际GGML图跨库逐bit差分'+check['status']+'：'+str(check['cases'])+'组/'+str(check['values'])+'个F32值，1/3/38线程各3重复，bit差异'+str(check['bit_mismatches'])+'；包含连续、填充、转置、hc1/2/4/8以及comb缺省/单位/稠密。'
    micro=job.get('summary',{}).get('hc_microbench',[])
    if micro:
        text+='算子微基准完成10轮AB/BA，形状与中位加速比分别为：'+'；'.join(str(r['shape'])+' '+format(r['speedup'],'.3f')+'x' for r in micro)+'。仅算子合成图，包含线程池开销，不能当作整模收益。'
    text+='每case独立PPL后继续PP10/TG10；目前尚无完整模型性能结论，不计算或挑选不完整样本分数。v1两个差分失败保留，未放宽逐bit或PPL门槛。'
    notes[job['job_id']]={'summary':text,'snapshot':job}
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
path=here.parent/'evidence/analysis_updates/hc4_post_v2_progress_20261020.json'
path.write_text(json.dumps({'updated_at_hkt':stamp,'source':snapshot['remote_root']+'/progress_snapshot.json','jobs':notes},ensure_ascii=False,indent=2),encoding='utf-8')
previous=here/'next_actions.json'
actions=json.loads(previous.read_text(encoding='utf-8'))
actions['updated_at_hkt']=stamp
actions['progress_snapshot']=str(here/'progress_snapshot.json')
actions['current_stages']={j['job_id']:j['status'] for j in snapshot['jobs']}
actions['phase']='v2 verification and balanced model comparison in progress'
actions['next']='Continue already running ABBA/BAAB jobs; check every fresh fixed PPL, all PP/TG samples and both pairs on both nodes. Do not submit duplicates, promote, or infer a model improvement from operator results.'
previous.write_text(json.dumps(actions,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'jobs':list(notes),'stages':actions['current_stages'],'recorded_at_hkt':stamp}))
