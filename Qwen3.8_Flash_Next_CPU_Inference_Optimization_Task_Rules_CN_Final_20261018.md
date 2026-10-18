# Qwen3.8-Flash-Next CPU 推理性能优化任务规则



## 1. 任务目标

参赛队伍基于指定的 `llama.cpp` 基础版本，在固定 CPU 节点上优化 Qwen3.8-Flash-Next 的 CPU 推理性能，**同时必须通过基于 `llama-perplexity` 的正确性验证**。正确性验证是正式评分的强制准入条件。

- 推理框架：`llama.cpp`
- 基础版本：`v0.6.0`
- 正式模型：`unsloth/Qwen3.8-Flash-Next-GGUF`
- 量化版本：`UD-Q4_K_XL`
- 模型分片：4 个 GGUF 文件
- 正式性能评测工具：`llama-bench`
- 正式正确性评测工具：`llama-perplexity`（PPL 回归测试）
- 正式评测：CPU-only

参赛者可以修改 `llama.cpp / ggml` 源代码、CPU kernel、构建配置，以及本规则明确允许的运行时执行策略；但不得改变正式模型、推理计算语义、必测 workload 或评分统计口径。

**本赛题确认使用的参考脚本：**

| 阶段 | 参考脚本文件名 | 主要职责 |
|---|---|---|
| 离线安装 / 编译 / 构建验证 | `install_llama_cpp_cpu_ppl.lsf` | 从预先准备的本地 `llama.cpp` 源码构建并验证所需可执行文件 |
| 正确性验证 / 性能评测 / 评分 | `llama_bench_38t_ppl_with_baselines.lsf` | 先比较 PPL，再执行 PP2048 和 TG128@D2048，并计算基准归一化得分 |

这两个脚本是**组委会的参考构建与评测入口**；路径值属于部署配置，不是参赛者必须使用的个人目录。组委会保留运行经过审核的等效包装脚本以接入本规则允许的调优选项的权利，但不能改变固定工作负载、正确性门槛或评分公式。

---

## 2. 固定硬件环境

正式成绩统一在以下硬件环境产生：

| 项目 | 固定配置 |
|---|---|
| 计算节点 | 1 个独占 CPU 节点 |
| CPU | 2 × Intel Xeon Gold 6148 |
| 物理核心 | 40 核（20 核 × 2 Socket） |
| NUMA | 2 NUMA nodes |
| 内存 | 192 GB |
| GPU / NPU / FPGA | 禁止使用 |
| llama-bench 线程 | **38 threads** |

正式评测必须独占一个节点。40 个物理核中，`llama-bench` 与 `llama-perplexity` 均固定使用 38 个计算线程，其余核心留给系统和调度运行时。

GCC、Clang、CMake 等编译与构建工具的具体版本**不作为参赛强制限制**。参赛者可以在官方 CPU 平台可用的软件环境范围内选择编译器、编译参数和构建方式，并可将其作为性能优化的一部分。

组委会生成参考 Baseline 时使用的软件环境另见第 6 节。

参考安装脚本申请 `ssc-cpu` 队列中的单节点 40 个作业 slot（`#BSUB -n 40`、`span[ptile=40]`）；计算进程的正式推理线程数依然固定为 38，**申请 40 个 slot 不等于允许使用 40 个推理线程**。

---

## 3. 固定模型

正式模型固定为：

```text
Qwen3.8-Flash-Next-UD-Q4_K_XL
```

运行时指定第一个 GGUF shard，例如：

```bash
MODEL=/work/ssc-zhaojh/llama_model/unsloth/Qwen3.8-Flash-Next-GGUF/UD-Q4_K_XL/Qwen3.8-Flash-Next-UD-Q4_K_XL-00001-of-00004.gguf
```

4 个 shard 必须位于同一目录。

正式评测不得：

- 更换模型或量化版本；
- 重新量化；
- 修改模型权重；
- 剪枝、蒸馏、删除层或跳过专家；
- 使用额外 GPU/加速器；
- 通过减少模型应执行的计算获得虚假加速。

---

## 4. 正式性能与正确性评测

**`llama-bench` 性能评测：固定约束与可调执行策略分开管理**

下面是**所有队伍必须保持不变**的正式性能评测核心参数：

