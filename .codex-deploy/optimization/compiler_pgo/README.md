# Intel Classic O3 / O2 PGO 实验

日期：2026-10-19，香港时间。远端目录 `/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo`。

最新重提：2026-10-19 10:40，O3 **4336626（r13n05）**、O2 **4336627（r13n45）**，10:41 查询均为 RUN、单节点 40 slots；尚待构建/训练/独立 PPL 验证。此前配额拒绝属于历史记录。后续 heartbeat 必须先检查这两个作业，不能再次重复提交。

题目第 2 节允许自选编译器，第 7 节明确允许 compiler flags / PGO。所有候选仍使用 Intel Classic 2021.9 icc/icpc，CPU-only、precise/no-ftz/CORE-AVX512/qsimd-honor-fp-model、OpenMP ON、BLAS OFF。未启用此前失败的 `-ipo`。

O3 与 O2 各自有独立无 PGO control、threadsafe 计数构建、反馈优化构建。合成训练为 PP1024、TG32@D512，各 1 次、38 线程，训练仅产生编译器执行计数，不读取 WikiText，不保存/复用模型答案，不作为正式测速。每个最终构建独立通过固定 PPL 后，才进行固定 PP2048 与 TG128@D2048、各 10 次的开发自测。

## 当前证据

- `4336529`：O3 初次提交，r13n28，10:18:37 提交、10:18:39 退出；计算节点缺少 git，在 INIT 源码检查前失败，尚未编译/加载模型。
- `4336530`：O2 初次提交，r13n33，10:18:37 提交、10:18:41 退出，同一原因。失败作业保留在主 Excel。
- 已修复：登录节点用 git 确认官方 commit `d81235049384534c167caea52b85a694f6103d14` 且 tracked diff 为空，保存 3,687 个 tracked 文件的 SHA256。计算节点用 `verify_source.py` 校验全部文件，无须安装 git。`source_identity.json` 保留本地和远端。
- 重提时遇到 LSF 准入限制：`Group <u-ssc>: Pending job slots threshold reached. Retrying in 60 seconds...`；O3、O2 均重试五次后返回 255，`User permission denied. Job not submitted.`，分别于 10:27:03、10:32:22 返回，没有生成新作业号；两个提交客户端都已退出。两条拒绝原文保存在 submission_registry.jsonl 和 Excel“提交拒绝”页。
- 10:29 左右查询显示组 PEND=3013 slots、MPEND=3000，当前账户 NJOBS=0；这属于组级提交限制，不能靠换 r13n 节点消除。查询仍可见空闲同配置节点，未尝试绕过调度器或缩减规定的 40 slots。

## 下一次 heartbeat

1. 检查 `results/submission_registry.jsonl` 末尾以及 `bjobs -w`，确认所有重提客户端是否已返回；不要根据 SSH 通道超时猜测提交失败，也不要重复提交未返回的请求。
2. 若有新作业号，立即 `collect_job_registry.py` → 下载 JSON → 本地 `write_excel_log.py` 更新 Excel，保留失败和拒绝页。若无作业号的拒绝已完成，则查看 `busers -w apac2602 u-ssc`，组配额允许时使用 `retry_O3.json` / `retry_O2.json` 通过 `submit_logged.py` 重提。
3. 用 `hg_6148` 自动选择符合配置的空闲 r13n 节点，不绑定繁忙节点。每个 job 单节点 40 slots，推理 38 线程。
4. 作业 `job.status` 若 READY，检查 manifest、固定 PPL、profile 计数和反馈构建 warning；热点计数有效后运行 `prepare_paired_specs.py <parent_job_id>`，生成正反序完整对照的 spec，仍通过统一登记器提交。
5. 作业失败先定位阶段，修复实际问题；若固定 PPL 不通过则停止该产物测速，不能改固定 PPL 条件强行通过。

`paired_bench.lsf` 在同一节点先后运行 control/pgo，每个构建独立固定 PPL。正反顺序使用不同节点，仍需明确节点、缓存和顺序影响。所有结果都是开发自测，尚无 PGO 性能收益结论。现有生产部署未替换。
