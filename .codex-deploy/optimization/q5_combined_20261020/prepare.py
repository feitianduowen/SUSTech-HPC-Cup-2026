import difflib
import hashlib
import json
from pathlib import Path

r=Path(__file__).resolve().parent
old=r.parent/'q5_unroll_20261020'
mask=r.parent/'q5_mask_20261019'
root='/work/apac2602/qwen38-cpu/optimization/20261020-q5-combined'
identity=json.loads((r.parent/'compiler_pgo/source_identity.json').read_text(encoding='utf-8'))
name='ggml/src/ggml-cpu/arch/x86/quants.c'
raw=(Path('D:/compete/q8-avx2-v2/source')/name).read_bytes()
u=(old/'variants/q5-unroll4'/name).read_bytes()
m=(mask/'variants/q5-mask'/name).read_bytes()
assert hashlib.sha256(raw).hexdigest()==identity['files'][name]
assert hashlib.sha256(u).hexdigest()==json.loads((old/'manifest.json').read_text())['variants']['q5-unroll4']['sha256']
assert hashlib.sha256(m).hexdigest()==json.loads((mask/'manifest.json').read_text())['variants']['q5-mask']['sha256']
ut=u.decode();mt=m.decode()
a=mt.index('#if defined(__AVX512BW__)',mt.index('void ggml_vec_dot_q5_1_q8_1('));b=mt.index('#endif',a)+len('#endif')
before='''        __m256i bxhi = bytes_from_bits_32(x[ib].qh);
        bxhi = _mm256_and_si256(bxhi, _mm256_set1_epi8(0x10));'''
a_u=ut.index('void ggml_vec_dot_q5_1_q8_1(');b_u=ut.index('#elif defined(__AVX__)',a_u)
part=ut[a_u:b_u];assert part.count(before)==1
data=(ut[:a_u]+part.replace(before,mt[a:b])+ut[b_u:]).encode()
p=r/'variants/q5-mask-unroll4'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
(r/'q5-mask-unroll4.patch').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),data.decode().splitlines(True),fromfile='a/'+name,tofile='b/'+name)),encoding='utf-8')
(r/'manifest.json').write_text(json.dumps({'base_commit':identity['revision'],'variants':{'q5-mask-unroll4':{'file':name,'original_sha256':hashlib.sha256(raw).hexdigest(),'sha256':hashlib.sha256(data).hexdigest()}},'reference_jobs':{'mask':'4338563','unroll':'4340602'}},indent=2),encoding='utf-8')
for f in ['copy_verify.py','ppl_gate.lsf','matmul_check.cpp','compare.py','disassemble.py','dot_check.cpp','assembly_stats.py']:
    s=(old/f).read_text(encoding='utf-8').replace('20261020-q5-unroll','20261020-q5-combined').replace('ordered Q5 loop unrolling','ordered Q5 mask plus loop unrolling')
    if f=='assembly_stats.py':s=s.replace("['baseline','candidate']","['baseline','mask','unroll','candidate']")
    (r/f).write_bytes(s.encode())
s=(old/'build_and_pair.lsf').read_text(encoding='utf-8').replace('20261020-q5-unroll','20261020-q5-combined').replace('q5-unroll4','q5-mask-unroll4').replace('q5_unroll4','q5_combined')
a=s.index('stage Q5_DOT_EXACT_CHECK');b=s.index('stage Q5_DOT_MICROBENCH',a)
part=s[a:b].replace('for name in baseline candidate; do','for name in baseline mask unroll candidate; do')
part=part.replace('    [[ "$name" != baseline ]] || BIN="$BASE/build/bin"','''    [[ "$name" != baseline ]] || BIN="$BASE/build/bin"
    [[ "$name" != mask ]] || BIN="$MASK_BIN"
    [[ "$name" != unroll ]] || BIN="$UNROLL_BIN"''')
refs='''stage VERIFY_SINGLE_CHANGE_REFERENCES
MASK_BIN=/work/apac2602/qwen38-cpu/optimization/20261019-q5-mask/sources/q5-mask-4338563/build/bin
UNROLL_BIN=/work/apac2602/qwen38-cpu/optimization/20261020-q5-unroll/sources/q5-unroll4-4340602/build/bin
sha256sum -c /work/apac2602/qwen38-cpu/optimization/20261019-q5-mask/results/4338563/sha256.txt > "$OUT/mask-reference-check.log"
sha256sum -c /work/apac2602/qwen38-cpu/optimization/20261020-q5-unroll/results/4340602/sha256.txt > "$OUT/unroll-reference-check.log"
sha256sum "$MASK_BIN/"lib*.so* "$UNROLL_BIN/"lib*.so* > "$OUT/reference-sha256.txt"
'''
s=s[:a]+refs+part+s[b:]
s=s.replace('python3 "$ROOT/bench.py" "$OUT" > "$OUT/dot-bench.log" 2>&1','''python3 "$ROOT/bench.py" "$OUT" > "$OUT/dot-bench.log" 2>&1
sha256sum -c "$OUT/reference-sha256.txt" > "$OUT/reference-after-check.log"''')
(r/'build_and_pair.lsf').write_bytes(s.encode())
d=json.loads((old/'submission.json').read_text(encoding='utf-8'))
d.update(script=root+'/build_and_pair.lsf',kind='Q5掩码加循环展开组合源码筛选',purpose='独立原版源码组合Q5_1高位掩码解包和Intel unroll(4)，不改变原浮点累加链；同节点同时比较原版、仅掩码4338563、仅展开4340602、组合四个实际库版本，确认组合是否有增量收益。',environment={'SOURCE_VARIANT':'q5-mask-unroll4'},lsf_args=['-J','qwen38_q5_combined'],case_prefix='confirm-q5-combined',baseline_case='confirm-q5-combined-baseline_{job_id}')
d['config']='Intel Classic2021.9 O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model；OpenMP ON/BLAS OFF；hg_6148 40slots，38推理线程close/cores。独立源码3687文件SHA，仅quants.c组合两项已单独验证改动。四工具构建、量化测试、矩阵144配置3重复逐bit；原版/仅掩码/仅展开/组合四实际库各262432点积用例3重复逐bit；参考产物SHA前后核验。单核CPU0/membind0，5长度、12轮四版本循环换序，每版本在每位置各3次。至少2560或6144相对两个单项中更快者>=2%、相对每个单项至少9/12轮胜出，所有长度相对最快单项>=0.95x才进入模型阶段。完整模型原版→组合→原版，各独立固定PPL t/tb38 c512 chunks2 b512ub256 f16KV ngl0 NUMA distribute no-warmup590s±5%，PP2048/TG128d2048各r10 b2048ub512。'
d['baseline']='微基准同时比较原版、仅掩码、仅展开；推进门槛相对更快单项，不只对原版。模型对照01_baseline和03_baseline_after原版Intel。'
d['note']='12轮仅用于四版本算子筛选，完整PP/TG仍各r10。组合可能增加寄存器压力，不能将两个单项收益相加；未达到增量门槛即停止、模型PPL未运行。保留所有样本及原始数据，正式收益尚未确立，不替换部署。'
(r/'submission.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'variant':'q5-mask-unroll4','sha256':hashlib.sha256(data).hexdigest()}))