| 参数 / 资源 | 固定值 |
|---|---|
| 正式模型 | 第 3 节规定的 4 个 GGUF 分片 |
| CPU 推理线程数（`-t`） | **38** |
| Batch（`-b`） | **2048** |
| UBatch（`-ub`） | **512** |
| KV Cache K / V（`-ctk`、`-ctv`） | **f16 / f16** |
| GPU layers（`-ngl`） | **0**（CPU-only） |
| 重复次数（`-r`） | **10** |
| 测试类型与 Token 数 | PP2048、TG128@D2048；详见第 4.1、4.2 节 |
| 计分数据 | `llama-bench` 正式 JSON 中的平均 tokens/s；不得更改统计口径 |

**参考脚本中的默认执行策略**：`--numa distribute`，`OMP_NUM_THREADS=38`、`OMP_DYNAMIC=FALSE`、`OMP_PROC_BIND=close`、`OMP_PLACES=cores`，以及 OpenBLAS/MKL/BLIS 的线程环境设置。`--numa distribute` 和不改变总线程数的绑定、内存策略等，属于第 7.1 节规定的**可申请调优的性能运行时策略**，并非不可变的计算 workload。

下方命令是**当前参考脚本的默认配置示例**，不表示除固定参数外的所有选项均必须永远保持原值。可调选项须经组委会确认后通过正式评测入口统一应用，而不是未经批准覆盖固定参数。

### 4.1 Prefill / Prompt Processing

固定测试：

```text
PP2048
```

参考命令（当前脚本默认运行时策略）：

```bash
./build/bin/llama-bench \
  -m "${MODEL}" \
  -t 38 \
  -ngl 0 \
  -b 2048 \
  -ub 512 \
  -ctk f16 \
  -ctv f16 \
  --numa distribute \
  -p 2048 \
  -n 0 \
  -r 10 \
  -o json \
  > pp2048.json
```

正式记录：

```text
PP2048 average tokens/s
PP2048 standard deviation
PP2048 CV
```

### 4.2 Decode / Token Generation

固定测试：

```text
TG128 @ context depth 2048
```

参考命令（当前脚本默认运行时策略）：

```bash
./build/bin/llama-bench \
  -m "${MODEL}" \
  -t 38 \
  -ngl 0 \
  -b 2048 \
  -ub 512 \
  -ctk f16 \
  -ctv f16 \
  --numa distribute \
  -p 0 \
  -n 128 \
  -d 2048 \
  -r 10 \
  -o json \
  > tg128_d2048.json
```

正式记录：

```text
TG128@D2048 average tokens/s
TG128@D2048 standard deviation
TG128@D2048 CV
```

`-d 2048` 为正式 Decode workload 的固定条件，不得用空上下文 `-p 0 -n 128` 代替。

**正式固定的 PP/TG 测试参数：** PP 使用 `-p 2048 -n 0`，TG 使用 `-p 0 -n 128 -d 2048`；二者均固定 `-t 38 -b 2048 -ub 512 -ctk f16 -ctv f16 -ngl 0 -r 10`。在这些约束外，允许按第 7.1 节调优 CPU 运行时执行策略；相关设置可以对 PP、TG 分别申报，但必须由统一评测流程记录且确保同一模型、同一优化构建产物。

### 4.3 正式正确性测试：llama-perplexity（必须通过）

正式成绩除满足第 4.1、4.2 节的性能测试外，**还必须通过 `llama-perplexity` 的 PPL 正确性回归测试**。PPL 是验证优化后的推理数值行为是否明显偏离官方参考版本的统一指标；它不是额外的性能评分项。

**固定测试输入：** 组委会提供的 WikiText-2 测试文本 `wiki.test.raw`。不同队伍必须使用相同文件内容，正式参考文件的 SHA-256 为：

```text
173c87a53759e0201f33e0ccf978e510c2042d7f2cb78229d9a50d79b9e7dd08
```

**固定测试参数（与 `llama-bench` 性能参数不同）：**

| 项目 | 固定值 |
|---|---|
| 模型 / 量化版本 | 第 3 节规定的 4-shard GGUF / `UD-Q4_K_XL` |
| Threads (`-t`) | 38 |
| Batch threads (`-tb`) | 38 |
| Context (`-c`) | **512** |
| Chunks (`--chunks`) | **2** |
| Batch (`-b`) | **512** |
| UBatch (`-ub`) | **256** |
| KV Cache K / V | `f16` / `f16` |
| NUMA | `distribute` |
| GPU layers | `0`（CPU-only） |
| Warmup | `false`（`--no-warmup`） |

