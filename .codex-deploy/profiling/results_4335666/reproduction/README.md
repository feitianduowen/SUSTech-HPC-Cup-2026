# Intel 构建的 CPU Profiling

服务器工作目录：`/work/apac2602/qwen38-cpu`。

本目录脚本针对已经通过 PPL 验证的同一套二进制，不修改模型、计算代码或编译选项。采样结果用于优化诊断，不能直接作为正式评分成绩。

## 采集

在登录节点提交，实际采集在 LSF 分配的单个 Gold 6148 节点运行：

```bash
cd /work/apac2602/qwen38-cpu
bsub < scripts/profile_probe.lsf
# 等待 profiling.status 显示 PROBE_READY mode=hw，再提交：
bsub < scripts/profile_cases.lsf
```

申请 40 slots，计算线程固定为 38。两个负载顺序执行，均保留 `-b 2048 -ub 512 -ctk f16 -ctv f16 -ngl 0 --numa distribute -r 10`。PP 使用 `-p 2048 -n 0`，TG 使用 `-p 0 -n 128 -d 2048`。

VTune 2023.1 使用 driverless 硬件事件采样、10 ms 采样间隔、2048 字节调用栈。不需要管理员权限，也不修改内核设置。内存带宽采集探测失败，因为系统没有可用的 Intel sampling driver；本方案不宣称得到 DRAM 带宽或 NUMA 远程访问计数。

采集器以暂停状态启动。`profile_exec.py` 记录原始 benchmark 输出、PID 和带时间戳的进度。独立的 `profile_monitor.py` 在首次正式 `prompt run 1/10` 或 `generation run 1/10` 后恢复采样；恢复命令的延迟写入 `resume.json`。恢复命令不会暂停计算进程。

测量窗口不包含启动、模型加载、预热和 TG 首次 depth prefill；包含重复之间的调度、TG 缓存状态恢复，以及退出前的短暂清理。`/proc` 监控记录 CPU 累积时间、RSS、缺页和 NUMA 驻留页分布。NUMA 页分布不是远程访问量。

## 文件与复查

`profiling/last_result` 指向最新的 `profiling/results_<JOBID>`，其中包含：

- `environment.txt`、`deployment_manifest.json`、`artifact_verification.json`：环境和构建身份。
- 每个负载的 `bench.json`：原始 10 次时间和吞吐；`bench.log`、`events.jsonl`：原始进度及时间。
- `vtune/`：完整原始采样；`summary.txt`、`hotspots.csv`、`threads.csv`：导出报告。
- `system.jsonl`、`resume.json`：独立系统监控和采样窗口证据。
- `analysis.json`：固定参数校验和 OS 样本汇总。

```bash
OUT=$(cat profiling/last_result)
python3 scripts/profile_status.py "$OUT"
python3 scripts/verify_profile_artifacts.py "$PWD" "$OUT/artifact_verification.json"
python3 scripts/analyze_profiles.py "$OUT"

VTUNE=/share/intel/oneapi-2023.1/vtune/2023.1.0/bin64/vtune
$VTUNE -report summary -r "$OUT/pp2048/vtune"
$VTUNE -report hotspots -r "$OUT/tg128_d2048/vtune" -group-by function
```

Release 构建保留函数符号，但没有完整源码调试行信息；热点优先定位到函数，源码位置通过同一版本源文件核对。自定义线程屏障可能不会被 VTune 自动计入 Spin Time，需结合具体函数分析。
