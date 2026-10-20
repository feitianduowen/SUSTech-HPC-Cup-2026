import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

here=Path(__file__).resolve().parent
evidence=here.parent/'evidence'
bundle=json.loads((here/'completed_report_bundle.json').read_text(encoding='utf-8'))
summary=json.loads((here/'completed_report_summary.json').read_text(encoding='utf-8'))
registry=json.loads((evidence/'job_registry.json').read_text(encoding='utf-8'))
jobs={j['job_id']:j for j in registry['jobs']}
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
analysis_path=evidence/'analysis_updates/vtune_wait_pair_20261020.json'
analysis=json.loads(analysis_path.read_text(encoding='utf-8'))
analysis['updated_at_hkt']=stamp
for jid,files in bundle.items():
    assert jobs[jid]['state']=='DONE'
    assert all(s.endswith(': OK') for s in files['hash-check.txt'].splitlines())
    ppl=json.loads(files['ppl/perplexity_result.json'])
    assert ppl['status']=='PASS' and ppl['ppl']==2.7767 and ppl['elapsed_seconds']<=590
    vals={}
    rois={}
    for case in ['01_first_pp','03_later_pp']:
        x=json.loads(files[case+'/pp.json'])[0]
        assert len(x['samples_ts'])==len(x['samples_ns'])==10
        vals[case]={'pp':x['avg_ts'],'cv_percent':100*x['stddev_ts']/x['avg_ts']}
        roi=json.loads(files[case+'/roi.json']);rois[case]=roi
        assert roi['status']=='PAUSED_WINDOW_COMPLETE'
        assert roi['resume']['returncode']==roi['pause']['returncode']==0
        assert 60<=roi['control_interval_seconds']<70
        assert all(line.endswith('=0') for line in files[case+'/report-status.txt'].splitlines())
        log=files[case+'/vtune.log'].lower()
        assert not any(s in log for s in ['data limit has been reached','data limit reached','reached the data limit'])
    tg=json.loads(files['02_intervening_tg/tg.json'])[0]
    assert len(tg['samples_ts'])==len(tg['samples_ns'])==10
    first,later=summary[jid]['01_first_pp'],summary[jid]['03_later_pp']
    if jid=='4340365':
        summary[jid]['01_first_pp']['reported_wait_sum']=None
        summary[jid]['03_later_pp']['reported_wait_sum']=None
        metrics=f'硬件target PID CPU热点：自旋占报告CPU时间约{first["spin_percent"]:.2f}%→{later["spin_percent"]:.2f}%，比例接近；硬件模式没有等待时间指标，禁止把缺失当0。'
    else:
        metrics='软件模式target PID的__kmp_fork_barrier记录约370.780539线程秒、74次等待；后续PP未记录该等待项。barrier自旋占报告CPU时间约31.88%→30.17%，比例接近。fork-barrier休眠/唤醒是可检验线索，尚不能认定唯一原因。'
    note=(f'同节点首次PP→TG→后续PP全部完成，独立固定PPL2.7767 PASS；PP {vals["01_first_pp"]["pp"]:.6f}→{vals["03_later_pp"]["pp"]:.6f}，TG{tg["avg_ts"]:.6f}，三进程各10样本。两个PP控制窗口均约61秒，resume/pause返回码0，所有报告导出成功，未发现数据上限截断日志。'+metrics+
          '已按target.pid及process/function过滤包装Python。完整elapsed包含暂停时段，不能把整个elapsed当采样窗口；等待事件可能跨窗口边界，等待数/线程秒不是墙钟因果分解。报告有跳帧/未知符号限制；软件与硬件作业不同节点且采样方式有开销，不直接比较模式间吞吐。保留原始报告、全部十次样本，不计算性能Score。下一轮以200/infinite等待时长单变量做无采样平衡顺序干预，运行时设置先核验。')
    analysis['jobs'][jid]={'summary':note,'ppl':ppl['ppl'],'values':vals,'tg':tg['avg_ts'],'rois':rois,
                           'target_process_hotspot_summary':summary[jid],
                           'evidence_files':[str(here/'completed_report_bundle.json'),str(here/'completed_report_summary.json')]}
analysis_path.write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(here/'completed_analysis.json').write_text(json.dumps(analysis,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(here/'completed_report_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=here/'next_actions.json'
next_actions=json.loads(p.read_text(encoding='utf-8'))
next_actions['updated_at_hkt']=stamp;next_actions['phase']='both paired VTune jobs completed; candidate runtime intervention prepared'
for job in next_actions['jobs']:job['state']=jobs[job['job_id']]['state']
next_actions['next']='采样与完整PP/TG均完成。首次fork-barrier等待提示休眠/唤醒线索，但CPU自旋比例前后接近，且等待可跨暂停窗口；不可认定单一根因。继续执行Intel原版KMP_BLOCKTIME200/infinite无采样ABBA/BAAB单变量干预，PPL默认固定设置、参数不变。保留失败4340364及所有原始报告；不把profiling吞吐当正式成绩。'
p.write_text(json.dumps(next_actions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'verified_completed':list(bundle),'all_three_workloads_each_ten':True,'roi_control_valid':True}))
