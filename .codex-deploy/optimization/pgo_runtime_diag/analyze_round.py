import csv
import json
from pathlib import Path

root=Path('/work/apac2602/qwen38-cpu/optimization')
for parent,jid,default in [('20261019-pgo-runtime-diag','4337634',False),('20261019-pgo-default-diag','4337642',True)]:
    out=root/parent/'results'/jid
    file=out/'summary.json'
    data=json.loads(file.read_text())
    backup=out/'summary-before-analysis.json'
    if not backup.exists():backup.write_text(file.read_text())
    cases={r['name']:r for r in data['runtime_probe_cases']}
    ratios={r:cases[r]['result']['seconds']/cases['plain_t'+str(cases[r]['threads'])]['result']['seconds'] for r in cases if r.split('_t')[0]!='plain'}
    data['relative_to_plain_compute_time']=ratios
    rows=list(csv.DictReader((out/'hotspots.csv').open()))
    total=sum(float(r['CPU Time']) for r in rows)
    checkpoints=[r for r in rows if 'Checkpoint_All' in r['Function']]
    data['vtune_checkpoint_seconds']=sum(float(r['CPU Time']) for r in checkpoints)
    data['vtune_reported_function_cpu_seconds']=total
    if default:
        conclusion='默认计数模式单线程热点版相对plain约4.67倍耗时，明显低于threadsafe轮的约256倍，但为跨节点诊断比较；38线程默认计数仍有开销且可能存在计数竞争，诊断计数禁止用于反馈。下一轮只用单线程收集新模型训练计数，PPL和测速继续38线程。'
    else:
        conclusion='VTune全量插桩38线程372.022秒CPU中约287.694秒(77.33%)在Intel线程安全PGO checkpoint，另约74.064秒在OpenMP barrier。合成正确性全部PASS；该证据证明本探针的插桩运行时开销，不直接证明先前模型训练超时的唯一根因。热点文件范围缩减仍很慢，不能仅延长训练超时。'
    data['interpretation']=data['interpretation'].split('\nAnalysis:')[0]+'\nAnalysis: '+conclusion
    file.write_text(json.dumps(data,ensure_ascii=False,indent=2))

q8=root/'20261019-q8-avx2-v2/results'
for jid,variant in [('4337219','schedule4'),('4337220','schedule4_prefetch16')]:
    out=q8/jid
    measurements={}
    for name in ['01_baseline','02_candidate']:
        case=out/name
        p=json.loads((case/'perplexity_result.json').read_text())
        pp=json.loads((case/'pp.json').read_text())[0]
        tg=json.loads((case/'tg.json').read_text())[0]
        assert 2.63112<=p['ppl']<=2.90808
        assert len(pp['samples_ts'])==len(tg['samples_ts'])==10
        measurements[name]={'ppl':p['ppl'],'pp':pp['avg_ts'],'tg':tg['avg_ts'],'pp_cv_percent':100*pp['stddev_ts']/pp['avg_ts'],'tg_cv_percent':100*tg['stddev_ts']/tg['avg_ts']}
    b,c=measurements['01_baseline'],measurements['02_candidate']
    data={'variant':variant,'values':measurements,'pp_relative_percent':100*(c['pp']/b['pp']-1),'tg_relative_percent':100*(c['tg']/b['tg']-1),'interpretation':'反序复核完成，顺序candidatePP→baselinePP→baselineTG→candidateTG，各10次样本完整保留；PPL按SHA核验复用各版本既有固定配置结果，未重跑。候选先PP时约21.6，后执行原版更高，首轮巨大PP改善不稳定、存在先后顺序/缓存影响；TG两候选方向不一致，未建立稳定完整模型收益，暂不替换生产。跨节点首轮与反序轮不可直接作因果比较，未删除慢样本。'}
    (out/'summary.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    print(json.dumps({'job_id':jid,'pp_relative_percent':data['pp_relative_percent'],'tg_relative_percent':data['tg_relative_percent']}))
