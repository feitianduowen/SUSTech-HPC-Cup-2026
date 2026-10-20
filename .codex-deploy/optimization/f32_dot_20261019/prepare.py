import difflib
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent
old=here.parent/'other_source_20261019'
name='ggml/src/ggml-cpu/vec.cpp'
raw=(Path('D:/compete/q8-avx2-v2/source')/name).read_bytes()
identity=json.loads((here.parent/'compiler_pgo/source_identity.json').read_text(encoding='utf-8'))
assert hashlib.sha256(raw).hexdigest()==identity['files'][name]
text=raw.decode()
insert='''#if defined(__AVX512F__)
    // Long F32 dot products: eight independent accumulation chains.
    // Preserve the original implementation for short vectors and other ISAs.
    if (n >= 256) {
        __m512 accum[8] = {};
        int i = 0;
        for (; i <= n - 128; i += 128) {
            for (int j = 0; j < 8; ++j) {
                accum[j] = _mm512_fmadd_ps(_mm512_loadu_ps(x + i + 16*j),
                                          _mm512_loadu_ps(y + i + 16*j), accum[j]);
            }
        }
        if (i <= n - 64) {
            for (int j = 0; j < 4; ++j) {
                accum[j] = _mm512_fmadd_ps(_mm512_loadu_ps(x + i + 16*j),
                                          _mm512_loadu_ps(y + i + 16*j), accum[j]);
            }
            i += 64;
        }
        for (int j = 0; j < 4; ++j) accum[j] = _mm512_add_ps(accum[j], accum[j+4]);
        accum[0] = _mm512_add_ps(accum[0], accum[2]);
        accum[1] = _mm512_add_ps(accum[1], accum[3]);
        float result = _mm512_reduce_add_ps(_mm512_add_ps(accum[0], accum[1]));
        for (; i < n; ++i) result += x[i]*y[i];
        *s = result;
        return;
    }
#endif

'''
pos=text.index('#if defined(GGML_SIMD)')
modified=(text[:pos]+insert+text[pos:]).encode()
variant='f32-acc8'
out=here/'variants'/variant/name
out.parent.mkdir(parents=True,exist_ok=True)
out.write_bytes(modified)
(here/(variant+'.patch')).write_bytes(''.join(difflib.unified_diff(text.splitlines(True),modified.decode().splitlines(True),fromfile='a/'+name,tofile='b/'+name)).encode())
manifest={'base_commit':identity['revision'],'variants':{variant:{'file':name,'original_sha256':hashlib.sha256(raw).hexdigest(),'sha256':hashlib.sha256(modified).hexdigest()}}}
(here/'manifest.json').write_bytes(json.dumps(manifest,indent=2).encode())
remote='/work/apac2602/qwen38-cpu/optimization/20261019-f32-dot'
for filename in ['copy_verify.py','matmul_check.cpp','ppl_gate.lsf']:
    data=(old/filename).read_text(encoding='utf-8').replace('20261019-other-source','20261019-f32-dot')
    (here/filename).write_bytes(data.encode())
script=(old/'build_and_pair.lsf').read_text(encoding='utf-8').replace('20261019-other-source','20261019-f32-dot').replace('qwen38_other_source','qwen38_f32_acc8').replace('%J.other_source','%J.f32_acc8')
script=script.replace('[[ "$VARIANT" == gemm-balanced || "$VARIANT" == row-quant ]]','[[ "$VARIANT" == f32-acc8 ]]')
anchor='python3 "$ROOT/compare.py" "$OUT" > "$OUT/differential.log"'
extra='''
stage F32_DOT_REFERENCE_CHECK
for name in baseline candidate; do
    BIN="$BUILD/bin"
    [[ "$name" != baseline ]] || BIN="$BASE/build/bin"
    icpc -gxx-name=/share/base/e5/gcc/11.2.0/bin/g++ -std=c++17 -O2 -fp-model strict -no-ftz -diag-disable=10441 -I"$SRC/ggml/include" "$ROOT/dot_check.cpp" -L"$BIN" -Wl,-rpath,"$BIN",--no-as-needed -lggml-cpu -lggml -lggml-base -Wl,--no-as-needed,/lib64/libm.so.6,--as-needed -o "$OUT/dot-$name" > "$OUT/dot-$name-build.log" 2>&1
    ldd "$OUT/dot-$name" > "$OUT/dot-$name-ldd.txt"
    ! grep -q 'not found' "$OUT/dot-$name-ldd.txt"
    timeout 300 "$OUT/dot-$name" --check > "$OUT/dot-$name-check.json" 2> "$OUT/dot-$name-check.log"
done
stage F32_DOT_MICROBENCH
python3 "$ROOT/bench.py" "$OUT" > "$OUT/dot-bench.log" 2>&1
'''
script=script.replace(anchor,anchor+'\n'+extra)
(here/'build_and_pair.lsf').write_bytes(script.encode())
spec={'script':remote+'/build_and_pair.lsf','kind':'F32源码内核修改、数值检查及完整对照',
 'purpose':'F32点积长向量AVX512改用8条独立累加链，减少依赖延迟；n<256和其他ISA保持原实现。独立源码副本，不叠加前轮Q8/PGO/调度修改。',
 'environment':{'SOURCE_VARIANT':variant},'lsf_args':['-J','qwen38_f32_acc8'],
 'config':'Intel Classic2021.9 O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model，OpenMP ON/BLAS OFF；hg_6148 40slots，38推理线程close/cores；官方源码3687文件SHA核验，新副本仅vec.cpp修改。四工具构建/量化测试/ldd；矩阵144配置3次重复对照，允许舍入误差1e-4+5e-5*abs(reference)，记录逐bit差异；实际F32函数约8500组长度/错位/数值模式对long-double参考误差界检查。单核CPU0 dot微基准10轮AB/BA保留全样本，不计模型分数。然后candidate先baseline后，各独立新固定PPL t/tb38 c512 chunks2 b512ub256 f16KV ngl0 NUMA distribute no-warmup 590s ±5%；PPL通过后PP2048/TG128d2048各r10 b2048ub512。',
 'baseline':'本作业01_baseline生产Intel原版，同节点后执行；直接dot函数检查和微基准对生产原版，微基准交替AB/BA',
 'case_prefix':'f32-acc8','baseline_case':'f32-acc8-baseline_{job_id}',
 'ppl_scope':'candidate/baseline分别本作业新固定PPL，无共享PPL',
 'note':'增加累加链改变浮点舍入顺序，不能宣称逐bit一致；依据高精度参考误差及官方PPL判断。单核微基准不是模型性能，完整模型比较保留顺序/缓存限制。有稳定收益再反序验证，任何正确性阶段失败即停止。旧源码/构建/原始JSON/慢样本全部保留。'}
(here/'submission.json').write_bytes(json.dumps(spec,ensure_ascii=False,indent=2).encode())
print(here)
