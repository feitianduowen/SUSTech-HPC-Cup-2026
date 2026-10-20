import json
from datetime import datetime,timedelta,timezone
from pathlib import Path

root=Path(__file__).resolve().parent
evidence=root.parent/'evidence'
registry=json.loads((evidence/'job_registry.json').read_text(encoding='utf-8'))
ids=['4341208','4341209']
jobs=[j for j in registry['jobs'] if j['job_id'] in ids]
assert len(jobs)==2
stamp=datetime.now(timezone(timedelta(hours=8))).isoformat()
initial=root/'initial_progress.json'
progress=json.loads(initial.read_text(encoding='utf-8')) if initial.is_file() else {}
data={
    'updated_at_hkt':stamp,'phase':'HC-post candidate controlled HW/SW profiling running',
    'jobs':jobs,'frozen_builds':str(root/'frozen_builds.json'),'initial_progress':progress,
    'modes':{'4341208':{'analysis':'hardware-hotspots','order':'ABBA'},'4341209':{'analysis':'software-threading','order':'BAAB'}},
    'selected_candidate':'Intel Classic HC-post v2 only; exact frozen build from 4340916. Current strongest end-to-end candidate, independent unprofiled confirmation pending.',
    'existing_ablation':'HC-post module on/off comparisons: 4340916 ABBA and 4340917 BAAB, eight PPL PASS/160 samples. No separate row-loop/hoist/unroll/SIMD ablation within HC-post. Q5 has actual-library four-arm mask/unroll factorial microbench, but model gain not established.',
    'parallel_unprofiled_jobs':['4341175','4341176'],
    'next':'Let each job finish its four fresh fixed PPL and PP/TG profiles. Validate resume/pause ROI, target PID, collection warnings and report export return codes; inspect matching A/B within each mode and both positions. Exclude wrapper Python; normalize active sampling window and note cross-pause wait spans. Compare HC-post, tinyBLAS, Q4/Q5/Q8 kernels and OpenMP waits. Profiling throughput is diagnostic and never a formal Score.',
    'excel':'D:/compete/Qwen38_CPU_实验日志.xlsx'}
