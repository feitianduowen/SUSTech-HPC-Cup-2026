import json
from pathlib import Path

here=Path(__file__).resolve().parent
rep=here.parent/'hc4_replicate_20261020'
prior=here.parent/'vtune_wait_pair'
remote='/work/apac2602/qwen38-cpu/optimization/20261020-hc4-profile'
for name in ['ppl_gate.lsf','frozen_builds.json','verify_frozen.py']:
    (here/name).write_text((rep/name).read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
for name in ['target_exec.py','observed_run.py','probe.py']:
    (here/name).write_text((prior/name).read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
monitor=(prior/'roi_monitor.py').read_text(encoding='utf-8')
monitor=monitor.replace("state={'requested_window_seconds':seconds,'marker':'prompt run 1/10','status':'WAITING_FOR_MARKER'}", "workload=sys.argv[4] if len(sys.argv)>4 else 'pp'\nassert workload in ['pp','tg']\nmarker=('prompt' if workload=='pp' else 'generation')+' run 1/10'\nstate={'requested_window_seconds':seconds,'marker':marker,'workload':workload,'status':'WAITING_FOR_MARKER'}")
monitor=monitor.replace("if 'prompt run 1/10' not in line:","if marker not in line:")
(here/'roi_monitor.py').write_text(monitor,encoding='utf-8',newline='\n')
for mode,order in [('hotspots','ABBA'),('threading','BAAB')]:
    prefix='profile-hc4-'+mode
    spec={
        'script':remote+'/profile.lsf','kind':'HC-post最优候选VTune对照诊断（不计分）',
        'purpose':'对当前最优候选HC-post v2及Intel原版做'+('硬件热点/调用栈' if mode=='hotspots' else '软件线程/等待')+'同节点'+order+'对照，覆盖PP/TG；核对HC-post热点是否消退、量化GEMM/dot及OpenMP同步瓶颈是否迁移。',
        'config':'Intel Classic2021.9 O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model，OpenMP/tinyBLAS ON，BLAS/GPU OFF；Gold6148双路40物理核/40slots，t38 close/cores。A原版，B冻结4340916 HC-post v2构建；eval二进制/动态库及源码SHA/ldd核验。先2.5秒非模型工具探测，再'+order+'四case各独立固定PPL t/tb38 c512 chunks2 b512ub256 f16KV ngl0 NUMA distribute no-warmup 590s ±5%。每case PP2048和TG128d2048各r10，b2048ub512 KVf16 ngl0 NUMA distribute --progress；每workload VTune '+('hotspots HW 10ms栈采样2048bytes' if mode=='hotspots' else 'threading sampling-and-waits=sw，使用已验证默认SW配置')+'。start-paused，正式prompt/generation run1/10出现后resume，约60秒后pause并继续完成十次；每结果数据上限2048MB，每workload3600s保护。每30秒读取目标PID/线程/NUMA状态。导出summary、function、thread、process/function、callstacks、top-down，原始结果留存。',
        'baseline':'同作业同节点A1/A2原版Intel；B1/A1、B2/A2均保留。不同采集模式分属节点，CPU/等待百分比和带采样吞吐不作跨模式成绩比较',
        'environment':{'PROFILE_MODE':mode,'PAIR_ORDER':order},
        'lsf_args':['-J','qwen38_hc4_'+mode],
        'case_prefix':prefix,'comparison_scope':'same-node',
        'measurement_baselines':{prefix+'-'+n+'_{job_id}':None if n[0]=='A' else prefix+'-'+('A1' if n=='B1' else 'A2')+'_{job_id}' for n in ['A1','B1','B2','A2']},
        'ppl_scope':'四case各自无VTune固定PPL；PP/TG均带VTune诊断开销，不计算Score；算子差分复用4340916已有证据',
        'note':'当前最优是候选HC-post单补丁，后段整模PP +5.43%-5.60%、TG +0.50%-1.78%、几何均值 +2.94%-3.67%，独立ABABA/BABAB复测4341175/4341176仍在运行。已有模块有/无消融，HC-post内部循环/展开/SIMD尚无逐项消融，不能给各子改动分摊收益。采样窗口按墙钟，覆盖token数及跨rep/depth状态恢复可能不同；必须结合roi/events和target.pid过滤到llama-bench，不能把包装Python或全运行Elapsed的平均CPU利用率当作目标活跃窗口。软件wait区间可能跨暂停边界；可选报告失败保留返回码。全部十次样本、首轮慢样本、原始VTune结果留存，诊断不计正式性能成绩，不修改部署。'}
    (here/('submission_'+mode+'.json')).write_text(json.dumps(spec,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
admit=(rep/'admit.py').read_text(encoding='utf-8').replace("['ababa','babab']","['hotspots','threading']").replace("['r13n08','r13n45']","['r13n08','r13n45','r13n10','r13n22']")
(here/'admit.py').write_text(admit,encoding='utf-8',newline='\n')
print('Prepared frozen Intel HC-post HW/SW profiles with PP/TG ROI markers and ABBA/BAAB controls')
