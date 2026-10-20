import difflib
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
old=here.parent/'f32_dot_20261019'
root='/work/apac2602/qwen38-cpu/optimization/20261019-q5-mask'
identity=json.loads((here.parent/'compiler_pgo/source_identity.json').read_text(encoding='utf-8'))
name='ggml/src/ggml-cpu/arch/x86/quants.c'
raw=(Path('D:/compete/q8-avx2-v2/source')/name).read_bytes()
assert hashlib.sha256(raw).hexdigest()==identity['files'][name]
text=raw.decode()
start=text.index('void ggml_vec_dot_q5_1_q8_1(')
end=text.index('#elif defined(__AVX__)',start)
part=text[start:end]
before='''        __m256i bxhi = bytes_from_bits_32(x[ib].qh);
        bxhi = _mm256_and_si256(bxhi, _mm256_set1_epi8(0x10));'''
after='''#if defined(__AVX512BW__) && defined(__AVX512VL__)
        // Expand one high-bit mask directly to the corresponding byte lanes.
        // The integer dot, scale products and ordered FMA remain unchanged.
        uint32_t high_bits;
        memcpy(&high_bits, x[ib].qh, sizeof(high_bits));
        const __m256i bxhi = _mm256_maskz_set1_epi8((__mmask32) high_bits, 0x10);
#else
        __m256i bxhi = bytes_from_bits_32(x[ib].qh);
        bxhi = _mm256_and_si256(bxhi, _mm256_set1_epi8(0x10));
#endif'''
assert part.count(before)==1
data=(text[:start]+part.replace(before,after)+text[end:]).encode()
dest=here/'variants/q5-mask'/name
dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
(here/'q5-mask.patch').write_text(''.join(difflib.unified_diff(text.splitlines(True),data.decode().splitlines(True),fromfile='a/'+name,tofile='b/'+name)),encoding='utf-8')
manifest={'base_commit':identity['revision'],'variants':{'q5-mask':{'file':name,'original_sha256':hashlib.sha256(raw).hexdigest(),'sha256':hashlib.sha256(data).hexdigest()}}}
(here/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for f in ['copy_verify.py','ppl_gate.lsf','matmul_check.cpp']:
    (here/f).write_bytes((old/f).read_bytes().replace(b'20261019-f32-dot',b'20261019-q5-mask'))
s=(old/'compare.py').read_text(encoding='utf-8')
s=s.replace("'PASS' if not bad else 'FAIL'", "'PASS' if not bad and not bit else 'FAIL'").replace('if bad:','if bad or bit:').replace('1e-4 + 5e-5*abs(baseline); float reassociation permitted; independent long-double dot test and fixed model PPL also required','bit-exact required; integer-only unpack change')
(here/'compare.py').write_text(s,encoding='utf-8')
s=(old/'build_and_pair.lsf').read_text(encoding='utf-8').replace('f32_acc8','q5_mask').replace('f32-acc8','q5-mask').replace('20261019-f32-dot','20261019-q5-mask').replace('F32_DOT_REFERENCE_CHECK','Q5_DOT_EXACT_CHECK').replace('F32_DOT_MICROBENCH','Q5_DOT_MICROBENCH')
s=s.replace('"$OUT/dot-$name" --check >','"$OUT/dot-$name" --check "$OUT/dot-$name.bin" >')
s=s.replace('stage Q5_DOT_MICROBENCH','''stage Q5_DOT_ASSEMBLY
for name in baseline candidate; do
    BIN="$BUILD/bin"
    [[ "$name" != baseline ]] || BIN="$BASE/build/bin"
    objdump -d --disassemble=ggml_vec_dot_q5_1_q8_1 "$BIN/libggml-cpu.so" > "$OUT/dot-$name-assembly.txt"
done
grep -Eq 'vpbroadcastb.*%k[0-7]|vpmovm2b' "$OUT/dot-candidate-assembly.txt"
stage Q5_DOT_MICROBENCH''')
s=s.replace('# Candidate first in both jobs. A reverse-order confirmation is needed if\n# apparent gains survive these initial full-workload screening measurements.\nfor name in candidate baseline; do', '''# Skip the expensive model phase unless the alternating kernel screen improves.
advance=$(python3 -c 'import json,sys;print(int(json.load(open(sys.argv[1]))["advance_to_model"]))' "$OUT/summary.json")
if [[ "$advance" == 0 ]]; then
    stage COMPLETE_KERNEL_SCREEN_NO_GAIN
    exit 0
fi
# Bracket the candidate with identical original builds; retain order limitations.
for name in baseline candidate baseline_after; do''')
s=s.replace('if [[ "$name" == baseline ]]; then CASE_ROOT="$BASE"; ordinal=01; fi','''if [[ "$name" == baseline ]]; then CASE_ROOT="$BASE"; ordinal=01; fi
    if [[ "$name" == baseline_after ]]; then CASE_ROOT="$BASE"; ordinal=03; fi''')
(here/'build_and_pair.lsf').write_bytes(s.encode())
submission={
 'script':root+'/build_and_pair.lsf','kind':'Q5_1整数高位解包源码优化',
 'purpose':'Q5_1 x Q8_1 AVX2分支在AVX512BW/VL平台改用掩码字节广播展开第5位，保留所有浮点算术及累加顺序；独立原版源码副本。',
 'environment':{'SOURCE_VARIANT':'q5-mask'},'lsf_args':['-J','qwen38_q5_mask'],
 'config':'Intel Classic2021.9 O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model; OpenMP ON/BLAS OFF; hg_6148单节点40slots,38推理线程close/cores。3687源码SHA核验，仅arch/x86/quants.c修改。四工具构建、量化测试、矩阵144配置3重复要求逐bit一致；实际Q5函数8480组输入3重复与原版逐bit一致，反汇编检查新掩码指令。五个长度单核CPU0/membind0微基准10轮AB/BA。至少一个代表长度2560或6144提升>=3%、10轮至少7轮胜出且各长度退化<=5%才进入模型阶段：baseline→candidate→baseline_after，各自固定PPL t/tb38 c512 chunks2 b512ub256 f16KV ngl0 NUMA distribute no-warmup590s ±5%，通过后PP2048/TG128d2048各r10 b2048ub512。',
 'baseline':'同节点本作业01_baseline原版Intel，03_baseline_after再次原版对照；直接dot及矩阵测试均对原版生产库',
 'case_prefix':'confirm-q5-mask','baseline_case':'confirm-q5-mask-baseline_{job_id}',
 'comparison_scope':'same-node','ppl_scope':'各case独立固定PPL；微基准未通过收益门槛则不运行模型PPL/PP/TG',
 'note':'微基准无收益则保留结果结束作业，不能标作模型PPL已通过。完整模型顺序仍可能受缓存/NUMA驻留影响，三段对照不能证明正式收益；全部原始样本保留，旧源码不覆盖。'
}
(here/'submission.json').write_text(json.dumps(submission,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest))
