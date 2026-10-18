# Qwen3.8-Flash-Next CPU 部署

部署目录：`/work/apac2602/qwen38-cpu`

源码：官方提供的 llama.cpp `v0.6.0`，commit `d81235049384534c167caea52b85a694f6103d14`。独立复制到本账户，未修改模型计算代码。

模型：`unsloth/Qwen3.8-Flash-Next-GGUF / UD-Q4_K_XL`，4 个分片，复用组委会共享文件。`models/UD-Q4_K_XL` 为便于浏览的符号链接；运行参数直接使用官方绝对路径，以保持 PPL 基准的路径一致性。

环境：Intel Classic 2021.9（oneAPI 2023.1，icc/icpc）、CMake 3.28.1。GCC 11.2.0 提供标准头文件和 C++ 标准库支持；全部本项目 C/C++ 源文件由 Intel 编译。Release，精确浮点模式，显式保留非规格化数，AVX-512，Intel OpenMP；基础数学函数优先链接与参考构建相同的系统 libm。BLAS 和 GPU 后端关闭。在 Xeon Gold 6148 计算节点构建。

## 本次验证结果

验证作业 `4335636` 已于 2026-10-18 21:26（香港时间）完成，节点为 `r13n16`，状态 `READY`。

- 固定参数 PPL：**2.7767，PASS**。
- 相对参考基准 2.7696 的偏差：**+0.2563547083%**，符合 0.5% 容差。
- PPL 用时：277 秒。
- `/health` 返回 `ok`；普通文本生成通过。
- `/v1/chat/completions` 实际请求通过，返回 `OK`。
- 4 个模型分片及 WikiText 测试文件检查通过。

接口服务按需由 LSF 启动，使用下方启动命令。完整 PP/TG 性能评测尚未运行，可使用已适配的原文件名脚本提交。

## 查看部署结果

```bash
cd /work/apac2602/qwen38-cpu
cat deployment.status
cat deployment_manifest.json
cat logs/assets.json
cat llama_bench_results_4335636/perplexity_result.json
cat logs/server_smoke_result.json
```

`READY` 只会在构建检查、真实 PPL 回归验证和服务器生成测试全部成功后写入。服务器测试完成后自动释放进程和计算资源。

## 使用环境

```bash
source /work/apac2602/qwen38-cpu/scripts/env.sh
```

模型加载、编译和推理必须在调度器分配的计算节点运行。此部署不修改账户现有 `.bashrc` 或其他项目环境。

## 生成文本

在登录节点提交：

```bash
cd /work/apac2602/qwen38-cpu
PROMPT='用中文简单介绍一下你自己。' bsub < scripts/cli.lsf
bjobs -w
```

输出在 `logs/<JOBID>.cli.out`；运行日志在 `logs/<JOBID>.cli.err`。

## 启动接口服务

```bash
cd /work/apac2602/qwen38-cpu
bsub < scripts/server.lsf
bjobs -w
```

服务在调度到的计算节点监听 `127.0.0.1:18080`，单个作业最长 4 小时；以 `bkill <JOBID>` 停止。节点名和日志位于 `logs/<JOBID>.server.out`、`logs/<JOBID>.server.err`。

在该计算节点检查并调用：

```bash
curl http://127.0.0.1:18080/health
curl http://127.0.0.1:18080/v1/models
curl http://127.0.0.1:18080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"/work/ssc-zhaojh/llama_model/unsloth/Qwen3.8-Flash-Next-GGUF/UD-Q4_K_XL/Qwen3.8-Flash-Next-UD-Q4_K_XL-00001-of-00004.gguf","messages":[{"role":"user","content":"你好"}],"max_tokens":128}'
```

如本机需要调用，可建立两段 SSH 转发：先在登录节点运行 `ssh -N -L 127.0.0.1:18081:127.0.0.1:18080 apac2602@<计算节点名>`；保持连接，再在本机运行 `ssh -N -L 127.0.0.1:18080:127.0.0.1:18081 -p 18188 apac2602@172.18.6.10`。随后访问本机 `http://127.0.0.1:18080`。计算节点 SSH 访问以集群允许的方式及作业权限为准。

## 正确性与完整性能测试

仅 PPL 回归：

```bash
cd /work/apac2602/qwen38-cpu
RUN_BENCH=0 bsub < llama_bench_38t_ppl_with_baselines.lsf
```

开发自测 PPL + PP2048 + TG128@D2048：

```bash
cd /work/apac2602/qwen38-cpu
bsub < llama_bench_38t_ppl_with_baselines.lsf
```

`scripts/benchmark.lsf` 来自组委会参考脚本，保留 PPL、PP/TG 固定参数及评分逻辑，仅调整本账户源码路径、日志位置、节点选择与作业时限。正式成绩仍由组委会受控评测产生。

PPL 基准为 2.7696，容差 0.5%，合格区间 `[2.755752, 2.783448]`。四个模型分片、WikiText SHA-256、运行参数与官方参考 JSON 均须一致。PPL 未通过时不执行后续性能测试。

## 重新编译

```bash
cd /work/apac2602/qwen38-cpu
bsub < install_llama_cpp_cpu_ppl.lsf
```

重跑完整部署验证：`bsub < scripts/bootstrap.lsf`。脚本保留已有构建目录进行增量编译。所有作业使用 `ssc-cpu` 队列、`hg_6148` 节点组、单节点 40 个槽；推理固定 38 线程。队列不接受 `-x`，因此通过申请该 40 槽节点的全部槽位取得单节点资源。

原始参考脚本保存于 `reference/`，构建日志保存于 `llama.cpp/build_logs/<JOBID>/`，PPL 和性能结果保存于提交目录的 `llama_bench_results_<JOBID>/`。

你提供的两个原始 LSF 文件与服务器参考副本逐字节相同。部署目录根部保留了原文件名入口，分别链接到适配后的构建及评测脚本。

## Profiling

作业 4335666 已完成两个固定负载各 10 次的 VTune 硬件事件采样。分析见 [Profiling 报告](D:/compete/Qwen38_CPU_Profiling报告.md)。原始采样位于服务器 `profiling/results_4335666/{pp2048,tg128_d2048}/vtune/`；文本、CSV、JSON 与复现脚本打包在该结果目录的 `reports.zip`。这些采样速度用于诊断，不是正式评分成绩。
