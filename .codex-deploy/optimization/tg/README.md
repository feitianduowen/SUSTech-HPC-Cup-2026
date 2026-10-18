# TG Q8_0 AVX2 candidates

本目录只生成独立候选和单线程诊断，不修改已通过 PPL 的生产源码或模型。没有正式性能结论；需要父任务在 Gold 6148 上用 Intel icc 编译、运行固定 38 线程 PP/TG 并验 PPL。

| 补丁 | 主循环 | 浮点次序 | 优先级 |
| --- | --- | --- | --- |
| `q8-u2.patch` | 展开 2 个 block，预先计算 scale 和整数点积 | 同一 acc，FMA 按原 block 顺序，原 hsum | 先测 |
| `q8-u4.patch` | 展开 4 个 block | 同上；寄存器压力可能更大 | 第二个 |
| `q8-a2.patch` | 2 个独立 acc，合并后处理 tail | 改变累加顺序 | microbench 有收益才测模型 |
| `q8-a4.patch` | 4 个独立 acc，树形合并后处理 tail | 改变累加顺序 | 同上 |

四份补丁都针对未修改的 `ggml/src/ggml-cpu/arch/x86/quants.c` 独立应用，不能叠加。仅 AVX2 分支改变；AVX 和 scalar 分支不变。不引入 VNNI、预取或 block 格式改变。尾块条件 `ib + width - 1 < nb` 保证整组有效，剩余 0..width-1 个块走原 FMA；n 是 int 且 nb=n/32，因此此处索引加法不会逼近 INT_MAX。

u2/u4 的数学数据流保持每 lane FMA 和最后 hsum 次序，有限有效 Q8 输入应 bitwise 相等。编译器实际生成的结果仍必须检验。a2/a4 的 FP32 舍入会变；本诊断记录相对于 baseline 的绝对/相对/RMS 误差与 double 参考误差，不把一个宽松数值阈值当作模型 PPL 合格。

## 生成、编译与运行

在计算节点上 source 账户的 `scripts/env.sh`。将本目录放到独立实验目录，执行以下命令。不要在登录节点执行性能工作。

```sh
python3 make_q8_candidates.py /work/apac2602/qwen38-cpu/llama.cpp/ggml/src/ggml-cpu/arch/x86/quants.c --out .
icc -gcc-name=/share/base/e5/gcc/11.2.0/bin/gcc \
    -std=gnu11 -O3 -g -fp-model precise -no-ftz -xCORE-AVX512 \
    -qsimd-honor-fp-model -diag-disable=10441 \
    q8-microbench.c -ldl -Wl,--no-as-needed,/lib64/libm.so.6,--as-needed \
    -o q8-microbench
export LD_LIBRARY_PATH=/work/apac2602/qwen38-cpu/llama.cpp/build/bin:$LD_LIBRARY_PATH
numactl --physcpubind=0 --membind=0 ./q8-microbench \
    /work/apac2602/qwen38-cpu/llama.cpp/build/bin/libggml-cpu.so 128 256 \
    > q8-nb128.csv 2> q8-nb128.log
python3 analyze_q8.py q8-nb128.csv > q8-nb128-summary.json
```

CPU 0 仅为示例，应选择本次 LSF 分配允许使用的单个物理核，并记录 CPU/NUMA 位置。每个 nb 需要单独运行，建议 `32, 64, 128, 256, 512`，分别对应 1024..16384 个元素；具体模型矩阵行长应从模型 tensor 元数据核实。命令中第一个参数 `-` 可以跳过生产符号比较，但首次筛选应传入未改动的已验收 `libggml-cpu.so`。加载生产库后，harness 必须解析并调用 `ggml_cpu_init()`，填充 FP16 转换表和初始化 ggml time，再做真实符号比较；找不到初始化符号就报错退出。

`q8-kernels.c` 使用从同一原始源码提取的助手、baseline 和候选；唯一独立适配是 Q8_0 ABI 声明与有限 half 的 F16C 转换。无需手工链接 shared ggml CPU 符号；可选 `dlopen` 比较真实库导出的 `ggml_vec_dot_q8_0_q8_0`。原始 `ggml-cpu.c` 的 `ggml_cpu_init()` 会填充 `ggml_table_f32_f16`，harness 在调用真实函数前执行该初始化。当前源的 `GGML_CPU_FP16_TO_FP32` 实际实现必须与 F16C 的有限 half 转换一致；如果不一致，生产对照会失败。生成时的源 SHA256 记录于 `candidate_manifest.json`。

## 覆盖与结果解释

- 1392 个正确性用例：29 个 nb，包括 0/1、奇数、u2/u4 主循环和 tail、4096；6 种字节/scale 模式，各 8 次固定种子随机重复。Q8 字节限制在 -127..127，覆盖零、稠密、极值、稀疏、块间抵消和有符号有限 scale。
- `baseline/u2/u4` 应 bitwise 一致。生产真实符号与独立 baseline 也要求 bitwise 一致。a2/a4 允许有限差异但报告全部误差，任何非有限输出都失败。相对误差对接近零的 dot 可很大，应结合绝对误差与 double 参考解释。
- resident 反复读取一行 x 和同一 y；默认 nb128 共约 8.5 KiB。stream 顺序遍历默认 256 MiB x，重复使用一个 y，模拟权重流式读取和激活复用。分配/填充不计入计时。5 轮轮换候选顺序，保留每轮原值和中位数，不设置脆弱的时间断言。
- `weight_GB_s` 是 x 字节数/墙钟时间的推算值，不是测得的 DRAM 带宽；resident 数值可能很高。该 harness 是单线程 kernel 诊断，不能替代 38 线程模型 bench，也不能证明模型端到端收益。
- 检查 Intel 反汇编是否有 spills、是否仍为 AVX2 maddubs/madd 路径、FMA 是否保序。微基准有收益且保序通过后，再在独立 build 里应用一个补丁并跑固定模型 bench/PPL。

```sh
objdump -d -Mintel q8-microbench > q8-microbench.disassembly.txt
git -C /path/to/independent/llama.cpp apply --check /path/to/q8-u2.patch
git -C /path/to/independent/llama.cpp apply /path/to/q8-u2.patch
```

## 已做的检查与审阅

已在本地用 `git apply --check` 验证四份独立补丁均能应用，生成 kernel 经 MinGW GCC 的 `-mavx2 -mfma -mf16c -Wall -Wextra -Werror` 汇编通过。此检查不代表 Intel Linux 正确性或速度。

按仓库 code-review skill 做 Scope/Security/General/ggml backend 自审：仅改一个现有 CPU kernel 的循环；没有 public API、模型格式、其他 backend、源数据布局或第三方依赖变化；新文件都留在私有诊断目录。无新 op，因此无需 ops 文档更动。模型 PPL、真实 kernel 对照及 Intel 性能数据仍待远端执行，未作合格或加速声称。没有 commit、push 或上游 PR。
