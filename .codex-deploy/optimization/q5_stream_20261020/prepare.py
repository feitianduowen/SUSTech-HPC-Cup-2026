import json
from pathlib import Path

r=Path(__file__).resolve().parent
root='/work/apac2602/qwen38-cpu/optimization/20261020-q5-stream'
d={
 'script':root+'/run.lsf','kind':'Q5四版本多核流式算子诊断',
 'purpose':'检查Q5掩码/展开组合的单核驻留收益在多核和缓存外权重流式访问下是否保留；原版、仅掩码、仅展开、组合四实际Intel库同节点比较。复用原产物，不改模型源码。',
 'config':'hg_6148单节点40slots；实际库均Intel Classic2021.9 O3 precise/no-ftz CORE-AVX512；驱动icpc O2 strict/no-ftz/qopenmp。1/19/38 OpenMP线程close/cores、dynamic=false。长度2560/6144；resident每线程4行与总512MiB流式权重两模式；每线程首触本线程权重及Q8输入。四版本12轮循环换序，各位置各3次，每驱动含12配置；每测量先校准后目标约200ms，计入一次OMP启动/同步。48个驱动进程，共576条原始算子样本。每次运行全行输出哈希对原版、检查实际函数dladdr路径及参考库SHA前后。effective_weight_GBps仅逻辑Q5字节/耗时，不是实测DRAM带宽。无VTune，无模型PPL/PP/TG或Score。',
 'baseline':'同作业同配置原版实际库，另外与仅掩码4338563、仅展开4340602、组合4340624比较；不使用跨节点历史耗时作为baseline',
 'case_prefix':'diagnostic-q5-stream','comparison_scope':'same-node',
 'note':'合成权重访问及OpenMP调度不同于完整GGML图；所有库沿用已逐bit验证的固定产物，本轮只编译诊断驱动。不得将算子收益、有效字节率或1/19/38线程缩放写作正式模型收益。多核频率和NUMA放置以实际CPU列表记录，保留全部样本。'
}
(r/'submission.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