该配置每次处理 `512 × 2 = 1,024` 个上下文 Token；PPL 通常仅对各上下文的后半部分进行计分。这是**比赛用轻量正确性回归测试**，并不等同于对模型所有实际任务准确率的完整评估。

正式运行示例（`MODEL` 使用第 3 节规定的 GGUF 第一分片；`PPL_DATA` 由组委会指定）：

```bash
PPL_DATA=/work/ssc-zhaojh/llama_model/unsloth/Qwen3.8-Flash-Next-GGUF/wikitext-2-raw/wiki.test.raw

./build/bin/llama-perplexity \
  -m "${MODEL}" -f "${PPL_DATA}" \
  -t 38 -tb 38 -ngl 0 \
  -c 512 -b 512 -ub 256 \
  -ctk f16 -ctv f16 \
  --numa distribute \
  --chunks 2 --no-warmup \
  > perplexity.log 2>&1
```

**正确性判定规则：** 以第 6.1 节的原始版本 PPL 基准 `PPL_base = 2.7696` 为准，采用绝对相对误差：

```text
PPL_relative_diff(%) = abs(PPL_team - 2.7696) / 2.7696 × 100%

PPL PASS  当且仅当：
  1) llama-perplexity 正常执行结束，并输出完整、有效的最终 PPL；
  2) PPL_relative_diff <= 0.5%；
  3) 模型、4 个分片、测试文本 SHA-256、固定运行参数与参考条件一致。
```

因此正式允许的 PPL 数值区间为 **`[2.755752, 2.783448]`（包含边界）**。判定使用实际解析的数值，不得先对参赛结果进行人为四舍五入以获得 PASS。

- 若 PPL 超过上述允许区间：`FAIL`，**该参赛版本不得获得有效正式成绩或排名**。
- 若进程异常退出、未产生完整最终 PPL、出现 NaN/Inf，或参考条件不一致：`ERROR / INVALID`，均视为**未通过正确性门槛**。
- `PPL_team` 数值变得更低也不自动视为正确；若绝对相对偏差超过 0.5%，仍需视为 `FAIL`，避免以改变模型计算语义的方式获得成绩。
- PPL 失败时应停止该版本的后续正式性能评测；即使已有较高的 `llama-bench` 性能结果，也**不得据此计算有效的比赛排名成绩**。

**PPL 测试的特殊约束：** 当前官方参考 JSON 对线程数、context、chunks、batch/ubatch、KV Cache、NUMA、warmup、GPU layers、模型分片路径与大小、数据文件 SHA-256 均作一致性检查。因此 **PPL 的 `--numa distribute` 也是固定正确性测试条件**；不得把“PP/TG 允许优化 NUMA 策略”理解为能够直接修改正式 PPL 的固定配置。可能改变数值计算路径的其他运行时优化，应接受组委会的附加正确性核验；不得让同一优化实现只在性能测试开启、在正确性测试刻意关闭以规避检查。

组委会保留对优化代码执行额外算子测试、输出对比或源码审查的权利；通过这项小样本 PPL 测试不代表自动豁免其他作弊或错误检查。

### 4.4 参考作业脚本与正式评测流程

组委会参考的评测提交文件为 `llama_bench_38t_ppl_with_baselines.lsf`，其主要配置与脚本行为如下：

| 配置项 | 脚本中的作用 | 正式规则 |
|---|---|---|
| `LLAMA_CPP_DIR` | 定位同一优化源码树中的 `build/bin/` | 路径由组委会部署，不是可替换模型或基准的通道 |
| `MODEL` | 4 分片 GGUF 中的第一个分片路径 | 模型内容、量化版本均固定 |
| `PPL_DATA` | WikiText-2 `wiki.test.raw` 路径 | 必须匹配第 4.3 节规定的 SHA-256 |
| `PPL_BASELINE_JSON` | 加载原始版本的 PPL 参考 JSON | 由组委会指定权威记录，须与第 6.1 节一致 |
| `RUN_BENCH` | `0` 只执行 PPL；`1` 执行 PPL 通过后的 PP/TG | **正式排名采用 `1`**，仅运行 PPL 不能获得综合性能分数 |
| `BASE_PP2048` / `BASE_TG128_D2048` | 将 PP/TG 结果转换为归一化分数 | 分别固定为 `46.929024`、`3.295524` |
| `PPL_MAX_REL_DIFF_PERCENT` | PPL 相对误差门槛 | **固定 0.5**，不允许参赛者修改 |

