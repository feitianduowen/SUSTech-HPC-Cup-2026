最新进展（2026-10-19T16:42:19.041976+08:00）：4337257与4337427均训练超时；4337488（r13n38）和4337448（r13n24）正在验证各3600秒合成训练。见 [PGO_DRIVER_LONG_TRAIN_NOTES.md](PGO_DRIVER_LONG_TRAIN_NOTES.md) 与next_actions.json。PGO最终PPL和完整性能尚待验证。

以下为历史阶段记录。

最新进展（2026-10-19 15:47 香港）：4336889、4337216、4337222已失败；4337425链接诊断完成；4337427和4337257运行中。当前配置、失败原因及PPL复用口径见 [PGO_DRIVER_NOTES.md](PGO_DRIVER_NOTES.md) 与 next_actions.json。尚无PGO最终PPL或性能结论。

以下为15:34及之前的历史记录，旧的运行状态及下一步段落不代表当前状态。

# Intel Classic O3 / O2 PGO 实验

日期：2026-10-19，香港时间。远端目录 `/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo`。

最新验证：**4336889 已在 BUILD_GEN 链接阶段退出**，libipgo.a 引用 `__start___pgoseg_addr`，链接器报 `DSO missing from command line`，尚未训练。control 固定 PPL 已通过。

15:26 **4337216（r13n10）** 在验证全部非 GGML 目标（包括静态/对象库及main）的编译和链接均关闭PGO。15:30 **4337222（r13n11）** 验证另一策略：GGML与薄 `llama-bench/main.cpp` 保留PGO，递归关闭其余冷目标的编译及链接插桩。4337222先执行的 main→cold共享库→hot共享库探针已正常链接、退出并产生2个非空dyn；探针计数与模型训练目录分开。两项均待完整模型训练与最终PPL，未认定PGO成功。

4337222 在 gen 开始前扩展了冷目标递归规则，避免遗漏 `llama-common-base` 等静态依赖；普通control编译参数不受影响。初始CMake文件保留为 `ggml_pgo_driver.initial.cmake`，修改时间、阶段、旧/新SHA256及原因保存在 `configuration_amendment.json`，gen/use实际配置保存在compile_commands及scope JSON。正式PPL和测速参数均未改变。

10:40 的历史重提 4336626/4336627 均已 EXIT：各自无 PGO control 固定 PPL=2.7767 PASS（240s/246s），但合成 PP1024 训练900s超时，未生成 PGO 产物。随后 4336716 改为 PP64，仍1200s超时；详细日志停在 `init_tokenizer`，OS观察为单线程约200MB RSS、CPU约1015秒，尚未进入模型计算。周期计数已保存，但这些失败训练计数只用于诊断，未拿来反馈编译。仅缩短训练 tokens 不足以解决初始化插桩开销，因此调整插桩范围。

PGO 周期计数环境变量依据 [Intel Compiler Classic说明](https://www.intel.com/content/dam/develop/external/us/en/documents/cpp_compiler_classic.pdf)。工作簿的旧 control PPL PASS 不能理解为 PGO 产物已通过。

题目第 2 节允许自选编译器，第 7 节明确允许 compiler flags / PGO。所有候选仍使用 Intel Classic 2021.9 icc/icpc，CPU-only、precise/no-ftz/CORE-AVX512/qsimd-honor-fp-model、OpenMP ON、BLAS OFF。未启用此前失败的 `-ipo`。

O3 与 O2 各自有独立无 PGO control、threadsafe 计数构建、反馈优化构建。合成训练为 PP1024、TG32@D512，各 1 次、38 线程，训练仅产生编译器执行计数，不读取 WikiText，不保存/复用模型答案，不作为正式测速。每个最终构建独立通过固定 PPL 后，才进行固定 PP2048 与 TG128@D2048、各 10 次的开发自测。

## 当前证据

- `4336529`：O3 初次提交，r13n28，10:18:37 提交、10:18:39 退出；计算节点缺少 git，在 INIT 源码检查前失败，尚未编译/加载模型。
- `4336530`：O2 初次提交，r13n33，10:18:37 提交、10:18:41 退出，同一原因。失败作业保留在主 Excel。
- 已修复：登录节点用 git 确认官方 commit `d81235049384534c167caea52b85a694f6103d14` 且 tracked diff 为空，保存 3,687 个 tracked 文件的 SHA256。计算节点用 `verify_source.py` 校验全部文件，无须安装 git。`source_identity.json` 保留本地和远端。
- 重提时遇到 LSF 准入限制：`Group <u-ssc>: Pending job slots threshold reached. Retrying in 60 seconds...`；O3、O2 均重试五次后返回 255，`User permission denied. Job not submitted.`，分别于 10:27:03、10:32:22 返回，没有生成新作业号；两个提交客户端都已退出。两条拒绝原文保存在 submission_registry.jsonl 和 Excel“提交拒绝”页。
- 10:29 左右查询显示组 PEND=3013 slots、MPEND=3000，当前账户 NJOBS=0；这属于组级提交限制，不能靠换 r13n 节点消除。查询仍可见空闲同配置节点，未尝试绕过调度器或缩减规定的 40 slots。

## 下一次 heartbeat

1. 优先检查 **4337216 和 4337222** 的状态、`gen-build/pgo-scope.json`、训练日志和 `training-validation.json`；正在 RUN/PEND 不得重复提交。旧 `retry_O3/O2.json`、`short_O3/O2.json`、`ggml_only_O3.json` 仅保留历史，不再原样重复提交。
2. 新作业号立即采集 → 下载 JSON → 本地 `write_excel_log.py` 更新 Excel，保留失败和拒绝页。公共采集卡在历史文件时，可用独立限定采集写 `pgo_scoped_snapshot.json`，下载到 `evidence/job_updates/`，写入器合并时保留其他行。O3训练及反馈流程正常完成后，再提交成功策略对应的O2；driver方案预备了 `driver_O2.json`。
3. 用 `hg_6148` 自动选择符合配置的空闲 r13n 节点，不绑定繁忙节点。每个 job 单节点 40 slots，推理 38 线程。
4. 作业 `job.status` 若 READY，检查 manifest、固定 PPL、profile 计数和反馈构建 warning；热点计数有效后运行 `prepare_paired_specs.py <parent_job_id>`，生成正反序完整对照的 spec，仍通过统一登记器提交。
5. 作业失败先定位阶段，修复实际问题；若固定 PPL 不通过则停止该产物测速，不能改固定 PPL 条件强行通过。

`paired_bench.lsf` 在同一节点先后运行 control/pgo，每个构建独立固定 PPL。正反顺序使用不同节点，仍需明确节点、缓存和顺序影响。所有结果都是开发自测，尚无 PGO 性能收益结论。现有生产部署未替换。
