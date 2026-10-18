# Qwen3.8 CPU Profiling 报告

采集日期：2026-10-18。LSF 作业 **4335666**，节点 **r13n16**，状态 **DONE / PROFILE_READY**。

当前 Intel 构建的主要优化方向是 **OpenMP 同步、量化计算内核和 NUMA 内存放置**。PP 与 TG 的热点不同：PP 的前三个量化内核占采样 CPU 时间约 **50.5%**；TG 的 **Q8_0 点积单项占 54.5%**。两者均有较高自旋等待：PP **32.4%**，TG **28.0%**。

这些比例来自 CPU 时间采样，不能直接换算成端到端提速比例。降低空转还需缩短关键路径，单纯让等待线程休眠可能只减少 CPU 消耗。

## 构建与测量条件

| 项目 | 实际配置 |
|---|---|
| CPU | 双路 Intel Xeon Gold 6148，40 个物理核，2 个 NUMA 节点，无 SMT |
| 调度 | `ssc-cpu`，单节点 40 slots；计算线程固定 38 |
| 编译器 | Intel Classic `icc/icpc 2021.9.0.20230302`，oneAPI 2023.1 |
| 构建 | Release、CPU-only、AVX-512 目标、OpenMP 开启、BLAS 关闭 |
| 数值选项 | `-fp-model precise -no-ftz -qsimd-honor-fp-model`；完整选项在 manifest |
| 源码 | `d81235049384534c167caea52b85a694f6103d14`，官方 `v0.6.0` |
| 模型 | 官方 `Qwen3.8-Flash-Next-UD-Q4_K_XL` 四分片，原共享路径 |
| 正确性 | 作业 4335636 的 PPL **2.7767，PASS**；官方参考 2.7696，差异 **+0.2564%** |
| 构建身份 | 本轮核对 14 个可执行文件与动态库 SHA-256，全部与 PPL 通过时一致 |
| 采样器 | VTune 2023.1，driverless Perf 用户态硬件事件，10 ms 间隔、2048 字节调用栈 |

两个负载均保留 `-t 38 -b 2048 -ub 512 -ctk f16 -ctv f16 -ngl 0 --numa distribute -r 10`。PP 为 `-p 2048 -n 0`；TG 为 `-p 0 -n 128 -d 2048`。环境保留 `OMP_NUM_THREADS=38`、`OMP_DYNAMIC=FALSE`、`OMP_PROC_BIND=close`、`OMP_PLACES=cores`。

采样跳过模型加载、预热和 TG 首次 depth prefill，在第一条正式测量进度后恢复。恢复延迟分别为 PP **1.344 s**、TG **0.773 s**，因此首个样本开头有少量未覆盖时间。窗口包含重复之间的调度、TG 缓存状态恢复和少量退出清理；OS 汇总另行剔除最后一次测量后的清理阶段。

本轮沿用已通过 PPL 的构建，没有重新执行正式的 PPL→PP/TG 评分流程。**以下速度是在 profiler 下测得的诊断值，不是正式成绩，也不据此计算 Score 或判定编译器相对官方基线的回退。**

## 结果概览

| 指标 | PP2048 | TG128@D2048 |
|---|---:|---:|
| 重复次数 | 10 | 10 |
| 平均吞吐，tokens/s | 27.637 | 3.017 |
| 吞吐标准差，tokens/s | 5.266 | 0.048 |
| 单次吞吐范围，tokens/s | 18.674–32.694 | 2.883–3.046 |
| OS 平均活跃 CPU 核数，含内核时间 | 19.63 | 37.28 |
| VTune 有效计算等效核数 | 12.84 | 25.80 |
| 自旋等待占采样 CPU 时间 | 32.41% | 28.04% |
| 用户态 CPI | 0.602 | 3.862 |
| 测量阶段 RSS 范围，GiB | 101.82–109.31 | 102.03–103.44 |
| 测量末期 NUMA 0 / 1 驻留，GiB | 30.34 / 78.97 | 29.21 / 74.23 |
| NUMA 0 / 1 采样 CPU 时间占比 | 49.99% / 50.01% | 50.02% / 49.98% |
| 测量阶段 minor / major faults 增量 | 2,305,976 / 0 | 696,597 / 0 |

“活跃核数”与“有效计算等效核数”口径不同：前者取 `/proc` 的进程 CPU 时间增量，包含空转及内核时间；后者由 VTune 剔除识别出的自旋和运行时开销。VTune 总线程数还包含 Python 封装及辅助线程；benchmark JSON 的正式计算线程数为 38。

PP 的前三次明显慢于后续测量，同时 RSS 与 minor faults 仍在增加。这说明即使经过一次预热，后续测量仍有工作集驻留或分配变化；不能将所有波动归咎于某个计算内核。TG 后九次较稳定。

![10 次诊断测量的吞吐趋势](throughput.png)

## PP 函数热点

占比的分母为采样 CPU 总时间；下表为函数自身时间，调用栈层级不重复相加。