正式流程：**离线构建及目标检查 → PPL 正确性 PASS → PP2048 / TG128@D2048 → Score 和有效排名判定**。脚本会自动记录运行环境、PPL 结果与 PP/TG JSON；若 PPL 未通过，不再继续正式性能评分。执行方式与参考部署值见第 6.1 节和第 9 节。

---

## 5. 稳定性

变异系数定义为：

```text
CV = standard deviation / mean × 100%
```

建议：

```text
CV <= 2%
```

若正式结果明显高于该值，组委会可要求重新运行。

---

## 6. Baseline 与 Score

### 6.1 参考 Baseline

比赛参考 Baseline 由组委会在固定硬件上使用**未修改的官方 `llama.cpp v0.6.0`**产生。

Baseline 测试使用的软件环境为：

```bash
module load cmake/3.28.1
module load gcc/12.2.0
```

上述 GCC/CMake 版本仅用于说明参考 Baseline 的生成环境，**不作为参赛者的强制软件版本要求**。

Baseline 使用与正式评测完全相同的模型和 `llama-bench` 参数：

```text
1 CPU node
40 physical cores / 192 GB memory
38 llama-bench threads
PP2048 × 10
TG128@D2048 × 10
Batch = 2048
UBatch = 512
KV cache = f16/f16
NUMA = distribute
GPU layers = 0
```

组委会使用两份已确认的参考脚本：

1. `install_llama_cpp_cpu_ppl.lsf`：参考 `LLAMA_CPP_DIR=/work/ssc-202621/llama.cpp`，在计算节点**离线编译**本地源码。参考构建默认加载 `cmake/3.28.1`、`gcc/12.2.0`，使用 `Release`、`GGML_NATIVE=ON`、`GGML_OPENMP=ON`、`GGML_BLAS=OFF` 和 CPU-only 配置，并构建检查 `llama-cli`、`llama-server`、`llama-bench`、`llama-perplexity` 四个目标。上述 CMake 默认值用于复现参考环境；除 CPU-only、必须成功构建所需目标及其他明示限制外，参赛者允许优化编译参数、CPU 库和构建方式。
2. `llama_bench_38t_ppl_with_baselines.lsf`：参考相同源码树下的 `build/bin/llama-perplexity` 和 `build/bin/llama-bench`，先通过 PPL 正确性检查，再输出 `pp2048.json`、`tg128_d2048.json` 和标准化 Score；测试结果目录为提交作业目录下的 `llama_bench_results_<JOBID>/`。

参考安装脚本**不会自动 clone、checkout 或验证指定 Git 标签**：参赛者仍必须基于第 1 节规定的基础版本；组委会通过源代码及 Git 修订信息核查。两脚本中的 `/work/...` 路径是参考部署值，组委会负责提供统一可访问的模型、PPL 数据和基准文件。

正式成绩由组委会在受控环境下生成；参赛者不得直接修改官方评分逻辑。获准的运行时调优可通过组委会确认的配置接入正式评测。

本比赛采用以下参考 Baseline：

```text
PP_base  = 46.929024 tokens/s
TG_base  = 3.295524 tokens/s
PPL_base = 2.7696
```

原始性能参考的标准差和变异系数（用于稳定性参考，不参与评分）：

```text
PP2048:        stddev = 0.732771 tokens/s, CV = 1.56%
TG128 @ D2048: stddev = 0.005524 tokens/s, CV = 0.17%
```

**正式 PPL 参考记录及路径配置：**

原始基准结果记录所在路径：

```text
/work/ssc-202621/llama_bench_results_4335405/perplexity_result.json
```

而当前上传的 `llama_bench_38t_ppl_with_baselines.lsf` 中，`PPL_BASELINE_JSON` 的默认值为：

```text
/work/ssc-zhaojh/llama_model/unsloth/Qwen3.8-Flash-Next-GGUF/perplexity_result.json
```

**这两个路径不能仅凭文件名推断为相同记录。** 正式评测前，组委会必须核实所使用的参考 JSON 与确认的 PPL 基准内容一致，或者通过脚本的 `PPL_BASELINE_JSON` 配置指向受控的权威副本；参赛者不得提供或更换基准文件。该 JSON 使用 `llama_cpp_ppl_regression_v1` 格式，记录 `PPL_base = 2.7696`、PPL 固定参数、模型分片路径与大小、测试文本 SHA-256 及 `tolerance_percent = 0.5`。其中 `REFERENCE_RECORDED` 表示**成功记录基准**，并非参赛版本的 PASS。

