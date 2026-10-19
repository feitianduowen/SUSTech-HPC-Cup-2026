import json
import math
from datetime import datetime
from pathlib import Path

work = Path('D:/compete')
evidence = work/'.codex-deploy/optimization/evidence'
registry = json.loads((evidence/'job_registry.json').read_text(encoding='utf-8'))
rows = json.loads((evidence/'experiment_summary.json').read_text())
by_name = {r['name']: r for r in rows}

def number(value, digits=3):
    return '-' if value is None else f'{value:.{digits}f}'

def table(selected):
    text = '| 构建/策略与作业 | PPL | PP tokens/s (CV) | TG tokens/s (CV) | 自测 Score |\n|---|---:|---:|---:|---:|\n'
    for r in selected:
        def perf(key):
            return '-' if r[key] is None else f"{r[key]:.6f} ({r[key+'_cv']:.2f}%)"
        text += f"| {r['name']} | {number(r['ppl'],4)} {r['ppl_status']} | {perf('pp')} | {perf('tg')} | {number(r['score'])} |\n"
    return text

paired = [r for r in rows if r['name'].startswith('confirm-')]
screen = [r for r in rows if not r['name'].startswith(('confirm-','diagnostic'))]
comparisons = []
for job, variants, baseline_variant in [('4335857',['native','concat'],'baseline'),('4335870',['q8-u2'],'baseline'),('4335903',['native'],'baseline'),('4335930',['native-concat-u2'],'native'),('4335934',['copy-interleave'],'baseline')]:
    base = by_name.get('confirm-'+baseline_variant+'_'+job)
    for variant in variants:
        candidate = by_name.get('confirm-'+variant+'_'+job)
        if base and candidate and base['score'] and candidate['score']:
            comparisons.append(f"- 作业 {job}，{variant} 相对该节点 {baseline_variant}：PP {100*(candidate['pp']/base['pp']-1):+.2f}%，TG {100*(candidate['tg']/base['tg']-1):+.2f}%，Score {100*(candidate['score']/base['score']-1):+.2f}%。")
        else:
            comparisons.append(f'- 作业 {job}，{variant}：同节点完整对照尚未完成。')

memory=json.loads((evidence/'memory_analysis.json').read_text()) if (evidence/'memory_analysis.json').exists() else {'runs':[]}
memory_rows=[]
for run in memory['runs']:
    pp=run['workloads']['pp'];tg=run['workloads']['tg']
    score=100*math.sqrt(pp['mean']/46.929024*tg['mean']/3.295524)
    assert abs(score-run['score'])<1e-6
    memory_rows.append({'name':run['job']+'/'+str(run['position'])+'/'+run['name'],'ppl':run['ppl'],'ppl_status':run['ppl_status'],'pp':pp['mean'],'pp_cv':pp['cv'],'tg':tg['mean'],'tg_cv':tg['cv'],'score':score})

