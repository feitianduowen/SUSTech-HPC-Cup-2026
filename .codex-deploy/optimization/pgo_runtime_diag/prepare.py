import json
from pathlib import Path

root=Path(__file__).resolve().parent
remote='/work/apac2602/qwen38-cpu/optimization/20261019-pgo-runtime-diag'
template=(root.parent/'orchestrator/build_variant.lsf').read_text(encoding='utf-8')
configure=template[template.index('cmake -S "$SRC"'):template.index('cmake --build "$BUILD"')]
configure=configure.replace('-DLLAMA_BUILD_TESTS=ON','-DLLAMA_BUILD_TESTS=OFF').replace('-DLLAMA_BUILD_EXAMPLES=ON','-DLLAMA_BUILD_EXAMPLES=OFF').replace('-DLLAMA_BUILD_TOOLS=ON','-DLLAMA_BUILD_TOOLS=OFF').replace('-DLLAMA_BUILD_SERVER=ON','-DLLAMA_BUILD_SERVER=OFF')
configure=configure.replace('> "$OUT/configure.log"','> "$OUT/configure-$variant.log"')
lsf='''#!/bin/bash
#BSUB -J qwen38_pgo_runtime_diag
#BSUB -q ssc-cpu
#BSUB -m hg_6148
#BSUB -n 40
#BSUB -R "span[ptile=40]"
#BSUB -W 00:30
#BSUB -o /work/apac2602/qwen38-cpu/logs/%J.pgo_runtime_diag.out
#BSUB -e /work/apac2602/qwen38-cpu/logs/%J.pgo_runtime_diag.err
set -Eeuo pipefail
source /work/apac2602/qwen38-cpu/scripts/env.sh
ROOT=/work/apac2602/qwen38-cpu/optimization/20261019-pgo-runtime-diag
SRC=/work/apac2602/qwen38-cpu/optimization/20261018-v1/sources/native
OUT="$ROOT/results/$LSB_JOBID"
mkdir -p "$OUT" "$OUT/profiles/broad" "$OUT/profiles/hot" "$OUT/profiles/plain"
phase=INIT
trap 'rc=$?; echo "FAILED phase=$phase exit=$rc" > "$OUT/job.status"; exit "$rc"' ERR
stage() { phase=$1; echo "$phase time=$(date -Is)" > "$OUT/job.status"; }
[[ "$LSB_DJOB_NUMPROC" == 40 ]]
[[ $(getconf _NPROCESSORS_ONLN) == 40 ]]
lscpu | grep -q 'Intel(R) Xeon(R) Gold 6148'
unset KMP_AFFINITY GOMP_CPU_AFFINITY KMP_BLOCKTIME OMP_WAIT_POLICY INTEL_PROF_DUMP_INTERVAL INTEL_PROF_DUMP_CUMULATIVE
{ date -Is; hostname; lscpu; module list; icc --version; icpc --version; } > "$OUT/environment.txt" 2>&1
python3 /work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo/verify_source.py "$SRC" /work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo/source_identity.json > "$OUT/source-verification.json"
omp=ON
blas=OFF
for variant in broad hot; do
    stage BUILD_$variant
    BUILD="$OUT/$variant/build"
    flags='-fp-model precise -no-ftz -xCORE-AVX512 -qsimd-honor-fp-model -diag-disable=10441'
    extra=()
    if [[ "$variant" == broad ]]; then
        flags="$flags -prof-gen=threadsafe -prof-dir $OUT/profiles/broad"
    else
        extra=("-DCMAKE_PROJECT_INCLUDE=$ROOT/hot_sources.cmake" "-DQWEN_PROFILE_DIR=$OUT/profiles/hot")
    fi
'''+configure+'''
    cmake --build "$BUILD" --target ggml-cpu ggml -j40 > "$OUT/build-$variant.log" 2>&1
    cp "$BUILD/compile_commands.json" "$OUT/compile-$variant.json"
done
stage DRIVERS
for variant in plain broad hot; do
    BIN="$OUT/$variant/build/bin"
    [[ "$variant" != plain ]] || BIN=/work/apac2602/qwen38-cpu/llama.cpp/build/bin
    flags='-fp-model precise -no-ftz -xCORE-AVX512 -qsimd-honor-fp-model -diag-disable=10441'
    [[ "$variant" == plain ]] || flags="$flags -prof-gen=threadsafe -prof-dir $OUT/profiles/$variant"
    icpc -gxx-name=/share/base/e5/gcc/11.2.0/bin/g++ -O3 -g -std=c++17 $flags -I"$SRC/ggml/include" "$ROOT/runtime_probe.cpp" -L"$BIN" -Wl,-rpath,"$BIN",--no-as-needed -lggml-cpu -lggml -lggml-base -Wl,--no-as-needed,/lib64/libm.so.6,--as-needed -qopenmp -o "$OUT/probe-$variant" > "$OUT/driver-$variant.log" 2>&1
    ldd "$OUT/probe-$variant" > "$OUT/ldd-$variant.txt"
done
stage RUNTIME_CASES_AND_VTUNE
python3 -u "$ROOT/run_cases.py" "$OUT" > "$OUT/cases.log" 2>&1
stage DIAGNOSTIC_COMPLETE
'''
(root/'diagnostic.lsf').write_bytes(lsf.encode())
spec={'script':remote+'/diagnostic.lsf','kind':'PGO运行时合成诊断/VTune','purpose':'3600秒PGO训练连续超时后，先隔离多线程运行时开销：同节点比较普通GGML、全GGML插桩、仅热点源码插桩的1/38线程合成图，并采集全插桩热点','config':'Intel Classic2021.9，O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model；hg_6148单节点40slots；新独立GGML库构建/计数目录，不加载模型；F32矩阵256x256乘256x64后16个ADD节点，每配置10轮；plain→broad→hot顺序，1线程后38线程，每子进程60s诊断限时；关闭周期计数转储；VTune对broad38额外采样10s；合成诊断没有PPL/正式PP/TG/Score','baseline':'同节点生产Intel原版GGML库，匹配的1线程或38线程合成图；无完整模型性能baseline','note':'保持原模型与全部旧构建/计数/失败结果；只读官方源，独立构建。子进程超时作为诊断结果保留，不视为正式训练；诊断计数不得合并至模型PGO。hot仅arch/x86/quants.c与llamafile/sgemm.cpp插桩，运行时/同步/重排不插桩。该作业用于验证可能的计数竞争或运行时开销，当前不预断根因。','retry_of':'4337448'}
(root/'diagnostic.json').write_bytes(json.dumps(spec,ensure_ascii=False,indent=2).encode())
print(root/'diagnostic.lsf')