现有比较脚本还会严格匹配 PPL 的**模型分片路径与文件大小**和数据集哈希；因此正式评测需要使用共同的模型挂载路径，不得仅以“模型内容看似相同”为由忽略路径差异。

该参考 Baseline 对应：

```text
Score = 100
```

### 6.2 参赛版本得分

定义：

```text
PP_team = 参赛版本 PP2048 average tokens/s
TG_team = 参赛版本 TG128@D2048 average tokens/s
```

最终性能分数：

```text
Score = 100 × sqrt(
    (PP_team / 46.929024)
    ×
    (TG_team / 3.295524)
)
```

等价地：

```text
Score = 100 × sqrt(
    (PP_team / PP_base)
    ×
    (TG_team / TG_base)
)
```

因此：

```text
Score = 100  与参考 Baseline 综合性能相当
Score > 100  表示综合性能提升
Score < 100  表示综合性能下降
```

上述公式仅用于 **PPL 正确性检验已通过**的参赛版本：`PP_base` 和 `TG_base` 用于归一化性能得分，`PPL_base` 仅用于正确性准入，**不纳入得分的加权或几何平均计算**。参赛者不得通过修改正式 workload、模型、PPL 输入或统计方式改变评分基准。

### 6.3 最终有效成绩（Correctness Gate + Performance Score）

```text
if (PPL_correctness == PASS
    and CPU_only == PASS
    and Official_model == PASS
    and Fixed_workload == PASS
    and Benchmark_completed == PASS):
    Final_Score = 100 × sqrt((PP_team / PP_base) × (TG_team / TG_base))
    Ranking_eligible = YES
else:
    Final_Score = INVALID  # 不产生有效排名分数；不等同于 0 分
    Ranking_eligible = NO
```

**正确性优先于性能**：未经 PPL 验证、PPL 超容差、PPL 结果无效或者正式性能测试不完整的提交，均不能凭借已观测到的部分速度结果进入排名。最终 Score 仍完全由 PP2048 和 TG128@D2048 两项性能构成。

---

## 7. 允许的优化

允许在不改变模型和 workload 的前提下进行：

- `llama.cpp / ggml` CPU 源码优化；
- SIMD / AVX2 / AVX-512 / VNNI 优化；
- quantized GEMM / GEMV / matvec 优化；
- MoE CPU kernel 优化；
- OpenMP 与线程同步优化；
- memory layout / cache / prefetch 优化；
- NUMA 与内存访问优化；
- compiler flags、LTO、PGO；
- BLAS / oneMKL 等 CPU 库；
- profiling 驱动的代码优化；
- Agent / Coding Agent / Skill 辅助优化。

正式评分时，**`llama-bench` 的线程数、Batch、UBatch、KV Cache 类型、PP/TG workload、重复次数，以及 `llama-perplexity` 的固定测试输入、参数和正确性阈值均不允许修改**。在这些不可变约束之外，符合下述条件的运行时优化同样属于本赛题鼓励的优化方向。

### 7.1 运行时参数调优（允许，须遵守固定约束）

本比赛**不要求所有队伍将 `llama.cpp` 的每个运行时选项都锁定为官方 Baseline 的默认值**。只要不改变固定硬件、线程总数、模型、PP/TG 测试负载、KV Cache 类型、PPL 正确性条件和计分方法，允许参赛者通过合法的运行时选项优化 CPU 性能。

| 分类 | 允许探索的方向和示例 | 适用边界 |
|---|---|---|
| CPU 亲和性及线程放置 | `-C / --cpu-mask`、`--cpu-strict`、`taskset`、线程绑定策略 | 仍为 38 个正式推理线程，全部在分配的 CPU 核心/作业 cpuset 内；不能借此增加可用算力 |
| NUMA / 内存放置 | 性能测试可尝试 `--numa distribute` / `isolate` / `numactl`，或等效的内存策略 | **性能 PP/TG 可申请调优**；PPL 的 `--numa distribute` 仍固定；不可使用其他节点内存或越过调度器分配 |
| 线程调度与等待策略 | `--poll`、普通用户有权限的 `--prio`、OpenMP 绑定/等待设置 | 不得增加推理线程数、申请超出普通作业权限的实时优先级或干扰其他作业 |
| CPU 数学库 / 运行时环境 | `OMP_PROC_BIND`、`OMP_PLACES`、兼容的 MKL/OpenBLAS/BLIS 绑定及库策略 | 以 38 线程上限及 CPU-only 为前提；禁止通过额外嵌套线程绕过线程限制 |
| 模型加载与内存管理 | 支持的 mmap、mlock、加载模式、内存预取/分配策略 | 仍须完整加载并执行正式 GGUF 模型；不得变更权重或使用额外计算设备 |
| CPU 内核执行策略 | 安全的 CPU tensor packing、repacking、算子调度、缓存与预取策略 | 不得跳过模型运算；涉及数值路径变化时须通过 PPL 并接受额外正确性核验 |

