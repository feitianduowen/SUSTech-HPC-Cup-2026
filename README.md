# SUSTech HPC Cup 2026

Qwen3.8-Flash-Next CPU 推理部署、性能分析与优化实验资料。

## 资料入口

- [任务规则](Qwen3.8_Flash_Next_CPU_Inference_Optimization_Task_Rules_CN_Final_20261018.md)
- [部署说明](Qwen38_CPU_部署说明.md)
- [性能分析报告](Qwen38_CPU_Profiling报告.md)
- [性能图表](Qwen38_CPU_Profiling.png)
- [原始安装脚本](install_llama_cpp_cpu_ppl.lsf)
- [原始评测脚本](llama_bench_38t_ppl_with_baselines.lsf)

## 脚本、源码与实验数据

`.codex-deploy/` 保留本地资料原有结构：

- `package/`：部署与复现脚本、运行配置及说明。
- `evidence/`：部署清单、环境记录与正确性验证结果。
- `profiling/`：采集和分析脚本、源码快照、报告及 `results_4335666/` 原始结果。
- `optimization/`：PP、TG、运行时分析相关的优化源码、补丁和实验脚本。

本仓库不包含已安装的运行环境、依赖目录、Python 缓存或编译生成的二进制文件。用于复现实验的环境配置脚本和环境记录作为资料保留。运行脚本中的集群路径需按实际部署位置调整。
