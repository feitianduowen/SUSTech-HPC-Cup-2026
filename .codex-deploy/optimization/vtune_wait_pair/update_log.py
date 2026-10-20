import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from openpyxl import load_workbook

here=Path(__file__).resolve().parent
evidence=here.parent/'evidence'
r=json.loads((evidence/'job_registry.json').read_text(encoding='utf-8'))
jobs={j['job_id']:j for j in r['jobs']}
quick=json.loads((here/'quick_diagnostics.json').read_text(encoding='utf-8'))
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
ids=['4340364','4340365','4340376']
analysis={'updated_at_hkt':stamp,'source':'Actual VTune probe stderr and summary, LSF state, pipeline stage','jobs':{}}
assert 'sampling-interval' in quick['4340364']['probe.log'] and jobs['4340364']['state']=='EXIT'
for jid in ids:
    actual=quick[jid]
    if jid=='4340364':
        summary='PROBE参数兼容失败：VTune threading软件模式拒绝sampling-interval，报告incorrect apply_state knob，exit1。未执行固定PPL或模型PP/TG，无性能结果。保留失败，已修复为软件模式默认采样/栈设置后重提4340376。'
    else:
        assert 'probe-summary.txt' in actual
        summary=('VTune硬件热点探测与summary导出通过。' if jid=='4340365' else '修复4340364参数兼容问题，使用threading sampling-and-waits=sw默认设置；软件线程分析探测及summary导出通过。')
        summary+='当前阶段：'+actual.get('job.status','待核对').strip()+'。模型PPL/首次PP/后续PP与60秒ROI结果须逐项核实，工具探测通过不代表PPL通过或完整分析完成。带采样诊断不计分。'
    analysis['jobs'][jid]={'summary':summary,'probe_evidence':actual}
(evidence/'analysis_updates/vtune_wait_pair_20261020.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
new=[{'job_id':jid,'state':jobs[jid]['state'],'host':jobs[jid].get('exec_host'),'mode':jobs[jid]['submission']['environment']['PROFILE_MODE']} for jid in ids]
data={'updated_at_hkt':stamp,'phase':'software retry and hardware paired profiling running','jobs':new,
      'next':'先检查PPL、case采样进度与roi.json；software4340376与hardware4340365使用相同流程，失败4340364保留。首次PP与后续PP必须各完整10样本，TG也需10样本；同作业一次新固定PPL。ROI以prompt run1/10为起点resume，60秒后pause，核验两个控制返回码、实际时间及是否数据上限截断。读取summary/hotspots/callstacks/top-down和report-status，按target.pid/process分组排除包装Python等待。软件插桩和硬件采样有开销，模式跨节点，不直接比较吞吐为优化收益。保留原始vtune结果和所有样本，不计Score。',
      'expected_case_directories':['01_first_pp','02_intervening_tg','03_later_pp'],
      'ppl_policy':'fixed requirements, Intel compiler, ±5% inclusive [2.63112,2.90808]',
      'do_not_duplicate':['4340350','4340351'],
      'excel':'D:/compete/Qwen38_CPU_实验日志.xlsx'}
(here/'next_actions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
prior=here.parent/'order_crossover/next_actions.json'
p=json.loads(prior.read_text(encoding='utf-8'))
p['updated_at_hkt']=stamp;p['latest_followup']=str(here/'next_actions.json');p['next']=data['next']
prior.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'jobs':new,'probe_modes_verified':['threading default SW','hardware hotspots']},ensure_ascii=False))
