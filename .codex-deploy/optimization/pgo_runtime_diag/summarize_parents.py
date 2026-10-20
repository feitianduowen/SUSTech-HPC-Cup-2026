import json
import math
from pathlib import Path

base=Path('/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo/results')
for jid in ['4337448','4337488']:
    out=base/jid
    rows=[json.loads(x) for x in (out/'training-os.jsonl').read_text().splitlines()]
    last=rows[-5:]
    cpu=(last[-1]['cpu_seconds']-last[0]['cpu_seconds'])/(last[-1]['time']-last[0]['time'])
    summary={'failure_reason':'TRAIN_PP_UNSCORED exit124，3600秒训练限时到期。模型已重排并预留图，末尾attach_threadpool/set_n_threads=38；完整PP64 JSON仍为空，TG、合并、反馈编译及PGO PPL均未执行。末段38线程持续消耗约%.1f核CPU，未见major page faults；需定位插桩/并行运行时开销，不能仅继续加时。所有不完整dyn只作诊断，不复用为完成训练。新合成诊断4337634比较plain/broad/hot与1/38线程，并尝试VTune。' % cpu,'recent_cpu_cores':cpu,'last_os_records':last,'training_pp_json_bytes':(out/'training-pp.json').stat().st_size,'partial_profiles_diagnostic_only':[{'name':p.name,'bytes':p.stat().st_size} for p in sorted((out/'profiles').glob('*.dyn'))],'training_complete':False}
    (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
root=Path('/work/apac2602/qwen38-cpu/optimization/20261019-ppl-policy5/results/4337539')
values={}
for case in ['01_baseline','02_mkl']:
    p=root/case
    gate=json.loads((p/'perplexity_result.json').read_text())
    assert gate['status']=='PASS' and gate['tolerance_percent']==5.0
    values[case]={'ppl':gate['ppl']}
    for phase,name in [('pp','pp2048.json'),('tg','tg128_d2048.json')]:
        data=json.loads((p/name).read_text())[0]
        assert len(data['samples_ts'])==len(data['samples_ns'])==10
        values[case][phase]=data['avg_ts']
        values[case][phase+'_cv']=data['stddev_ts']/data['avg_ts']
    values[case]['development_score']=100*math.sqrt(values[case]['pp']/46.929024*values[case]['tg']/3.295524)
summary={'values':values,'interpretation':'首轮MKL同节点顺序对照已完成，两版各独立PPL及完整PP/TG十次。MKL PP高于先执行原版，但TG无改善；首轮PP差异不能直接归因于MKL，保留先后顺序及缓存限制。反序复核4337633已提交，原始样本全部保留；开发自测不是正式成绩。','reverse_job':'4337633'}
(root/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False))
