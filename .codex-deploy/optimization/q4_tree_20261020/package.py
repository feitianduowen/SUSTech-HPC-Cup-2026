import json
import tarfile
from pathlib import Path

here = Path(__file__).resolve().parent
base = here.parent
root = '/work/apac2602/qwen38-cpu/optimization/20261020-q4-tree'
text = (base / 'q5_unroll_20261020/build_and_pair.lsf').read_text(encoding='utf-8')
text = text.replace('qwen38_q5_unroll4', 'qwen38_q4_int_tree').replace('%J.q5_unroll4', '%J.q4_int_tree')
text = text.replace('20261020-q5-unroll', '20261020-q4-tree').replace('q5-unroll4', 'q4-int-tree')
# Preserve the immutable original's known fingerprint before building or testing.
text = text.replace('stage COPY_VERIFY_SOURCE', 'stage VERIFY_ORIGINAL_IDENTITY\nsha256sum -c /work/apac2602/qwen38-cpu/optimization/20261020-q5-combined/results/4340624/baseline-sha256.txt > "$OUT/original-identity.log"\nstage COPY_VERIFY_SOURCE')
start = text.index('stage Q5_DOT_EXACT_CHECK')
end = text.index('\n# Skip the expensive model phase', start)
text = text[:start] + '''stage BUILD_Q4_DIRECT_DRIVER
icpc -gxx-name=/share/base/e5/gcc/11.2.0/bin/g++ -std=c++17 -O2 -fp-model strict -no-ftz -diag-disable=10441 "$ROOT/q4_check_bench.cpp" -ldl -o "$OUT/q4-driver" > "$OUT/q4-driver-build.log" 2>&1
BASELIB="$BASE/build/bin/libggml-cpu.so"
CANDLIB="$BUILD/bin/libggml-cpu.so"
sha256sum "$BASE/build/bin/llama-bench" "$BASE/build/bin/llama-perplexity" "$BASE/build/bin/"lib*.so* "$BUILD/bin/llama-bench" "$BUILD/bin/llama-perplexity" "$BUILD/bin/"lib*.so* > "$OUT/test-identity-sha256.txt"
stage Q4_DIRECT_EXACT_AND_MICROBENCH
timeout --signal=TERM --kill-after=10s 1200 numactl --physcpubind=0 --membind=0 "$OUT/q4-driver" "$BASELIB" "$CANDLIB" "$OUT" > "$OUT/q4-driver.log" 2>&1
sha256sum -c "$OUT/test-identity-sha256.txt" > "$OUT/test-identity-after.log"
python3 "$ROOT/analyze.py" "$OUT" > "$OUT/q4-analysis.log"
''' + text[end:]
text = text.replace('stage COMPLETE\n', 'sha256sum -c "$OUT/test-identity-sha256.txt" > "$OUT/final-identity.log"\nstage COMPLETE\n')
(here / 'build_and_pair.lsf').write_text(text, encoding='utf-8', newline='\n')
spec = {
    'script': root + '/build_and_pair.lsf', 'kind': 'Q4_K repack GEMV整数平衡加法树源码筛选',
    'purpose': '新方向：修改PP profiling占9.55%的ggml_gemv_q4_K_8x8_q8_K，将两条八项16位整数加法链改为平衡树，保留乘加项、scale和浮点累加顺序；检查是否缩短整数依赖链。',
    'environment': {'SOURCE_VARIANT': 'q4-int-tree'}, 'lsf_args': ['-J', 'qwen38_q4_int_tree'],
    'config': 'Intel Classic2021.9 icc/icpc O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model；OpenMP ON/BLAS OFF；hg_6148单节点40slots，模型38线程close/cores。从原版完整复制3687文件并逐SHA验证，仅arch/x86/repack.cpp一个函数改变；独立源码/构建保留旧目录。四工具构建和量化测试；144矩阵配置3重复逐bit；实际原版/候选动态库导出Q4_Kx8/Q8_K GEMV经dladdr核验，nr1直接差分128128用例3重复，8种n、6种nc、3种指针对齐、8种量化原始pattern及d/dmin全部63488有限FP16编码，输出guard验证。实际库驻留/约256MiB流式、n2560/6144和nc8/64，共8配置10轮交替AB/BA，CPU0/membind0。驻留nc64至少一项配对中位吞吐>=3%、>=7/10胜出，所有配置不低于-5%才进入原版→候选→原版，各独立固定PPL(t/tb38,c512,chunks2,b512ub256,f16KV,ngl0,NUMAdistribute,no-warmup590s,±5%)后PP2048/TG128d2048各r10,b2048ub512。前后SHA核验。',
    'baseline': '同节点原始Intel O3动态库。算子同数据交替AB/BA；若进入模型则01_baseline及03_baseline_after双原版保留，不能只选低速首轮。',
    'case_prefix': 'confirm-q4-tree', 'baseline_case': 'confirm-q4-tree-baseline_{job_id}',
    'comparison_scope': 'same-node', 'ppl_scope': '通过算子正确性与收益门槛才进入每case独立固定PPL，否则PPL/PP/TG未运行',
    'note': '16位VPADDW模2^16加法可重括号，VPMADDWD及浮点表达式不改。仍要求实际库逐位完全一致；不通过则失败。平衡树可能增加寄存器压力或被编译器改写，不能预设收益。开发筛选，不替换部署；保留所有样本，模型顺序漂移需单独判读。动态库双句柄按实际函数地址核验，通用矩阵验证另用独立链接两个可执行程序。'
}
(here / 'submission.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding='utf-8')
with tarfile.open(here / 'inputs.tar.gz', 'w:gz') as archive:
    for path in here.rglob('*'):
        if path.is_file() and path.suffix in ['.py', '.cpp', '.lsf', '.json', '.patch'] and '__pycache__' not in str(path):
            archive.add(path, arcname=path.relative_to(here))
print(here / 'inputs.tar.gz')
