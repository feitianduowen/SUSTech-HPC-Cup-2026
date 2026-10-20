import json
from datetime import datetime,timedelta,timezone
from pathlib import Path

root=Path(__file__).resolve().parent
registry=json.loads((root.parent/'evidence/job_registry.json').read_text(encoding='utf-8'))
ids=['4341175','4341176']
jobs=[j for j in registry['jobs'] if j['job_id'] in ids]
assert len(jobs)==2
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
data={'updated_at_hkt':stamp,'phase':'Independent five-case HC-post replication running' if all(j['state']=='RUN' for j in jobs) else 'Independent five-case HC-post replication submitted',
      'jobs':jobs,'orders':{'4341175':'ABABA','4341176':'BABAB'},
      'late_brackets':{'4341175':['A2','B2','A3'],'4341176':['B2','A2','B3']},
      'frozen_builds':str(root/'frozen_builds.json'),
      'prior_completed_analysis':str(root.parent/'hc4_post_v2_20261020/completed_model_analysis.json'),
      'prior_result':'8 fixed PPL=2.7767 PASS, 160 raw samples. Later pairs PP +5.595/+5.432%, TG +1.784/+0.504%, geometric mean +3.672/+2.939%. First-pair PP +60.448/-32.738% is order-confounded; all samples retained.',
      'next':'Check frozen hash/ldd and hardware gates; if failed diagnose and log before retry. If passed, let all five fresh fixed PPL and PP10/TG10 cases finish. Analyze every pair and both sides of late A-B-A/B-A-B brackets; do not select only fast samples, duplicate running jobs, or promote before results.',
      'excel':'D:/compete/Qwen38_CPU_实验日志.xlsx'}
initial=root/'initial_progress.json'
if initial.is_file():
    progress=json.loads(initial.read_text(encoding='utf-8'))
    data['initial_progress']=progress
    notes={j['job_id']:{'summary':'启动核验（'+progress['at_hkt']+'）：冻结两构建共48项eval二进制/库SHA、候选源码SHA及ldd依赖均PASS，首轮前重复核验PASS；当时阶段为'+j['phase']+'。节点Gold6148、40物理核/40slots检查通过；沿用先前Intel构建及972组算子差分证据，各轮PPL和完整PP/TG仍独立重新执行，尚未形成新复测结论。','initial_evidence':j} for j in progress['jobs']}
    (root.parent/'evidence/analysis_updates/hc4_replicate_initial_20261020.json').write_text(json.dumps({'updated_at_hkt':stamp,'source':'/work/apac2602/qwen38-cpu/optimization/20261020-hc4-replicate/initial_progress.json','jobs':notes},ensure_ascii=False,indent=2),encoding='utf-8')
(root/'next_actions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
for previous in [root.parent/'hc4_post_v2_20261020/next_actions.json',root.parent/'barrier_tree/next_actions.json']:
    old=json.loads(previous.read_text(encoding='utf-8'))
    old['latest_followup']={'updated_at_hkt':stamp,'path':str(root/'next_actions.json'),'jobs':ids,'purpose':'Independent five-case ABABA/BABAB HC-post v2 confirmation on other matching nodes; frozen same Intel binaries and fresh fixed PPL per case'}
    previous.write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'jobs':ids,'state':[(j['job_id'],j['state']) for j in jobs],'registry_jobs':len(registry['jobs'])}))
