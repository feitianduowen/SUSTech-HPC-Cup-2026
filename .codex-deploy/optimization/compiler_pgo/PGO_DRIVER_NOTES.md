# Intel PGO 入口与共享库链接试验（2026-10-19，香港时间）

当前并行作业：4337427（r13n16，薄main保留插桩、gen保留DSO依赖）和4337257（r13n12，递归关闭全部非GGML目标插桩）。O2等待完整O3流程通过。

4337222在r13n11于15:40:36退出，失败阶段BUILD_GEN。control固定PPL=2.7767 PASS，但PGO版本未训练、未校验，无完整PP/TG或Score。先前小型共享库探针虽通过，未复现真实链接命令的--as-needed行为，不能据此认定完整修复成功。冷模块递归规则、UTILITY跳过和全局PGO链接选项去重在BUILD_GEN前生效；BUILD_GEN开始后追加最后链接项的修改被阶段保护拒绝，未改动该作业有效CMake文件。初始文件及已生效修改时间、阶段、SHA保留在原结果目录。

4337425（r13n20，15:43提交）用4337222真实已编译对象，仅链接到新目录，不执行、不加载模型、不修改旧构建或计数。同作业内按original→no_as_needed→shared_intel顺序：原命令失败rc1；在对象及依赖前追加-Wl,--no-as-needed成功rc0；追加-shared-intel失败rc1。这只验证链接，尚不证明运行、计数或PPL正确。Excel运行结果逐项保留三种配置。

4337427通过pipeline_driver_no_as_needed.lsf验证完整流程。Intel Classic2021.9 icc/icpc、O3、precise/no-ftz/CORE-AVX512/qsimd-honor-fp-model、CPU-only、OpenMP ON、BLAS OFF、40 slots/38推理线程；未启用IPO；官方原始源码和模型不改。gen全局EXE/SHARED链接选项去除重复PGO选项，并在原libm选项后追加-Wl,--no-as-needed。GGML及薄main保留-prof-gen=threadsafe，其余目标递归追加-no-prof-gen；反馈构建对应-prof-use=nomerge/-no-prof-use。构建前后检查实际编译及链接参数；预检通过：28个GGML编译单元、1个薄入口、103个冷目标链接。helper/checker分别命名，避免影响其他活跃作业。

control只读复用4337222：核验四工具及动态库SHA和固定PPL条件，PPL=2.7767 PASS，不重建或重跑control。新PGO产物仍须独立固定PPL：t/tb38,c512,chunks2,b512,ub256,KVf16,ngl0,NUMA distribute,no-warmup,590s。训练仅合成PP64/TG8@D64各r1，正常退出且参数校验通过才合并计数。60秒周期保存的失败计数只作诊断。训练不读取WikiText、不计分。完整PP2048/TG128@D2048各10次测速待后续成对作业。

4337257独立复用4337216的SHA核验control及PPL；本轮未改其脚本或构建。15:47仍TRAIN_PP_UNSCORED，已越过tokenizer初始化并进入模型权重repack。仅阶段进展，不认定PGO成功。

4336889是链接失败；4337216是构建前链接选项顺序检查失败；4336626/4336627训练PP1024超时；4336716训练PP64卡tokenizer并超时。全部失败保留。新产物固定PPL与完整测速通过前，不替换生产部署，不报告PGO性能收益。

登记说明曾因本地PowerShell默认ASCII管道损坏中文。submission_metadata_corrections.json保留原始及修正后的4337425/4337427描述，原始submission_registry.jsonl不改；作业脚本、环境和运行参数未受影响。Excel写入器合并证据目录内对应修正文件，后续重建仍保持正确描述。

日志：D:/compete/Qwen38_CPU_实验日志.xlsx。限定采集快照下载到evidence/job_updates，统一写入器合并时保留其他任务记录、人工备注及原始样本。

15:56更新：4337427已BUILD_GEN通过，TRAIN_PP_UNSCORED，repack到blk20、RSS约35GB；4337257在blk33、RSS约60GB。两者继续运行，尚未取得训练完成结果。若退出124但末尾仍持续repack，应在新作业内延长合成训练时限，不改变固定PPL的590秒或正式测速参数；在RUN期间不重复提交。
