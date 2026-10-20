import json
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
from openpyxl import load_workbook

here=Path(__file__).resolve().parent
evidence=here.parent/'evidence'
data=json.loads((here/'completed_summary.json').read_text(encoding='utf-8'))
registry=json.loads((evidence/'job_registry.json').read_text(encoding='utf-8'))
jobs={j['job_id']:j for j in registry['jobs']}
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
analysis={'updated_at_hkt':stamp,'source':'All original benchmark JSON, fresh fixed PPL, SHA checks, thread and NUMA snapshots; raw archive preserved','jobs':{}}
for jid,job in data.items():
    assert jobs[jid]['state']=='DONE'
    assert job['sha_all_ok'] and len(job['cases'])==12
    p=job['ppl']
    assert p['status']=='PASS' and p['ppl']==2.7767 and p['elapsed_seconds']<=590
    assert sum(c['meta']['workload']=='pp' for c in job['cases'])==8
    assert sum(c['meta']['workload']=='tg' for c in job['cases'])==4
    for c in job['cases']:
        assert len(c['samples_ts'])==10
    blocks=job['blocks']
    ratios='；'.join('第%d段%s：PP %.6f→%.6f（%+.2f%%）'%(b['block'],b['order'],b['anchor_pp'],b['probe_pp'],b['probe_change_percent']) for b in blocks)
    cold=job['cases'][0]
    cpu=cold['thread_deltas_over_observed_lifetimes']
    wait_share=100*cpu['runnable_wait_ns']/(cpu['runtime_ns']+cpu['runnable_wait_ns'])
    summary=(f'平衡顺序{jobs[jid]["submission"]["environment"]["CROSSOVER"]}完成；PPL2.7767 PASS，12个诊断命令各10次，所有SHA通过。'+ratios+'。'
             '首次状态转换幅度大，后续同节点段中A与B均接近54t/s，TG穿插未表现一致的稳定提升；ABBA/BAAB仍有跨段状态延续，不能将首次差异直接当作TG因果效应。'
             f'首次PP采样窗口内跨线程自愿切换约{cpu["voluntary_context_switches"]:,}次，runnable排队时间占CPU运行+排队统计约{wait_share:.3f}%；看到互斥/条件等待符号快照，后续快速PP此类快照减少。'
             '采样时38线程主要为两NUMA节点各19线程，未见线程数超过38的采样快照；全部诊断进程major faults=0且采样read_bytes=0。同步/阻塞及启动状态是后续线索，尚未识别到具体代码或根因。采样有开销、覆盖离散时间且schedstat不包括全部阻塞时间；仅诊断不计算Score，不删除任何慢样本。')
    analysis['jobs'][jid]={'summary':summary,'blocks':blocks,
                           'evidence_files':[str(here/'completed_summary.json'),str(here/'completed-telemetry.tar.gz')],
                           'thread_telemetry_scope':'per-TID observed lifetime deltas, 30s snapshots, not whole-run blocking-time attribution',
                           'ppl':p['ppl'],'raw_samples':120}
(evidence/'analysis_updates/order_crossover_20261020.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(here/'completed_analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
next_path=here/'next_actions.json'
next_actions=json.loads(next_path.read_text(encoding='utf-8'))
next_actions['updated_at_hkt']=stamp
next_actions['phase']='ABBA and BAAB complete; no consistent steady-state TG benefit'
for job in next_actions['jobs']: job['state']='DONE'
next_actions['next']='原作业已完成，不重复重提。首次慢PP出现数百万自愿上下文切换和互斥/条件等待符号，后续PP稳定约54t/s，主要亲和性19+19，major faults和采样read_bytes均0。后续若继续诊断，应限定最初慢PP及TG后快PP的同节点VTune线程/同步窗口，区分阻塞等待、屏障与启动状态；需要保留完整10样本、固定PPL及参数，带采样结果不计分。后续源码候选必须以固定流程配对重复评估，不能把状态转换当作收益。'
next_path.write_text(json.dumps(next_actions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'completed':list(data),'block_changes':{jid:[round(b['probe_change_percent'],3) for b in j['blocks']] for jid,j in data.items()}}))
