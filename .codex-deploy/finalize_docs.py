from pathlib import Path
import re

root = Path(__file__).parent / 'package'
path = root / 'README.md'
text = path.read_text(encoding='utf-8').replace('4335568', '4335636')
text = re.sub(r'^环境：.*$', '环境：Intel Classic 2021.9（oneAPI 2023.1，icc/icpc）、CMake 3.28.1。GCC 11.2.0 提供标准头文件和 C++ 标准库支持；全部本项目 C/C++ 源文件由 Intel 编译。Release，精确浮点模式，显式保留非规格化数，AVX-512，Intel OpenMP；基础数学函数优先链接与参考构建相同的系统 libm。BLAS 和 GPU 后端关闭。在 Xeon Gold 6148 计算节点构建。', text, flags=re.M)
text = text.replace('## 查看部署结果', '''## 本次验证结果

验证作业 `4335636` 已于 2026-10-18 21:26（香港时间）完成，节点为 `r13n16`，状态 `READY`。

- 固定参数 PPL：**2.7767，PASS**。
- 相对参考基准 2.7696 的偏差：**+0.2563547083%**，符合 0.5% 容差。
- PPL 用时：277 秒。
- `/health` 返回 `ok`；普通文本生成通过。
- `/v1/chat/completions` 实际请求通过，返回 `OK`。
- 4 个模型分片及 WikiText 测试文件检查通过。

接口服务按需由 LSF 启动，使用下方启动命令。完整 PP/TG 性能评测尚未运行，可使用已适配的原文件名脚本提交。

## 查看部署结果''')
text = text.replace('cat deployment.status\n', 'cat deployment.status\ncat deployment_manifest.json\n', 1)
text = text.replace('健康', '健康')
path.write_text(text, encoding='utf-8', newline='\n')
(root / 'runtime_config.md').write_text('''# Runtime configuration

Source: llama.cpp v0.6.0, d81235049384534c167caea52b85a694f6103d14. Model computation source is unmodified.

Final compilers: Intel Classic 2021.9.0.20230302 (icc/icpc), from oneAPI 2023.1. Modules: cmake/3.28.1, gcc/11.2.0, icc/2023.1.0. GCC provides standard headers and libstdc++; the project C/C++ translation units are compiled by Intel.

C flags: -gcc-name=/share/base/e5/gcc/11.2.0/bin/gcc -fp-model precise -no-ftz -xCORE-AVX512 -qsimd-honor-fp-model -diag-disable=10441.

C++ flags: -gxx-name=/share/base/e5/gcc/11.2.0/bin/g++ -fp-model precise -no-ftz -xCORE-AVX512 -qsimd-honor-fp-model -diag-disable=10441.

Release uses -O3 -DNDEBUG. GGML_NATIVE=ON, GGML_OPENMP=ON, GGML_BLAS=OFF. Accelerator backends are disabled. Both executable and shared-library linker flags are -Wl,--no-as-needed,/lib64/libm.so.6,--as-needed. System libm is linked first for scalar math consistency with the reference environment. OpenMP is Intel libiomp5, using -qopenmp.

All jobs request one 40-slot node from hg_6148 in ssc-cpu. The queue does not accept the LSF exclusive flag; all 40 slots on the selected 40-slot node are allocated to the job. Inference uses 38 threads. No additional PP/TG runtime tuning is applied.

Common environment: OMP_NUM_THREADS=38, OMP_DYNAMIC=FALSE, OMP_PROC_BIND=close, OMP_PLACES=cores, OPENBLAS_NUM_THREADS=38, MKL_NUM_THREADS=38, BLIS_NUM_THREADS=38.

PPL: -t 38 -tb 38 -ngl 0 -c 512 -b 512 -ub 256 -ctk f16 -ctv f16 --numa distribute --chunks 2 --no-warmup.

PP: -t 38 -ngl 0 -b 2048 -ub 512 -ctk f16 -ctv f16 --numa distribute -p 2048 -n 0 -r 10 -o json.

TG: -t 38 -ngl 0 -b 2048 -ub 512 -ctk f16 -ctv f16 --numa distribute -p 0 -n 128 -d 2048 -r 10 -o json.

Successful deployment validation: job 4335636 on r13n16. PPL=2.7767, relative difference +0.2563547082611084%, PASS. Server health, completion generation, and chat completion PASS. The temporary validation server exits after the checks. The service launcher is scripts/server.lsf.

The HTTP server is for interactive use, not competition scoring. It uses 38 compute threads, 2048 context, f16 KV, CPU only, and loopback binding. Full PP/TG performance benchmarks have not been run for this deployment.
''', encoding='utf-8', newline='\n')
(root / 'agent_usage.md').write_text('''# Agent usage

OpenAI Codex configured an account-local deployment using the official shared source, model, dataset, and baseline. It adapted the supplied LSF scripts, built the required targets, checked fixed-parameter PPL, and tested real server completion and chat requests.

A GCC reference build passed PPL=2.7696. Intel LLVM presets produced PPL=2.8403, 2.8274, and 2.7931; their failed results are retained under the corresponding job result directories. They were not used for performance scoring.

The final Intel Classic build passed PPL=2.7767 (+0.2563547083%) in job 4335636. Server health, ordinary completion, and chat completion also passed. The final manifest records compiler paths, flags, model assets, and binary/library SHA-256 values.

No llama.cpp or ggml computation source was changed. No model weights, dataset content, official baseline JSON, benchmark statistics, or correctness thresholds were modified. Full PP/TG performance benchmarks were not run.
''', encoding='utf-8', newline='\n')

guide = Path('D:/compete/Qwen38_CPU_部署说明.md')
guide.write_text(text, encoding='utf-8', newline='\n')