(root/'next_actions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
previous=root.parent/'hc4_post_v2_20261020/next_actions.json'
old=json.loads(previous.read_text(encoding='utf-8'))
old['profiling_followup']={'updated_at_hkt':stamp,'path':str(root/'next_actions.json'),'jobs':ids,'mode':'HW hotspots and SW threading, each same-node A/B controls and PP/TG ROI'}
previous.write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf-8')
if progress:
    notes={j['job_id']:{'summary':'启动快照（'+progress['updated_at_hkt']+'）：冻结文件SHA/ldd PASS、VTune真实采集工具探测PASS；当时阶段为'+j['stage']+'。本任务是当前HC-post候选及原版的受控profiling，PP/TG均带采样、只诊断不计分；四case各自独立固定PPL，后续ROI/热点/等待结果尚待完成。','initial_profile_evidence':j} for j in progress['jobs']}
    (evidence/'analysis_updates/hc4_profile_initial_20261020.json').write_text(json.dumps({'updated_at_hkt':stamp,'source':'/work/apac2602/qwen38-cpu/optimization/20261020-hc4-profile/initial_progress.json','jobs':notes},ensure_ascii=False,indent=2),encoding='utf-8')

completed=json.loads((root.parent/'hc4_post_v2_20261020/completed_model_analysis.json').read_text(encoding='utf-8'))
assert completed['complete_cases']==completed['ppl_passed']==8 and completed['full_benchmark_samples']==160
by_id={j['job_id']:j for j in registry['jobs']}
q5_late=[]
for jid in ['4340898','4340899']:
    ms=by_id[jid]['measurements']
    b=next(m for m in ms if '-candidate2_' in m['name'])
    a=next(m for m in ms if '-baseline2_' in m['name'])
    change={}
    for key in ['pp','tg']:
        bv=b[key][0] if isinstance(b[key],list) else b[key]
        av=a[key][0] if isinstance(a[key],list) else a[key]
        change[key]=100*(bv['avg_ts']/av['avg_ts']-1)
    q5_late.append(change)
q5=json.loads((root.parent/'q5_combined_20261020/next_actions.json').read_text(encoding='utf-8'))['review']
columns=['优化点','对照/消融范围','PP变化','TG变化','PP/TG几何均值变化','算子/数值证据','证据作业','结论与限制']
rows=[]
for job in completed['jobs']:
    late=job['pairs'][1]['change_percent']
    node='r13n08 ABBA' if job['job_id']=='4340916' else 'r13n45 BAAB'
    rows.append(['HC-post四路专用分支',node+'，模块开启/关闭；后段B2/A2',f"{late['pp']:+.2f}%",f"{late['tg']:+.2f}%",f"{late['geomean']:+.2f}%",'实际GGML图972组、42341535个F32值、3重复/1/3/38线程，0 bit差异；PPL均2.7767 PASS',job['job_id'],'当前最优候选；两对及首轮慢样本全部保留。首对PP为+60.45%/-32.74%，受顺序影响，后段结果不是全轮无偏汇总。独立五轮复测4341175/4341176在运行；未替换部署。'])
rows.append(['HC-post内部子改动','循环分段/系数提升、四路展开、AVX2与舍入屏障尚未逐项移除','未分摊','未分摊','未分摊','八通道SIMD+标量尾段；保持原版先mul舍入、按流FMA顺序','4340916/4340917','已有模块级消融，尚无内部组件的完整消融，不能把整模收益分别归给每个技巧。'])
rows.append(['Q5掩码+有序unroll4','原版/仅掩码/仅展开/组合：算子级四臂；整模ABBA/BAAB后段同口径B2/A2',' / '.join(f"{r['pp']:+.2f}%" for r in q5_late),' / '.join(f"{r['tg']:+.2f}%" for r in q5_late),'未证明稳定综合收益','组合单核驻留算子相对原版+5.13%至+20.49%；四库各262432个dot用例及144矩阵用例均逐bit通过','4340624；4340898/4340899','算子加速不等于整模收益。后段PP方向不一致且TG下降，未加入当前HC-post候选；四臂为算子级，并非完整模型四臂消融。'])
rows.append(['OpenMP等待/屏障','KMP_BLOCKTIME 200/infinite及普通barrier hyper/tree，单变量ABBA/BAAB','未证明稳定收益','受波动影响','未采用','原版代码及编译选项固定，四作业均完成固定PPL和十次样本','4340520/4340521；4340614/4340615','首次慢速未消除，不能把先后顺序差异当作参数收益；当前最优候选保持原基线默认等待配置。'])
rows.append(['当前profiling','A原版/B当前HC-post候选，HW ABBA及SW BAAB；PP/TG均采集','诊断不计分','诊断不计分','不计算Score','冻结48项eval二进制/动态库SHA及源码SHA；独立PPL后采集约60秒ROI','4341208（HW）；4341209（SW）','观察HC-post热点下降及GEMM/量化点积/OpenMP等待迁移；用target.pid排除Python、结合ROI和事件校准窗口，结果待完成。'])
overview={'updated_at_hkt':stamp,'selected_candidate':'HC-post v2 + original Intel O3 precise/OpenMP/tinyBLAS/38-thread close settings','columns':columns,'rows':rows,'source_analysis':str(root.parent/'hc4_post_v2_20261020/completed_model_analysis.json'),'q5_late_pairs':q5_late,'q5_microbench_percent':{k:v*100 for k,v in q5['combined_vs_original'].items()}}
(evidence/'optimization_overview.json').write_text(json.dumps(overview,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'profile_jobs':[(j['job_id'],j['state']) for j in jobs],'overview_rows':len(rows),'q5_late_pairs':q5_late,'registry_jobs':len(registry['jobs'])}))