上述参数名均为**可能使用的选项示例，不是强制配置**。具体能否使用，以参赛源码版本实际提供的 `./build/bin/llama-bench --help`、`llama-perplexity --help` 和官方评测节点的权限为准。某些 `llama-cli` / `llama-server` 专用参数并非 `llama-bench` 支持项，不能直接用于正式性能评测。

**边界与执行规则：**

1. **固定 workload 优先**：不得通过设置其他参数间接改变 `PP2048`、`TG128@D2048`、38 线程、`-b 2048`、`-ub 512`、F16 KV Cache、10 次重复、`-ngl 0` 或正式模型。
2. **PPL 独立锁定**：PPL 仍按第 4.3 节的参考参数运行；任何会改变推理数值路径的新增模式不得只在 `llama-bench` 中启用、在正确性检查中规避；组委会可要求等效模式下的补充正确性检验。
3. **可区分 PP 与 TG 配置**：允许申报不同的合法执行策略以适应 Prefill 和 Decode，但必须提前披露、可复现，且两个 workload 都使用相同正式模型与优化版本，不得特判测试数据或伪造性能。
4. **当前脚本的实际限制**：所提供的 `llama_bench_38t_ppl_with_baselines.lsf` 目前直接写入 `--numa distribute`、`OMP_PROC_BIND=close`、`OMP_PLACES=cores` 等设置；**仅修改提交环境变量不一定能覆盖脚本内的显式参数或 `export`**。要在正式评分中使用不同的获准执行策略，须由组委会审核后通过受控脚本配置或等效评测封装来传入，同时锁定所有不可变参数，保存最终有效命令与环境；参赛者不得私自替换组委会的正式测试入口。
5. **提交声明**：采用运行时调优的队伍应在 `runtime_config.md` 中逐项记录 PP、TG 的附加参数与相关环境变量、支持的 llama.cpp 构建版本、硬件资源使用边界及可重复运行方法；没有申报的参数按参考脚本默认配置执行。

### 7.2 Agentic / Coding Agent / Skill 辅助优化（鼓励）

本赛题鼓励参赛者使用 Agent、Coding Agent、Skill 或自建 Agent workflow 辅助性能优化。工具不作强制限定，重点是形成可重复的性能优化闭环：

```text
Profile / Benchmark
        ↓
Agent 分析热点与瓶颈
        ↓
提出优化方案
        ↓
修改代码 / 编译参数
        ↓
Build
        ↓
llama-perplexity（正确性 PASS？）
        ├─ FAIL → 回退 / 修复
        ↓ PASS
llama-bench
        ↓
计算 Score / 对比历史结果
        ↓
保留有效优化或回退，继续迭代
```

#### A. 通用 Coding Agent / Agent Workflow

| 项目 | GitHub | 用途 |
|---|---|---|
| OpenAI Codex | https://github.com/openai/codex | 终端 Coding Agent，可直接分析、修改、构建和测试 `llama.cpp` |
| OpenHands | https://github.com/OpenHands/OpenHands | 软件工程 Agent 平台，可执行代码修改、Shell、Build 和测试 |
| mini-SWE-agent / SWE-agent | https://github.com/SWE-agent/mini-swe-agent / https://github.com/SWE-agent/SWE-agent | 面向真实代码仓库的自动修改与验证，可参考构建 optimization agent |
| Aider | https://github.com/Aider-AI/aider | Terminal AI pair programming，适合大型 C/C++ 代码库交互式优化 |
| goose | https://github.com/aaif-goose/goose | 本地可扩展 Agent，支持 CLI/MCP，可连接 benchmark、profiling 等工具 |
| OpenCode | https://github.com/anomalyco/opencode | 开源 Coding Agent，适合代码探索、计划和实现 |
| humanize | https://github.com/humanfia/humanize | Coding Agent flow/harness，可用于组织多轮优化工作流 |
| AI-Infra-Auto-Driven-SKILLS | https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS | AI Infra benchmark/profiling/优化 Skill 集合，可参考 Skill 的设计与自动优化流程 |
| NVIDIA KDA | https://github.com/NVlabs/kda | Kernel Design Agent；主要针对 CUDA，但其“研究→实现→验证→性能迭代”模式可作为 CPU kernel agent 的方法论参考 |