report = f'''# Qwen3.8 CPU 优化实验报告

更新时间：{datetime.now().astimezone().isoformat(timespec='seconds')}。本报告由原始 JSON 自动汇总，保留全部 10 次样本，未筛除低速样本。本轮记录的作业均已结束，失败作业也保留在 Excel 中。

## 当前结论

本轮没有足够可复现的全模型证据来替换现有部署。现有部署继续使用通过 PPL 的 Intel Classic 构建，14 个生产产物哈希核验一致；所有候选独立保存。

已完成 Intel OpenMP 等待策略、绑定、NUMA interleave、原生线程池、Q8 dot 展开/多累加器、tinyBLAS 数据复用/展开、oneMKL、IPO、组合候选及模型加载模式对照。CONCAT 的局部拷贝优化逐位通过，但完整模型结果未显示可稳定归因的综合收益。

KMP passive/0 严重拖慢 TG，oneMKL 未通过 PPL，IPO 编译失败；这些方案不采用。tinyBLAS 的手工数据复用与原构建生成相同的热点机器码，不能把不同节点的速度差当作代码收益。Q8 多累加器在微基准中退化，PPL 通过也不足以采用。

## 固定条件与正确性

- 基础版本：`d81235049384534c167caea52b85a694f6103d14`，CPU-only；双路 Xeon Gold 6148，40 个物理核，作业申请单节点 40 slots，推理线程固定 38。
- 编译器：Intel Classic `icc/icpc 2021.9.0.20230302`。GCC 11.2 仅提供头文件/运行库。采用 `-O3 -fp-model precise -no-ftz -xCORE-AVX512 -qsimd-honor-fp-model`；默认 OpenMP ON、BLAS OFF。
- PPL：`-t 38 -tb 38 -c 512 --chunks 2 -b 512 -ub 256 -ctk f16 -ctv f16 -ngl 0 --numa distribute --no-warmup`。参考 2.7696，允许区间 `[2.63112, 2.90808]`；模型路径、四个分片大小、WikiText 哈希均按参考记录核验。
- PP：`-p 2048 -n 0`；TG：`-p 0 -n 128 -d 2048`；共同固定 `-t 38 -b 2048 -ub 512 -ctk f16 -ctv f16 -ngl 0 -r 10`。先 PPL PASS，再运行两项性能测试。
- 自测分数为 `100*sqrt(PP/46.929024 * TG/3.295524)`，仅在完整 PPL/PP/TG 通过后列出。正式成绩仍须由组委会受控评测生成。
- 规则第 2 节及第 6.1 节允许选择平台可用编译器和构建参数，因此使用 Intel 编译器符合本地提供的题目规则。PP/TG 运行时策略按第 7.1 节记录，正式使用须经组委会接入；PPL 的固定 NUMA 条件保持一致。

## 同节点完整对照

作业 4335857 在 r13n09 顺序运行 baseline、native、concat；4335870 在 r13n10 顺序运行 baseline、q8-u2。为检查顺序影响，4335903 在 r13n04 反向运行 native、baseline。4335930 在 r13n30 先测组合候选 native-concat-u2，再测 native；4335934 在 r13n15 先测原版构建的 `-lm none + numactl --interleave=all`，再测默认加载。每个版本重新运行固定 PPL、PP 十次和 TG 十次；加载策略仅作用于性能测试。

{table(paired)}
{chr(10).join(comparisons)}

这些实验为同一节点的顺序对照，尚不能消除运行先后、文件缓存、首次触页和温度/频率的影响。CV 是样本标准差除以平均吞吐，不是收益置信区间；几乎相同的结果不应视作稳定提升。

native 与 q8-u2 在各自基线之后运行时，PP 都从约34升至约53 tokens/s；反向测试没有复现相同提升。已对比实际编译命令，q8-u2 保持 OpenMP ON，native 为 OFF，其余主要编译参数与生产构建一致。因此不能把前向作业的全部差值归因于某一个修改。

反向作业中 native 先运行的 PP 为 33.771816，与后运行的 53.361444 差异很大。OS 采样也显示先运行 PP 的进程 CPU 活跃核数约24，后运行时约38（包含自旋）。已记录线程亲和性，两个 socket 各19个计算线程；不能用这些数据直接确认某一种内存硬件瓶颈。

4335903 中 native 相对该节点后运行 baseline 的 Score 为 -10.47%；4335930 的组合候选相对后运行 native 为 -20.72%。4335934 的 copy-interleave 在该组 Score +8.23%，同时 TG -4.07%；后续两节点矩阵未支持把 interleave 作为普遍更优配置。保持默认部署，避免依据单组最优样本更换配置。

## 补充加载/NUMA矩阵

4336045 在 r13n05 正序测试 auto-default、auto-interleave、copy-interleave、copy-default；4336046 在 r13n15 使用相反顺序。同一 Intel 生产产物，每作业独立执行一次固定 PPL，四个加载配置共享该数值门槛；每个配置的 PP/TG 各完整十次，含15秒轻量 OS 监控。

{table(memory_rows)}

copy-default 的 PP 在两个节点约53，copy-interleave 约39–40；auto-default 从正序第一位的33.56到逆序最后一位的53.62，显示明显的节点/顺序相关变化。copy-default 的一组 TG CV 达26.60%，auto-default 的一组 PP CV 达25.01%，低速样本全部保留。这些开发结果不能证明某个加载模式同时稳定改善 PP 与 TG。

## 第一轮完整筛选

以下作业分布在同配置的不同节点，用于排除明显退化与数值失败。跨节点 PP 差异明显，不能直接用某行相对原始作业的差值归因于优化。

{table(screen)}

`q8-a4` 只完成 PPL，因微基准退化未继续完整性能评测，故没有 Score。IPO 作业 4335838 在 Intel 多文件优化链接阶段报内部错误 `010101_3096` / `#10014`，没有可用性能结果。

## 线程与节点计时发现

VTune 作业 4335666 发现 PP 的 barrier CPU 采样占比 30.79%，TG 为 28.07%；这不是可直接回收的墙钟时间。为定位等待来源，诊断构建记录各线程节点计算、到达和边界等待时间，不删除同步，不纳入性能评分。

正式 PP 测量窗口作业 4335859 跳过四个预热图，记录前四个测量微批图：292 次 CONCAT 的关键计算累计 4.428649 秒，线程边界等待累计 163.879419 CPU 秒。原实现按 `ne2` 分工，典型输入 `9x10240x1x1` 与 `512x10240x1x1` 的 `ne2=1`，只有一个线程执行拷贝。CONCAT 的等待不能通过单纯降低 blocktime 消除。

同一窗口 MUL_MAT_ID 的关键计算累计 47.641077 秒，MUL_MAT 为 13.217878 秒。主要 Q8 tinyBLAS 形状为 `m=10240,n=512,k_blocks=80` 和 `m=2560,n=512,k_blocks=192`，均有 38 个活跃线程、无空闲线程，tile 数差异很小；大 GEMM 的简单重分块缺少收益依据。

TG 的 Q8 dot 高 CPI 与 NUMA 驻留偏斜仍不足以证明远程内存就是瓶颈。平台未提供可用的远程访问/带宽硬件计数；`numactl --interleave=all` 也未必重新放置已存在的文件页缓存。本轮保留 OS 驻留、CPU 时间和缺页记录，不把驻留比例换算成远程访存率。

## 候选代码与算子验证

CONCAT 补丁仅修改 `ggml/src/ggml-cpu/ops.cpp` 的 F32/I32 连续行路径：按完整行数为线程划分连续块，使用 `memcpy`，四个拼接轴均按原 tensor stride 定位；不连续列保留原路径。没有修改模型、量化权重、数值运算或图同步。

- 作业 4335851：216 个真实基线/候选动态库差分用例逐位一致，覆盖 F32/I32 原始位模式、四个轴、填充行 stride、转置回退、1/3/38 任务。
- 作业 4335883：相同 216 个用例改为实际并发执行后通过；另对 `3+512`、`9+512` 列与 10240 行的真实形状，以 38 线程执行并逐位核验。五轮交替顺序的热缓存微基准中，原函数每次约 8.78/8.94 ms，候选中位约 0.054/0.058 ms。这只证明该拷贝路径提速，不能替代完整模型 PP/TG 结果。
- CONCAT 完整 PPL 为 2.7767，与默认构建一致。q8-u2 为 2.7767；q8-a4 为 2.7789，均在门槛内。
- Q8 微基准作业 4335817：每实现 1392 个数值用例。顺序展开 u2/u4 与原函数逐位一致；独立累加器 a2/a4 改变舍入，并且微基准慢约 2%–4%。真实 `k_blocks=80/192` 的流式测试中，u2 仅约 0.3% 收益，不足以独立证明 TG 改善。
- tinyBLAS 数据复用作业 4335828：768 个差分用例通过；Q8 主热点 2000 字节机器码与原版 SHA-256 完全相同。Intel `#pragma unroll` 的真实形状微基准收益约 0.4%–1.1%，未升级为部署候选。

## 复现与证据

远端实验根目录：`/work/apac2602/qwen38-cpu/optimization/20261018-v1`。

`scripts/build_variant.lsf` 负责 Intel 离线构建与量化测试；`benchmark_variant.lsf` 负责固定 PPL/PP/TG 门槛；`benchmark_runtime.lsf` 记录运行时策略；`confirm_variants.lsf`、`confirm_q8.lsf` 负责同节点对照。源码差异、构建日志、CMake 配置、逐次 JSON、诊断 CSV 和候选 SHA-256 分别位于 `patches/`、`logs/`、`results/`。原有生产源码、正式模型及参考 JSON 未被这些候选替换。

完整作业日志：[Qwen38_CPU_实验日志.xlsx](D:/compete/Qwen38_CPU_实验日志.xlsx)，包含每个作业的提交时间、配置、改动、结果与 baseline；无比较对象时填“无”。失败作业和原始十次样本均保留。

本轮优化候选均使用用户要求的 Intel 编译器；首次部署的历史 GCC 作业 4335554 早于该要求。没有穷举全部等待参数组合，也没有改写全局 NUMA 分配器。Q5_1/repack、F32 dot 等更深层优化尚未实施，不应把本轮筛选描述为已经完成所有可能优化。
'''
pgo_jobs=[j for j in registry['jobs'] if '20261019-compiler-pgo' in j.get('submission',{}).get('script','')]
if pgo_jobs:
    rejected=[r for r in registry.get('rejected_submissions',[]) if '20261019-compiler-pgo' in r.get('script','')]
    report+='\n## Intel Classic PGO 后续阶段\n\n'
    report+='O3/O2 分别设计无 PGO control、threadsafe 计数构建和反馈优化构建，维持原浮点约束、OpenMP ON、BLAS OFF，未启用 -ipo。训练仅为合成 PP1024 / TG32@D512、38 线程、各 1 次，不读取 WikiText，也不计入性能结果。最终各构建仍须独立固定 PPL 后才能完整测速。\n\n'
    report+='登记的 PGO 阶段作业：'+'；'.join(j['job_id']+' / '+j['state']+' / '+j.get('exec_host','尚未分配') for j in pgo_jobs)+'。状态以本次原始登记快照时间为准。\n\n'
    report+='初次作业 4336529（r13n28）和 4336530（r13n33）在 INIT 因计算节点无 git 退出，尚未编译/加载模型。已改为登录节点验证官方 commit 并保存 3,687 个源码文件 SHA256，计算节点逐文件校验。失败记录保留。\n\n'
    if rejected:
        report+=f'保留 {len(rejected)} 次未取得作业号的历史 PGO 重提拒绝；当时 LSF 原文为 Group <u-ssc>: Pending job slots threshold reached，最终 User permission denied. Job not submitted。当时组排队 slots 达到 MPEND=3000 阈值；换节点不能消除此组级准入限制。这些历史尝试列入 Excel“提交拒绝”页，不算 PEND/RUN 作业；后续重提状态见上方。\n\n'
    report+='PGO 产物尚未完成固定 PPL 和完整 PP/TG 验证，不能给出收益或分数；现有 READY 部署未替换。下一阶段正反序同节点对照脚本及哈希验证已备齐，见 `.codex-deploy/optimization/compiler_pgo/README.md`。\n'
(work/'Qwen38_CPU_优化实验报告.md').write_text(report,encoding='utf-8')
print(work/'Qwen38_CPU_优化实验报告.md')