| 函数 | CPU 时间占比 | 定位 |
|---|---:|---|
| `__kmpc_barrier` | 30.79% | Intel OpenMP 屏障 |
| `tinyBLAS_Q0_AVX<block_q8_0, block_q8_0, float>::gemm4xN<4>` | 29.67% | `ggml-cpu/llamafile/sgemm.cpp:1615` |
| `ggml_vec_dot_q5_1_q8_1` | 11.25% | `ggml-cpu/arch/x86/quants.c:1222` |
| `ggml_gemv_q4_K_8x8_q8_K` | 9.55% | `ggml-cpu/arch/x86/repack.cpp:1464` |
| `ggml_compute_forward_dsv4_hc_post` | 4.20% | `ggml-cpu/ops.cpp:11556` |
| `__kmp_fork_barrier` | 1.64% | OpenMP 并行区域同步 |
| `ggml_compute_forward_gated_delta_net` | 1.50% | gated delta net |

前三个量化计算内核合计占总 CPU 时间 **50.47%**，约占 VTune 有效计算时间 **74.7%**。当前应优先分析这些路径，而不是先优化占比较低的 attention、norm 或激活函数。

调用栈将大部分 `__kmpc_barrier` 时间指向 `ggml_graph_compute_thread`。同一版本源码中，`ggml_barrier()` 在 OpenMP 构建下直接执行 `#pragma omp barrier`（`ggml-cpu.c:576`），图计算循环在节点之间调用该屏障（`ggml-cpu.c:3157` 附近）。因此图节点粒度、串行或低并行度节点、任务分配及节点间同步是重点检查对象。该证据不能进一步确定每个具体节点的墙钟代价。

## TG 函数热点

| 函数 | CPU 时间占比 | 该函数 CPI |
|---|---:|---:|
| `ggml_vec_dot_q8_0_q8_0` | 54.49% | 7.069 |
| `__kmpc_barrier` | 28.07% | 2.526 |
| `ggml_vec_dot_f32` | 7.03% | 46.923 |
| `ggml_gemv_q4_K_8x8_q8_K` | 2.92% | 1.405 |
| `ggml_vec_dot_bf16` | 1.56% | 50.522 |
| `__intel_avx_rep_memcpy` | 1.46% | 30.000 |
| `ggml_vec_dot_q5_1_q8_1` | 1.16% | 0.523 |

TG 的 Q8_0 点积是首要计算热点，占有效计算时间约 **76.3%**。若只优化 PP 的 tinyBLAS GEMM，不能据此期待相同的 TG 收益。

TG 点积路径的高 CPI、较大的工作集及 NUMA 驻留偏置，与内存访问压力相符，**这是待验证的推断**。现有数据不足以区分 DRAM 带宽、远程访问延迟、缓存缺失与其他停顿的各自贡献，不能宣称已经测得“内存带宽瓶颈”。

## 建议的下一轮实验顺序

1. **同步与工作划分。** 保持 Intel 编译器和 38 线程，比较当前 Intel OpenMP 与 ggml 原生线程池；检查低并行度节点、任务切分及可保持依赖和数值语义的融合机会。单独降低 spin 参数不等于缩短关键路径。
2. **分别优化两个阶段的计算热点。** PP 从 `gemm4xN<4>`、Q5_1 点积及 Q4_K repack GEMV 入手；TG 从 Q8_0 点积入手，检查数据复用、预取、展开和向量路径。保持官方模型及量化格式不变。
3. **NUMA 对照实验。** 当前两侧 CPU 工作量约各半，而约 72% 的驻留内存在节点 1。比较受控的 interleave / first-touch 策略，并检查吞吐、线程等待和页分布是否同时改善。驻留分布本身不是远程访问量。
4. **复验。** 每次涉及计算或构建的变更先跑固定 PPL，再用不带 profiler 的受控流程测 PP/TG；正式运行时策略按题面第 7.1 节接入。当前 profiling 未修改计算代码或编译参数。

## 数据边界与复查

- 系统缺少内存带宽采样所需的 Intel sampling driver，因此没有 DRAM 带宽或 NUMA 远程访问计数；未修改系统权限或内核参数。
- Top-down `Microarchitecture Usage` 字段全部为零，未把它当作有效的利用率结论。CPI 来自当前用户态事件采样，不能替代完整的瓶颈分解。
- Release 构建没有完整源码调试行信息，perf 日志还有 DWARF 寄存器/调用栈展开警告，部分栈显示 skipped frames。函数 IP 热点与源码核对是本文的主要依据，未用不完整的栈断言具体源码行耗时。
- 原始 benchmark 的 `build_commit` 为 `unknown`；真实源码 commit 由独立 Git 记录及部署 manifest 保存，二进制身份由 SHA-256 核验。
- 使用 Intel 编译器符合题面第 2 节、第 6.1 节允许选择编译器及构建方式的规定。[规则原文](reproduction/task_rules_CN.md)

服务器原始采样及报告：

```text
/work/apac2602/qwen38-cpu/profiling/results_4335666/
├── pp2048/vtune/       # 原始采样
├── tg128_d2048/vtune/  # 原始采样
├── analysis.json       # 固定参数与系统指标汇总
├── artifact_verification.json
└── reports.zip        # 文本、CSV、JSON 和复现脚本，不含大型原始采样
```

本地材料：[结果目录](.)、[复现说明](reproduction/README.md)、[PP 热点 CSV](./pp2048/hotspots.csv)、[TG 热点 CSV](./tg128_d2048/hotspots.csv)。
