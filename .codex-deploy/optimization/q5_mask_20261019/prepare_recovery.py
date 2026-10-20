import json
from pathlib import Path

r=Path(__file__).resolve().parent
s=(r/'build_and_pair.lsf').read_text(encoding='utf-8')
s=s.replace('qwen38_q5_mask','qwen38_q5_mask_resume').replace('%J.q5_mask.','%J.q5_mask_resume.')
s=s.replace('SRC="$ROOT/sources/$VARIANT-$LSB_JOBID"','SRC="$ROOT/sources/q5-mask-4338563"')
s=s.replace('cp "$ROOT/build_and_pair.lsf" "$OUT/pipeline.lsf"','cp "$ROOT/resume_checks.lsf" "$OUT/pipeline.lsf"')
a=s.index('stage COPY_VERIFY_SOURCE');b=s.index('stage BUILD_MATMUL_CHECK')
s=s[:a]+'''stage VERIFY_EXISTING_SOURCE_AND_BUILD
python3 "$ROOT/verify_existing.py" > "$OUT/source-verification.json"
cp "$ROOT/results/4338563/sha256.txt" "$OUT/reused-build-sha256.txt"
sha256sum -c "$OUT/reused-build-sha256.txt" > "$OUT/reused-build-check.log"
cp "$BUILD/CMakeCache.txt" "$OUT/CMakeCache.txt"
for name in llama-cli llama-server llama-bench llama-perplexity; do
    test -x "$BUILD/bin/$name"
    ldd "$BUILD/bin/$name" >> "$OUT/ldd.txt"
done
! grep -q 'not found' "$OUT/ldd.txt"
"$BUILD/bin/test-quantize-fns" > "$OUT/quantize-tests.log" 2>&1
flags='-fp-model precise -no-ftz -xCORE-AVX512 -qsimd-honor-fp-model -diag-disable=10441'

'''+s[b:]
s=s.replace('objdump -d --disassemble=ggml_vec_dot_q5_1_q8_1 "$BIN/libggml-cpu.so"','python3 "$ROOT/disassemble.py" "$BIN/libggml-cpu.so"')
(r/'resume_checks.lsf').write_bytes(s.encode())
d=json.loads((r/'submission.json').read_text(encoding='utf-8'))
d['script']=d['script'].replace('build_and_pair.lsf','resume_checks.lsf')
d['purpose']='修复4338563的objdump2.30不支持--disassemble=函数名问题；按nm符号地址范围反汇编，复用4338563原封不动的Q5候选源码及Intel构建，重新核验源码/产物后补跑数值、微基准及有条件模型测试。'
d['lsf_args']=['-J','qwen38_q5_mask_resume']
d['config']='复用4338563源码及构建，3687文件SHA及3个关键产物SHA复核，无重新编译；其余验证配置：'+d['config']
d['note']='4338563原始失败记录保留；本作业仅修复反汇编验证工具兼容性。'+d['note']
(r/'resume_submission.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
