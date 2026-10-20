import difflib
import hashlib
import json
from pathlib import Path

r=Path(__file__).resolve().parent
root='/work/apac2602/qwen38-cpu/optimization/20261020-softmax-rows'
old=r.parent/'f32_dot_20261019'
identity=json.loads((r.parent/'compiler_pgo/source_identity.json').read_text(encoding='utf-8'))
name='ggml/src/ggml-cpu/ops.cpp'
raw=(Path('D:/compete/q8-avx2-v2/source')/name).read_bytes()
assert hashlib.sha256(raw).hexdigest()==identity['files'][name]
text=raw.decode()
a=text.index('static void ggml_compute_forward_soft_max_f32(')
b=text.index('\nvoid ggml_compute_forward_soft_max(',a)
part=text[a:b]
before='''    for (int64_t i03 = 0; i03 < ne03; i03++) {
        for (int64_t i02 = 0; i02 < ne02; i02++) {
            for (int64_t i01 = ith; i01 < ne01; i01 += nth) {'''
after='''    // Distribute all independent rows, including heads and batches. This
    // keeps short-query attention from assigning every head to worker zero.
    const int64_t nrows = ne01 * ne02 * ne03;
    for (int64_t row = ith; row < nrows; row += nth) {
        const int64_t i01 = row % ne01;
        const int64_t i02 = (row / ne01) % ne02;
        const int64_t i03 = row / (ne01 * ne02);'''
assert part.count(before)==1
part=part.replace(before,after)
ending='''            }
        }
    }
}
'''
assert part.endswith(ending)
part=part[:-len(ending)]+'''    }
}
'''
# Unindent the unchanged per-row body for review.
body_a=part.index('                const int64_t i11')
body_b=part.rindex('    }\n}')
body=part[body_a:body_b]
body=''.join(line[8:] if line.startswith('        ') else line for line in body.splitlines(True))
part=part[:body_a]+body+part[body_b:]
data=(text[:a]+part+text[b:]).encode()
p=r/'variants/softmax-rows'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
(r/'softmax-rows.patch').write_text(''.join(difflib.unified_diff(text.splitlines(True),data.decode().splitlines(True),fromfile='a/'+name,tofile='b/'+name)),encoding='utf-8')
(r/'manifest.json').write_text(json.dumps({'base_commit':identity['revision'],'variants':{'softmax-rows':{'file':name,'original_sha256':hashlib.sha256(raw).hexdigest(),'sha256':hashlib.sha256(data).hexdigest()}}},indent=2),encoding='utf-8')
for f in ['copy_verify.py','ppl_gate.lsf']:
    (r/f).write_bytes((old/f).read_bytes().replace(b'20261019-f32-dot',b'20261020-softmax-rows'))
s=(old/'build_and_pair.lsf').read_text(encoding='utf-8')
s=s.replace('f32_acc8','softmax_rows').replace('f32-acc8','softmax-rows').replace('20261019-f32-dot','20261020-softmax-rows')
start=s.index('stage BUILD_MATMUL_CHECK')
s=s[:start]+'''stage BUILD_SOFTMAX_CHECK
BASE=/work/apac2602/qwen38-cpu/llama.cpp
for name in baseline candidate; do
    BIN="$BUILD/bin"
    [[ "$name" != baseline ]] || BIN="$BASE/build/bin"
    icpc -gxx-name=/share/base/e5/gcc/11.2.0/bin/g++ -std=c++17 -O2 -fp-model strict -no-ftz -diag-disable=10441 -I"$SRC/ggml/include" "$ROOT/softmax_check.cpp" -L"$BIN" -Wl,-rpath,"$BIN",--no-as-needed -lggml-cpu -lggml -lggml-base -Wl,--no-as-needed,/lib64/libm.so.6,--as-needed -qopenmp -o "$OUT/check-$name" > "$OUT/check-$name-build.log" 2>&1
    ldd "$OUT/check-$name" > "$OUT/check-$name-ldd.txt"
    ! grep -q 'not found' "$OUT/check-$name-ldd.txt"
    stage "SOFTMAX_CHECK_$name"
    timeout --signal=TERM --kill-after=10s 900 "$OUT/check-$name" --check "$OUT/$name.bin" > "$OUT/$name-check.json" 2> "$OUT/$name-check.log"
done
stage SOFTMAX_MICROBENCH
python3 "$ROOT/bench.py" "$OUT" > "$OUT/softmax-bench.log" 2>&1

# The op may be bypassed by fused attention in the full model. Keep full model
# tests independent of synthetic operator speedup, and retain every sample.
for name in baseline candidate baseline_after; do
    stage "PPL_PP10_TG10_$name"
    CASE_ROOT="$SRC"
    ordinal=02
    if [[ "$name" == baseline ]]; then CASE_ROOT="$BASE"; ordinal=01; fi
    if [[ "$name" == baseline_after ]]; then CASE_ROOT="$BASE"; ordinal=03; fi
    sha256sum "$CASE_ROOT/build/bin/llama-bench" "$CASE_ROOT/build/bin/llama-perplexity" "$CASE_ROOT/build/bin/"lib*.so* > "$OUT/$name-sha256.txt"
    COMPILER_BUILD_ROOT="$CASE_ROOT" RUN_BENCH=1 EXPERIMENT_OUTPUT_DIR="$OUT/${ordinal}_$name" bash "$OUT/ppl_gate.lsf" > "$OUT/$name-bench.log" 2>&1
done
stage COMPLETE
'''
(r/'build_and_pair.lsf').write_bytes(s.encode())
d={
 'script':root+'/build_and_pair.lsf','kind':'Softmax跨head/batch行调度源码修改',
 'purpose':'Softmax把query/head/batch全部独立行按线程分配，避免单query多head仅一线程工作；每行浮点计算顺序不改。独立官方源码副本，仅ops.cpp修改，不叠加Q5/Q8/PGO。',
 'environment':{'SOURCE_VARIANT':'softmax-rows'},'lsf_args':['-J','qwen38_softmax_rows'],
 'config':'Intel Classic2021.9 O3 precise/no-ftz CORE-AVX512 qsimd-honor-fp-model；OpenMP ON/BLAS OFF；hg_6148 40slots，推理38线程close/cores。3687源码SHA核验、四工具构建、量化测试、ldd。Softmax实际graph 1280配置×3重复，1/38线程、none/F16/F32 mask、ALiBi、sink、mask广播/完整head-batch、原地/非原地、两种scale，输出有限/归一化及与原版逐bit核验。接口只支持连续输入。实际graph四种代表形状10轮AB/BA微基准。随后原版→候选→原版各自固定PPL t/tb38 c512 chunks2 b512ub256 f16KV ngl0 NUMA distribute no-warmup 590s ±5%，各PP2048/TG128d2048 r10 b2048ub512。',
 'baseline':'同节点本作业01_baseline原版Intel，03_baseline_after再次原版；Softmax算子对原版实际库',
 'case_prefix':'confirm-softmax-rows','baseline_case':'confirm-softmax-rows-baseline_{job_id}','comparison_scope':'same-node',
 'ppl_scope':'每case独立固定PPL，无共享PPL',
 'note':'融合attention可能绕过普通Softmax，算子收益不能当作模型收益。保留A/B/A顺序、缓存、NUMA局限；未验证完整模型前不替换部署。源码/原始数据/慢样本全部保留。'
}
(r/'submission.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'variant':'softmax-rows','file':name,'sha256':hashlib.sha256(data).hexdigest()}))
