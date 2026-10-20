import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from openpyxl import load_workbook

here=Path(__file__).resolve().parent
evidence=here.parent/'evidence'
r=json.loads((evidence/'job_registry.json').read_text(encoding='utf-8'))
jobs={j['job_id']:j for j in r['jobs']}
runtime=json.loads((here/'runtime_check_evidence.json').read_text(encoding='utf-8'))
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
ids=['4340520','4340521'];new=[]
analysis={'updated_at_hkt':stamp,'source':'Actual Intel runtime KMP_SETTINGS output and LSF state','jobs':{}}
for jid in ids:
    v=json.loads(runtime[jid]['runtime-validation.json'])
    assert v['200']['effective_KMP_BLOCKTIME']=='200'
    assert v['infinite']['effective_KMP_BLOCKTIME']=='2147483647'
    assert v['200']['threads']==v['infinite']['threads']==38
    job=jobs[jid];order=job['submission']['environment']['CASE_ORDER']
    new.append({'job_id':jid,'state':job['state'],'host':job.get('exec_host'),'order':order})
    analysis['jobs'][jid]={'summary':'Intel OpenMP运行时设置探测已通过：200实际为200，infinite实际为2147483647，两者38线程/ACTIVE，未静默回落。四轮'+order+'完整PPL/PP/TG执行中；未完成指标保持空，不提前认定参数有效或评分。','runtime_evidence':runtime[jid]}
(evidence/'analysis_updates/kmp_infinite_20261020.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
next_actions={'updated_at_hkt':stamp,'phase':'unprofiled 200/infinite runtime intervention running','jobs':new,
              'hypothesis':'4340376 first PP reported fork-barrier wait records, later PP none; both first/later spin share about30%. Test longer active waiting instead of assuming barrier spin explains 2x speed.',
              'next':'检查四轮每轮固定PPL与PP10/TG10，全部样本保留。A=KMP_BLOCKTIME200，B=infinite，两者ACTIVE。ABBA/BAAB各自同节点B1对A1、B2对A2，另看首次A/B与后续轮次走势，警惕节点/顺序/温度/跨段延续混杂。不得只报最快轮次。已验证infinite被实际运行时识别为2147483647。源码/二进制不改，无采样；固定PPL默认等待设置，与测速变量分开。运行时策略正式采用前按赛题申报。',
              'runtime_validation':v,'do_not_duplicate':['4340350','4340351'],
              'excel':'D:/compete/Qwen38_CPU_实验日志.xlsx'}
(here/'next_actions.json').write_text(json.dumps(next_actions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=here.parent/'vtune_wait_pair/next_actions.json'
prev=json.loads(p.read_text(encoding='utf-8'));prev['latest_followup']=str(here/'next_actions.json');prev['next']=next_actions['next'];prev['updated_at_hkt']=stamp
p.write_text(json.dumps(prev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'jobs':new,'actual_runtime_settings_verified':True},ensure_ascii=False))
