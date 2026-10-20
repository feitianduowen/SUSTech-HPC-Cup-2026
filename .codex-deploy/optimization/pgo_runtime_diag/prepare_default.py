import json
from pathlib import Path

here = Path(__file__).resolve().parent
dest = here.parent / 'pgo_default_diag'
dest.mkdir(exist_ok=True)
old = '/work/apac2602/qwen38-cpu/optimization/20261019-pgo-runtime-diag'
remote = '/work/apac2602/qwen38-cpu/optimization/20261019-pgo-default-diag'
for name in ['diagnostic.lsf', 'hot_sources.cmake', 'runtime_probe.cpp', 'run_cases.py']:
    text = (here/name).read_text(encoding='utf-8')
    text = text.replace(old, remote).replace('-prof-gen=threadsafe', '-prof-gen=default')
    text = text.replace('qwen38_pgo_runtime_diag', 'qwen38_pgo_default_diag')
    text = text.replace('%J.pgo_runtime_diag', '%J.pgo_default_diag')
    text = text.replace('Synthetic diagnostic only:', 'Default counter mode diagnostic only; 38-thread counters may race and MUST NOT be merged or used for feedback:')
    (dest/name).write_bytes(text.encode('utf-8'))
spec = {
    'script': remote+'/diagnostic.lsf',
    'kind': 'PGO计数器模式诊断+VTune',
    'purpose': '4337634显示77.3% CPU时间在Intel线程安全PGO checkpoint中；用编译器帮助中支持的default模式验证该运行时是否导致异常开销',
    'config': 'Intel Classic2021.9 O3 precise/no-ftz CORE-AVX512；hg_6148 40slots；新独立broad/hot默认计数构建；同节点plain→broad→hot、1线程后38线程；F32矩阵及16ADD，10轮；各子进程60s；VTune broad38采样10s；无模型/PPL/正式PP/TG/Score',
    'baseline': '本作业同节点匹配线程数plain合成计算；4337634线程安全模式仅作跨节点诊断参照',
    'note': '仅验证编译器插桩开销。default模式不提供多线程计数保护，38线程诊断计数可能竞争，绝不用于PGO反馈。若有效，后续正式训练仅1线程且新计数目录；PPL及评测仍38线程固定官方配置。保留全部旧结果和原始源码。',
    'retry_of': '4337634'
}
(dest/'diagnostic.json').write_bytes(json.dumps(spec, ensure_ascii=False, indent=2).encode('utf-8'))
print(dest)
