import difflib
import hashlib
import json
import re
import tarfile
from pathlib import Path

base = Path('D:/compete/.codex-deploy/optimization')
old = base / 'q4_tree_20261020'
out = base / 'q4_maskshuffle_20261020'
assert not (out / 'manifest.json').exists()
out.mkdir(exist_ok=True)
relative = 'ggml/src/ggml-cpu/arch/x86/repack.cpp'
data = (Path('D:/compete/q8-avx2-v2/source') / relative).read_bytes()
identity = json.loads((base / 'compiler_pgo/source_identity.json').read_text(encoding='utf-8'))
assert hashlib.sha256(data).hexdigest() == identity['files'][relative]
text = data.decode()
start = text.index('void ggml_gemv_q4_K_8x8_q8_K(')
end = text.index('\nvoid ggml_gemv_iq4_nl_8x8_q8_0', start)
body = text[start:end]
first = r'_mm256_blend_epi32\((rhs_vec_\w+)\s*,\s*_mm256_shuffle_epi32\((rhs_vec_\w+), 177\), 170\)'
second = r'_mm256_blend_epi32\(_mm256_shuffle_epi32\((rhs_vec_\w+), 177\)\s*,\s*(rhs_vec_\w+), 170\)'
body, n0 = re.subn(first, r'q4_pair_even(\1, \2)', body)
body, n1 = re.subn(second, r'q4_pair_odd(\1, \2)', body)
assert n0 == n1 == 8
anchor = '#if defined(__AVX2__)\n'
helpers = '''    // Fuse lane shuffle+merge while preserving the original dword lane order.
    const auto q4_pair_even = [](__m256i a, __m256i b) {
#if defined(__AVX512F__) && defined(__AVX512VL__)
        return _mm256_mask_shuffle_epi32(a, (__mmask8) 0xAA, b, 177);
#else
        return _mm256_blend_epi32(a, _mm256_shuffle_epi32(b, 177), 170);
#endif
    };
    const auto q4_pair_odd = [](__m256i a, __m256i b) {
#if defined(__AVX512F__) && defined(__AVX512VL__)
        return _mm256_mask_shuffle_epi32(b, (__mmask8) 0x55, a, 177);
#else
        return _mm256_blend_epi32(_mm256_shuffle_epi32(a, 177), b, 170);
#endif
    };
'''
assert body.count(anchor) == 1
body = body.replace(anchor, anchor + helpers)
modified = (text[:start] + body + text[end:]).encode()
variant = 'q4-maskshuffle'
dest = out / 'variants' / variant / relative
dest.parent.mkdir(parents=True)
dest.write_bytes(modified)
(out / (variant + '.patch')).write_text(''.join(difflib.unified_diff(text.splitlines(True), modified.decode().splitlines(True), fromfile='a/'+relative, tofile='b/'+relative)), encoding='utf-8')
manifest = {'base_commit': identity['revision'], 'variants': {variant: {'file': relative, 'original_sha256': hashlib.sha256(data).hexdigest(), 'sha256': hashlib.sha256(modified).hexdigest()}}}
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
for name in ['copy_verify.py', 'ppl_gate.lsf', 'matmul_check.cpp', 'compare.py', 'analyze.py', 'q4_check_bench.cpp', 'build_and_pair.lsf']:
    content = (old / name).read_text(encoding='utf-8').replace('20261020-q4-tree', '20261020-q4-maskshuffle').replace('q4-int-tree', variant).replace('qwen38_q4_int_tree', 'qwen38_q4_maskshuffle').replace('%J.q4_int_tree', '%J.q4_maskshuffle')
    content = content.replace('Q4 integer balanced-add tree', 'Q4 mask-shuffle lane-preserving fusion')
    content = content.replace('Only VPADDW integer sums reparenthesized; modulo2^16 associativity preserves lanes before the original VPMADDWD. All floating point scales, FMAs, accumulation order and final permutation remain unchanged.', 'Only shuffle+blend pairs replaced by AVX512VL masked dword shuffle with complementary masks0xAA/0x55. Every lane and all integer/FP arithmetic chains retained. Original AVX2 fallback preserved; target-node path tested.')
    if name == 'analyze.py':
        content = content.replace("'advance_to_model': advance,", "'advance_to_model': advance, 'assembly_statistics': json.loads((out / 'q4-assembly-stats.json').read_text()),")
    if name == 'build_and_pair.lsf':
        content = content.replace('stage BUILD_MATMUL_CHECK', '''stage Q4_ASSEMBLY_AND_LANE_PROBE
python3 "$ROOT/assembly_stats.py" "$OUT" /work/apac2602/qwen38-cpu/llama.cpp/build/bin/libggml-cpu.so "$BUILD/bin/libggml-cpu.so" > "$OUT/assembly-stats.log"
icpc -gxx-name=/share/base/e5/gcc/11.2.0/bin/g++ -std=c++17 -O2 -xCORE-AVX512 -diag-disable=10441 "$ROOT/mask_shuffle_probe.cpp" -o "$OUT/mask-shuffle-probe" > "$OUT/mask-shuffle-probe-build.log" 2>&1
"$OUT/mask-shuffle-probe" > "$OUT/mask-shuffle-probe.json"
stage BUILD_MATMUL_CHECK''')
    (out / name).write_text(content, encoding='utf-8', newline='\n')
root = '/work/apac2602/qwen38-cpu/optimization/20261020-q4-maskshuffle'
spec = json.loads((old / 'submission.json').read_text(encoding='utf-8'))
spec.update(script=root+'/build_and_pair.lsf', kind='Q4_K repack GEMV掩码shuffle融合源码筛选',
    purpose='4341178整数树逐位PASS但算子收益仅-0.17%到+0.49%，未推进模型。本轮从原版新建独立源码，针对原版汇编仍保留8次vpblendmd和8次前置shuffle，显式用AVX512VL互补0xAA/0x55掩码shuffle融合16处shuffle+blend表达式；原整数累加链和浮点链均保留。',
    environment={'SOURCE_VARIANT': variant}, lsf_args=['-J', 'qwen38_q4_maskshuffle'],
    config=spec['config']+' 本轮仅原版一个GEMV函数16处shuffle+blend改为掩码shuffle，保留非AVX512VL回退；未叠加整数树。额外执行4096组32位随机lane布局差分及原版/候选实际函数汇编计数，统计静态指令不可代替运行时性能。',
    case_prefix='confirm-q4-maskshuffle', baseline_case='confirm-q4-maskshuffle-baseline_{job_id}',
    note='独立原版源码，仅lane重排表达式改变。期望减少shuffle/merge指令，但Intel可能还原为同样代码，必须看实际汇编和10轮AB/BA；不预设收益。4096组lane差分与128128实际库GEMV用例、144矩阵配置要求0bit差异。所有驻留/流式样本保留；不达门槛不运行模型PPL/PP/TG。模型阶段仍保留双原版及顺序漂移，未证明收益前不替换部署。')
(out / 'submission.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding='utf-8')
print(out)