#### B. CPU / HPC 性能分析与优化 Skill

以下项目对本赛题的 CPU 优化更加直接：

| 项目 | GitHub | 与本赛题的关系 |
|---|---|---|
| **Intel Performance Skills** | https://github.com/intel/intel-performance-skills | **优先推荐**。面向 x86 Linux 的 AI Agent CPU 性能 Skill，包括 Linux `perf`、性能反模式、false sharing、core scaling 等，特别适合本赛题 Intel Xeon 平台 |
| perf-labs/perf | https://github.com/perf-labs/perf | 面向 Human–Agent performance engineering，支持硬件性能计数器、机器码分析、benchmark 和优化闭环；需检查 HPC 内核及 PMU 权限 |
| Linux Perf Skills | https://github.com/caomengxuan666/perf-skills | 给 Claude/OpenCode/Cursor 等 Agent 使用的 Linux `perf` Skill，覆盖 hotspot、syscall、before/after 对比等流程 |
| perf-benchmark-skill | https://github.com/jc1122/perf-benchmark-skill | Linux CPU/cache/branch/memory/ASM benchmark Skill，可用于辅助判断算法、cache 和汇编层瓶颈 |
| Performance Hints Agent Skills | https://github.com/boshjerns/performance-hints-agent-skills | 将通用性能工程经验组织成 Agent Skills，可作为代码审查和优化建议 Skill |
| Intel `vllm-xeon-cpu` Skill | https://github.com/intel/optimization-zone/tree/main/software/vllm | 虽然目标框架是 vLLM，而非 `llama.cpp`，但其中 Xeon CPU、NUMA、OpenMP、benchmark Agent Skill 的组织方式值得参考 |
| OpenTuner | https://github.com/jansel/opentuner | 程序自动调优框架，可用于搜索 compiler flags、block size、线程/参数组合；适合作为 Agent 自动参数搜索组件 |
| CompilerGym | https://github.com/facebookresearch/CompilerGym | 面向 compiler optimization agent/RL 的研究框架；项目已归档，但仍可作为编译优化 Agent 的研究参考 |

对于本赛题的 Intel Xeon CPU，推荐优先组合：

```text
Coding Agent
    +
Intel Performance Skills / Linux perf Skill
    +
perf / VTune / PMU 数据
    +
llama-perplexity（PPL correctness gate）
    +
llama-bench
    +
Score
```

例如：

```text
llama-bench 得到 baseline
        ↓
perf stat / perf record
        ↓
Agent + linux-perf Skill 分析
        ↓
定位热点：
  quantized GEMM / GEMV
  MoE dispatch / expert
  AVX2 / AVX-512
  cache miss
  memory bandwidth
  false sharing
  NUMA remote access
        ↓
Coding Agent 修改 ggml / llama.cpp
        ↓
重新编译
        ↓
llama-perplexity：PPL PASS？
    ├─ No → rollback / 修复
    └─ Yes → llama-bench
        ↓
Score 提升？
   ├─ Yes → 保存 commit
   └─ No  → rollback
```

HPC 系统可能限制 `perf_event_paranoid`、PMU、eBPF 或 root 权限，因此上述 CPU profiling Skill 是否可直接运行取决于比赛平台权限。即使无法使用完整硬件计数器，这些 Skill 的分析流程仍可作为参考。

建议 `agent_usage.md` 简要记录：

```text
使用的 Agent / Coding Agent / Skill
使用的模型（如适用）
Agent 在优化中的主要任务
采用的 profiling / benchmark 信息
主要优化迭代及最终有效修改
```
---

## 8. 禁止事项

正式评测禁止：

