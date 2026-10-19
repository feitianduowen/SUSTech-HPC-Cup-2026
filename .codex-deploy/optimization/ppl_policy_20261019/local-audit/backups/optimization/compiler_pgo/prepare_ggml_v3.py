import json
from pathlib import Path

root=Path(__file__).resolve().parent
remote='/work/apac2602/qwen38-cpu/optimization/20261019-compiler-pgo'
text=(root/'pipeline_ggml_pgo_v2.lsf').read_text(encoding='utf-8')
text=text.replace('pipeline_ggml_pgo_v2.lsf','pipeline_ggml_pgo_v3.lsf')
text=text.replace('"-DCMAKE_EXE_LINKER_FLAGS=$link $pgo"','"-DCMAKE_EXE_LINKER_FLAGS=$link"')
text=text.replace('"-DCMAKE_SHARED_LINKER_FLAGS=$link $pgo"','"-DCMAKE_SHARED_LINKER_FLAGS=$link"')
# C/C++ driver flags still supply PGO for GGML links. Target -no-prof-* options
# now come last, instead of being overridden by CMAKE_*_LINKER_FLAGS.
old='stage BUILD_CONTROL\nbuild_stage control plain\nstage PPL_CONTROL\ngate control 01\n'
reuse='''stage REUSE_VERIFIED_CONTROL
CONTROL_PARENT=4337216
CONTROL_OUT="$ROOT/results/$CONTROL_PARENT"
CONTROL_BUILD="$ROOT/builds/$CONTROL_PARENT/control"
sha256sum -c "$CONTROL_OUT/control-build/sha256.txt" > "$OUT/control-parent-sha256.txt"
python3 - "$CONTROL_OUT/01_control/perplexity_result.json" <<'PY'
import json,sys
p=json.load(open(sys.argv[1]))
assert p['status']=='PASS' and 2.755752 <= p['ppl'] <= 2.783448
c=p['conditions']
assert (c['ppl_ctx'],c['ppl_chunks'],c['ppl_batch'],c['ppl_ubatch'],c['threads'],c['kv_cache_k'],c['kv_cache_v'],c['numa'],c['warmup'],c['gpu_layers'])==(512,2,512,256,38,'f16','f16','distribute',False,0)
PY
test ! -e "$BUILDS/control"
ln -s "$CONTROL_BUILD" "$BUILDS/control"
mkdir -p "$OUT/01_control" "$OUT/control-build"
cp "$CONTROL_OUT/01_control/perplexity_result.json" "$OUT/01_control/perplexity_result.json"
for file in configure.command CMakeCache.txt quantize-tests.log sha256.txt; do
    cp "$CONTROL_OUT/control-build/$file" "$OUT/control-build/$file"
done
printf 'Reused immutable control from job %s; no control rebuild or PPL rerun.\\n' "$CONTROL_PARENT" > "$OUT/control-reuse.txt"
'''
assert old in text
text=text.replace(old,reuse)
(root/'pipeline_ggml_pgo_v3.lsf').write_bytes(text.encode())
spec=json.loads((root/'ggml_v2_O3.json').read_text(encoding='utf-8'))
spec.update(script=remote+'/pipeline_ggml_pgo_v3.lsf',retry_of='4337216',kind='GGML定向PGO V3/参数顺序修复/训练/PPL',purpose='修复4337216预检发现的链接参数覆盖：仅由C/C++ driver flags启用GGML PGO，使非GGML目标禁用选项最后生效；复用已核验的control',lsf_args=['-J','qwen38_O3_ggml_pgo_v3'])
spec['config']+='；V3移除CMAKE_EXE/SHARED_LINKER_FLAGS中的重复PGO选项，保留C/CXX driver PGO选项；链接预检必须确认非GGML最后为-no-prof-*；control来自4337216，同源码同plain flags且SHA256核验、PPL2.7767 PASS，不重新构建/跑control PPL；gen/use与计数在新独立目录'
spec['note']='4337216 control PPL2.7767 PASS；gen预检发现目标-no-prof-gen被后面的全局-prof-gen覆盖，尚未编译gen或训练，提前失败记录保留。本次修正全局链接参数重复。control仅只读复用，SHA256和完整固定PPL条件强制检查；pgo构建仍必须独立通过固定PPL。4337222为账户另一路薄main保留PGO的试验，本轮不改动或重复提交。'
spec['ppl_scope']='control按SHA256及固定条件核验后复用4337216的PPL，未重跑；pgo为新反馈构建独立固定PPL'
(root/'ggml_v3_O3.json').write_bytes(json.dumps(spec,ensure_ascii=False,indent=2).encode())
print(root/'pipeline_ggml_pgo_v3.lsf')
