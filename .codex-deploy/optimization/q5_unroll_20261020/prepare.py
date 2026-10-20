import difflib
import hashlib
import json
from pathlib import Path

r=Path(__file__).resolve().parent
old=r.parent/'q5_paircvt_20261020'
root='/work/apac2602/qwen38-cpu/optimization/20261020-q5-unroll'
identity=json.loads((r.parent/'compiler_pgo/source_identity.json').read_text(encoding='utf-8'))
name='ggml/src/ggml-cpu/arch/x86/quants.c'
raw=(Path('D:/compete/q8-avx2-v2/source')/name).read_bytes()
assert hashlib.sha256(raw).hexdigest()==identity['files'][name]
text=raw.decode();a=text.index('void ggml_vec_dot_q5_1_q8_1(');b=text.index('#elif defined(__AVX__)',a)
part=text[a:b]
before='''    // Main loop
    for (; ib < nb; ++ib) {'''
after='''    // Expose adjacent block loads while preserving the original ordered
    // vector accumulator and minimum-term sum; no additional FP chains.
#if defined(__INTEL_COMPILER)
#pragma unroll(4)
#endif
    for (; ib < nb; ++ib) {'''
assert part.count(before)==1
data=(text[:a]+part.replace(before,after)+text[b:]).encode()
p=r/'variants/q5-unroll4'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
(r/'q5-unroll4.patch').write_text(''.join(difflib.unified_diff(text.splitlines(True),data.decode().splitlines(True),fromfile='a/'+name,tofile='b/'+name)),encoding='utf-8')
(r/'manifest.json').write_text(json.dumps({'base_commit':identity['revision'],'variants':{'q5-unroll4':{'file':name,'original_sha256':hashlib.sha256(raw).hexdigest(),'sha256':hashlib.sha256(data).hexdigest()}}},indent=2),encoding='utf-8')
for f in ['copy_verify.py','ppl_gate.lsf','matmul_check.cpp','compare.py','disassemble.py','dot_check.cpp','bench.py']:
    s=(old/f).read_text(encoding='utf-8').replace('20261020-q5-paircvt','20261020-q5-unroll').replace('finite FP16 conversion batching','ordered Q5 loop unrolling').replace('Q5 paired-FP16-conversion actual-library','Q5 ordered-unroll actual-library')
    if f=='bench.py':
        s=s.replace("summary={'dot_checks':checks", "summary={'assembly_statistics':json.loads((out/'dot-assembly-stats.json').read_text()),'dot_checks':checks")
    (r/f).write_bytes(s.encode())
s=(old/'build_and_pair.lsf').read_text(encoding='utf-8').replace('20261020-q5-paircvt','20261020-q5-unroll').replace('q5-paircvt','q5-unroll4').replace('q5_paircvt','q5_unroll4')
s=s.replace("grep -Eq 'vcvtph2ps' \"$OUT/dot-candidate-assembly.txt\"",'python3 "$ROOT/assembly_stats.py" "$OUT" > "$OUT/assembly-stats.log"')
(r/'build_and_pair.lsf').write_bytes(s.encode())
d=json.loads((old/'submission.json').read_text(encoding='utf-8'))
d.update(script=root+'/build_and_pair.lsf',kind='Q5_1有序循环展开源码筛选',purpose='Intel pragma unroll(4)用于Q5_1 x Q8_1原始AVX2循环，增加相邻块读取的调度空间；保留单条向量累加器和原summs顺序。独立官方源码副本，不叠加FP16转换、Q5掩码等补丁。',environment={'SOURCE_VARIANT':'q5-unroll4'},lsf_args=['-J','qwen38_q5_unroll4'],case_prefix='confirm-q5-unroll4',baseline_case='confirm-q5-unroll4-baseline_{job_id}')
d['config']=d['config'].replace('反汇编检查vcvtph2ps','保存实际函数反汇编和FMA/查表/跳转指令静态计数').replace('262432组输入3重复','262432组输入3重复')
d['note']='循环展开能否增加并行调度由Intel生成代码和实际微基准判断；不宣称指令计数等于性能。262432组有限输入差分及矩阵要求逐bit一致；无内核收益即结束，不重跑同一候选。'+json.loads((r.parent/'q5_mask_20261019/submission.json').read_text(encoding='utf-8'))['note']
(r/'submission.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'variant':'q5-unroll4','sha256':hashlib.sha256(data).hexdigest()}))