- 修改 `llama-bench` 的计时或 tokens/s 统计逻辑；
- 修改 PP/TG token 数量或 context depth；
- 修改正式模型或量化版本；
- 跳过模型应执行的计算；
- hard-code benchmark 结果；
- 使用缓存或预计算伪造性能；
- 使用 GPU、NPU、FPGA 或其他加速器；
- 篡改 JSON 结果；
- 修改 `llama-perplexity` 的 PPL 计算逻辑、结果输出或正确性判断逻辑以绕过真实模型计算；
- 修改正式 PPL 数据集内容、截断计分范围、固定参数、参考 PPL 或 `0.5%` 容差；
- 直接硬编码 PPL 结果、伪造 `perplexity_result.json`，或通过缓存、预计算绕过真实 PPL 评估；
- 为不同队伍使用不同硬件、PPL 输入或**固定** benchmark 工作负载与核心参数；
- 以“运行时优化”为由增加线程数、更改 KV Cache、改变 token 数、修改模型计算图语义或规避 PPL 正确性检查；
- 未经申报/审核擅自更改官方正式评测入口，或利用脚本环境、输出格式、计分解析漏洞获得不公平成绩。

第 7.1 节允许的 CPU 亲和性、NUMA、内存及调度等策略调整**不属于上述禁止的固定 benchmark 参数变更**，但须由组委会按统一流程接入并核验。

组委会将执行第 4.3 节规定的 **PPL 强制正确性检查**，并可进行源码审查、算子核对和额外 correctness spot-check。任何一项正式正确性检查未通过的成绩均无效。

---

## 9. 提交内容

建议每支队伍提交：

```text
submission/
├── source/ 或 optimization.patch
├── build.sh              # 可复现离线 CPU 构建（或等效明确的构建说明）
├── README.md
├── runtime_config.md     # 如使用第 7.1 节允许的运行时调优
└── agent_usage.md        # 如使用 Agent/Skill
```

`build.sh`（或经组委会认可的等效离线构建说明）必须能在官方 CPU 节点使用提供的离线源码成功生成以下**正式必需**目标：

```text
build/bin/llama-bench
build/bin/llama-perplexity
```

参考安装脚本 `install_llama_cpp_cpu_ppl.lsf` 还会生成并验证 `build/bin/llama-cli` 和 `build/bin/llama-server`；**这是参考安装流程的构建验证内容，不表示评分改用 `llama-server`**。安装脚本使用统一源码路径 `LLAMA_CPP_DIR` 推导构建路径，在本地源码上构建并检查二进制及动态库依赖。参赛者可优化源码、编译器、构建参数和 CPU 库，但必须保证统一环境下可离线构建、CPU-only，且正式评测二进制来自同一提交版本。

正式评测使用 `llama_bench_38t_ppl_with_baselines.lsf`（或保留固定约束的组委会等效封装）执行 **PPL → PP/TG** 流程，并至少保留：

```text
llama_bench_results_<JOBID>/
├── environment.txt
├── perplexity.log
├── perplexity_result.json
├── pp2048.json
└── tg128_d2048.json
```

允许申请第 7.1 节的性能运行时调优时，应由组委会记录两项 benchmark 各自的实际完整命令、有效环境变量及参赛版本标识，便于审计与复现。**参考脚本的 `LLAMA_CPP_DIR`、`MODEL`、`PPL_DATA`、`PPL_BASELINE_JSON` 是部署路径配置，不属于可修改的测试内容或评分基准。** 正式脚本、模型和数据、资源分配、固定 workload、PPL 基准和 Score 计算始终由组委会控制。

---

## 10. 正式排名

参赛版本首先必须满足：

```text
CPU-only                   = PASS
Official model             = PASS
Fixed PP/TG/PPL workload   = PASS
Runtime options compliant  = PASS
PPL correctness (±0.5%)   = PASS
Additional correctness    = PASS（如组委会要求）
Benchmark completed        = PASS
```

**只有上述条件全部满足时**，才按照第 6 节定义的有效 `Score` 从高到低排名。PPL `FAIL`、`ERROR` 或 `INVALID` 的参赛版本列为“未通过正确性/不参与排名”，不能用速度提升抵消。

同时公布：

```text
Reference PPL = 2.7696
Team PPL
PPL relative difference (%)
PPL correctness status (PASS / FAIL / ERROR / INVALID)
PP2048 tokens/s
TG128@D2048 tokens/s
PP CV
TG CV
Approved PP/TG runtime configuration（如适用）
Final Score（仅通过正确性门槛者有效）
```

