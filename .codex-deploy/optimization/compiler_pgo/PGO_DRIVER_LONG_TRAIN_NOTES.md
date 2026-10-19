# PGO训练时限修复：4337488

更新时间：2026-10-19T16:42:19.041976+08:00

已核对4337257、4337427均TRAIN_PP_UNSCORED超时退出124，并非训练或PPL通过。前者20分钟仍repack到blk41；后者完成模型加载与图预留，末尾attach_threadpool/set_n_threads38。两作业PP JSON未完整、TG/merge/use/PPL未执行，失败周期计数只作诊断，绝不复用。

4337488通过pipeline_driver_long_train.lsf于16:40提交，已RUN于r13n38，40slots，Intel Classic2021.9 icc/icpc、O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model，OpenMP ON、BLAS OFF。与4337427相比只延长非计分合成PP64及TG8@D64各r1的时限：PP1200/TG900秒改为各3600秒。gen重新构建并在新目录产生计数；薄main加GGML保留插桩、冷模块关闭、gen链接保留DSO依赖的策略不变。源文件及模型不变；38线程、PPL590秒与正式PP/TG十次参数不变。

control只读复用4337222经SHA与全部固定条件核验的PPL2.7767 PASS，未在新作业重跑。新PGO产物仍须独立固定PPL通过，随后才做完整性能对照。本作业未测完整PP/TG，不计算分数。

4337448是账户内另一路非GGML全关闭插桩的3600秒方案，本轮仅检查及登记，不改动它。16:40观察为38线程持续消耗CPU、RSS约83GiB；已进入重排后的计算阶段。两项活动作业均不重复提交。

若再次超时，应先检查实际热点和OS进展，不能只反复扩大时间。新作业通过统一submit_logged.py登记；Excel保留所有失败、人工备注、原始样本及control PPL复用口径。旧登记中文修正文件submission_metadata_corrections.json继续保留。

16:43阶段更新：4337488已通过BUILD_GEN及构建后插桩范围检查，16:42:59进入TRAIN_PP_UNSCORED。正式PPL与完整性能验证尚未完成。
