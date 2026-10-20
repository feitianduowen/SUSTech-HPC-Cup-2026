import json
from pathlib import Path

root=Path('/work/apac2602/qwen38-cpu/optimization')
out=root/'20261019-pgo-hot-serial/results/4337670'
manifest=json.loads((out/'manifest.json').read_text())
pp=json.loads((out/'training-pp.json').read_text())[0]
tg=json.loads((out/'training-tg.json').read_text())[0]
for row in [pp,tg]:
    assert row['n_threads']==1 and len(row['samples_ts'])==1 and row['samples_ns'][0]>0
assert manifest['builds']['pgo']['ppl']['status']=='PASS'
remarks=(out/'pgo-build/profile-remarks.txt').read_text()
summary={
 'training_complete':True,'training_pp_seconds':pp['avg_ns']/1e9,'training_tg_seconds':tg['avg_ns']/1e9,
 'training_unscored':True,'training_threads':1,'candidate_ppl':manifest['builds']['pgo']['ppl']['ppl'],
 'candidate_ppl_elapsed_seconds':manifest['builds']['pgo']['ppl']['elapsed_seconds'],
 'profile_count':manifest['profile_count'],'dpi_sha256':manifest['dpi_sha256'],
 'feedback_static_profile_remarks':len(remarks.splitlines()),
 'interpretation':'单线程热点默认计数训练两阶段正常完成，完整JSON通过、仅本作业新计数合并；gen/use三源范围校验通过，反馈构建、量化测试、四工具链接、独立38线程固定PPL全部通过(PPL2.7767,232秒)。部分未覆盖函数报告No .dpi information并回退静态profile，保留全部日志；尚无完整模型PP/TG性能结论。control复用4337216 SHA核验构建及旧PPL，本作业未重新跑control PPL；下一轮同节点正反顺序各自新PPL及完整PP/TG十次。'
}
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))

out=root/'20261019-ppl-policy5/results/4337633'
values={}
for name in ['01_baseline','02_mkl']:
    case=out/name
    ppl=json.loads((case/'perplexity_result.json').read_text())
    pp=json.loads((case/'pp2048.json').read_text())[0]
    tg=json.loads((case/'tg128_d2048.json').read_text())[0]
    assert ppl['status']=='PASS' and 2.63112<=ppl['ppl']<=2.90808
    assert len(pp['samples_ts'])==len(tg['samples_ts'])==10
    values[name]={'ppl':ppl['ppl'],'pp':pp['avg_ts'],'tg':tg['avg_ts'],'pp_cv_percent':100*pp['stddev_ts']/pp['avg_ts'],'tg_cv_percent':100*tg['stddev_ts']/tg['avg_ts']}
b,m=values['01_baseline'],values['02_mkl']
summary={'values':values,'pp_relative_percent':100*(m['pp']/b['pp']-1),'tg_relative_percent':100*(m['tg']/b['tg']-1),'interpretation':'MKL反序同节点对照完整完成，mkl先PPL/PP10/TG10后baseline，各自新PPL通过当前±5%。MKL PP约-19.77%、TG约+10.87%；首轮4337539 PP约+47.58%、TG约-0.35%，两个方向均不稳定。先后顺序/缓存及跨节点限制保留，不直接归因或提升生产版本。完整10次样本和慢样本保留；开发自测非正式成绩。'}
(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False))
